#!/usr/bin/env python3
"""
OPSI Toolbox v3.0 - Modern Admin Suite
Full-featured OPSI administration with packaging, WOL, and diagnostics
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import zipfile
import shutil
import subprocess
import threading
import re
import socket
import json
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# MODERN THEME
# ══════════════════════════════════════════════════════════════════════════════
BG = "#0a0a0a"
BG_SECONDARY = "#111111"
SIDEBAR = "#0f0f0f"
CARD = "#161616"
CARD_HOVER = "#1c1c1c"
BORDER = "#222222"
ACCENT = "#3b82f6"
ACCENT_HOVER = "#2563eb"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
ERROR = "#ef4444"
TEXT = "#f5f5f5"
TEXT_SECONDARY = "#a3a3a3"
TEXT_MUTED = "#525252"

FONT = "Segoe UI"
FONT_MONO = "Consolas"


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOM WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

class ModernEntry(tk.Entry):
    def __init__(self, parent, placeholder="", **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        self.configure(
            bg=CARD, fg=TEXT, insertbackground=ACCENT,
            relief="flat", highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
            font=(FONT, 11)
        )
        self.bind("<FocusIn>", lambda _: self._focus_in())
        self.bind("<FocusOut>", lambda _: self._focus_out())
        if placeholder:
            self._show_placeholder()

    def _show_placeholder(self):
        self.delete(0, tk.END)
        self.insert(0, self.placeholder)
        self.configure(fg=TEXT_MUTED)

    def _focus_in(self):
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.configure(fg=TEXT)

    def _focus_out(self):
        if not self.get():
            self._show_placeholder()

    def get_value(self):
        v = self.get()
        return "" if v == self.placeholder else v


class ModernButton(tk.Canvas):
    def __init__(self, parent, text="", command=None, primary=False, width=120, height=36, **kwargs):
        super().__init__(parent, width=width, height=height,
                        bg=parent.cget('bg'), highlightthickness=0, **kwargs)
        self.command = command
        self.primary = primary
        self.text = text
        self.width = width
        self.height = height
        self.bg_normal = ACCENT if primary else CARD
        self.bg_hover = ACCENT_HOVER if primary else CARD_HOVER
        self.fg_color = "#ffffff" if primary else TEXT
        self._draw(self.bg_normal)
        self.bind("<Enter>", lambda _: self._draw(self.bg_hover))
        self.bind("<Leave>", lambda _: self._draw(self.bg_normal))
        self.bind("<Button-1>", lambda _: self._click())
        self.configure(cursor="hand2")

    def _draw(self, bg):
        self.delete("all")
        r = 6
        self.create_rounded_rect(2, 2, self.width-2, self.height-2, r, fill=bg, outline="")
        self.create_text(self.width//2, self.height//2, text=self.text,
                        fill=self.fg_color, font=(FONT, 10, "bold"))

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r, x1, y1+r, x1, y1, x1+r, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _click(self):
        if self.command:
            self.command()


class SidebarButton(tk.Frame):
    def __init__(self, parent, text="", icon="", command=None, **kwargs):
        super().__init__(parent, bg=SIDEBAR, cursor="hand2", **kwargs)
        self.command = command
        self.active = False
        self.indicator = tk.Frame(self, bg=SIDEBAR, width=3)
        self.indicator.pack(side="left", fill="y")
        content = tk.Frame(self, bg=SIDEBAR)
        content.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        if icon:
            tk.Label(content, text=icon, font=(FONT, 14),
                    bg=SIDEBAR, fg=TEXT_SECONDARY).pack(side="left")
        self.label = tk.Label(content, text=text, font=(FONT, 11),
                             bg=SIDEBAR, fg=TEXT_SECONDARY)
        self.label.pack(side="left", padx=(10 if icon else 0, 0))
        for widget in [self, content, self.label]:
            widget.bind("<Enter>", lambda _: self._hover())
            widget.bind("<Leave>", lambda _: self._leave())
            widget.bind("<Button-1>", lambda _: self._click())

    def _hover(self):
        if not self.active:
            self.configure(bg=CARD)
            for w in self.winfo_children():
                self._set_bg(w, CARD)

    def _leave(self):
        if not self.active:
            self.configure(bg=SIDEBAR)
            for w in self.winfo_children():
                self._set_bg(w, SIDEBAR)

    def _set_bg(self, widget, color):
        try:
            widget.configure(bg=color)
            for child in widget.winfo_children():
                self._set_bg(child, color)
        except:
            pass

    def _click(self):
        if self.command:
            self.command()

    def set_active(self, active):
        self.active = active
        if active:
            self.indicator.configure(bg=ACCENT)
            self.label.configure(fg=TEXT)
            self._set_bg(self, CARD)
        else:
            self.indicator.configure(bg=SIDEBAR)
            self.label.configure(fg=TEXT_SECONDARY)
            self._set_bg(self, SIDEBAR)


class TabButton(tk.Canvas):
    """Simple tab button for sub-page navigation."""
    def __init__(self, parent, text="", command=None, width=120, height=32, **kwargs):
        super().__init__(parent, width=width, height=height,
                        bg=parent.cget('bg'), highlightthickness=0, **kwargs)
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.active = False
        self._draw()
        self.bind("<Button-1>", lambda _: self._click())
        self.bind("<Enter>", lambda _: self._draw(hover=True))
        self.bind("<Leave>", lambda _: self._draw())
        self.configure(cursor="hand2")

    def _draw(self, hover=False):
        self.delete("all")
        if self.active:
            self.create_rectangle(0, self.height-2, self.width, self.height, fill=ACCENT, outline="")
            self.create_text(self.width//2, self.height//2 - 1, text=self.text,
                            fill=TEXT, font=(FONT, 10, "bold"))
        else:
            if hover:
                self.create_rectangle(0, 0, self.width, self.height, fill=CARD_HOVER, outline="")
            self.create_text(self.width//2, self.height//2, text=self.text,
                            fill=TEXT_SECONDARY, font=(FONT, 10))

    def set_active(self, active):
        self.active = active
        self._draw()

    def _click(self):
        if self.command:
            self.command()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

class OPSIToolbox(tk.Tk):

    INSTALLER_TYPES = {
        "msi": {"name": "MSI", "params": "/qn /norestart"},
        "inno": {"name": "InnoSetup", "params": "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART"},
        "nsis": {"name": "NSIS", "params": "/S"},
        "exe": {"name": "EXE", "params": "/silent"},
        "ps1": {"name": "PowerShell", "params": ""},
        "bat": {"name": "Batch", "params": ""},
    }

    def __init__(self):
        super().__init__()
        self.title("OPSI Toolbox")
        self.geometry("1200x800")
        self.configure(bg=BG)
        self.minsize(1000, 650)

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1200) // 2
        y = (self.winfo_screenheight() - 800) // 2
        self.geometry(f"1200x800+{x}+{y}")

        # Global state
        self.selected_files = []
        self.installer_type = tk.StringVar(value="exe")
        self.wol_clients = []
        self.wol_client_vars = {}
        self.wol_auto_refresh = False

        self._build_layout()
        self._show_page("dashboard")

    # ══════════════════════════════════════════════════════════════════════════
    # LAYOUT
    # ══════════════════════════════════════════════════════════════════════════

    def _build_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(self.sidebar, bg=SIDEBAR)
        logo_frame.pack(fill="x", pady=20, padx=16)
        tk.Label(logo_frame, text="OPSI", font=(FONT, 20, "bold"),
                bg=SIDEBAR, fg=ACCENT).pack(side="left")
        tk.Label(logo_frame, text="Toolbox", font=(FONT, 20),
                bg=SIDEBAR, fg=TEXT).pack(side="left", padx=(4, 0))

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=16)

        # Global server settings in sidebar
        settings_frame = tk.Frame(self.sidebar, bg=SIDEBAR)
        settings_frame.pack(fill="x", padx=16, pady=(16, 0))

        tk.Label(settings_frame, text="Server", font=(FONT, 9),
                bg=SIDEBAR, fg=TEXT_MUTED).pack(anchor="w")
        self.global_server = ModernEntry(settings_frame, placeholder="10.1.0.2", width=18)
        self.global_server.pack(fill="x", pady=(2, 8))

        tk.Label(settings_frame, text="SSH User", font=(FONT, 9),
                bg=SIDEBAR, fg=TEXT_MUTED).pack(anchor="w")
        self.global_user = ModernEntry(settings_frame, placeholder="root", width=18)
        self.global_user.pack(fill="x", pady=(2, 0))

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(16, 0))

        # Navigation
        nav = tk.Frame(self.sidebar, bg=SIDEBAR)
        nav.pack(fill="x", pady=12)

        self.nav_buttons = {}
        pages = [
            ("dashboard", "Dashboard", "◎"),
            ("packaging", "Packaging", "◫"),
            ("wakeonlan", "Wake on LAN", "⏻"),
            ("diagnostics", "Diagnostics", "⚙"),
        ]
        for key, text, icon in pages:
            btn = SidebarButton(nav, text=text, icon=icon,
                               command=lambda k=key: self._show_page(k))
            btn.pack(fill="x")
            self.nav_buttons[key] = btn

        tk.Label(self.sidebar, text="v3.0", font=(FONT, 9),
                bg=SIDEBAR, fg=TEXT_MUTED).pack(side="bottom", pady=16)

        # Main content
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="right", fill="both", expand=True)

        self.pages = {}
        self._create_dashboard()
        self._create_packaging()
        self._create_wakeonlan()
        self._create_diagnostics()

    def _show_page(self, page_name):
        for page in self.pages.values():
            page.pack_forget()
        for btn in self.nav_buttons.values():
            btn.set_active(False)
        self.pages[page_name].pack(fill="both", expand=True)
        self.nav_buttons[page_name].set_active(True)

    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _get_server(self):
        return self.global_server.get_value() or "10.1.0.2"

    def _get_user(self):
        return self.global_user.get_value() or "root"

    def _subprocess_kwargs(self):
        """Return extra kwargs to hide console windows on Windows."""
        kwargs = {}
        if os.name == "nt":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0  # SW_HIDE
            kwargs["startupinfo"] = si
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        return kwargs

    def _ssh_cmd(self, cmd, timeout=30):
        """Run a command on the OPSI server via SSH. Returns (stdout, stderr, returncode)."""
        server = self._get_server()
        user = self._get_user()
        try:
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
                 f"{user}@{server}", cmd],
                capture_output=True, text=True, timeout=timeout,
                **self._subprocess_kwargs()
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "", "Timeout", -1
        except Exception as e:
            return "", str(e), -1

    def _ssh_bg(self, cmd, callback, timeout=30):
        """Run SSH command in background thread, call callback(stdout, stderr, rc) on completion."""
        def run():
            out, err, rc = self._ssh_cmd(cmd, timeout)
            self.after(0, lambda: callback(out, err, rc))
        threading.Thread(target=run, daemon=True).start()

    def _create_card(self, parent, title, expand=False):
        card = tk.Frame(parent, bg=CARD)
        if expand:
            card.pack(fill="both", expand=True, pady=(0, 16))
        else:
            card.pack(fill="x", pady=(0, 16))
        tk.Label(card, text=title, font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))
        return card

    def _add_form_field(self, parent, label, attr, placeholder="", side=None, width=None):
        frame = tk.Frame(parent, bg=CARD)
        if side:
            frame.pack(side=side, padx=(0, 16))
        else:
            frame.pack(fill="x", pady=4)
        tk.Label(frame, text=label, font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w")
        entry = ModernEntry(frame, placeholder=placeholder, width=width or 30)
        entry.pack(anchor="w", pady=(4, 0))
        setattr(self, attr, entry)

    def _get_text(self, widget):
        if isinstance(widget, tk.Text):
            return widget.get("1.0", tk.END).strip()
        elif isinstance(widget, ModernEntry):
            return widget.get_value()
        return widget.get().strip()

    def _make_log_widget(self, parent):
        """Create a scrolled text log widget with standard tags."""
        log = scrolledtext.ScrolledText(parent, bg=BG_SECONDARY, fg=TEXT,
                                        font=(FONT_MONO, 9), relief="flat",
                                        highlightthickness=0)
        log.tag_config("ok", foreground=SUCCESS)
        log.tag_config("error", foreground=ERROR)
        log.tag_config("warn", foreground=WARNING)
        log.tag_config("info", foreground=ACCENT)
        return log

    def _log_to(self, widget, msg, tag=""):
        widget.insert(tk.END, msg + "\n", tag)
        widget.see(tk.END)
        self.update_idletasks()

    # ══════════════════════════════════════════════════════════════════════════
    # DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════

    def _create_dashboard(self):
        page = tk.Frame(self.content, bg=BG)
        self.pages["dashboard"] = page

        header = tk.Frame(page, bg=BG)
        header.pack(fill="x", padx=32, pady=(32, 24))
        tk.Label(header, text="Dashboard", font=(FONT, 24, "bold"),
                bg=BG, fg=TEXT).pack(side="left", anchor="w")
        ModernButton(header, text="Refresh", command=self._refresh_dashboard,
                    width=90, height=32).pack(side="right")

        # Stats grid
        self.dash_grid = tk.Frame(page, bg=BG)
        self.dash_grid.pack(fill="x", padx=32, pady=(0, 16))

        # Row 1: status cards
        row1 = tk.Frame(self.dash_grid, bg=BG)
        row1.pack(fill="x", pady=(0, 12))

        self.dash_cards = {}
        card_defs = [
            ("server", "Server Status", "--", ACCENT),
            ("packages", "Packages", "--", ACCENT),
            ("clients", "Clients Online", "--", ACCENT),
            ("disk", "Disk Space", "--", ACCENT),
            ("failed", "Failed Deploys", "--", ACCENT),
        ]
        for key, title, default, color in card_defs:
            card = tk.Frame(row1, bg=CARD, width=180, height=100)
            card.pack(side="left", fill="both", expand=True, padx=(0, 12))
            card.pack_propagate(False)

            inner = tk.Frame(card, bg=CARD)
            inner.pack(fill="both", expand=True, padx=16, pady=12)

            tk.Label(inner, text=title, font=(FONT, 9),
                    bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w")
            val_label = tk.Label(inner, text=default, font=(FONT, 20, "bold"),
                                bg=CARD, fg=TEXT)
            val_label.pack(anchor="w", pady=(4, 0))
            status_label = tk.Label(inner, text="", font=(FONT, 9),
                                   bg=CARD, fg=TEXT_MUTED)
            status_label.pack(anchor="w")

            self.dash_cards[key] = {"value": val_label, "status": status_label}

        # Quick actions row
        row2 = tk.Frame(self.dash_grid, bg=BG)
        row2.pack(fill="x", pady=(0, 12))

        actions_card = tk.Frame(row2, bg=CARD)
        actions_card.pack(fill="x")
        inner = tk.Frame(actions_card, bg=CARD)
        inner.pack(fill="x", padx=20, pady=16)

        tk.Label(inner, text="Quick Actions", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", pady=(0, 12))

        btn_row = tk.Frame(inner, bg=CARD)
        btn_row.pack(fill="x")

        ModernButton(btn_row, text="Health Check",
                    command=lambda: (self._show_page("diagnostics"), self._run_health_check()),
                    primary=True, width=130).pack(side="left", padx=(0, 8))
        ModernButton(btn_row, text="Packaging",
                    command=lambda: self._show_page("packaging"),
                    width=110).pack(side="left", padx=(0, 8))
        ModernButton(btn_row, text="Wake on LAN",
                    command=lambda: self._show_page("wakeonlan"),
                    width=110).pack(side="left", padx=(0, 8))
        ModernButton(btn_row, text="View Clients",
                    command=lambda: self._show_page("wakeonlan"),
                    width=110).pack(side="left")

        # Server log / recent activity
        log_card = self._create_card(page, "Server Info", expand=True)
        log_inner = tk.Frame(log_card, bg=CARD)
        log_inner.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.dash_log = self._make_log_widget(log_inner)
        self.dash_log.pack(fill="both", expand=True)

    def _refresh_dashboard(self):
        self.dash_log.delete("1.0", tk.END)
        self._log_to(self.dash_log, "Connecting to server...", "info")

        for key in self.dash_cards:
            self.dash_cards[key]["value"].configure(text="...", fg=TEXT_MUTED)
            self.dash_cards[key]["status"].configure(text="")

        # Server status
        def on_server(out, err, rc):
            if rc == 0 and "active" in out:
                self.dash_cards["server"]["value"].configure(text="Online", fg=SUCCESS)
                self.dash_cards["server"]["status"].configure(text="opsiconfd running")
                self._log_to(self.dash_log, "[OK] Server online, opsiconfd active", "ok")
            else:
                self.dash_cards["server"]["value"].configure(text="Offline", fg=ERROR)
                self.dash_cards["server"]["status"].configure(text=err[:40] if err else "unreachable")
                self._log_to(self.dash_log, f"[ERROR] Server: {err or 'unreachable'}", "error")
        self._ssh_bg("systemctl is-active opsiconfd", on_server)

        # Package count
        def on_packages(out, err, rc):
            if rc == 0:
                lines = [l for l in out.split("\n") if l.strip()]
                count = len(lines)
                self.dash_cards["packages"]["value"].configure(text=str(count), fg=TEXT)
                self.dash_cards["packages"]["status"].configure(text="installed on depot")
                self._log_to(self.dash_log, f"[OK] {count} packages on depot", "ok")
            else:
                self.dash_cards["packages"]["value"].configure(text="?", fg=WARNING)
                self._log_to(self.dash_log, f"[WARN] Could not list packages", "warn")
        self._ssh_bg("opsi-package-manager -l 2>/dev/null", on_packages)

        # Clients online
        def on_clients(out, err, rc):
            if rc == 0 and out:
                try:
                    data = json.loads(out)
                    total = len(data)
                    online = sum(1 for v in data.values() if v is True)
                    self.dash_cards["clients"]["value"].configure(
                        text=f"{online}/{total}", fg=SUCCESS if online > 0 else TEXT)
                    self.dash_cards["clients"]["status"].configure(text="reachable")
                    self._log_to(self.dash_log, f"[OK] {online}/{total} clients online", "ok")
                except (json.JSONDecodeError, AttributeError):
                    self.dash_cards["clients"]["value"].configure(text="?", fg=WARNING)
                    self._log_to(self.dash_log, f"[WARN] Could not parse client data", "warn")
            else:
                self.dash_cards["clients"]["value"].configure(text="?", fg=WARNING)
        self._ssh_bg("""opsi-admin -d -S method hostControlSafe_reachable '["*"]' 2>/dev/null || echo '{}'""", on_clients)

        # Disk space
        def on_disk(out, err, rc):
            if rc == 0 and out:
                lines = out.strip().split("\n")
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 2:
                        pct = parts[0].strip()
                        avail = parts[1].strip() if len(parts) > 1 else ""
                        pct_num = int(pct.replace("%", "")) if "%" in pct else 0
                        color = SUCCESS if pct_num < 80 else (WARNING if pct_num < 90 else ERROR)
                        self.dash_cards["disk"]["value"].configure(text=pct, fg=color)
                        self.dash_cards["disk"]["status"].configure(text=f"{avail} available")
                        self._log_to(self.dash_log, f"[OK] Disk usage: {pct} ({avail} free)", "ok")
                        return
            self.dash_cards["disk"]["value"].configure(text="?", fg=WARNING)
        self._ssh_bg("df /var/lib/opsi --output=pcent,avail 2>/dev/null | tail -1", on_disk)

        # Failed deployments
        def on_failed(out, err, rc):
            if rc == 0:
                try:
                    data = json.loads(out) if out else []
                    count = len(data)
                    color = SUCCESS if count == 0 else ERROR
                    self.dash_cards["failed"]["value"].configure(text=str(count), fg=color)
                    self.dash_cards["failed"]["status"].configure(
                        text="all good" if count == 0 else "need attention")
                    tag = "ok" if count == 0 else "error"
                    self._log_to(self.dash_log, f"[{'OK' if count == 0 else 'WARN'}] {count} failed deployments", tag)
                except json.JSONDecodeError:
                    self.dash_cards["failed"]["value"].configure(text="?", fg=WARNING)
            else:
                self.dash_cards["failed"]["value"].configure(text="?", fg=WARNING)
        self._ssh_bg("""opsi-admin -d -S method productOnClient_getObjects '[]' '{"actionResult":"failed"}' 2>/dev/null || echo '[]'""", on_failed)

    # ══════════════════════════════════════════════════════════════════════════
    # PACKAGING
    # ══════════════════════════════════════════════════════════════════════════

    def _create_packaging(self):
        page = tk.Frame(self.content, bg=BG)
        self.pages["packaging"] = page

        header = tk.Frame(page, bg=BG)
        header.pack(fill="x", padx=32, pady=(32, 0))
        tk.Label(header, text="Packaging", font=(FONT, 24, "bold"),
                bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(header, text="Create, update, and remove OPSI packages",
                font=(FONT, 12), bg=BG, fg=TEXT_SECONDARY).pack(anchor="w", pady=(4, 0))

        # Tab bar
        tab_bar = tk.Frame(page, bg=BG)
        tab_bar.pack(fill="x", padx=32, pady=(16, 16))

        self.pkg_tab_buttons = {}
        self.pkg_tab_frames = {}

        for key, label in [("create", "Create Package"), ("update", "Update Package"), ("remove", "Remove Package")]:
            btn = TabButton(tab_bar, text=label, width=140,
                           command=lambda k=key: self._show_pkg_tab(k))
            btn.pack(side="left", padx=(0, 4))
            self.pkg_tab_buttons[key] = btn

        # Container for tab content + log
        main_container = tk.Frame(page, bg=BG)
        main_container.pack(fill="both", expand=True, padx=32, pady=(0, 16))

        # Left side: tab content
        self.pkg_left = tk.Frame(main_container, bg=BG)
        self.pkg_left.pack(side="left", fill="both", expand=True, padx=(0, 16))

        # Right side: log (shared)
        right = tk.Frame(main_container, bg=BG, width=300)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        log_card = self._create_card(right, "Build Log", expand=True)
        log_inner = tk.Frame(log_card, bg=CARD)
        log_inner.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.pkg_log = self._make_log_widget(log_inner)
        self.pkg_log.pack(fill="both", expand=True)

        self._create_pkg_create_tab()
        self._create_pkg_update_tab()
        self._create_pkg_remove_tab()

        self._show_pkg_tab("create")

    def _show_pkg_tab(self, tab_name):
        for frame in self.pkg_tab_frames.values():
            frame.pack_forget()
        for btn in self.pkg_tab_buttons.values():
            btn.set_active(False)
        self.pkg_tab_frames[tab_name].pack(fill="both", expand=True)
        self.pkg_tab_buttons[tab_name].set_active(True)

    def _create_pkg_create_tab(self):
        frame = tk.Frame(self.pkg_left, bg=BG)
        self.pkg_tab_frames["create"] = frame

        # Package Info
        card1 = tk.Frame(frame, bg=CARD)
        card1.pack(fill="x", pady=(0, 12))
        tk.Label(card1, text="Package Info", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))

        form = tk.Frame(card1, bg=CARD)
        form.pack(fill="x", padx=20, pady=(0, 20))

        row1 = tk.Frame(form, bg=CARD)
        row1.pack(fill="x", pady=4)
        self._add_form_field(row1, "Package ID", "pkg_id", "firefox", side="left", width=20)
        self._add_form_field(row1, "Version", "pkg_version", "1.0.0", side="left", width=15)

        row2 = tk.Frame(form, bg=CARD)
        row2.pack(fill="x", pady=4)
        self._add_form_field(row2, "Product Name", "pkg_name", "Mozilla Firefox", side="left", width=30)

        tk.Label(form, text="Description", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w", pady=(8, 4))
        self.pkg_desc = tk.Text(form, bg=BG_SECONDARY, fg=TEXT, font=(FONT, 11),
                               relief="flat", height=2, insertbackground=ACCENT,
                               highlightthickness=1, highlightbackground=BORDER,
                               highlightcolor=ACCENT)
        self.pkg_desc.pack(fill="x")

        # Installer Files
        card2 = tk.Frame(frame, bg=CARD)
        card2.pack(fill="x", pady=(0, 12))
        tk.Label(card2, text="Installer Files", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))

        files_inner = tk.Frame(card2, bg=CARD)
        files_inner.pack(fill="x", padx=20, pady=(0, 20))

        type_frame = tk.Frame(files_inner, bg=CARD)
        type_frame.pack(fill="x", pady=(0, 12))
        tk.Label(type_frame, text="Type:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(side="left")
        for key, info in self.INSTALLER_TYPES.items():
            rb = tk.Radiobutton(type_frame, text=info["name"],
                               variable=self.installer_type, value=key,
                               bg=CARD, fg=TEXT, selectcolor=BG_SECONDARY,
                               activebackground=CARD, activeforeground=ACCENT,
                               font=(FONT, 10), highlightthickness=0,
                               command=self._on_type_change)
            rb.pack(side="left", padx=(12, 0))

        params_frame = tk.Frame(files_inner, bg=CARD)
        params_frame.pack(fill="x", pady=(0, 12))
        tk.Label(params_frame, text="Silent Parameters:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(side="left")
        self.params_entry = ModernEntry(params_frame, width=40)
        self.params_entry.pack(side="left", padx=(12, 0))
        self._on_type_change()

        self.file_list = tk.Listbox(files_inner, bg=BG_SECONDARY, fg=TEXT,
                                    font=(FONT_MONO, 10), relief="flat",
                                    highlightthickness=1, highlightbackground=BORDER,
                                    selectbackground=ACCENT, selectforeground=TEXT,
                                    height=4)
        self.file_list.pack(fill="x", pady=(0, 8))

        btn_row = tk.Frame(files_inner, bg=CARD)
        btn_row.pack(fill="x")
        ModernButton(btn_row, text="Add Files", command=self._browse_files,
                    primary=True, width=100).pack(side="left")
        ModernButton(btn_row, text="Remove", command=self._remove_file,
                    width=80).pack(side="left", padx=(8, 0))

        # Deploy options
        card3 = tk.Frame(frame, bg=CARD)
        card3.pack(fill="x", pady=(0, 12))
        tk.Label(card3, text="Deploy", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))

        deploy_inner = tk.Frame(card3, bg=CARD)
        deploy_inner.pack(fill="x", padx=20, pady=(0, 20))

        tk.Label(deploy_inner, text="If package exists:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.overwrite_var = tk.StringVar(value="Overwrite")
        overwrite_menu = tk.OptionMenu(deploy_inner, self.overwrite_var,
                                       "Overwrite", "New version", "Abort")
        overwrite_menu.config(bg=CARD, fg=TEXT, font=(FONT, 10),
                             activebackground=ACCENT, activeforeground=BG,
                             highlightthickness=0, bd=0, relief="flat")
        overwrite_menu["menu"].config(bg=CARD, fg=TEXT, font=(FONT, 10),
                                      activebackground=ACCENT, activeforeground=BG)
        overwrite_menu.pack(fill="x", pady=(0, 8))

        tk.Label(deploy_inner, text="Output Directory:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.output_entry = ModernEntry(deploy_inner)
        self.output_entry.insert(0, str(Path.home() / "Desktop"))
        self.output_entry.pack(fill="x", pady=(0, 12))

        btn_frame = tk.Frame(deploy_inner, bg=CARD)
        btn_frame.pack(fill="x")
        ModernButton(btn_frame, text="Build ZIP", command=self._build_package,
                    width=110).pack(side="left")
        ModernButton(btn_frame, text="Deploy", command=self._build_and_deploy,
                    primary=True, width=110).pack(side="left", padx=(8, 0))

    def _create_pkg_update_tab(self):
        frame = tk.Frame(self.pkg_left, bg=BG)
        self.pkg_tab_frames["update"] = frame

        card = tk.Frame(frame, bg=CARD)
        card.pack(fill="both", expand=True)
        tk.Label(card, text="Update Existing Package", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))

        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Controls row
        ctrl = tk.Frame(inner, bg=CARD)
        ctrl.pack(fill="x", pady=(0, 12))

        ModernButton(ctrl, text="Refresh List", command=self._refresh_pkg_list_update,
                    primary=True, width=120).pack(side="left")

        tk.Label(ctrl, text="Deploy mode:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(side="left", padx=(20, 8))
        self.update_mode = tk.StringVar(value="Setup on clients")
        mode_menu = tk.OptionMenu(ctrl, self.update_mode,
                                  "Setup on clients", "Update action")
        mode_menu.config(bg=CARD, fg=TEXT, font=(FONT, 10),
                        activebackground=ACCENT, activeforeground=BG,
                        highlightthickness=0, bd=0, relief="flat")
        mode_menu["menu"].config(bg=CARD, fg=TEXT, font=(FONT, 10),
                                activebackground=ACCENT, activeforeground=BG)
        mode_menu.pack(side="left")

        # Package list
        tk.Label(inner, text="Installed packages on server:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))

        self.update_pkg_list = tk.Listbox(inner, bg=BG_SECONDARY, fg=TEXT,
                                          font=(FONT_MONO, 10), relief="flat",
                                          highlightthickness=1, highlightbackground=BORDER,
                                          selectbackground=ACCENT, selectforeground=TEXT,
                                          height=12)
        self.update_pkg_list.pack(fill="both", expand=True, pady=(0, 12))

        # Upload and deploy
        bottom = tk.Frame(inner, bg=CARD)
        bottom.pack(fill="x")

        tk.Label(bottom, text="Upload .opsi file:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(side="left")
        self.update_file_path = ModernEntry(bottom, placeholder="Select .opsi file...", width=30)
        self.update_file_path.pack(side="left", padx=(8, 8))
        ModernButton(bottom, text="Browse", command=self._browse_opsi_file,
                    width=80).pack(side="left", padx=(0, 8))
        ModernButton(bottom, text="Deploy Update", command=self._deploy_update,
                    primary=True, width=130).pack(side="left")

    def _create_pkg_remove_tab(self):
        frame = tk.Frame(self.pkg_left, bg=BG)
        self.pkg_tab_frames["remove"] = frame

        card = tk.Frame(frame, bg=CARD)
        card.pack(fill="both", expand=True)
        tk.Label(card, text="Remove Package", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))

        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Controls
        ctrl = tk.Frame(inner, bg=CARD)
        ctrl.pack(fill="x", pady=(0, 12))

        ModernButton(ctrl, text="Refresh List", command=self._refresh_pkg_list_remove,
                    primary=True, width=120).pack(side="left")

        self.remove_purge = tk.BooleanVar(value=False)
        tk.Checkbutton(ctrl, text="Purge (remove client states too)",
                      variable=self.remove_purge, bg=CARD, fg=TEXT,
                      selectcolor=BG_SECONDARY, activebackground=CARD,
                      activeforeground=ACCENT, font=(FONT, 10),
                      highlightthickness=0).pack(side="left", padx=(20, 0))

        self.remove_all_depots = tk.BooleanVar(value=False)
        tk.Checkbutton(ctrl, text="All depots",
                      variable=self.remove_all_depots, bg=CARD, fg=TEXT,
                      selectcolor=BG_SECONDARY, activebackground=CARD,
                      activeforeground=ACCENT, font=(FONT, 10),
                      highlightthickness=0).pack(side="left", padx=(16, 0))

        # Search
        search_frame = tk.Frame(inner, bg=CARD)
        search_frame.pack(fill="x", pady=(0, 8))
        tk.Label(search_frame, text="Filter:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(side="left")
        self.remove_search = ModernEntry(search_frame, placeholder="Search packages...", width=30)
        self.remove_search.pack(side="left", padx=(8, 0))
        self.remove_search.bind("<KeyRelease>", lambda _: self._filter_remove_list())

        # Package list
        self.remove_pkg_list = tk.Listbox(inner, bg=BG_SECONDARY, fg=TEXT,
                                          font=(FONT_MONO, 10), relief="flat",
                                          highlightthickness=1, highlightbackground=BORDER,
                                          selectbackground=ACCENT, selectforeground=TEXT,
                                          height=12, selectmode="extended")
        self.remove_pkg_list.pack(fill="both", expand=True, pady=(0, 12))

        self.remove_all_packages = []  # Store full list for filtering

        btn_frame = tk.Frame(inner, bg=CARD)
        btn_frame.pack(fill="x")
        ModernButton(btn_frame, text="Remove Selected", command=self._remove_packages,
                    primary=True, width=150).pack(side="left")

    # ══════════════════════════════════════════════════════════════════════════
    # WAKE ON LAN
    # ══════════════════════════════════════════════════════════════════════════

    def _create_wakeonlan(self):
        page = tk.Frame(self.content, bg=BG)
        self.pages["wakeonlan"] = page

        header = tk.Frame(page, bg=BG)
        header.pack(fill="x", padx=32, pady=(32, 16))
        tk.Label(header, text="Wake on LAN", font=(FONT, 24, "bold"),
                bg=BG, fg=TEXT).pack(side="left", anchor="w")

        container = tk.Frame(page, bg=BG)
        container.pack(fill="both", expand=True, padx=32, pady=(0, 16))

        # Left panel: Client Status
        left = tk.Frame(container, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 16))

        client_card = tk.Frame(left, bg=CARD)
        client_card.pack(fill="both", expand=True)

        # Client card header
        ch = tk.Frame(client_card, bg=CARD)
        ch.pack(fill="x", padx=20, pady=(16, 12))
        tk.Label(ch, text="Client Status", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(side="left")

        self.wol_auto_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ch, text="Auto-refresh", variable=self.wol_auto_var,
                      bg=CARD, fg=TEXT_SECONDARY, selectcolor=BG_SECONDARY,
                      activebackground=CARD, font=(FONT, 9),
                      highlightthickness=0,
                      command=self._toggle_wol_auto_refresh).pack(side="right", padx=(8, 0))

        ModernButton(ch, text="Refresh", command=self._refresh_wol_clients,
                    width=80, height=28).pack(side="right")

        # Select all checkbox
        sa_frame = tk.Frame(client_card, bg=CARD)
        sa_frame.pack(fill="x", padx=20)
        self.wol_select_all = tk.BooleanVar(value=False)
        tk.Checkbutton(sa_frame, text="Select All", variable=self.wol_select_all,
                      bg=CARD, fg=TEXT_SECONDARY, selectcolor=BG_SECONDARY,
                      activebackground=CARD, font=(FONT, 9),
                      highlightthickness=0,
                      command=self._toggle_select_all_wol).pack(side="left")

        # Column headers
        hdr = tk.Frame(client_card, bg=BG_SECONDARY)
        hdr.pack(fill="x", padx=20, pady=(8, 0))
        tk.Label(hdr, text="", width=3, bg=BG_SECONDARY).pack(side="left")
        tk.Label(hdr, text="Client", font=(FONT, 9, "bold"), bg=BG_SECONDARY,
                fg=TEXT_SECONDARY, width=25, anchor="w").pack(side="left")
        tk.Label(hdr, text="IP", font=(FONT, 9, "bold"), bg=BG_SECONDARY,
                fg=TEXT_SECONDARY, width=14, anchor="w").pack(side="left")
        tk.Label(hdr, text="MAC", font=(FONT, 9, "bold"), bg=BG_SECONDARY,
                fg=TEXT_SECONDARY, width=18, anchor="w").pack(side="left")
        tk.Label(hdr, text="Status", font=(FONT, 9, "bold"), bg=BG_SECONDARY,
                fg=TEXT_SECONDARY, width=8, anchor="w").pack(side="left")

        # Scrollable client list
        list_container = tk.Frame(client_card, bg=CARD)
        list_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        canvas = tk.Canvas(list_container, bg=BG_SECONDARY, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        self.wol_client_frame = tk.Frame(canvas, bg=BG_SECONDARY)

        self.wol_client_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.wol_client_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Right panel: Actions
        right = tk.Frame(container, bg=BG, width=280)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        # Wake actions card
        wake_card = tk.Frame(right, bg=CARD)
        wake_card.pack(fill="x", pady=(0, 12))
        tk.Label(wake_card, text="Wake Actions", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))

        wake_inner = tk.Frame(wake_card, bg=CARD)
        wake_inner.pack(fill="x", padx=20, pady=(0, 20))

        ModernButton(wake_inner, text="Wake All Clients",
                    command=self._wol_wake_all,
                    primary=True, width=240).pack(pady=(0, 8))

        # Group wake
        group_frame = tk.Frame(wake_inner, bg=CARD)
        group_frame.pack(fill="x", pady=(0, 8))
        tk.Label(group_frame, text="Group:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w")
        self.wol_group_var = tk.StringVar(value="")
        self.wol_group_menu = tk.OptionMenu(group_frame, self.wol_group_var, "")
        self.wol_group_menu.config(bg=CARD, fg=TEXT, font=(FONT, 10),
                                   activebackground=ACCENT, activeforeground=BG,
                                   highlightthickness=0, bd=0, relief="flat")
        self.wol_group_menu["menu"].config(bg=CARD, fg=TEXT, font=(FONT, 10),
                                           activebackground=ACCENT, activeforeground=BG)
        self.wol_group_menu.pack(fill="x", pady=(4, 4))
        ModernButton(group_frame, text="Wake Group", command=self._wol_wake_group,
                    width=240).pack()

        ModernButton(wake_inner, text="Wake Selected",
                    command=self._wol_wake_selected, width=240).pack(pady=(8, 0))

        # Single MAC wake
        single_card = tk.Frame(right, bg=CARD)
        single_card.pack(fill="x", pady=(0, 12))
        tk.Label(single_card, text="Manual Wake", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))

        single_inner = tk.Frame(single_card, bg=CARD)
        single_inner.pack(fill="x", padx=20, pady=(0, 20))

        tk.Label(single_inner, text="MAC Address:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w")
        self.wol_mac = ModernEntry(single_inner, placeholder="AA:BB:CC:DD:EE:FF")
        self.wol_mac.pack(fill="x", pady=(4, 8))
        ModernButton(single_inner, text="Send Magic Packet",
                    command=self._wol_wake_single, width=240).pack()

        # Additional actions
        extra_card = tk.Frame(right, bg=CARD)
        extra_card.pack(fill="x", pady=(0, 12))
        tk.Label(extra_card, text="Client Actions", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))

        extra_inner = tk.Frame(extra_card, bg=CARD)
        extra_inner.pack(fill="x", padx=20, pady=(0, 20))
        ModernButton(extra_inner, text="Reboot Selected",
                    command=self._wol_reboot_selected, width=240).pack(pady=(0, 8))
        ModernButton(extra_inner, text="Shutdown Selected",
                    command=self._wol_shutdown_selected, width=240).pack()

        # Status log
        log_card = self._create_card(right, "Status Log", expand=True)
        log_inner = tk.Frame(log_card, bg=CARD)
        log_inner.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.wol_log = self._make_log_widget(log_inner)
        self.wol_log.pack(fill="both", expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    # DIAGNOSTICS
    # ══════════════════════════════════════════════════════════════════════════

    def _create_diagnostics(self):
        page = tk.Frame(self.content, bg=BG)
        self.pages["diagnostics"] = page

        header = tk.Frame(page, bg=BG)
        header.pack(fill="x", padx=32, pady=(32, 0))
        tk.Label(header, text="Diagnostics", font=(FONT, 24, "bold"),
                bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(header, text="Server health, client diagnostics, and paedML checks",
                font=(FONT, 12), bg=BG, fg=TEXT_SECONDARY).pack(anchor="w", pady=(4, 0))

        # Tab bar
        tab_bar = tk.Frame(page, bg=BG)
        tab_bar.pack(fill="x", padx=32, pady=(16, 16))

        self.diag_tab_buttons = {}
        self.diag_tab_frames = {}

        for key, label in [("connection", "Connection"), ("health", "Server Health"),
                           ("clients", "Client Diagnostics"), ("paedml", "paedML Checks")]:
            btn = TabButton(tab_bar, text=label, width=140,
                           command=lambda k=key: self._show_diag_tab(k))
            btn.pack(side="left", padx=(0, 4))
            self.diag_tab_buttons[key] = btn

        # Container
        self.diag_container = tk.Frame(page, bg=BG)
        self.diag_container.pack(fill="both", expand=True, padx=32, pady=(0, 16))

        self._create_diag_connection()
        self._create_diag_health()
        self._create_diag_clients()
        self._create_diag_paedml()

        self._show_diag_tab("connection")

    def _show_diag_tab(self, tab_name):
        for frame in self.diag_tab_frames.values():
            frame.pack_forget()
        for btn in self.diag_tab_buttons.values():
            btn.set_active(False)
        self.diag_tab_frames[tab_name].pack(fill="both", expand=True)
        self.diag_tab_buttons[tab_name].set_active(True)

    def _create_diag_connection(self):
        frame = tk.Frame(self.diag_container, bg=BG)
        self.diag_tab_frames["connection"] = frame

        card = tk.Frame(frame, bg=CARD)
        card.pack(fill="x", pady=(0, 12))
        tk.Label(card, text="Connection Test", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))

        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=20, pady=(0, 20))

        row = tk.Frame(inner, bg=CARD)
        row.pack(fill="x")
        tk.Label(row, text="Host:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(side="left")
        self.diag_host = ModernEntry(row, placeholder="10.1.0.15", width=25)
        self.diag_host.pack(side="left", padx=(12, 0))
        ModernButton(row, text="Ping", command=self._diag_ping,
                    primary=True, width=80).pack(side="left", padx=(12, 0))
        ModernButton(row, text="SSH Test", command=self._diag_ssh,
                    width=90).pack(side="left", padx=(8, 0))
        ModernButton(row, text="Port Check", command=self._diag_port_check,
                    width=100).pack(side="left", padx=(8, 0))

        # Output
        out_card = self._create_card(frame, "Output", expand=True)
        out_inner = tk.Frame(out_card, bg=CARD)
        out_inner.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.diag_output = self._make_log_widget(out_inner)
        self.diag_output.pack(fill="both", expand=True)

    def _create_diag_health(self):
        frame = tk.Frame(self.diag_container, bg=BG)
        self.diag_tab_frames["health"] = frame

        # Top controls
        top_card = tk.Frame(frame, bg=CARD)
        top_card.pack(fill="x", pady=(0, 12))
        top_inner = tk.Frame(top_card, bg=CARD)
        top_inner.pack(fill="x", padx=20, pady=16)

        tk.Label(top_inner, text="Server Health", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(side="left")
        ModernButton(top_inner, text="Run Health Check", command=self._run_health_check,
                    primary=True, width=150).pack(side="right")
        ModernButton(top_inner, text="Check Services", command=self._check_services,
                    width=130).pack(side="right", padx=(0, 8))

        # Service status grid
        svc_card = tk.Frame(frame, bg=CARD)
        svc_card.pack(fill="x", pady=(0, 12))
        tk.Label(svc_card, text="Service Status", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))

        self.svc_grid = tk.Frame(svc_card, bg=CARD)
        self.svc_grid.pack(fill="x", padx=20, pady=(0, 20))

        self.svc_labels = {}
        services = ["opsiconfd", "smbd", "isc-dhcp-server", "named",
                    "apache2", "mysql", "tftpd-hpa"]
        for i, svc in enumerate(services):
            row_frame = tk.Frame(self.svc_grid, bg=CARD)
            row_frame.grid(row=i // 4, column=i % 4, padx=(0, 24), pady=4, sticky="w")
            dot = tk.Label(row_frame, text="●", font=(FONT, 10), bg=CARD, fg=TEXT_MUTED)
            dot.pack(side="left")
            tk.Label(row_frame, text=svc, font=(FONT, 10), bg=CARD, fg=TEXT).pack(side="left", padx=(4, 0))
            self.svc_labels[svc] = dot

        # Quick checks
        quick_card = tk.Frame(frame, bg=CARD)
        quick_card.pack(fill="x", pady=(0, 12))
        tk.Label(quick_card, text="Quick Checks", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))
        self.health_checks_frame = tk.Frame(quick_card, bg=CARD)
        self.health_checks_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.health_check_labels = {}

        checks = ["Disk Space", "Certificate Expiry", "NTP Sync", "OPSI Version", "paedML Version"]
        for check in checks:
            row = tk.Frame(self.health_checks_frame, bg=CARD)
            row.pack(fill="x", pady=2)
            dot = tk.Label(row, text="●", font=(FONT, 10), bg=CARD, fg=TEXT_MUTED)
            dot.pack(side="left")
            tk.Label(row, text=check, font=(FONT, 10), bg=CARD, fg=TEXT).pack(side="left", padx=(4, 0))
            val = tk.Label(row, text="", font=(FONT, 10), bg=CARD, fg=TEXT_SECONDARY)
            val.pack(side="right")
            self.health_check_labels[check] = {"dot": dot, "value": val}

        # Output
        out_card = self._create_card(frame, "Health Check Output", expand=True)
        out_inner = tk.Frame(out_card, bg=CARD)
        out_inner.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.health_output = self._make_log_widget(out_inner)
        self.health_output.pack(fill="both", expand=True)

    def _create_diag_clients(self):
        frame = tk.Frame(self.diag_container, bg=BG)
        self.diag_tab_frames["clients"] = frame

        # Client selection
        top_card = tk.Frame(frame, bg=CARD)
        top_card.pack(fill="x", pady=(0, 12))
        top_inner = tk.Frame(top_card, bg=CARD)
        top_inner.pack(fill="x", padx=20, pady=16)

        tk.Label(top_inner, text="Client:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(side="left")
        self.diag_client_entry = ModernEntry(top_inner, placeholder="client.domain.local", width=30)
        self.diag_client_entry.pack(side="left", padx=(8, 12))

        ModernButton(top_inner, text="Check Client", command=self._check_client,
                    primary=True, width=120).pack(side="left", padx=(0, 8))
        ModernButton(top_inner, text="Failed Installs (All)", command=self._check_failed_all,
                    width=160).pack(side="left", padx=(0, 8))
        ModernButton(top_inner, text="View Logs", command=self._view_client_logs,
                    width=100).pack(side="left")

        # Output
        out_card = self._create_card(frame, "Client Info", expand=True)
        out_inner = tk.Frame(out_card, bg=CARD)
        out_inner.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.client_output = self._make_log_widget(out_inner)
        self.client_output.pack(fill="both", expand=True)

    def _create_diag_paedml(self):
        frame = tk.Frame(self.diag_container, bg=BG)
        self.diag_tab_frames["paedml"] = frame

        top_card = tk.Frame(frame, bg=CARD)
        top_card.pack(fill="x", pady=(0, 12))
        top_inner = tk.Frame(top_card, bg=CARD)
        top_inner.pack(fill="x", padx=20, pady=16)

        tk.Label(top_inner, text="paedML Linux Diagnostics", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(side="left")
        ModernButton(top_inner, text="Run All Checks", command=self._run_paedml_checks,
                    primary=True, width=140).pack(side="right")

        # Check results grid
        results_card = tk.Frame(frame, bg=CARD)
        results_card.pack(fill="x", pady=(0, 12))
        tk.Label(results_card, text="Check Results", font=(FONT, 12, "bold"),
                bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 12))

        self.paedml_grid = tk.Frame(results_card, bg=CARD)
        self.paedml_grid.pack(fill="x", padx=20, pady=(0, 20))

        self.paedml_checks = {}
        checks = [
            ("time_sync", "NTP Time Sync"),
            ("disk_var", "Disk Space /var"),
            ("disk_srv", "Disk Space /srv"),
            ("cert_opsi", "OPSI Certificate"),
            ("dns_forward", "DNS Forward Lookup"),
            ("dns_reverse", "DNS Reverse Lookup"),
            ("dhcp_config", "DHCP Configuration"),
            ("samba_ad", "Samba AD Domain"),
            ("domain_join", "Domain Join Status"),
            ("sophomorix", "Sophomorix Check"),
        ]
        for i, (key, label) in enumerate(checks):
            row = tk.Frame(self.paedml_grid, bg=CARD)
            row.grid(row=i, column=0, sticky="w", pady=3)
            dot = tk.Label(row, text="○", font=(FONT, 12), bg=CARD, fg=TEXT_MUTED)
            dot.pack(side="left")
            name = tk.Label(row, text=label, font=(FONT, 10), bg=CARD, fg=TEXT, width=20, anchor="w")
            name.pack(side="left", padx=(8, 0))
            detail = tk.Label(row, text="Not checked", font=(FONT, 9), bg=CARD, fg=TEXT_MUTED)
            detail.pack(side="left", padx=(8, 0))
            self.paedml_checks[key] = {"dot": dot, "detail": detail}

        # Output
        out_card = self._create_card(frame, "Diagnostic Output", expand=True)
        out_inner = tk.Frame(out_card, bg=CARD)
        out_inner.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.paedml_output = self._make_log_widget(out_inner)
        self.paedml_output.pack(fill="both", expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    # PACKAGING ACTIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _on_type_change(self):
        itype = self.installer_type.get()
        params = self.INSTALLER_TYPES[itype]["params"]
        self.params_entry.delete(0, tk.END)
        if params:
            self.params_entry.insert(0, params)

    def _browse_files(self):
        files = filedialog.askopenfilenames(
            title="Select installer files",
            filetypes=[
                ("All supported", "*.exe *.msi *.ps1 *.bat *.cmd"),
                ("Executables", "*.exe *.msi"),
                ("Scripts", "*.ps1 *.bat *.cmd"),
                ("All files", "*.*")
            ]
        )
        for f in files:
            if f not in self.selected_files:
                self.selected_files.append(f)
                self.file_list.insert(tk.END, os.path.basename(f))

    def _remove_file(self):
        sel = self.file_list.curselection()
        if sel:
            idx = sel[0]
            self.file_list.delete(idx)
            del self.selected_files[idx]

    def _browse_opsi_file(self):
        f = filedialog.askopenfilename(
            title="Select .opsi package",
            filetypes=[("OPSI packages", "*.opsi"), ("All files", "*.*")]
        )
        if f:
            self.update_file_path.delete(0, tk.END)
            self.update_file_path.insert(0, f)
            self.update_file_path.configure(fg=TEXT)

    def _validate(self):
        pkg_id = self._get_text(self.pkg_id)
        if not pkg_id:
            messagebox.showerror("Error", "Package ID is required!")
            return False
        if not re.match(r'^[a-z0-9\-]+$', pkg_id):
            messagebox.showerror("Error", "Package ID: lowercase, numbers, hyphens only!")
            return False
        return True

    def _generate_control(self, data):
        return f"""[Package]
