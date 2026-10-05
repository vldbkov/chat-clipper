# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Simple i18n module: t(key) returns string for current locale
import json
import os

from logger import log


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALES_DIR = os.path.join(BASE_DIR, "locales")

_current_locale = "en"
_strings = {}
_fallback = {}


# Load locale file, return dict or empty dict on error
def _load_locale(locale: str) -> dict:
    path = os.path.join(LOCALES_DIR, locale + ".json")
    if not os.path.exists(path):
        log.warning("i18n: locale file not found: %s", path)
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.exception("i18n: cannot load %s: %s", path, e)
        return {}


# Initialize with given locale; fallback is always en
def init(locale: str = "en") -> None:
    global _current_locale, _strings, _fallback
    _current_locale = locale or "en"
    _fallback = _load_locale("en")
    if _current_locale == "en":
        _strings = _fallback
    else:
        _strings = _load_locale(_current_locale)
    log.info("i18n: locale='%s' loaded (%d strings)", _current_locale, len(_strings))


# Switch locale at runtime
def set_locale(locale: str) -> None:
    init(locale)


# Return current locale
def get_locale() -> str:
    return _current_locale


# Detect OS locale code (e.g. 'en', 'ru'); fallback to 'en'
# Windows: query OS locale name via WinAPI (returns e.g. 'ru-RU')
def _detect_windows_locale() -> str:
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(85)
        ok = ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85)
        if ok:
            return buf.value
    except Exception:
        pass
    return ""


# Detect OS locale code (e.g. 'en', 'ru'); fallback to 'en'
def detect_os_locale() -> str:
    candidates = []
    if os.name == "nt":
        win_loc = _detect_windows_locale()
        if win_loc:
            candidates.append(win_loc)
    for env in ("LC_ALL", "LC_MESSAGES", "LANG"):
        v = os.environ.get(env)
        if v:
            candidates.append(v)
    try:
        import locale as _locale
        loc = _locale.getlocale(_locale.LC_CTYPE)[0]
        if loc:
            candidates.append(loc)
    except Exception:
        pass
    for c in candidates:
        code = c.split(".")[0].split("_")[0].split("-")[0].strip().lower()
        if code:
            return code
    return "en"


# List locale codes available in locales/ folder (JSON file stems)
def list_available_locales() -> list:
    try:
        files = os.listdir(LOCALES_DIR)
    except Exception:
        return ["en"]
    codes = [fn[:-5] for fn in files if fn.endswith(".json")]
    return codes or ["en"]


# List available languages as (code, display_name) pairs.
# Display name is read from each locale file under "lang.name";
# falls back to the code itself when missing.
def list_languages() -> list:
    result = []
    for code in sorted(list_available_locales()):
        data = _load_locale(code)
        name = data.get("lang.name") or code
        result.append((code, name))
    return result


# Translate key; fallback to en, then key itself
def t(key: str) -> str:
    if key in _strings:
        return _strings[key]
    if key in _fallback:
        return _fallback[key]
    return key