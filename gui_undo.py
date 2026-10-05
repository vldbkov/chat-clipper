# Window to pick a project for undoing the last write
import tkinter as tk
from tkinter import ttk

from ui_helpers import center_window, apply_icon
import i18n


# Dialog to pick target project for undo
class UndoDialog:
    # Initialize window
    def __init__(self, parent, app_state, source_project: str, candidates: list):
        self.app_state = app_state
        self.candidates = candidates
        self.result = None
        self.win = tk.Toplevel(parent)
        apply_icon(self.win)
        self.win.title(i18n.t("undo.title"))
        self.win.geometry("420x220")
        self._build(source_project)
        self._center()
        self.win.deiconify()
        self.win.lift()
        self.win.attributes("-topmost", True)
        self.win.after(300, lambda: self.win.attributes("-topmost", False))
        try:
            self.win.focus_force()
        except Exception:
            pass
        try:
            self.win.grab_set()
        except Exception:
            pass

    # Build UI
    def _build(self, source_project: str):
        pad = {"padx": 10, "pady": 8}
        ttk.Label(self.win, text=i18n.t("undo.from") + source_project).grid(row=0, column=0, columnspan=2, sticky="w", **pad)
        ttk.Label(self.win, text=i18n.t("undo.move_to")).grid(row=1, column=0, sticky="w", **pad)
        self.var_choice = tk.StringVar()
        names = [p.name for p in self.candidates]
        self.var_choice.set(names[0] if names else "")
        cb = ttk.Combobox(self.win, textvariable=self.var_choice, values=names, state="readonly", width=40)
        cb.grid(row=1, column=1, sticky="we", **pad)
        self.win.columnconfigure(1, weight=1)
        btns = ttk.Frame(self.win)
        btns.grid(row=2, column=0, columnspan=2, sticky="e", padx=10, pady=10)
        ttk.Button(btns, text="OK", command=self._ok).pack(side="right", padx=4)
        ttk.Button(btns, text=i18n.t("undo.cancel"), command=self.win.destroy).pack(side="right", padx=4)

    # Center window
    def _center(self):
        center_window(self.win)

    # Confirm choice
    def _ok(self):
        name = self.var_choice.get().strip()
        if not name:
            return
        for p in self.candidates:
            if p.name == name:
                self.result = p
                break
        self.win.destroy()