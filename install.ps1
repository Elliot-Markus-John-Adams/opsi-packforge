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
            Write-Host "OK - Python installiert" -ForegroundColor Green
            Write-Host ""
            
            Write-Host "Installation abgeschlossen!" -ForegroundColor Green
            Write-Host "Installiert in: $installPath" -ForegroundColor Cyan
            
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