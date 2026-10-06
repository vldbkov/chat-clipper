# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Source factory: choose and cache clipboard sources by key
from sources.source_chrome import SourceChrome
from logger import log
import i18n


# Cached source instances per key
_sources = {}


# Return source instance by key
def get_source(key: str):
    k = (key or "browser").lower()
    # Backward compatibility: old keys map to the browser source
    if k in ("chrome", "desktop"):
        k = "browser"
    if k not in _sources:
        _sources[k] = SourceChrome()
        log.info("source_factory: created source for key '%s'", k)
    return _sources[k]


# Return list of available source keys with display names
def list_sources() -> list:
    return [
        ("browser", i18n.t("source.browser")),
    ]