# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Markdown writer: appends markdown text into .md file with stamp and separator
import os
import time

from writers.writer_base import WriterBase
from logger import log


# Markdown format writer
class WriterMd(WriterBase):
    # Initialize writer
    def __init__(self):
        self._last_paragraphs = 0

    # Append markdown text into the project .md file
    def append(self, project, text: str, html: str = "") -> bool:
        path = project.docx_path
        if path.lower().endswith(".docx"):
            path = path[:-5] + ".md"
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as e:
                log.exception("WriterMd: cannot create folder %s: %s", folder, e)
                return False
        try:
            stamp = time.strftime("%d.%m.%y %H:%M")
            block = "\n---\n\n" + stamp + "\n\n" + (text or "") + "\n"
            with open(path, "a", encoding="utf-8") as f:
                f.write(block)
            self._last_paragraphs = 2
            log.info("WriterMd: appended %d chars to %s", len(text or ""), path)
            return True
        except Exception as e:
            log.exception("WriterMd: append error: %s", e)
            return False

    # Number of paragraphs added by last append
    def last_paragraphs(self) -> int:
        return self._last_paragraphs