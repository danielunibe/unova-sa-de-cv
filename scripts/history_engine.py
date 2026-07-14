from __future__ import annotations

import csv
import json
import os
import re
import sys
import uuid
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from audit_projects import (
    ASSET_EXTENSIONS,
    CODE_EXTENSIONS,
    CSV_FIELDS,
    DATA_DIR,
    DOC_EXTENSIONS,
    MANIFEST_NAMES,
    SKIP_EXACT,
    SKIP_PREFIXES,
    WORKSPACE,
    clean_field,
    read_document_text,
    write_csv,
)


HISTORY_DIR = WORKSPACE / "history"
EVENTS_DIR = HISTORY_DIR / "events"
STATE_DIR = HISTORY_DIR / "project_state"
DAILY_DIR = HISTORY_DIR / "daily"
MONITOR_STATUS_PATH = HISTORY_DIR / "monitor_status.json"
HISTORY_META_PATH = HISTORY_DIR / "history_meta.json"
LOCALHOST_STATE_PATH = HISTORY_DIR / "localhost_state.json"
STATUS_FILENAME = "UNOVA_PROJECT_STATUS.md"
BACKFILL_DAYS = 180

HISTORY_FIELDS = [
    "timestamp",
    "project_id",
    "project",
    "event_type",
    "reason",
    "precision",
    "added",
    "modified",
    "deleted",
    "sample_files",
]

CHECKBOX_RE = re.compile(r"(?im)^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$")
NEXT_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:pr[oó]ximo paso|siguiente paso|next step)"
    r"\s*[:\-]?\s*(.*)$"
)
ADVANCE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:[uú]ltimo avance|avance reciente|completado|"
    r"implementado|finalizado|hecho|done)\s*[:\-]\s*(.+?)\s*$"
)
BLOCKER_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:bloqueo|bloqueador|blocker|impedimento)"
    r"\s*[:\-]\s*(.+?)\s*$"
)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_dirs() -> None:
    for path in (HISTORY_DIR, EVENTS_DIR, STATE_DIR, DAILY_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2))


def load_catalog() -> list[dict[str, str]]:
    with (DATA_DIR / "proyectos.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    localhost_state = load_json(LOCALHOST_STATE_PATH, {})
    active_ids = {
        item.get("project_id", "")
        for item in localhost_state.get("listeners", [])
        if item.get("project_id")
    }
    for row in rows:
        row["localhost_activo"] = "sí" if row.get("id") in active_ids else "no"
    return rows


def normalize_fields(rows: list[dict[str, str]]) -> list[str]:
    fields = list(CSV_FIELDS)
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    return fields


def split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(";") if item.strip()]


def should_skip_dir(name: str) -> bool:
    lower = name.lower()
    return lower in SKIP_EXACT or lower.startswith(SKIP_PREFIXES)


def relevant_file(path: Path) -> bool:
    if path.name == STATUS_FILENAME:
        return False
    lower = path.name.lower()
    if lower.endswith((".tmp", ".lock", ".log", ".pyc")):
        return False
    return True


