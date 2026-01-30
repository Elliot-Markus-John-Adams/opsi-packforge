# OPSI PackForge - Simple Installer
# Checks if already installed and starts directly

$installPath = "$env:LOCALAPPDATA\OPSI-PackForge"
$appPath = "$installPath\app\opsi_packforge.bat"

# Check if already installed - but still update
if (Test-Path $appPath) {
    Write-Host ""
    Write-Host "OPSI PackForge is already installed!" -ForegroundColor Green
    Write-Host "Updating to latest version..." -ForegroundColor Yellow
    Write-Host ""
    # Continue with installation to update the file
}

Clear-Host
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  OPSI PackForge - Simple Installer" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1] Start installation" -ForegroundColor Yellow
Write-Host "[2] Exit" -ForegroundColor Yellow
Write-Host ""

$choice = Read-Host "Please select an option (1-2)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Starting installation..." -ForegroundColor Green
        Write-Host ""

        # Step 1
        Write-Host "Step 1: Creating directory..." -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $installPath -Force | Out-Null
        Write-Host "OK - Directory created: $installPath" -ForegroundColor Green
        Write-Host ""

        # Step 2 - Python only if needed
        if (-not (Test-Path "$installPath\python\python.exe")) {
            Write-Host "Step 2: Downloading Python..." -ForegroundColor Yellow
            Write-Host "This may take a few minutes..." -ForegroundColor Gray

            try {
                $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
                $pythonZip = "$env:TEMP\python.zip"

                # Proxy support
                [System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials
                $client = New-Object System.Net.WebClient
                $client.Proxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials
                $client.DownloadFile($pythonUrl, $pythonZip)

                Write-Host "OK - Python downloaded" -ForegroundColor Green
                Write-Host ""

                # Step 3
                Write-Host "Step 3: Extracting Python..." -ForegroundColor Yellow
                Expand-Archive -Path $pythonZip -DestinationPath "$installPath\python" -Force
                Remove-Item $pythonZip

                Write-Host "OK - Python installed" -ForegroundColor Green
                Write-Host ""
            } catch {
                Write-Host "ERROR: $_" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "Step 2-3: Python already present - skipping download" -ForegroundColor Green
            Write-Host ""
        }

        # Step 4
        Write-Host "Step 4: Creating OPSI PackForge..." -ForegroundColor Yellow
        $appPath = "$installPath\app"
        New-Item -ItemType Directory -Path $appPath -Force | Out-Null

        # Create the main script
        $batchScript = @'
@echo off
setlocal enabledelayedexpansion
title OPSI PackForge v2.0
color 0A

:menu
cls
echo.
echo  ########################################################
echo  ##                                                    ##
echo  ##              OPSI PACKFORGE v2.0                   ##
echo  ##                                                    ##
echo  ##          Package Management Made Easy              ##
echo  ##                                                    ##
echo  ########################################################
echo.
echo [1] Create new package
echo [2] Update package
echo [3] Delete package
echo [4] Show server packages
echo [5] Advanced options
echo [6] Help
echo [7] Exit
echo.
set /p choice="Your choice: "

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
echo === CREATE NEW OPSI PACKAGE ===
echo.
echo --- BASIC INFORMATION ---
set /p pkgid="Package ID (e.g. firefox): "
set /p pkgname="Package name: "
set /p pkgversion="Version (e.g. 1.0.0): "
if "%pkgversion%"=="" set pkgversion=1.0.0

echo.
echo --- EXTENDED METADATA ---
set /p pkgdesc="Description: "
if "%pkgdesc%"=="" set pkgdesc=%pkgname% Installation
set /p pkgadvice="Notes (optional): "
set /p pkgdepends="Dependencies (comma-separated, optional): "
set /p pkgpriority="Priority (0-100, Enter=0): "
if "%pkgpriority%"=="" set pkgpriority=0
set /p pkgclasses="Product classes (comma-separated, optional): "

echo.
echo --- SETUP CONFIGURATION ---
set /p setupfile="Setup file (path or Enter for later): "

set /p output="Output folder (Enter for Desktop): "
if "%output%"=="" set output=%USERPROFILE%\Desktop

set pkgdir=%output%\%pkgid%_%pkgversion%

echo.
echo Creating package structure...
mkdir "%pkgdir%\OPSI" 2>nul
mkdir "%pkgdir%\CLIENT_DATA" 2>nul
mkdir "%pkgdir%\CLIENT_DATA\files" 2>nul

REM Copy setup file and auto-detect type
set setupfilename=
set silentparam=
set installertype=exe

if not "%setupfile%"=="" (
    if exist "%setupfile%" (
        echo Copying setup file...
        copy "%setupfile%" "%pkgdir%\CLIENT_DATA\files\" >nul
        for %%F in ("%setupfile%") do (
            set setupfilename=%%~nxF
            set setupext=%%~xF
        )
        REM Auto-detect installer type based on extension
        if /i "!setupext!"==".msi" (
            set installertype=msi
            set silentparam=/qn /norestart
            echo [AUTO] MSI installer detected - msiexec /qn /norestart
        )
        if /i "!setupext!"==".bat" (
            set installertype=batch
            set silentparam=
            echo [AUTO] Batch file detected - No silent parameter
        )
        if /i "!setupext!"==".cmd" (
            set installertype=batch
            set silentparam=
            echo [AUTO] CMD file detected - No silent parameter
        )
        if /i "!setupext!"==".ps1" (
            set installertype=powershell
            set silentparam=-ExecutionPolicy Bypass -File
            echo [AUTO] PowerShell script detected
        )
        if /i "!setupext!"==".exe" (
            set installertype=exe
            echo [AUTO] EXE installer detected
            echo Checking installer type...
            findstr /i /c:"Inno Setup" "%setupfile%" >nul 2>&1
            if not errorlevel 1 (
                set installertype=inno
                set silentparam=/VERYSILENT /SUPPRESSMSGBOXES /NORESTART
                echo [AUTO] InnoSetup detected
            ) else (
                findstr /i /c:"Nullsoft" "%setupfile%" >nul 2>&1
                if not errorlevel 1 (
                    set installertype=nsis
                    set silentparam=/S
                    echo [AUTO] NSIS detected - Note: /S must be uppercase!
                ) else (
                    findstr /i /c:"InstallShield" "%setupfile%" >nul 2>&1
                    if not errorlevel 1 (
                        set installertype=installshield
                        set silentparam=/s /sms
                        echo [AUTO] InstallShield detected
                    ) else (
                        echo [INFO] Unknown EXE type - Please specify silent parameter
                        echo Common options: /S, /silent, /quiet, /VERYSILENT
                        set /p silentparam="Silent parameter (Enter for none): "
                    )
                )
            )
        )
    ) else (
        echo WARNING: Setup file not found!
        echo You can copy the file manually to CLIENT_DATA\files\ later.
    )
) else (
    echo [INFO] No setup file specified.
    echo You can copy files manually to CLIENT_DATA\files\ later.
    echo.
    echo --- INSTALLER TYPE ---
    echo [1] MSI installer        - msiexec /qn /norestart
    echo [2] EXE InnoSetup        - /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
    echo [3] EXE NSIS             - /S
    echo [4] EXE InstallShield    - /s /sms
    echo [5] EXE Other            - Custom silent parameter
    echo [6] PowerShell script
    echo [7] Batch file
    echo [8] Skip for now
    echo.
    set /p insttype="Select installer type (1-8): "
    if "!insttype!"=="1" (
        set installertype=msi
        set silentparam=/qn /norestart
        echo [OK] MSI selected - msiexec /i file.msi /qn /norestart
    )
    if "!insttype!"=="2" (
        set installertype=inno
        set silentparam=/VERYSILENT /SUPPRESSMSGBOXES /NORESTART
        echo [OK] InnoSetup selected
    )
    if "!insttype!"=="3" (
        set installertype=nsis
        set silentparam=/S
        echo [OK] NSIS selected - Note: /S must be uppercase!
    )
    if "!insttype!"=="4" (
        set installertype=installshield
        set silentparam=/s /sms
        echo [OK] InstallShield selected
    )
    if "!insttype!"=="5" (
        set installertype=exe
        set /p silentparam="Enter silent parameter: "
        echo [OK] Custom EXE - Silent: !silentparam!
    )
    if "!insttype!"=="6" (
        set installertype=powershell
        set silentparam=
        echo [OK] PowerShell script selected
    )
    if "!insttype!"=="7" (
        set installertype=batch
        set silentparam=
        echo [OK] Batch file selected
    )
    if "!insttype!"=="8" (
        echo [OK] Skipped - configure manually later
    )
)

REM Create control file with extended metadata
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

REM Create setup script based on detected type
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
    echo ; TODO: Set your setup filename here >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
    echo Set $SetupFile$ = "%%ScriptPath%%\files\YOUR_FILE_HERE" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
) else (
    echo Set $SetupFile$ = "%%ScriptPath%%\files\!setupfilename!" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
)

echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo Message "Installing " + $ProductId$ + " ..." >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo comment "Start setup program" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
echo ChangeDirectory "%%ScriptPath%%\files" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"

REM Different Winbatch calls depending on installer type
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

REM Create uninstall script
echo ; Uninstall script for %pkgname% > "%pkgdir%\CLIENT_DATA\uninstall.opsiscript"
echo [Actions] >> "%pkgdir%\CLIENT_DATA\uninstall.opsiscript"
echo Message "Uninstalling %pkgname%" >> "%pkgdir%\CLIENT_DATA\uninstall.opsiscript"

echo.
echo ===================================
echo PACKAGE CREATED SUCCESSFULLY!
echo ===================================
echo.
echo Package directory:
echo %pkgdir%
echo.
echo Opening Explorer...
start explorer "%pkgdir%"
echo.
echo --- OPSI SERVER CONNECTION ---
echo.
set /p connect="Would you like to connect to the OPSI server? (Y/N): "
if /i NOT "%connect%"=="Y" goto skip_ssh

echo.
echo Enter the connection details:
echo ------------------------------------
set /p opsiserver="OPSI Server (Enter = 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH User (Enter = root): "
if "%opsiuser%"=="" set opsiuser=root

echo.
echo Testing server connection...
ping -n 1 %opsiserver% >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Server not reachable!
    goto skip_ssh
)

