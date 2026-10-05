# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# IPC client for sending commands from tray/panel to the GUI process
import os
import sys
from multiprocessing.connection import Client

from config import IPC_TOKEN_PATH
from logger import log


# Compute IPC endpoint address based on the current OS
def _endpoint() -> str:
    if sys.platform.startswith("win"):
        return r"\\.\pipe\ChatClipper-ipc"
    # POSIX: keep the socket on a native Linux FS (drvfs/9p does not support bind)
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime and os.path.isdir(runtime):
        return os.path.join(runtime, "chatclipper.sock")
    return "/tmp/chatclipper.sock"


IPC_ENDPOINT = _endpoint()
IPC_FAMILY = "AF_PIPE" if sys.platform.startswith("win") else "AF_UNIX"


# Read the shared IPC token from disk
def _read_token() -> str:
    try:
        with open(IPC_TOKEN_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


# Send an IPC command to the GUI process
def send_ipc_command(cmd: str) -> bool:
    token = _read_token()
    if not token:
        log.debug("IPC send skipped: token not ready")
        return False
    conn = None
    try:
        conn = Client(IPC_ENDPOINT, family=IPC_FAMILY)
        conn.send(("auth", token))
        reply = conn.recv()
        if reply != "ok":
            log.error("IPC auth rejected by server")
            return False
        conn.send(("cmd", cmd))
        log.debug("IPC sent: %s", cmd)
        return True
    except Exception as e:
        log.error("IPC send error for '%s': %s", cmd, e)
        return False
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass