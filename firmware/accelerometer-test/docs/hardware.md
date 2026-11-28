# Hardware Architecture: nRF52832 LIS2DH Pilot

## Overview

The pilot uses a Nordic nRF52832 in a QFN48 package. The application target is
ST LIS2DH in an LGA-14 package, connected through I2C at address 0x19,
and an RGB LED with a common anode. The ESP32_nRF52_SWD programmer provides
SWD flashing and target reset.

> The application uses I2C: SCL P0.12 and SDA P0.11. P0.05 and P0.06 remain
> reserved buzzer pins and are not configured.

## nRF52832 QFN48

The MCU supply is 3.3 V. Pins P0.09 and P0.10 are NFC1/NFC2 on pins 12 and 13
and are routed through capacitors to GND. They must not be used as ordinary
GPIO unless NFC is disabled in UICR. The physical buttons are connected to
P0.14 and P0.15.

| MCU physical pin | Port | Device pin / function | Direction | Zephyr / electrical parameter |
|---|---|---|---|---|
| 14 | P0.12 | LIS2DH SCL/SPC | Bidirectional | I2C SCL, Nordic TWIM, 100 kHz |
| 13 | P0.11 | LIS2DH SDA/SDI/SDO | Bidirectional | I2C SDA, address 0x19, Nordic TWIM |
| 12/13 MCU pins | P0.10/P0.09 | NFC1/NFC2 | Reserved | Capacitors to GND; NFC UICR handling required before GPIO use |
| 17 | P0.14 | Physical button 1 | Input | Pull-up, active-low; usable as a wake input |
| 18 | P0.15 | Physical button 2 | Input | Pull-up, active-low; usable as a wake input |
| 20 | P0.17 | RGB red | Output | Common-anode LED, 510 ohm series resistor, GPIO_ACTIVE_LOW |
| 21 | P0.18 | RGB green | Output | Common-anode LED, 100 ohm series resistor, GPIO_ACTIVE_LOW |
| 22 | P0.19 | RGB blue | Output | Common-anode LED, 100 ohm series resistor, GPIO_ACTIVE_LOW |

## LIS2DH LGA-14

| LGA-14 pin | Package marking | nRF52832 connection | Function |
|---|---|---|---|
| 1 | SPC/SCL | P0.12 | I2C SCL |
| 2 | CS | VDD_IO | I2C mode selected |
| 3 | SDO/SA0 | VDD_IO | Sets I2C address 0x19 |
| 4 | SDA/SDI | P0.11 | I2C SDA |
| 5 | INT1 | P0.03 | Interrupt1, GPIO_ACTIVE_HIGH |
| 6 | INT2 | P0.04 | Interrupt2, reserved |
| 7 | VDD_IO | 3.3 V | Digital interface supply with decoupling to GND |
| 8 | VDD | 3.3 V | Sensor supply with decoupling to GND |
| 9-14 | GND/reserved | GND | Ground and reserved pins per board layout; tie reserved pins to GND |

The DeviceTree entry is `lis2dh12: lis2dh12@19`, compatible with
`"st,lis2dh"`, under `&i2c0`, with `reg = <0x19>` and a 100 kHz bus.
Zephyr alias `accel0` references this node.

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

The application sets the LIS2DH sampling frequency to 50 Hz and reads
`SENSOR_CHAN_ACCEL_XYZ` every 150 ms. The axis with the largest absolute
acceleration controls the RGB channel:

- X axis -> red,
- Y axis -> green,
- Z axis -> blue.

Sensor and LED readiness are checked and logged through RTT.

Hardware verification confirmed I2C XYZ reads after SWD transfer and reset:
dominant X lights red, dominant Y lights green, and dominant Z lights blue.

## Future Wake-Up Architecture

INT1 is available on P0.03 and can later be configured as a LIS2DH activity,
free-fall, or threshold wake source. The physical button inputs P0.14 and P0.15
can also be configured as wake-up inputs. The implementation can
combine LIS2DH motion thresholds and button GPIO wake events with Zephyr
deep sleep APIs or Nordic system-off mode. NFC pins P0.09/P0.10 must remain
NFC-reserved or have NFC disabled in UICR before GPIO reuse.

## Programing and Flashing

Build:

```powershell
uv run pio run --project-dir firmware/accelerometer-test -e nrf52_dk
```

Upload through PlatformIO:

```powershell
pio run -t upload --project-dir firmware\accelerometer-test -e nrf52_dk
```

The PlatformIO upload target is not a direct nRF52 connection. In this project,
upload and BIN transfer are performed through the ESP32_nRF52_SWD HTTP API.
After transfer, reset the nRF52 through SWD.
