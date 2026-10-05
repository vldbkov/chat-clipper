import os
import sys

from logger import log


IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")
IS_MAC = sys.platform == "darwin"

APP_NAME = "ChatClipper"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

LINUX_AUTOSTART_DIR = os.path.join(os.path.expanduser("~"), ".config", "autostart")
LINUX_DESKTOP_FILE = os.path.join(LINUX_AUTOSTART_DIR, "chatclipper.desktop")
MAC_LAUNCH_AGENTS = os.path.join(os.path.expanduser("~"), "Library", "LaunchAgents")
MAC_PLIST_FILE = os.path.join(MAC_LAUNCH_AGENTS, "com.chatclipper.plist")


# Path to pythonw.exe on Windows (or plain pythonw not found)
def _pythonw_path() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    exe = sys.executable
    pythonw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    return pythonw if os.path.exists(pythonw) else exe


# Command to launch main.py on Windows
def _command_windows() -> str:
    main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    return f'"{_pythonw_path()}" "{main_py}"'


# Check whether autostart is enabled
def is_enabled() -> bool:
    if IS_WINDOWS:
        return _is_enabled_windows()
    if IS_LINUX:
        return os.path.exists(LINUX_DESKTOP_FILE)
    if IS_MAC:
        return os.path.exists(MAC_PLIST_FILE)
    return False


# Enable autostart
def enable() -> bool:
    if IS_WINDOWS:
        return _enable_windows()
    if IS_LINUX:
        return _enable_linux()
    if IS_MAC:
        return _enable_mac()
    return False


# Disable autostart
def disable() -> bool:
    if IS_WINDOWS:
        return _disable_windows()
    if IS_LINUX:
        return _disable_linux()
    if IS_MAC:
        return _disable_mac()
    return False


# Apply autostart state
def apply(enabled: bool) -> None:
    if enabled:
        enable()
    else:
        disable()


# -------- Windows --------

# Check registry entry HKCU\...\Run
def _is_enabled_windows() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as k:
            try:
                winreg.QueryValueEx(k, APP_NAME)
                return True
            except FileNotFoundError:
                return False
    except Exception as e:
        log.exception("autostart.is_enabled error: %s", e)
        return False


# Add registry entry HKCU\...\Run
def _enable_windows() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _command_windows())
        log.info("Autostart enabled: %s", _command_windows())
        return True
    except Exception as e:
        log.exception("autostart.enable error: %s", e)
        return False


# Remove registry entry
def _disable_windows() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            try:
                winreg.DeleteValue(k, APP_NAME)
                log.info("Autostart disabled")
            except FileNotFoundError:
                pass
        return True
    except Exception as e:
        log.exception("autostart.disable error: %s", e)
        return False


# -------- Linux --------

# Create .desktop in ~/.config/autostart
def _enable_linux() -> bool:
    try:
        os.makedirs(LINUX_AUTOSTART_DIR, exist_ok=True)
        main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        content = ("[Desktop Entry]\n"
                   "Type=Application\n"
                   "Name=ChatClipper\n"
                   "Exec=" + sys.executable + " " + main_py + "\n"
                   "X-GNOME-Autostart-enabled=true\n")
        with open(LINUX_DESKTOP_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        log.info("Autostart enabled (Linux): %s", LINUX_DESKTOP_FILE)
        return True
    except Exception as e:
        log.exception("autostart.enable (Linux) error: %s", e)
        return False


# Remove .desktop from autostart
def _disable_linux() -> bool:
    try:
        if os.path.exists(LINUX_DESKTOP_FILE):
            os.remove(LINUX_DESKTOP_FILE)
            log.info("Autostart disabled (Linux)")
        return True
    except Exception as e:
        log.exception("autostart.disable (Linux) error: %s", e)
        return False


# -------- macOS --------

# Create LaunchAgent plist
def _enable_mac() -> bool:
    try:
        os.makedirs(MAC_LAUNCH_AGENTS, exist_ok=True)
        main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        content = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                   "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
                   "<plist version=\"1.0\">\n"
                   "<dict>\n"
                   "<key>Label</key><string>com.chatclipper</string>\n"
                   "<key>ProgramArguments</key>\n"
                   "<array>\n"
                   "<string>" + sys.executable + "</string>\n"
                   "<string>" + main_py + "</string>\n"
                   "</array>\n"
                   "<key>RunAtLoad</key><true/>\n"
                   "</dict>\n"
                   "</plist>\n")
        with open(MAC_PLIST_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        log.info("Autostart enabled (macOS): %s", MAC_PLIST_FILE)
        return True
    except Exception as e:
        log.exception("autostart.enable (macOS) error: %s", e)
        return False


# Remove LaunchAgent plist
def _disable_mac() -> bool:
    try:
        if os.path.exists(MAC_PLIST_FILE):
            os.remove(MAC_PLIST_FILE)
            log.info("Autostart disabled (macOS)")
        return True
    except Exception as e:
        log.exception("autostart.disable (macOS) error: %s", e)
        return False