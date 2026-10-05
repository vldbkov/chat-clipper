# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# GUI process: Tk main loop, mouse hook, IPC server, dispatcher
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

from logger import log
from config import ensure_dirs
from ipc_server import start_ipc_server
from single_instance import acquire_single_instance
from mouse_hook import MouseHook
from gui_popup import PopupWindow
from control_panel import ControlPanel
from app_state import state
from ui_helpers import apply_icon
from platform_utils import IS_WINDOWS
import actions
import autostart


# Handle copy from Chrome: dedup, hash, queue popup action
def on_copy_caught(text: str, html: str = "") -> None:
    if state.paused:
        log.info("Pause active - copy ignored")
        return
    if state.hash_ring.is_duplicate(text):
        log.info("Duplicate by CRC32 - skip (length=%d)", len(text))
        return
    h = state.hash_ring.add(text)
    log.info("Copy accepted: plain=%d html=%d CRC32=0x%08X", len(text), len(html), h)
    if state.config.get_main() is None:
        log.warning("Main project not set - write skipped")
        return
    with state.pending_lock:
        state.pending_popup_text = text
        state.pending_popup_html = html
        state.pending_action = "popup"


# Thin dispatcher: read command from tray/panel and call matching action
def poll_pending_actions():
    action = None
    with state.pending_lock:
        if state.pending_action:
            action = state.pending_action
            state.pending_action = None

    if action:
        log.info("GUI: handle action '%s'", action)
        handler = actions.ACTIONS.get(action)
        if handler is None:
            log.warning("GUI: unknown action '%s'", action)
        else:
            try:
                handler(state)
            except Exception as e:
                log.exception("Action '%s' error: %s", action, e)

    if state.root_hidden:
        state.root_hidden.after(100, poll_pending_actions)


# Background thread: flush pending queue to .docx
def sync_queue_loop():
    while True:
        try:
            time.sleep(3.0)
            n = state.docx_writer.sync_all()
            if n:
                log.info("sync_queue_loop: flushed %d items", n)
        except Exception as e:
            log.exception("sync_queue_loop error: %s", e)


# Register AppUserModelID on Windows so the taskbar uses our icon
# Safe no-op on non-Windows

def _set_windows_app_id() -> None:
    if not IS_WINDOWS:
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ChatClipper.App")
    except Exception as e:
        log.debug("AppUserModelID set failed: %s", e)


# Show status popup once at startup
def show_startup_status():
    try:
        PopupWindow(state.root_hidden, state, on_choice=None, status_only=True)
        log.info("Startup status popup shown")
    except Exception as e:
        log.exception("Startup status error: %s", e)


# Run GUI process (main thread of parent process)
def run_gui_process():
    state.is_gui_process = True

    if not acquire_single_instance():
        r = tk.Tk()
        r.withdraw()
        messagebox.showwarning("ChatClipper", "ChatClipper уже запущен.")
        r.destroy()
        sys.exit(0)

    ensure_dirs()
    state.apply_sound()
    autostart.apply(state.config.autostart)

    start_ipc_server(state)

    sync_thread = threading.Thread(target=sync_queue_loop, daemon=True)
    sync_thread.start()

    state.mouse_hook = MouseHook(on_copy_callback=on_copy_caught, min_text_len=state.config.min_text_len, app_state=state)
    state.mouse_hook.start()

    _set_windows_app_id()
    root = tk.Tk()
    root.withdraw()
    apply_icon(root)
    state.root_hidden = root
    root.after(100, poll_pending_actions)
    root.after(500, show_startup_status)
    if not state.tray_started:
        try:
            root.after(700, lambda: ControlPanel(root, state))
            log.info("ControlPanel shown (tray disabled)")
        except Exception as e:
            log.exception("ControlPanel error: %s", e)
    log.info("=== ChatClipper GUI started ===")
    root.mainloop()
    log.info("=== ChatClipper stopped ===")
    try:
        state.docx_writer.close()
    except Exception:
        pass
    try:
        state.hash_ring.flush()
    except Exception:
        pass
    os._exit(0)