echo [OK] Server reachable
echo.
echo ----------------------------------------
echo Package directory: %pkgdir%
echo Target server: %opsiserver%
echo ----------------------------------------
echo.
set /p readydeploy="Have you copied all setup files to CLIENT_DATA? (Y/N): "

REM Auto-detect setup file from files folder if not already set
if /i "%readydeploy%"=="Y" (
    if "!setupfilename!"=="" (
        echo.
        echo [AUTO] Scanning CLIENT_DATA\files for setup file...
        for %%F in ("%pkgdir%\CLIENT_DATA\files\*.bat" "%pkgdir%\CLIENT_DATA\files\*.cmd" "%pkgdir%\CLIENT_DATA\files\*.exe" "%pkgdir%\CLIENT_DATA\files\*.msi" "%pkgdir%\CLIENT_DATA\files\*.ps1") do (
            if "!setupfilename!"=="" (
                set setupfilename=%%~nxF
                set setupext=%%~xF
                echo [AUTO] Found: !setupfilename!
            )
        )
        if not "!setupfilename!"=="" (
            REM Detect installer type and set silent params
            if /i "!setupext!"==".msi" (
                set installertype=msi
                set silentparam=/qn
                echo [AUTO] MSI installer - Silent: /qn
            )
            if /i "!setupext!"==".bat" (
                set installertype=batch
                set silentparam=
                echo [AUTO] Batch file detected
            )
            if /i "!setupext!"==".cmd" (
                set installertype=batch
                set silentparam=
                echo [AUTO] CMD file detected
            )
            if /i "!setupext!"==".ps1" (
                set installertype=powershell
                echo [AUTO] PowerShell script detected
            )
            if /i "!setupext!"==".exe" (
                set installertype=exe
                echo [AUTO] EXE installer detected
            )
            echo.
            echo [AUTO] Regenerating setup.opsiscript with !setupfilename!...
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
            echo Set $SetupFile$ = "%%ScriptPath%%\files\!setupfilename!" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
            echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
            echo Message "Installing " + $ProductId$ + " ..." >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
            echo. >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
            echo comment "Start setup program" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
            echo ChangeDirectory "%%ScriptPath%%\files" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
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
            echo if ^($ExitCode$ = "0"^) >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
            echo     comment "Setup successful" >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
            echo else >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
            echo     logError "Setup failed with exit code: " + $ExitCode$ >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
            echo     isFatalError >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
            echo endif >> "%pkgdir%\CLIENT_DATA\setup.opsiscript"
            echo [OK] setup.opsiscript updated
        ) else (
            echo [WARNING] No setup file found in CLIENT_DATA\files!
        )
    )
)

