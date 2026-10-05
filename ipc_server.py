# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# IPC server: listens for commands from tray process and stores them in state
import os
import secrets
import sys
import threading
from multiprocessing.connection import Listener

from config import IPC_TOKEN_PATH
from ipc_client import IPC_ENDPOINT, IPC_FAMILY
from logger import log


# Generate and persist a fresh IPC token with restrictive permissions
def _write_token() -> str:
    token = secrets.token_hex(16)
    try:
        with open(IPC_TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(token)
        if not sys.platform.startswith("win"):
            os.chmod(IPC_TOKEN_PATH, 0o600)
    except Exception as e:
        log.exception("IPC token write error: %s", e)
    return token


# Remove stale Unix socket file before binding
def _cleanup_endpoint() -> None:
    if sys.platform.startswith("win"):
        return
    try:
        if os.path.exists(IPC_ENDPOINT):
            os.remove(IPC_ENDPOINT)
    except Exception as e:
        log.exception("IPC socket cleanup error: %s", e)


# Start IPC server in a background daemon thread
# Returns the thread object
def start_ipc_server(state) -> threading.Thread:
    t = threading.Thread(target=_ipc_server_loop, args=(state,), daemon=True)
    t.start()
    return t


# Server loop: authenticate client, read one command, store in state.pending_action
def _ipc_server_loop(state):
    token = _write_token()
    _cleanup_endpoint()
    try:
        srv = Listener(IPC_ENDPOINT, family=IPC_FAMILY)
    except Exception as e:
        log.exception("IPC server bind error: %s", e)
        return
    log.info("IPC server started at %s", IPC_ENDPOINT)
    while True:
        try:
            conn = srv.accept()
        except Exception as e:
            log.exception("IPC accept error: %s", e)
            continue
        try:
            msg = conn.recv()
            if not isinstance(msg, tuple) or len(msg) != 2 or msg[0] != "auth":
                conn.send("denied")
                conn.close()
                continue
            if msg[1] != token:
                log.warning("IPC auth rejected: bad token")
                conn.send("denied")
                conn.close()
                continue
            conn.send("ok")
            msg2 = conn.recv()
            if isinstance(msg2, tuple) and len(msg2) == 2 and msg2[0] == "cmd":
                data = str(msg2[1]).strip()
                if data:
                    with state.pending_lock:
                        state.pending_action = data
        except Exception as e:
            log.exception("IPC server error: %s", e)
        finally:
            try:
                conn.close()
            except Exception:
                pass