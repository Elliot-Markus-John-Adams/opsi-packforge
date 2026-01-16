# OPSI PackForge - Einfacher Installer
# Prueft ob bereits installiert und startet direkt

$installPath = "$env:LOCALAPPDATA\OPSI-PackForge"
$appPath = "$installPath\app\opsi_packforge.bat"

# Pruefen ob bereits installiert - aber trotzdem aktualisieren
if (Test-Path $appPath) {
    Write-Host ""
    Write-Host "OPSI PackForge ist bereits installiert!" -ForegroundColor Green
    Write-Host "Aktualisiere auf neueste Version..." -ForegroundColor Yellow
    Write-Host ""
    # Fahre mit Installation fort um die Datei zu aktualisieren
}

Clear-Host
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  OPSI PackForge - Simple Installer" -ForegroundColor Cyan  
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1] Installation starten" -ForegroundColor Yellow
Write-Host "[2] Beenden" -ForegroundColor Yellow
Write-Host ""

$choice = Read-Host "Bitte waehlen Sie eine Option (1-2)"

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
        
        # Schritt 2 - Python nur wenn noetig
        if (-not (Test-Path "$installPath\python\python.exe")) {
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
            
                Write-Host "OK - Python installiert" -ForegroundColor Green
                Write-Host ""
            } catch {
                Write-Host "FEHLER: $_" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "Schritt 2-3: Python bereits vorhanden - ueberspringe Download" -ForegroundColor Green
            Write-Host ""
        }
        
        # Schritt 4
        Write-Host "Schritt 4: Erstelle OPSI PackForge..." -ForegroundColor Yellow
        $appPath = "$installPath\app"
        New-Item -ItemType Directory -Path $appPath -Force | Out-Null
        
        # Erstelle das Haupt-Script
        $batchScript = @'
@echo off
setlocal enabledelayedexpansion
title OPSI PackForge v2.0
color 0A

:menu
cls
echo.
echo =====================================
echo       OPSI PackForge v2.0
echo =====================================
echo.
echo [1] Neues Paket erstellen
echo [2] Paket aktualisieren
echo [3] Paket loeschen
echo [4] Server-Pakete anzeigen
echo [5] Erweiterte Optionen
echo [6] Hilfe
echo [7] Beenden
echo.
set /p choice="Ihre Wahl: "

if "%choice%"=="1" goto create
if "%choice%"=="2" goto update
if "%choice%"=="3" goto delete
if "%choice%"=="4" goto listpackages
if "%choice%"=="5" goto advanced
if "%choice%"=="6" goto help
if "%choice%"=="7" exit
goto menu

:create
cls
echo.
echo === NEUES OPSI-PAKET ERSTELLEN ===
echo.
echo --- GRUNDLEGENDE INFORMATIONEN ---
set /p pkgid="Paket-ID (z.B. firefox): "
set /p pkgname="Paket-Name: "
set /p pkgversion="Version (z.B. 1.0.0): "
if "%pkgversion%"=="" set pkgversion=1.0.0

echo.
echo --- ERWEITERTE METADATEN ---
set /p pkgdesc="Beschreibung: "
if "%pkgdesc%"=="" set pkgdesc=%pkgname% Installation
set /p pkgadvice="Hinweise (optional): "
set /p pkgdepends="Abhaengigkeiten (kommagetrennt, optional): "
set /p pkgpriority="Prioritaet (0-100, Enter=0): "
if "%pkgpriority%"=="" set pkgpriority=0
set /p pkgclasses="Produkt-Klassen (kommagetrennt, optional): "

echo.
echo --- SETUP-KONFIGURATION ---
set /p setupfile="Setup-Datei (Pfad oder Enter fuer spaeter): "

set /p output="Ausgabe-Ordner (Enter fuer Desktop): "
if "%output%"=="" set output=%USERPROFILE%\Desktop

set pkgdir=%output%\%pkgid%_%pkgversion%

echo.
echo Erstelle Paket-Struktur...
mkdir "%pkgdir%\OPSI" 2>nul
mkdir "%pkgdir%\CLIENT_DATA" 2>nul
mkdir "%pkgdir%\CLIENT_DATA\files" 2>nul

REM Setup-Datei kopieren und Typ auto-erkennen
set setupfilename=
set silentparam=
set installertype=exe

