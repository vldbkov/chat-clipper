# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Source factory: choose and cache clipboard sources by key
from sources.source_chrome import SourceChrome
from sources.source_desktop_chat import SourceDesktopChat
from logger import log
import i18n


# Cached source instances per key
_sources = {}


# Return source instance by key
def get_source(key: str):
    k = (key or "chrome").lower()
    if k not in _sources:
        if k == "desktop":
            _sources[k] = SourceDesktopChat()
        else:
            _sources[k] = SourceChrome()
        log.info("source_factory: created source for key '%s'", k)
    return _sources[k]


# Return list of available source keys with display names
def list_sources() -> list:
    return [
        ("chrome", i18n.t("source.chrome")),
        ("desktop", i18n.t("source.desktop")),
    ]