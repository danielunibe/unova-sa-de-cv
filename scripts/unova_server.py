from __future__ import annotations

import argparse
import hashlib
import json
import logging
import mimetypes
import os
import re
import subprocess
import sys
import threading
import time
from datetime import date, datetime, time as clock_time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from history_engine import (  # noqa: E402
    DATA_DIR,
    HISTORY_META_PATH,
    LOCALHOST_STATE_PATH,
    MONITOR_STATUS_PATH,
    STATE_DIR,
    append_event,
    atomic_write_json,
    catalog_stats,
    enrich_and_track,
    load_catalog,
    load_events,
    load_json,
    make_event,
    now_iso,
    update_localhost_flags,
)
from workspace_store import (  # noqa: E402
    archive_task,
    create_task,
    ensure_personal_files,
    load_overrides,
    load_settings,
    load_workspace,
    update_project_override,
    update_settings,
    update_task,
)

HOST = "127.0.0.1"
PORT = 4173
POLL_SECONDS = 60
ACTIVE_SCAN_SECONDS = 15 * 60
NIGHTLY_AT = clock_time(hour=23, minute=30)
AUDIT_SCRIPT = SCRIPT_DIR / "audit_projects.py"
LOG_DIR = WORKSPACE / "history" / "logs"
LOG_PATH = LOG_DIR / "monitor.log"

scan_lock = threading.Lock()
scan_thread: threading.Thread | None = None
stop_event = threading.Event()
GITHUB_REMOTE_RE = re.compile(
    r"(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?$",
    re.IGNORECASE,
)
PIPELINE_AXES = [
    ("definicion", "Definición", 15, "file-text"),
    ("diseno", "Diseño", 10, "palette"),
    ("arquitectura", "Arquitectura", 10, "blocks"),
    ("implementacion", "Implementación", 30, "code"),
    ("pruebas", "Pruebas", 15, "flask"),
    ("empaquetado", "Empaquetado", 10, "package"),
    ("continuidad", "Continuidad", 5, "route"),
    ("validacion", "Validación", 5, "badge-check"),
]


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def monitor_status(**updates: Any) -> dict[str, Any]:
    payload = load_json(MONITOR_STATUS_PATH, {})
    payload.update(updates)
    payload["updated_at"] = now_iso()
    atomic_write_json(MONITOR_STATUS_PATH, payload)
    return payload


def run_catalog_audit() -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), "--catalog-only"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60 * 45,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or process.stdout.strip() or "Auditoría fallida")
    output = process.stdout.strip()
    for marker in ("\n{", "{"):
        start = output.rfind(marker)
        if start >= 0:
            candidate = output[start + (1 if marker == "\n{" else 0):]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    return {"output_tail": output[-2000:]}


def perform_scan(reason: str, project_ids: list[str] | None = None) -> dict[str, Any]:
    with scan_lock:
        started_at = now_iso()
        monitor_status(
            state="scanning",
            current_reason=reason,
            scan_started_at=started_at,
            last_error="",
        )
        try:
            catalog_result: dict[str, Any] | None = None
            if not project_ids:
                catalog_result = run_catalog_audit()
            history_result = enrich_and_track(
                reason=reason,
                project_ids=project_ids,
                create_backfill=True,
                write_project_status=True,
            )
            result = {
                "started_at": started_at,
                "completed_at": now_iso(),
                "reason": reason,
                "scope": project_ids or "global",
                "catalog": catalog_result,
                "history": history_result,
            }
            monitor_status(
                state="idle",
                current_reason="",
                last_scan=result,
                last_success_at=result["completed_at"],
            )
            logging.info("Escaneo completado: %s", json.dumps(result, ensure_ascii=False))
            return result
        except Exception as error:  # noqa: BLE001
            logging.exception("Escaneo fallido")
            monitor_status(
                state="error",
                current_reason="",
                last_error=str(error),
                last_failure_at=now_iso(),
            )
            raise


