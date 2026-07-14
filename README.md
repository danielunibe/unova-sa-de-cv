# UNOVA Personal Work Manager

Gestor local y personal para consultar los 68 proyectos UNOVA, saber qué se hizo, qué falta y cuál es el siguiente paso sin mezclar la auditoría automática con tus tareas manuales.

## Abrir

```powershell
.\start_catalog.ps1
```

Abre [http://127.0.0.1:4173](http://127.0.0.1:4173). El monitor queda oculto y puede seguir funcionando aunque cierres el navegador.

## Áreas

- **Mi trabajo:** tareas personales, estados, prioridades, fechas y sugerencias documentales.
- **Proyectos:** dashboard con gráficas reales, 36 en marcha, 32 ideas y lista completa.
- **Actividad:** timeline exacto y reconstrucción estimada, con reproducción, pausa, velocidad y navegación temporal.
- **Estado:** revisión automática, carpetas disponibles y problemas recientes.
- **Configuración:** tema claro, oscuro o automático; densidad y vista inicial.

Cada proyecto tiene Resumen, Tareas, Avance, Actividad y Documentos, además de accesos seguros a su carpeta y a GitHub cuando existe.

## Actualizar

- Interfaz: botón de actualización.
- Catálogo: `python .\scripts\audit_projects.py --catalog-only`.
- Auditoría completa: `python .\scripts\unova_server.py --scan-once`.
- Automático: al iniciar sesión y diariamente a las 23:30.

Instalar o reparar automatización:

```powershell
.\scripts\install_automation.ps1
```

## Separación de datos

- `data/proyectos.csv`: catálogo automático compatible con Excel.
- `data/personal_workspace.json`: tareas y orden personal.
- `data/project_overrides.json`: GitHub manual, color e icono.
- `data/settings.json`: preferencias de interfaz.
- `history/events/YYYY-MM.jsonl`: historial append-only.
- `history/project_state/`: snapshot verificable por proyecto.
- `UNOVA_PROJECT_STATUS.md`: ficha automática autorizada en cada ruta canónica.

Una auditoría nunca debe borrar tareas personales ni editar roadmaps originales.

## Verificar

```powershell
python -m unittest scripts\test_audit_projects.py scripts\test_history_engine.py scripts\test_workspace_store.py -v
```

El progreso MVP es una estimación basada en evidencia y muestra confianza. La visión completa solo tiene porcentaje cuando existe un roadmap o checklist explícito; de lo contrario muestra `N/D`.
