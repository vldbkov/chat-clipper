# Module for remembering and undoing the last write to .docx
import json
import os
import re

from docx import Document

from config import LAST_BUFFERS_PATH
from config import load_config
from logger import log


# Patterns for credentials commonly seen in copy buffers
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",
    r"ghp_[A-Za-z0-9]{20,}",
    r"Bearer\s+[A-Za-z0-9._\-]{20,}",
    r"api[_-]?key\s*[:=]\s*[A-Za-z0-9._\-]{16,}",
]


# Remember the last successful write
# Sanitize text before storing for undo: enforce limit, optionally skip secrets
def _sanitize_for_undo(text: str) -> str | None:
    if text is None:
        return None
    try:
        cfg = load_config()
    except Exception:
        return text
    if getattr(cfg, "skip_secrets", True):
        for pat in SECRET_PATTERNS:
            if re.search(pat, text):
                return None
    max_len = int(getattr(cfg, "undo_max_text_len", 10000))
    if max_len > 0 and len(text) > max_len:
        text = text[:max_len]
    return text


def remember(project_name: str, docx_path: str, text: str, paragraphs: int = 2) -> None:
    text = _sanitize_for_undo(text)
    if text is None:
        log.info("undo: skipped (secret or empty) for project '%s'", project_name)
        return
    try:
        data = _load()
        data["prev"] = data.get("last")
        data["last"] = {
            "project": project_name,
            "docx": docx_path,
            "text": text,
            "paragraphs": int(paragraphs),
        }
        _save(data)
        log.info("undo: last write remembered in '%s' (%d chars, %d paragraphs)", project_name, len(text), paragraphs)
    except Exception as e:
        log.exception("undo.remember error: %s", e)


# Get last write data
def get_last() -> dict | None:
    data = _load()
    return data.get("last")


# Clear last write memory
def clear_last() -> None:
    data = _load()
    data["last"] = None
    _save(data)


# Undo last write: remove from source .docx, append to target
def undo_last(new_project_name: str, new_docx_path: str) -> bool:
    last = get_last()
    if not last:
        log.warning("undo: nothing to undo")
        return False
    old_docx = last.get("docx", "")
    old_project = last.get("project", "")
    text = last.get("text", "")
    paragraphs = int(last.get("paragraphs", 2))
    if not old_docx or not os.path.exists(old_docx):
        log.error("undo: source .docx not found: %s", old_docx)
        return False
    if not text:
        log.error("undo: empty text in memory")
        return False
    removed = _remove_last_paragraphs(old_docx, paragraphs)
    if not removed:
        log.error("undo: failed to remove last paragraphs from %s", old_docx)
        return False
    ok = _append_to(new_docx_path, text)
    if not ok:
        log.error("undo: failed to append to %s", new_docx_path)
        return False
    clear_last()
    log.info("undo: moved from '%s' to '%s' (%d chars)", old_project, new_project_name, len(text))
    return True


# Remove last N paragraphs from .docx
def _remove_last_paragraphs(docx_path: str, count: int) -> bool:
    try:
        doc = Document(docx_path)
        all_p = doc.paragraphs
        if len(all_p) < count:
            log.warning("undo._remove_last_paragraphs: file has %d paragraphs, need to remove %d", len(all_p), count)
            return False
        tail = all_p[-count:]
        for p in tail:
            el = p._element
            el.getparent().remove(el)
        doc.save(docx_path)
        return True
    except Exception as e:
        log.exception("undo._remove_last_paragraphs error: %s", e)
        return False


# Append text to .docx via the same writer used for normal writes
# Keeps stamp, separator line and markdown parsing consistent
def _append_to(docx_path: str, text: str) -> bool:
    try:
        from docx_writer import DocxWriter
        writer = DocxWriter()
        return writer.append_markdown(docx_path, text)
    except Exception as e:
        log.exception("undo._append_to error: %s", e)
        return False


# Load last_buffers.json
def _load() -> dict:
    if not os.path.exists(LAST_BUFFERS_PATH):
        return {"last": None, "prev": None}
    try:
        with open(LAST_BUFFERS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"last": None, "prev": None}
        data.setdefault("last", None)
        data.setdefault("prev", None)
        return data
    except Exception as e:
        log.exception("undo._load error: %s", e)
        return {"last": None, "prev": None}


# Save last_buffers.json
def _save(data: dict) -> None:
    try:
        with open(LAST_BUFFERS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.exception("undo._save error: %s", e)