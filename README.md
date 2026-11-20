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

Upload firmware from the submodule directory:

```powershell
Set-Location .\ESP32_nRF52_SWD
uv run pio run -e ESP32_nRF52_SWD -t upload --upload-port COM3
```

Replace `COM3` with the port reported by `uv run pio device list`.
