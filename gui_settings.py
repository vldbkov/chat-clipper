# ChatClipper settings window: project list, capture params, autostart
import os
from pathlib import Path
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from docx import Document

from logger import log
from config import Project, save_config, ensure_dirs, APP_VERSION
from platform_utils import open_file, IS_WINDOWS, is_pandoc_available
from ui_helpers import center_window, apply_icon, apply_theme, Tooltip, show_warning, ask_yesno
from sources.source_factory import list_sources
from ipc_client import send_ipc_command
from theme import get_palette
import i18n
import autostart
from updater import check_for_update


# Create empty .docx if missing
def ensure_file_exists(file_path: str) -> None:
    if not file_path:
        return
    if os.path.exists(file_path):
        return
    try:
        folder = os.path.dirname(file_path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".docx":
            doc = Document()
            doc.save(file_path)
            log.info("Created empty .docx: %s", file_path)
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("")
            log.info("Created empty %s: %s", ext, file_path)
    except Exception as e:
        log.exception("Cannot create file %s: %s", file_path, e)


# Settings window class
class SettingsWindow(tk.Toplevel):
    # Initialize settings window
    def _center_window(self):
        center_window(self)

    def __init__(self, parent, app_state):
        super().__init__(parent)
        self.withdraw()
        apply_icon(self, dark_theme=bool(getattr(app_state.config, "dark_theme", False)))
        self.app_state = app_state
        self.cfg = app_state.config
        self.palette = get_palette(bool(getattr(self.cfg, "dark_theme", False)))
        self.title("ChatClipper v" + APP_VERSION + " " + i18n.t("settings.title_suffix"))
        self.geometry("620x380")
        self.minsize(600, 370)
        self._apply_ttk_style()
        self._build()
        self._paint_tk_widgets()
        self._load_projects()
        self._load_params()
        self._snapshot_state()
        self._projects_changed = False
        self._dialog_open = False
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._center_window()
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.after(300, lambda: self.attributes("-topmost", False))
        try:
            self.grab_set()
        except Exception:
            pass
        try:
            self.focus_force()
        except Exception:
            pass

    # Open user manual for current locale
    def _on_help(self):
        lang = getattr(self.cfg, "locale", "en")
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "docs", f"manual-{lang}.html")
        if not os.path.exists(path):
            path = os.path.join(base, "docs", "manual-en.html")
        if os.path.exists(path):
            webbrowser.open(Path(path).resolve().as_uri())
        else:
            show_warning(self, "ChatClipper", "User manual not found", dark=self.cfg.dark_theme)

    # Open feedback form in default browser
    def _on_feedback(self):
        webbrowser.open("https://forms.gle/DWwChQb2e9o8Wrym6")

    # Open sponsor page in default browser
    def _on_sponsor(self):
        webbrowser.open("https://yoomoney.ru/to/4100119453410920")

    # Check GitHub for newer release in background thread
    def _on_check_update(self):
        if getattr(self, "_update_check_running", False):
            return
        self._update_check_running = True
        try:
            self.btn_check_update.configure(state="disabled")
        except Exception:
            pass
        threading.Thread(target=self._run_update_check, daemon=True).start()

    # Background worker: query GitHub and show result dialog on the main thread
    def _run_update_check(self):
        result = check_for_update()
        try:
            self.after(0, lambda: self._finish_update_check(result))
        except Exception:
            pass

    # Show result first, then re-enable the button (so it stays disabled while dialog is open)
    def _finish_update_check(self, result):
        self._show_update_result(result)
        self._update_check_running = False
        try:
            self.btn_check_update.configure(state="normal")
        except Exception:
            pass

    # Show update dialog: newer version with notes, or up-to-date message
    def _show_update_result(self, result):
        if result is None:
            messagebox.showinfo(i18n.t("upd.title"), i18n.t("upd.up_to_date") + " v" + APP_VERSION, parent=self)
            return
        dlg = tk.Toplevel(self)
        dlg.title(i18n.t("upd.title"))
        dlg.transient(self)
        dlg.grab_set()
        wrap = ttk.Frame(dlg, padding=12)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text=i18n.t("upd.available") + " v" + result["version"], font=("Segoe UI", 11, "bold")).pack(anchor="w")
        notes_text = tk.Text(wrap, width=60, height=12, wrap="word")
        notes_text.insert("1.0", result["notes"] or "")
        notes_text.configure(state="disabled")
        notes_text.pack(fill="both", expand=True, pady=(8, 8))
        btns = ttk.Frame(wrap)
        btns.pack(fill="x")
        ttk.Button(btns, text=i18n.t("upd.btn_later"), command=dlg.destroy).pack(side="right", padx=4)
        ttk.Button(btns, text=i18n.t("upd.btn_download"), command=lambda: (webbrowser.open(result["url"]), dlg.destroy())).pack(side="right", padx=4)
        center_window(dlg)
        dlg.lift()
        dlg.attributes("-topmost", True)
        dlg.after(300, lambda: dlg.attributes("-topmost", False))
        try:
            dlg.focus_force()
        except Exception:
            pass
        self.wait_window(dlg)

    # Build UI
    # Apply ttk style (clam) colored by current palette
    def _apply_ttk_style(self):
        pal = self.palette
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(".", background=pal["bg"], foreground=pal["fg"], fieldbackground=pal["field_bg"])
        style.configure("TFrame", background=pal["bg"])
        style.configure("TLabel", background=pal["bg"], foreground=pal["fg"])
        style.configure("TButton", background=pal["btn"], foreground=pal["fg"])
        style.map("TButton", background=[("active", pal["btn_hover"])])
        style.configure("TCheckbutton", background=pal["bg"], foreground=pal["fg"])
        style.map("TCheckbutton", background=[("active", pal["bg"])])
        style.configure("TEntry", fieldbackground=pal["entry_bg"], foreground=pal["entry_fg"])
        style.configure("TSpinbox", fieldbackground=pal["entry_bg"], foreground=pal["entry_fg"], background=pal["btn"])
        style.configure("TCombobox", fieldbackground=pal["entry_bg"], foreground=pal["entry_fg"], background=pal["btn"])
        style.configure("Treeview", background=pal["tree_bg"], fieldbackground=pal["tree_bg"], foreground=pal["tree_fg"])
        style.map("Treeview", background=[("selected", pal["select_bg"])], foreground=[("selected", pal["select_fg"])])
        style.configure("Treeview.Heading", background=pal["btn"], foreground=pal["fg"])
        style.configure("TScrollbar", background=pal["btn"], troughcolor=pal["trough"])
        style.map("TCombobox",
                  fieldbackground=[("readonly", pal["entry_bg"]), ("!disabled", pal["entry_bg"])],
                  foreground=[("readonly", pal["entry_fg"]), ("!disabled", pal["entry_fg"])],
                  background=[("readonly", pal["btn"]), ("!disabled", pal["btn"])])
        try:
            self.option_add("*TCombobox*Listbox.background", pal["entry_bg"])
            self.option_add("*TCombobox*Listbox.foreground", pal["entry_fg"])
            self.option_add("*TCombobox*Listbox.selectBackground", pal["select_bg"])
            self.option_add("*TCombobox*Listbox.selectForeground", pal["select_fg"])
        except Exception:
            pass
        try:
            self.configure(bg=pal["bg"])
        except Exception:
            pass
        self._paint_tk_widgets()

    # Repaint tk widgets (Checkbutton, Combobox dropdown) with current palette
    def _paint_tk_widgets(self):
        pal = self.palette
        for chk in (getattr(self, "chk_autostart", None), getattr(self, "chk_tray", None),
                    getattr(self, "chk_pandoc", None), getattr(self, "chk_sound", None)):
            if chk is None:
                continue
            try:
                chk.configure(bg=pal["bg"], fg=pal["fg"],
                              activebackground=pal["bg"], activeforeground=pal["fg"],
                              selectcolor=pal["btn"],
                              highlightthickness=0, bd=0)
            except Exception:
                pass
        for cb in (getattr(self, "cb_language", None), getattr(self, "cb_source", None),
                   getattr(self, "entry_alpha", None)):
            if cb is None:
                continue
            try:
                cb.configure(background=pal["btn"], foreground=pal["entry_fg"])
            except Exception:
                pass

    # Toggle dark/light theme; applies to all windows
    def _on_toggle_theme(self):
        self.cfg.dark_theme = not bool(getattr(self.cfg, "dark_theme", False))
        save_config(self.cfg)
        self.palette = get_palette(self.cfg.dark_theme)
        self._apply_ttk_style()
        self._paint_tk_widgets()
        apply_icon(self, dark_theme=self.cfg.dark_theme)
        try:
            self.btn_theme.configure(text="☀" if self.cfg.dark_theme else "🌙")
        except Exception:
            pass
        try:
            self.tree.tag_configure("main", font=("Segoe UI", 9, "bold"), foreground=self.palette["highlight_fg"])
        except Exception:
            pass
        self._load_projects()

    def _build(self):
        top = ttk.Frame(self, padding=(8, 8, 8, 0))
        top.pack(fill="x")
        ttk.Label(top, text=i18n.t("settings.projects"), font=("Segoe UI", 10, "bold")).pack(side="left", anchor="w")
        btn_sponsor = ttk.Button(top, text="🙏 " + i18n.t("settings.btn_donate"), command=self._on_sponsor)
        btn_sponsor.pack(side="right", padx=(0, 20))
        Tooltip(btn_sponsor, "Support the author")
        btn_help = ttk.Button(top, text="📖 " + i18n.t("settings.btn_help"), command=self._on_help)
        btn_help.pack(side="right", padx=(0, 4))
        Tooltip(btn_help, "Open user manual")
        btn_feedback = ttk.Button(top, text="💬 " + i18n.t("settings.btn_feedback"), command=self._on_feedback)
        btn_feedback.pack(side="right", padx=(0, 4))
        Tooltip(btn_feedback, "Send feedback")
        self.btn_check_update = ttk.Button(top, text="🔄 " + i18n.t("settings.btn_check_update"), command=self._on_check_update)
        self.btn_check_update.pack(side="right", padx=(0, 4))
        Tooltip(self.btn_check_update, "Check for updates")
        self.btn_theme = ttk.Button(top, text="☀" if getattr(self.cfg, "dark_theme", False) else "🌙", command=self._on_toggle_theme, width=3)
        self.btn_theme.pack(side="right", padx=(0, 4))
        Tooltip(self.btn_theme, "Toggle theme")

        mid = ttk.Frame(self, padding=8)
        mid.pack(fill="x")

        cols = ("name", "folder", "docx", "active", "main")
        self.tree = ttk.Treeview(mid, columns=cols, show="headings", height=5)
        self.tree.heading("name", text=i18n.t("settings.name"))
        self.tree.heading("folder", text=i18n.t("settings.folder"))
        self.tree.heading("docx", text=i18n.t("settings.file"))
        self.tree.heading("active", text="")
        self.tree.heading("main", text="")
        self.tree.column("name", width=150)
        self.tree.column("folder", width=180)
        self.tree.column("docx", width=220)
        self.tree.column("active", width=0, minwidth=0, stretch=False)
        self.tree.column("main", width=0, minwidth=0, stretch=False)
        self.tree.tag_configure("main", font=("Segoe UI", 9, "bold"), foreground=self.palette["highlight_fg"])
        self.tree.tag_configure("active", font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("inactive", font=("Segoe UI", 9, "normal"))
        self.tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        sb.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Button-3>", self._on_tree_right_click)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        btns = ttk.Frame(self, padding=8)
        btns.pack(fill="x")
        for i in range(5):
            btns.columnconfigure(i, weight=1)
        ttk.Button(btns, text=i18n.t("settings.btn_add"), command=self._on_add).grid(row=0, column=0, sticky="ew", padx=4)
        ttk.Button(btns, text=i18n.t("settings.btn_edit"), command=self._on_edit).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(btns, text=i18n.t("settings.btn_delete"), command=self._on_delete).grid(row=0, column=2, sticky="ew", padx=4)
        ttk.Button(btns, text=i18n.t("settings.btn_set_main"), command=self._on_set_main).grid(row=0, column=3, sticky="ew", padx=4)
        ttk.Button(btns, text=i18n.t("settings.btn_toggle_active"), command=self._on_toggle_active).grid(row=0, column=4, sticky="ew", padx=4)

        self.status_row = ttk.Frame(self, padding=(8, 0, 8, 8))
        self.status_row.pack(fill="x")

        params = ttk.Frame(self, padding=8)
        params.pack(fill="x", padx=8, pady=4)

        # Row 0: min length, popup seconds, transparency, autostart (right)
        row0 = ttk.Frame(params)
        row0.pack(fill="x", pady=4)

        # Autostart checkbox (Windows only), first on the left of row 0
        self.autostart_state = False
        self.var_autostart = tk.BooleanVar(value=False)
        self.chk_autostart = tk.Checkbutton(row0, text=i18n.t("settings.autostart"), variable=self.var_autostart, command=self._on_autostart_click, takefocus=0, highlightthickness=0, bd=0)
        self.chk_autostart.pack(side="left", padx=2)

        f_min = ttk.Frame(row0)
        f_min.pack(side="left", padx=4)
        ttk.Label(f_min, text=i18n.t("settings.min_len")).pack(side="left")
        self.var_min_len = tk.StringVar()
        self.entry_min_len = ttk.Entry(f_min, textvariable=self.var_min_len, width=3)
        self.entry_min_len.pack(side="left", padx=4)

        f_popup = ttk.Frame(row0)
        f_popup.pack(side="left", padx=4)
        ttk.Label(f_popup, text=i18n.t("settings.popup_sec")).pack(side="left")
        self.var_popup = tk.StringVar()
        self.entry_popup = ttk.Spinbox(f_popup, from_=1, to=10, increment=1, textvariable=self.var_popup, width=3)
        self.entry_popup.pack(side="left", padx=4)

        f_alpha = ttk.Frame(row0)
        f_alpha.pack(side="left", padx=4)
        ttk.Label(f_alpha, text=i18n.t("settings.alpha")).pack(side="left")
        self.var_alpha = tk.StringVar()
        self.entry_alpha = ttk.Combobox(f_alpha, textvariable=self.var_alpha, values=("30", "40", "50", "60", "70", "80", "90", "100"), state="readonly", width=3)
        self.entry_alpha.pack(side="left", padx=4)

        # Row 1: language, tray, pandoc, source
        row1 = ttk.Frame(params)
        row1.pack(fill="x", pady=4)

        ttk.Label(row1, text=i18n.t("settings.language")).pack(side="left", padx=(0, 4))
        self.var_language = tk.StringVar()
        self._lang_items = i18n.list_languages()
        self._lang_names = [n for _, n in self._lang_items]
        self.cb_language = ttk.Combobox(row1, textvariable=self.var_language, values=self._lang_names, state="readonly", width=8)
        self.cb_language.pack(side="left", padx=4)

        # Tray checkbox (Windows only, disabled on other OS)
        self.tray_state = True
        self.var_tray = tk.BooleanVar(value=True)
        self.chk_tray = tk.Checkbutton(row1, text=i18n.t("settings.tray"), variable=self.var_tray, command=self._on_tray_click, takefocus=0, highlightthickness=0, bd=0)
        self.chk_tray.pack(side="left", padx=8)
        if not IS_WINDOWS:
            self.chk_tray.configure(state="disabled")

        # Pandoc checkbox: enabled only when pandoc is available in PATH
        self.pandoc_available = is_pandoc_available()
        self.var_pandoc = tk.BooleanVar(value=False)
        self.chk_pandoc = tk.Checkbutton(row1, text=i18n.t("settings.use_pandoc"), variable=self.var_pandoc, takefocus=0, highlightthickness=0, bd=0)
        self.chk_pandoc.pack(side="left", padx=2)
        if not self.pandoc_available:
            self.chk_pandoc.configure(state="disabled")
        Tooltip(self.chk_pandoc, i18n.t("settings.use_pandoc_tip"))

        ttk.Label(row1, text=i18n.t("settings.source")).pack(side="left", padx=(8, 4))
        self.var_source = tk.StringVar()
        self._source_items = list_sources()
        self._source_names = [name for _, name in self._source_items]
        self.cb_source = ttk.Combobox(row1, textvariable=self.var_source, values=self._source_names, state="readonly", width=12)
        self.cb_source.pack(side="left", padx=4)

        # Sound checkbox + button to pick waiting sound
        self.var_sound = tk.BooleanVar(value=True)
        self.chk_sound = tk.Checkbutton(row1, text=i18n.t("settings.sound"), variable=self.var_sound, takefocus=0, highlightthickness=0, bd=0)
        self.chk_sound.pack(side="left", padx=(8, 2))
        Tooltip(self.chk_sound, i18n.t("settings.sound_tip"))
        self.btn_sound = ttk.Button(row1, text="...", width=3, command=self._on_pick_sound)
        self.btn_sound.pack(side="left", padx=2)

        bottom = ttk.Frame(self, padding=8)
        bottom.pack(fill="x")
        ttk.Button(bottom, text=i18n.t("settings.btn_save"), command=self._on_save).pack(side="right", padx=4)
        ttk.Button(bottom, text=i18n.t("settings.btn_cancel"), command=self._on_close).pack(side="right", padx=4)

    # Load projects into table
    def _load_projects(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main = self.cfg.main_project or i18n.t("settings.status_none")
        active_names = [p.name for p in self.cfg.projects if p.active]
        for child in self.status_row.winfo_children():
            child.destroy()
        ttk.Label(self.status_row, text=i18n.t("settings.status_main") + ": ").pack(side="left")
        ttk.Label(self.status_row, text=main, font=("Segoe UI", 9, "bold"), foreground="#FF8000").pack(side="left")
        ttk.Label(self.status_row, text="    |    " + i18n.t("settings.status_active") + ": ").pack(side="left")
        if active_names:
            for idx, name in enumerate(active_names):
                sep = ", " if idx > 0 else ""
                ttk.Label(self.status_row, text=sep + name, font=("Segoe UI", 9, "bold")).pack(side="left")
        else:
            ttk.Label(self.status_row, text=i18n.t("settings.status_no_active")).pack(side="left")
        main_name = self.cfg.main_project
        def sort_key(proj):
            if proj.name == main_name:
                return (0, proj.name.lower())
            if proj.active:
                return (1, proj.name.lower())
            return (2, proj.name.lower())
        for p in sorted(self.cfg.projects, key=sort_key):
            folder = p.folder
            if folder.upper().startswith(base.upper()):
                folder = "~" + folder[len(base):]
            if p.name == main_name:
                tag = "main"
            elif p.active:
                tag = "active"
            else:
                tag = "inactive"
            self.tree.insert("", "end", values=(p.name, folder, p.docx_name, "", ""), tags=(tag,))

    # Load capture params
    def _load_params(self):
        self.var_min_len.set(str(self.cfg.min_text_len))
        self.entry_min_len.delete(0, "end")
        self.entry_min_len.insert(0, str(self.cfg.min_text_len))
        self.var_popup.set(str(self.cfg.popup_seconds))
        self.entry_popup.delete(0, "end")
        self.entry_popup.insert(0, str(self.cfg.popup_seconds))
        alpha_pct = int(round(float(self.cfg.popup_alpha) * 100))
        self.var_alpha.set(str(alpha_pct))
        self.entry_alpha.set(str(alpha_pct))
        
        self.autostart_state = bool(self.cfg.autostart)
        self.var_autostart.set(self.autostart_state)
        self.tray_state = bool(getattr(self.cfg, "tray_enabled", True))
        self.var_tray.set(self.tray_state)
        use_pandoc_cfg = bool(getattr(self.cfg, "use_pandoc", False))
        if not self.pandoc_available:
            use_pandoc_cfg = False
        self.var_pandoc.set(use_pandoc_cfg)
        key = getattr(self.cfg, "active_source", "chrome")
        name = self._key_to_name(key)
        self.var_source.set(name)
        lang_key = getattr(self.cfg, "locale", "en")
        self.var_language.set(self._lang_key_to_name(lang_key))
        self.var_sound.set(bool(getattr(self.cfg, "sound_enabled", True)))
        self.update_idletasks()
        log.info("SettingsWindow._load_params: autostart=%s tray=%s source=%s locale=%s", self.cfg.autostart, self.tray_state, key, lang_key)

    # Refresh autostart state from config.json (called from tray)
    def refresh_from_config(self):
        try:
            # Use the shared cfg object, do not re-create it from disk
            self.cfg = self.app_state.config
            self.autostart_state = bool(self.cfg.autostart)
            self.var_autostart.set(self.autostart_state)
            self.tray_state = bool(getattr(self.cfg, "tray_enabled", True))
            self.var_tray.set(self.tray_state)
            self.update_idletasks()
            log.info("SettingsWindow.refresh_from_config: autostart=%s tray=%s", self.cfg.autostart, self.tray_state)
        except Exception as e:
            log.exception("SettingsWindow.refresh_from_config error: %s", e)

    # Map source key to display name
    def _key_to_name(self, key):
        for k, n in self._source_items:
            if k == key:
                return n
        return self._source_names[0] if self._source_names else ""

    # Map display name to source key
    def _name_to_key(self, name):
        for k, n in self._source_items:
            if n == name:
                return k
        return "chrome"

    # Map locale key to display name
    def _lang_key_to_name(self, key):
        for k, n in self._lang_items:
            if k == key:
                return n
        return "English"

    # Map display name to locale key
    def _lang_name_to_key(self, name):
        for k, n in self._lang_items:
            if n == name:
                return k
        return "en"

    # Autostart checkbox click: update local state
    def _on_autostart_click(self):
        self.autostart_state = bool(self.var_autostart.get())
        log.info("SettingsWindow._on_autostart_click: autostart_state=%s", self.autostart_state)

    # Click on tray checkbox - update own state
    def _on_tray_click(self):
        self.tray_state = bool(self.var_tray.get())
        log.info("SettingsWindow._on_tray_click: tray_state=%s", self.tray_state)

    # Get selected project
    def _selected_project(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], "values")
        return self.cfg.get_project(vals[0])

    # Right click on project row: context menu
    def _on_tree_right_click(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        self.tree.selection_set(row)
        project = self._selected_project()
        if not project:
            return
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=i18n.t("ctx.open_chat_file"), command=lambda p=project: self._open_docx(p))
        menu.add_command(label=i18n.t("ctx.open_folder"), command=lambda p=project: self._open_folder(p))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # Double click on project row: open its folder in file manager
    def _on_tree_double_click(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        self.tree.selection_set(row)
        project = self._selected_project()
        if not project:
            return
        self._open_folder(project)

    # Open project folder in system file manager
    def _open_folder(self, project):
        folder = project.folder
        if not os.path.isdir(folder):
            show_warning(self, "ChatClipper", i18n.t("msg.file_not_found") + folder, dark=self.cfg.dark_theme)
            return
        open_file(folder)

    # Open project .docx in associated application
    def _open_docx(self, project):
        path = project.docx_path
        if not os.path.exists(path):
            show_warning(self, "ChatClipper", i18n.t("msg.file_not_found") + path, dark=self.cfg.dark_theme)
            return
        try:
            open_file(path)
            log.info("Opened .docx: %s", path)
        except Exception as e:
            log.exception("Failed to open .docx %s: %s", path, e)
            show_warning(self, "ChatClipper", i18n.t("msg.cannot_open_file"), dark=self.cfg.dark_theme)

    # Add project
    def _on_add(self):
        dlg = ProjectDialog(self, None)
        self.wait_window(dlg.win)
        if dlg.result:
            if self.cfg.get_project(dlg.result.name):
                show_warning(self, "ChatClipper", i18n.t("msg.project_exists"), dark=self.cfg.dark_theme)
                return
            self.cfg.projects.append(dlg.result)
            if not self.cfg.main_project:
                self.cfg.main_project = dlg.result.name
            ensure_file_exists(dlg.result.docx_path)
            self._load_projects()
            self._projects_changed = True

    # Edit project
    def _on_edit(self):
        p = self._selected_project()
        if not p:
            return
        dlg = ProjectDialog(self, p)
        self.wait_window(dlg.win)
        if dlg.result:
            old_name = p.name
            p.name = dlg.result.name
            p.folder = dlg.result.folder
            p.docx_name = dlg.result.docx_name
            p.format = getattr(dlg.result, "format", "docx")
            if self.cfg.main_project == old_name:
                self.cfg.main_project = p.name
            ensure_file_exists(p.docx_path)
            self._load_projects()
            self._projects_changed = True

    # Delete project
    def _on_delete(self):
        p = self._selected_project()
        if not p:
            return
        if not ask_yesno(self, "ChatClipper", i18n.t("msg.delete_confirm") + p.name + "\"?", dark=self.cfg.dark_theme):
            return
        remaining = [x for x in self.cfg.projects if x.name != p.name]
        if self.cfg.main_project == p.name:
            new_main = None
            for x in remaining:
                if x.active:
                    new_main = x.name
                    break
            if new_main is None:
                show_warning(self, "ChatClipper", i18n.t("msg.cannot_delete_main"), dark=self.cfg.dark_theme)
                return
            self.cfg.main_project = new_main
        if not any(x.active for x in remaining):
            show_warning(self, "ChatClipper", i18n.t("msg.cannot_delete_last"), dark=self.cfg.dark_theme)
            return
        self.cfg.projects = remaining
        self._load_projects()
        self._projects_changed = True

    # Set project as main
    def _on_set_main(self):
        p = self._selected_project()
        if not p:
            return
        if not p.active:
            show_warning(self, "ChatClipper", i18n.t("msg.cannot_make_inactive_main"), dark=self.cfg.dark_theme)
            return
        self.cfg.main_project = p.name
        self._load_projects()
        self._projects_changed = True

    # Toggle project active
    def _on_toggle_active(self):
        p = self._selected_project()
        if not p:
            return
        if p.active and p.name == self.cfg.main_project:
            show_warning(self, "ChatClipper", i18n.t("msg.cannot_deactivate_main"), dark=self.cfg.dark_theme)
            return
        if p.active:
            active_count = len([x for x in self.cfg.projects if x.active])
            if active_count <= 1:
                show_warning(self, "ChatClipper", i18n.t("msg.cannot_deactivate_last"), dark=self.cfg.dark_theme)
                return
        p.active = not p.active
        self._load_projects()
        self._projects_changed = True

    # Open dialog to pick the waiting sound from sounds/*.wav
    def _on_pick_sound(self):
        dlg = SoundDialog(self, self.cfg)
        self.wait_window(dlg.win)
        if dlg.result is not None:
            self._pending_sound_name = dlg.result

    # Save settings
    # Snapshot current UI values to detect unsaved changes later
    def _snapshot_state(self):
        self._snap = {
            "min_len": self.entry_min_len.get().strip(),
            "popup": self.entry_popup.get().strip(),
            "alpha": self.entry_alpha.get().strip(),
            "autostart": bool(self.var_autostart.get()),
            "tray": bool(self.var_tray.get()),
            "source": self.var_source.get(),
            "language": self.var_language.get(),
            "pandoc": bool(self.var_pandoc.get()),
            "main": self.cfg.main_project,
            "locale": self.cfg.locale,
            "sound": bool(self.var_sound.get()),
        }

    # Return True if any tracked field or project list has changed
    def _is_dirty(self) -> bool:
        if getattr(self, "_projects_changed", False):
            return True
        snap = getattr(self, "_snap", None)
        if snap is None:
            return False
        cur = {
            "min_len": self.entry_min_len.get().strip(),
            "popup": self.entry_popup.get().strip(),
            "alpha": self.entry_alpha.get().strip(),
            "autostart": bool(self.var_autostart.get()),
            "tray": bool(self.var_tray.get()),
            "source": self.var_source.get(),
            "language": self.var_language.get(),
            "pandoc": bool(self.var_pandoc.get()),
            "main": self.cfg.main_project,
            "locale": self.cfg.locale,
            "sound": bool(self.var_sound.get()),
        }
        return cur != snap

    # Localized modal dialog with two buttons: Save / Cancel
    # Returns True (save & close), False (cancel = discard changes & close)
    def _ask_unsaved(self):
        dlg = tk.Toplevel(self)
        apply_icon(dlg)
        dlg.title("ChatClipper")
        dlg.transient(self)
        dlg.resizable(False, False)
        wrap = ttk.Frame(dlg, padding=16)
        wrap.pack()
        ttk.Label(wrap, text=i18n.t("settings.unsaved_msg"), font=("Segoe UI", 10)).pack(pady=(0, 12))
        btns = ttk.Frame(wrap)
        btns.pack()
        result = {"value": None}

        def choose(val):
            result["value"] = val
            dlg.destroy()

        ttk.Button(btns, text=i18n.t("settings.btn_save"), width=12, command=lambda: choose(True)).pack(side="left", padx=4)
        ttk.Button(btns, text=i18n.t("settings.btn_cancel"), width=12, command=lambda: choose(False)).pack(side="left", padx=4)
        dlg.protocol("WM_DELETE_WINDOW", lambda: choose(False))
        dlg.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - dlg.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        try:
            dlg.grab_set()
        except Exception:
            pass
        dlg.focus_force()
        self.wait_window(dlg)
        return result["value"]

    # Intercept window close: ask user about unsaved changes
    def _on_close(self):
        if self._dialog_open:
            return
        if not self._is_dirty():
            self.destroy()
            return
        self._dialog_open = True
        try:
            answer = self._ask_unsaved()
        finally:
            self._dialog_open = False
        if answer:
            self._on_save()
            try:
                if self.state() != "withdrawn":
                    return
            except Exception:
                pass
        self.destroy()

    # Localized Yes/No dialog for a restart-required change; returns True to restart
    def _ask_restart_confirm(self, msg_key: str = "settings.restart_confirm") -> bool:
        dlg = tk.Toplevel(self)
        apply_icon(dlg)
        dlg.title("ChatClipper")
        dlg.transient(self)
        dlg.resizable(False, False)
        wrap = ttk.Frame(dlg, padding=16)
        wrap.pack()
        ttk.Label(wrap, text=i18n.t(msg_key), font=("Segoe UI", 10)).pack(pady=(0, 12))
        btns = ttk.Frame(wrap)
        btns.pack()
        result = {"value": False}

        def choose(val):
            result["value"] = val
            dlg.destroy()

        ttk.Button(btns, text=i18n.t("settings.btn_yes"), width=12, command=lambda: choose(True)).pack(side="left", padx=4)
        ttk.Button(btns, text=i18n.t("settings.btn_no"), width=12, command=lambda: choose(False)).pack(side="left", padx=4)
        dlg.protocol("WM_DELETE_WINDOW", lambda: choose(False))
        dlg.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - dlg.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        try:
            dlg.grab_set()
        except Exception:
            pass
        dlg.focus_force()
        self.wait_window(dlg)
        return result["value"]

    def _on_save(self):
        try:
            min_len = int(self.entry_min_len.get().strip())
            if min_len < 1:
                min_len = 1
            if min_len > 100000:
                min_len = 100000
            popup_sec = int(self.entry_popup.get().strip())
            if popup_sec < 1:
                popup_sec = 1
            if popup_sec > 60:
                popup_sec = 60
            alpha_pct = int(self.entry_alpha.get().strip())
            if alpha_pct < 10:
                alpha_pct = 10
            if alpha_pct > 100:
                alpha_pct = 100
            self.cfg.min_text_len = min_len
            self.cfg.popup_seconds = popup_sec
            self.cfg.popup_alpha = alpha_pct / 100.0
        except ValueError:
            show_warning(self, "ChatClipper", i18n.t("msg.check_numbers"), dark=self.cfg.dark_theme)
            return
        old_autostart = self.cfg.autostart
        old_tray = bool(self._snap.get("tray", self.cfg.tray_enabled))
        new_tray = bool(self.tray_state)
        tray_restart = (old_tray != new_tray) and IS_WINDOWS
        new_locale = self._lang_name_to_key(self.var_language.get())
        locale_restart = self._snap.get("locale") != new_locale
        restart_needed = tray_restart or locale_restart
        if restart_needed:
            msg_key = "settings.restart_confirm" if tray_restart else "settings.restart_confirm_lang"
            if not self._ask_restart_confirm(msg_key):
                self.var_tray.set(old_tray)
                self.tray_state = old_tray
                old_lang_name = self._snap.get("language")
                if old_lang_name:
                    self.var_language.set(old_lang_name)
                return
        self.cfg.autostart = bool(self.autostart_state)
        self.cfg.tray_enabled = new_tray
        self.cfg.sound_enabled = bool(self.var_sound.get())
        pending_sound = getattr(self, "_pending_sound_name", None)
        if pending_sound is not None:
            self.cfg.sound_name = pending_sound
        self.cfg.active_source = self._name_to_key(self.var_source.get())
        self.cfg.locale = self._lang_name_to_key(self.var_language.get())
        self.cfg.use_pandoc = bool(self.var_pandoc.get()) and bool(self.pandoc_available)
        save_config(self.cfg)
        ensure_dirs()
        self.app_state.apply_sound()
        if old_autostart != self.cfg.autostart:
            autostart.apply(self.cfg.autostart)
        for p in self.cfg.projects:
            ensure_file_exists(p.docx_path)
        log.info("Settings saved: projects=%d, main=%s", len(self.cfg.projects), self.cfg.main_project)
        try:
            from config import flush_config
            flush_config()
        except Exception:
            pass
        self.app_state.reload_after_settings()
        try:
            self.grab_release()
        except Exception:
            pass
        self.withdraw()
        if restart_needed:
            try:
                send_ipc_command("restart")
            except Exception as e:
                log.exception("SettingsWindow: restart IPC error: %s", e)
        if self.cfg.main_project != self._snap.get("main"):
            try:
                from gui_popup import PopupWindow
                PopupWindow(self.app_state.root_hidden, self.app_state, on_choice=None, status_only=True)
            except Exception as e:
                log.exception("SettingsWindow: status popup error: %s", e)


# Dialog to pick the waiting sound from the sounds/ folder
class SoundDialog:
    # Initialize dialog with the current project config
    def __init__(self, parent, cfg):
        self.cfg = cfg
        self.result = None
        self.win = tk.Toplevel(parent)
        self.win.withdraw()
        apply_icon(self.win)
        self.win.title(i18n.t("settings.sound_dialog"))
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        wrap = ttk.Frame(self.win, padding=12)
        wrap.pack(fill="both", expand=True)

        self.var_choice = tk.StringVar(value=getattr(cfg, "sound_name", "") or "")
        self._files = self._list_sounds()
        if self._files:
            for name in self._files:
                label = self._humanize(name)
                ttk.Radiobutton(wrap, text=label, value=name, variable=self.var_choice).pack(anchor="w", pady=2)
        else:
            ttk.Label(wrap, text=i18n.t("settings.sound_none")).pack(anchor="w")

        btns = ttk.Frame(wrap)
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="OK", command=self._ok).pack(side="right", padx=4)
        ttk.Button(btns, text=i18n.t("settings.btn_cancel"), command=self._cancel).pack(side="right", padx=4)

        self.win.deiconify()
        center_window(self.win)
        try:
            self.win.focus_force()
        except Exception:
            pass

    # List .wav files in the sounds/ folder, sorted
    def _list_sounds(self):
        import os
        from config import BASE_DIR
        sounds_dir = os.path.join(BASE_DIR, "sounds")
        if not os.path.isdir(sounds_dir):
            return []
        return sorted([f for f in os.listdir(sounds_dir) if f.lower().endswith(".wav")])

    # Humanize file name: strip extension, replace - and _ with spaces, capitalize
    def _humanize(self, file_name: str) -> str:
        base = file_name.rsplit(".", 1)[0]
        s = base.replace("-", " ").replace("_", " ")
        return s.strip().capitalize()

    # Confirm selection
    def _ok(self):
        self.result = self.var_choice.get() or ""
        self.win.destroy()

    # Cancel dialog, leave result None
    def _cancel(self):
        self.result = None
        self.win.destroy()


# Project create/edit dialog class
class ProjectDialog:
    # Initialize dialog
    def __init__(self, parent, project):
        self.result = None
        self.dark = bool(getattr(getattr(parent, "cfg", None), "dark_theme", False))
        self.win = tk.Toplevel(parent)
        apply_icon(self.win, dark_theme=self.dark)
        self.win.title(i18n.t("project.title"))
        self.win.geometry("560x250")
        self.win.transient(parent)
        self.win.grab_set()
        apply_theme(self.win, self.dark)

        self.var_name = tk.StringVar(value=project.name if project else "")
        self.var_folder = tk.StringVar(value=project.folder if project else "")
        self.var_docx = tk.StringVar(value=project.docx_name if project else "")
        self.var_format = tk.StringVar(value=getattr(project, "format", "docx") if project else "docx")
        self.win.geometry("560x280")
        center_window(self.win)

        pad = {"padx": 8, "pady": 6}
        ttk.Label(self.win, text=i18n.t("project.name")).grid(row=0, column=0, sticky="w", **pad)
        self.entry_name = ttk.Entry(self.win, textvariable=self.var_name, width=50, state="readonly")
        self.entry_name.grid(row=0, column=1, columnspan=2, sticky="we", **pad)

        ttk.Label(self.win, text=i18n.t("project.folder")).grid(row=1, column=0, sticky="w", **pad)
        self.entry_folder = ttk.Entry(self.win, textvariable=self.var_folder, width=40)
        self.entry_folder.grid(row=1, column=1, sticky="we", **pad)
        ttk.Button(self.win, text=i18n.t("project.browse"), command=self._browse).grid(row=1, column=2, **pad)

        ttk.Label(self.win, text=i18n.t("project.file")).grid(row=2, column=0, sticky="w", **pad)
        self.entry_docx = ttk.Entry(self.win, textvariable=self.var_docx, width=50, state="readonly")
        self.entry_docx.grid(row=2, column=1, columnspan=2, sticky="we", **pad)

        ttk.Label(self.win, text=i18n.t("project.format")).grid(row=3, column=0, sticky="w", **pad)
        self.cb_format = ttk.Combobox(self.win, textvariable=self.var_format, values=["docx", "md", "txt"], state="readonly", width=10)
        self.cb_format.grid(row=3, column=1, sticky="w", **pad)

        btns = ttk.Frame(self.win)
        btns.grid(row=4, column=0, columnspan=3, sticky="e", padx=8, pady=8)
        ttk.Button(btns, text="OK", command=self._ok).pack(side="right", padx=4)
        ttk.Button(btns, text=i18n.t("project.cancel"), command=self.win.destroy).pack(side="right", padx=4)

        self.win.columnconfigure(1, weight=1)

    # Browse folder
    def _browse(self):
        try:
            self.win.grab_release()
        except Exception:
            pass
        initial = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.isdir(initial):
            initial = os.path.expanduser("~")
        folder = filedialog.askdirectory(parent=self.win, title=i18n.t("project.browse"), initialdir=initial, mustexist=True)
        try:
            self.win.grab_set()
        except Exception:
            pass
        if not folder:
            return
        folder = os.path.normpath(folder)
        name = os.path.basename(folder)
        fmt = self.var_format.get() or "docx"
        file_name = f"{name}-chat.{fmt}"
        self.var_folder.set(folder)
        self.var_name.set(name)
        self.var_docx.set(file_name)
        self.entry_folder.configure(state="normal")
        self.entry_folder.delete(0, "end")
        self.entry_folder.insert(0, folder)
        self.entry_name.configure(state="normal")
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, name)
        self.entry_name.configure(state="readonly")
        self.entry_docx.configure(state="normal")
        self.entry_docx.delete(0, "end")
        self.entry_docx.insert(0, file_name)
        self.entry_docx.configure(state="readonly")
        self.win.update_idletasks()
        self.win.lift()
        self.win.focus_force()

    # Confirm
    def _ok(self):
        name = self.var_name.get().strip()
        folder = self.var_folder.get().strip()
        docx = self.var_docx.get().strip()
        if not name:
            show_warning(self.win, "ChatClipper", i18n.t("msg.name_undefined"), dark=self.dark)
            return
        if not folder:
            show_warning(self.win, "ChatClipper", i18n.t("msg.folder_required"), dark=self.dark)
            return
        if not os.path.isdir(folder):
            if not ask_yesno(self.win, "ChatClipper", i18n.t("msg.folder_missing"), dark=self.dark):
                return
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as e:
                show_warning(self.win, "ChatClipper", i18n.t("msg.folder_create_fail") + str(e), dark=self.dark)
                return
        fmt = self.var_format.get() or "docx"
        if not docx.lower().endswith("." + fmt.lower()):
            docx = docx.rsplit(".", 1)[0] + "." + fmt
        self.result = Project(name=name, folder=folder, docx_name=docx, active=True, format=fmt)
        self.win.destroy()