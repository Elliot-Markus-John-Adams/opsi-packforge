#!/usr/bin/env python3
"""OPSI PackForge CLI v4.0.0 — On-server OPSI administration tool.

Run directly on an OPSI server. No external dependencies required.
https://github.com/elliot-markus-john-adams/opsi-packforge
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import threading
import time

VERSION = "4.0.0"
WORKBENCH = "/var/lib/opsi/workbench"
LOG_DIR = "/var/log/opsi"
GITHUB_RAW = (
    "https://raw.githubusercontent.com/"
    "elliot-markus-john-adams/opsi-packforge/main/packforge.py"
)

SERVICES = [
    "opsiconfd",
    "opsipxeconfd",
    "smbd",
    "isc-dhcp-server",
    "apache2",
    "mysql",
    "redis-server",
]

# Global options set by main()
OPTS = {"no_color": False, "json_mode": False, "yes": False}


# ============================================================
# ANSI COLORS
# ============================================================

class C:
    """ANSI color codes. Call C.disable() to strip all color."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    @classmethod
    def disable(cls):
        for attr in (
            "RESET", "BOLD", "DIM", "RED", "GREEN",
            "YELLOW", "BLUE", "CYAN", "WHITE", "GRAY",
        ):
            setattr(cls, attr, "")


# ============================================================
# OUTPUT HELPERS
# ============================================================

def ok(msg):
    print(f"  {C.GREEN}\u2713{C.RESET} {msg}")


def err(msg):
    print(f"  {C.RED}\u2717{C.RESET} {msg}")


def warn(msg):
    print(f"  {C.YELLOW}!{C.RESET} {msg}")


def info(msg):
    print(f"  {C.BLUE}\u2022{C.RESET} {msg}")


def header(title):
    print(f"\n{C.BOLD}{C.CYAN}  {title}{C.RESET}")
    line = "\u2500" * len(title)
    print(f"  {line}")


def die(msg):
    err(msg)
    sys.exit(1)


def table(rows, headers=None, indent=2):
    """Print a simple aligned table."""
    if not rows:
        return
    all_rows = ([headers] + list(rows)) if headers else list(rows)
    cols = len(all_rows[0])
    widths = [0] * cols
    # Strip ANSI for width calculation
    ansi_re = re.compile(r"\033\[[0-9;]*[a-zA-Z]")
    for row in all_rows:
        for i, cell in enumerate(row):
            visible = ansi_re.sub("", str(cell))
            widths[i] = max(widths[i], len(visible))
    prefix = " " * indent
    for j, row in enumerate(all_rows):
        parts = []
        for i, cell in enumerate(row):
            s = str(cell)
            visible_len = len(ansi_re.sub("", s))
            pad = widths[i] - visible_len
            parts.append(s + " " * pad)
        print(prefix + "  ".join(parts).rstrip())
        if headers and j == 0:
            total = sum(widths) + 2 * (cols - 1)
            print(prefix + "\u2500" * total)


def confirm(msg):
    """Ask yes/no. Returns True if --yes or user answers y."""
    if OPTS["yes"]:
        return True
    try:
        answer = input(f"  {msg} [y/N] ").strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


# ============================================================
# SPINNER
# ============================================================

class Spinner:
    """Simple braille spinner for long-running commands."""

    CHARS = "\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f"

    def __init__(self, msg):
        self.msg = msg
        self.running = False
        self.thread = None

    def __enter__(self):
        if sys.stdout.isatty() and not OPTS["no_color"]:
            self.running = True
            self.thread = threading.Thread(target=self._spin, daemon=True)
            self.thread.start()
        else:
            print(f"  {self.msg}...")
        return self

    def __exit__(self, *_):
        self.running = False
        if self.thread:
            self.thread.join()
            print(f"\r  {' ' * (len(self.msg) + 4)}\r", end="", flush=True)

    def _spin(self):
        i = 0
        while self.running:
            ch = self.CHARS[i % len(self.CHARS)]
            print(f"\r  {C.BLUE}{ch}{C.RESET} {self.msg}", end="", flush=True)
            i += 1
            time.sleep(0.08)


# ============================================================
# COMMAND RUNNER
# ============================================================

