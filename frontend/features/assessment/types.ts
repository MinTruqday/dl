export type TiptapDoc = {
  type: "doc";
  content: Record<string, unknown>[];
};

export type QuestionOption = {
  id: string;
  content_doc: TiptapDoc;
};

export type QuestionDraft = {
  _id: string;
  assessment_draft_id: string;
  question_type: "single_choice" | "multiple_choice" | "true_false" | "matching" | "ordering" | "numeric" | "symbolic_math" | "short_answer" | "essay";
  authoring_source: "manual_tiptap" | "import" | "ai_generated" | "hybrid";
  stem_doc: TiptapDoc;
  options: QuestionOption[];
  answer_key: Record<string, unknown>;
  solution_doc: TiptapDoc;
  scoring_rule: Record<string, unknown>;
  curriculum_links: Record<string, unknown>[];
  concept_ids: string[];
  skill_ids: string[];
  tags: string[];
  question_id?: string | null;
  cognitive_level: string | null;
  construct: Record<string, unknown>;
  source_evidence: Record<string, unknown>[];
  revision: number;
  status: string;
  locked: boolean;
  frozen_version_id?: string;
  frozen_revision?: number;
  validity_review?: {
    status: "pending" | "approved" | "rejected";
    risk_flags: string[];
    reviewer_note?: string;
  };
};

export type Assessment = {
  _id: string;
  owner_id: string;
  assessment_draft_id: string;
  title?: string;
  status: string;
  current_version_id?: string;
  delivery_policy: Record<string, unknown>;
  target_context: Record<string, unknown>;
};

export type AssignedAssessment = {
  _id: string;
  assessment_id: string;
  assessment_version_id: string;
  status: string;
  availability_status?: "available" | "upcoming" | "expired";
  available_from?: string;
  due_at?: string;
  assessment?: Assessment;
  attempt?: Attempt;
};

export type PlayerQuestion = Omit<QuestionDraft, "answer_key" | "solution_doc"> & { version: number };

export type AssessmentPlayer = {
  assessment_id: string;
  assessment_version_id: string;
  assignment_id?: string | null;
  title: string;
  layout_doc: TiptapDoc;
  delivery_policy: Record<string, unknown>;
  items: { question_version_id: string; position: number; points: number; question: PlayerQuestion }[];
};

export type Attempt = {
  _id: string;
  assessment_id: string;
  assessment_version_id: string;
  assignment_id?: string;
  status: string;
  started_at?: string;
  expires_at?: string | null;
  policy_snapshot?: Record<string, unknown>;
  responses?: Record<string, unknown>[];
};

export type AssessmentDraft = {
  _id: string;
  title: string;
  context: Record<string, unknown>;
  layout_doc: TiptapDoc;
  question_order: string[];
  blueprint_id: string | null;
  revision: number;
  status: "draft" | "review" | "ready";
  research_blind_mode: boolean;
  questions?: QuestionDraft[];
  updated_at: string;
};

export const emptyTiptapDoc = (): TiptapDoc => ({ type: "doc", content: [] });

export function textDoc(text: string): TiptapDoc {
  return {
    type: "doc",
    content: text
      ? [{ type: "paragraph", content: [{ type: "text", text }] }]
      : [],
  };
}