if not "%setupfile%"=="" (
    if exist "%setupfile%" (
        echo Kopiere Setup-Datei...
        copy "%setupfile%" "%pkgdir%\CLIENT_DATA\files\" >nul
        for %%F in ("%setupfile%") do (
            set setupfilename=%%~nxF
            set setupext=%%~xF
        )
        REM Auto-detect installer type based on extension
        if /i "!setupext!"==".msi" (
            set installertype=msi
            set silentparam=/qn
            echo [AUTO] MSI Installer erkannt - Silent: /qn
        )
        if /i "!setupext!"==".bat" (
            set installertype=batch
            set silentparam=
            echo [AUTO] Batch-Datei erkannt - Kein Silent-Parameter
        )
        if /i "!setupext!"==".cmd" (
            set installertype=batch
            set silentparam=
            echo [AUTO] CMD-Datei erkannt - Kein Silent-Parameter
        )
        if /i "!setupext!"==".ps1" (
            set installertype=powershell
            set silentparam=-ExecutionPolicy Bypass -File
            echo [AUTO] PowerShell-Script erkannt
        )
        if /i "!setupext!"==".exe" (
            set installertype=exe
            echo [AUTO] EXE-Installer erkannt
            echo Pruefe Installer-Typ...
            findstr /i /c:"Inno Setup" "%setupfile%" >nul 2>&1
            if not errorlevel 1 (
                set installertype=inno
                set silentparam=/VERYSILENT /NORESTART
                echo [AUTO] InnoSetup erkannt - Silent: /VERYSILENT /NORESTART
            ) else (
                findstr /i /c:"Nullsoft" "%setupfile%" >nul 2>&1
                if not errorlevel 1 (
                    set installertype=nsis
                    set silentparam=/S
                    echo [AUTO] NSIS erkannt - Silent: /S
                ) else (
                    echo [INFO] Standard EXE - Bitte Silent-Parameter manuell angeben falls noetig
                    set /p silentparam="Silent-Parameter (Enter fuer keinen): "
                )
            )
        )
    ) else (
        echo WARNUNG: Setup-Datei nicht gefunden!
        echo Sie koennen die Datei spaeter manuell in CLIENT_DATA\files\ kopieren.
    )
) else (
    echo [INFO] Keine Setup-Datei angegeben.
    echo Sie koennen Dateien spaeter manuell in CLIENT_DATA\files\ kopieren.
)

REM Control-Datei mit erweiterten Metadaten erstellen
echo [Package] > "%pkgdir%\OPSI\control"
echo version: 1 >> "%pkgdir%\OPSI\control"
echo depends: %pkgdepends% >> "%pkgdir%\OPSI\control"
echo incremental: False >> "%pkgdir%\OPSI\control"
echo. >> "%pkgdir%\OPSI\control"
echo [Product] >> "%pkgdir%\OPSI\control"
echo type: localboot >> "%pkgdir%\OPSI\control"
echo id: %pkgid% >> "%pkgdir%\OPSI\control"
echo name: %pkgname% >> "%pkgdir%\OPSI\control"
echo description: %pkgdesc% >> "%pkgdir%\OPSI\control"
echo advice: %pkgadvice% >> "%pkgdir%\OPSI\control"
echo version: %pkgversion% >> "%pkgdir%\OPSI\control"
echo priority: %pkgpriority% >> "%pkgdir%\OPSI\control"
echo licenseRequired: False >> "%pkgdir%\OPSI\control"
echo productClasses: %pkgclasses% >> "%pkgdir%\OPSI\control"
echo setupScript: setup.opsiscript >> "%pkgdir%\OPSI\control"
echo uninstallScript: uninstall.opsiscript >> "%pkgdir%\OPSI\control"
echo updateScript: >> "%pkgdir%\OPSI\control"
echo alwaysScript: >> "%pkgdir%\OPSI\control"
echo onceScript: >> "%pkgdir%\OPSI\control"

REM Setup-Script erstellen basierend auf erkanntem Typ
echo ; Setup script for %pkgname% > "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo ; Generated by OPSI PackForge v2.0 >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo ; Installer type: !installertype! >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo [Actions] >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo requiredWinstVersion ^>= "4.11.6" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo DefVar $SetupFile$ >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo DefVar $ProductId$ >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo DefVar $ExitCode$ >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo Set $ProductId$ = "%pkgid%" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"

