import { icon } from "./icons.js";
import { eventItem, pageHeader } from "./components.js";
import { state } from "./state.js";
import { escapeHtml, formatDate } from "./utils.js";

export function filteredActivityEvents() {
  return state.events.filter((event) =>
    (!state.activityProject || event.project_id === state.activityProject)
    && (!state.activityType || event.event_type === state.activityType)
  );
}

export function renderActivity() {
  const projects = [...state.projects].sort((a, b) => a.proyecto.localeCompare(b.proyecto, "es"));
  const events = filteredActivityEvents();
  const playbackEvents = events.slice(0, 350).reverse();
  const maxCursor = Math.max(0, playbackEvents.length - 1);
  state.activityCursor = Math.min(Math.max(0, state.activityCursor), maxCursor);
  const current = playbackEvents[state.activityCursor];
  return `
    ${pageHeader("Actividad", "Recuerda qué proyectos tocaste y cuándo.", "")}
    <section class="panel projects-panel">
      <div class="projects-toolbar">
        <label class="field" style="display:flex;align-items:center;gap:7px"><span class="sr-only">Proyecto</span>
          <select id="activityProjectFilter">
            <option value="">Todos los proyectos</option>
            ${projects.map((project) => `<option value="${escapeHtml(project.id)}" ${state.activityProject === project.id ? "selected" : ""}>${escapeHtml(project.proyecto)}</option>`).join("")}
          </select>
        </label>
        <label class="field" style="display:flex;align-items:center;gap:7px"><span class="sr-only">Tipo</span>
          <select id="activityTypeFilter">
            <option value="">Todos los eventos</option>
            <option value="file_change" ${state.activityType === "file_change" ? "selected" : ""}>Archivos actualizados</option>
            <option value="historical_activity" ${state.activityType === "historical_activity" ? "selected" : ""}>Actividad anterior</option>
            <option value="localhost_started" ${state.activityType === "localhost_started" ? "selected" : ""}>Proyecto abierto</option>
            <option value="localhost_stopped" ${state.activityType === "localhost_stopped" ? "selected" : ""}>Proyecto cerrado</option>
          </select>
        </label>
        <span class="faint">${events.length} eventos</span>
      </div>
      <div class="activity-player">
        <div class="activity-player-controls">
          <button class="icon-button" type="button" data-activity-step="-1" aria-label="Evento anterior" data-tooltip="Anterior" ${!playbackEvents.length || state.activityCursor === 0 ? "disabled" : ""}>${icon("chevron-left", 16)}</button>
          <button class="primary-button activity-play-button" type="button" data-activity-play aria-label="${state.activityPlaying ? "Pausar reproducción" : "Reproducir actividad"}" ${!playbackEvents.length ? "disabled" : ""}>
            ${icon(state.activityPlaying ? "pause" : "play", 16)}
            <span>${state.activityPlaying ? "Pausar" : "Reproducir"}</span>
          </button>
          <button class="icon-button" type="button" data-activity-step="1" aria-label="Evento siguiente" data-tooltip="Siguiente" ${!playbackEvents.length || state.activityCursor >= maxCursor ? "disabled" : ""}>${icon("chevron-right", 16)}</button>
          <label class="activity-speed">Velocidad
            <select id="activitySpeed">
              ${[0.5, 1, 2, 4].map((speed) => `<option value="${speed}" ${Number(state.activitySpeed) === speed ? "selected" : ""}>${speed}×</option>`).join("")}
            </select>
          </label>
        </div>
        <label class="activity-scrubber">
          <span>${current ? `${state.activityCursor + 1} de ${playbackEvents.length}` : "Sin eventos"}</span>
          <input id="activityCursor" type="range" min="0" max="${maxCursor}" value="${state.activityCursor}" ${!playbackEvents.length ? "disabled" : ""} aria-label="Posición de reproducción">
        </label>
        <div class="activity-now">
          ${current ? `${eventItem(current, { current: true })}` : '<p class="faint">No hay eventos disponibles para reproducir.</p>'}
        </div>
      </div>
      <div class="panel-pad timeline">${events.slice(0, 350).map(eventItem).join("") || '<div class="empty-state"><p>Sin eventos para estos filtros.</p></div>'}</div>
    </section>`;
}

function auditRow(label, value, className = "") {
  return `<div class="audit-row"><span>${escapeHtml(label)}</span><strong class="${className}">${escapeHtml(value)}</strong></div>`;
}

