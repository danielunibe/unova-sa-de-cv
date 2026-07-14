import { icon } from "./icons.js";
import { eventItem, suggestionRow, taskRow } from "./components.js";
import { state } from "./state.js";
import { categoryIcon, escapeHtml, formatDate, projectColor, safeText, taskStatuses } from "./utils.js";

const stageColors = {
  definicion: "var(--blue)",
  diseno: "var(--purple)",
  arquitectura: "var(--teal)",
  implementacion: "var(--primary)",
  pruebas: "var(--amber)",
  empaquetado: "#b779d0",
  continuidad: "var(--coral)",
  validacion: "var(--green)",
};
const stageLabels = {
  definicion: "Idea clara",
  diseno: "Diseño",
  arquitectura: "Estructura",
  implementacion: "Construcción",
  pruebas: "Pruebas",
  empaquetado: "Preparación",
  continuidad: "Seguimiento",
  validacion: "Revisión final",
};

function friendlyEvidence(stage) {
  const messages = {
    definicion: "La idea, el problema y para quién es están descritos.",
    diseno: "Se revisaron diseños, imágenes y materiales visuales.",
    arquitectura: "Se revisó cómo está organizado el proyecto.",
    implementacion: "Se revisaron los archivos donde se está construyendo la aplicación.",
    pruebas: "Se buscaron pruebas y comprobaciones del funcionamiento.",
    empaquetado: "Se revisó si ya puede prepararse para instalarse o compartirse.",
    continuidad: "Se buscó un próximo paso claro para poder retomarlo.",
    validacion: "Se revisó si existe una comprobación final del resultado.",
  };
  return messages[stage.key] || stage.evidence;
}

function friendlySource(stage) {
  const sources = {
    definicion: "descripción y documentos del proyecto",
    diseno: "diseños, imágenes y documentos",
    arquitectura: "organización de carpetas y archivos",
    implementacion: "archivos donde se construye la aplicación",
    pruebas: "pruebas y comprobaciones encontradas",
    empaquetado: "formas de instalar o compartir el proyecto",
    continuidad: "notas, pendientes y siguiente paso",
    validacion: "pruebas y revisiones finales",
  };
  return sources[stage.key] || "archivos del proyecto";
}

function pipelineStrip(detail) {
  return `
    <section class="panel pipeline-panel">
      <div class="panel-heading">
        <div><h3>Camino del proyecto</h3><p>Ocho pasos sencillos para saber qué está listo y qué falta.</p></div>
        <span class="pipeline-meta">${icon("badge-check", 15)} Se actualiza solo ${icon("info", 14)}</span>
      </div>
      <div class="pipeline">
        ${detail.pipeline.map((stage) => {
          const color = stageColors[stage.key] || "var(--primary)";
          const width = Math.round(stage.value * 100 / stage.maximum);
          const stateIcon = stage.status === "completed" ? "check" : stage.status === "partial" ? "activity" : "circle";
          return `
            <button class="pipeline-stage ${stage.status === "pending" ? "is-pending" : ""}" type="button" data-project-tab="pipeline" style="--stage-color:${color}" title="${escapeHtml(friendlyEvidence(stage))}">
              <span class="pipeline-stage-head">${icon(stage.icon, 16)}${icon(stateIcon, 14)}</span>
              <strong>${escapeHtml(stageLabels[stage.key] || stage.label)}</strong>
              <div class="pipeline-meter"><i style="width:${width}%"></i></div>
              <small>${width}% · ${stage.status === "completed" ? "listo" : stage.status === "partial" ? "en progreso" : "por empezar"}</small>
            </button>`;
        }).join("")}
      </div>
    </section>`;
}

