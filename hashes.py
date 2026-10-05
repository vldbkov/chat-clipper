# CRC32 ring buffer module for duplicate detection
import json
import os
import zlib

from logger import log


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HASHES_PATH = os.path.join(BASE_DIR, "hashes.json")


# Ring storage of CRC32 for the last accepted texts
class HashRing:
    # Initialize ring and load from file
    def __init__(self, size: int = 5):
        self.size = size
        self.items = []
        self._dirty = False
        self._load()

    # Load saved hashes from hashes.json
    def _load(self) -> None:
        if not os.path.exists(HASHES_PATH):
            return
        try:
            if os.path.getsize(HASHES_PATH) == 0:
                log.warning("hashes.json is empty - creating new")
                self.items = []
                self._save()
                return
            with open(HASHES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self.items = [int(x) for x in data][-self.size:]
            log.info("hashes.json loaded: %d values", len(self.items))
        except Exception as e:
            log.exception("Error reading hashes.json: %s", e)
            self.items = []
            self._save()

    # Save ring of hashes to hashes.json
    def _save(self) -> None:
        try:
            with open(HASHES_PATH, "w", encoding="utf-8") as f:
                json.dump(self.items, f)
            self._dirty = False
        except Exception as e:
            log.exception("Error saving hashes.json: %s", e)

    # Compute CRC32 for text
    # Explicit flush for exit / settings change
    def flush(self) -> None:
        if self._dirty:
            self._save()

    @staticmethod
    def calc(text: str) -> int:
        return zlib.crc32(text.encode("utf-8")) & 0xFFFFFFFF

    # Check text for duplicate
    def is_duplicate(self, text: str) -> bool:
        h = self.calc(text)
        return h in self.items

    # Add text to ring
    def add(self, text: str) -> int:
        h = self.calc(text)
        self.items.append(h)
        if len(self.items) > self.size:
            self.items = self.items[-self.size:]
        self._dirty = True
        return h

    # Set ring size (from settings)
    def set_size(self, size: int) -> None:
        self.size = max(1, int(size))
        if len(self.items) > self.size:
            self.items = self.items[-self.size:]
            self._dirty = True