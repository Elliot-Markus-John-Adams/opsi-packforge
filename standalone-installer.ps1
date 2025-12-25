# OPSI PackForge - Standalone Installer
# Alles in einem Script - keine externen Downloads nötig!

param(
    [switch]$Debug
)

Clear-Host
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  OPSI PackForge Standalone Setup  " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"
$WorkDir = "$env:LOCALAPPDATA\OPSI-PackForge"
$PythonDir = "$WorkDir\python"
$AppDir = "$WorkDir\app"

# Erstelle Arbeitsverzeichnis
Write-Host "[1/4] Erstelle Arbeitsverzeichnis..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
New-Item -ItemType Directory -Path $AppDir -Force | Out-Null
Write-Host "      ✓ $WorkDir" -ForegroundColor Green

# Python Portable installieren
Write-Host "[2/4] Installiere Python..." -ForegroundColor Yellow
if (-not (Test-Path "$PythonDir\python.exe")) {
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
    $pythonZip = "$WorkDir\python.zip"
    
    try {
        Write-Host "      Lade Python herunter (ca. 15 MB)..." -ForegroundColor Gray
        $wc = New-Object System.Net.WebClient
        $wc.Proxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials
        $wc.DownloadFile($pythonUrl, $pythonZip)
        
        Write-Host "      Entpacke..." -ForegroundColor Gray
        Expand-Archive -Path $pythonZip -DestinationPath $PythonDir -Force
        Remove-Item $pythonZip -Force
        
        # Python konfigurieren
        $pthFile = "$PythonDir\python311._pth"
        if (Test-Path $pthFile) {
            $content = Get-Content $pthFile
            $content = $content -replace "#import site", "import site"
            Set-Content -Path $pthFile -Value $content
        }
        Write-Host "      ✓ Python installiert" -ForegroundColor Green
    } catch {
        Write-Host "      ✗ Python-Download fehlgeschlagen" -ForegroundColor Red
        Write-Host "        Fehler: $_" -ForegroundColor Red
        Read-Host "Enter zum Beenden"
        exit 1
    }
} else {
    Write-Host "      ✓ Python bereits vorhanden" -ForegroundColor Green
}

# GUI-Anwendung erstellen
Write-Host "[3/4] Erstelle OPSI PackForge..." -ForegroundColor Yellow

# Hauptanwendung
$mainApp = @'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import sys
from datetime import datetime
from pathlib import Path

