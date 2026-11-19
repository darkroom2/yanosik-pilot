# nRF52 Python Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add machine-readable ESP32 HTTP control and a Python CLI for glitching, dumps, and factory restoration without replacing existing browser functionality.

**Architecture:** Keep the existing Arduino/SPIFFS implementation as the backend and add thin `/api/v1` routes plus a host-side stdlib-only Python CLI. Binary dumps and restores use existing SWD primitives; the Python CLI validates size and SHA-256 and polls ESP32 state.

**Tech Stack:** C++/Arduino, ESPAsyncWebServer, Python 3.14 stdlib, PlatformIO

**Spec:** `docs/superpowers/specs/2026-11-18-nrf-python-control-design.md`

## Global Constraints

- Preserve every existing web route, glitcher route, SWD command, and browser UI behavior.
- Use the known APPROTECT glitch delay `2368` as the CLI default.
- Restore flash from offset `0` and UICR from offset `0x10001000`.
- Require `--confirm` for restore.
- No third-party Python package may be added for this CLI.

## Review Focus

- Invalid or missing HTTP parameters must return HTTP 400 and JSON `{"ok":false,"error":"..."}`.
- A glitch timeout must leave the existing glitcher disabled and report failure without claiming success.
- Dump size mismatches must fail before an output file is accepted; tests in Task 2 must pin 512 KiB/4 KiB validation.
- Restore must reject wrong-size or wrong-checksum input in the Python CLI before sending bytes; tests in Task 2 cover both.
- Existing web routes must remain registered and unchanged; verify by compiling the project after Task 1.

---

### Task 1: Add ESP32 machine API

**Files:**
- Modify: `ESP32_nRF52_SWD/src/web.cpp`
- Modify: `ESP32_nRF52_SWD/src/glitcher.h`
- Modify: `ESP32_nRF52_SWD/src/glitcher.cpp`

**Interfaces:**
- Consumes: `set_glitcher`, `set_delay`, `set_width`, `set_read_flash`, `nrf_ufcr`, `nrf_write_bank`.
- Produces:
  - `GET /api/v1/status`
  - `POST /api/v1/glitch`
  - `POST /api/v1/dump/flash`
  - `POST /api/v1/dump/uicr`
  - `POST /api/v1/restore/flash`
  - `POST /api/v1/restore/uicr`

- [ ] **Step 1: Add JSON parameter and state helpers**

In `web.cpp`, add static helpers that return JSON from C++:

```cpp
void send_api_json(AsyncWebServerRequest *request, int status_code, bool ok, const char *error = nullptr);
String api_hex(uint32_t value);
```

Keep the existing `server.on(...)` registrations below these helpers.

- [ ] **Step 2: Register the status route**

Add `GET /api/v1/status` returning:

```json
{
  "ok": true,
  "state": "idle",
  "connected": 0,
  "flash_size": 0,
  "uicr_size": 4096,
  "glitch": {"running": false, "delay": 2368, "delay_end": 2368, "width": 0},
  "task": {"active": false, "percent": 0, "speed_kbps": 0.0}
}
```

Use `get_glitcher()`, `is_nrf_connected()`, `get_task_flash()`, `get_last_speed()`, `get_delay()`, `get_width()`, and `nrf_ufcr.flash_size`.

- [ ] **Step 3: Register the glitch route**

Add `POST /api/v1/glitch` accepting form parameters `delay`, `delay_end`, `power_off`, `swd_wait`, and `width`; every parameter is optional except the route may default:

- `delay = 2368`
- `delay_end = 2368`
- `power_off = 50`
- `swd_wait = 100`
- `width = 0`

Reject negative values and values outside Arduino `uint32_t` range with HTTP 400. On success call `set_delay(...)`, `set_width(...)`, then `set_glitcher(true)`, and return HTTP 202 with JSON `{"ok":true,"started":true}`.

- [ ] **Step 4: Register dump routes**

Add `POST /api/v1/dump/flash` and `POST /api/v1/dump/uicr`. The flash route requires the target to be unlocked and calls `set_read_flash(0, nrf_ufcr.flash_size, "/full_flash.bin")`. The UICR route calls `set_read_flash(0x10001000, 0x1000, "/full_uicr.bin")`. Return HTTP 202 with JSON `{"ok":true,"started":true,"filename":"full_flash.bin","size":...}`.

Reject a running glitcher or active flash task with HTTP 409 and JSON `{"ok":false,"error":"..."}`.

- [ ] **Step 5: Register raw binary restore routes**

