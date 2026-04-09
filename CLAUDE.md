# CLAUDE.md - OPSI Toolbox

## Project Overview

OPSI Toolbox is a Python/tkinter GUI application for OPSI (Open Source Platform for System Integration) server administration — packaging, Wake-on-LAN, diagnostics, and paedML Linux support.

**Version:** v3.0
**Repository:** https://github.com/Elliot-Markus-John-Adams/opsi-packforge.git

## Tech Stack

- **Python 3.x** with tkinter for GUI (no external dependencies)
- **PowerShell** for Windows installation automation
- **OPSI** - Linux-based client management platform target
- **SSH/SCP** for remote server communication

## Project Structure

```
opsi-packforge/
├── packforge.pyw      # Main GUI application (~2200 lines)
├── install.ps1        # Windows PowerShell installer
└── CLAUDE.md          # This file
```

## Application Pages

### 1. Dashboard
Live server overview with auto-refresh:
- Server status (opsiconfd)
- Package count, clients online, disk space, failed deployments
- Quick action buttons

### 2. Packaging (3 sub-tabs)
- **Create Package** — Build OPSI packages from installers (MSI, InnoSetup, NSIS, EXE, PS1, BAT)
- **Update Package** — Upload .opsi files, deploy with `-S` (setup on clients) or `-U` (update action)
- **Remove Package** — Remove/purge packages with search filter, multi-select, all-depots option

### 3. Wake on LAN
- Left panel: Live client status list (name, IP, MAC, online/offline) from OPSI API
- Right panel: Wake All / Wake Group / Wake Selected / Manual MAC entry
- Additional: Reboot Selected, Shutdown Selected
- Auto-refresh toggle (10s interval)
- Groups fetched from OPSI server

### 4. Diagnostics (4 sub-tabs)
- **Connection** — Ping, SSH test, port check (22, 4447, 445, 80, 443)
- **Server Health** — `opsi-cli support health-check`, service status grid (7 services), quick checks (disk, certs, NTP, versions)
- **Client Diagnostics** — Product status per client, failed installs across all clients, log viewer
- **paedML Checks** — 10-point diagnostic: NTP, disk, certs, DNS, DHCP, Samba AD, domain join, Sophomorix

## Key OPSI Commands Used

| Operation | Command |
|-----------|---------|
| Build package | `opsi-makepackage --keep-versions` |
| Install package | `opsi-package-manager -i <pkg.opsi>` |
| Update (setup clients) | `opsi-package-manager -S -i <pkg.opsi>` |
| Remove package | `opsi-package-manager -r <product-id>` |
| Purge package | `opsi-package-manager --purge <product-id>` |
| List packages | `opsi-package-manager -l` |
| Wake clients | `opsi-admin -d method hostControlSafe_start` |
| Client reachability | `opsi-admin -d method hostControlSafe_reachable` |
| Health check | `opsi-cli support health-check` |

## Global Settings

Server IP and SSH user are configured in the sidebar (shared across all pages).

## Custom Widgets

- **ModernEntry** — Styled entry with placeholder support
- **ModernButton** — Canvas button with hover effects and rounded corners
- **SidebarButton** — Navigation button with active indicator
- **TabButton** — Sub-page tab switching

## Color Theme

Dark theme with blue accents:
- Background: `#0a0a0a`
- Cards: `#161616`
- Accent: `#3b82f6`
- Success: `#22c55e`
- Warning: `#f59e0b`
- Error: `#ef4444`

## Running the Application

```bash
python packforge.pyw
pythonw packforge.pyw  # No console window

# Windows installation
irm https://raw.githubusercontent.com/elliot-markus-john-adams/opsi-packforge/main/install.ps1 | iex
```

## Development Notes

- All SSH commands run in background threads to avoid UI blocking
- `_ssh_cmd()` / `_ssh_bg()` are centralized SSH helpers using global server settings
- `self.after(0, callback)` is used for thread-safe UI updates
- Package IDs must be lowercase, numbers, hyphens only
- No external Python dependencies required
