#!/usr/bin/env python3
"""
OPSI Toolbox - Modern Admin Suite
Clean, minimal UI for OPSI administration
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
ACCENT = "#3b82f6"  # Modern blue
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
        r = 6  # Corner radius
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
        self.geometry("1100x750")
        self.configure(bg=BG)
        self.minsize(900, 600)

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1100) // 2
        y = (self.winfo_screenheight() - 750) // 2
        self.geometry(f"1100x750+{x}+{y}")

        # Data
        self.selected_files = []
        self.installer_type = tk.StringVar(value="exe")
        self.clients = []  # For WoL

        # Build UI
        self._build_layout()
        self._show_page("dashboard")

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

        # Divider
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=16)

        # Navigation
        nav = tk.Frame(self.sidebar, bg=SIDEBAR)
        nav.pack(fill="x", pady=20)

        self.nav_buttons = {}

        pages = [
            ("dashboard", "Dashboard", "◎"),
            ("packforge", "PackForge", "◫"),
            ("wakeonlan", "Wake on LAN", "⏻"),
            ("debug", "Diagnostics", "⚙"),
        ]

        for key, text, icon in pages:
            btn = SidebarButton(nav, text=text, icon=icon,
                               command=lambda k=key: self._show_page(k))
            btn.pack(fill="x")
            self.nav_buttons[key] = btn

        # Version at bottom
        tk.Label(self.sidebar, text="v2.0", font=(FONT, 9),
                bg=SIDEBAR, fg=TEXT_MUTED).pack(side="bottom", pady=16)

        # Main content area
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="right", fill="both", expand=True)

        # Create all pages
        self.pages = {}
        self._create_dashboard()
        self._create_packforge()
        self._create_wakeonlan()
        self._create_debug()

    def _show_page(self, page_name):
        # Hide all pages
        for page in self.pages.values():
            page.pack_forget()

        # Deactivate all nav buttons
        for btn in self.nav_buttons.values():
            btn.set_active(False)

        # Show selected page
        self.pages[page_name].pack(fill="both", expand=True)
        self.nav_buttons[page_name].set_active(True)

    # ══════════════════════════════════════════════════════════════════════════
    # DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════

    def _create_dashboard(self):
        page = tk.Frame(self.content, bg=BG)
        self.pages["dashboard"] = page

        # Header
        header = tk.Frame(page, bg=BG)
        header.pack(fill="x", padx=32, pady=(32, 24))
        tk.Label(header, text="Dashboard", font=(FONT, 24, "bold"),
                bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(header, text="Quick access to OPSI administration tools",
                font=(FONT, 12), bg=BG, fg=TEXT_SECONDARY).pack(anchor="w", pady=(4, 0))

        # Cards grid
        grid = tk.Frame(page, bg=BG)
        grid.pack(fill="both", expand=True, padx=32)

        cards = [
            ("PackForge", "Create OPSI packages from installers", "◫", "packforge"),
            ("Wake on LAN", "Wake up clients remotely", "⏻", "wakeonlan"),
            ("Diagnostics", "Debug client connections", "⚙", "debug"),
        ]

        for i, (title, desc, icon, target) in enumerate(cards):
            card = tk.Frame(grid, bg=CARD, cursor="hand2")
            card.grid(row=i//3, column=i%3, padx=8, pady=8, sticky="nsew")

            inner = tk.Frame(card, bg=CARD)
            inner.pack(fill="both", expand=True, padx=24, pady=24)

            tk.Label(inner, text=icon, font=(FONT, 32),
                    bg=CARD, fg=ACCENT).pack(anchor="w")
            tk.Label(inner, text=title, font=(FONT, 14, "bold"),
                    bg=CARD, fg=TEXT).pack(anchor="w", pady=(12, 4))
            tk.Label(inner, text=desc, font=(FONT, 10),
                    bg=CARD, fg=TEXT_SECONDARY, wraplength=200,
                    justify="left").pack(anchor="w")

            for widget in [card, inner] + inner.winfo_children():
                widget.bind("<Button-1>", lambda _, t=target: self._show_page(t))
                widget.bind("<Enter>", lambda _, c=card: c.configure(bg=CARD_HOVER))
                widget.bind("<Leave>", lambda _, c=card: c.configure(bg=CARD))

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)

    # ══════════════════════════════════════════════════════════════════════════
    # PACKFORGE
    # ══════════════════════════════════════════════════════════════════════════

    def _create_packforge(self):
        page = tk.Frame(self.content, bg=BG)
        self.pages["packforge"] = page

        # Header
        header = tk.Frame(page, bg=BG)
        header.pack(fill="x", padx=32, pady=(32, 24))
        tk.Label(header, text="PackForge", font=(FONT, 24, "bold"),
                bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(header, text="Create OPSI packages from Windows installers",
                font=(FONT, 12), bg=BG, fg=TEXT_SECONDARY).pack(anchor="w", pady=(4, 0))

        # Main container with scroll
        container = tk.Frame(page, bg=BG)
        container.pack(fill="both", expand=True, padx=32)

        # Left column - Form
        left = tk.Frame(container, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 16))

        # Package Info Card
        card1 = self._create_card(left, "Package Info")

        form = tk.Frame(card1, bg=CARD)
        form.pack(fill="x", padx=20, pady=(0, 20))

        # Row 1
        row1 = tk.Frame(form, bg=CARD)
        row1.pack(fill="x", pady=4)

        self._add_form_field(row1, "Package ID", "pkg_id", "firefox", side="left", width=20)
        self._add_form_field(row1, "Version", "pkg_version", "1.0.0", side="left", width=15)

        # Row 2
        row2 = tk.Frame(form, bg=CARD)
        row2.pack(fill="x", pady=4)

        self._add_form_field(row2, "Product Name", "pkg_name", "Mozilla Firefox", side="left", width=30)

        # Row 3 - Description
        tk.Label(form, text="Description", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w", pady=(8, 4))
        self.pkg_desc = tk.Text(form, bg=BG_SECONDARY, fg=TEXT, font=(FONT, 11),
                               relief="flat", height=2, insertbackground=ACCENT,
                               highlightthickness=1, highlightbackground=BORDER,
                               highlightcolor=ACCENT)
        self.pkg_desc.pack(fill="x")

        # Files Card
        card2 = self._create_card(left, "Installer Files")

        files_inner = tk.Frame(card2, bg=CARD)
        files_inner.pack(fill="x", padx=20, pady=(0, 20))

        # Installer type
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

        # Silent params
        params_frame = tk.Frame(files_inner, bg=CARD)
        params_frame.pack(fill="x", pady=(0, 12))
        tk.Label(params_frame, text="Silent Parameters:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(side="left")
        self.params_entry = ModernEntry(params_frame, width=40)
        self.params_entry.pack(side="left", padx=(12, 0))
        self._on_type_change()

        # File list
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

        # Right column - Deploy
        right = tk.Frame(container, bg=BG, width=280)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        # Deploy Card
        card3 = self._create_card(right, "Deploy")

        deploy_inner = tk.Frame(card3, bg=CARD)
        deploy_inner.pack(fill="x", padx=20, pady=(0, 20))

        self._add_form_field(deploy_inner, "OPSI Server", "deploy_server", "10.1.0.2")
        self._add_form_field(deploy_inner, "SSH User", "deploy_user", "root")

        tk.Label(deploy_inner, text="If package exists:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w", pady=(12, 4))
        self.overwrite_var = tk.StringVar(value="Overwrite")
        overwrite_menu = tk.OptionMenu(deploy_inner, self.overwrite_var,
                                       "Overwrite", "New version", "Abort")
        overwrite_menu.config(bg=CARD, fg=TEXT, font=(FONT, 10),
                             activebackground=ACCENT, activeforeground=BG,
                             highlightthickness=0, bd=0, relief="flat")
        overwrite_menu["menu"].config(bg=CARD, fg=TEXT, font=(FONT, 10),
                                      activebackground=ACCENT, activeforeground=BG)
        overwrite_menu.pack(fill="x")

        tk.Label(deploy_inner, text="Output:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w", pady=(12, 4))
        self.output_entry = ModernEntry(deploy_inner)
        self.output_entry.insert(0, str(Path.home() / "Desktop"))
        self.output_entry.pack(fill="x")

        # Build buttons
        btn_frame = tk.Frame(deploy_inner, bg=CARD)
        btn_frame.pack(fill="x", pady=(16, 0))

        ModernButton(btn_frame, text="Build ZIP", command=self._build_package,
                    width=110).pack(side="left")
        ModernButton(btn_frame, text="Deploy", command=self._build_and_deploy,
                    primary=True, width=110).pack(side="left", padx=(8, 0))

        # Log Card
        card4 = self._create_card(right, "Build Log", expand=True)

        log_frame = tk.Frame(card4, bg=CARD)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.log_text = scrolledtext.ScrolledText(log_frame, bg=BG_SECONDARY, fg=TEXT,
                                                  font=(FONT_MONO, 9), relief="flat",
                                                  highlightthickness=0, height=10)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_config("ok", foreground=SUCCESS)
        self.log_text.tag_config("error", foreground=ERROR)
        self.log_text.tag_config("warn", foreground=WARNING)
        self.log_text.tag_config("info", foreground=ACCENT)

    # ══════════════════════════════════════════════════════════════════════════
    # WAKE ON LAN
    # ══════════════════════════════════════════════════════════════════════════

    def _create_wakeonlan(self):
        page = tk.Frame(self.content, bg=BG)
        self.pages["wakeonlan"] = page

        # Header
        header = tk.Frame(page, bg=BG)
        header.pack(fill="x", padx=32, pady=(32, 24))
        tk.Label(header, text="Wake on LAN", font=(FONT, 24, "bold"),
                bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(header, text="Send magic packets to wake up clients",
                font=(FONT, 12), bg=BG, fg=TEXT_SECONDARY).pack(anchor="w", pady=(4, 0))

        container = tk.Frame(page, bg=BG)
        container.pack(fill="both", expand=True, padx=32)

        # Single MAC
        card1 = self._create_card(container, "Wake Single Client")

        inner1 = tk.Frame(card1, bg=CARD)
        inner1.pack(fill="x", padx=20, pady=(0, 20))

        row = tk.Frame(inner1, bg=CARD)
        row.pack(fill="x")

        tk.Label(row, text="MAC Address:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(side="left")
        self.wol_mac = ModernEntry(row, placeholder="AA:BB:CC:DD:EE:FF", width=25)
        self.wol_mac.pack(side="left", padx=(12, 0))

        ModernButton(row, text="Wake", command=self._wake_single,
                    primary=True, width=80).pack(side="left", padx=(12, 0))

        self.wol_status = tk.Label(inner1, text="", font=(FONT, 10),
                                   bg=CARD, fg=TEXT_SECONDARY)
        self.wol_status.pack(anchor="w", pady=(12, 0))

        # Bulk wake
        card2 = self._create_card(container, "Wake Multiple Clients")

        inner2 = tk.Frame(card2, bg=CARD)
        inner2.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tk.Label(inner2, text="Enter MAC addresses (one per line):",
                font=(FONT, 10), bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w")

        self.wol_bulk = tk.Text(inner2, bg=BG_SECONDARY, fg=TEXT,
                               font=(FONT_MONO, 11), relief="flat", height=8,
                               insertbackground=ACCENT, highlightthickness=1,
                               highlightbackground=BORDER, highlightcolor=ACCENT)
        self.wol_bulk.pack(fill="both", expand=True, pady=(8, 12))

        ModernButton(inner2, text="Wake All", command=self._wake_bulk,
                    primary=True, width=100).pack(anchor="w")

    # ══════════════════════════════════════════════════════════════════════════
    # DIAGNOSTICS
    # ══════════════════════════════════════════════════════════════════════════

    def _create_debug(self):
        page = tk.Frame(self.content, bg=BG)
        self.pages["debug"] = page

        # Header
        header = tk.Frame(page, bg=BG)
        header.pack(fill="x", padx=32, pady=(32, 24))
        tk.Label(header, text="Diagnostics", font=(FONT, 24, "bold"),
                bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(header, text="Debug and test OPSI client connections",
                font=(FONT, 12), bg=BG, fg=TEXT_SECONDARY).pack(anchor="w", pady=(4, 0))

        container = tk.Frame(page, bg=BG)
        container.pack(fill="both", expand=True, padx=32)

        # Ping test
        card1 = self._create_card(container, "Connection Test")

        inner1 = tk.Frame(card1, bg=CARD)
        inner1.pack(fill="x", padx=20, pady=(0, 20))

        row = tk.Frame(inner1, bg=CARD)
        row.pack(fill="x")

        tk.Label(row, text="Host:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(side="left")
        self.ping_host = ModernEntry(row, placeholder="10.1.0.1 or hostname", width=30)
        self.ping_host.pack(side="left", padx=(12, 0))

        ModernButton(row, text="Ping", command=self._ping_host,
                    primary=True, width=80).pack(side="left", padx=(12, 0))
        ModernButton(row, text="SSH Test", command=self._ssh_test,
                    width=90).pack(side="left", padx=(8, 0))

        # OPSI commands
        card2 = self._create_card(container, "OPSI Server Commands")

        inner2 = tk.Frame(card2, bg=CARD)
        inner2.pack(fill="x", padx=20, pady=(0, 20))

        row2 = tk.Frame(inner2, bg=CARD)
        row2.pack(fill="x")

        tk.Label(row2, text="Server:", font=(FONT, 10),
                bg=CARD, fg=TEXT_SECONDARY).pack(side="left")
        self.cmd_server = ModernEntry(row2, placeholder="10.1.0.2", width=20)
        self.cmd_server.pack(side="left", padx=(12, 0))

        # Quick commands
        btn_row = tk.Frame(inner2, bg=CARD)
        btn_row.pack(fill="x", pady=(12, 0))

        commands = [
            ("List Packages", "opsi-package-manager -l"),
            ("List Clients", "opsi-admin -d method host_getObjects"),
            ("Service Status", "systemctl status opsiconfd"),
        ]

        for name, cmd in commands:
            ModernButton(btn_row, text=name, width=120,
                        command=lambda c=cmd: self._run_opsi_cmd(c)).pack(side="left", padx=(0, 8))

        # Output
        card3 = self._create_card(container, "Output", expand=True)

        inner3 = tk.Frame(card3, bg=CARD)
        inner3.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.debug_output = scrolledtext.ScrolledText(inner3, bg=BG_SECONDARY, fg=TEXT,
                                                      font=(FONT_MONO, 10), relief="flat",
                                                      highlightthickness=0)
        self.debug_output.pack(fill="both", expand=True)
        self.debug_output.tag_config("ok", foreground=SUCCESS)
        self.debug_output.tag_config("error", foreground=ERROR)

    # ══════════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ══════════════════════════════════════════════════════════════════════════

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

    def _on_type_change(self):
        itype = self.installer_type.get()
        params = self.INSTALLER_TYPES[itype]["params"]
        self.params_entry.delete(0, tk.END)
        if params:
            self.params_entry.insert(0, params)

    def _log(self, msg, tag=""):
        self.log_text.insert(tk.END, msg + "\n", tag)
        self.log_text.see(tk.END)
        self.update_idletasks()

    def _debug_log(self, msg, tag=""):
        self.debug_output.insert(tk.END, msg + "\n", tag)
        self.debug_output.see(tk.END)
        self.update_idletasks()

    def _get_text(self, widget):
        if isinstance(widget, tk.Text):
            return widget.get("1.0", tk.END).strip()
        elif isinstance(widget, ModernEntry):
            return widget.get_value()
        return widget.get().strip()

    # ══════════════════════════════════════════════════════════════════════════
    # PACKFORGE ACTIONS
    # ══════════════════════════════════════════════════════════════════════════

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
                    f"Winbatch_install_{i}",
                    "Sub_check_exitcode",
                    "",
                    f"[Winbatch_install_{i}]",
                    f'msiexec /i "$SetupFile$" {params}',
                    ""
                ])
            elif itype == "ps1":
                lines.extend([
                    f"DosInAnIcon_install_{i}",
                    "Sub_check_exitcode",
                    "",
                    f"[DosInAnIcon_install_{i}]",
                    f'powershell.exe -ExecutionPolicy Bypass -File "$SetupFile$"',
                    ""
                ])
            elif itype == "bat":
                lines.extend([
                    f"DosInAnIcon_install_{i}",
                    "Sub_check_exitcode",
                    "",
                    f"[DosInAnIcon_install_{i}]",
                    f'cmd.exe /c "$SetupFile$"',
                    ""
                ])
            else:
                lines.extend([
                    f"Winbatch_install_{i}",
                    "Sub_check_exitcode",
                    "",
                    f"[Winbatch_install_{i}]",
                    f'"$SetupFile$" {params}' if params else '"$SetupFile$"',
                    ""
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

    def _build_package(self):
        if not self._validate():
            return

        self.log_text.delete("1.0", tk.END)
        self._log("Starting build...", "info")

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
            self._log(f"Creating: {pkg_folder}")
            os.makedirs(os.path.join(pkg_path, "OPSI"), exist_ok=True)
            os.makedirs(os.path.join(pkg_path, "CLIENT_DATA", "files"), exist_ok=True)

            # Control
            with open(os.path.join(pkg_path, "OPSI", "control"), "w", encoding="utf-8") as f:
                f.write(self._generate_control(data))
            self._log("[OK] control", "ok")

            # Setup
            with open(os.path.join(pkg_path, "CLIENT_DATA", "setup.opsiscript"), "w", encoding="utf-8") as f:
                f.write(self._generate_setup(data, self.selected_files))
            self._log("[OK] setup.opsiscript", "ok")

            # Uninstall
            with open(os.path.join(pkg_path, "CLIENT_DATA", "uninstall.opsiscript"), "w", encoding="utf-8") as f:
                f.write(self._generate_uninstall(data))
            self._log("[OK] uninstall.opsiscript", "ok")

            # Copy files
            for f in self.selected_files:
                fname = os.path.basename(f)
                shutil.copy2(f, os.path.join(pkg_path, "CLIENT_DATA", "files", fname))
                self._log(f"[OK] {fname}", "ok")

            # ZIP
            zip_path = os.path.join(output_base, f"{pkg_folder}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(pkg_path):
                    for file in files:
                        fp = os.path.join(root, file)
                        zf.write(fp, os.path.relpath(fp, output_base))

            self._log("")
            self._log("BUILD SUCCESSFUL!", "ok")
            self._log(f"Package: {zip_path}", "info")

        except Exception as e:
            self._log(f"[ERROR] {str(e)}", "error")

    def _build_and_deploy(self):
        self._build_package()

        server = self._get_text(self.deploy_server) or "10.1.0.2"
        user = self._get_text(self.deploy_user) or "root"

        data = {
            "id": self._get_text(self.pkg_id),
            "version": self._get_text(self.pkg_version) or "1.0.0",
        }
        pkg_folder = f"{data['id']}_{data['version']}-1"
        pkg_path = os.path.join(self.output_entry.get(), pkg_folder)

        self._log("")
        self._log(f"DEPLOYING TO {server}...", "info")

        try:
            # SCP
            result = subprocess.run(
                ["scp", "-r", pkg_path, f"{user}@{server}:/var/lib/opsi/workbench/"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"SCP failed: {result.stderr}")
            self._log("[OK] Files copied", "ok")

            # Make package
            overwrite_choice = self.overwrite_var.get()
            if overwrite_choice == "Overwrite":
                makepackage_cmd = f"cd /var/lib/opsi/workbench && opsi-makepackage --keep-versions {pkg_folder}"
            elif overwrite_choice == "New version":
                # Find current highest package-version on server and increment
                find_cmd = f"ls /var/lib/opsi/workbench/{data['id']}_{data['version']}-*.opsi 2>/dev/null | sort -V | tail -1"
                find_result = subprocess.run(
                    ["ssh", f"{user}@{server}", find_cmd],
                    capture_output=True, text=True
                )
                release = 2
                if find_result.stdout.strip():
                    try:
                        existing = find_result.stdout.strip().rsplit("-", 1)[-1].split(".opsi")[0]
                        release = int(existing) + 1
                    except (ValueError, IndexError):
                        pass
                makepackage_cmd = f"cd /var/lib/opsi/workbench && opsi-makepackage --product-version {data['version']} --package-version {release} {pkg_folder}"
            else:
                # Check if package exists first, abort if it does
                check_cmd = f"ls /var/lib/opsi/workbench/{pkg_folder}-*.opsi 2>/dev/null"
                check = subprocess.run(
                    ["ssh", f"{user}@{server}", check_cmd],
                    capture_output=True, text=True
                )
                if check.stdout.strip():
                    self._log("[ABORTED] Package already exists on server", "warning")
                    return
                makepackage_cmd = f"cd /var/lib/opsi/workbench && opsi-makepackage {pkg_folder}"

            result = subprocess.run(
                ["ssh", f"{user}@{server}", makepackage_cmd],
                capture_output=True, text=True
            )
            self._log(result.stdout, "")
            if result.returncode != 0:
                self._log(f"[ERROR] {result.stderr}", "error")
                return

            # Install
            result = subprocess.run(
                ["ssh", f"{user}@{server}",
                 f"opsi-package-manager -i /var/lib/opsi/workbench/{pkg_folder}-*.opsi"],
                capture_output=True, text=True
            )
            self._log(result.stdout, "")
            if result.returncode != 0:
                self._log(f"[ERROR] {result.stderr}", "error")
                return

            self._log("")
            self._log("DEPLOYMENT COMPLETE!", "ok")

        except Exception as e:
            self._log(f"[ERROR] {str(e)}", "error")

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

    def _wake_single(self):
        mac = self.wol_mac.get_value()
        if not mac:
            self.wol_status.configure(text="Enter a MAC address", fg=ERROR)
            return

        if self._send_wol(mac):
            self.wol_status.configure(text=f"Magic packet sent to {mac}", fg=SUCCESS)
        else:
            self.wol_status.configure(text="Failed to send packet", fg=ERROR)

    def _wake_bulk(self):
        macs = self.wol_bulk.get("1.0", tk.END).strip().split("\n")
        macs = [m.strip() for m in macs if m.strip()]

        sent = 0
        for mac in macs:
            if self._send_wol(mac):
                sent += 1

        self.wol_status.configure(text=f"Sent {sent}/{len(macs)} packets",
                                  fg=SUCCESS if sent == len(macs) else WARNING)

    # ══════════════════════════════════════════════════════════════════════════
    # DIAGNOSTICS ACTIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _ping_host(self):
        host = self.ping_host.get_value()
        if not host:
            return

        self.debug_output.delete("1.0", tk.END)
        self._debug_log(f"Pinging {host}...", "info")

        def do_ping():
            try:
                param = "-n" if os.name == "nt" else "-c"
                result = subprocess.run(
                    ["ping", param, "4", host],
                    capture_output=True, text=True, timeout=10
                )
                self._debug_log(result.stdout)
                if result.returncode == 0:
                    self._debug_log("Host is reachable", "ok")
                else:
                    self._debug_log("Host unreachable", "error")
            except Exception as e:
                self._debug_log(f"Error: {str(e)}", "error")

        threading.Thread(target=do_ping, daemon=True).start()

    def _ssh_test(self):
        host = self.ping_host.get_value()
        if not host:
            return

        self.debug_output.delete("1.0", tk.END)
        self._debug_log(f"Testing SSH to {host}...", "info")

        def do_ssh():
            try:
                result = subprocess.run(
                    ["ssh", "-o", "ConnectTimeout=5", f"root@{host}", "echo 'SSH OK'"],
                    capture_output=True, text=True, timeout=10
                )
                self._debug_log(result.stdout)
                if result.returncode == 0:
                    self._debug_log("SSH connection successful", "ok")
                else:
                    self._debug_log(f"SSH failed: {result.stderr}", "error")
            except Exception as e:
                self._debug_log(f"Error: {str(e)}", "error")

        threading.Thread(target=do_ssh, daemon=True).start()

    def _run_opsi_cmd(self, cmd):
        server = self.cmd_server.get_value() or "10.1.0.2"

        self.debug_output.delete("1.0", tk.END)
        self._debug_log(f"Running: {cmd}", "info")
        self._debug_log("")

        def do_cmd():
            try:
                result = subprocess.run(
                    ["ssh", f"root@{server}", cmd],
                    capture_output=True, text=True, timeout=30
                )
                self._debug_log(result.stdout)
                if result.stderr:
                    self._debug_log(result.stderr, "error")
            except Exception as e:
                self._debug_log(f"Error: {str(e)}", "error")

        threading.Thread(target=do_cmd, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = OPSIToolbox()
    app.mainloop()