version: 1
depends:
incremental: False

[Product]
type: localboot
id: {data['id']}
name: {data['name']}
description: {data['desc']}
advice:
version: {data['version']}
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
"""

    def _generate_setup(self, data, files):
        itype = self.installer_type.get()
        params = self.params_entry.get()

        lines = [
            f"; Setup script for {data['name']}",
            "; Generated by OPSI Toolbox",
            "",
            "[Actions]",
            'requiredWinstVersion >= "4.11.6"',
            "",
            "DefVar $SetupFile$",
            "DefVar $ExitCode$",
            ""
        ]

        for i, f in enumerate(files):
            fname = os.path.basename(f)
            lines.append(f'Set $SetupFile$ = "%ScriptPath%\\files\\{fname}"')
            lines.append(f'Message "Installing {fname}..."')
            lines.append("")

            if itype == "msi":
                lines.extend([
                    f"Winbatch_install_{i}", "Sub_check_exitcode", "",
                    f"[Winbatch_install_{i}]",
                    f'msiexec /i "$SetupFile$" {params}', ""
                ])
            elif itype == "ps1":
                lines.extend([
                    f"DosInAnIcon_install_{i}", "Sub_check_exitcode", "",
                    f"[DosInAnIcon_install_{i}]",
                    f'powershell.exe -ExecutionPolicy Bypass -File "$SetupFile$"', ""
                ])
            elif itype == "bat":
                lines.extend([
                    f"DosInAnIcon_install_{i}", "Sub_check_exitcode", "",
                    f"[DosInAnIcon_install_{i}]",
                    f'cmd.exe /c "$SetupFile$"', ""
                ])
            else:
                lines.extend([
                    f"Winbatch_install_{i}", "Sub_check_exitcode", "",
                    f"[Winbatch_install_{i}]",
                    f'"$SetupFile$" {params}' if params else '"$SetupFile$"', ""
                ])

        lines.extend([
            "[Sub_check_exitcode]",
            "set $ExitCode$ = getLastExitCode",
            'if ($ExitCode$ = "0")',
            '    comment "OK"',
            "else",
            '    logError "Failed: " + $ExitCode$',
            "    isFatalError",
            "endif"
        ])
        return "\n".join(lines)

    def _generate_uninstall(self, data):
        return f"""; Uninstall script for {data['name']}
