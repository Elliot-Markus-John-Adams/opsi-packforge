# OPSI PackForge - One-Line Installer
# Usage: irm https://raw.githubusercontent.com/elliot-markus-john-adams/opsi-packforge/main/install.ps1 | iex

$ErrorActionPreference = "Stop"
$installDir = "$env:LOCALAPPDATA\OPSI-PackForge"
$appScript = "$installDir\packforge.pyw"
$repoBase = "https://raw.githubusercontent.com/elliot-markus-john-adams/opsi-packforge/main"

Write-Host ""
Write-Host "  OPSI PackForge Installer" -ForegroundColor Cyan
Write-Host "  ========================" -ForegroundColor Cyan
Write-Host ""

# Check if Python with tkinter is available
$pythonOk = $false
try {
    $result = python -c "import tkinter; print('ok')" 2>$null
    if ($result -eq "ok") { $pythonOk = $true }
} catch {}

if (-not $pythonOk) {
    Write-Host "  [!] Python with tkinter not found" -ForegroundColor Yellow
    Write-Host "  [*] Installing Python via winget..." -ForegroundColor Cyan

    try {
        winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements

        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

        Write-Host "  [OK] Python installed" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Could not install Python automatically" -ForegroundColor Red
        Write-Host "  Please install Python manually: https://python.org/downloads" -ForegroundColor Yellow
        Write-Host "  Make sure to check 'Add to PATH' during installation!" -ForegroundColor Yellow
        pause
        exit 1
    }
}

Write-Host "  [OK] Python ready" -ForegroundColor Green

# Create install directory
Write-Host "  [*] Creating app directory..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

# Download the app
Write-Host "  [*] Downloading OPSI PackForge..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri "$repoBase/packforge.pyw" -OutFile $appScript -UseBasicParsing
    Write-Host "  [OK] Downloaded" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Download failed: $_" -ForegroundColor Red
    pause
    exit 1
}

# Create desktop shortcut
Write-Host "  [*] Creating shortcut..." -ForegroundColor Cyan
try {
    $desktop = [Environment]::GetFolderPath("Desktop")
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$desktop\OPSI PackForge.lnk")
    $Shortcut.TargetPath = "pythonw.exe"
    $Shortcut.Arguments = "`"$appScript`""
    $Shortcut.WorkingDirectory = $installDir
    $Shortcut.Description = "OPSI PackForge"
    $Shortcut.Save()
    Write-Host "  [OK] Desktop shortcut created" -ForegroundColor Green
} catch {
    Write-Host "  [!] Shortcut creation failed (not critical)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host "  Starting OPSI PackForge..." -ForegroundColor Cyan
Write-Host ""

# Launch the app
Start-Process pythonw.exe -ArgumentList "`"$appScript`""
