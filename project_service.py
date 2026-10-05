# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Single entry point for all write and project-state operations
# Keeps write logic in one place: writer call, undo.remember, config save
from config import save_config
from logger import log
import undo


# Write text or html into a project via the given writer
# This is the only place where writes to a project should happen
# remember: whether to update undo memory (default True)
def write_to_project(cfg, writer, project, text: str, html: str = "", remember: bool = True) -> bool:
    if not project:
        return False
    from writers.writer_factory import get_writer_for_project
    actual = get_writer_for_project(project)
    if text:
        ok = actual.append(project, text, html)
    elif html:
        ok = actual.append(project, "", html)
    else:
        return False
    if ok:
        if remember:
            paragraphs = int(actual.last_paragraphs() or 2)
            undo.remember(project.name, project.docx_path, text, paragraphs=paragraphs)
        log.info("project_service: written to '%s': %s", project.name, project.docx_path)
    else:
        log.info("project_service: project '%s' busy or empty content", project.name)
    return ok


# Switch the main project and persist cfg
# Returns True if changed, False if same
def set_main(cfg, name: str) -> bool:
    if not name:
        return False
    if name == cfg.main_project:
        return False
    cfg.main_project = name
    save_config(cfg)
    log.info("project_service: main project switched to '%s'", name)
    return True


# Transfer last undo entry into the target project
# Delegates to undo.undo_last (which writes via its own writer path)
def transfer_undo(target_name: str, target_docx: str) -> bool:
    return undo.undo_last(target_name, target_docx)