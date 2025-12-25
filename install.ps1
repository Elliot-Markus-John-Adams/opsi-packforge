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
            
            # Schritt 4
            Write-Host "Schritt 4: Erstelle OPSI PackForge GUI..." -ForegroundColor Yellow
            $appPath = "$installPath\app"
            New-Item -ItemType Directory -Path $appPath -Force | Out-Null
            
            # Erstelle die GUI-Anwendung direkt
            $guiCode = @'
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime

class OPSIPackForge:
    def __init__(self, root):
        self.root = root
        self.root.title("OPSI PackForge v1.0")
        self.root.geometry("600x400")
        
        # Header
        header = tk.Label(root, text="OPSI PackForge", font=("Arial", 16, "bold"))
        header.pack(pady=10)
        
        # Form
        frame = ttk.Frame(root, padding="20")
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Paket-ID:").grid(row=0, column=0, sticky="w", pady=5)
        self.package_id = ttk.Entry(frame, width=30)
        self.package_id.grid(row=0, column=1, pady=5)
        
        ttk.Label(frame, text="Name:").grid(row=1, column=0, sticky="w", pady=5)
        self.package_name = ttk.Entry(frame, width=30)
        self.package_name.grid(row=1, column=1, pady=5)
        
        ttk.Label(frame, text="Version:").grid(row=2, column=0, sticky="w", pady=5)
        self.package_version = ttk.Entry(frame, width=30)
        self.package_version.grid(row=2, column=1, pady=5)
        
        # Button
        ttk.Button(frame, text="Paket generieren", command=self.generate).grid(row=3, column=0, columnspan=2, pady=20)
        
    def generate(self):
        if not all([self.package_id.get(), self.package_name.get(), self.package_version.get()]):
            messagebox.showerror("Fehler", "Bitte alle Felder ausfuellen!")
            return
        
        output_dir = filedialog.askdirectory(title="Ausgabe-Verzeichnis waehlen")
        if output_dir:
            pkg_dir = os.path.join(output_dir, f"{self.package_id.get()}_{self.package_version.get()}")
            os.makedirs(os.path.join(pkg_dir, "OPSI"), exist_ok=True)
            os.makedirs(os.path.join(pkg_dir, "CLIENT_DATA"), exist_ok=True)
            
            # Control file
            with open(os.path.join(pkg_dir, "OPSI", "control"), "w") as f:
                f.write(f"[Product]\nid: {self.package_id.get()}\nname: {self.package_name.get()}\nversion: {self.package_version.get()}\n")
            
            messagebox.showinfo("Erfolg", f"Paket erstellt in:\n{pkg_dir}")

root = tk.Tk()
app = OPSIPackForge(root)
root.mainloop()
'@
            
            $guiCode | Out-File -FilePath "$appPath\opsi_packforge.py" -Encoding UTF8
            Write-Host "OK - GUI erstellt" -ForegroundColor Green
            Write-Host ""
            
            # Schritt 5
            Write-Host "Schritt 5: Erstelle Desktop-Verknuepfung..." -ForegroundColor Yellow
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\OPSI PackForge.lnk")
            $Shortcut.TargetPath = "$installPath\python\python.exe"
            $Shortcut.Arguments = "`"$appPath\opsi_packforge.py`""
            $Shortcut.WorkingDirectory = $appPath
            $Shortcut.Description = "OPSI PackForge"
            $Shortcut.Save()
            Write-Host "OK - Desktop-Verknuepfung erstellt" -ForegroundColor Green
            Write-Host ""
            
            Write-Host "Installation abgeschlossen!" -ForegroundColor Green
            Write-Host "Installiert in: $installPath" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Starten mit:" -ForegroundColor Yellow
            Write-Host "- Desktop-Verknuepfung 'OPSI PackForge'" -ForegroundColor White
            Write-Host "- Oder: $installPath\python\python.exe $appPath\opsi_packforge.py" -ForegroundColor White
            
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