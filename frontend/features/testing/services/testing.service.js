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

export async function agentRequest(path, options = {}) {
  const response = await authenticatedFetch(`${API_URL}/tac-tu${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    const error = new Error(detail?.message || detail?.code || "Không thể hoàn tất yêu cầu AI");
    error.status = response.status;
    error.code = detail?.code;
    throw error;
  }
  return body;
}

export async function testingStreamRequest(path, options = {}) {
  const { onDelta, ...requestOptions } = options;
  const streamId = crypto.randomUUID();
  let received = 0;
  const notify = (status) => {
    window.dispatchEvent(
      new CustomEvent("veriq-ai-stream", {
        detail: { id: streamId, path, received, status },
      }),
    );
  };
  const response = await authenticatedFetch(`${API_URL}/kiem-thu${path}`, {
    ...requestOptions,
    headers: {
      ...(requestOptions.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      Accept: "text/event-stream",
      ...requestOptions.headers,
    },
  });
  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => null);
    const error = new Error(body?.error?.message || "Không thể hoàn tất yêu cầu AI");
    error.status = response.status;
    error.code = body?.error?.code;
    throw error;
  }
  notify("streaming");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result;
  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";
    for (const rawEvent of events) {
      const dataLine = rawEvent.split("\n").find((line) => line.startsWith("data: "));
      if (!dataLine) continue;
      const event = JSON.parse(dataLine.slice(6));
      if (event.type === "delta") {
        const delta = event.delta || "";
        received += delta.length;
        onDelta?.(delta);
        notify("streaming");
      }
      if (event.type === "result") result = event.data;
      if (event.type === "error") {
        const body = event.data;
        const error = new Error(body?.error?.message || "Không thể hoàn tất yêu cầu AI");
        error.status = event.status;
        error.code = body?.error?.code || event.code;
        notify("failed");
        throw error;
      }
    }
    if (done) break;
  }
  if (!result) {
    notify("failed");
    throw new Error("Luồng AI kết thúc nhưng không trả về kết quả");
  }
  notify("complete");
  return result?.data;
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
  runAgent: (payload) =>
    agentRequest("/luot-chay", { method: "POST", body: JSON.stringify(payload) }),
  getAgentRun: (runId) => agentRequest(`/luot-chay/${runId}`),
  decideAgentRun: (runId, payload) =>
    agentRequest(`/luot-chay/${runId}/quyet-dinh`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
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
  listTestStrategies: (projectId, filters = {}) => {
    const query = listQuery(filters);
    return testingRequest(`/du-an/${projectId}/chien-luoc${query ? `?${query}` : ""}`);
  },
  createTestStrategy: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/chien-luoc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getTestStrategy: (strategyId) => testingRequest(`/chien-luoc/${strategyId}`),
  updateTestStrategy: (strategyId, payload) =>
    testingRequest(`/chien-luoc/${strategyId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  submitTestStrategy: (strategyId, payload) =>
    testingRequest(`/chien-luoc/${strategyId}/gui-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  requestTestStrategyChanges: (strategyId, payload) =>
    testingRequest(`/chien-luoc/${strategyId}/yeu-cau-chinh-sua`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  reviewTestStrategy: (strategyId, payload) =>
    testingRequest(`/chien-luoc/${strategyId}/ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  approveTestStrategy: (strategyId, payload) =>
    testingRequest(`/chien-luoc/${strategyId}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  versionTestStrategy: (strategyId, payload) =>
    testingRequest(`/chien-luoc/${strategyId}/tao-phien-ban`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  compareTestStrategyVersions: (strategyId, otherStrategyId) =>
    testingRequest(
      `/chien-luoc/${strategyId}/so-sanh?other_strategy_id=${encodeURIComponent(otherStrategyId)}`,
    ),
  cloneTestStrategy: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/chien-luoc/nhan-ban`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  validateTestStrategy: (strategyId) =>
    testingRequest(`/chien-luoc/${strategyId}/kiem-tra`, { method: "POST" }),
  archiveTestStrategy: (strategyId, payload) =>
    testingRequest(`/chien-luoc/${strategyId}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listTestConditions: (projectId, filters = {}) => {
    const query = listQuery(filters);
    return testingRequest(`/du-an/${projectId}/dieu-kien-kiem-thu${query ? `?${query}` : ""}`);
  },
  createTestCondition: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/dieu-kien-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateTestCondition: (conditionId, payload) =>
    testingRequest(`/dieu-kien-kiem-thu/${conditionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  submitTestCondition: (conditionId, payload) =>
    testingRequest(`/dieu-kien-kiem-thu/${conditionId}/gui-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  reviewTestCondition: (conditionId, payload) =>
    testingRequest(`/dieu-kien-kiem-thu/${conditionId}/ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  approveTestCondition: (conditionId, payload) =>
    testingRequest(`/dieu-kien-kiem-thu/${conditionId}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  archiveTestCondition: (conditionId, payload) =>
    testingRequest(`/dieu-kien-kiem-thu/${conditionId}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  resolveTestAnalysisFinding: (conditionId, findingId, payload) =>
    testingRequest(`/dieu-kien-kiem-thu/${conditionId}/ket-qua/${findingId}/giai-quyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  runTestAnalysisAi: (projectId, payload) =>
    testingStreamRequest(`/du-an/${projectId}/phan-tich-kiem-thu/ai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listTestAnalysisBasis: (projectId, filters = {}) => {
    const query = listQuery(filters);
    return testingRequest(
      `/du-an/${projectId}/phan-tich-kiem-thu/co-so${query ? `?${query}` : ""}`,
    );
  },
  runDeterministicTestAnalysis: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/phan-tich-kiem-thu/kiem-tra`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listTestAnalysisFindings: (projectId, filters = {}) => {
    const query = listQuery(filters);
    return testingRequest(`/du-an/${projectId}/ket-qua-phan-tich${query ? `?${query}` : ""}`);
  },
  createTestAnalysisFinding: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/ket-qua-phan-tich`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  assignTestAnalysisFinding: (findingId, payload) =>
    testingRequest(`/ket-qua-phan-tich/${findingId}/phan-cong`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  resolveStandaloneTestAnalysisFinding: (findingId, payload) =>
    testingRequest(`/ket-qua-phan-tich/${findingId}/giai-quyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  verifyTestAnalysisFinding: (findingId, payload) =>
    testingRequest(`/ket-qua-phan-tich/${findingId}/xac-minh`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  bulkPrioritizeTestConditions: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/dieu-kien-kiem-thu/uu-tien`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  getTestConditionCoverage: (projectId) =>
    testingRequest(`/du-an/${projectId}/phan-tich-kiem-thu/truy-vet`),
  listMonitoringSnapshots: (projectId, filters = {}) => {
    const query = listQuery(filters);
    return testingRequest(`/du-an/${projectId}/giam-sat-kiem-thu${query ? `?${query}` : ""}`);
  },
  createMonitoringSnapshot: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/giam-sat-kiem-thu/anh-chup`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getMonitoringSnapshot: (snapshotId) =>
    testingRequest(`/giam-sat-kiem-thu/anh-chup/${snapshotId}`),
  overrideMonitoringCriterion: (snapshotId, payload) =>
    testingRequest(`/giam-sat-kiem-thu/anh-chup/${snapshotId}/ghi-de-tieu-chi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getQualityGate: (snapshotId) =>
    testingRequest(`/giam-sat-kiem-thu/anh-chup/${snapshotId}/danh-gia-chat-luong`),
  listQualityDecisions: (projectId, releaseId = "") =>
    testingRequest(
      `/du-an/${projectId}/quyet-dinh-chat-luong${releaseId ? `?release_id=${encodeURIComponent(releaseId)}` : ""}`,
    ),
  createQualityDecision: (snapshotId, payload) =>
    testingRequest(`/giam-sat-kiem-thu/anh-chup/${snapshotId}/quyet-dinh-chat-luong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  exportQualityGate: (snapshotId) =>
    testingRequest(`/giam-sat-kiem-thu/anh-chup/${snapshotId}/xuat-bang-chung`),
  listControlActions: (projectId, filters = {}) => {
    const query = listQuery(filters);
    return testingRequest(`/du-an/${projectId}/hanh-dong-dieu-khien${query ? `?${query}` : ""}`);
  },
  createControlAction: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hanh-dong-dieu-khien`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateControlAction: (actionId, payload) =>
    testingRequest(`/hanh-dong-dieu-khien/${actionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  listTestStatusReports: (projectId, filters = {}) => {
    const query = listQuery(filters);
    return testingRequest(`/du-an/${projectId}/bao-cao-trang-thai${query ? `?${query}` : ""}`);
  },
  generateTestStatusReport: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/bao-cao-trang-thai/tao-tu-anh-chup`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getTestStatusReport: (reportId) => testingRequest(`/bao-cao-trang-thai/${reportId}`),
  updateTestStatusReport: (reportId, payload) =>
    testingRequest(`/bao-cao-trang-thai/${reportId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  draftTestStatusReportNarrative: (reportId, payload) =>
    testingStreamRequest(`/bao-cao-trang-thai/${reportId}/ai/ban-nhap`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  attachTestStatusReportEvidence: (reportId, payload) =>
    testingRequest(`/bao-cao-trang-thai/${reportId}/bang-chung`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  submitTestStatusReport: (reportId, payload) =>
    testingRequest(`/bao-cao-trang-thai/${reportId}/gui-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  requestTestStatusReportChanges: (reportId, payload) =>
    testingRequest(`/bao-cao-trang-thai/${reportId}/yeu-cau-chinh-sua`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  approveTestStatusReport: (reportId, payload) =>
    testingRequest(`/bao-cao-trang-thai/${reportId}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  publishTestStatusReport: (reportId, payload) =>
    testingRequest(`/bao-cao-trang-thai/${reportId}/phat-hanh`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  archiveTestStatusReport: (reportId, payload) =>
    testingRequest(`/bao-cao-trang-thai/${reportId}/luu-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  compareTestStatusReports: (reportId, otherReportId) =>
    testingRequest(
      `/bao-cao-trang-thai/${reportId}/so-sanh?other_report_id=${encodeURIComponent(otherReportId)}`,
    ),
  exportTestStatusReport: (reportId, format) =>
    downloadTestingFile(
      `/bao-cao-trang-thai/${reportId}/xuat?format=${encodeURIComponent(format)}`,
      `test-status-report-${reportId}.${format}`,
    ),
  listTestCompletionReports: (projectId, filters = {}) => {
    const query = listQuery(filters);
    return testingRequest(`/du-an/${projectId}/hoan-tat-kiem-thu${query ? `?${query}` : ""}`);
  },
  createTestCompletionReport: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/hoan-tat-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getTestCompletionReport: (reportId) => testingRequest(`/hoan-tat-kiem-thu/${reportId}`),
  updateTestCompletionReport: (reportId, payload) =>
    testingRequest(`/hoan-tat-kiem-thu/${reportId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  draftTestCompletionNarrative: (reportId, payload) =>
    testingStreamRequest(`/hoan-tat-kiem-thu/${reportId}/ai/ban-nhap`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  clusterTestCompletionLessons: (reportId, payload) =>
    testingStreamRequest(`/hoan-tat-kiem-thu/${reportId}/ai/gom-bai-hoc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  addTestCompletionResidualRisk: (reportId, payload) =>
    testingRequest(`/hoan-tat-kiem-thu/${reportId}/rui-ro`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  addTestCompletionLesson: (reportId, payload) =>
    testingRequest(`/hoan-tat-kiem-thu/${reportId}/bai-hoc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  manageTestCompletionHandover: (reportId, payload) =>
    testingRequest(`/hoan-tat-kiem-thu/${reportId}/ban-giao`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  submitTestCompletionReport: (reportId, payload) =>
    testingRequest(`/hoan-tat-kiem-thu/${reportId}/gui-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  requestTestCompletionChanges: (reportId, payload) =>
    testingRequest(`/hoan-tat-kiem-thu/${reportId}/yeu-cau-chinh-sua`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  signOffTestCompletion: (reportId, payload) =>
    testingRequest(`/hoan-tat-kiem-thu/${reportId}/ky-xac-nhan`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  decideTestCompletionResidualRisk: (reportId, riskId, payload) =>
    testingRequest(`/hoan-tat-kiem-thu/${reportId}/rui-ro/${riskId}/xu-ly`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  approveTestCompletionReport: (reportId, payload) =>
    testingRequest(`/hoan-tat-kiem-thu/${reportId}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  closeTestCompletionReport: (reportId, payload) =>
    testingRequest(`/hoan-tat-kiem-thu/${reportId}/dong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  exportTestCompletionReport: (reportId, format) =>
    downloadTestingFile(
      `/hoan-tat-kiem-thu/${reportId}/xuat?format=${encodeURIComponent(format)}`,
      `test-completion-${reportId}.${format}`,
    ),
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
  lintRequirement: (id, payload) =>
    testingStreamRequest(`/phien-ban-yeu-cau/${id}/ai/kiem-tra`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  applyRequirementAiSuggestion: (id, payload) =>
    testingRequest(`/phien-ban-yeu-cau/${id}/ai/ap-dung-de-xuat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
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
    testingStreamRequest(`/phien-ban-yeu-cau/${versionId}/ai/sinh-kich-ban`, {
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
    testingStreamRequest(`/phien-ban-yeu-cau/${versionId}/ai/sinh-ca-kiem-thu`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  generateProjectTestCases: (projectId, payload) =>
    testingStreamRequest(`/du-an/${projectId}/ca-kiem-thu/sinh`, {
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
    testingStreamRequest(`/dac-ta-giao-dien/thao-tac/${id}/sinh-ca-kiem-thu`, {
      method: "POST",
    }),
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
    testingStreamRequest(`/bo-thay-doi/${id}/phan-tich-anh-huong`, { method: "POST" }),
  getChangeSetImpact: (id) => testingRequest(`/bo-thay-doi/${id}/phan-tich-anh-huong`),
  getImpact: (id) => testingRequest(`/phan-tich-anh-huong/${id}`),
  reviewImpact: (id, payload) =>
    testingRequest(`/phan-tich-anh-huong/${id}/ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  rerunImpact: (id, payload) =>
    testingStreamRequest(`/phan-tich-anh-huong/${id}/chay-lai`, {
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
  regression: (id) =>
    testingStreamRequest(`/bo-thay-doi/${id}/de-xuat-hoi-quy`, { method: "POST" }),
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
  validatePlan: (id) => testingRequest(`/ke-hoach-kiem-thu/${id}/kiem-tra`, { method: "POST" }),
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
    testingStreamRequest(`/du-an/${projectId}/ai/goi-y-kiem-thu-bao-mat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listPerformancePlanDrafts: (projectId) =>
    testingRequest(`/du-an/${projectId}/ai/ke-hoach-hieu-nang`),
  generatePerformancePlanDraft: (projectId, payload) =>
    testingStreamRequest(`/du-an/${projectId}/ai/ke-hoach-hieu-nang`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listAutomationScriptDrafts: (projectId) =>
    testingRequest(`/du-an/${projectId}/ban-nhap-kich-ban-tu-dong`),
  getAutomationScriptDraft: (draftId) => testingRequest(`/ban-nhap-kich-ban-tu-dong/${draftId}`),
  generateAutomationScriptDraft: (projectId, payload) =>
    testingStreamRequest(`/du-an/${projectId}/ai/ban-nhap-kich-ban-tu-dong`, {
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
    testingStreamRequest(`/du-an/${projectId}/ai/loi/${defectId}/goi-y-truy-vet`, {
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
    testingStreamRequest(`/du-an/${id}/ai/hoi-dap`, {
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
  listReviewSessions: (projectId, filters = {}) =>
    testingRequest(`/du-an/${projectId}/phien-ra-soat?${listQuery(filters)}`),
  createReviewSession: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/phien-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getReviewSession: (reviewId) => testingRequest(`/phien-ra-soat/${reviewId}`),
  updateReviewSession: (reviewId, payload) =>
    testingRequest(`/phien-ra-soat/${reviewId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  assignReviewSessionReviewers: (reviewId, payload) =>
    testingRequest(`/phien-ra-soat/${reviewId}/nguoi-ra-soat`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  startReviewSession: (reviewId, payload) =>
    testingRequest(`/phien-ra-soat/${reviewId}/bat-dau`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createReviewFinding: (reviewId, payload) =>
    testingRequest(`/phien-ra-soat/${reviewId}/ket-qua`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  assignReviewFinding: (findingId, payload) =>
    testingRequest(`/phien-ra-soat/ket-qua/${findingId}/gan`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  resolveReviewFinding: (findingId, payload) =>
    testingRequest(`/phien-ra-soat/ket-qua/${findingId}/giai-quyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  verifyReviewFinding: (findingId, payload) =>
    testingRequest(`/phien-ra-soat/ket-qua/${findingId}/xac-minh`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  recordReviewSessionDecision: (reviewId, payload) =>
    testingRequest(`/phien-ra-soat/${reviewId}/quyet-dinh`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  completeReviewSession: (reviewId, payload) =>
    testingRequest(`/phien-ra-soat/${reviewId}/hoan-tat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  transitionReviewSessionTerminal: (reviewId, payload) =>
    testingRequest(`/phien-ra-soat/${reviewId}/trang-thai-cuoi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getReviewSessionMetrics: (reviewId) => testingRequest(`/phien-ra-soat/${reviewId}/so-lieu`),
  createFollowUpReviewSession: (reviewId, payload) =>
    testingRequest(`/phien-ra-soat/${reviewId}/phien-tiep-theo`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  exportReviewSession: (reviewId) =>
    downloadTestingFile(`/phien-ra-soat/${reviewId}/xuat`, `formal-review-${reviewId}.csv`),
  listMeasurementDefinitions: (projectId) =>
    testingRequest(`/du-an/${projectId}/dinh-nghia-do-luong`),
  createMeasurementDefinition: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/dinh-nghia-do-luong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateMeasurementDefinition: (definitionId, payload) =>
    testingRequest(`/dinh-nghia-do-luong/${definitionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  versionMeasurementDefinition: (definitionId, payload) =>
    testingRequest(`/dinh-nghia-do-luong/${definitionId}/tao-phien-ban`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  transitionMeasurementDefinition: (definitionId, payload) =>
    testingRequest(`/dinh-nghia-do-luong/${definitionId}/trang-thai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listMeasurementSnapshots: (projectId, filters = {}) =>
    testingRequest(`/du-an/${projectId}/anh-do-luong?${listQuery(filters)}`),
  createMeasurementSnapshot: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/anh-do-luong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getMeasurementTrend: (definitionId, releaseId = "") =>
    testingRequest(
      `/dinh-nghia-do-luong/${definitionId}/xu-huong${releaseId ? `?release_id=${encodeURIComponent(releaseId)}` : ""}`,
    ),
  compareMeasurementReleases: (projectId, releaseA, releaseB) =>
    testingRequest(
      `/du-an/${projectId}/do-luong/so-sanh-ban-phat-hanh?release_a=${encodeURIComponent(releaseA)}&release_b=${encodeURIComponent(releaseB)}`,
    ),
  listMeasurementThresholdAlerts: (projectId) =>
    testingRequest(`/du-an/${projectId}/do-luong/canh-bao`),
  validateMeasurementDefinition: (definitionId) =>
    testingRequest(`/dinh-nghia-do-luong/${definitionId}/xac-thuc`),
  pinMeasurementToDashboard: (definitionId, pinned) =>
    testingRequest(`/dinh-nghia-do-luong/${definitionId}/ghim`, {
      method: "PUT",
      body: JSON.stringify({ pinned }),
    }),
  exportMeasurementData: (definitionId, key) =>
    downloadTestingFile(`/dinh-nghia-do-luong/${definitionId}/xuat`, `metric-${key}.csv`),
  listQualityEvaluations: (projectId, releaseId = "") =>
    testingRequest(
      `/du-an/${projectId}/danh-gia-chat-luong${releaseId ? `?release_id=${encodeURIComponent(releaseId)}` : ""}`,
    ),
  createQualityEvaluation: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/danh-gia-chat-luong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getQualityEvaluation: (evaluationId) => testingRequest(`/danh-gia-chat-luong/${evaluationId}`),
  updateQualityEvaluation: (evaluationId, payload) =>
    testingRequest(`/danh-gia-chat-luong/${evaluationId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  submitQualityEvaluation: (evaluationId, payload) =>
    testingRequest(`/danh-gia-chat-luong/${evaluationId}/gui-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  reviewQualityEvaluation: (evaluationId, payload) =>
    testingRequest(`/danh-gia-chat-luong/${evaluationId}/ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createQualityWaiver: (evaluationId, payload) =>
    testingRequest(`/danh-gia-chat-luong/${evaluationId}/mien-tru`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  decideQualityWaiver: (evaluationId, waiverId, payload) =>
    testingRequest(`/danh-gia-chat-luong/${evaluationId}/mien-tru/${waiverId}/quyet-dinh`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  approveQualityEvaluation: (evaluationId, payload) =>
    testingRequest(`/danh-gia-chat-luong/${evaluationId}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listCausalAnalyses: (projectId) => testingRequest(`/du-an/${projectId}/phan-tich-nguyen-nhan`),
  listCausalAnalysisCandidates: (projectId) =>
    testingRequest(`/du-an/${projectId}/phan-tich-nguyen-nhan/ung-vien`),
  createCausalAnalysis: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/phan-tich-nguyen-nhan`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getCausalAnalysis: (analysisId) => testingRequest(`/phan-tich-nguyen-nhan/${analysisId}`),
  updateCausalAnalysis: (analysisId, payload) =>
    testingRequest(`/phan-tich-nguyen-nhan/${analysisId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  linkCausalAnalysisDefects: (analysisId, payload) =>
    testingRequest(`/phan-tich-nguyen-nhan/${analysisId}/lien-ket-loi`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  addCausalFiveWhy: (analysisId, payload) =>
    testingRequest(`/phan-tich-nguyen-nhan/${analysisId}/nam-tai-sao`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  recordCausalRootCause: (analysisId, payload) =>
    testingRequest(`/phan-tich-nguyen-nhan/${analysisId}/nguyen-nhan-goc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createCorrectiveAction: (analysisId, payload) =>
    testingRequest(`/phan-tich-nguyen-nhan/${analysisId}/hanh-dong-khac-phuc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createPreventiveAction: (analysisId, payload) =>
    testingRequest(`/phan-tich-nguyen-nhan/${analysisId}/hanh-dong-phong-ngua`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  assignPreventionAction: (actionId, payload) =>
    testingRequest(`/hanh-dong-phong-ngua/${actionId}/phan-cong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updatePreventionAction: (actionId, payload) =>
    testingRequest(`/hanh-dong-phong-ngua/${actionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  submitCausalAnalysis: (analysisId, payload) =>
    testingRequest(`/phan-tich-nguyen-nhan/${analysisId}/gui-ra-soat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  approveCausalAnalysis: (analysisId, payload) =>
    testingRequest(`/phan-tich-nguyen-nhan/${analysisId}/phe-duyet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  reviewCausalEffectiveness: (analysisId, payload) =>
    testingRequest(`/phan-tich-nguyen-nhan/${analysisId}/danh-gia-hieu-luc`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  closeCausalAnalysis: (analysisId, payload) =>
    testingRequest(`/phan-tich-nguyen-nhan/${analysisId}/dong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  generateCausalHypotheses: (analysisId, payload) =>
    testingStreamRequest(`/phan-tich-nguyen-nhan/${analysisId}/ai/goi-y`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listEnvironmentIncidents: (projectId, filters = {}) =>
    testingRequest(`/du-an/${projectId}/su-co-moi-truong?${listQuery(filters)}`),
  createEnvironmentIncident: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/su-co-moi-truong`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateEnvironmentIncident: (incidentId, payload) =>
    testingRequest(`/su-co-moi-truong/${incidentId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  transitionEnvironmentIncident: (incidentId, payload, close = false) =>
    testingRequest(`/su-co-moi-truong/${incidentId}/${close ? "ket-thuc" : "dieu-tra"}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listNonFunctionalTestPlans: (projectId, planType = "") =>
    testingRequest(
      `/du-an/${projectId}/ke-hoach-phi-chuc-nang${planType ? `?plan_type=${encodeURIComponent(planType)}` : ""}`,
    ),
  getNonFunctionalTestPlan: (planId) => testingRequest(`/ke-hoach-phi-chuc-nang/${planId}`),
  createNonFunctionalTestPlan: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/ke-hoach-phi-chuc-nang`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateNonFunctionalTestPlan: (planId, payload) =>
    testingRequest(`/ke-hoach-phi-chuc-nang/${planId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  transitionNonFunctionalTestPlan: (planId, payload, approve = false) =>
    testingRequest(`/ke-hoach-phi-chuc-nang/${planId}/${approve ? "phe-duyet" : "gui-ra-soat"}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  importNonFunctionalEvidence: (planId, payload) =>
    testingRequest(`/ke-hoach-phi-chuc-nang/${planId}/bang-chung-ben-ngoai`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listProcessImprovements: (projectId) => testingRequest(`/du-an/${projectId}/cai-tien-quy-trinh`),
  getProcessImprovement: (proposalId) => testingRequest(`/cai-tien-quy-trinh/${proposalId}`),
  createProcessImprovement: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/cai-tien-quy-trinh`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateProcessImprovement: (proposalId, payload) =>
    testingRequest(`/cai-tien-quy-trinh/${proposalId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  linkProcessImprovementSources: (proposalId, payload) =>
    testingRequest(`/cai-tien-quy-trinh/${proposalId}/lien-ket-nguon`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  approveProcessImprovementExperiment: (proposalId, payload) =>
    testingRequest(`/cai-tien-quy-trinh/${proposalId}/phe-duyet-thu-nghiem`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  recordProcessImprovementBaseline: (proposalId, payload) =>
    testingRequest(`/cai-tien-quy-trinh/${proposalId}/duong-co-so`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  startProcessImprovementExperiment: (proposalId, payload) =>
    testingRequest(`/cai-tien-quy-trinh/${proposalId}/bat-dau`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  evaluateProcessImprovement: (proposalId, payload) =>
    testingRequest(`/cai-tien-quy-trinh/${proposalId}/danh-gia`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  decideProcessImprovement: (proposalId, payload, adopt = true) =>
    testingRequest(`/cai-tien-quy-trinh/${proposalId}/${adopt ? "ap-dung" : "tu-choi"}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listStatisticalQualityAnalyses: (projectId) =>
    testingRequest(`/du-an/${projectId}/kiem-soat-thong-ke`),
  getStatisticalQualityAnalysis: (analysisId) =>
    testingRequest(`/kiem-soat-thong-ke/${analysisId}`),
  calculateStatisticalQualityBaseline: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/kiem-soat-thong-ke`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  annotateStatisticalSpecialCause: (analysisId, payload) =>
    testingRequest(`/kiem-soat-thong-ke/${analysisId}/nguyen-nhan-dac-biet`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  compareStatisticalQuality: (projectId, payload) =>
    testingRequest(`/du-an/${projectId}/kiem-soat-thong-ke/so-sanh`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
