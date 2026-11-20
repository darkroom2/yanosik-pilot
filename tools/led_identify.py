#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from tools.nrf52_swd import (
        FLASH_SIZE,
        UICR_SIZE,
        NrfSwdClient,
        NrfSwdError,
        sha256_file,
    )
except ModuleNotFoundError:
    from nrf52_swd import (
        FLASH_SIZE,
        UICR_SIZE,
        NrfSwdClient,
        NrfSwdError,
        sha256_file,
    )


FLASH_SHA256 = "ec3060bb5d8160296f1891a2d4d2db7882535f80779dd6fe611bf300a475d826"
UICR_SHA256 = "8cf25c59ad391780435765317039d2256cc618ff036a3c0847033c8d593e13dd"


def validate_backups(flash: Path, uicr: Path) -> None:
    if not flash.is_file():
        raise ValueError(f"flash backup does not exist: {flash}")
    if not uicr.is_file():
        raise ValueError(f"uicr backup does not exist: {uicr}")
    if flash.stat().st_size != FLASH_SIZE:
        raise ValueError(
            f"flash size mismatch: expected {FLASH_SIZE} bytes, got {flash.stat().st_size}"
        )
    if uicr.stat().st_size != UICR_SIZE:
        raise ValueError(
            f"uicr size mismatch: expected {UICR_SIZE} bytes, got {uicr.stat().st_size}"
        )
    flash_hash = sha256_file(flash)
    uicr_hash = sha256_file(uicr)
    if flash_hash != FLASH_SHA256:
        raise ValueError(
            f"flash SHA-256 mismatch: expected {FLASH_SHA256}, got {flash_hash}"
        )
    if uicr_hash != UICR_SHA256:
        raise ValueError(
            f"uicr SHA-256 mismatch: expected {UICR_SHA256}, got {uicr_hash}"
        )


def record_mapping(answer18: str, answer19: str) -> dict[str, str]:
    allowed = {"blue", "green", "unknown"}
    answer18 = answer18.strip().lower()
    answer19 = answer19.strip().lower()
    if answer18 not in allowed or answer19 not in allowed:
        raise ValueError("LED answers must be blue, green, or unknown")
    known = [answer for answer in (answer18, answer19) if answer != "unknown"]
    if len(set(known)) != len(known):
        raise ValueError("P0.18 and P0.19 cannot both be the same known color")
    return {"P0.18": answer18, "P0.19": answer19}


def restore_archives(
    client: NrfSwdClient,
    flash: Path,
    uicr: Path,
    timeout: float,
) -> None:
    validate_backups(flash, uicr)
    try:
        client.erase_flash(confirm=True)
        client.wait_for_task(timeout)
    except (NrfSwdError, ValueError, OSError) as exc:
        raise NrfSwdError(f"erase before restore failed: {exc}") from exc
    try:
        client.restore("flash", flash)
        client.wait_for_task(timeout, label="flash", require_percent=True)
    except (NrfSwdError, ValueError, OSError) as exc:
        raise NrfSwdError(f"flash restore failed: {exc}") from exc
    try:
        client.restore("uicr", uicr)
        client.wait_for_task(timeout, label="uicr", require_percent=True)
    except (NrfSwdError, ValueError, OSError) as exc:
        raise NrfSwdError(f"uicr restore failed: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Identify P0.18/P0.19 LED colors and restore the original archive"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="build and flash the temporary LED fixture")
    run.add_argument("--host", default="swd.local")
    run.add_argument("--timeout", type=float, default=60.0)
    run.add_argument("--delay", type=int, default=2368)
    run.add_argument("--confirm", action="store_true")
    run.add_argument("--restore-confirm", action="store_true")
    run.add_argument(
        "--flash",
        type=Path,
        default=Path("dumps/full_flash.bin"),
    )
    run.add_argument(
        "--uicr",
        type=Path,
        default=Path("dumps/full_uicr.bin"),
    )
    run.add_argument("--output", type=Path)

    restore = subparsers.add_parser("restore", help="restore the original flash and UICR")
    restore.add_argument("--host", default="swd.local")
    restore.add_argument("--timeout", type=float, default=60.0)
    restore.add_argument("--confirm", action="store_true")
    restore.add_argument(
        "--flash",
        type=Path,
        default=Path("dumps/full_flash.bin"),
    )
    restore.add_argument(
        "--uicr",
        type=Path,
        default=Path("dumps/full_uicr.bin"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.command == "restore":
            if not args.confirm:
                raise NrfSwdError("restore requires --confirm")
            validate_backups(args.flash, args.uicr)
            client = NrfSwdClient(args.host, timeout=max(args.timeout, 0.1))
            restore_archives(client, args.flash, args.uicr, args.timeout)
            print("Original flash and UICR restore completed.")
            return 0

        if not args.confirm:
            raise NrfSwdError("LED flash operation requires --confirm")

        validate_backups(args.flash, args.uicr)
        client = NrfSwdClient(args.host, timeout=max(args.timeout, 0.1))
        client.glitch(delay=args.delay)
        subprocess.run(
            [
                "uv",
                "run",
                "pio",
                "run",
                "-d",
                "led_smoke_test",
                "-e",
                "led-smoke-test",
            ],
            check=True,
        )
        client.erase_flash(confirm=True)
        hex_file = Path("led_smoke_test/.pio/build/led-smoke-test/firmware.hex")
        client.upload_hex(hex_file, timeout=args.timeout)

        answer18 = input("Is P0.18 blue or green? [blue/green/unknown]: ")
        answer19 = input("Is P0.19 blue or green? [blue/green/unknown]: ")
        mapping = record_mapping(answer18, answer19)
        print(json.dumps(mapping, sort_keys=True))

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(mapping, sort_keys=True), encoding="utf-8")

        if args.restore_confirm:
            restore_archives(client, args.flash, args.uicr, args.timeout)
            print("Original flash and UICR restore completed.")
        else:
            print("Restore not performed. Run the separate `restore --confirm` command.")
        return 0
    except (NrfSwdError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
