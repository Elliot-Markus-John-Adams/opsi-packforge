#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import sys
import subprocess
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

# Import des OPSI-Generators
from opsi_generator import OPSIPackageGenerator

class OPSIPackForge:
    def __init__(self, root):
        self.root = root
        self.root.title("OPSI PackForge - paedML Linux")
        self.root.geometry("1200x800")
        
        # Konfiguration laden
        self.config = self.load_config()
        
        # Generator initialisieren
        self.generator = OPSIPackageGenerator()
        
        # UI Style
        self.setup_styles()
        
        # Hauptlayout erstellen
        self.create_ui()
        
        # Fenster zentrieren
        self.center_window()
    
    def load_config(self):
        """Lädt die Konfigurationsdatei"""
        config_path = Path(__file__).parent / "config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.get_default_config()
    
    def get_default_config(self):
        """Standard-Konfiguration"""
        return {
            "opsi_server": "opsi.schule.local",
            "default_vendor": "schule",
            "default_priority": "0",
            "default_architecture": "x64",
            "output_dir": "C:\\OPSI-Pakete",
            "templates_dir": "templates"
        }
    
    def save_config(self):
        """Speichert die aktuelle Konfiguration"""
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
    
    def setup_styles(self):
        """Definiert das Aussehen der GUI"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Farben
        bg_color = '#f0f0f0'
        fg_color = '#333333'
        accent_color = '#0078d4'
        
        self.root.configure(bg=bg_color)
        
        # Button Style
        style.configure('Accent.TButton',
                       background=accent_color,
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 8))
        style.map('Accent.TButton',
                 background=[('active', '#005a9e')])
        
        # Frame Style
        style.configure('Card.TFrame',
                       background='white',
                       relief='flat',
                       borderwidth=1)
    
    def create_ui(self):
        """Erstellt die Benutzeroberfläche"""
        # Hauptcontainer
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Konfiguriere Grid-Gewichtung
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # Header
        self.create_header(main_container)
        
        # Notebook für Tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Tabs erstellen
        self.create_package_tab()
        self.create_template_tab()
        self.create_settings_tab()
        self.create_log_tab()
    
    def create_header(self, parent):
        """Erstellt den Header-Bereich"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Titel
        title_label = tk.Label(header_frame, text="OPSI PackForge", 
                              font=('Segoe UI', 20, 'bold'),
                              fg='#0078d4', bg='#f0f0f0')
        title_label.pack(side=tk.LEFT)
        
        # Buttons rechts
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="📚 Hilfe", 
                  command=self.show_help).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="ℹ️ Über", 
                  command=self.show_about).pack(side=tk.LEFT, padx=2)
    
    def create_package_tab(self):
        """Tab für Paket-Erstellung"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="📦 Paket erstellen")
        
        # Scrollable Frame
        canvas = tk.Canvas(tab_frame, bg='white')
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Formular-Felder
        row = 0
        
        # Basis-Informationen
        section_label = tk.Label(scrollable_frame, text="Basis-Informationen",
                                font=('Segoe UI', 12, 'bold'))
        section_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        row += 1
        
        # Paket-ID
        tk.Label(scrollable_frame, text="Paket-ID:*").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.package_id_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=self.package_id_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=3)
        tk.Label(scrollable_frame, text="(z.B. firefox, chrome, office2021)", fg='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Name
        tk.Label(scrollable_frame, text="Name:*").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.package_name_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=self.package_name_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=3)
        row += 1
        
        # Version
        tk.Label(scrollable_frame, text="Version:*").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.package_version_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=self.package_version_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=3)
        tk.Label(scrollable_frame, text="(z.B. 1.0.0, 2021.3.5)", fg='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Beschreibung
        tk.Label(scrollable_frame, text="Beschreibung:").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.package_desc_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=self.package_desc_var, width=60).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=3)
        row += 1
        
        # Vendor
        tk.Label(scrollable_frame, text="Vendor:").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.package_vendor_var = tk.StringVar(value=self.config.get('default_vendor', 'schule'))
        tk.Entry(scrollable_frame, textvariable=self.package_vendor_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=3)
        row += 1
        
        # Installation
        section_label = tk.Label(scrollable_frame, text="Installation",
                                font=('Segoe UI', 12, 'bold'))
        section_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(15, 5))
        row += 1
        
        # Setup-Datei
        tk.Label(scrollable_frame, text="Setup-Datei:").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.setup_file_var = tk.StringVar()
        file_frame = ttk.Frame(scrollable_frame)
        file_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=3)
        tk.Entry(file_frame, textvariable=self.setup_file_var, width=50).pack(side=tk.LEFT)
        ttk.Button(file_frame, text="Durchsuchen...", 
                  command=self.browse_setup_file).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Silent Install Parameter
        tk.Label(scrollable_frame, text="Silent Parameter:").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.silent_params_var = tk.StringVar(value="/S /quiet")
        tk.Entry(scrollable_frame, textvariable=self.silent_params_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=3)
        tk.Label(scrollable_frame, text="(z.B. /S, /quiet, /silent)", fg='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Installation Type
        tk.Label(scrollable_frame, text="Installations-Typ:").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.install_type_var = tk.StringVar(value="exe")
        install_frame = ttk.Frame(scrollable_frame)
        install_frame.grid(row=row, column=1, sticky=tk.W, pady=3)
        ttk.Radiobutton(install_frame, text="EXE", variable=self.install_type_var, value="exe").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(install_frame, text="MSI", variable=self.install_type_var, value="msi").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(install_frame, text="Script", variable=self.install_type_var, value="script").pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Architektur
        tk.Label(scrollable_frame, text="Architektur:").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.architecture_var = tk.StringVar(value=self.config.get('default_architecture', 'x64'))
        arch_frame = ttk.Frame(scrollable_frame)
        arch_frame.grid(row=row, column=1, sticky=tk.W, pady=3)
        ttk.Radiobutton(arch_frame, text="32-bit", variable=self.architecture_var, value="x86").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(arch_frame, text="64-bit", variable=self.architecture_var, value="x64").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(arch_frame, text="Beide", variable=self.architecture_var, value="both").pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Abhängigkeiten
        section_label = tk.Label(scrollable_frame, text="Abhängigkeiten & Anforderungen",
                                font=('Segoe UI', 12, 'bold'))
        section_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(15, 5))
        row += 1
        
        # Abhängigkeiten
        tk.Label(scrollable_frame, text="Abhängigkeiten:").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.dependencies_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=self.dependencies_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=3)
        tk.Label(scrollable_frame, text="(Komma-getrennt, z.B. dotnet,vcredist)", fg='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Min Windows Version
        tk.Label(scrollable_frame, text="Min. Windows:").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.min_windows_var = tk.StringVar()
        win_combo = ttk.Combobox(scrollable_frame, textvariable=self.min_windows_var, width=38)
        win_combo['values'] = ('', 'Windows 7', 'Windows 8', 'Windows 8.1', 'Windows 10', 'Windows 11')
        win_combo.grid(row=row, column=1, sticky=tk.W, pady=3)
        row += 1
        
        # Priorität
        tk.Label(scrollable_frame, text="Priorität:").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.priority_var = tk.StringVar(value=self.config.get('default_priority', '0'))
        priority_spin = tk.Spinbox(scrollable_frame, from_=-100, to=100, textvariable=self.priority_var, width=10)
        priority_spin.grid(row=row, column=1, sticky=tk.W, pady=3)
        tk.Label(scrollable_frame, text="(Höhere Zahl = höhere Priorität)", fg='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Erweiterte Optionen
        section_label = tk.Label(scrollable_frame, text="Erweiterte Optionen",
                                font=('Segoe UI', 12, 'bold'))
        section_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(15, 5))
        row += 1
        
        # Pre-Install Script
        tk.Label(scrollable_frame, text="Pre-Install Script:").grid(row=row, column=0, sticky=(tk.W, tk.N), padx=(20, 5), pady=3)
        self.pre_install_text = scrolledtext.ScrolledText(scrollable_frame, width=60, height=4)
        self.pre_install_text.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=3)
        row += 1
        
        # Post-Install Script
        tk.Label(scrollable_frame, text="Post-Install Script:").grid(row=row, column=0, sticky=(tk.W, tk.N), padx=(20, 5), pady=3)
        self.post_install_text = scrolledtext.ScrolledText(scrollable_frame, width=60, height=4)
        self.post_install_text.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=3)
        row += 1
        
        # Uninstall Command
        tk.Label(scrollable_frame, text="Uninstall Befehl:").grid(row=row, column=0, sticky=tk.W, padx=(20, 5), pady=3)
        self.uninstall_cmd_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=self.uninstall_cmd_var, width=60).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=3)
        row += 1
        
        # Action Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="✓ Paket generieren", 
                  style='Accent.TButton',
                  command=self.generate_package).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Als Template speichern", 
                  command=self.save_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Formular zurücksetzen", 
                  command=self.reset_form).pack(side=tk.LEFT, padx=5)
    
    def create_template_tab(self):
        """Tab für Templates"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="📋 Templates")
        
        # Template Liste
        list_frame = ttk.LabelFrame(tab_frame, text="Verfügbare Templates", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Listbox mit Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.template_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.template_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.template_listbox.yview)
        
        # Template laden
        self.load_templates()
        
        # Buttons
        btn_frame = ttk.Frame(tab_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Template laden", 
                  command=self.load_selected_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Template löschen", 
                  command=self.delete_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Template importieren", 
                  command=self.import_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Template exportieren", 
                  command=self.export_template).pack(side=tk.LEFT, padx=5)
    
    def create_settings_tab(self):
        """Tab für Einstellungen"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="⚙️ Einstellungen")
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(tab_frame, text="Allgemeine Einstellungen", padding=20)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        row = 0
        
        # OPSI Server
        tk.Label(settings_frame, text="OPSI Server:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.opsi_server_var = tk.StringVar(value=self.config.get('opsi_server', 'opsi.schule.local'))
        tk.Entry(settings_frame, textvariable=self.opsi_server_var, width=40).grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1
        
        # Output Directory
        tk.Label(settings_frame, text="Ausgabe-Verzeichnis:").grid(row=row, column=0, sticky=tk.W, pady=5)
        output_frame = ttk.Frame(settings_frame)
        output_frame.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        self.output_dir_var = tk.StringVar(value=self.config.get('output_dir', 'C:\\OPSI-Pakete'))
        tk.Entry(output_frame, textvariable=self.output_dir_var, width=35).pack(side=tk.LEFT)
        ttk.Button(output_frame, text="...", width=3,
                  command=self.browse_output_dir).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Default Vendor
        tk.Label(settings_frame, text="Standard Vendor:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.default_vendor_var = tk.StringVar(value=self.config.get('default_vendor', 'schule'))
        tk.Entry(settings_frame, textvariable=self.default_vendor_var, width=40).grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1
        
        # Default Priority
        tk.Label(settings_frame, text="Standard Priorität:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.default_priority_var = tk.StringVar(value=self.config.get('default_priority', '0'))
        tk.Spinbox(settings_frame, from_=-100, to=100, textvariable=self.default_priority_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1
        
        # Default Architecture
        tk.Label(settings_frame, text="Standard Architektur:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.default_arch_var = tk.StringVar(value=self.config.get('default_architecture', 'x64'))
        arch_combo = ttk.Combobox(settings_frame, textvariable=self.default_arch_var, width=38)
        arch_combo['values'] = ('x86', 'x64', 'both')
        arch_combo.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1
        
        # Save Button
        ttk.Button(settings_frame, text="Einstellungen speichern", 
                  style='Accent.TButton',
                  command=self.save_settings).grid(row=row, column=0, columnspan=2, pady=20)
    
    def create_log_tab(self):
        """Tab für Logs"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="📄 Log")
        
        # Log Text Widget
        self.log_text = scrolledtext.ScrolledText(tab_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Button Frame
        btn_frame = ttk.Frame(tab_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Log löschen", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Log speichern", 
                  command=self.save_log).pack(side=tk.LEFT, padx=5)
        
        # Initial Log
        self.log("OPSI PackForge gestartet")
        self.log(f"Version: 1.0.0")
        self.log(f"Arbeitsverzeichnis: {os.getcwd()}")
    
    def browse_setup_file(self):
        """Datei-Browser für Setup-Datei"""
        filename = filedialog.askopenfilename(
            title="Setup-Datei auswählen",
            filetypes=[
                ("Ausführbare Dateien", "*.exe;*.msi"),
                ("EXE Dateien", "*.exe"),
                ("MSI Dateien", "*.msi"),
                ("Alle Dateien", "*.*")
            ]
        )
        if filename:
            self.setup_file_var.set(filename)
            # Auto-detect install type
            if filename.lower().endswith('.msi'):
                self.install_type_var.set('msi')
                self.silent_params_var.set('/quiet /norestart')
            elif filename.lower().endswith('.exe'):
                self.install_type_var.set('exe')
                self.silent_params_var.set('/S')
    
    def browse_output_dir(self):
        """Verzeichnis-Browser für Output"""
        directory = filedialog.askdirectory(
            title="Ausgabe-Verzeichnis wählen"
        )
        if directory:
            self.output_dir_var.set(directory)
    
    def generate_package(self):
        """Generiert das OPSI-Paket"""
        # Validierung
        if not self.validate_input():
            return
        
        # Thread für die Generierung
        threading.Thread(target=self._generate_package_thread, daemon=True).start()
    
    def _generate_package_thread(self):
        """Thread-Funktion für Paket-Generierung"""
        try:
            self.log("=" * 50)
            self.log("Starte Paket-Generierung...")
            
            # Paket-Daten sammeln
            package_data = {
                'id': self.package_id_var.get(),
                'name': self.package_name_var.get(),
                'version': self.package_version_var.get(),
                'description': self.package_desc_var.get(),
                'vendor': self.package_vendor_var.get(),
                'setup_file': self.setup_file_var.get(),
                'silent_params': self.silent_params_var.get(),
                'install_type': self.install_type_var.get(),
                'architecture': self.architecture_var.get(),
                'dependencies': self.dependencies_var.get(),
                'min_windows': self.min_windows_var.get(),
                'priority': self.priority_var.get(),
                'pre_install': self.pre_install_text.get(1.0, tk.END).strip(),
                'post_install': self.post_install_text.get(1.0, tk.END).strip(),
                'uninstall_cmd': self.uninstall_cmd_var.get(),
                'output_dir': self.output_dir_var.get() or self.config.get('output_dir')
            }
            
            self.log(f"Paket-ID: {package_data['id']}")
            self.log(f"Version: {package_data['version']}")
            self.log(f"Ausgabe: {package_data['output_dir']}")
            
            # Generator aufrufen
            result = self.generator.generate(package_data)
            
            if result['success']:
                self.log("✓ Paket erfolgreich generiert!")
                self.log(f"  Pfad: {result['path']}")
                
                # Erfolgsmeldung
                self.root.after(0, lambda: messagebox.showinfo(
                    "Erfolg",
                    f"Paket wurde erfolgreich generiert!\n\nPfad: {result['path']}"
                ))
            else:
                self.log(f"✗ Fehler: {result['error']}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Fehler",
                    f"Paket konnte nicht generiert werden:\n\n{result['error']}"
                ))
                
        except Exception as e:
            self.log(f"✗ Unerwarteter Fehler: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror(
                "Fehler",
                f"Ein unerwarteter Fehler ist aufgetreten:\n\n{str(e)}"
            ))
    
    def validate_input(self):
        """Validiert die Eingaben"""
        errors = []
        
        if not self.package_id_var.get():
            errors.append("- Paket-ID ist erforderlich")
        elif ' ' in self.package_id_var.get():
            errors.append("- Paket-ID darf keine Leerzeichen enthalten")
        
        if not self.package_name_var.get():
            errors.append("- Name ist erforderlich")
        
        if not self.package_version_var.get():
            errors.append("- Version ist erforderlich")
        
        if errors:
            messagebox.showerror("Validierungsfehler", 
                                "Bitte korrigieren Sie folgende Fehler:\n\n" + "\n".join(errors))
            return False
        
        return True
    
    def save_template(self):
        """Speichert aktuelle Eingaben als Template"""
        name = tk.simpledialog.askstring("Template speichern", 
                                         "Name für das Template:")
        if not name:
            return
        
        template_data = {
            'name': name,
            'package_name': self.package_name_var.get(),
            'description': self.package_desc_var.get(),
            'vendor': self.package_vendor_var.get(),
            'silent_params': self.silent_params_var.get(),
            'install_type': self.install_type_var.get(),
            'architecture': self.architecture_var.get(),
            'dependencies': self.dependencies_var.get(),
            'min_windows': self.min_windows_var.get(),
            'priority': self.priority_var.get(),
            'pre_install': self.pre_install_text.get(1.0, tk.END).strip(),
            'post_install': self.post_install_text.get(1.0, tk.END).strip(),
            'uninstall_cmd': self.uninstall_cmd_var.get()
        }
        
        # Template speichern
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)
        
        template_file = template_dir / f"{name}.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=4)
        
        self.log(f"Template '{name}' gespeichert")
        messagebox.showinfo("Erfolg", f"Template '{name}' wurde gespeichert")
        
        # Template-Liste aktualisieren
        self.load_templates()
    
    def load_templates(self):
        """Lädt verfügbare Templates"""
        self.template_listbox.delete(0, tk.END)
        
        template_dir = Path(__file__).parent / "templates"
        if template_dir.exists():
            for template_file in template_dir.glob("*.json"):
                self.template_listbox.insert(tk.END, template_file.stem)
    
    def load_selected_template(self):
        """Lädt das ausgewählte Template"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Kein Template", "Bitte wählen Sie ein Template aus")
            return
        
        template_name = self.template_listbox.get(selection[0])
        template_file = Path(__file__).parent / "templates" / f"{template_name}.json"
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Formular mit Template-Daten füllen
            self.package_name_var.set(data.get('package_name', ''))
            self.package_desc_var.set(data.get('description', ''))
            self.package_vendor_var.set(data.get('vendor', ''))
            self.silent_params_var.set(data.get('silent_params', ''))
            self.install_type_var.set(data.get('install_type', 'exe'))
            self.architecture_var.set(data.get('architecture', 'x64'))
            self.dependencies_var.set(data.get('dependencies', ''))
            self.min_windows_var.set(data.get('min_windows', ''))
            self.priority_var.set(data.get('priority', '0'))
            
            self.pre_install_text.delete(1.0, tk.END)
            self.pre_install_text.insert(1.0, data.get('pre_install', ''))
            
            self.post_install_text.delete(1.0, tk.END)
            self.post_install_text.insert(1.0, data.get('post_install', ''))
            
            self.uninstall_cmd_var.set(data.get('uninstall_cmd', ''))
            
            self.log(f"Template '{template_name}' geladen")
            messagebox.showinfo("Template geladen", f"Template '{template_name}' wurde geladen")
            
            # Zum ersten Tab wechseln
            self.notebook.select(0)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Template konnte nicht geladen werden: {str(e)}")
    
    def delete_template(self):
        """Löscht das ausgewählte Template"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Kein Template", "Bitte wählen Sie ein Template aus")
            return
        
        template_name = self.template_listbox.get(selection[0])
        
        if messagebox.askyesno("Template löschen", 
                               f"Möchten Sie das Template '{template_name}' wirklich löschen?"):
            template_file = Path(__file__).parent / "templates" / f"{template_name}.json"
            try:
                template_file.unlink()
                self.log(f"Template '{template_name}' gelöscht")
                self.load_templates()
            except Exception as e:
                messagebox.showerror("Fehler", f"Template konnte nicht gelöscht werden: {str(e)}")
    
    def import_template(self):
        """Importiert ein Template"""
        filename = filedialog.askopenfilename(
            title="Template importieren",
            filetypes=[("JSON Dateien", "*.json"), ("Alle Dateien", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                name = data.get('name', Path(filename).stem)
                template_dir = Path(__file__).parent / "templates"
                template_dir.mkdir(exist_ok=True)
                
                target_file = template_dir / f"{name}.json"
                with open(target_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                
                self.log(f"Template '{name}' importiert")
                self.load_templates()
                messagebox.showinfo("Erfolg", f"Template '{name}' wurde importiert")
                
            except Exception as e:
                messagebox.showerror("Fehler", f"Template konnte nicht importiert werden: {str(e)}")
    
    def export_template(self):
        """Exportiert das ausgewählte Template"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Kein Template", "Bitte wählen Sie ein Template aus")
            return
        
        template_name = self.template_listbox.get(selection[0])
        template_file = Path(__file__).parent / "templates" / f"{template_name}.json"
        
        filename = filedialog.asksaveasfilename(
            title="Template exportieren",
            defaultextension=".json",
            initialfile=f"{template_name}.json",
            filetypes=[("JSON Dateien", "*.json"), ("Alle Dateien", "*.*")]
        )
        
        if filename:
            try:
                import shutil
                shutil.copy2(template_file, filename)
                self.log(f"Template '{template_name}' exportiert nach {filename}")
                messagebox.showinfo("Erfolg", f"Template wurde exportiert nach:\n{filename}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Template konnte nicht exportiert werden: {str(e)}")
    
    def reset_form(self):
        """Setzt das Formular zurück"""
        if messagebox.askyesno("Formular zurücksetzen", 
                               "Möchten Sie alle Eingaben zurücksetzen?"):
            self.package_id_var.set("")
            self.package_name_var.set("")
            self.package_version_var.set("")
            self.package_desc_var.set("")
            self.package_vendor_var.set(self.config.get('default_vendor', 'schule'))
            self.setup_file_var.set("")
            self.silent_params_var.set("/S /quiet")
            self.install_type_var.set("exe")
            self.architecture_var.set(self.config.get('default_architecture', 'x64'))
            self.dependencies_var.set("")
            self.min_windows_var.set("")
            self.priority_var.set(self.config.get('default_priority', '0'))
            self.pre_install_text.delete(1.0, tk.END)
            self.post_install_text.delete(1.0, tk.END)
            self.uninstall_cmd_var.set("")
            
            self.log("Formular zurückgesetzt")
    
    def save_settings(self):
        """Speichert die Einstellungen"""
        self.config['opsi_server'] = self.opsi_server_var.get()
        self.config['output_dir'] = self.output_dir_var.get()
        self.config['default_vendor'] = self.default_vendor_var.get()
        self.config['default_priority'] = self.default_priority_var.get()
        self.config['default_architecture'] = self.default_arch_var.get()
        
        self.save_config()
        self.log("Einstellungen gespeichert")
        messagebox.showinfo("Erfolg", "Einstellungen wurden gespeichert")
    
    def log(self, message):
        """Schreibt eine Nachricht ins Log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Löscht das Log"""
        self.log_text.delete(1.0, tk.END)
        self.log("Log gelöscht")
    
    def save_log(self):
        """Speichert das Log in eine Datei"""
        filename = filedialog.asksaveasfilename(
            title="Log speichern",
            defaultextension=".txt",
            initialfile=f"opsi_packforge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            filetypes=[("Text Dateien", "*.txt"), ("Alle Dateien", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Erfolg", f"Log wurde gespeichert nach:\n{filename}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Log konnte nicht gespeichert werden: {str(e)}")
    
    def show_help(self):
        """Zeigt die Hilfe"""
        help_text = """OPSI PackForge - Hilfe

OPSI PackForge ist ein Tool zur einfachen Erstellung von OPSI-Paketen für paedML Linux.

Hauptfunktionen:
• Einfache GUI zur Paket-Erstellung
• Template-System für häufig verwendete Pakete
• Automatische Generierung von OPSI-Skripten
• Export/Import von Templates

Workflow:
1. Füllen Sie die Paket-Informationen aus
2. Wählen Sie die Setup-Datei aus
3. Konfigurieren Sie die Silent-Installation
4. Generieren Sie das Paket
5. Das Paket wird im Ausgabe-Verzeichnis erstellt

Tipps:
• Verwenden Sie Templates für ähnliche Pakete
• Testen Sie Silent-Parameter vorher
• Prüfen Sie Abhängigkeiten sorgfältig

Support:
Bei Fragen wenden Sie sich an Ihre paedML-Support-Stelle."""
        
        messagebox.showinfo("Hilfe", help_text)
    
    def show_about(self):
        """Zeigt About-Dialog"""
        about_text = """OPSI PackForge
Version 1.0.0

Tool zur Erstellung von OPSI-Paketen
für paedML Linux Umgebungen

© 2024 - Entwickelt für Schul-IT
        
Dieses Tool vereinfacht die Erstellung
von OPSI-Paketen durch eine intuitive
grafische Oberfläche."""
        
        messagebox.showinfo("Über OPSI PackForge", about_text)
    
    def center_window(self):
        """Zentriert das Fenster auf dem Bildschirm"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

def main():
    root = tk.Tk()
    app = OPSIPackForge(root)
    root.mainloop()

if __name__ == "__main__":
    main()