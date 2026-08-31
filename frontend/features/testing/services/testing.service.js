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

function listQuery(value) {
  if (!value) return "";
  if (typeof value === "string") return `q=${encodeURIComponent(value)}`;
  if (value instanceof URLSearchParams) return value.toString();
  const query = new URLSearchParams();
  Object.entries(value).forEach(([key, item]) => {
    if (item !== "" && item !== null && item !== undefined) query.set(key, String(item));
  });
  return query.toString();
}

async function listPage(path, value) {
  const query = listQuery(value);
  const result = await qaRequest(`${path}${query ? `?${query}` : ""}`);
  if (Array.isArray(result)) {
    return {
      items: result,
      page: 1,
      page_size: result.length,
      total: result.length,
      total_pages: result.length ? 1 : 0,
    };
  }
  return result;
}

export const testingApi = {
  listProjects: (query = "", status = "active") => {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (status !== "all") params.set("status", status);
    return qaRequest(`/projects?${params.toString()}`);
  },
  createProject: (payload) =>
    qaRequest("/projects", { method: "POST", body: JSON.stringify(payload) }),
  getProject: (id) => qaRequest(`/projects/${id}`),
  listMembers: (id) => qaRequest(`/projects/${id}/members`),
  addMember: (id, payload) =>
    qaRequest(`/projects/${id}/members`, { method: "POST", body: JSON.stringify(payload) }),
  inviteMember: (id, payload) =>
    qaRequest(`/projects/${id}/invitations`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  resendMemberInvite: (id, userId) =>
    qaRequest(`/projects/${id}/members/${userId}/resend-invite`, { method: "POST" }),
  cancelMemberInvite: (id, userId) =>
    qaRequest(`/projects/${id}/members/${userId}/cancel-invite`, { method: "POST" }),
  updateMember: (id, userId, payload) =>
    qaRequest(`/projects/${id}/members/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  removeMember: (id, userId) =>
    qaRequest(`/projects/${id}/members/${userId}`, { method: "DELETE" }),
  updateProject: (id, payload) =>
    qaRequest(`/projects/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  archiveProject: (id, payload) =>
    qaRequest(`/projects/${id}/archive`, { method: "POST", body: JSON.stringify(payload) }),
  restoreProject: (id, payload) =>
    qaRequest(`/projects/${id}/restore`, { method: "POST", body: JSON.stringify(payload) }),
  dashboard: (id) => qaRequest(`/projects/${id}/dashboard`),
  listRequirementPage: (id, query = "") => listPage(`/projects/${id}/requirements`, query),
  listRequirements: (id, query = "") =>
    listPage(`/projects/${id}/requirements`, query).then((result) => result.items),
  createRequirement: (id, payload) =>
    qaRequest(`/projects/${id}/requirements`, { method: "POST", body: JSON.stringify(payload) }),
  updateRequirementDraft: (projectId, requirementId, payload) =>
    qaRequest(`/projects/${projectId}/requirements/${requirementId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
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
  confirmRequirementImport: (id, selectedIndexes, expectedRevision) =>
    qaRequest(`/requirement-imports/${id}/confirm`, {
      method: "POST",
      body: JSON.stringify({
        selected_indexes: selectedIndexes,
        expected_revision: expectedRevision,
      }),
    }),
  updateRequirementImport: (id, payload) =>
    qaRequest(`/requirement-imports/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  uploadRequirementImport: (id, file, format) => {
    const body = new FormData();
    body.append("format", format);
    body.append("file", file);
    return qaRequest(`/projects/${id}/requirement-imports/upload`, { method: "POST", body });
  },
  createRequirementDocument: (id, payload) =>
    qaRequest(`/projects/${id}/requirement-documents`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  uploadRequirementDocument: (id, file, format) => {
    const body = new FormData();
    body.append("format", format);
    body.append("file", file);
    return qaRequest(`/projects/${id}/requirement-documents/upload`, { method: "POST", body });
  },
  listRequirementDocuments: (id, query = "") =>
    qaRequest(`/projects/${id}/requirement-documents${query ? `?${query}` : ""}`),
  createKnowledgeSource: (id, payload) =>
    qaRequest(`/projects/${id}/knowledge-sources`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listKnowledgeSources: (id, includeArchived = false) =>
    qaRequest(`/projects/${id}/knowledge-sources?include_archived=${includeArchived}`),
  archiveKnowledgeSource: (id, payload) =>
    qaRequest(`/knowledge-sources/${id}/archive`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  registerAttachment: (id, payload) =>
    qaRequest(`/projects/${id}/attachments`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listAttachments: (id, query = "") =>
    qaRequest(`/projects/${id}/attachments${query ? `?${query}` : ""}`),
  deleteAttachment: (id) => qaRequest(`/attachments/${id}`, { method: "DELETE" }),
  moderateAttachment: (id, payload) =>
    qaRequest(`/attachments/${id}/moderate`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getRequirementDocument: (id) => qaRequest(`/requirement-documents/${id}`),
  updateRequirementDocument: (id, payload) =>
    qaRequest(`/requirement-documents/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  reindexRequirementDocument: (id) =>
    qaRequest(`/requirement-documents/${id}/reindex`, { method: "POST" }),
  downloadRequirementDocument: (id, filename) =>
    downloadQaFile(`/requirement-documents/${id}/download`, filename),
  archiveRequirementDocument: (id, payload) =>
    qaRequest(`/requirement-documents/${id}/archive`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  restoreRequirementDocument: (id, payload) =>
    qaRequest(`/requirement-documents/${id}/restore`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  retryRequirementDocumentParse: (id, revision) =>
    qaRequest(`/requirement-documents/${id}/retry-parse`, {
      method: "POST",
      body: JSON.stringify({ expected_revision: revision }),
    }),
  extractRequirementDocument: (id, idempotencyKey = crypto.randomUUID()) =>
    qaRequest(`/requirement-documents/${id}/extract`, {
      method: "POST",
      body: JSON.stringify({ idempotency_key: idempotencyKey }),
    }),
  submitRequirementReview: (projectId, requirementId, payload) =>
    qaRequest(`/projects/${projectId}/requirements/${requirementId}/submit-review`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  requestRequirementChanges: (projectId, requirementId, payload) =>
    qaRequest(`/projects/${projectId}/requirements/${requirementId}/request-changes`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  approveRequirement: (projectId, requirementId, payload) =>
    qaRequest(`/projects/${projectId}/requirements/${requirementId}/approve`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  obsoleteRequirement: (id, payload) =>
    qaRequest(`/requirements/${id}/obsolete`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  restoreRequirement: (id, payload) =>
    qaRequest(`/requirements/${id}/restore`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  submitTestCaseReview: (projectId, draftId, payload) =>
    qaRequest(`/projects/${projectId}/test-cases/${draftId}/submit-review`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  requestTestCaseChanges: (projectId, draftId, payload) =>
    qaRequest(`/projects/${projectId}/test-cases/${draftId}/request-changes`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listScenarios: (id, query = "") => {
    const value = listQuery(query);
    return qaRequest(`/projects/${id}/test-scenarios${value ? `?${value}` : ""}`);
  },
  listDataSets: (id, query = "") =>
    qaRequest(`/projects/${id}/data-sets${query ? `?q=${encodeURIComponent(query)}` : ""}`),
  createDataSet: (id, payload) =>
    qaRequest(`/projects/${id}/data-sets`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listDataSetVersions: (id) => qaRequest(`/data-sets/${id}/versions`),
  createDataSetVersion: (id, payload) =>
    qaRequest(`/data-sets/${id}/versions`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createScenario: (id, payload) =>
    qaRequest(`/projects/${id}/test-scenarios`, { method: "POST", body: JSON.stringify(payload) }),
  updateScenario: (id, payload) =>
    qaRequest(`/test-scenarios/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  cloneScenario: (id) => qaRequest(`/test-scenarios/${id}/clone`, { method: "POST" }),
  archiveScenario: (id, payload) =>
    qaRequest(`/test-scenarios/${id}/archive`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
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
  listTestCasePage: (id, query = "") => listPage(`/projects/${id}/test-cases`, query),
  listTestCases: (id, query = "") =>
    listPage(`/projects/${id}/test-cases`, query).then((result) => result.items),
  listTestVersions: (id) => qaRequest(`/test-cases/${id}/versions`),
  cloneTestCase: (id, payload) =>
    qaRequest(`/test-cases/${id}/clone`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  obsoleteTestCase: (id, payload) =>
    qaRequest(`/test-cases/${id}/obsolete`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  restoreTestCase: (id, payload) =>
    qaRequest(`/test-cases/${id}/restore`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  generateTestCases: (versionId, payload) =>
    qaRequest(`/requirement-versions/${versionId}/ai/generate-test-cases`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  generateProjectTestCases: (projectId, payload) =>
    qaRequest(`/projects/${projectId}/test-cases/generate`, {
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
    downloadQaFile(
      `/projects/${id}/test-cases/export?format=${format}`,
      `test-cases-${id}.${format}`,
    ),
  importApiArtifact: (id, payload) =>
    qaRequest(`/projects/${id}/api-imports`, { method: "POST", body: JSON.stringify(payload) }),
  listApiOperations: (id) => qaRequest(`/projects/${id}/api-operations`),
  generateApiTests: (id) => qaRequest(`/api-operations/${id}/generate-tests`, { method: "POST" }),
  traceability: (id) => qaRequest(`/projects/${id}/traceability`),
  exportTraceability: (id) =>
    downloadQaFile(`/projects/${id}/traceability/export`, `traceability-${id}.csv`),
  coverage: (id, scope = {}) => {
    const query = listQuery(scope);
    return qaRequest(`/projects/${id}/coverage${query ? `?${query}` : ""}`);
  },
  listCoverageSnapshots: (id) => qaRequest(`/projects/${id}/coverage-snapshots`),
  createCoverageSnapshot: (id, payload = {}) =>
    qaRequest(`/projects/${id}/coverage-snapshots`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  recoverTrace: (id) => qaRequest(`/projects/${id}/trace-recovery`, { method: "POST" }),
  createTrace: (payload) =>
    qaRequest("/trace-links", { method: "POST", body: JSON.stringify(payload) }),
  confirmTrace: (id) => qaRequest(`/trace-links/${id}/confirm`, { method: "POST" }),
  rejectTrace: (id) => qaRequest(`/trace-links/${id}/reject`, { method: "POST" }),
  revokeTrace: (id) => qaRequest(`/trace-links/${id}`, { method: "DELETE" }),
  listReviewComments: (projectId, query = "") =>
    qaRequest(`/projects/${projectId}/review-comments${query ? `?${query}` : ""}`),
  createReviewComment: (projectId, payload) =>
    qaRequest(`/projects/${projectId}/review-comments`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  resolveReviewComment: (id, reason = "") =>
    qaRequest(`/review-comments/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  reopenReviewComment: (id, reason = "") =>
    qaRequest(`/review-comments/${id}/reopen`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  listChangeSets: (id, query = "") => {
    const value = listQuery(query);
    return qaRequest(`/projects/${id}/change-sets${value ? `?${value}` : ""}`);
  },
  createChangeSet: (requirementId, payload) =>
    qaRequest(`/requirements/${requirementId}/change-sets`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getChangeSet: (id) => qaRequest(`/change-sets/${id}`),
  reviewChangeSet: (id, payload) =>
    qaRequest(`/change-sets/${id}/review`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  analyzeImpact: (id) => qaRequest(`/change-sets/${id}/impact-analysis`, { method: "POST" }),
  getChangeSetImpact: (id) => qaRequest(`/change-sets/${id}/impact-analysis`),
  getImpact: (id) => qaRequest(`/impact-analyses/${id}`),
  reviewImpact: (id, payload) =>
    qaRequest(`/impact-analyses/${id}/review`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createProposals: (id) =>
    qaRequest(`/impact-analyses/${id}/maintenance-proposals`, { method: "POST" }),
  listProposals: (id, query = { status: "PENDING" }) => {
    const value = listQuery(typeof query === "string" ? { status: query } : query);
    return qaRequest(`/projects/${id}/maintenance-proposals${value ? `?${value}` : ""}`);
  },
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
  regenerateProposal: (id, payload) =>
    qaRequest(`/maintenance-proposals/${id}/regenerate`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkTags: (projectId, payload) =>
    qaRequest(`/projects/${projectId}/bulk/tags`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkAddToSuite: (projectId, payload) =>
    qaRequest(`/projects/${projectId}/bulk/test-cases/add-to-suite`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkMarkReviewRequired: (projectId, payload) =>
    qaRequest(`/projects/${projectId}/bulk/test-cases/mark-review-required`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkArchive: (projectId, payload) =>
    qaRequest(`/projects/${projectId}/bulk/archive`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkGenerateProposals: (projectId, payload) =>
    qaRequest(`/projects/${projectId}/bulk/impact-proposals`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkApproveProposals: (projectId, payload) =>
    qaRequest(`/projects/${projectId}/bulk/approve-proposals`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  regression: (id) => qaRequest(`/change-sets/${id}/regression-recommendation`, { method: "POST" }),
  getChangeSetRegression: (id) => qaRequest(`/change-sets/${id}/regression-recommendation`),
  approveRegression: (id, payload) =>
    qaRequest(`/regression-recommendations/${id}/approve`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listPlans: (id, query = "") => {
    const value = listQuery(query);
    return qaRequest(`/projects/${id}/test-plans${value ? `?${value}` : ""}`);
  },
  createPlan: (payload) =>
    qaRequest("/test-plans", { method: "POST", body: JSON.stringify(payload) }),
  updatePlan: (id, payload) =>
    qaRequest(`/test-plans/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  submitPlan: (id, payload) =>
    qaRequest(`/test-plans/${id}/submit-review`, { method: "POST", body: JSON.stringify(payload) }),
  approvePlan: (id, payload) =>
    qaRequest(`/test-plans/${id}/approve`, { method: "POST", body: JSON.stringify(payload) }),
  archivePlan: (id, payload) =>
    qaRequest(`/test-plans/${id}/archive`, { method: "POST", body: JSON.stringify(payload) }),
  clonePlan: (id) => qaRequest(`/test-plans/${id}/clone`, { method: "POST" }),
  listSuites: (id, query = "") => {
    const value = listQuery(query);
    return qaRequest(`/projects/${id}/test-suites${value ? `?${value}` : ""}`);
  },
  createSuite: (payload) =>
    qaRequest("/test-suites", { method: "POST", body: JSON.stringify(payload) }),
  updateSuite: (id, payload) =>
    qaRequest(`/test-suites/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  cloneSuite: (id) => qaRequest(`/test-suites/${id}/clone`, { method: "POST" }),
  archiveSuite: (id, payload) =>
    qaRequest(`/test-suites/${id}/archive`, { method: "POST", body: JSON.stringify(payload) }),
  listRunPage: (id, query = "") => listPage(`/projects/${id}/test-runs`, query),
  listRuns: (id, query = "") =>
    listPage(`/projects/${id}/test-runs`, query).then((result) => result.items),
  listResults: (id, status = "") =>
    qaRequest(
      `/projects/${id}/test-results${status ? `?status=${encodeURIComponent(status)}` : ""}`,
    ),
  createRun: (payload) =>
    qaRequest("/test-runs", { method: "POST", body: JSON.stringify(payload) }),
  getRun: (id) => qaRequest(`/test-runs/${id}`),
  startRun: (id) => qaRequest(`/test-runs/${id}/start`, { method: "POST" }),
  recordResult: (runId, versionId, payload) =>
    qaRequest(`/test-runs/${runId}/results/${versionId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateExecution: (projectId, executionId, payload) =>
    qaRequest(`/projects/${projectId}/test-executions/${executionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  completeRun: (id) => qaRequest(`/test-runs/${id}/complete`, { method: "POST" }),
  abortRun: (id, reason) =>
    qaRequest(`/test-runs/${id}/abort`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  exportRunReport: (id) => downloadQaFile(`/test-runs/${id}/report`, `test-run-${id}.csv`),
  listDefectPage: (id, query = "") => listPage(`/projects/${id}/defects`, query),
  listDefects: (id, query = "") =>
    listPage(`/projects/${id}/defects`, query).then((result) => result.items),
  findDuplicateDefects: (id) => qaRequest(`/projects/${id}/defects/duplicates`),
  findDefectTraceCandidates: (id) => qaRequest(`/defects/${id}/trace-candidates`),
  exportDefects: (id) => downloadQaFile(`/projects/${id}/defects/export`, `defects-${id}.csv`),
  createDefect: (id, payload) =>
    qaRequest(`/projects/${id}/defects`, { method: "POST", body: JSON.stringify(payload) }),
  updateDefect: (id, payload) =>
    qaRequest(`/defects/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  transitionDefect: (id, payload) =>
    qaRequest(`/defects/${id}/transition`, { method: "POST", body: JSON.stringify(payload) }),
  retestDefect: (projectId, defectId, payload) =>
    qaRequest(`/projects/${projectId}/defects/${defectId}/retest`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  searchKnowledge: (id, payload) =>
    qaRequest(`/projects/${id}/knowledge/search`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  askProject: (id, payload) =>
    qaRequest(`/projects/${id}/ai/ask`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  audit: (id) => qaRequest(`/projects/${id}/audit`),
  maintenanceAnalytics: (id) => qaRequest(`/projects/${id}/maintenance-analytics`),
  aiAnalytics: (id) => qaRequest(`/projects/${id}/ai-analytics`),
  executionReport: (id, scope = {}) =>
    qaRequest(`/projects/${id}/reports/execution?${listQuery(scope)}`),
  defectReport: (id, scope = {}) =>
    qaRequest(`/projects/${id}/reports/defects?${listQuery(scope)}`),
  projectActivity: (id) => qaRequest(`/projects/${id}/activity`),
  operations: (query = "") => qaRequest(`/operations${query ? `?${query}` : ""}`),
  retryOperationJob: (jobId) => qaRequest(`/operations/jobs/${jobId}/retry`, { method: "POST" }),
};
