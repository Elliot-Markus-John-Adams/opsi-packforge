# OPSI PackForge - One-Line Installer
# Usage: irm https://raw.githubusercontent.com/elliot-markus-john-adams/opsi-packforge/main/install.ps1 | iex

$ErrorActionPreference = "SilentlyContinue"
$installDir = "$env:LOCALAPPDATA\OPSI-PackForge"
$appScript = "$installDir\packforge.pyw"
$repoBase = "https://raw.githubusercontent.com/elliot-markus-john-adams/opsi-packforge/main"

Write-Host ""
Write-Host "  OPSI PackForge Installer" -ForegroundColor Cyan
Write-Host "  ========================" -ForegroundColor Cyan
Write-Host ""

# Function to find Python executable
function Find-Python {
    # Check PATH first
    $pythonPath = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    if ($pythonPath) { return $pythonPath }

    # Check common install locations
    $locations = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "$env:ProgramFiles\Python311\python.exe"
    )
    foreach ($loc in $locations) {
        if (Test-Path $loc) { return $loc }
    }
    return $null
}

function Find-Pythonw {
    $python = Find-Python
    if ($python) {
        $pythonw = $python -replace "python\.exe$", "pythonw.exe"
        if (Test-Path $pythonw) { return $pythonw }
    }
    return $null
}

# Check if Python with tkinter is available
$pythonExe = Find-Python
$pythonOk = $false

if ($pythonExe) {
    $result = & $pythonExe -c "import tkinter; print('ok')" 2>$null
    if ($result -eq "ok") { $pythonOk = $true }
}

if (-not $pythonOk) {
    Write-Host "  [!] Python with tkinter not found" -ForegroundColor Yellow
    Write-Host "  [*] Installing Python via winget..." -ForegroundColor Cyan

    winget install Python.Python.3.12 --source winget --silent --accept-package-agreements --accept-source-agreements 2>$null

    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    # Find Python again after install
    Start-Sleep -Seconds 2
    $pythonExe = Find-Python

    if (-not $pythonExe) {
        Write-Host "  [!] Python not in PATH yet. Searching..." -ForegroundColor Yellow
        $pythonExe = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
        if (-not (Test-Path $pythonExe)) {
            Write-Host "  [ERROR] Could not find Python after installation" -ForegroundColor Red
            Write-Host "  Please restart PowerShell and run this command again." -ForegroundColor Yellow
            Write-Host ""
            pause
            exit 1
        }
    }
    Write-Host "  [OK] Python installed: $pythonExe" -ForegroundColor Green
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

# Find pythonw.exe
$pythonwExe = Find-Pythonw
if (-not $pythonwExe) {
    # Fallback: use python.exe instead
    $pythonwExe = $pythonExe
}

# Create desktop shortcut
Write-Host "  [*] Creating shortcut..." -ForegroundColor Cyan
try {
    $desktop = [Environment]::GetFolderPath("Desktop")
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$desktop\OPSI PackForge.lnk")
    $Shortcut.TargetPath = $pythonwExe
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
Start-Process $pythonwExe -ArgumentList "`"$appScript`""
