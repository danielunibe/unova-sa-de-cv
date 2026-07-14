import { icon } from "./icons.js";
import { pageHeader } from "./components.js";
import {
  activityChart,
  categoryBubbleChart,
  dashboardStat,
  projectDonut,
  stageProgressChart,
} from "./dashboard-charts.js";
import { state } from "./state.js";
import { categoryIcon, escapeHtml, projectColor, relativeDate, safeText } from "./utils.js";

function projectRows(projects) {
  return projects.map((project) => {
    const override = state.workspace.project_overrides?.[project.id] || {};
    const color = projectColor(project, override);
    const value = Number(project.progreso_mvp || 0);
    const hasGithub = Boolean(override.github_url || project.github_url);
    return `
      <tr data-project-row="${escapeHtml(project.id)}">
        <td>
          <button class="project-link" type="button" data-open-project="${escapeHtml(project.id)}">
            <span style="display:inline-flex;align-items:center;gap:8px;color:${color}">${icon(override.icon || categoryIcon(project), 17)}<strong style="color:var(--text)">${escapeHtml(project.proyecto)}</strong></span>
          </button>
          <small class="faint">${escapeHtml(project.subcategoria || project.tipo || "")}</small>
        </td>
        <td>${escapeHtml(project.categoria)}</td>
        <td><span class="status-cell" style="--status-color:${project.grupo_operativo === "iniciado" ? "var(--green)" : "var(--text-faint)"}">${project.grupo_operativo === "iniciado" ? "En marcha" : "Idea"}</span></td>
        <td><div class="progress-inline"><i><b style="width:${value}%"></b></i><strong>${value}%</strong></div></td>
        <td>${escapeHtml(safeText(project.proximo_paso, "Sin definir"))}</td>
        <td>${escapeHtml(relativeDate(project.ultimo_cambio))}</td>
        <td>
          <div class="row-actions">
            <button class="icon-button" type="button" data-open-folder="${escapeHtml(project.id)}" aria-label="Abrir carpeta" data-tooltip="Abrir carpeta">${icon("folder", 16)}</button>
            <button class="icon-button" type="button" data-open-github="${escapeHtml(project.id)}" aria-label="Abrir GitHub" data-tooltip="${hasGithub ? "Abrir GitHub" : "GitHub no vinculado"}" ${hasGithub ? "" : "disabled"}>${icon("github", 16)}</button>
            <button class="icon-button" type="button" data-open-project="${escapeHtml(project.id)}" aria-label="Abrir proyecto" data-tooltip="Abrir espacio">${icon("chevron-right", 16)}</button>
          </div>
        </td>
      </tr>`;
  }).join("");
}

export function renderProjects() {
  const term = state.search.toLocaleLowerCase("es");
  const all = state.projects.filter((project) =>
    !term || `${project.proyecto} ${project.categoria} ${project.stack} ${project.proposito}`.toLocaleLowerCase("es").includes(term)
  );
  const started = all.filter((project) => project.grupo_operativo === "iniciado");
  const ideas = all.filter((project) => project.grupo_operativo === "no_iniciado");
  const recent = all.filter((project) => {
    const date = new Date(project.ultimo_cambio || project.ultima_actividad || 0);
    return Date.now() - date.getTime() <= 30 * 86_400_000;
  });
  const average = all.length ? Math.round(all.reduce((sum, project) => sum + Number(project.progreso_mvp || 0), 0) / all.length) : 0;

  return `
    ${pageHeader("Dashboard de proyectos", "Una vista clara de lo que está avanzando y lo que necesita atención.", `
      <button class="secondary-button" type="button" data-export-csv>${icon("external-link", 16)} Descargar lista</button>
    `)}
    <section class="dashboard-stats" aria-label="Resumen de proyectos">
      ${dashboardStat("Todos los proyectos", all.length, "en tu espacio", "layout", "var(--primary)")}
      ${dashboardStat("En marcha", started.length, "ya tienen avances", "activity", "var(--green)")}
      ${dashboardStat("Ideas", ideas.length, "para empezar después", "sun", "var(--amber)")}
      ${dashboardStat("Avance promedio", `${average}%`, `${recent.length} se movieron recientemente`, "route", "var(--blue)")}
    </section>
    <section class="dashboard-charts">
      ${activityChart(state.events)}
      ${projectDonut(started.length, ideas.length)}
      ${stageProgressChart(state.progress)}
      ${categoryBubbleChart(all)}
    </section>
    <section class="panel projects-panel">
      <div class="projects-toolbar">
        <div class="projects-toolbar-title"><strong>Lista de proyectos</strong><span>${all.length} en total</span></div>
        <label class="inline-search">${icon("search", 16)}<input id="projectInlineSearch" value="${escapeHtml(state.search)}" placeholder="Buscar proyecto…"></label>
        <button class="small-button ${state.projectFilter === "started" ? "is-active" : ""}" type="button" data-project-filter="started">En marcha</button>
        <button class="small-button ${state.projectFilter === "all" ? "is-active" : ""}" type="button" data-project-filter="all">Todos</button>
        <button class="small-button ${state.projectFilter === "ideas" ? "is-active" : ""}" type="button" data-project-filter="ideas">Ideas</button>
      </div>
      <div class="table-scroll">
        <table class="project-table">
          <thead><tr><th>Proyecto</th><th>Tipo</th><th>Situación</th><th>Avance</th><th>Próximo paso</th><th>Último movimiento</th><th>Acciones</th></tr></thead>
          <tbody>
            ${projectRows(state.projectFilter === "ideas" ? ideas : state.projectFilter === "all" ? all : started)}
          </tbody>
        </table>
      </div>
    </section>
    ${state.projectFilter !== "ideas" && ideas.length ? `
      <section class="panel projects-panel no-code-section">
        <div class="panel-heading panel-pad"><div><h3>Ideas para después</h3><p>Aquí viven los proyectos que todavía no has empezado.</p></div><strong>${ideas.length}</strong></div>
        <div class="table-scroll">
          <table class="project-table">
            <thead><tr><th>Proyecto</th><th>Tipo</th><th>Situación</th><th>Avance</th><th>Qué falta definir</th><th>Último movimiento</th><th>Acciones</th></tr></thead>
            <tbody>${projectRows(ideas)}</tbody>
          </table>
        </div>
      </section>` : ""}`;
}
