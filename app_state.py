# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Shared application state for tray and GUI processes
import threading

from logger import log
from config import load_config
from hashes import HashRing
from docx_writer import DocxWriter


# Global application state shared across modules within a process
class AppState:
    def __init__(self):
        self.config = load_config()
        self.paused = bool(self.config.paused)
        self.tray_icon = None
        self.root_hidden = None
        self.hash_ring = HashRing(size=self.config.hash_ring_size)
        self.mouse_hook = None
        self.docx_writer = DocxWriter()
        self.pending_action = None
        self.pending_lock = threading.Lock()
        self.pending_popup_text = None
        self.pending_popup_html = None
        self.is_tray_process = False
        self.is_gui_process = False
        self.tray_started = False
        self.settings_window = None

    # Apply current config values to runtime components after settings save
    def reload_after_settings(self):
        self.hash_ring.set_size(self.config.hash_ring_size)
        if self.mouse_hook:
            self.mouse_hook.min_text_len = self.config.min_text_len
        self.apply_sound()
        log.info("Settings applied: projects=%d", len(self.config.projects))

    # Start or stop waiting sound according to config and paused state
    def apply_sound(self):
        try:
            from sound_player import player
            from config import BASE_DIR, DEFAULT_SOUND_NAME
            if not getattr(self.config, "sound_enabled", True):
                player.stop()
                return
            if self.paused:
                player.stop()
                return
            name = getattr(self.config, "sound_name", "") or ""
            if not name:
                name = DEFAULT_SOUND_NAME
            if not name:
                player.stop()
                return
            import os
            path = os.path.join(BASE_DIR, "sounds", name)
            player.start(path)
        except Exception as e:
            log.exception("app_state.apply_sound error: %s", e)


# Single global instance
state = AppState()