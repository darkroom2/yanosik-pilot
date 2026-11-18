#!/usr/bin/env python3

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Literal


FLASH_SIZE = 512 * 1024
UICR_SIZE = 4 * 1024
DEFAULT_DELAY = 2368
ORIGINAL_SHA256 = {
    "flash": "ec3060bb5d8160296f1891a2d4d2db7882535f80779dd6fe611bf300a475d826",
    "uicr": "8cf25c59ad391780435765317039d2256cc618ff036a3c0847033c8d593e13dd",
}


class NrfSwdError(RuntimeError):
    pass


def validate_dump(kind: Literal["flash", "uicr"], data: bytes) -> int:
    expected = FLASH_SIZE if kind == "flash" else UICR_SIZE
    if kind not in ("flash", "uicr"):
        raise ValueError(f"unsupported dump kind: {kind}")
    if len(data) != expected:
        raise ValueError(f"{kind} size mismatch: expected {expected} bytes, got {len(data)}")
    return len(data)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class NrfSwdClient:
    def __init__(self, host: str, timeout: float = 10.0):
        self.base_url = host if host.startswith("http://") or host.startswith("https://") else f"http://{host}"
        self.timeout = timeout

    def _request(self, path: str, method: str = "GET", data: bytes | None = None, content_type: str = "application/x-www-form-urlencoded"):
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": content_type},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            raise NrfSwdError(f"HTTP {exc.code}: {text}") from exc
        except urllib.error.URLError as exc:
            raise NrfSwdError(str(exc.reason)) from exc
        except TimeoutError as exc:
            raise NrfSwdError(str(exc)) from exc

        if not body:
            return {}
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return body

    def status(self) -> dict:
        result = self._request("/api/v1/status")
        return result if isinstance(result, dict) else {}

    def glitch(
        self,
        delay: int = DEFAULT_DELAY,
        delay_end: int = DEFAULT_DELAY,
        power_off: int = 50,
        swd_wait: int = 100,
        width: int = 0,
    ) -> dict:
        fields = {
            "delay": delay,
            "delay_end": delay_end,
            "power_off": power_off,
            "swd_wait": swd_wait,
            "width": width,
        }
        body = urllib.parse.urlencode(fields).encode("ascii")
        result = self._request("/api/v1/glitch", "POST", body)
        return result if isinstance(result, dict) else {}

    def start_dump(self, kind: Literal["flash", "uicr"]) -> dict:
        if kind not in ("flash", "uicr"):
            raise ValueError(f"unsupported dump kind: {kind}")
        result = self._request(f"/api/v1/dump/{kind}", "POST", b"")
        return result if isinstance(result, dict) else {}

    def wait_for_task(self, timeout: float = 60.0) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self.status()
            if not status.get("task", {}).get("active", False):
                return status
            time.sleep(0.5)
        raise NrfSwdError("operation timed out")

    def download(self, kind: Literal["flash", "uicr"], output: Path) -> None:
        if kind not in ("flash", "uicr"):
            raise ValueError(f"unsupported dump kind: {kind}")
        path = "/download_flash" if kind == "flash" else "/full_uicr.bin"
        data = self._request(path)
        if not isinstance(data, bytes):
            raise NrfSwdError(f"invalid binary response for {kind}")
        validate_dump(kind, data)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        digest = sha256_file(output)
        print(f"{digest}  {output}")

    def restore(self, kind: Literal["flash", "uicr"], input: Path) -> None:
        if kind not in ("flash", "uicr"):
            raise ValueError(f"unsupported restore kind: {kind}")
        data = input.read_bytes()
        validate_dump(kind, data)
        digest = hashlib.sha256(data).hexdigest()
        expected = ORIGINAL_SHA256[kind]
        if digest != expected:
            raise ValueError(
                f"{kind} SHA-256 mismatch: expected {expected}, got {digest}"
            )
        self._request(
            f"/api/v1/restore/{kind}",
            "POST",
            data,
            "application/octet-stream",
        )

    def sha256(self, path: Path) -> str:
        return sha256_file(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="nRF52 SWD ESP32 control CLI")
    parser.add_argument("--host", default="swd.local", help="ESP32 host name or URL")
    parser.add_argument("--timeout", type=float, default=60.0, help="task timeout in seconds")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="show ESP32 status")
    status.add_argument("--host", dest="subhost")
    glitch = subparsers.add_parser("glitch", help="start the glitcher")
    glitch.add_argument("--host", dest="subhost")
    glitch.add_argument(
        "--delay", type=int, default=DEFAULT_DELAY
    )

    dump = subparsers.add_parser("dump", help="dump flash or UICR")
    dump.add_argument("--host", dest="subhost")
    dump.add_argument("--kind", choices=("flash", "uicr"), required=True)
    dump.add_argument("--output", type=Path, required=True)

    restore = subparsers.add_parser("restore", help="restore flash and UICR")
    restore.add_argument("--host", dest="subhost")
    restore.add_argument("--flash", type=Path)
    restore.add_argument("--uicr", type=Path)
    restore.add_argument("--confirm", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    host = getattr(args, "subhost", None) or args.host
    client = NrfSwdClient(host, timeout=max(args.timeout, 0.1))

    try:
        if args.command == "status":
            print(json.dumps(client.status(), sort_keys=True))
        elif args.command == "glitch":
            print(json.dumps(client.glitch(delay=args.delay), sort_keys=True))
        elif args.command == "dump":
            client.start_dump(args.kind)
            client.wait_for_task(args.timeout)
            client.download(args.kind, args.output)
        elif args.command == "restore":
            if not args.confirm:
                raise NrfSwdError("restore requires --confirm")
            if not args.flash or not args.uicr:
                raise NrfSwdError("restore requires --flash and --uicr")
            client.restore("flash", args.flash)
            client.wait_for_task(args.timeout)
            client.restore("uicr", args.uicr)
            client.wait_for_task(args.timeout)
    except (NrfSwdError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
