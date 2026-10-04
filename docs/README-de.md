# ChatClipper

[![License](https://img.shields.io/badge/license-MIT-yellow)](../LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-windows-0078D6)](https://www.microsoft.com/windows)

**Deutsch** · [English](../README.md) · [Русский](README-ru.md) · [Español](README-es.md) · [日本語](README-ja.md)

Desktop-Dienstprogramm, das die Zwischenablage nach einem einzelnen Linksklick in
Chrome beobachtet (Schaltfläche „Kopieren“ in Web-Chats, z. B. DeepSeek) und den Text
an die Datei .docx / .md / .txt des ausgewählten Projekts anhängt.
Läuft unter Windows; Linux-/WSL-/macOS-Unterstützung ist experimentell.

---

## 📋 Über

ChatClipper ist ein leichtgewichtiges Dienstprogramm, das Ihre Chats
mit KI-Assistenten (DeepSeek, ChatGPT und ähnliche) automatisch in einer einzigen
Projektdatei speichert. Kein manuelles Kopieren und Einfügen mehr — das Programm
erledigt das für Sie.

- Beobachtet die Zwischenablage und erkennt „Kopieren“ in Web-Chats.
- Hängt den kopierten Text an die Projektdatei an (.docx / .md / .txt).
- Unterstützt mehrere Projekte mit einem Hauptprojekt.
- Läuft im Hintergrund — lebt im System-Tray.

---

## ✨ Funktionen

- Zwischenablage-Watcher bei Linksklick in Chrome
- Text an Projektdateien anhängen: docx, md, txt
- Markdown-Parsing (mistune): Überschriften, fett, kursiv, Inline-Code,
  Codeblöcke, Listen, Zitate, Tabellen
- Optionaler Pandoc-Konverter (Fallback auf mistune bei Fehler)
- Zeitstempel und Trennlinie vor jedem Block
- Mehrere Projekte mit einem Hauptprojekt; Projektformat ist pro Projekt
- Popup-Fenster zur Projektauswahl (Deckkraft und Dauer konfigurierbar)
- Klick auf ein Nicht-Hauptprojekt im Popup macht es still zum Hauptprojekt
- Status-Popup beim Start; PAUSE-Stempel bei Pause
- Duplikatunterdrückung über CRC32-Ring (5 letzte Werte)
- Letzte Schreiboperation rückgängig machen: entfernt sie aus der Quell-.docx und
  verschiebt sie in ein anderes Projekt; berücksichtigt undo_max_text_len und skip_secrets
- Gepufferte .docx-Schreibvorgänge: alle 5 s oder beim Beenden geleert
- Warteschlange, wenn die Zieldatei beschäftigt ist
- Inhaltverlustprüfung (loss_threshold_pct + loss_min_abs_chars)
- IPC: Named Pipe unter Windows, Unix-Socket unter POSIX, mit Token-Authentifizierung
- Tray-Symbol (Windows) oder Tk-Systemsteuerung (Linux / WSL / macOS)
- Autostart (standardmäßig aus)
- Tray aktiviert (standardmäßig aus; nur Windows)
- Einzelinstanz-Schutz (Mutex / Dateisperre)
- i18n: Englisch, Russisch, Deutsch, Spanisch, Japanisch
- Automatische Erkennung aus OS-Locale beim ersten Start
- Neue Sprache hinzufügen: `locales/<code>.json` mit `"lang.name"` ablegen
- Fenstersymbol: chatclipper-light.ico

---

## ⚙️ Anforderungen
- Windows 10/11 (Linux / macOS — experimentell)
- Python 3.10+
- LibreOffice oder MS Word zum Bearbeiten von .docx
- Chrome als Zwischenablagequelle
- Optional: Pandoc im PATH für Markdown → docx
---

## 🚀 Installation

### Empfohlen: uv-virtuelle Umgebung
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
### Am einfachsten für Endnutzer: Windows-Installer

Laden Sie `chatclipper-setup.exe` aus dem neuesten Release herunter und führen Sie es aus.
Keine Python-Installation erforderlich.
Nach der Installation erscheint das Tray-Symbol (Windows).

---

## 🎮 Verwendung

1. Klicken Sie auf das ChatClipper-Tray-Symbol → **Einstellungen**.
2. Fügen Sie ein Projekt hinzu: Name, Ordner, Dateiname. Beispiel: „DeepSeek“ → „deepseek-chat.docx“.
3. Legen Sie ein Projekt als Hauptprojekt fest — Schreibvorgänge gehen standardmäßig dorthin.
4. Öffnen Sie einen Chat mit einer KI, kopieren Sie die Antwort (Strg+C oder die Schaltfläche „Kopieren“).
5. ChatClipper hängt den Text an die Datei an. Öffnen Sie sie in Word, um das Ergebnis zu sehen.

---

## 📁 Projektaufbau
```
    main.py                  — Einstiegspunkt, wählt Tray- oder GUI-Modus
    app_state.py             — gemeinsamer AppState, Einzelinstanz
    tray_process.py          — Tray (pystray), Menü, Handler
    gui_process.py           — Tk-Hauptschleife, Maus-Hook, IPC-Server
    control_panel.py         — Tk-Systemsteuerung statt Tray
    actions.py               — IPC-Aktionsregistry (ACTIONS-Dict)
    ipc_server.py            — IPC-Server (Pipe/Socket, Token)
    ipc_client.py            — IPC-Client
    config.py                — Project, AppConfig, config.json
    logger.py                — Logging + SafeStream
    single_instance.py       — Mutex / fcntl
    autostart.py             — Registry / .desktop / plist
    platform_utils.py        — OS-Wrapper (Zwischenablage, aktives Fenster, pandoc)
    clipboard.py             — Wrapper über platform_utils
    mouse_hook.py            — pynput, Source-Factory, Klickfenster
    hashes.py                — CRC32-Ring, hashes.json
    docx_writer.py           — gepufferter Writer, Stempel, Warteschlange
    markdown_to_docx.py      — mistune AST -> python-docx
    html_to_docx.py          — html4docx (selten verwendet)
    undo.py                  — remember / undo_last, last_buffers.json
    project_service.py       — einzelner Einstiegspunkt für write_to_project
    writers/                 — writer_base, writer_docx, writer_md,
                               writer_txt, writer_factory
    sources/                 — source_base, source_chrome,
                               source_desktop_chat, source_factory
    gui_settings.py          — SettingsWindow, ProjectDialog
    gui_popup.py             — PopupWindow (Auswahl / Status)
    gui_undo.py              — UndoDialog
    ui_helpers.py            — center_window, Drag-Helfer, apply_icon
    i18n.py                  — t(key), init, set_locale, list_languages
    locales/                 — en.json, ru.json, de.json, es.json, ja.json
    pytest.ini               — testpaths = tests
    tests/                   — Unit-Tests für die Kernschicht
```
---

## 🗂 Datendateien (nicht committet)
```
    config.json              — Einstellungen und Projekte
    hashes.json              — Ring der letzten CRC32-Werte
    last_buffers.json        — letzte / vorherige Schreibvorgänge für Undo
    logging/                 — chatclipper.log (rotierend)
    pending/                 — wartende Texte, wenn .docx beschäftigt ist
    ipc_token                — gemeinsames IPC-Token (Modus 0600 unter POSIX)
    chatclipper.sock         — Unix-Socket-Endpunkt (nur POSIX)
    chatclipper-light.ico    — App-/Tray-Symbol
```
---

## 🧩 Projektstruktur

Jedes Projekt hat einen Namen, einen Ordner, einen Dateinamen und ein Format
(docx / md / txt). Standard-Dateiname ist `<ProjectName>-chat.<fmt>`.
Ein Projekt ist das Hauptprojekt — Schreibvorgänge gehen standardmäßig dorthin.
Das Hauptprojekt kann im Popup, im Status-Popup oder im Einstellungsfenster gewechselt werden.

---

## ⚠️ Wichtig: gepufferte Schreibvorgänge

Nach einem Kopiervorgang wird die Zieldatei nicht sofort aktualisiert: Änderungen werden
gepuffert und etwa alle 5 Sekunden oder beim Beenden der App geleert. Wenn die
Datei in Word / LibreOffice geöffnet ist, zeigt sie den neuen Inhalt nicht
sofort an — schließen und öffnen Sie sie erneut, um neue Einträge zu sehen.

---

## ⚠️ Wichtig: .docx nicht manuell bearbeiten

ChatClipper merkt sich, wie viele Absätze es beim letzten Schreiben hinzugefügt hat,
und entfernt beim Undo genau diese Anzahl. Wenn Sie nach dem Schreiben manuell Absätze
am Ende der Datei hinzufügen, löschen oder ändern, entfernt Undo die letzten Absätze
nach Anzahl, nicht die, die das Dienstprogramm geschrieben hat.
Mögliche Folgen:

- Ihr manueller Text verschwindet — das Dienstprogramm zählt ihn als eigenen.
- Ein Teil des Eintrags des Dienstprogramms bleibt in der Datei.

Regel: Wenn Sie Undo benötigen — berühren Sie die .docx zwischen Schreiben und Undo nicht.
Wenn Sie sie manuell bearbeitet haben, überspringen Sie Undo und kopieren Sie den Text erneut.

---

## 🌍 Plattformen

- **Windows 10/11** — Tray-Symbol, Autostart über Registry, IPC über Named Pipe.
- **Linux / WSL / macOS** — experimentell: Tk-Systemsteuerung, IPC über Unix-Socket.

---

## 🌐 Neue Sprache hinzufügen

1. Erstellen Sie `locales/<code>.json` mit denselben Schlüsseln wie `locales/en.json`.
2. Fügen Sie `"lang.name": "<NativeName>"` hinzu — das Einstellungs-Dropdown und die
   OS-Locale-Automatikerkennung lesen es aus der Datei.
3. Keine Code- oder Konfigurationsänderungen erforderlich.
---

## 🐛 Fehlerbehebung

| Problem | Lösung |
|---------|----------|
| Text wird nicht gespeichert | Prüfen Sie, ob Chrome beim Kopieren das aktive Fenster ist |
| Datei wird nicht aktualisiert | Warten Sie ~5 s, oder schließen und öffnen Sie die Datei (gepufferte Schreibvorgänge) |
| Tray-Symbol nicht sichtbar | Prüfen Sie die Windows-Tray-Einstellungen; stellen Sie sicher, dass ChatClipper läuft |
| Undo hat falschen Text entfernt | Bearbeiten Sie die .docx zwischen Schreiben und Undo nicht manuell |
| Sprache nicht erkannt | Stellen Sie die Sprache in den Einstellungen manuell ein |

---

## 🤝 Mitwirken

- [Fehler melden](https://github.com/vldbkov/chat-clipper/issues/new)
- [Funktion vorschlagen](https://github.com/vldbkov/chat-clipper/issues/new)
- [Repo auf GitHub mit Stern markieren](https://github.com/vldbkov/chat-clipper) ⭐

---

## 📄 Lizenz

Copyright (©) 2026, Vladimir Baykov. Lizenziert unter der [MIT License](../LICENSE).

---

[🌐 Back to English README](../README.md)