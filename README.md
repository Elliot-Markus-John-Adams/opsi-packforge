# OPSI PackForge

Tool for OPSI package management in paedML Linux.

## Installation

```powershell
[System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials
iex ((New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/Elliot-Markus-John-Adams/opsi-packforge/main/install.ps1'))
```

## Features

- Create, update and delete packages
- Deploy directly to OPSI server
- Manage workbench projects
- View logs

## Requirements

- Windows 10/11
- PowerShell 5.1+
- SSH access to OPSI server (10.1.0.2)

## Changelog v2.0.1

### Fixes
- `opsi-package-manager -r` now works with `TERM=dumb`
- `opsi-makepackage --no-interactive` overwrites automatically
- Workbench is completely cleaned up when deleting

### New Features
- Shows installed packages AND workbench projects when deleting
- Can handle package IDs or workbench folder names
- Multiple log files in advanced options

## Known Issues

If a package is not deleted properly:
```bash
ssh root@10.1.0.2
opsi-package-manager -r packagename --purge
rm -rf /var/lib/opsi/workbench/packagename*
```

## SSH without Password

```bash
ssh-keygen -t rsa -b 4096
ssh-copy-id root@10.1.0.2
```

## Silent Parameters

| Installer | Parameter |
|-----------|-----------|
| MSI | `/qn` |
| NSIS | `/S` |
| InnoSetup | `/VERYSILENT /NORESTART` |

## Support

GitHub Issues: https://github.com/Elliot-Markus-John-Adams/opsi-packforge/issues

---

MIT License
