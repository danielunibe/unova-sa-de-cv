from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

from safe_storage import atomic_write_json, file_lock


WORKSPACE = Path(__file__).resolve().parents[1]
DATA_DIR = WORKSPACE / "data"
PERSONAL_WORKSPACE_PATH = DATA_DIR / "personal_workspace.json"
PROJECT_OVERRIDES_PATH = DATA_DIR / "project_overrides.json"
SETTINGS_PATH = DATA_DIR / "settings.json"
PERSONAL_LOCK_PATH = DATA_DIR / ".personal-workspace.lock"

TASK_STATUSES = {"next", "in_progress", "blocked", "review", "done"}
TASK_PRIORITIES = {"low", "medium", "high", "urgent"}
THEMES = {"light", "dark", "system"}
DENSITIES = {"comfortable", "compact"}
START_VIEWS = {"my-work", "projects", "activity", "audit"}
PROJECT_ICONS = {
    "default",
    "software",
    "mobile",
    "game",
    "music",
    "book",
    "board",
    "food",
    "browser",
}
GITHUB_RE = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$",
    re.IGNORECASE,
)
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def default_workspace() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": now_iso(),
        "tasks": [],
        "dismissed_suggestions": [],
    }


def default_overrides() -> dict[str, Any]:
    return {"version": 1, "updated_at": now_iso(), "projects": {}}


def default_settings() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": now_iso(),
        "theme": "system",
        "start_view": "my-work",
        "density": "comfortable",
    }


