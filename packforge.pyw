#!/usr/bin/env python3
"""
OPSI PackForge - GUI Package Builder
Modern tkinter-based OPSI package creation tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import zipfile
import shutil
import subprocess
import threading
import re
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# THEME / COLORS
# ══════════════════════════════════════════════════════════════════════════════
BG = "#0d0d0d"
BG_LIGHT = "#141414"
CARD = "#1a1a1a"
BORDER = "#2a2a2a"
ACCENT = "#00d4ff"
ACCENT_DARK = "#0099bb"
SUCCESS = "#00ff88"
WARNING = "#ffaa00"
ERROR = "#ff4444"
TEXT = "#e8e8e8"
TEXT_DIM = "#666666"
TEXT_MID = "#999999"


class ModernEntry(tk.Entry):
    """Custom styled entry widget"""
    def __init__(self, parent, placeholder="", **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = TEXT_DIM
        self.default_fg = kwargs.get('fg', TEXT)

        self.configure(
            bg=CARD,
            fg=TEXT,
            insertbackground=ACCENT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            font=("Consolas", 10)
        )

        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

        if placeholder:
            self._show_placeholder()

    def _show_placeholder(self):
        self.delete(0, tk.END)
        self.insert(0, self.placeholder)
        self.configure(fg=self.placeholder_color)

    def _on_focus_in(self, event):
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.configure(fg=self.default_fg)

    def _on_focus_out(self, event):
        if not self.get():
            self._show_placeholder()

    def get_value(self):
        val = self.get()
        return "" if val == self.placeholder else val


class ModernButton(tk.Button):
    """Custom styled button widget"""
    def __init__(self, parent, primary=False, **kwargs):
        super().__init__(parent, **kwargs)

        bg_color = ACCENT if primary else CARD
        fg_color = BG if primary else TEXT
        hover_bg = ACCENT_DARK if primary else BORDER

        self.configure(
            bg=bg_color,
            fg=fg_color,
            activebackground=hover_bg,
            activeforeground=fg_color,
            relief="flat",
            cursor="hand2",
            font=("Consolas", 10, "bold"),
            padx=16,
            pady=8
        )

        self.bind("<Enter>", lambda e: self.configure(bg=hover_bg))
        self.bind("<Leave>", lambda e: self.configure(bg=bg_color))


class PackForgeApp(tk.Tk):
    """Main application window"""

    INSTALLER_TYPES = {
        "msi": {"name": "MSI (msiexec)", "params": "/qn /norestart", "method": "msi"},
        "inno": {"name": "InnoSetup", "params": "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART", "method": "exe"},
        "nsis": {"name": "NSIS", "params": "/S", "method": "exe"},
        "installshield": {"name": "InstallShield", "params": "/s /sms", "method": "exe"},
        "exe": {"name": "Generic EXE", "params": "/silent", "method": "exe"},
        "ps1": {"name": "PowerShell", "params": "-ExecutionPolicy Bypass -File", "method": "shell"},
        "bat": {"name": "Batch", "params": "", "method": "shell"},
    }

    def __init__(self):
        super().__init__()

        self.title("OPSI PackForge")
        self.geometry("900x700")
        self.configure(bg=BG)
        self.minsize(800, 600)

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 900) // 2
        y = (self.winfo_screenheight() - 700) // 2
        self.geometry(f"900x700+{x}+{y}")

        # Data
        self.selected_files = []
        self.dependencies = []
        self.properties = []
        self.current_installer_type = tk.StringVar(value="exe")

        # Build UI
        self._create_styles()
        self._build_ui()

    def _create_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=CARD,
                        foreground=TEXT_DIM,
                        padding=[16, 8],
                        font=("Consolas", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", BG_LIGHT)],
                  foreground=[("selected", ACCENT)])

        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD)

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG_LIGHT, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="OPSI PackForge", font=("Consolas", 18, "bold"),
                 bg=BG_LIGHT, fg=ACCENT).pack(side="left", padx=20, pady=15)

        tk.Label(header, text="v2.0", font=("Consolas", 10),
                 bg=BG_LIGHT, fg=TEXT_DIM).pack(side="right", padx=20)

        # Accent line
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

        # Notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: Package Info
        self.tab_info = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_info, text="  Package Info  ")
        self._build_info_tab()

        # Tab 2: Files
        self.tab_files = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_files, text="  Files  ")
        self._build_files_tab()

        # Tab 3: Dependencies
        self.tab_deps = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_deps, text="  Dependencies  ")
        self._build_deps_tab()

        # Tab 4: Properties
        self.tab_props = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_props, text="  Properties  ")
        self._build_props_tab()

        # Tab 5: Build & Deploy
        self.tab_build = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_build, text="  Build & Deploy  ")
        self._build_build_tab()

    def _build_info_tab(self):
        container = tk.Frame(self.tab_info, bg=BG)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Left column
        left = tk.Frame(container, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self._add_field(left, "Package ID", "pkg_id", "z.B. firefox")
        self._add_field(left, "Product Name", "pkg_name", "z.B. Mozilla Firefox")
        self._add_field(left, "Version", "pkg_version", "1.0.0")
        self._add_field(left, "Package Version", "pkg_release", "1")
        self._add_field(left, "Priority", "pkg_priority", "0")

        # Right column
        right = tk.Frame(container, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self._add_field(right, "Description", "pkg_desc", "Software installation", multiline=True)
        self._add_field(right, "Advice/Notes", "pkg_advice", "Optional notes", multiline=True)

        # License checkbox
        self.license_required = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(right, text="License Required",
                           variable=self.license_required,
                           bg=BG, fg=TEXT, selectcolor=CARD,
                           activebackground=BG, activeforeground=TEXT,
                           font=("Consolas", 10))
        cb.pack(anchor="w", pady=10)

    def _build_files_tab(self):
        container = tk.Frame(self.tab_files, bg=BG)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Installer type selection
        type_frame = tk.Frame(container, bg=BG)
        type_frame.pack(fill="x", pady=(0, 15))

        tk.Label(type_frame, text="Installer Type:", font=("Consolas", 10, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")

        btn_frame = tk.Frame(type_frame, bg=BG)
        btn_frame.pack(fill="x", pady=5)

        for key, info in self.INSTALLER_TYPES.items():
            rb = tk.Radiobutton(btn_frame, text=info["name"],
                               variable=self.current_installer_type, value=key,
                               bg=BG, fg=TEXT, selectcolor=CARD,
                               activebackground=BG, activeforeground=ACCENT,
                               font=("Consolas", 9),
                               command=self._on_installer_type_change)
            rb.pack(side="left", padx=(0, 15))

        # Silent parameters
        params_frame = tk.Frame(container, bg=BG)
        params_frame.pack(fill="x", pady=(0, 15))

        tk.Label(params_frame, text="Silent Parameters:", font=("Consolas", 10),
                 bg=BG, fg=TEXT).pack(anchor="w")
        self.params_entry = ModernEntry(params_frame, width=60)
        self.params_entry.pack(fill="x", pady=5)
        self._on_installer_type_change()

        # File selection
        file_frame = tk.Frame(container, bg=CARD, highlightbackground=BORDER,
                             highlightthickness=1)
        file_frame.pack(fill="both", expand=True)

        # Dropzone
        self.dropzone = tk.Frame(file_frame, bg=CARD, height=150)
        self.dropzone.pack(fill="x", padx=20, pady=20)

        tk.Label(self.dropzone, text="Drop files here or click to browse",
                 font=("Consolas", 12), bg=CARD, fg=TEXT_DIM).pack(expand=True)

        ModernButton(self.dropzone, text="Browse Files", primary=True,
                    command=self._browse_files).pack(pady=10)

        # File list
        self.file_listbox = tk.Listbox(file_frame, bg=CARD, fg=TEXT,
                                       selectbackground=ACCENT,
                                       selectforeground=BG,
                                       font=("Consolas", 10),
                                       relief="flat", highlightthickness=0)
        self.file_listbox.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Remove button
        btn_frame2 = tk.Frame(file_frame, bg=CARD)
        btn_frame2.pack(fill="x", padx=20, pady=(0, 20))
        ModernButton(btn_frame2, text="Remove Selected",
                    command=self._remove_file).pack(side="right")

    def _build_deps_tab(self):
        container = tk.Frame(self.tab_deps, bg=BG)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Add dependency form
        form = tk.Frame(container, bg=CARD, highlightbackground=BORDER,
                       highlightthickness=1)
        form.pack(fill="x", pady=(0, 15))

        inner = tk.Frame(form, bg=CARD)
        inner.pack(fill="x", padx=15, pady=15)

        tk.Label(inner, text="Add Dependency", font=("Consolas", 12, "bold"),
                 bg=CARD, fg=ACCENT).pack(anchor="w", pady=(0, 10))

        row = tk.Frame(inner, bg=CARD)
        row.pack(fill="x")

        tk.Label(row, text="Product ID:", bg=CARD, fg=TEXT,
                 font=("Consolas", 10)).pack(side="left")
        self.dep_product = ModernEntry(row, width=20)
        self.dep_product.pack(side="left", padx=10)

        tk.Label(row, text="Action:", bg=CARD, fg=TEXT,
                 font=("Consolas", 10)).pack(side="left")
        self.dep_action = ttk.Combobox(row, values=["setup", "uninstall"], width=10)
        self.dep_action.set("setup")
        self.dep_action.pack(side="left", padx=10)

        tk.Label(row, text="Type:", bg=CARD, fg=TEXT,
                 font=("Consolas", 10)).pack(side="left")
        self.dep_type = ttk.Combobox(row, values=["before", "after"], width=10)
        self.dep_type.set("before")
        self.dep_type.pack(side="left", padx=10)

        ModernButton(row, text="Add", primary=True,
                    command=self._add_dependency).pack(side="right")

        # Dependencies list
        self.deps_listbox = tk.Listbox(container, bg=CARD, fg=TEXT,
                                       selectbackground=ACCENT,
                                       selectforeground=BG,
                                       font=("Consolas", 10),
                                       relief="flat", highlightthickness=1,
                                       highlightbackground=BORDER,
                                       height=10)
        self.deps_listbox.pack(fill="both", expand=True)

        ModernButton(container, text="Remove Selected",
                    command=self._remove_dependency).pack(anchor="e", pady=10)

    def _build_props_tab(self):
        container = tk.Frame(self.tab_props, bg=BG)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Add property form
        form = tk.Frame(container, bg=CARD, highlightbackground=BORDER,
                       highlightthickness=1)
        form.pack(fill="x", pady=(0, 15))

        inner = tk.Frame(form, bg=CARD)
        inner.pack(fill="x", padx=15, pady=15)

        tk.Label(inner, text="Add Property", font=("Consolas", 12, "bold"),
                 bg=CARD, fg=ACCENT).pack(anchor="w", pady=(0, 10))

        row1 = tk.Frame(inner, bg=CARD)
        row1.pack(fill="x", pady=5)

        tk.Label(row1, text="Name:", bg=CARD, fg=TEXT,
                 font=("Consolas", 10)).pack(side="left")
        self.prop_name = ModernEntry(row1, width=20)
        self.prop_name.pack(side="left", padx=10)

        tk.Label(row1, text="Type:", bg=CARD, fg=TEXT,
                 font=("Consolas", 10)).pack(side="left")
        self.prop_type = ttk.Combobox(row1, values=["unicode", "bool"], width=10)
        self.prop_type.set("unicode")
        self.prop_type.pack(side="left", padx=10)

        row2 = tk.Frame(inner, bg=CARD)
        row2.pack(fill="x", pady=5)

        tk.Label(row2, text="Default:", bg=CARD, fg=TEXT,
                 font=("Consolas", 10)).pack(side="left")
        self.prop_default = ModernEntry(row2, width=20)
        self.prop_default.pack(side="left", padx=10)

        tk.Label(row2, text="Values (comma-sep):", bg=CARD, fg=TEXT,
                 font=("Consolas", 10)).pack(side="left")
        self.prop_values = ModernEntry(row2, width=25)
        self.prop_values.pack(side="left", padx=10)

        ModernButton(row2, text="Add", primary=True,
                    command=self._add_property).pack(side="right")

        # Properties list
        self.props_listbox = tk.Listbox(container, bg=CARD, fg=TEXT,
                                        selectbackground=ACCENT,
                                        selectforeground=BG,
                                        font=("Consolas", 10),
                                        relief="flat", highlightthickness=1,
                                        highlightbackground=BORDER,
                                        height=10)
        self.props_listbox.pack(fill="both", expand=True)

        ModernButton(container, text="Remove Selected",
                    command=self._remove_property).pack(anchor="e", pady=10)

    def _build_build_tab(self):
        container = tk.Frame(self.tab_build, bg=BG)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Output options
        output_frame = tk.Frame(container, bg=CARD, highlightbackground=BORDER,
                               highlightthickness=1)
        output_frame.pack(fill="x", pady=(0, 15))

        inner = tk.Frame(output_frame, bg=CARD)
        inner.pack(fill="x", padx=15, pady=15)

        tk.Label(inner, text="Output Directory:", font=("Consolas", 10),
                 bg=CARD, fg=TEXT).pack(anchor="w")

        row = tk.Frame(inner, bg=CARD)
        row.pack(fill="x", pady=5)

        self.output_dir = ModernEntry(row, width=50)
        self.output_dir.insert(0, str(Path.home() / "Desktop"))
        self.output_dir.pack(side="left", fill="x", expand=True)

        ModernButton(row, text="Browse",
                    command=self._browse_output).pack(side="right", padx=(10, 0))

        # Build buttons
        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(fill="x", pady=15)

        ModernButton(btn_frame, text="Build Package (ZIP)", primary=True,
                    command=self._build_package).pack(side="left", padx=(0, 10))

        ModernButton(btn_frame, text="Build & Deploy to OPSI",
                    command=self._build_and_deploy).pack(side="left")

        # Log output
        tk.Label(container, text="Build Log:", font=("Consolas", 10, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w", pady=(10, 5))

        self.log_text = scrolledtext.ScrolledText(container, bg=CARD, fg=TEXT,
                                                  font=("Consolas", 9),
                                                  relief="flat",
                                                  highlightthickness=1,
                                                  highlightbackground=BORDER,
                                                  height=15)
        self.log_text.pack(fill="both", expand=True)

        # Configure log tags
        self.log_text.tag_config("ok", foreground=SUCCESS)
        self.log_text.tag_config("error", foreground=ERROR)
        self.log_text.tag_config("warn", foreground=WARNING)
        self.log_text.tag_config("info", foreground=ACCENT)

    # ══════════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ══════════════════════════════════════════════════════════════════════════

    def _add_field(self, parent, label, attr, placeholder="", multiline=False):
        tk.Label(parent, text=label, font=("Consolas", 10),
                 bg=BG, fg=TEXT).pack(anchor="w", pady=(10, 2))

        if multiline:
            widget = tk.Text(parent, bg=CARD, fg=TEXT, font=("Consolas", 10),
                            relief="flat", highlightthickness=1,
                            highlightbackground=BORDER, highlightcolor=ACCENT,
                            height=4, insertbackground=ACCENT)
            widget.pack(fill="x")
        else:
            widget = ModernEntry(parent, placeholder=placeholder)
            widget.pack(fill="x")

        setattr(self, attr, widget)

    def _on_installer_type_change(self):
        itype = self.current_installer_type.get()
        params = self.INSTALLER_TYPES[itype]["params"]
        self.params_entry.delete(0, tk.END)
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
                self.file_listbox.insert(tk.END, os.path.basename(f))

    def _remove_file(self):
        sel = self.file_listbox.curselection()
        if sel:
            idx = sel[0]
            self.file_listbox.delete(idx)
            del self.selected_files[idx]

    def _add_dependency(self):
        product = self.dep_product.get_value()
        if not product:
            return
        action = self.dep_action.get()
        dtype = self.dep_type.get()

        dep = {"product": product, "action": action, "type": dtype}
        self.dependencies.append(dep)
        self.deps_listbox.insert(tk.END, f"{product} ({action}, {dtype})")
        self.dep_product.delete(0, tk.END)

    def _remove_dependency(self):
        sel = self.deps_listbox.curselection()
        if sel:
            idx = sel[0]
            self.deps_listbox.delete(idx)
            del self.dependencies[idx]

    def _add_property(self):
        name = self.prop_name.get_value()
        if not name:
            return
        ptype = self.prop_type.get()
        default = self.prop_default.get_value()
        values = self.prop_values.get_value()

        prop = {"name": name, "type": ptype, "default": default, "values": values}
        self.properties.append(prop)
        self.props_listbox.insert(tk.END, f"{name} ({ptype}) = {default}")

        self.prop_name.delete(0, tk.END)
        self.prop_default.delete(0, tk.END)
        self.prop_values.delete(0, tk.END)

    def _remove_property(self):
        sel = self.props_listbox.curselection()
        if sel:
            idx = sel[0]
            self.props_listbox.delete(idx)
            del self.properties[idx]

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select output directory")
        if path:
            self.output_dir.delete(0, tk.END)
            self.output_dir.insert(0, path)

    def _log(self, msg, tag=""):
        self.log_text.insert(tk.END, msg + "\n", tag)
        self.log_text.see(tk.END)
        self.update_idletasks()

    def _get_text_value(self, widget):
        if isinstance(widget, tk.Text):
            return widget.get("1.0", tk.END).strip()
        elif isinstance(widget, ModernEntry):
            return widget.get_value()
        return widget.get().strip()

    # ══════════════════════════════════════════════════════════════════════════
    # BUILD METHODS
    # ══════════════════════════════════════════════════════════════════════════

    def _validate(self):
        pkg_id = self._get_text_value(self.pkg_id)
        if not pkg_id:
            messagebox.showerror("Error", "Package ID is required!")
            return False
        if not re.match(r'^[a-z0-9\-]+$', pkg_id):
            messagebox.showerror("Error", "Package ID must be lowercase, numbers, hyphens only!")
            return False
        return True

    def _generate_control(self, data):
        lines = [
            "[Package]",
            "version: 1",
            "depends:",
            "incremental: False",
            "",
            "[Product]",
            "type: localboot",
            f"id: {data['id']}",
            f"name: {data['name']}",
            f"description: {data['desc']}",
            f"advice: {data['advice']}",
            f"version: {data['version']}",
            f"priority: {data['priority']}",
            f"licenseRequired: {str(data['license']).lower()}",
            "productClasses:",
            "setupScript: setup.opsiscript",
            "uninstallScript: uninstall.opsiscript",
            "updateScript:",
            "alwaysScript:",
            "onceScript:",
            "customScript:",
            "userLoginScript:",
            ""
        ]

        # Dependencies
        for dep in self.dependencies:
            lines.extend([
                "[ProductDependency]",
                f"action: setup",
                f"requiredProduct: {dep['product']}",
                f"requiredAction: {dep['action']}",
                f"requirementType: {dep['type']}",
                ""
            ])

        # Properties
        for prop in self.properties:
            lines.extend([
                "[ProductProperty]",
                f"type: {prop['type']}",
                f"name: {prop['name']}",
                f"description:",
            ])
            if prop['values']:
                for v in prop['values'].split(','):
                    lines.append(f"values: {v.strip()}")
            lines.extend([
                f"default: {prop['default']}",
                ""
            ])

        return "\n".join(lines)

    def _generate_setup_script(self, data, files):
        itype = self.current_installer_type.get()
        type_info = self.INSTALLER_TYPES[itype]
        params = self.params_entry.get()

        lines = [
            f"; Setup script for {data['name']}",
            "; Generated by OPSI PackForge",
            "",
            "[Actions]",
            'requiredWinstVersion >= "4.11.6"',
            "",
            "DefVar $ProductId$",
            "DefVar $SetupFile$",
            "DefVar $ExitCode$",
            "",
            f'Set $ProductId$ = "{data["id"]}"',
            ""
        ]

        for i, f in enumerate(files):
            fname = os.path.basename(f)
            lines.append(f'Set $SetupFile$ = "%ScriptPath%\\files\\{fname}"')
            lines.append(f'Message "Installing {fname}..."')
            lines.append("")

            if type_info["method"] == "msi":
                lines.extend([
                    f"Winbatch_install_{i}",
                    f"Sub_check_exitcode",
                    "",
                    f"[Winbatch_install_{i}]",
                    f'msiexec /i "$SetupFile$" {params}',
                    ""
                ])
            elif type_info["method"] == "shell":
                lines.extend([
                    f"ShellCall_install_{i}",
                    f"Sub_check_exitcode",
                    "",
                    f"[ShellCall_install_{i}]",
                ])
                if itype == "ps1":
                    lines.append(f'powershell.exe -ExecutionPolicy Bypass -File "$SetupFile$"')
                else:
                    lines.append(f'"$SetupFile$"')
                lines.append("")
            else:
                lines.extend([
                    f"Winbatch_install_{i}",
                    f"Sub_check_exitcode",
                    "",
                    f"[Winbatch_install_{i}]",
                    f'"$SetupFile$" {params}' if params else '"$SetupFile$"',
                    ""
                ])

        lines.extend([
            "[Sub_check_exitcode]",
            "set $ExitCode$ = getLastExitCode",
            'if ($ExitCode$ = "0")',
            '    comment "Setup successful"',
            "else",
            '    logError "Setup failed with exit code: " + $ExitCode$',
            "    isFatalError",
            "endif"
        ])

        return "\n".join(lines)

    def _generate_uninstall_script(self, data):
        return f"""; Uninstall script for {data['name']}
