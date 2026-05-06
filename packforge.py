#!/usr/bin/env python3
"""OPSI PackForge CLI v4.0.0 -- On-server OPSI administration tool.

Run directly on an OPSI server. No external dependencies required.
Python 3.5+ compatible.
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

# Symbols — ASCII fallbacks for non-UTF-8 terminals
def _can_utf8():
    try:
        "\u2713".encode(sys.stdout.encoding or "ascii")
        return True
    except (UnicodeEncodeError, LookupError):
        return False

class S:
    """Display symbols. Swapped to ASCII if terminal can't do UTF-8."""
    CHECK = "+"
    CROSS = "x"
    BULLET = "*"
    HLINE = "-"
    DASH = "--"
    ARROW = "->"
    SPINNER = "|/-\\"

    @classmethod
    def use_utf8(cls):
        cls.CHECK = "\u2713"
        cls.CROSS = "\u2717"
        cls.BULLET = "\u2022"
        cls.HLINE = "\u2500"
        cls.DASH = "\u2014"
        cls.ARROW = "\u2192"
        cls.SPINNER = "\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f"


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
    print("  {}{}{} {}".format(C.GREEN, S.CHECK, C.RESET, msg))


def err(msg):
    print("  {}{}{} {}".format(C.RED, S.CROSS, C.RESET, msg))


def warn(msg):
    print("  {}!{} {}".format(C.YELLOW, C.RESET, msg))


def info(msg):
    print("  {}{}{} {}".format(C.BLUE, S.BULLET, C.RESET, msg))


def header(title):
    print("\n{}{}  {}{}".format(C.BOLD, C.CYAN, title, C.RESET))
    print("  {}".format(S.HLINE * len(title)))


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
            print(prefix + S.HLINE * total)


def confirm(msg):
    """Ask yes/no. Returns True if --yes or user answers y."""
    if OPTS["yes"]:
        return True
    try:
        answer = input("  {} [y/N] ".format(msg)).strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


# ============================================================
# SPINNER
# ============================================================

class Spinner:
    """Simple braille spinner for long-running commands."""

    CHARS = "|/-\\"  # overridden to braille if UTF-8

    def __init__(self, msg):
        self.msg = msg
        self.running = False
        self.thread = None

    def __enter__(self):
        if sys.stdout.isatty() and not OPTS["no_color"]:
            self.running = True
            self.thread = threading.Thread(target=self._spin)
            self.thread.daemon = True
            self.thread.start()
        else:
            print("  {}...".format(self.msg))
        return self

    def __exit__(self, *_):
        self.running = False
        if self.thread:
            self.thread.join()
            blanks = " " * (len(self.msg) + 4)
            print("\r  {}\r".format(blanks), end="", flush=True)

    def _spin(self):
        i = 0
        while self.running:
            ch = S.SPINNER[i % len(S.SPINNER)]
            sys.stdout.write(
                "\r  {}{}{} {}".format(C.BLUE, ch, C.RESET, self.msg)
            )
            sys.stdout.flush()
            i += 1
            time.sleep(0.08)


# ============================================================
# COMMAND RUNNER
# ============================================================