function planTable(detail, includeSuggestions = true) {
  const project = detail.project;
  const override = detail.preferences || {};
  const tasks = detail.tasks || [];
  const suggestions = includeSuggestions ? detail.suggestions || [] : [];
  return `
    <section class="panel projects-panel">
      <div class="panel-heading panel-pad">
        <div><h3>Mis tareas</h3><p>Tu lista personal para seguir avanzando cuando vuelvas al proyecto.</p></div>
        <button class="primary-button" type="button" data-new-task-project="${escapeHtml(project.id)}">${icon("plus", 16)} Añadir tarea</button>
      </div>
      ${tasks.length || suggestions.length ? `
        <div class="table-scroll">
          <table class="task-table">
            <thead><tr><th>Tarea</th><th>Proyecto</th><th>Estado</th><th>Prioridad</th><th>Fecha</th><th>Origen</th><th>Acciones</th></tr></thead>
            <tbody>
              ${tasks.map((task) => taskRow(task, project, override)).join("")}
              ${suggestions.map((item) => suggestionRow(item, project, override)).join("")}
            </tbody>
          </table>
        </div>` : `
        <div class="empty-state">
          ${icon("check-square", 28)}
          <h3>Sin tareas personales</h3>
          <p>Crea el siguiente paso que quieres ejecutar en este proyecto.</p>
          <button class="primary-button" type="button" data-new-task-project="${escapeHtml(project.id)}">${icon("plus", 16)} Crear primera tarea</button>
        </div>`}
    </section>`;
}

function summaryView(detail) {
  const project = detail.project;
  const nextTask = (detail.tasks || []).find((task) => ["in_progress", "next"].includes(task.status));
  const lastEvent = detail.events?.[0];
  return `
    ${pipelineStrip(detail)}
    <div class="project-overview">
      ${planTable(detail)}
      <aside class="project-side">
        <section class="info-panel" style="--item-color:var(--primary)">
          <span class="faint">SIGUIENTE PASO</span>
          <h3>${escapeHtml(nextTask?.title || safeText(project.proximo_paso, "Define tu siguiente tarea"))}</h3>
          <p>${nextTask ? `${taskStatuses[nextTask.status]?.label || "Plan personal"} · ${nextTask.due_date ? formatDate(nextTask.due_date) : "sin fecha"}` : "El proyecto no tiene un próximo paso personal activo."}</p>
        </section>
        <section class="info-panel" style="--item-color:var(--teal)">
          <span class="faint">ÚLTIMO AVANCE DETECTADO</span>
          <h3>${escapeHtml(lastEvent ? formatDate(lastEvent.timestamp, true) : formatDate(project.ultimo_cambio, true))}</h3>
          <p>${escapeHtml(lastEvent?.event_type === "file_change" ? `${lastEvent.added || 0} archivos nuevos · ${lastEvent.modified || 0} actualizados` : safeText(project.ultimo_avance_documentado, "Hay movimiento reciente, pero falta escribir un resumen."))}</p>
        </section>
        <section class="info-panel" style="--item-color:var(--blue)">
          <span class="faint">ACCESOS</span>
          <div class="access-list">
            <button class="secondary-button" type="button" data-open-folder="${escapeHtml(project.id)}" ${detail.folder_available ? "" : "disabled"}>${icon("folder", 16)} Carpeta</button>
            <button class="secondary-button" type="button" data-open-github="${escapeHtml(project.id)}" ${detail.github_url ? "" : "disabled"}>${icon("github", 16)} GitHub</button>
          </div>
          ${!detail.github_url ? `<button class="danger-text-button" type="button" data-project-settings="${escapeHtml(project.id)}">${icon("plus", 14)} Vincular repositorio</button>` : ""}
        </section>
      </aside>
    </div>`;
}

function pipelineView(detail) {
  return `
    <section class="pipeline-detail-list">
      ${detail.pipeline.map((stage) => {
        const color = stageColors[stage.key] || "var(--primary)";
        const statusLabel = stage.status === "completed" ? "Completada" : stage.status === "partial" ? "Parcial" : "Pendiente";
        const statusColor = stage.status === "completed" ? "var(--green)" : stage.status === "partial" ? "var(--amber)" : "var(--text-faint)";
        return `
          <article class="pipeline-detail" style="--stage-color:${color}">
            <span class="pipeline-detail-icon">${icon(stage.icon, 19)}</span>
            <div>
              <h3>${escapeHtml(stageLabels[stage.key] || stage.label)}</h3>
              <p>${escapeHtml(friendlyEvidence(stage))}</p>
              <small class="pipeline-source">${icon("file-text", 13)} Revisado en: ${escapeHtml(friendlySource(stage))}</small>
            </div>
            <div style="text-align:right">
              <span class="pipeline-status" style="--pipeline-status-color:${statusColor}">${escapeHtml(statusLabel)}</span>
              <small class="faint" style="display:block;margin-top:4px">${Math.round(stage.value * 100 / stage.maximum)}% · certeza ${escapeHtml(stage.confidence).toLowerCase()}</small>
            </div>
          </article>`;
      }).join("")}
    </section>`;
}

