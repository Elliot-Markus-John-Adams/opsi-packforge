# OPSI PackForge - Schnellstart Script
# Startet OPSI PackForge direkt wenn installiert

$appPath = "$env:LOCALAPPDATA\OPSI-PackForge\app\opsi_packforge.bat"

if (Test-Path $appPath) {
    Write-Host "Starte OPSI PackForge..." -ForegroundColor Green
    Start-Process $appPath
} else {
    Write-Host "OPSI PackForge nicht gefunden. Bitte erst installieren:" -ForegroundColor Yellow
    Write-Host "[System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials; iex ((New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/Elliot-Markus-John-Adams/opsi-packforge/main/install.ps1'))" -ForegroundColor Cyan
}