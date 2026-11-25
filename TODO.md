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

- [x] Potwierdzić fizyczne mapowanie buzzera: pin 7 -> P0.05, pin 8 -> P0.06.
- [ ] Zidentyfikować układ podbijania napięcia używany przez buzzer.
- [ ] Zweryfikować sprzętowo ton i ciszę projektu `firmware/buzzer-test`.
- [ ] Dodać dwukierunkową sygnalizację stanów przez buzzer i diodę/LED:
  zdarzenia wychodzące z pilota do Home Assistant oraz potwierdzenia lub stany
  przychodzące z Home Assistant lub innych systemów.
- [ ] Ustalić priorytety i zachowania podczas konfliktu sygnałów, np. alarm,
  potwierdzenie, utrata połączenia i tryb uśpienia.

## Firmware i narzędzia

- [ ] Uzupełnić dokumentację API ESP32_nRF52_SWD o wszystkie dostępne operacje.
- [ ] Dodawać przykłady poleceń zachowujące zgodność składni między Linuxem i
  PowerShell.
- [ ] Zweryfikować instrukcje przywracania flash i UICR na rzeczywistym urządzeniu.
- [ ] Potwierdzić sprzętowo rozgłaszanie `nRF52_Test_BLE` po wgraniu SoftDevice
  S132 i firmware przez ESP32/SWD.
- [ ] Potwierdzić sprzętowo rozgłaszanie `nRF52_Zephyr_BLE` po zbudowaniu i wgraniu
  projektu `firmware/ble-zephyr` przez ESP32/SWD.
- [ ] Dodać bezpośredni endpoint ESP32 do pobierania RAM jako `.bin`, aby nie
  musieć pobierać zrzutu przez uwierzytelniony edytor SPIFFS.
- [ ] Jeśli urządzenie nie uruchamia po SWD, sprawdzić APPROTECT i wykonać
  pełne wymazanie przed ponownym flashowaniem.

## NFC

- [ ] Zwizualizować płytkę od strony komponentów i ścieżek, aby sprawdzić
  obecność cewki NFC oraz rezystorów/mostków przy P0.09 i P0.10.
- [ ] Odczytać UICR `NFCPINS` i potwierdzić, czy piny 9 i 10 są skonfigurowane
  jako interfejs NFC, czy GPIO.
- [ ] Jeśli cewki nie ma, ocenić dostępne miejsce i możliwość dodania zewnętrznej
  anteny NFC-A ze ścieżkami NFC1/NFC2 oraz elementami dopasowującymi zgodnymi
  z referencyjnym układem Nordic.
- [ ] Po dodaniu i zaprojektowaniu anteny zweryfikować odczyt w telefonie,
  wake-on-field oraz, jeśli używany, Touch-to-Pair.

## ANT+

- [ ] Potwierdzić, że docelowy wariant firmware i nRF52832 umożliwiają wybranie
  SoftDevice/stacku ANT przez obsługiwane SDK i narzędzia.
- [ ] Sprawdzić licencję, wymagania EULA i klucz licencyjny przed komercyjnym
  użyciem ANT/ANT+.
- [ ] Zbudować i uruchomić minimalny test transmisji i odbioru ANT na pilotach
  lub kompatybilnym urządzeniu testowym.
- [ ] Jeśli wymagane równoczesne BLE i ANT, zweryfikować obsługę wariantu
  concurrent SoftDevice oraz zachowanie zużycia energii.
