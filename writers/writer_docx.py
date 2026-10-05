# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Docx writer: wraps DocxWriter for use via WriterBase interface
from writers.writer_base import WriterBase
from docx_writer import DocxWriter


# Docx format writer
class WriterDocx(WriterBase):
    # Initialize with a fresh DocxWriter
    def __init__(self):
        self._w = DocxWriter()

    # Append markdown or html to the project .docx
    def append(self, project, text: str, html: str = "") -> bool:
        if text:
            return self._w.append_markdown(project.docx_path, text)
        if html:
            return self._w.append_html(project.docx_path, html)
        return False

    # Flush pending queue
    def sync(self) -> int:
        return self._w.sync_all()

    # Number of paragraphs added by last append
    def last_paragraphs(self) -> int:
        return int(getattr(self._w, "last_appended_paragraphs", 0) or 0)

    # Access underlying DocxWriter (for undo legacy paths)
    @property
    def docx_writer(self):
        return self._w