# CLAUDE.md

Guidance for working in this repo.

## What this is

`packforge.sh` — a single-file, menu-driven Bash TUI for managing paedML OPSI packages on the
OPSI depot server. It wraps `opsi-makepackage`, `opsi-package-manager`, `opsi-admin`, and
`opsi-package-updater` behind a `whiptail` interface. See [README.md](README.md) for install/usage.

## Conventions

- **Everything lives in `packforge.sh`.** No build step, no dependencies beyond bash + whiptail +
  the opsi tools. Keep it a single file.
- **UI language is English.** All menus, prompts, and messages are English.
- **Menus & confirmations are plain `echo`/`read`** (like the main menu). Use `whiptail` **only**
  for multi-select package/client checklists — not for menus, yes/no prompts, or result output.
- For long/spinning operations use the `run_spin` (spinner) / `run_progress` (progress bar)
  helpers; they capture output to a temp file and strip ANSI codes. Show a clean summary, not the
  raw opsi log.
- State-changing `opsi-admin` / install commands must confirm before running.
- Target runtime is an older paedML server (opsi 4.1, Python 2.7) — keep shell portable; avoid
  assuming new opsi subcommands exist (gate by version, e.g. `opsiconfd health-check` is 4.2+).

## Gotchas

- `opsi-package-updater` writes to **stderr** and **colorizes** output — capture with `2>&1` and
  strip ANSI before parsing.
- Its `list` output is **not indented**; parse accordingly.
- Don't run a command that reads stdin inside a `while read` loop fed by a pipe without
  `</dev/null` (it will eat the loop's input).
- `.opsi` packages using **zstd** compression need opsi ≥ 4.2; opsi 4.1 can't read them.

## Verify changes

`bash -n packforge.sh` for syntax. There are no automated tests; test menu flows manually on a
real opsi server.
