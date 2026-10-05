# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Abstract writer interface: all format writers implement append()
from abc import ABC, abstractmethod


# Base class for all project writers
class WriterBase(ABC):
    # Append text or html into the project file
    # Returns True on success, False on failure
    @abstractmethod
    def append(self, project, text: str, html: str = "") -> bool:
        pass

    # Flush any pending queued items, return number written
    def sync(self) -> int:
        return 0

    # Return number of paragraphs written by last append call
    def last_paragraphs(self) -> int:
        return 0