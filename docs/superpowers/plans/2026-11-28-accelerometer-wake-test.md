# LIS2DH Sleep-to-Wake and FIFO Gesture Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `firmware/accelerometer-wake-test` for LIS2DH/LIS2DH12 Sleep-to-Wake and Stream-to-FIFO gesture capture with nRF52832 SYSTEM OFF.

**Architecture:** `main.c` reads and clears `RESETREAS` first, configures LIS2DH only after a cold/PinReset start, and on System OFF wake drains FIFO data without rewriting the sensor configuration. The project keeps RTT logging, Nordic DCDC/TWIM/GPIO controls, and a minimal Zephyr overlay.

**Tech Stack:** C, Zephyr RTOS, Nordic nRF52 PlatformIO platform, LIS2DH raw I2C registers, SEGGER RTT.

**Spec:** Detailed user request dated 2026-11-28; register values and hardware pins in that request are authoritative.

## Global Constraints

- MCU: nRF52832; set `NRF_POWER->DCDCEN = 1`.
- LIS2DH I2C address: `0x19`; SDA P0.11 and SCL P0.12 with no external pull-ups.
- INT1: P0.03 active high; RGB P0.17/P0.18/P0.19 common-anode active-low; buzzer P0.05/P0.06 low; buttons P0.13/P0.14 input-disconnected.
- Enable `CONFIG_CONSOLE`, SEGGER RTT console/logging and LOG backend RTT in `prj.conf`; add a final-measurement comment requiring them to be disabled and SWD disconnected.
- Cold boot writes CTRL_REG1 `0x57`, CTRL_REG2 `0x09`, CTRL_REG3 `0x40`, CTRL_REG4 `0x80`, CTRL_REG5 `0x40`, FIFO_CTRL_REG `0xC0`, ACT_THS `0x08`, ACT_DUR `0x26`, INT1_THS `0x08`, INT1_DURATION `0x02`, and INT1_CFG `0x2A`.
- Wake reads FIFO_SRC_REG `0x2F`, burst-reads `0x28 | 0x80`, converts signed 10-bit samples, logs samples over RTT, re-arms FIFO through bypass `0x00` then Stream-to-FIFO `0xC0`, and waits for P0.03 low.
- Every System OFF path disconnects TWIM/I2C pins with pull-up, configures P0.03 SENSE HIGH, and sets `NRF_POWER->SYSTEMOFF = 1`.

## Review Focus

- Cold versus wake boot: `RESETREAS` must be read and cleared at main entry, cold starts configure LIS2DH, and `RESETREAS_OFF` starts drain FIFO without reconfiguration.
- Wrong address/device: probe exactly `0x19`; WHO_AM_I `0x33` is mandatory and failure must not enter an assumed LIS2DH sleep state.
- FIFO completeness: FSS must come from `FIFO_SRC_REG 0x2F`, burst count must be bounded to 32 samples, and sample conversion must use signed 10-bit right shift by 6.
- FIFO re-arm: bypass `0x00` must precede Stream-to-FIFO `0xC0`, and P0.03 low wait must use `k_msleep(50)`.
- I2C/SENSE leakage: TWIM0 disable and P0.11/P0.12 disconnect/pull-up must occur before P0.03 SENSE HIGH and SYSTEM OFF.

---

### Task 1: Add failing structural tests

**Files:**
- Modify: `tools/tests/test_accelerometer_wake_test_project.py`

- [ ] **Step 1: Require reset source markers `RESETREAS`, `RESETREAS_OFF`, and first-in-main clearing by writing the captured reset-reason value.**
- [ ] **Step 2: Require fixed-address WHO_AM_I and exact cold-register values `0x57`, `0x09`, `0x40`, `0x80`, `0x40`, `0xC0`, `0x08`, `0x26`, `0x02`, `0x2A`, `0x26`, and `0x31`.**
- [ ] **Step 3: Require FIFO markers `0x2F`, `0x28 | 0x80`, `0x1F`, `>> 6`, `0x00`, `0xC0`, and RTT wait through `k_msleep(50)`.**
- [ ] **Step 4: Require P0.13/P0.14 INPUT_DISCONNECT and RTT/Kconfig symbols in configuration assertions.**
- [ ] **Step 5: Run `uv run pytest tools/tests/test_accelerometer_wake_test_project.py -q`; it must fail until implementation is updated.**

### Task 2: Implement reset dispatch and cold LIS2DH configuration

**Files:**
- Modify: `firmware/accelerometer-wake-test/src/main.c`
- Test: `tools/tests/test_accelerometer_wake_test_project.py`

