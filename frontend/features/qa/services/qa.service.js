import { API_URL, authenticatedFetch } from "@/shared/services/api-client";

export async function qaRequest(path, options = {}) {
  const response = await authenticatedFetch(`${API_URL}/api/qa${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(body?.error?.message || "Không thể hoàn tất yêu cầu");
    error.status = response.status;
    error.code = body?.error?.code;
    error.details = body?.error?.details;
    error.traceId = body?.trace_id;
    throw error;
  }
  return body?.data;
}

export async function downloadQaFile(path, filename) {
  const response = await authenticatedFetch(`${API_URL}/api/qa${path}`);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message || "Không thể tải tệp");
  }
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export const qaApi = {
  listProjects: (query = "") =>
    qaRequest(`/projects${query ? `?q=${encodeURIComponent(query)}` : ""}`),
  createProject: (payload) =>
    qaRequest("/projects", { method: "POST", body: JSON.stringify(payload) }),
  getProject: (id) => qaRequest(`/projects/${id}`),
  updateProject: (id, payload) =>
    qaRequest(`/projects/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  dashboard: (id) => qaRequest(`/projects/${id}/dashboard`),
  listRequirements: (id, query = "") =>
    qaRequest(`/projects/${id}/requirements${query ? `?q=${encodeURIComponent(query)}` : ""}`),
  createRequirement: (id, payload) =>
    qaRequest(`/projects/${id}/requirements`, { method: "POST", body: JSON.stringify(payload) }),
  getRequirement: (id) => qaRequest(`/requirements/${id}`),
  listRequirementVersions: (id) => qaRequest(`/requirements/${id}/versions`),
  createRequirementVersion: (id, payload) =>
    qaRequest(`/requirements/${id}/versions`, { method: "POST", body: JSON.stringify(payload) }),
  baselineRequirement: (id, revision) =>
    qaRequest(`/requirement-versions/${id}/baseline`, {
      method: "POST",
      body: JSON.stringify({ expected_revision: revision }),
    }),
  lintRequirement: (id) => qaRequest(`/requirement-versions/${id}/ai/lint`, { method: "POST" }),
  compareRequirement: (id, fromId, toId) =>
    qaRequest(`/requirements/${id}/compare`, {
      method: "POST",
      body: JSON.stringify({ from_version_id: fromId, to_version_id: toId }),
    }),
  createRequirementImport: (id, payload) =>
    qaRequest(`/projects/${id}/requirement-imports`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  confirmRequirementImport: (id, selectedIndexes) =>
    qaRequest(`/requirement-imports/${id}/confirm`, {
      method: "POST",
      body: JSON.stringify({ selected_indexes: selectedIndexes }),
    }),
  uploadRequirementImport: (id, file, format) => {
    const body = new FormData();
    body.append("format", format);
    body.append("file", file);
    return qaRequest(`/projects/${id}/requirement-imports/upload`, { method: "POST", body });
  },
  listScenarios: (id) => qaRequest(`/projects/${id}/test-scenarios`),
  createScenario: (id, payload) =>
    qaRequest(`/projects/${id}/test-scenarios`, { method: "POST", body: JSON.stringify(payload) }),
  generateScenarios: (versionId, payload) =>
    qaRequest(`/requirement-versions/${versionId}/ai/generate-scenarios`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listTestDrafts: (id) => qaRequest(`/projects/${id}/test-case-drafts`),
  createTestDraft: (id, payload) =>
    qaRequest(`/projects/${id}/test-case-drafts`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getTestDraft: (id) => qaRequest(`/test-case-drafts/${id}`),
  updateTestDraft: (id, payload) =>
    qaRequest(`/test-case-drafts/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  lintTestDraft: (id) => qaRequest(`/test-case-drafts/${id}/lint`, { method: "POST" }),
  freezeTestDraft: (id, revision, reason) =>
    qaRequest(`/test-case-drafts/${id}/freeze`, {
      method: "POST",
      body: JSON.stringify({ expected_revision: revision, change_reason: reason }),
    }),
  listTestCases: (id, query = "") =>
    qaRequest(`/projects/${id}/test-cases${query ? `?q=${encodeURIComponent(query)}` : ""}`),
  listTestVersions: (id) => qaRequest(`/test-cases/${id}/versions`),
  generateTestCases: (versionId, payload) =>
    qaRequest(`/requirement-versions/${versionId}/ai/generate-test-cases`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  findDuplicates: (id) => qaRequest(`/projects/${id}/test-cases/duplicates`),
  uploadTestImport: (id, file) => {
    const body = new FormData();
    const format = file.name.toLowerCase().endsWith(".xlsx") ? "xlsx" : "csv";
    body.append("format", format);
    body.append("file", file);
    return qaRequest(`/projects/${id}/test-case-imports/upload`, { method: "POST", body });
  },
  confirmTestImport: (id, selectedIndexes) =>
    qaRequest(`/test-case-imports/${id}/confirm`, {
      method: "POST",
      body: JSON.stringify({ selected_indexes: selectedIndexes }),
    }),
  exportTestCases: (id, format = "csv") =>
    downloadQaFile(`/projects/${id}/test-cases/export?format=${format}`, `test-cases-${id}.${format}`),
  importApiArtifact: (id, payload) =>
    qaRequest(`/projects/${id}/api-imports`, { method: "POST", body: JSON.stringify(payload) }),
  listApiOperations: (id) => qaRequest(`/projects/${id}/api-operations`),
  generateApiTests: (id) => qaRequest(`/api-operations/${id}/generate-tests`, { method: "POST" }),
  traceability: (id) => qaRequest(`/projects/${id}/traceability`),
  exportTraceability: (id) =>
    downloadQaFile(`/projects/${id}/traceability/export`, `traceability-${id}.csv`),
  coverage: (id) => qaRequest(`/projects/${id}/coverage`),
  recoverTrace: (id) => qaRequest(`/projects/${id}/trace-recovery`, { method: "POST" }),
  createTrace: (payload) =>
    qaRequest("/trace-links", { method: "POST", body: JSON.stringify(payload) }),
  confirmTrace: (id) => qaRequest(`/trace-links/${id}/confirm`, { method: "POST" }),
  rejectTrace: (id) => qaRequest(`/trace-links/${id}/reject`, { method: "POST" }),
  listChangeSets: (id) => qaRequest(`/projects/${id}/change-sets`),
  createChangeSet: (requirementId, payload) =>
    qaRequest(`/requirements/${requirementId}/change-sets`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getChangeSet: (id) => qaRequest(`/change-sets/${id}`),
  analyzeImpact: (id) => qaRequest(`/change-sets/${id}/impact-analysis`, { method: "POST" }),
  getImpact: (id) => qaRequest(`/impact-analyses/${id}`),
  createProposals: (id) =>
    qaRequest(`/impact-analyses/${id}/maintenance-proposals`, { method: "POST" }),
  listProposals: (id, status = "PENDING") =>
    qaRequest(`/projects/${id}/maintenance-proposals?status=${status}`),
  acceptProposal: (id, payload, edited = false) =>
    qaRequest(`/maintenance-proposals/${id}/${edited ? "accept-with-edit" : "accept"}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  rejectProposal: (id, payload) =>
    qaRequest(`/maintenance-proposals/${id}/reject`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  regression: (id) => qaRequest(`/change-sets/${id}/regression-recommendation`, { method: "POST" }),
  listPlans: (id) => qaRequest(`/projects/${id}/test-plans`),
  createPlan: (payload) =>
    qaRequest("/test-plans", { method: "POST", body: JSON.stringify(payload) }),
  listSuites: (id) => qaRequest(`/projects/${id}/test-suites`),
  createSuite: (payload) =>
    qaRequest("/test-suites", { method: "POST", body: JSON.stringify(payload) }),
  listRuns: (id) => qaRequest(`/projects/${id}/test-runs`),
  createRun: (payload) =>
    qaRequest("/test-runs", { method: "POST", body: JSON.stringify(payload) }),
  getRun: (id) => qaRequest(`/test-runs/${id}`),
  startRun: (id) => qaRequest(`/test-runs/${id}/start`, { method: "POST" }),
  recordResult: (runId, versionId, payload) =>
    qaRequest(`/test-runs/${runId}/results/${versionId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  completeRun: (id) => qaRequest(`/test-runs/${id}/complete`, { method: "POST" }),
  exportRunReport: (id) => downloadQaFile(`/test-runs/${id}/report`, `test-run-${id}.csv`),
  listDefects: (id) => qaRequest(`/projects/${id}/defects`),
  exportDefects: (id) => downloadQaFile(`/projects/${id}/defects/export`, `defects-${id}.csv`),
  createDefect: (id, payload) =>
    qaRequest(`/projects/${id}/defects`, { method: "POST", body: JSON.stringify(payload) }),
  transitionDefect: (id, payload) =>
    qaRequest(`/defects/${id}/transition`, { method: "POST", body: JSON.stringify(payload) }),
  searchKnowledge: (id, payload) =>
    qaRequest(`/projects/${id}/knowledge/search`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  audit: (id) => qaRequest(`/projects/${id}/audit`),
  maintenanceAnalytics: (id) => qaRequest(`/projects/${id}/maintenance-analytics`),
};
