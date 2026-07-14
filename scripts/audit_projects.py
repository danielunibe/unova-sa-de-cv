from __future__ import annotations

import csv
import json
import os
import re
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree

from safe_storage import atomic_write_csv, file_lock

VOYAGER_ROOT = Path(r"G:\Otros ordenadores\AorusPC\Voyager 2026\Proyectos personales 2026\proyectos voyager")
DEV_ROOT = Path(r"C:\Desarrollos DEV daniel")
WORKSPACE = Path(__file__).resolve().parents[1]
DATA_DIR = WORKSPACE / "data"

CATEGORY_MAP = {
    "01_software": ("Software", "Software de escritorio"),
    "02_App IOS y android": ("Apps móviles", "Aplicación móvil"),
    "04_Musica composicion": ("Música y composición", "Proyecto musical"),
    "05_videojuegos": ("Videojuegos", "Videojuego"),
    "06_Juegos de mesa": ("Juegos de mesa", "Juego de mesa"),
    "08_Gastronomia": ("Gastronomía", "Producto gastronómico"),
    "09_extensiones google chrome": ("Extensiones Chrome", "Extensión de navegador"),
    "10_Ebooks": ("Ebooks", "Publicación digital"),
}

DEV_EXCLUDED = {
    "desarrollo cv borderlands3": "Contenido de CV y portafolio personal fuera del catálogo de producto.",
    "plan de financiamiento": "Información financiera y de terceros fuera del catálogo público.",
    "tmp": "Artefactos temporales y respaldos técnicos.",
    "todos documentos": "Repositorio documental transversal, no producto independiente.",
    "unova sa de cv": "Carpeta de salida de este catálogo.",
}

DEV_OVERRIDES = {
    "21_pixvoxia": ("Pixvoxia", "Apps móviles", "Editor creativo"),
    "app vivo": ("Vivo Promotor", "Apps móviles", "Aplicación móvil comercial"),
    "desarrollo web unova games studio": ("Unova Games Studio", "Videojuegos", "Sitio y dossier de estudio"),
    "ethyria": ("Ethyria", "Software", "IA personal"),
    "ethyria-app": ("Ethyria", "Software", "IA personal"),
    "julia": ("Julia", "Software", "Sistema de conocimiento"),
    "master dev click switch swiss": ("Switch Click Swiss", "Software", "Utilidad de sistema"),
    "nodia": ("Nodia", "Software", "Herramienta visual"),
    "nodia-home-clone": ("Nodia", "Software", "Herramienta visual"),
    "nueva propuesta windows 12": ("Windows A", "Software", "Interfaz de sistema"),
    "pulsar-project": ("Pulsar TikTok", "Software", "Inteligencia de contenido"),
    "reactbite": ("React Bite", "Software", "Runtime de microaplicaciones"),
    "retriver": ("Retriver", "Software", "Conocimiento y recuperación"),
    "transparentimagen": ("Asteria", "Software", "Procesamiento de imagen"),
    "tsk diseno": ("Proyectia", "Software", "Gestión y productividad"),
}

ALIASES = {
    "faast slap faast": "faast",
    "slap faast": "faast",
    "slapfaast": "faast",
    "switch click swiss": "switch click swiss",
    "master dev click switch swiss": "switch click swiss",
    "pulsar tiktok eventide": "pulsar tiktok",
    "pulsar project": "pulsar tiktok",
    "reactbite": "react bite",
    "react bite": "react bite",
    "proyectia tsk": "proyectia",
    "proyectia main tsk": "proyectia",
    "windows a voyager": "windows a",
    "windows a": "windows a",
    "nueva propuesta windows 12": "windows a",
    "dragon alebrije": "dragon alebrije",
    "dragón alebrije": "dragon alebrije",
    "neko nesushi": "neko nesushi",
    "juego ingles con ia": "app juego ingles con ia",
    "app juego ingles ia": "app juego ingles con ia",
    "app juego ingles con ia": "app juego ingles con ia",
    "aparment": "aparment",
    "apartment": "aparment",
    "apartament": "aparment",
    "visual ia suite": "visual ia suite",
    "voyager files the perfect explorer": "voyager files",
    "ethyria ia evolutiva": "ethyria",
    "julia solar system memory": "julia",
    "pixvoxia canvas pro": "pixvoxia",
    "coraline pink palace": "coraline",
}

SKIP_EXACT = {
    ".git", ".svn", ".hg", ".next", ".cache", ".turbo", ".idea",
    "node_modules", "dist", "build", "out", "target", "target-tauri",
    "coverage", "venv", ".venv", "__pycache__", "bin", "obj", "vendor",
    "test-results", "playwright-report", "blob-report", "test-output",
    "external", "integrations", "archivo_personal_y_legacy", "boveda_legacy",
    "relacion analisis", "backup dms", "mysoul_backups", "asset-backups",
}

SKIP_PREFIXES = (
    "node_modules_", "_codex_backup", "backup_", "backup-", "snapshot_",
    "mysoul_snapshot_", "target-",
)

CODE_EXTENSIONS = {
    ".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript",
    ".jsx": "JavaScript", ".py": "Python", ".rs": "Rust", ".cs": "C#",
    ".cpp": "C++", ".cc": "C++", ".c": "C", ".h": "C/C++",
    ".swift": "Swift", ".kt": "Kotlin", ".kts": "Kotlin", ".java": "Java",
    ".dart": "Dart", ".go": "Go", ".vue": "Vue", ".svelte": "Svelte",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".ps1": "PowerShell",
}