function activityView(detail) {
  return `
    <section class="panel panel-pad">
      <div class="panel-heading"><div><h3>Cambios del proyecto</h3><p>Una bitácora sencilla de lo que se ha movido.</p></div><strong>${detail.events.length}</strong></div>
      <div class="timeline">${detail.events.length ? detail.events.map(eventItem).join("") : '<div class="empty-state"><p>Sin eventos registrados.</p></div>'}</div>
    </section>`;
}

function documentsView(detail) {
  const documents = String(detail.project.documentos_principales || "").split(";").map((item) => item.trim()).filter(Boolean);
  return `
    <section class="panel projects-panel">
      <div class="panel-heading panel-pad"><div><h3>Archivos importantes</h3><p>Documentos útiles para entender y retomar el proyecto.</p></div><strong>${documents.length}</strong></div>
      <div class="table-scroll">
        <table>
          <thead><tr><th>Documento</th><th>Ruta</th><th>Uso</th></tr></thead>
          <tbody>
            ${documents.map((path) => `<tr><td><strong>${escapeHtml(path.split("\\").pop())}</strong></td><td class="mono">${escapeHtml(path)}</td><td><span class="task-origin">${icon("file-text", 14)}Referencia</span></td></tr>`).join("") || '<tr><td colspan="3">Todavía no se encontraron documentos importantes.</td></tr>'}
          </tbody>
        </table>
      </div>
    </section>`;
}

export function renderProjectWorkspace() {
  const detail = state.projectDetail;
  if (!detail) {
    return `<div class="loading-screen"><span class="loading-mark"></span><strong>Cargando proyecto…</strong></div>`;
  }
  const project = detail.project;
  const override = detail.preferences || {};
  const color = projectColor(project, override);
  const progress = Number(project.progreso_mvp || 0);
  const tabs = [
    ["summary", "Resumen"],
    ["tasks", "Tareas"],
    ["pipeline", "Avance"],
    ["activity", "Actividad"],
    ["documents", "Documentos"],
  ];
  const body = state.projectTab === "tasks"
    ? planTable(detail)
    : state.projectTab === "pipeline"
      ? pipelineView(detail)
      : state.projectTab === "activity"
        ? activityView(detail)
        : state.projectTab === "documents"
          ? documentsView(detail)
          : summaryView(detail);

  return `
    <header class="project-header">
      <button class="icon-button" type="button" data-nav="projects" aria-label="Volver a proyectos" data-tooltip="Volver">${icon("arrow-left", 18)}</button>
      <div>
        <div class="project-title-row" style="color:${color}">${icon(override.icon || categoryIcon(project), 22)}<h1 style="color:var(--text)">${escapeHtml(project.proyecto)}</h1></div>
        <p>${escapeHtml(project.categoria)}${project.subcategoria ? ` · ${escapeHtml(project.subcategoria)}` : ""}</p>
        <div class="project-progress"><i><b style="width:${progress}%"></b></i><strong>${progress}% primera versión</strong><span class="faint">· meta completa ${project.progreso_vision === "N/D" ? "por definir" : `${project.progreso_vision}%`}</span></div>
      </div>
      <div class="project-actions">
        <button class="icon-button" type="button" data-open-folder="${escapeHtml(project.id)}" aria-label="Abrir carpeta raíz" data-tooltip="Abrir carpeta raíz" ${detail.folder_available ? "" : "disabled"}>${icon("folder", 17)}</button>
        <button class="icon-button" type="button" data-open-github="${escapeHtml(project.id)}" aria-label="Abrir GitHub" data-tooltip="${detail.github_url ? "Abrir GitHub" : "GitHub no vinculado"}" ${detail.github_url ? "" : "disabled"}>${icon("github", 17)}</button>
        <button class="icon-button" type="button" data-project-settings="${escapeHtml(project.id)}" aria-label="Configurar accesos" data-tooltip="Configurar proyecto">${icon("more-horizontal", 17)}</button>
      </div>
    </header>
    <nav class="project-tabs" aria-label="Secciones del proyecto">
      ${tabs.map(([id, label]) => `<button class="project-tab ${state.projectTab === id ? "is-active" : ""}" type="button" data-project-tab="${id}">${label}</button>`).join("")}
    </nav>
    ${body}`;
}
