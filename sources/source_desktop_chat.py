# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Desktop chat app source: any window with a known chat process name
from sources.source_base import SourceBase
from platform_utils import get_active_process_name


# Known desktop chat app process names (lowercase, substring match)
KNOWN_CHAT_APPS = [
    "qwen",
    "chatglm",
    "glm",
    "chatbox",
    "openwebui",
    "lmstudio",
    "ollama",
]


# Desktop chat source: matches known chat app processes
class SourceDesktopChat(SourceBase):
    # Human-readable name
    @property
    def display_name(self) -> str:
        import i18n
        return i18n.t("source.desktop")

    # Machine key
    @property
    def key(self) -> str:
        return "desktop"

    # Check that active window belongs to any known chat app
    def is_active(self) -> bool:
        name = get_active_process_name()
        if not name:
            return False
        for known in KNOWN_CHAT_APPS:
            if known in name:
                return True
        return False