import json
import os
import threading
from dataclasses import dataclass, field, asdict
from typing import List

from logger import log
import i18n

import sys

# Application version — keep in sync with GitHub release tag (v1.0.0)
APP_VERSION = "1.0.0"

# Resource directory: read-only data (sounds, locales, docs, icon)
# Inside PyInstaller bundle, resources live in sys._MEIPASS
# In normal run, they live next to the source files
def _resource_dir() -> str:
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.dirname(os.path.abspath(__file__))


# Data directory: writable runtime files (config, hashes, pending, ipc_token)
# Inside PyInstaller bundle, use %APPDATA%/ChatClipper to avoid writing to Program Files
def _data_dir() -> str:
    if getattr(sys, "frozen", False):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        path = os.path.join(base, "ChatClipper")
        os.makedirs(path, exist_ok=True)
        return path
    return os.path.dirname(os.path.abspath(__file__))


RESOURCE_DIR = _resource_dir()
DATA_DIR = _data_dir()
BASE_DIR = RESOURCE_DIR
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
PENDING_DIR = os.path.join(DATA_DIR, "pending")
HASHES_PATH = os.path.join(DATA_DIR, "hashes.json")
LAST_BUFFERS_PATH = os.path.join(DATA_DIR, "last_buffers.json")
ICON_PATH = os.path.join(RESOURCE_DIR, "chatclipper-light.ico")
ICON_PATH_DARK = os.path.join(RESOURCE_DIR, "chatclipper-dark.ico")
IPC_TOKEN_PATH = os.path.join(DATA_DIR, "ipc_token")

DEFAULT_MIN_TEXT_LEN = 50
DEFAULT_POPUP_SECONDS = 1
DEFAULT_HASH_RING_SIZE = 5
DEFAULT_POPUP_ALPHA = 0.5
DEFAULT_LOSS_THRESHOLD_PCT = 0.10
DEFAULT_LOSS_MIN_ABS_CHARS = 20
DEFAULT_UNDO_MAX_TEXT_LEN = 10000
DEFAULT_SKIP_SECRETS = True
DEFAULT_USE_PANDOC = False
DEFAULT_SOUND_ENABLED = True
DEFAULT_SOUND_NAME = "old-clock-ticking.wav"


@dataclass
class Project:
    name: str
    folder: str
    docx_name: str
    active: bool = True
    format: str = "docx"

    @property
    def docx_path(self) -> str:
        return os.path.join(self.folder, self.docx_name)


@dataclass
class AppConfig:
    projects: List[Project] = field(default_factory=list)
    main_project: str = ""           # имя основного проекта
    min_text_len: int = DEFAULT_MIN_TEXT_LEN
    popup_seconds: int = DEFAULT_POPUP_SECONDS
    hash_ring_size: int = DEFAULT_HASH_RING_SIZE
    popup_alpha: float = DEFAULT_POPUP_ALPHA
    popup_x: int = -1
    popup_y: int = -1
    panel_x: int = -1
    panel_y: int = -1
    paused: bool = False
    autostart: bool = False
    tray_enabled: bool = False
    loss_threshold_pct: float = DEFAULT_LOSS_THRESHOLD_PCT
    loss_min_abs_chars: int = DEFAULT_LOSS_MIN_ABS_CHARS
    active_source: str = "chrome"
    locale: str = "en"
    undo_max_text_len: int = DEFAULT_UNDO_MAX_TEXT_LEN
    skip_secrets: bool = DEFAULT_SKIP_SECRETS
    use_pandoc: bool = DEFAULT_USE_PANDOC
    sound_enabled: bool = DEFAULT_SOUND_ENABLED
    sound_name: str = DEFAULT_SOUND_NAME
    dark_theme: bool = False

    # -------- serialization --------
    def to_dict(self) -> dict:
        d = asdict(self)
        d["projects"] = [asdict(p) for p in self.projects]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "AppConfig":
        projects = [Project(**p) for p in d.get("projects", [])]
        return cls(
            projects=projects,
            main_project=d.get("main_project", ""),
            min_text_len=d.get("min_text_len", DEFAULT_MIN_TEXT_LEN),
            popup_seconds=d.get("popup_seconds", DEFAULT_POPUP_SECONDS),
            hash_ring_size=d.get("hash_ring_size", DEFAULT_HASH_RING_SIZE),
            popup_alpha=d.get("popup_alpha", DEFAULT_POPUP_ALPHA),
            popup_x=d.get("popup_x", -1),
            popup_y=d.get("popup_y", -1),
            panel_x=d.get("panel_x", -1),
            panel_y=d.get("panel_y", -1),
            paused=d.get("paused", False),
            autostart=d.get("autostart", False),
            tray_enabled=d.get("tray_enabled", False),
            loss_threshold_pct=d.get("loss_threshold_pct", DEFAULT_LOSS_THRESHOLD_PCT),
            loss_min_abs_chars=d.get("loss_min_abs_chars", DEFAULT_LOSS_MIN_ABS_CHARS),
            active_source=d.get("active_source", "chrome"),
            locale=d.get("locale", "en"),
            undo_max_text_len=d.get("undo_max_text_len", DEFAULT_UNDO_MAX_TEXT_LEN),
            skip_secrets=d.get("skip_secrets", DEFAULT_SKIP_SECRETS),
            use_pandoc=d.get("use_pandoc", DEFAULT_USE_PANDOC),
            sound_enabled=d.get("sound_enabled", DEFAULT_SOUND_ENABLED),
            sound_name=d.get("sound_name", DEFAULT_SOUND_NAME),
            dark_theme=d.get("dark_theme", False),
        )

    # -------- project access --------
    def get_project(self, name: str) -> Project | None:
        for p in self.projects:
            if p.name == name:
                return p
        return None

    def active_projects(self) -> List[Project]:
        return [p for p in self.projects if p.active]

    def get_main(self) -> Project | None:
        return self.get_project(self.main_project)


