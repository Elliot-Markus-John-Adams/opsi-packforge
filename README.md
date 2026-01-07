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
- **Löschen** - Pakete vom OPSI-Server entfernen (NEU: mit Workbench-Bereinigung)
- **Deployment** - Automatisches Hochladen und Installieren

### 🔧 Erweiterte Features
- ✅ **Vollständige Metadaten** - Description, Advice, Dependencies
- ✅ **Multi-Datei Support** - Mehrere Setup-Dateien pro Paket
- ✅ **Automatische Versionierung** - Incrementelle Updates
- ✅ **Silent-Parameter Bibliothek** - Vordefinierte Installer-Parameter
- ✅ **SSH-Integration** - Direkte Server-Kommunikation
- ✅ **Depot-Synchronisation** - Live-Updates vom Server
- ✅ **Workbench-Management** - Verwaltung installierter und nicht-installierter Pakete
- ✅ **Non-Interactive Mode** - Automatisches Überschreiben ohne Rückfragen

## 📋 Systemanforderungen

- **OS:** Windows 10/11 (paedML Admin-VM)
- **PowerShell:** Version 5.1 oder höher
- **Netzwerk:** Zugriff auf OPSI-Server (10.1.0.2)
- **SSH:** Windows OpenSSH Client

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

Zeigt alle installierten Pakete aus opsi-package-manager -l
Wählen Sie das Paket: firefox

Neue Version: 115.1.0
[1] Setup-Dateien ersetzen
[2] Control-Datei bearbeiten
[3] Scripts aktualisieren
[4] Alles aktualisieren
```

### Paket löschen (VERBESSERT)
```
[3] Paket löschen

=== INSTALLIERTE PAKETE ===
[Liste aller installierten Pakete]

=== WORKBENCH PROJEKTE (nicht installiert) ===
[Liste aller Workbench-Only Projekte]

Paket-ID oder Workbench-Ordner zum Löschen: test01

Löschoptionen:
[1] Normal löschen (empfohlen)
[2] Mit --purge (entfernt auch alle Client-Zuordnungen)

→ Automatische Bereinigung von:
  - Workbench-Ordner und .opsi Dateien
  - Repository-Dateien
  - Depot-Ordner
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
```

## 🆕 Neue Features in Version 2.0

### Verbesserte Löschfunktion
- Unterscheidung zwischen installierten Paketen und Workbench-Projekten
- Vollständige Bereinigung aller Paket-Spuren
- Unterstützung für `--purge` Option
- Automatische Paket-ID Extraktion aus Workbench-Ordnernamen

### Non-Interactive Mode
- `opsi-makepackage --no-interactive` für automatisches Überschreiben
- Keine Terminal-Fehler mehr bei SSH-Verbindungen
- `TERM=dumb` Environment für fehlerfreie Remote-Ausführung

### Erweiterte Log-Anzeige
- Zeigt verfügbare Log-Dateien
- package.log, opsiconfd.log und Client-Logs
- Fehlertolerante Anzeige (prüft Existenz)

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

# Paket entfernen (einfach)
opsi-package-manager -r paket-id

# Paket entfernen mit Client-Zuordnungen
opsi-package-manager -r paket-id --purge

# Workbench bereinigen
rm -rf /var/lib/opsi/workbench/paket*
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

**Terminal-Fehler bei Paket-Löschung**
```
ERROR: Failed to process command 'remove': setupterm: could not find terminal
```
→ Wurde behoben durch `TERM=dumb` und `-q` Flags

**Paket existiert bereits**
```
Package file already exists. Press <O> to overwrite...
```
→ Wird automatisch überschrieben mit `--no-interactive`

**SSH-Verbindung schlägt fehl**
```powershell
# Windows OpenSSH installieren
Add-WindowsCapability -Online -Name OpenSSH.Client
```

**Workbench-Dateien bleiben nach Löschung**
→ Nutzen Sie Option 2 (--purge) oder löschen Sie manuell:
```bash
ssh root@10.1.0.2 "rm -rf /var/lib/opsi/workbench/paket*"
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

## 📝 Changelog

### Version 2.0.1 (Aktuell)
- ✅ Verbesserte Paket-Löschfunktion mit Workbench-Bereinigung
- ✅ Fix für Terminal-Probleme bei opsi-package-manager
- ✅ Erweiterte Log-Anzeige mit mehreren Log-Dateien
- ✅ Unterstützung für Workbench-only Projekte
- ✅ Automatisches Überschreiben existierender Pakete
- ✅ Bessere Unterscheidung zwischen installierten und Workbench-Paketen
- ✅ Non-Interactive Mode für alle Remote-Operationen

### Version 2.0.0
- Initiale Hauptversion mit grundlegenden Funktionen

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

**Version:** 2.0.1  
**Autor:** Elliot-Markus-John-Adams  
**Repository:** https://github.com/Elliot-Markus-John-Adams/opsi-packforge