def request_scan(reason: str = "manual_api") -> tuple[bool, str]:
    global scan_thread
    if scan_thread and scan_thread.is_alive():
        return False, "Ya hay una auditoría en curso."
    scan_thread = threading.Thread(
        target=_scan_worker,
        args=(reason, None),
        name="unova-manual-scan",
        daemon=True,
    )
    scan_thread.start()
    return True, "Auditoría iniciada."


def _scan_worker(reason: str, project_ids: list[str] | None) -> None:
    try:
        perform_scan(reason, project_ids)
    except Exception:
        return


def powershell_json(script: str) -> Any:
    process = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or "No se pudieron consultar puertos locales.")
    output = process.stdout.strip()
    return json.loads(output) if output else []


def discover_localhost() -> list[dict[str, Any]]:
    ps_script = r"""
$processes = @{}
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | ForEach-Object {
  $processes[[int]$_.ProcessId] = $_
}
$items = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object {
    $_.LocalPort -ne 4173 -and
    $_.LocalPort -ge 1024 -and
    $_.OwningProcess -gt 0 -and
    $_.LocalAddress -in @('127.0.0.1','0.0.0.0','::1','::')
  } |
  ForEach-Object {
    $proc = $processes[[int]$_.OwningProcess]
    [pscustomobject]@{
      address = $_.LocalAddress
      port = $_.LocalPort
      pid = $_.OwningProcess
      name = $proc.Name
      executable = $proc.ExecutablePath
      command = $proc.CommandLine
      parent_pid = $proc.ParentProcessId
    }
  } |
  Sort-Object port,pid -Unique
@($items) | ConvertTo-Json -Compress
"""
    data = powershell_json(ps_script)
    if isinstance(data, dict):
        return [data]
    return data if isinstance(data, list) else []


def normalized(value: Any) -> str:
    return os.path.normcase(os.path.normpath(str(value or "")))


