import { icon } from "./icons.js";
import {
  escapeHtml,
  friendlySuggestionTitle,
  formatDate,
  priorities,
  projectColor,
  taskStatuses,
} from "./utils.js";

export function pageHeader(title, subtitle, actions = "") {
  return `
    <header class="page-header">
      <div><h1>${escapeHtml(title)}</h1><p>${escapeHtml(subtitle)}</p></div>
      <div class="page-actions">${actions}</div>
    </header>`;
}

export function focusItem(label, value, note, color) {
  return `
    <article class="focus-item" style="--item-color:${color}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
      <small>${escapeHtml(note)}</small>
    </article>`;
}

export function statusCell(status, editable = false, taskId = "") {
  const meta = taskStatuses[status] || taskStatuses.next;
  if (!editable) {
    return `<span class="status-cell" style="--status-color:${meta.color}">${escapeHtml(meta.label)}</span>`;
  }
  return `
    <select class="status-cell" data-task-status="${escapeHtml(taskId)}" style="--status-color:${meta.color}" aria-label="Estado de tarea">
      ${Object.entries(taskStatuses).map(([value, item]) => `
        <option value="${value}" ${value === status ? "selected" : ""}>${escapeHtml(item.label)}</option>
      `).join("")}
    </select>`;
}

export function priorityLabel(priority) {
  const meta = priorities[priority] || priorities.medium;
  return `<span class="priority" style="--priority-color:${meta.color}">${icon("flag", 15)}${escapeHtml(meta.label)}</span>`;
}

export function projectBadge(project, override = {}) {
  const color = projectColor(project, override);
  return `<span class="agenda-dot" style="--item-color:${color}"></span>`;
}

export function taskRow(task, project, override = {}) {
  const hasGithub = Boolean(override.github_url || project?.github_url);
  return `
    <tr draggable="true" data-task-row="${escapeHtml(task.id)}">
      <td>
        <div style="display:flex;align-items:center;gap:9px">
          <input class="task-check" type="checkbox" data-task-complete="${escapeHtml(task.id)}" ${task.status === "done" ? "checked" : ""} aria-label="Marcar tarea como terminada">
          <button class="task-title-button" type="button" data-edit-task="${escapeHtml(task.id)}">${escapeHtml(task.title)}</button>
        </div>
      </td>
      <td>
        <button class="project-link" type="button" data-open-project="${escapeHtml(project?.id || "")}">
          <span style="display:inline-flex;align-items:center;gap:7px">${projectBadge(project, override)}${escapeHtml(project?.proyecto || "Proyecto")}</span>
        </button>
      </td>
      <td>${statusCell(task.status, true, task.id)}</td>
      <td>${priorityLabel(task.priority)}</td>
      <td class="nowrap">${task.due_date ? escapeHtml(formatDate(task.due_date)) : '<span class="faint">Sin fecha</span>'}</td>
      <td><span class="task-origin">${icon(task.origin === "suggested" ? "badge-check" : "edit", 14)}${task.origin === "suggested" ? "Sugerida" : "Manual"}</span></td>
      <td>
        <div class="row-actions">
          <button class="icon-button" type="button" data-open-folder="${escapeHtml(project?.id || "")}" aria-label="Abrir carpeta" data-tooltip="Abrir carpeta">${icon("folder", 16)}</button>
          <button class="icon-button" type="button" data-open-github="${escapeHtml(project?.id || "")}" aria-label="Abrir GitHub" data-tooltip="${hasGithub ? "Abrir GitHub" : "GitHub no vinculado"}" ${hasGithub ? "" : "disabled"}>${icon("github", 16)}</button>
          <button class="icon-button" type="button" data-edit-task="${escapeHtml(task.id)}" aria-label="Editar tarea" data-tooltip="Editar tarea">${icon("edit", 16)}</button>
        </div>
      </td>
    </tr>`;
}

export function suggestionRow(suggestion, project, override = {}) {
  return `
    <tr class="suggestion-row">
      <td><strong>${escapeHtml(friendlySuggestionTitle(suggestion.title))}</strong><small class="task-origin">${icon("badge-check", 14)}Sugerida al revisar el proyecto</small></td>
      <td>
        <button class="project-link" type="button" data-open-project="${escapeHtml(project?.id || "")}">
          <span style="display:inline-flex;align-items:center;gap:7px">${projectBadge(project, override)}${escapeHtml(project?.proyecto || "Proyecto")}</span>
        </button>
      </td>
      <td>${statusCell("next")}</td>
      <td>${priorityLabel(suggestion.priority || "low")}</td>
      <td><span class="faint">Sin fecha</span></td>
      <td><span class="task-origin">${icon("badge-check", 14)}Sugerida</span></td>
      <td>
        <div class="row-actions">
          <button class="icon-button" type="button" data-adopt-suggestion="${escapeHtml(suggestion.id)}" aria-label="Convertir en tarea" data-tooltip="Añadir a mi plan">${icon("plus", 16)}</button>
          <button class="icon-button" type="button" data-open-project="${escapeHtml(project?.id || "")}" aria-label="Abrir proyecto" data-tooltip="Abrir proyecto">${icon("chevron-right", 16)}</button>
        </div>
      </td>
    </tr>`;
}

export function eventItem(event, { current = false } = {}) {
  const labels = {
    file_change: "Se actualizaron archivos",
    historical_activity: "Actividad anterior",
    localhost_started: "Se abrió el proyecto",
    localhost_stopped: "Se cerró el proyecto",
  };
  const summary = event.event_type === "file_change"
    ? `${event.added || 0} añadidos · ${event.modified || 0} modificados · ${event.deleted || 0} eliminados`
    : event.event_type?.startsWith("localhost")
      ? "Sesión de trabajo"
      : `${event.modified || 0} archivos con movimiento`;
  return `
    <div class="timeline-item ${event.precision === "estimated" ? "is-estimated" : ""} ${current ? "is-current" : ""}">
      <span class="timeline-marker"></span>
      <div class="timeline-copy">
        <small>${escapeHtml(formatDate(event.timestamp, true))} · ${event.precision === "estimated" ? "fecha aproximada" : "registrado"}</small>
        <strong>${escapeHtml(event.project || "Proyecto")}</strong>
        <span>${escapeHtml(labels[event.event_type] || event.event_type)} — ${escapeHtml(summary)}</span>
      </div>
    </div>`;
}
