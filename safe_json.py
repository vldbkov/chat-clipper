# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Atomic JSON write with rotating backups and safe read fallback
import json
import os
import shutil
import time

from logger import log


# Number of most recent backups to keep per file
MAX_BACKUPS = 5


# Directory for backup files, next to the original file
def _backup_dir_for(path: str) -> str:
    return os.path.join(os.path.dirname(path), "backups")


# Write JSON atomically: tmp file, then os.replace
def atomic_write_json(path: str, data, ensure_ascii: bool = False, indent: int = 2) -> bool:
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        return True
    except Exception as e:
        log.exception("safe_json.atomic_write_json failed for %s: %s", path, e)
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return False


# Copy existing file to backups/ with timestamp; drop older backups above MAX_BACKUPS
def backup_json(path: str) -> None:
    if not os.path.exists(path):
        return
    bdir = _backup_dir_for(path)
    try:
        os.makedirs(bdir, exist_ok=True)
    except Exception as e:
        log.exception("safe_json.backup_json cannot create %s: %s", bdir, e)
        return
    base = os.path.basename(path)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    # Counter derived from existing backups; avoids reliance on system clock precision
    counter = 1
    target = os.path.join(bdir, base + "." + stamp + f".{counter:04d}.bak")
    while os.path.exists(target):
        counter += 1
        target = os.path.join(bdir, base + "." + stamp + f".{counter:04d}.bak")
    try:
        shutil.copy2(path, target)
    except Exception as e:
        log.exception("safe_json.backup_json copy failed: %s", e)
        return
    # Rotation: keep only MAX_BACKUPS newest by name sort
    try:
        candidates = sorted([f for f in os.listdir(bdir) if f.startswith(base + ".") and f.endswith(".bak")])
        while len(candidates) > MAX_BACKUPS:
            try:
                os.remove(os.path.join(bdir, candidates[0]))
            except Exception:
                pass
            candidates.pop(0)
    except Exception as e:
        log.debug("safe_json.backup_json rotation skipped: %s", e)


# List backups of a file, newest first
def list_backups(path: str) -> list:
    bdir = _backup_dir_for(path)
    if not os.path.isdir(bdir):
        return []
    base = os.path.basename(path)
    try:
        items = [f for f in os.listdir(bdir) if f.startswith(base + ".") and f.endswith(".bak")]
        items.sort(reverse=True)
        return [os.path.join(bdir, f) for f in items]
    except Exception:
        return []


# Read JSON: try main file first, on error fall back to newest backup
def read_json_with_fallback(path: str, default=None):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception as e:
            log.exception("safe_json.read_json_with_fallback main failed %s: %s", path, e)
    for bkp in list_backups(path):
        try:
            with open(bkp, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            log.info("safe_json: recovered %s from backup %s", path, os.path.basename(bkp))
            return data
        except Exception as e:
            log.debug("safe_json: backup %s failed: %s", bkp, e)
    return default