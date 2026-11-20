param(
    [string]$DownloadUrl = "https://www.silabs.com/documents/public/software/CP210x_Universal_Windows_Driver.zip",
    [string]$ZipPath,
    [switch]$NoReboot
)

$ErrorActionPreference = "Stop"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Uruchom ten skrypt w PowerShell z uprawnieniami administratora."
    }
}

Assert-Administrator

if (-not $NoReboot) {
    Write-Host "Instalacja sterownika CP210x Universal Windows v11.6.0."
}

$tempDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ("cp210x-driver-" + [guid]::NewGuid().ToString("N"))
$downloadedZipPath = Join-Path $tempDirectory "CP210x_Universal_Windows_Driver.zip"

try {
    New-Item -ItemType Directory -Path $tempDirectory -Force | Out-Null

    if ($ZipPath) {
        $zipPath = (Resolve-Path -LiteralPath $ZipPath -ErrorAction Stop).Path
    } else {
        $zipPath = $downloadedZipPath
        try {
            $headers = @{
                "accept" = "text/html,application/xhtml+xml,application/xml;q=0.9,image/jxl,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
                "accept-language" = "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
                "cache-control" = "no-cache"
                "pragma" = "no-cache"
                "priority" = "u=0, i"
                "sec-ch-ua" = "`"Not-A.Brand`";v=`"99`", `"Google Chrome`";v=`"157`", `"Chromium`";v=`"157`""
                "sec-ch-ua-mobile" = "?0"
                "sec-ch-ua-platform" = "`"Windows`""
                "sec-fetch-dest" = "document"
                "sec-fetch-mode" = "navigate"
                "sec-fetch-site" = "none"
                "sec-fetch-user" = "?1"
                "upgrade-insecure-requests" = "1"
            }
            $userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36"
            Invoke-WebRequest -UseBasicParsing -Uri $DownloadUrl -Headers $headers -UserAgent $userAgent -OutFile $zipPath
        } catch {
            throw "Pobranie sterownika zostalo zablokowane przez serwer Silicon Labs (HTTP 403/Access Denied). Pobierz ZIP recznie ze strony i uruchom skrypt ponownie z parametrem -ZipPath C:\sciezka\CP210x_Universal_Windows_Driver.zip"
        }
    }

    if (-not (Test-Path -LiteralPath $zipPath -PathType Leaf)) {
        throw "Nie znaleziono archiwum ZIP: $zipPath"
    }

    Expand-Archive -LiteralPath $zipPath -DestinationPath $tempDirectory -Force

    $wantedArchitecture = if ([Environment]::Is64BitOperatingSystem) { "x64" } else { "x86" }
    $installer = Get-ChildItem -Path $tempDirectory -Filter "CP210xVCPInstaller_$wantedArchitecture.exe" -Recurse |
        Select-Object -First 1

    if (-not $installer) {
        $installer = Get-ChildItem -Path $tempDirectory -Filter "DPInst_$wantedArchitecture.exe" -Recurse |
            Select-Object -First 1
    }

    if ($installer) {
        Write-Host "Uruchamiam instalator: $($installer.FullName)"
        $process = Start-Process -FilePath $installer.FullName -Wait -PassThru
        if ($process.ExitCode -ne 0) {
            throw "Instalator zakonczyl sie kodem $($process.ExitCode)."
        }
    } else {
        $infFiles = Get-ChildItem -Path $tempDirectory -Filter "*.inf" -Recurse |
            Where-Object { $_.Name -match 'CP210|silab|slab' }

        if (-not $infFiles) {
            throw "Nie znaleziono instalatora ani pliku INF CP210x w pobranym archiwum."
        }

        foreach ($infFile in $infFiles) {
            Write-Host "Instaluje $($infFile.FullName)"
            & pnputil.exe /add-driver $infFile.FullName /install
            if ($LASTEXITCODE -ne 0) {
                throw "pnputil nie udal sie dla $($infFile.Name), kod $LASTEXITCODE."
            }
        }
    }

    pnputil.exe /scan-devices | Out-Host

    $device = Get-PnpDevice -PresentOnly |
        Where-Object { $_.InstanceId -match 'USB\\VID_10C4&PID_EA60' } |
        Select-Object -First 1

    if ($device) {
        Write-Host "Znaleziono urzadzenie: $($device.FriendlyName) - $($device.Status)"
    } else {
        Write-Host "Plytka nie jest obecnie widoczna. Podlacz lub odpolacz USB i sprawdz ponownie."
    }
}
finally {
    Remove-Item -LiteralPath $tempDirectory -Recurse -Force -ErrorAction SilentlyContinue
}