def build_snapshot(root: Path) -> tuple[dict[str, list[int]], dict[str, Any]]:
    files: dict[str, list[int]] = {}
    summary: dict[str, Any] = {
        "connected": root.exists(),
        "file_count": 0,
        "code_count": 0,
        "doc_count": 0,
        "asset_count": 0,
        "test_count": 0,
        "manifest_count": 0,
        "latest_mtime": "",
        "latest_file": "",
        "extensions": {},
    }
    if not root.exists():
        return files, summary

    latest_ns = 0
    extension_counts: Counter[str] = Counter()
    for current, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda _error: None):
        dirnames[:] = [name for name in dirnames if not should_skip_dir(name)]
        current_path = Path(current)
        for filename in filenames:
            path = current_path / filename
            if not relevant_file(path):
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            relative = str(path.relative_to(root)).replace("\\", "/")
            files[relative] = [stat.st_size, stat.st_mtime_ns]
            suffix = path.suffix.lower()
            extension_counts[suffix or "[sin extensión]"] += 1
            summary["file_count"] += 1
            if suffix in CODE_EXTENSIONS:
                summary["code_count"] += 1
            if suffix in DOC_EXTENSIONS:
                summary["doc_count"] += 1
            if suffix in ASSET_EXTENSIONS:
                summary["asset_count"] += 1
            if "test" in relative.lower() or "spec" in filename.lower():
                summary["test_count"] += 1
            if filename.lower() in MANIFEST_NAMES or suffix in {".sln", ".csproj"}:
                summary["manifest_count"] += 1
            if stat.st_mtime_ns > latest_ns:
                latest_ns = stat.st_mtime_ns
                summary["latest_file"] = relative

    summary["extensions"] = dict(extension_counts.most_common(20))
    if latest_ns:
        summary["latest_mtime"] = datetime.fromtimestamp(
            latest_ns / 1_000_000_000
        ).astimezone().isoformat(timespec="seconds")
    return files, summary


def compare_snapshots(
    previous: dict[str, list[int]], current: dict[str, list[int]]
) -> dict[str, list[str]]:
    previous_names = set(previous)
    current_names = set(current)
    added = sorted(current_names - previous_names)
    deleted = sorted(previous_names - current_names)
    modified = sorted(
        name
        for name in previous_names & current_names
        if previous[name] != current[name]
    )
    return {"added": added, "modified": modified, "deleted": deleted}


def event_path(timestamp: datetime) -> Path:
    return EVENTS_DIR / f"{timestamp:%Y-%m}.jsonl"


def append_event(event: dict[str, Any]) -> None:
    ensure_dirs()
    timestamp = datetime.fromisoformat(event["timestamp"])
    with event_path(timestamp).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    daily_path = DAILY_DIR / f"{timestamp:%Y-%m-%d}.csv"
    exists = daily_path.exists()
    with daily_path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_FIELDS, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        row = dict(event)
        row["sample_files"] = "; ".join(event.get("sample_files", []))
        writer.writerow(row)


