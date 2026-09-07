import { API_URL, authenticatedFetch } from "@/shared/services/api-client";

export async function testingRequest(path, options = {}) {
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

export async function downloadTestingFile(path, filename) {
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
  const result = await testingRequest(`${path}${query ? `?${query}` : ""}`);
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
    if (status) params.set("status", status);
    return testingRequest(`/du-an?${params.toString()}`);
  },
  createProject: (payload) =>
    testingRequest("/du-an", { method: "POST", body: JSON.stringify(payload) }),
  getProject: (id) => testingRequest(`/du-an/${id}`),
  listMembers: (id) => testingRequest(`/du-an/${id}/thanh-vien`),
  listInvitations: () => testingRequest("/loi-moi-du-an"),
  addMember: (id, payload) =>
    testingRequest(`/du-an/${id}/thanh-vien`, { method: "POST", body: JSON.stringify(payload) }),
  inviteMember: (id, payload) =>
    testingRequest(`/du-an/${id}/loi-moi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  acceptInvitation: (invitationId) =>
    testingRequest(`/loi-moi-du-an/${invitationId}/chap-nhan`, { method: "POST" }),
  declineInvitation: (invitationId) =>
    testingRequest(`/loi-moi-du-an/${invitationId}/tu-choi`, { method: "POST" }),
  leaveProject: (id) => testingRequest(`/du-an/${id}/roi-du-an`, { method: "POST" }),
  resendMemberInvite: (id, userId) =>
    testingRequest(`/du-an/${id}/thanh-vien/${userId}/gui-lai-loi-moi`, { method: "POST" }),
  cancelMemberInvite: (id, userId) =>
    testingRequest(`/du-an/${id}/thanh-vien/${userId}/huy-loi-moi`, { method: "POST" }),
  updateMember: (id, userId, payload) =>
    testingRequest(`/du-an/${id}/thanh-vien/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  removeMember: (id, userId) =>
    testingRequest(`/du-an/${id}/thanh-vien/${userId}`, { method: "DELETE" }),
  updateProject: (id, payload) =>
    testingRequest(`/du-an/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  getProjectSettings: (id) => testingRequest(`/du-an/${id}/cai-dat`),
  updateProjectSettings: (id, payload) =>
    testingRequest(`/du-an/${id}/cai-dat`, { method: "PATCH", body: JSON.stringify(payload) }),
  archiveProject: (id, payload) =>
    testingRequest(`/du-an/${id}/luu-tru`, { method: "POST", body: JSON.stringify(payload) }),
  restoreProject: (id, payload) =>
    testingRequest(`/du-an/${id}/khoi-phuc`, { method: "POST", body: JSON.stringify(payload) }),
  dashboard: (id) => testingRequest(`/du-an/${id}/tong-quan`),
  searchProject: (id, query) =>
    testingRequest(`/du-an/${id}/tim-kiem?q=${encodeURIComponent(query)}&limit=50`),
  listRequirementPage: (id, query = "") => listPage(`/du-an/${id}/yeu-cau`, query),
  listRequirements: (id, query = "") =>
    listPage(`/du-an/${id}/yeu-cau`, query).then((result) => result.items),
  createRequirement: (id, payload) =>
    testingRequest(`/du-an/${id}/yeu-cau`, { method: "POST", body: JSON.stringify(payload) }),
  updateRequirementDraft: (projectId, requirementId, payload) =>
    testingRequest(`/du-an/${projectId}/yeu-cau/${requirementId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  getRequirement: (id) => testingRequest(`/yeu-cau/${id}`),
  listRequirementVersions: (id) => testingRequest(`/yeu-cau/${id}/phien-ban`),
  createRequirementVersion: (id, payload) =>
    testingRequest(`/yeu-cau/${id}/phien-ban`, { method: "POST", body: JSON.stringify(payload) }),
  baselineRequirement: (id, revision) =>
    testingRequest(`/phien-ban-yeu-cau/${id}/chot-chuan`, {
      method: "POST",
      body: JSON.stringify({ expected_revision: revision }),
    }),
  lintRequirement: (id) =>
    testingRequest(`/phien-ban-yeu-cau/${id}/ai/kiem-tra`, { method: "POST" }),
  compareRequirement: (id, fromId, toId) =>
    testingRequest(`/yeu-cau/${id}/so-sanh`, {
      method: "POST",
      body: JSON.stringify({ from_version_id: fromId, to_version_id: toId }),
    }),
  splitRequirement: (projectId, requirementId, payload) =>
    testingRequest(`/du-an/${projectId}/yeu-cau/${requirementId}/tach`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  mergeRequirements: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/yeu-cau/gop`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  findDuplicateRequirements: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/yeu-cau/kiem-tra-trung-lap`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createRequirementImport: (id, payload) =>
    testingRequest(`/du-an/${id}/nhap-yeu-cau`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  confirmRequirementImport: (id, selectedIndexes, expectedRevision) =>
    testingRequest(`/nhap-yeu-cau/${id}/xac-nhan`, {
      method: "POST",
      body: JSON.stringify({
        selected_indexes: selectedIndexes,
        expected_revision: expectedRevision,
      }),
    }),
  updateRequirementImport: (id, payload) =>
    testingRequest(`/nhap-yeu-cau/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  mergeRequirementCandidates: (id, payload) =>
    testingRequest(`/nhap-yeu-cau/${id}/ung-vien/gop`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  splitRequirementCandidate: (id, candidateId, payload) =>
    testingRequest(`/nhap-yeu-cau/${id}/ung-vien/${candidateId}/tach`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  rejectRequirementCandidate: (id, candidateId, payload) =>
    testingRequest(`/nhap-yeu-cau/${id}/ung-vien/${candidateId}/tu-choi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  uploadRequirementImport: (id, file, format) => {
    const body = new FormData();
    body.append("format", format);
    body.append("file", file);
    return testingRequest(`/du-an/${id}/nhap-yeu-cau/tai-len`, { method: "POST", body });
  },
  createRequirementDocument: (id, payload) =>
    testingRequest(`/du-an/${id}/tai-lieu-yeu-cau`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  uploadRequirementDocument: (id, file, format) => {
    const body = new FormData();
    body.append("format", format);
    body.append("file", file);
    return testingRequest(`/du-an/${id}/tai-lieu-yeu-cau/tai-len`, { method: "POST", body });
  },
  listRequirementDocuments: (id, query = "") =>
    testingRequest(`/du-an/${id}/tai-lieu-yeu-cau${query ? `?${query}` : ""}`),
  createKnowledgeSource: (id, payload) =>
    testingRequest(`/du-an/${id}/nguon-tri-thuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listKnowledgeSources: (id, includeArchived = false) =>
    testingRequest(`/du-an/${id}/nguon-tri-thuc?include_archived=${includeArchived}`),
  archiveKnowledgeSource: (id, payload) =>
    testingRequest(`/nguon-tri-thuc/${id}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  registerAttachment: (id, payload) =>
    testingRequest(`/du-an/${id}/tep-dinh-kem`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listAttachments: (id, query = "") =>
    testingRequest(`/du-an/${id}/tep-dinh-kem${query ? `?${query}` : ""}`),
  deleteAttachment: (id) => testingRequest(`/tep-dinh-kem/${id}`, { method: "DELETE" }),
  moderateAttachment: (id, payload) =>
    testingRequest(`/tep-dinh-kem/${id}/kiem-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getRequirementDocument: (id) => testingRequest(`/tai-lieu-yeu-cau/${id}`),
  updateRequirementDocument: (id, payload) =>
    testingRequest(`/tai-lieu-yeu-cau/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  reindexRequirementDocument: (id) =>
    testingRequest(`/tai-lieu-yeu-cau/${id}/lap-chi-muc-lai`, { method: "POST" }),
  reindexKnowledgeSource: (id) =>
    testingRequest(`/tai-lieu-yeu-cau/${id}/lap-chi-muc-lai`, { method: "POST" }),
  downloadRequirementDocument: (id, filename) =>
    downloadTestingFile(`/tai-lieu-yeu-cau/${id}/tai-xuong`, filename),
  archiveRequirementDocument: (id, payload) =>
    testingRequest(`/tai-lieu-yeu-cau/${id}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  restoreRequirementDocument: (id, payload) =>
    testingRequest(`/tai-lieu-yeu-cau/${id}/khoi-phuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  retryRequirementDocumentParse: (id, revision) =>
    testingRequest(`/tai-lieu-yeu-cau/${id}/thu-lai-phan-tich`, {
      method: "POST",
      body: JSON.stringify({ expected_revision: revision }),
    }),
  extractRequirementDocument: (id, idempotencyKey = crypto.randomUUID()) =>
    testingRequest(`/tai-lieu-yeu-cau/${id}/trich-xuat`, {
      method: "POST",
      body: JSON.stringify({ idempotency_key: idempotencyKey }),
    }),
  submitRequirementReview: (projectId, requirementId, payload) =>
    testingRequest(`/du-an/${projectId}/yeu-cau/${requirementId}/gui-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  requestRequirementChanges: (projectId, requirementId, payload) =>
    testingRequest(`/du-an/${projectId}/yeu-cau/${requirementId}/yeu-cau-chinh-sua`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  approveRequirement: (projectId, requirementId, payload) =>
    testingRequest(`/du-an/${projectId}/yeu-cau/${requirementId}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  obsoleteRequirement: (id, payload) =>
    testingRequest(`/yeu-cau/${id}/ngung-hieu-luc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  restoreRequirement: (id, payload) =>
    testingRequest(`/yeu-cau/${id}/khoi-phuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  submitTestCaseReview: (projectId, draftId, payload) =>
    testingRequest(`/du-an/${projectId}/ca-kiem-thu/${draftId}/gui-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  requestTestCaseChanges: (projectId, draftId, payload) =>
    testingRequest(`/du-an/${projectId}/ca-kiem-thu/${draftId}/yeu-cau-chinh-sua`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listScenarios: (id, query = "") => {
    const value = listQuery(query);
    return testingRequest(`/du-an/${id}/kich-ban-kiem-thu${value ? `?${value}` : ""}`);
  },
  listDataSets: (id, query = "") =>
    testingRequest(
      `/du-an/${id}/du-lieu-kiem-thu${query ? `?q=${encodeURIComponent(query)}` : ""}`,
    ),
  createDataSet: (id, payload) =>
    testingRequest(`/du-an/${id}/du-lieu-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listDataSetVersions: (id) => testingRequest(`/du-lieu-kiem-thu/${id}/phien-ban`),
  createDataSetVersion: (id, payload) =>
    testingRequest(`/du-lieu-kiem-thu/${id}/phien-ban`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bindDataSet: (projectId, dataSetId, payload) =>
    testingRequest(`/du-an/${projectId}/du-lieu-kiem-thu/${dataSetId}/gan-ca-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewDataSet: (projectId, dataSetId, payload) =>
    testingRequest(`/du-an/${projectId}/du-lieu-kiem-thu/${dataSetId}/xem-truoc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  archiveDataSet: (projectId, dataSetId, payload) =>
    testingRequest(`/du-an/${projectId}/du-lieu-kiem-thu/${dataSetId}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listTestCaseTemplates: (projectId, templateType = "") =>
    testingRequest(
      `/du-an/${projectId}/mau-ca-kiem-thu${templateType ? `?template_type=${encodeURIComponent(templateType)}` : ""}`,
    ),
  getTestCaseTemplate: (templateId) => testingRequest(`/mau-ca-kiem-thu/${templateId}`),
  createTestCaseTemplate: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/mau-ca-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateTestCaseTemplate: (templateId, payload) =>
    testingRequest(`/mau-ca-kiem-thu/${templateId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  archiveTestCaseTemplate: (templateId, payload) =>
    testingRequest(`/mau-ca-kiem-thu/${templateId}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createScenario: (id, payload) =>
    testingRequest(`/du-an/${id}/kich-ban-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateScenario: (id, payload) =>
    testingRequest(`/kich-ban-kiem-thu/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  cloneScenario: (id) => testingRequest(`/kich-ban-kiem-thu/${id}/nhan-ban`, { method: "POST" }),
  archiveScenario: (id, payload) =>
    testingRequest(`/kich-ban-kiem-thu/${id}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  generateScenarios: (versionId, payload) =>
    testingRequest(`/phien-ban-yeu-cau/${versionId}/ai/sinh-kich-ban`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listTestDrafts: (id) => testingRequest(`/du-an/${id}/ban-nhap-ca-kiem-thu`),
  createTestDraft: (id, payload) =>
    testingRequest(`/du-an/${id}/ban-nhap-ca-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getTestDraft: (id) => testingRequest(`/ban-nhap-ca-kiem-thu/${id}`),
  updateTestDraft: (id, payload) =>
    testingRequest(`/ban-nhap-ca-kiem-thu/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  lintTestDraft: (id) => testingRequest(`/ban-nhap-ca-kiem-thu/${id}/kiem-tra`, { method: "POST" }),
  freezeTestDraft: (id, revision, reason) =>
    testingRequest(`/ban-nhap-ca-kiem-thu/${id}/dong-bang`, {
      method: "POST",
      body: JSON.stringify({ expected_revision: revision, change_reason: reason }),
    }),
  listTestCasePage: (id, query = "") => listPage(`/du-an/${id}/ca-kiem-thu`, query),
  listTestCases: (id, query = "") =>
    listPage(`/du-an/${id}/ca-kiem-thu`, query).then((result) => result.items),
  listTestVersions: (id) => testingRequest(`/ca-kiem-thu/${id}/phien-ban`),
  cloneTestCase: (id, payload) =>
    testingRequest(`/ca-kiem-thu/${id}/nhan-ban`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  obsoleteTestCase: (id, payload) =>
    testingRequest(`/ca-kiem-thu/${id}/ngung-hieu-luc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  restoreTestCase: (id, payload) =>
    testingRequest(`/ca-kiem-thu/${id}/khoi-phuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  generateTestCases: (versionId, payload) =>
    testingRequest(`/phien-ban-yeu-cau/${versionId}/ai/sinh-ca-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  generateProjectTestCases: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/ca-kiem-thu/sinh`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  findDuplicates: (id) => testingRequest(`/du-an/${id}/ca-kiem-thu/trung-lap`),
  uploadTestImport: (id, file) => {
    const body = new FormData();
    const format = file.name.toLowerCase().endsWith(".xlsx") ? "xlsx" : "csv";
    body.append("format", format);
    body.append("file", file);
    return testingRequest(`/du-an/${id}/nhap-ca-kiem-thu/tai-len`, { method: "POST", body });
  },
  confirmTestImport: (id, selectedIndexes) =>
    testingRequest(`/nhap-ca-kiem-thu/${id}/xac-nhan`, {
      method: "POST",
      body: JSON.stringify({ selected_indexes: selectedIndexes }),
    }),
  exportTestCases: (id, format = "csv") =>
    downloadTestingFile(
      `/du-an/${id}/ca-kiem-thu/xuat?format=${format}`,
      `test-cases-${id}.${format}`,
    ),
  importApiArtifact: (id, payload) =>
    testingRequest(`/du-an/${id}/dac-ta-giao-dien/nhap`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listApiArtifacts: (id) => testingRequest(`/du-an/${id}/dac-ta-giao-dien`),
  getApiArtifact: (id) => testingRequest(`/dac-ta-giao-dien/${id}`),
  reviewApiArtifact: (id, payload) =>
    testingRequest(`/dac-ta-giao-dien/${id}/ra-soat`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  confirmApiArtifact: (id, payload) =>
    testingRequest(`/dac-ta-giao-dien/${id}/xac-nhan`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  archiveApiArtifact: (id, payload) =>
    testingRequest(`/dac-ta-giao-dien/${id}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  diffApiArtifacts: (projectId, fromArtifactId, toArtifactId) =>
    testingRequest(
      `/du-an/${projectId}/dac-ta-giao-dien/khac-biet?from_artifact_id=${encodeURIComponent(fromArtifactId)}&to_artifact_id=${encodeURIComponent(toArtifactId)}`,
    ),
  analyzeApiArtifactImpact: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/dac-ta-giao-dien/phan-tich-anh-huong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listApiOperations: (id) => testingRequest(`/du-an/${id}/dac-ta-giao-dien/thao-tac`),
  generateApiTests: (id) =>
    testingRequest(`/dac-ta-giao-dien/thao-tac/${id}/sinh-ca-kiem-thu`, { method: "POST" }),
  traceability: (id) => testingRequest(`/du-an/${id}/truy-vet`),
  exportTraceability: (id) =>
    downloadTestingFile(`/du-an/${id}/truy-vet/xuat`, `traceability-${id}.csv`),
  coverage: (id, scope = {}) => {
    const query = listQuery(scope);
    return testingRequest(`/du-an/${id}/do-phu${query ? `?${query}` : ""}`);
  },
  listCoverageSnapshots: (id) => testingRequest(`/du-an/${id}/anh-chup-do-phu`),
  createCoverageSnapshot: (id, payload = {}) =>
    testingRequest(`/du-an/${id}/anh-chup-do-phu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  recoverTrace: (id) => testingRequest(`/du-an/${id}/khoi-phuc-truy-vet`, { method: "POST" }),
  createTrace: (payload) =>
    testingRequest("/lien-ket-truy-vet", { method: "POST", body: JSON.stringify(payload) }),
  confirmTrace: (id) => testingRequest(`/lien-ket-truy-vet/${id}/xac-nhan`, { method: "POST" }),
  rejectTrace: (id) => testingRequest(`/lien-ket-truy-vet/${id}/tu-choi`, { method: "POST" }),
  revokeTrace: (id) => testingRequest(`/lien-ket-truy-vet/${id}`, { method: "DELETE" }),
  listReviewComments: (projectId, query = "") =>
    testingRequest(`/du-an/${projectId}/nhan-xet-ra-soat${query ? `?${query}` : ""}`),
  createReviewComment: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/nhan-xet-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  resolveReviewComment: (id, reason = "") =>
    testingRequest(`/nhan-xet-ra-soat/${id}/giai-quyet`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  reopenReviewComment: (id, reason = "") =>
    testingRequest(`/nhan-xet-ra-soat/${id}/mo-lai`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  listChangeSets: (id, query = "") => {
    const value = listQuery(query);
    return testingRequest(`/du-an/${id}/bo-thay-doi${value ? `?${value}` : ""}`);
  },
  createChangeSet: (requirementId, payload) =>
    testingRequest(`/yeu-cau/${requirementId}/bo-thay-doi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getChangeSet: (id) => testingRequest(`/bo-thay-doi/${id}`),
  reviewChangeSet: (id, payload) =>
    testingRequest(`/bo-thay-doi/${id}/ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  analyzeImpact: (id) =>
    testingRequest(`/bo-thay-doi/${id}/phan-tich-anh-huong`, { method: "POST" }),
  getChangeSetImpact: (id) => testingRequest(`/bo-thay-doi/${id}/phan-tich-anh-huong`),
  getImpact: (id) => testingRequest(`/phan-tich-anh-huong/${id}`),
  reviewImpact: (id, payload) =>
    testingRequest(`/phan-tich-anh-huong/${id}/ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  rerunImpact: (id, payload) =>
    testingRequest(`/phan-tich-anh-huong/${id}/chay-lai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createProposals: (id) =>
    testingRequest(`/phan-tich-anh-huong/${id}/de-xuat-bao-tri`, { method: "POST" }),
  listProposals: (id, query = { status: "PENDING" }) => {
    const value = listQuery(typeof query === "string" ? { status: query } : query);
    return testingRequest(`/du-an/${id}/de-xuat-bao-tri${value ? `?${value}` : ""}`);
  },
  acceptProposal: (id, payload, edited = false) =>
    testingRequest(`/de-xuat-bao-tri/${id}/${edited ? "chap-nhan-co-chinh-sua" : "chap-nhan"}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  rejectProposal: (id, payload) =>
    testingRequest(`/de-xuat-bao-tri/${id}/tu-choi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  regenerateProposal: (id, payload) =>
    testingRequest(`/de-xuat-bao-tri/${id}/sinh-lai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkTags: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hang-loat/nhan`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewBulkTags: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hang-loat/nhan`, {
      method: "POST",
      body: JSON.stringify({ ...payload, preview: true }),
    }),
  bulkAddToSuite: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hang-loat/ca-kiem-thu/them-vao-bo-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewBulkAddToSuite: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hang-loat/ca-kiem-thu/them-vao-bo-kiem-thu`, {
      method: "POST",
      body: JSON.stringify({ ...payload, preview: true }),
    }),
  bulkMarkReviewRequired: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hang-loat/ca-kiem-thu/danh-dau-can-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewBulkMarkReviewRequired: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hang-loat/ca-kiem-thu/danh-dau-can-ra-soat`, {
      method: "POST",
      body: JSON.stringify({ ...payload, preview: true }),
    }),
  bulkArchive: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hang-loat/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewBulkArchive: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hang-loat/luu-tru`, {
      method: "POST",
      body: JSON.stringify({ ...payload, preview: true }),
    }),
  bulkGenerateProposals: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hang-loat/de-xuat-anh-huong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewBulkGenerateProposals: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hang-loat/de-xuat-anh-huong`, {
      method: "POST",
      body: JSON.stringify({ ...payload, preview: true }),
    }),
  bulkApproveProposals: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hang-loat/phe-duyet-de-xuat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  previewBulkApproveProposals: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hang-loat/phe-duyet-de-xuat`, {
      method: "POST",
      body: JSON.stringify({ ...payload, preview: true }),
    }),
  regression: (id) => testingRequest(`/bo-thay-doi/${id}/de-xuat-hoi-quy`, { method: "POST" }),
  getChangeSetRegression: (id) => testingRequest(`/bo-thay-doi/${id}/de-xuat-hoi-quy`),
  approveRegression: (id, payload) =>
    testingRequest(`/de-xuat-hoi-quy/${id}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listPlans: (id, query = "") => {
    const value = listQuery(query);
    return testingRequest(`/du-an/${id}/ke-hoach-kiem-thu${value ? `?${value}` : ""}`);
  },
  createPlan: (payload) =>
    testingRequest("/ke-hoach-kiem-thu", { method: "POST", body: JSON.stringify(payload) }),
  updatePlan: (id, payload) =>
    testingRequest(`/ke-hoach-kiem-thu/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  submitPlan: (id, payload) =>
    testingRequest(`/ke-hoach-kiem-thu/${id}/gui-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  approvePlan: (id, payload) =>
    testingRequest(`/ke-hoach-kiem-thu/${id}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  archivePlan: (id, payload) =>
    testingRequest(`/ke-hoach-kiem-thu/${id}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  clonePlan: (id) => testingRequest(`/ke-hoach-kiem-thu/${id}/nhan-ban`, { method: "POST" }),
  listSuites: (id, query = "") => {
    const value = listQuery(query);
    return testingRequest(`/du-an/${id}/bo-kiem-thu${value ? `?${value}` : ""}`);
  },
  listReleases: (id, query = {}) => {
    const value = listQuery(query);
    return testingRequest(`/du-an/${id}/ban-phat-hanh${value ? `?${value}` : ""}`);
  },
  listBuilds: (id, query = {}) => {
    const value = listQuery(query);
    return testingRequest(`/du-an/${id}/ban-dung${value ? `?${value}` : ""}`);
  },
  listEnvironments: (id) => testingRequest(`/du-an/${id}/moi-truong`),
  listDeviceMatrices: (id, includeArchived = false) =>
    testingRequest(`/du-an/${id}/ma-tran-thiet-bi?include_archived=${includeArchived}`),
  getDeviceMatrix: (id) => testingRequest(`/ma-tran-thiet-bi/${id}`),
  createDeviceMatrix: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/ma-tran-thiet-bi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateDeviceMatrix: (id, payload) =>
    testingRequest(`/ma-tran-thiet-bi/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  archiveDeviceMatrix: (id, payload) =>
    testingRequest(`/ma-tran-thiet-bi/${id}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  assignDeviceMatrix: (id, payload) =>
    testingRequest(`/ma-tran-thiet-bi/${id}/gan`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listProjectNotificationWatches: (projectId, artifactType = "") =>
    testingRequest(
      `/du-an/${projectId}/thong-bao/theo-doi${artifactType ? `?artifact_type=${encodeURIComponent(artifactType)}` : ""}`,
    ),
  setProjectNotificationWatch: (projectId, artifactType, artifactId, watching) =>
    testingRequest(`/du-an/${projectId}/thong-bao/theo-doi/${artifactType}/${artifactId}`, {
      method: "PUT",
      body: JSON.stringify({ watching }),
    }),
  getProjectNotificationRules: (projectId) =>
    testingRequest(`/du-an/${projectId}/thong-bao/quy-tac`),
  updateProjectNotificationRules: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/thong-bao/quy-tac`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  getProjectNotificationPreferences: (projectId) =>
    testingRequest(`/du-an/${projectId}/thong-bao/tuy-chon`),
  updateProjectNotificationPreferences: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/thong-bao/tuy-chon`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  listSecurityTestSuggestions: (projectId) =>
    testingRequest(`/du-an/${projectId}/ai/goi-y-kiem-thu-bao-mat`),
  generateSecurityTestSuggestions: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/ai/goi-y-kiem-thu-bao-mat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listPerformancePlanDrafts: (projectId) =>
    testingRequest(`/du-an/${projectId}/ai/ke-hoach-hieu-nang`),
  generatePerformancePlanDraft: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/ai/ke-hoach-hieu-nang`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listAutomationScriptDrafts: (projectId) =>
    testingRequest(`/du-an/${projectId}/ban-nhap-kich-ban-tu-dong`),
  getAutomationScriptDraft: (draftId) => testingRequest(`/ban-nhap-kich-ban-tu-dong/${draftId}`),
  generateAutomationScriptDraft: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/ai/ban-nhap-kich-ban-tu-dong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateAutomationScriptDraft: (draftId, payload) =>
    testingRequest(`/ban-nhap-kich-ban-tu-dong/${draftId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  approveAutomationScriptDraft: (draftId, payload) =>
    testingRequest(`/ban-nhap-kich-ban-tu-dong/${draftId}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  exportAutomationScriptDraft: (draftId, filename) =>
    downloadTestingFile(`/ban-nhap-kich-ban-tu-dong/${draftId}/xuat`, filename),
  listProjectConnectors: (projectId) => testingRequest(`/du-an/${projectId}/ket-noi`),
  bindProjectConnector: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/ket-noi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateProjectConnector: (projectId, connectorId, payload) =>
    testingRequest(`/du-an/${projectId}/ket-noi/${connectorId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  unbindProjectConnector: (projectId, connectorId, payload) =>
    testingRequest(`/du-an/${projectId}/ket-noi/${connectorId}/ngat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  startProjectConnectorSync: (projectId, connectorId, payload) =>
    testingRequest(`/du-an/${projectId}/ket-noi/${connectorId}/dong-bo`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listProjectConnectorSyncLog: (projectId) => testingRequest(`/du-an/${projectId}/ket-noi/nhat-ky`),
  listProjectConnectorConflicts: (projectId) =>
    testingRequest(`/du-an/${projectId}/ket-noi/xung-dot`),
  resolveProjectConnectorConflict: (projectId, conflictId, payload) =>
    testingRequest(`/du-an/${projectId}/ket-noi/xung-dot/${conflictId}/giai-quyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listAutomationExecutions: (projectId) => testingRequest(`/du-an/${projectId}/thuc-thi-tu-dong`),
  getAutomationExecution: (executionId) => testingRequest(`/thuc-thi-tu-dong/${executionId}`),
  createAutomationExecution: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/thuc-thi-tu-dong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  startAutomationExecution: (executionId, payload) =>
    testingRequest(`/thuc-thi-tu-dong/${executionId}/bat-dau`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  cancelAutomationExecution: (executionId, payload) =>
    testingRequest(`/thuc-thi-tu-dong/${executionId}/huy`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getAutomationEvidence: (executionId) =>
    testingRequest(`/thuc-thi-tu-dong/${executionId}/bang-chung`),
  getCicdState: (projectId) => testingRequest(`/du-an/${projectId}/tich-hop-trien-khai-lien-tuc`),
  createCicdBinding: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/tich-hop-trien-khai-lien-tuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateCicdBinding: (projectId, bindingId, payload) =>
    testingRequest(`/du-an/${projectId}/tich-hop-trien-khai-lien-tuc/${bindingId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  retryCicdRun: (projectId, runId, payload) =>
    testingRequest(`/du-an/${projectId}/tich-hop-trien-khai-lien-tuc/lan-chay/${runId}/thu-lai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateCollaborationPresence: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/cong-tac/phien`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  listCollaborationPresence: (projectId, artifactType, artifactId) =>
    testingRequest(
      `/du-an/${projectId}/cong-tac/hien-dien?artifact_type=${encodeURIComponent(artifactType)}&artifact_id=${encodeURIComponent(artifactId)}`,
    ),
  applyRequirementCollaborationOperation: (projectId, artifactId, payload) =>
    testingRequest(`/du-an/${projectId}/cong-tac/yeu-cau/${artifactId}/thao-tac`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  applyTestCaseCollaborationOperation: (projectId, artifactId, payload) =>
    testingRequest(`/du-an/${projectId}/cong-tac/ca-kiem-thu/${artifactId}/thao-tac`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listCollaborationConflicts: (projectId) =>
    testingRequest(`/du-an/${projectId}/cong-tac/xung-dot`),
  resolveCollaborationConflict: (projectId, conflictId, payload) =>
    testingRequest(`/du-an/${projectId}/cong-tac/xung-dot/${conflictId}/giai-quyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listWebhookSubscriptions: (projectId, includeDisabled = true) =>
    testingRequest(`/du-an/${projectId}/moc-goi?include_disabled=${includeDisabled}`),
  createWebhookSubscription: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/moc-goi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateWebhookSubscription: (projectId, subscriptionId, payload) =>
    testingRequest(`/du-an/${projectId}/moc-goi/${subscriptionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  listWebhookDeliveries: (projectId, status = "") =>
    testingRequest(
      `/du-an/${projectId}/moc-goi/giao-hang${status ? `?status=${encodeURIComponent(status)}` : ""}`,
    ),
  replayWebhookDelivery: (projectId, deliveryId, payload) =>
    testingRequest(`/du-an/${projectId}/moc-goi/giao-hang/${deliveryId}/phat-lai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createSuite: (payload) =>
    testingRequest("/bo-kiem-thu", { method: "POST", body: JSON.stringify(payload) }),
  updateSuite: (id, payload) =>
    testingRequest(`/bo-kiem-thu/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  cloneSuite: (id) => testingRequest(`/bo-kiem-thu/${id}/nhan-ban`, { method: "POST" }),
  archiveSuite: (id, payload) =>
    testingRequest(`/bo-kiem-thu/${id}/luu-tru`, { method: "POST", body: JSON.stringify(payload) }),
  listRunPage: (id, query = "") => listPage(`/du-an/${id}/lan-chay-kiem-thu`, query),
  listRuns: (id, query = "") =>
    listPage(`/du-an/${id}/lan-chay-kiem-thu`, query).then((result) => result.items),
  listResults: (id, status = "") =>
    testingRequest(
      `/du-an/${id}/ket-qua-kiem-thu${status ? `?status=${encodeURIComponent(status)}` : ""}`,
    ),
  createRun: (payload) =>
    testingRequest("/lan-chay-kiem-thu", { method: "POST", body: JSON.stringify(payload) }),
  getRun: (id) => testingRequest(`/lan-chay-kiem-thu/${id}`),
  startRun: (id) => testingRequest(`/lan-chay-kiem-thu/${id}/bat-dau`, { method: "POST" }),
  resumeRun: (projectId, runId, payload) =>
    testingRequest(`/du-an/${projectId}/lan-chay-kiem-thu/${runId}/tiep-tuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  recordResult: (runId, versionId, payload) =>
    testingRequest(`/lan-chay-kiem-thu/${runId}/ket-qua/${versionId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateExecution: (projectId, executionId, payload) =>
    testingRequest(`/du-an/${projectId}/thuc-thi-kiem-thu/${executionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  completeRun: (id) => testingRequest(`/lan-chay-kiem-thu/${id}/hoan-tat`, { method: "POST" }),
  abortRun: (id, reason) =>
    testingRequest(`/lan-chay-kiem-thu/${id}/huy`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  exportRunReport: (id) =>
    downloadTestingFile(`/lan-chay-kiem-thu/${id}/bao-cao`, `test-run-${id}.csv`),
  listDefectPage: (id, query = "") => listPage(`/du-an/${id}/loi`, query),
  listDefects: (id, query = "") =>
    listPage(`/du-an/${id}/loi`, query).then((result) => result.items),
  findDuplicateDefects: (id) => testingRequest(`/du-an/${id}/loi/trung-lap`),
  suggestDefectTrace: (projectId, defectId, payload) =>
    testingRequest(`/du-an/${projectId}/ai/loi/${defectId}/goi-y-truy-vet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateDefectTrace: (projectId, defectId, payload) =>
    testingRequest(`/du-an/${projectId}/loi/${defectId}/truy-vet`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  exportDefects: (id) => downloadTestingFile(`/du-an/${id}/loi/xuat`, `defects-${id}.csv`),
  createDefect: (id, payload) =>
    testingRequest(`/du-an/${id}/loi`, { method: "POST", body: JSON.stringify(payload) }),
  updateDefect: (id, payload) =>
    testingRequest(`/loi/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  transitionDefect: (id, payload) =>
    testingRequest(`/loi/${id}/chuyen-trang-thai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  retestDefect: (projectId, defectId, payload) =>
    testingRequest(`/du-an/${projectId}/loi/${defectId}/kiem-thu-lai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  searchKnowledge: (id, payload) =>
    testingRequest(`/du-an/${id}/tri-thuc/tim-kiem`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  askProject: (id, payload) =>
    testingRequest(`/du-an/${id}/ai/hoi-dap`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  audit: (id) => testingRequest(`/du-an/${id}/nhat-ky`),
  maintenanceAnalytics: (id) => testingRequest(`/du-an/${id}/phan-tich-bao-tri`),
  aiAnalytics: (id) => testingRequest(`/du-an/${id}/phan-tich-ai`),
  executionReport: (id, scope = {}) =>
    testingRequest(`/du-an/${id}/bao-cao/thuc-thi?${listQuery(scope)}`),
  defectReport: (id, scope = {}) => testingRequest(`/du-an/${id}/bao-cao/loi?${listQuery(scope)}`),
  projectActivity: (id) => testingRequest(`/du-an/${id}/hoat-dong`),
  operations: (query = "") => testingRequest(`/van-hanh${query ? `?${query}` : ""}`),
  retryOperationJob: (jobId) =>
    testingRequest(`/van-hanh/tac-vu/${jobId}/thu-lai`, { method: "POST" }),
};
