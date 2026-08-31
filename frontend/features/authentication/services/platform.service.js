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

async function downloadPlatformFile(path, filename) {
  const response = await authenticatedFetch(`${API_URL}/api/admin${path}`);
  if (!response.ok) throw new Error("Không thể tải tệp quản trị");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
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
  resendVerification: (id, reason) =>
    platformRequest(`/users/${id}/resend-verification`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  deleteUser: (id, confirmation, reason) =>
    platformRequest(`/users/${id}`, {
      method: "DELETE",
      body: JSON.stringify({ confirmation, reason }),
    }),
  previewBulkUsers: (action, userIds, reason) =>
    platformRequest("/users/bulk/preview", {
      method: "POST",
      body: JSON.stringify({ action, user_ids: userIds, reason }),
    }),
  confirmBulkUsers: (operationId) =>
    platformRequest(`/users/bulk/${operationId}/confirm`, {
      method: "POST",
      body: JSON.stringify({ confirmation: "CONFIRM" }),
    }),
  listMemberships: (id) => platformRequest(`/users/${id}/memberships`),
  listUserAudit: (id) => platformRequest(`/users/${id}/audit`),
  listProjects: (search = "") =>
    platformRequest(`/projects${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  getProject: (id) => platformRequest(`/projects/${id}`),
  listProjectMemberships: (id) => platformRequest(`/projects/${id}/memberships`),
  updateProjectStatus: (id, status, reason) =>
    platformRequest(`/projects/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, reason }),
    }),
  updateProjectQuota: (id, values, reason) =>
    platformRequest(`/projects/${id}/quota`, {
      method: "PATCH",
      body: JSON.stringify({ ...values, reason }),
    }),
  deleteProject: (id, confirmation, reason) =>
    platformRequest(`/projects/${id}`, {
      method: "DELETE",
      body: JSON.stringify({ confirmation, reason }),
    }),
  getProjectPolicy: () => platformRequest("/platform/project-policy"),
  updateProjectPolicy: (projectCreationPolicy, reason) =>
    platformRequest("/platform/project-policy", {
      method: "PATCH",
      body: JSON.stringify({ project_creation_policy: projectCreationPolicy, reason }),
    }),
  listProviders: () => platformRequest("/ai/providers"),
  listModels: () => platformRequest("/ai/models"),
  getAiDefaults: () => platformRequest("/ai/defaults"),
  updateAiDefaults: (values, reason) =>
    platformRequest("/ai/defaults", {
      method: "PATCH",
      body: JSON.stringify({ values, reason }),
    }),
  getAiVersions: () => platformRequest("/ai/versions"),
  getAiLimits: () => platformRequest("/ai/limits"),
  updateAiLimits: (values, reason) =>
    platformRequest("/ai/limits", {
      method: "PATCH",
      body: JSON.stringify({ values, reason }),
    }),
  getAiRetrieval: () => platformRequest("/ai/retrieval"),
  updateAiRetrieval: (values, reason) =>
    platformRequest("/ai/retrieval", {
      method: "PATCH",
      body: JSON.stringify({ values, reason }),
    }),
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
  getRateLimits: () => platformRequest("/security/rate-limits"),
  updateRateLimits: (values, reason) =>
    platformRequest("/security/rate-limits", {
      method: "PATCH",
      body: JSON.stringify({ values, reason }),
    }),
  listServiceIdentities: () => platformRequest("/security/service-identities"),
  createServiceIdentity: (payload) =>
    platformRequest("/security/service-identities", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  rotateServiceIdentity: (id, secretReference, reason) =>
    platformRequest(`/security/service-identities/${id}/rotate`, {
      method: "POST",
      body: JSON.stringify({ secret_reference: secretReference, reason }),
    }),
  listBreakGlass: () => platformRequest("/security/break-glass"),
  createBreakGlass: (payload) =>
    platformRequest("/security/break-glass", { method: "POST", body: JSON.stringify(payload) }),
  revokeBreakGlass: (id, reason) =>
    platformRequest(`/security/break-glass/${id}/revoke`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  getBreakGlassPolicy: () => platformRequest("/security/break-glass-policy"),
  updateBreakGlassPolicy: (values, reason) =>
    platformRequest("/security/break-glass-policy", {
      method: "PATCH",
      body: JSON.stringify({ values, reason }),
    }),
  emergencyRevoke: (payload) =>
    platformRequest("/security/emergency-revoke", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getSecurityAudit: () => platformRequest("/security/audit"),
  getIntegrations: () => platformRequest("/integrations"),
  updateIntegrations: (values, reason) =>
    platformRequest("/integrations", { method: "PATCH", body: JSON.stringify({ values, reason }) }),
  getIntegrationHealth: () => platformRequest("/integrations/health"),
  testSmtp: (recipient, reason) =>
    platformRequest("/integrations/smtp/test", {
      method: "POST",
      body: JSON.stringify({ recipient, reason }),
    }),
  getStorage: () => platformRequest("/storage"),
  updateStorage: (values, reason) =>
    platformRequest("/storage", { method: "PATCH", body: JSON.stringify({ values, reason }) }),
  testStorage: () => platformRequest("/storage/test", { method: "POST" }),
  listSecrets: () => platformRequest("/secrets"),
  createSecret: (payload) =>
    platformRequest("/secrets", { method: "POST", body: JSON.stringify(payload) }),
  rotateSecret: (id, reference, reason) =>
    platformRequest(`/secrets/${id}/rotate`, {
      method: "POST",
      body: JSON.stringify({ reference, reason }),
    }),
  deleteSecret: (id, reason) =>
    platformRequest(`/secrets/${id}`, {
      method: "DELETE",
      body: JSON.stringify({ reason }),
    }),
  updateProvider: (id, payload) =>
    platformRequest(`/ai/providers/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  testProvider: (id) => platformRequest(`/ai/providers/${id}/test`, { method: "POST" }),
  getHealth: () => platformRequest("/health"),
  getMetrics: () => platformRequest("/operations/metrics"),
  getQueue: () => platformRequest("/operations/queue"),
  getDlq: () => platformRequest("/operations/dlq"),
  requeueDlq: (id, reason) =>
    platformRequest(`/operations/dlq/${id}/requeue`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  discardDlq: (id, reason) =>
    platformRequest(`/operations/dlq/${id}/discard`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  cancelJob: (id) => platformRequest(`/operations/jobs/${id}/cancel`, { method: "POST" }),
  getRagOperations: () => platformRequest("/operations/rag"),
  requestRagReindex: (payload) =>
    platformRequest("/operations/rag/reindex", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getCache: () => platformRequest("/operations/cache"),
  clearCache: (scope, reason) =>
    platformRequest("/operations/cache/clear", {
      method: "POST",
      body: JSON.stringify({ scope, confirmation: "CLEAR_SAFE_CACHE", reason }),
    }),
  getStorageUsage: () => platformRequest("/operations/storage-usage"),
  getRuntimeVersions: () => platformRequest("/operations/runtime-versions"),
  getMaintenance: () => platformRequest("/config/maintenance"),
  updateMaintenance: (enabled, banner, reason) =>
    platformRequest("/config/maintenance", {
      method: "PATCH",
      body: JSON.stringify({ enabled, banner, reason }),
    }),
  getPlatformConfigGroup: (name) => platformRequest(`/config/${name}`),
  updatePlatformConfigGroup: (name, values, reason) =>
    platformRequest(`/config/${name}`, {
      method: "PATCH",
      body: JSON.stringify({ values, reason }),
    }),
  getAudit: () => platformRequest("/audit"),
  exportAudit: () => downloadPlatformFile("/audit/export", "veriq-global-audit.csv"),
  listJobs: (status = "") =>
    platformRequest(`/operations/jobs${status ? `?status=${encodeURIComponent(status)}` : ""}`),
  retryJob: (id) => platformRequest(`/operations/jobs/${id}/retry`, { method: "POST" }),
};
