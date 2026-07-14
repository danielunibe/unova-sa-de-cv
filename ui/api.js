export async function api(path, options = {}) {
  const response = await fetch(path, {
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || payload.message || `HTTP ${response.status}`);
  }
  return payload;
}

export const getJson = (path) => api(path);
export const postJson = (path, body = {}) => api(path, { method: "POST", body: JSON.stringify(body) });
export const patchJson = (path, body = {}) => api(path, { method: "PATCH", body: JSON.stringify(body) });