def read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        import json

        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else default
    except (OSError, json.JSONDecodeError):
        backup = path.with_suffix(path.suffix + ".bak")
        try:
            value = json.loads(backup.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else default
        except (OSError, json.JSONDecodeError):
            return default


def ensure_personal_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with file_lock(PERSONAL_LOCK_PATH):
        if not PERSONAL_WORKSPACE_PATH.exists():
            atomic_write_json(PERSONAL_WORKSPACE_PATH, default_workspace())
        if not PROJECT_OVERRIDES_PATH.exists():
            atomic_write_json(PROJECT_OVERRIDES_PATH, default_overrides())
        if not SETTINGS_PATH.exists():
            atomic_write_json(SETTINGS_PATH, default_settings())


def load_workspace() -> dict[str, Any]:
    return read_json(PERSONAL_WORKSPACE_PATH, default_workspace())


def load_overrides() -> dict[str, Any]:
    return read_json(PROJECT_OVERRIDES_PATH, default_overrides())


def load_settings() -> dict[str, Any]:
    return read_json(SETTINGS_PATH, default_settings())


def _clean_string(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _valid_date(value: Any) -> str:
    text = _clean_string(value, 10)
    if not text:
        return ""
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as error:
        raise ValueError("La fecha debe usar el formato AAAA-MM-DD.") from error


def _normalize_checklist(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    output: list[dict[str, Any]] = []
    for item in value[:40]:
        if isinstance(item, str):
            text = _clean_string(item, 240)
            done = False
            item_id = uuid.uuid4().hex
        elif isinstance(item, dict):
            text = _clean_string(item.get("text"), 240)
            done = bool(item.get("done"))
            item_id = _clean_string(item.get("id"), 64) or uuid.uuid4().hex
        else:
            continue
        if text:
            output.append({"id": item_id, "text": text, "done": done})
    return output


def _normalize_link(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {"type": "", "value": ""}
    link_type = _clean_string(value.get("type"), 12)
    link_value = _clean_string(value.get("value"), 1000)
    if link_type not in {"", "file", "url"}:
        raise ValueError("El enlace relacionado debe ser file, url o vacío.")
    if link_type == "url" and link_value and not link_value.startswith(("http://", "https://")):
        raise ValueError("El enlace web debe comenzar con http:// o https://.")
    return {"type": link_type, "value": link_value}


def _save_workspace(payload: dict[str, Any]) -> dict[str, Any]:
    payload["updated_at"] = now_iso()
    atomic_write_json(PERSONAL_WORKSPACE_PATH, payload)
    return payload


def create_task(payload: dict[str, Any], project_ids: set[str]) -> dict[str, Any]:
    title = _clean_string(payload.get("title"), 240)
    project_id = _clean_string(payload.get("project_id"), 120)
    if not title:
        raise ValueError("La tarea necesita un título.")
    if project_id not in project_ids:
        raise ValueError("El proyecto no existe en el catálogo.")
    status = _clean_string(payload.get("status"), 24) or "next"
    priority = _clean_string(payload.get("priority"), 24) or "medium"
    if status not in TASK_STATUSES:
        raise ValueError("Estado de tarea no válido.")
    if priority not in TASK_PRIORITIES:
        raise ValueError("Prioridad de tarea no válida.")
    timestamp = now_iso()
    with file_lock(PERSONAL_LOCK_PATH):
        workspace = load_workspace()
        tasks = workspace.setdefault("tasks", [])
        order = max(
            (
                int(task.get("order", 0))
                for task in tasks
                if task.get("status") == status and not task.get("archived_at")
            ),
            default=-1,
        ) + 1
        task = {
            "id": uuid.uuid4().hex,
            "title": title,
            "project_id": project_id,
            "status": status,
            "priority": priority,
            "due_date": _valid_date(payload.get("due_date")),
            "notes": _clean_string(payload.get("notes"), 6000),
            "checklist": _normalize_checklist(payload.get("checklist")),
            "link": _normalize_link(payload.get("link")),
            "origin": "suggested" if payload.get("origin") == "suggested" else "manual",
            "source_ref": _clean_string(payload.get("source_ref"), 1000),
            "created_at": timestamp,
            "updated_at": timestamp,
            "completed_at": timestamp if status == "done" else "",
            "archived_at": "",
            "order": order,
        }
        tasks.append(task)
        _save_workspace(workspace)
        return task


def update_task(
    task_id: str,
    payload: dict[str, Any],
    project_ids: set[str],
) -> dict[str, Any]:
    with file_lock(PERSONAL_LOCK_PATH):
        workspace = load_workspace()
        task = next(
            (item for item in workspace.get("tasks", []) if item.get("id") == task_id),
            None,
        )
        if task is None:
            raise KeyError("Tarea no encontrada.")
        if "title" in payload:
            title = _clean_string(payload.get("title"), 240)
            if not title:
                raise ValueError("La tarea necesita un título.")
            task["title"] = title
        if "project_id" in payload:
            project_id = _clean_string(payload.get("project_id"), 120)
            if project_id not in project_ids:
                raise ValueError("El proyecto no existe en el catálogo.")
            task["project_id"] = project_id
        if "status" in payload:
            status = _clean_string(payload.get("status"), 24)
            if status not in TASK_STATUSES:
                raise ValueError("Estado de tarea no válido.")
            task["status"] = status
            task["completed_at"] = now_iso() if status == "done" else ""
        if "priority" in payload:
            priority = _clean_string(payload.get("priority"), 24)
            if priority not in TASK_PRIORITIES:
                raise ValueError("Prioridad de tarea no válida.")
            task["priority"] = priority
        if "due_date" in payload:
            task["due_date"] = _valid_date(payload.get("due_date"))
        if "notes" in payload:
            task["notes"] = _clean_string(payload.get("notes"), 6000)
        if "checklist" in payload:
            task["checklist"] = _normalize_checklist(payload.get("checklist"))
        if "link" in payload:
            task["link"] = _normalize_link(payload.get("link"))
        if "order" in payload:
            try:
                task["order"] = max(0, int(payload.get("order", 0)))
            except (TypeError, ValueError) as error:
                raise ValueError("El orden debe ser un número entero.") from error
        task["updated_at"] = now_iso()
        _save_workspace(workspace)
        return task


def archive_task(task_id: str) -> dict[str, Any]:
    with file_lock(PERSONAL_LOCK_PATH):
        workspace = load_workspace()
        task = next(
            (item for item in workspace.get("tasks", []) if item.get("id") == task_id),
            None,
        )
        if task is None:
            raise KeyError("Tarea no encontrada.")
        task["archived_at"] = now_iso()
        task["updated_at"] = task["archived_at"]
        _save_workspace(workspace)
        return task


def update_settings(payload: dict[str, Any]) -> dict[str, Any]:
    with file_lock(PERSONAL_LOCK_PATH):
        settings = load_settings()
        if "theme" in payload:
            theme = _clean_string(payload.get("theme"), 16)
            if theme not in THEMES:
                raise ValueError("Tema no válido.")
            settings["theme"] = theme
        if "start_view" in payload:
            start_view = _clean_string(payload.get("start_view"), 24)
            if start_view not in START_VIEWS:
                raise ValueError("Vista inicial no válida.")
            settings["start_view"] = start_view
        if "density" in payload:
            density = _clean_string(payload.get("density"), 20)
            if density not in DENSITIES:
                raise ValueError("Densidad no válida.")
            settings["density"] = density
        settings["updated_at"] = now_iso()
        atomic_write_json(SETTINGS_PATH, settings)
        return settings


def update_project_override(project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    with file_lock(PERSONAL_LOCK_PATH):
        overrides = load_overrides()
        projects = overrides.setdefault("projects", {})
        current = projects.setdefault(project_id, {})
        if "github_url" in payload:
            github_url = _clean_string(payload.get("github_url"), 500).rstrip("/")
            if github_url and not GITHUB_RE.match(github_url):
                raise ValueError("La URL debe apuntar a un repositorio de github.com.")
            current["github_url"] = github_url
        if "color" in payload:
            color = _clean_string(payload.get("color"), 7)
            if color and not HEX_COLOR_RE.match(color):
                raise ValueError("El color debe usar formato hexadecimal #RRGGBB.")
            current["color"] = color
        if "icon" in payload:
            icon = _clean_string(payload.get("icon"), 24)
            if icon not in PROJECT_ICONS:
                raise ValueError("Icono de proyecto no válido.")
            current["icon"] = icon
        current["updated_at"] = now_iso()
        overrides["updated_at"] = current["updated_at"]
        atomic_write_json(PROJECT_OVERRIDES_PATH, overrides)
        return current