def run(cmd, timeout=30, check=False):
    """Run a local shell command. Returns (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout,
        )
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if check and result.returncode != 0:
            die(f"Command failed: {cmd}\n    {stderr}")
        return stdout, stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", f"Timed out after {timeout}s", -1
    except Exception as exc:
        return "", str(exc), -1


def run_json(cmd, timeout=30):
    """Run command and parse JSON from its output."""
    stdout, _, rc = run(cmd, timeout=timeout)
    if rc != 0:
        return None
    return parse_json(stdout)


def parse_json(text):
    """Extract JSON from text that may have non-JSON prefix (warnings, banners)."""
    if not text:
        return None
    for i, ch in enumerate(text):
        if ch in ("[", "{"):
            try:
                return json.loads(text[i:])
            except json.JSONDecodeError:
                continue
    return None


# ============================================================
# OPSI CLI HELPERS
# ============================================================

_OPSI_CLI = None  # cached after first detection


def detect_opsi_cli():
    """Return 'opsi-cli', 'opsi-admin', or None."""
    global _OPSI_CLI
    if _OPSI_CLI is None:
        if shutil.which("opsi-cli"):
            _OPSI_CLI = "opsi-cli"
        elif shutil.which("opsi-admin"):
            _OPSI_CLI = "opsi-admin"
        else:
            _OPSI_CLI = ""
    return _OPSI_CLI or None


def opsi_jsonrpc(method, params="'[]'", filter_arg="'[]'", timeout=30):
    """Execute an OPSI JSONRPC call via whichever CLI is available."""
    cli = detect_opsi_cli()
    if cli == "opsi-cli":
        cmd = (
            f"opsi-cli --output-format json jsonrpc execute "
            f"{method} {params} {filter_arg}"
        )
    elif cli == "opsi-admin":
        cmd = f"opsi-admin -d method {method} {params} {filter_arg}"
    else:
        return None
    return run_json(cmd, timeout=timeout)


# ============================================================
# INTERACTIVE HELPERS
# ============================================================

def pick_one(items, prompt="Select", display=None):
    """Show numbered list, return single selected item or None."""
    if not items:
        warn("No items to select from.")
        return None
    for i, item in enumerate(items, 1):
        label = display(item) if display else str(item)
        print(f"  {C.DIM}{i:3d}{C.RESET}  {label}")
    print()
    try:
        choice = input(f"  {prompt} [1-{len(items)}, q]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if choice.lower() == "q":
        return None
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(items):
            return items[idx]
    except ValueError:
        pass
    err("Invalid selection.")
    return None


def pick_many(items, prompt="Select", display=None):
    """Show numbered list, return list of selected items.

    Supports: single numbers, comma-separated, ranges (1-5), 'all', 'q'.
    """
    if not items:
        warn("No items to select from.")
        return []
    for i, item in enumerate(items, 1):
        label = display(item) if display else str(item)
        print(f"  {C.DIM}{i:3d}{C.RESET}  {label}")
    print()
    try:
        choice = input(f"  {prompt} [numbers/ranges, 'all', q]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return []
    if choice.lower() == "q":
        return []
    if choice.lower() == "all":
        return list(items)
    selected = set()
    for part in choice.split(","):
        part = part.strip()
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                for n in range(int(a), int(b) + 1):
                    if 1 <= n <= len(items):
                        selected.add(n - 1)
            except ValueError:
                pass
        else:
            try:
                n = int(part)
                if 1 <= n <= len(items):
                    selected.add(n - 1)
            except ValueError:
                pass
    return [items[i] for i in sorted(selected)]


# ============================================================
# DASHBOARD
# ============================================================

def cmd_dashboard(args):
    """Show server status overview."""
    header("OPSI PackForge Dashboard")

    # opsiconfd status
    stdout, _, rc = run("systemctl is-active opsiconfd 2>/dev/null")
    if rc == 0 and stdout == "active":
        ok(f"opsiconfd {C.GREEN}active{C.RESET}")
    else:
        err(f"opsiconfd {C.RED}{stdout or 'inactive'}{C.RESET}")

    # Package count
    stdout, _, rc = run("opsi-package-manager -l 2>/dev/null | wc -l")
    pkg_count = stdout.strip() if rc == 0 else "?"
    info(f"Packages installed: {C.BOLD}{pkg_count}{C.RESET}")

    # Client count
    clients = opsi_jsonrpc(
        "host_getObjects", "'[]'", """'{"type":"OpsiClient"}'""",
    )
    client_count = len(clients) if clients else "?"
    info(f"Clients registered: {C.BOLD}{client_count}{C.RESET}")

    # Disk space
    stdout, _, rc = run(
        "df /var/lib/opsi --output=pcent,avail 2>/dev/null | tail -1",
    )
    if rc == 0 and stdout:
        parts = stdout.split()
        pct = parts[0] if parts else "?"
        avail = parts[1] if len(parts) > 1 else "?"
        info(f"Disk: {C.BOLD}{pct}{C.RESET} used, {avail} available")
    else:
        warn("Disk info unavailable")

    # Failed deployments
    failed = opsi_jsonrpc(
        "productOnClient_getObjects", "'[]'", """'{"actionResult":"failed"}'""",
    )
    fail_count = len(failed) if failed else 0
    if fail_count > 0:
        warn(f"Failed deployments: {C.RED}{C.BOLD}{fail_count}{C.RESET}")
    else:
        ok(f"Failed deployments: {C.GREEN}0{C.RESET}")

    # Services
    print()
    header("Services")
    for svc in SERVICES:
        stdout, _, rc = run(f"systemctl is-active {svc} 2>/dev/null")
        if rc == 0 and stdout == "active":
            ok(svc)
        else:
            status = stdout if stdout else "not found"
            if status == "inactive":
                warn(f"{svc} ({status})")
            else:
                err(f"{svc} ({status})")


# ============================================================
# PACKAGING
# ============================================================

def cmd_pkg_list(args):
    """List installed packages."""
    header("Installed Packages")
    with Spinner("Fetching package list"):
        stdout, stderr, rc = run("opsi-package-manager -l 2>/dev/null", timeout=30)

    if rc != 0 or not stdout:
        die("Failed to list packages. Is OPSI installed?")

    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]

    if OPTS["json_mode"]:
        print(json.dumps([{"raw": ln} for ln in lines], indent=2))
        return

    for line in sorted(lines):
        print(f"  {line}")
    print(f"\n  {C.DIM}{len(lines)} package(s){C.RESET}")


def cmd_pkg_create(args):
    """Create / build an OPSI package."""
    if getattr(args, "wizard", False):
        _pkg_wizard()
        return

    path = getattr(args, "path", None)
    if not path:
        header("Workbench Packages")
        if not os.path.isdir(WORKBENCH):
            die(f"Workbench not found: {WORKBENCH}")
        dirs = sorted(
            d for d in os.listdir(WORKBENCH)
            if os.path.isdir(os.path.join(WORKBENCH, d))
            and os.path.isdir(os.path.join(WORKBENCH, d, "OPSI"))
        )
        if not dirs:
            die("No packages found in workbench.")
        selected = pick_one(dirs, prompt="Select package to build")
        if not selected:
            return
        path = os.path.join(WORKBENCH, selected)

    if not os.path.isdir(path):
        die(f"Directory not found: {path}")
    if not os.path.isdir(os.path.join(path, "OPSI")):
        die(f"Not a valid OPSI package (no OPSI/ folder): {path}")

    pkg_name = os.path.basename(os.path.normpath(path))

    if getattr(args, "keep_versions", False):
        build_cmd = f"cd '{path}' && opsi-makepackage --keep-versions"
    elif getattr(args, "version", None):
        build_cmd = f"cd '{path}' && opsi-makepackage --product-version {args.version}"
        if getattr(args, "release", None):
            build_cmd += f" --package-version {args.release}"
    else:
        build_cmd = f"cd '{path}' && opsi-makepackage"

    info(f"Building {C.BOLD}{pkg_name}{C.RESET}...")
    with Spinner("Running opsi-makepackage"):
        stdout, stderr, rc = run(build_cmd, timeout=300)

    if rc != 0:
        err(f"Build failed:\n    {stderr}")
        if stdout:
            print(f"    {stdout}")
        return

    ok(f"Package built: {pkg_name}")
    for line in (stdout or "").splitlines():
        if ".opsi" in line:
            print(f"  {C.DIM}{line.strip()}{C.RESET}")

    if confirm(f"Install {pkg_name} to depot?"):
        opsi_file, _, _ = run(
            f"ls -t '{WORKBENCH}'/{pkg_name}*.opsi 2>/dev/null | head -1",
        )
        if not opsi_file:
            opsi_file, _, _ = run(
                f"ls -t '{path}'/{pkg_name}*.opsi 2>/dev/null | head -1",
            )
        if opsi_file:
            _pkg_install_file(opsi_file)
        else:
            warn("Could not find built .opsi file. Install manually.")


def _pkg_wizard():
    """Interactive package creation wizard."""
    header("Package Creation Wizard")
    print()

    silent_defaults = {
        "msi": "/qn /norestart",
        "inno": "/VERYSILENT /NORESTART",
        "nsis": "/S",
        "exe": "/S",
        "ps1": "",
        "bat": "",
    }

    try:
        pkg_id = input("  Package ID (lowercase, hyphens): ").strip()
        if not pkg_id or not re.match(r"^[a-z0-9][a-z0-9\-]*$", pkg_id):
            die("Invalid package ID. Use lowercase letters, numbers, hyphens.")

        version = input("  Version [1.0.0]: ").strip() or "1.0.0"
        name = input(f"  Product Name [{pkg_id}]: ").strip() or pkg_id
        description = input("  Description: ").strip()

        print(f"\n  Installer types: msi, inno, nsis, exe, ps1, bat")
        inst_type = input("  Installer type [exe]: ").strip().lower() or "exe"
        if inst_type not in silent_defaults:
            warn(f"Unknown type '{inst_type}', defaulting to exe.")
            inst_type = "exe"

        default_params = silent_defaults[inst_type]
        silent = input(f"  Silent parameters [{default_params}]: ").strip()
        if not silent:
            silent = default_params
    except (EOFError, KeyboardInterrupt):
        print()
        return

    # Create directory structure
    pkg_dir = os.path.join(WORKBENCH, pkg_id)
    opsi_dir = os.path.join(pkg_dir, "OPSI")
    client_dir = os.path.join(pkg_dir, "CLIENT_DATA")
    files_dir = os.path.join(client_dir, "files")

    if os.path.exists(pkg_dir):
        if not confirm(f"Directory {pkg_dir} exists. Overwrite scripts?"):
            return

    os.makedirs(opsi_dir, exist_ok=True)
    os.makedirs(files_dir, exist_ok=True)

    # control file
    control = textwrap.dedent(f"""\
        [Package]
        version: 1
        depends:

        [Product]
        type: localboot
        id: {pkg_id}
        name: {name}
        description: {description}
        advice:
        version: {version}
        packageVersion: 1
        priority: 0
        licenseRequired: False
        productClasses:
        setupScript: setup.opsiscript
        uninstallScript: uninstall.opsiscript
        updateScript:
        alwaysScript:
        onceScript:
        customScript:
        userLoginScript:
    """)
    with open(os.path.join(opsi_dir, "control"), "w") as fh:
        fh.write(control)

    # setup script
    if inst_type == "msi":
        install_block = (
            "Winbatch_install\n\n"
            "[Winbatch_install]\n"
            f'msiexec /i "%ScriptPath%\\files\\*.msi" {silent}'
        )
    elif inst_type in ("inno", "nsis", "exe"):
        install_block = (
            "Winbatch_install\n\n"
            "[Winbatch_install]\n"
            f'"%ScriptPath%\\files\\*.exe" {silent}'
        )
    elif inst_type == "ps1":
        install_block = (
            "ShellScript_install\n\n"
            "[ShellScript_install]\n"
            'powershell -ExecutionPolicy Bypass '
            '-File "%ScriptPath%\\files\\install.ps1"'
        )
    else:
        install_block = (
            "ShellScript_install\n\n"
            "[ShellScript_install]\n"
            'call "%ScriptPath%\\files\\install.bat"'
        )

    setup_script = textwrap.dedent(f"""\
        [Actions]
        requiredWinstVersion >= "4.12"
        ScriptErrorMessages = false

        DefVar $ProductId$
        Set $ProductId$ = "{pkg_id}"

        Message "Installing " + $ProductId$ + " ..."

        {install_block}
    """)
    with open(os.path.join(client_dir, "setup.opsiscript"), "w") as fh:
        fh.write(setup_script)

    # uninstall script
    uninstall_script = textwrap.dedent(f"""\
        [Actions]
        requiredWinstVersion >= "4.12"
        ScriptErrorMessages = false

        DefVar $ProductId$
        Set $ProductId$ = "{pkg_id}"

        Message "Uninstalling " + $ProductId$ + " ..."

        comment "TODO: Add uninstall command"
    """)
    with open(os.path.join(client_dir, "uninstall.opsiscript"), "w") as fh:
        fh.write(uninstall_script)

    ok(f"Package created at {pkg_dir}")
    info(f"Place installer files in: {files_dir}/")
    print()

    if confirm("Build package now?"):
        with Spinner("Running opsi-makepackage"):
            stdout, stderr, rc = run(
                f"cd '{WORKBENCH}' && opsi-makepackage --keep-versions {pkg_id}",
                timeout=300,
            )
        if rc == 0:
            ok("Package built successfully.")
        else:
            err(f"Build failed: {stderr}")


def cmd_pkg_install(args):
    """Install a .opsi package to the depot."""
    setup = getattr(args, "setup_where_installed", False)
    update = getattr(args, "update_where_installed", False)
    _pkg_install_file(args.file, setup=setup, update=update)


def _pkg_install_file(filepath, setup=False, update=False):
    """Install an .opsi file."""
    if not os.path.isfile(filepath):
        die(f"File not found: {filepath}")

    cli = detect_opsi_cli()
    if cli == "opsi-cli":
        cmd = "TERM=dumb opsi-cli package install"
        if setup:
            cmd += " --setup-where-installed"
        elif update:
            cmd += " --update-where-installed"
        cmd += f" '{filepath}'"
    else:
        cmd = "opsi-package-manager -i"
        if setup:
            cmd += " -S"
        elif update:
            cmd += " -U"
        cmd += f" '{filepath}'"

    info(f"Installing {C.BOLD}{os.path.basename(filepath)}{C.RESET}...")
    with Spinner("Installing package"):
        stdout, stderr, rc = run(cmd, timeout=600)

    if rc == 0:
        ok("Package installed.")
        if stdout:
            for line in stdout.splitlines()[-3:]:
                print(f"  {C.DIM}{line}{C.RESET}")
    else:
        err(f"Install failed: {stderr}")


def cmd_pkg_remove(args):
    """Remove a package from the depot."""
    product_id = getattr(args, "product_id", None)
    depots_all = getattr(args, "depots_all", False)

    if not product_id:
        header("Remove Package")
        with Spinner("Fetching package list"):
            stdout, _, rc = run("opsi-package-manager -l 2>/dev/null", timeout=30)
        if rc != 0 or not stdout:
            die("Failed to list packages.")
        packages = sorted(
            line.strip().split()[0]
            for line in stdout.splitlines()
            if line.strip()
        )
        selected = pick_many(packages, prompt="Select package(s) to remove")
        if not selected:
            return
        for pkg in selected:
            _remove_one(pkg, depots_all=depots_all)
        return

    _remove_one(product_id, depots_all=depots_all)


def _remove_one(product_id, depots_all=False):
    """Remove a single package."""
    if not confirm(f"Remove {C.BOLD}{product_id}{C.RESET}?"):
        return

    cli = detect_opsi_cli()
    if cli == "opsi-cli":
        cmd = "opsi-cli package uninstall"
        if depots_all:
            cmd += " --depots all"
        cmd += f" {product_id}"
    else:
        cmd = "opsi-package-manager -r"
        if depots_all:
            cmd += " --depots '*'"
        cmd += f" {product_id}"

    with Spinner(f"Removing {product_id}"):
        _, stderr, rc = run(cmd, timeout=120)

    if rc == 0:
        ok(f"Removed {product_id}")
    else:
        err(f"Failed to remove {product_id}: {stderr}")


# ============================================================
# WAKE ON LAN
# ============================================================

def _fetch_clients():
    """Fetch all OPSI clients with online/offline status."""
    clients = opsi_jsonrpc(
        "host_getObjects", "'[]'", """'{"type":"OpsiClient"}'""", timeout=30,
    )
    if not clients:
        return []

    reachable = opsi_jsonrpc(
        "hostControlSafe_reachable", '\'["*"]\'', timeout=30,
    )
    reach_map = {}
    if isinstance(reachable, dict):
        for host_id, val in reachable.items():
            reach_map[host_id] = val is True
    elif isinstance(reachable, list):
        for item in reachable:
            if isinstance(item, dict) and "id" in item:
                reach_map[item["id"]] = item.get("reachable", False) is True

    result = []
    for c in clients:
        cid = c.get("id", "")
        result.append({
            "id": cid,
            "ip": c.get("ipAddress", ""),
            "mac": c.get("hardwareAddress", ""),
            "online": reach_map.get(cid, False),
        })
    return sorted(result, key=lambda x: x["id"])


def cmd_wol_list(args):
    """List clients with online/offline status."""
    header("Clients")
    with Spinner("Fetching clients"):
        clients = _fetch_clients()

    if not clients:
        warn("No clients found.")
        return

    if OPTS["json_mode"]:
        print(json.dumps(clients, indent=2))
        return

    online = sum(1 for c in clients if c["online"])
    rows = []
    for c in clients:
        status = (
            f"{C.GREEN}Online{C.RESET}"
            if c["online"]
            else f"{C.DIM}Offline{C.RESET}"
        )
        rows.append((c["id"], c["ip"] or "-", c["mac"] or "-", status))

    table(rows, headers=("Client ID", "IP", "MAC", "Status"))
    print(f"\n  {C.DIM}{online}/{len(clients)} online{C.RESET}")


def cmd_wol_wake(args):
    """Wake clients via OPSI."""
    if getattr(args, "all", False):
        if not confirm("Wake ALL clients?"):
            return
        info("Waking all clients...")
        cli = detect_opsi_cli()
        if cli == "opsi-cli":
            cmd = "opsi-cli jsonrpc execute hostControlSafe_start '[\"*\"]'"
        else:
            cmd = "opsi-admin -d method hostControlSafe_start '*'"
        _, stderr, rc = run(cmd, timeout=30)
        if rc == 0:
            ok("Wake signal sent to all clients.")
        else:
            err(f"Failed: {stderr}")
        return

    group = getattr(args, "group", None)
    if group:
        _wol_group(group)
        return

    client_ids = getattr(args, "clients", None)
    if client_ids:
        _wol_send(client_ids)
        return

    # Interactive picker
    header("Wake on LAN")
    with Spinner("Fetching clients"):
        clients = _fetch_clients()
    offline = [c for c in clients if not c["online"]]
    if not offline:
        ok("All clients are already online.")
        return
    selected = pick_many(
        offline,
        prompt="Select clients to wake",
        display=lambda c: f"{c['id']:<40} {c['ip'] or '-':<15} {c['mac'] or '-'}",
    )
    if selected:
        _wol_send([c["id"] for c in selected])


def _wol_group(group_name):
    """Wake all clients in a host group."""
    members = opsi_jsonrpc(
        "objectToGroup_getObjects", "'[]'",
        f"""'{{"groupType":"HostGroup","groupId":"{group_name}"}}'""",
        timeout=30,
    )
    if not members:
        die(f"No members found in group '{group_name}'.")
    ids = [m.get("objectId", "") for m in members if m.get("objectId")]
    if not ids:
        die(f"No client IDs in group '{group_name}'.")
    info(f"Waking {len(ids)} client(s) in group '{group_name}'...")
    _wol_send(ids)


def _wol_send(client_ids):
    """Send WoL signal to specific clients."""
    ids_json = json.dumps(client_ids)
    cli = detect_opsi_cli()
    if cli == "opsi-cli":
        cmd = f"opsi-cli jsonrpc execute hostControlSafe_start '{ids_json}'"
    else:
        cmd = f"opsi-admin -d method hostControlSafe_start '{ids_json}'"
    _, stderr, rc = run(cmd, timeout=30)
    if rc == 0:
        ok(f"Wake signal sent to {len(client_ids)} client(s).")
    else:
        err(f"Failed: {stderr}")


def cmd_wol_reboot(args):
    """Reboot selected clients."""
    if not args.clients:
        die("Specify client ID(s) to reboot.")
    if not confirm(f"Reboot {len(args.clients)} client(s)?"):
        return
    ids_json = json.dumps(args.clients)
    cli = detect_opsi_cli()
    if cli == "opsi-cli":
        cmd = f"opsi-cli jsonrpc execute hostControlSafe_reboot '{ids_json}'"
    else:
        cmd = f"opsi-admin -d method hostControlSafe_reboot '{ids_json}'"
    _, stderr, rc = run(cmd, timeout=30)
    if rc == 0:
        ok("Reboot signal sent.")
    else:
        err(f"Failed: {stderr}")


def cmd_wol_shutdown(args):
    """Shut down selected clients."""
    if not args.clients:
        die("Specify client ID(s) to shut down.")
    if not confirm(f"Shut down {len(args.clients)} client(s)?"):
        return
    ids_json = json.dumps(args.clients)
    cli = detect_opsi_cli()
    if cli == "opsi-cli":
        cmd = f"opsi-cli jsonrpc execute hostControlSafe_shutdown '{ids_json}'"
    else:
        cmd = f"opsi-admin -d method hostControlSafe_shutdown '{ids_json}'"
    _, stderr, rc = run(cmd, timeout=30)
    if rc == 0:
        ok("Shutdown signal sent.")
    else:
        err(f"Failed: {stderr}")


def cmd_wol_groups(args):
    """List host groups."""
    header("Host Groups")
    groups = opsi_jsonrpc(
        "group_getObjects", "'[]'", """'{"type":"HostGroup"}'""", timeout=30,
    )
    if not groups:
        warn("No groups found.")
        return

    if OPTS["json_mode"]:
        print(json.dumps(groups, indent=2))
        return

    for g in sorted(groups, key=lambda x: x.get("id", "")):
        gid = g.get("id", "")
        desc = g.get("description", "")
        line = f"  {C.BOLD}{gid}{C.RESET}"
        if desc:
            line += f"  {C.DIM}\u2014 {desc}{C.RESET}"
        print(line)
    print(f"\n  {C.DIM}{len(groups)} group(s){C.RESET}")


# ============================================================
# DIAGNOSTICS
# ============================================================

def cmd_diag_health(args):
    """Run opsi-cli support health-check."""
    header("OPSI Health Check")
    cli = detect_opsi_cli()
    if cli != "opsi-cli":
        die("opsi-cli required for health check (not available).")
    info("Running health check (may take a moment)...")
    stdout, stderr, rc = run(
        "TERM=dumb opsi-cli support health-check 2>&1", timeout=120,
    )
    if stdout:
        cleaned = re.sub(r"\[/?[a-z_ ]+\]", "", stdout)
        cleaned = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", cleaned)
        print(cleaned)
    if rc != 0 and stderr:
        warn(stderr)


def cmd_diag_services(args):
    """Check systemd service status."""
    header("Service Status")
    for svc in SERVICES:
        stdout, _, rc = run(f"systemctl is-active {svc} 2>/dev/null")
        status = stdout.strip() if stdout else "not found"
        if status == "active":
            ok(svc)
        elif status == "inactive":
            warn(f"{svc} (inactive)")
        else:
            err(f"{svc} ({status})")


def cmd_diag_quick(args):
    """Quick server diagnostics."""
    header("Quick Diagnostics")

    # Disk
    stdout, _, rc = run("df /var/lib/opsi --output=pcent 2>/dev/null | tail -1")
    if rc == 0 and stdout:
        pct_str = stdout.strip().replace("%", "")
        try:
            pct = int(pct_str)
            msg = f"Disk /var/lib/opsi: {pct}% used"
            (err if pct >= 90 else warn if pct >= 75 else ok)(msg)
        except ValueError:
            info(f"Disk /var/lib/opsi: {stdout.strip()}")
    else:
        warn("Disk info unavailable")

    # Certificate
    stdout, _, rc = run(
        "openssl s_client -connect localhost:4447 </dev/null 2>/dev/null | "
        "openssl x509 -noout -enddate 2>/dev/null",
    )
    if rc == 0 and stdout:
        match = re.search(r"notAfter=(.+)", stdout)
        if match:
            ok(f"Certificate expires: {match.group(1).strip()}")
        else:
            ok(f"Certificate: {stdout}")
    else:
        warn("Certificate check failed")

    # NTP
    stdout, _, rc = run(
        "timedatectl show --property=NTPSynchronized --value 2>/dev/null",
    )
    if stdout and stdout.strip().lower() == "yes":
        ok("NTP synchronized")
    elif stdout:
        warn(f"NTP: {stdout.strip()}")
    else:
        stdout2, _, _ = run("timedatectl status 2>/dev/null | grep -i ntp")
        if stdout2:
            info(f"NTP: {stdout2.strip()}")
        else:
            warn("NTP status unknown")

    # OPSI version
    stdout, _, _ = run(
        "opsi-cli --version 2>/dev/null || opsiconfd --version 2>/dev/null",
    )
    if stdout:
        ok(f"OPSI version: {stdout.splitlines()[0]}")
    else:
        warn("OPSI version unknown")

    # paedML version
    stdout, _, rc = run("cat /etc/paedml-version 2>/dev/null")
    if rc == 0 and stdout:
        ok(f"paedML version: {stdout.strip()}")


def cmd_diag_client(args):
    """Show product status for a specific client."""
    client_id = args.client_id
    header(f"Client: {client_id}")

    # Last seen
    seen = opsi_jsonrpc(
        "host_getObjects",
        '\'["id","lastSeen"]\'',
        f"""'{{"id":"{client_id}"}}'""",
        timeout=30,
    )
    if seen and len(seen) > 0:
        info(f"Last seen: {seen[0].get('lastSeen', 'never')}")

    # Products
    products = opsi_jsonrpc(
        "productOnClient_getObjects",
        '\'["productId","installationStatus","actionResult","actionRequest"]\'',
        f"""'{{"clientId":"{client_id}"}}'""",
        timeout=30,
    )
    if not products:
        warn("No product data found.")
        return

    if OPTS["json_mode"]:
        print(json.dumps(products, indent=2))
        return

    rows = []
    for p in sorted(products, key=lambda x: x.get("productId", "")):
        pid = p.get("productId", "")
        status = p.get("installationStatus", "")
        result = p.get("actionResult", "")
        request = p.get("actionRequest", "")
        if result == "failed":
            result = f"{C.RED}{result}{C.RESET}"
        elif result == "successful":
            result = f"{C.GREEN}{result}{C.RESET}"
        rows.append((pid, status, result, request))

    table(rows, headers=("Product", "Status", "Result", "Request"))


def cmd_diag_failed(args):
    """List all failed installations across all clients."""
    header("Failed Installations")
    with Spinner("Fetching failed deployments"):
        failed = opsi_jsonrpc(
            "productOnClient_getObjects",
            '\'["clientId","productId"]\'',
            """'{"actionResult":"failed"}'""",
            timeout=60,
        )
    if not failed:
        ok("No failed installations.")
        return

    if OPTS["json_mode"]:
        print(json.dumps(failed, indent=2))
        return

    rows = []
    for item in sorted(
        failed, key=lambda x: (x.get("clientId", ""), x.get("productId", "")),
    ):
        rows.append((item.get("clientId", ""), item.get("productId", "")))
    table(rows, headers=("Client", "Product"))
    print(f"\n  {C.RED}{len(rows)} failure(s){C.RESET}")


def cmd_diag_logs(args):
    """View recent logs for a client."""
    client_id = args.client_id
    header(f"Logs: {client_id}")
    cmd = (
        "for dir in /var/log/opsi/instlog /var/log/opsi/clientconnect "
        "/var/log/opsi/bootimage; do "
        f"for f in $(ls -t $dir/{client_id}* 2>/dev/null | head -1); do "
        "echo '=== '$f' ==='; tail -80 \"$f\"; echo; "
        "done; done"
    )
    stdout, _, _ = run(cmd, timeout=30)
    if stdout:
        print(stdout)
    else:
        warn(f"No logs found for {client_id}")


def cmd_diag_paedml(args):
    """paedML 10-point diagnostic check."""
    header("paedML Diagnostics")

    def _pct_ok(output):
        return int(output.strip().replace("%", "")) < 90

    checks = [
        (
            "NTP Sync",
            "timedatectl show --property=NTPSynchronized --value 2>&1",
            lambda o: o.strip().lower() == "yes",
        ),
        ("Disk /var", "df /var --output=pcent 2>&1 | tail -1", _pct_ok),
        ("Disk /srv", "df /srv --output=pcent 2>&1 | tail -1", _pct_ok),
        (
            "Certificate",
            "openssl s_client -connect localhost:4447 </dev/null 2>/dev/null "
            "| openssl x509 -checkend 2592000 -noout 2>&1",
            None,  # rc == 0 means valid > 30 days
        ),
        (
            "DNS Forward",
            "dig @localhost $(hostname -d 2>/dev/null || echo localhost) "
            "SOA +short",
            lambda o: bool(o.strip()),
        ),
        (
            "DNS Reverse",
            "dig @localhost -x $(hostname -I 2>/dev/null | awk "
            "'{print $1}') +short",
            lambda o: bool(o.strip()),
        ),
        (
            "DHCP Config",
            "dhcpd -t -cf /etc/dhcp/dhcpd.conf 2>&1 | tail -3",
            None,
        ),
        (
            "Samba AD",
            "samba-tool domain level show 2>&1 | head -5",
            lambda o: bool(o.strip()),
        ),
        (
            "Domain Join",
            "net ads testjoin 2>&1",
            lambda o: "ok" in o.lower() or "join is ok" in o.lower(),
        ),
        ("Sophomorix", "sophomorix-check 2>&1", None),
    ]

    for name, cmd, check_fn in checks:
        stdout, stderr, rc = run(cmd, timeout=30)
        output = stdout or stderr

        if check_fn:
            try:
                passed = check_fn(output) and rc == 0
            except (ValueError, TypeError):
                passed = False
        else:
            passed = rc == 0

        detail = ""
        if output.strip():
            first_line = output.strip().splitlines()[0]
            if len(first_line) > 80:
                first_line = first_line[:77] + "..."
            detail = f" {C.DIM}{first_line}{C.RESET}"

        if passed:
            ok(f"{name:<20}{detail}")
        else:
            err(f"{name:<20}{detail}")


# ============================================================
# SELF-UPDATE
# ============================================================

def cmd_self_update(args):
    """Download the latest version from GitHub and replace this script."""
    import urllib.request as urlreq

    header("Self-Update")
    info("Checking for updates...")

    try:
        req = urlreq.Request(GITHUB_RAW, headers={"User-Agent": "packforge"})
        resp = urlreq.urlopen(req, timeout=15)
        new_content = resp.read().decode("utf-8")
    except Exception as exc:
        die(f"Update check failed: {exc}")

    match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', new_content)
    if not match:
        die("Could not parse version from remote file.")

    remote_version = match.group(1)
    if remote_version == VERSION:
        ok(f"Already up to date (v{VERSION})")
        return

    info(f"Update available: v{VERSION} \u2192 v{remote_version}")
    if not confirm("Install update?"):
        return

    script_path = os.path.realpath(__file__)
    try:
        with open(script_path, "w") as fh:
            fh.write(new_content)
        os.chmod(script_path, 0o755)
        ok(f"Updated to v{remote_version}")
    except PermissionError:
        die(f"Cannot write to {script_path}. Run as root.")
    except Exception as exc:
        die(f"Update failed: {exc}")


def cmd_self_install(args):
    """Copy this script to /usr/local/bin/packforge."""
    dest = "/usr/local/bin/packforge"
    header("Self-Install")
    info(f"Installing to {dest}...")

    try:
        src = os.path.realpath(__file__)
        shutil.copy2(src, dest)
        os.chmod(dest, 0o755)
        ok(f"Installed to {dest}")
        info("Run 'packforge' from anywhere.")
    except PermissionError:
        die(f"Cannot write to {dest}. Run as root.")
    except Exception as exc:
        die(f"Install failed: {exc}")


# ============================================================
# ARGUMENT PARSER
# ============================================================

def build_parser():
    parser = argparse.ArgumentParser(
        prog="packforge",
        description="OPSI PackForge CLI \u2014 on-server OPSI administration tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              packforge                     Show dashboard
              packforge pkg list            List installed packages
              packforge pkg create -w       Interactive package wizard
              packforge wol wake --all      Wake all clients
              packforge diag paedml         Run paedML checks
              packforge self-update         Update to latest version
        """),
    )
    parser.add_argument(
        "--version", action="version", version=f"packforge v{VERSION}",
    )
    parser.add_argument(
        "--no-color", action="store_true", help="disable colored output",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_mode", help="JSON output",
    )
    parser.add_argument(
        "-y", "--yes", action="store_true", help="skip confirmations",
    )

    sub = parser.add_subparsers(dest="command")

    # Dashboard
    sub.add_parser("dashboard", aliases=["dash", "status"], help="server overview")

    # --- pkg ---
    pkg = sub.add_parser("pkg", help="package management")
    pkg_sub = pkg.add_subparsers(dest="pkg_cmd")

    pkg_sub.add_parser("list", aliases=["ls"], help="list packages")

    p = pkg_sub.add_parser("create", aliases=["build"], help="create/build package")
    p.add_argument("path", nargs="?", help="package directory in workbench")
    p.add_argument("-w", "--wizard", action="store_true", help="interactive wizard")
    p.add_argument(
        "-k", "--keep-versions", action="store_true", help="keep existing version",
    )
    p.add_argument("--version", dest="version", help="product version")
    p.add_argument("--release", help="package release number")

    p = pkg_sub.add_parser("install", aliases=["deploy"], help="install .opsi file")
    p.add_argument("file", help="path to .opsi file")
    p.add_argument(
        "-S", "--setup-where-installed", action="store_true",
        help="set setup on clients that have it installed",
    )
    p.add_argument(
        "-U", "--update-where-installed", action="store_true",
        help="set update action on installed clients",
    )

    p = pkg_sub.add_parser("remove", aliases=["rm", "uninstall"], help="remove package")
    p.add_argument("product_id", nargs="?", help="product ID")
    p.add_argument(
        "--depots-all", action="store_true", help="remove from all depots",
    )

    # --- wol ---
    wol = sub.add_parser("wol", help="wake on LAN / power control")
    wol_sub = wol.add_subparsers(dest="wol_cmd")

    wol_sub.add_parser("list", aliases=["ls"], help="list clients with status")

    p = wol_sub.add_parser("wake", help="wake clients")
    p.add_argument("clients", nargs="*", help="client IDs")
    p.add_argument("-a", "--all", action="store_true", help="wake all clients")
    p.add_argument("-g", "--group", help="wake by group name")

    p = wol_sub.add_parser("reboot", help="reboot clients")
    p.add_argument("clients", nargs="+", help="client IDs")

    p = wol_sub.add_parser("shutdown", help="shut down clients")
    p.add_argument("clients", nargs="+", help="client IDs")

    wol_sub.add_parser("groups", help="list host groups")

    # --- diag ---
    diag = sub.add_parser("diag", help="diagnostics")
    diag_sub = diag.add_subparsers(dest="diag_cmd")

    diag_sub.add_parser("health", aliases=["hc"], help="OPSI health check")
    diag_sub.add_parser("services", aliases=["svc"], help="service status")
    diag_sub.add_parser("quick", aliases=["q"], help="quick checks")

    p = diag_sub.add_parser("client", help="client product status")
    p.add_argument("client_id", help="client ID")

    diag_sub.add_parser("failed", help="failed installations")

    p = diag_sub.add_parser("logs", help="view client logs")
    p.add_argument("client_id", help="client ID")

    diag_sub.add_parser("paedml", help="paedML checks")

    # --- self-update / self-install ---
    sub.add_parser("self-update", aliases=["update"], help="update from GitHub")
    sub.add_parser("self-install", help="install to /usr/local/bin/packforge")

    return parser


