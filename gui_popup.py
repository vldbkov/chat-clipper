# Semi-transparent project picker shown for 1 second after copy
import tkinter as tk

from logger import log
from config import save_config
from ui_helpers import apply_icon
from theme import get_palette


# Popup project picker class
class PopupWindow:
    # Initialize window
    def __init__(self, parent, app_state, on_choice, status_only: bool = False):
        self.app_state = app_state
        self.on_choice = on_choice
        self.status_only = status_only
        self.cfg = app_state.config
        self.chosen = None
        self.alpha = float(getattr(self.cfg, "popup_alpha", 0.5))
        if self.alpha < 0.1:
            self.alpha = 0.1
        if self.alpha > 1.0:
            self.alpha = 1.0
        self.win = tk.Toplevel(parent)
        apply_icon(self.win, dark_theme=bool(getattr(self.cfg, "dark_theme", False)))
        self.win.overrideredirect(True)
        self.win.attributes("-alpha", self.alpha)
        self.win.attributes("-topmost", True)
        self.palette = get_palette(bool(getattr(self.cfg, "dark_theme", False)))
        self.win.configure(bg=self.palette["bg"])
        self._paused = False
        self._after_id = None
        self._stamp_click_x = 0
        self._stamp_click_y = 0
        self._build()
        self._center()
        self.win.bind("<Enter>", self._on_enter)
        self.win.bind("<Leave>", self._on_leave)
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.win.bind("<ButtonPress-1>", self._on_drag_start)
        self.win.bind("<B1-Motion>", self._on_drag_move)
        self.win.bind("<ButtonRelease-1>", self._on_drag_end)
        self._bind_drag_recursive(self.win)
        self._schedule_close()

    # Recursively bind drag events to all child widgets
    def _bind_drag_recursive(self, widget):
        for child in widget.winfo_children():
            if child.winfo_class() == "Button":
                continue
            if child.winfo_class() == "Label":
                continue
            child.bind("<ButtonRelease-1>", self._on_drag_end, add="+")
            child.bind("<ButtonPress-1>", self._on_drag_start)
            child.bind("<B1-Motion>", self._on_drag_move)
            self._bind_drag_recursive(child)
        widget.bind("<ButtonRelease-1>", self._on_drag_end, add="+")

    # Window drag start
    def _on_drag_start(self, event):
        self._drag_start_x = event.x_root - self.win.winfo_x()
        self._drag_start_y = event.y_root - self.win.winfo_y()
        self._dragging = True
        try:
            if self._after_id:
                self.win.after_cancel(self._after_id)
                self._after_id = None
        except Exception:
            pass

    # Window drag and position save
    def _on_drag_move(self, event):
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self.win.geometry(f"+{x}+{y}")
        self._save_position()

    # Remember click position on PAUSE stamp to detect click vs drag
    def _on_stamp_press(self, event):
        self._stamp_click_x = event.x_root
        self._stamp_click_y = event.y_root

    # Release on PAUSE stamp: unpause and resume tracking
    def _on_stamp_release(self, event):
        try:
            from config import save_config
            self.app_state.paused = False
            self.cfg.paused = False
            save_config(self.cfg)
            self.app_state.apply_sound()
            log.info("Popup: PAUSE stamp clicked, tracking resumed")
        except Exception as e:
            log.exception("Popup: unpause error: %s", e)
            return
        self._render_buttons()
        self._schedule_close()

    # Drag end: save position and restart the timer
    def _on_drag_end(self, event):
        self._dragging = False
        self._save_position()
        try:
            if self._after_id:
                self.win.after_cancel(self._after_id)
                self._after_id = None
        except Exception:
            pass
        if self.chosen is None:
            self._schedule_close()
        log.info("Popup: drag end, timer restarted")

    # Build UI
    def _build(self):
        self.wrap = tk.Frame(self.win, bg=self.palette["bg"], padx=8, pady=8)
        self.wrap.pack()
        self._render_buttons()

    # Render project buttons
    def _render_buttons(self):
        wrap = self.wrap
        for child in list(wrap.winfo_children()):
            child.destroy()
        active = self.cfg.active_projects()
        main_name = self.cfg.main_project
        ordered = list(active)
        total = len(ordered)
        if total <= 1:
            cols = 1
        elif total <= 6:
            cols = 2
        else:
            cols = 3
        for idx, p in enumerate(ordered):
            row = idx // cols
            col = idx % cols
            row_items = min(cols, total - row * cols)
            is_main = (p.name == main_name)
            pal = self.palette
            bg = pal["main_bg"] if is_main else pal["btn"]
            fg = pal["main_fg"] if is_main else pal["fg"]
            btn = tk.Button(wrap, text=p.name, bg=bg, fg=fg, activebackground=pal["btn_hover"],
                            relief="flat", padx=12, pady=6, font=("Segoe UI", 10, "bold" if is_main else "normal"),
                            command=lambda name=p.name: self._choose(name))
            if row_items == 1 and cols > 1:
                btn.grid(row=row, column=0, columnspan=cols, padx=4, pady=4)
            else:
                btn.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        for c in range(cols):
            wrap.columnconfigure(c, weight=1, uniform="btn")
        if getattr(self.app_state, "paused", False):
            stamp = tk.Label(wrap, text="PAUSE", fg=self.palette["pause_fg"], bg=self.palette["bg"],
                             font=("Segoe UI", 14, "bold"),
                             bd=0, highlightthickness=0)
            stamp.place(relx=0.5, rely=0.5, anchor="center")
            stamp.bind("<ButtonPress-1>", self._on_stamp_press, add="+")
            stamp.bind("<ButtonRelease-1>", self._on_stamp_release, add="+")
            stamp.configure(cursor="hand2")

    # Window placement: saved coordinates or centered
    def _center(self):
        self.win.update_idletasks()
        w = self.win.winfo_width()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        saved_x = int(getattr(self.cfg, "popup_x", -1))
        saved_y = int(getattr(self.cfg, "popup_y", -1))
        if saved_x >= 0 and saved_y >= 0 and saved_x < sw and saved_y < sh:
            x = saved_x
            y = saved_y
        else:
            # Default: above screen center, horizontally centered; no absolute pixels
            x = (sw - w) // 2
            y = int(sh * 0.40)
        self.win.geometry(f"+{x}+{y}")

    # (drag handlers moved to ui_helpers.attach_drag_with_save)

    # Save current window coordinates to config.json
    def _save_position(self):
        try:
            x = int(self.win.winfo_x())
            y = int(self.win.winfo_y())
            if x == getattr(self.cfg, "popup_x", -1) and y == getattr(self.cfg, "popup_y", -1):
                return
            self.cfg.popup_x = x
            self.cfg.popup_y = y
            save_config(self.cfg)
            log.info("Popup: saved window position (%d, %d)", x, y)
        except Exception as e:
            log.exception("Popup: save position error: %s", e)

    # Schedule auto-close
    def _schedule_close(self):
        sec = max(1, int(self.cfg.popup_seconds))
        self._after_id = self.win.after(sec * 1000, self._auto_close)

    # Auto-close without choice: default project will be used
    def _auto_close(self):
        if self.chosen is not None:
            return
        if self.status_only:
            self._finish()
            return
        self.chosen = self.cfg.main_project
        log.info("Popup: auto-close, choice = default project '%s'", self.chosen)
        self._finish()

    # Project button click
    def _choose(self, name: str):
        if self.chosen is not None:
            return
        if self.status_only:
            if name != self.cfg.main_project:
                self.cfg.main_project = name
                save_config(self.cfg)
                log.info("Status popup: main project switched to '%s'", name)
                self._render_buttons()
                self._schedule_close()
            else:
                self._finish()
            return
        self.chosen = name
        log.info("Popup: project chosen '%s'", name)
        self._finish()

    # Window shutdown
    def _finish(self):
        try:
            if self._after_id:
                self.win.after_cancel(self._after_id)
                self._after_id = None
        except Exception:
            pass
        try:
            self.win.destroy()
        except Exception:
            pass
        if self.status_only:
            return
        if self.on_choice is None:
            return
        try:
            self.on_choice(self.chosen)
        except Exception as e:
            log.exception("Popup: error in on_choice: %s", e)

    # Cursor over window: pause timer
    def _on_enter(self, event):
        self._paused = True
        try:
            if self._after_id:
                self.win.after_cancel(self._after_id)
                self._after_id = None
        except Exception:
            pass
        self.win.attributes("-alpha", min(1.0, self.alpha + 0.3))

    # Cursor left window: resume timer
    def _on_leave(self, event):
        self._paused = False
        self.win.attributes("-alpha", self.alpha)
        if self._after_id is None and self.chosen is None and not getattr(self, "_dragging", False):
            self._schedule_close()