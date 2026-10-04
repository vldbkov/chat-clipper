# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# AGENTS.md — instructions for AI coding agents working in this repository

## Project

ChatClipper — desktop utility for Windows that watches the clipboard after
an LMB click in Chrome (Copy button in web chats such as DeepSeek) and
appends the copied text to the project file (.docx / .md / .txt).
Linux / WSL / macOS support is experimental.

## Stack

- Python 3.10+
- Tk (GUI, popup, settings, control panel)
- pystray (Windows tray), pynput (mouse hook)
- python-docx, mistune, optional Pandoc
- No web framework, no database

## Layout

- main.py               — entry point; chooses tray vs GUI mode
- app_state.py          — shared AppState, single instance
- tray_process.py       — tray (pystray), menu, handlers
- gui_process.py        — Tk mainloop, mouse hook, IPC server
- control_panel.py      — Tk control panel (used instead of tray)
- actions.py            — IPC action registry (ACTIONS dict)
- ipc_server.py         — IPC server (named pipe / Unix socket, token)
- ipc_client.py         — IPC client
- config.py             — Project, AppConfig, config.json
- docx_writer.py        — buffered writer, stamp, pending queue
- markdown_to_docx.py   — mistune AST -> python-docx
- project_service.py    — single entry point for write_to_project
- writers/              — writer_base, writer_docx, writer_md, writer_txt
- sources/              — source_base, source_chrome, source_desktop_chat
- gui_settings.py       — SettingsWindow, ProjectDialog
- gui_popup.py          — PopupWindow (choice / status)
- gui_undo.py           — UndoDialog
- i18n.py               — t(key), init, set_locale, list_languages
- locales/              — en.json, ru.json, de.json, es.json, ja.json
- tests/                — unit tests for the core layer (no GUI)

## Commands

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    python main.py

Tests:

    pytest -q

Lint:

    ruff check .

## Conventions

- Comments in code: English only.
- Commit messages: English only, one line, no newlines.
- Indentation: 4 spaces. Do not use tabs.
- One blank line between functions and methods.
- Do not split long import lists or long signatures across lines.
- Every method has a comment above it describing its purpose.
- All comments start with `#`.

## Boundaries

- Do not change method or class signatures without explicit approval.
- Do not refactor unrelated code. Fix X only, do not touch Y.
- Do not remove functional code or comments without approval.
- Do not change GUI elements without an explicit request.
- Do not add debug prints to confirm facts the user already reported.
- Do not guess file contents — request an exact dump before any replace.
- Do not use markdown triple backticks inside code comments.

## Data files (not committed)

    config.json, hashes.json, last_buffers.json, logging/, pending/,
    ipc_token, chatclipper.sock

## Tests before commit

Run all three and make sure each passes before committing changes to
Python code:

    python -m py_compile <changed files>
    ruff check .
    pytest -q

Not required for changes limited to *.md, docs/, requirements.txt
(without dependency changes in code), locales/*.json, .gitignore,
*.ico, *.png.