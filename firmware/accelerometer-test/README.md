# Zephyr LIS2DH12 Accelerometer Test

Projekt odczytuje LIS2DH12TR przez sprzętowe I2C:
SCL P0.12, SDA P0.11, adres urządzenia 0x19.
Piny P0.05 i P0.06 buzzera oraz pozostałe GPIO nie są konfigurowane przez aplikację.

## Budowanie

W katalogu repozytorium uruchom:

```powershell
uv run pio run --project-dir firmware/accelerometer-test -e nrf52_dk
```

Wynikowy plik BIN:

```text
firmware/accelerometer-test/.pio/build/nrf52_dk/zephyr/zephyr.bin
```

PlatformIO upload (poprzez skonfigurowaną integrację projektu):

```powershell
pio run -t upload --project-dir firmware/accelerometer-test -e nrf52_dk
```

## Wgrywanie przez ESP32/SWD

Po zbudowaniu wgraj obraz przez API `ESP32_nRF52_SWD`, a następnie zresetuj cel:

```powershell
curl -X POST "http://swd.local/set_swd?cmd=init"
curl -X POST "http://swd.local/set_swd?cmd=erase_all"
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@firmware/accelerometer-test/.pio/build/nrf52_dk/zephyr/zephyr.bin" http://swd.local/flash_file_direct
curl -X POST "http://swd.local/set_swd?cmd=set_reset"
```

## Działanie testowe

Aplikacja ustawia ODR LIS2DH12 na 50 Hz i co 150 ms odczytuje
`SENSOR_CHAN_ACCEL_XYZ`. Wartości X, Y i Z są logowane przez SEGGER RTT.
Oś o największej bezwzględnej składowej steruje diodą: X czerwony, Y zielony,
Z niebieski. Dioda RGB jest wspólnej anody i kanały są aktywne stanem niskim.

Sprzętowe potwierdzenie: odczyty I2C X/Y/Z działają po wgraniu przez ESP32/SWD,
a przechylanie płytki poprawnie przełącza czerwony, zielony i niebieski kanał LED.

Pełny opis połączeń znajduje się w [docs/hardware.md](docs/hardware.md).
