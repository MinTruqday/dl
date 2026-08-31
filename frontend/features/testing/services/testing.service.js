import { API_URL, authenticatedFetch } from "@/shared/services/api-client";

export async function qaRequest(path, options = {}) {
  const response = await authenticatedFetch(`${API_URL}/kiem-thu${path}`, {
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
  const response = await authenticatedFetch(`${API_URL}/kiem-thu${path}`);
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
    return qaRequest(`/du-an?${params.toString()}`);
  },
  createProject: (payload) =>
    qaRequest("/du-an", { method: "POST", body: JSON.stringify(payload) }),
  getProject: (id) => qaRequest(`/du-an/${id}`),
  listMembers: (id) => qaRequest(`/du-an/${id}/thanh-vien`),
  addMember: (id, payload) =>
    qaRequest(`/du-an/${id}/thanh-vien`, { method: "POST", body: JSON.stringify(payload) }),
  inviteMember: (id, payload) =>
    qaRequest(`/du-an/${id}/loi-moi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  resendMemberInvite: (id, userId) =>
    qaRequest(`/du-an/${id}/thanh-vien/${userId}/gui-lai-loi-moi`, { method: "POST" }),
  cancelMemberInvite: (id, userId) =>
    qaRequest(`/du-an/${id}/thanh-vien/${userId}/huy-loi-moi`, { method: "POST" }),
  updateMember: (id, userId, payload) =>
    qaRequest(`/du-an/${id}/thanh-vien/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  removeMember: (id, userId) =>
    qaRequest(`/du-an/${id}/thanh-vien/${userId}`, { method: "DELETE" }),
  updateProject: (id, payload) =>
    qaRequest(`/du-an/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  archiveProject: (id, payload) =>
    qaRequest(`/du-an/${id}/luu-tru`, { method: "POST", body: JSON.stringify(payload) }),
  restoreProject: (id, payload) =>
    qaRequest(`/du-an/${id}/khoi-phuc`, { method: "POST", body: JSON.stringify(payload) }),
  dashboard: (id) => qaRequest(`/du-an/${id}/tong-quan`),
  listRequirementPage: (id, query = "") => listPage(`/du-an/${id}/yeu-cau`, query),
  listRequirements: (id, query = "") =>
    listPage(`/du-an/${id}/yeu-cau`, query).then((result) => result.items),
  createRequirement: (id, payload) =>
    qaRequest(`/du-an/${id}/yeu-cau`, { method: "POST", body: JSON.stringify(payload) }),
  updateRequirementDraft: (projectId, requirementId, payload) =>
    qaRequest(`/du-an/${projectId}/yeu-cau/${requirementId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  getRequirement: (id) => qaRequest(`/yeu-cau/${id}`),
  listRequirementVersions: (id) => qaRequest(`/yeu-cau/${id}/phien-ban`),
  createRequirementVersion: (id, payload) =>
    qaRequest(`/yeu-cau/${id}/phien-ban`, { method: "POST", body: JSON.stringify(payload) }),
  baselineRequirement: (id, revision) =>
    qaRequest(`/phien-ban-yeu-cau/${id}/chot-chuan`, {
      method: "POST",
      body: JSON.stringify({ expected_revision: revision }),
    }),
  lintRequirement: (id) => qaRequest(`/phien-ban-yeu-cau/${id}/ai/kiem-tra`, { method: "POST" }),
  compareRequirement: (id, fromId, toId) =>
    qaRequest(`/yeu-cau/${id}/so-sanh`, {
      method: "POST",
      body: JSON.stringify({ from_version_id: fromId, to_version_id: toId }),
    }),
  createRequirementImport: (id, payload) =>
    qaRequest(`/du-an/${id}/nhap-yeu-cau`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  confirmRequirementImport: (id, selectedIndexes, expectedRevision) =>
    qaRequest(`/nhap-yeu-cau/${id}/xac-nhan`, {
      method: "POST",
      body: JSON.stringify({
        selected_indexes: selectedIndexes,
        expected_revision: expectedRevision,
      }),
    }),
  updateRequirementImport: (id, payload) =>
    qaRequest(`/nhap-yeu-cau/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  uploadRequirementImport: (id, file, format) => {
    const body = new FormData();
    body.append("format", format);
    body.append("file", file);
    return qaRequest(`/du-an/${id}/nhap-yeu-cau/tai-len`, { method: "POST", body });
  },
  createRequirementDocument: (id, payload) =>
    qaRequest(`/du-an/${id}/tai-lieu-yeu-cau`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  uploadRequirementDocument: (id, file, format) => {
    const body = new FormData();
    body.append("format", format);
    body.append("file", file);
    return qaRequest(`/du-an/${id}/tai-lieu-yeu-cau/tai-len`, { method: "POST", body });
  },
  listRequirementDocuments: (id, query = "") =>
    qaRequest(`/du-an/${id}/tai-lieu-yeu-cau${query ? `?${query}` : ""}`),
  createKnowledgeSource: (id, payload) =>
    qaRequest(`/du-an/${id}/nguon-tri-thuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listKnowledgeSources: (id, includeArchived = false) =>
    qaRequest(`/du-an/${id}/nguon-tri-thuc?include_archived=${includeArchived}`),
  archiveKnowledgeSource: (id, payload) =>
    qaRequest(`/nguon-tri-thuc/${id}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  registerAttachment: (id, payload) =>
    qaRequest(`/du-an/${id}/tep-dinh-kem`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listAttachments: (id, query = "") =>
    qaRequest(`/du-an/${id}/tep-dinh-kem${query ? `?${query}` : ""}`),
  deleteAttachment: (id) => qaRequest(`/tep-dinh-kem/${id}`, { method: "DELETE" }),
  moderateAttachment: (id, payload) =>
    qaRequest(`/tep-dinh-kem/${id}/kiem-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getRequirementDocument: (id) => qaRequest(`/tai-lieu-yeu-cau/${id}`),
  updateRequirementDocument: (id, payload) =>
    qaRequest(`/tai-lieu-yeu-cau/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  reindexRequirementDocument: (id) =>
    qaRequest(`/tai-lieu-yeu-cau/${id}/lap-chi-muc-lai`, { method: "POST" }),
  reindexKnowledgeSource: (id) =>
    qaRequest(`/tai-lieu-yeu-cau/${id}/lap-chi-muc-lai`, { method: "POST" }),
  downloadRequirementDocument: (id, filename) =>
    downloadQaFile(`/tai-lieu-yeu-cau/${id}/tai-xuong`, filename),
  archiveRequirementDocument: (id, payload) =>
    qaRequest(`/tai-lieu-yeu-cau/${id}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  restoreRequirementDocument: (id, payload) =>
    qaRequest(`/tai-lieu-yeu-cau/${id}/khoi-phuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  retryRequirementDocumentParse: (id, revision) =>
    qaRequest(`/tai-lieu-yeu-cau/${id}/thu-lai-phan-tich`, {
      method: "POST",
      body: JSON.stringify({ expected_revision: revision }),
    }),
  extractRequirementDocument: (id, idempotencyKey = crypto.randomUUID()) =>
    qaRequest(`/tai-lieu-yeu-cau/${id}/trich-xuat`, {
      method: "POST",
      body: JSON.stringify({ idempotency_key: idempotencyKey }),
    }),
  submitRequirementReview: (projectId, requirementId, payload) =>
    qaRequest(`/du-an/${projectId}/yeu-cau/${requirementId}/gui-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  requestRequirementChanges: (projectId, requirementId, payload) =>
    qaRequest(`/du-an/${projectId}/yeu-cau/${requirementId}/yeu-cau-chinh-sua`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  approveRequirement: (projectId, requirementId, payload) =>
    qaRequest(`/du-an/${projectId}/yeu-cau/${requirementId}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  obsoleteRequirement: (id, payload) =>
    qaRequest(`/yeu-cau/${id}/ngung-hieu-luc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  restoreRequirement: (id, payload) =>
    qaRequest(`/yeu-cau/${id}/khoi-phuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  submitTestCaseReview: (projectId, draftId, payload) =>
    qaRequest(`/du-an/${projectId}/ca-kiem-thu/${draftId}/gui-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  requestTestCaseChanges: (projectId, draftId, payload) =>
    qaRequest(`/du-an/${projectId}/ca-kiem-thu/${draftId}/yeu-cau-chinh-sua`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listScenarios: (id, query = "") => {
    const value = listQuery(query);
    return qaRequest(`/du-an/${id}/kich-ban-kiem-thu${value ? `?${value}` : ""}`);
  },
  listDataSets: (id, query = "") =>
    qaRequest(`/du-an/${id}/bo-du-lieu${query ? `?q=${encodeURIComponent(query)}` : ""}`),
  createDataSet: (id, payload) =>
    qaRequest(`/du-an/${id}/bo-du-lieu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listDataSetVersions: (id) => qaRequest(`/bo-du-lieu/${id}/phien-ban`),
  createDataSetVersion: (id, payload) =>
    qaRequest(`/bo-du-lieu/${id}/phien-ban`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createScenario: (id, payload) =>
    qaRequest(`/du-an/${id}/kich-ban-kiem-thu`, { method: "POST", body: JSON.stringify(payload) }),
  updateScenario: (id, payload) =>
    qaRequest(`/kich-ban-kiem-thu/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  cloneScenario: (id) => qaRequest(`/kich-ban-kiem-thu/${id}/nhan-ban`, { method: "POST" }),
  archiveScenario: (id, payload) =>
    qaRequest(`/kich-ban-kiem-thu/${id}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  generateScenarios: (versionId, payload) =>
    qaRequest(`/phien-ban-yeu-cau/${versionId}/ai/sinh-kich-ban`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listTestDrafts: (id) => qaRequest(`/du-an/${id}/ban-nhap-ca-kiem-thu`),
  createTestDraft: (id, payload) =>
    qaRequest(`/du-an/${id}/ban-nhap-ca-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getTestDraft: (id) => qaRequest(`/ban-nhap-ca-kiem-thu/${id}`),
  updateTestDraft: (id, payload) =>
    qaRequest(`/ban-nhap-ca-kiem-thu/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  lintTestDraft: (id) => qaRequest(`/ban-nhap-ca-kiem-thu/${id}/kiem-tra`, { method: "POST" }),
  freezeTestDraft: (id, revision, reason) =>
    qaRequest(`/ban-nhap-ca-kiem-thu/${id}/dong-bang`, {
      method: "POST",
      body: JSON.stringify({ expected_revision: revision, change_reason: reason }),
    }),
  listTestCasePage: (id, query = "") => listPage(`/du-an/${id}/ca-kiem-thu`, query),
  listTestCases: (id, query = "") =>
    listPage(`/du-an/${id}/ca-kiem-thu`, query).then((result) => result.items),
  listTestVersions: (id) => qaRequest(`/ca-kiem-thu/${id}/phien-ban`),
  cloneTestCase: (id, payload) =>
    qaRequest(`/ca-kiem-thu/${id}/nhan-ban`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  obsoleteTestCase: (id, payload) =>
    qaRequest(`/ca-kiem-thu/${id}/ngung-hieu-luc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  restoreTestCase: (id, payload) =>
    qaRequest(`/ca-kiem-thu/${id}/khoi-phuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  generateTestCases: (versionId, payload) =>
    qaRequest(`/phien-ban-yeu-cau/${versionId}/ai/sinh-ca-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  generateProjectTestCases: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/ca-kiem-thu/sinh`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  findDuplicates: (id) => qaRequest(`/du-an/${id}/ca-kiem-thu/trung-lap`),
  uploadTestImport: (id, file) => {
    const body = new FormData();
    const format = file.name.toLowerCase().endsWith(".xlsx") ? "xlsx" : "csv";
    body.append("format", format);
    body.append("file", file);
    return qaRequest(`/du-an/${id}/nhap-ca-kiem-thu/tai-len`, { method: "POST", body });
  },
  confirmTestImport: (id, selectedIndexes) =>
    qaRequest(`/nhap-ca-kiem-thu/${id}/xac-nhan`, {
      method: "POST",
      body: JSON.stringify({ selected_indexes: selectedIndexes }),
    }),
  exportTestCases: (id, format = "csv") =>
    downloadQaFile(`/du-an/${id}/ca-kiem-thu/xuat?format=${format}`, `test-cases-${id}.${format}`),
  importApiArtifact: (id, payload) =>
    qaRequest(`/du-an/${id}/nhap-dac-ta`, { method: "POST", body: JSON.stringify(payload) }),
  listApiOperations: (id) => qaRequest(`/du-an/${id}/thao-tac-dac-ta`),
  generateApiTests: (id) => qaRequest(`/thao-tac-dac-ta/${id}/sinh-kiem-thu`, { method: "POST" }),
  traceability: (id) => qaRequest(`/du-an/${id}/truy-vet`),
  exportTraceability: (id) =>
    downloadQaFile(`/du-an/${id}/truy-vet/xuat`, `traceability-${id}.csv`),
  coverage: (id, scope = {}) => {
    const query = listQuery(scope);
    return qaRequest(`/du-an/${id}/do-phu${query ? `?${query}` : ""}`);
  },
  listCoverageSnapshots: (id) => qaRequest(`/du-an/${id}/anh-chup-do-phu`),
  createCoverageSnapshot: (id, payload = {}) =>
    qaRequest(`/du-an/${id}/anh-chup-do-phu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  recoverTrace: (id) => qaRequest(`/du-an/${id}/khoi-phuc-truy-vet`, { method: "POST" }),
  createTrace: (payload) =>
    qaRequest("/lien-ket-truy-vet", { method: "POST", body: JSON.stringify(payload) }),
  confirmTrace: (id) => qaRequest(`/lien-ket-truy-vet/${id}/xac-nhan`, { method: "POST" }),
  rejectTrace: (id) => qaRequest(`/lien-ket-truy-vet/${id}/tu-choi`, { method: "POST" }),
  revokeTrace: (id) => qaRequest(`/lien-ket-truy-vet/${id}`, { method: "DELETE" }),
  listReviewComments: (projectId, query = "") =>
    qaRequest(`/du-an/${projectId}/nhan-xet-ra-soat${query ? `?${query}` : ""}`),
  createReviewComment: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/nhan-xet-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  resolveReviewComment: (id, reason = "") =>
    qaRequest(`/nhan-xet-ra-soat/${id}/giai-quyet`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  reopenReviewComment: (id, reason = "") =>
    qaRequest(`/nhan-xet-ra-soat/${id}/mo-lai`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  listChangeSets: (id, query = "") => {
    const value = listQuery(query);
    return qaRequest(`/du-an/${id}/bo-thay-doi${value ? `?${value}` : ""}`);
  },
  createChangeSet: (requirementId, payload) =>
    qaRequest(`/yeu-cau/${requirementId}/bo-thay-doi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getChangeSet: (id) => qaRequest(`/bo-thay-doi/${id}`),
  reviewChangeSet: (id, payload) =>
    qaRequest(`/bo-thay-doi/${id}/ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  analyzeImpact: (id) => qaRequest(`/bo-thay-doi/${id}/phan-tich-anh-huong`, { method: "POST" }),
  getChangeSetImpact: (id) => qaRequest(`/bo-thay-doi/${id}/phan-tich-anh-huong`),
  getImpact: (id) => qaRequest(`/phan-tich-anh-huong/${id}`),
  reviewImpact: (id, payload) =>
    qaRequest(`/phan-tich-anh-huong/${id}/ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createProposals: (id) =>
    qaRequest(`/phan-tich-anh-huong/${id}/de-xuat-bao-tri`, { method: "POST" }),
  listProposals: (id, query = { status: "PENDING" }) => {
    const value = listQuery(typeof query === "string" ? { status: query } : query);
    return qaRequest(`/du-an/${id}/de-xuat-bao-tri${value ? `?${value}` : ""}`);
  },
  acceptProposal: (id, payload, edited = false) =>
    qaRequest(`/de-xuat-bao-tri/${id}/${edited ? "accept-with-edit" : "accept"}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  rejectProposal: (id, payload) =>
    qaRequest(`/de-xuat-bao-tri/${id}/tu-choi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  regenerateProposal: (id, payload) =>
    qaRequest(`/de-xuat-bao-tri/${id}/sinh-lai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkTags: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/nhan`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkAddToSuite: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/ca-kiem-thu/them-vao-bo-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkMarkReviewRequired: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/ca-kiem-thu/danh-dau-can-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkArchive: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkGenerateProposals: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/de-xuat-anh-huong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkApproveProposals: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/phe-duyet-de-xuat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  regression: (id) => qaRequest(`/bo-thay-doi/${id}/de-xuat-hoi-quy`, { method: "POST" }),
  getChangeSetRegression: (id) => qaRequest(`/bo-thay-doi/${id}/de-xuat-hoi-quy`),
  approveRegression: (id, payload) =>
    qaRequest(`/de-xuat-hoi-quy/${id}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listPlans: (id, query = "") => {
    const value = listQuery(query);
    return qaRequest(`/du-an/${id}/ke-hoach-kiem-thu${value ? `?${value}` : ""}`);
  },
  createPlan: (payload) =>
    qaRequest("/ke-hoach-kiem-thu", { method: "POST", body: JSON.stringify(payload) }),
  updatePlan: (id, payload) =>
    qaRequest(`/ke-hoach-kiem-thu/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  submitPlan: (id, payload) =>
    qaRequest(`/ke-hoach-kiem-thu/${id}/gui-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  approvePlan: (id, payload) =>
    qaRequest(`/ke-hoach-kiem-thu/${id}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  archivePlan: (id, payload) =>
    qaRequest(`/ke-hoach-kiem-thu/${id}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  clonePlan: (id) => qaRequest(`/ke-hoach-kiem-thu/${id}/nhan-ban`, { method: "POST" }),
  listSuites: (id, query = "") => {
    const value = listQuery(query);
    return qaRequest(`/du-an/${id}/bo-kiem-thu${value ? `?${value}` : ""}`);
  },
  createSuite: (payload) =>
    qaRequest("/bo-kiem-thu", { method: "POST", body: JSON.stringify(payload) }),
  updateSuite: (id, payload) =>
    qaRequest(`/bo-kiem-thu/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  cloneSuite: (id) => qaRequest(`/bo-kiem-thu/${id}/nhan-ban`, { method: "POST" }),
  archiveSuite: (id, payload) =>
    qaRequest(`/bo-kiem-thu/${id}/luu-tru`, { method: "POST", body: JSON.stringify(payload) }),
  listRunPage: (id, query = "") => listPage(`/du-an/${id}/lan-chay-kiem-thu`, query),
  listRuns: (id, query = "") =>
    listPage(`/du-an/${id}/lan-chay-kiem-thu`, query).then((result) => result.items),
  listResults: (id, status = "") =>
    qaRequest(
      `/du-an/${id}/ket-qua-kiem-thu${status ? `?status=${encodeURIComponent(status)}` : ""}`,
    ),
  createRun: (payload) =>
    qaRequest("/lan-chay-kiem-thu", { method: "POST", body: JSON.stringify(payload) }),
  getRun: (id) => qaRequest(`/lan-chay-kiem-thu/${id}`),
  startRun: (id) => qaRequest(`/lan-chay-kiem-thu/${id}/bat-dau`, { method: "POST" }),
  recordResult: (runId, versionId, payload) =>
    qaRequest(`/lan-chay-kiem-thu/${runId}/ket-qua/${versionId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateExecution: (projectId, executionId, payload) =>
    qaRequest(`/du-an/${projectId}/thuc-thi-kiem-thu/${executionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  completeRun: (id) => qaRequest(`/lan-chay-kiem-thu/${id}/hoan-tat`, { method: "POST" }),
  abortRun: (id, reason) =>
    qaRequest(`/lan-chay-kiem-thu/${id}/huy`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  exportRunReport: (id) => downloadQaFile(`/lan-chay-kiem-thu/${id}/bao-cao`, `test-run-${id}.csv`),
  listDefectPage: (id, query = "") => listPage(`/du-an/${id}/loi`, query),
  listDefects: (id, query = "") =>
    listPage(`/du-an/${id}/loi`, query).then((result) => result.items),
  findDuplicateDefects: (id) => qaRequest(`/du-an/${id}/loi/trung-lap`),
  findDefectTraceCandidates: (id) => qaRequest(`/loi/${id}/ung-vien-truy-vet`),
  exportDefects: (id) => downloadQaFile(`/du-an/${id}/loi/xuat`, `defects-${id}.csv`),
  createDefect: (id, payload) =>
    qaRequest(`/du-an/${id}/loi`, { method: "POST", body: JSON.stringify(payload) }),
  updateDefect: (id, payload) =>
    qaRequest(`/loi/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  transitionDefect: (id, payload) =>
    qaRequest(`/loi/${id}/chuyen-trang-thai`, { method: "POST", body: JSON.stringify(payload) }),
  retestDefect: (projectId, defectId, payload) =>
    qaRequest(`/du-an/${projectId}/loi/${defectId}/kiem-thu-lai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  searchKnowledge: (id, payload) =>
    qaRequest(`/du-an/${id}/tri-thuc/tim-kiem`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  askProject: (id, payload) =>
    qaRequest(`/du-an/${id}/ai/hoi-dap`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  audit: (id) => qaRequest(`/du-an/${id}/nhat-ky`),
  maintenanceAnalytics: (id) => qaRequest(`/du-an/${id}/phan-tich-bao-tri`),
  aiAnalytics: (id) => qaRequest(`/du-an/${id}/phan-tich-ai`),
  executionReport: (id, scope = {}) =>
    qaRequest(`/du-an/${id}/bao-cao/thuc-thi?${listQuery(scope)}`),
  defectReport: (id, scope = {}) => qaRequest(`/du-an/${id}/bao-cao/loi?${listQuery(scope)}`),
  projectActivity: (id) => qaRequest(`/du-an/${id}/hoat-dong`),
  operations: (query = "") => qaRequest(`/van-hanh${query ? `?${query}` : ""}`),
  retryOperationJob: (jobId) => qaRequest(`/van-hanh/tac-vu/${jobId}/thu-lai`, { method: "POST" }),
};
