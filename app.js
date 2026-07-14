import { getJson, patchJson, postJson } from "./ui/api.js";
import { hydrateIcons, icon } from "./ui/icons.js";
import { renderMyWork } from "./ui/my-work.js";
import { renderProjects } from "./ui/projects.js";
import { renderProjectWorkspace } from "./ui/project-workspace.js";
import { filteredActivityEvents, renderActivity, renderAudit, renderSettings } from "./ui/secondary-views.js";
import { activeTasks, projectById, state } from "./ui/state.js";
import { taskStatuses } from "./ui/utils.js";

const main = document.querySelector("#mainContent");
const taskModal = document.querySelector("#taskModal");
const projectSettingsModal = document.querySelector("#projectSettingsModal");
const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
let initialized = false;
let draggedTaskId = "";
let activityTimer = 0;

function stopActivityPlayback() {
  window.clearInterval(activityTimer);
  activityTimer = 0;
}

function playbackEvents() {
  return filteredActivityEvents().slice(0, 350).reverse();
}

function startActivityPlayback() {
  stopActivityPlayback();
  if (!state.activityPlaying) return;
  const interval = Math.max(260, Math.round(1200 / Number(state.activitySpeed || 1)));
  activityTimer = window.setInterval(() => {
    const events = playbackEvents();
    if (!events.length || state.activityCursor >= events.length - 1) {
      state.activityPlaying = false;
      stopActivityPlayback();
      render();
      return;
    }
    state.activityCursor += 1;
    render();
  }, interval);
}

function resetActivityPlayback() {
  state.activityPlaying = false;
  state.activityCursor = 0;
  stopActivityPlayback();
}

function toast(message, tone = "info") {
  const node = document.createElement("div");
  node.className = `toast ${tone === "error" ? "is-error" : tone === "success" ? "is-success" : ""}`;
  node.textContent = message;
  document.querySelector("#toastRegion").append(node);
  window.setTimeout(() => node.remove(), 5000);
}

function applyTheme() {
  const settings = state.workspace.settings || {};
  const resolved = settings.theme === "system"
    ? systemTheme.matches ? "dark" : "light"
    : settings.theme || "light";
  document.documentElement.dataset.theme = resolved;
  document.documentElement.dataset.density = settings.density || "comfortable";
  const themeIcon = document.querySelector("#themeButton [data-icon]");
  if (themeIcon) {
    themeIcon.dataset.icon = resolved === "dark" ? "sun" : "moon";
    hydrateIcons(document.querySelector("#themeButton"));
  }
}

function renderMonitor() {
  const chip = document.querySelector("#monitorChip");
  const label = document.querySelector("#monitorLabel");
  const status = state.monitor.state || "idle";
  chip.className = `monitor-chip ${status === "scanning" ? "is-scanning" : status === "error" ? "is-error" : ""}`;
  label.textContent = status === "scanning" ? "Revisando" : status === "error" ? "Necesita atención" : "Todo al día";
  document.querySelector("#refreshButton").disabled = status === "scanning";
}

function render() {
  const views = {
    "my-work": renderMyWork,
    projects: renderProjects,
    project: renderProjectWorkspace,
    activity: renderActivity,
    audit: renderAudit,
    settings: renderSettings,
  };
  main.innerHTML = (views[state.view] || renderMyWork)();
  document.querySelectorAll(".side-link[data-nav]").forEach((button) => {
    const activeView = state.view === "project" ? "projects" : state.view;
    button.classList.toggle("is-active", button.dataset.nav === activeView);
  });
  document.querySelector("#globalSearch").value = state.search;
  hydrateIcons(main);
  renderMonitor();
  applyTheme();
}

