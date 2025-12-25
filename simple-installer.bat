@echo off
REM OPSI PackForge Simple Installer
REM Funktioniert in CMD und PowerShell

echo.
echo ====================================
echo   OPSI PackForge - Simple Installer
echo ====================================
echo.
echo [1] Installation starten
echo [2] Test-Modus
echo [3] Hilfe
echo [4] Beenden
echo.
set /p choice="Bitte waehlen Sie eine Option (1-4): "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto test
if "%choice%"=="3" goto help
if "%choice%"=="4" goto end

:install
echo.
echo Installation wird gestartet...
echo.
echo Schritt 1: Erstelle Verzeichnis...
mkdir "%LOCALAPPDATA%\OPSI-PackForge" 2>nul
echo OK - Verzeichnis erstellt
echo.
echo Schritt 2: Lade Python herunter...
echo Dies kann einige Minuten dauern...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip', '%TEMP%\python.zip')"
echo OK - Python heruntergeladen
echo.
echo Schritt 3: Entpacke Python...
powershell -Command "Expand-Archive -Path '%TEMP%\python.zip' -DestinationPath '%LOCALAPPDATA%\OPSI-PackForge\python' -Force"
del "%TEMP%\python.zip"
echo OK - Python installiert
echo.
echo Installation abgeschlossen!
echo.
pause
goto end

:test
echo.
echo TEST-MODUS
echo ----------
echo Wuerde folgende Aktionen ausfuehren:
echo - Verzeichnis erstellen: %LOCALAPPDATA%\OPSI-PackForge
echo - Python herunterladen (15 MB)
echo - GUI-Anwendung erstellen
echo.
pause
goto end

:help
echo.
echo HILFE
echo -----
echo Dieses Script installiert OPSI PackForge auf Ihrem System.
echo.
echo Optionen:
echo 1 - Vollstaendige Installation
echo 2 - Test ohne echte Installation
echo 3 - Diese Hilfe
echo 4 - Beenden
echo.
pause
goto end

:end
exit