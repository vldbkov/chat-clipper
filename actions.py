# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Action registry: handlers for IPC commands from tray and panel
import os
import sys
import subprocess
from tkinter import messagebox

from logger import log
from config import save_config, flush_config
from project_service import set_main, write_to_project
from gui_popup import PopupWindow
from gui_settings import SettingsWindow
from gui_undo import UndoDialog
from platform_utils import detached_creation_flags
import i18n
import undo
import autostart


# Handle status: show popup in status-only mode
def action_status(state):
    try:
        PopupWindow(state.root_hidden, state, on_choice=None, status_only=True)
    except Exception as e:
        log.exception("Status popup error: %s", e)


# Handle undo: transfer last entry to another project
def action_undo(state):
    last = undo.get_last()
    if not last:
        messagebox.showinfo("ChatClipper", i18n.t("msg.no_last_record"))
        return
    old_project = last.get("project", "")
    candidates = [p for p in state.config.active_projects() if p.name != old_project]
    if not candidates:
        messagebox.showinfo("ChatClipper", i18n.t("msg.no_other_project"))
        return
    dlg = UndoDialog(state.root_hidden, state, old_project, candidates)
    state.root_hidden.wait_window(dlg.win)
    if not dlg.result:
        return
    target_project = dlg.result
    if not messagebox.askyesno("ChatClipper", i18n.t("msg.move_confirm")):
        return
    ok = undo.undo_last(target_project.name, target_project.docx_path)
    if ok:
        log.info("undo: transferred to '%s'", target_project.name)
        messagebox.showinfo("ChatClipper", i18n.t("msg.moved_ok") + target_project.name + "'.")
    else:
        log.error("undo: transfer failed")
        messagebox.showerror("ChatClipper", i18n.t("msg.moved_fail"))


# Handle popup: choose project and write text
def action_popup(state):
    text = None
    html = None
    with state.pending_lock:
        text = state.pending_popup_text
        html = state.pending_popup_html
        state.pending_popup_text = None
        state.pending_popup_html = None
    if not text:
        return
    try:
        PopupWindow(state.root_hidden, state,
                    lambda name, t=text, h=(html or ""): _popup_choice(state, name, t, h))
    except Exception as e:
        log.exception("Popup open error: %s", e)


# Internal: process popup choice
def _popup_choice(state, name, text, html):
    if not name:
        name = state.config.main_project
    project = state.config.get_project(name)
    if project is None:
        log.error("popup_choice: project '%s' not found", name)
        return
    set_main(state.config, name)
    write_to_project(state.config, state.docx_writer, project, text, html)


# Handle settings: open or bring to front
def action_settings(state):
    try:
        if state.settings_window is None or not state.settings_window.winfo_exists():
            state.settings_window = SettingsWindow(state.root_hidden, state)
        else:
            state.settings_window.deiconify()
            state.settings_window.lift()
    except Exception as e:
        log.exception("Settings open error: %s", e)


# Handle pause toggle
def action_toggle_pause(state):
    state.paused = not state.paused
    state.config.paused = state.paused
    save_config(state.config)
    log.info("GUI: pause = %s", state.paused)
    state.apply_sound()
    if state.tray_icon is not None:
        try:
            state.tray_icon.update_menu()
        except Exception:
            pass
    try:
        PopupWindow(state.root_hidden, state, on_choice=None, status_only=True)
    except Exception as e:
        log.exception("Pause status popup error: %s", e)


# Handle autostart toggle
def action_toggle_autostart(state):
    new_val = not state.config.autostart
    state.config.autostart = new_val
    save_config(state.config)
    flush_config()
    autostart.apply(new_val)
    if state.settings_window is not None:
        try:
            state.settings_window.refresh_from_config()
        except Exception as e:
            log.exception("Cannot refresh settings window: %s", e)
    log.info("GUI: autostart = %s", new_val)


# Handle exit
def action_exit(state):
    log.info("GUI: exit command received")
    if state.mouse_hook:
        state.mouse_hook.force_stop()
    try:
        state.docx_writer.close()
    except Exception:
        pass
    try:
        state.hash_ring.flush()
    except Exception:
        pass
    try:
        flush_config()
    except Exception:
        pass
    try:
        state.root_hidden.destroy()
    except Exception:
        pass
    os._exit(0)


# Handle restart
def action_restart(state):
    log.info("GUI: restart command received")
    if state.mouse_hook:
        state.mouse_hook.force_stop()
    try:
        state.docx_writer.close()
    except Exception:
        pass
    try:
        state.hash_ring.flush()
    except Exception:
        pass
    try:
        import psutil
        for p in psutil.process_iter(['name', 'cmdline']):
            try:
                if p.info.get('name', '').lower().startswith('python'):
                    cmd = ' '.join(p.info.get('cmdline') or [])
                    if 'main.py' in cmd and '--tray' in cmd:
                        p.kill()
                        log.info("Killed old tray process pid=%d", p.pid)
            except Exception:
                pass
    except Exception as e:
        log.exception("Kill tray error: %s", e)
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        main_py = os.path.join(base_dir, "main.py")
        creationflags = detached_creation_flags()
        subprocess.Popen([sys.executable, main_py], creationflags=creationflags, close_fds=True)
    except Exception as e:
        log.exception("Cannot start new instance on restart: %s", e)
    try:
        flush_config()
    except Exception:
        pass
    os._exit(0)


# Action registry: map IPC command to handler
ACTIONS = {
    "status": action_status,
    "undo": action_undo,
    "popup": action_popup,
    "settings": action_settings,
    "toggle_pause": action_toggle_pause,
    "toggle_autostart": action_toggle_autostart,
    "exit": action_exit,
    "restart": action_restart,
}