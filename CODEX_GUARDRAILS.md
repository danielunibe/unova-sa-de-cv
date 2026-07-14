# CODEX_GUARDRAILS.md

## Solicitud activa completada

- Convertir el catálogo vivo en `UNOVA Personal Work Manager`.
- Mantener el dashboard anterior dentro de `Proyectos`.
- Añadir plan personal, pipeline automático, espacios individuales, temas y accesos.
- Conservar 36 desarrollos iniciados y 32 no iniciados separados.
- Hacer la experiencia más simpática y comprensible, con sensación Monday.
- Convertir Proyectos en un dashboard gráfico real.

## Zonas protegidas

| Zona | Nivel | Regla |
|---|---|---|
| Raíces de proyectos C: y G: | Alto | Solo lectura excepto `UNOVA_PROJECT_STATUS.md` |
| Catálogo `data/proyectos.csv` | Alto | Solo auditor/historial; nunca tareas personales |
| JSON personales | Alto | No sobrescribirlos durante auditorías |
| Historial central | Alto | Append-only después de la línea base |
| Datos personales, financieros y societarios | Bloqueado | No publicar |
| API | Alto | Mantener en `127.0.0.1` |

## Reglas endurecidas

- La primera propuesta visual está aprobada y protegida.
- La segunda propuesta colorida queda descartada.
- Las nuevas gráficas deben usar datos reales; no inventar métricas decorativas.
- El lenguaje visible debe ser cotidiano. La terminología técnica puede permanecer en código y documentación interna, no como texto principal de la interfaz.
- Conservar la tabla de proyectos debajo de las gráficas.
- No agregar equipos, colaboración, chat, comentarios ni perfiles múltiples.
- No registrar eliminaciones cuando una unidad está desconectada.
- No contar dependencias, builds, cachés, backups, temporales ni fichas generadas.
- No inventar progreso de visión completa; usar `N/D`.
- No presentar actividad detectada como avance documentado.
- No declarar un proyecto terminado por tener código.
- Un remoto GitHub automático debe existir realmente.
- Una URL GitHub manual se valida y queda separada del catálogo.
- Las sugerencias no se convierten en tareas sin una acción explícita.
- El CSV debe usar bloqueo, reemplazo atómico y copia anterior válida.
- El auditor de catálogo debe preservar el enriquecimiento dinámico existente.
- No instalar paquetes ni servicios externos.

## Validación obligatoria

- Pruebas unitarias de auditor, historial y espacio personal.
- Regeneración real del CSV con 68 registros, 36 iniciados y 32 no iniciados.
- Comprobación de 3 repositorios GitHub detectados por remoto.
- Navegación, formularios, proyecto individual, temas y consola en navegador.
- Reproducción, pausa, velocidad, scrubber y navegación del timeline.
- Revisión visual de escritorio y móvil sin desbordamiento del documento.

## Rollback

- Detener `unova_server.py`.
- Restaurar archivos modificados desde una copia manual si se requiere.
- `data/proyectos.csv.bak` conserva la versión válida anterior.
- Las tareas personales permanecen separadas de las aplicaciones auditadas.