if /i NOT "%readydeploy%"=="Y" (
    echo.
    echo Please copy all required files to:
    echo %pkgdir%\CLIENT_DATA\
    echo.
    echo Then run these commands manually:
    echo ----------------------------------------
    echo scp -r "%pkgdir%" %opsiuser%@%opsiserver%:/var/lib/opsi/workbench/
    echo ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver%
    echo opsi-makepackage %pkgid%_%pkgversion%
    echo opsi-package-manager -i %pkgid%_%pkgversion%.opsi
    echo ----------------------------------------
    goto skip_ssh
)

echo.
echo [AUTOMATIC DEPLOYMENT STARTING]
echo ==================================
echo.

echo Step 1/4: Copying package to OPSI server...
echo.
scp -r "%pkgdir%" %opsiuser%@%opsiserver%:/var/lib/opsi/workbench/
if errorlevel 1 (
    echo [ERROR] Transfer failed
    echo SSH/SCP might be missing. Install with:
    echo   winget install OpenSSH.Client
    goto skip_ssh
)
echo [OK] Package copied to server
echo.

echo Step 2/4: Building OPSI package...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "cd /var/lib/opsi/workbench && rm -f %pkgid%_%pkgversion%-*.opsi 2>/dev/null; opsi-makepackage %pkgid%_%pkgversion%"
echo.

echo Step 3/4: Installing in OPSI...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-package-manager -q -i /var/lib/opsi/workbench/%pkgid%_%pkgversion%-1.opsi"
if errorlevel 1 (
    echo [WARNING] Installation may have failed
) else (
    echo [OK] Package installed
)
echo.

