import { API_URL, authenticatedFetch } from "@/shared/services/api-client";
import type { AssignedAssessment, Assessment, AssessmentDraft, AssessmentPlayer, Attempt, QuestionDraft, TiptapDoc } from "../types";

type RequestOptions = RequestInit & { expectedStatus?: number };

export async function assessmentRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
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
    ) as Error & { status?: number; detail?: unknown };
    error.status = response.status;
    error.detail = body?.detail;
    throw error;
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function exportAssessmentVersion(versionId: string, format: "pdf" | "docx") {
  const response = await authenticatedFetch(`${API_URL}/exports/assessment/${encodeURIComponent(versionId)}/${format}`, {
    method: "POST",
  });
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
  return assessmentRequest<AssessmentDraft[]>("/assessment-drafts");
}

export function getAssessmentDraft(id: string) {
  return assessmentRequest<AssessmentDraft>(`/assessment-drafts/${id}`);
}

export function getAssessmentDifficultyAnalysis(id: string) {
  return assessmentRequest<Record<string, any>>(`/assessment-drafts/${id}/difficulty-analysis`);
}

export function getAssessmentLearnerFit(
  id: string,
  abilityBand: [number, number],
  targetSuccessRange: [number, number] = [0.45, 0.8],
) {
  return assessmentRequest<Record<string, any>>(`/assessment-drafts/${id}/learner-fit`, {
    method: "POST",
    body: JSON.stringify({
      target_learner: { ability_band: abilityBand, confidence: 0.4, source: "generic_learner_band" },
      target_success_range: targetSuccessRange,
    }),
  });
}

export function proposeAssessmentRebalance(id: string, expectedRevision: number) {
  return assessmentRequest<Record<string, any>>(`/assessment-drafts/${id}/rebalance`, {
    method: "POST",
    body: JSON.stringify({
      expected_revision: expectedRevision,
      idempotency_key: `rebalance-${crypto.randomUUID()}`,
    }),
  });
}

export function approveAssessmentRebalance(id: string, proposalId: string) {
  return assessmentRequest<Record<string, any>>(`/assessment-drafts/${id}/rebalance-proposals/${proposalId}/approve`, {
    method: "POST",
  });
}

export function rejectAssessmentRebalance(id: string, proposalId: string) {
  return assessmentRequest<Record<string, any>>(`/assessment-drafts/${id}/rebalance-proposals/${proposalId}/reject`, {
    method: "POST",
  });
}

export function undoAssessmentRebalance(id: string, proposalId: string) {
  return assessmentRequest<Record<string, any>>(`/assessment-drafts/${id}/rebalance-proposals/${proposalId}/undo`, {
    method: "POST",
  });
}

