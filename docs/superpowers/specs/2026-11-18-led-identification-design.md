# LED Identification Smoke Test Design

## Intent

Identify which nRF52832 GPIO, P0.18 or P0.19, drives the blue and green
LED channels on the Yanosik remote. The board is assumed to be unlocked, and
the original flash and UICR backups already exist in `dumps/`.

## Goals

- Provide a reproducible temporary LED smoke-test firmware.
- Sequence P0.18 and P0.19 separately, with P0.17 available as a red control.
- Require an exact-size, known-hash backup before any destructive operation.
- Add a host script that builds, flashes, observes, and restores safely.
- Record the observed GPIO-to-color mapping in a local operator output.

## Non-goals

- Change or flash the final BTHome firmware.
- Guess or encode the blue/green mapping before hardware observation.
- Commit firmware dumps or observed backup secrets.

## Constraints

- P0.17, P0.18, and P0.19 are active-low outputs.
- `dumps/full_flash.bin` must be 512 KiB with SHA-256
  `ec3060bb5d8160296f1891a2d4d2db7882535f80779dd6fe611bf300a475d826`.
- `dumps/full_uicr.bin` must be 4 KiB with SHA-256
  `8cf25c59ad391780435765317039d2256cc618ff036a3c0847033c8d593e13dd`.
- The ESP32 is addressed through `--host`; Wi-Fi credentials remain local.
- No erase or flash operation occurs without `--confirm`.

## Approaches

1. **PlatformIO firmware plus host runner:** chosen. It produces a known Intel
   HEX image, while the existing ESP32 project provides erase, direct upload,
   and original archive restore operations.
2. Host-only register writes: rejected because it would require a working
   unflashed board to expose SWD and would leave less evidence of the sequence.
3. Camera-assisted classification: rejected because camera color and lighting
   vary and human observation is the reliable source for this unknown mapping.

## Design

Create `led_smoke_test/platformio.ini` and `led_smoke_test/src/main.cpp`.
The firmware initializes P0.17, P0.18, and P0.19 high (off), waits 500 ms,
then repeats P0.18 and P0.19 in separate 1000 ms on/300 ms off phases. The
red P0.17 LED is not used to infer blue/green and is omitted from the sequence.

Create `tools/led_identify.py` as a stdlib CLI with `run` and `restore`
subcommands. `run` validates the original backups and their hashes, optionally
glitches the target at delay `2368`, builds the smoke-test HEX with PlatformIO,
requires `--confirm`, erases all flash through the ESP32 `/flash_cmd` route,
uploads the HEX through `/flash_file_direct`, and pauses for the operator.

The script prints one explicit prompt at a time:

- Is P0.18 blue or green?
- Is P0.19 blue or green?

Accepted responses are `blue`, `green`, or `unknown`. It rejects inconsistent
answers where both pins are assigned the same color. It writes the result to
stdout and optionally `--output` JSON, never to firmware or the original
archive.

After the session, either run the script's separate `restore` subcommand or
pass `--restore-confirm` to `run`; both actions restore flash and UICR using
the existing `NrfSwdClient.restore()` methods. If restore begins and fails,
it prints the exact failure and does not claim the original firmware was
recovered.
