# Cross-platform wrappers: OS detection, clipboard, active window, process launch
import os
import subprocess
import sys

from logger import log


IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")
IS_MAC = sys.platform == "darwin"


# Read clipboard text
def get_clipboard_text() -> str:
    if IS_WINDOWS:
        try:
            import win32clipboard
            import win32con
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                    data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                    return data if isinstance(data, str) else ""
                return ""
            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:
            log.exception("get_clipboard_text (Windows) error: %s", e)
            return ""
    if IS_LINUX:
        try:
            out = subprocess.check_output(["xclip", "-selection", "clipboard", "-o"], stderr=subprocess.DEVNULL)
            return out.decode("utf-8", errors="replace")
        except Exception:
            pass
        try:
            out = subprocess.check_output(["xsel", "--clipboard", "--output"], stderr=subprocess.DEVNULL)
            return out.decode("utf-8", errors="replace")
        except Exception:
            pass
    try:
        import pyperclip
        return pyperclip.paste() or ""
    except Exception as e:
        log.exception("get_clipboard_text error: %s", e)
        return ""


# Read clipboard HTML
# Windows: HTML Format (CF_HTML), fragment extracted between StartFragment and EndFragment
# Linux: xclip -selection clipboard -t text/html -o
# Returns HTML string or empty string
def get_clipboard_html() -> str:
    if IS_WINDOWS:
        try:
            import win32clipboard
            fmt = win32clipboard.RegisterClipboardFormat("HTML Format")
            win32clipboard.OpenClipboard()
            try:
                if not win32clipboard.IsClipboardFormatAvailable(fmt):
                    names = _list_clipboard_formats()
                    log.debug("get_clipboard_html: HTML Format not available. Formats: %s", names)
                    return ""
                raw = win32clipboard.GetClipboardData(fmt)
            finally:
                win32clipboard.CloseClipboard()
            if isinstance(raw, bytes):
                text = raw.decode("utf-8", errors="replace")
            else:
                text = str(raw)
            return _extract_html_fragment(text)
        except Exception as e:
            log.exception("get_clipboard_html (Windows) error: %s", e)
            return ""
    if IS_LINUX:
        try:
            out = subprocess.check_output(["xclip", "-selection", "clipboard", "-t", "text/html", "-o"], stderr=subprocess.DEVNULL)
            return out.decode("utf-8", errors="replace")
        except Exception as e:
            log.exception("get_clipboard_html (Linux) error: %s", e)
            return ""
    if IS_MAC:
        try:
            out = subprocess.check_output(["osascript", "-e", 'the clipboard as «class HTML»'], stderr=subprocess.DEVNULL)
            return out.decode("utf-8", errors="replace")
        except Exception as e:
            log.exception("get_clipboard_html (macOS) error: %s", e)
            return ""
    return ""


# List all available clipboard format names (Windows only, for diagnostics)
def _list_clipboard_formats() -> list:
    try:
        import win32clipboard
        formats = []
        fmt = 0
        while True:
            fmt = win32clipboard.EnumClipboardFormats(fmt)
            if fmt == 0:
                break
            try:
                name = win32clipboard.GetClipboardFormatName(fmt)
            except Exception:
                name = "(id=%d)" % fmt
            formats.append(name)
        return formats
    except Exception as e:
        return ["list error: " + str(e)]


# Extract HTML fragment from Windows CF_HTML header
# Returns only content between StartFragment and EndFragment
def _extract_html_fragment(cf_html: str) -> str:
    try:
        start_marker = "StartFragment:"
        end_marker = "EndFragment:"
        start_pos = cf_html.find(start_marker)
        end_pos = cf_html.find(end_marker)
        if start_pos < 0 or end_pos < 0:
            return cf_html
        start_line_end = cf_html.find("\n", start_pos)
        end_line_end = cf_html.find("\n", end_pos)
        if start_line_end < 0 or end_line_end < 0:
            return cf_html
        start_offset = int(cf_html[start_pos + len(start_marker):start_line_end].strip())
        end_offset = int(cf_html[end_pos + len(end_marker):end_line_end].strip())
        return cf_html[start_offset:end_offset]
    except Exception:
        return cf_html


# Try to get active window PID via python-xlib
# Returns PID or 0 if library is unavailable or an error occurs
def _get_active_pid_xlib() -> int:
    try:
        from Xlib import display, X
        from Xlib.error import XError
    except Exception:
        return 0
    try:
        d = display.Display()
        root = d.screen().root
        atom = d.intern_atom("_NET_ACTIVE_WINDOW")
        pid_atom = d.intern_atom("_NET_WM_PID")
        prop = root.get_full_property(atom, X.AnyPropertyType)
        if prop is None or not prop.value:
            return 0
        win_id = prop.value[0]
        if not win_id:
            return 0
        win = d.create_resource_object("window", win_id)
        pid_prop = win.get_full_property(pid_atom, X.AnyPropertyType)
        if pid_prop is None or not pid_prop.value:
            return 0
        return int(pid_prop.value[0])
    except XError:
        return 0
    except Exception:
        return 0


# Get active window process name (lowercase)
def get_active_process_name() -> str:
    if IS_WINDOWS:
        try:
            import win32gui
            import win32process
            import psutil
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return psutil.Process(pid).name().lower()
        except Exception:
            return ""
    if IS_LINUX:
        pid = _get_active_pid_xlib()
        if not pid:
            try:
                import subprocess as sp
                out = sp.check_output(["xdotool", "getactivewindow", "getwindowpid"], stderr=sp.DEVNULL)
                pid = int(out.decode("utf-8").strip())
            except Exception:
                return ""
        try:
            import psutil
            return psutil.Process(pid).name().lower()
        except Exception:
            return ""
    if IS_MAC:
        try:
            import subprocess as sp
            out = sp.check_output(["osascript", "-e", 'tell application "System Events" to get name of first process whose frontmost is true'], stderr=sp.DEVNULL)
            return out.decode("utf-8").strip().lower()
        except Exception:
            return ""
    return ""


# Known install locations for pandoc, checked if not found in PATH
def _pandoc_candidate_paths() -> list:
    candidates = []
    if IS_WINDOWS:
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            candidates.append(os.path.join(local, "Pandoc", "pandoc.exe"))
        for base in (os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", "")):
            if base:
                candidates.append(os.path.join(base, "Pandoc", "pandoc.exe"))
    else:
        candidates.extend([
            "/usr/bin/pandoc",
            "/usr/local/bin/pandoc",
            "/opt/homebrew/bin/pandoc",
        ])
    return candidates


# Check whether pandoc is available in PATH or in a known install location
def is_pandoc_available() -> bool:
    return get_pandoc_path() is not None


# Return path to pandoc or None
def get_pandoc_path():
    import shutil
    found = shutil.which("pandoc")
    if found:
        return found
    for path in _pandoc_candidate_paths():
        if os.path.isfile(path):
            return path
    return None


# Creation flags for detached process without console
def detached_creation_flags() -> int:
    if IS_WINDOWS:
        return 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    return 0


# Open file in associated application
def open_file(path: str) -> None:
    if IS_WINDOWS:
        os.startfile(path)
        return
    if IS_MAC:
        subprocess.Popen(["open", path])
        return
    subprocess.Popen(["xdg-open", path])