# ============================================================
# DISPATCH
# ============================================================

DISPATCH = {
    "dashboard": cmd_dashboard,
    "dash": cmd_dashboard,
    "status": cmd_dashboard,
    "self-update": cmd_self_update,
    "update": cmd_self_update,
    "self-install": cmd_self_install,
}

PKG_DISPATCH = {
    "list": cmd_pkg_list,
    "ls": cmd_pkg_list,
    "create": cmd_pkg_create,
    "build": cmd_pkg_create,
    "install": cmd_pkg_install,
    "deploy": cmd_pkg_install,
    "remove": cmd_pkg_remove,
    "rm": cmd_pkg_remove,
    "uninstall": cmd_pkg_remove,
}

WOL_DISPATCH = {
    "list": cmd_wol_list,
    "ls": cmd_wol_list,
    "wake": cmd_wol_wake,
    "reboot": cmd_wol_reboot,
    "shutdown": cmd_wol_shutdown,
    "groups": cmd_wol_groups,
}

DIAG_DISPATCH = {
    "health": cmd_diag_health,
    "hc": cmd_diag_health,
    "services": cmd_diag_services,
    "svc": cmd_diag_services,
    "quick": cmd_diag_quick,
    "q": cmd_diag_quick,
    "client": cmd_diag_client,
    "failed": cmd_diag_failed,
    "logs": cmd_diag_logs,
    "paedml": cmd_diag_paedml,
}


