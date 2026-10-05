# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# ChatClipper entry point: decides between tray-only and GUI mode
import os
import sys
import subprocess
import time

from logger import log
from config import load_config
from platform_utils import detached_creation_flags, IS_WINDOWS
from tray_process import run_tray_process
from gui_process import run_gui_process
from app_state import state
import i18n


# Decide whether to start tray process and run GUI
def main():
    if "--tray" in sys.argv:
        run_tray_process()
        return

    cfg = load_config()
    i18n.init(getattr(cfg, "locale", "en"))
    tray_needed = IS_WINDOWS and bool(getattr(cfg, "tray_enabled", False))

    state.tray_started = False
    if tray_needed:
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            main_py = os.path.join(base_dir, "main.py")
            creationflags = detached_creation_flags()
            subprocess.Popen([sys.executable, main_py, "--tray"],
                             creationflags=creationflags, close_fds=True)
            time.sleep(1.0)
            state.tray_started = True
        except Exception as e:
            log.error("Failed to start tray process: %s", e)
    else:
        log.info("Tray disabled or OS is not Windows - running GUI with control panel")

    run_gui_process()


if __name__ == "__main__":
    main()