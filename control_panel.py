# Visible control panel used instead of tray icon (Windows without tray, Linux, macOS)
import tkinter as tk

from config import save_config
from ui_helpers import attach_drag_with_save, apply_icon
from ipc_client import send_ipc_command
from logger import log
from theme import get_palette
import i18n





# Simple visible window with control buttons
class ControlPanel:
    # Initialize panel with parent Tk root
    def __init__(self, parent, app_state):
        self.app_state = app_state
        self.cfg = app_state.config
        self.win = tk.Toplevel(parent)
        self.win.withdraw()
        apply_icon(self.win, dark_theme=bool(getattr(self.cfg, "dark_theme", False)))
        self.palette = get_palette(bool(getattr(self.cfg, "dark_theme", False)))
        self.win.title("ChatClipper")
        self.win.configure(bg=self.palette["bg"])
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self._exit_after_id = None
        self._build()
        self.win.update()
        self._place()
        self.win.deiconify()
        attach_drag_with_save(self.win, self._on_drag_save)
        self.win.lift()
        try:
            self.win.focus_force()
        except Exception:
            pass
        self._update_pause_button()
        self.win.after(300, self._poll_state)

    # Build interface
    def _build(self):
        pal = self.palette
        wrap = tk.Frame(self.win, bg=pal["bg"], padx=8, pady=8)
        wrap.pack()
        self.btn_status = tk.Button(wrap, text=i18n.t("control.status"), command=lambda: self._send("status"),
                                    bg=pal["btn"], fg=pal["fg"], activebackground=pal["btn_hover"],
                                    relief="flat", padx=12, pady=6, font=("Segoe UI", 9))
        self.btn_status.pack(side="left", padx=3)
        self.btn_settings = tk.Button(wrap, text=i18n.t("control.settings"), command=lambda: self._send("settings"),
                                      bg=pal["btn"], fg=pal["fg"], activebackground=pal["btn_hover"],
                                      relief="flat", padx=12, pady=6, font=("Segoe UI", 9))
        self.btn_settings.pack(side="left", padx=3)
        self.btn_undo = tk.Button(wrap, text=i18n.t("control.undo"), command=lambda: self._send("undo"),
                                  bg=pal["btn"], fg=pal["fg"], activebackground=pal["btn_hover"],
                                  relief="flat", padx=12, pady=6, font=("Segoe UI", 9))
        self.btn_undo.pack(side="left", padx=3)
        self.btn_pause = tk.Button(wrap, text=i18n.t("control.pause"), command=lambda: self._send("toggle_pause"),
                                   bg=pal["btn"], fg=pal["fg"], activebackground=pal["btn_hover"],
                                   relief="flat", padx=12, pady=6, font=("Segoe UI", 9))
        self.btn_pause.pack(side="left", padx=3)
        self.btn_exit = tk.Button(wrap, text=i18n.t("control.exit"),
                                  bg=pal["btn"], fg=pal["fg"], activebackground=pal["btn_hover"],
                                  relief="flat", padx=12, pady=6, font=("Segoe UI", 9))
        self.btn_exit.pack(side="left", padx=3)
        self.btn_exit.bind("<Button-1>", self._on_exit_click)
        self.btn_exit.bind("<Double-Button-1>", self._on_exit_double)

    # Bind drag events to all widgets except buttons
    # Place panel at saved coordinates or default bottom-right corner
    def _place(self):
        self.win.update_idletasks()
        self.win.update()
        w = self.win.winfo_width()
        h = self.win.winfo_height()
        if w <= 1 or h <= 1:
            w = self.win.winfo_reqwidth()
            h = self.win.winfo_reqheight()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        saved_x = int(getattr(self.cfg, "panel_x", -1))
        saved_y = int(getattr(self.cfg, "panel_y", -1))
        if saved_x >= 0 and saved_y >= 0 and saved_x < sw and saved_y < sh:
            x = saved_x
            y = saved_y
        else:
            # Default: horizontally centered, vertically below the popup
            x = max(0, (sw - w) // 2)
            y = int(sh * 0.55)
            log.info("ControlPanel._place: w=%d h=%d sw=%d sh=%d -> x=%d y=%d", w, h, sw, sh, x, y)
        self.win.geometry(f"+{x}+{y}")

    # Estimate taskbar height; on Windows use SPI_GETWORKAREA
    def _get_taskbar_height(self) -> int:
        try:
            import sys
            if not sys.platform.startswith("win"):
                return 0
            import ctypes
            from ctypes import wintypes
            SPI_GETWORKAREA = 0x0030
            rect = wintypes.RECT()
            ok = ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
            if not ok:
                return 60
            sh = ctypes.windll.user32.GetSystemMetrics(1)
            return max(0, int(sh - rect.bottom))
        except Exception:
            return 60

    # Start drag
    # Save position after drag (called by ui_helpers)
    def _on_drag_save(self, win):
        try:
            x = int(self.win.winfo_x())
            y = int(self.win.winfo_y())
            if x == getattr(self.cfg, "panel_x", -1) and y == getattr(self.cfg, "panel_y", -1):
                return
            self.cfg.panel_x = x
            self.cfg.panel_y = y
            save_config(self.cfg)
            log.info("ControlPanel: saved position (%d, %d)", x, y)
        except Exception as e:
            log.exception("ControlPanel: save position error: %s", e)

    # Send IPC command to GUI process
    def _send(self, cmd: str):
        ok = send_ipc_command(cmd)
        if ok:
            log.info("ControlPanel: sent '%s'", cmd)

    # Update pause button label based on current state
    def _update_pause_button(self):
        try:
            paused = bool(getattr(self.app_state, "paused", False))
            text = i18n.t("control.start") if paused else i18n.t("control.pause")
            self.btn_pause.configure(text=text)
        except Exception:
            pass

    # Repaint panel colors when theme changes in config
    def _refresh_theme(self):
        dark = bool(getattr(self.cfg, "dark_theme", False))
        new_pal = get_palette(dark)
        if new_pal == self.palette:
            return
        self.palette = new_pal
        pal = new_pal
        try:
            self.win.configure(bg=pal["bg"])
        except Exception:
            pass
        for btn in (self.btn_status, self.btn_settings, self.btn_undo, self.btn_pause, self.btn_exit):
            try:
                btn.configure(bg=pal["btn"], fg=pal["fg"], activebackground=pal["btn_hover"])
            except Exception:
                pass
        try:
            for child in self.win.winfo_children():
                child.configure(bg=pal["bg"])
        except Exception:
            pass
        apply_icon(self.win, dark_theme=dark)
        log.info("ControlPanel: theme refreshed (dark=%s)", dark)

    # Periodically refresh button state and theme
    def _poll_state(self):
        self._update_pause_button()
        self._refresh_theme()
        try:
            self.win.after(300, self._poll_state)
        except Exception:
            pass

    # Single click on exit: schedule exit after short delay to detect double click
    def _on_exit_click(self, event):
        if self._exit_after_id is not None:
            try:
                self.win.after_cancel(self._exit_after_id)
            except Exception:
                pass
        self._exit_after_id = self.win.after(350, self._on_exit_single)

    # Execute single click exit
    def _on_exit_single(self):
        self._exit_after_id = None
        self._send("exit")

    # Double click on exit: cancel single, show Restart label, then send restart
    def _on_exit_double(self, event):
        if self._exit_after_id is not None:
            try:
                self.win.after_cancel(self._exit_after_id)
            except Exception:
                pass
            self._exit_after_id = None
        try:
            self.btn_exit.configure(text=i18n.t("control.restart"))
        except Exception:
            pass
        self.win.after(1000, self._do_restart)

    # Send restart command and restore button label
    def _do_restart(self):
        try:
            self.btn_exit.configure(text=i18n.t("control.exit"))
        except Exception:
            pass
        self._send("restart")

    # Handle window close - just hide, app continues
    def _on_close(self):
        self._send("exit")
        log.info("ControlPanel: exit requested by close button")