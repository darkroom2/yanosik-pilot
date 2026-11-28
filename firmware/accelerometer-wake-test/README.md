# Zephyr LIS2DH Sleep-to-Wake / Stream-to-FIFO Test

Projekt testuje nRF52832 SYSTEM OFF oraz samoistne Sleep-to-Wake LIS2DH.
Na zimnym starcie sensor jest konfigurowany raz do 100 Hz / trybu Normal
z buforem Stream-to-FIFO i aktywnością ruchową. W kolejnym System OFF
INT1 jest jedynym źródłem wybudzenia nRF52832.

Potwierdzona/specyfikowana konfiguracja:

- nRF52832 z DCDC, I2C SDA P0.11, SCL P0.12, adres LIS2DH `0x19`.
- Brak zewnętrznych rezystorów pull-up na magistrali I2C.
- LIS2DH INT1 P0.03, aktywny stanem wysokim.
- RGB wspólna anoda: czerwony P0.17, zielony P0.18, niebieski P0.19.
- Buzzer P0.05/P0.06 ustawiony w stan niski.
- Przyciski P0.13/P0.14 odłączone od wejścia.
- Rejestry LIS2DH: CTRL_REG1 `0x57`, CTRL_REG2 `0x09`,
  CTRL_REG3 `0x40`, CTRL_REG4 `0x80`, CTRL_REG5 `0x40`,
  FIFO_CTRL_REG `0xC0`, ACT_THS `0x08`, ACT_DUR `0x26`,
  INT1_THS `0x08`, INT1_DURATION `0x02`, INT1_CFG `0x2A`.

Po zimnym starcie aplikacja miga zielono przez 10 ms i przechodzi do
SYSTEM OFF. Po wybudzeniu przez P0.03 miga niebiesko przez 5 ms, odczytuje
FSS z FIFO_SRC_REG `0x2F` i wykonuje wielobajtowy odczyt próbek od
`OUT_X_L (0x28 | 0x80)`. Pierwsze kilka próbek X/Y/Z jest logowanych przez RTT.
Następnie FIFO przechodzi przez Bypass `0x00` i wraca do Stream-to-FIFO `0xC0`.

Po re-uzbrojeniu aplikacja co 50 ms sprawdza P0.03 i wraca do System OFF,
gdy sensor automatycznie zakończy zdarzenie i linię INT1 opuści stan wysoki.

Zbuduj projekt:

```powershell
uv run pio run --project-dir firmware\accelerometer-wake-test -e nrf52_dk
```

Plik BIN:

```text
firmware/accelerometer-wake-test/.pio/build/nrf52_dk/zephyr/zephyr.bin
```

Wgraj przez ESP32/SWD i zresetuj cel:

```powershell
curl -X POST "http://swd.local/set_swd?cmd=init"
curl -X POST "http://swd.local/set_swd?cmd=erase_all"
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@firmware/accelerometer-wake-test/.pio/build/nrf52_dk/zephyr/zephyr.bin" http://swd.local/flash_file_direct
curl -X POST "http://swd.local/set_swd?cmd=set_reset"
```

Weryfikacja sprzętowa: po niebieskim mignięciu zmierz prąd całej płytki i
porusz akcelerometrem. Oczekiwane jest wybudzenie nRF52832 przez przejście
P0.03 do stanu wysokiego. Pomyślna kompilacja nie potwierdza działania SYSTEM
OFF ani poboru prądu.

Do pomiaru finalnego poboru 3-4 uA ustaw w `zephyr/prj.conf`
`CONFIG_CONSOLE=n`, `CONFIG_USE_SEGGER_RTT=n`, `CONFIG_RTT_CONSOLE=n`,
`CONFIG_LOG=n` i `CONFIG_LOG_BACKEND_RTT=n`, a następnie odłącz SWD.