echo Step 4/4: Verifying installation...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-package-manager -l | grep -i %pkgid%"
echo.

echo ==================================
echo DEPLOYMENT COMPLETE!
echo ==================================
echo.
echo The package is now available in OPSI Configed.
echo You can assign it to clients.

:skip_ssh

echo.
pause
goto menu

:update
cls
echo.
echo === UPDATE PACKAGE ===
echo.
set /p opsiserver="OPSI Server (Enter = 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH User (Enter = root): "
if "%opsiuser%"=="" set opsiuser=root

echo.
echo Testing server connection...
ping -n 1 %opsiserver% >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Server not reachable!
    pause
    goto menu
)

echo.
echo Loading installed packages from server...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-package-manager -l | tail -n +4 | awk '{print $1}' | sort"
echo.
set /p pkgupdate="Which package to update? (Enter package ID): "

echo.
echo Checking if workbench folder exists...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "if [ -d /var/lib/opsi/workbench/%pkgupdate%_* ]; then echo 'Workbench folder found'; else echo 'No workbench folder - copying from depot...'; cp -r /var/lib/opsi/depot/%pkgupdate% /var/lib/opsi/workbench/%pkgupdate%_update 2>/dev/null || echo '[WARNING] Depot folder not found'; fi"

echo.
set /p newversion="New version (Enter = keep version): "

echo.
echo [1] Replace setup files
echo [2] Edit control file
echo [3] Update scripts
echo [4] Update everything
set /p updatetype="What should be updated? (1-4): "

if "%updatetype%"=="1" (
    echo.
    set /p newsetup="Path to new setup file: "
    echo Copying new setup file to server...
    ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "find /var/lib/opsi/workbench -maxdepth 2 -name '%pkgupdate%*' -type d | head -1" > %temp%\pkgdir.txt
    set /p pkgdir=<%temp%\pkgdir.txt
    scp "%newsetup%" %opsiuser%@%opsiserver%:%pkgdir%/CLIENT_DATA/files/
    echo [OK] Setup file updated
)

echo.
echo Searching workbench folder and rebuilding package...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "pkgdir=$(find /var/lib/opsi/workbench -maxdepth 2 -name '%pkgupdate%*' -type d | head -1); if [ -n \"$pkgdir\" ]; then cd \"$pkgdir\" && cd .. && opsi-makepackage \"$(basename $pkgdir)\"; else echo '[ERROR] No workbench folder found'; fi"
echo.
echo Installing updated package...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "latest=$(ls -t /var/lib/opsi/workbench/%pkgupdate%*.opsi 2>/dev/null | head -1); if [ -n \"$latest\" ]; then opsi-package-manager -q -i \"$latest\"; else echo '[ERROR] No package found'; fi"

echo.
echo [OK] Package updated!
pause
goto menu

:delete
cls
echo.
echo === DELETE PACKAGE ===
echo.

set /p opsiserver="OPSI Server (Enter = 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH User (Enter = root): "
if "%opsiuser%"=="" set opsiuser=root

echo.
echo Installed packages:
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-package-manager -l"
echo.
echo === WORKBENCH PROJECTS (not installed) ===
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "cd /var/lib/opsi/workbench && for dir in */; do pkg=${dir%/}; pkgid=${pkg%%_*}; opsi-package-manager -l | grep -q \"^   $pkgid \" || echo $pkg; done 2>/dev/null"
echo.
set /p pkgdelete="Package ID or workbench folder to delete: "

echo.
echo WARNING: Package '%pkgdelete%' will be completely removed!
echo.
echo Delete options:
echo [1] Normal delete (recommended)
echo [2] With --purge (also removes all client assignments)
echo [3] Cancel
echo.
set /p deleteoption="Your choice (1-3): "

if "%deleteoption%"=="3" (
    echo Cancelled.
    pause
    goto menu
)

echo.
echo === DELETE PROCESS STARTING ===
echo.

