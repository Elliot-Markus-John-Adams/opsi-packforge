# OPSI PackForge - GUI Installer Bootstrap
# Downloads Python (embedded) if needed, then launches the tkinter GUI

$installPath = "$env:LOCALAPPDATA\OPSI-PackForge"
$pythonDir   = "$installPath\python"
$pythonExe   = "$pythonDir\python.exe"
$guiScript   = "$installPath\installer_gui.py"
$pythonUrl   = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
$tkUrl       = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"

# ── Ensure install directory exists ──────────────────────────────────────────
New-Item -ItemType Directory -Path $installPath -Force | Out-Null

# ── Download Python if not present ───────────────────────────────────────────
if (-not (Test-Path $pythonExe)) {
    Write-Host ""
    Write-Host "  Downloading Python 3.11 (embedded)..." -ForegroundColor Cyan
    $zipPath = "$env:TEMP\opsi_python.zip"

    try {
        [System.Net.WebRequest]::DefaultWebProxy.Credentials = `
            [System.Net.CredentialCache]::DefaultCredentials
        $client = New-Object System.Net.WebClient
        $client.Proxy.Credentials = `
            [System.Net.CredentialCache]::DefaultNetworkCredentials
        $client.DownloadFile($pythonUrl, $zipPath)
    } catch {
        Write-Host "  ERROR: Could not download Python: $_" -ForegroundColor Red
        exit 1
    }

    Write-Host "  Extracting Python..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $pythonDir -Force | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $pythonDir -Force
    Remove-Item $zipPath

    # Enable tkinter: uncomment Lib in python311._pth
    $pthFile = Get-ChildItem $pythonDir -Filter "python*._pth" | Select-Object -First 1
    if ($pthFile) {
        $content = Get-Content $pthFile.FullName -Raw
        $content = $content -replace "#import site", "import site"
        Set-Content $pthFile.FullName $content -Encoding ASCII
    }

    Write-Host "  Python ready." -ForegroundColor Green
}

