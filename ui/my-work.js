import { icon } from "./icons.js";
import { focusItem, pageHeader, priorityLabel, projectBadge, taskRow } from "./components.js";
import { activeTasks, projectById, state } from "./state.js";
import { dueBucket, escapeHtml, formatDate, friendlySuggestionTitle, statusOrder, taskStatuses, todayIso } from "./utils.js";

function filteredTasks() {
  const term = state.search.toLocaleLowerCase("es");
  return activeTasks().filter((task) => {
    const project = projectById(task.project_id);
    return !term || `${task.title} ${project?.proyecto || ""} ${task.notes || ""}`.toLocaleLowerCase("es").includes(term);
  });
}

function taskGroup(status, tasks) {
  const meta = taskStatuses[status];
  if (!tasks.length) return "";
  return `
    <section class="task-group" style="--group-color:${meta.color}" data-task-group="${status}">
      <header class="task-group-header">
        <div class="task-group-title">${icon(meta.icon, 17)}<strong>${escapeHtml(meta.label)}</strong><span>${tasks.length}</span></div>
        <button class="icon-button" type="button" data-new-task-status="${status}" aria-label="Añadir tarea a ${escapeHtml(meta.label)}" data-tooltip="Añadir tarea">${icon("plus", 15)}</button>
      </header>
      <div class="table-scroll">
        <table class="task-table">
          <thead><tr><th>Tarea</th><th>Proyecto</th><th>Estado</th><th>Prioridad</th><th>Fecha</th><th>Origen</th><th>Acciones</th></tr></thead>
          <tbody>
            ${tasks.map((task) => taskRow(task, projectById(task.project_id), state.workspace.project_overrides?.[task.project_id])).join("")}
          </tbody>
        </table>
      </div>
    </section>`;
}

function suggestionsGroup(suggestions) {
  if (!suggestions.length) return "";
  return `
    <section class="task-group" style="--group-color:var(--teal)">
      <header class="task-group-header">
        <div class="task-group-title">${icon("sun", 17)}<strong>Ideas para avanzar</strong><span>${suggestions.length}</span></div>
        <span class="faint">Elige solo las que te sirvan</span>
      </header>
      <div class="table-scroll">
        <table class="suggestion-table">
          <thead><tr><th>Idea</th><th>Proyecto</th><th>Importancia</th><th>Acciones</th></tr></thead>
          <tbody>
            ${suggestions.map((suggestion) => {
              const project = projectById(suggestion.project_id);
              const override = state.workspace.project_overrides?.[suggestion.project_id] || {};
              return `<tr class="suggestion-row">
                <td><strong>${escapeHtml(friendlySuggestionTitle(suggestion.title))}</strong><small class="task-origin">${icon("badge-check", 14)}Sugerida al revisar el proyecto</small></td>
                <td><button class="project-link" type="button" data-open-project="${escapeHtml(project?.id || "")}"><span style="display:inline-flex;align-items:center;gap:7px">${projectBadge(project, override)}${escapeHtml(project?.proyecto || "Proyecto")}</span></button></td>
                <td>${priorityLabel(suggestion.priority || "low")}</td>
                <td><div class="row-actions">
                  <button class="icon-button" type="button" data-adopt-suggestion="${escapeHtml(suggestion.id)}" aria-label="Añadir a mis tareas" data-tooltip="Añadir a mis tareas">${icon("plus", 16)}</button>
                  <button class="icon-button" type="button" data-open-project="${escapeHtml(project?.id || "")}" aria-label="Ver proyecto" data-tooltip="Ver proyecto">${icon("chevron-right", 16)}</button>
                </div></td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>
      </div>
    </section>`;
}

export function renderMyWork() {
  const tasks = filteredTasks();
  const suggestions = (state.workspace.suggestions || [])
    .filter((item) => !state.search || `${item.title} ${projectById(item.project_id)?.proyecto || ""}`.toLocaleLowerCase("es").includes(state.search.toLocaleLowerCase("es")))
    .slice(0, 8);
  const today = tasks.filter((task) => dueBucket(task) === "today");
  const upcoming = tasks.filter((task) => dueBucket(task) === "upcoming");
  const blocked = tasks.filter((task) => task.status === "blocked");
  const done = tasks.filter((task) => task.status === "done");
  const agenda = [...tasks]
    .filter((task) => ["overdue", "today", "upcoming"].includes(dueBucket(task)) && task.status !== "done")
    .sort((a, b) => String(a.due_date).localeCompare(String(b.due_date)))
    .slice(0, 8);
  const dateLabel = new Intl.DateTimeFormat("es-MX", { weekday: "long", day: "numeric", month: "long" }).format(new Date());

  return `
    ${pageHeader("Mi trabajo", `Tu espacio personal · ${dateLabel}`, `
      <button class="secondary-button" type="button" data-nav="projects">${icon("layout", 16)} Ver dashboard</button>
    `)}
    <section class="focus-strip" aria-label="Resumen personal">
      ${focusItem("Para hoy", today.length, "tareas", "var(--blue)")}
      ${focusItem("Próximas", upcoming.length, "en los siguientes 7 días", "var(--purple)")}
      ${focusItem("En espera", blocked.length, "necesitan atención", "var(--coral)")}
      ${focusItem("Terminadas", done.length, "en tu plan", "var(--green)")}
    </section>
    <div class="work-layout">
      <div class="work-main">
        ${statusOrder.map((status) => taskGroup(status, tasks.filter((task) => task.status === status))).join("")}
        ${suggestionsGroup(suggestions)}
        ${!tasks.length && !suggestions.length ? `
          <section class="panel empty-state">
            ${icon("check-square", 30)}
            <h2>Tu plan está vacío</h2>
            <p>Crea tu primera tarea o revisa las ideas que encontramos en tus proyectos.</p>
            <button class="primary-button" type="button" data-new-task>${icon("plus", 16)} Nueva tarea</button>
          </section>` : ""}
      </div>
      <aside class="panel panel-pad agenda-panel">
        <div class="panel-heading"><div><h3>Hoy y próximas</h3><p>Tu foco inmediato.</p></div>${icon("calendar", 18)}</div>
        <div class="agenda-list">
          ${agenda.length ? agenda.map((task) => {
            const project = projectById(task.project_id);
            const meta = taskStatuses[task.status] || taskStatuses.next;
            return `<button class="agenda-item task-title-button" type="button" data-edit-task="${escapeHtml(task.id)}">
              <span class="agenda-dot" style="--item-color:${meta.color}"></span>
              <span><strong>${escapeHtml(task.title)}</strong><small>${escapeHtml(project?.proyecto || "Proyecto")} · ${formatDate(task.due_date)}</small></span>
            </button>`;
          }).join("") : `<div class="empty-state" style="min-height:150px;padding:12px">${icon("calendar", 24)}<p>No tienes fechas próximas.</p></div>`}
        </div>
      </aside>
    </div>`;
}
