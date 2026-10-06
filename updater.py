# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# GitHub Releases update checker: compares local version with the latest release
import json
import urllib.request
import urllib.error

from logger import log
from config import APP_VERSION


# GitHub repository for update checks
REPO_OWNER = "vldbkov"
REPO_NAME = "chat-clipper"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
TIMEOUT_SECONDS = 5


# Normalize a version string: strip leading 'v' and whitespace
def _normalize(v: str) -> str:
    if not v:
        return ""
    v = v.strip()
    if v.startswith("v") or v.startswith("V"):
        v = v[1:]
    return v


# Compare two dotted version strings; return True if latest is newer than current
def _is_newer(latest: str, current: str) -> bool:
    try:
        latest_parts = [int(x) for x in latest.split(".")]
        current_parts = [int(x) for x in current.split(".")]
        while len(latest_parts) < len(current_parts):
            latest_parts.append(0)
        while len(current_parts) < len(latest_parts):
            current_parts.append(0)
        return latest_parts > current_parts
    except Exception:
        return False


# Query GitHub for the latest release; return dict with version/url/notes or None
def check_for_update() -> dict | None:
    try:
        req = urllib.request.Request(API_URL, headers={"User-Agent": "ChatClipper/" + APP_VERSION})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        log.warning("update check: HTTP %s", e.code)
        return None
    except Exception as e:
        log.warning("update check failed: %s", e)
        return None

    tag = _normalize(data.get("tag_name", ""))
    url = data.get("html_url", "")
    notes = (data.get("body", "") or "").strip()
    if not tag or not url:
        return None
    if not _is_newer(tag, APP_VERSION):
        return None
    return {"version": tag, "url": url, "notes": notes}