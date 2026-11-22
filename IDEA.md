# Pomysł projektu

Pilot Yanosik ma zostać przekształcony w bezprzewodowy przycisk sterujący
urządzeniami w Home Assistant. Do komunikacji ma być wykorzystywany nRF52832
oraz protokół BTHome.

## Najważniejsze wymagania

- Zachować oryginalne firmware i UICR pilota, aby możliwy był powrót do stanu
  fabrycznego.
- Wykorzystać istniejący nRF52832, przyciski, diody, buzzer oraz akcelerometr
  LIS2DH.
- Zidentyfikować pozostałe nieznane elementy płytki oraz ich połączenia.
- Przesłać zdarzenia przycisków do Home Assistant przez BTHome.
- Wprowadzić czytelną sygnalizację stanów i błędów diodami oraz buzzerem.
- Traktować odblokowanie, kasowanie i programowanie pamięci jako operacje
  wymagające świadomego potwierdzenia.

## Zakres prac

1. Uwierzytelnić i zabezpieczyć pełną kopię pamięci fabrycznej.
2. Zidentyfikować pinout przycisków, diod, buzzera i akcelerometru.
3. Ustalić logikę zdarzeń przycisków:
   - pojedyncze kliknięcie,
   - podwójne kliknięcie,
   - przytrzymanie,
   - reakcje diod i buzzera.
4. Przygotować oprogramowanie nRF52832 w środowisku VS Code i PlatformIO.
5. Włączyć transmisję danych przez BTHome do Home Assistant.
6. Usunąć blokadę pamięci APPROTECT, zaprogramować płytkę i przeprowadzić testy.
7. Zachować możliwość przywrócenia oryginalnych danych z archiwum.

## Wykorzystanie akcelerometru (LIS2DH)

Wbudowany 3-osiowy akcelerometr **LIS2DH** pozwala rozszerzyć funkcje pilota
poza same przyciski oraz znacząco ograniczyć zużycie energii:

- **Oszczędzanie energii (Wake-on-Motion)** – usypianie nRF52832 w głębokim śnie
  i wybudzanie przerwaniem z LIS2DH po wykryciu ruchu lub podniesienia pilota,
  co wydłuża czas pracy na baterii CR2450.
- **Dodatkowe gesty (Shake / Tap)** – rozpoznawanie potrząśnięcia lub
  stuknięcia jako osobnych zdarzeń BTHome w Home Assistant (np. tryb nocny lub
  „wyłącz wszystko”).
- **Wykrywanie orientacji (Flip / Tilt)** – odwrócenie pilota do góry nogami
  jako szybkie wyciszenie lub przełączenie trybu pracy.
- **Zdarzenie ruchu w Home Assistant** – wysyłanie informacji o poruszeniu
  pilota jako wyzwalacza do automatyzacji (np. obecność lub zabranie pilota).

## Wybrany sprzęt i narzędzia

- Mikrokontroler: Nordic nRF52832 w obudowie QFN48.
- Programator: ESP32 NodeMCU + MOSFET N-channel i projekt `ESP32_nRF52_SWD`.
- Środowisko: VS Code, PlatformIO CLI i Python.

Szczegółowy opis sprzętu znajduje się w [README.md](README.md). Instrukcje
programowania, kopii zapasowej i przywracania firmware są również opisane
w `README.md`.