DOC_EXTENSIONS = {".md", ".txt", ".rst", ".pdf", ".docx", ".doc"}
ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".mp4", ".mov", ".obj", ".fbx", ".blend", ".max", ".ai", ".psd", ".wav", ".mp3"}
MANIFEST_NAMES = {
    "package.json", "cargo.toml", "pyproject.toml", "requirements.txt",
    "requirements-dev.txt", "vite.config.ts", "vite.config.js", "next.config.ts",
    "next.config.js", "tauri.conf.json", "capacitor.config.ts", "pubspec.yaml",
    "androidmanifest.xml", "build.gradle", "build.gradle.kts", "podfile",
}
GENERATED_STATUS_FILENAME = "UNOVA_PROJECT_STATUS.md"

TECH_DEPENDENCIES = {
    "react": "React", "react-dom": "React", "typescript": "TypeScript",
    "vite": "Vite", "next": "Next.js", "vue": "Vue", "svelte": "Svelte",
    "electron": "Electron", "@tauri-apps/api": "Tauri", "@tauri-apps/cli": "Tauri",
    "@capacitor/core": "Capacitor", "@capacitor/android": "Android",
    "@capacitor/ios": "iOS", "tailwindcss": "Tailwind CSS", "three": "Three.js",
    "@react-three/fiber": "React Three Fiber", "zustand": "Zustand",
    "@supabase/supabase-js": "Supabase", "firebase": "Firebase",
    "better-sqlite3": "SQLite", "@google/genai": "Gemini API",
    "@google/generative-ai": "Gemini API", "openai": "OpenAI API",
    "framer-motion": "Framer Motion", "gsap": "GSAP", "expo": "Expo",
    "react-native": "React Native", "fastapi": "FastAPI", "langchain": "LangChain",
    "ollama": "Ollama", "gradio": "Gradio", "pytest": "Pytest",
    "vitest": "Vitest", "playwright": "Playwright",
}

CSV_FIELDS = [
    "id", "proyecto", "categoria", "subcategoria", "tipo", "proposito", "resumen",
    "problema_que_resuelve", "publico_objetivo", "estado", "madurez_documentada",
    "estado_tecnico_detectado", "decision_producto", "modelo_negocio",
    "score_desarrollo", "score_rentabilidad", "score_total", "caracteristicas",
    "diferenciadores", "diagnostico", "stack", "lenguajes", "frameworks",
    "plataformas", "apis_integraciones", "persistencia", "tiene_codigo",
    "tiene_documentacion", "tiene_tests", "tiene_git", "archivos_relevantes",
    "tamano_relevante_mb", "documentos_principales", "ruta_vigente",
    "ruta_fuente_documental", "ubicacion", "ultima_actividad", "copias_detectadas",
    "confianza", "fuente_descripcion", "notas_auditoria", "grupo_operativo",
    "ultimo_cambio", "ultimo_avance_documentado", "pendientes_documentados",
    "proximo_paso", "bloqueos_documentados", "progreso_mvp", "progreso_vision",
    "confianza_progreso", "evidencia_faltante", "documentos_desactualizados",
    "localhost_activo",
]
ENRICHED_FIELDS = (
    "grupo_operativo",
    "ultimo_cambio",
    "ultimo_avance_documentado",
    "pendientes_documentados",
    "proximo_paso",
    "bloqueos_documentados",
    "progreso_mvp",
    "progreso_vision",
    "confianza_progreso",
    "evidencia_faltante",
    "documentos_desactualizados",
    "localhost_activo",
)


def repair_mojibake(value: str) -> str:
    if any(token in value for token in ("Ã", "Â", "â€", "ðŸ")):
        try:
            return value.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value
    return value


def strip_markdown(value: str) -> str:
    value = repair_mojibake(value)
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", value)
    value = re.sub(r"[*_>#]", "", value)
    value = re.sub(r"\s+", " ", value).strip(" -|\t\r\n")
    return value


def display_name(folder_name: str) -> str:
    value = repair_mojibake(folder_name)
    value = re.sub(r"^\d+[\s_.-]*", "", value)
    value = value.replace("_", " ").strip()
    value = re.sub(r"\s+", " ", value)
    return value


def simple_key(value: str) -> str:
    value = strip_markdown(value)
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"^\d+[\s_.-]*", "", value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower().replace("_", " ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return ALIASES.get(value, value)


def should_skip_dir(name: str) -> bool:
    lower = name.lower()
    return lower in SKIP_EXACT or lower.startswith(SKIP_PREFIXES)


def read_text(path: Path, max_chars: int = 180_000) -> str:
    try:
        raw = path.read_bytes()[: max_chars * 4]
    except OSError:
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return repair_mojibake(raw.decode(encoding))[:max_chars]
        except UnicodeDecodeError:
            continue
    return ""


def read_docx_text(path: Path, max_chars: int = 180_000) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
        document = ElementTree.fromstring(xml)
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError):
        return ""
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs = []
    for paragraph in document.iter(namespace + "p"):
        text = "".join(node.text or "" for node in paragraph.iter(namespace + "t")).strip()
        if text:
            paragraphs.append(text)
    return repair_mojibake("\n\n".join(paragraphs))[:max_chars]