def make_event(
    row: dict[str, str],
    event_type: str,
    reason: str,
    precision: str,
    timestamp: datetime | None = None,
    changes: dict[str, list[str]] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    changes = changes or {"added": [], "modified": [], "deleted": []}
    samples = (
        changes.get("added", [])[:4]
        + changes.get("modified", [])[:4]
        + changes.get("deleted", [])[:4]
    )[:10]
    return {
        "id": uuid.uuid4().hex,
        "timestamp": (timestamp or datetime.now().astimezone()).isoformat(timespec="seconds"),
        "project_id": row.get("id", ""),
        "project": row.get("proyecto", ""),
        "event_type": event_type,
        "reason": reason,
        "precision": precision,
        "added": len(changes.get("added", [])),
        "modified": len(changes.get("modified", [])),
        "deleted": len(changes.get("deleted", [])),
        "sample_files": samples,
        "root": row.get("ruta_vigente", ""),
        "details": details or {},
    }


def load_events(limit: int = 1000) -> list[dict[str, Any]]:
    ensure_dirs()
    events: list[dict[str, Any]] = []
    for path in sorted(EVENTS_DIR.glob("*.jsonl"), reverse=True):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(events) >= limit:
                return sorted(events, key=lambda item: item.get("timestamp", ""), reverse=True)
    return sorted(events, key=lambda item: item.get("timestamp", ""), reverse=True)


def collect_doc_paths(row: dict[str, str], root: Path) -> list[Path]:
    candidates: list[Path] = []
    for value in split_semicolon(row.get("documentos_principales", "")):
        path = Path(value)
        if path.exists() and path.suffix.lower() in {".md", ".txt", ".rst", ".docx"}:
            candidates.append(path)
    if root.exists():
        for pattern in (
            "*README*.md",
            "*ROADMAP*.md",
            "*PLAN*.md",
            "*STATUS*.md",
            "*PRD*.md",
            "*PROTOCOL*.md",
            "*ARQUITECT*.md",
        ):
            try:
                for path in root.glob(pattern):
                    if path.name != STATUS_FILENAME:
                        candidates.append(path)
            except OSError:
                continue
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique[:16]


def extract_continuity(
    row: dict[str, str], docs: list[Path], snapshot_summary: dict[str, Any]
) -> dict[str, str]:
    checked: list[str] = []
    pending: list[str] = []
    advances: list[tuple[float, str]] = []
    explicit_next: list[str] = []
    blockers: list[str] = []
    stale: list[str] = []
    latest_project = snapshot_summary.get("latest_mtime", "")
    latest_project_dt = (
        datetime.fromisoformat(latest_project) if latest_project else None
    )

    for path in docs:
        text = read_document_text(path, 160_000)
        if not text:
            continue
        for mark, item in CHECKBOX_RE.findall(text):
            cleaned = clean_field(item)
            if mark.strip().lower() == "x":
                checked.append(cleaned)
            else:
                pending.append(cleaned)
        for match in ADVANCE_RE.finditer(text):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                mtime = 0
            advances.append((mtime, clean_field(match.group(1))))
        for match in NEXT_RE.finditer(text):
            inline = clean_field(match.group(1))
            if inline:
                explicit_next.append(inline)
        blockers.extend(clean_field(match.group(1)) for match in BLOCKER_RE.finditer(text))

        if latest_project_dt:
            try:
                doc_dt = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
            except OSError:
                continue
            if latest_project_dt - doc_dt > timedelta(days=60):
                stale.append(path.name)

    checked = list(dict.fromkeys(item for item in checked if item))
    pending = list(dict.fromkeys(item for item in pending if item))
    blockers = list(dict.fromkeys(item for item in blockers if item))
    explicit_next = list(dict.fromkeys(item for item in explicit_next if item))
    advances.sort(key=lambda item: item[0], reverse=True)

    latest_advance = advances[0][1] if advances else ""
    if not latest_advance and checked:
        latest_advance = checked[-1]
    next_step = explicit_next[0] if explicit_next else (pending[0] if pending else "")
    total_checklist = len(checked) + len(pending)
    vision_progress = (
        str(round(len(checked) * 100 / total_checklist))
        if total_checklist >= 3
        else "N/D"
    )
    return {
        "ultimo_avance_documentado": latest_advance or "No documentado",
        "pendientes_documentados": "; ".join(pending[:10]) or "No documentado",
        "proximo_paso": next_step or "No documentado",
        "bloqueos_documentados": "; ".join(blockers[:6]) or "No documentado",
        "progreso_vision": vision_progress,
        "documentos_desactualizados": "; ".join(list(dict.fromkeys(stale))[:8])
        or "Ninguno detectado",
        "checked_count": str(len(checked)),
        "pending_count": str(len(pending)),
    }


def score_progress(
    row: dict[str, str],
    summary: dict[str, Any],
    docs: list[Path],
    continuity: dict[str, str],
) -> dict[str, Any]:
    doc_names = " ".join(path.name.lower() for path in docs)
    extensions = summary.get("extensions", {})
    code_count = int(summary.get("code_count", 0))
    test_count = int(summary.get("test_count", 0))
    manifest_count = int(summary.get("manifest_count", 0))
    asset_count = int(summary.get("asset_count", 0))

    definition = 0
    definition += 5 if row.get("proposito") or row.get("resumen") else 0
    definition += 5 if row.get("problema_que_resuelve") else 0
    definition += 5 if row.get("publico_objetivo") else 0

    design = 0
    if re.search(r"design|dise[nñ]o|ui|ux|visual", doc_names):
        design += 6
    if asset_count >= 3:
        design += 4
    design = min(design, 10)

    architecture = 0
    if re.search(r"architecture|arquitect|tdd|tech.stack", doc_names):
        architecture += 5
    if manifest_count:
        architecture += 5
    architecture = min(architecture, 10)

    if code_count == 0:
        implementation = 0
    elif code_count < 5:
        implementation = 8
    elif code_count < 20:
        implementation = 15
    elif code_count < 100:
        implementation = 22
    else:
        implementation = 30

    if test_count == 0:
        tests = 0
    elif test_count < 5:
        tests = 6
    elif test_count < 20:
        tests = 10
    else:
        tests = 15

    packaging = 0
    manifest_names = " ".join(extensions.keys()) + " " + doc_names
    if manifest_count:
        packaging += 3
    if re.search(r"tauri|capacitor|android|xcode|electron|\\.sln|installer|package", manifest_names):
        packaging += 5
    if re.search(r"release|deploy|distribution|dist-apk|publicaci", doc_names):
        packaging += 2
    packaging = min(packaging, 10)

    continuity_score = 0
    if re.search(r"readme|roadmap|plan|status|changelog|protocol", doc_names):
        continuity_score += 3
    if continuity.get("proximo_paso") != "No documentado":
        continuity_score += 2
    continuity_score = min(continuity_score, 5)

    validation = 0
    if test_count:
        validation += 3
    if re.search(r"qa|test.plan|validation|smoke|acceptance", doc_names):
        validation += 2
    validation = min(validation, 5)

    breakdown = {
        "definicion": definition,
        "diseno": design,
        "arquitectura": architecture,
        "implementacion": implementation,
        "pruebas": tests,
        "empaquetado": packaging,
        "continuidad": continuity_score,
        "validacion": validation,
    }
    total = sum(breakdown.values())
    evidence_axes = sum(1 for value in breakdown.values() if value > 0)
    if evidence_axes >= 6 and summary.get("doc_count", 0) >= 3:
        confidence = "Alta"
    elif evidence_axes >= 3:
        confidence = "Media"
    else:
        confidence = "Baja"

    missing_labels = {
        "definicion": "definición completa",
        "diseno": "diseño documentado",
        "arquitectura": "arquitectura verificable",
        "implementacion": "implementación",
        "pruebas": "pruebas",
        "empaquetado": "empaquetado/distribución",
        "continuidad": "próximo paso documentado",
        "validacion": "validación",
    }
    missing = [
        missing_labels[key]
        for key, value in breakdown.items()
        if value == 0
    ]
    return {
        "mvp": total,
        "confidence": confidence,
        "breakdown": breakdown,
        "missing": missing,
    }


def estimated_backfill(
    row: dict[str, str],
    files: dict[str, list[int]],
    cutoff: datetime,
    known_days: set[tuple[str, str]] | None = None,
) -> int:
    known_days = known_days if known_days is not None else set()
    by_day: dict[date, list[tuple[str, datetime]]] = defaultdict(list)
    for relative, (_size, mtime_ns) in files.items():
        timestamp = datetime.fromtimestamp(mtime_ns / 1_000_000_000).astimezone()
        if timestamp >= cutoff:
            by_day[timestamp.date()].append((relative, timestamp))
    created = 0
    for event_day, entries in sorted(by_day.items()):
        key = (row.get("id", ""), event_day.isoformat())
        if key in known_days:
            continue
        event_time = max(timestamp for _name, timestamp in entries)
        names = sorted(name for name, _timestamp in entries)
        changes = {"added": [], "modified": names, "deleted": []}
        event = make_event(
            row,
            event_type="historical_activity",
            reason="initial_backfill",
            precision="estimated",
            timestamp=event_time,
            changes=changes,
            details={"note": "Reconstruido desde fechas de modificación; no representa un diff exacto."},
        )
        append_event(event)
        known_days.add(key)
        created += 1
    return created


def status_markdown(
    row: dict[str, str],
    summary: dict[str, Any],
    continuity: dict[str, str],
    progress: dict[str, Any],
) -> str:
    breakdown = progress["breakdown"]
    lines = [
        "# UNOVA_PROJECT_STATUS.md",
        "",
        "> Ficha automática. Se regenera desde evidencia del proyecto y el historial central UNOVA.",
        "",
        f"- Proyecto: {row.get('proyecto') or 'No documentado'}",
        f"- Identificador: `{row.get('id') or ''}`",
        f"- Grupo operativo: {row.get('grupo_operativo') or 'No documentado'}",
        f"- Última generación: {now_iso()}",
        f"- Ruta canónica: `{row.get('ruta_vigente') or ''}`",
        "",
        "## Propósito y estado",
        "",
        row.get("proposito") or row.get("resumen") or "No documentado",
        "",
        f"- Estado documentado: {row.get('estado') or 'No documentado'}",
        f"- Evidencia técnica: {row.get('estado_tecnico_detectado') or 'No documentado'}",
        f"- Decisión de producto: {row.get('decision_producto') or 'No documentado'}",
        "",
        "## Continuidad",
        "",
        f"- Último movimiento detectado: {row.get('ultimo_cambio') or 'No documentado'}",
        f"- Último avance documentado: {continuity['ultimo_avance_documentado']}",
        f"- Pendientes documentados: {continuity['pendientes_documentados']}",
        f"- Próximo paso: {continuity['proximo_paso']}",
        f"- Bloqueos documentados: {continuity['bloqueos_documentados']}",
        "",
        "## Progreso estimado",
        "",
        f"- MVP verificable: {progress['mvp']}%",
        f"- Visión completa: {continuity['progreso_vision']}{'%' if continuity['progreso_vision'].isdigit() else ''}",
        f"- Confianza de la estimación: {progress['confidence']}",
        "",
        "| Eje | Puntos | Máximo |",
        "|---|---:|---:|",
        f"| Definición | {breakdown['definicion']} | 15 |",
        f"| Diseño | {breakdown['diseno']} | 10 |",
        f"| Arquitectura | {breakdown['arquitectura']} | 10 |",
        f"| Implementación | {breakdown['implementacion']} | 30 |",
        f"| Pruebas | {breakdown['pruebas']} | 15 |",
        f"| Empaquetado | {breakdown['empaquetado']} | 10 |",
        f"| Continuidad documental | {breakdown['continuidad']} | 5 |",
        f"| Validación | {breakdown['validacion']} | 5 |",
        "",
        "## Evidencia",
        "",
        f"- Archivos relevantes: {summary.get('file_count', 0)}",
        f"- Archivos de código: {summary.get('code_count', 0)}",
        f"- Documentos: {summary.get('doc_count', 0)}",
        f"- Pruebas detectadas: {summary.get('test_count', 0)}",
        f"- Último archivo modificado: `{summary.get('latest_file') or 'No documentado'}`",
        f"- Evidencia faltante: {'; '.join(progress['missing']) or 'Ninguna crítica detectada'}",
        f"- Documentos posiblemente desactualizados: {continuity['documentos_desactualizados']}",
        "",
        "## Fuente central",
        "",
        f"- Historial: `{HISTORY_DIR}`",
        f"- Catálogo: `{DATA_DIR / 'proyectos.csv'}`",
        "",
    ]
    return "\n".join(lines)


def write_project_status_file(
    row: dict[str, str],
    summary: dict[str, Any],
    continuity: dict[str, str],
    progress: dict[str, Any],
) -> tuple[bool, str]:
    root = Path(row.get("ruta_vigente", ""))
    if not root.exists():
        return False, "Ruta desconectada"
    try:
        atomic_write_text(root / STATUS_FILENAME, status_markdown(row, summary, continuity, progress))
        return True, ""
    except OSError as error:
        return False, str(error)


def enrich_and_track(
    reason: str,
    project_ids: Iterable[str] | None,
    create_backfill: bool,
    write_project_status: bool,
) -> dict[str, Any]:
    ensure_dirs()
    rows = load_catalog()
    selected_ids = set(project_ids or [])
    selected = [row for row in rows if not selected_ids or row.get("id") in selected_ids]
    history_meta = load_json(HISTORY_META_PATH, {})
    baseline_exists = bool(history_meta.get("baseline_complete"))
    cutoff = datetime.now().astimezone() - timedelta(days=BACKFILL_DAYS)
    changes_logged = 0
    backfill_events = 0
    status_written = 0
    errors: list[dict[str, str]] = []
    disconnected: list[str] = []
    progress_payload: dict[str, Any] = load_json(DATA_DIR / "progress.json", {})
    known_backfill_days = {
        (event.get("project_id", ""), str(event.get("timestamp", ""))[:10])
        for event in load_events(limit=100_000)
        if event.get("event_type") == "historical_activity"
        and event.get("reason") == "initial_backfill"
    }

    for row in selected:
        project_id = row.get("id", "")
        root = Path(row.get("ruta_vigente", ""))
        state_path = STATE_DIR / f"{project_id}.json"
        previous_state = load_json(state_path, {})
        previous_files = {
            name: signature
            for name, signature in previous_state.get("files", {}).items()
            if Path(name).name != STATUS_FILENAME
            and not any(should_skip_dir(part) for part in Path(name).parts)
        }
        current_files, summary = build_snapshot(root)

        if not summary["connected"]:
            disconnected.append(project_id)
            continue

        docs = collect_doc_paths(row, root)
        continuity = extract_continuity(row, docs, summary)
        progress = score_progress(row, summary, docs, continuity)
        progress_payload[project_id] = {
            "project_id": project_id,
            "project": row.get("proyecto", ""),
            "mvp": progress["mvp"],
            "vision": continuity["progreso_vision"],
            "confidence": progress["confidence"],
            "breakdown": progress["breakdown"],
            "missing": progress["missing"],
        }

        changes = compare_snapshots(previous_files, current_files) if previous_files else {
            "added": [],
            "modified": [],
            "deleted": [],
        }
        has_changes = any(changes.values())
        if previous_files and has_changes:
            event = make_event(
                row,
                event_type="file_change",
                reason=reason,
                precision="exact",
                changes=changes,
                details={"latest_file": summary.get("latest_file", "")},
            )
            append_event(event)
            changes_logged += 1
            row["ultimo_cambio"] = event["timestamp"]
        elif previous_state.get("last_change"):
            row["ultimo_cambio"] = str(previous_state["last_change"])
        elif summary.get("latest_mtime"):
            row["ultimo_cambio"] = str(summary["latest_mtime"])

        if create_backfill and not baseline_exists and current_files:
            backfill_events += estimated_backfill(
                row,
                current_files,
                cutoff,
                known_backfill_days,
            )

        row["grupo_operativo"] = (
            "iniciado" if int(summary.get("code_count", 0)) > 0 else "no_iniciado"
        )
        row["ultimo_avance_documentado"] = continuity["ultimo_avance_documentado"]
        row["pendientes_documentados"] = continuity["pendientes_documentados"]
        row["proximo_paso"] = continuity["proximo_paso"]
        row["bloqueos_documentados"] = continuity["bloqueos_documentados"]
        row["progreso_mvp"] = str(progress["mvp"])
        row["progreso_vision"] = continuity["progreso_vision"]
        row["confianza_progreso"] = progress["confidence"]
        row["evidencia_faltante"] = "; ".join(progress["missing"]) or "Ninguna crítica detectada"
        row["documentos_desactualizados"] = continuity["documentos_desactualizados"]

        current_state = {
            "project_id": project_id,
            "project": row.get("proyecto", ""),
            "root": str(root),
            "captured_at": now_iso(),
            "last_change": row.get("ultimo_cambio", ""),
            "summary": summary,
            "progress": progress_payload[project_id],
            "continuity": continuity,
            "files": current_files,
        }
        atomic_write_json(state_path, current_state)

        if write_project_status:
            written, error = write_project_status_file(row, summary, continuity, progress)
            if written:
                status_written += 1
            else:
                errors.append({"project_id": project_id, "error": error})

    # Conservar enriquecimiento previo de proyectos no incluidos en un escaneo focalizado.
    if selected_ids:
        existing_by_id = {item["id"]: item for item in load_catalog()}
        for row in rows:
            if row.get("id") not in selected_ids and row.get("id") in existing_by_id:
                row.update(existing_by_id[row["id"]])

    write_csv(DATA_DIR / "proyectos.csv", normalize_fields(rows), rows)
    atomic_write_json(DATA_DIR / "progress.json", progress_payload)

    if not baseline_exists:
        history_meta.update(
            {
                "baseline_complete": True,
                "baseline_at": now_iso(),
                "backfill_days": BACKFILL_DAYS,
                "backfill_precision": "estimated",
            }
        )
    history_meta["last_scan_at"] = now_iso()
    history_meta["last_scan_reason"] = reason
    history_meta["last_global_scan_date"] = (
        date.today().isoformat() if not selected_ids else history_meta.get("last_global_scan_date", "")
    )
    atomic_write_json(HISTORY_META_PATH, history_meta)

    result = {
        "scanned_projects": len(selected),
        "changes_logged": changes_logged,
        "backfill_events": backfill_events,
        "status_files_written": status_written,
        "disconnected_projects": disconnected,
        "errors": errors,
        "completed_at": now_iso(),
        "reason": reason,
    }
    atomic_write_json(
        MONITOR_STATUS_PATH,
        {
            **load_json(MONITOR_STATUS_PATH, {}),
            "last_scan": result,
            "state": "idle",
            "updated_at": now_iso(),
        },
    )
    return result


def update_localhost_flags(active_project_ids: set[str]) -> None:
    # El estado localhost vive en history/localhost_state.json y se fusiona al leer
    # el catálogo. Así el monitor no reescribe continuamente la fuente CSV.
    return None


def catalog_stats() -> dict[str, Any]:
    rows = load_catalog()
    now = datetime.now().astimezone()
    started = [row for row in rows if row.get("grupo_operativo") == "iniciado"]
    unstarted = [row for row in rows if row.get("grupo_operativo") == "no_iniciado"]
    recent = []
    progress_values = []
    category_counts: Counter[str] = Counter()
    technical_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    localhost_active = []
    for row in rows:
        category_counts[row.get("categoria", "Sin categoría")] += 1
        technical_counts[row.get("estado_tecnico_detectado", "Sin clasificar")] += 1
        decision_counts[row.get("decision_producto") or "Sin decisión"] += 1
        if row.get("localhost_activo") == "sí":
            localhost_active.append(row.get("id", ""))
        try:
            progress_values.append(int(row.get("progreso_mvp", "")))
        except ValueError:
            pass
        latest = row.get("ultimo_cambio") or row.get("ultima_actividad")
        if latest:
            try:
                latest_dt = datetime.fromisoformat(latest)
                if latest_dt.tzinfo is None:
                    latest_dt = latest_dt.astimezone()
                if now - latest_dt <= timedelta(days=30):
                    recent.append(row.get("id", ""))
            except ValueError:
                pass
    return {
        "generated_at": now_iso(),
        "total": len(rows),
        "started": len(started),
        "unstarted": len(unstarted),
        "recent_30_days": len(recent),
        "average_mvp_progress": round(sum(progress_values) / len(progress_values)) if progress_values else 0,
        "localhost_active": len(localhost_active),
        "localhost_project_ids": localhost_active,
        "categories": dict(category_counts.most_common()),
        "technical_states": dict(technical_counts.most_common()),
        "decisions": dict(decision_counts.most_common()),
        "documentation_coverage": {
            "with_documentation": sum(row.get("tiene_documentacion") == "sí" for row in rows),
            "with_next_step": sum(row.get("proximo_paso") not in {"", "No documentado"} for row in rows),
            "with_vision_progress": sum(row.get("progreso_vision") not in {"", "N/D"} for row in rows),
            "high_progress_confidence": sum(row.get("confianza_progreso") == "Alta" for row in rows),
        },
    }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    result = enrich_and_track(
        reason="direct",
        project_ids=None,
        create_backfill=True,
        write_project_status=True,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
