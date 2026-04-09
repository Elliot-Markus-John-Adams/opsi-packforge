# CLAUDE.md - OPSI PackForge

## Project Overview

OPSI PackForge is a Python/tkinter GUI application for creating OPSI (Open Source Platform for System Integration) packages for Windows software deployment.

**Version:** v2.0
**Repository:** https://github.com/Elliot-Markus-John-Adams/opsi-packforge.git

## Tech Stack

- **Python 3.x** with tkinter for GUI (no external dependencies)
- **PowerShell** for Windows installation automation
- **OPSI** - Linux-based client management platform target

## Project Structure

```
opsi-packforge/
├── packforge.pyw      # Main GUI application (~900 lines)
├── install.ps1        # Windows PowerShell installer
└── CLAUDE.md          # This file
```

## Key Components

### packforge.pyw

Single-file application with:

- **ModernEntry** - Custom styled entry with placeholder support
- **ModernButton** - Custom styled button with hover effects
- **PackForgeApp** - Main application window (5-tab interface)

### Application Tabs

1. **Package Info** - Package metadata (ID, name, version, description)
2. **Files** - Installer selection with type detection (MSI, InnoSetup, NSIS, InstallShield, EXE, PowerShell, Batch)
3. **Dependencies** - Product dependencies for installation order
4. **Properties** - Custom configuration properties
5. **Build & Deploy** - Build ZIP packages or deploy to OPSI server via SSH

### Supported Installer Types

| Type | Silent Parameters |
|------|-------------------|
| MSI | `/qn /norestart` |
| InnoSetup | `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART` |
| NSIS | `/S` |
| InstallShield | `/s /sms` |
| Generic EXE | `/silent` |
| PowerShell | `-ExecutionPolicy Bypass -File` |
| Batch | (none) |

## Build Output

Generates OPSI package structure:
```
{id}_{version}-{release}/
├── OPSI/
│   └── control           # Package metadata
└── CLIENT_DATA/
    ├── setup.opsiscript  # Installation script
    ├── uninstall.opsiscript
    └── files/            # Installer files
```

## Running the Application

```bash
# Direct execution
python packforge.pyw
pythonw packforge.pyw  # No console window

# Windows installation (downloads and sets up)
irm https://raw.githubusercontent.com/elliot-markus-john-adams/opsi-packforge/main/install.ps1 | iex
```

## Deployment

Remote deployment uses SSH/SCP to:
1. Transfer package to `/var/lib/opsi/workbench/` on OPSI server
2. Run `opsi-makepackage` to build .opsi file
3. Run `opsi-package-manager -i` to install

## Color Theme

Dark theme with cyan accents:
- Background: `#0d0d0d`
- Cards: `#1a1a1a`
- Accent: `#00d4ff`
- Success: `#00ff88`
- Warning: `#ffaa00`
- Error: `#ff4444`

## Development Notes

- Validation: Package IDs must be lowercase, numbers, hyphens only
- File operations use `shutil`, `zipfile`, `pathlib`
- SSH operations use `subprocess` to call system `scp` and `ssh`
- No external Python dependencies required