def read_document_text(path: Path, max_chars: int = 180_000) -> str:
    if path.suffix.lower() == ".docx":
        return read_docx_text(path, max_chars)
    return read_text(path, max_chars)


def clean_field(value: str) -> str:
    value = strip_markdown(value)
    value = re.sub(r"\s*\|\s*", " / ", value)
    return value[:2000]


def split_tech(value: str) -> set[str]:
    if not value:
        return set()
    pieces = re.split(r"[,;/+]|\s+\|\s+", strip_markdown(value))
    return {piece.strip() for piece in pieces if 1 < len(piece.strip()) < 80}


def is_tech_label(value: str) -> bool:
    lower = value.lower().strip()
    rejected = (
        "archivos presentes", "moodboard", "comparte documentación", "comparte documentacion",
        "alimenta la base", "brazo ejecutor", "versión alternativa", "version alternativa",
        "módulo de visualización", "modulo de visualizacion", "extensión satelital",
        "extension satelital", "pdfs de entrenamiento", "tipografía custom", "tipografia custom",
    )
    if not value or any(token in lower for token in rejected):
        return False
    if lower in {"no definido", "no definido (conceptual)", "a"}:
        return False
    return len(value) <= 55 and len(value.split()) <= 7


def doc_score(path: Path) -> int:
    name = path.name.lower()
    score = 0
    priority = {
        "readme": 80, "prd": 78, "tech_stack": 72, "architecture": 70,
        "design": 65, "producto": 60, "proyecto": 55, "master": 50,
        "maestro": 50, "manual": 45, "roadmap": 40, "vision": 35,
        "descripcion": 35, "resumen": 35, "protocol": 18, "protocolo": 18,
    }
    for token, value in priority.items():
        if token in name:
            score += value
    score -= len(path.parts)
    return score


