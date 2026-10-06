# ChatClipper

[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-windows-0078D6)](https://www.microsoft.com/windows)
[![Kaspersky](https://img.shields.io/badge/Kaspersky-OpenTIP%20clear-brightgreen)](https://opentip.kaspersky.com/38FC30C3E1A40412F40FF27D5ACC2771C34422E928C2E85FBC23188D260F8109)

**English** · [Русский](docs/README-ru.md) · [Deutsch](docs/README-de.md) · [Español](docs/README-es.md) · [日本語](docs/README-ja.md)

Desktop utility that watches the clipboard after a single LMB click in
Chrome (Copy button in web chats, e.g. DeepSeek) and appends the text to
the .docx / .md / .txt file of the selected project.
Works on Windows; Linux / WSL / macOS support is experimental.

**Safety note:** The Windows installer is verified by Kaspersky OpenTIP.
No threats were detected. The source code is open and auditable.

---

## 📋 About

ChatClipper is a lightweight utility that automatically saves your chats
with AI assistants (DeepSeek, ChatGPT and similar) into a single project
file. No more manual copy-paste — the program does it for you.

- Watches the clipboard and detects Copy in web chats.
- Appends the copied text to the project file (.docx / .md / .txt).
- Supports multiple projects with one main project.
- Works in the background — lives in the system tray.
- First run creates a default project at `~/ChatClipper` with an empty
  file that already has a heading — you can start copying right away.
- A ticking clock sound plays while the app is waiting for a copy —
  this means the app is running and ready.

---

## ✨ Features

- Clipboard watcher on LMB click in Chrome
- Append text to project files: docx, md, txt
- Markdown parsing (mistune): headings, bold, italic, inline code,
  code blocks, lists, quotes, tables
- Optional Pandoc converter (fallback to mistune on failure)
- Timestamp stamp and separator line before each block
- Multiple projects with one main project; project format is per-project
- Popup window to pick a project (opacity and duration configurable)
- Clicking a non-main project in the popup silently makes it main
- Startup status popup; PAUSE stamp when paused
- Duplicate suppression via CRC32 ring (5 last values)
- Undo last write: removes it from source .docx and moves it to another
  project; respects undo_max_text_len and skip_secrets
- Buffered .docx writes: flushed every 5 s or on exit
- Pending queue when target file is busy
- Content loss check (loss_threshold_pct + loss_min_abs_chars)
- IPC: named pipe on Windows, Unix socket on POSIX, with token auth
- Tray icon (Windows) or Tk control panel (Linux / WSL / macOS)
- Autostart (off by default)
- Tray enabled (off by default; Windows only)
- Single instance guard (mutex / file lock)
- i18n: English, Russian, German, Spanish, Japanese
- Auto-detect from OS locale on first run
- Add a new language by dropping `locales/<code>.json` with `"lang.name"`
- Window icon: chatclipper-light.ico

---

## ⚙️ Requirements
- Windows 10/11 (Linux / macOS — experimental)
- Python 3.10+
- LibreOffice or MS Word for editing .docx
- Chrome as clipboard source
- Optional: Pandoc in PATH for Markdown → docx
---

## 🚀 Install

### Recommended: uv virtual environment
```
    git clone https://github.com/vldbkov/chat-clipper.git
    cd chat-clipper
    uv venv
    uv pip install -r requirements.txt
    uv run python main.py
```
### Alternative: pip
```
    git clone https://github.com/vldbkov/chat-clipper.git
    cd chat-clipper
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    python main.py
```
### Easiest for end users: Windows installer

Download `chatclipper-setup.exe` from the latest release and run it.
No Python installation required.
After install, the tray icon appears (Windows).

---

## 🎮 Usage

On first launch ChatClipper automatically creates a default project at
`~/ChatClipper` (your user home folder) with an empty Word file that
already contains a heading. No setup needed — just start copying.

1. Open a chat with an AI (DeepSeek, ChatGPT, Qwen, GLM and similar) in Chrome.
2. Copy the reply in one of two ways:
   - click the **Copy** button shown in the chat UI (recommended — it
     also preserves HTML formatting), or
   - select the text and press **Ctrl+C** on the keyboard.
3. A popup appears in a second with the project choice — click the one
   you want, or let it auto-close (the main project is used).
4. Open the project file in Word — the text is there (writes are delayed
   by about 5 seconds).
5. To add more projects: ChatClipper panel → **Settings** → **Add**.
   Set one project as main — writes go there by default.

---

## 📁 Project layout
```
    main.py                  — entry point, chooses tray vs GUI mode
    app_state.py             — shared AppState, single instance
    tray_process.py          — tray (pystray), menu, handlers
    gui_process.py           — Tk mainloop, mouse hook, IPC server
    control_panel.py         — Tk control panel instead of tray
    actions.py               — IPC action registry (ACTIONS dict)
    ipc_server.py            — IPC server (pipe/socket, token)
    ipc_client.py            — IPC client
    config.py                — Project, AppConfig, config.json
    logger.py                — logging + SafeStream
    single_instance.py       — mutex / fcntl
    autostart.py             — registry / .desktop / plist
    platform_utils.py        — OS wrappers (clipboard, active window, pandoc)
    clipboard.py             — wrapper over platform_utils
    mouse_hook.py            — pynput, source factory, click window
    hashes.py                — CRC32 ring, hashes.json
    docx_writer.py           — buffered writer, stamp, pending queue
    markdown_to_docx.py      — mistune AST -> python-docx
    html_to_docx.py          — html4docx (rarely used)
    undo.py                  — remember / undo_last, last_buffers.json
    project_service.py       — single entry point for write_to_project
    writers/                 — writer_base, writer_docx, writer_md,
                               writer_txt, writer_factory
    sources/                 — source_base, source_chrome,
                               source_desktop_chat, source_factory
    gui_settings.py          — SettingsWindow, ProjectDialog
    gui_popup.py             — PopupWindow (choice / status)
    gui_undo.py              — UndoDialog
    ui_helpers.py            — center_window, drag helpers, apply_icon
    i18n.py                  — t(key), init, set_locale, list_languages
    locales/                 — en.json, ru.json, de.json, es.json, ja.json
    pytest.ini               — testpaths = tests
    tests/                   — unit tests for core layer
```
---

## 🗂 Data files (not committed)
```
    config.json              — settings and projects
    hashes.json              — ring of last CRC32 values
    last_buffers.json        — last / prev writes for undo
    logging/                 — chatclipper.log (rotated)
    pending/                 — queued texts when .docx is busy
    ipc_token                — shared IPC token (mode 0600 on POSIX)
    chatclipper.sock         — Unix socket endpoint (POSIX only)
    chatclipper-light.ico    — app / tray icon
```
---

## 🧩 Project structure

Each project has a name, a folder, a file name and a format
(docx / md / txt). Default file name is `<ProjectName>-chat.<fmt>`.
One project is the main one — writes go there by default.
The main project can be switched from the popup, from the status popup,
or from the settings window.

---

## ⚠️ Important: buffered writes

After a copy, the target file is not updated immediately: changes are
buffered and flushed every ~5 seconds or when the app exits. If the
file is open in Word / LibreOffice, it will not reflect the new content
on the fly — close and reopen it to see new entries.

---

## ⚠️ Important: do not edit the .docx by hand

ChatClipper remembers how many paragraphs it added on the last write,
and on undo removes exactly that many. If you manually add, delete or
change paragraphs at the end of the file after a write, the undo will
remove the last paragraphs by count, not the ones the utility wrote.
Possible outcomes:

- Your manual text disappears — the utility counts it as its own.
- Part of the utility's entry remains in the file.

Rule: if you need undo — do not touch the .docx between write and undo.
If you did edit it manually, skip undo and copy the text again.

---

## 🌍 Platforms

- **Windows 10/11** — tray icon, autostart via registry, IPC over named pipe.
- **Linux / WSL / macOS** — experimental: Tk control panel, IPC over Unix socket.

---

## 🌐 Adding a new language

1. Create `locales/<code>.json` with the same keys as `locales/en.json`.
2. Include `"lang.name": "<NativeName>"` — the settings dropdown and the
   OS-locale autodetect read it from the file.
3. No code or config changes needed.
---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Text is not saved | Click the **Copy** button in the chat, or select text and press **Ctrl+C**; make sure Chrome is the active window |
| File is not updated | Wait ~5 s, or close and reopen the file (buffered writes) |
| Ticking sound bothers me | Disable it in Settings → Sound, or pick a quieter .wav |
| Tray icon not visible | Check Windows tray settings; ensure ChatClipper is running |
| Undo removed wrong text | Do not edit the .docx manually between write and undo |
| Language not detected | Set language manually in Settings |

---

## 🤝 Contributing

- [Report a bug](https://github.com/vldbkov/chat-clipper/issues/new)
- [Suggest a feature](https://github.com/vldbkov/chat-clipper/issues/new)
- [Star the repo on GitHub](https://github.com/vldbkov/chat-clipper) ⭐

---

## 📄 License

Copyright (©) 2026, Vladimir Baykov. Licensed under the [MIT License](LICENSE).

---

[🌐 Back to English README](README.md)
