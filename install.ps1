# paedML OPSI PackForge Installer
# Dieses Script lädt die aktuelle Version von OPSI PackForge herunter und startet es

param(
    [string]$GithubUser = "Elliot-Markus-John-Adams",
    [string]$Repo = "opsi-packforge",
    [switch]$Update,
    [switch]$Debug
)

$ErrorActionPreference = "Continue"
$ProgressPreference = 'SilentlyContinue'

# Farben für die Konsole
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  paedML OPSI PackForge Installer  " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Prüfe Admin-Rechte
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[WARNUNG] Script wird ohne Administrator-Rechte ausgeführt." -ForegroundColor Yellow
    Write-Host "         Einige Funktionen könnten eingeschränkt sein." -ForegroundColor Yellow
    Write-Host ""
}

# Arbeitsverzeichnis
$WorkDir = "$env:LOCALAPPDATA\OPSI-PackForge"
$PythonDir = "$WorkDir\python"
$AppDir = "$WorkDir\app"

# Erstelle Arbeitsverzeichnis
if (-not (Test-Path $WorkDir)) {
    Write-Host "[INFO] Erstelle Arbeitsverzeichnis: $WorkDir" -ForegroundColor Green
    New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
}

# Python Portable herunterladen und installieren
function Install-PortablePython {
    Write-Host "[INFO] Installiere Python Portable..." -ForegroundColor Green
    
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
    $pipUrl = "https://bootstrap.pypa.io/get-pip.py"
    
    $pythonZip = "$WorkDir\python.zip"
    
    try {
        if (-not (Test-Path $PythonDir)) {
            Write-Host "      Lade Python herunter..." -ForegroundColor Gray
            Write-Host "      URL: $pythonUrl" -ForegroundColor DarkGray
            
            # Alternative Download-Methode mit besserem Proxy-Support
            $client = New-Object System.Net.WebClient
            $client.Proxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials
            $client.DownloadFile($pythonUrl, $pythonZip)
            
            Write-Host "      Entpacke Python..." -ForegroundColor Gray
            Expand-Archive -Path $pythonZip -DestinationPath $PythonDir -Force
            Remove-Item $pythonZip
            
            # Python konfigurieren für pip
            $pthFile = "$PythonDir\python311._pth"
            if (Test-Path $pthFile) {
                $content = Get-Content $pthFile
                $content = $content -replace "#import site", "import site"
                $content += "`nLib\site-packages"
                Set-Content -Path $pthFile -Value $content
            }
            
            # Pip installieren - optional, da nicht zwingend erforderlich
            Write-Host "      Installiere pip (optional)..." -ForegroundColor Gray
            try {
                $getPip = "$WorkDir\get-pip.py"
                $client.DownloadFile($pipUrl, $getPip)
                & "$PythonDir\python.exe" $getPip --no-warn-script-location 2>$null
                Remove-Item $getPip -ErrorAction SilentlyContinue
            } catch {
                Write-Host "      [WARNUNG] Pip konnte nicht installiert werden (nicht kritisch)" -ForegroundColor Yellow
            }
        }
        
        Write-Host "[OK] Python ist installiert" -ForegroundColor Green
    } catch {
        Write-Host "[FEHLER] Python-Installation fehlgeschlagen: $_" -ForegroundColor Red
        throw
    }
}