REM Extract package ID: remove only _VERSION at the end (e.g. _1.0.0)
REM Extract server-side to handle complex names like opsi-hotfix correctly
echo Determining package ID...
for /f "delims=" %%i in ('ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "echo '%pkgdelete%' | sed 's/_[0-9][0-9.]*[-0-9]*$//' "') do set pkgid=%%i
if "%pkgid%"=="" set pkgid=%pkgdelete%
echo Package ID: %pkgid%

echo.
echo Checking if package is installed...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-package-manager -l | grep -q \"   %pkgid% \" && echo '[INFO] Package is installed' || echo '[INFO] Only in workbench'"

if "%deleteoption%"=="1" (
    echo Deleting package '%pkgid%' ...
    ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "TERM=dumb opsi-package-manager -q -r %pkgid% 2>/dev/null"
    if errorlevel 1 (
        echo [INFO] Package not installed or error during deletion
    ) else (
        echo [OK] Package removed from OPSI
    )
) else if "%deleteoption%"=="2" (
    echo Deleting package '%pkgid%' with --purge ...
    ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "TERM=dumb opsi-package-manager -q -r %pkgid% --purge 2>/dev/null"
    if errorlevel 1 (
        echo [INFO] Package not installed or error during deletion
    ) else (
        echo [OK] Package removed from OPSI (including client assignments)
    )
)

echo.
echo Cleaning up workbench and repository...
ssh -o ConnectTimeout=10 -o ServerAliveInterval=5 %opsiuser%@%opsiserver% "rm -rf /var/lib/opsi/workbench/'%pkgid%'* /var/lib/opsi/workbench/'%pkgdelete%'* /var/lib/opsi/repository/'%pkgid%'* /var/lib/opsi/depot/'%pkgid%' 2>/dev/null; echo '[OK] Cleanup complete'"

echo.
echo Checking if package was removed...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-package-manager -l | grep -q -i '%pkgid%'"
if errorlevel 1 (
    echo [OK] Package '%pkgid%' successfully removed!
    echo.
    pause
    goto menu
)

echo [INFO] Package still present - AGGRESSIVE DELETE...
echo.

ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "echo '=== DELETING EVERYTHING FOR %pkgid% ==='; opsi-admin -d method productOnClient_delete '*' '%pkgid%' 2>/dev/null; opsi-admin -d method productPropertyState_delete '*' '%pkgid%' '*' 2>/dev/null; opsi-admin -d method productDependency_delete '%pkgid%' '*' '*' '*' '*' 2>/dev/null; opsi-admin -d method productProperty_delete '%pkgid%' '*' '*' 2>/dev/null; opsi-admin -d method productOnDepot_delete '%pkgid%' '*' 2>/dev/null; opsi-admin -d method product_delete '%pkgid%' 2>/dev/null; opsi-package-manager -r '%pkgid%' --purge 2>/dev/null; opsi-package-manager -r '%pkgid%' 2>/dev/null; rm -rf /var/lib/opsi/workbench/%pkgid%* /var/lib/opsi/workbench/%pkgdelete%* 2>/dev/null; rm -rf /var/lib/opsi/repository/%pkgid%* 2>/dev/null; rm -rf /var/lib/opsi/depot/%pkgid% 2>/dev/null; opsiconfd reload 2>/dev/null; echo '=== DONE ==='"

echo Final check...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-package-manager -l | grep -q -i '%pkgid%'"
if errorlevel 1 (
    echo [OK] Package '%pkgid%' successfully removed!
) else (
    echo [ERROR] Package '%pkgid%' could not be removed!
    echo Please check manually on the server.
)

echo.
pause
goto menu

:listpackages
cls
echo.
echo === SHOW SERVER PACKAGES ===
echo.
set /p opsiserver="OPSI Server (Enter = 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH User (Enter = root): "
if "%opsiuser%"=="" set opsiuser=root

echo.
echo Testing server connection...
ping -n 1 %opsiserver% >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Server not reachable!
    pause
    goto menu
)

echo.
echo ===== INSTALLED PACKAGES =====
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-package-manager -l"
echo.
echo ===== WORKBENCH PACKAGES =====
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "ls -la /var/lib/opsi/workbench/"
echo.
pause
goto menu

:advanced
cls
echo.
echo === ADVANCED OPTIONS ===
echo.
echo [1] Set up SSH key
echo [2] Show server logs
echo [3] Check client status
echo [4] Synchronize depot
echo [5] Wake on LAN
echo [6] Shutdown clients
echo [7] Reboot clients
echo [8] Execute command on client
echo [9] Back to main menu
echo.
set /p advchoice="Your choice: "

if "%advchoice%"=="1" (
    echo.
    echo === AUTOMATIC SSH KEY SETUP ===
    echo.
    set /p opsiserver="OPSI Server (Enter = 10.1.0.2): "
    if "!opsiserver!"=="" set opsiserver=10.1.0.2
    set /p opsiuser="SSH User (Enter = root): "
    if "!opsiuser!"=="" set opsiuser=root
    echo.
    echo Step 1/4: Checking if SSH key exists...
    if exist "%USERPROFILE%\.ssh\id_rsa.pub" (
        echo [OK] SSH key already exists
    ) else (
        echo [INFO] No SSH key found - creating new key...
        echo.
        if not exist "%USERPROFILE%\.ssh" mkdir "%USERPROFILE%\.ssh"
        ssh-keygen -t rsa -b 4096 -f "%USERPROFILE%\.ssh\id_rsa" -N ""
        if errorlevel 1 (
            echo [ERROR] Key generation failed
            echo Make sure OpenSSH is installed:
            echo   winget install Microsoft.OpenSSH.Client
            pause
            goto advanced
        )
        echo [OK] SSH key created
    )
    echo.
    echo Step 2/4: Testing server reachability...
    ping -n 1 !opsiserver! >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Server !opsiserver! not reachable!
        pause
        goto advanced
    )
    echo [OK] Server reachable
    echo.
    echo Step 3/4: Copying public key to server...
    echo [INFO] You will be asked for the password for !opsiuser!@!opsiserver!
    echo.
    type "%USERPROFILE%\.ssh\id_rsa.pub" | ssh -o ConnectTimeout=10 !opsiuser!@!opsiserver! "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
    if errorlevel 1 (
        echo [ERROR] Key copy failed
        pause
        goto advanced
    )
    echo [OK] Public key copied to server
    echo.
    echo Step 4/4: Testing passwordless connection...
    ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new !opsiuser!@!opsiserver! "echo SSH connection successful"
    if errorlevel 1 (
        echo [WARNING] Passwordless connection not yet possible
        echo Try again or check the server configuration
    ) else (
        echo.
        echo ====================================
        echo SSH KEY SETUP SUCCESSFUL!
        echo ====================================
        echo You can now connect without a password.
    )
    echo.
    pause
    goto advanced
)