class OPSIPackForge:
    def __init__(self, root):
        self.root = root
        self.root.title("OPSI PackForge - paedML Linux")
        self.root.geometry("900x650")
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Header
        header_frame = ttk.Frame(root)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        title = tk.Label(header_frame, text="OPSI PackForge", 
                        font=('Segoe UI', 18, 'bold'), fg='#0078d4')
        title.pack(side="left")
        
        version = tk.Label(header_frame, text="v1.0.0 - Standalone", 
                          font=('Segoe UI', 10), fg='gray')
        version.pack(side="left", padx=10)
        
        # Notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Tabs
        self.create_package_tab()
        self.create_log_tab()
        
        # Status Bar
        self.status = tk.Label(root, text="Bereit", bd=1, relief="sunken", anchor="w")
        self.status.pack(side="bottom", fill="x")
        
        self.log("OPSI PackForge gestartet")
        
    def create_package_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📦 Paket erstellen")
        
        # Scrollable Frame
        canvas = tk.Canvas(tab, bg='white')
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)
        
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Basis-Informationen
        ttk.Label(frame, text="Basis-Informationen", font=('Segoe UI', 11, 'bold')).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(10,5), padx=10)
        
        # Paket-ID
        ttk.Label(frame, text="Paket-ID:*").grid(row=1, column=0, sticky="w", padx=(20,5), pady=3)
        self.package_id = ttk.Entry(frame, width=35)
        self.package_id.grid(row=1, column=1, sticky="w", pady=3)
        ttk.Label(frame, text="(z.B. firefox, chrome)", fg='gray').grid(row=1, column=2, sticky="w", padx=5)
        
        # Name
        ttk.Label(frame, text="Name:*").grid(row=2, column=0, sticky="w", padx=(20,5), pady=3)
        self.package_name = ttk.Entry(frame, width=35)
        self.package_name.grid(row=2, column=1, sticky="w", pady=3)
        
        # Version
        ttk.Label(frame, text="Version:*").grid(row=3, column=0, sticky="w", padx=(20,5), pady=3)
        self.package_version = ttk.Entry(frame, width=35)
        self.package_version.grid(row=3, column=1, sticky="w", pady=3)
        ttk.Label(frame, text="(z.B. 1.0.0)", fg='gray').grid(row=3, column=2, sticky="w", padx=5)
        
        # Beschreibung
        ttk.Label(frame, text="Beschreibung:").grid(row=4, column=0, sticky="w", padx=(20,5), pady=3)
        self.package_desc = ttk.Entry(frame, width=50)
        self.package_desc.grid(row=4, column=1, columnspan=2, sticky="w", pady=3)
        
        # Installation
        ttk.Label(frame, text="Installation", font=('Segoe UI', 11, 'bold')).grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(15,5), padx=10)
        
        # Setup-Datei
        ttk.Label(frame, text="Setup-Datei:").grid(row=6, column=0, sticky="w", padx=(20,5), pady=3)
        file_frame = ttk.Frame(frame)
        file_frame.grid(row=6, column=1, columnspan=2, sticky="w", pady=3)
        self.setup_file = ttk.Entry(file_frame, width=40)
        self.setup_file.pack(side="left")
        ttk.Button(file_frame, text="Durchsuchen...", command=self.browse_file).pack(side="left", padx=5)
        
        # Silent Parameter
        ttk.Label(frame, text="Silent Parameter:").grid(row=7, column=0, sticky="w", padx=(20,5), pady=3)
        self.silent_params = ttk.Entry(frame, width=35)
        self.silent_params.grid(row=7, column=1, sticky="w", pady=3)
        self.silent_params.insert(0, "/S /quiet")
        
        # Install Type
        ttk.Label(frame, text="Typ:").grid(row=8, column=0, sticky="w", padx=(20,5), pady=3)
        self.install_type = tk.StringVar(value="exe")
        type_frame = ttk.Frame(frame)
        type_frame.grid(row=8, column=1, sticky="w", pady=3)
        ttk.Radiobutton(type_frame, text="EXE", variable=self.install_type, value="exe").pack(side="left", padx=5)
        ttk.Radiobutton(type_frame, text="MSI", variable=self.install_type, value="msi").pack(side="left", padx=5)
        
        # Erweiterte Optionen
        ttk.Label(frame, text="Erweiterte Optionen", font=('Segoe UI', 11, 'bold')).grid(
            row=9, column=0, columnspan=3, sticky="w", pady=(15,5), padx=10)
        
        # Dependencies
        ttk.Label(frame, text="Abhängigkeiten:").grid(row=10, column=0, sticky="w", padx=(20,5), pady=3)
        self.dependencies = ttk.Entry(frame, width=35)
        self.dependencies.grid(row=10, column=1, sticky="w", pady=3)
        ttk.Label(frame, text="(komma-getrennt)", fg='gray').grid(row=10, column=2, sticky="w", padx=5)
        
        # Priority
        ttk.Label(frame, text="Priorität:").grid(row=11, column=0, sticky="w", padx=(20,5), pady=3)
        self.priority = ttk.Spinbox(frame, from_=-100, to=100, width=10)
        self.priority.set("0")
        self.priority.grid(row=11, column=1, sticky="w", pady=3)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=20, column=0, columnspan=3, pady=20)
        
        ttk.Button(btn_frame, text="✓ Paket generieren", 
                  command=self.generate_package).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="↻ Zurücksetzen", 
                  command=self.reset_form).pack(side="left", padx=5)
        
    def create_log_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📄 Log")
        
        self.log_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD, height=20)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", padx=10, pady=(0,10))
        ttk.Button(btn_frame, text="Log löschen", command=self.clear_log).pack(side="left", padx=5)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Setup-Datei wählen",
            filetypes=[("Ausführbare Dateien", "*.exe;*.msi"), ("Alle", "*.*")]
        )
        if filename:
            self.setup_file.delete(0, "end")
            self.setup_file.insert(0, filename)
            if filename.lower().endswith('.msi'):
                self.install_type.set('msi')
                self.silent_params.delete(0, "end")
                self.silent_params.insert(0, "/quiet /norestart")
    
    def generate_package(self):
        # Validierung
        if not all([self.package_id.get(), self.package_name.get(), self.package_version.get()]):
            messagebox.showerror("Fehler", "Bitte füllen Sie alle Pflichtfelder aus!")
            return
        
        # Output-Verzeichnis
        output_dir = filedialog.askdirectory(title="Ausgabe-Verzeichnis wählen")
        if not output_dir:
            return
        
        try:
            self.status.config(text="Generiere Paket...")
            self.log(f"Generiere Paket: {self.package_id.get()} v{self.package_version.get()}")
            
            # Paket-Verzeichnis
            pkg_name = f"{self.package_id.get()}_{self.package_version.get()}"
            pkg_dir = os.path.join(output_dir, pkg_name)
            os.makedirs(os.path.join(pkg_dir, "OPSI"), exist_ok=True)
            os.makedirs(os.path.join(pkg_dir, "CLIENT_DATA"), exist_ok=True)
            
            # Control-Datei
            self.create_control_file(pkg_dir)
            
            # Setup-Script
            self.create_setup_script(pkg_dir)
            
            # Uninstall-Script
            self.create_uninstall_script(pkg_dir)
            
            self.log(f"✓ Paket erstellt: {pkg_dir}")
            self.status.config(text="Paket erfolgreich generiert")
            
            messagebox.showinfo("Erfolg", f"Paket wurde erstellt:\n{pkg_dir}")
            
        except Exception as e:
            self.log(f"✗ Fehler: {str(e)}")
            self.status.config(text="Fehler bei Paket-Generierung")
            messagebox.showerror("Fehler", f"Fehler: {str(e)}")
    
    def create_control_file(self, pkg_dir):
        control = f"""[Package]
version: 1
depends: 
incremental: False

[Product]
type: localboot
id: {self.package_id.get()}
name: {self.package_name.get()}
description: {self.package_desc.get() or self.package_name.get()}
version: {self.package_version.get()}
priority: {self.priority.get()}
licenseRequired: False
setupScript: setup.opsiscript
uninstallScript: uninstall.opsiscript
"""
        
        # Abhängigkeiten
        if self.dependencies.get():
            for dep in self.dependencies.get().split(','):
                control += f"""
[ProductDependency]
action: setup
requiredProduct: {dep.strip()}
requiredStatus: installed
requirementType: before
"""
        
        with open(os.path.join(pkg_dir, "OPSI", "control"), "w", encoding="utf-8") as f:
            f.write(control)
    
    def create_setup_script(self, pkg_dir):
        setup_file = self.setup_file.get() or "setup.exe"
        setup_name = os.path.basename(setup_file)
        
        script = f"""; Setup script for {self.package_name.get()}
; Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[Actions]
requiredWinstVersion >= "4.11.6"

DefVar $ProductId$
DefVar $ProductName$
DefVar $Version$
DefVar $SetupFile$
DefVar $ExitCode$

Set $ProductId$ = "{self.package_id.get()}"
Set $ProductName$ = "{self.package_name.get()}"
Set $Version$ = "{self.package_version.get()}"
Set $SetupFile$ = "%ScriptPath%\\{setup_name}"

Message "Installing " + $ProductId$ + " " + $Version$ + " ..."

comment "Start setup program"
ChangeDirectory "%ScriptPath%"
"""
        
        if self.install_type.get() == "msi":
            script += """
Winbatch_install_msi
Sub_check_exitcode

[Winbatch_install_msi]
msiexec /i "$SetupFile$" """ + self.silent_params.get()
        else:
            script += """
Winbatch_install_exe
Sub_check_exitcode

[Winbatch_install_exe]
"$SetupFile$" """ + self.silent_params.get()
        
        script += """

[Sub_check_exitcode]
set $ExitCode$ = getLastExitCode
if ($ExitCode$ = "0")
    comment "Installation successful"
else
    logError "Installation failed with exit code: " + $ExitCode$
endif
"""
        
        with open(os.path.join(pkg_dir, "CLIENT_DATA", "setup.opsiscript"), "w", encoding="utf-8") as f:
            f.write(script)
    
    def create_uninstall_script(self, pkg_dir):
        script = f"""; Uninstall script for {self.package_name.get()}

[Actions]
requiredWinstVersion >= "4.11.6"

DefVar $ProductId$
Set $ProductId$ = "{self.package_id.get()}"

Message "Uninstalling " + $ProductId$ + " ..."

comment "Uninstall program"
"""
        
        with open(os.path.join(pkg_dir, "CLIENT_DATA", "uninstall.opsiscript"), "w", encoding="utf-8") as f:
            f.write(script)
    
    def reset_form(self):
        self.package_id.delete(0, "end")
        self.package_name.delete(0, "end")
        self.package_version.delete(0, "end")
        self.package_desc.delete(0, "end")
        self.setup_file.delete(0, "end")
        self.silent_params.delete(0, "end")
        self.silent_params.insert(0, "/S /quiet")
        self.dependencies.delete(0, "end")
        self.priority.set("0")
        self.install_type.set("exe")
        self.log("Formular zurückgesetzt")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
    
    def clear_log(self):
        self.log_text.delete(1.0, "end")
        self.log("Log gelöscht")