- [ ] **Step 1: Add register constants for ACT_THS `0x3E`, ACT_DUR `0x3F`, FIFO_SRC `0x2F`, FIFO_CTRL `0x2E`, OUT_X_L `0x28`, REFERENCE `0x26`, and INT1_SRC `0x31`.**
- [ ] **Step 2: At first executable point in `main()`, save `NRF_POWER->RESETREAS`, write the saved value back to clear it, and compute a cold-start or `RESETREAS_OFF` branch.**
- [ ] **Step 3: On cold start only, enable DCDC, verify WHO_AM_I `0x33` at address `0x19`, and write CTRL_REG1 through FIFO and ACT/INT1 register values exactly from the spec.**
- [ ] **Step 4: Read REFERENCE `0x26` and INT1_SRC `0x31`, blink green 10 ms, then enter the shared safe System OFF path.**
- [ ] **Step 5: Run the focused unittest; reset and cold-configuration assertions must pass.**

### Task 3: Implement wake FIFO drain and re-arm

**Files:**
- Modify: `firmware/accelerometer-wake-test/src/main.c`
- Test: `tools/tests/test_accelerometer_wake_test_project.py`

**Interfaces:**
- Consumes: `lis2dh_read_fifo(i2c, address)` on wake.
- Produces: signed X/Y/Z samples in RTT and FIFO rearmed Stream-to-FIFO.

- [ ] **Step 1: In the `RESETREAS_OFF` branch blink blue 5 ms and do not call LIS2DH cold configuration.**
- [ ] **Step 2: Read FIFO_SRC_REG `0x2F`, compute `fss = reg & 0x1F`, and limit count to 32 samples.**
- [ ] **Step 3: Burst-read `fss * 6` bytes starting at `LIS2DH_OUT_X_L | 0x80`, and combine each low/high byte pair into `int16_t`.**
- [ ] **Step 4: Convert all axes with `int16_t raw >> 6` and log several first samples with X/Y/Z values over RTT.**
- [ ] **Step 5: Write FIFO_CTRL_REG `0x00`, then `0xC0`, read INT1_SRC `0x31`, and poll P0.03 low using `k_msleep(50)` before System OFF.**
- [ ] **Step 6: Run the focused unittest; FIFO wake assertions must pass.**

### Task 4: Configure minimal Zephyr settings and safe System OFF

**Files:**
- Modify: `firmware/accelerometer-wake-test/src/main.c`
- Modify: `firmware/accelerometer-wake-test/zephyr/prj.conf`
- Modify: `firmware/accelerometer-wake-test/zephyr/app.overlay`
- Test: `tools/tests/test_accelerometer_wake_test_project.py`

- [ ] **Step 1: Configure P0.05/P0.06 low and P0.13/P0.14 as input-disconnected.**
- [ ] **Step 2: Before every System OFF call, stop TWIM0 and set `NRF_TWIM0->ENABLE = 0`; configure P0.11/P0.12 input-disconnected with `NRF_GPIO_PIN_PULLUP`.**
- [ ] **Step 3: Configure P0.03 SENSE HIGH and set `NRF_POWER->SYSTEMOFF = 1` with a final DSB/wait loop.**
- [ ] **Step 4: Keep only needed I2C/GPIO/RTT settings in `prj.conf` and add the comment that RTT/console settings must be `=n` and SWD disconnected for 3-4 uA measurement.**
- [ ] **Step 5: Keep only required I2C pinctrl and LEDs/int1 nodes in `app.overlay`; remove unused nodes and external pull-up assumptions.**
- [ ] **Step 6: Run the focused unittest; safe-sleep and minimal-config assertions must pass.**

### Task 5: Update documentation and verify

**Files:**
- Modify: `firmware/accelerometer-wake-test/README.md`
- Modify: `README.md`
- Modify: `TODO.md`

- [ ] **Step 1: Document cold/wake RESETREAS behavior, FIFO gesture capture, RTT sample output, build/flash/reset commands, and physical verification caveat.**
- [ ] **Step 2: Document 3-4 uA measurement procedure: RTT/console `=n`, SWD disconnected, reset target, and observe P0.03 wake plus blue-green indicators.**
- [ ] **Step 3: Run `uv run pytest tools/tests/test_accelerometer_wake_test_project.py -q`.**
- [ ] **Step 4: Run `uv run pytest`.**
- [ ] **Step 5: Run `uv run pio run --project-dir firmware/accelerometer-wake-test -e nrf52_dk`; pass means compilation/linking only.**
- [ ] **Step 6: Leave physical wake/current measurement open in `TODO.md` until observed on hardware.**
