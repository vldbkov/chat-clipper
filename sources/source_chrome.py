# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Chrome source: any window whose process name contains "chrome"
from sources.source_base import SourceBase
from platform_utils import get_active_process_name


# Chrome browser source
class SourceChrome(SourceBase):
    # Human-readable name
    @property
    def display_name(self) -> str:
        import i18n
        return i18n.t("source.chrome")

    # Machine key
    @property
    def key(self) -> str:
        return "chrome"

    # Check that active window belongs to Chrome
    def is_active(self) -> bool:
        name = get_active_process_name()
        if not name:
            return False
        return "chrome" in name