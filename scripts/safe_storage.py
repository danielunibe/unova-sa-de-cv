from __future__ import annotations

import csv
import io
import json
import os
import shutil
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

try:
    import msvcrt
except ImportError:  # pragma: no cover - el entorno principal es Windows
    msvcrt = None


@contextmanager
def file_lock(lock_path: Path, timeout: float = 30.0):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"\0")
            handle.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                handle.seek(0)
                if msvcrt is not None:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"No se pudo obtener el bloqueo: {lock_path}")
                time.sleep(0.05)
        try:
            yield
        finally:
            if msvcrt is not None:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def atomic_write_bytes(path: Path, content: bytes, backup: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if backup and path.exists() and path.stat().st_size > 0:
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        deadline = time.monotonic() + 8
        while True:
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_text(
    path: Path,
    content: str,
    *,
    encoding: str = "utf-8",
    backup: bool = False,
) -> None:
    atomic_write_bytes(path, content.encode(encoding), backup=backup)


def atomic_write_json(path: Path, value: Any, *, backup: bool = True) -> None:
    atomic_write_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        backup=backup,
    )


def atomic_write_csv(
    path: Path,
    fields: list[str],
    rows: Iterable[dict[str, Any]],
    *,
    backup: bool = True,
) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    atomic_write_text(path, buffer.getvalue(), encoding="utf-8-sig", backup=backup)
