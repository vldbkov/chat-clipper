# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Tray process: system tray icon and menu handlers
import os
import time

from logger import log
from config import load_config, flush_config, ICON_PATH, ICON_PATH_DARK
from ipc_client import send_ipc_command
from app_state import state
import i18n


# Build tray icon image from .ico or fallback stub
# Picks the dark-theme icon when config has dark_theme enabled
def make_tray_image():
    from PIL import Image, ImageDraw
    try:
        cfg = state.config
    except Exception:
        cfg = None
    dark = bool(getattr(cfg, "dark_theme", False)) if cfg is not None else False
    path = ICON_PATH_DARK if (dark and os.path.exists(ICON_PATH_DARK)) else ICON_PATH
    if os.path.exists(path):
        try:
            return Image.open(path)
        except Exception as e:
            log.exception("Cannot open .ico: %s", e)
    img = Image.new("RGBA", (64, 64), (30, 90, 200, 255))
    d = ImageDraw.Draw(img)
    d.text((18, 14), "C", fill=(255, 255, 255, 255))
    return img


# Tray menu handlers
def on_open_settings(icon, item):
    log.info("Tray: click Settings")
    send_ipc_command("settings")


def on_show_status(icon, item):
    log.info("Tray: click Status")
    send_ipc_command("status")


def on_toggle_pause(icon, item):
    state.paused = not state.paused
    log.info("Tray: pause = %s", state.paused)
    send_ipc_command("toggle_pause")
    try:
        icon.update_menu()
    except Exception:
        pass


def on_undo(icon, item):
    send_ipc_command("undo")


def on_toggle_autostart(icon, item):
    log.info("Tray: click Autostart")
    send_ipc_command("toggle_autostart")
    time.sleep(0.6)
    try:
        state.config = load_config()
    except Exception as e:
        log.exception("Cannot reload config.json in tray process: %s", e)


def on_exit(icon, item):
    log.info("Tray: exit")
    send_ipc_command("exit")
    time.sleep(0.2)
    try:
        icon.stop()
    except Exception:
        pass
    try:
        flush_config()
    except Exception:
        pass
    log.info("=== Tray process finished ===")
    os._exit(0)


def on_restart(icon, item):
    log.info("Tray: restart")
    send_ipc_command("restart")
    time.sleep(0.3)
    try:
        icon.stop()
    except Exception:
        pass
    log.info("=== Tray process finished (restart) ===")
    os._exit(0)


# Build tray menu
def build_menu():
    import pystray
    return pystray.Menu(
        pystray.MenuItem(i18n.t("tray.status"), on_show_status, default=True),
        pystray.MenuItem(i18n.t("tray.settings"), on_open_settings),
        pystray.MenuItem(i18n.t("tray.undo"), on_undo),
        pystray.MenuItem(i18n.t("tray.pause"), on_toggle_pause, checked=lambda item: state.paused),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(i18n.t("tray.restart"), on_restart),
        pystray.MenuItem(i18n.t("tray.exit"), on_exit),
    )


# Run tray process (called with --tray argument)
def run_tray_process():
    import pystray
    state.is_tray_process = True
    state.config = load_config()
    i18n.init(getattr(state.config, "locale", "en"))
    icon = pystray.Icon(
        "ChatClipper_" + str(os.getpid()),
        icon=make_tray_image(),
        title="ChatClipper",
        menu=build_menu(),
    )
    state.tray_icon = icon
    log.info("Tray started in separate process (PID=%d)", os.getpid())
    icon.run()