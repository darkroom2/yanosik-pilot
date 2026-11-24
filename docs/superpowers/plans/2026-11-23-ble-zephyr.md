# BLE Zephyr Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an independent PlatformIO Zephyr project that broadcasts a minimal non-connectable BLE advertisement named `nRF52_PIO`.

**Architecture:** Create `firmware/ble-zephyr` beside the existing Arduino BLE project. PlatformIO owns the `nrf52_dk` build and invokes Zephyr through `zephyr/CMakeLists.txt`; the C entry point enables the native Bluetooth controller and starts BLE advertising.

**Tech Stack:** PlatformIO, Nordic nRF52 platform, Zephyr RTOS, Zephyr Bluetooth API.

**Spec:** Approved request in the conversation between user and assistant on 2026-11-23.

## Global Constraints

- Work in a new `firmware/ble-zephyr` project; do not modify `firmware/ble-test`.
- Use PlatformIO board `nrf52_dk`, platform `nordicnrf52`, and framework `zephyr`.
- Advertise a non-connectable BLE device named `nRF52_PIO`.
- Use the external 32.768 kHz crystal without adding clock overrides.
- Do not flash nRF52 or run direct SWD/register operations during implementation.
- Keep README project instructions grouped under `Budowanie i wgrywanie projektów firmware`.

## Review Focus

- Zephyr source layout: `target_sources(app PRIVATE ../src/main.c)` must resolve from `zephyr/CMakeLists.txt`, verified by a successful nrf52 build.
- BLE enable failure: `bt_enable(NULL)` must return success before advertising starts, verified by source review and compilation.
- Advertisement flags: the payload must omit BR/EDR and use complete device name `nRF52_PIO`, verified by source review.
- Platform selection: build output must come from `[env:nrf52_dk]`, not host test environments, verified with the project build command.
- Physical behavior: final BLE visibility requires ESP32/SWD flashing and a BLE scanner on hardware; HTTP or build success alone is insufficient and remains hardware verification work.

---

### Task 1: Create the Zephyr BLE project

**Files:**
- Create: `firmware/ble-zephyr/platformio.ini`
- Create: `firmware/ble-zephyr/zephyr/prj.conf`
- Create: `firmware/ble-zephyr/zephyr/CMakeLists.txt`
- Create: `firmware/ble-zephyr/src/main.c`

**Interfaces:**
- Consumes: PlatformIO board `nrf52_dk` and Zephyr Bluetooth symbols `bt_enable`, `bt_le_adv_start`, `BT_DATA`, `BT_DATA_BYTES`, `CONFIG_BT_DEVICE_NAME`.
- Produces: a firmware build target named `nrf52_dk` with a non-connectable advertisement for `nRF52_PIO`.

- [ ] **Step 1: Create the PlatformIO environment**

Create `firmware/ble-zephyr/platformio.ini` with:

```ini
[env:nrf52_dk]
platform = nordicnrf52
board = nrf52_dk
framework = zephyr
```

- [ ] **Step 2: Enable Zephyr Bluetooth in Kconfig**

Create `firmware/ble-zephyr/zephyr/prj.conf` with:

```ini
CONFIG_BT=y
CONFIG_BT_BROADCASTER=y
CONFIG_BT_DEVICE_NAME="nRF52_PIO"
```

- [ ] **Step 3: Add the Zephyr CMake entry point**

Create `firmware/ble-zephyr/zephyr/CMakeLists.txt` with the supplied `cmake_minimum_required`, `find_package`, `project`, and `target_sources` declarations.

- [ ] **Step 4: Implement the BLE broadcaster**

Create `firmware/ble-zephyr/src/main.c` with:
- A BLE advertisement packet containing `BT_LE_AD_NO_BREDR` and complete name `CONFIG_BT_DEVICE_NAME`.
- `main()` calling `bt_enable(NULL)`.
- `bt_le_adv_start(BT_LE_ADV_NCONN, ad, ARRAY_SIZE(ad), NULL, 0)` only after Bluetooth initialization succeeds.

- [ ] **Step 5: Build the firmware**

Run from the repository root:

```powershell
uv run pio run --project-dir firmware\ble-zephyr -e nrf52_dk
```

Expected: PlatformIO installs/resolves Zephyr dependencies as needed and produces `.pio/build/nrf52_dk/firmware.hex` without build errors.

### Task 2: Document the project

**Files:**
- Modify: `README.md`
- Modify: `TODO.md` only if hardware verification remains unconfirmed

**Interfaces:**
- Consumes: the built `nrf52_dk` output and the ESP32/SWD flashing workflow already documented in README.
- Produces: project-specific build and hardware verification instructions under `Budowanie i wgrywanie projektów firmware`.

- [ ] **Step 1: Add the project subsection**

Under `### Budowanie i wgrywanie projektów firmware`, add a `#### firmware/ble-zephyr` subsection containing:
- A short confirmation that Zephyr uses the native Bluetooth stack and broadcasts `nRF52_PIO`.
- The board build command:

```powershell
uv run pio run --project-dir firmware\ble-zephyr -e nrf52_dk
```

- A statement that upload is performed through the existing ESP32/SWD API and that reset plus BLE scanner observation are required for hardware confirmation.

- [ ] **Step 2: Keep TODO accurate**

If BLE visibility is not physically verified, retain or add one hardware follow-up in TODO. Do not mark it complete solely on compilation or flash transfer success.
