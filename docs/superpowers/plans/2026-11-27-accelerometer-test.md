# Accelerometer Test Zephyr Project Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `firmware/accelerometer-test` as a Zephyr/PlatformIO application for the nRF52832 pilot that reads LIS2DH12 over SPI1 and maps X/Y/Z tilt to RGB LED channels.

**Architecture:** Copy the existing Zephyr template, then replace only project identity and hardware-facing configuration. DeviceTree owns LED, SPI1, pinctrl, LIS2DH12, IRQ, and aliases; Kconfig enables required GPIO/SPI/sensor drivers; `src/main.c` performs readiness checks, ODR setup, 50 ms sampling, and RGB threshold control.

**Tech Stack:** Zephyr RTOS, Nordic nRF52 PlatformIO platform, nRF52832 nRF52 DK board profile, LIS2DH12 sensor driver, Python unittest/pytest for project structure verification.

**Spec:** User request dated 2026-11-27: QFN48/LGA-12 pinout, `firmware/zephyr-template` source, `firmware/accelerometer-test` destination, Zephyr PlatformIO build, ESP32/SWD flashing, and complete documentation.

## Global Constraints

- The project must build with `pio run` using framework `zephyr`, board `nrf52_dk`, and PlatformIO CLI.
- `zephyr/app.overlay` must define `gpio-leds` for P0.17/P0.18/P0.19, SPI1 on P0.13/P0.07/P0.08, CS P0.12, LIS2DH12 IRQ P0.03, and `accel0` alias.
- `zephyr/prj.conf` must enable GPIO, SPI, SENSOR, LIS2DH, and LIS2DH trigger-none.
- `src/main.c` must set LIS2DH12 ODR to 50 Hz, read `SENSOR_CHAN_ACCEL_XYZ` every 50 ms, and use `|axis| > 5.0` for RGB mapping.
- NFC pins P0.09/P0.10 and future button pins P0.14/P0.15 must remain out of active GPIO configuration.
- Documentation must include the QFN48 and LGA-12 pin maps, electrical parameters, SWD build/flash workflow, RGB behavior, and future wake lines.

## Review Focus

- Missing sensor or LED readiness must trigger a visible red fast-blink error path, tested by inspecting the exact readiness checks and blink loop.
- Wrong SPI pin/CS/IRQ configuration must fail project structure tests before build, pinned to exact DeviceTree properties and PSEL values.
- ODR or 50 ms timing drift must remain explicit, pinned to `SENSOR_ATTR_SAMPLING_FREQUENCY`, 50 Hz, and `K_MSEC(50)`.
- Active-low RGB logic must be preserved, pinned to `GPIO_ACTIVE_LOW`, GPIO output configuration, and per-axis threshold behavior.
- Documentation omissions must fail README/docs tests, pinned to complete pinout, flash commands, and wake-up future-use notes.

---

### Task 1: Add project tests first

**Files:**
- Create: `tools/tests/test_accelerometer_test_project.py`

- [ ] **Step 1: Write project structure tests**

Create a unittest test class that resolves the repository root and `firmware/accelerometer-test`. Assert the overlay contains exact P0 LED pins, aliases, SPI1 pinctrl, CS, LIS2DH12 node compatibility/max frequency/IRQ/alias, prj.conf feature flags, main.c readiness checks and exact 50 Hz/50 ms/5.0 behavior, and README/docs hardware documentation markers.

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `uv run pytest tools/tests/test_accelerometer_test_project.py`
Expected: FAIL because `firmware/accelerometer-test` or required content does not exist.

### Task 2: Copy template and add hardware configuration

**Files:**
- Create: `firmware/accelerometer-test/platformio.ini`
- Create: `firmware/accelerometer-test/post_build_bin.py`
- Create: `firmware/accelerometer-test/zephyr/CMakeLists.txt`
- Create: `firmware/accelerometer-test/zephyr/prj.conf`
- Create: `firmware/accelerometer-test/zephyr/app.overlay`
- Create: `firmware/accelerometer-test/src/main.c`

- [ ] **Step 1: Copy template files without build or git metadata**

Copy `platformio.ini`, `post_build_bin.py`, `src/main.c`, `zephyr/CMakeLists.txt`, and `zephyr/prj.conf` as the starting project, excluding `.pio` and `.git`.

- [ ] **Step 2: Update CMake project identity**

Set `project(accelerometer_test)` while retaining `target_sources(app PRIVATE ../src/main.c)`.

- [ ] **Step 3: Implement required Kconfig**

Keep RTT diagnostics from the template, and add `CONFIG_GPIO=y`, `CONFIG_SPI=y`, `CONFIG_SENSOR=y`, `CONFIG_LIS2DH=y`, `CONFIG_LIS2DH_TRIGGER_NONE=y`.

- [ ] **Step 4: Add DeviceTree hardware nodes**

Create `/aliases` entries `led-red`, `led-green`, `led-blue`, and `accel0`; create `gpio-leds` entries with P0.17/P0.18/P0.19 and `GPIO_ACTIVE_LOW`; configure `&spi1` and `&pinctrl` with P0.13 SCK, P0.07 MOSI, P0.08 MISO, P0.12 CS, and LIS2DH12 IRQ P0.03.

- [ ] **Step 5: Implement the application**

Verify the sensor and each LED spec with `device_is_ready`/`gpio_is_ready_dt`. Fast-blink the red LED on initialization failure. Set LIS2DH12 sampling frequency to 50 Hz. Every 50 ms, read one three-axis sensor value and independently set each LED according to whether `fabs`-style absolute X/Y/Z value exceeds 5.0 m/s^2.

- [ ] **Step 6: Run the focused test and verify it passes**

Run: `uv run pytest tools/tests/test_accelerometer_test_project.py`
Expected: PASS for project structure and source configuration assertions.

### Task 3: Document hardware and workflows

**Files:**
- Create: `firmware/accelerometer-test/README.md`
- Create: `firmware/accelerometer-test/docs/hardware.md`
- Modify: root `README.md`

- [ ] **Step 1: Create hardware documentation**

Document nRF52832 QFN48, LIS2DH12 LGA-12, RGB LED, buttons, NFC reservations, ESP32 SWD, and every specified P0 mapping. Include roles, power levels, resistor values, active-low behavior, and future INT1/P0.14/P0.15 wake-use notes.

- [ ] **Step 2: Add project README**

Describe application behavior and include `pio run`, BIN output, `pio run -t upload`, and ESP32/SWD reset/flash commands.

- [ ] **Step 3: Link project documentation from root README**

Add `firmware/accelerometer-test` under the firmware build section and link its hardware document.

- [ ] **Step 4: Run documentation assertions**

Run: `uv run pytest tools/tests/test_accelerometer_test_project.py`
Expected: PASS for README and hardware document content.

### Task 4: Build and verify

**Files:**
- Modify: no production files unless build reveals required corrections

- [ ] **Step 1: Run the project build**

Run: `uv run pio run --project-dir firmware\accelerometer-test -e nrf52_dk`
Expected: Build completes without errors and warnings.

- [ ] **Step 2: Run focused repository tests**

Run: `uv run pytest tools/tests/test_accelerometer_test_project.py`
Expected: PASS.

- [ ] **Step 3: Run the full Python suite**

Run: `uv run pytest`
Expected: Existing and new tests pass.
