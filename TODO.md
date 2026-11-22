# TODO

## Namierzanie pinów akcelerometru

- [ ] Poszerzyć testy sprzętowe dla akcelerometru LIS2DH i ustalić jego rzeczywiste
  połączenia z nRF52832.
- [ ] Sprawdzić podłączenie magistrali I2C lub SPI oraz zidentyfikować piny SDA/SDO,
  SCL/SCK i CS.
- [ ] Odszukać i potwierdzić sygnał wybudzenia akcelerometru, jeśli jest podłączony
  do osobnego pinu nRF52.
- [ ] Rozszerzyć `tools/hardware_test.py` o tryb skanujący potencjalne kombinacje
  pinów magistrali i wyświetlający wynik każdego wariantu.
- [ ] Dodać testy komunikacyjne dla odczytu identyfikatora LIS2DH i podstawowych
  rejestrów czujnika.
- [ ] Zapisać potwierdzone mapowanie pinów w README.md wraz z napięciami logicznymi
  i sterowanymi liniami.

## Buzzer

- [ ] Zidentyfikować piny buzzera i układu podbijania napięcia.
- [ ] Dodać potwierdzony wynik do tabeli mapowania pinów.

## Firmware i narzędzia

- [ ] Uzupełnić dokumentację API ESP32_nRF52_SWD o wszystkie dostępne operacje.
- [ ] Dodawać przykłady poleceń zachowujące zgodność składni między Linuxem i
  PowerShell.
- [ ] Zweryfikować instrukcje przywracania flash i UICR na rzeczywistym urządzeniu.
