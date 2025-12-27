# OPSI PackForge - Einfacher Installer
# Prueft ob bereits installiert und startet direkt

$installPath = "$env:LOCALAPPDATA\OPSI-PackForge"
$appPath = "$installPath\app\opsi_packforge.bat"

# Pruefen ob bereits installiert
if (Test-Path $appPath) {
    Write-Host ""
    Write-Host "OPSI PackForge ist bereits installiert!" -ForegroundColor Green
    Write-Host "Starte Anwendung..." -ForegroundColor Yellow
    Write-Host ""
    Start-Process $appPath
    exit
}

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
if "%pkgversion%"=="" set pkgversion=1.0.0
set /p setupfile="Setup-Datei (Pfad oder Enter fuer spaeter): "
set /p silentparam="Silent-Parameter (z.B. /S oder /quiet): "
set /p output="Ausgabe-Ordner (Enter fuer Desktop): "

if "%output%"=="" set output=%USERPROFILE%\Desktop

set pkgdir=%output%\%pkgid%_%pkgversion%

echo.
echo Erstelle Paket-Struktur...
mkdir "%pkgdir%\OPSI" 2>nul
mkdir "%pkgdir%\CLIENT_DATA" 2>nul

REM Setup-Datei kopieren falls angegeben
if not "%setupfile%"=="" (
    if exist "%setupfile%" (
        echo Kopiere Setup-Datei...
        copy "%setupfile%" "%pkgdir%\CLIENT_DATA\" >nul
        for %%F in ("%setupfile%") do set setupfilename=%%~nxF
    ) else (
        echo WARNUNG: Setup-Datei nicht gefunden!
        set setupfilename=setup.exe
    )
) else (
    set setupfilename=setup.exe
)

REM Control-Datei erstellen
echo [Package] > "%pkgdir%\OPSI\control"
echo version: 1 >> "%pkgdir%\OPSI\control"
echo depends: >> "%pkgdir%\OPSI\control"
echo incremental: False >> "%pkgdir%\OPSI\control"
echo. >> "%pkgdir%\OPSI\control"
echo [Product] >> "%pkgdir%\OPSI\control"
echo type: localboot >> "%pkgdir%\OPSI\control"
echo id: %pkgid% >> "%pkgdir%\OPSI\control"
echo name: %pkgname% >> "%pkgdir%\OPSI\control"
echo description: %pkgname% Installation >> "%pkgdir%\OPSI\control"
echo advice: >> "%pkgdir%\OPSI\control"
echo version: %pkgversion% >> "%pkgdir%\OPSI\control"
echo priority: 0 >> "%pkgdir%\OPSI\control"
echo licenseRequired: False >> "%pkgdir%\OPSI\control"
echo productClasses: >> "%pkgdir%\OPSI\control"
echo setupScript: setup.opsiscript >> "%pkgdir%\OPSI\control"
echo uninstallScript: uninstall.opsiscript >> "%pkgdir%\OPSI\control"
echo updateScript: >> "%pkgdir%\OPSI\control"
echo alwaysScript: >> "%pkgdir%\OPSI\control"
echo onceScript: >> "%pkgdir%\OPSI\control"

REM Setup-Script erstellen
echo ; Setup script for %pkgname% > "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo ; Generated by OPSI PackForge >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo [Actions] >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo requiredWinstVersion ^>= "4.11.6" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo DefVar $SetupFile$ >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo DefVar $ProductId$ >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo DefVar $ExitCode$ >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo Set $ProductId$ = "%pkgid%" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo Set $SetupFile$ = "%%ScriptPath%%\%setupfilename%" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo Message "Installing " + $ProductId$ + " ..." >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo comment "Start setup program" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo ChangeDirectory "%%ScriptPath%%" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo Winbatch_install >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo Sub_check_exitcode >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo [Winbatch_install] >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo "$SetupFile$" %silentparam% >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo [Sub_check_exitcode] >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo set $ExitCode$ = getLastExitCode >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo if ($ExitCode$ = "0"^) >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo     comment "Setup successful" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo else >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo     logError "Setup failed with exit code: " + $ExitCode$ >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo     isFatalError >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo endif >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"

