# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-05

### Added

- Clipboard watcher on LMB click in Chrome
- Append copied text to project files: docx, md, txt
- Markdown parsing via mistune: headings, bold, italic, inline code,
  code blocks, lists, quotes, tables
- Optional Pandoc converter with mistune fallback
- Timestamp stamp and separator line before each block
- Multiple projects with one main project; per-project file format
- Popup window to pick a project with configurable opacity and duration
- Clicking a non-main project in the popup silently makes it main
- Startup status popup; PAUSE stamp when paused
- Duplicate suppression via CRC32 ring of last 5 values
- Undo last write: removes the entry from source file and moves it to
  another project; respects undo_max_text_len and skip_secrets
- Buffered docx writes: flushed every 5 seconds or on exit
- Pending queue when the target file is busy
- Content loss check via loss_threshold_pct and loss_min_abs_chars
- IPC over named pipe (Windows) or Unix socket (POSIX) with token auth
- Tray icon on Windows; Tk control panel on Linux / WSL / macOS
- Autostart on login (off by default)
- Single instance guard via mutex / file lock
- i18n: English, Russian, German, Spanish, Japanese
- Auto-detect interface language from OS locale on first run
- User manual in HTML for all supported languages
- Feedback button opening a Google Form
- Help button opening the user manual for the current locale
- Donate button opening the author's support page
- Window icon: chatclipper-light.ico

### Known limitations

- Windows is the primary platform; Linux / WSL / macOS support is experimental.
- In WSL: settings window not centered, mouse click copy not working,
  restart from panel not working, status window 100% opaque.

[1.0.0]: https://github.com/vldbkov/chat-clipper/releases/tag/v1.0.0