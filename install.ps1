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
title OPSI PackForge v1.0 - paedML Linux Tool
color 0B
mode con: cols=80 lines=40

:menu
cls
echo.
echo    [36m╔═══════════════════════════════════════════════════════════════╗[0m
echo    [36m║                                                               ║[0m
echo    [36m║[0m     [96m█████╗ ██████╗ ███████╗██╗[0m  [93m██████╗  █████╗  ██████╗[0m   [36m║[0m
echo    [36m║[0m    [96m██╔══██╗██╔══██╗██╔════╝██║[0m  [93m██╔══██╗██╔══██╗██╔════╝[0m   [36m║[0m
echo    [36m║[0m    [96m██║  ██║██████╔╝███████╗██║[0m  [93m██████╔╝███████║██║[0m        [36m║[0m
echo    [36m║[0m    [96m██║  ██║██╔═══╝ ╚════██║██║[0m  [93m██╔═══╝ ██╔══██║██║[0m        [36m║[0m
echo    [36m║[0m    [96m╚█████╔╝██║     ███████║██║[0m  [93m██║     ██║  ██║╚██████╗[0m   [36m║[0m
echo    [36m║[0m     [96m╚════╝ ╚═╝     ╚══════╝╚═╝[0m  [93m╚═╝     ╚═╝  ╚═╝ ╚═════╝[0m   [36m║[0m
echo    [36m║                                                               ║[0m
echo    [36m║[0m              [95mPackForge[0m - [32mTool fuer paedML Linux[0m              [36m║[0m
echo    [36m╚═══════════════════════════════════════════════════════════════╝[0m
echo.
echo                        [92m╔════════════════════╗[0m
echo                        [92m║[0m  [97mHAUPTMENUE[0m        [92m║[0m
echo                        [92m╚════════════════════╝[0m
echo.
echo            [33m[[0m[36m1[0m[33m][0m [97m📦 Neues OPSI-Paket erstellen[0m
echo.
echo            [33m[[0m[36m2[0m[33m][0m [97m📚 Hilfe und Dokumentation[0m
echo.
echo            [33m[[0m[36m3[0m[33m][0m [97m🚪 Programm beenden[0m
echo.
echo    [90m═══════════════════════════════════════════════════════════════[0m
echo.
set /p choice="    [94m▶[0m Ihre Auswahl eingeben [36m[[0m1-3[36m][0m: "

if "%choice%"=="1" goto create
if "%choice%"=="2" goto help
if "%choice%"=="3" exit
goto menu

:create
cls
echo.
echo    [36m╔═══════════════════════════════════════════════════════════════╗[0m
echo    [36m║[0m            [93m✨ NEUES OPSI-PAKET ERSTELLEN ✨[0m                  [36m║[0m
echo    [36m╚═══════════════════════════════════════════════════════════════╝[0m
echo.
echo    [32mBitte geben Sie die Paket-Informationen ein:[0m
echo    [90m───────────────────────────────────────────[0m
echo.
set /p pkgid="    [94m▶[0m Paket-ID [90m(z.B. firefox)[0m: "
echo.
set /p pkgname="    [94m▶[0m Paket-Name [90m(z.B. Mozilla Firefox)[0m: "
echo.
set /p pkgversion="    [94m▶[0m Version [90m(Standard: 1.0.0)[0m: "
if "%pkgversion%"=="" set pkgversion=1.0.0
echo.
echo    [33m⚙️  Erweiterte Optionen (optional):[0m
echo    [90m───────────────────────────────────────────[0m
echo.
set /p setupfile="    [94m▶[0m Setup-Datei [90m(Pfad oder Enter)[0m: "
echo.
set /p silentparam="    [94m▶[0m Silent-Parameter [90m(/S, /quiet)[0m: "
echo.
set /p output="    [94m▶[0m Ausgabe-Ordner [90m(Enter = Desktop)[0m: "

if "%output%"=="" set output=%USERPROFILE%\Desktop

set pkgdir=%output%\%pkgid%_%pkgversion%

echo.
echo    [93m⏳ Erstelle Paket-Struktur...[0m
echo.
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
echo    [92m╔═══════════════════════════════════════════════════════════════╗[0m
echo    [92m║[0m           [97m✅ PAKET ERFOLGREICH ERSTELLT! ✅[0m                 [92m║[0m
echo    [92m╚═══════════════════════════════════════════════════════════════╝[0m
echo.
echo    [32m📁 Paket-Verzeichnis:[0m
echo    [96m%pkgdir%[0m
echo.
echo    [93m📂 Oeffne Explorer-Fenster...[0m
start explorer "%pkgdir%"
echo.
echo --- OPSI-SERVER VERBINDUNG ---
echo.
set /p connect="Moechten Sie sich mit dem OPSI-Server verbinden? (J/N): "
if /i "%connect%"=="J" goto connect_server
echo.
echo Paket wurde lokal erstellt in: %pkgdir%
goto end_create

:connect_server
echo.
set /p opsiserver="OPSI-Server IP/Hostname (Default: 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH-Benutzer (meist root): "
if "%opsiuser%"=="" set opsiuser=root

echo.
echo Teste Verbindung zum OPSI-Server %opsiserver%...
ping -n 1 %opsiserver% >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Server %opsiserver% nicht erreichbar!
    echo.
    echo Pruefen Sie:
    echo - IP-Adresse/Hostname
    echo - Netzwerkverbindung
    echo - Firewall-Einstellungen
) else (
    echo [OK] Server %opsiserver% ist erreichbar
    echo.
    echo Verbinde mit SSH als %opsiuser%@%opsiserver%...
    echo.
    
    REM Zeige vorhandene OPSI-Pakete auf dem Server
    echo OPSI Workbench Verzeichnis:
    echo ----------------------------------------
    ssh %opsiuser%@%opsiserver% "ls -la /var/lib/opsi/workbench/ 2>/dev/null | head -10" 2>nul
    if errorlevel 1 (
        echo [WARNUNG] SSH-Verbindung fehlgeschlagen
        echo Installieren Sie SSH mit: winget install OpenSSH.Client
    )
    
    echo.
    echo OPSI Depot Verzeichnis:
    echo ----------------------------------------
    ssh %opsiuser%@%opsiserver% "ls -la /var/lib/opsi/depot/ 2>/dev/null | head -10" 2>nul
    
    echo.
    echo ----------------------------------------
    echo Lokales Paket wurde erstellt in:
    echo %pkgdir%
    echo.
    echo Inhalt des lokalen Pakets:
    dir /B "%pkgdir%\OPSI"
    dir /B "%pkgdir%\CLIENT_DATA"
    echo.
    echo Deployment-Befehle fuer OPSI-Server (%opsiserver%):
    echo ----------------------------------------
    echo 1. Paket auf Server kopieren:
    echo    scp -r "%pkgdir%" %opsiuser%@%opsiserver%:/var/lib/opsi/workbench/
    echo.
    echo 2. Auf Server einloggen:
    echo    ssh %opsiuser%@%opsiserver%
    echo.
    echo 3. Paket bauen und installieren:
    echo    cd /var/lib/opsi/workbench
    echo    opsi-makepackage %pkgid%_%pkgversion%
    echo    opsi-package-manager -i %pkgid%_%pkgversion%.opsi
    echo.
    echo ----------------------------------------
    echo.
    set /p autodeploy="Moechten Sie das Paket JETZT automatisch deployen? (J/N): "
    if /i "%autodeploy%"=="J" (
        echo.
        echo [DEPLOYMENT STARTET]
        echo.
        
        echo Schritt 1: Kopiere Paket auf Server...
        scp -r "%pkgdir%" %opsiuser%@%opsiserver%:/var/lib/opsi/workbench/
        if errorlevel 1 (
            echo [FEHLER] Kopieren fehlgeschlagen!
            echo Pruefen Sie:
            echo - SSH/SCP installiert? (winget install OpenSSH.Client)
            echo - Server erreichbar?
            echo - Passwort korrekt?
        ) else (
            echo [OK] Paket kopiert
        )
        echo.
        
        echo Schritt 2: Baue OPSI-Paket auf Server...
        ssh %opsiuser%@%opsiserver% "cd /var/lib/opsi/workbench && opsi-makepackage %pkgid%_%pkgversion%"
        if errorlevel 1 (
            echo [WARNUNG] Paket-Build moeglicherweise fehlgeschlagen
        ) else (
            echo [OK] OPSI-Paket gebaut
        )
        echo.
        
        echo Schritt 3: Installiere Paket in OPSI...
        ssh %opsiuser%@%opsiserver% "opsi-package-manager -i /var/lib/opsi/workbench/%pkgid%_%pkgversion%.opsi"
        if errorlevel 1 (
            echo [WARNUNG] Installation moeglicherweise fehlgeschlagen
        ) else (
            echo [OK] Paket in OPSI installiert
        )
        echo.
        
        echo Schritt 4: Zeige installierte Pakete...
        ssh %opsiuser%@%opsiserver% "opsi-package-manager -l | grep %pkgid%"
        echo.
        
        echo ===================================
        echo DEPLOYMENT ABGESCHLOSSEN!
        echo ===================================
        echo.
        echo Das Paket sollte jetzt im OPSI-Configed verfuegbar sein.
        echo Sie koennen es Clients zuweisen unter:
        echo - OPSI Configed starten
        echo - Produktkonfiguration
        echo - %pkgid% suchen
        echo.
    ) else (
        echo.
        echo Manuelles Deployment spaeter moeglich mit obigen Befehlen.
    )
)

:end_create
echo.
pause
goto menu

:help
cls
echo.
echo    [36m╔═══════════════════════════════════════════════════════════════╗[0m
echo    [36m║[0m                 [93m📚 HILFE UND DOKUMENTATION 📚[0m               [36m║[0m
echo    [36m╚═══════════════════════════════════════════════════════════════╝[0m
echo.
echo    [97m▶ Was ist OPSI PackForge?[0m
echo    [90m───────────────────────────────────────────[0m
echo    Ein Tool zur einfachen Erstellung von OPSI-Paketen
echo    speziell fuer paedML Linux Umgebungen.
echo.
echo    [97m▶ Hauptfunktionen:[0m
echo    [90m───────────────────────────────────────────[0m
echo    [32m✓[0m Erstellt OPSI-konforme Paketstruktur
echo    [32m✓[0m Generiert control und opsiscript Dateien
echo    [32m✓[0m SSH-Verbindung zum OPSI-Server
echo    [32m✓[0m Automatisches Deployment moeglich
echo.
echo    [97m▶ Erstellte Dateien:[0m
echo    [90m───────────────────────────────────────────[0m
echo    [36mOPSI/control[0m         - Paket-Metadaten
echo    [36mCLIENT_DATA/[0m
echo      [36m├─ setup.opsiscript[0m    - Installations-Script
echo      [36m└─ uninstall.opsiscript[0m - Deinstallations-Script
echo.
echo    [97m▶ OPSI-Server:[0m
echo    [90m───────────────────────────────────────────[0m
echo    Standard: [93m10.1.0.2[0m ([93mbackup.paedml-linux.lokal[0m)
echo.
echo    [97m▶ Support:[0m
echo    [90m───────────────────────────────────────────[0m
echo    GitHub: [94mhttps://github.com/Elliot-Markus-John-Adams/opsi-packforge[0m
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