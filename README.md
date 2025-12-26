# 📦 OPSI PackForge

**OPSI PackForge** - Einfaches Tool zur Erstellung von OPSI-Paketen für paedML Linux

## 🚀 Schnellinstallation

In PowerShell (Admin-VM) ausführen:

```powershell
# Mit Proxy-Authentifizierung (für Schulnetzwerke)
[System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials; iex ((New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/Elliot-Markus-John-Adams/opsi-packforge/main/install.ps1'))
```

## ✨ Features

- ✅ **Einfache Paket-Erstellung** - Interaktives Menü-System
- ✅ **OPSI-konforme Struktur** - Erstellt control und opsiscript Dateien
- ✅ **SSH-Integration** - Direkter Zugriff auf OPSI-Server
- ✅ **Setup-Datei Support** - Automatisches Kopieren der Installer
- ✅ **Silent-Parameter** - Unterstützung für unbeaufsichtigte Installation

## 📋 Systemanforderungen

- Windows 10/11 (paedML Admin-VM)
- PowerShell 5.1+
- SSH-Client (optional, für Server-Verbindung)
- Netzwerkzugriff zum OPSI-Server (10.1.0.2 / backup.paedml-linux.lokal)

## 🎯 Verwendung

### 1. Installation ausführen
Nach der Installation finden Sie "OPSI PackForge" auf dem Desktop.

### 2. Paket erstellen
```
[1] Neues Paket erstellen
    → Paket-ID: firefox
    → Name: Mozilla Firefox  
    → Version: 120.0.0
    → Setup-Datei: C:\Downloads\Firefox.exe
    → Silent-Parameter: /S
```

### 3. OPSI-Server Verbindung
Das Tool verbindet sich standardmäßig mit dem OPSI-Server (10.1.0.2 / backup.paedml-linux.lokal) und zeigt:
- Vorhandene Pakete in `/var/lib/opsi/workbench/`
- Installierte Pakete in `/var/lib/opsi/depot/`

### 4. Deployment
Das Tool zeigt die notwendigen Befehle für das Deployment:
```bash
scp -r "Paket-Ordner" root@10.1.0.2:/var/lib/opsi/workbench/
ssh root@10.1.0.2
opsi-makepackage paket-name
opsi-package-manager -i paket-name.opsi
```

## 📁 Erstellte Struktur

```
paket-name_version/
├── OPSI/
│   └── control          # Paket-Metadaten
└── CLIENT_DATA/
    ├── setup.opsiscript # Installations-Script
    └── setup.exe        # Setup-Datei (optional)
```

## 🔧 control Datei Beispiel

```ini
[Product]
type: localboot
id: firefox
name: Mozilla Firefox
version: 120.0.0
priority: 0
setupScript: setup.opsiscript
```

## 📝 setup.opsiscript Beispiel

```
[Actions]
DefVar $SetupFile$
Set $SetupFile$ = "%ScriptPath%\Firefox.exe"
Message "Installing Firefox..."
Winbatch_install

[Winbatch_install]
"$SetupFile$" /S
```

## 🛠️ Bekannte Einschränkungen

- Python GUI funktioniert nicht (tkinter fehlt in Embedded Python)
- Batch-basierte Lösung als Alternative
- SSH muss auf Windows separat installiert sein
- Automatisches Deployment noch nicht implementiert

## 📚 Tipps

1. **Silent-Parameter** vorher testen:
   - `/S` - Für NSIS-Installer
   - `/quiet` oder `/qn` - Für MSI
   - `/silent` - Für andere Installer

2. **SSH-Verbindung** vorbereiten:
   - SSH-Key einrichten für passwortlosen Zugriff
   - Oder WinSCP für grafischen Transfer nutzen

3. **Paket-IDs** ohne Sonderzeichen und Leerzeichen

## 🤝 Support

Bei Fragen oder Problemen:
- [Issues auf GitHub](https://github.com/Elliot-Markus-John-Adams/opsi-packforge/issues)
- Für paedML-spezifische Fragen: paedML Support

## 📄 Lizenz

MIT License - Frei verwendbar für Bildungseinrichtungen

## 🙏 Credits

Entwickelt für die paedML Linux Community

---

**Version:** 1.0.0  
**Autor:** Elliot-Markus-John-Adams  
**Repository:** https://github.com/Elliot-Markus-John-Adams/opsi-packforge