if "%advchoice%"=="2" (
    set /p opsiserver="OPSI Server (Enter = 10.1.0.2): "
    if "%opsiserver%"=="" set opsiserver=10.1.0.2
    set /p opsiuser="SSH User (Enter = root): "
    if "%opsiuser%"=="" set opsiuser=root
    echo.
    echo === AVAILABLE LOG FILES ===
    ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "ls -la /var/log/opsi/*.log 2>/dev/null | tail -10"
    echo.
    echo === LATEST PACKAGE.LOG ENTRIES ===
    ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "if [ -f /var/log/opsi/package.log ]; then tail -20 /var/log/opsi/package.log; else echo 'package.log not found'; fi"
    echo.
    echo === LATEST OPSICONFD.LOG ENTRIES ===
    ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "if [ -f /var/log/opsi/opsiconfd.log ]; then tail -20 /var/log/opsi/opsiconfd.log; else echo 'opsiconfd.log not found'; fi"
    echo.
    echo === LATEST CLIENT LOGS ===
    ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "ls -lt /var/log/opsi/clientconnect/*.log 2>/dev/null | head -5"
    pause
)

if "%advchoice%"=="3" goto clientstatus

if "%advchoice%"=="4" (
    set /p opsiserver="OPSI Server (Enter = 10.1.0.2): "
    if "%opsiserver%"=="" set opsiserver=10.1.0.2
    set /p opsiuser="SSH User (Enter = root): "
    if "%opsiuser%"=="" set opsiuser=root
    echo Synchronizing depot...
    ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-package-updater -v update"
    pause
)

if "%advchoice%"=="5" goto wakeonlan
if "%advchoice%"=="6" goto shutdownclients
if "%advchoice%"=="7" goto rebootclients
if "%advchoice%"=="8" goto execcommand
if "%advchoice%"=="9" goto menu

goto menu

:clientstatus
cls
echo.
echo === CHECK CLIENT STATUS ===
echo.
set opsiserver=10.1.0.2
set opsiuser=root
set /p opsiserver="OPSI Server [%opsiserver%]: "
set /p opsiuser="SSH User [%opsiuser%]: "
echo.
echo Connecting to %opsiuser%@%opsiserver%...
echo.
echo === REGISTERED CLIENTS ===
ssh -o ConnectTimeout=10 -o ServerAliveInterval=5 %opsiuser%@%opsiserver% "opsi-admin -d method host_getIdents 2>/dev/null"
if errorlevel 1 echo [ERROR] Could not retrieve clients
echo.
echo === REACHABLE CLIENTS ===
ssh -o ConnectTimeout=10 -o ServerAliveInterval=5 %opsiuser%@%opsiserver% "opsi-admin -d method hostControl_reachable 2>/dev/null | grep true"
if errorlevel 1 echo [INFO] No reachable clients found
echo.
echo Done.
pause
goto advanced

:wakeonlan
cls
echo.
echo === WAKE ON LAN ===
echo.
set /p opsiserver="OPSI Server (Enter = 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH User (Enter = root): "
if "%opsiuser%"=="" set opsiuser=root
echo.
echo Fetching client list...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method host_getIdents"
echo.
echo [1] Wake single client
echo [2] Wake by pattern (e.g. 405-pc-*)
echo [3] Wake all clients
echo [4] Cancel
echo.
set /p wolchoice="Your choice: "

if "%wolchoice%"=="1" goto wolsingle
if "%wolchoice%"=="2" goto wolpattern
if "%wolchoice%"=="3" goto wolall
goto advanced

:wolsingle
set /p wolclient="Enter client FQDN: "