def run(cmd, timeout=30, check=False):
    """Run a local shell command. Returns (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=timeout,
        )
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if check and result.returncode != 0:
            die("Command failed: {}\n    {}".format(cmd, stderr))
        return stdout, stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timed out after {}s".format(timeout), -1
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
            "opsi-cli --output-format json jsonrpc execute "
            "{} {} {}".format(method, params, filter_arg)
        )
    elif cli == "opsi-admin":
        cmd = "opsi-admin -d method {} {} {}".format(method, params, filter_arg)
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
        print("  {}{:3d}{}  {}".format(C.DIM, i, C.RESET, label))
    print()
    try:
        choice = input("  {} [1-{}, q]: ".format(prompt, len(items))).strip()
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
        print("  {}{:3d}{}  {}".format(C.DIM, i, C.RESET, label))
    print()
    try:
        choice = input("  {} [numbers/ranges, 'all', q]: ".format(prompt)).strip()
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
        ok("opsiconfd {}active{}".format(C.GREEN, C.RESET))
    else:
        err("opsiconfd {}{}{}".format(C.RED, stdout or "inactive", C.RESET))

    # Package count
    stdout, _, rc = run("opsi-package-manager -l 2>/dev/null | wc -l")
    pkg_count = stdout.strip() if rc == 0 else "?"
    info("Packages installed: {}{}{}".format(C.BOLD, pkg_count, C.RESET))

    # Client count
    clients = opsi_jsonrpc(
        "host_getObjects", "'[]'", """'{"type":"OpsiClient"}'""",
    )
    client_count = len(clients) if clients else "?"
    info("Clients registered: {}{}{}".format(C.BOLD, client_count, C.RESET))

    # Disk space
    stdout, _, rc = run(
        "df /var/lib/opsi --output=pcent,avail 2>/dev/null | tail -1",
    )
    if rc == 0 and stdout:
        parts = stdout.split()
        pct = parts[0] if parts else "?"
        avail = parts[1] if len(parts) > 1 else "?"
        info("Disk: {}{}{} used, {} available".format(C.BOLD, pct, C.RESET, avail))
    else:
        warn("Disk info unavailable")

    # Failed deployments
    failed = opsi_jsonrpc(
        "productOnClient_getObjects", "'[]'", """'{"actionResult":"failed"}'""",
    )
    fail_count = len(failed) if failed else 0
    if fail_count > 0:
        warn("Failed deployments: {}{}{}{}".format(
            C.RED, C.BOLD, fail_count, C.RESET,
        ))
    else:
        ok("Failed deployments: {}0{}".format(C.GREEN, C.RESET))

    # Services
    print()
    header("Services")
    for svc in SERVICES:
        stdout, _, rc = run("systemctl is-active {} 2>/dev/null".format(svc))
        if rc == 0 and stdout == "active":
            ok(svc)
        else:
            status = stdout if stdout else "not found"
            if status == "inactive":
                warn("{} ({})".format(svc, status))
            else:
                err("{} ({})".format(svc, status))


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
        print("  {}".format(line))
    print("\n  {}{}  package(s){}".format(C.DIM, len(lines), C.RESET))


def cmd_pkg_create(args):
    """Create / build an OPSI package."""
    if getattr(args, "wizard", False):
        _pkg_wizard()
        return

    path = getattr(args, "path", None)
    if not path:
        header("Workbench Packages")
        if not os.path.isdir(WORKBENCH):
            die("Workbench not found: {}".format(WORKBENCH))
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
        die("Directory not found: {}".format(path))
    if not os.path.isdir(os.path.join(path, "OPSI")):
        die("Not a valid OPSI package (no OPSI/ folder): {}".format(path))

    pkg_name = os.path.basename(os.path.normpath(path))

    if getattr(args, "keep_versions", False):
        build_cmd = "cd '{}' && opsi-makepackage --keep-versions".format(path)
    elif getattr(args, "version", None):
        build_cmd = "cd '{}' && opsi-makepackage --product-version {}".format(
            path, args.version,
        )
        if getattr(args, "release", None):
            build_cmd += " --package-version {}".format(args.release)
    else:
        build_cmd = "cd '{}' && opsi-makepackage".format(path)

    info("Building {}{}{}...".format(C.BOLD, pkg_name, C.RESET))
    with Spinner("Running opsi-makepackage"):
        stdout, stderr, rc = run(build_cmd, timeout=300)

    if rc != 0:
        err("Build failed:\n    {}".format(stderr))
        if stdout:
            print("    {}".format(stdout))
        return

    ok("Package built: {}".format(pkg_name))
    for line in (stdout or "").splitlines():
        if ".opsi" in line:
            print("  {}{}{}".format(C.DIM, line.strip(), C.RESET))

    if confirm("Install {} to depot?".format(pkg_name)):
        opsi_file, _, _ = run(
            "ls -t '{}'/{}_*.opsi 2>/dev/null | head -1".format(WORKBENCH, pkg_name),
        )
        if not opsi_file:
            opsi_file, _, _ = run(
                "ls -t '{}'/{}_*.opsi 2>/dev/null | head -1".format(path, pkg_name),
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
        name = input("  Product Name [{}]: ".format(pkg_id)).strip() or pkg_id
        description = input("  Description: ").strip()

        print("\n  Installer types: msi, inno, nsis, exe, ps1, bat")
        inst_type = input("  Installer type [exe]: ").strip().lower() or "exe"
        if inst_type not in silent_defaults:
            warn("Unknown type '{}', defaulting to exe.".format(inst_type))
            inst_type = "exe"

        default_params = silent_defaults[inst_type]
        silent = input("  Silent parameters [{}]: ".format(default_params)).strip()
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
        if not confirm("Directory {} exists. Overwrite scripts?".format(pkg_dir)):
            return

    os.makedirs(opsi_dir, exist_ok=True)
    os.makedirs(files_dir, exist_ok=True)

    # control file
    control = textwrap.dedent("""\
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
    """).format(pkg_id=pkg_id, name=name, description=description, version=version)
    with open(os.path.join(opsi_dir, "control"), "w") as fh:
        fh.write(control)

    # setup script
    if inst_type == "msi":
        install_block = (
            "Winbatch_install\n\n"
            "[Winbatch_install]\n"
            'msiexec /i "%ScriptPath%\\files\\*.msi" {}'.format(silent)
        )
    elif inst_type in ("inno", "nsis", "exe"):
        install_block = (
            "Winbatch_install\n\n"
            "[Winbatch_install]\n"
            '"%ScriptPath%\\files\\*.exe" {}'.format(silent)
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

    setup_script = textwrap.dedent("""\
        [Actions]
        requiredWinstVersion >= "4.12"
        ScriptErrorMessages = false

        DefVar $ProductId$
        Set $ProductId$ = "{pkg_id}"

        Message "Installing " + $ProductId$ + " ..."

        {install_block}
    """).format(pkg_id=pkg_id, install_block=install_block)
    with open(os.path.join(client_dir, "setup.opsiscript"), "w") as fh:
        fh.write(setup_script)

    # uninstall script
    uninstall_script = textwrap.dedent("""\
        [Actions]
        requiredWinstVersion >= "4.12"
        ScriptErrorMessages = false

        DefVar $ProductId$
        Set $ProductId$ = "{pkg_id}"

        Message "Uninstalling " + $ProductId$ + " ..."

        comment "TODO: Add uninstall command"
    """).format(pkg_id=pkg_id)
    with open(os.path.join(client_dir, "uninstall.opsiscript"), "w") as fh:
        fh.write(uninstall_script)

    ok("Package created at {}".format(pkg_dir))
    info("Place installer files in: {}/".format(files_dir))
    print()

    if confirm("Build package now?"):
        with Spinner("Running opsi-makepackage"):
            stdout, stderr, rc = run(
                "cd '{}' && opsi-makepackage --keep-versions {}".format(
                    WORKBENCH, pkg_id,
                ),
                timeout=300,
            )
        if rc == 0:
            ok("Package built successfully.")
        else:
            err("Build failed: {}".format(stderr))


def cmd_pkg_install(args):
    """Install a .opsi package to the depot."""
    setup = getattr(args, "setup_where_installed", False)
    update = getattr(args, "update_where_installed", False)
    _pkg_install_file(args.file, setup=setup, update=update)


def _pkg_install_file(filepath, setup=False, update=False):
    """Install an .opsi file."""
    if not os.path.isfile(filepath):
        die("File not found: {}".format(filepath))

    cli = detect_opsi_cli()
    if cli == "opsi-cli":
        cmd = "TERM=dumb opsi-cli package install"
        if setup:
            cmd += " --setup-where-installed"
        elif update:
            cmd += " --update-where-installed"
        cmd += " '{}'".format(filepath)
    else:
        cmd = "opsi-package-manager -i"
        if setup:
            cmd += " -S"
        elif update:
            cmd += " -U"
        cmd += " '{}'".format(filepath)

    info("Installing {}{}{}...".format(C.BOLD, os.path.basename(filepath), C.RESET))
    with Spinner("Installing package"):
        stdout, stderr, rc = run(cmd, timeout=600)

    if rc == 0:
        ok("Package installed.")
        if stdout:
            for line in stdout.splitlines()[-3:]:
                print("  {}{}{}".format(C.DIM, line, C.RESET))
    else:
        err("Install failed: {}".format(stderr))


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
    if not confirm("Remove {}{}{}?".format(C.BOLD, product_id, C.RESET)):
        return

    cli = detect_opsi_cli()
    if cli == "opsi-cli":
        cmd = "opsi-cli package uninstall"
        if depots_all:
            cmd += " --depots all"
        cmd += " " + product_id
    else:
        cmd = "opsi-package-manager -r"
        if depots_all:
            cmd += " --depots '*'"
        cmd += " " + product_id

    with Spinner("Removing {}".format(product_id)):
        _, stderr, rc = run(cmd, timeout=120)

    if rc == 0:
        ok("Removed {}".format(product_id))
    else:
        err("Failed to remove {}: {}".format(product_id, stderr))


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
        if c["online"]:
            status = "{}Online{}".format(C.GREEN, C.RESET)
        else:
            status = "{}Offline{}".format(C.DIM, C.RESET)
        rows.append((c["id"], c["ip"] or "-", c["mac"] or "-", status))

    table(rows, headers=("Client ID", "IP", "MAC", "Status"))
    print("\n  {}{}/{} online{}".format(C.DIM, online, len(clients), C.RESET))


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
            err("Failed: {}".format(stderr))
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
        display=lambda c: "{:<40} {:<15} {}".format(
            c["id"], c["ip"] or "-", c["mac"] or "-",
        ),
    )
    if selected:
        _wol_send([c["id"] for c in selected])


def _wol_group(group_name):
    """Wake all clients in a host group."""
    members = opsi_jsonrpc(
        "objectToGroup_getObjects", "'[]'",
        """'{{"groupType":"HostGroup","groupId":"{}"}}'""".format(group_name),
        timeout=30,
    )
    if not members:
        die("No members found in group '{}'.".format(group_name))
    ids = [m.get("objectId", "") for m in members if m.get("objectId")]
    if not ids:
        die("No client IDs in group '{}'.".format(group_name))
    info("Waking {} client(s) in group '{}'...".format(len(ids), group_name))
    _wol_send(ids)


def _wol_send(client_ids):
    """Send WoL signal to specific clients."""
    ids_json = json.dumps(client_ids)
    cli = detect_opsi_cli()
    if cli == "opsi-cli":
        cmd = "opsi-cli jsonrpc execute hostControlSafe_start '{}'".format(ids_json)
    else:
        cmd = "opsi-admin -d method hostControlSafe_start '{}'".format(ids_json)
    _, stderr, rc = run(cmd, timeout=30)
    if rc == 0:
        ok("Wake signal sent to {} client(s).".format(len(client_ids)))
    else:
        err("Failed: {}".format(stderr))


def cmd_wol_reboot(args):
    """Reboot selected clients."""
    if not args.clients:
        die("Specify client ID(s) to reboot.")
    if not confirm("Reboot {} client(s)?".format(len(args.clients))):
        return
    ids_json = json.dumps(args.clients)
    cli = detect_opsi_cli()
    if cli == "opsi-cli":
        cmd = "opsi-cli jsonrpc execute hostControlSafe_reboot '{}'".format(ids_json)
    else:
        cmd = "opsi-admin -d method hostControlSafe_reboot '{}'".format(ids_json)
    _, stderr, rc = run(cmd, timeout=30)
    if rc == 0:
        ok("Reboot signal sent.")
    else:
        err("Failed: {}".format(stderr))


def cmd_wol_shutdown(args):
    """Shut down selected clients."""
    if not args.clients:
        die("Specify client ID(s) to shut down.")
    if not confirm("Shut down {} client(s)?".format(len(args.clients))):
        return
    ids_json = json.dumps(args.clients)
    cli = detect_opsi_cli()
    if cli == "opsi-cli":
        cmd = "opsi-cli jsonrpc execute hostControlSafe_shutdown '{}'".format(ids_json)
    else:
        cmd = "opsi-admin -d method hostControlSafe_shutdown '{}'".format(ids_json)
    _, stderr, rc = run(cmd, timeout=30)
    if rc == 0:
        ok("Shutdown signal sent.")
    else:
        err("Failed: {}".format(stderr))


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
        line = "  {}{}{}".format(C.BOLD, gid, C.RESET)
        if desc:
            line += "  {}{} {}{}".format(C.DIM, S.DASH, desc, C.RESET)
        print(line)
    print("\n  {}{} group(s){}".format(C.DIM, len(groups), C.RESET))


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
        stdout, _, rc = run("systemctl is-active {} 2>/dev/null".format(svc))
        status = stdout.strip() if stdout else "not found"
        if status == "active":
            ok(svc)
        elif status == "inactive":
            warn("{} (inactive)".format(svc))
        else:
            err("{} ({})".format(svc, status))


def cmd_diag_quick(args):
    """Quick server diagnostics."""
    header("Quick Diagnostics")

    # Disk
    stdout, _, rc = run("df /var/lib/opsi --output=pcent 2>/dev/null | tail -1")
    if rc == 0 and stdout:
        pct_str = stdout.strip().replace("%", "")
        try:
            pct = int(pct_str)
            msg = "Disk /var/lib/opsi: {}% used".format(pct)
            (err if pct >= 90 else warn if pct >= 75 else ok)(msg)
        except ValueError:
            info("Disk /var/lib/opsi: {}".format(stdout.strip()))
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
            ok("Certificate expires: {}".format(match.group(1).strip()))
        else:
            ok("Certificate: {}".format(stdout))
    else:
        warn("Certificate check failed")

    # NTP
    stdout, _, rc = run(
        "timedatectl show --property=NTPSynchronized --value 2>/dev/null",
    )
    if stdout and stdout.strip().lower() == "yes":
        ok("NTP synchronized")
    elif stdout:
        warn("NTP: {}".format(stdout.strip()))
    else:
        stdout2, _, _ = run("timedatectl status 2>/dev/null | grep -i ntp")
        if stdout2:
            info("NTP: {}".format(stdout2.strip()))
        else:
            warn("NTP status unknown")

    # OPSI version
    stdout, _, _ = run(
        "opsi-cli --version 2>/dev/null || opsiconfd --version 2>/dev/null",
    )
    if stdout:
        ok("OPSI version: {}".format(stdout.splitlines()[0]))
    else:
        warn("OPSI version unknown")

    # paedML version
    stdout, _, rc = run("cat /etc/paedml-version 2>/dev/null")
    if rc == 0 and stdout:
        ok("paedML version: {}".format(stdout.strip()))


def cmd_diag_client(args):
    """Show product status for a specific client."""
    client_id = args.client_id
    header("Client: {}".format(client_id))

    # Last seen
    seen = opsi_jsonrpc(
        "host_getObjects",
        '\'["id","lastSeen"]\'',
        """'{{"id":"{}"}}'""".format(client_id),
        timeout=30,
    )
    if seen and len(seen) > 0:
        info("Last seen: {}".format(seen[0].get("lastSeen", "never")))

    # Products
    products = opsi_jsonrpc(
        "productOnClient_getObjects",
        '\'["productId","installationStatus","actionResult","actionRequest"]\'',
        """'{{"clientId":"{}"}}'""".format(client_id),
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
            result = "{}{}{}".format(C.RED, result, C.RESET)
        elif result == "successful":
            result = "{}{}{}".format(C.GREEN, result, C.RESET)
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
    print("\n  {}{} failure(s){}".format(C.RED, len(rows), C.RESET))


def cmd_diag_logs(args):
    """View recent logs for a client."""
    client_id = args.client_id
    header("Logs: {}".format(client_id))
    cmd = (
        "for dir in /var/log/opsi/instlog /var/log/opsi/clientconnect "
        "/var/log/opsi/bootimage; do "
        "for f in $(ls -t $dir/{}* 2>/dev/null | head -1); do "
        "echo '=== '$f' ==='; tail -80 \"$f\"; echo; "
        "done; done".format(client_id)
    )
    stdout, _, _ = run(cmd, timeout=30)
    if stdout:
        print(stdout)
    else:
        warn("No logs found for {}".format(client_id))


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
            None,
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
            detail = " {}{}{}".format(C.DIM, first_line, C.RESET)

        if passed:
            ok("{:<20}{}".format(name, detail))
        else:
            err("{:<20}{}".format(name, detail))


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
        die("Update check failed: {}".format(exc))

    match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', new_content)
    if not match:
        die("Could not parse version from remote file.")

    remote_version = match.group(1)
    if remote_version == VERSION:
        ok("Already up to date (v{})".format(VERSION))
        return

    info("Update available: v{} {} v{}".format(VERSION, S.ARROW, remote_version))
    if not confirm("Install update?"):
        return

    script_path = os.path.realpath(__file__)
    try:
        with open(script_path, "w") as fh:
            fh.write(new_content)
        os.chmod(script_path, 0o755)
        ok("Updated to v{}".format(remote_version))
    except PermissionError:
        die("Cannot write to {}. Run as root.".format(script_path))
    except Exception as exc:
        die("Update failed: {}".format(exc))


def cmd_self_install(args):
    """Copy this script to /usr/local/bin/packforge."""
    dest = "/usr/local/bin/packforge"
    header("Self-Install")
    info("Installing to {}...".format(dest))

    try:
        src = os.path.realpath(__file__)
        shutil.copy2(src, dest)
        os.chmod(dest, 0o755)
        ok("Installed to {}".format(dest))
        info("Run 'packforge' from anywhere.")
    except PermissionError:
        die("Cannot write to {}. Run as root.".format(dest))
    except Exception as exc:
        die("Install failed: {}".format(exc))


# ============================================================
# ARGUMENT PARSER
# ============================================================

def build_parser():
    parser = argparse.ArgumentParser(
        prog="packforge",
        description="OPSI PackForge CLI -- on-server OPSI administration tool",
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
        "--version", action="version",
        version="packforge v{}".format(VERSION),
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

    p = pkg_sub.add_parser(
        "remove", aliases=["rm", "uninstall"], help="remove package",
    )
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
    parser = build_parser()
    args = parser.parse_args()

    # Apply global flags
    OPTS["no_color"] = args.no_color
    OPTS["json_mode"] = args.json_mode
    OPTS["yes"] = args.yes

    if args.no_color or not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        C.disable()

    if _can_utf8():
        S.use_utf8()

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