if __name__ == "__main__":
    root = tk.Tk()
    app = OPSIPackForge(root)
    root.mainloop()
'@

$mainApp | Out-File -FilePath "$AppDir\opsi_packforge.py" -Encoding UTF8
Write-Host "      ✓ Anwendung erstellt" -ForegroundColor Green

# Desktop-Verknüpfung
Write-Host "[4/4] Erstelle Desktop-Verknüpfung..." -ForegroundColor Yellow
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\OPSI PackForge.lnk")
    $Shortcut.TargetPath = "$PythonDir\python.exe"
    $Shortcut.Arguments = "`"$AppDir\opsi_packforge.py`""
    $Shortcut.WorkingDirectory = $AppDir
    $Shortcut.IconLocation = "$PythonDir\python.exe"
    $Shortcut.Description = "OPSI PackForge - Standalone"
    $Shortcut.Save()
    Write-Host "      ✓ Desktop-Verknüpfung erstellt" -ForegroundColor Green
} catch {
    Write-Host "      ! Desktop-Verknüpfung konnte nicht erstellt werden" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "    Installation abgeschlossen!     " -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Installiert in: $WorkDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starten über:" -ForegroundColor Yellow
Write-Host "  • Desktop-Verknüpfung 'OPSI PackForge'" -ForegroundColor White
Write-Host "  • PowerShell: & `"$PythonDir\python.exe`" `"$AppDir\opsi_packforge.py`"" -ForegroundColor White
Write-Host ""

$response = Read-Host "Möchten Sie OPSI PackForge jetzt starten? (J/N)"
if ($response -eq 'J' -or $response -eq 'j') {
    Start-Process "$PythonDir\python.exe" -ArgumentList "`"$AppDir\opsi_packforge.py`""
}

Write-Host ""
Read-Host "Drücken Sie Enter zum Beenden"