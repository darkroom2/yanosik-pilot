import hashlib
import io
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.nrf52_swd import NrfSwdClient, NrfSwdError, validate_dump


def test_validate_dump_accepts_flash_size_and_rejects_one_byte_short(tmp_path):
    assert validate_dump("flash", b"x" * (512 * 1024)) == 512 * 1024
    with pytest.raises(ValueError):
        validate_dump("flash", b"x" * (512 * 1024 - 1))


def test_validate_dump_accepts_uicr_size_and_rejects_one_byte_short():
    assert validate_dump("uicr", b"x" * (4 * 1024)) == 4 * 1024
    with pytest.raises(ValueError):
        validate_dump("uicr", b"x" * (4 * 1024 - 1))


def test_restore_rejects_wrong_flash_size_before_http(tmp_path):
    path = tmp_path / "full_flash.bin"
    path.write_bytes(b"x" * (512 * 1024 - 1))
    client = NrfSwdClient("swd.local")

    with patch("tools.nrf52_swd.urllib.request.urlopen") as urlopen:
        with pytest.raises(ValueError):
            client.restore("flash", path)
    urlopen.assert_not_called()


def test_restore_rejects_wrong_uicr_size_before_http(tmp_path):
    path = tmp_path / "full_uicr.bin"
    path.write_bytes(b"x" * (4 * 1024 - 1))
    client = NrfSwdClient("swd.local")

    with patch("tools.nrf52_swd.urllib.request.urlopen") as urlopen:
        with pytest.raises(ValueError):
            client.restore("uicr", path)
    urlopen.assert_not_called()


def test_glitch_sends_default_2368_for_every_glitch_delay_field():
    client = NrfSwdClient("swd.local")

    with patch("tools.nrf52_swd.urllib.request.urlopen") as urlopen:
        urlopen.side_effect = [
            io.BytesIO(b'{"ok":true,"started":true}'),
            io.BytesIO(b'{"glitch":{"running":false},"task":{"active":false}}'),
        ]
        client.glitch()

    request = urlopen.call_args_list[0].args[0]
    body = request.data.decode()
    assert "delay=2368" in body
    assert "delay_end=2368" in body


def test_dump_download_writes_bytes_and_reports_sha256(tmp_path):
    client = NrfSwdClient("swd.local")
    payload = b"x" * (4 * 1024)
    output = tmp_path / "full_uicr.bin"

    with patch("tools.nrf52_swd.urllib.request.urlopen") as urlopen:
        urlopen.return_value = io.BytesIO(payload)
        client.download("uicr", output)

    assert output.read_bytes() == payload
    assert hashlib.sha256(payload).hexdigest() == client.sha256(output)


def test_dump_download_accepts_non_utf8_binary_payload(tmp_path):
    client = NrfSwdClient("swd.local")
    payload = b"\xff\xfe" + b"x" * (4 * 1024 - 2)
    output = tmp_path / "full_uicr.bin"

    with patch("tools.nrf52_swd.urllib.request.urlopen") as urlopen:
        urlopen.return_value = io.BytesIO(payload)
        client.download("uicr", output)

    assert output.read_bytes() == payload


def test_wait_for_task_rejects_restore_last_error():
    client = NrfSwdClient("swd.local")

    with patch.object(
        client,
        "status",
        return_value={
            "task": {"active": False},
            "last_error": "flash write failed",
        },
    ):
        with pytest.raises(NrfSwdError) as exc:
            client.wait_for_task(timeout=1.0)

    assert "flash write failed" in str(exc.value)


def test_glitch_times_out_and_disables_glitcher():
    client = NrfSwdClient("swd.local")

    with patch.object(
        client,
        "_request",
        side_effect=[
            {"ok": True, "started": True},
            {"state": "glitch"},
            {"ok": True},
        ],
    ):
        with pytest.raises(NrfSwdError) as exc:
            client.glitch(timeout=0.01)

    assert "timed out" in str(exc.value)


@pytest.mark.parametrize(
    ("code", "server_text"),
    [(400, "invalid parameter"), (409, "glitcher is running")],
)
def test_http_errors_preserve_server_text(code, server_text):
    client = NrfSwdClient("swd.local")
    error = urllib.error.HTTPError(
        "http://swd.local/api/v1/status",
        code,
        server_text,
        {},
        io.BytesIO(server_text.encode()),
    )

    with patch("tools.nrf52_swd.urllib.request.urlopen", side_effect=error):
        with pytest.raises(NrfSwdError) as exc:
            client.status()

    assert server_text in str(exc.value)


def test_timeout_response_raises_nrf_swd_error():
    client = NrfSwdClient("swd.local")

    with patch(
        "tools.nrf52_swd.urllib.request.urlopen",
        side_effect=TimeoutError("timed out"),
    ):
        with pytest.raises(NrfSwdError) as exc:
            client.status()

    assert "timed out" in str(exc.value)
