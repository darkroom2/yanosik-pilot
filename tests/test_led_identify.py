import io
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.led_identify import (
    FLASH_SHA256,
    UICR_SHA256,
    main,
    record_mapping,
    validate_backups,
)


def test_validate_backups_accepts_exact_size_and_hash(tmp_path):
    flash = tmp_path / "full_flash.bin"
    uicr = tmp_path / "full_uicr.bin"

    import hashlib

    flash_data = b"f" * (512 * 1024)
    uicr_data = b"u" * (4 * 1024)
    flash.write_bytes(flash_data)
    uicr.write_bytes(uicr_data)

    flash_expected = hashlib.sha256(flash_data).hexdigest()
    uicr_expected = hashlib.sha256(uicr_data).hexdigest()
    with patch("tools.led_identify.FLASH_SHA256", flash_expected), patch(
        "tools.led_identify.UICR_SHA256", uicr_expected
    ):
        validate_backups(flash, uicr)


@pytest.mark.parametrize(
    ("wrong_kind", "wrong_sha"),
    [("flash", True), ("uicr", True)],
)
def test_validate_backups_rejects_wrong_hash(tmp_path, wrong_kind, wrong_sha):
    flash = tmp_path / "full_flash.bin"
    uicr = tmp_path / "full_uicr.bin"
    flash.write_bytes(b"f" * (512 * 1024))
    uicr.write_bytes(b"u" * (4 * 1024))

    import hashlib

    flash_hash = hashlib.sha256(flash.read_bytes()).hexdigest()
    uicr_hash = hashlib.sha256(uicr.read_bytes()).hexdigest()
    patch_target = "tools.led_identify.FLASH_SHA256" if wrong_kind == "flash" else "tools.led_identify.UICR_SHA256"
    with patch("tools.led_identify.FLASH_SHA256", flash_hash), patch(
        "tools.led_identify.UICR_SHA256", uicr_hash
    ), patch(patch_target, "0" * 64):
        with pytest.raises(ValueError, match=f"{wrong_kind}"):
            validate_backups(flash, uicr)


def test_record_mapping_accepts_distinct_or_unknown_values():
    assert record_mapping("blue", "green") == {"P0.18": "blue", "P0.19": "green"}
    assert record_mapping("unknown", "green") == {"P0.18": "unknown", "P0.19": "green"}


@pytest.mark.parametrize(
    ("answer18", "answer19"),
    [
        ("blue", "blue"),
        ("green", "green"),
        ("red", "green"),
        ("blue", "yellow"),
    ],
)
def test_record_mapping_rejects_invalid_or_duplicate_known_colors(answer18, answer19):
    with pytest.raises(ValueError):
        record_mapping(answer18, answer19)


def test_run_missing_confirm_has_no_side_effects(tmp_path):
    flash = tmp_path / "full_flash.bin"
    uicr = tmp_path / "full_uicr.bin"
    flash.write_bytes(b"x")
    uicr.write_bytes(b"x")

    with patch("tools.led_identify.NrfSwdClient") as client_type, patch(
        "tools.led_identify.subprocess.run"
    ) as subprocess_run:
        assert main(["run", "--host", "swd.local"]) == 1

    client_type.assert_not_called()
    subprocess_run.assert_not_called()


def test_run_confirm_validates_before_glitch_build_erase_and_upload():
    calls = []

    class FakeClient:
        def __init__(self, host, timeout):
            calls.append(("client", host, timeout))

        def glitch(self, delay):
            calls.append(("glitch", delay))

        def erase_flash(self, confirm):
            calls.append(("erase", confirm))

        def upload_hex(self, path, timeout):
            calls.append(("upload", path.name))

    def fake_validate(flash, uicr):
        calls.append(("validate", flash.name, uicr.name))

    def fake_run(command, check):
        calls.append(("build", command[-1]))
        return object()

    with patch("tools.led_identify.validate_backups", side_effect=fake_validate), patch(
        "tools.led_identify.NrfSwdClient", FakeClient
    ), patch("tools.led_identify.subprocess.run", side_effect=fake_run), patch(
        "builtins.input", side_effect=["blue", "green"]
    ):
        assert main([
            "run",
            "--host",
            "swd.local",
            "--confirm",
        ]) == 0

    assert calls[0][0] == "validate"
    assert ("glitch", 2368) in calls
    assert ("erase", True) in calls
    assert ("upload", "firmware.hex") in calls
    assert calls.index(("glitch", 2368)) < calls.index(("erase", True))


