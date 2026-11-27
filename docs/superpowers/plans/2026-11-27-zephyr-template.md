# Zephyr Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Przerobić `firmware/zephyr-template` na gotowy do skopiowania, minimalny szablon aplikacji Zephyr dla nRF52832/nRF52 DK.

**Architecture:** Projekt pozostaje projektem PlatformIO z frameworkiem Zephyr; źródło C używa publicznych API Zephyr, konfigurację RTT trzyma `zephyr/prj.conf`, a sprzętowe aliasy/piny można dodać przez lokalny overlay DTS. Szablon ma uruchamiać jeden przewidywalny przykładowy przebieg (logowanie + miganie LED) bez Bluetooth ani konkretnego peryferium.

**Tech Stack:** PlatformIO, Nordic nRF52 Zephyr, C, Zephyr kernel/gpio/logging API, Python 3/unittest tests, SEGGER RTT.

**Spec:** Zatwierdzony ustnie zakres użytkownika z 2026-11-27: czysty, ogólny szablon gotowy do kopiowania, bez logiki konkretnego urządzenia, z minimalnym cyklem, RTT, poprawnym CMake i PlatformIO oraz README build/flash.

## Global Constraints

- Projekt musi zachować środowisko PlatformIO `nrf52_dk`.
- Framework musi pozostać `zephyr`.
- Wynik firmware musi generować `zephyr/zephyr.bin` przez istniejący skrypt post-build.
- Szablon nie może zależeć od Bluetooth ani nazwy/bloku BLE.
- Diagnostykę podstawową należy prowadzić przez SEGGER RTT.
- Projekt powinien używać aliasu LED z Device Tree, nie wpisanego numeru portu P0 jako jedynego sposobu sterowania.

## Review Focus

- Kopiowanie katalogu pod inną nazwę nie pozostawia nazwy starego projektu w CMake ani logach. Test: nazwa CMake i moduł logowania nie zawierają `ble_zephyr`.
- Konfiguracja RTT nadal działa po usunięciu ustawień UART. Test: `prj.conf` ma włączone konsolę RTT i wyłączony UART console.
- LED wykrywa brak urządzenia GPIO bez zawieszania builda. Test: `main.c` sprawdza `DEVICE_DT_GET(DT_ALIAS(led0))` i `device_is_ready(...)`.
- Wynik builda pozostaje zgodny z ESP32/SWD workflow. Test: `platformio.ini` i `post_build_bin.py` są obecne i kompletne.

---

### Task 1: Ustalić testy kontraktu szablonu

**Files:**
- Create: `tools/tests/test_zephyr_template_project.py`

**Interfaces:**
- Consumes: pliki projektu `firmware/zephyr-template`.
- Produces: testy unittest/pytest sprawdzające kod źródłowy, CMake, konfigurację i skrypt builda.

- [ ] **Step 1: Dodać testy, które wymagają ogólnej nazwy projektu i LED/RTT startera**

```python
class ZephyrTemplateProject(unittest.TestCase):
    def test_cmake_has_generic_project_name_and_template_source(self): ...
    def test_application_uses_led_alias_and_rtt_logging(self): ...
    def test_configuration_enables_rtt_and_disables_uart_console(self): ...
    def test_project_keeps_post_build_bin_workflow(self): ...
```

- [ ] **Step 2: Uruchomić test i potwierdzić, że obecny szablon go nie spełnia**

Run: `uv run pytest tools/tests/test_zephyr_template_project.py -q`

Expected: co najmniej test nazwy CMake i test aplikacji LED/RTT fail.

### Task 2: Ulepszyć aplikację i konfigurację Zephyr

**Files:**
- Modify: `firmware/zephyr-template/src/main.c`
- Modify: `firmware/zephyr-template/zephyr/CMakeLists.txt`
- Modify: `firmware/zephyr-template/zephyr/prj.conf`

**Interfaces:**
- Produces: `main(void)` z poprawnym `return`, sprawdzeniem GPIO i zatrzymaniem na błędzie gotowości LED.
- Produces: CMake project name `zephyr_template`, który jest neutralny i nie sugeruje BLE.
- Produces: RTT jako jedyne używane wejście/wyjście konsoli, bez zależności od UART.

- [ ] **Step 1: Zastąpić zawartość `main.c` neutralnym starterem**

Podać exact API: `#include <zephyr/kernel.h>`, `<zephyr/drivers/gpio.h>`, `<zephyr/logging/log.h>`, `LOG_MODULE_REGISTER(template, LOG_LEVEL_INF)`, `DEVICE_DT_GET(DT_ALIAS(led0))`, `GPIO_OUTPUT_ACTIVE`, `gpio_pin_toggle`, `k_sleep(K_SECONDS(1))`.

- [ ] **Step 2: Ustawić neutralną nazwę projektu w CMake**

W `firmware/zephyr-template/zephyr/CMakeLists.txt` ustawić `project(zephyr_template)`.

- [ ] **Step 3: Zachować/doprecyzować konfigurację RTT**

Usunąć identyfikatory BLE z konfiguracji i zachować:
`CONFIG_SERIAL=n`, `CONFIG_UART_CONSOLE=n`, `CONFIG_CONSOLE=y`,
`CONFIG_USE_SEGGER_RTT=y`, `CONFIG_RTT_CONSOLE=y`, `CONFIG_LOG=y`,
`CONFIG_LOG_BACKEND_RTT=y`, `CONFIG_NRF_APPROTECT_USE_UICR=y`,
`CONFIG_NRF_APPROTECT_LOCK=n`.

- [ ] **Step 4: Uruchomić testy i potwierdzić przejście**

Run: `uv run pytest tools/tests/test_zephyr_template_project.py -q`

Expected: wszystkie testy szablonu PASS.

### Task 3: Dodać instrukcje kopiowania i dokumentację projektu

**Files:**
- Modify: `README.md`

**Interfaces:**
- Produces: nowa sekcja `firmware/zephyr-template` pod `Budowanie i wgrywanie projektów firmware`.

- [ ] **Step 1: Opisać cel szablonu i zachowanie startowe**

Zanotować, że starter jest neutralnym przykładem: loguje przez RTT i miga LED0 nRF52 DK co 1 sekundę.

- [ ] **Step 2: Dodać build i flash przez ESP32/SWD**

Umieścić komendę:
`uv run pio run --project-dir firmware\zephyr-template -e nrf52_dk`

Wskazać wynik:
`firmware/zephyr-template/.pio/build/nrf52_dk/zephyr/zephyr.bin`

Zachować kolejność `init`, `erase_all`, `flash_file_direct`, `set_reset` zgodną z innymi projektami Zephyr.

- [ ] **Step 3: Opisać kopiowanie i pierwszą zmianę**

Wprost napisać, że po skopiowaniu należy zmienić nazwę katalogu i wartość `project(...)`, a następnie dodać własne pliki do `target_sources(app PRIVATE ...)`.

- [ ] **Step 4: Potwierdzić obecność sekcji**

Run: `uv run pytest tools/tests/test_zephyr_template_project.py -q`

Expected: testy przechodzą; README ma sekcję szablonu i instrukcje.
