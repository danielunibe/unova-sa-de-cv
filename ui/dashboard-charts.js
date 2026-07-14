import { icon } from "./icons.js";
import { escapeHtml } from "./utils.js";

const stageConfig = [
  ["definicion", "Idea clara", 15, "var(--purple)"],
  ["diseno", "Diseño", 10, "var(--blue)"],
  ["arquitectura", "Estructura", 10, "var(--teal)"],
  ["implementacion", "Construcción", 30, "var(--green)"],
  ["pruebas", "Pruebas", 15, "var(--amber)"],
  ["empaquetado", "Preparación", 10, "#b779d0"],
  ["continuidad", "Seguimiento", 5, "var(--text-faint)"],
  ["validacion", "Revisión final", 5, "var(--coral)"],
];

const categoryColors = [
  "var(--teal)",
  "var(--blue)",
  "#d47ac7",
  "var(--coral)",
  "var(--purple)",
  "var(--amber)",
];

function polylinePoints(values, width, height, padding, maximum) {
  const step = values.length > 1 ? (width - padding * 2) / (values.length - 1) : 0;
  return values.map((value, index) => {
    const x = padding + index * step;
    const y = height - padding - ((value || 0) / maximum) * (height - padding * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
}

function monthBuckets(events, count = 6) {
  const now = new Date();
  const buckets = [];
  for (let offset = count - 1; offset >= 0; offset -= 1) {
    const date = new Date(now.getFullYear(), now.getMonth() - offset, 1);
    buckets.push({
      key: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`,
      label: new Intl.DateTimeFormat("es-MX", { month: "short" }).format(date).replace(".", ""),
      registered: 0,
      previous: 0,
    });
  }
  const byKey = new Map(buckets.map((bucket) => [bucket.key, bucket]));
  events.forEach((event) => {
    const date = new Date(event.timestamp);
    if (Number.isNaN(date.getTime())) return;
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    const bucket = byKey.get(key);
    if (!bucket) return;
    if (event.precision === "estimated") bucket.previous += 1;
    else bucket.registered += 1;
  });
  return buckets;
}

export function dashboardStat(label, value, note, iconName, color) {
  return `
    <article class="dashboard-stat" style="--stat-color:${color}">
      <span class="dashboard-stat-icon">${icon(iconName, 21)}</span>
      <div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></div>
    </article>`;
}

export function activityChart(events) {
  const buckets = monthBuckets(events);
  const registered = buckets.map((bucket) => bucket.registered);
  const previous = buckets.map((bucket) => bucket.previous);
  const maximum = Math.max(1, ...registered, ...previous);
  const width = 560;
  const height = 190;
  const padding = 24;
  const registeredPoints = polylinePoints(registered, width, height, padding, maximum);
  const previousPoints = polylinePoints(previous, width, height, padding, maximum);
  const labels = buckets.map((bucket, index) => {
    const x = padding + index * ((width - padding * 2) / (buckets.length - 1));
    return `<text x="${x}" y="${height - 3}" text-anchor="middle">${escapeHtml(bucket.label)}</text>`;
  }).join("");
  return `
    <article class="chart-card chart-card-wide">
      <header class="chart-heading">
        <div><h3>Movimiento reciente</h3><p>Cuándo has estado trabajando en tus proyectos.</p></div>
        ${icon("activity", 19)}
      </header>
      <svg class="line-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Actividad de los últimos seis meses">
        <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" class="chart-axis"/>
        <polyline points="${previousPoints}" class="chart-line chart-line-secondary"/>
        <polyline points="${registeredPoints}" class="chart-line chart-line-primary"/>
        ${registered.map((value, index) => {
          const point = registeredPoints.split(" ")[index].split(",");
          return `<circle cx="${point[0]}" cy="${point[1]}" r="4" class="chart-dot chart-dot-primary"><title>${buckets[index].label}: ${value} cambios</title></circle>`;
        }).join("")}
        ${labels}
      </svg>
      <div class="chart-legend">
        <span><i style="--legend-color:var(--blue)"></i>Cambios registrados</span>
        <span><i style="--legend-color:var(--teal)"></i>Actividad anterior</span>
      </div>
    </article>`;
}

export function projectDonut(started, ideas) {
  const total = Math.max(1, started + ideas);
  const percent = Math.round(started * 100 / total);
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const dash = circumference * started / total;
  return `
    <article class="chart-card">
      <header class="chart-heading"><div><h3>Estado de tus proyectos</h3><p>Qué ya está en marcha y qué sigue como idea.</p></div>${icon("layout", 19)}</header>
      <div class="donut-layout">
        <svg class="donut-chart" viewBox="0 0 130 130" role="img" aria-label="${started} proyectos en marcha y ${ideas} ideas">
          <circle cx="65" cy="65" r="${radius}" class="donut-track"/>
          <circle cx="65" cy="65" r="${radius}" class="donut-value" stroke-dasharray="${dash} ${circumference - dash}"/>
          <text x="65" y="61" text-anchor="middle" class="donut-number">${percent}%</text>
          <text x="65" y="79" text-anchor="middle" class="donut-label">en marcha</text>
        </svg>
        <div class="donut-legend">
          <span><i style="--legend-color:var(--primary)"></i><strong>${started}</strong> En marcha</span>
          <span><i style="--legend-color:var(--surface-strong)"></i><strong>${ideas}</strong> Ideas</span>
        </div>
      </div>
    </article>`;
}

export function stageProgressChart(progressById) {
  const entries = Object.values(progressById || {});
  const rows = stageConfig.map(([key, label, maximum, color]) => {
    const average = entries.length
      ? Math.round(entries.reduce((sum, item) => sum + Number(item.breakdown?.[key] || 0) / maximum * 100, 0) / entries.length)
      : 0;
    return `
      <div class="stage-chart-row">
        <span>${escapeHtml(label)}</span>
        <i><b style="width:${average}%;--bar-color:${color}"></b></i>
        <strong>${average}%</strong>
      </div>`;
  }).join("");
  return `
    <article class="chart-card chart-card-wide">
      <header class="chart-heading"><div><h3>Avance por etapa</h3><p>Promedio de la primera versión en todos tus proyectos.</p></div>${icon("route", 19)}</header>
      <div class="stage-chart">${rows}</div>
    </article>`;
}

export function categoryBubbleChart(projects) {
  const counts = new Map();
  projects.forEach((project) => counts.set(project.categoria || "Otros", (counts.get(project.categoria || "Otros") || 0) + 1));
  const categories = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6);
  const maximum = Math.max(1, ...categories.map(([, count]) => count));
  return `
    <article class="chart-card">
      <header class="chart-heading"><div><h3>Tipos de proyecto</h3><p>En qué áreas estás creando más.</p></div>${icon("blocks", 19)}</header>
      <div class="bubble-chart" role="img" aria-label="Distribución por tipo de proyecto">
        ${categories.map(([label, count], index) => {
          const size = Math.round(50 + (count / maximum) * 50);
          return `<div class="category-bubble" style="--bubble-size:${size}px;--bubble-color:${categoryColors[index % categoryColors.length]}"><strong>${count}</strong><span>${escapeHtml(label)}</span></div>`;
        }).join("")}
      </div>
    </article>`;
}
