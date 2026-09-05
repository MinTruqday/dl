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
  acceptInvitation: (invitationId) =>
    qaRequest(`/loi-moi-du-an/${invitationId}/chap-nhan`, { method: "POST" }),
  declineInvitation: (invitationId) =>
    qaRequest(`/loi-moi-du-an/${invitationId}/tu-choi`, { method: "POST" }),
  leaveProject: (id) => qaRequest(`/du-an/${id}/roi-du-an`, { method: "POST" }),
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
  getProjectSettings: (id) => qaRequest(`/du-an/${id}/cai-dat`),
  updateProjectSettings: (id, payload) =>
    qaRequest(`/du-an/${id}/cai-dat`, { method: "PATCH", body: JSON.stringify(payload) }),
  archiveProject: (id, payload) =>
    qaRequest(`/du-an/${id}/luu-tru`, { method: "POST", body: JSON.stringify(payload) }),
  restoreProject: (id, payload) =>
    qaRequest(`/du-an/${id}/khoi-phuc`, { method: "POST", body: JSON.stringify(payload) }),
  dashboard: (id) => qaRequest(`/du-an/${id}/tong-quan`),
  searchProject: (id, query) =>
    qaRequest(`/du-an/${id}/tim-kiem?q=${encodeURIComponent(query)}&limit=50`),
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
  splitRequirement: (projectId, requirementId, payload) =>
    qaRequest(`/du-an/${projectId}/yeu-cau/${requirementId}/tach`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  mergeRequirements: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/yeu-cau/gop`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  findDuplicateRequirements: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/yeu-cau/kiem-tra-trung-lap`, {
      method: "POST",
      body: JSON.stringify(payload),
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
  mergeRequirementCandidates: (id, payload) =>
    qaRequest(`/nhap-yeu-cau/${id}/ung-vien/gop`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  splitRequirementCandidate: (id, candidateId, payload) =>
    qaRequest(`/nhap-yeu-cau/${id}/ung-vien/${candidateId}/tach`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  rejectRequirementCandidate: (id, candidateId, payload) =>
    qaRequest(`/nhap-yeu-cau/${id}/ung-vien/${candidateId}/tu-choi`, {
      method: "POST",
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
    qaRequest(`/du-an/${id}/du-lieu-kiem-thu${query ? `?q=${encodeURIComponent(query)}` : ""}`),
  createDataSet: (id, payload) =>
    qaRequest(`/du-an/${id}/du-lieu-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listDataSetVersions: (id) => qaRequest(`/du-lieu-kiem-thu/${id}/phien-ban`),
  createDataSetVersion: (id, payload) =>
    qaRequest(`/du-lieu-kiem-thu/${id}/phien-ban`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bindDataSet: (projectId, dataSetId, payload) =>
    qaRequest(`/du-an/${projectId}/du-lieu-kiem-thu/${dataSetId}/gan-ca-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewDataSet: (projectId, dataSetId, payload) =>
    qaRequest(`/du-an/${projectId}/du-lieu-kiem-thu/${dataSetId}/xem-truoc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  archiveDataSet: (projectId, dataSetId, payload) =>
    qaRequest(`/du-an/${projectId}/du-lieu-kiem-thu/${dataSetId}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listTestCaseTemplates: (projectId, templateType = "") =>
    qaRequest(
      `/du-an/${projectId}/mau-ca-kiem-thu${templateType ? `?template_type=${encodeURIComponent(templateType)}` : ""}`,
    ),
  getTestCaseTemplate: (templateId) => qaRequest(`/mau-ca-kiem-thu/${templateId}`),
  createTestCaseTemplate: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/mau-ca-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateTestCaseTemplate: (templateId, payload) =>
    qaRequest(`/mau-ca-kiem-thu/${templateId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  archiveTestCaseTemplate: (templateId, payload) =>
    qaRequest(`/mau-ca-kiem-thu/${templateId}/luu-tru`, {
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
    qaRequest(`/du-an/${id}/dac-ta-giao-dien/nhap`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listApiArtifacts: (id) => qaRequest(`/du-an/${id}/dac-ta-giao-dien`),
  getApiArtifact: (id) => qaRequest(`/dac-ta-giao-dien/${id}`),
  reviewApiArtifact: (id, payload) =>
    qaRequest(`/dac-ta-giao-dien/${id}/ra-soat`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  confirmApiArtifact: (id, payload) =>
    qaRequest(`/dac-ta-giao-dien/${id}/xac-nhan`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  archiveApiArtifact: (id, payload) =>
    qaRequest(`/dac-ta-giao-dien/${id}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  diffApiArtifacts: (projectId, fromArtifactId, toArtifactId) =>
    qaRequest(
      `/du-an/${projectId}/dac-ta-giao-dien/khac-biet?from_artifact_id=${encodeURIComponent(fromArtifactId)}&to_artifact_id=${encodeURIComponent(toArtifactId)}`,
    ),
  analyzeApiArtifactImpact: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/dac-ta-giao-dien/phan-tich-anh-huong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listApiOperations: (id) => qaRequest(`/du-an/${id}/dac-ta-giao-dien/thao-tac`),
  generateApiTests: (id) =>
    qaRequest(`/dac-ta-giao-dien/thao-tac/${id}/sinh-ca-kiem-thu`, { method: "POST" }),
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
  rerunImpact: (id, payload) =>
    qaRequest(`/phan-tich-anh-huong/${id}/chay-lai`, {
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
    qaRequest(`/de-xuat-bao-tri/${id}/${edited ? "chap-nhan-co-chinh-sua" : "chap-nhan"}`, {
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
  previewBulkTags: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/nhan`, {
      method: "POST",
      body: JSON.stringify({ ...payload, preview: true }),
    }),
  bulkAddToSuite: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/ca-kiem-thu/them-vao-bo-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewBulkAddToSuite: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/ca-kiem-thu/them-vao-bo-kiem-thu`, {
      method: "POST",
      body: JSON.stringify({ ...payload, preview: true }),
    }),
  bulkMarkReviewRequired: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/ca-kiem-thu/danh-dau-can-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewBulkMarkReviewRequired: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/ca-kiem-thu/danh-dau-can-ra-soat`, {
      method: "POST",
      body: JSON.stringify({ ...payload, preview: true }),
    }),
  bulkArchive: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewBulkArchive: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/luu-tru`, {
      method: "POST",
      body: JSON.stringify({ ...payload, preview: true }),
    }),
  bulkGenerateProposals: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/de-xuat-anh-huong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewBulkGenerateProposals: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/de-xuat-anh-huong`, {
      method: "POST",
      body: JSON.stringify({ ...payload, preview: true }),
    }),
  bulkApproveProposals: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/phe-duyet-de-xuat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewBulkApproveProposals: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/hang-loat/phe-duyet-de-xuat`, {
      method: "POST",
      body: JSON.stringify({ ...payload, preview: true }),
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
  listReleases: (id, query = {}) => {
    const value = listQuery(query);
    return qaRequest(`/du-an/${id}/ban-phat-hanh${value ? `?${value}` : ""}`);
  },
  listBuilds: (id, query = {}) => {
    const value = listQuery(query);
    return qaRequest(`/du-an/${id}/ban-dung${value ? `?${value}` : ""}`);
  },
  listEnvironments: (id) => qaRequest(`/du-an/${id}/moi-truong`),
  listDeviceMatrices: (id, includeArchived = false) =>
    qaRequest(`/du-an/${id}/ma-tran-thiet-bi?include_archived=${includeArchived}`),
  getDeviceMatrix: (id) => qaRequest(`/ma-tran-thiet-bi/${id}`),
  createDeviceMatrix: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/ma-tran-thiet-bi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateDeviceMatrix: (id, payload) =>
    qaRequest(`/ma-tran-thiet-bi/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  archiveDeviceMatrix: (id, payload) =>
    qaRequest(`/ma-tran-thiet-bi/${id}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  assignDeviceMatrix: (id, payload) =>
    qaRequest(`/ma-tran-thiet-bi/${id}/gan`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listProjectNotificationWatches: (projectId, artifactType = "") =>
    qaRequest(
      `/du-an/${projectId}/thong-bao/theo-doi${artifactType ? `?artifact_type=${encodeURIComponent(artifactType)}` : ""}`,
    ),
  setProjectNotificationWatch: (projectId, artifactType, artifactId, watching) =>
    qaRequest(`/du-an/${projectId}/thong-bao/theo-doi/${artifactType}/${artifactId}`, {
      method: "PUT",
      body: JSON.stringify({ watching }),
    }),
  getProjectNotificationRules: (projectId) => qaRequest(`/du-an/${projectId}/thong-bao/quy-tac`),
  updateProjectNotificationRules: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/thong-bao/quy-tac`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  getProjectNotificationPreferences: (projectId) =>
    qaRequest(`/du-an/${projectId}/thong-bao/tuy-chon`),
  updateProjectNotificationPreferences: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/thong-bao/tuy-chon`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  listSecurityTestSuggestions: (projectId) =>
    qaRequest(`/du-an/${projectId}/ai/goi-y-kiem-thu-bao-mat`),
  generateSecurityTestSuggestions: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/ai/goi-y-kiem-thu-bao-mat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listPerformancePlanDrafts: (projectId) => qaRequest(`/du-an/${projectId}/ai/ke-hoach-hieu-nang`),
  generatePerformancePlanDraft: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/ai/ke-hoach-hieu-nang`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listAutomationScriptDrafts: (projectId) =>
    qaRequest(`/du-an/${projectId}/ban-nhap-kich-ban-tu-dong`),
  getAutomationScriptDraft: (draftId) => qaRequest(`/ban-nhap-kich-ban-tu-dong/${draftId}`),
  generateAutomationScriptDraft: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/ai/ban-nhap-kich-ban-tu-dong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateAutomationScriptDraft: (draftId, payload) =>
    qaRequest(`/ban-nhap-kich-ban-tu-dong/${draftId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  approveAutomationScriptDraft: (draftId, payload) =>
    qaRequest(`/ban-nhap-kich-ban-tu-dong/${draftId}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  exportAutomationScriptDraft: (draftId, filename) =>
    downloadQaFile(`/ban-nhap-kich-ban-tu-dong/${draftId}/xuat`, filename),
  listProjectConnectors: (projectId) => qaRequest(`/du-an/${projectId}/ket-noi`),
  bindProjectConnector: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/ket-noi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateProjectConnector: (projectId, connectorId, payload) =>
    qaRequest(`/du-an/${projectId}/ket-noi/${connectorId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  unbindProjectConnector: (projectId, connectorId, payload) =>
    qaRequest(`/du-an/${projectId}/ket-noi/${connectorId}/ngat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  startProjectConnectorSync: (projectId, connectorId, payload) =>
    qaRequest(`/du-an/${projectId}/ket-noi/${connectorId}/dong-bo`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listProjectConnectorSyncLog: (projectId) => qaRequest(`/du-an/${projectId}/ket-noi/nhat-ky`),
  listProjectConnectorConflicts: (projectId) => qaRequest(`/du-an/${projectId}/ket-noi/xung-dot`),
  resolveProjectConnectorConflict: (projectId, conflictId, payload) =>
    qaRequest(`/du-an/${projectId}/ket-noi/xung-dot/${conflictId}/giai-quyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listAutomationExecutions: (projectId) => qaRequest(`/du-an/${projectId}/thuc-thi-tu-dong`),
  getAutomationExecution: (executionId) => qaRequest(`/thuc-thi-tu-dong/${executionId}`),
  createAutomationExecution: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/thuc-thi-tu-dong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  startAutomationExecution: (executionId, payload) =>
    qaRequest(`/thuc-thi-tu-dong/${executionId}/bat-dau`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  cancelAutomationExecution: (executionId, payload) =>
    qaRequest(`/thuc-thi-tu-dong/${executionId}/huy`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getAutomationEvidence: (executionId) => qaRequest(`/thuc-thi-tu-dong/${executionId}/bang-chung`),
  getCicdState: (projectId) => qaRequest(`/du-an/${projectId}/tich-hop-trien-khai-lien-tuc`),
  createCicdBinding: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/tich-hop-trien-khai-lien-tuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateCicdBinding: (projectId, bindingId, payload) =>
    qaRequest(`/du-an/${projectId}/tich-hop-trien-khai-lien-tuc/${bindingId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  retryCicdRun: (projectId, runId, payload) =>
    qaRequest(`/du-an/${projectId}/tich-hop-trien-khai-lien-tuc/lan-chay/${runId}/thu-lai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateCollaborationPresence: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/cong-tac/phien`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  listCollaborationPresence: (projectId, artifactType, artifactId) =>
    qaRequest(
      `/du-an/${projectId}/cong-tac/hien-dien?artifact_type=${encodeURIComponent(artifactType)}&artifact_id=${encodeURIComponent(artifactId)}`,
    ),
  applyRequirementCollaborationOperation: (projectId, artifactId, payload) =>
    qaRequest(`/du-an/${projectId}/cong-tac/yeu-cau/${artifactId}/thao-tac`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  applyTestCaseCollaborationOperation: (projectId, artifactId, payload) =>
    qaRequest(`/du-an/${projectId}/cong-tac/ca-kiem-thu/${artifactId}/thao-tac`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listCollaborationConflicts: (projectId) => qaRequest(`/du-an/${projectId}/cong-tac/xung-dot`),
  resolveCollaborationConflict: (projectId, conflictId, payload) =>
    qaRequest(`/du-an/${projectId}/cong-tac/xung-dot/${conflictId}/giai-quyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listWebhookSubscriptions: (projectId, includeDisabled = true) =>
    qaRequest(`/du-an/${projectId}/moc-goi?include_disabled=${includeDisabled}`),
  createWebhookSubscription: (projectId, payload) =>
    qaRequest(`/du-an/${projectId}/moc-goi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateWebhookSubscription: (projectId, subscriptionId, payload) =>
    qaRequest(`/du-an/${projectId}/moc-goi/${subscriptionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  listWebhookDeliveries: (projectId, status = "") =>
    qaRequest(
      `/du-an/${projectId}/moc-goi/giao-hang${status ? `?status=${encodeURIComponent(status)}` : ""}`,
    ),
  replayWebhookDelivery: (projectId, deliveryId, payload) =>
    qaRequest(`/du-an/${projectId}/moc-goi/giao-hang/${deliveryId}/phat-lai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
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
  resumeRun: (projectId, runId, payload) =>
    qaRequest(`/du-an/${projectId}/lan-chay-kiem-thu/${runId}/tiep-tuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
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
  suggestDefectTrace: (projectId, defectId, payload) =>
    qaRequest(`/du-an/${projectId}/ai/loi/${defectId}/goi-y-truy-vet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateDefectTrace: (projectId, defectId, payload) =>
    qaRequest(`/du-an/${projectId}/loi/${defectId}/truy-vet`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
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
