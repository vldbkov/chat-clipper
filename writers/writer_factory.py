# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Writer factory: choose writer by project format
from writers.writer_docx import WriterDocx
from writers.writer_md import WriterMd
from writers.writer_txt import WriterTxt
from logger import log


# Cached writer instances per format
_writers = {}


# Return writer instance for the given format
# format: "docx" | "md" | "txt" (default docx)
def get_writer(fmt: str):
    key = (fmt or "docx").lower()
    if key not in _writers:
        if key == "md":
            _writers[key] = WriterMd()
        elif key == "txt":
            _writers[key] = WriterTxt()
        else:
            _writers[key] = WriterDocx()
        log.info("writer_factory: created writer for format '%s'", key)
    return _writers[key]


# Return writer for a project (uses project.format if present, else docx)
def get_writer_for_project(project):
    fmt = getattr(project, "format", "docx") or "docx"
    return get_writer(fmt)