def extract_labeled(text: str, labels: Iterable[str]) -> str:
    for label in labels:
        patterns = (
            rf"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?{label}(?:\*\*)?\s*[:|]\s*(.+?)\s*$",
            rf"(?im)^\s*\|\s*(?:\*\*)?{label}(?:\*\*)?\s*\|\s*(.+?)\s*\|\s*$",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = clean_field(match.group(1))
                if value and value.lower() not in {"valor", "pendiente", "n/a"}:
                    return value
    return ""


def extract_summary_from_docs(docs: list[Path]) -> tuple[str, str, str, list[str], str]:
    purpose = ""
    problem = ""
    audience = ""
    features: list[str] = []
    source = ""
    for path in sorted(docs, key=doc_score, reverse=True)[:12]:
        if path.suffix.lower() not in {".md", ".txt", ".rst", ".docx"}:
            continue
        text = read_document_text(path, 90_000)
        if not text:
            continue
        if not purpose:
            purpose = extract_labeled(text, ("Qué es", "Que es", "Propósito", "Proposito", "Objetivo", "Visión", "Vision", "Resumen"))
            if purpose:
                source = str(path)
            else:
                plain = re.sub(r"(?s)```.*?```", "", text)
                paragraphs = re.split(r"\n\s*\n", plain)
                for paragraph in paragraphs:
                    candidate = clean_field(paragraph)
                    rejected = simple_key(candidate)
                    blocked = ("instrucciones", "protocolo maestro", "autoridad maxima", "handoff", "migracion desde", "aviso critico", "agente de ia")
                    if 45 <= len(candidate) <= 520 and not candidate.startswith(("---", "|")) and not any(token in rejected for token in blocked):
                        purpose = candidate
                        source = str(path)
                        break
        if not problem:
            problem = extract_labeled(text, ("Problema que resuelve", "Necesidad", "Dolor"))
        if not audience:
            audience = extract_labeled(text, ("Público objetivo", "Publico objetivo", "Usuario objetivo", "Audiencia"))
        if len(features) < 8:
            for line in text.splitlines():
                line = line.strip()
                if re.match(r"^[-*]\s+", line):
                    cleaned = clean_field(re.sub(r"^[-*]\s+", "", line))
                    if 20 <= len(cleaned) <= 220 and not cleaned.lower().startswith(("http", "archivo", "fecha")):
                        features.append(cleaned)
                        if len(features) >= 8:
                            break
        if purpose and problem and audience and len(features) >= 4:
            break
    return purpose, problem, audience, list(dict.fromkeys(features)), source


@dataclass
class ScanResult:
    key: str
    name: str
    category: str
    product_type: str
    root: Path
    origin: str
    file_count: int = 0
    size_bytes: int = 0
    latest: datetime = field(default_factory=lambda: datetime.fromtimestamp(0))
    ext_counts: Counter = field(default_factory=Counter)
    languages: set[str] = field(default_factory=set)
    technologies: set[str] = field(default_factory=set)
    frameworks: set[str] = field(default_factory=set)
    platforms: set[str] = field(default_factory=set)
    apis: set[str] = field(default_factory=set)
    persistence: set[str] = field(default_factory=set)
    docs: list[Path] = field(default_factory=list)
    manifests: list[Path] = field(default_factory=list)
    code_count: int = 0
    doc_count: int = 0
    asset_count: int = 0
    has_tests: bool = False
    has_git: bool = False
    skipped_dirs: Counter = field(default_factory=Counter)
    purpose: str = ""
    problem: str = ""
    audience: str = ""
    features: list[str] = field(default_factory=list)
    description_source: str = ""


def scan_project(root: Path, name: str, category: str, product_type: str, origin: str) -> ScanResult:
    result = ScanResult(simple_key(name), name, category, product_type, root, origin)
    result.has_git = (root / ".git").exists()
    package_paths: list[Path] = []
    if not root.exists():
        return result
    for current, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda _error: None):
        current_path = Path(current)
        kept = []
        for dirname in dirnames:
            if should_skip_dir(dirname):
                result.skipped_dirs[dirname.lower()] += 1
            else:
                kept.append(dirname)
        dirnames[:] = kept
        relative_depth = len(current_path.relative_to(root).parts)
        for filename in filenames:
            if filename == GENERATED_STATUS_FILENAME:
                continue
            path = current_path / filename
            try:
                stat = path.stat()
            except OSError:
                continue
            suffix = path.suffix.lower()
            lower_name = filename.lower()
            result.file_count += 1
            result.size_bytes += stat.st_size
            result.ext_counts[suffix or "[sin extensión]"] += 1
            if suffix in CODE_EXTENSIONS:
                result.code_count += 1
                result.languages.add(CODE_EXTENSIONS[suffix])
                if datetime.fromtimestamp(stat.st_mtime) > result.latest:
                    result.latest = datetime.fromtimestamp(stat.st_mtime)
            if suffix in DOC_EXTENSIONS:
                result.doc_count += 1
                if len(result.docs) < 220 and stat.st_size <= 2_500_000:
                    result.docs.append(path)
                if datetime.fromtimestamp(stat.st_mtime) > result.latest:
                    result.latest = datetime.fromtimestamp(stat.st_mtime)
            if suffix in ASSET_EXTENSIONS:
                result.asset_count += 1
            if "test" in lower_name or any("test" in part.lower() for part in path.parts):
                result.has_tests = True
            if lower_name in MANIFEST_NAMES or suffix in {".sln", ".csproj", ".xcodeproj"}:
                if relative_depth <= 7:
                    result.manifests.append(path)
                if datetime.fromtimestamp(stat.st_mtime) > result.latest:
                    result.latest = datetime.fromtimestamp(stat.st_mtime)
            if lower_name == "package.json" and relative_depth <= 7:
                package_paths.append(path)
            if lower_name == "cargo.toml":
                result.technologies.update({"Rust"})
            elif suffix in {".csproj", ".sln"}:
                result.technologies.update({".NET", "C#"})
            elif lower_name == "tauri.conf.json":
                result.technologies.add("Tauri")
                result.platforms.add("Escritorio")
            elif lower_name.startswith("androidmanifest") or lower_name.startswith("build.gradle"):
                result.platforms.add("Android")
            elif lower_name == "podfile" or suffix == ".swift":
                result.platforms.update({"iOS", "macOS"})
            elif lower_name == "pubspec.yaml":
                result.technologies.add("Flutter")
                result.platforms.update({"Android", "iOS"})

    for package_path in package_paths[:20]:
        try:
            package = json.loads(read_text(package_path, 400_000))
        except (json.JSONDecodeError, OSError):
            continue
        dependencies = {}
        for field_name in ("dependencies", "devDependencies", "peerDependencies"):
            value = package.get(field_name, {})
            if isinstance(value, dict):
                dependencies.update(value)
        for dependency in dependencies:
            if dependency in TECH_DEPENDENCIES:
                technology = TECH_DEPENDENCIES[dependency]
                result.technologies.add(technology)
                if technology in {"React", "Next.js", "Vue", "Svelte", "Tailwind CSS", "Three.js", "React Three Fiber", "Zustand", "Framer Motion", "GSAP"}:
                    result.frameworks.add(technology)
                if technology.endswith("API"):
                    result.apis.add(technology)
                if technology in {"Supabase", "Firebase", "SQLite"}:
                    result.persistence.add(technology)
        scripts = package.get("scripts", {})
        if isinstance(scripts, dict) and any("test" in key for key in scripts):
            result.has_tests = True
        if any(item in result.technologies for item in {"React", "Next.js", "Vue", "Svelte", "Vite"}):
            result.platforms.add("Web")
        if "Electron" in result.technologies:
            result.platforms.add("Escritorio")

    if "Python" in result.languages:
        result.technologies.add("Python")
    if "Rust" in result.languages:
        result.technologies.add("Rust")
    if "Kotlin" in result.languages:
        result.platforms.add("Android")
    if "Swift" in result.languages:
        result.platforms.update({"iOS", "macOS"})
    if result.product_type in {"Videojuego", "Juego de mesa", "Proyecto musical", "Producto gastronómico", "Publicación digital"} and not result.platforms:
        result.platforms.add("Concepto / contenido")
    result.docs.sort(key=doc_score, reverse=True)
    result.purpose, result.problem, result.audience, result.features, result.description_source = extract_summary_from_docs(result.docs)
    return result