# Anwendung herunterladen
function Download-Application {
    Write-Host "[INFO] Lade OPSI PackForge herunter..." -ForegroundColor Green
    
    $baseUrl = "https://raw.githubusercontent.com/$GithubUser/$Repo/main"
    
    # Erstelle App-Verzeichnis
    if (Test-Path $AppDir) {
        Remove-Item -Path $AppDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $AppDir -Force | Out-Null
    
    # Liste der herunterzuladenden Dateien
    $files = @(
        "src/opsi_packforge.py",
        "src/opsi_generator.py",
        "src/config.json",
        "requirements.txt"
    )
    
    $client = New-Object System.Net.WebClient
    $client.Proxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials
    
    foreach ($file in $files) {
        $url = "$baseUrl/$file"
        $filename = Split-Path $file -Leaf
        $destination = "$AppDir\$filename"
        
        Write-Host "      Lade $filename..." -ForegroundColor Gray
        try {
            $client.DownloadFile($url, $destination)
        } catch {
            Write-Host "[FEHLER] Konnte $filename nicht herunterladen: $_" -ForegroundColor Red
            Write-Host "      URL: $url" -ForegroundColor DarkGray
            return $false
        }
    }
    
    Write-Host "[OK] Anwendung heruntergeladen" -ForegroundColor Green
    return $true
}

# Python-Pakete installieren
function Install-PythonPackages {
    Write-Host "[INFO] Installiere Python-Pakete..." -ForegroundColor Green
    
    $requirementsFile = "$AppDir\requirements.txt"
    if (Test-Path $requirementsFile) {
        & "$PythonDir\python.exe" -m pip install --upgrade pip --no-warn-script-location 2>$null
        & "$PythonDir\python.exe" -m pip install -r $requirementsFile --no-warn-script-location 2>$null
    }
    
    Write-Host "[OK] Python-Pakete installiert" -ForegroundColor Green
}

# Desktop-Verknüpfung erstellen
function Create-DesktopShortcut {
    Write-Host "[INFO] Erstelle Desktop-Verknüpfung..." -ForegroundColor Green
    
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\OPSI PackForge.lnk")
    $Shortcut.TargetPath = "$PythonDir\pythonw.exe"
    $Shortcut.Arguments = "`"$AppDir\opsi_packforge.py`""
    $Shortcut.WorkingDirectory = $AppDir
    $Shortcut.IconLocation = "$PythonDir\python.exe"
    $Shortcut.Description = "OPSI PackForge - GUI für OPSI-Paket-Erstellung"
    $Shortcut.Save()
    
    Write-Host "[OK] Desktop-Verknüpfung erstellt" -ForegroundColor Green
}

# Hauptinstallation
try {
    # Debug-Modus
    if ($Debug) {
        $ErrorActionPreference = "Continue"
        $VerbosePreference = "Continue"
    }
    
    # Python installieren
    if (-not (Test-Path "$PythonDir\python.exe") -or $Update) {
        Install-PortablePython
    }
    
    # Anwendung herunterladen
    $downloadSuccess = Download-Application
    if (-not $downloadSuccess) {
        Write-Host "[FEHLER] Download fehlgeschlagen. Prüfen Sie die Internetverbindung." -ForegroundColor Red
        Read-Host "Drücken Sie Enter zum Beenden"
        exit 1
    }
    
    # Python-Pakete installieren (optional)
    Install-PythonPackages
    
    # Desktop-Verknüpfung erstellen
    Create-DesktopShortcut
    
    Write-Host ""
    Write-Host "====================================" -ForegroundColor Green
    Write-Host "  Installation erfolgreich!         " -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "OPSI PackForge wurde installiert in:" -ForegroundColor Cyan
    Write-Host "  $WorkDir" -ForegroundColor White
    Write-Host ""
    Write-Host "Starten Sie die Anwendung über:" -ForegroundColor Cyan
    Write-Host "  - Desktop-Verknüpfung 'OPSI PackForge'" -ForegroundColor White
    Write-Host "  - Oder direkt: $PythonDir\pythonw.exe `"$AppDir\opsi_packforge.py`"" -ForegroundColor White
    Write-Host ""
    
    # Frage ob die Anwendung gestartet werden soll
    Write-Host ""
    $response = Read-Host "Möchten Sie OPSI PackForge jetzt starten? (J/N)"
    if ($response -eq 'J' -or $response -eq 'j') {
        Write-Host "[INFO] Starte OPSI PackForge..." -ForegroundColor Green
        Start-Process -FilePath "$PythonDir\pythonw.exe" -ArgumentList "`"$AppDir\opsi_packforge.py`"" -WorkingDirectory $AppDir
    }
    
    Write-Host ""
    Write-Host "Installation beendet." -ForegroundColor Green
    Read-Host "Drücken Sie Enter zum Schließen"
    
} catch {
    Write-Host ""
    Write-Host "[FEHLER] Installation fehlgeschlagen!" -ForegroundColor Red
    Write-Host "        $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Bitte prüfen Sie:" -ForegroundColor Yellow
    Write-Host "  - Internetverbindung" -ForegroundColor Yellow
    Write-Host "  - Firewall-Einstellungen" -ForegroundColor Yellow
    Write-Host "  - Proxy-Einstellungen" -ForegroundColor Yellow
    Write-Host "  - GitHub Repository: https://github.com/$GithubUser/$Repo" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}