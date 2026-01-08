# OPSI PackForge

Tool für OPSI-Paketverwaltung in paedML Linux.

## Installation

```powershell
[System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials
iex ((New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/Elliot-Markus-John-Adams/opsi-packforge/main/install.ps1'))
```

## Was kann das Tool?

- Pakete erstellen, updaten und löschen
- Direkt auf OPSI-Server deployen  
- Workbench-Projekte verwalten
- Logs anzeigen

## Anforderungen

- Windows 10/11
- PowerShell 5.1+
- SSH Zugriff auf OPSI-Server (10.1.0.2)

## Changelog v2.0.1

### Fixes
- `opsi-package-manager -r` funktioniert jetzt mit `TERM=dumb`
- `opsi-makepackage --no-interactive` überschreibt automatisch
- Workbench wird beim Löschen komplett aufgeräumt

### Neue Features  
- Zeigt installierte Pakete UND Workbench-Projekte beim Löschen
- Kann mit Paket-IDs oder Workbench-Ordnernamen umgehen
- Mehrere Log-Dateien in den erweiterten Optionen

## Bekannte Probleme

Wenn ein Paket nicht richtig gelöscht wird:
```bash
ssh root@10.1.0.2
opsi-package-manager -r paketname --purge
rm -rf /var/lib/opsi/workbench/paketname*
```

## SSH ohne Passwort

```bash
ssh-keygen -t rsa -b 4096
ssh-copy-id root@10.1.0.2
```

## Silent-Parameter

| Installer | Parameter |
|-----------|-----------|
| MSI | `/qn` |
| NSIS | `/S` |
| InnoSetup | `/VERYSILENT /NORESTART` |

## Support

GitHub Issues: https://github.com/Elliot-Markus-John-Adams/opsi-packforge/issues

---

MIT License