REM Auto-complete FQDN if user entered short name (no dots)
echo %wolclient% | find "." >nul
if errorlevel 1 (
    echo Resolving full FQDN for '%wolclient%'...
    for /f "delims=" %%i in ('ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method host_getIdents | tr -d '[]\",' | grep -i '^%wolclient%\.' | head -1"') do set wolclient=%%i
    if "!wolclient!"=="" (
        echo [ERROR] Client not found
        pause
        goto advanced
    )
    echo Found: !wolclient!
)
echo.
echo Sending WOL packet to %wolclient%...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method hostControl_start '%wolclient%'"
if errorlevel 1 (
    echo [ERROR] WOL failed
) else (
    echo [OK] WOL packet sent to %wolclient%
)
pause
goto advanced

:wolpattern
set /p wolpattern="Enter pattern (e.g. 405-pc or laptop): "
echo.
echo Waking clients matching '%wolpattern%'...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method host_getIdents | tr -d '[]\",' | grep -i '%wolpattern%' | while read client; do echo \"Waking $client...\"; opsi-admin -d method hostControl_start \"$client\"; done"
echo [OK] WOL packets sent to matching clients
pause
goto advanced

:wolall
echo.
echo Waking all clients...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method hostControl_start"
echo [OK] WOL packets sent
pause
goto advanced

:shutdownclients
cls
echo.
echo === SHUTDOWN CLIENTS ===
echo.
set /p opsiserver="OPSI Server (Enter = 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH User (Enter = root): "
if "%opsiuser%"=="" set opsiuser=root
echo.
echo Fetching client list...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method host_getIdents"
echo.
echo [1] Shutdown single client
echo [2] Shutdown by pattern (e.g. 405-pc-*)
echo [3] Shutdown ALL clients (DANGEROUS!)
echo [4] Cancel
echo.
set /p sdchoice="Your choice: "

if "%sdchoice%"=="1" goto sdsingle
if "%sdchoice%"=="2" goto sdpattern
if "%sdchoice%"=="3" goto sdall
goto advanced

:sdsingle
set /p sdclient="Enter client FQDN: "

REM Auto-complete FQDN if user entered short name (no dots)
echo %sdclient% | find "." >nul
if errorlevel 1 (
    echo Resolving full FQDN for '%sdclient%'...
    for /f "delims=" %%i in ('ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method host_getIdents | tr -d '[]\",' | grep -i '^%sdclient%\.' | head -1"') do set sdclient=%%i
    if "!sdclient!"=="" (
        echo [ERROR] Client not found
        pause
        goto advanced
    )
    echo Found: !sdclient!
)
echo.
echo Shutting down %sdclient%...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method hostControlSafe_shutdown '%sdclient%'"
echo [OK] Shutdown command sent to %sdclient%
pause
goto advanced

:sdpattern
set /p sdpattern="Enter pattern (e.g. 405-pc or laptop): "
echo.
echo Shutting down clients matching '%sdpattern%'...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method host_getIdents | tr -d '[]\",' | grep -i '%sdpattern%' | while read client; do echo \"Shutting down $client...\"; opsi-admin -d method hostControlSafe_shutdown \"$client\"; done"
echo [OK] Shutdown commands sent to matching clients
pause
goto advanced

:sdall
echo.
echo WARNING: This will shutdown ALL clients!
set /p sdconfirm="Type YES to confirm: "
if not "%sdconfirm%"=="YES" goto advanced
echo.
echo Shutting down all clients...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method hostControlSafe_shutdown '*'"
echo [OK] Shutdown commands sent to all clients
pause
goto advanced

:rebootclients
cls
echo.
echo === REBOOT CLIENTS ===
echo.
set /p opsiserver="OPSI Server (Enter = 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH User (Enter = root): "
if "%opsiuser%"=="" set opsiuser=root
echo.
echo Fetching client list...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method host_getIdents"
echo.
echo [1] Reboot single client
echo [2] Reboot by pattern (e.g. 405-pc-*)
echo [3] Reboot ALL clients (DANGEROUS!)
echo [4] Cancel
echo.
set /p rbchoice="Your choice: "

if "%rbchoice%"=="1" goto rbsingle
if "%rbchoice%"=="2" goto rbpattern
if "%rbchoice%"=="3" goto rball
goto advanced

:rbsingle
set /p rbclient="Enter client FQDN: "

REM Auto-complete FQDN if user entered short name (no dots)
echo %rbclient% | find "." >nul
if errorlevel 1 (
    echo Resolving full FQDN for '%rbclient%'...
    for /f "delims=" %%i in ('ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method host_getIdents | tr -d '[]\",' | grep -i '^%rbclient%\.' | head -1"') do set rbclient=%%i
    if "!rbclient!"=="" (
        echo [ERROR] Client not found
        pause
        goto advanced
    )
    echo Found: !rbclient!
)
echo.
echo Rebooting %rbclient%...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method hostControlSafe_reboot '%rbclient%'"
echo [OK] Reboot command sent to %rbclient%
pause
goto advanced

:rbpattern
set /p rbpattern="Enter pattern (e.g. 405-pc or laptop): "
echo.
echo Rebooting clients matching '%rbpattern%'...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method host_getIdents | tr -d '[]\",' | grep -i '%rbpattern%' | while read client; do echo \"Rebooting $client...\"; opsi-admin -d method hostControlSafe_reboot \"$client\"; done"
echo [OK] Reboot commands sent to matching clients
pause
goto advanced

:rball
echo.
echo WARNING: This will reboot ALL clients!
set /p rbconfirm="Type YES to confirm: "
if not "%rbconfirm%"=="YES" goto advanced
echo.
echo Rebooting all clients...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method hostControlSafe_reboot '*'"
echo [OK] Reboot commands sent to all clients
pause
goto advanced

:execcommand
cls
echo.
echo === EXECUTE COMMAND ON CLIENT ===
echo.
set /p opsiserver="OPSI Server (Enter = 10.1.0.2): "
if "%opsiserver%"=="" set opsiserver=10.1.0.2
set /p opsiuser="SSH User (Enter = root): "
if "%opsiuser%"=="" set opsiuser=root
echo.
echo Fetching client list...
ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method host_getIdents"
echo.
set /p execclient="Enter client FQDN: "

REM Auto-complete FQDN if user entered short name (no dots)
echo %execclient% | find "." >nul
if errorlevel 1 (
    echo Resolving full FQDN for '%execclient%'...
    for /f "delims=" %%i in ('ssh -o ConnectTimeout=10 %opsiuser%@%opsiserver% "opsi-admin -d method host_getIdents | tr -d '[]\",' | grep -i '^%execclient%\.' | head -1"') do set execclient=%%i
    if "!execclient!"=="" (
        echo [ERROR] Client '%execclient%' not found
        pause
        goto advanced
    )
    echo Found: !execclient!
)
echo.
echo Example commands:
echo   - cmd.exe /c "ipconfig /all"
echo   - cmd.exe /c "whoami"
echo   - cmd.exe /c "systeminfo"
echo   - powershell.exe -Command "Get-Process"
echo.
set /p execcmd="Enter command to execute: "
echo.
echo Executing on %execclient%...
ssh -o ConnectTimeout=30 %opsiuser%@%opsiserver% "opsi-admin -d method hostControlSafe_execute '%execcmd%' '%execclient%'"
echo.
echo [OK] Command executed
pause
goto advanced

:help
cls
echo.
echo === HELP ===
echo.
echo OPSI PackForge v2.0 - Professional OPSI Package Management
echo.
echo FEATURES:
echo -----------
echo [1] Create new package
echo     - Full metadata support
echo     - Automatic silent parameter detection
echo     - Multi-file support
echo.
echo [2] Update package
echo     - Replace setup files
echo     - Versioning
echo     - Live update in depot
echo.
echo [3] Delete package
echo     - Safe removal from server
echo     - Client check
echo.
echo [4] Show server packages
echo     - Installed packages
echo     - Workbench contents
echo.
echo [5] Advanced options
echo     - SSH key setup
echo     - Log display
echo     - Client status
echo     - Depot sync
echo.
echo TIPS:
echo ------
echo - Set up SSH keys for passwordless access
echo - Always place setup files in CLIENT_DATA/files/
echo - Use version numbers in X.Y.Z format
echo.
echo OPSI Server: 10.1.0.2 (backup.paedml-linux.lokal)
echo GitHub: https://github.com/Elliot-Markus-John-Adams/opsi-packforge
echo.
pause
goto menu
'@

        $batchScript | Out-File -FilePath "$appPath\opsi_packforge.bat" -Encoding ASCII
        Write-Host "OK - Application created" -ForegroundColor Green
        Write-Host ""

        # Step 5
        Write-Host "Step 5: Creating desktop shortcut..." -ForegroundColor Yellow
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
            Write-Host "OK - Desktop shortcut created" -ForegroundColor Green
        } catch {
            Write-Host "WARNING: Desktop shortcut could not be created" -ForegroundColor Yellow
            Write-Host "         Start the application manually:" -ForegroundColor Yellow
            Write-Host "         $appPath\opsi_packforge.bat" -ForegroundColor Cyan
        }
        Write-Host ""

        Write-Host "Installation complete!" -ForegroundColor Green
        Write-Host "Installed in: $installPath" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Start with:" -ForegroundColor Yellow
        Write-Host "- Desktop shortcut 'OPSI PackForge'" -ForegroundColor White
        Write-Host "- Or directly: $appPath\opsi_packforge.bat" -ForegroundColor White
        Write-Host ""

        $startNow = Read-Host "Would you like to start OPSI PackForge now? (Y/N)"
        if ($startNow -eq "Y" -or $startNow -eq "y") {
            Start-Process "$appPath\opsi_packforge.bat"
        }
    }

    "2" {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit
    }

    default {
        Write-Host "Invalid selection!" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
