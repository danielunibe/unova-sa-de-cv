export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function parseDate(value) {
  if (!value) return null;
  const normalized = /^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T12:00:00` : value;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDate(value, withTime = false) {
  const date = parseDate(value);
  if (!date) return "Sin fecha";
  return new Intl.DateTimeFormat("es-MX", {
    dateStyle: "medium",
    ...(withTime ? { timeStyle: "short" } : {}),
  }).format(date);
}

export function relativeDate(value) {
  const date = parseDate(value);
  if (!date) return "Sin fecha";
  const days = Math.round((date.getTime() - Date.now()) / 86_400_000);
  if (Math.abs(days) <= 45) {
    return new Intl.RelativeTimeFormat("es-MX", { numeric: "auto" }).format(days, "day");
  }
  return formatDate(value);
}

export function todayIso() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

export const taskStatuses = {
  in_progress: { label: "En curso", color: "var(--blue)", soft: "var(--blue-soft)", icon: "activity" },
  next: { label: "Siguiente", color: "var(--purple)", soft: "var(--purple-soft)", icon: "chevron-right" },
  blocked: { label: "Bloqueada", color: "var(--coral)", soft: "var(--coral-soft)", icon: "alert-triangle" },
  review: { label: "En revisión", color: "var(--amber)", soft: "var(--amber-soft)", icon: "search" },
  done: { label: "Terminada", color: "var(--green)", soft: "var(--green-soft)", icon: "check" },
};

export const statusOrder = ["in_progress", "next", "blocked", "review", "done"];

export const priorities = {
  low: { label: "Baja", color: "var(--teal)" },
  medium: { label: "Media", color: "var(--blue)" },
  high: { label: "Alta", color: "var(--amber)" },
  urgent: { label: "Urgente", color: "var(--coral)" },
};

export function dueBucket(task) {
  if (!task.due_date) return "none";
  const today = todayIso();
  if (task.due_date < today && task.status !== "done") return "overdue";
  if (task.due_date === today) return "today";
  const limit = new Date();
  limit.setDate(limit.getDate() + 7);
  const limitIso = `${limit.getFullYear()}-${String(limit.getMonth() + 1).padStart(2, "0")}-${String(limit.getDate()).padStart(2, "0")}`;
  return task.due_date <= limitIso ? "upcoming" : "later";
}

export function categoryIcon(project) {
  const category = String(project?.categoria || "").toLowerCase();
  if (category.includes("móvil")) return "smartphone";
  if (category.includes("videojuego")) return "gamepad";
  if (category.includes("música")) return "music";
  if (category.includes("ebook")) return "book";
  if (category.includes("mesa")) return "board";
  if (category.includes("gastronom")) return "food";
  if (category.includes("extensión")) return "browser";
  return "code";
}

export function projectColor(project, override = {}) {
  if (override.color) return override.color;
  const palette = ["#5b5bd6", "#4c8bf5", "#8a63d2", "#2ca6a4", "#d9982d", "#e56a78"];
  let hash = 0;
  for (const char of String(project?.id || "")) hash = ((hash << 5) - hash) + char.charCodeAt(0);
  return palette[Math.abs(hash) % palette.length];
}

export function safeText(value, fallback = "Sin definir") {
  const text = String(value || "").trim();
  return text && text !== "No documentado" ? text : fallback;
}

export function friendlySuggestionTitle(value) {
  const text = String(value || "").trim();
  const translations = {
    "Completar próximo paso documentado": "Definir el siguiente paso",
    "Completar arquitectura verificable": "Aclarar cómo estará organizado",
    "Completar implementación": "Seguir construyendo la aplicación",
    "Completar empaquetado/distribución": "Preparar una versión para compartir",
    "Completar diseño documentado": "Definir y guardar el diseño",
    "Completar definición completa": "Terminar de explicar la idea",
    "Completar pruebas": "Comprobar que funciona",
    "Completar validación": "Hacer una revisión final",
  };
  return translations[text] || text;
}
