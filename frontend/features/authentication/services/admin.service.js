import { API_URL, authenticatedFetch } from "@/shared/services/api-client";

async function adminRequest(path, options = {}) {
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

export const adminApi = {
  createUser: (payload) =>
    adminRequest("/users", { method: "POST", body: JSON.stringify(payload) }),
  listUsers: (search = "") =>
    adminRequest(`/users${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  getUser: (id) => adminRequest(`/users/${id}`),
  updateProfile: (id, payload) =>
    adminRequest(`/users/${id}/profile`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  enableUser: (id, reason) =>
    adminRequest(`/users/${id}/enable`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  disableUser: (id, reason) =>
    adminRequest(`/users/${id}/disable`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  lockUser: (id, reason) =>
    adminRequest(`/users/${id}/lock`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  unlockUser: (id, reason) =>
    adminRequest(`/users/${id}/unlock`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  forcePasswordReset: (id, reason) =>
    adminRequest(`/users/${id}/force-password-reset`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  updateSystemRole: (id, systemRole, reason) =>
    adminRequest(`/users/${id}/system-role`, {
      method: "PATCH",
      body: JSON.stringify({ system_role: systemRole, reason }),
    }),
  listSessions: (id) => adminRequest(`/users/${id}/sessions`),
  revokeSession: (id, sessionId) =>
    adminRequest(`/users/${id}/sessions/${sessionId}`, { method: "DELETE" }),
  revokeAllSessions: (id) => adminRequest(`/users/${id}/sessions`, { method: "DELETE" }),
  resetPasskeys: (id, reason) =>
    adminRequest(`/users/${id}/passkeys`, {
      method: "DELETE",
      body: JSON.stringify({ reason }),
    }),
  listMemberships: (id) => adminRequest(`/users/${id}/memberships`),
  listUserAudit: (id) => adminRequest(`/users/${id}/audit`),
  listProjects: (search = "") =>
    adminRequest(`/projects${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  getProjectPolicy: () => adminRequest("/platform/project-policy"),
  updateProjectPolicy: (projectCreationPolicy, reason) =>
    adminRequest("/platform/project-policy", {
      method: "PATCH",
      body: JSON.stringify({ project_creation_policy: projectCreationPolicy, reason }),
    }),
  listProviders: () => adminRequest("/ai/providers"),
  listModels: () => adminRequest("/ai/models"),
  registerModel: (payload) =>
    adminRequest("/ai/models", { method: "POST", body: JSON.stringify(payload) }),
  updateModel: (id, payload) =>
    adminRequest(`/ai/models/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  getAuthPolicy: () => adminRequest("/security/auth-policy"),
  updateAuthPolicy: (values, reason) =>
    adminRequest("/security/auth-policy", {
      method: "PATCH",
      body: JSON.stringify({ values, reason }),
    }),
  getIntegrations: () => adminRequest("/integrations"),
  updateIntegrations: (values, reason) =>
    adminRequest("/integrations", {
      method: "PATCH",
      body: JSON.stringify({ values, reason }),
    }),
  getStorage: () => adminRequest("/storage"),
  updateStorage: (values, reason) =>
    adminRequest("/storage", { method: "PATCH", body: JSON.stringify({ values, reason }) }),
  updateProvider: (id, payload) =>
    adminRequest(`/ai/providers/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  testProvider: (id) => adminRequest(`/ai/providers/${id}/test`, { method: "POST" }),
  getHealth: () => adminRequest("/health"),
  listJobs: (status = "") =>
    adminRequest(`/operations/jobs${status ? `?status=${encodeURIComponent(status)}` : ""}`),
  retryJob: (id) => adminRequest(`/operations/jobs/${id}/retry`, { method: "POST" }),
};