export function createAssessmentDraft(payload: {
  title: string;
  context: Record<string, unknown>;
  layout_doc: TiptapDoc;
  research_blind_mode: boolean;
}) {
  return assessmentRequest<AssessmentDraft>("/assessment-drafts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAssessmentDraft(
  id: string,
  payload: {
    expected_revision: number;
    title?: string;
    context?: Record<string, unknown>;
    layout_doc?: TiptapDoc;
    question_order?: string[];
    blueprint_id?: string;
    status?: string;
  },
) {
  return assessmentRequest<AssessmentDraft>(`/assessment-drafts/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function createQuestionDraft(
  assessmentDraftId: string,
  payload: Omit<QuestionDraft, "_id" | "assessment_draft_id" | "revision" | "status" | "frozen_version_id">,
) {
  return assessmentRequest<QuestionDraft>(`/assessment-drafts/${assessmentDraftId}/questions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateQuestionDraft(
  id: string,
  payload: Partial<QuestionDraft> & { expected_revision: number },
) {
  return assessmentRequest<QuestionDraft>(`/question-drafts/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function duplicateQuestionDraft(id: string) {
  return assessmentRequest<QuestionDraft>(`/question-drafts/${id}/duplicate`, { method: "POST" });
}

export function deleteQuestionDraft(id: string) {
  return assessmentRequest<void>(`/question-drafts/${id}`, { method: "DELETE", expectedStatus: 204 });
}

export function recordDifficultyTarget(id: string, targetDifficulty: number, blueprintId?: string | null) {
  return assessmentRequest<Record<string, unknown>>(`/question-drafts/${id}/target-difficulty`, {
    method: "POST",
    body: JSON.stringify({ target_difficulty: targetDifficulty, blueprint_id: blueprintId || null }),
  });
}

export function validateQuestionDraft(id: string) {
  return assessmentRequest<Record<string, unknown>>(`/question-drafts/${id}/validate`, { method: "POST" });
}

export function recordTeacherEstimate(id: string, estimatedDifficulty: number, selfConfidence: string) {
  return assessmentRequest<Record<string, unknown>>(`/question-drafts/${id}/teacher-estimate`, {
    method: "POST",
    body: JSON.stringify({ estimated_difficulty: estimatedDifficulty, self_confidence: selfConfidence }),
  });
}

export function recordValidityReview(id: string, status: "approved" | "rejected", riskFlags: string[], reviewerNote: string) {
  return assessmentRequest<QuestionDraft>(`/question-drafts/${id}/validity-review`, {
    method: "POST",
    body: JSON.stringify({ status, risk_flags: riskFlags, reviewer_note: reviewerNote }),
  });
}

export function predictDifficulty(id: string, predictionKind: "structured" | "llm_direct" = "structured") {
  return assessmentRequest<Record<string, unknown>>(`/question-drafts/${id}/predict-difficulty`, {
    method: "POST",
    body: JSON.stringify({
      model_version: predictionKind === "llm_direct" ? "llm_direct_v1" : "structured_cold_start_v2",
      prediction_kind: predictionKind,
    }),
  });
}

export function proposeQuestionDraftRevision(
  id: string,
  action: "clarify_wording" | "increase_difficulty" | "decrease_difficulty" | "regenerate_distractors" | "regenerate_item" | "change_question_type",
  instruction = "",
) {
  return assessmentRequest<Record<string, unknown>>(`/question-drafts/${id}/ai/revise`, {
    method: "POST",
    body: JSON.stringify({ action, instruction }),
  });
}

export function freezeQuestionDraft(id: string) {
  return assessmentRequest<Record<string, unknown>>(`/question-drafts/${id}/freeze`, { method: "POST" });
}

export function restoreQuestionDraftVersion(id: string, versionId: string) {
  return assessmentRequest<QuestionDraft>(`/question-drafts/${id}/restore-version/${versionId}`, { method: "POST" });
}

export function listAssessments() {
  return assessmentRequest<Assessment[]>("/assessments");
}

export function listQuestionBank(filters: Record<string, string> = {}) {
  const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => value));
  const queryString = query.toString();
  return assessmentRequest<Record<string, any>[]>(`/questions${queryString ? `?${queryString}` : ""}`);
}

export function addQuestionBankItemsToDraft(assessmentDraftId: string, questionIds: string[]) {
  return assessmentRequest<Record<string, any>>("/question-bank/add-to-draft", {
    method: "POST",
    body: JSON.stringify({ assessment_draft_id: assessmentDraftId, question_ids: questionIds }),
  });
}

export function duplicateQuestionBankItem(questionId: string) {
  return assessmentRequest<Record<string, any>>(`/questions/${questionId}/duplicate`, { method: "POST" });
}

export function archiveQuestionBankItem(questionId: string, reason = "") {
  return assessmentRequest<Record<string, any>>(`/questions/${questionId}/archive`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export function listQuestionVersions(questionId: string) {
  return assessmentRequest<Record<string, any>[]>(`/questions/${questionId}/versions`);
}

export function getQuestionUsage(questionId: string) {
  return assessmentRequest<Record<string, any>>(`/questions/${questionId}/usage`);
}

export function getTeacherDashboard() {
  return assessmentRequest<Record<string, unknown>>("/dashboard/teacher");
}

export function getReviewQueue() {
  return assessmentRequest<Record<string, unknown>>("/review-queue");
}

export function createTeacherMaterialMapping(documentId: string, payload: Record<string, unknown>) {
  return assessmentRequest<Record<string, any>>(`/education/sources/${documentId}/map`, {
    method: "POST",
    body: JSON.stringify({ ...payload, document_id: documentId, source_type: "teacher_material", authority: "supplementary" }),
  });
}

export function listSourceMappings(documentId: string) {
  return assessmentRequest<Record<string, any>[]>(`/education/sources/${documentId}/mapping`);
}

export function searchTeacherMaterials(query: string, subject = "") {
  const params = new URLSearchParams({ q: query, limit: "20" });
  if (subject) params.set("subject", subject);
  return assessmentRequest<Record<string, any>>(`/teacher-materials/search?${params.toString()}`);
}

export function reviewSourceMapping(documentId: string, mappingId: string, payload: Record<string, unknown>) {
  return assessmentRequest<Record<string, any>>(`/education/sources/${documentId}/mapping/${mappingId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getDifficultyComparison(assessmentId: string) {
  return assessmentRequest<Record<string, unknown>>(`/assessments/${assessmentId}/difficulty-comparison`);
}

export function getAssessmentAnalytics(assessmentId: string) {
  return assessmentRequest<Record<string, any>>(`/assessments/${assessmentId}/analytics`);
}

export function getResearchMetrics(questionId: string) {
  return assessmentRequest<Record<string, any>>(`/questions/${questionId}/research-metrics`);
}

export function getResearchEvaluation() {
  return assessmentRequest<Record<string, any>>("/research/evaluation");
}

export function listAssignedAssessments() {
  return assessmentRequest<AssignedAssessment[]>("/students/me/assessments");
}

export function getAssessmentPlayer(assessmentId: string, assignmentId?: string) {
  const query = assignmentId ? `?assignment_id=${encodeURIComponent(assignmentId)}` : "";
  return assessmentRequest<AssessmentPlayer>(`/assessments/${assessmentId}/player${query}`);
}

export function createAttempt(assessmentId: string, idempotencyKey: string, assignmentId?: string) {
  return assessmentRequest<Attempt>(`/assessments/${assessmentId}/attempts`, {
    method: "POST",
    body: JSON.stringify({ attempt_number: 1, assignment_id: assignmentId || null, idempotency_key: idempotencyKey }),
  });
}

export function getAttempt(attemptId: string) {
  return assessmentRequest<Attempt>(`/attempts/${attemptId}`);
}

export function saveResponse(attemptId: string, payload: Record<string, unknown>) {
  return assessmentRequest<Record<string, unknown>>(`/attempts/${attemptId}/responses`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function submitAttempt(attemptId: string) {
  return assessmentRequest<Attempt>(`/attempts/${attemptId}/submit`, { method: "POST" });
}

export function getAttemptResult(attemptId: string) {
  return assessmentRequest<Record<string, unknown>>(`/attempts/${attemptId}/result`);
}

export function validateAssessmentDraft(id: string) {
  return assessmentRequest<Record<string, any>>(`/assessment-drafts/${id}/validate`, { method: "POST" });
}

export function previewAssessmentDraft(id: string) {
  return assessmentRequest<Record<string, any>>(`/assessment-drafts/${id}/preview`, { method: "POST" });
}

export function createBlueprint(payload: Record<string, unknown>) {
  return assessmentRequest<Record<string, any>>("/blueprints", { method: "POST", body: JSON.stringify(payload) });
}

export function listBlueprintTemplates() {
  return assessmentRequest<Record<string, any>[]>("/blueprints?templates_only=true");
}

export function cloneBlueprint(id: string) {
  return assessmentRequest<Record<string, any>>(`/blueprints/${id}/clone`, { method: "POST" });
}

export function suggestBlueprintDistribution(totalQuestions: number, currentDistribution: Record<string, number>) {
  return assessmentRequest<Record<string, any>>("/blueprints/suggest-distribution", {
    method: "POST",
    body: JSON.stringify({ total_questions: totalQuestions, current_distribution: currentDistribution }),
  });
}

export function createAssessment(assessmentDraftId: string, deliveryPolicy: Record<string, unknown>) {
  return assessmentRequest<Assessment>("/assessments", { method: "POST", body: JSON.stringify({ assessment_draft_id: assessmentDraftId, delivery_policy: deliveryPolicy }) });
}

export function publishAssessment(assessmentId: string, assessmentDraftId: string, expectedRevision: number, scheduledFor?: string) {
  return assessmentRequest<Record<string, any>>(`/assessments/${assessmentId}/publish`, { method: "POST", body: JSON.stringify({ assessment_draft_id: assessmentDraftId, expected_revision: expectedRevision, idempotency_key: `publish-${crypto.randomUUID()}`, scheduled_for: scheduledFor || null }) });
}

export function assignAssessment(assessmentId: string, studentIds: string[], availableFrom?: string, dueAt?: string) {
  return assessmentRequest<Record<string, any>>(`/assessments/${assessmentId}/assignments`, {
    method: "POST",
    body: JSON.stringify({ student_ids: studentIds, available_from: availableFrom || null, due_at: dueAt || null, idempotency_key: `assign-${crypto.randomUUID()}` }),
  });
}

export function cloneAssessment(assessmentId: string, title?: string) {
  return assessmentRequest<AssessmentDraft>(`/assessments/${assessmentId}/clone`, {
    method: "POST",
    body: JSON.stringify({ title: title || null }),
  });
}

export function archiveAssessment(assessmentId: string, reason = "") {
  return assessmentRequest<Assessment>(`/assessments/${assessmentId}/archive`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export function unpublishAssessment(assessmentId: string, reason = "") {
  return assessmentRequest<Assessment>(`/assessments/${assessmentId}/unpublish`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}
