# LED Identification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a temporary PlatformIO LED smoke-test firmware and a host runner that safely identifies P0.18/P0.19 color mapping and restores the original archive.

**Architecture:** Keep the LED fixture isolated in `led_smoke_test/`; extend the existing stdlib-only `NrfSwdClient` with erase and HEX upload operations, and keep interactive prompts/output in `tools/led_identify.py`. Tests cover backup validation, exact prompts, destructive confirmation, and HTTP upload behavior.

**Tech Stack:** Python 3.14, pytest, PlatformIO Nordic nRF52, Arduino nRF52 framework, ESP32 HTTP API.

**Spec:** [LED Identification Smoke Test Design](../specs/2026-11-18-led-identification-design.md) and [Yanosik BTHome Remote Design](../specs/2026-11-14-yanosik-remote-design.md).

## Global Constraints

- P0.17, P0.18 and P0.19 are active-low outputs.
- `dumps/full_flash.bin` is 512 KiB and must hash to `ec3060bb5d8160296f1891a2d4d2db7882535f80779dd6fe611bf300a475d826`.
- `dumps/full_uicr.bin` is 4 KiB and must hash to `8cf25c59ad391780435765317039d2256cc618ff036a3c0847033c8d593e13dd`.
- Default the unlock delay to `2368`.
- Never erase or flash unless the original backups pass size and hash validation and the operator supplies explicit confirmation.
- Never claim a restore succeeded until `/api/v1/status` reports the restore task inactive and no `last_error` remains.
- Do not commit firmware dumps or credentials.

## Review Focus

1. Backup corruption must stop before erase: test wrong size and wrong SHA-256 for both dumps.
2. Missing confirmation must stop before every destructive HTTP operation: test missing erase and missing restore confirmation separately.
3. Upload failure or a restore error must not be reported as success: test HTTP 409 and `last_error` propagation.
4. Operator input must not assign conflicting colors: test `blue`/`green`/`unknown` acceptance and duplicate-color rejection.
5. Restore interruption must remain explicit: test that a `NrfSwdError` during flash or UICR restore includes the region and does not claim success.

---

### Task 1: Temporary LED smoke-test firmware

**Files:**
- Create: `led_smoke_test/platformio.ini`
- Create: `led_smoke_test/src/main.cpp`

**Interfaces:**
- Produces a PlatformIO environment named `led-smoke-test`.
- Produces `led_smoke_test/.pio/build/led-smoke-test/firmware.hex`.
- GPIO behavior: P0.17/P0.18/P0.19 initialize high; P0.18 then P0.19 illuminate separately for 1000 ms with 300 ms off between channels.

- [ ] **Step 1: Add the PlatformIO target**

Create `led_smoke_test/platformio.ini` with `platform=nordicnrf52`, `board=nrf52_dk`, `framework=arduino`, `build_unflags=-std=gnu++11`, and `board_build.mcu=nrf52832`.

- [ ] **Step 2: Add the LED sequence**

Create `led_smoke_test/src/main.cpp`. Use `pinMode(17, OUTPUT)`, `pinMode(18, OUTPUT)`, and `pinMode(19, OUTPUT)`, initialize all three high, wait 500 ms, then pulse P0.18 and P0.19 for 1000 ms with 300 ms low-to-off gaps. Leave P0.17 high throughout.

- [ ] **Step 3: Build the fixture**

Run `pio run -d led_smoke_test -e led-smoke-test`.
Expected: successful firmware build with `firmware.hex` in `.pio/build/led-smoke-test/`.

### Task 2: Add erase and HEX upload to the SWD client

**Files:**
- Modify: `tools/nrf52_swd.py`
- Test: `tests/test_nrf52_swd.py`

**Interfaces:**
- Produces `NrfSwdClient.erase_flash(confirm: bool) -> dict`.
- Produces `NrfSwdClient.upload_hex(hex_file: Path) -> dict`.
- Both operations reject preconditions before sending HTTP; `erase_flash` requires `confirm=True`; `upload_hex` requires the target to be unlocked and the file to exist and end in `.hex`.

- [ ] **Step 1: Write failing erase tests**

Add tests asserting `erase_flash(False)` raises `NrfSwdError` and sends no HTTP request, and `erase_flash(True)` posts to `/flash_cmd` with `cmd=erase_all`.