; Generated by OPSI PackForge

[Actions]
Message "Uninstalling {data['name']}..."

; TODO: Add uninstall commands here
; Example for MSI:
; Winbatch_uninstall
;
; [Winbatch_uninstall]
; msiexec /x {{PRODUCT-CODE}} /qn /norestart
"""

    def _build_package(self):
        if not self._validate():
            return

        self.log_text.delete("1.0", tk.END)
        self._log("Starting build...", "info")

        data = {
            "id": self._get_text_value(self.pkg_id),
            "name": self._get_text_value(self.pkg_name) or self._get_text_value(self.pkg_id),
            "version": self._get_text_value(self.pkg_version) or "1.0.0",
            "release": self._get_text_value(self.pkg_release) or "1",
            "desc": self._get_text_value(self.pkg_desc),
            "advice": self._get_text_value(self.pkg_advice),
            "priority": self._get_text_value(self.pkg_priority) or "0",
            "license": self.license_required.get()
        }

        pkg_folder = f"{data['id']}_{data['version']}-{data['release']}"
        output_base = self.output_dir.get()
        pkg_path = os.path.join(output_base, pkg_folder)

        try:
            # Create directories
            self._log(f"Creating package structure: {pkg_folder}")
            os.makedirs(os.path.join(pkg_path, "OPSI"), exist_ok=True)
            os.makedirs(os.path.join(pkg_path, "CLIENT_DATA", "files"), exist_ok=True)

            # Write control file
            self._log("Writing control file...", "info")
            control = self._generate_control(data)
            with open(os.path.join(pkg_path, "OPSI", "control"), "w", encoding="utf-8") as f:
                f.write(control)
            self._log("[OK] control", "ok")

            # Write setup script
            self._log("Writing setup.opsiscript...", "info")
            setup = self._generate_setup_script(data, self.selected_files)
            with open(os.path.join(pkg_path, "CLIENT_DATA", "setup.opsiscript"), "w", encoding="utf-8") as f:
                f.write(setup)
            self._log("[OK] setup.opsiscript", "ok")

            # Write uninstall script
            self._log("Writing uninstall.opsiscript...", "info")
            uninstall = self._generate_uninstall_script(data)
            with open(os.path.join(pkg_path, "CLIENT_DATA", "uninstall.opsiscript"), "w", encoding="utf-8") as f:
                f.write(uninstall)
            self._log("[OK] uninstall.opsiscript", "ok")

            # Copy files
            for f in self.selected_files:
                fname = os.path.basename(f)
                self._log(f"Copying {fname}...", "info")
                shutil.copy2(f, os.path.join(pkg_path, "CLIENT_DATA", "files", fname))
                self._log(f"[OK] {fname}", "ok")

            # Create ZIP
            self._log("Creating ZIP archive...", "info")
            zip_path = os.path.join(output_base, f"{pkg_folder}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(pkg_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, output_base)
                        zf.write(file_path, arc_name)

            self._log("", "")
            self._log("=" * 50, "ok")
            self._log("BUILD SUCCESSFUL!", "ok")
            self._log("=" * 50, "ok")
            self._log(f"Package: {zip_path}", "info")

            # Open folder
            if os.name == 'nt':
                os.startfile(output_base)
            elif os.name == 'posix':
                subprocess.run(['open', output_base])

        except Exception as e:
            self._log(f"[ERROR] {str(e)}", "error")
            messagebox.showerror("Build Error", str(e))

    def _build_and_deploy(self):
        # First build
        self._build_package()

        # Then show deploy dialog
        deploy_win = tk.Toplevel(self)
        deploy_win.title("Deploy to OPSI Server")
        deploy_win.geometry("400x200")
        deploy_win.configure(bg=BG)

        tk.Label(deploy_win, text="OPSI Server:", bg=BG, fg=TEXT,
                 font=("Consolas", 10)).pack(anchor="w", padx=20, pady=(20, 5))
        server_entry = ModernEntry(deploy_win, placeholder="10.1.0.2")
        server_entry.pack(fill="x", padx=20)

        tk.Label(deploy_win, text="SSH User:", bg=BG, fg=TEXT,
                 font=("Consolas", 10)).pack(anchor="w", padx=20, pady=(10, 5))
        user_entry = ModernEntry(deploy_win, placeholder="root")
        user_entry.pack(fill="x", padx=20)

        def do_deploy():
            server = server_entry.get_value() or "10.1.0.2"
            user = user_entry.get_value() or "root"
            deploy_win.destroy()
            self._deploy_to_server(server, user)

        ModernButton(deploy_win, text="Deploy", primary=True,
                    command=do_deploy).pack(pady=20)

    def _deploy_to_server(self, server, user):
        data = {
            "id": self._get_text_value(self.pkg_id),
            "version": self._get_text_value(self.pkg_version) or "1.0.0",
            "release": self._get_text_value(self.pkg_release) or "1",
        }
        pkg_folder = f"{data['id']}_{data['version']}-{data['release']}"
        output_base = self.output_dir.get()
        pkg_path = os.path.join(output_base, pkg_folder)

        self._log("", "")
        self._log("=" * 50, "info")
        self._log(f"DEPLOYING TO {server}...", "info")
        self._log("=" * 50, "info")

        try:
            # SCP copy
            self._log(f"Copying to {user}@{server}...", "info")
            result = subprocess.run(
                ["scp", "-r", pkg_path, f"{user}@{server}:/var/lib/opsi/workbench/"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"SCP failed: {result.stderr}")
            self._log("[OK] Files copied", "ok")

            # Build package on server
            self._log("Building package on server...", "info")
            result = subprocess.run(
                ["ssh", f"{user}@{server}",
                 f"cd /var/lib/opsi/workbench && opsi-makepackage {pkg_folder}"],
                capture_output=True, text=True
            )
            self._log(result.stdout, "")
            if result.returncode != 0:
                self._log(f"[WARN] {result.stderr}", "warn")

            # Install package
            self._log("Installing package...", "info")
            result = subprocess.run(
                ["ssh", f"{user}@{server}",
                 f"opsi-package-manager -i /var/lib/opsi/workbench/{pkg_folder}-*.opsi"],
                capture_output=True, text=True
            )
            self._log(result.stdout, "")

            self._log("", "")
            self._log("=" * 50, "ok")
            self._log("DEPLOYMENT COMPLETE!", "ok")
            self._log("=" * 50, "ok")

        except FileNotFoundError:
            self._log("[ERROR] SSH/SCP not found. Install OpenSSH.", "error")
        except Exception as e:
            self._log(f"[ERROR] {str(e)}", "error")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = PackForgeApp()
    app.mainloop()