async function loadAll({ quiet = false } = {}) {
  try {
    const [catalog, stats, events, progress, monitor, audit, workspace] = await Promise.all([
      getJson("/api/catalog"),
      getJson("/api/stats"),
      getJson("/api/events?limit=2500"),
      getJson("/api/progress"),
      getJson("/api/monitor"),
      getJson("/api/audit"),
      getJson("/api/workspace"),
    ]);
    state.projects = catalog.projects || [];
    state.stats = stats || {};
    state.events = events.events || [];
    state.progress = progress || {};
    state.monitor = monitor || {};
    state.audit = audit || {};
    state.workspace = workspace || state.workspace;
    if (!initialized) {
      state.view = state.workspace.settings?.start_view || "my-work";
      initialized = true;
    }
    if (state.view === "project" && state.projectId) {
      state.projectDetail = await getJson(`/api/projects/${encodeURIComponent(state.projectId)}`);
    }
    render();
    if (!quiet) toast("Espacio personal sincronizado.", "success");
  } catch (error) {
    console.error(error);
    if (!quiet) toast(`No se pudo cargar el gestor: ${error.message}`, "error");
  }
}

async function refreshWorkspace() {
  state.workspace = await getJson("/api/workspace");
  if (state.view === "project" && state.projectId) {
    state.projectDetail = await getJson(`/api/projects/${encodeURIComponent(state.projectId)}`);
  }
  render();
}

