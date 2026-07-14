# AGENTS.md — UNOVA Personal Work Manager

Actúa como programador principal. El usuario define intención, prioridad y aprobación; Codex resuelve la implementación técnica.

## Regla principal

Lo confirmado se preserva. Lo dudoso se reporta. Lo nuevo se agrega de forma aislada. Lo destructivo requiere autorización explícita.

## Antes de modificar

1. Leer `TECH_STACK.md`, `ARCHITECTURE.md` y `CODEX_GUARDRAILS.md`.
2. Leer `DESIGN.md` si el cambio afecta la interfaz.
3. Revisar solo los archivos necesarios y elegir el cambio mínimo viable.
4. No instalar dependencias. Las carpetas fuente solo admiten la ficha automática autorizada.

## Reglas de implementación

- Las raíces auditadas son de solo lectura excepto por `UNOVA_PROJECT_STATUS.md`.
- `data/proyectos.csv` es el catálogo automático oficial; no editarlo desde la interfaz.
- Las tareas y preferencias personales viven únicamente en los JSON de `data/`.
- El auditor debe conservar los campos dinámicos ya enriquecidos y escribir el CSV con bloqueo, reemplazo atómico y copia anterior.
- El servidor debe permanecer ligero, sin dependencias y limitado a `127.0.0.1`.
- Las rutas para abrir carpetas se resuelven solo desde identificadores incluidos en el catálogo.
- GitHub automático requiere un remoto real; una URL manual validada vive en `project_overrides.json`.
- El historial exacto es append-only y central; la reconstrucción inicial debe etiquetarse como estimada.
- No publicar datos personales, financieros o societarios.
- No confundir madurez documentada, actividad detectada, avance documentado y estimación.
- No agregar equipos, avatares, chat, comentarios ni colaboración.

## Después de modificar

- Regenerar el CSV si cambió el auditor.
- Ejecutar las pruebas de historial, auditor y espacio personal.
- Servir la interfaz por HTTP y comprobar carga, navegación, formularios, proyecto individual, temas y responsive.
- Actualizar la documentación viva correspondiente.