; Generated by OPSI Toolbox

[Actions]
Message "Uninstalling {data['name']}..."

; Add uninstall commands here
"""

    def _pkg_log(self, msg, tag=""):
        self._log_to(self.pkg_log, msg, tag)

    def _build_package(self):
        if not self._validate():
            return
        self.pkg_log.delete("1.0", tk.END)
        self._pkg_log("Starting build...", "info")

        data = {
            "id": self._get_text(self.pkg_id),
            "name": self._get_text(self.pkg_name) or self._get_text(self.pkg_id),
            "version": self._get_text(self.pkg_version) or "1.0.0",
            "desc": self._get_text(self.pkg_desc),
        }

        pkg_folder = f"{data['id']}_{data['version']}-1"
        output_base = self.output_entry.get()
        pkg_path = os.path.join(output_base, pkg_folder)

        try:
            self._pkg_log(f"Creating: {pkg_folder}")
            os.makedirs(os.path.join(pkg_path, "OPSI"), exist_ok=True)
            os.makedirs(os.path.join(pkg_path, "CLIENT_DATA", "files"), exist_ok=True)

            with open(os.path.join(pkg_path, "OPSI", "control"), "w", encoding="utf-8") as f:
                f.write(self._generate_control(data))
            self._pkg_log("[OK] control", "ok")

            with open(os.path.join(pkg_path, "CLIENT_DATA", "setup.opsiscript"), "w", encoding="utf-8") as f:
                f.write(self._generate_setup(data, self.selected_files))
            self._pkg_log("[OK] setup.opsiscript", "ok")

            with open(os.path.join(pkg_path, "CLIENT_DATA", "uninstall.opsiscript"), "w", encoding="utf-8") as f:
                f.write(self._generate_uninstall(data))
            self._pkg_log("[OK] uninstall.opsiscript", "ok")

            for f in self.selected_files:
                fname = os.path.basename(f)
                shutil.copy2(f, os.path.join(pkg_path, "CLIENT_DATA", "files", fname))
                self._pkg_log(f"[OK] {fname}", "ok")

            zip_path = os.path.join(output_base, f"{pkg_folder}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(pkg_path):
                    for file in files:
                        fp = os.path.join(root, file)
                        zf.write(fp, os.path.relpath(fp, output_base))

            self._pkg_log("")
            self._pkg_log("BUILD SUCCESSFUL!", "ok")
            self._pkg_log(f"Package: {zip_path}", "info")
        except Exception as e:
            self._pkg_log(f"[ERROR] {str(e)}", "error")

    def _build_and_deploy(self):
        self._build_package()
        server = self._get_server()
        user = self._get_user()

        data = {
            "id": self._get_text(self.pkg_id),
            "version": self._get_text(self.pkg_version) or "1.0.0",
        }
        pkg_folder = f"{data['id']}_{data['version']}-1"
        pkg_path = os.path.join(self.output_entry.get(), pkg_folder)

        self._pkg_log("")
        self._pkg_log(f"DEPLOYING TO {server}...", "info")

        def do_deploy():
            try:
                result = subprocess.run(
                    ["scp", "-r", pkg_path, f"{user}@{server}:/var/lib/opsi/workbench/"],
                    capture_output=True, text=True,
                    **self._subprocess_kwargs()
                )
                if result.returncode != 0:
                    raise Exception(f"SCP failed: {result.stderr}")
                self.after(0, lambda: self._pkg_log("[OK] Files copied", "ok"))

                overwrite_choice = self.overwrite_var.get()
                if overwrite_choice == "Overwrite":
                    makepackage_cmd = f"cd /var/lib/opsi/workbench && opsi-makepackage --keep-versions {pkg_folder}"
                elif overwrite_choice == "New version":
                    find_cmd = f"ls /var/lib/opsi/workbench/{data['id']}_{data['version']}-*.opsi 2>/dev/null | sort -V | tail -1"
                    find_out, _, _ = self._ssh_cmd(find_cmd)
                    release = 2
                    if find_out:
                        try:
                            existing = find_out.rsplit("-", 1)[-1].split(".opsi")[0]
                            release = int(existing) + 1
                        except (ValueError, IndexError):
                            pass
                    makepackage_cmd = f"cd /var/lib/opsi/workbench && opsi-makepackage --product-version {data['version']} --package-version {release} {pkg_folder}"
                else:
                    check_out, _, _ = self._ssh_cmd(f"ls /var/lib/opsi/workbench/{pkg_folder}-*.opsi 2>/dev/null")
                    if check_out:
                        self.after(0, lambda: self._pkg_log("[ABORTED] Package already exists on server", "warn"))
                        return
                    makepackage_cmd = f"cd /var/lib/opsi/workbench && opsi-makepackage {pkg_folder}"

                out, err, rc = self._ssh_cmd(makepackage_cmd, timeout=120)
                if out:
                    self.after(0, lambda o=out: self._pkg_log(o, ""))
                if rc != 0:
                    self.after(0, lambda e=err: self._pkg_log(f"[ERROR] {e}", "error"))
                    return

                out, err, rc = self._ssh_cmd(
                    f"opsi-package-manager -i /var/lib/opsi/workbench/{pkg_folder}-*.opsi",
                    timeout=120
                )
                if out:
                    self.after(0, lambda o=out: self._pkg_log(o, ""))
                if rc != 0:
                    self.after(0, lambda e=err: self._pkg_log(f"[ERROR] {e}", "error"))
                    return

                self.after(0, lambda: self._pkg_log(""))
                self.after(0, lambda: self._pkg_log("DEPLOYMENT COMPLETE!", "ok"))
            except Exception as e:
                self.after(0, lambda e=e: self._pkg_log(f"[ERROR] {str(e)}", "error"))

        threading.Thread(target=do_deploy, daemon=True).start()

    def _refresh_pkg_list_update(self):
        self.update_pkg_list.delete(0, tk.END)
        self.update_pkg_list.insert(tk.END, "Loading...")
        def on_done(out, err, rc):
            self.update_pkg_list.delete(0, tk.END)
            if rc == 0 and out:
                for line in out.split("\n"):
                    if line.strip():
                        self.update_pkg_list.insert(tk.END, line.strip())
            else:
                self.update_pkg_list.insert(tk.END, f"Error: {err or 'no packages found'}")
        self._ssh_bg("opsi-package-manager -l 2>/dev/null", on_done)

    def _deploy_update(self):
        sel = self.update_pkg_list.curselection()
        opsi_file = self.update_file_path.get_value()

        if not opsi_file:
            messagebox.showerror("Error", "Select an .opsi file to upload")
            return

        self.pkg_log.delete("1.0", tk.END)
        self._pkg_log("Deploying update...", "info")

        mode = self.update_mode.get()
        flag = "-S" if mode == "Setup on clients" else "-U"

        def do_update():
            server = self._get_server()
            user = self._get_user()
            fname = os.path.basename(opsi_file)
            remote_path = f"/var/lib/opsi/workbench/{fname}"

            try:
                result = subprocess.run(
                    ["scp", opsi_file, f"{user}@{server}:{remote_path}"],
                    capture_output=True, text=True,
                    **self._subprocess_kwargs()
                )
                if result.returncode != 0:
                    raise Exception(f"SCP failed: {result.stderr}")
                self.after(0, lambda: self._pkg_log("[OK] File uploaded", "ok"))

                out, err, rc = self._ssh_cmd(f"opsi-package-manager {flag} -i {remote_path}", timeout=120)
                if out:
                    self.after(0, lambda o=out: self._pkg_log(o, ""))
                if rc != 0:
                    self.after(0, lambda e=err: self._pkg_log(f"[ERROR] {e}", "error"))
                else:
                    self.after(0, lambda: self._pkg_log("UPDATE COMPLETE!", "ok"))
            except Exception as e:
                self.after(0, lambda e=e: self._pkg_log(f"[ERROR] {str(e)}", "error"))

        threading.Thread(target=do_update, daemon=True).start()

    def _refresh_pkg_list_remove(self):
        self.remove_pkg_list.delete(0, tk.END)
        self.remove_pkg_list.insert(tk.END, "Loading...")
        self.remove_all_packages = []
        def on_done(out, err, rc):
            self.remove_pkg_list.delete(0, tk.END)
            self.remove_all_packages = []
            if rc == 0 and out:
                for line in out.split("\n"):
                    if line.strip():
                        self.remove_all_packages.append(line.strip())
                        self.remove_pkg_list.insert(tk.END, line.strip())
            else:
                self.remove_pkg_list.insert(tk.END, f"Error: {err or 'no packages found'}")
        self._ssh_bg("opsi-package-manager -l 2>/dev/null", on_done)

    def _filter_remove_list(self):
        query = self.remove_search.get_value().lower()
        self.remove_pkg_list.delete(0, tk.END)
        for pkg in self.remove_all_packages:
            if query in pkg.lower():
                self.remove_pkg_list.insert(tk.END, pkg)

    def _remove_packages(self):
        sel = self.remove_pkg_list.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Select packages to remove")
            return

        packages = [self.remove_pkg_list.get(i) for i in sel]
        # Extract product ID (first column before any whitespace/version info)
        product_ids = [p.split()[0] if " " in p else p for p in packages]

        purge = self.remove_purge.get()
        all_depots = self.remove_all_depots.get()

        msg = f"Remove {len(product_ids)} package(s)?"
        if purge:
            msg += "\n(PURGE mode: client states will also be removed)"
        if not messagebox.askyesno("Confirm Removal", msg):
            return

        self.pkg_log.delete("1.0", tk.END)
        self._pkg_log(f"Removing {len(product_ids)} package(s)...", "info")

        def do_remove():
            for pid in product_ids:
                flag = "--purge" if purge else "-r"
                depot = "-d ALL" if all_depots else ""
                cmd = f"opsi-package-manager {flag} {depot} {pid}".strip()
                self.after(0, lambda c=cmd: self._pkg_log(f"Running: {c}", "info"))

                out, err, rc = self._ssh_cmd(cmd, timeout=60)
                if out:
                    self.after(0, lambda o=out: self._pkg_log(o, ""))
                if rc == 0:
                    self.after(0, lambda p=pid: self._pkg_log(f"[OK] Removed {p}", "ok"))
                else:
                    self.after(0, lambda p=pid, e=err: self._pkg_log(f"[ERROR] {p}: {e}", "error"))

            self.after(0, lambda: self._pkg_log("REMOVAL COMPLETE!", "ok"))
            self.after(0, self._refresh_pkg_list_remove)

        threading.Thread(target=do_remove, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # WAKE ON LAN ACTIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _send_wol(self, mac):
        mac = mac.replace(":", "").replace("-", "").upper()
        if len(mac) != 12:
            return False
        try:
            data = bytes.fromhex("FF" * 6 + mac * 16)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(data, ("255.255.255.255", 9))
            sock.close()
            return True
        except:
            return False

    def _wol_log(self, msg, tag=""):
        self._log_to(self.wol_log, msg, tag)

    def _refresh_wol_clients(self):
        for widget in self.wol_client_frame.winfo_children():
            widget.destroy()
        self.wol_client_vars.clear()
        self.wol_clients = []

        loading = tk.Label(self.wol_client_frame, text="Loading clients...",
                          font=(FONT, 10), bg=BG_SECONDARY, fg=TEXT_MUTED)
        loading.pack(pady=20)

        def fetch():
            # Get all clients
            out, err, rc = self._ssh_cmd(
                """opsi-admin -d -S method host_getObjects '[]' '{"type":"OpsiClient"}' 2>/dev/null""",
                timeout=30
            )
            clients = []
            if rc == 0 and out:
                try:
                    data = json.loads(out)
                    for c in data:
                        clients.append({
                            "id": c.get("id", ""),
                            "ip": c.get("ipAddress", ""),
                            "mac": c.get("hardwareAddress", ""),
                        })
                except json.JSONDecodeError:
                    pass

            # Get reachability
            reach_out, _, _ = self._ssh_cmd(
                """opsi-admin -d -S method hostControlSafe_reachable '["*"]' 2>/dev/null""",
                timeout=30
            )
            reachable = {}
            if reach_out:
                try:
                    reachable = json.loads(reach_out)
                except json.JSONDecodeError:
                    pass

            # Also refresh groups
            grp_out, _, _ = self._ssh_cmd(
                """opsi-admin -d -S method group_getObjects '[]' '{"type":"HostGroup"}' 2>/dev/null""",
                timeout=15
            )
            groups = []
            if grp_out:
                try:
                    grp_data = json.loads(grp_out)
                    groups = [g.get("id", "") for g in grp_data if g.get("id")]
                except json.JSONDecodeError:
                    pass

            self.after(0, lambda: self._populate_wol_clients(clients, reachable, groups))

        threading.Thread(target=fetch, daemon=True).start()

    def _populate_wol_clients(self, clients, reachable, groups):
        for widget in self.wol_client_frame.winfo_children():
            widget.destroy()
        self.wol_client_vars.clear()
        self.wol_clients = clients

        if not clients:
            tk.Label(self.wol_client_frame, text="No clients found. Check server connection.",
                    font=(FONT, 10), bg=BG_SECONDARY, fg=TEXT_MUTED).pack(pady=20)
            return

        for client in clients:
            cid = client["id"]
            is_online = reachable.get(cid, False) is True

            row = tk.Frame(self.wol_client_frame, bg=BG_SECONDARY)
            row.pack(fill="x", pady=1)

            var = tk.BooleanVar(value=False)
            self.wol_client_vars[cid] = var
            tk.Checkbutton(row, variable=var, bg=BG_SECONDARY,
                          selectcolor=CARD, highlightthickness=0,
                          activebackground=BG_SECONDARY).pack(side="left")

            tk.Label(row, text=cid, font=(FONT, 9), bg=BG_SECONDARY,
                    fg=TEXT, width=25, anchor="w").pack(side="left")
            tk.Label(row, text=client["ip"] or "-", font=(FONT, 9), bg=BG_SECONDARY,
                    fg=TEXT_SECONDARY, width=14, anchor="w").pack(side="left")
            tk.Label(row, text=client["mac"] or "-", font=(FONT_MONO, 9), bg=BG_SECONDARY,
                    fg=TEXT_SECONDARY, width=18, anchor="w").pack(side="left")

            status_text = "Online" if is_online else "Offline"
            status_color = SUCCESS if is_online else ERROR
            tk.Label(row, text=status_text, font=(FONT, 9, "bold"), bg=BG_SECONDARY,
                    fg=status_color, width=8, anchor="w").pack(side="left")

        # Update group dropdown
        menu = self.wol_group_menu["menu"]
        menu.delete(0, "end")
        for g in groups:
            menu.add_command(label=g, command=lambda v=g: self.wol_group_var.set(v))
        if groups:
            self.wol_group_var.set(groups[0])

        self._wol_log(f"Loaded {len(clients)} clients, {sum(1 for v in reachable.values() if v is True)} online", "ok")

    def _toggle_select_all_wol(self):
        val = self.wol_select_all.get()
        for var in self.wol_client_vars.values():
            var.set(val)

    def _toggle_wol_auto_refresh(self):
        self.wol_auto_refresh = self.wol_auto_var.get()
        if self.wol_auto_refresh:
            self._wol_auto_tick()

    def _wol_auto_tick(self):
        if self.wol_auto_refresh:
            self._refresh_wol_clients()
            self.after(10000, self._wol_auto_tick)

    def _get_selected_client_ids(self):
        return [cid for cid, var in self.wol_client_vars.items() if var.get()]

    def _wol_wake_all(self):
        self._wol_log("Waking ALL clients via OPSI...", "info")
        self._ssh_bg(
            """opsi-admin -d method hostControlSafe_start '["*"]'""",
            lambda out, err, rc: self._wol_log(
                "[OK] Wake-all command sent" if rc == 0 else f"[ERROR] {err}", "ok" if rc == 0 else "error"
            )
        )

    def _wol_wake_group(self):
        group = self.wol_group_var.get()
        if not group:
            self._wol_log("No group selected", "warn")
            return
        self._wol_log(f"Waking group '{group}'...", "info")

        def do_wake():
            # Get group members
            out, err, rc = self._ssh_cmd(
                f"""opsi-admin -d -S method objectToGroup_getObjects '[]' '{{"groupType":"HostGroup","groupId":"{group}"}}' """,
                timeout=15
            )
            if rc != 0:
                self.after(0, lambda: self._wol_log(f"[ERROR] {err}", "error"))
                return
            try:
                members = json.loads(out)
                client_ids = [m.get("objectId", "") for m in members if m.get("objectId")]
                if not client_ids:
                    self.after(0, lambda: self._wol_log("No clients in group", "warn"))
                    return

                ids_json = json.dumps(client_ids)
                out2, err2, rc2 = self._ssh_cmd(
                    f"""opsi-admin -d method hostControlSafe_start '{ids_json}'""",
                    timeout=30
                )
                count = len(client_ids)
                self.after(0, lambda: self._wol_log(
                    f"[OK] Wake sent to {count} clients in '{group}'" if rc2 == 0 else f"[ERROR] {err2}",
                    "ok" if rc2 == 0 else "error"
                ))
            except json.JSONDecodeError:
                self.after(0, lambda: self._wol_log("[ERROR] Could not parse group members", "error"))

        threading.Thread(target=do_wake, daemon=True).start()

    def _wol_wake_selected(self):
        selected = self._get_selected_client_ids()
        if not selected:
            self._wol_log("No clients selected", "warn")
            return
        self._wol_log(f"Waking {len(selected)} selected client(s)...", "info")
        ids_json = json.dumps(selected)
        self._ssh_bg(
            f"""opsi-admin -d method hostControlSafe_start '{ids_json}'""",
            lambda out, err, rc: self._wol_log(
                f"[OK] Wake sent to {len(selected)} client(s)" if rc == 0 else f"[ERROR] {err}",
                "ok" if rc == 0 else "error"
            )
        )

    def _wol_wake_single(self):
        mac = self.wol_mac.get_value()
        if not mac:
            self._wol_log("Enter a MAC address", "warn")
            return
        if self._send_wol(mac):
            self._wol_log(f"[OK] Magic packet sent to {mac}", "ok")
        else:
            self._wol_log(f"[ERROR] Failed to send to {mac}", "error")

    def _wol_reboot_selected(self):
        selected = self._get_selected_client_ids()
        if not selected:
            self._wol_log("No clients selected", "warn")
            return
        if not messagebox.askyesno("Confirm", f"Reboot {len(selected)} client(s)?"):
            return
        self._wol_log(f"Rebooting {len(selected)} client(s)...", "info")
        ids_json = json.dumps(selected)
        self._ssh_bg(
            f"""opsi-admin -d method hostControlSafe_reboot '{ids_json}'""",
            lambda out, err, rc: self._wol_log(
                f"[OK] Reboot sent" if rc == 0 else f"[ERROR] {err}",
                "ok" if rc == 0 else "error"
            )
        )

    def _wol_shutdown_selected(self):
        selected = self._get_selected_client_ids()
        if not selected:
            self._wol_log("No clients selected", "warn")
            return
        if not messagebox.askyesno("Confirm", f"Shutdown {len(selected)} client(s)?"):
            return
        self._wol_log(f"Shutting down {len(selected)} client(s)...", "info")
        ids_json = json.dumps(selected)
        self._ssh_bg(
            f"""opsi-admin -d method hostControlSafe_shutdown '{ids_json}'""",
            lambda out, err, rc: self._wol_log(
                f"[OK] Shutdown sent" if rc == 0 else f"[ERROR] {err}",
                "ok" if rc == 0 else "error"
            )
        )

    # ══════════════════════════════════════════════════════════════════════════
    # DIAGNOSTICS ACTIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _diag_log(self, msg, tag=""):
        self._log_to(self.diag_output, msg, tag)

    def _diag_ping(self):
        host = self.diag_host.get_value()
        if not host:
            return
        self.diag_output.delete("1.0", tk.END)
        self._diag_log(f"Pinging {host}...", "info")

        def do_ping():
            try:
                param = "-n" if os.name == "nt" else "-c"
                result = subprocess.run(
                    ["ping", param, "4", host],
                    capture_output=True, text=True, timeout=15,
                    **self._subprocess_kwargs()
                )
                self.after(0, lambda: self._diag_log(result.stdout or ""))
                if result.returncode == 0:
                    self.after(0, lambda: self._diag_log("Host is reachable", "ok"))
                else:
                    self.after(0, lambda: self._diag_log("Host unreachable", "error"))
            except subprocess.TimeoutExpired:
                self.after(0, lambda: self._diag_log("Ping timed out", "error"))
            except Exception as e:
                self.after(0, lambda: self._diag_log(f"Error: {str(e)}", "error"))

        threading.Thread(target=do_ping, daemon=True).start()

    def _diag_ssh(self):
        host = self.diag_host.get_value()
        if not host:
            return
        self.diag_output.delete("1.0", tk.END)
        self._diag_log(f"Testing SSH to {host}...", "info")

        def do_ssh():
            try:
                result = subprocess.run(
                    ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
                     f"root@{host}", "echo 'SSH OK'"],
                    capture_output=True, text=True, timeout=10,
                    **self._subprocess_kwargs()
                )
                if result.returncode == 0:
                    self.after(0, lambda: self._diag_log("SSH connection successful", "ok"))
                else:
                    self.after(0, lambda: self._diag_log(f"SSH failed: {result.stderr}", "error"))
            except Exception as e:
                self.after(0, lambda: self._diag_log(f"Error: {str(e)}", "error"))

        threading.Thread(target=do_ssh, daemon=True).start()

    def _diag_port_check(self):
        host = self.diag_host.get_value()
        if not host:
            return
        self.diag_output.delete("1.0", tk.END)
        self._diag_log(f"Checking ports on {host}...", "info")

        def do_check():
            ports = [(22, "SSH"), (4447, "opsiconfd"), (445, "SMB"), (80, "HTTP"), (443, "HTTPS")]
            for port, name in ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    if result == 0:
                        self.after(0, lambda p=port, n=name: self._diag_log(f"  {n} (:{p}) - OPEN", "ok"))
                    else:
                        self.after(0, lambda p=port, n=name: self._diag_log(f"  {n} (:{p}) - CLOSED", "error"))
                except Exception:
                    self.after(0, lambda p=port, n=name: self._diag_log(f"  {n} (:{p}) - TIMEOUT", "warn"))
            self.after(0, lambda: self._diag_log("Port check complete", "info"))

        threading.Thread(target=do_check, daemon=True).start()

    def _run_health_check(self):
        self.health_output.delete("1.0", tk.END)
        self._log_to(self.health_output, "Running OPSI health check...", "info")

        # Also show diag tab if we're on it
        if "health" in self.diag_tab_frames:
            self._show_diag_tab("health")

        def on_done(out, err, rc):
            if out:
                self._log_to(self.health_output, out, "")
            if err:
                self._log_to(self.health_output, err, "error")
            if rc == 0:
                self._log_to(self.health_output, "\nHealth check complete", "ok")
            else:
                self._log_to(self.health_output, "\nHealth check failed or not available", "error")

        self._ssh_bg("opsi-cli support health-check 2>&1 || opsiconfd diagnostic 2>&1", on_done, timeout=60)

        # Run quick checks in parallel
        self._run_quick_health_checks()

    def _run_quick_health_checks(self):
        # Disk space
        def on_disk(out, err, rc):
            lbl = self.health_check_labels["Disk Space"]
            if rc == 0 and out:
                lbl["value"].configure(text=out.strip())
                pct = int(re.search(r'(\d+)%', out).group(1)) if re.search(r'(\d+)%', out) else 0
                lbl["dot"].configure(fg=SUCCESS if pct < 80 else (WARNING if pct < 90 else ERROR))
            else:
                lbl["value"].configure(text="Error")
                lbl["dot"].configure(fg=ERROR)
        self._ssh_bg("df /var/lib/opsi --output=pcent 2>/dev/null | tail -1", on_disk)

        # Certificate
        def on_cert(out, err, rc):
            lbl = self.health_check_labels["Certificate Expiry"]
            if rc == 0 and out:
                lbl["value"].configure(text=out.replace("notAfter=", "").strip())
                lbl["dot"].configure(fg=SUCCESS)
            else:
                lbl["value"].configure(text="Check failed" if rc != 0 else "N/A")
                lbl["dot"].configure(fg=WARNING)
        self._ssh_bg("openssl s_client -connect localhost:4447 </dev/null 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null", on_cert)

        # NTP
        def on_ntp(out, err, rc):
            lbl = self.health_check_labels["NTP Sync"]
            if rc == 0:
                synced = "yes" in out.lower()
                lbl["value"].configure(text="Synced" if synced else "NOT synced")
                lbl["dot"].configure(fg=SUCCESS if synced else ERROR)
            else:
                lbl["value"].configure(text="Unknown")
                lbl["dot"].configure(fg=WARNING)
        self._ssh_bg("timedatectl show --property=NTPSynchronized --value 2>/dev/null || echo unknown", on_ntp)

        # OPSI version
        def on_ver(out, err, rc):
            lbl = self.health_check_labels["OPSI Version"]
            lbl["value"].configure(text=out.strip() if out else "Unknown")
            lbl["dot"].configure(fg=SUCCESS if out else WARNING)
        self._ssh_bg("opsi-cli --version 2>/dev/null || opsiconfd --version 2>/dev/null", on_ver)

        # paedML version
        def on_paedml(out, err, rc):
            lbl = self.health_check_labels["paedML Version"]
            lbl["value"].configure(text=out.strip() if out else "Not paedML")
            lbl["dot"].configure(fg=SUCCESS if out else TEXT_MUTED)
        self._ssh_bg("cat /etc/paedml-version 2>/dev/null", on_paedml)

    def _check_services(self):
        for svc, dot in self.svc_labels.items():
            dot.configure(fg=TEXT_MUTED)

        for svc in self.svc_labels:
            def on_svc(out, err, rc, s=svc):
                if rc == 0 and "active" in out:
                    self.svc_labels[s].configure(fg=SUCCESS)
                else:
                    self.svc_labels[s].configure(fg=ERROR)
            self._ssh_bg(f"systemctl is-active {svc} 2>/dev/null", on_svc)

    def _check_client(self):
        client = self.diag_client_entry.get_value()
        if not client:
            return
        self.client_output.delete("1.0", tk.END)
        self._log_to(self.client_output, f"Checking client: {client}", "info")

        def do_check():
            # Product status
            out, err, rc = self._ssh_cmd(
                f"""opsi-admin -d -S method productOnClient_getObjects '["productId","installationStatus","actionResult","actionRequest"]' '{{"clientId":"{client}"}}' """,
                timeout=30
            )
            if rc == 0 and out:
                try:
                    products = json.loads(out)
                    self.after(0, lambda: self._log_to(self.client_output, f"\nProducts ({len(products)}):", "info"))
                    for p in products:
                        pid = p.get("productId", "?")
                        status = p.get("installationStatus", "?")
                        result = p.get("actionResult", "")
                        request = p.get("actionRequest", "")
                        tag = "error" if result == "failed" else ("ok" if status == "installed" else "")
                        line = f"  {pid}: {status}"
                        if result:
                            line += f" (result: {result})"
                        if request and request != "none":
                            line += f" [pending: {request}]"
                        self.after(0, lambda l=line, t=tag: self._log_to(self.client_output, l, t))
                except json.JSONDecodeError:
                    self.after(0, lambda o=out: self._log_to(self.client_output, o, ""))
            else:
                self.after(0, lambda: self._log_to(self.client_output, f"Could not fetch products: {err}", "error"))

            # Last seen
            out2, _, rc2 = self._ssh_cmd(
                f"""opsi-admin -d -S method host_getObjects '["id","lastSeen"]' '{{"id":"{client}"}}' """,
                timeout=15
            )
            if rc2 == 0 and out2:
                try:
                    hosts = json.loads(out2)
                    if hosts:
                        last = hosts[0].get("lastSeen", "unknown")
                        self.after(0, lambda l=last: self._log_to(self.client_output, f"\nLast seen: {l}", "info"))
                except json.JSONDecodeError:
                    pass

        threading.Thread(target=do_check, daemon=True).start()

    def _check_failed_all(self):
        self.client_output.delete("1.0", tk.END)
        self._log_to(self.client_output, "Checking for failed installations across all clients...", "info")

        def on_done(out, err, rc):
            if rc == 0 and out:
                try:
                    failed = json.loads(out)
                    if not failed:
                        self._log_to(self.client_output, "\nNo failed installations found!", "ok")
                        return
                    self._log_to(self.client_output, f"\n{len(failed)} failed installation(s):", "error")
                    for f in failed:
                        cid = f.get("clientId", "?")
                        pid = f.get("productId", "?")
                        self._log_to(self.client_output, f"  {cid} - {pid}", "error")
                except json.JSONDecodeError:
                    self._log_to(self.client_output, out, "")
            else:
                self._log_to(self.client_output, f"Error: {err}", "error")

        self._ssh_bg(
            """opsi-admin -d -S method productOnClient_getObjects '["clientId","productId"]' '{"actionResult":"failed"}' 2>/dev/null""",
            on_done, timeout=30
        )

    def _view_client_logs(self):
        client = self.diag_client_entry.get_value()
        if not client:
            return
        self.client_output.delete("1.0", tk.END)
        self._log_to(self.client_output, f"Fetching recent logs for {client}...", "info")

        def on_done(out, err, rc):
            if out:
                self._log_to(self.client_output, out, "")
            else:
                self._log_to(self.client_output, f"No logs found or error: {err}", "warn")

        self._ssh_bg(f"tail -100 /var/log/opsi/instlog/{client}.log 2>/dev/null || echo 'No install log found'", on_done)

    # paedML checks
    def _run_paedml_checks(self):
        self.paedml_output.delete("1.0", tk.END)
        self._log_to(self.paedml_output, "Running paedML diagnostics...", "info")

        for key in self.paedml_checks:
            self.paedml_checks[key]["dot"].configure(text="◌", fg=WARNING)
            self.paedml_checks[key]["detail"].configure(text="Checking...")

        checks = [
            ("time_sync", "timedatectl show --property=NTPSynchronized --value 2>/dev/null",
             lambda o, e, rc: ("yes" in o.lower(), "Synced" if "yes" in o.lower() else "NOT synced")),

            ("disk_var", "df /var --output=pcent 2>/dev/null | tail -1",
             lambda o, e, rc: (int(re.search(r'(\d+)', o).group(1)) < 90 if re.search(r'(\d+)', o) else False,
                              o.strip())),

            ("disk_srv", "df /srv --output=pcent 2>/dev/null | tail -1",
             lambda o, e, rc: (int(re.search(r'(\d+)', o).group(1)) < 90 if re.search(r'(\d+)', o) else False,
                              o.strip())),

            ("cert_opsi", "openssl s_client -connect localhost:4447 </dev/null 2>/dev/null | openssl x509 -checkend 2592000 -noout 2>/dev/null",
             lambda o, e, rc: (rc == 0, "Valid >30d" if rc == 0 else "Expiring soon!")),

            ("dns_forward", "dig @localhost $(hostname -d 2>/dev/null || echo localhost) SOA +short 2>/dev/null | head -1",
             lambda o, e, rc: (bool(o.strip()), o.strip()[:50] if o.strip() else "No result")),

            ("dns_reverse", "dig @localhost -x $(hostname -I 2>/dev/null | awk '{print $1}') +short 2>/dev/null | head -1",
             lambda o, e, rc: (bool(o.strip()), o.strip()[:50] if o.strip() else "No result")),

            ("dhcp_config", "dhcpd -t -cf /etc/dhcp/dhcpd.conf 2>&1 | tail -1",
             lambda o, e, rc: (rc == 0, "Config OK" if rc == 0 else (o + e)[:50])),

            ("samba_ad", "samba-tool domain level show 2>&1 | head -1",
             lambda o, e, rc: (rc == 0 and "error" not in o.lower(), o.strip()[:50] if rc == 0 else "Error")),

            ("domain_join", "net ads testjoin 2>&1",
             lambda o, e, rc: ("ok" in (o + e).lower(), (o + e).strip()[:50])),

            ("sophomorix", "sophomorix-check 2>&1 | tail -3",
             lambda o, e, rc: (rc == 0 and "error" not in o.lower(), "OK" if rc == 0 and "error" not in o.lower() else (o + e).strip()[:50])),
        ]

        for key, cmd, evaluator in checks:
            def on_result(out, err, rc, k=key, ev=evaluator):
                try:
                    passed, detail = ev(out, err, rc)
                except Exception:
                    passed, detail = False, "Parse error"
                self.paedml_checks[k]["dot"].configure(
                    text="●", fg=SUCCESS if passed else ERROR)
                self.paedml_checks[k]["detail"].configure(
                    text=str(detail), fg=SUCCESS if passed else ERROR)
                status = "PASS" if passed else "FAIL"
                tag = "ok" if passed else "error"
                self._log_to(self.paedml_output, f"[{status}] {k}: {detail}", tag)

            self._ssh_bg(cmd, on_result)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = OPSIToolbox()
    app.mainloop()