# Resolve default locale from OS; fallback to 'en' if not in available locales
# Used on first run (no config.json) or when config.json has no 'locale' field
def _resolve_default_locale() -> str:
    detected = i18n.detect_os_locale()
    available = i18n.list_available_locales()
    if detected in available:
        log.info("locale autodetect: os='%s' -> using '%s'", detected, detected)
        return detected
    log.info("locale autodetect: os='%s' not in %s -> fallback to 'en'", detected, available)
    return "en"


# Create an initial file for a project if it does not exist yet
def _create_project_file(project: Project) -> None:
    fmt = (getattr(project, "format", "docx") or "docx").lower()
    path = project.docx_path
    if fmt == "md" and path.lower().endswith(".docx"):
        path = path[:-5] + ".md"
    elif fmt == "txt" and path.lower().endswith(".docx"):
        path = path[:-5] + ".txt"
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            log.exception("Failed to create project folder %s: %s", folder, e)
            return
    if os.path.exists(path):
        return
    try:
        if fmt == "md":
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write("# " + project.name + "\n")
        elif fmt == "txt":
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(project.name + "\n" + "-" * 40 + "\n")
        else:
            from docx import Document
            doc = Document()
            doc.add_heading(project.name, level=0)
            doc.save(path)
        log.info("created project file: %s", path)
    except Exception as e:
        log.exception("Failed to create project file %s: %s", path, e)


# Create default project on first run or when config has no projects
def _ensure_default_project(cfg: AppConfig) -> None:
    if cfg.projects:
        return
    folder = os.path.join(os.path.expanduser("~"), "ChatClipper")
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        log.exception("Failed to create default folder: %s", e)
    project = Project(name="Default", folder=folder, docx_name="default-chat.docx", active=True, format="docx")
    cfg.projects.append(project)
    if not cfg.main_project:
        cfg.main_project = "Default"
    _create_project_file(project)
    log.info("first run: created default project at %s", folder)


# Ensure exactly one main project exists, and it is always active
def _normalize_main_project(cfg: AppConfig) -> None:
    if not cfg.projects:
        return
    main = cfg.get_project(cfg.main_project) if cfg.main_project else None
    if main is None:
        active = [p for p in cfg.projects if p.active]
        target = active[0] if active else cfg.projects[0]
    else:
        target = main
    if not target.active:
        target.active = True
    if cfg.main_project != target.name:
        log.info("main_project normalized to '%s'", target.name)
        cfg.main_project = target.name


# Load config from disk; auto-create default project if missing
def load_config() -> AppConfig:
    if not os.path.exists(CONFIG_PATH):
        log.info("config.json not found - creating default")
        cfg = AppConfig()
        cfg.locale = _resolve_default_locale()
        _ensure_default_project(cfg)
        _normalize_main_project(cfg)
        save_config(cfg)
        return cfg
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        if "locale" not in data or not data.get("locale"):
            data["locale"] = _resolve_default_locale()
        cfg = AppConfig.from_dict(data)
        log.info("config.json loaded: %d projects", len(cfg.projects))
        if not cfg.projects:
            _ensure_default_project(cfg)
            save_config(cfg)
        _normalize_main_project(cfg)
        return cfg
    except Exception as e:
        log.exception("Error reading config.json: %s", e)
        cfg = AppConfig()
        cfg.locale = _resolve_default_locale()
        _ensure_default_project(cfg)
        _normalize_main_project(cfg)
        return cfg


_pending_cfg = None
_save_timer = None
_save_lock = threading.Lock()
DEBOUNCE_SECONDS = 1.0


# Write config.json immediately (no debounce)
def _write_config_now(cfg: AppConfig) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8", newline="\n") as f:
            json.dump(cfg.to_dict(), f, ensure_ascii=False, indent=2)
        log.info("config.json saved")
    except Exception as e:
        log.exception("Error saving config.json: %s", e)


# Debounced save: coalesce multiple calls within DEBOUNCE_SECONDS
# The last cfg wins (stored in module-level _pending_cfg)
def save_config(cfg: AppConfig) -> None:
    global _save_timer, _pending_cfg
    with _save_lock:
        _pending_cfg = cfg
        if _save_timer is not None:
            _save_timer.cancel()
        _save_timer = threading.Timer(DEBOUNCE_SECONDS, _flush_config)
        _save_timer.daemon = True
        _save_timer.start()


# Flush pending config to disk
# Called by timer; ensures the last assigned cfg is written
# Global for pending config
def _flush_config() -> None:
    global _save_timer, _pending_cfg
    with _save_lock:
        cfg = _pending_cfg
        _save_timer = None
    if cfg is not None:
        _write_config_now(cfg)


def ensure_dirs() -> None:
    os.makedirs(PENDING_DIR, exist_ok=True)


# Force flush pending config to disk (use before os._exit)
def flush_config() -> None:
    global _save_timer
    if _save_timer is not None:
        try:
            _save_timer.cancel()
        except Exception:
            pass
        _save_timer = None
    _flush_config()