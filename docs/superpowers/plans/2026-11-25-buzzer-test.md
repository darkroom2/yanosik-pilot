# Buzzer Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a simple Zephyr nRF52 project that drives a differential buzzer with hardware PWM on P0.05 and P0.06.

**Architecture:** Follow the existing `firmware/ble-zephyr` PlatformIO layout, adding a dedicated Zephyr project with PWM aliases in the board overlay and an application that alternates 500 ms tones with 1 s pauses.

**Tech Stack:** PlatformIO, Nordic nRF52 platform, Zephyr RTOS, DeviceTree, Zephyr PWM API.

**Spec:** Approved request in the 2026-11-25 conversation; hardware and PWM requirements supplied verbatim in that request.

## Global Constraints

- Target environment: `nrf52_dk`.
- Differential buzzer outputs: physical pin 7 -> P0.05 and physical pin 8 -> P0.06.
- Hardware PWM: PWM0 channel 0 normal polarity and channel 1 inverted polarity.
- Tone: 2 kHz, 50% duty, 500 ms; then 1 s silence.
- Silence: both PWM outputs must have no potential difference.
- Console and UART dependencies must be disabled or moved to RTT.

## Review Focus

- Wrong polarity during tone could reverse the buzzer channels; the overlay and 50% duty cycle pin them to normal/inverted operation.
- Wrong silence values could leave current flowing; the test includes explicit zero-duty and full-duty stop calls.
- UART cannot compile if serial dependencies remain enabled; the configuration task disables UART and console paths consistently.
- PWM device not ready could silently produce no tone; `main.c` must return without starting the loop when either device is unavailable.
- The board overlay must use P0.05/P0.06 rather than P0.17/P0.18; build logs and final documentation pin these exact ports.

---

### Task 1: Scaffold the PlatformIO project

**Files:**
- Create: `firmware/buzzer-test/platformio.ini`
- Create: `firmware/buzzer-test/src/main.c`
- Create: `firmware/buzzer-test/zephyr/prj.conf`
- Create: `firmware/buzzer-test/zephyr/nrf52dk_nrf52832.overlay`

**Interfaces:**
- Consumes: `nrf52_dk` PlatformIO board profile and Zephyr PWM DeviceTree nodes.
- Produces: a buildable `firmware/buzzer-test` project with aliases `buzzer-pwm-a` and `buzzer-pwm-b`.

- [ ] **Step 1: Create `platformio.ini`**

```ini
[env:nrf52_dk]
platform = nordicnrf52
board = nrf52_dk
framework = zephyr
```

- [ ] **Step 2: Create `zephyr/prj.conf`**

Enable PWM and RTT-based console/logging. Disable UART and standard console features.

```ini
CONFIG_PWM=y
CONFIG_SERIAL=n
CONFIG_CONSOLE=n
CONFIG_UART_CONSOLE=n
CONFIG_LOG_BACKEND_UART=n
CONFIG_USE_SEGGER_RTT=y
CONFIG_LOG_BACKEND_RTT=y
CONFIG_RTT_CONSOLE=y
```

- [ ] **Step 3: Create the board overlay**

Map channel 0 to P0.05 with normal polarity and channel 1 to P0.06 with inverted polarity. Add aliases named `buzzer_pwm_a` and `buzzer_pwm_b`. Disable `&uart0`.

- [ ] **Step 4: Create `src/main.c`**

Implement `buzzer_tone(uint32_t freq_hz, uint32_t duration_ms)` and `main()`.

- Obtain the PWM specs with `PWM_DT_SPEC_GET(DT_ALIAS(buzzer_pwm_a))` and `PWM_DT_SPEC_GET(DT_ALIAS(buzzer_pwm_b))`.
- Calculate period and 50% pulse from `freq_hz`.
- Set both channels to the same period and 50% pulse.
- Sleep for `duration_ms`.
- Stop the differential signal with channel A pulse 0 and channel B pulse equal to period.
- In `main()`, return when either PWM device is not ready; otherwise loop at 2 kHz for 500 ms and silence for 1000 ms.

- [ ] **Step 5: Build the project**

Run:

```powershell
uv run pio run --project-dir firmware\buzzer-test -e nrf52_dk
```

Expected: PlatformIO produces `firmware/buzzer-test/.pio/build/nrf52_dk/firmware.hex`.

### Task 2: Document the buzzer project

**Files:**
- Modify: `README.md`
- Modify: `TODO.md`

- [ ] **Step 1: Update identified physical pin mappings**

In the `Zidentyfikowane piny` table, set physical pin 7 to P0.05 and physical pin 8 to P0.06 for the differential buzzer.

- [ ] **Step 2: Remove buzzer identification follow-up**

Update the remaining identification list so it no longer says buzzer pins are unknown. Add a note that P0.05/P0.06 are confirmed, while the boost circuit remains to be identified if applicable.

- [ ] **Step 3: Add the project build and flash section**

Under `Budowanie i wgrywanie projektów firmware`, add `firmware/buzzer-test` with its stable pin map, PWM behavior, build command, ESP32/SWD flash command, reset command, and hardware verification method.

- [ ] **Step 4: Update TODO**

Mark confirmed buzzer pin mapping work complete or replace it with only the remaining boost-circuit verification and hardware-behavior verification.

- [ ] **Step 5: Rebuild documentation state**

Run the project build again and confirm the README flash command references the generated HEX path.

### Task 3: Final verification

**Files:**
- Verify: `firmware/buzzer-test/.pio/build/nrf52_dk/firmware.hex`
- Verify: `README.md`
- Verify: `TODO.md`

- [ ] **Step 1: Inspect the final project diff**

Run:

```powershell
git --no-pager diff --stat
git --no-pager diff -- firmware\buzzer-test README.md TODO.md
```

- [ ] **Step 2: Run the smallest complete build**

```powershell
uv run pio run --project-dir firmware\buzzer-test -e nrf52_dk
```

Expected: exit code 0 and no UART/PWM DeviceTree configuration errors.

- [ ] **Step 3: Record the hardware verification boundary**

Do not mark buzzer behavior as verified until the board has been flashed and reset through ESP32/SWD and a 2 kHz tone plus 1 s silence has been heard physically.