# ============================================================
# MAIN
# ============================================================

def main():
    if sys.version_info < (3, 6):
        sys.exit(
            "packforge requires Python 3.6+. "
            "You have {}.{}.{}".format(*sys.version_info[:3])
        )

    parser = build_parser()
    args = parser.parse_args()

    # Apply global flags
    OPTS["no_color"] = args.no_color
    OPTS["json_mode"] = args.json_mode
    OPTS["yes"] = args.yes

    if args.no_color or not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        C.disable()

    # Root warning (Linux only)
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        warn("Not running as root. Some commands may fail.\n")

    cmd = args.command

    # Default: dashboard
    if cmd is None:
        cmd_dashboard(args)
        return

    # Sub-command groups
    if cmd == "pkg":
        handler = PKG_DISPATCH.get(getattr(args, "pkg_cmd", None))
        if handler:
            handler(args)
        else:
            parser.parse_args(["pkg", "--help"])
        return

    if cmd == "wol":
        handler = WOL_DISPATCH.get(getattr(args, "wol_cmd", None))
        if handler:
            handler(args)
        else:
            parser.parse_args(["wol", "--help"])
        return

    if cmd == "diag":
        handler = DIAG_DISPATCH.get(getattr(args, "diag_cmd", None))
        if handler:
            handler(args)
        else:
            parser.parse_args(["diag", "--help"])
        return

    # Top-level commands
    handler = DISPATCH.get(cmd)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Aborted.")
        sys.exit(130)
