function readCookie(name) {
  const prefix = `${name}=`;
  const found = document.cookie.split("; ").find((part) => part.startsWith(prefix));
  return found ? decodeURIComponent(found.slice(prefix.length)) : "";
}

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const method = (options.method || "GET").toUpperCase();
  if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  if (["POST", "PATCH", "PUT", "DELETE"].includes(method)) {
    headers["X-CSRF-Token"] = readCookie("iesm_csrf");
  }
  const response = await fetch(path, {
    ...options,
    headers,
    credentials: "include",
  });
  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }
  if (!response.ok) {
    const detail =
      (data && data.detail) ||
      (typeof data === "string" && data) ||
      `Request failed (${response.status})`;
    throw new ApiError(response.status, Array.isArray(detail) ? JSON.stringify(detail) : detail);
  }
  return data;
}

export const api = {
  login: (email, password) => request("/api/v1/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () => request("/api/v1/auth/logout", { method: "POST" }),
  me: () => request(" /api/v1/auth/me".trim()),
  employees: (params) => request(`/api/v1/employees?${new URLSearchParams(clean(params))}`),
  employee: (id) => request(`/api/v1/employees/${id}`),
  createEmployee: (payload) => request("/api/v1/employees", { method: "POST", body: JSON.stringify(payload) }),
  patchEmployee: (id, payload) =>
    request(`/api/v1/employees/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  adjustCompensation: (id, payload) =>
    request(`/api/v1/employees/${id}/compensation`, { method: "POST", body: JSON.stringify(payload) }),
  compensationHistory: (id) => request(`/api/v1/employees/${id}/compensation`),
  filters: () => request("/api/v1/meta/filters"),
  summary: () => request("/api/v1/analytics/summary"),
  breakdowns: () => request("/api/v1/analytics/breakdowns"),
  distribution: () => request("/api/v1/analytics/distribution"),
  recentChanges: () => request("/api/v1/analytics/recent-changes"),
  exportUrl: (params) => `/api/v1/exports/employees.csv?${new URLSearchParams(clean(params))}`,
  importEmployees: (file) => {
    const body = new FormData();
    body.append("file", file);
    return request("/api/v1/imports/employees", { method: "POST", body });
  },
};

function clean(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== ""),
  );
}
