I have a remote control and want to modify it so I can use it to control devices in my Home Assistant. It is essential to preserve the original firmware from this remote to revert it to its factory state!!!

• Remote hardware: nRF52832 chip (QFN48) with an external 32.000 MHz crystal and RF components (all functional and necessary).
• Pin mapping (physical pin → GPIO port):
    • Button #1: Pin 16 → P0.13 (short to GND, requires INPUT_PULLUP).
    • Button #2: Pin 17 → P0.14 (short to GND, requires INPUT_PULLUP).
	• Red LED (510 Ω): Pin 20 → P0.17 (common anode, lights up at LOW).
    • Blue/Green LED (100 Ω): Pin 21 → P0.18 and Pin 22 → P0.19 (common anode, lights up at LOW).
• Programmer: You have an ESP32 NodeMCU and N-Channel MOSFET, which you can turn into a programmer by uploading the ESP32_nRF52_SWD project at https://github.com/atc1441/ESP32_nRF52_SWD

ESP32_nRF52_SWD README.md excerpt:
```
This software makes it possible to Read and Write the internal Flash of the Nordic nRF52 series with an ESP32 using the SWD interface. A tool to exploit the APPROTECT vulnerability is included as well.

To flash an nRF52 connect the following:
nRF52 SWDCLK to ESP32 GPIO 21
nRF52 SWDIO to ESP32 GPIO 19
nRF52 GND to ESP32 GND to N-Channel MOSFET GND (Optional: O-scope GND Clips)
Then power the nRF52 as needed

To bypass the Readout protection (APPROTECT) of an nRF52 connect all of the above and the following:
nRF52 3.3V Power VDD to ESP32 GPIO 22 (Optional: O-scope Channel 2 Probe)
N-Channel MOSFET PWM+ to ESP32 GPIO 5 (as shown)
N-Channel MOSFET VOUT- to nRF52 DEC1 (as shown) (Optional: O-scope Channel 1 Probe)
Then power the nRF52 as needed
```

• Development Environment: Visual Studio Code + PlatformIO CLI for compiling software for the remote control and the programmer.

1. Upload the ESP32_nRF52_SWD project to the ESP32
2. Distinguish between the colors on pins 21 and 22:
   - Keep `dumps/full_flash.bin` (512 KiB) and `dumps/full_uicr.bin` (4 KiB)
     available. The LED script verifies their known SHA-256 values before any
     erase or upload.
   - Build and flash the temporary fixture only with explicit confirmation:
     `python tools/led_identify.py run --host swd.local --confirm`
   - Observe P0.18 and P0.19 separately. Do not assign a color in source code
     until one complete sequence has been repeated and both channels are
     visibly distinct. Record the result with `--output mapping.json`.
   - Restore the original archive only with explicit confirmation:
     `python tools/led_identify.py restore --host swd.local --confirm`
3. Selecting the remote control’s operating logic: Determine which events the buttons should send to Home Assistant via the BTHome protocol (e.g., single click, double click, long press) and how the LEDs should indicate these events.
4. Back-up the original firmware
5. Compiling and flashing the batch: Preparing the code for PlatformIO, generating a .bin/.hex file, disabling the memory lock (APPROTECT) using the ESP32, and flashing the program to the nRF52832.

## Original firmware archive

Complete reads captured by the ESP32/nRF52 SWD setup:

* [`dumps/full_uicr.bin`](dumps/full_uicr.bin) - UICR backup (4 KiB, SHA-256 `8cf25c59ad391780435765317039d2256cc618ff036a3c0847033c8d593e13dd`)
* [`dumps/full_flash.bin`](dumps/full_flash.bin) - full internal flash backup (512 KiB, SHA-256 `ec3060bb5d8160296f1891a2d4d2db7882535f80779dd6fe611bf300a475d826`)

APPROTECT unlock timing parameter: `Delay 2368`.

## Python control workflow

The ESP32 exposes machine-readable API routes for status, glitching, dumping, and restoring. Use the stdlib-only CLI on the host computer:

```bash
python tools/nrf52_swd.py --host swd.local status
python tools/nrf52_swd.py --host swd.local glitch --delay 2368
python tools/nrf52_swd.py --host swd.local dump --kind flash --output dumps/full_flash.bin
python tools/nrf52_swd.py --host swd.local dump --kind uicr --output dumps/full_uicr.bin
python tools/nrf52_swd.py --host swd.local restore --flash dumps/full_flash.bin --uicr dumps/full_uicr.bin --confirm
```

The restore command is destructive and therefore requires `--confirm`. It rejects wrong flash/UICR sizes and mismatched archive SHA-256 values before opening an HTTP connection.