if "!setupfilename!"=="" (
    echo ; TODO: Setzen Sie hier Ihren Setup-Dateinamen ein >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo Set $SetupFile$ = "%%ScriptPath%%\files\IHRE_DATEI_HIER" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
) else (
    echo Set $SetupFile$ = "%%ScriptPath%%\files\!setupfilename!" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
)

echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo Message "Installing " + $ProductId$ + " ..." >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo comment "Start setup program" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo ChangeDirectory "%%ScriptPath%%\files" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"

REM Unterschiedliche Winbatch-Aufrufe je nach Installer-Typ
if "!installertype!"=="msi" (
    echo Winbatch_install_msi >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo Sub_check_exitcode >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo [Winbatch_install_msi] >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo msiexec /i "$SetupFile$" /qn /norestart >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
) else if "!installertype!"=="powershell" (
    echo ShellCall_install >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo Sub_check_exitcode >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo [ShellCall_install] >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo powershell.exe -ExecutionPolicy Bypass -File "$SetupFile$" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
) else (
    echo Winbatch_install >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo Sub_check_exitcode >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo [Winbatch_install] >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    if "!silentparam!"=="" (
        echo "$SetupFile$" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    ) else (
        echo "$SetupFile$" !silentparam! >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    )
)

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
ssh %opsiuser%@%opsiserver% "cd /var/lib/opsi/workbench && rm -f %pkgid%_%pkgversion%-*.opsi 2>/dev/null; opsi-makepackage %pkgid%_%pkgversion%"
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

:update
cls
echo.
echo === PAKET AKTUALISIEREN ===
echo.
set /p opsiserver="OPSI-Server (Enter = 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH-Benutzer (Enter = root): "
if "%opsiuser%"=="" set opsiuser=root

echo.
echo Teste Server-Verbindung...
ping -n 1 %opsiserver% >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Server nicht erreichbar!
    pause
    goto menu
)

echo.
echo Lade installierte Pakete vom Server...
ssh %opsiuser%@%opsiserver% "opsi-package-manager -l | tail -n +4 | awk '{print $1}' | sort"
echo.
set /p pkgupdate="Welches Paket aktualisieren? (Paket-ID eingeben): "

echo.
echo Pruefe ob Workbench-Ordner existiert...
ssh %opsiuser%@%opsiserver% "if [ -d /var/lib/opsi/workbench/%pkgupdate%_* ]; then echo 'Workbench-Ordner gefunden'; else echo 'Kein Workbench-Ordner - kopiere vom Depot...'; cp -r /var/lib/opsi/depot/%pkgupdate% /var/lib/opsi/workbench/%pkgupdate%_update 2>/dev/null || echo '[WARNUNG] Depot-Ordner nicht gefunden'; fi"

echo.
set /p newversion="Neue Version (Enter = Version beibehalten): "

echo.
echo [1] Setup-Dateien ersetzen
echo [2] Control-Datei bearbeiten
echo [3] Scripts aktualisieren
echo [4] Alles aktualisieren
set /p updatetype="Was soll aktualisiert werden? (1-4): "

if "%updatetype%"=="1" (
    echo.
    set /p newsetup="Pfad zur neuen Setup-Datei: "
    echo Kopiere neue Setup-Datei auf Server...
    ssh %opsiuser%@%opsiserver% "find /var/lib/opsi/workbench -maxdepth 2 -name '%pkgupdate%*' -type d | head -1" > %temp%\pkgdir.txt
    set /p pkgdir=<%temp%\pkgdir.txt
    scp "%newsetup%" %opsiuser%@%opsiserver%:%pkgdir%/CLIENT_DATA/files/
    echo [OK] Setup-Datei aktualisiert
)

