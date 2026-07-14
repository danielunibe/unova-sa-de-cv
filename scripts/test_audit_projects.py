from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import audit_projects


class AuditProjectTests(unittest.TestCase):
    def test_previous_enrichment_recovers_from_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            fields = ["id", *audit_projects.ENRICHED_FIELDS]
            current = data_dir / "proyectos.csv"
            backup = data_dir / "proyectos.csv.bak"

            with backup.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "id": "asteria",
                        "grupo_operativo": "iniciado",
                        "progreso_mvp": "64",
                        "localhost_activo": "sí",
                    }
                )

            with current.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "id": "asteria",
                        "grupo_operativo": "",
                        "progreso_mvp": "",
                        "localhost_activo": "no",
                    }
                )

            with patch.object(audit_projects, "DATA_DIR", data_dir):
                preserved = audit_projects.load_previous_enrichment()

            self.assertEqual(preserved["asteria"]["grupo_operativo"], "iniciado")
            self.assertEqual(preserved["asteria"]["progreso_mvp"], "64")
            self.assertEqual(preserved["asteria"]["localhost_activo"], "no")


if __name__ == "__main__":
    unittest.main()