Add `POST /api/v1/restore/flash` and `POST /api/v1/restore/uicr` upload handlers. Reject when locked, disconnected, or glitching. The flash upload writes chunks into flash starting at `0`; UICR writes starting at `0x10001000`. Return HTTP 202 at the start and track progress/last error for `/api/v1/status`; do not pad or truncate uploads.

- [ ] **Step 6: Preserve existing routes and build**

Do not edit or remove existing `/set_glitcher`, `/set_delay`, `/set_swd`, `/flash_cmd`, `/download_flash`, `/flash_file_direct`, or browser static routes.

Run:

```bash
cd ESP32_nRF52_SWD
pio run -e ESP32_nRF52_SWD
```

Expected: exit 0 and `.pio/build/ESP32_nRF52_SWD/firmware.bin` is regenerated.

### Task 2: Add Python CLI and tests

**Files:**
- Create: `tools/nrf52_swd.py`
- Create: `tests/test_nrf52_swd.py`
- Modify: `pyproject.toml`
- Modify: `ESP32_nRF52_SWD/README.md`

**Interfaces:**
- Produces:
  - `NrfSwdClient.status() -> dict`
  - `NrfSwdClient.glitch(delay=2368, delay_end=2368, power_off=50, swd_wait=100, width=0) -> dict`
  - `NrfSwdClient.start_dump(kind: Literal["flash","uicr"]) -> dict`
  - `NrfSwdClient.download(kind, output: Path) -> None`
  - `NrfSwdClient.restore(kind, input: Path) -> None`
- CLI subcommands: `status`, `glitch`, `dump`, `restore`.

- [ ] **Step 1: Write failing CLI unit tests**

Create `tests/test_nrf52_swd.py` and test:

1. `validate_dump("flash", bytes of 512 KiB)` succeeds and `bytes of 512 KiB - 1` raises `ValueError`.
2. `validate_dump("uicr", bytes of 4 KiB)` succeeds and `bytes of 4 KiB - 1` raises `ValueError`.
3. `restore` rejects a wrong-size flash file before opening an HTTP connection.
4. `restore` rejects a wrong-size UICR file before opening an HTTP connection.
5. `glitch` sends `2368` for every glitch delay field when no delay override is supplied.
6. `dump` writes downloaded bytes to the requested path and verifies its SHA-256.
7. HTTP 400/409/timeout responses raise `NrfSwdError` with server text preserved.

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest tests/test_nrf52_swd.py -q
```

Expected: pytest reports `NrfSwdClient`, `validate_dump`, or module import missing.

- [ ] **Step 3: Implement minimal stdlib CLI**

Create `tools/nrf52_swd.py`. Use `urllib.request` and `urllib.parse`, with no third-party HTTP dependency. Expose:

```text
python tools/nrf52_swd.py --host swd.local status
python tools/nrf52_swd.py --host swd.local glitch [--delay 2368]
python tools/nrf52_swd.py --host swd.local dump --kind flash --output dumps/full_flash.bin
python tools/nrf52_swd.py --host swd.local dump --kind uicr --output dumps/full_uicr.bin
python tools/nrf52_swd.py --host swd.local restore --flash dumps/full_flash.bin --uicr dumps/full_uicr.bin --confirm
```

Implement size constants and SHA-256 output. Poll `GET /api/v1/status` at 500 ms until dump/restore completion or the configured timeout.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
uv run pytest tests/test_nrf52_swd.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Install pytest only if needed**

If pytest is unavailable in the configured environment, use `uv add --dev pytest` only after the RED run proves the test dependency is missing.

### Task 3: Document and verify the user workflow

**Files:**
- Modify: `ESP32_nRF52_SWD/README.md`
- Modify: `IDEA.md`

- [ ] **Step 1: Add CLI documentation**

Document host configuration, original archive paths, `2368` unlock delay, dump commands, restore command, and `--confirm` safety requirement.

- [ ] **Step 2: Run the full verification**

Run:

```bash
cd ESP32_nRF52_SWD
pio run -e ESP32_nRF52_SWD
cd ..
uv run pytest -q
sha256sum -c <(printf '8cf25c59ad391780435765317039d2256cc618ff036a3c0847033c8d593e13dd  dumps/full_uicr.bin\nec3060bb5d8160296f1891a2d4d2db7882535f80779dd6fe611bf300a475d826  dumps/full_flash.bin\n')
python tools/nrf52_swd.py --help
```

Expected: ESP32 firmware builds, pytest passes, both archive hashes match, and CLI help lists all four subcommands.

- [ ] **Step 3: Commit the implementation**

Create a git commit only if the repository status and diff show no unrelated changes, with a Co-authored-by trailer.
