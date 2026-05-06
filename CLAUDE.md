# CLAUDE.md - OPSI PackForge CLI

## Project Overview

OPSI PackForge is a Python CLI tool that runs **directly on OPSI servers** for administration — packaging, Wake-on-LAN, diagnostics, and paedML Linux support.

Technicians SSH into a customer server, then run `packforge` locally. No GUI, no external dependencies.

**Version:** v4.0
**Repository:** https://github.com/Elliot-Markus-John-Adams/opsi-packforge.git

## Tech Stack

- **Python 3.6+** (stdlib only, zero external dependencies)
- **OPSI** — Linux-based client management platform
- Runs on **Univention DC Master** / Debian-based OPSI servers

## Project Structure

```
opsi-packforge/
├── packforge.py       # Single-file CLI tool (~900 lines)
└── CLAUDE.md          # This file
```

## CLI Commands

```
packforge [--no-color] [--json] [-y] <command> [subcommand]

(no args)                          Dashboard (default)

pkg list                           List installed packages
pkg create [path]                  Build package from workbench dir
pkg create --wizard                Interactive package wizard
pkg install <file.opsi> [-S|-U]    Install package to depot
pkg remove [product-id]            Remove package (interactive if no ID)
  --depots-all                     Remove from all depots

wol list                           Client status (online/offline)
wol wake [--all|--group <g>|<id>]  Wake clients
wol reboot <id>...                 Reboot clients
wol shutdown <id>...               Shutdown clients
wol groups                         List host groups

diag health                        opsi-cli support health-check
diag services                      Check systemd services
diag quick                         Disk, certs, NTP, version
diag client <id>                   Product status per client
diag failed                        All failed installations
diag logs <id>                     View client logs
diag paedml                        paedML 10-point check

self-update                        Update from GitHub
self-install                       Install to /usr/local/bin/
```

## Key OPSI Commands Used

| Operation | Command |
|-----------|---------|
| Build package | `opsi-makepackage --keep-versions` |
| Install package | `opsi-cli package install <file>` |
| Install + setup | `opsi-cli package install --setup-where-installed` |
| Remove package | `opsi-cli package uninstall <id>` |
| List packages | `opsi-package-manager -l` |
| Wake clients | `opsi-cli jsonrpc execute hostControlSafe_start` |
| Reachability | `opsi-cli jsonrpc execute hostControlSafe_reachable` |
| Health check | `opsi-cli support health-check` |

Falls back to `opsi-admin` on older OPSI installations.

## Deployment

```bash
# Install on a server
curl -fsSL https://raw.githubusercontent.com/elliot-markus-john-adams/opsi-packforge/main/packforge.py -o /usr/local/bin/packforge && chmod +x /usr/local/bin/packforge

# Or self-install after download
python3 packforge.py self-install

# Update
packforge self-update
```

## Architecture Notes

- Single file, zero dependencies — runs anywhere with Python 3.6+
- All commands run locally via `subprocess.run()` (no SSH — the tool is ON the server)
- `detect_opsi_cli()` auto-detects `opsi-cli` vs `opsi-admin` for compatibility
- `opsi_jsonrpc()` is the central helper for all OPSI API calls
- ANSI colors auto-disabled when piped or `--no-color` / `NO_COLOR` env
- `--json` flag for machine-readable output (scripting)
- `-y` flag skips confirmations (automation)
- Interactive pickers (`pick_one`, `pick_many`) when no args given
- Package IDs: lowercase, numbers, hyphens only
