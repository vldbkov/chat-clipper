# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Background playback of a looping WAV file; cross-platform, no heavy deps
import os
import subprocess
import sys
import threading
import time

from logger import log


IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"


# Singleton player that loops a WAV file until stop() is called
class SoundPlayer:
    # Initialize player state; no sound is playing yet
    def __init__(self):
        self._lock = threading.RLock()
        self._thread = None
        self._stop_event = threading.Event()
        self._current_path = ""

    # Start looping the given WAV file; no-op if already playing the same file
    def start(self, path: str) -> None:
        if not path or not os.path.isfile(path):
            log.debug("SoundPlayer.start: file not found: %s", path)
            return
        with self._lock:
            if self._thread is not None and self._current_path == path:
                return
            self.stop()
            self._current_path = path
            self._stop_event = threading.Event()
            self._thread = threading.Thread(target=self._loop, args=(path, self._stop_event), daemon=True)
            self._thread.start()
            log.info("SoundPlayer: started %s", os.path.basename(path))

    # Stop playback; safe to call when nothing is playing
    def stop(self) -> None:
        with self._lock:
            if self._thread is None:
                return
            self._stop_event.set()
            self._thread = None
            self._current_path = ""
        log.info("SoundPlayer: stopped")

    # Return True if a sound is currently playing
    def is_playing(self) -> bool:
        with self._lock:
            return self._thread is not None

    # Loop body: dispatch per OS; exits when stop_event is set
    def _loop(self, path: str, stop_event: threading.Event) -> None:
        if IS_WINDOWS:
            self._loop_windows(path, stop_event)
        elif IS_MAC:
            self._loop_afplay(path, stop_event)
        else:
            self._loop_posix(path, stop_event)

    # Windows: use winsound with native loop flag
    def _loop_windows(self, path: str, stop_event: threading.Event) -> None:
        try:
            import winsound
        except Exception as e:
            log.debug("SoundPlayer: winsound unavailable: %s", e)
            return
        try:
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
        except Exception as e:
            log.debug("SoundPlayer: winsound error: %s", e)
            return
        while not stop_event.is_set():
            time.sleep(0.2)
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass

    # macOS: afplay via subprocess; emulate loop by restarting
    def _loop_afplay(self, path: str, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            try:
                proc = subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                log.debug("SoundPlayer: afplay error: %s", e)
                return
            while proc.poll() is None and not stop_event.is_set():
                time.sleep(0.1)
            if stop_event.is_set():
                try:
                    proc.terminate()
                except Exception:
                    pass
                return

    # POSIX (Linux/WSL): paplay or aplay, loop via restart
    def _loop_posix(self, path: str, stop_event: threading.Event) -> None:
        players = [["paplay", path], ["aplay", "-q", path]]
        chosen = None
        for cmd in players:
            try:
                subprocess.run([cmd[0], "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                chosen = cmd
                break
            except Exception:
                continue
        if chosen is None:
            log.debug("SoundPlayer: no paplay/aplay available")
            return
        while not stop_event.is_set():
            try:
                proc = subprocess.Popen(chosen, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                log.debug("SoundPlayer: posix play error: %s", e)
                return
            while proc.poll() is None and not stop_event.is_set():
                time.sleep(0.1)
            if stop_event.is_set():
                try:
                    proc.terminate()
                except Exception:
                    pass
                return


# Global singleton
player = SoundPlayer()