- [ ] **Step 2: Write failing upload tests**

Add tests asserting a missing `.hex` path and a non-`.hex` path raise `ValueError` before HTTP, and a valid `.hex` upload posts multipart form data containing `filename="firmware.hex"` and `flash_up_file_offset=0` only if the response is expected.

- [ ] **Step 3: Implement the client operations**

Implement `erase_flash(confirm)` and `upload_hex(hex_file)` in `NrfSwdClient`. Use existing `_request` or a bounded standard-library multipart request. Upload with `filename=firmware.hex`, content type `application/octet-stream`, and no offset for HEX files.

- [ ] **Step 4: Run focused tests**

Run `pytest tests/test_nrf52_swd.py -q`.
Expected: all existing and new SWD client tests pass.

### Task 3: LED identification runner

**Files:**
- Create: `tools/led_identify.py`
- Test: `tests/test_led_identify.py`

**Interfaces:**
- Consumes `NrfSwdClient` and backup constants from `tools/nrf52_swd.py`.
- Produces `validate_backups(flash: Path, uicr: Path) -> None`.
- Produces `record_mapping(answer18: str, answer19: str) -> dict[str, str]`.
- Produces CLI subcommands `run` and `restore`.

- [ ] **Step 1: Write backup and mapping tests**

Test exact known-size/hash acceptance, wrong size/hash rejection, and mapping rejection for duplicate or invalid colors. Test unknown is accepted only for pins whose human observation is unknown.

- [ ] **Step 2: Write CLI flow tests**

Mock `NrfSwdClient` and PlatformIO subprocess execution. Assert `run --confirm` validates backups before glitch/build/erase/upload; missing `--confirm` performs no client or subprocess action; `restore --confirm` restores flash then UICR and waits after each upload.

- [ ] **Step 3: Implement backup validation and mapping recording**

Implement `validate_backups` using exact size and SHA-256 constants. Implement `record_mapping` with allowed values `blue`, `green`, `unknown`, rejecting duplicate known colors.

- [ ] **Step 4: Implement the `run` subcommand**

Parse `--host`, `--timeout`, `--delay` default `2368`, `--confirm`, `--restore-confirm`, and `--output` optional JSON. Validate backups, call `glitch(delay=args.delay)`, run `pio run -d led_smoke_test -e led-smoke-test`, call `erase_flash(confirm=True)`, call `upload_hex(...)`, then prompt for P0.18 and P0.19 mapping. If `--restore-confirm` is present, restore flash and UICR after prompting; otherwise leave restoration to the separate `restore` subcommand.

- [ ] **Step 5: Implement the `restore` subcommand**

Parse `--host`, `--timeout`, `--confirm`, `--flash`, `--uicr`. Require `--confirm`, validate both backups again, then call `client.restore("flash", flash)`, `wait_for_task(timeout)`, `client.restore("uicr", uicr)`, and `wait_for_task(timeout)`. Print success only after both complete without `last_error`.

- [ ] **Step 6: Run focused and full host tests**

Run `pytest tests/test_led_identify.py tests/test_nrf52_swd.py -q`.
Expected: LED and SWD tests pass.

### Task 4: Operator documentation and final validation

**Files:**
- Modify: `IDEA.md`
- Create: `docs/led-identification.md` if operator detail is not already maintained in `IDEA.md`

**Interfaces:** Document exact commands and safety requirements for hardware execution.

- [ ] **Step 1: Document the LED workflow**

In `IDEA.md`, replace the speculative smoke-test step with commands for build/run and restore. Explicitly say P0.18/P0.19 are not assigned until observed. State that the script requires a verified 512 KiB flash and 4 KiB UICR backup.

- [ ] **Step 2: Document manual acceptance**

Record P0.18 and P0.19 separately, repeat the sequence once, and mark one pin blue and the other green only after observing distinct colors. Add a stop condition: if restore reports an error or leaves `last_error`, do not claim recovery and retain the backup files.

- [ ] **Step 3: Run final verification**

Run `pytest -q` and `pio run -d led_smoke_test -e led-smoke-test`.
Expected: all host tests pass and the temporary fixture builds. Do not invoke any upload or erase target.