export function renderAudit() {
  const monitor = state.monitor;
  const lastScan = monitor.last_scan || {};
  const history = monitor.history || {};
  const audit = state.audit.meta || {};
  const disconnected = lastScan.history?.disconnected_projects || lastScan.disconnected_projects || [];
  const errors = lastScan.history?.errors || lastScan.errors || [];
  return `
    ${pageHeader("Estado", "Comprueba que tus proyectos se están revisando correctamente.", `
      <button class="secondary-button" type="button" data-refresh>${icon("refresh", 16)} Revisar ahora</button>
    `)}
    <section class="audit-grid">
      <article class="panel panel-pad">
        <div class="panel-heading"><div><h3>Estado de la aplicación</h3><p>La revisión automática y las apps abiertas.</p></div><strong class="${monitor.state === "error" ? "health-bad" : "health-good"}">${monitor.state === "error" ? "Revisar" : monitor.state === "scanning" ? "Revisando" : "Todo bien"}</strong></div>
        <div class="audit-list">
          ${auditRow("Aplicación local", "Conectada")}
          ${auditRow("Última revisión", formatDate(history.last_scan_at || lastScan.completed_at, true))}
          ${auditRow("Proyectos abiertos", monitor.localhost?.listeners?.length ?? monitor.localhost?.count ?? 0)}
          ${auditRow("Próxima revisión completa", "Hoy a las 23:30")}
        </div>
      </article>
      <article class="panel panel-pad">
        <div class="panel-heading"><div><h3>Carpetas revisadas</h3><p>Si un disco se desconecta, conservamos la información anterior.</p></div>${icon("shield", 18)}</div>
        <div class="audit-list">
          ${auditRow("Voyager", disconnected.length ? "Revisar conexión" : "Disponible", disconnected.length ? "health-bad" : "health-good")}
          ${auditRow("Carpetas Voyager", audit.voyager_project_folders_scanned ?? "—")}
          ${auditRow("Desarrollos C:", audit.dev_folders_scanned ?? "—")}
          ${auditRow("Carpetas no disponibles", disconnected.length)}
        </div>
      </article>
      <article class="panel panel-pad">
        <div class="panel-heading"><div><h3>Información disponible</h3><p>Qué tan fácil será entender y retomar cada proyecto.</p></div>${icon("file-text", 18)}</div>
        <div class="audit-list">
          ${auditRow("Con documentación", `${state.stats.documentation_coverage?.with_documentation || 0}/${state.stats.total || 0}`)}
          ${auditRow("Con siguiente paso", `${state.stats.documentation_coverage?.with_next_step || 0}/${state.stats.total || 0}`)}
          ${auditRow("Con meta completa definida", `${state.stats.documentation_coverage?.with_vision_progress || 0}/${state.stats.total || 0}`)}
          ${auditRow("Información muy clara", `${state.stats.documentation_coverage?.high_progress_confidence || 0}/${state.stats.total || 0}`)}
        </div>
      </article>
      <article class="panel panel-pad">
        <div class="panel-heading"><div><h3>Problemas recientes</h3><p>Si algo falla, tus datos anteriores siguen disponibles.</p></div><strong>${errors.length + (monitor.last_error ? 1 : 0)}</strong></div>
        ${errors.length || monitor.last_error ? `<div class="audit-list">${errors.map((error) => auditRow(error.project_id, error.error, "health-bad")).join("")}${monitor.last_error ? auditRow("Monitor", monitor.last_error, "health-bad") : ""}</div>` : '<p class="health-good">No hay errores registrados en la última ejecución.</p>'}
      </article>
    </section>`;
}

export function renderSettings() {
  const settings = state.workspace.settings || {};
  return `
    ${pageHeader("Configuración", "Preferencias del gestor personal. No modifican tus proyectos.", "")}
    <section class="settings-grid">
      <article class="panel panel-pad">
        <div class="panel-heading"><div><h3>Apariencia</h3><p>La misma composición en claro y oscuro.</p></div>${icon("palette", 18)}</div>
        <div class="setting-row">
          <div><strong>Tema</strong><p>Automático sigue la configuración de Windows.</p></div>
          <div class="theme-options">
            ${[["light", "sun", "Claro"], ["dark", "moon", "Oscuro"], ["system", "monitor", "Automático"]].map(([id, symbol, label]) => `
              <button class="theme-option ${settings.theme === id ? "is-active" : ""}" type="button" data-theme-choice="${id}">${icon(symbol, 17)}${label}</button>
            `).join("")}
          </div>
        </div>
        <div class="setting-row">
          <div><strong>Densidad</strong><p>Ajusta el espacio vertical de tablas y controles.</p></div>
          <select id="densitySetting"><option value="comfortable" ${settings.density === "comfortable" ? "selected" : ""}>Cómoda</option><option value="compact" ${settings.density === "compact" ? "selected" : ""}>Compacta</option></select>
        </div>
        <div class="setting-row">
          <div><strong>Vista inicial</strong><p>Se abrirá al iniciar el dashboard.</p></div>
          <select id="startViewSetting">
            <option value="my-work" ${settings.start_view === "my-work" ? "selected" : ""}>Mi trabajo</option>
            <option value="projects" ${settings.start_view === "projects" ? "selected" : ""}>Proyectos</option>
            <option value="activity" ${settings.start_view === "activity" ? "selected" : ""}>Actividad</option>
            <option value="audit" ${settings.start_view === "audit" ? "selected" : ""}>Estado</option>
          </select>
        </div>
      </article>
      <aside class="panel panel-pad">
        <div class="panel-heading"><div><h3>Tu información está protegida</h3><p>Las tareas personales no cambian los archivos de tus proyectos.</p></div>${icon("shield", 18)}</div>
        <div class="audit-list">
          ${auditRow("Lista de proyectos", "Se actualiza sola")}
          ${auditRow("Mis tareas", "Solo tú las cambias")}
          ${auditRow("Avance por etapas", "Se calcula solo")}
          ${auditRow("Carpetas originales", "No se modifican")}
        </div>
      </aside>
    </section>`;
}
