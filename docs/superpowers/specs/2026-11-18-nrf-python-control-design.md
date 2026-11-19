# nRF52 Python control design

## Intent

Provide a repeatable, scriptable workflow for the ESP32_nRF52_SWD programmer:

- trigger the APPROTECT glitch,
- dump the nRF52 flash and UICR,
- restore both regions from a local binary archive,
- preserve the original browser UI and existing HTTP endpoints.

## Goals

- Add machine-readable JSON endpoints alongside the existing text endpoints.
- Add a Python CLI usable on the host computer.
- Support `status`, `glitch`, `dump`, and `restore` operations.
- Default known-good glitch settings to `Delay 2368`, while allowing explicit override.
- Verify local dump and restore file sizes and SHA-256 hashes.
- Require explicit confirmation for destructive restore and erase operations.

## Non-goals

- Replace or remove the existing web interface.
- Remove or change existing ESP32 flash/glitch routes.
- Implement an on-device GUI.
- Automatically recover from a failed erase or write.

## Constraints

- ESP32-side operations remain HTTP-based and continue to use the existing SWD implementation.
- Flash dumps are 512 KiB in this project; UICR dumps are 4 KiB at offset `0x10001000`.
- Restore operations must write flash at offset `0` and UICR at offset `0x10001000`.
- Wi-Fi credentials and HTTP credentials remain in the ESP32 firmware configuration.
- Binary transfer must use bounded chunk sizes and preserve existing upload behavior.

## Approaches

1. **Serial protocol:** rejected. It would duplicate state and transfer logic already exposed over HTTP.
2. **New HTTP JSON API plus Python CLI:** chosen. It adds a stable automation interface without changing existing routes or UI behavior.

## Design

The ESP32 adds `/api/v1/status`, `/api/v1/glitch`, `/api/v1/dump/{flash,uicr}`, and `/api/v1/restore/{flash,uicr}` routes. Responses use JSON and include operation state, connection state, progress, and errors.

The Python CLI in `tools/nrf52_swd.py` talks to `http://<host>` and provides:

```text
python tools/nrf52_swd.py status --host <ESP32-IP>
python tools/nrf52_swd.py glitch --host <ESP32-IP> --delay 2368
python tools/nrf52_swd.py dump --host <ESP32-IP> --kind full-flash --output dumps/full_flash.bin
python tools/nrf52_swd.py dump --host <ESP32-IP> --kind uicr --output dumps/full_uicr.bin
python tools/nrf52_swd.py restore --host <ESP32-IP> --flash dumps/full_flash.bin --uicr dumps/full_uicr.bin --confirm
```

`glitch` configures the existing glitcher, starts it, and polls status until the existing state machine completes or a configurable timeout expires. `dump` starts the existing SWD read task, polls completion, downloads the file, and reports SHA-256. `restore` validates file length and SHA-256 before upload, uploads through a new JSON progress-oriented workflow or the existing direct upload route, polls completion, and requires `--confirm`.

Original archive constants and the known-unlock delay are documented in the CLI help and README.
