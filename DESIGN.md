# DESIGN.md

## Identidad visual confirmada

- Referencia aprobada: primera propuesta, limpia, equilibrada y con color funcional sin saturación.
- Referencias de evolución: dashboard claro tipo Monday aportado el 20 de junio de 2026 y familia de gráficas redondeadas aportada en la misma revisión.
- Sensación: gestor personal calmado inspirado en la claridad de Monday, sin copiar su identidad.
- Fondo blanco o gris frío, superficies claras, acento índigo y colores semánticos contenidos.
- Modo oscuro: adaptación tonal de la misma composición; no una propuesta distinta.
- Sin gradientes, glassmorphism, hero comercial, gráficos decorativos ni saturación.

## Navegación confirmada

- `Mi trabajo`: plan personal agrupado, sugerencias y agenda.
- `Proyectos`: dashboard gráfico, lista completa y caja inferior de ideas no iniciadas.
- `Actividad`: timeline filtrable con reproducción.
- `Estado`: revisión automática, carpetas e información disponible.
- `Configuración`: tema, vista inicial y densidad.

## Dashboard de proyectos

- Cuatro indicadores: todos, en marcha, ideas y avance promedio.
- Gráfica de líneas: cambios registrados y actividad anterior.
- Gráfica de dona: proyectos en marcha frente a ideas.
- Barras horizontales: avance promedio por ocho etapas.
- Burbujas: distribución por tipo de proyecto.
- Las gráficas usan únicamente datos reales del catálogo, progreso e historial.
- La lista detallada permanece debajo de las gráficas.

## Espacio individual de proyecto

- Cabecera con progreso MVP, visión completa y accesos de carpeta/GitHub.
- Pestañas: Resumen, Tareas, Pipeline, Actividad y Documentos.
- Pipeline horizontal de ocho etapas.
- Estados del pipeline: `Completada`, `Parcial` y `Pendiente`.
- Cada etapa expone evidencia, fuente y confianza.
- Plan personal separado y nunca sobrescrito por una auditoría.

## Componentes confirmados

- Tabla agrupada como componente dominante.
- Encabezados de tabla en lenguaje natural, sin mayúsculas técnicas.
- Estados de tarea: Siguiente, En curso, Bloqueado, En revisión y Terminado.
- Iconos SVG outline de 18 px aproximados.
- Tooltips en escritorio; `aria-label` y foco visible en controles icónicos.
- Caja independiente para 32 ideas y proyectos no iniciados.
- Timeline con diferencia visible entre exacto y estimado.
- Reproductor temporal con anterior, reproducir/pausar, siguiente, scrubber y velocidades 0.5×–4×.
- Modal ligero para tareas y modal separado para preferencias de proyecto.
- Términos visibles preferidos: `Camino del proyecto`, `Primera versión`, `En marcha`, `Estado`, `Ideas para avanzar`.
- Evitar en la interfaz principal: `pipeline`, `MVP`, `auditoría`, `evidencia`, `exacto`, `canónico` y `localhost`.

## Tokens

- Acento: índigo `#5b5bd6`.
- Fondo claro: gris frío muy suave.
- Superficie clara: blanco.
- Texto: azul negro de alto contraste.
- Estados: azul, violeta, coral, ámbar y verde, usados con moderación.
- Radio base: 8–10 px.
- Sombras: mínimas; la estructura depende principalmente de borde y espaciado.

## Responsive

- Escritorio: sidebar completa, tabla + agenda y espacios amplios.
- Tablet: sidebar compacta.
- Móvil: navegación inferior, indicadores 2×2, gráficas apiladas y tablas con scroll interno.
- El documento no debe tener desbordamiento horizontal.

## Decisiones descartadas

- Segunda propuesta más colorida: descartada.
- Colaboración, usuarios, equipos, avatares, comentarios y chat: fuera de producto.