echo.
echo Suche Workbench-Ordner und baue Paket neu...
ssh %opsiuser%@%opsiserver% "pkgdir=$(find /var/lib/opsi/workbench -maxdepth 2 -name '%pkgupdate%*' -type d | head -1); if [ -n \"$pkgdir\" ]; then cd \"$pkgdir\" && cd .. && opsi-makepackage \"$(basename $pkgdir)\"; else echo '[FEHLER] Kein Workbench-Ordner gefunden'; fi"
echo.
echo Installiere aktualisiertes Paket...
ssh %opsiuser%@%opsiserver% "latest=$(ls -t /var/lib/opsi/workbench/%pkgupdate%*.opsi 2>/dev/null | head -1); if [ -n \"$latest\" ]; then opsi-package-manager -q -i \"$latest\"; else echo '[FEHLER] Kein Paket gefunden'; fi"

echo.
echo [OK] Paket aktualisiert!
pause
goto menu

:delete
cls
echo.
echo === PAKET LOESCHEN ===
echo.

set /p opsiserver="OPSI-Server (Enter = 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH-Benutzer (Enter = root): "
if "%opsiuser%"=="" set opsiuser=root

echo.
echo Installierte Pakete:
ssh %opsiuser%@%opsiserver% "opsi-package-manager -l"
echo.
echo === WORKBENCH PROJEKTE (nicht installiert) ===
ssh %opsiuser%@%opsiserver% "cd /var/lib/opsi/workbench && for dir in */; do pkg=${dir%/}; pkgid=${pkg%%_*}; opsi-package-manager -l | grep -q \"^   $pkgid \" || echo $pkg; done 2>/dev/null"
echo.
set /p pkgdelete="Paket-ID oder Workbench-Ordner zum Loeschen: "

echo.
echo WARNUNG: Paket '%pkgdelete%' wird komplett entfernt!
echo.
echo Loeschoptionen:
echo [1] Normal loeschen (empfohlen)
echo [2] Mit --purge (entfernt auch alle Client-Zuordnungen)
echo [3] Abbrechen
echo.
set /p deleteoption="Ihre Wahl (1-3): "

if "%deleteoption%"=="3" (
    echo Abbruch.
    pause
    goto menu
)

echo.
echo === LOESCHVORGANG STARTET ===
echo.

REM Extrahiere Paket-ID: entferne nur _VERSION am Ende (z.B. _1.0.0)
REM Server-seitig extrahieren um komplexe Namen wie opsi-hotfix korrekt zu behandeln
echo Ermittle Paket-ID...
for /f "delims=" %%i in ('ssh %opsiuser%@%opsiserver% "echo '%pkgdelete%' | sed 's/_[0-9][0-9.]*[-0-9]*$//' "') do set pkgid=%%i
if "%pkgid%"=="" set pkgid=%pkgdelete%
echo Paket-ID: %pkgid%

echo.
echo Pruefe ob Paket installiert ist...
ssh %opsiuser%@%opsiserver% "opsi-package-manager -l | grep -q \"   %pkgid% \" && echo '[INFO] Paket ist installiert' || echo '[INFO] Nur in Workbench vorhanden'"

if "%deleteoption%"=="1" (
    echo Loesche Paket '%pkgid%' ...
    ssh %opsiuser%@%opsiserver% "TERM=dumb opsi-package-manager -q -r %pkgid% 2>/dev/null"
    if errorlevel 1 (
        echo [INFO] Paket nicht installiert oder Fehler beim Loeschen
    ) else (
        echo [OK] Paket aus OPSI entfernt
    )
) else if "%deleteoption%"=="2" (
    echo Loesche Paket '%pkgid%' mit --purge ...
    ssh %opsiuser%@%opsiserver% "TERM=dumb opsi-package-manager -q -r %pkgid% --purge 2>/dev/null"
    if errorlevel 1 (
        echo [INFO] Paket nicht installiert oder Fehler beim Loeschen
    ) else (
        echo [OK] Paket aus OPSI entfernt (inkl. Client-Zuordnungen)
    )
)

echo.
echo Raeume Workbench und Repository auf...
ssh %opsiuser%@%opsiserver% "cd /var/lib/opsi/workbench && rm -rf '%pkgid%' '%pkgid%'_* '%pkgid%'.opsi* '%pkgdelete%' '%pkgdelete%'.opsi* 2>/dev/null; echo '[OK] Workbench bereinigt'"
ssh %opsiuser%@%opsiserver% "cd /var/lib/opsi/repository && rm -rf '%pkgid%'* 2>/dev/null; echo '[OK] Repository bereinigt'"
ssh %opsiuser%@%opsiserver% "cd /var/lib/opsi/depot && rm -rf '%pkgid%' 2>/dev/null; echo '[OK] Depot bereinigt'"

echo.
echo Pruefe ob Paket entfernt wurde...
ssh %opsiuser%@%opsiserver% "opsi-package-manager -l | grep -i '%pkgid%' || echo '[OK] Paket nicht mehr in der Liste'"

echo.
echo Fertig.
pause
goto menu

:listpackages
cls
echo.
echo === SERVER-PAKETE ANZEIGEN ===
echo.
set /p opsiserver="OPSI-Server (Enter = 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH-Benutzer (Enter = root): "
if "%opsiuser%"=="" set opsiuser=root

echo.
echo Teste Server-Verbindung...
ping -n 1 %opsiserver% >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Server nicht erreichbar!
    pause
    goto menu
)

