from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import history_engine as engine


class HistoryEngineTests(unittest.TestCase):
    def test_compare_snapshots_detects_added_modified_deleted(self) -> None:
        previous = {
            "kept.txt": [10, 100],
            "changed.js": [20, 100],
            "removed.md": [30, 100],
        }
        current = {
            "kept.txt": [10, 100],
            "changed.js": [21, 200],
            "added.py": [5, 300],
        }
        self.assertEqual(
            engine.compare_snapshots(previous, current),
            {
                "added": ["added.py"],
                "modified": ["changed.js"],
                "deleted": ["removed.md"],
            },
        )

    def test_generated_status_is_excluded(self) -> None:
        self.assertFalse(engine.relevant_file(Path(engine.STATUS_FILENAME)))
        self.assertTrue(engine.relevant_file(Path("src/app.js")))
        self.assertTrue(engine.should_skip_dir("node_modules"))

    def test_disconnected_root_preserves_previous_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            data_dir = base / "data"
            history_dir = base / "history"
            state_dir = history_dir / "project_state"
            events_dir = history_dir / "events"
            daily_dir = history_dir / "daily"
            data_dir.mkdir()
            state_dir.mkdir(parents=True)

            row = {field: "" for field in engine.CSV_FIELDS}
            row.update(
                {
                    "id": "offline-project",
                    "proyecto": "Offline Project",
                    "ruta_vigente": str(base / "missing-drive" / "project"),
                }
            )
            with (data_dir / "proyectos.csv").open(
                "w", encoding="utf-8-sig", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=engine.CSV_FIELDS)
                writer.writeheader()
                writer.writerow(row)

            prior_state = {
                "project_id": "offline-project",
                "files": {
                    "src/app.js": [100, 1000],
                    "README.md": [50, 1000],
                },
            }
            state_path = state_dir / "offline-project.json"
            state_path.write_text(json.dumps(prior_state), encoding="utf-8")

            patches = {
                "DATA_DIR": data_dir,
                "HISTORY_DIR": history_dir,
                "EVENTS_DIR": events_dir,
                "STATE_DIR": state_dir,
                "DAILY_DIR": daily_dir,
                "MONITOR_STATUS_PATH": history_dir / "monitor_status.json",
                "HISTORY_META_PATH": history_dir / "history_meta.json",
                "LOCALHOST_STATE_PATH": history_dir / "localhost_state.json",
            }
            with patch.multiple(engine, **patches):
                result = engine.enrich_and_track(
                    reason="test",
                    project_ids=None,
                    create_backfill=False,
                    write_project_status=False,
                )

            preserved = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(result["disconnected_projects"], ["offline-project"])
            self.assertEqual(preserved["files"], prior_state["files"])
            self.assertFalse(list(events_dir.glob("*.jsonl")))


if __name__ == "__main__":
    unittest.main()
