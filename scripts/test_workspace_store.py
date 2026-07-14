from __future__ import annotations

import csv
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import safe_storage
import workspace_store as store


class WorkspaceStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.data = self.base / "data"
        self.data.mkdir()
        self.patch = patch.multiple(
            store,
            DATA_DIR=self.data,
            PERSONAL_WORKSPACE_PATH=self.data / "personal_workspace.json",
            PROJECT_OVERRIDES_PATH=self.data / "project_overrides.json",
            SETTINGS_PATH=self.data / "settings.json",
            PERSONAL_LOCK_PATH=self.data / ".personal.lock",
        )
        self.patch.start()
        store.ensure_personal_files()

    def tearDown(self) -> None:
        self.patch.stop()
        self.temporary.cleanup()

    def test_task_lifecycle_is_persistent(self) -> None:
        task = store.create_task(
            {
                "title": "Preparar validación",
                "project_id": "asteria",
                "status": "next",
                "priority": "high",
                "checklist": ["Build", "Prueba visual"],
            },
            {"asteria"},
        )
        updated = store.update_task(
            task["id"],
            {
                "status": "done",
                "notes": "Validado",
                "order": 7,
                "checklist": [
                    {"id": "build", "text": "Build", "done": True},
                    {"id": "visual", "text": "Prueba visual", "done": False},
                ],
            },
            {"asteria"},
        )
        self.assertEqual(updated["status"], "done")
        self.assertTrue(updated["completed_at"])
        self.assertEqual(updated["order"], 7)
        self.assertTrue(updated["checklist"][0]["done"])
        self.assertEqual(store.load_workspace()["tasks"][0]["notes"], "Validado")
        archived = store.archive_task(task["id"])
        self.assertTrue(archived["archived_at"])

    def test_invalid_project_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            store.create_task(
                {"title": "No válida", "project_id": "missing"},
                {"asteria"},
            )

    def test_atomic_csv_never_exposes_empty_file(self) -> None:
        target = self.data / "catalog.csv"
        fields = ["id", "value"]
        safe_storage.atomic_write_csv(target, fields, [{"id": "seed", "value": "ok"}])
        empty_reads: list[int] = []
        writer_errors: list[Exception] = []

        def writer(prefix: str) -> None:
            try:
                for index in range(30):
                    rows = [{"id": f"{prefix}-{index}", "value": "x" * 100}]
                    safe_storage.atomic_write_csv(target, fields, rows)
            except Exception as error:  # noqa: BLE001 - la prueba debe capturarlo
                writer_errors.append(error)

        threads = [threading.Thread(target=writer, args=(name,)) for name in ("a", "b")]
        for thread in threads:
            thread.start()
        while any(thread.is_alive() for thread in threads):
            if target.exists() and target.stat().st_size == 0:
                empty_reads.append(0)
        for thread in threads:
            thread.join()

        with target.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertFalse(empty_reads)
        self.assertFalse(writer_errors)
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