echo.
echo ===== INSTALLIERTE PAKETE =====
ssh %opsiuser%@%opsiserver% "opsi-package-manager -l"
echo.
echo ===== WORKBENCH PAKETE =====
ssh %opsiuser%@%opsiserver% "ls -la /var/lib/opsi/workbench/"
echo.
pause
goto menu

:advanced
cls
echo.
echo === ERWEITERTE OPTIONEN ===
echo.
echo [1] SSH-Key einrichten
echo [2] Server-Logs anzeigen
echo [3] Client-Status pruefen
echo [4] Depot synchronisieren
echo [5] Zurueck zum Hauptmenue
echo.
set /p advchoice="Ihre Wahl: "

if "%advchoice%"=="1" (
    echo.
    echo === AUTOMATISCHES SSH-KEY SETUP ===
    echo.
    set /p opsiserver="OPSI-Server (Enter = 10.1.0.2): "
    if "!opsiserver!"=="" set opsiserver=10.1.0.2
    set /p opsiuser="SSH-Benutzer (Enter = root): "
    if "!opsiuser!"=="" set opsiuser=root
    echo.
    echo Schritt 1/4: Pruefe ob SSH-Key existiert...
    if exist "%USERPROFILE%\.ssh\id_rsa.pub" (
        echo [OK] SSH-Key bereits vorhanden
    ) else (
        echo [INFO] Kein SSH-Key gefunden - erstelle neuen Key...
        echo.
        if not exist "%USERPROFILE%\.ssh" mkdir "%USERPROFILE%\.ssh"
        ssh-keygen -t rsa -b 4096 -f "%USERPROFILE%\.ssh\id_rsa" -N ""
        if errorlevel 1 (
            echo [FEHLER] Key-Generierung fehlgeschlagen
            echo Stellen Sie sicher dass OpenSSH installiert ist:
            echo   winget install Microsoft.OpenSSH.Client
            pause
            goto advanced
        )
        echo [OK] SSH-Key erstellt
    )
    echo.
    echo Schritt 2/4: Teste Server-Erreichbarkeit...
    ping -n 1 !opsiserver! >nul 2>&1
    if errorlevel 1 (
        echo [FEHLER] Server !opsiserver! nicht erreichbar!
        pause
        goto advanced
    )
    echo [OK] Server erreichbar
    echo.
    echo Schritt 3/4: Kopiere Public-Key auf Server...
    echo [INFO] Sie werden nach dem Passwort fuer !opsiuser!@!opsiserver! gefragt
    echo.
    type "%USERPROFILE%\.ssh\id_rsa.pub" | ssh !opsiuser!@!opsiserver! "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
    if errorlevel 1 (
        echo [FEHLER] Key-Kopie fehlgeschlagen
        pause
        goto advanced
    )
    echo [OK] Public-Key auf Server kopiert
    echo.
    echo Schritt 4/4: Teste passwortlose Verbindung...
    ssh -o BatchMode=yes -o ConnectTimeout=5 !opsiuser!@!opsiserver! "echo SSH-Verbindung erfolgreich"
    if errorlevel 1 (
        echo [WARNUNG] Passwortlose Verbindung noch nicht moeglich
        echo Versuchen Sie es erneut oder pruefen Sie die Server-Konfiguration
    ) else (
        echo.
        echo ====================================
        echo SSH-KEY SETUP ERFOLGREICH!
        echo ====================================
        echo Sie koennen sich jetzt ohne Passwort verbinden.
    )
    echo.
    pause
    goto advanced
)

