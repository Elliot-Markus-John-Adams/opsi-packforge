# OPSI PackForge - Einfacher Installer
# Minimale Version mit Benutzer-Interaktion

Clear-Host
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  OPSI PackForge - Simple Installer" -ForegroundColor Cyan  
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1] Installation starten" -ForegroundColor Yellow
Write-Host "[2] Test-Modus" -ForegroundColor Yellow
Write-Host "[3] Hilfe" -ForegroundColor Yellow
Write-Host "[4] Beenden" -ForegroundColor Yellow
Write-Host ""

$choice = Read-Host "Bitte waehlen Sie eine Option (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Installation wird gestartet..." -ForegroundColor Green
        Write-Host ""
        
        # Schritt 1
        Write-Host "Schritt 1: Erstelle Verzeichnis..." -ForegroundColor Yellow
        $installPath = "$env:LOCALAPPDATA\OPSI-PackForge"
        New-Item -ItemType Directory -Path $installPath -Force | Out-Null
        Write-Host "OK - Verzeichnis erstellt: $installPath" -ForegroundColor Green
        Write-Host ""
        
        # Schritt 2
        Write-Host "Schritt 2: Lade Python herunter..." -ForegroundColor Yellow
        Write-Host "Dies kann einige Minuten dauern..." -ForegroundColor Gray
        
        try {
            $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
            $pythonZip = "$env:TEMP\python.zip"
            
            # Proxy-Support
            [System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials
            $client = New-Object System.Net.WebClient
            $client.Proxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials
            $client.DownloadFile($pythonUrl, $pythonZip)
            
            Write-Host "OK - Python heruntergeladen" -ForegroundColor Green
            Write-Host ""
            
            # Schritt 3
            Write-Host "Schritt 3: Entpacke Python..." -ForegroundColor Yellow
            Expand-Archive -Path $pythonZip -DestinationPath "$installPath\python" -Force
            Remove-Item $pythonZip
            
            # Python konfigurieren für tkinter
            $pthFile = "$installPath\python\python311._pth"
            if (Test-Path $pthFile) {
                $content = Get-Content $pthFile
                $content = $content -replace "#import site", "import site"
                Set-Content -Path $pthFile -Value $content
            }
            
            Write-Host "OK - Python installiert" -ForegroundColor Green
            Write-Host ""
            
            # Schritt 4
            Write-Host "Schritt 4: Erstelle OPSI PackForge..." -ForegroundColor Yellow
            $appPath = "$installPath\app"
            New-Item -ItemType Directory -Path $appPath -Force | Out-Null
            
            # Erstelle ein einfaches Batch-Script als GUI-Alternative
            $batchScript = @'
@echo off
title OPSI PackForge v1.0
color 0A

:menu
cls
echo.
echo =====================================
echo       OPSI PackForge v1.0
echo =====================================
echo.
echo [1] Neues Paket erstellen
echo [2] Hilfe
echo [3] Beenden
echo.
set /p choice="Ihre Wahl: "

if "%choice%"=="1" goto create
if "%choice%"=="2" goto help
if "%choice%"=="3" exit
goto menu

:create
cls
echo.
echo === NEUES OPSI-PAKET ERSTELLEN ===
echo.
set /p pkgid="Paket-ID (z.B. firefox): "
set /p pkgname="Paket-Name: "
set /p pkgversion="Version (z.B. 1.0.0): "
set /p output="Ausgabe-Ordner (Enter fuer Desktop): "

if "%output%"=="" set output=%USERPROFILE%\Desktop

set pkgdir=%output%\%pkgid%_%pkgversion%

echo.
echo Erstelle Paket-Struktur...
mkdir "%pkgdir%\OPSI" 2>nul
mkdir "%pkgdir%\CLIENT_DATA" 2>nul

echo [Product] > "%pkgdir%\OPSI\control"
echo type: localboot >> "%pkgdir%\OPSI\control"
echo id: %pkgid% >> "%pkgdir%\OPSI\control"
echo name: %pkgname% >> "%pkgdir%\OPSI\control"
echo version: %pkgversion% >> "%pkgdir%\OPSI\control"
echo priority: 0 >> "%pkgdir%\OPSI\control"
echo licenseRequired: False >> "%pkgdir%\OPSI\control"
echo setupScript: setup.opsiscript >> "%pkgdir%\OPSI\control"

echo ; Setup script for %pkgname% > "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo [Actions] >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo Message "Installing %pkgname% %pkgversion%" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"

echo.
echo ===================================
echo PAKET ERFOLGREICH ERSTELLT!
echo ===================================
echo.
echo Paket-Verzeichnis:
echo %pkgdir%
echo.
pause
goto menu

:help
cls
echo.
echo === HILFE ===
echo.
echo OPSI PackForge erstellt OPSI-Paket-Strukturen
echo fuer die paedML Linux Umgebung.
echo.
echo Erstellt:
echo - OPSI/control Datei
echo - CLIENT_DATA/setup.opsiscript
echo.
pause
goto menu
'@
            
            $batchScript | Out-File -FilePath "$appPath\opsi_packforge.bat" -Encoding ASCII
            Write-Host "OK - Anwendung erstellt" -ForegroundColor Green
            Write-Host ""
            
            # Schritt 5
            Write-Host "Schritt 5: Erstelle Desktop-Verknuepfung..." -ForegroundColor Yellow
            try {
                $desktopPath = [Environment]::GetFolderPath("Desktop")
                if (-not $desktopPath) {
                    $desktopPath = "$env:USERPROFILE\Desktop"
                }
                
                $WshShell = New-Object -ComObject WScript.Shell
                $Shortcut = $WshShell.CreateShortcut("$desktopPath\OPSI PackForge.lnk")
                $Shortcut.TargetPath = "$appPath\opsi_packforge.bat"
                $Shortcut.WorkingDirectory = $appPath
                $Shortcut.Description = "OPSI PackForge"
                $Shortcut.Save()
                Write-Host "OK - Desktop-Verknuepfung erstellt" -ForegroundColor Green
            } catch {
                Write-Host "WARNUNG: Desktop-Verknuepfung konnte nicht erstellt werden" -ForegroundColor Yellow
                Write-Host "         Starten Sie die Anwendung manuell:" -ForegroundColor Yellow
                Write-Host "         $appPath\opsi_packforge.bat" -ForegroundColor Cyan
            }
            Write-Host ""
            
            Write-Host "Installation abgeschlossen!" -ForegroundColor Green
            Write-Host "Installiert in: $installPath" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Starten mit:" -ForegroundColor Yellow
            Write-Host "- Desktop-Verknuepfung 'OPSI PackForge'" -ForegroundColor White
            Write-Host "- Oder direkt: $appPath\opsi_packforge.bat" -ForegroundColor White
            Write-Host ""
            
            $startNow = Read-Host "Moechten Sie OPSI PackForge jetzt starten? (J/N)"
            if ($startNow -eq "J" -or $startNow -eq "j") {
                Start-Process "$appPath\opsi_packforge.bat"
            }
            
        } catch {
            Write-Host "FEHLER: $_" -ForegroundColor Red
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "TEST-MODUS" -ForegroundColor Yellow
        Write-Host "----------" -ForegroundColor Yellow
        Write-Host "Wuerde folgende Aktionen ausfuehren:" -ForegroundColor White
        Write-Host "- Verzeichnis erstellen: $env:LOCALAPPDATA\OPSI-PackForge" -ForegroundColor Gray
        Write-Host "- Python herunterladen (15 MB)" -ForegroundColor Gray
        Write-Host "- GUI-Anwendung erstellen" -ForegroundColor Gray
        Write-Host ""
    }
    
    "3" {
        Write-Host ""
        Write-Host "HILFE" -ForegroundColor Yellow
        Write-Host "-----" -ForegroundColor Yellow
        Write-Host "Dieses Script installiert OPSI PackForge auf Ihrem System." -ForegroundColor White
        Write-Host ""
        Write-Host "Optionen:" -ForegroundColor White
        Write-Host "1 - Vollstaendige Installation" -ForegroundColor Gray
        Write-Host "2 - Test ohne echte Installation" -ForegroundColor Gray
        Write-Host "3 - Diese Hilfe" -ForegroundColor Gray
        Write-Host "4 - Beenden" -ForegroundColor Gray
        Write-Host ""
    }
    
    "4" {
        Write-Host "Beende..." -ForegroundColor Yellow
        exit
    }
    
    default {
        Write-Host "Ungueltige Auswahl!" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Druecken Sie eine beliebige Taste zum Beenden..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")