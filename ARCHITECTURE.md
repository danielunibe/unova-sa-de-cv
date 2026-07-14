# ARCHITECTURE.md

## Flujo principal

```txt
Carpetas canónicas C: + G:
        │ lectura y ficha autorizada
        ▼
audit_projects.py ──► data/proyectos.csv
        │                catálogo oficial, atómico y con backup
        ▼
history_engine.py ──► snapshots + JSONL + CSV diario + progreso
        │
        ├──► unova_server.py ──► API local ──► interfaz modular
        │
        └──► monitor de localhost + auditoría diaria 23:30

Gestión personal
interfaz ──► workspace_store.py ──► JSON personales separados
```

## Módulos

| Módulo | Responsabilidad |
|---|---|
| `scripts/audit_projects.py` | Descubrir y consolidar 68 productos; preservar campos dinámicos |
| `scripts/history_engine.py` | Snapshots, diffs, backfill, continuidad, progreso y fichas |
| `scripts/safe_storage.py` | Bloqueo entre procesos y escrituras atómicas con recuperación |
| `scripts/workspace_store.py` | Tareas, preferencias de proyecto y configuración personal |
| `scripts/unova_server.py` | Archivos estáticos, API, monitor, agenda y apertura segura de carpetas |
| `app.js` | Orquestación de vistas, navegación, diálogos y eventos |
| `ui/*.js` | Componentes, Mi trabajo, portafolio, proyecto, actividad y ajustes |
| `ui/dashboard-charts.js` | Gráficas SVG/CSS derivadas de catálogo, progreso e historial |
| `styles/*.css` | Tokens, shell, componentes, vistas y responsive |

## API

Consulta:

- `GET /api/catalog`
- `GET /api/stats`
- `GET /api/events`
- `GET /api/progress`
- `GET /api/monitor`
- `GET /api/audit`
- `GET /api/workspace`
- `GET /api/projects/{id}`
- `GET /api/settings`

Acciones locales:

- `POST /api/scan`
- `POST /api/tasks`
- `PATCH /api/tasks/{id}`
- `POST /api/tasks/{id}/archive`
- `POST /api/projects/{id}/open-folder`
- `PATCH /api/projects/{id}/preferences`
- `PATCH /api/settings`

Las acciones personales no alteran datos oficiales. La apertura de carpetas acepta únicamente IDs del catálogo.

## Límites

- Un registro canónico por producto.
- Pipeline automático separado del plan personal editable.
- Historial posterior a la línea base exacto; backfill inicial estimado.
- Una ruta desconectada conserva su estado previo.
- Escaneos focalizados solo para proyectos con localhost activo.
- Las sugerencias documentales no se vuelven tareas hasta una acción explícita del usuario.