if "%advchoice%"=="2" (
    set /p opsiserver="OPSI-Server (Enter = 10.1.0.2): "
    if "%opsiserver%"=="" set opsiserver=10.1.0.2
    set /p opsiuser="SSH-Benutzer (Enter = root): "
    if "%opsiuser%"=="" set opsiuser=root
    echo.
    echo === VERFUEGBARE LOG-DATEIEN ===
    ssh %opsiuser%@%opsiserver% "ls -la /var/log/opsi/*.log 2>/dev/null | tail -10"
    echo.
    echo === LETZTE PACKAGE.LOG EINTRAEGE ===
    ssh %opsiuser%@%opsiserver% "if [ -f /var/log/opsi/package.log ]; then tail -20 /var/log/opsi/package.log; else echo 'package.log nicht gefunden'; fi"
    echo.
    echo === LETZTE OPSICONFD.LOG EINTRAEGE ===
    ssh %opsiuser%@%opsiserver% "if [ -f /var/log/opsi/opsiconfd.log ]; then tail -20 /var/log/opsi/opsiconfd.log; else echo 'opsiconfd.log nicht gefunden'; fi"
    echo.
    echo === LETZTE CLIENT-LOGS ===
    ssh %opsiuser%@%opsiserver% "ls -lt /var/log/opsi/clientconnect/*.log 2>/dev/null | head -5"
    pause
)

if "%advchoice%"=="3" goto clientstatus

if "%advchoice%"=="4" (
    set /p opsiserver="OPSI-Server (Enter = 10.1.0.2): "
    if "%opsiserver%"=="" set opsiserver=10.1.0.2
    set /p opsiuser="SSH-Benutzer (Enter = root): "
    if "%opsiuser%"=="" set opsiuser=root
    echo Synchronisiere Depot...
    ssh %opsiuser%@%opsiserver% "opsi-package-updater -v update"
    pause
)

goto menu

:clientstatus
cls
echo.
echo === CLIENT-STATUS PRUEFEN ===
echo.
set opsiserver=10.1.0.2
set opsiuser=root
set /p opsiserver="OPSI-Server [%opsiserver%]: "
set /p opsiuser="SSH-Benutzer [%opsiuser%]: "
echo.
echo Verbinde mit %opsiuser%@%opsiserver%...
echo.
echo === REGISTRIERTE CLIENTS ===
ssh %opsiuser%@%opsiserver% opsi-admin -d method host_getIdents
if errorlevel 1 echo [FEHLER] Konnte Clients nicht abrufen
echo.
echo === ERREICHBARE CLIENTS ===
ssh %opsiuser%@%opsiserver% "opsi-admin -d method hostControl_reachable | grep true"
if errorlevel 1 echo [INFO] Keine erreichbaren Clients gefunden
echo.
echo Fertig.
pause
goto advanced

:help
cls
echo.
echo === HILFE ===
echo.
echo OPSI PackForge v2.0 - Professionelle OPSI-Paketverwaltung
echo.
echo FUNKTIONEN:
echo -----------
echo [1] Neues Paket erstellen
echo     - Vollstaendige Metadaten-Unterstuetzung
echo     - Automatische Silent-Parameter Erkennung
echo     - Multi-Datei Support
echo.
echo [2] Paket aktualisieren
echo     - Setup-Dateien ersetzen
echo     - Versionierung
echo     - Live-Update im Depot
echo.
echo [3] Paket loeschen
echo     - Sichere Entfernung vom Server
echo     - Client-Pruefung
echo.
echo [4] Server-Pakete anzeigen
echo     - Installierte Pakete
echo     - Workbench-Inhalte
echo.
echo [5] Erweiterte Optionen
echo     - SSH-Key Setup
echo     - Log-Anzeige
echo     - Client-Status
echo     - Depot-Sync
echo.
echo TIPPS:
echo ------
echo - SSH-Keys einrichten fuer passwortlosen Zugriff
echo - Setup-Dateien immer in CLIENT_DATA/files/ platzieren
echo - Versionsnummern im Format X.Y.Z verwenden
echo.
echo OPSI-Server: 10.1.0.2 (backup.paedml-linux.lokal)
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
    }
    
    "2" {
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