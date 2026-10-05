# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Abstract source interface: decides whether a mouse click is a Copy in the source app
from abc import ABC, abstractmethod


# Base class for clipboard sources
class SourceBase(ABC):
    # Human-readable name for settings UI
    @property
    @abstractmethod
    def display_name(self) -> str:
        pass

    # Machine key, e.g. "chrome", "desktop"
    @property
    @abstractmethod
    def key(self) -> str:
        pass

    # Return True if the currently active window belongs to this source
    @abstractmethod
    def is_active(self) -> bool:
        pass