def parse_old_audit() -> dict[str, dict[str, str | list[str]]]:
    path = VOYAGER_ROOT / "AUDITORIA_INTEGRAL_VOYAGER.md"
    text = read_text(path, 1_000_000)
    output: dict[str, dict[str, str | list[str]]] = {}
    pattern = re.compile(r"(?m)^###\s+\d+\s+[—-]\s+(.+?)\s*$")
    matches = list(pattern.finditer(text))
    for index, match in enumerate(matches):
        title = strip_markdown(match.group(1))
        title = re.sub(r"[^\w\s()!/-]+$", "", title).strip()
        section = text[match.end(): matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        key = simple_key(title)
        points = [clean_field(item) for item in re.findall(r"(?m)^\s*-\s+\[[xX ]\]\s+(.+?)\s*$", section)]
        output[key] = {
            "name": title,
            "subcategoria": extract_labeled(section, ("Categoría", "Categoria")),
            "proposito": extract_labeled(section, ("Propósito", "Proposito")),
            "stack": extract_labeled(section, ("Stack Técnico", "Stack Tecnico")),
            "madurez": extract_labeled(section, ("Estado de Madurez",)),
            "diagnostico": extract_labeled(section, ("Diagnóstico del Auditor", "Diagnostico del Auditor")),
            "integraciones": extract_labeled(section, ("Contexto Cruzado",)),
            "caracteristicas": points[:12],
            "source": str(path),
        }
    return output


def parse_fast_audit() -> dict[str, dict[str, list[str]]]:
    path = VOYAGER_ROOT / "audit_temp.json"
    try:
        items = json.loads(read_text(path, 2_000_000))
    except json.JSONDecodeError:
        return {}
    output: dict[str, dict[str, list[str]]] = {}
    for item in items if isinstance(items, list) else []:
        key = simple_key(str(item.get("name", "")))
        output[key] = {
            "tech": [clean_field(str(value)) for value in item.get("tech_clues", []) if value],
            "apis": [clean_field(str(value)) for value in item.get("apis", []) if value],
        }
    return output


def markdown_tables(text: str) -> Iterable[tuple[list[str], list[list[str]]]]:
    lines = text.splitlines()
    index = 0
    while index + 1 < len(lines):
        if lines[index].lstrip().startswith("|") and re.match(r"^\s*\|?\s*:?-+", lines[index + 1]):
            header = [strip_markdown(cell) for cell in lines[index].strip().strip("|").split("|")]
            rows: list[list[str]] = []
            index += 2
            while index < len(lines) and lines[index].lstrip().startswith("|"):
                row = [strip_markdown(cell) for cell in lines[index].strip().strip("|").split("|")]
                if len(row) == len(header):
                    rows.append(row)
                index += 1
            yield header, rows
        else:
            index += 1


def parse_master_docs() -> dict[str, dict[str, str | list[str]]]:
    product_root = VOYAGER_ROOT / "sociedad unova" / "Producto"
    output: dict[str, dict[str, str | list[str]]] = defaultdict(dict)
    if not product_root.exists():
        return output
    for path in product_root.rglob("*.md"):
        if "11_Analisis_Financiero" in str(path):
            continue
        text = read_text(path, 1_000_000)
        if not text:
            continue
        headings = list(re.finditer(r"(?im)^#{2,4}\s+.*?FICHA\s+\d+\s*:\s*(.+?)\s*$", text))
        for idx, heading in enumerate(headings):
            raw_name = strip_markdown(heading.group(1))
            section = text[heading.end(): headings[idx + 1].start() if idx + 1 < len(headings) else len(text)]
            key = simple_key(raw_name)
            record = output[key]
            record.setdefault("name", re.sub(r"\s+[^\x00-\x7F]+$", "", raw_name).strip())
            field_map = {
                "que es": "resumen", "qué es": "resumen", "concepto": "proposito",
                "problema que resuelve": "problema", "publico objetivo": "publico",
                "público objetivo": "publico", "tipo": "tipo", "tipo de producto": "tipo",
                "estado": "estado", "estado actual": "estado", "modelo de negocio": "modelo_negocio",
                "diferencial": "diferenciadores", "observaciones": "caracteristicas",
            }
            for line in section.splitlines():
                match = re.match(r"^\s*\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|\s*$", line)
                if not match:
                    continue
                label = simple_key(match.group(1))
                target = field_map.get(label)
                if target and not record.get(target):
                    record[target] = clean_field(match.group(2))
            vision = extract_labeled(section, ("Visión", "Vision"))
            if vision:
                record.setdefault("proposito", vision)
            summary = extract_labeled(section, ("Qué es", "Que es"))
            if summary:
                record.setdefault("resumen", summary)
            model = extract_labeled(section, ("Modelo de Negocio",))
            if model:
                record.setdefault("modelo_negocio", model)
            state = extract_labeled(section, ("Estado", "Estado actual"))
            if state:
                record.setdefault("estado", state)
            for score_name, target in (("DESARROLLO", "score_desarrollo"), ("RENTABILIDAD", "score_rentabilidad")):
                match = re.search(rf"(?i)SCORE\s+DE\s+{score_name}\s*:\s*(\d+)\s*/\s*25", section)
                if match:
                    record[target] = f"{match.group(1)}/25"
            total = re.search(r"(?i)(?:Total|TOTAL)\s*:\s*(\d+)\s*/\s*50", section)
            if total:
                record["score_total"] = f"{total.group(1)}/50"
            decision = re.search(r"(?i)\*\*Decisión\s*:\s*([^*|\n]+)", section)
            if decision:
                record["decision"] = clean_field(decision.group(1))
            sources = list(record.get("sources", []))
            sources.append(str(path))
            record["sources"] = list(dict.fromkeys(sources))

        for header, rows in markdown_tables(text):
            normalized = [simple_key(cell) for cell in header]
            if "producto" not in normalized and "producto desarrollo" not in normalized and "nombre" not in normalized:
                continue
            name_index = next((i for i, cell in enumerate(normalized) if cell in {"producto", "producto desarrollo", "nombre"}), None)
            if name_index is None:
                continue
            for row in rows:
                name = row[name_index]
                if not name or name.lower() in {"producto", "proyecto"}:
                    continue
                key = simple_key(name)
                record = output[key]
                record.setdefault("name", name)
                for idx, label in enumerate(normalized):
                    if idx >= len(row) or not row[idx]:
                        continue
                    value = row[idx]
                    if label in {"que es", "qué es"}:
                        record.setdefault("resumen", value)
                    elif label in {"estado", "estado rectificado"}:
                        record.setdefault("estado", value)
                    elif label == "decision":
                        record.setdefault("decision", value)
                    elif label == "dev" and re.match(r"\d+", value):
                        record.setdefault("score_desarrollo", f"{value}/25" if "/" not in value else value)
                    elif label == "rent" and re.match(r"\d+", value):
                        record.setdefault("score_rentabilidad", f"{value}/25" if "/" not in value else value)
                    elif label == "total" and re.match(r"\d+", value):
                        record.setdefault("score_total", f"{value}/50" if "/" not in value else value)
                sources = list(record.get("sources", []))
                sources.append(str(path))
                record["sources"] = list(dict.fromkeys(sources))
    return output


def voyager_candidates() -> list[tuple[Path, str, str, str]]:
    candidates = []
    for folder, (category, product_type) in CATEGORY_MAP.items():
        category_root = VOYAGER_ROOT / folder
        if not category_root.exists():
            continue
        for child in sorted((item for item in category_root.iterdir() if item.is_dir()), key=lambda item: item.name.lower()):
            candidates.append((child, display_name(child.name), category, product_type))
    return candidates


def dev_candidates() -> tuple[list[tuple[Path, str, str, str]], list[dict[str, str]]]:
    candidates = []
    exclusions = []
    if not DEV_ROOT.exists():
        return candidates, exclusions
    for child in sorted((item for item in DEV_ROOT.iterdir() if item.is_dir()), key=lambda item: item.name.lower()):
        lower = child.name.lower()
        if lower in DEV_EXCLUDED:
            exclusions.append({"ruta": str(child), "nivel": "raíz", "razon": DEV_EXCLUDED[lower], "revisada": "sí"})
            continue
        override = DEV_OVERRIDES.get(lower)
        if not override:
            exclusions.append({"ruta": str(child), "nivel": "raíz", "razon": "No se identificó como producto consolidado; requiere clasificación manual.", "revisada": "sí"})
            continue
        name, category, product_type = override
        candidates.append((child, name, category, product_type))
    return candidates, exclusions


def derive_status(scan: ScanResult, documented: str) -> str:
    if scan.code_count >= 20 and scan.manifests:
        return "Código y estructura ejecutable detectados"
    if scan.code_count > 0:
        return "Código parcial detectado"
    if scan.doc_count > 0 and scan.asset_count > 0:
        return "Concepto documentado con assets"
    if scan.doc_count > 0:
        return "Concepto documentado"
    if documented:
        return "Estado descrito, sin evidencia técnica suficiente"
    return "Información insuficiente"


def bool_text(value: bool) -> str:
    return "sí" if value else "no"


def semicolon(values: Iterable[str], limit: int | None = None) -> str:
    cleaned = [clean_field(value) for value in values if clean_field(value)]
    unique = list(dict.fromkeys(cleaned))
    if limit:
        unique = unique[:limit]
    return "; ".join(unique)


def choose_primary(scans: list[ScanResult]) -> ScanResult:
    return max(scans, key=lambda item: (item.latest, bool(item.manifests), item.code_count, item.origin == "C"))


def merge_group(
    scans: list[ScanResult],
    old_audit: dict[str, dict[str, str | list[str]]],
    fast_audit: dict[str, dict[str, list[str]]],
    master: dict[str, dict[str, str | list[str]]],
) -> dict[str, str]:
    primary = choose_primary(scans)
    key = primary.key
    old = old_audit.get(key, {})
    fast = fast_audit.get(key, {})
    business = master.get(key, {})
    voyager_scans = [scan for scan in scans if scan.origin == "G"]
    all_docs = sorted({path for scan in scans for path in scan.docs}, key=doc_score, reverse=True)
    all_tech = set().union(*(scan.technologies for scan in scans))
    all_frameworks = set().union(*(scan.frameworks for scan in scans))
    all_languages = set().union(*(scan.languages for scan in scans))
    all_platforms = set().union(*(scan.platforms for scan in scans))
    all_apis = set().union(*(scan.apis for scan in scans))
    all_persistence = set().union(*(scan.persistence for scan in scans))
    all_features = [feature for scan in scans for feature in scan.features]

    old_stack = str(old.get("stack", ""))
    all_tech.update(split_tech(old_stack))
    for value in fast.get("tech", []):
        if value in TECH_DEPENDENCIES:
            all_tech.add(TECH_DEPENDENCIES[value])
        elif value in {"Python", "Rust", "C#", ".NET", "CSS", "React/JS/TS"}:
            all_tech.add(value)
    all_apis.update(fast.get("apis", []))

    business_sources = [str(value) for value in business.get("sources", [])]
    purpose = str(business.get("proposito", "")) or str(old.get("proposito", "")) or primary.purpose
    summary = str(business.get("resumen", "")) or purpose or primary.purpose
    if not purpose and summary:
        purpose = summary
    problem = str(business.get("problema", "")) or primary.problem
    audience = str(business.get("publico", "")) or primary.audience
    documented_state = str(business.get("estado", "")) or str(old.get("madurez", ""))
    subcategory = str(old.get("subcategoria", ""))
    product_type = str(business.get("tipo", "")) or primary.product_type
    old_features = [str(value) for value in old.get("caracteristicas", [])]
    business_features = [str(business.get("caracteristicas", ""))] if business.get("caracteristicas") else []
    features = old_features + business_features + all_features
    source_description = business_sources[0] if business_sources else str(old.get("source", "")) or primary.description_source
    documentary_paths = [str(scan.root) for scan in voyager_scans]
    location = "C: y G:" if {scan.origin for scan in scans} == {"C", "G"} else f"{primary.origin}:"
    confidence = "Alta" if (purpose or summary) and primary.manifests else "Media" if (purpose or summary or primary.manifests) else "Baja"
    notes = []
    if len(scans) > 1:
        notes.append(f"Se detectaron {len(scans)} ubicaciones; se muestra la versión con actividad relevante más reciente.")
    if documented_state and not primary.manifests:
        notes.append("La madurez proviene de documentación; no equivale a build verificado.")
    if not purpose:
        notes.append("No se encontró una descripción explícita; requiere revisión editorial.")
    if voyager_scans:
        notes.append("Características enriquecidas con documentación de Voyager y Caja de Producto Unova.")

    name = str(business.get("name", "")) or str(old.get("name", "")) or primary.name
    return {
        "id": key.replace(" ", "-"),
        "proyecto": clean_field(name),
        "categoria": primary.category,
        "subcategoria": clean_field(subcategory),
        "tipo": clean_field(product_type),
        "proposito": clean_field(purpose),
        "resumen": clean_field(summary),
        "problema_que_resuelve": clean_field(problem),
        "publico_objetivo": clean_field(audience),
        "estado": clean_field(documented_state or derive_status(primary, documented_state)),
        "madurez_documentada": clean_field(str(old.get("madurez", "")) or documented_state),
        "estado_tecnico_detectado": derive_status(primary, documented_state),
        "decision_producto": clean_field(str(business.get("decision", ""))),
        "modelo_negocio": clean_field(str(business.get("modelo_negocio", ""))),
        "score_desarrollo": clean_field(str(business.get("score_desarrollo", ""))),
        "score_rentabilidad": clean_field(str(business.get("score_rentabilidad", ""))),
        "score_total": clean_field(str(business.get("score_total", ""))),
        "caracteristicas": semicolon(features, 16),
        "diferenciadores": clean_field(str(business.get("diferenciadores", ""))),
        "diagnostico": clean_field(str(old.get("diagnostico", ""))),
        "stack": semicolon(sorted(value for value in all_tech if is_tech_label(value)), 24),
        "lenguajes": semicolon(sorted(all_languages), 12),
        "frameworks": semicolon(sorted(all_frameworks), 12),
        "plataformas": semicolon(sorted(all_platforms), 8),
        "apis_integraciones": semicolon(sorted(all_apis | split_tech(str(old.get("integraciones", "")))), 16),
        "persistencia": semicolon(sorted(all_persistence), 8),
        "tiene_codigo": bool_text(any(scan.code_count > 0 for scan in scans)),
        "tiene_documentacion": bool_text(any(scan.doc_count > 0 for scan in scans)),
        "tiene_tests": bool_text(any(scan.has_tests for scan in scans)),
        "tiene_git": bool_text(any(scan.has_git for scan in scans)),
        "archivos_relevantes": str(sum(scan.file_count for scan in scans)),
        "tamano_relevante_mb": f"{sum(scan.size_bytes for scan in scans) / 1_048_576:.1f}",
        "documentos_principales": semicolon([str(path) for path in all_docs], 8),
        "ruta_vigente": str(primary.root),
        "ruta_fuente_documental": semicolon(documentary_paths + business_sources, 8),
        "ubicacion": location,
        "ultima_actividad": primary.latest.strftime("%Y-%m-%d") if primary.latest.year > 1970 else "",
        "copias_detectadas": str(len(scans)),
        "confianza": confidence,
        "fuente_descripcion": source_description,
        "notas_auditoria": " ".join(notes),
        "grupo_operativo": "",
        "ultimo_cambio": "",
        "ultimo_avance_documentado": "",
        "pendientes_documentados": "",
        "proximo_paso": "",
        "bloqueos_documentados": "",
        "progreso_mvp": "",
        "progreso_vision": "",
        "confianza_progreso": "",
        "evidencia_faltante": "",
        "documentos_desactualizados": "",
        "localhost_activo": "no",
    }


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    lock_path = path.parent / f".{path.name}.lock"
    with file_lock(lock_path, timeout=120):
        atomic_write_csv(path, fields, rows, backup=path.name == "proyectos.csv")


def load_previous_enrichment() -> dict[str, dict[str, str]]:
    preserved: dict[str, dict[str, str]] = {}
    catalog = DATA_DIR / "proyectos.csv"
    # La copia anterior se consulta primero para poder recuperar un catálogo
    # enriquecido si una ejecución interrumpida dejó campos dinámicos vacíos.
    for path in (catalog.with_suffix(catalog.suffix + ".bak"), catalog):
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = csv.DictReader(handle)
                for row in rows:
                    project_id = str(row.get("id") or "").strip()
                    if not project_id:
                        continue
                    target = preserved.setdefault(project_id, {})
                    for field_name in ENRICHED_FIELDS:
                        value = str(row.get(field_name) or "").strip()
                        if value:
                            target[field_name] = value
        except OSError:
            continue
    return preserved


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    if not VOYAGER_ROOT.exists():
        print(f"ERROR: No existe la raíz Voyager: {VOYAGER_ROOT}", file=sys.stderr)
        return 2
    if not DEV_ROOT.exists():
        print(f"ERROR: No existe la raíz de desarrollos: {DEV_ROOT}", file=sys.stderr)
        return 2

    old_audit = parse_old_audit()
    fast_audit = parse_fast_audit()
    master = parse_master_docs()
    previous_enrichment = load_previous_enrichment()
    grouped: dict[str, list[ScanResult]] = defaultdict(list)
    exclusions: list[dict[str, str]] = []

    voyager = voyager_candidates()
    print(f"Auditando {len(voyager)} carpetas de proyecto en Voyager...")
    for index, (path, name, category, product_type) in enumerate(voyager, start=1):
        scan = scan_project(path, name, category, product_type, "G")
        grouped[scan.key].append(scan)
        print(f"[{index:02d}/{len(voyager)}] {name}: {scan.file_count} archivos relevantes")

    dev, dev_exclusions = dev_candidates()
    exclusions.extend(dev_exclusions)
    print(f"Auditando {len(dev)} carpetas de desarrollo activo en C:...")
    for index, (path, name, category, product_type) in enumerate(dev, start=1):
        scan = scan_project(path, name, category, product_type, "C")
        grouped[scan.key].append(scan)
        print(f"[C {index:02d}/{len(dev)}] {name}: {scan.file_count} archivos relevantes")

    records = [merge_group(scans, old_audit, fast_audit, master) for _, scans in sorted(grouped.items())]
    for record in records:
        record.update(previous_enrichment.get(record["id"], {}))
    records.sort(key=lambda item: (item["categoria"], item["proyecto"].lower()))

    for key, scans in grouped.items():
        if len(scans) <= 1:
            continue
        primary = choose_primary(scans)
        for scan in scans:
            if scan.root == primary.root:
                continue
            exclusions.append({
                "ruta": str(scan.root),
                "nivel": "copia/variante",
                "razon": f"Se consolidó bajo {primary.name}; la ruta vigente seleccionada es {primary.root}.",
                "revisada": "sí",
            })

    exclusions.extend([
        {"ruta": str(VOYAGER_ROOT / "FICHAS_PRODUCTO"), "nivel": "raíz Voyager", "razon": "Carpeta vacía al momento de la auditoría.", "revisada": "sí"},
        {"ruta": str(VOYAGER_ROOT / "pryectos"), "nivel": "raíz Voyager", "razon": "Bóveda Obsidian sin fichas de producto; no se publicó como producto.", "revisada": "sí"},
        {"ruta": str(VOYAGER_ROOT / "sociedad unova"), "nivel": "raíz Voyager", "razon": "Se usaron únicamente los análisis de Producto para enriquecer fichas; datos societarios, personales y financieros no se publican.", "revisada": "sí"},
    ])

    write_csv(DATA_DIR / "proyectos.csv", CSV_FIELDS, records)
    write_csv(DATA_DIR / "exclusiones_auditoria.csv", ["ruta", "nivel", "razon", "revisada"], exclusions)

    category_counts = Counter(record["categoria"] for record in records)
    meta = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "voyager_root": str(VOYAGER_ROOT),
        "dev_root": str(DEV_ROOT),
        "voyager_project_folders_scanned": len(voyager),
        "dev_folders_scanned": len(dev),
        "canonical_projects": len(records),
        "categories": dict(sorted(category_counts.items())),
        "exclusions_logged": len(exclusions),
    }
    (DATA_DIR / "audit_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    report_lines = [
        "# Resultado de auditoría",
        "",
        f"- Fecha: {meta['generated_at']}",
        f"- Carpetas de proyecto Voyager revisadas: {len(voyager)}",
        f"- Carpetas de desarrollo C: revisadas: {len(dev)}",
        f"- Productos canónicos publicados: {len(records)}",
        f"- Exclusiones y copias registradas: {len(exclusions)}",
        "",
        "## Productos por categoría",
        "",
    ]
    report_lines.extend(f"- {category}: {count}" for category, count in sorted(category_counts.items()))
    report_lines.extend([
        "",
        "## Criterio",
        "",
        "Se publica una sola ruta vigente por producto. La información de producto se enriquece con la auditoría integral, los análisis maestros de Sociedad Unova/Producto y los documentos internos de cada carpeta. No se publican datos personales, financieros, dependencias, builds ni respaldos como productos independientes.",
        "",
    ])
    (DATA_DIR / "INFORME_AUDITORIA.md").write_text("\n".join(report_lines), encoding="utf-8")
    if "--catalog-only" not in sys.argv:
        try:
            from history_engine import enrich_and_track

            history_result = enrich_and_track(
                reason="manual",
                project_ids=None,
                create_backfill=True,
                write_project_status=True,
            )
            meta["history"] = history_result
            (DATA_DIR / "audit_meta.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as error:  # noqa: BLE001 - el catálogo base debe sobrevivir
            meta["history_error"] = str(error)
            (DATA_DIR / "audit_meta.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"ADVERTENCIA: no se pudo actualizar el historial: {error}", file=sys.stderr)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
