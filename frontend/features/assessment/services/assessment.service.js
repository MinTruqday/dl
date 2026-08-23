import { API_URL, authenticatedFetch } from "@/shared/services/api-client";
export async function assessmentRequest(path, options = {}) {
  const response = await authenticatedFetch(`${API_URL}${path}`, {
    ...options,

    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  const expected = options.expectedStatus;
  if (expected ? response.status !== expected : !response.ok) {
    const body = await response.json().catch(() => null);
    const error = new Error(
      typeof body?.detail === "string" ? body.detail : "Không thể hoàn tất yêu cầu",
    );
    error.status = response.status;
    error.detail = body?.detail;
    throw error;
  }
  if (response.status === 204) return undefined;
  return response.json();
}
export async function exportAssessmentVersion(versionId, format) {
  const response = await authenticatedFetch(
    `${API_URL}/exports/assessment/${encodeURIComponent(versionId)}/${format}`,
    {
      method: "POST",
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(typeof body?.detail === "string" ? body.detail : "Không thể xuất bài đánh giá");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${versionId}.${format}`;
  anchor.click();
  URL.revokeObjectURL(url);
}
export function listAssessmentDrafts() {
  return assessmentRequest("/assessment-drafts");
}
export function getAssessmentDraft(id) {
  return assessmentRequest(`/assessment-drafts/${id}`);
}
export function getAssessmentDifficultyAnalysis(id) {
  return assessmentRequest(`/assessment-drafts/${id}/difficulty-analysis`);
}
export function getAssessmentLearnerFit(id, abilityBand, targetSuccessRange = [0.45, 0.8]) {
  return assessmentRequest(`/assessment-drafts/${id}/learner-fit`, {
    method: "POST",
    body: JSON.stringify({
      target_learner: {
        ability_band: abilityBand,
        confidence: 0.4,
        source: "generic_learner_band",
      },
      target_success_range: targetSuccessRange,
    }),
  });
}
export function proposeAssessmentRebalance(id, expectedRevision) {
  return assessmentRequest(`/assessment-drafts/${id}/rebalance`, {
    method: "POST",
    body: JSON.stringify({
      expected_revision: expectedRevision,
      idempotency_key: `rebalance-${crypto.randomUUID()}`,
    }),
  });
}
export function approveAssessmentRebalance(id, proposalId) {
  return assessmentRequest(`/assessment-drafts/${id}/rebalance-proposals/${proposalId}/approve`, {
    method: "POST",
  });
}
export function rejectAssessmentRebalance(id, proposalId) {
  return assessmentRequest(`/assessment-drafts/${id}/rebalance-proposals/${proposalId}/reject`, {
    method: "POST",
  });
}
export function undoAssessmentRebalance(id, proposalId) {
  return assessmentRequest(`/assessment-drafts/${id}/rebalance-proposals/${proposalId}/undo`, {
    method: "POST",
  });
}
export function createAssessmentDraft(payload) {
  return assessmentRequest("/assessment-drafts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
export function updateAssessmentDraft(id, payload) {
  return assessmentRequest(`/assessment-drafts/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
export function createQuestionDraft(assessmentDraftId, payload) {
  return assessmentRequest(`/assessment-drafts/${assessmentDraftId}/questions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
export function updateQuestionDraft(id, payload) {
  return assessmentRequest(`/question-drafts/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
export function duplicateQuestionDraft(id) {
  return assessmentRequest(`/question-drafts/${id}/duplicate`, { method: "POST" });
}
export function deleteQuestionDraft(id) {
  return assessmentRequest(`/question-drafts/${id}`, { method: "DELETE", expectedStatus: 204 });
}
export function recordDifficultyTarget(id, targetDifficulty, blueprintId) {
  return assessmentRequest(`/question-drafts/${id}/target-difficulty`, {
    method: "POST",
    body: JSON.stringify({
      target_difficulty: targetDifficulty,
      blueprint_id: blueprintId || null,
    }),
  });
}
export function validateQuestionDraft(id) {
  return assessmentRequest(`/question-drafts/${id}/validate`, { method: "POST" });
}
export function recordTeacherEstimate(id, estimatedDifficulty, selfConfidence) {
  return assessmentRequest(`/question-drafts/${id}/teacher-estimate`, {
    method: "POST",
    body: JSON.stringify({
      estimated_difficulty: estimatedDifficulty,
      self_confidence: selfConfidence,
    }),
  });
}
export function recordValidityReview(id, status, riskFlags, reviewerNote) {
  return assessmentRequest(`/question-drafts/${id}/validity-review`, {
    method: "POST",
    body: JSON.stringify({ status, risk_flags: riskFlags, reviewer_note: reviewerNote }),
  });
}
export function predictDifficulty(id, predictionKind = "structured") {
  return assessmentRequest(`/question-drafts/${id}/predict-difficulty`, {
    method: "POST",
    body: JSON.stringify({
      model_version: predictionKind === "llm_direct" ? "llm_direct_v1" : "structured_cold_start_v2",
      prediction_kind: predictionKind,
    }),
  });
}
export function proposeQuestionDraftRevision(id, action, instruction = "") {
  return assessmentRequest(`/question-drafts/${id}/ai/revise`, {
    method: "POST",
    body: JSON.stringify({ action, instruction }),
  });
}
export function freezeQuestionDraft(id) {
  return assessmentRequest(`/question-drafts/${id}/freeze`, { method: "POST" });
}
export function restoreQuestionDraftVersion(id, versionId) {
  return assessmentRequest(`/question-drafts/${id}/restore-version/${versionId}`, {
    method: "POST",
  });
}
export function listAssessments() {
  return assessmentRequest("/assessments");
}
export function listQuestionBank(filters = {}) {
  const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => value));
  const queryString = query.toString();
  return assessmentRequest(`/questions${queryString ? `?${queryString}` : ""}`);
}
export function addQuestionBankItemsToDraft(assessmentDraftId, questionIds) {
  return assessmentRequest("/question-bank/add-to-draft", {
    method: "POST",
    body: JSON.stringify({ assessment_draft_id: assessmentDraftId, question_ids: questionIds }),
  });
}
export function duplicateQuestionBankItem(questionId) {
  return assessmentRequest(`/questions/${questionId}/duplicate`, { method: "POST" });
}
export function archiveQuestionBankItem(questionId, reason = "") {
  return assessmentRequest(`/questions/${questionId}/archive`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}
export function listQuestionVersions(questionId) {
  return assessmentRequest(`/questions/${questionId}/versions`);
}
export function getQuestionUsage(questionId) {
  return assessmentRequest(`/questions/${questionId}/usage`);
}
export function getTeacherDashboard() {
  return assessmentRequest("/dashboard/teacher");
}
export function getReviewQueue() {
  return assessmentRequest("/review-queue");
}
export function createTeacherMaterialMapping(documentId, payload) {
  return assessmentRequest(`/education/sources/${documentId}/map`, {
    method: "POST",
    body: JSON.stringify({
      ...payload,
      document_id: documentId,
      source_type: "teacher_material",
      authority: "supplementary",
    }),
  });
}
export function listSourceMappings(documentId) {
  return assessmentRequest(`/education/sources/${documentId}/mapping`);
}
export function searchTeacherMaterials(query, subject = "") {
  const params = new URLSearchParams({ q: query, limit: "20" });
  if (subject) params.set("subject", subject);
  return assessmentRequest(`/teacher-materials/search?${params.toString()}`);
}
export function reviewSourceMapping(documentId, mappingId, payload) {
  return assessmentRequest(`/education/sources/${documentId}/mapping/${mappingId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
export function getDifficultyComparison(assessmentId) {
  return assessmentRequest(`/assessments/${assessmentId}/difficulty-comparison`);
}
export function getAssessmentAnalytics(assessmentId) {
  return assessmentRequest(`/assessments/${assessmentId}/analytics`);
}
export function getResearchMetrics(questionId) {
  return assessmentRequest(`/questions/${questionId}/research-metrics`);
}
export function getResearchEvaluation() {
  return assessmentRequest("/research/evaluation");
}
export function listAssignedAssessments() {
  return assessmentRequest("/students/me/assessments");
}
export function getAssessmentPlayer(assessmentId, assignmentId) {
  const query = assignmentId ? `?assignment_id=${encodeURIComponent(assignmentId)}` : "";
  return assessmentRequest(`/assessments/${assessmentId}/player${query}`);
}
export function createAttempt(assessmentId, idempotencyKey, assignmentId) {
  return assessmentRequest(`/assessments/${assessmentId}/attempts`, {
    method: "POST",
    body: JSON.stringify({
      attempt_number: 1,
      assignment_id: assignmentId || null,
      idempotency_key: idempotencyKey,
    }),
  });
}
export function getAttempt(attemptId) {
  return assessmentRequest(`/attempts/${attemptId}`);
}
export function saveResponse(attemptId, payload) {
  return assessmentRequest(`/attempts/${attemptId}/responses`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
export function submitAttempt(attemptId) {
  return assessmentRequest(`/attempts/${attemptId}/submit`, { method: "POST" });
}
export function getAttemptResult(attemptId) {
  return assessmentRequest(`/attempts/${attemptId}/result`);
}
export function validateAssessmentDraft(id) {
  return assessmentRequest(`/assessment-drafts/${id}/validate`, { method: "POST" });
}
export function previewAssessmentDraft(id) {
  return assessmentRequest(`/assessment-drafts/${id}/preview`, { method: "POST" });
}
export function createBlueprint(payload) {
  return assessmentRequest("/blueprints", { method: "POST", body: JSON.stringify(payload) });
}
export function listBlueprintTemplates() {
  return assessmentRequest("/blueprints?templates_only=true");
}
export function cloneBlueprint(id) {
  return assessmentRequest(`/blueprints/${id}/clone`, { method: "POST" });
}
export function suggestBlueprintDistribution(totalQuestions, currentDistribution) {
  return assessmentRequest("/blueprints/suggest-distribution", {
    method: "POST",
    body: JSON.stringify({
      total_questions: totalQuestions,
      current_distribution: currentDistribution,
    }),
  });
}
export function createAssessment(assessmentDraftId, deliveryPolicy) {
  return assessmentRequest("/assessments", {
    method: "POST",
    body: JSON.stringify({
      assessment_draft_id: assessmentDraftId,
      delivery_policy: deliveryPolicy,
    }),
  });
}
export function publishAssessment(assessmentId, assessmentDraftId, expectedRevision, scheduledFor) {
  return assessmentRequest(`/assessments/${assessmentId}/publish`, {
    method: "POST",
    body: JSON.stringify({
      assessment_draft_id: assessmentDraftId,
      expected_revision: expectedRevision,
      idempotency_key: `publish-${crypto.randomUUID()}`,
      scheduled_for: scheduledFor || null,
    }),
  });
}
export function assignAssessment(assessmentId, studentIds, availableFrom, dueAt) {
  return assessmentRequest(`/assessments/${assessmentId}/assignments`, {
    method: "POST",
    body: JSON.stringify({
      student_ids: studentIds,
      available_from: availableFrom || null,
      due_at: dueAt || null,
      idempotency_key: `assign-${crypto.randomUUID()}`,
    }),
  });
}
export function cloneAssessment(assessmentId, title) {
  return assessmentRequest(`/assessments/${assessmentId}/clone`, {
    method: "POST",
    body: JSON.stringify({ title: title || null }),
  });
}
export function archiveAssessment(assessmentId, reason = "") {
  return assessmentRequest(`/assessments/${assessmentId}/archive`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}
export function unpublishAssessment(assessmentId, reason = "") {
  return assessmentRequest(`/assessments/${assessmentId}/unpublish`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}