function navigate(view) {
  if (view !== "activity") resetActivityPlayback();
  state.view = view;
  if (view !== "project") {
    state.projectId = "";
    state.projectDetail = null;
  }
  render();
  main.focus({ preventScroll: true });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function openProject(projectId, tab = "summary") {
  state.projectId = projectId;
  state.projectTab = tab;
  state.view = "project";
  state.projectDetail = null;
  render();
  try {
    state.projectDetail = await getJson(`/api/projects/${encodeURIComponent(projectId)}`);
    render();
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (error) {
    toast(error.message, "error");
    navigate("projects");
  }
}

function projectOptions(selected = "") {
  return [...state.projects]
    .sort((a, b) => a.proyecto.localeCompare(b.proyecto, "es"))
    .map((project) => `<option value="${project.id}" ${project.id === selected ? "selected" : ""}>${project.proyecto}</option>`)
    .join("");
}

function openTaskModal(task = null, defaults = {}) {
  state.selectedTaskId = task?.id || "";
  document.querySelector("#taskModalTitle").textContent = task ? "Editar tarea" : "Nueva tarea";
  document.querySelector("#taskSubmitLabel").textContent = task ? "Guardar cambios" : "Crear tarea";
  document.querySelector("#taskId").value = task?.id || "";
  document.querySelector("#taskTitle").value = task?.title || defaults.title || "";
  document.querySelector("#taskProject").innerHTML = projectOptions(task?.project_id || defaults.project_id || state.projectId || state.projects[0]?.id);
  document.querySelector("#taskStatus").value = task?.status || defaults.status || "next";
  document.querySelector("#taskPriority").value = task?.priority || defaults.priority || "medium";
  document.querySelector("#taskDueDate").value = task?.due_date || "";
  document.querySelector("#taskNotes").value = task?.notes || "";
  document.querySelector("#taskChecklist").value = (task?.checklist || []).map((item) => item.text).join("\n");
  document.querySelector("#taskLinkType").value = task?.link?.type || "";
  document.querySelector("#taskLinkValue").value = task?.link?.value || "";
  document.querySelector("#archiveTaskButton").hidden = !task;
  taskModal.showModal();
  document.querySelector("#taskTitle").focus();
}

function currentTask() {
  return activeTasks().find((task) => task.id === state.selectedTaskId);
}

function taskPayloadFromForm() {
  const existing = currentTask();
  const existingChecklist = new Map((existing?.checklist || []).map((item) => [item.text, item]));
  const checklist = document.querySelector("#taskChecklist").value
    .split("\n")
    .map((text) => text.trim())
    .filter(Boolean)
    .map((text) => existingChecklist.get(text) || { text, done: false });
  return {
    title: document.querySelector("#taskTitle").value,
    project_id: document.querySelector("#taskProject").value,
    status: document.querySelector("#taskStatus").value,
    priority: document.querySelector("#taskPriority").value,
    due_date: document.querySelector("#taskDueDate").value,
    notes: document.querySelector("#taskNotes").value,
    checklist,
    link: {
      type: document.querySelector("#taskLinkType").value,
      value: document.querySelector("#taskLinkValue").value,
    },
  };
}

async function saveTask(event) {
  event.preventDefault();
  const submit = event.submitter;
  submit.disabled = true;
  try {
    const payload = taskPayloadFromForm();
    if (state.selectedTaskId) {
      await patchJson(`/api/tasks/${encodeURIComponent(state.selectedTaskId)}`, payload);
      toast("Tarea actualizada.", "success");
    } else {
      await postJson("/api/tasks", payload);
      toast("Tarea creada.", "success");
    }
    taskModal.close();
    await refreshWorkspace();
  } catch (error) {
    toast(error.message, "error");
  } finally {
    submit.disabled = false;
  }
}

async function archiveCurrentTask() {
  if (!state.selectedTaskId) return;
  try {
    await postJson(`/api/tasks/${encodeURIComponent(state.selectedTaskId)}/archive`);
    taskModal.close();
    toast("Tarea archivada.", "success");
    await refreshWorkspace();
  } catch (error) {
    toast(error.message, "error");
  }
}

async function patchTask(taskId, payload) {
  try {
    await patchJson(`/api/tasks/${encodeURIComponent(taskId)}`, payload);
    await refreshWorkspace();
  } catch (error) {
    toast(error.message, "error");
  }
}

async function adoptSuggestion(id) {
  const suggestion = state.workspace.suggestions?.find((item) => item.id === id)
    || state.projectDetail?.suggestions?.find((item) => item.id === id);
  if (!suggestion) return;
  try {
    await postJson("/api/tasks", {
      title: suggestion.title,
      project_id: suggestion.project_id,
      status: "next",
      priority: suggestion.priority || "low",
      origin: "suggested",
      source_ref: suggestion.source_ref,
    });
    toast("Sugerencia añadida a tu plan.", "success");
    await refreshWorkspace();
  } catch (error) {
    toast(error.message, "error");
  }
}

async function openFolder(projectId) {
  try {
    await postJson(`/api/projects/${encodeURIComponent(projectId)}/open-folder`);
    toast("Carpeta abierta.", "success");
  } catch (error) {
    toast(error.message, "error");
  }
}

async function openGithub(projectId) {
  try {
    const detail = state.projectDetail?.project?.id === projectId
      ? state.projectDetail
      : await getJson(`/api/projects/${encodeURIComponent(projectId)}`);
    if (!detail.github_url) throw new Error("Este proyecto no tiene un repositorio GitHub confirmado.");
    window.open(detail.github_url, "_blank", "noopener");
  } catch (error) {
    toast(error.message, "error");
  }
}

function openProjectSettings(projectId) {
  const project = projectById(projectId);
  const detail = state.projectDetail?.project?.id === projectId ? state.projectDetail : null;
  const override = state.workspace.project_overrides?.[projectId] || detail?.preferences || {};
  document.querySelector("#projectSettingsTitle").textContent = `Configurar ${project?.proyecto || "proyecto"}`;
  document.querySelector("#settingsProjectId").value = projectId;
  document.querySelector("#settingsGithubUrl").value = override.github_url || detail?.github_url || "";
  document.querySelector("#settingsProjectColor").value = override.color || "#5b5bd6";
  document.querySelector("#settingsProjectIcon").value = override.icon || "default";
  projectSettingsModal.showModal();
}

async function saveProjectSettings(event) {
  event.preventDefault();
  const projectId = document.querySelector("#settingsProjectId").value;
  try {
    await patchJson(`/api/projects/${encodeURIComponent(projectId)}/preferences`, {
      github_url: document.querySelector("#settingsGithubUrl").value,
      color: document.querySelector("#settingsProjectColor").value,
      icon: document.querySelector("#settingsProjectIcon").value,
    });
    projectSettingsModal.close();
    toast("Accesos del proyecto actualizados.", "success");
    await loadAll({ quiet: true });
  } catch (error) {
    toast(error.message, "error");
  }
}

async function requestScan() {
  const buttons = [document.querySelector("#refreshButton"), ...document.querySelectorAll("[data-refresh]")];
  buttons.forEach((button) => { if (button) button.disabled = true; });
  try {
    const result = await postJson("/api/scan");
    toast("Estamos revisando tus proyectos.", "success");
    state.monitor.state = "scanning";
    renderMonitor();
    window.setTimeout(() => loadAll({ quiet: true }), 3000);
  } catch (error) {
    toast(error.message, "error");
  } finally {
    buttons.forEach((button) => { if (button) button.disabled = false; });
  }
}

async function updateSettings(payload) {
  try {
    const result = await patchJson("/api/settings", payload);
    state.workspace.settings = result.settings;
    render();
  } catch (error) {
    toast(error.message, "error");
  }
}

async function toggleTheme() {
  const current = document.documentElement.dataset.theme;
  await updateSettings({ theme: current === "dark" ? "light" : "dark" });
}

document.addEventListener("click", async (event) => {
  const nav = event.target.closest("[data-nav]");
  if (nav) {
    navigate(nav.dataset.nav);
    return;
  }
  const newTask = event.target.closest("[data-new-task], #newTaskButton");
  if (newTask) {
    openTaskModal();
    return;
  }
  const statusTask = event.target.closest("[data-new-task-status]");
  if (statusTask) {
    openTaskModal(null, { status: statusTask.dataset.newTaskStatus });
    return;
  }
  const projectTask = event.target.closest("[data-new-task-project]");
  if (projectTask) {
    openTaskModal(null, { project_id: projectTask.dataset.newTaskProject });
    return;
  }
  const openProjectButton = event.target.closest("[data-open-project]");
  if (openProjectButton) {
    await openProject(openProjectButton.dataset.openProject);
    return;
  }
  const editTask = event.target.closest("[data-edit-task]");
  if (editTask) {
    const task = activeTasks().find((item) => item.id === editTask.dataset.editTask)
      || state.projectDetail?.tasks?.find((item) => item.id === editTask.dataset.editTask);
    if (task) openTaskModal(task);
    return;
  }
  const suggestion = event.target.closest("[data-adopt-suggestion]");
  if (suggestion) {
    await adoptSuggestion(suggestion.dataset.adoptSuggestion);
    return;
  }
  const folder = event.target.closest("[data-open-folder]");
  if (folder) {
    await openFolder(folder.dataset.openFolder);
    return;
  }
  const github = event.target.closest("[data-open-github]");
  if (github && !github.disabled) {
    await openGithub(github.dataset.openGithub);
    return;
  }
  const projectTab = event.target.closest("[data-project-tab]");
  if (projectTab) {
    state.projectTab = projectTab.dataset.projectTab;
    render();
    return;
  }
  const projectSettings = event.target.closest("[data-project-settings]");
  if (projectSettings) {
    openProjectSettings(projectSettings.dataset.projectSettings);
    return;
  }
  const closeModal = event.target.closest("[data-close-modal]");
  if (closeModal) {
    document.querySelector(`#${closeModal.dataset.closeModal}`).close();
    return;
  }
  const projectFilter = event.target.closest("[data-project-filter]");
  if (projectFilter) {
    state.projectFilter = projectFilter.dataset.projectFilter;
    render();
    return;
  }
  const themeChoice = event.target.closest("[data-theme-choice]");
  if (themeChoice) {
    await updateSettings({ theme: themeChoice.dataset.themeChoice });
    return;
  }
  const activityPlay = event.target.closest("[data-activity-play]");
  if (activityPlay) {
    state.activityPlaying = !state.activityPlaying;
    startActivityPlayback();
    render();
    return;
  }
  const activityStep = event.target.closest("[data-activity-step]");
  if (activityStep) {
    state.activityPlaying = false;
    stopActivityPlayback();
    const events = playbackEvents();
    state.activityCursor = Math.min(
      Math.max(0, state.activityCursor + Number(activityStep.dataset.activityStep || 0)),
      Math.max(0, events.length - 1),
    );
    render();
    return;
  }
  if (event.target.closest("[data-refresh]")) {
    await requestScan();
    return;
  }
  if (event.target.closest("[data-export-csv]")) {
    window.location.href = "/data/proyectos.csv";
  }
});

document.addEventListener("change", async (event) => {
  const complete = event.target.closest("[data-task-complete]");
  if (complete) {
    await patchTask(complete.dataset.taskComplete, { status: complete.checked ? "done" : "next" });
    return;
  }
  const status = event.target.closest("[data-task-status]");
  if (status) {
    await patchTask(status.dataset.taskStatus, { status: status.value });
    return;
  }
  if (event.target.id === "activityProjectFilter") {
    state.activityProject = event.target.value;
    resetActivityPlayback();
    render();
    return;
  }
  if (event.target.id === "activityTypeFilter") {
    state.activityType = event.target.value;
    resetActivityPlayback();
    render();
    return;
  }
  if (event.target.id === "activitySpeed") {
    state.activitySpeed = Number(event.target.value) || 1;
    startActivityPlayback();
    render();
    return;
  }
  if (event.target.id === "densitySetting") {
    await updateSettings({ density: event.target.value });
    return;
  }
  if (event.target.id === "startViewSetting") {
    await updateSettings({ start_view: event.target.value });
  }
});

document.addEventListener("input", (event) => {
  if (event.target.id === "activityCursor") {
    state.activityPlaying = false;
    stopActivityPlayback();
    state.activityCursor = Number(event.target.value) || 0;
    render();
    return;
  }
  if (event.target.id === "globalSearch" || event.target.id === "projectInlineSearch") {
    state.search = event.target.value;
    document.querySelector("#globalSearch").value = state.search;
    render();
    const inline = document.querySelector("#projectInlineSearch");
    if (inline) {
      inline.focus();
      inline.setSelectionRange(inline.value.length, inline.value.length);
    }
  }
});

document.addEventListener("dragstart", (event) => {
  const row = event.target.closest("[data-task-row]");
  if (!row) return;
  draggedTaskId = row.dataset.taskRow;
  row.style.opacity = "0.45";
  event.dataTransfer.effectAllowed = "move";
});

document.addEventListener("dragend", (event) => {
  const row = event.target.closest("[data-task-row]");
  if (row) row.style.opacity = "";
  draggedTaskId = "";
});

document.addEventListener("dragover", (event) => {
  if (draggedTaskId && event.target.closest("[data-task-row]")) event.preventDefault();
});

document.addEventListener("drop", async (event) => {
  const targetRow = event.target.closest("[data-task-row]");
  if (!draggedTaskId || !targetRow || targetRow.dataset.taskRow === draggedTaskId) return;
  event.preventDefault();
  const dragged = activeTasks().find((task) => task.id === draggedTaskId);
  const target = activeTasks().find((task) => task.id === targetRow.dataset.taskRow);
  if (!dragged || !target) return;
  await patchTask(dragged.id, { status: target.status, order: target.order });
});

document.querySelector("#taskForm").addEventListener("submit", saveTask);
document.querySelector("#archiveTaskButton").addEventListener("click", archiveCurrentTask);
document.querySelector("#projectSettingsForm").addEventListener("submit", saveProjectSettings);
document.querySelector("#refreshButton").addEventListener("click", requestScan);
document.querySelector("#themeButton").addEventListener("click", toggleTheme);
systemTheme.addEventListener("change", () => {
  if (state.workspace.settings?.theme === "system") applyTheme();
});

hydrateIcons(document);
loadAll();
window.setInterval(() => loadAll({ quiet: true }), 30_000);