def associate_listeners(
    listeners: list[dict[str, Any]], rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    roots = [
        (row, normalized(row.get("ruta_vigente", "")))
        for row in rows
        if row.get("ruta_vigente")
    ]
    associated: list[dict[str, Any]] = []
    for listener in listeners:
        haystack = normalized(
            " ".join(
                str(listener.get(key, ""))
                for key in ("command", "executable")
            )
        )
        candidates: list[tuple[int, dict[str, str]]] = []
        for row, root in roots:
            if root and root in haystack:
                candidates.append((len(root), row))
                continue
            folder_name = Path(root).name.lower()
            if len(folder_name) >= 8 and folder_name in haystack.lower():
                candidates.append((len(folder_name), row))
        if not candidates:
            continue
        _, row = max(candidates, key=lambda item: item[0])
        associated.append(
            {
                **listener,
                "project_id": row.get("id", ""),
                "project": row.get("proyecto", ""),
                "root": row.get("ruta_vigente", ""),
            }
        )
    return associated


def listener_key(listener: dict[str, Any]) -> str:
    return f"{listener.get('project_id')}:{listener.get('port')}:{listener.get('pid')}"


def register_localhost_changes(
    previous: list[dict[str, Any]],
    current: list[dict[str, Any]],
    rows: list[dict[str, str]],
) -> None:
    row_by_id = {row.get("id", ""): row for row in rows}
    previous_map = {listener_key(item): item for item in previous}
    current_map = {listener_key(item): item for item in current}
    for key, listener in current_map.items():
        if key in previous_map:
            continue
        row = row_by_id.get(listener.get("project_id", ""))
        if row:
            append_event(
                make_event(
                    row,
                    event_type="localhost_started",
                    reason="localhost_monitor",
                    precision="exact",
                    details={
                        "port": listener.get("port"),
                        "pid": listener.get("pid"),
                        "command": listener.get("command", ""),
                    },
                )
            )
    for key, listener in previous_map.items():
        if key in current_map:
            continue
        row = row_by_id.get(listener.get("project_id", ""))
        if row:
            append_event(
                make_event(
                    row,
                    event_type="localhost_stopped",
                    reason="localhost_monitor",
                    precision="exact",
                    details={
                        "port": listener.get("port"),
                        "pid": listener.get("pid"),
                    },
                )
            )


def refresh_localhost() -> list[dict[str, Any]]:
    rows = load_catalog()
    listeners = associate_listeners(discover_localhost(), rows)
    prior_state = load_json(LOCALHOST_STATE_PATH, {})
    previous = prior_state.get("listeners", [])
    register_localhost_changes(previous, listeners, rows)
    active_ids = {item.get("project_id", "") for item in listeners}
    update_localhost_flags(active_ids)
    atomic_write_json(
        LOCALHOST_STATE_PATH,
        {
            "captured_at": now_iso(),
            "listeners": listeners,
            "unmatched_note": "Solo se publican listeners asociados de forma verificable a una ruta canónica.",
        },
    )
    monitor_status(
        localhost={"active": listeners, "count": len(listeners)},
        last_error="",
    )
    return listeners


def should_run_global_catchup() -> bool:
    history_meta = load_json(HISTORY_META_PATH, {})
    return history_meta.get("last_global_scan_date") != date.today().isoformat()


def monitor_loop() -> None:
    last_active_scan = 0.0
    nightly_date = ""
    while not stop_event.is_set():
        try:
            listeners = refresh_localhost()
            now = datetime.now().astimezone()
            if should_run_global_catchup() and not scan_lock.locked():
                perform_scan("startup_catchup")
            if (
                now.time() >= NIGHTLY_AT
                and nightly_date != now.date().isoformat()
                and not scan_lock.locked()
            ):
                perform_scan("nightly_2330")
                nightly_date = now.date().isoformat()
            active_ids = sorted({item["project_id"] for item in listeners})
            if (
                active_ids
                and time.monotonic() - last_active_scan >= ACTIVE_SCAN_SECONDS
                and not scan_lock.locked()
            ):
                perform_scan("localhost_active", active_ids)
                last_active_scan = time.monotonic()
        except Exception as error:  # noqa: BLE001
            logging.exception("Fallo en ciclo del monitor")
            monitor_status(last_error=str(error), last_monitor_failure_at=now_iso())
        stop_event.wait(POLL_SECONDS)


def read_json_file(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def project_map() -> dict[str, dict[str, str]]:
    return {row.get("id", ""): row for row in load_catalog() if row.get("id")}


def normalize_github_remote(value: str) -> str:
    match = GITHUB_REMOTE_RE.search(value.strip())
    if not match:
        return ""
    owner, repo = match.groups()
    return f"https://github.com/{owner}/{repo.removesuffix('.git')}"


def detect_github_url(root: Path) -> str:
    candidates = [root / ".git" / "config"]
    try:
        candidates.extend(
            child / ".git" / "config"
            for child in root.iterdir()
            if child.is_dir()
        )
    except OSError:
        pass
    for config in candidates[:40]:
        try:
            text = config.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if line.strip().lower().startswith("url") and "=" in line:
                url = normalize_github_remote(line.split("=", 1)[1])
                if url:
                    return url
    return ""


def github_url_for_project(
    row: dict[str, str],
    override: dict[str, Any] | None = None,
) -> str:
    manual_url = str((override or {}).get("github_url") or "").strip()
    if manual_url:
        return manual_url
    if row.get("tiene_git") != "sí":
        return ""
    return detect_github_url(Path(row.get("ruta_vigente", "")))


def catalog_payload() -> list[dict[str, Any]]:
    overrides = load_overrides().get("projects", {})
    projects: list[dict[str, Any]] = []
    for row in load_catalog():
        override = overrides.get(row.get("id", ""), {})
        root = Path(row.get("ruta_vigente", ""))
        projects.append(
            {
                **row,
                "github_url": github_url_for_project(row, override),
                "folder_available": root.exists() and root.is_dir(),
            }
        )
    return projects


def suggestion_id(project_id: str, text: str, source_ref: str) -> str:
    digest = hashlib.sha1(
        f"{project_id}|{text}|{source_ref}".encode("utf-8")
    ).hexdigest()[:16]
    return f"suggestion-{digest}"


def project_suggestions(
    row: dict[str, str],
    progress: dict[str, Any],
    dismissed: set[str],
) -> list[dict[str, str]]:
    suggestions: list[dict[str, str]] = []
    pending = [
        item.strip()
        for item in row.get("pendientes_documentados", "").split(";")
        if item.strip() and item.strip() != "No documentado"
    ]
    for item in pending[:8]:
        item_id = suggestion_id(row["id"], item, "documented-pending")
        if item_id not in dismissed:
            suggestions.append(
                {
                    "id": item_id,
                    "title": item,
                    "project_id": row["id"],
                    "origin": "suggested",
                    "source_ref": "Pendiente documentado",
                    "priority": "medium",
                }
            )
    if not suggestions:
        for missing in progress.get("missing", [])[:3]:
            title = f"Completar {missing}"
            item_id = suggestion_id(row["id"], title, f"pipeline:{missing}")
            if item_id not in dismissed:
                suggestions.append(
                    {
                        "id": item_id,
                        "title": title,
                        "project_id": row["id"],
                        "origin": "suggested",
                        "source_ref": "Evidencia faltante del pipeline",
                        "priority": "low",
                    }
                )
    return suggestions


def pipeline_payload(
    row: dict[str, str],
    progress: dict[str, Any],
    state_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    breakdown = progress.get("breakdown", {})
    summary = state_payload.get("summary", {})
    evidence = {
        "definicion": "Propósito, problema y público documentados.",
        "diseno": f"{summary.get('asset_count', 0)} recursos visuales; documentación de diseño cuando existe.",
        "arquitectura": f"{summary.get('manifest_count', 0)} manifiestos o archivos estructurales detectados.",
        "implementacion": f"{summary.get('code_count', 0)} archivos de código detectados.",
        "pruebas": f"{summary.get('test_count', 0)} archivos o referencias de prueba detectados.",
        "empaquetado": f"Plataformas: {row.get('plataformas') or 'No documentado'}.",
        "continuidad": (
            f"Próximo paso: {row.get('proximo_paso')}"
            if row.get("proximo_paso") not in {"", "No documentado"}
            else "No existe un próximo paso documentado."
        ),
        "validacion": (
            "Existe evidencia de pruebas o validación."
            if summary.get("test_count", 0)
            else "No existe evidencia suficiente de validación."
        ),
    }
    sources = {
        "definicion": "Catálogo y documentación principal",
        "diseno": "Recursos visuales y documentos de diseño",
        "arquitectura": "Manifiestos y estructura detectada",
        "implementacion": "Snapshot de archivos de código",
        "pruebas": "Archivos y referencias de pruebas",
        "empaquetado": "Manifiestos, plataformas y artefactos",
        "continuidad": "Pendientes, próximo paso y ficha de estado",
        "validacion": "Pruebas y evidencia documental de validación",
    }
    output: list[dict[str, Any]] = []
    for key, label, maximum, icon in PIPELINE_AXES:
        value = int(breakdown.get(key, 0) or 0)
        status = "completed" if value >= maximum else "partial" if value > 0 else "pending"
        output.append(
            {
                "key": key,
                "label": label,
                "icon": icon,
                "value": value,
                "maximum": maximum,
                "status": status,
                "evidence": evidence[key],
                "source": sources[key],
                "confidence": row.get("confianza_progreso") or "Baja",
            }
        )
    return output


def project_payload(project_id: str) -> dict[str, Any]:
    rows = project_map()
    row = rows.get(project_id)
    if row is None:
        raise KeyError("Proyecto no encontrado.")
    progress = read_json_file(DATA_DIR / "progress.json", {}).get(project_id, {})
    state_payload = read_json_file(STATE_DIR / f"{project_id}.json", {})
    workspace = load_workspace()
    overrides = load_overrides()
    override = overrides.get("projects", {}).get(project_id, {})
    root = Path(row.get("ruta_vigente", ""))
    github_url = github_url_for_project(row, override)
    events = [
        event
        for event in load_events(limit=3000)
        if event.get("project_id") == project_id
    ][:60]
    tasks = [
        task
        for task in workspace.get("tasks", [])
        if task.get("project_id") == project_id and not task.get("archived_at")
    ]
    dismissed = set(workspace.get("dismissed_suggestions", []))
    return {
        "project": row,
        "progress": progress,
        "pipeline": pipeline_payload(row, progress, state_payload),
        "tasks": sorted(tasks, key=lambda item: (item.get("status", ""), item.get("order", 0))),
        "suggestions": project_suggestions(row, progress, dismissed),
        "events": events,
        "github_url": github_url,
        "folder_available": root.exists(),
        "preferences": override,
        "state_summary": state_payload.get("summary", {}),
    }


class UnovaHandler(BaseHTTPRequestHandler):
    server_version = "UNOVA/1.0"

    def log_message(self, format_string: str, *args: Any) -> None:
        logging.info("%s - %s", self.address_string(), format_string % args)

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Content-Length no válido.") from error
        if length <= 0:
            return {}
        if length > 1_000_000:
            raise ValueError("La solicitud excede el tamaño permitido.")
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("El cuerpo debe ser JSON válido.") from error
        if not isinstance(value, dict):
            raise ValueError("El cuerpo JSON debe ser un objeto.")
        return value

    def send_api_error(self, error: Exception) -> None:
        if isinstance(error, KeyError):
            message = str(error).strip("'")
            self.send_json({"error": message}, HTTPStatus.NOT_FOUND)
        elif isinstance(error, (ValueError, TimeoutError)):
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        else:
            logging.exception("Error inesperado de API")
            self.send_json(
                {"error": "Ocurrió un error interno al procesar la solicitud."},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api_get(parsed.path, parse_qs(parsed.query))
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/scan":
                started, message = request_scan("manual_api")
                status = HTTPStatus.ACCEPTED if started else HTTPStatus.CONFLICT
                self.send_json({"started": started, "message": message, "at": now_iso()}, status)
                return
            if parsed.path == "/api/tasks":
                task = create_task(self.read_json_body(), set(project_map()))
                self.send_json({"task": task}, HTTPStatus.CREATED)
                return
            task_archive = re.fullmatch(r"/api/tasks/([^/]+)/archive", parsed.path)
            if task_archive:
                task = archive_task(unquote(task_archive.group(1)))
                self.send_json({"task": task})
                return
            open_folder = re.fullmatch(r"/api/projects/([^/]+)/open-folder", parsed.path)
            if open_folder:
                project_id = unquote(open_folder.group(1))
                row = project_map().get(project_id)
                if row is None:
                    raise KeyError("Proyecto no encontrado.")
                root = Path(row.get("ruta_vigente", "")).resolve()
                if not root.exists() or not root.is_dir():
                    raise ValueError("La carpeta raíz no está disponible.")
                subprocess.Popen(
                    ["explorer.exe", str(root)],
                    cwd=root,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                self.send_json({"opened": True, "project_id": project_id})
                return
            self.send_json({"error": "Endpoint no encontrado."}, HTTPStatus.NOT_FOUND)
        except Exception as error:  # noqa: BLE001
            self.send_api_error(error)

    def do_PATCH(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/settings":
                self.send_json({"settings": update_settings(self.read_json_body())})
                return
            task_match = re.fullmatch(r"/api/tasks/([^/]+)", parsed.path)
            if task_match:
                task = update_task(
                    unquote(task_match.group(1)),
                    self.read_json_body(),
                    set(project_map()),
                )
                self.send_json({"task": task})
                return
            preferences = re.fullmatch(
                r"/api/projects/([^/]+)/preferences",
                parsed.path,
            )
            if preferences:
                project_id = unquote(preferences.group(1))
                if project_id not in project_map():
                    raise KeyError("Proyecto no encontrado.")
                override = update_project_override(project_id, self.read_json_body())
                self.send_json({"preferences": override})
                return
            self.send_json({"error": "Endpoint no encontrado."}, HTTPStatus.NOT_FOUND)
        except Exception as error:  # noqa: BLE001
            self.send_api_error(error)

    def handle_api_get(self, path: str, query: dict[str, list[str]]) -> None:
        if path == "/api/catalog":
            self.send_json({"generated_at": now_iso(), "projects": catalog_payload()})
        elif path == "/api/stats":
            self.send_json(catalog_stats())
        elif path == "/api/events":
            try:
                limit = min(max(int(query.get("limit", ["500"])[0]), 1), 5000)
            except ValueError:
                limit = 500
            events = load_events(limit=limit)
            project_id = query.get("project_id", [""])[0]
            if project_id:
                events = [item for item in events if item.get("project_id") == project_id]
            self.send_json({"events": events, "count": len(events)})
        elif path == "/api/progress":
            self.send_json(read_json_file(DATA_DIR / "progress.json", {}))
        elif path == "/api/monitor":
            self.send_json(
                {
                    **load_json(MONITOR_STATUS_PATH, {}),
                    "history": load_json(HISTORY_META_PATH, {}),
                    "localhost": load_json(LOCALHOST_STATE_PATH, {}),
                    "server": {
                        "host": HOST,
                        "port": PORT,
                        "pid": os.getpid(),
                        "started_at": getattr(self.server, "started_at", ""),
                    },
                }
            )
        elif path == "/api/audit":
            self.send_json(
                {
                    "meta": read_json_file(DATA_DIR / "audit_meta.json", {}),
                    "exclusions_csv": "/data/exclusiones_auditoria.csv",
                    "report": "/data/INFORME_AUDITORIA.md",
                }
            )
        elif path == "/api/workspace":
            workspace = load_workspace()
            progress_by_id = read_json_file(DATA_DIR / "progress.json", {})
            dismissed = set(workspace.get("dismissed_suggestions", []))
            suggestions = [
                suggestion
                for row in load_catalog()
                for suggestion in project_suggestions(
                    row,
                    progress_by_id.get(row.get("id", ""), {}),
                    dismissed,
                )
            ]
            self.send_json(
                {
                    **workspace,
                    "suggestions": suggestions,
                    "settings": load_settings(),
                    "project_overrides": load_overrides().get("projects", {}),
                }
            )
        elif path == "/api/settings":
            self.send_json({"settings": load_settings()})
        elif re.fullmatch(r"/api/projects/[^/]+", path):
            try:
                self.send_json(project_payload(unquote(path.rsplit("/", 1)[-1])))
            except Exception as error:  # noqa: BLE001
                self.send_api_error(error)
        else:
            self.send_json({"error": "Endpoint no encontrado."}, HTTPStatus.NOT_FOUND)

    def serve_static(self, request_path: str) -> None:
        relative = unquote(request_path).lstrip("/") or "index.html"
        candidate = (WORKSPACE / relative).resolve()
        try:
            candidate.relative_to(WORKSPACE.resolve())
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if candidate.is_dir():
            candidate = candidate / "index.html"
        if not candidate.exists() or not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        mime, _ = mimetypes.guess_type(candidate.name)
        body = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Servidor y monitor local del dashboard UNOVA.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--no-monitor", action="store_true")
    parser.add_argument("--scan-once", action="store_true")
    args = parser.parse_args()
    configure_logging()
    ensure_personal_files()
    if args.scan_once:
        perform_scan("scheduled_task")
        return 0

    server = ThreadingHTTPServer((args.host, args.port), UnovaHandler)
    server.started_at = now_iso()  # type: ignore[attr-defined]
    monitor_status(
        state="starting",
        server={"host": args.host, "port": args.port, "pid": os.getpid()},
        started_at=server.started_at,  # type: ignore[attr-defined]
        last_error="",
    )
    if not args.no_monitor:
        threading.Thread(
            target=monitor_loop,
            name="unova-monitor",
            daemon=True,
        ).start()
    monitor_status(state="idle")
    logging.info("Dashboard UNOVA disponible en http://%s:%s", args.host, args.port)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        server.server_close()
        monitor_status(state="stopped", stopped_at=now_iso())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
