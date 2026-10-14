# Release notes for ChatClipper

[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE) [![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/) [![Platform](https://img.shields.io/badge/platform-windows-0078D6)](https://www.microsoft.com/windows) [![VirusTotal](https://img.shields.io/badge/VirusTotal-clean-brightgreen)](https://github.com/vldbkov/chat-clipper/blob/main/README.md)

---

## 📦 v1.0.0 — 2026-10-06

First public release of ChatClipper — a clipboard watcher for AI web chats on Windows.

### 📥 What's included

- Installer: `ChatClipper_Setup_1.0.0.exe` (21.45 MB)
- Requires Windows 10/11
- No Python installation required

### ✨ Highlights

- Watches clipboard after Copy in Chromium browsers and Electron-based desktop AI apps
- Detects copy via the Copy button, mouse click, or Ctrl+C
- Appends text to project files: .docx / .md / .txt
- Markdown parsing via mistune, optional Pandoc
- Multiple projects with one main project; sorted list (main, active, inactive)
- Popup to pick a project, Undo last write
- Single click on the PAUSE stamp resumes tracking
- Single click on the main project in the status window pauses tracking
- Light and dark themes, switchable in the settings header
- Tray icon, autostart, single-instance guard
- i18n: English, Russian, German, Spanish, Japanese
- Built-in update check via GitHub Releases
- Atomic JSON write with rotating backups for config, hashes and undo state

### 🚀 First run

- A default project is created at `~/ChatClipper` with an empty Word file.
- A ticking clock sound plays while waiting for a copy.
- Copy in the chat by clicking the **Copy** button or pressing **Ctrl+C**.

### 🛡 Safety

- The installer is verified by VirusTotal. No threats were detected.
- Report: https://www.virustotal.com/gui/file/17d6cfce17bf2bf63276c47f55f9423fe53a67b50991cd77f60e95c04d63e97f
- Source code is open and auditable: https://github.com/vldbkov/chat-clipper

### ⚠️ Known limitations

- Windows is the primary platform; Linux / WSL / macOS support is experimental.
- In WSL: settings window not centered, mouse click copy not working.

---

## 🔮 Unreleased

Placeholder for the next release entry. Add highlights, fixes and known issues here. Keep the newest entry at the top.

---

[🌐 Back to README](https://github.com/vldbkov/chat-clipper/blob/main/README.md)