# Blinker firmware design

## Intent

Provide a minimal interactive firmware sketch for experimenting with the RGB LED and two buttons on the nRF52832-based pilot board.

## Goals and behavior

- Blink one selected RGB color continuously.
- Button 1 (P0.13) advances through red, green, and blue.
- Button 2 (P0.14) pauses or resumes blinking.
- Debounce button input and keep the loop non-blocking so both buttons remain responsive.

## Non-goals

- BLE, buzzer, accelerometer, configurable timing, or additional modes.
- Changing the existing PlatformIO board or framework configuration.

## Constraints

- Use the existing PlatformIO Arduino environment (`nrf52_dk`).
- Buttons are active-low with `INPUT_PULLUP`.
- RGB LED channels are active-low: red P0.17, green P0.18, blue P0.19.
- For the `nRF52DK` Arduino variant, address P0.13/P0.14/P0.17/P0.18/P0.19 as digital pins D2/D3/D6/D7/D8.
- Keep the test harness within PlatformIO and Unity; add no external dependencies.

## Approaches

1. Automatically cycle RGB colors while buttons adjust blink speed. This shows every color without interaction, but makes button testing less direct.
2. Blink one selected color; button 1 changes color and button 2 pauses/resumes. This was selected because each button has one obvious, testable action and the program stays small.
3. Use Unity tests built for a host platform or execute them on the nRF52 target. Host tests exercise the same C++ logic without the ESP32/SWD upload and serial-output bridge that an on-target test run would require, so host execution is selected.

## Implementation

Put the Arduino-independent state machine in `firmware/blinker/lib/blinker_logic/` so both the sketch and tests use the same code. Add the sketch in `firmware/blinker/src/main.cpp`, and test the state machine with PlatformIO Unity tests in `firmware/blinker/test/`. Use `millis()` for blinking and simple per-button debounce. Document the build and test commands in the root README.

## Test harness

Use PlatformIO's Unity test runner on host platforms: `windows_x86` on Windows and `linux_x86_64` on Linux. Tests cover color cycling, one action per debounced press, blinking, and pause/resume in the same Arduino-independent C++ state machine used by firmware. These tests run without a board; GPIO polarity and the physical pin mapping still need hardware verification through the existing ESP32/SWD workflow.
