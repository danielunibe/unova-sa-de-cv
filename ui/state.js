export const state = {
  projects: [],
  stats: {},
  events: [],
  progress: {},
  monitor: {},
  audit: {},
  workspace: { tasks: [], suggestions: [], settings: {}, project_overrides: {} },
  view: "my-work",
  projectId: "",
  projectDetail: null,
  projectTab: "summary",
  search: "",
  projectFilter: "started",
  activityProject: "",
  activityType: "",
  activityCursor: 0,
  activityPlaying: false,
  activitySpeed: 1,
  selectedTaskId: "",
  loading: false,
};

export function projectById(id) {
  return state.projects.find((project) => project.id === id);
}

export function activeTasks() {
  return (state.workspace.tasks || []).filter((task) => !task.archived_at);
}
