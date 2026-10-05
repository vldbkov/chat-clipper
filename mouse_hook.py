# Module tracking single LMB click in Chrome window and clipboard changes
import threading
import time

from pynput import mouse

from clipboard import get_text_with_format
from sources.source_factory import get_source
from logger import log


CLICK_WINDOW_MS = 400          # окно после клика, в течение которого ждём изменение буфера


# LMB hook class
class MouseHook:
    # Initialize hook
    def __init__(self, on_copy_callback, min_text_len: int = 50, app_state=None):
        self.on_copy_callback = on_copy_callback
        self.min_text_len = min_text_len
        self.app_state = app_state
        self.listener = None
        self.pending_until = 0.0
        self.last_buffer = ""
        self.accepted_buffer = ""
        self.timer = None
        self._lock = threading.Lock()
        self._source_cache = None
        self._source_cache_until = 0.0

    # Check that the click was made in the configured source window
    def _is_source_active(self) -> bool:
        try:
            key = getattr(self.app_state.config, "active_source", "chrome")
        except Exception:
            key = "chrome"
        now = time.time()
        if self._source_cache is not None and now < self._source_cache_until:
            return self._source_cache
        src = get_source(key)
        result = src.is_active()
        self._source_cache = result
        self._source_cache_until = now + 0.2
        return result

    # Single LMB click handler
    def _on_click(self, x, y, button, pressed):
        if button != mouse.Button.left:
            return
        if not pressed:
            return
        if not self._is_source_active():
            return
        with self._lock:
            self.pending_until = time.time() + CLICK_WINDOW_MS / 1000.0
        # Immediate check: clipboard is usually already updated by Chrome
        self._check_buffer()
        # Fallback timer in case the clipboard updates a bit later
        self._schedule_check()

    # Schedule clipboard check after wait window
    def _schedule_check(self):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = threading.Timer(CLICK_WINDOW_MS / 1000.0 + 0.05, self._check_buffer)
        self.timer.daemon = True
        self.timer.start()

    # Check buffer change after click
    def _check_buffer(self):
        with self._lock:
            if time.time() > self.pending_until + 0.2:
                return
            plain, html = get_text_with_format()
            changed = plain != self.accepted_buffer and len(plain) > 0
            log.debug("MouseHook._check_buffer: accepted=%d now=%d changed=%s", len(self.accepted_buffer), len(plain), changed)
        if not changed:
            return
        if len(plain) < self.min_text_len:
            log.info("Copy ignored: length %d < %d", len(plain), self.min_text_len)
            return
        self.accepted_buffer = plain
        log.info("Copy caught from Chrome: plain=%d html=%d", len(plain), len(html))
        try:
            self.on_copy_callback(plain, html)
        except Exception as e:
            log.exception("Error in copy callback: %s", e)

    # Start hook
    def start(self):
        self.listener = mouse.Listener(on_click=self._on_click)
        self.listener.daemon = True
        self.listener.start()
        log.info("MouseHook started (Chrome, window %d ms)", CLICK_WINDOW_MS)

    # Stop hook
    def stop(self):
        try:
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None
        except Exception:
            pass
        if self.listener:
            try:
                self.listener.stop()
            except Exception as e:
                log.exception("listener.stop error: %s", e)
            try:
                self.listener.join(timeout=1.0)
            except Exception:
                pass
            self.listener = None
            log.info("MouseHook stopped")

    # Force-stop hook ensuring removal
    def force_stop(self):
        try:
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None
        except Exception:
            pass
        try:
            if self.listener:
                self.listener.stop()
        except Exception:
            pass
        try:
            from pynput import mouse as _mouse
            for _listener in list(getattr(_mouse.Listener, "_listeners", []) or []):
                try:
                    _listener.stop()
                except Exception:
                    pass
        except Exception:
            pass
        self.listener = None
        log.info("MouseHook force_stop done")