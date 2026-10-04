# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of ChatClipper.
- Clipboard watching on LMB click in Chrome.
- Buffered writing to .docx, .md, and .txt files.
- Markdown parsing via mistune.
- Optional Pandoc converter.
- Multiple project support with one main project.
- Project picker popup.
- Duplicate suppression via CRC32 ring.
- Undo last write functionality.
- Content loss check.
- IPC via named pipe (Windows) / Unix socket (POSIX).
- Tray icon (Windows) and Tk control panel.
- Autostart support.
- Single instance guard.
- i18n: English, Russian, German, Spanish, Japanese.