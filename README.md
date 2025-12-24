# 📦 OPSI PackForge

**OPSI PackForge** ist ein benutzerfreundliches GUI-Tool zur Erstellung von OPSI-Paketen für paedML Linux Umgebungen. Es vereinfacht den Prozess der Paket-Erstellung durch eine intuitive Oberfläche und automatisierte Skript-Generierung.

## 🚀 Schnellstart

Installation mit einem einzigen PowerShell-Befehl auf der Admin-VM:

```powershell
irm https://raw.githubusercontent.com/Elliot-Markus-John-Adams/opsi-packforge/main/install.ps1 | iex
```

## ✨ Features

- 🎨 **Intuitive GUI** - Einfache Bedienung ohne Kommandozeilen-Kenntnisse
- 📋 **Template-System** - Wiederverwendbare Vorlagen für häufige Pakete
- 🔧 **Automatische Script-Generierung** - OPSI-konforme setup.opsiscript und control Dateien
- 📦 **Paket-Export** - Direkt einsatzbereit für OPSI-Server
- 🏢 **paedML-optimiert** - Speziell für Schulumgebungen entwickelt

## 📋 Systemanforderungen

- Windows 10/11 (Admin-VM)
- PowerShell 5.1+
- Ca. 100 MB freier Speicherplatz
- Internetverbindung für Installation

## 🔧 Installation

### Option 1: One-Line-Installation
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; irm https://raw.githubusercontent.com/Elliot-Markus-John-Adams/opsi-packforge/main/install.ps1 | iex
```

### Option 2: Manuelle Installation
1. [Installer-Script](https://raw.githubusercontent.com/Elliot-Markus-John-Adams/opsi-packforge/main/install.ps1) herunterladen
2. PowerShell als Administrator öffnen
3. Script ausführen: `.\install.ps1`

### Update
```powershell
.\install.ps1 -Update
```

## 📚 Verwendung

### 1. Anwendung starten
- Desktop-Verknüpfung "OPSI PackForge" doppelklicken
- Oder: `C:\Users\%USERNAME%\AppData\Local\OPSI-PackForge\python\pythonw.exe app\opsi_packforge.py`

### 2. Paket erstellen
1. **Basis-Informationen** eingeben:
   - Paket-ID (z.B. `firefox`, `chrome`)
   - Name und Version
   - Beschreibung

2. **Installation** konfigurieren:
   - Setup-Datei auswählen
   - Silent-Parameter angeben
   - Installations-Typ wählen (EXE/MSI/Script)

3. **Optionen** festlegen:
   - Abhängigkeiten
   - Architektur (32/64-bit)
   - Pre-/Post-Install Scripts

4. **Paket generieren** klicken

### 3. Paket deployen
Das generierte Paket liegt im konfigurierten Ausgabe-Verzeichnis (Standard: `C:\OPSI-Pakete`) und kann auf den OPSI-Server kopiert werden.

## 🎯 Beispiele

### Firefox-Paket erstellen
```
Paket-ID: firefox
Name: Mozilla Firefox
Version: 120.0
Setup: Firefox_Setup_120.0.exe
Silent: /S
Typ: EXE
```

### Office-Paket mit Abhängigkeiten
```
Paket-ID: office2021
Name: Microsoft Office 2021
Dependencies: dotnet,vcredist2019
Min. Windows: Windows 10
```

## 📁 Projektstruktur

```
opsi-packforge/
├── install.ps1           # PowerShell Installer
├── src/
│   ├── opsi_packforge.py # Haupt-GUI-Anwendung
│   ├── opsi_generator.py # OPSI-Paket-Generator
│   └── config.json       # Konfiguration
├── docs/
│   └── index.html        # GitHub Pages Website
├── templates/            # Gespeicherte Templates
└── requirements.txt      # Python-Abhängigkeiten
```

## 🛠️ Entwicklung

### Lokale Entwicklung
```bash
# Repository klonen
git clone https://github.com/Elliot-Markus-John-Adams/opsi-packforge.git
cd opsi-packforge

# Python-Umgebung einrichten
python -m venv venv
venv\Scripts\activate

# Anwendung starten
python src/opsi_packforge.py
```

### Beitragen
1. Fork erstellen
2. Feature-Branch anlegen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request öffnen

## 📄 Generierte OPSI-Struktur

Ein generiertes Paket hat folgende Struktur:
```
paket-name_1.0.0/
├── OPSI/
│   └── control           # Paket-Metadaten
├── CLIENT_DATA/
│   ├── setup.opsiscript  # Installations-Script
│   ├── uninstall.opsiscript # Deinstallations-Script
│   └── setup.exe         # Setup-Datei (optional)
```

## ⚙️ Konfiguration

Die Standardeinstellungen können im Tab "Einstellungen" angepasst werden:
- OPSI-Server-Adresse
- Ausgabe-Verzeichnis
- Standard-Vendor
- Standard-Priorität
- Standard-Architektur

## 🔍 Troubleshooting

### PowerShell-Ausführung blockiert
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python/tkinter fehlt
Das Tool installiert Python Portable automatisch. Bei Problemen:
1. `C:\Users\%USERNAME%\AppData\Local\OPSI-PackForge` löschen
2. Installer erneut ausführen

### Paket-Generierung schlägt fehl
- Log-Tab prüfen für Details
- Pfade auf Sonderzeichen prüfen
- Schreibrechte im Ausgabe-Verzeichnis prüfen

## 📝 Lizenz

Dieses Projekt ist für den Einsatz in Schulumgebungen entwickelt und frei verwendbar.

## 🤝 Support

Bei Fragen oder Problemen:
- [GitHub Issues](https://github.com/Elliot-Markus-John-Adams/opsi-packforge/issues) erstellen
- paedML Support kontaktieren

## 🙏 Credits

Entwickelt für die paedML Linux Community zur Vereinfachung der OPSI-Paket-Verwaltung in Schulen.