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
- [Firmware blinker](#firmware-blinker)
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

### Zidentyfikowane piny

| Fizyczny pin | Port nRF52 | Podłączony element |
|---|---|---|
| 16 | P0.13 | Przycisk nr 1; styk zwiera do masy, wejście `INPUT_PULLUP` |
| 17 | P0.14 | Przycisk nr 2; styk zwiera do masy, wejście `INPUT_PULLUP` |
| 20 | P0.17 | Czerwona dioda LED, rezystor 510 Ω; anoda wspólna, świeci przy stanie niski |
| 21 | P0.18 | Zielony kanał diody RGB, rezystor 100 Ω; anoda wspólna, świeci przy stanie niski |
| 22 | P0.19 | Niebieski kanał diody RGB, rezystor 100 Ω; anoda wspólna, świeci przy stanie niski |

### Elementy wymagające dalszej identyfikacji

- Nie zidentyfikowano jeszcze podłączeń pinów buzzera i układu podbijającego
  napięcie.
- Nie zidentyfikowano jeszcze podłączeń akcelerometru LIS2DH, w tym magistrali
  komunikacyjnej i sygnału wybudzenia.
- Nie potwierdzono ostatecznej funkcji fizycznych pinów przycisków poza ich
  przypisaniem do P0.13 i P0.14.

## Przygotowanie środowiska

Na Linuxie podłącz ESP32 przez USB i sprawdź wykryte urządzenia:

```bash
uv run pio device list
```

Wgraj firmware ESP32_nRF52_SWD z katalogu repozytorium:

```bash
uv run pio run --project-dir tools/ESP32_nRF52_SWD -e ESP32_nRF52_SWD -t upload
```

### Alternatywa dla Windows

Na Windows wgrywanie zwykle wymaga wskazania portu COM:

```powershell
uv run pio run --project-dir tools/ESP32_nRF52_SWD -e ESP32_nRF52_SWD -t upload --upload-port COM3
```

Zastąp `COM3` portem zwróconym przez `uv run pio device list`.

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

| Numer pinu złącza | Sygnał nRF52 | Pin ESP32 LILYGO T5 V2.3.1 |
|---|---|---|
| 1 | SWDCLK | GPIO 21 (`21`) |
| 2 | SWDIO | GPIO 19 (`19`) |
| 3 | VDD 3.3 V | `3V3` |
| 4 | GND | `GND` |

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

Środowisko `nrf52_dk` w `firmware/blinker/platformio.ini` służy do kompilacji
firmware i wyboru wariantu Arduino. Nie oznacza, że do komputera jest podłączona
płytka Nordic nRF52-DK. Standardowe `pio run -t upload` dla tego środowiska
oczekuje programatora J-Link; do wgrania firmware na pilot użyj ESP32/SWD.

Po zbudowaniu szkicu Blinker wgraj plik HEX przez istniejące API ESP32:

```bash
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@firmware/blinker/.pio/build/nrf52_dk/firmware.hex" http://swd.local/flash_file_direct
```

Po wgraniu zresetuj nRF52 przez ESP32/SWD przed testem sprzętowym:

```bash
curl -X POST "http://swd.local/set_swd?cmd=set_reset"
```

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

1. W polu **Offset 0x** wpisz `0` dla [`dumps/full_flash.bin`](dumps/full_flash.bin).
2. Wybierz plik `dumps/full_flash.bin` na dysku.
3. Kliknij **Submit** lub przycisk wgrywania formularza.
4. Aby przywrócić UICR, ponownie użyj formularza i wpisz offset
   `10001000`, wybierając [`dumps/full_uicr.bin`](dumps/full_uicr.bin).

Offset adresowy UICR jest podany w szesnastkowym zapisie bez prefiksu `0x`.

#### Z wiersza polecenia na Linuxie

Najpierw przejdź do katalogu repozytorium, a następnie wyślij plik bezpośrednio
do ESP32:

```bash
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@dumps/full_flash.bin" http://swd.local/flash_file_direct
```

UICR należy wgrać osobno pod offsetem `0x10001000`:

```bash
curl -F "flash_up_file_offset=10001000" -F "flash_file_direct=@dumps/full_uicr.bin" http://swd.local/flash_file_direct
```

Możesz sprawdzić postęp i stan połączenia przez:

```bash
curl "http://swd.local/get_state"
```

Do pełnego przywrócenia archiwum można najpierw wykonać kasowanie całej pamięci:

```bash
curl -X POST "http://swd.local/flash_cmd?cmd=erase_all"
```

Następnie wgraj kolejno oba pliki z dysku:

```bash
curl -F "flash_up_file_offset=0" -F "flash_file_direct=@dumps/full_flash.bin" http://swd.local/flash_file_direct
curl -F "flash_up_file_offset=10001000" -F "flash_file_direct=@dumps/full_uicr.bin" http://swd.local/flash_file_direct
```

> [!WARNING]
> Kasowanie i wgrywanie firmware zmieniają zawartość pamięci nRF52 i są
> operacjami destrukcyjnymi. Przed ich wykonaniem upewnij się, że plik,
> offset i docelowy układ pamięci są poprawne. Nie kasuj ani nie wgrywaj UICR,
> jeśli nie masz pewności, że taki UICR jest przeznaczony dla tej płytki.

## Firmware blinker

Prosty szkic do testowania LED RGB i przycisków:

- LED miga początkowo na czerwono;
- przycisk 1 zmienia kolor w kolejności czerwony → zielony → niebieski;
- przycisk 2 zatrzymuje miganie (LED gaśnie) i wznawia je w wybranym kolorze.

Wariant Arduino `nRF52DK` używa numerów cyfrowych pinów, które odpowiadają
poniższym portom nRF52:

| Funkcja | Port nRF52 | Pin Arduino |
|---|---|---|
| Przycisk zmiany koloru | P0.13 | D2 |
| Przycisk pauzy | P0.14 | D3 |
| Czerwony kanał LED | P0.17 | D6 |
| Zielony kanał LED | P0.18 | D7 |
| Niebieski kanał LED | P0.19 | D8 |

Zbuduj firmware:

```powershell
uv run pio run --project-dir firmware\blinker -e nrf52_dk
```

Plik wynikowy to `firmware\blinker\.pio\build\nrf52_dk\firmware.hex`.
Wgraj go przez istniejący programator ESP32/SWD; standardowy upload PlatformIO
dla `nrf52_dk` oczekuje programatora J-Link.

Logikę przycisków, debounce i migania można testować na komputerze bez płytki:

```powershell
uv run pio test --project-dir firmware\blinker -e host-test-windows
```

Na Linuxie uruchom:

```bash
uv run pio test --project-dir firmware/blinker -e host-test-linux
```

Testy hostowe nie sprawdzają fizycznego mapowania pinów ani działania LED na
płytce.

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
- `--buzzer-pins 15,16,20,24,25,31` — lista pinów testowanych w trybie buzzera;
- `--output mapping.json` — zapis wyniku testu do pliku JSON.

## Planowane prace

Bieżąca lista zadań, znanych ograniczeń i kierunków dalszych badań znajduje się
w [`TODO.md`](TODO.md). Priorytetem jest poszerzenie testów umożliwiających
namierzenie pinów akcelerometru LIS2DH.

## Archiwum fabrycznego firmware

Poniższe pliki to pełne odczyty pamięci wykonane przez ESP32 i interfejs SWD:

| Plik | Zawartość | Rozmiar | SHA-256 |
|---|---|---:|---|
| [`dumps/full_flash.bin`](dumps/full_flash.bin) | Pełna pamięć flash | 512 KiB | `ec3060bb5d8160296f1891a2d4d2db7882535f80779dd6fe611bf300a475d826` |
| [`dumps/full_uicr.bin`](dumps/full_uicr.bin) | UICR | 4 KiB | `8cf25c59ad391780435765317039d2256cc618ff036a3c0847033c8d593e13dd` |
