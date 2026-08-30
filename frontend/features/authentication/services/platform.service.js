import { API_URL, authenticatedFetch } from "@/shared/services/api-client";

async function platformRequest(path, options = {}) {
  const response = await authenticatedFetch(`${API_URL}/api/admin${path}`, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(
      body?.detail ||
        body?.error?.message ||
        body?.message ||
        "Không thể hoàn tất thao tác quản trị",
    );
  }
  return body?.data;
}

export const platformApi = {
  createUser: (payload) =>
    platformRequest("/users", { method: "POST", body: JSON.stringify(payload) }),
  listUsers: (search = "") =>
    platformRequest(`/users${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  getUser: (id) => platformRequest(`/users/${id}`),
  updateProfile: (id, payload) =>
    platformRequest(`/users/${id}/profile`, { method: "PATCH", body: JSON.stringify(payload) }),
  enableUser: (id, reason) =>
    platformRequest(`/users/${id}/enable`, { method: "POST", body: JSON.stringify({ reason }) }),
  disableUser: (id, reason) =>
    platformRequest(`/users/${id}/disable`, { method: "POST", body: JSON.stringify({ reason }) }),
  lockUser: (id, reason) =>
    platformRequest(`/users/${id}/lock`, { method: "POST", body: JSON.stringify({ reason }) }),
  unlockUser: (id, reason) =>
    platformRequest(`/users/${id}/unlock`, { method: "POST", body: JSON.stringify({ reason }) }),
  forcePasswordReset: (id, reason) =>
    platformRequest(`/users/${id}/force-password-reset`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  updateSystemRole: (id, systemRole, reason) =>
    platformRequest(`/users/${id}/system-role`, {
      method: "PATCH",
      body: JSON.stringify({ system_role: systemRole, reason }),
    }),
  listSessions: (id) => platformRequest(`/users/${id}/sessions`),
  revokeSession: (id, sessionId) =>
    platformRequest(`/users/${id}/sessions/${sessionId}`, { method: "DELETE" }),
  revokeAllSessions: (id) => platformRequest(`/users/${id}/sessions`, { method: "DELETE" }),
  resetPasskeys: (id, reason) =>
    platformRequest(`/users/${id}/passkeys`, {
      method: "DELETE",
      body: JSON.stringify({ reason }),
    }),
  listMemberships: (id) => platformRequest(`/users/${id}/memberships`),
  listUserAudit: (id) => platformRequest(`/users/${id}/audit`),
  listProjects: (search = "") =>
    platformRequest(`/projects${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  getProjectPolicy: () => platformRequest("/platform/project-policy"),
  updateProjectPolicy: (projectCreationPolicy, reason) =>
    platformRequest("/platform/project-policy", {
      method: "PATCH",
      body: JSON.stringify({ project_creation_policy: projectCreationPolicy, reason }),
    }),
  listProviders: () => platformRequest("/ai/providers"),
  listModels: () => platformRequest("/ai/models"),
  registerModel: (payload) =>
    platformRequest("/ai/models", { method: "POST", body: JSON.stringify(payload) }),
  updateModel: (id, payload) =>
    platformRequest(`/ai/models/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  getAuthPolicy: () => platformRequest("/security/auth-policy"),
  updateAuthPolicy: (values, reason) =>
    platformRequest("/security/auth-policy", {
      method: "PATCH",
      body: JSON.stringify({ values, reason }),
    }),
  getIntegrations: () => platformRequest("/integrations"),
  updateIntegrations: (values, reason) =>
    platformRequest("/integrations", { method: "PATCH", body: JSON.stringify({ values, reason }) }),
  getStorage: () => platformRequest("/storage"),
  updateStorage: (values, reason) =>
    platformRequest("/storage", { method: "PATCH", body: JSON.stringify({ values, reason }) }),
  updateProvider: (id, payload) =>
    platformRequest(`/ai/providers/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  testProvider: (id) => platformRequest(`/ai/providers/${id}/test`, { method: "POST" }),
  getHealth: () => platformRequest("/health"),
  listJobs: (status = "") =>
    platformRequest(`/operations/jobs${status ? `?status=${encodeURIComponent(status)}` : ""}`),
  retryJob: (id) => platformRequest(`/operations/jobs/${id}/retry`, { method: "POST" }),
};