REM Uninstall-Script erstellen
echo ; Uninstall script for %pkgname% > "%pkgdir%\CLIENT_DATA\uninstall.opsiscript"
echo [Actions] >> "%pkgdir%\CLIENT_DATA\uninstall.opsiscript"
echo Message "Uninstalling %pkgname%" >> "%pkgdir%\CLIENT_DATA\uninstall.opsiscript"

echo.
echo ===================================
echo PAKET ERFOLGREICH ERSTELLT!
echo ===================================
echo.
echo Paket-Verzeichnis:
echo %pkgdir%
echo.
echo Oeffne Explorer...
start explorer "%pkgdir%"
echo.
echo --- OPSI-SERVER VERBINDUNG ---
echo.
set /p connect="Moechten Sie sich mit dem OPSI-Server verbinden? (J/N): "
if /i NOT "%connect%"=="J" goto skip_ssh

echo.
echo Geben Sie die Verbindungsdaten ein:
echo ------------------------------------
set /p opsiserver="OPSI-Server (Enter = 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH-Benutzer (Enter = root): "
if "%opsiuser%"=="" set opsiuser=root

echo.
echo Teste Server-Verbindung...
ping -n 1 %opsiserver% >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Server nicht erreichbar!
    goto skip_ssh
)

echo [OK] Server erreichbar
echo.
echo ----------------------------------------
echo Paket-Verzeichnis: %pkgdir%
echo Ziel-Server: %opsiserver%
echo ----------------------------------------
echo.
set /p readydeploy="Haben Sie alle Setup-Dateien in CLIENT_DATA kopiert? (J/N): "
if /i NOT "%readydeploy%"=="J" (
    echo.
    echo Bitte kopieren Sie erst alle benoetigten Dateien nach:
    echo %pkgdir%\CLIENT_DATA\
    echo.
    echo Dann fuehren Sie diese Befehle manuell aus:
    echo ----------------------------------------
    echo scp -r "%pkgdir%" %opsiuser%@%opsiserver%:/var/lib/opsi/workbench/
    echo ssh %opsiuser%@%opsiserver%
    echo opsi-makepackage %pkgid%_%pkgversion%
    echo opsi-package-manager -i %pkgid%_%pkgversion%.opsi
    echo ----------------------------------------
    goto skip_ssh
)

echo.
echo [AUTOMATISCHES DEPLOYMENT STARTET]
echo ==================================
echo.

echo Schritt 1/4: Kopiere Paket auf OPSI-Server...
echo.
scp -r "%pkgdir%" %opsiuser%@%opsiserver%:/var/lib/opsi/workbench/
if errorlevel 1 (
    echo [FEHLER] Transfer fehlgeschlagen
    echo Moeglicherweise fehlt SSH/SCP. Installation mit:
    echo   winget install OpenSSH.Client
    goto skip_ssh
)
echo [OK] Paket auf Server kopiert
echo.

echo Schritt 2/4: Baue OPSI-Paket...
ssh %opsiuser%@%opsiserver% "cd /var/lib/opsi/workbench && opsi-makepackage %pkgid%_%pkgversion%"
echo.

echo Schritt 3/4: Installiere in OPSI...
ssh %opsiuser%@%opsiserver% "opsi-package-manager -q -i /var/lib/opsi/workbench/%pkgid%_%pkgversion%-1.opsi"
if errorlevel 1 (
    echo [WARNUNG] Installation moeglicherweise fehlgeschlagen
) else (
    echo [OK] Paket installiert
)
echo.

echo Schritt 4/4: Pruefe Installation...
ssh %opsiuser%@%opsiserver% "opsi-package-manager -l | grep -i %pkgid%"
echo.

echo ==================================
echo DEPLOYMENT ABGESCHLOSSEN!
echo ==================================
echo.
echo Das Paket ist jetzt im OPSI-Configed verfuegbar.
echo Sie koennen es den Clients zuweisen.

:skip_ssh

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
echo - CLIENT_DATA/uninstall.opsiscript
echo.
echo OPSI-Server: 10.1.0.2 (backup.paedml-linux.lokal)
echo.
echo GitHub: https://github.com/Elliot-Markus-John-Adams/opsi-packforge
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