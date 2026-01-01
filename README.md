# 📦 OPSI PackForge

**OPSI PackForge** - Professionelles Tool zur Verwaltung von OPSI-Paketen für paedML Linux

## 🚀 Installation

### PowerShell (empfohlen)
```powershell
# Einmalige Installation mit Proxy-Support
[System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials
iex ((New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/Elliot-Markus-John-Adams/opsi-packforge/main/install.ps1'))
```

### Alternative: Lokale Installation
1. Repository herunterladen
2. PowerShell als Administrator öffnen
3. `.\install.ps1` ausführen

## ✨ Hauptfunktionen

### 📋 Paketverwaltung
- **Erstellen** - Neue OPSI-Pakete mit vollständigen Metadaten
- **Aktualisieren** - Bestehende Pakete im Depot updaten
- **Löschen** - Pakete vom OPSI-Server entfernen
- **Deployment** - Automatisches Hochladen und Installieren

### 🔧 Erweiterte Features
- ✅ **Vollständige Metadaten** - Description, Advice, Dependencies
- ✅ **Multi-Datei Support** - Mehrere Setup-Dateien pro Paket
- ✅ **Automatische Versionierung** - Incrementelle Updates
- ✅ **Silent-Parameter Bibliothek** - Vordefinierte Installer-Parameter
- ✅ **SSH-Integration** - Direkte Server-Kommunikation
- ✅ **Depot-Synchronisation** - Live-Updates vom Server

## 📋 Systemanforderungen

- **OS:** Windows 10/11 (paedML Admin-VM)
- **PowerShell:** Version 5.1 oder höher
- **Netzwerk:** Zugriff auf OPSI-Server (10.1.0.2)
- **Optional:** SSH-Client für erweiterte Funktionen

## 🎯 Verwendungsbeispiele

### Neues Paket erstellen
```
OPSI PackForge Hauptmenü
[1] Neues Paket erstellen

Paket-Konfiguration:
- Paket-ID: mozilla-firefox
- Name: Mozilla Firefox ESR
- Version: 115.0.0
- Beschreibung: Webbrowser für Bildungseinrichtungen
- Abhängigkeiten: msvcredist2019
- Setup-Dateien: Firefox-ESR.exe, config.ini
- Silent-Parameter: /S /INI=config.ini
```

### Paket aktualisieren
```
[2] Paket aktualisieren

Wählen Sie das Paket:
→ mozilla-firefox_115.0.0

Neue Version: 115.1.0
Dateien ersetzen: Firefox-ESR.exe
→ Automatisches Backup der alten Version
→ Upload zum Server
→ Depot-Aktualisierung
```

### Paket vom Server löschen
```
[3] Paket löschen

Server-Pakete anzeigen...
→ Auswahl: mozilla-firefox
→ Clients prüfen (Warnung bei zugewiesenen Clients)
→ Sicherheitsabfrage
→ Entfernung aus Depot und Workbench
```

## 📁 Paketstruktur

```
paket-id_version/
├── OPSI/
│   ├── control           # Vollständige Metadaten
│   ├── preinst           # Pre-Installation Script
│   └── postinst          # Post-Installation Script
└── CLIENT_DATA/
    ├── setup.opsiscript  # Hauptinstallations-Script
    ├── uninstall.opsiscript
    ├── files/            # Setup-Dateien
    │   ├── setup.exe
    │   └── config.ini
    └── custom/           # Benutzerdefinierte Scripts
```

## 🔧 control Datei - Vollständiges Beispiel

```ini
[Package]
version: 1
depends: 
incremental: False

[Product]
type: localboot
id: mozilla-firefox
name: Mozilla Firefox ESR
description: Der freie Webbrowser für Bildungseinrichtungen
advice: Bitte alle Browser-Fenster vor Installation schließen
version: 115.0.0
priority: 0
licenseRequired: False
productClasses: web,browser
setupScript: setup.opsiscript
uninstallScript: uninstall.opsiscript
updateScript: update.opsiscript
alwaysScript: 
onceScript: 
customScript: 
userLoginScript:

[ProductDependency]
action: setup
requiredProduct: msvcredist2019
requiredStatus: installed
requirementType: before

[ProductProperty]
type: bool
name: desktop-link
description: Desktop-Verknüpfung erstellen
default: True
```