def test_restore_confirm_restores_flash_then_uicr_and_waits(tmp_path):
    flash = tmp_path / "full_flash.bin"
    uicr = tmp_path / "full_uicr.bin"
    flash.write_bytes(b"x")
    uicr.write_bytes(b"x")
    calls = []

    class FakeClient:
        def __init__(self, host, timeout):
            calls.append(("client", host, timeout))

        def erase_flash(self, confirm):
            calls.append(("erase", confirm))

        def restore(self, kind, path):
            calls.append(("restore", kind, path.name))

        def wait_for_task(self, timeout, label=None, require_percent=False):
            calls.append(("wait", timeout))

    with patch("tools.led_identify.validate_backups"), patch(
        "tools.led_identify.NrfSwdClient", FakeClient
    ):
        assert main([
            "restore",
            "--host",
            "swd.local",
            "--confirm",
            "--flash",
            str(flash),
            "--uicr",
            str(uicr),
        ]) == 0

    assert calls.count(("erase", True)) == 1
    assert calls.index(("erase", True)) < calls.index(("restore", "flash", flash.name))
    waits = [i for i, call in enumerate(calls) if call == ("wait", 60.0)]
    assert len(waits) == 3
    erase_index = calls.index(("erase", True))
    flash_index = calls.index(("restore", "flash", flash.name))
    uicr_index = calls.index(("restore", "uicr", uicr.name))
    assert erase_index < waits[0] < flash_index < waits[1] < uicr_index < waits[2]


def test_restore_without_confirm_has_no_side_effects(tmp_path):
    flash = tmp_path / "full_flash.bin"
    uicr = tmp_path / "full_uicr.bin"

    with patch("tools.led_identify.NrfSwdClient") as client_type, patch(
        "tools.led_identify.validate_backups"
    ) as validate:
        assert main([
            "restore",
            "--host",
            "swd.local",
            "--flash",
            str(flash),
            "--uicr",
            str(uicr),
        ]) == 1

    client_type.assert_not_called()
    validate.assert_not_called()


@pytest.mark.parametrize("kind", ["flash", "uicr"])
def test_validate_backups_rejects_wrong_size(tmp_path, kind):
    flash = tmp_path / "full_flash.bin"
    uicr = tmp_path / "full_uicr.bin"
    flash.write_bytes(b"f" * (512 * 1024 - 1 if kind == "flash" else 512 * 1024))
    uicr.write_bytes(b"u" * (4 * 1024 - 1 if kind == "uicr" else 4 * 1024))

    with pytest.raises(ValueError, match=kind):
        validate_backups(flash, uicr)


def test_restore_archives_reports_flash_region(tmp_path):
    from tools.led_identify import restore_archives
    from tools.nrf52_swd import NrfSwdError

    flash = tmp_path / "full_flash.bin"
    uicr = tmp_path / "full_uicr.bin"

    class FakeClient:
        def erase_flash(self, confirm):
            pass

        def wait_for_task(self, timeout):
            pass

        def restore(self, region, path):
            raise NrfSwdError("flash write failed")

    with patch("tools.led_identify.validate_backups"):
        with pytest.raises(NrfSwdError, match="flash restore failed"):
            restore_archives(FakeClient(), flash, uicr, 60.0)


def test_direct_script_entry_shows_restore_confirmation_error():
    result = subprocess.run(
        [sys.executable, "tools/led_identify.py", "restore"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "restore requires --confirm" in result.stderr
