# Packforge

```
                      ______ ________
______________ _________  /____  __/___________________ _____
___  __ \  __ `/  ___/_  //_/_  /_ _  __ \_  ___/_  __ `/  _ \
__  /_/ / /_/ // /__ _  ,<  _  __/ / /_/ /  /   _  /_/ //  __/
_  .___/\__,_/ \___/ /_/|_| /_/    \____//_/    _\__, / \___/
/_/                                             /____/
```

A menu-driven CLI tool for managing **paedML OPSI packages** — create, build, deploy,
update from the repository, wake clients, and run diagnostics. It's a single self-contained
Bash script that wraps the native `opsi-*` tools behind a `whiptail` interface.

## Requirements

Run it **directly on the OPSI depot/config server** (the paedML memberserver), as **root**.
It needs:

- `bash` and `whiptail`
- the OPSI tools: `opsi-makepackage`, `opsi-package-manager`, `opsi-admin`, `opsi-package-updater`
- write access to `/var/lib/opsi/workbench`

`whiptail` is usually preinstalled; if not: `apt install whiptail`.

## Installation

Install to `/usr/local/bin` (on `$PATH`, so you can run `packforge` from anywhere) — run each
line on its own:

```
curl -fsSL -o /usr/local/bin/packforge https://raw.githubusercontent.com/Elliot-Markus-John-Adams/opsi-packforge/main/packforge.sh
```

```
chmod +x /usr/local/bin/packforge
```

```
packforge
```

> Note: `raw.githubusercontent.com` caches for a few minutes. To force the very latest
> version, replace `main` in the URL with a commit hash.

To update later, just re-run the `curl` + `chmod` lines. To uninstall:
`rm /usr/local/bin/packforge`.

## Usage

Run `packforge` and pick from the menu:

| # | Item | What it does |
|---|------|--------------|
| 1 | Create package | Scaffold an OPSI package (control + setup/uninstall scripts), then build & install |
| 2 | Build package | Build a workbench package with `opsi-makepackage` and install it |
| 3 | Remove package | Remove a package from the depot (and clean its workbench dir) |
| 4 | Deploy to clients | Set `setup` for selected packages on all / selected / pattern-matched clients |
| 5 | Wake-on-LAN | Wake clients and check reachability |
| 6 | List packages | `opsi-package-manager -l` |
| 7 | Diagnostics | Failed actions, reset failed, client status/logs, services, disk, health check |
| 8 | Update from repository | Pull/update packages from the configured OPSI repositories |

Menus and confirmations are plain text; package selection uses `whiptail` checklists.

## Notes

- **`[8] Update from repository`** uses `opsi-package-updater` against the repos configured in
  `/etc/opsi/package-updater.repos.d/` (on paedML: the LMZ update server). It only sees the
  subset of the catalog provided there — not the full Service Desk catalog.
- **opsi version / zstd:** packages compressed with **zstd** require **opsi ≥ 4.2**. On an
  opsi 4.1 server they fail with *"No metadata archive found"* — that's a server-version issue,
  not a download problem. Packforge detects this and tells you instead of looping.
- `[7] OPSI health check` runs `opsiconfd health-check` on opsi ≥ 4.2, and falls back to basic
  service/backend/zstd checks on opsi 4.1.

## Single-file

Everything lives in [`packforge.sh`](packforge.sh). No dependencies beyond what's listed above.
