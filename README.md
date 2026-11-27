# Yanosik Pilot

Projekt zawiera narzędzia do:

- odczytywania i identyfikacji pamięci płytki pilota opartej na nRF52832,
- odblokowania zabezpieczenia APPROTECT,
- wykonywania pełnych zrzutów pamięci,
- przywracania fabrycznego firmware,
- testowania diod, przycisków i przypisania pinów sprzętowych.

## Spis treści

- [Opis płytki pilota](#opis-płytki-pilota)
  - [Wykryte elementy](#wykryte-elementy)
  - [Zidentyfikowane piny](#zidentyfikowane-piny)
  - [Elementy wymagające dalszej identyfikacji](#elementy-wymagające-dalszej-identyfikacji)
- [Przygotowanie środowiska](#przygotowanie-środowiska)
- [Podłączenie programatora ESP32](#podłączenie-programatora-esp32)
- [Praca z firmware nRF52](#praca-z-firmware-nrf52)
  - [nRF52832 Hardware & SWD Flashing Notes](#nrf52832-hardware--swd-flashing-notes)
  - [Budowanie i wgrywanie projektów firmware](#budowanie-i-wgrywanie-projektów-firmware)
    - [`firmware/blinker`](#firmwareblinker)
    - [`firmware/ble-test`](#firmwareble-test)
    - [`firmware/buzzer-test`](#firmwarebuzzer-test)
    - [`firmware/ble-zephyr`](#firmwareble-zephyr)
     - [`firmware/zephyr-template`](#firmwarezephyr-template)
     - [`firmware/accelerometer-test`](#firmwareaccelerometer-test)
- [Testowanie firmware](#testowanie-firmware)
- [Test mapowania sprzętu](#test-mapowania-sprzętu)
- [Planowane prace](#planowane-prace)
- [Archiwum fabrycznego firmware](#archiwum-fabrycznego-firmware)

## Opis płytki pilota

Płytka pilota jest zbudowana wokół mikrokontrolera **Nordic nRF52832 (nRF52)**.
Obsługuje łączność Bluetooth Low Energy z telefonem, przyciski, diodę oraz
zarządzanie poborem energii.

### Wykryte elementy

- **Akcelerometr LIS2DH (oznaczenie `NAI`)** — trójosiowy czujnik o niewielkim
  poborze prądu. Wykrywa ruch i wibracje pojazdu oraz może wybudzać procesor ze
  stanu uśpienia.
- **Buzzer piezoelektryczny z układem podbijającym napięcie** — płaski głośnik
  SMD współpracujący z tranzystorem i cewką. Układ podbija napięcie z około 3 V
  do kilku–kilkunastu woltów, co umożliwia uzyskanie odpowiednio wysokiego dźwięku.
- **Rezonatory kwarcowe 32 MHz i 32,768 kHz** — stabilizują pracę radia BLE
  oraz odmierzenie czasu podczas trybu uśpienia.
- **Antena PCB i układ dopasowania** — ścieżka antenowa umieszczona przy
  krawędzi płytki oraz miniaturowe kondensatory i cewki zapewniające transmisję
  sygnału BLE.
- **Dioda LED RGB i rezystory** — sygnalizują rodzaj zagrożenia oraz stan
  połączenia za pomocą różnych kolorów.
- **Dwa mikroprzełączniki `+` i `-`** — umożliwiają potwierdzanie i odwoływanie
  zdarzeń oraz ręczne wybudzanie płytki.
- **Koszyk baterii CR2450 i kondensatory MLCC** — zapewniają zasilanie 3 V oraz
  buforują krótkotrwałe skoki poboru prądu, np. podczas pracy buzzera.
- **Pady serwisowe SWD** — złote pola lutownicze służące do programowania i
  diagnostyki układu nRF52832.
- **Cewka DCC (10 µH)** — zewnętrzna indukcyjność obsługująca przetwornicę
  nRF52832 w trybie DC/DC.
- **Cewka DEC4 (15 nH)** — zewnętrzna indukcyjność nRF52832.

### Zidentyfikowane piny

| Fizyczny pin | Port nRF52 | Podłączony element |
|---|---|---|
| 7 | P0.05 | Jeden biegun buzzera; podłączenie różnicowe / mostkowe |
| 8 | P0.06 | Drugi biegun buzzera; podłączenie różnicowe / mostkowe |
| 16 | P0.13 | Przycisk nr 1; styk zwiera do masy, wejście `INPUT_PULLUP` |
| 17 | P0.14 | Przycisk nr 2; styk zwiera do masy, wejście `INPUT_PULLUP` |
| 20 | P0.17 | Czerwona dioda LED, rezystor 510 Ω; anoda wspólna, świeci przy stanie niski |
| 21 | P0.18 | Zielony kanał diody RGB, rezystor 100 Ω; anoda wspólna, świeci przy stanie niski |
| 22 | P0.19 | Niebieski kanał diody RGB, rezystor 100 Ω; anoda wspólna, świeci przy stanie niski |

### Elementy wymagające dalszej identyfikacji

- Nie zidentyfikowano jeszcze układu podbijającego napięcie używanego przez
  buzzer.
- Nie zidentyfikowano jeszcze podłączeń akcelerometru LIS2DH, w tym magistrali
  komunikacyjnej i sygnału wybudzenia.
- Nie potwierdzono ostatecznej funkcji fizycznych pinów przycisków poza ich
  przypisaniem do P0.13 i P0.14.
- Nie potwierdzono istnienia obwodu NFC ani cewki NFC na płytce. nRF52832 ma
  wejścia NFC1/NFC2 na P0.09 i P0.10, ale ich obecność zależy od połączeń PCB
  i konfiguracji UICR `NFCPINS`.
- Nie zweryfikowano obsługi ANT+. nRF52832 ma radio zdolne do pracy z
  protokołem ANT, jednak potrzebny jest oddzielny SoftDevice/stack ANT i licencja
  użycia oraz aktualny firmware do testu.

## Przygotowanie środowiska

Na Linuxie podłącz ESP32 przez USB i sprawdź wykryte urządzenia:

```bash
uv run pio device list
```

Wgraj firmware ESP32_nRF52_SWD z katalogu repozytorium:

```bash
uv run pio run --project-dir tools/ESP32_nRF52_SWD -e ESP32_nRF52_SWD -t upload
uv run pio run --project-dir tools/ESP32_nRF52_SWD -e ESP32_nRF52_SWD -t uploadfs
```

### Alternatywa dla Windows

Na Windows wgrywanie zwykle wymaga wskazania portu COM:

```powershell
uv run pio run --project-dir tools/ESP32_nRF52_SWD -e ESP32_nRF52_SWD -t upload --upload-port COM3
uv run pio run --project-dir tools/ESP32_nRF52_SWD -e ESP32_nRF52_SWD -t uploadfs --upload-port COM3
```

Zastąp `COM3` portem zwróconym przez `uv run pio device list`.

### Monitor portu szeregowego ESP32

Otwórz monitor, wskazując port i prędkość używaną przez firmware:

```powershell
uv run pio device monitor --port COM3 --baud 115200
```

Na Linuxie ścieżka portu może mieć postać `/dev/ttyUSB0`. Z monitora wyjdziesz
skrótami `Ctrl+C`.

> [!WARNING]
> Uruchomienie monitora może zresetować ESP32 przez linię DTR lub inne
> ustawienia adaptera USB-UART. Restart przerywa trwające zadania SWD, dlatego
> nie uruchamiaj monitora podczas programowania, kasowania ani zrzutu pamięci
> nRF52.

Jeśli system nie przypisuje portu urządzeniu
`CP2102 USB to UART Bridge Controller`, zainstaluj oficjalny CP210x Universal
Windows Driver. Uruchom PowerShell jako administrator i wykonaj:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\tools\install-cp210x-driver.ps1
```

Jeśli serwer Silicon Labs zwróci błąd `Access Denied`, pobierz ręcznie
`CP210x_Universal_Windows_Driver.zip` i podaj ścieżkę do archiwum:

```powershell
.\tools\install-cp210x-driver.ps1 -ZipPath "$env:USERPROFILE\Downloads\CP210x_Universal_Windows_Driver.zip"
```

## Podłączenie programatora ESP32

Złącze programatora nie ma podpisanych pinów. Znana jest tylko kolejność:
ostatni pin ma numer **4** i jest sygnałem **GND**. Numery piny przypisuj
zaczynając od tego samego końca złącza i nie odwracaj jego orientacji.

| Numer pinu złącza | Sygnał nRF52 | Domyślny pin ESP32 |
|---|---|---|
| 1 | SWDCLK | GPIO 21 (`21`) |
| 2 | SWDIO | GPIO 19 (`19`) |
| 3 | VDD 3.3 V | `3V3` |
| 4 | GND | `GND` |

Piny ESP32 powyżej są domyślnymi ustawieniami środowiska
`ESP32_nRF52_SWD` z `tools/ESP32_nRF52_SWD/platformio.ini`. Są one
konfigurowalne build flagami i mogą być inne na alternatywnych płytkach ESP32
lub w innym środowisku PlatformIO. Płytkę ESP32 należy traktować jako
uniwersalny programator SWD; nazwa obudowy, typ Wi-Fi lub procesor płytki nie
jest częścią protokołu obsługi nRF52.

Podłącz dodatkowo wspólną masę z pinu 4 złącza do pinu `GND` modułu ESP32.

> [!WARNING]
> - Zasilanie 3.3 V z pinu 3 podłączaj tylko wtedy, gdy płytka nRF52 nie ma
>   własnego zasilania, np. baterii.
> - Jeśli nRF52 jest zasilany osobno, pozostaw pin 3 złącza nRF52 niepodłączony.
> - Nie podłączaj napięcia 5 V ani żadnego napięcia większego niż 3.3 V do płytki
>   ESP32.

## Praca z firmware nRF52

ESP32 udostępnia API do odczytu stanu, odblokowania APPROTECT, zrzutu pamięci i
przywracania firmware. Wszystkie operacje można wykonywać ręcznie w interfejsie
WWW pod adresem `http://swd.local/` lub za pomocą zapytań `curl`.

### Programowanie nRF52 przez ESP32/SWD

W tym projekcie komputer komunikuje się z programatorem ESP32, a ESP32 łączy się
z nRF52 przez SWD. Płytka pilota nRF52 nie jest podłączana bezpośrednio do
komputera ani wykrywana przez PlatformIO jako urządzenie programujące.

Środowisko `nrf52_dk` z `firmware/blinker/platformio.ini` jest tylko jednym
przykładem wariantu PlatformIO używanego do kompilacji nRF52. W repozytorium
mogą istnieć inne katalogi firmware i alternatywne pliki HEX. Nazwa środowiska
`nrf52_dk` nie oznacza, że do komputera jest podłączona płytka Nordic
nRF52-DK. Standardowe `pio run -t upload` może oczekiwać programatora J-Link;
do wgrania dowolnego zbudowanego firmware na pilot użyj ESP32/SWD.

### nRF52832 Hardware & SWD Flashing Notes

Wszystkie firmware Zephyr powinny zachować:

```ini
CONFIG_NRF_APPROTECT_USE_UICR=y
CONFIG_NRF_APPROTECT_LOCK=n
```

`CONFIG_NRF_APPROTECT_LOCK=n` z `CONFIG_NRF_APPROTECT_USE_UICR=y` utrzymuje
SWD odblokowane podczas rozwoju i zapobiega ponownemu zablokowaniu po każdym
starcie Zephyr.

Jeżeli przypadkowo wgrano firmware, które włącza DC/DC lub blokuje
`APPROTECT`, odzyskanie wykonuje ESP32 przez procedurę cold-boot `ERASEALL`:

1. VDD, `SWDCLK` i `SWDIO` są jednocześnie ustawiane na stan niski na 500 ms.
2. VDD wraca na stan wysoki, `SWDCLK` pozostaje niski, a po 1 ms inicjowane jest SWD.
3. ESP32 wysyła sekwencję line reset SWD, czyści DP, włącza zasilanie debugera,
   wybiera AP 1 i wykonuje `CTRL-AP RESET` oraz `ERASEALL`, zanim Zephyr zdąży
   uruchomić DCDC, APPROTECT albo stan uśpienia.

Operację uruchamia polecenie `curl -X POST "http://swd.local/set_swd?cmd=erase_all"`.
Odpowiedź HTTP `Erase started` oznacza przyjęcie polecenia; dalszy przebieg i
diagnostyka `ERASEALLSTATUS` są raportowane przez port szeregowy ESP32.

### Nowy projekt firmware nRF52

Aby utworzyć nowy, niezależny szkic z Arduino, przejdź do katalogu
`firmware` i wybierz nazwę projektu:

```powershell
mkdir firmware\nazwa-projektu
cd firmware\nazwa-projektu
uv run pio project init --board nrf52_dk --project-option "framework=arduino"
```

Z katalogu nowego projektu:

```powershell
uv run pio run -e nrf52_dk
```

Możesz też wrócić do katalogu głównego i użyć:

```powershell
cd ..\..
uv run pio run --project-dir firmware\nazwa-projektu -e nrf52_dk
```

Polecenie `project init` tworzy szkielet PlatformIO, katalog `src` i plik
`platformio.ini`. Nazwa środowiska powstająca z opcji `--board nrf52_dk` to
`nrf52_dk`; jest ona punktem wyjścia dla wielu projektów firmware w katalogu
`firmware`.

### Budowanie i wgrywanie projektów firmware

Budowanie jest wykonywane przez PlatformIO. Wgrywanie przez ESP32/SWD odbywa się
przez endpoint `flash_file_direct`, a po transferze cel należy zresetować przez
`set_reset`. Każdy projekt ma własny wynikowy HEX i może mieć inne wymagania
pamięciowe.

#### `firmware/blinker`

Ten szkic testuje LED RGB i dwa przyciski:

- LED miga początkowo na czerwono;
- przycisk 1 zmienia kolor w kolejności czerwony → zielony → niebieski;
- przycisk 2 zatrzymuje miganie (LED gaśnie) i wznawia je w wybranym kolorze.

Wariant Arduino `nRF52DK` używa następujących pinów:

| Funkcja | Port nRF52 | Pin Arduino |
|---|---|---|
| Przycisk zmiany koloru | P0.13 | D2 |
| Przycisk pauzy | P0.14 | D3 |
| Czerwony kanał LED | P0.17 | D6 |
| Zielony kanał LED | P0.18 | D7 |
| Niebieski kanał LED | P0.19 | D8 |

Uruchom testy hostowe tego projektu:

```powershell
uv run pio test --project-dir firmware\blinker -e host-test-windows
```

Na Linuxie:

```bash
uv run pio test --project-dir firmware/blinker -e host-test-linux
```

Zbuduj szkic:

```powershell
uv run pio run --project-dir firmware\blinker -e nrf52_dk
```

Wgraj aplikację:

```bash
curl -X POST "http://swd.local/set_swd?cmd=init"
curl -X POST "http://swd.local/set_swd?cmd=erase_all"
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@firmware/blinker/.pio/build/nrf52_dk/firmware.hex" http://swd.local/flash_file_direct
curl -X POST "http://swd.local/set_swd?cmd=set_reset"
```

#### `firmware/ble-test`

Projekt `firmware/ble-test` używa środowiska PlatformIO `nrf52_dk`,
frameworka Arduino i biblioteki `BLEPeripheral` (`sandeepmistry/BLEPeripheral`).
Po uruchomieniu rozgłasza urządzenie o nazwie `nRF52_Test_BLE`.
Do testu radio mapa pinów płytki nie ma znaczenia.

Konfiguracja projektu określa SoftDevice S132 w wersji 2.0.1:

```ini
[env:nrf52_dk]
platform = nordicnrf52
board = nrf52_dk
framework = arduino

board_build.softdevice.sd_name = s132
board_build.softdevice.sd_version = 2.0.1
build_flags = -DNRF52_S132

lib_deps =
    sandeepmistry/BLEPeripheral
```

Przed pierwszym testem BLE przygotuj SoftDevice. Skrypt pobiera pakiet S132 do
pamięci i wypakowuje wyłącznie plik HEX:

```powershell
uv run python tools/extract_s132_softdevice.py
```

Wynik jest zapisany jako
[`dumps/s132_nrf52_2.0.1_softdevice.hex`](dumps/s132_nrf52_2.0.1_softdevice.hex).

Wgraj SoftDevice pod offsetem `0`, zbuduj aplikację i wgraj wynikowy HEX:

```powershell
curl -X POST "http://swd.local/set_swd?cmd=init"
curl -X POST "http://swd.local/set_swd?cmd=erase_all"
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@dumps/s132_nrf52_2.0.1_softdevice.hex" http://swd.local/flash_file_direct
uv run pio run --project-dir firmware\ble-test -e nrf52_dk
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@firmware/ble-test/.pio/build/nrf52_dk/firmware.hex" http://swd.local/flash_file_direct
curl -X POST "http://swd.local/set_swd?cmd=set_reset"
```

Wynikowy plik HEX aplikacji:

```text
firmware/ble-test/.pio/build/nrf52_dk/firmware.hex
```

SoftDevice nie jest częścią `firmware.hex`; po zmianie SoftDevice lub przy
ponownym flashowaniu aplikacji zachowaj poprawną kolejność i zresetuj cel.
Obecność rozgłaszania `nRF52_Test_BLE` potwierdź skanerem BLE. Sam pomyślny
build lub odpowiedź HTTP 200 nie potwierdzają działania radio.

#### `firmware/buzzer-test`

Projekt `firmware/buzzer-test` używa frameworka Zephyr i sprzętowego PWM do
testu różnicowego podłączenia buzzera:

| Funkcja | Port nRF52 | Fizyczny pin |
|---|---|---|
| Kanał A buzzera | P0.05 / GPIO 5 | 7 |
| Kanał B buzzera | P0.06 / GPIO 6 | 8 |

PWM0 generuje ton 2 kHz z wypełnieniem 50% na obu kanałach. Drugi kanał ma
odwróconą polaryzację, więc sygnał jest sterowany przeciwfazowo. Ton trwa
500 ms, następnie następuje cisza przez 1000 ms. W stanie ciszy oba kanały
ustawiają się tak, aby nie utrzymywać różnicy potencjałów.

UART0 i standardowe wejście/wyjście konsoli są wyłączone w celu zwolnienia
P0.05 i P0.06. Diagnostykę można realizować przez RTT.

Zbuduj projekt środowiskiem `nrf52_dk`:

```powershell
uv run pio run --project-dir firmware\buzzer-test -e nrf52_dk
```

Wynikowy plik BIN:

```text
firmware/buzzer-test/.pio/build/nrf52_dk/zephyr/zephyr.bin
```

Wgraj plik przez ESP32/SWD, a następnie zresetuj cel:

```powershell
curl -X POST "http://swd.local/set_swd?cmd=init"
curl -X POST "http://swd.local/set_swd?cmd=erase_all"
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@firmware/buzzer-test/.pio/build/nrf52_dk/zephyr/zephyr.bin" http://swd.local/flash_file_direct
curl -X POST "http://swd.local/set_swd?cmd=set_reset"
```

Potwierdzenie sprzętowe wymaga fizycznego usłyszenia tonu około 2 kHz przez
500 ms i ciszy przez około 1000 ms po zresetowaniu nRF52. Pomyślna kompilacja
lub odpowiedź HTTP 200 potwierdzają tylko kompilację i transfer pliku.

#### `firmware/ble-zephyr`

Projekt `firmware/ble-zephyr` używa frameworka Zephyr i natywnego stosu
Bluetooth do rozgłaszania niełączonego urządzenia o nazwie `nRF52_Zephyr_BLE`.
SEGGER RTT jest włączony w `zephyr/prj.conf` do przyszłej diagnostyki przez pamięć RAM i SWD.

Zbuduj projekt środowiskiem `nrf52_dk`:

```powershell
uv run pio run --project-dir firmware\ble-zephyr -e nrf52_dk
```

Wynikowy plik BIN:

```text
firmware/ble-zephyr/.pio/build/nrf52_dk/zephyr/zephyr.bin
```

Wgraj plik BIN przez istniejące API ESP32/SWD:

```powershell
curl -X POST "http://swd.local/set_swd?cmd=init"
curl -X POST "http://swd.local/set_swd?cmd=erase_all"
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@firmware/ble-zephyr/.pio/build/nrf52_dk/zephyr/zephyr.bin" http://swd.local/flash_file_direct
curl -X POST "http://swd.local/set_swd?cmd=set_reset"
```

Potwierdzenie sprzętowe wymaga zaobserwowania rozgłaszania `nRF52_Zephyr_BLE`
skanerem BLE po zresetowaniu celu. Pomyślna kompilacja i odpowiedź HTTP 200
same w sobie nie potwierdzają działania radio.

#### `firmware/zephyr-template`

Projekt `firmware/zephyr-template` jest neutralnym szablonem aplikacji Zephyr
dla płytki nRF52 DK. Po uruchomieniu loguje komunikat startowy przez SEGGER
RTT i przełącza LED0 raz na sekundę. Nie zawiera stosu Bluetooth ani logiki
konkretnego urządzenia, dzięki czemu można go skopiować jako punkt startowy
nowego projektu firmware.

Skopiuj cały katalog `firmware/zephyr-template`, nadaj mu nazwę nowego projektu
i zaktualizuj `project(...)` w `zephyr/CMakeLists.txt`. Własne moduły dodawaj
poprzez `target_sources(app PRIVATE ...)`; konfigurację RTT pozostaw w
`zephyr/prj.conf`, chyba że nowy projekt świadomie zmienia sposób diagnostyki.

Zbuduj szablon środowiskiem `nrf52_dk`:

```powershell
uv run pio run --project-dir firmware\zephyr-template -e nrf52_dk
```

Wynikowy plik BIN:

```text
firmware/zephyr-template/.pio/build/nrf52_dk/zephyr/zephyr.bin
```

Wgraj plik BIN przez istniejące API ESP32/SWD i zresetuj cel:

```powershell
curl -X POST "http://swd.local/set_swd?cmd=init"
curl -X POST "http://swd.local/set_swd?cmd=erase_all"
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@firmware/zephyr-template/.pio/build/nrf52_dk/zephyr/zephyr.bin" http://swd.local/flash_file_direct
curl -X POST "http://swd.local/set_swd?cmd=set_reset"
```

#### `firmware/accelerometer-test`

Projekt `firmware/accelerometer-test` testuje akcelerometr LIS2DH12 podłączony
do SPI1 nRF52832 oraz wspólną anodową diodę RGB. Potwierdzone połączenia to
SCK P0.12, MOSI P0.07, MISO P0.08 i CS P0.05. X, Y i Z mapują się odpowiednio
na czerwony, zielony i niebieski kanał po przekroczeniu progu 5.0 m/s².
Konfigurację pinów i urządzeń opisuje
[docs/hardware.md](firmware/accelerometer-test/docs/hardware.md).

Zbuduj projekt:

```powershell
uv run pio run --project-dir firmware\accelerometer-test -e nrf52_dk
```

Wynikowy plik BIN:

```text
firmware/accelerometer-test/.pio/build/nrf52_dk/zephyr/zephyr.bin
```

Wgraj przez ESP32/SWD i zresetuj cel:

```powershell
curl -X POST "http://swd.local/set_swd?cmd=init"
curl -X POST "http://swd.local/set_swd?cmd=erase_all"
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@firmware/accelerometer-test/.pio/build/nrf52_dk/zephyr/zephyr.bin" http://swd.local/flash_file_direct
curl -X POST "http://swd.local/set_swd?cmd=set_reset"
```

TODO: poprawic skrypt i wywalic te sekcje 
Zweryfikowany sposób odczytu logów SEGGER RTT przez ESP32/SWD:

1. Zatrzymaj lub zresetuj nRF52832 przez endpoint SWD.
2. Zleć zrzut 64 KB RAM w oparciu o endpoint programu ESP32:

```powershell
curl.exe -u admin:admin -X POST "http://swd.local/flash_cmd?cmd=dump_flash&file=ram.bin&offset=20000000&size=10000"
```

3. Po zakończeniu zadania pobierz plik przez edytor SPIFFS:

```powershell
curl.exe -u admin:admin --fail -o ram.bin "http://swd.local/edit?download=ram.bin"
```

W zrzucie RAM należy szukać magic `SEGGER`/`SEggerRTT` oraz tekstów
`nRF52 Zephyr BLE starting` i `BLE advertising started`.

Automatyczny odczyt jednego ze skryptów:

```powershell
uv run python tools/read_rtt_logs.py --host http://swd.local --username admin --password admin
```

Skrypt zleca zrzut 64 KB RAM, czeka na ukończenie zadania i pobiera dane
bezpośrednio do pamięci programu, bez tworzenia lokalnego pliku `ram.bin`.
Zawartość pierwszego kanału RTT (up channel 0) zapisuje do `rtt.log` i jednocześnie
wypisuje ją na konsolę. Nazwę pliku można zmienić opcją `--log`.

Firmware sygnalizuje błędy na pinie P0.17:

- dwa szybkie migania: błąd `bt_enable()`;
- trzy szybkie migania: błąd `bt_le_adv_start()`;
- przełączanie co 1 sekundę: Bluetooth został uruchomiony i program żyje.

Przy samodzielnej płytce zmień `LED_PIN` na dostępny pin P0.xx. Jeśli po
wgraniu nie ma reakcji LED, odłącz zasilanie i SWD, następnie uruchom układ
ponownie. Sprawdź również reset po flaszu i pełne wymazanie flash, jeśli
APPROTECT blokuje zapis.

Port szeregowy ESP32 nie jest portem szeregowym nRF52. Nie zakładaj, że
`pio device monitor` albo testy PlatformIO uruchomione dla targetu nRF52 będą
mogły wgrać firmware lub odczytać z niego logi. Logikę niezależną od sprzętu
testuj hostowo, a fizyczne GPIO i działanie płytki weryfikuj przez ESP32/SWD,
np. narzędziem [`tools/hardware_test.py`](tools/hardware_test.py).

### Interfejs przeglądarkowy

Interfejs zawiera sekcje:

- **Glitcher** — ustawienie opóźnienia, uruchomienie odblokowania oraz zrzut
  pełnej pamięci flash i UICR;
- **SWD** — inicjalizacja połączenia, odczyt stanu zabezpieczenia, reset,
  kasowanie i zapis rejestrów;
- **Flash** — kasowanie, zapis pliku, zrzut pamięci oraz pobieranie jej
  zawartości.

Po wgraniu firmware otwórz `http://swd.local/` i wykonaj operacje z
odpowiednich sekcji interfejsu.

### Podstawowe operacje przez API

Sprawdzenie stanu nRF52 i postępu zadania:

```bash
curl "http://swd.local/get_state"
curl "http://swd.local/get_state?cmd=1"
```

Inicjalizacja SWD i odczyt stanu blokady:

```bash
curl -X POST "http://swd.local/set_swd?cmd=init"
curl -X POST "http://swd.local/set_swd?cmd=lock_state"
```

Odblokowanie zabezpieczenia APPROTECT można uruchomić przez Glitcher. Najpierw
ustaw opóźnienia, a następnie włącz Glitcher:

```bash
curl -X POST "http://swd.local/set_delay?delay=2000&delay_end=3000&power_off=50&swd_wait=100"
curl -X POST "http://swd.local/set_glitcher?state=1"
```

Stan działania sprawdzaj ponownie przez `/get_state`. Podczas pracy Glitchera
mechanizm automatycznie próbuje wykryć wariant nRF52832 i odczytać zablokowany
stan zabezpieczenia.

### Zrzuty pamięci przez API

Pełny zrzut flash i UICR tworzą zadania na ESP32:

```bash
curl -X POST "http://swd.local/set_glitcher?state=dump_full_flash"
curl -X POST "http://swd.local/set_glitcher?state=dump_full_uicr"
```

Pliki są zapisywane w pamięci SPIFFS ESP32 jako:

- `/full_flash.bin`,
- `/full_uicr.bin`.

Można je pobrać z interfejsu edytora plików dostępnego pod
`http://swd.local/edit`.

Zrzut fragmentu pamięci do pliku na ESP32 oraz pobranie go bezpośrednio:

```bash
curl -X POST "http://swd.local/flash_cmd?cmd=dump_flash&file=file_dump.bin&offset=0&size=100"
curl "http://swd.local/download_flash?offset=0&len=100" --output flash.bin
```

Adresy i rozmiary podawane w parametrach API są wartościami szesnastkowymi.

### Przywracanie firmware

Pliki z katalogu [`dumps/`](dumps/) są wgrane bezpośrednio z dysku komputera
do nRF52. Nie trzeba wcześniej kopiować ich do pamięci SPIFFS ESP32.

#### Z przeglądarki

W sekcji **Flash** interfejsu `http://swd.local/` znajduje się formularz
**Flash Uploaded File**:

1. W polu **Offset 0x** wpisz `0` dla [`dumps/factory/full_flash.bin`](dumps/factory/full_flash.bin).
2. Wybierz plik `dumps/factory/full_flash.bin` na dysku.
3. Kliknij **Submit** lub przycisk wgrywania formularza.
4. Aby przywrócić UICR, ponownie użyj formularza i wpisz offset
   `10001000`, wybierając [`dumps/factory/full_uicr.bin`](dumps/factory/full_uicr.bin).

Offset adresowy UICR jest podany w szesnastkowym zapisie bez prefiksu `0x`.

#### Z wiersza polecenia na Linuxie


Do pełnego przywrócenia archiwum można najpierw wykonać kasowanie całej pamięci, następnie wgraj kolejno oba pliki z dysku:

```bash
curl -X POST "http://swd.local/set_swd?cmd=init"
curl -X POST "http://swd.local/set_swd?cmd=erase_all"
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@dumps/factory/full_flash.bin" http://swd.local/flash_file_direct
curl -F "flash_up_file_offset=10001000" -F "flash_file_direct=@dumps/factory/full_uicr.bin" http://swd.local/flash_file_direct
curl -X POST "http://swd.local/set_swd?cmd=set_reset"
```

> [!WARNING]
> Kasowanie i wgrywanie firmware zmieniają zawartość pamięci nRF52 i są
> operacjami destrukcyjnymi. Przed ich wykonaniem upewnij się, że plik,
> offset i docelowy układ pamięci są poprawne. Nie kasuj ani nie wgrywaj UICR,
> jeśli nie masz pewności, że taki UICR jest przeznaczony dla tej płytki.

## Testowanie firmware

Każdy projekt firmware powinien rozdzielać logikę testowalną na komputerze od
integracji ze sprzętem. Zalecane jest stosowanie niżej opisanej piramidy testów;
nie trzeba tworzyć wszystkiego naraz, ale nowa funkcja niepowiązana bezpośrednio
ze sprzętem powinna mieć test hostowy.

### Przygotowanie środowisk testowych

Dodaj do `platformio.ini` każdego projektu środowiska hostowe, oddzielnie dla
Windows i Linuxa:

```ini
[env:host-test-windows]
platform = windows_x86
test_framework = unity
build_flags = -std=gnu++11

[env:host-test-linux]
platform = linux_x86_64
test_framework = unity
build_flags = -std=gnu++11
```

W projektach testowych umieść Unity testy pod `test/<nazwa-testów>/`, a logikę
bez zależności od Arduino i nRF52 wydziel do `lib/` lub osobnego modułu. Hostowe
środowisko powinno kompilować tę czystą logikę i testy, bez dołączania szkicu
firmware i kodu sprzętowego.

1. **Logika hostowa** — wydziel czystą logikę do biblioteki lub modułu bez
   zależności od Arduino, rejestrów nRF52 i pinów. Testy Unity uruchamiaj w
   środowisku `host-test-windows` lub `host-test-linux`, zależnie od systemu.
2. **Kompilacja firmware** — po zmianach zbuduj właściwe środowisko projektu.
   Zielony build potwierdza zależności i linkowanie, ale nie potwierdza działania
   radio, GPIO ani timerów na płytce.
3. **Integracja sprzętowa** — po wgraniu przez ESP32/SWD zresetuj nRF52 i
   obserwuj konkretne zachowanie: LED, przyciski, komunikację BLE, pomiary czy
   inne interfejsy. HTTP 200 z ESP32 potwierdza tylko transfer, a nie działanie
   firmware.
4. **Testy przyszłych wariantów** — dla każdego nowego projektu utwórz własne
   przypadki integracyjne i dopisz wynik do README lub TODO. Dla testów tworzących
   stan powtarzalny należy podać kroki wejściowe, oczekiwany rezultat i sposób
   przywrócenia płytki do stanu startowego.

Testy hostowe powinny obejmować stan, przejścia i przypadki brzegowe bez sprzętu.
Testy sprzętowe powinny pozostawać krótkimi procedurami obserwacyjnymi i nie
powinny zastępować testów czystej logiki.

## Test mapowania sprzętu

Skrypt [`tools/hardware_test.py`](tools/hardware_test.py) pozwala interaktywnie
zweryfikować diody, przyciski i potencjalne piny buzzera przez rejestry nRF52:

```bash
python tools/hardware_test.py --host http://swd.local --duration 0.5
```

### Dostępne opcje

- `--led-only` — test pinów P0.17, P0.18 i P0.19;
- `--button-only` — test pinów P0.13 i P0.14;
- `--buzzer-only` — test wskazanych pinów buzzera;
- `--buzzer-pins 5,6` — potwierdzone piny różnicowe buzzera P0.05 i P0.06;
- `--output mapping.json` — zapis wyniku testu do pliku JSON.

## Planowane prace

Bieżąca lista zadań, znanych ograniczeń i kierunków dalszych badań znajduje się
w [`TODO.md`](TODO.md). Priorytetem jest poszerzenie testów umożliwiających
namierzenie pinów akcelerometru LIS2DH.

## Archiwum fabrycznego firmware

Poniższe pliki to pełne odczyty pamięci wykonane przez ESP32 i interfejs SWD:

| Plik | Zawartość | Rozmiar | SHA-256 |
|---|---|---:|---|
| [`dumps/factory/full_flash.bin`](dumps/factory/full_flash.bin) | Pełna pamięć flash | 512 KiB | `ec3060bb5d8160296f1891a2d4d2db7882535f80779dd6fe611bf300a475d826` |
| [`dumps/factory/full_uicr.bin`](dumps/factory/full_uicr.bin) | UICR | 4 KiB | `8cf25c59ad391780435765317039d2256cc618ff036a3c0847033c8d593e13dd` |
