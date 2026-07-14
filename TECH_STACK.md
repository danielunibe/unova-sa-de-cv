# TECH_STACK.md

## Resumen técnico

- Interfaz: HTML5, CSS modular y JavaScript ES Modules sin framework.
- Servidor/API: Python 3.10 con `ThreadingHTTPServer`.
- Auditor, historial y almacenamiento seguro: Python, únicamente biblioteca estándar.
- Datos: CSV UTF-8 con BOM, JSON, JSONL y Markdown.
- Automatización: Windows Task Scheduler y PowerShell.
- Dirección local: `127.0.0.1:4173`.
- Dependencias externas: ninguna.

## Comandos confirmados

| Comando | Uso |
|---|---|
| `.\start_catalog.ps1` | Inicia el monitor si hace falta y abre el gestor |
| `.\scripts\start_monitor.ps1` | Inicia únicamente el servidor/monitor oculto |
| `python .\scripts\audit_projects.py --catalog-only` | Regenera el catálogo conservando el enriquecimiento previo |
| `python .\scripts\unova_server.py --scan-once` | Auditoría global completa sin servidor |
| `python -m unittest scripts\test_audit_projects.py scripts\test_history_engine.py scripts\test_workspace_store.py -v` | Pruebas de auditor, historial, tareas y escritura atómica |
| `.\scripts\install_automation.ps1` | Registra inicio de sesión y auditoría de las 23:30 |
| `.\scripts\uninstall_automation.ps1` | Retira las tareas automáticas |

## Datos persistentes

| Archivo | Responsabilidad |
|---|---|
| `data/proyectos.csv` | Catálogo automático protegido y exportable a Excel |
| `data/personal_workspace.json` | Tareas personales, orden, estados y archivo |
| `data/project_overrides.json` | GitHub manual, color e icono por proyecto |
| `data/settings.json` | Tema, vista inicial y densidad |
| `history/events/*.jsonl` | Historial append-only |
| `history/project_state/*.json` | Snapshot verificable actual |

## Restricciones

- No instalar paquetes, base de datos ni servicio externo sin autorización.
- No exponer el servidor fuera de `127.0.0.1`.
- No cambiar framework, formatos centrales ni tareas automáticas sin autorización.
- No guardar tareas personales dentro del CSV ni de las carpetas auditadas.
