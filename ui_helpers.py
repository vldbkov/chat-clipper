# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Shared UI helpers: window centering and drag&drop attachment
import os

from logger import log
from config import ICON_PATH


# Center a Tk window on the screen
# If saved coordinates are provided (saved_x, saved_y) and valid, use them
def center_window(win, saved_x: int = -1, saved_y: int = -1) -> None:
    try:
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        if not win.winfo_viewable():
            w = win.winfo_reqwidth()
            h = win.winfo_reqheight()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        log.debug("center_window: w=%d h=%d sw=%d sh=%d", w, h, sw, sh)
        if saved_x >= 0 and saved_y >= 0 and saved_x < sw and saved_y < sh:
            x = saved_x
            y = saved_y
        else:
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.update_idletasks()
    except Exception as e:
        log.exception("ui_helpers.center_window error: %s", e)


# Lightweight tooltip: shows a small topmost window on <Enter>, hides on <Leave>
class Tooltip:
    # Attach tooltip to a widget
    def __init__(self, widget, text: str, delay_ms: int = 400):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    # Schedule tooltip after the delay
    def _schedule(self, _event=None):
        self._cancel()
        try:
            self._after_id = self.widget.after(self.delay_ms, self._show)
        except Exception:
            pass

    # Cancel a scheduled tooltip
    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    # Show the tooltip window
    def _show(self):
        self._after_id = None
        if self._tip is not None:
            return
        try:
            import tkinter as tk
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
            tip = tk.Toplevel(self.widget)
            tip.wm_overrideredirect(True)
            tip.attributes("-topmost", True)
            tip.geometry(f"+{x}+{y}")
            tk.Label(tip, text=self.text, background="#FFFFE0", relief="solid", borderwidth=1, font=("Segoe UI", 9)).pack()
            self._tip = tip
        except Exception:
            self._tip = None

    # Hide the tooltip window
    def _hide(self, _event=None):
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


# Apply app icon to a Tk/Toplevel window; safe no-op when icon is missing
def apply_icon(win) -> None:
    try:
        if os.path.isfile(ICON_PATH):
            win.iconbitmap(default=ICON_PATH)
            win.iconbitmap(ICON_PATH)
    except Exception as e:
        log.debug("ui_helpers.apply_icon: %s", e)


# Attach drag&drop to a window and its children
# Buttons are skipped by default so clicks still fire their command
# Returns a state dict that persists drag start coordinates
def attach_drag(win, skip_buttons: bool = True) -> dict:
    state = {"x": 0, "y": 0}

    def on_start(event):
        state["x"] = event.x_root - win.winfo_x()
        state["y"] = event.y_root - win.winfo_y()

    def on_move(event):
        x = event.x_root - state["x"]
        y = event.y_root - state["y"]
        win.geometry(f"+{x}+{y}")

    def bind_recursive(widget):
        for child in widget.winfo_children():
            if skip_buttons and child.winfo_class() == "Button":
                continue
            child.bind("<ButtonPress-1>", on_start)
            child.bind("<B1-Motion>", on_move)
            bind_recursive(child)
        widget.bind("<ButtonPress-1>", on_start)
        widget.bind("<B1-Motion>", on_move)

    bind_recursive(win)
    return state


# Attach drag&drop with automatic position saving
# on_save(win) is called on ButtonRelease; caller persists coordinates
def attach_drag_with_save(win, on_save, skip_buttons: bool = True) -> dict:
    state = {"x": 0, "y": 0}

    def on_start(event):
        state["x"] = event.x_root - win.winfo_x()
        state["y"] = event.y_root - win.winfo_y()

    def on_move(event):
        x = event.x_root - state["x"]
        y = event.y_root - state["y"]
        win.geometry(f"+{x}+{y}")

    def on_release(event):
        try:
            on_save(win)
        except Exception as e:
            log.exception("ui_helpers.attach_drag_with_save error: %s", e)

    def bind_recursive(widget):
        for child in widget.winfo_children():
            if skip_buttons and child.winfo_class() == "Button":
                continue
            child.bind("<ButtonPress-1>", on_start)
            child.bind("<B1-Motion>", on_move)
            child.bind("<ButtonRelease-1>", on_release)
            bind_recursive(child)
        widget.bind("<ButtonPress-1>", on_start)
        widget.bind("<B1-Motion>", on_move)
        widget.bind("<ButtonRelease-1>", on_release)

    bind_recursive(win)
    return state