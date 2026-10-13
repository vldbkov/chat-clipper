# CRC32 ring buffer module for duplicate detection
import os
import zlib

from logger import log
from config import HASHES_PATH
from safe_json import backup_json, atomic_write_json, read_json_with_fallback


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
            data = read_json_with_fallback(HASHES_PATH, None)
            if data is None:
                log.warning("hashes.json unreadable and no valid backup")
                self.items = []
                self._save()
                return
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
            backup_json(HASHES_PATH)
            ok = atomic_write_json(HASHES_PATH, self.items, ensure_ascii=True, indent=None)
            if ok:
                self._dirty = False
            else:
                log.warning("hashes.json not saved (atomic write failed)")
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