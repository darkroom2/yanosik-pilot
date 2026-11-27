# Zephyr LIS2DH12 Accelerometer Test

Projekt zawiera deterministyczny skaner diagnostyczny LIS2DH12TR.
Przeglądane są wyłącznie piny P0.03, P0.04, P0.07, P0.08, P0.12 i P0.13.
Piny P0.05 i P0.06 buzzera oraz pozostałe GPIO nie są konfigurowane przez skaner.

## Budowanie

W katalogu repozytorium uruchom:

```powershell
uv run pio run --project-dir firmware\accelerometer-test -e nrf52_dk
```

Wynikowy plik BIN:

```text
firmware/accelerometer-test/.pio/build/nrf52_dk/zephyr/zephyr.bin
```

PlatformIO upload (poprzez skonfigurowaną integrację projektu):

```powershell
pio run -t upload --project-dir firmware\accelerometer-test -e nrf52_dk
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

Aplikacja ustawia ODR LIS2DH12 na 50 Hz i co 100 ms odczytuje
`SENSOR_CHAN_ACCEL_XYZ`. Wartości X, Y i Z są logowane przez SEGGER RTT
co około 500 ms. Oś X steruje czerwonym LED, Y zielonym, Z niebieskim;
kanał świeci, gdy bezwzględna wartość osi przekracza 5.0 m/s².
Po skanie zielony LED pozostaje zapalony przy znalezieniu urządzenia, a czerwony
miga przy braku trafienia. Dioda RGB jest wspólnej anody i kanały są aktywne stanem niskim.

Pełny opis połączeń znajduje się w [docs/hardware.md](docs/hardware.md).
