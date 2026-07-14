const paths = {
  "check-square": '<path d="M9 11l2 2 4-4"/><rect x="3" y="3" width="18" height="18" rx="3"/>',
  folder: '<path d="M3 7.5h6l2-2h4l2 2h4v10.5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  activity: '<path d="M3 12h4l2.5-7 5 14 2.5-7h4"/>',
  shield: '<path d="M12 22s8-3.5 8-10V5l-8-3-8 3v7c0 6.5 8 10 8 10z"/><path d="M9 12l2 2 4-4"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.8 1.8 0 0 0 .36 2l.06.06-2.12 2.12-.06-.06a1.8 1.8 0 0 0-2-.36 1.8 1.8 0 0 0-1.1 1.65V21h-3v-.09A1.8 1.8 0 0 0 10.4 19.3a1.8 1.8 0 0 0-2 .36l-.06.06-2.12-2.12.06-.06a1.8 1.8 0 0 0 .36-2A1.8 1.8 0 0 0 5 14.45H5v-3h.09A1.8 1.8 0 0 0 6.7 10.4a1.8 1.8 0 0 0-.36-2l-.06-.06 2.12-2.12.06.06a1.8 1.8 0 0 0 2 .36A1.8 1.8 0 0 0 11.55 5V5h3v.09a1.8 1.8 0 0 0 1.1 1.65 1.8 1.8 0 0 0 2-.36l.06-.06 2.12 2.12-.06.06a1.8 1.8 0 0 0-.36 2A1.8 1.8 0 0 0 21 11.55V14.5h-.09A1.8 1.8 0 0 0 19.4 15z"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  refresh: '<path d="M20 11a8 8 0 0 0-14.8-4M4 4v5h5"/><path d="M4 13a8 8 0 0 0 14.8 4M20 20v-5h-5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  moon: '<path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5 8.5 8.5 0 1 0 20.5 14.2z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42"/>',
  monitor: '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
  github: '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3.3-.37 6.8-1.62 6.8-7.4A5.8 5.8 0 0 0 19.3 3c.15-.38.65-1.95-.15-4 0 0-1.3-.42-4.15 1.58a14.5 14.5 0 0 0-7.5 0C4.65-1.42 3.35-1 3.35-1c-.8 2.05-.3 3.62-.15 4A5.8 5.8 0 0 0 1.7 7.1c0 5.77 3.5 7.02 6.8 7.4a4.8 4.8 0 0 0-1 3.5v4"/><path d="M7.5 19c-3 .9-3-1.5-4.2-2"/>',
  "external-link": '<path d="M14 3h7v7M10 14 21 3"/><path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5"/>',
  flag: '<path d="M5 21V4m0 0h10l-1 4 1 4H5"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>',
  play: '<path d="m8 5 11 7-11 7z"/>',
  pause: '<path d="M8 5v14M16 5v14"/>',
  "chevron-left": '<path d="m15 18-6-6 6-6"/>',
  "chevron-right": '<path d="m9 18 6-6-6-6"/>',
  "chevron-up": '<path d="m18 15-6-6-6 6"/>',
  "chevron-down": '<path d="m6 9 6 6 6-6"/>',
  "arrow-left": '<path d="m15 18-6-6 6-6"/><path d="M9 12h12"/>',
  "more-horizontal": '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  x: '<path d="m6 6 12 12M18 6 6 18"/>',
  archive: '<path d="M21 8v13H3V8M1 3h22v5H1zM10 12h4"/>',
  edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L8 18l-4 1 1-4z"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
  "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h8"/>',
  palette: '<path d="M12 22a10 10 0 1 1 10-10c0 2-1 3-3 3h-2.2a2 2 0 0 0-1.8 2.9A2.8 2.8 0 0 1 12 22z"/><circle cx="7.5" cy="10" r="1"/><circle cx="10.5" cy="6.5" r="1"/><circle cx="15" cy="7.5" r="1"/>',
  blocks: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="8.5" y="14" width="7" height="7" rx="1"/><path d="M6.5 10v2h11v-2M12 12v2"/>',
  code: '<path d="m8 9-4 3 4 3M16 9l4 3-4 3M14 5l-4 14"/>',
  flask: '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.75 3h10.5A2 2 0 0 0 19 18l-5-9V3"/><path d="M7.5 15h9"/>',
  package: '<path d="m12 2 9 5-9 5-9-5z"/><path d="m3 7 9 5 9-5v10l-9 5-9-5z"/><path d="M12 12v10"/>',
  route: '<circle cx="6" cy="19" r="3"/><circle cx="18" cy="5" r="3"/><path d="M6 16V9a4 4 0 0 1 4-4h5M9 19h7a2 2 0 0 0 2-2V8"/>',
  "badge-check": '<path d="M12 2l2.4 2 3.1-.1.8 3 2.5 1.8-1 3 1 3-2.5 1.8-.8 3-3.1-.1L12 22l-2.4-2-3.1.1-.8-3-2.5-1.8 1-3-1-3 2.5-1.8.8-3 3.1.1z"/><path d="m8 12 2.5 2.5L16 9"/>',
  "alert-triangle": '<path d="M10.3 3.6 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13"/><circle cx="3" cy="6" r="1"/><circle cx="3" cy="12" r="1"/><circle cx="3" cy="18" r="1"/>',
  layout: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>',
  home: '<path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10M9 20v-6h6v6"/>',
  layers: '<path d="m12 2 9 5-9 5-9-5z"/><path d="m3 12 9 5 9-5M3 17l9 5 9-5"/>',
  smartphone: '<rect x="6" y="2" width="12" height="20" rx="2"/><path d="M10 18h4"/>',
  gamepad: '<path d="M6 9h12a4 4 0 0 1 3.8 5.2l-1.2 3.6a2 2 0 0 1-3.4.7L15 16H9l-2.2 2.5a2 2 0 0 1-3.4-.7l-1.2-3.6A4 4 0 0 1 6 9z"/><path d="M7 12v4M5 14h4M16 13h.01M19 15h.01"/>',
  music: '<path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/>',
  book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 5.5v14"/>',
  board: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8" cy="8" r="1.5"/><circle cx="16" cy="16" r="1.5"/><path d="m10 14 4-4"/>',
  food: '<path d="M3 2v7a3 3 0 0 0 6 0V2M6 2v20M15 2v20M15 2c4 2 5 6 5 10h-5"/>',
  browser: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M7 6h.01M11 6h.01"/>',
  circle: '<circle cx="12" cy="12" r="9"/>',
};

export function icon(name, size = 18, label = "") {
  const body = paths[name] || paths.circle;
  const aria = label ? ` role="img" aria-label="${label}"` : ' aria-hidden="true"';
  return `<svg class="icon" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"${aria}>${body}</svg>`;
}

export function hydrateIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((node) => {
    node.innerHTML = icon(node.dataset.icon);
  });
}
