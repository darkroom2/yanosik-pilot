# Hardware Architecture: nRF52832 LIS2DH12 Pilot

## Overview

The pilot uses a Nordic nRF52832 in a QFN48 package. The application target is
ST LIS2DH12 in an LGA-12 package, connected through the 4-wire SPI interface,
and an RGB LED with a common anode. The ESP32_nRF52_SWD programmer provides
SWD flashing and target reset.

> The final configuration uses Zephyr SPI1 in 4-wire Mode 3 and the LIS2DH12
> sensor driver. The diagnostic GPIO pin scanner is no longer part of the application.

## nRF52832 QFN48

The MCU supply is 3.3 V. Pins P0.09 and P0.10 are NFC1/NFC2 on pins 12 and 13
and are routed through capacitors to GND. They must not be used as ordinary
GPIO unless NFC is disabled in UICR. P0.14 and P0.15 are reserved future
physical button inputs.

| MCU physical pin | Port | Device pin / function | Direction | Zephyr / electrical parameter |
|---|---|---|---|---|
| 7 | P0.05 | LIS2DH12 CS | Output | SPI chip select, GPIO_ACTIVE_LOW |
| 9 | P0.07 | LIS2DH12 SDA/SDI/MOSI | Output | SPI MOSI, 3.3 V logic; P0.13 is fallback only |
| 10 | P0.08 | LIS2DH12 SDO/SA0/MISO | Input | SPI MISO, 3.3 V logic |
| 14 | P0.12 | LIS2DH12 SCL/SPC/SCK | Output | SPI clock, Mode 3, 1 MHz maximum |
| 12/13 MCU pins | P0.10/P0.09 | NFC1/NFC2 | Reserved | Capacitors to GND; NFC UICR handling required before GPIO use |
| 16 | P0.14 | Physical button 1 | Input | Reserved; future deep-sleep wake input |
| 17 | P0.15 | Physical button 2 | Input | Reserved; future deep-sleep wake input |
| 20 | P0.17 | RGB red | Output | Common-anode LED, 510 ohm series resistor, GPIO_ACTIVE_LOW |
| 21 | P0.18 | RGB green | Output | Common-anode LED, 100 ohm series resistor, GPIO_ACTIVE_LOW |
| 22 | P0.19 | RGB blue | Output | Common-anode LED, 100 ohm series resistor, GPIO_ACTIVE_LOW |

## LIS2DH12 LGA-12

| LGA-12 pin | Package marking | nRF52832 connection | Function |
|---|---|---|---|
| 1 | SPC/SCL | P0.12 | SPI_SCK |
| 2 | CS | P0.05 | SPI chip select, active low |
| 3 | SDO/SA0 | P0.08 | SPI_MISO |
| 4 | SDA/SDI | P0.07 | SPI_MOSI |
| 5 | INT1 | P0.03 | Interrupt1, GPIO_ACTIVE_HIGH |
| 6 | INT2 | P0.04 | Interrupt2, reserved |
| 7 | VDD_IO | 3.3 V | Digital interface supply with decoupling to GND |
| 8 | VDD | 3.3 V | Sensor supply with decoupling to GND |
| 9-14 | GND/reserved | GND | Ground and reserved pins per board layout; tie reserved pins to GND |

The DeviceTree entry is `lis2dh12: lis2dh@0`, compatible with `"st,lis2dh"`,
under `&spi1`, with a maximum SPI frequency of 1 MHz. Zephyr alias `accel0`
references this node.

## RGB LED

The LED is common-anode. Setting the logical LED state on in Zephyr makes the
active-low GPIO drive LOW. The resistors are in series with the individual
channels:

| Channel | nRF52832 | MCU pin | Resistance | Active state |
|---|---|---|---|---|
| Red | P0.17 | 20 | 510 ohm | LOW |
| Green | P0.18 | 21 | 100 ohm | LOW |
| Blue | P0.19 | 22 | 100 ohm | LOW |

## Accelerometer Software Behavior

The application sets the LIS2DH12 sampling frequency to 50 Hz and reads
`SENSOR_CHAN_ACCEL_XYZ` every 50 ms. A channel is switched on when the absolute
acceleration on its axis exceeds 5.0 m/s², approximately 0.5 g:

- X axis -> red,
- Y axis -> green,
- Z axis -> blue.

Initialization errors are indicated by fast red LED blinking. Sensor reads,
ODR configuration, and LED readiness are checked and logged through RTT.

## Future Wake-Up Architecture

INT1 is available on P0.03 and can later be configured as a LIS2DH12 activity,
free-fall, or threshold wake source. P0.14 and P0.15 are reserved for physical
buttons and can later be configured as wake-up inputs. The implementation can
combine LIS2DH12 motion thresholds and button GPIO wake events with Zephyr
deep sleep APIs or Nordic system-off mode. NFC pins P0.09/P0.10 must remain
NFC-reserved or have NFC disabled in UICR before GPIO reuse.

## Programing and Flashing

Build:

```powershell
pio run --project-dir firmware\accelerometer-test -e nrf52_dk
```

Upload through PlatformIO:

```powershell
pio run -t upload --project-dir firmware\accelerometer-test -e nrf52_dk
```

The PlatformIO upload target is not a direct nRF52 connection. In this project,
upload and BIN transfer are performed through the ESP32_nRF52_SWD HTTP API.
After transfer, reset the nRF52 through SWD.
