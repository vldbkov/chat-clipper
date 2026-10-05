import os
import sys
import tempfile

from logger import log


IS_WINDOWS = sys.platform.startswith("win")
MUTEX_NAME = "Global\\ChatClipper_SingleInstance_Mutex"
LOCK_FILE = os.path.join(tempfile.gettempdir(), "chatclipper.lock")

_mutex_handle = None
_lock_file_handle = None


# Acquire single instance lock (cross-platform)
def acquire_single_instance() -> bool:
    if IS_WINDOWS:
        return _acquire_windows()
    return _acquire_posix()


# Windows: global mutex via Win API
# Returns True if this is the first instance
def _acquire_windows() -> bool:
    global _mutex_handle
    try:
        import win32event
        import win32api
        import winerror
        _mutex_handle = win32event.CreateMutex(None, False, MUTEX_NAME)
        last_error = win32api.GetLastError()
        if last_error == winerror.ERROR_ALREADY_EXISTS:
            log.warning("ChatClipper already running - second instance will not start")
            return False
        log.info("Mutex acquired - first instance started")
        return True
    except Exception as e:
        log.exception("Mutex creation error: %s", e)
        return True


# Linux/macOS: file lock via fcntl.flock
# Returns True if this is the first instance
def _acquire_posix() -> bool:
    global _lock_file_handle
    try:
        import fcntl
        _lock_file_handle = open(LOCK_FILE, "a+")
        try:
            fcntl.flock(_lock_file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log.warning("ChatClipper already running - second instance will not start")
            return False
        _lock_file_handle.seek(0)
        _lock_file_handle.truncate()
        _lock_file_handle.write(str(os.getpid()))
        _lock_file_handle.flush()
        log.info("File lock acquired - first instance started")
        return True
    except Exception as e:
        log.exception("File lock error: %s", e)
        return True