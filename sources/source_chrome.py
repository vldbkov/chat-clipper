# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Chromium source: any window whose process name contains a known browser
from sources.source_base import SourceBase
from platform_utils import get_active_process_name


# Process name substrings of Chromium-based browsers
CHROMIUM_PROCESSES = ("chrome", "opera", "brave", "msedge", "vivaldi", "yandex", "chromium")


# Chromium browser source (Chrome, Opera, Edge, Brave, Vivaldi, Yandex)
class SourceChrome(SourceBase):
    # Human-readable name
    @property
    def display_name(self) -> str:
        import i18n
        return i18n.t("source.browser")

    # Machine key
    @property
    def key(self) -> str:
        return "browser"

    # Check that active window belongs to a Chromium-based browser
    def is_active(self) -> bool:
        name = get_active_process_name()
        if not name:
            return False
        lowered = name.lower()
        return any(p in lowered for p in CHROMIUM_PROCESSES)