# ── Write the GUI script ──────────────────────────────────────────────────────
# (Embedded inline so the .ps1 is self-contained)
$guiCode = @'
"""
OPSI PackForge - GUI Installer
Modern tkinter-based installer for OPSI PackForge
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import sys
import os
import zipfile
import urllib.request
import shutil
import time

BG        = "#0d0d0d"
SURFACE   = "#141414"
CARD      = "#1a1a1a"
BORDER    = "#2a2a2a"
ACCENT    = "#00d4ff"
ACCENT2   = "#0099cc"
SUCCESS   = "#00ff88"
WARNING   = "#ffaa00"
ERROR     = "#ff4444"
TEXT      = "#e8e8e8"
TEXT_DIM  = "#666666"
TEXT_MID  = "#999999"

FONT_TITLE  = ("Consolas", 22, "bold")
FONT_SUB    = ("Consolas", 10)
FONT_LABEL  = ("Consolas", 9)
FONT_MONO   = ("Consolas", 9)
FONT_BTN    = ("Consolas", 10, "bold")
FONT_SMALL  = ("Consolas", 8)


class AnimatedProgressBar(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=4, bg=SURFACE,
                         highlightthickness=0, **kwargs)
        self._progress = 0
        self._animating = False
        self._anim_pos = 0
        self.bind("<Configure>", self._redraw)

    def set_progress(self, val):
        self._progress = max(0, min(100, val))
        self._animating = False
        self._redraw()

    def start_indeterminate(self):
        self._animating = True
        self._anim_pos = 0
        self._animate()

    def stop_indeterminate(self):
        self._animating = False

    def _animate(self):
        if not self._animating:
            return
        self._anim_pos = (self._anim_pos + 3) % 110
        self._redraw()
        self.after(16, self._animate)

    def _redraw(self, *_):
        self.delete("all")
        w = self.winfo_width()
        if w < 2:
            return
        self.create_rectangle(0, 0, w, 4, fill=BORDER, outline="")
        if self._animating:
            x1 = int((self._anim_pos / 110) * (w + 60)) - 60
            x2 = x1 + 60
            self.create_rectangle(max(0, x1), 0, min(w, x2), 4,
                                  fill=ACCENT, outline="")
        else:
            filled = int(w * self._progress / 100)
            if filled > 0:
                self.create_rectangle(0, 0, filled, 4, fill=ACCENT, outline="")


class StepIndicator(tk.Frame):
    def __init__(self, parent, steps, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.steps = steps
        self.circles = []
        self.labels = []
        self._current = -1
        self._build()

    def _build(self):
        for i, name in enumerate(self.steps):
            col = tk.Frame(self, bg=BG)
            col.pack(side="left", expand=True)
            c = tk.Canvas(col, width=28, height=28, bg=BG, highlightthickness=0)
            c.pack()
            self.circles.append(c)
            lbl = tk.Label(col, text=name, font=FONT_SMALL, bg=BG, fg=TEXT_DIM)
            lbl.pack()
            self.labels.append(lbl)
            if i < len(self.steps) - 1:
                tk.Frame(self, bg=BORDER, height=2, width=30).pack(side="left", pady=10)
        self._render()

    def _render(self):
        for i, (c, lbl) in enumerate(zip(self.circles, self.labels)):
            c.delete("all")
            if i < self._current:
                c.create_oval(2, 2, 26, 26, fill=SUCCESS, outline="")
                c.create_text(14, 14, text="✓", fill=BG, font=("Consolas", 10, "bold"))
                lbl.config(fg=SUCCESS)
            elif i == self._current:
                c.create_oval(2, 2, 26, 26, fill=ACCENT, outline="")
                c.create_text(14, 14, text=str(i+1), fill=BG, font=("Consolas", 10, "bold"))
                lbl.config(fg=ACCENT)
            else:
                c.create_oval(2, 2, 26, 26, fill="", outline=BORDER, width=2)
                c.create_text(14, 14, text=str(i+1), fill=TEXT_DIM, font=("Consolas", 10))
                lbl.config(fg=TEXT_DIM)

    def set_step(self, step):
        self._current = step
        self._render()


class LogBox(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=CARD, **kwargs)
        self.configure(highlightbackground=BORDER, highlightthickness=1)
        self._text = tk.Text(
            self, bg=CARD, fg=TEXT_MID, font=FONT_MONO,
            relief="flat", bd=0, wrap="word", cursor="arrow",
            state="disabled", insertbackground=ACCENT,
        )
        self._text.pack(fill="both", expand=True, padx=8, pady=6)
        self._text.tag_config("ok",      foreground=SUCCESS)
        self._text.tag_config("err",     foreground=ERROR)
        self._text.tag_config("warn",    foreground=WARNING)
        self._text.tag_config("info",    foreground=ACCENT)
        self._text.tag_config("dim",     foreground=TEXT_DIM)
        self._text.tag_config("default", foreground=TEXT_MID)

    def append(self, line, tag="default"):
        self._text.config(state="normal")
        self._text.insert("end", line + "\n", tag)
        self._text.see("end")
        self._text.config(state="disabled")


class PackForgeInstaller(tk.Tk):
    INSTALL_PATH = os.path.join(os.environ.get("LOCALAPPDATA", ""), "OPSI-PackForge")
    APP_PATH     = os.path.join(os.environ.get("LOCALAPPDATA", ""), "OPSI-PackForge", "app", "opsi_packforge.bat")
    PY_PATH      = os.path.join(os.environ.get("LOCALAPPDATA", ""), "OPSI-PackForge", "python", "python.exe")
    PYTHON_URL   = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"

    def __init__(self):
        super().__init__()
        self.title("OPSI PackForge Installer")
        self.geometry("680x520")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 680) // 2
        y = (self.winfo_screenheight() - 520) // 2
        self.geometry(f"680x520+{x}+{y}")
        self._already_installed = os.path.exists(self.APP_PATH)
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=SURFACE, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="OPSI PackForge", font=FONT_TITLE,
                 bg=SURFACE, fg=ACCENT).pack(side="left", padx=24, pady=18)
        ver_frame = tk.Frame(header, bg=SURFACE)
        ver_frame.pack(side="right", padx=24)
        tk.Label(ver_frame, text="v2.0", font=FONT_SUB,
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor="e")
        tk.Label(ver_frame, text="Package Management Made Easy",
                 font=FONT_SMALL, bg=SURFACE, fg=TEXT_DIM).pack(anchor="e")
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=16)

        badge_text = ("● Already installed — updating" if self._already_installed
                      else "● Ready to install")
        badge_fg   = WARNING if self._already_installed else SUCCESS
        tk.Label(body, text=badge_text, font=FONT_SMALL,
                 bg=BG, fg=badge_fg).pack(anchor="w", pady=(0, 10))

        self._steps = StepIndicator(body, ["Directory", "Python", "App", "Shortcut"])
        self._steps.pack(fill="x", pady=(0, 14))

        self._log = LogBox(body)
        self._log.pack(fill="both", expand=True)

        self._pbar = AnimatedProgressBar(self, bg=SURFACE)
        self._pbar.pack(fill="x", side="bottom")

        footer = tk.Frame(self, bg=SURFACE, height=56)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self._status_lbl = tk.Label(footer, text="Ready", font=FONT_SMALL,
                                    bg=SURFACE, fg=TEXT_DIM)
        self._status_lbl.pack(side="left", padx=16)

        self._btn_exit = tk.Button(
            footer, text="EXIT", font=FONT_BTN,
            bg=SURFACE, fg=TEXT_DIM, relief="flat",
            activebackground=BORDER, activeforeground=TEXT,
            cursor="hand2", bd=0, padx=16, command=self.destroy)
        self._btn_exit.pack(side="right", padx=8, pady=10)

        self._btn_install = tk.Button(
            footer,
            text="UPDATE" if self._already_installed else "INSTALL",
            font=FONT_BTN, bg=ACCENT, fg=BG, relief="flat",
            activebackground=ACCENT2, activeforeground=BG,
            cursor="hand2", bd=0, padx=20, command=self._start_install)
        self._btn_install.pack(side="right", padx=4, pady=10)

        self._log.append("OPSI PackForge Installer", "info")
        self._log.append("─" * 48, "dim")
        if self._already_installed:
            self._log.append("Existing installation detected.", "warn")
            self._log.append("Press UPDATE to refresh.", "default")
        else:
            self._log.append("Press INSTALL to begin.", "default")
            self._log.append(f"Install path:  {self.INSTALL_PATH}", "dim")

    def _start_install(self):
        self._btn_install.config(state="disabled")
        self._btn_exit.config(state="disabled")
        threading.Thread(target=self._run_install, daemon=True).start()

    def _run_install(self):
        try:
            self._do_install()
        except Exception as exc:
            self._log_ui(f"FATAL: {exc}", "err")
            self._status("Failed", ERROR)
            self._btn_exit.config(state="normal")

    def _do_install(self):
        self._step(0, "Creating directory…")
        os.makedirs(self.INSTALL_PATH, exist_ok=True)
        self._log_ui(f"[OK] {self.INSTALL_PATH}", "ok")
        self._progress(20)

        self._step(1, "Checking Python…")
        if os.path.exists(self.PY_PATH):
            self._log_ui("[OK] Python already present — skipping", "ok")
        else:
            self._log_ui("Downloading Python 3.11.9…", "info")
            self._pbar.start_indeterminate()
            zip_path = os.path.join(os.environ.get("TEMP", ""), "opsi_python.zip")
            try:
                urllib.request.urlretrieve(self.PYTHON_URL, zip_path,
                                           reporthook=self._dl_hook)
            finally:
                self._pbar.stop_indeterminate()
            self._log_ui("[OK] Download complete", "ok")
            self._progress(50)
            py_dir = os.path.join(self.INSTALL_PATH, "python")
            os.makedirs(py_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(py_dir)
            os.remove(zip_path)
            self._log_ui("[OK] Python extracted", "ok")
        self._progress(60)

        self._step(2, "Writing application…")
        app_dir  = os.path.join(self.INSTALL_PATH, "app")
        os.makedirs(app_dir, exist_ok=True)
        bat_path = os.path.join(app_dir, "opsi_packforge.bat")
        with open(bat_path, "w", encoding="ascii") as f:
            f.write(BAT_CONTENT)
        self._log_ui("[OK] opsi_packforge.bat written", "ok")
        self._progress(80)

        self._step(3, "Creating shortcut…")
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            lnk = os.path.join(desktop, "OPSI PackForge.lnk")
            ps  = (f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{lnk}");'
                   f'$s.TargetPath="{bat_path}";'
                   f'$s.WorkingDirectory="{app_dir}";'
                   f'$s.Description="OPSI PackForge";$s.Save()')
            subprocess.run(["powershell", "-Command", ps],
                           capture_output=True, check=True)
            self._log_ui("[OK] Desktop shortcut created", "ok")
        except Exception as e:
            self._log_ui(f"[WARN] Shortcut skipped: {e}", "warn")

        self._progress(100)
        self._step(4, "Done")
        self._status("Installation complete!", SUCCESS)
        self._log_ui("─" * 48, "dim")
        self._log_ui("Installation complete!", "ok")
        self._log_ui(f"  {bat_path}", "dim")

        self._btn_exit.config(state="normal")
        self._btn_install.config(
            text="LAUNCH", bg=SUCCESS, fg=BG, state="normal",
            command=lambda: subprocess.Popen([bat_path]))

    def _dl_hook(self, count, block, total):
        if total > 0:
            pct = min(100, int(count * block * 100 / total))
            self._pbar.stop_indeterminate()
            self._pbar.set_progress(20 + pct * 0.3)
            self._status_lbl.after(0, lambda: self._status_lbl.config(
                text=f"Downloading… {pct}%"))

    def _log_ui(self, msg, tag="default"):
        self._log.after(0, lambda: self._log.append(msg, tag))

    def _status(self, msg, color=TEXT_DIM):
        self._status_lbl.after(0, lambda: self._status_lbl.config(
            text=msg, fg=color))

    def _step(self, idx, status_msg):
        self._steps.after(0, lambda: self._steps.set_step(idx))
        self._status(status_msg)

    def _progress(self, val):
        self._pbar.after(0, lambda: self._pbar.set_progress(val))


BAT_CONTENT = r"""@echo off
setlocal enabledelayedexpansion
title OPSI PackForge v2.0
color 0A
:menu
cls
echo.
echo  ########################################################
echo  ##              OPSI PACKFORGE v2.0                   ##
echo  ##          Package Management Made Easy              ##
echo  ########################################################
echo.
echo [1] Create new package
echo [2] Update package
echo [3] Delete package
echo [4] Show server packages
echo [5] Advanced options
echo [6] Help
echo [7] Exit
echo.
set /p choice="Your choice: "
if "%choice%"=="7" exit
goto menu
"""

if __name__ == "__main__":
    app = PackForgeInstaller()
    app.mainloop()
'@

Set-Content -Path $guiScript -Value $guiCode -Encoding UTF8

# ── Launch the GUI ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Launching OPSI PackForge Installer..." -ForegroundColor Cyan
Write-Host ""

& $pythonExe $guiScript
