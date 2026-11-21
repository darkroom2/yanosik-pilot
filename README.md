# Yanosik Pilot

## Windows USB setup

If Windows shows `CP2102 USB to UART Bridge Controller` with an error or does not assign a `COM` port, install the official CP210x Universal Windows Driver v11.6.0.

Open PowerShell as administrator and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\tools\install-cp210x-driver.ps1
```

Jeśli serwer Silicon Labs zwróci błąd `Access Denied`, pobierz ZIP
`CP210x_Universal_Windows_Driver.zip` ręcznie ze strony Silicon Labs, a następnie uruchom:

```powershell
.\tools\install-cp210x-driver.ps1 -ZipPath "$env:USERPROFILE\Downloads\CP210x_Universal_Windows_Driver.zip"
```

Then connect or reconnect the ESP32 and verify the USB port:

```powershell
uv run pio device list
```

Upload the stock ESP32_nRF52_SWD firmware from the repository directory:

```powershell
uv run pio run --project-dir tools/ESP32_nRF52_SWD -e ESP32_nRF52_SWD -t upload --upload-port COM3
```

Replace `COM3` with the port reported by `uv run pio device list`.

## Podłączenie programatora ESP32 do płytki pilota

Złącze programatora nie ma podpisanych pinów. Znana jest jedynie kolejność:
ostatni pin ma numer **4** i jest to **GND**. Piny numeruj od tego samego początku
złącza i nie odwracaj jego orientacji:

| Numer pinu złącza | Sygnał nRF52 | Pin ESP32 LILYGO T5 V2.3.1 |
|---|---|---|
| 1 | SWDCLK | GPIO 21 (`21`) |
| 2 | SWDIO | GPIO 19 (`19`) |
| 3 | VDD 3.3 V | `3V3` |
| 4 | GND | `GND` |

Podłącz także wspólną masę z pinu 4 do ESP32 `GND`.

- Zasilanie 3.3 V z pinu 3 podłączaj tylko wtedy, gdy płytka nRF52 nie ma
  własnego zasilania, np. baterii.
- Jeśli nRF52 jest zasilany osobno, pozostaw pin 3 złącza nRF52 niepodłączony.
- Nie podłączaj 5 V ani innych napięć większych niż 3.3 V do płytki ESP32.