## 🚀 Erweiterte Befehle

### SSH-Key einrichten (empfohlen)
```powershell
# Einmalig für passwortlosen Zugriff
ssh-keygen -t rsa -b 4096
ssh-copy-id root@10.1.0.2
```

### Manuelle Server-Befehle
```bash
# Paket-Liste anzeigen
opsi-package-manager -l

# Paket-Info
opsi-package-manager -i paket-id

# Paket zu Client zuweisen
opsi-admin -d method setProductActionRequest paket-id client-id setup

# Depot synchronisieren
opsi-package-updater -v update
```

## 📚 Best Practices

### Silent-Parameter Referenz
| Installer-Typ | Parameter | Beispiel |
|--------------|-----------|----------|
| NSIS | `/S` | `setup.exe /S` |
| MSI | `/qn` | `installer.msi /qn` |
| InnoSetup | `/VERYSILENT` | `setup.exe /VERYSILENT /NORESTART` |
| InstallShield | `/s /v/qn` | `setup.exe /s /v/qn` |
| 7-Zip SFX | `-y` | `archive.exe -y` |

### Versionierung
- **Major:** Große Änderungen (1.0.0 → 2.0.0)
- **Minor:** Neue Features (1.0.0 → 1.1.0)
- **Patch:** Bugfixes (1.0.0 → 1.0.1)

### Testing-Workflow
1. Paket lokal erstellen
2. Test-Client zuweisen
3. Installation überwachen
4. Logs prüfen (`/var/log/opsi/`)
5. Bei Erfolg: Produktiv-Rollout

## 🛠️ Fehlerbehebung

### Häufige Probleme

**SSH-Verbindung schlägt fehl**
```powershell
# Windows OpenSSH installieren
Add-WindowsCapability -Online -Name OpenSSH.Client
```

**Paket-Upload fehlgeschlagen**
```bash
# Rechte prüfen
ssh root@10.1.0.2 "ls -la /var/lib/opsi/workbench/"
# Speicherplatz prüfen
ssh root@10.1.0.2 "df -h /var/lib/opsi/"
```

**Installation auf Client schlägt fehl**
```bash
# Client-Logs prüfen
ssh root@10.1.0.2 "tail -f /var/log/opsi/clientconnect/*.log"
# Paket-Integrität prüfen
opsi-package-manager -t paket-id
```

## 🔐 Sicherheit

- Keine Passwörter im Klartext speichern
- SSH-Keys mit Passphrase schützen
- Regelmäßige Backups der Pakete
- Test-Umgebung vor Produktion

## 📊 Monitoring

### OPSI-Webinterface
```
https://10.1.0.2:4447/
Benutzer: adminuser
```

### Kommandozeilen-Monitoring
```bash
# Aktive Installationen
opsi-admin -d method getProductActionRequests

# Client-Status
opsi-admin -d method getClientIds

# Fehlerhafte Installationen
opsi-admin -d method getProductInstallationStatus_hash
```

## 🤝 Mitwirkung

Contributions sind willkommen! Bitte erstellen Sie einen Pull Request mit:
- Detaillierter Beschreibung
- Test-Ergebnissen
- Dokumentations-Updates

## 📄 Lizenz

MIT License - Frei verwendbar für Bildungseinrichtungen

## 🏢 Über paedML Linux

OPSI PackForge wurde speziell für die paedML Linux Schulnetzwerklösung entwickelt und optimiert für:
- Zentrale Software-Verteilung
- Automatisierte Client-Verwaltung
- Vereinfachte Paket-Erstellung für Lehrkräfte

## 📞 Support

- **GitHub Issues:** [Bug-Reports und Feature-Requests](https://github.com/Elliot-Markus-John-Adams/opsi-packforge/issues)
- **paedML Support:** Über das offizielle Support-Portal
- **Community:** paedML Linux Anwender-Forum

---

**Version:** 2.0.0  
**Autor:** Elliot-Markus-John-Adams  
**Repository:** https://github.com/Elliot-Markus-John-Adams/opsi-packforge