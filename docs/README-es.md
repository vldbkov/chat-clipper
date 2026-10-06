# ChatClipper

[![License](https://img.shields.io/badge/license-MIT-yellow)](../LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-windows-0078D6)](https://www.microsoft.com/windows)
[![Kaspersky](https://img.shields.io/badge/Kaspersky-OpenTIP%20clear-brightgreen)](https://opentip.kaspersky.com/38FC30C3E1A40412F40FF27D5ACC2771C34422E928C2E85FBC23188D260F8109)

**Español** · [English](../README.md) · [Русский](README-ru.md) · [Deutsch](README-de.md) · [日本語](README-ja.md)

Utilidad de escritorio que vigila el portapapeles después de un solo clic con el botón
izquierdo en Chrome (botón Copiar en chats web, p. ej. DeepSeek) y añade el texto al
archivo .docx / .md / .txt del proyecto seleccionado.
Funciona en Windows; la compatibilidad con Linux / WSL / macOS es experimental.

**Seguridad:** El instalador de Windows está verificado por Kaspersky OpenTIP. No se detectaron amenazas. El código fuente es abierto y auditable.

---

## 📋 Acerca de

ChatClipper es una utilidad ligera que guarda automáticamente tus chats
con asistentes de IA (DeepSeek, ChatGPT y similares) en un único archivo de proyecto.
Se acabó el copiar y pegar manual: el programa lo hace por ti.

- Vigila el portapapeles y detecta Copiar en chats web.
- Añade el texto copiado al archivo del proyecto (.docx / .md / .txt).
- Admite varios proyectos con un proyecto principal.
- Funciona en segundo plano: vive en la bandeja del sistema.
- En el primer inicio se crea un proyecto Default en `~/ChatClipper`
  con un archivo vacío que ya contiene un encabezado — listo para usar.
- Mientras espera una copia se oye un tic-tac — la app está en marcha
  y lista.

---

## ✨ Características

- Vigilante del portapapeles al hacer clic con el botón izquierdo en Chrome
- Añadir texto a archivos de proyecto: docx, md, txt
- Análisis de Markdown (mistune): encabezados, negrita, cursiva, código en línea,
  bloques de código, listas, citas, tablas
- Conversor Pandoc opcional (si falla, se usa mistune)
- Marca de tiempo y línea separadora antes de cada bloque
- Varios proyectos con un proyecto principal; el formato es por proyecto
- Ventana emergente para elegir proyecto (opacidad y duración configurables)
- Al hacer clic en un proyecto no principal en la ventana emergente, se convierte en principal silenciosamente
- Ventana emergente de estado al inicio; marca PAUSE cuando está en pausa
- Supresión de duplicados mediante anillo CRC32 (5 últimos valores)
- Deshacer la última escritura: la elimina del .docx de origen y la mueve a otro
  proyecto; respeta undo_max_text_len y skip_secrets
- Escrituras .docx en búfer: se vuelcan cada 5 s o al salir
- Cola pendiente cuando el archivo de destino está ocupado
- Comprobación de pérdida de contenido (loss_threshold_pct + loss_min_abs_chars)
- IPC: named pipe en Windows, socket Unix en POSIX, con autenticación por token
- Icono de bandeja (Windows) o panel de control Tk (Linux / WSL / macOS)
- Inicio automático (desactivado por defecto)
- Bandeja activada (desactivada por defecto; solo Windows)
- Protección de instancia única (mutex / bloqueo de archivo)
- i18n: inglés, ruso, alemán, español, japonés
- Detección automática desde la configuración regional del SO en el primer inicio
- Añadir un idioma nuevo colocando `locales/<code>.json` con `"lang.name"`
- Icono de ventana: chatclipper-light.ico

---

## ⚙️ Requisitos
- Windows 10/11 (Linux / macOS — experimental)
- Python 3.10+
- LibreOffice o MS Word para editar .docx
- Chrome como fuente del portapapeles
- Opcional: Pandoc en PATH para Markdown → docx
---

## 🚀 Instalación

### Recomendado: entorno virtual uv
```
    git clone https://github.com/vldbkov/chat-clipper.git
    cd chat-clipper
    uv venv
    uv pip install -r requirements.txt
    uv run python main.py
```
### Alternativa: pip
```
    git clone https://github.com/vldbkov/chat-clipper.git
    cd chat-clipper
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    python main.py
```
### Lo más fácil para usuarios finales: instalador de Windows

Descarga `chatclipper-setup.exe` de la última versión y ejecútalo.
No se requiere instalar Python.
Tras la instalación, aparece el icono de bandeja (Windows).

---

## 🎮 Uso

En el primer inicio ChatClipper crea automáticamente un proyecto Default
en `~/ChatClipper` (carpeta personal del usuario) con un archivo Word
vacío que ya contiene un encabezado. No hace falta configurar nada —
puedes empezar a copiar de inmediato.

1. Abre un chat con IA (DeepSeek, ChatGPT, Qwen, GLM y similares) en Chrome.
2. Copia la respuesta de una de dos formas:
   - haz clic en el botón **Copiar** de la interfaz del chat (recomendado
     — así se conserva el formato HTML), o
   - selecciona el texto y pulsa **Ctrl+C** en el teclado.
3. Aparece una ventana emergente en un segundo con la elección de proyecto:
   haz clic en el que quieras o deja que se cierre automáticamente (se usa
   el principal).
4. Abre el archivo del proyecto en Word — el texto ya está allí (las
   escrituras se retrasan unos 5 segundos).
5. Para añadir más proyectos: panel de ChatClipper → **Configuración** → **Añadir**.
   Marca uno como principal — las escrituras van allí por defecto.

---

## 📁 Disposición del proyecto
```
    main.py                  — punto de entrada, elige modo bandeja o GUI
    app_state.py             — AppState compartido, instancia única
    tray_process.py          — bandeja (pystray), menú, manejadores
    gui_process.py           — bucle principal Tk, hook de ratón, servidor IPC
    control_panel.py         — panel de control Tk en lugar de bandeja
    actions.py               — registro de acciones IPC (dict ACTIONS)
    ipc_server.py            — servidor IPC (pipe/socket, token)
    ipc_client.py            — cliente IPC
    config.py                — Project, AppConfig, config.json
    logger.py                — logging + SafeStream
    single_instance.py       — mutex / fcntl
    autostart.py             — registro / .desktop / plist
    platform_utils.py        — envoltorios de SO (portapapeles, ventana activa, pandoc)
    clipboard.py             — envoltorio sobre platform_utils
    mouse_hook.py            — pynput, fábrica de fuentes, ventana de clic
    hashes.py                — anillo CRC32, hashes.json
    docx_writer.py           — escritor en búfer, sello, cola pendiente
    markdown_to_docx.py      — mistune AST -> python-docx
    html_to_docx.py          — html4docx (rara vez usado)
    undo.py                  — remember / undo_last, last_buffers.json
    project_service.py       — punto de entrada único para write_to_project
    writers/                 — writer_base, writer_docx, writer_md,
                               writer_txt, writer_factory
    sources/                 — source_base, source_chrome,
                               source_desktop_chat, source_factory
    gui_settings.py          — SettingsWindow, ProjectDialog
    gui_popup.py             — PopupWindow (elección / estado)
    gui_undo.py              — UndoDialog
    ui_helpers.py            — center_window, ayudas de arrastre, apply_icon
    i18n.py                  — t(key), init, set_locale, list_languages
    locales/                 — en.json, ru.json, de.json, es.json, ja.json
    pytest.ini               — testpaths = tests
    tests/                   — pruebas unitarias para la capa central
```
---

## 🗂 Archivos de datos (no versionados)
```
    config.json              — ajustes y proyectos
    hashes.json              — anillo de últimos valores CRC32
    last_buffers.json        — últimas / anteriores escrituras para deshacer
    logging/                 — chatclipper.log (rotado)
    pending/                 — textos en cola cuando .docx está ocupado
    ipc_token                — token IPC compartido (modo 0600 en POSIX)
    chatclipper.sock         — endpoint de socket Unix (solo POSIX)
    chatclipper-light.ico    — icono de app / bandeja
```
---

## 🧩 Estructura del proyecto

Cada proyecto tiene un nombre, una carpeta, un nombre de archivo y un formato
(docx / md / txt). El nombre de archivo predeterminado es `<ProjectName>-chat.<fmt>`.
Un proyecto es el principal: las escrituras van allí por defecto.
El proyecto principal se puede cambiar desde la ventana emergente, desde la ventana de estado
o desde la ventana de configuración.

---

## ⚠️ Importante: escrituras en búfer

Después de copiar, el archivo de destino no se actualiza inmediatamente: los cambios se
almacenan en búfer y se vuelcan cada ~5 segundos o al salir de la aplicación. Si el
archivo está abierto en Word / LibreOffice, no reflejará el nuevo contenido
al instante: ciérralo y vuelve a abrirlo para ver las nuevas entradas.

---

## ⚠️ Importante: no edites el .docx a mano

ChatClipper recuerda cuántos párrafos añadió en la última escritura
y al deshacer elimina exactamente esa cantidad. Si añades, eliminas o
cambias párrafos manualmente al final del archivo después de una escritura, deshacer
eliminará los últimos párrafos por cantidad, no los que escribió la utilidad.
Posibles consecuencias:

- Tu texto manual desaparece: la utilidad lo cuenta como propio.
- Parte de la entrada de la utilidad permanece en el archivo.

Regla: si necesitas deshacer, no toques el .docx entre la escritura y el deshacer.
Si lo editaste manualmente, omite deshacer y copia el texto de nuevo.

---

## 🌍 Plataformas

- **Windows 10/11** — icono de bandeja, inicio automático vía registro, IPC por named pipe.
- **Linux / WSL / macOS** — experimental: panel de control Tk, IPC por socket Unix.

---

## 🌐 Añadir un idioma nuevo

1. Crea `locales/<code>.json` con las mismas claves que `locales/en.json`.
2. Incluye `"lang.name": "<NativeName>"`: el desplegable de configuración y la
   autodetección por configuración regional del SO lo leen del archivo.
3. No se necesitan cambios de código ni de configuración.
---

## 🐛 Solución de problemas

| Problema | Solución |
|---------|----------|
| El texto no se guarda | Haz clic en el botón **Copiar** del chat o selecciona el texto y pulsa **Ctrl+C**; asegúrate de que Chrome sea la ventana activa |
| Molesta el tic-tac | Desactívalo en Configuración → Sonido, o elige un .wav más silencioso |
| El archivo no se actualiza | Espera ~5 s, o cierra y vuelve a abrir el archivo (escrituras en búfer) |
| El icono de bandeja no se ve | Revisa la configuración de bandeja de Windows; asegúrate de que ChatClipper esté en ejecución |
| Deshacer eliminó el texto incorrecto | No edites el .docx manualmente entre la escritura y el deshacer |
| El idioma no se detecta | Establece el idioma manualmente en Configuración |

---

## 🤝 Contribuir

- [Informar de un error](https://github.com/vldbkov/chat-clipper/issues/new)
- [Sugerir una función](https://github.com/vldbkov/chat-clipper/issues/new)
- [Dar estrella al repositorio en GitHub](https://github.com/vldbkov/chat-clipper) ⭐

---

## 📄 Licencia

Copyright (©) 2026, Vladimir Baykov. Licenciado bajo la [MIT License](../LICENSE).

---

[🌐 Back to English README](../README.md)