"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { BookOpenCheck, Database, FileUp, GripVertical, Plus, Sparkles } from "lucide-react";
import { Button } from "@/shared/components/ui/Button";
import TiptapDocumentEditor from "../editor/TiptapDocumentEditor";
import QuestionDraftCard from "../components/QuestionDraftCard";
import {
  createAssessment,
  createAssessmentDraft,
  createBlueprint,
  createQuestionDraft,
  cloneBlueprint,
  assignAssessment,
  approveAssessmentRebalance,
  getAssessmentDifficultyAnalysis,
  getAssessmentLearnerFit,
  getAssessmentDraft,
  listBlueprintTemplates,
  previewAssessmentDraft,
  proposeAssessmentRebalance,
  publishAssessment,
  rejectAssessmentRebalance,
  suggestBlueprintDistribution,
  undoAssessmentRebalance,
  updateAssessmentDraft,
  validateAssessmentDraft,
} from "../services/assessment.service";
import { emptyTiptapDoc, textDoc } from "../types";
import {
  distributeDifficulty,
  moveItem,
  questionTypes,
  validDifficultyDistribution,
} from "../lib/assessment.logic.mjs";
function messageOf(reason) {
  return reason instanceof Error ? reason.message : "Không thể hoàn tất thao tác";
}
const questionTypeLabels = {
  single_choice: "Một đáp án",
  multiple_choice: "Nhiều đáp án",
  true_false: "Đúng sai",
  matching: "Ghép cặp",
  ordering: "Sắp xếp",
  numeric: "Trả lời số",
  symbolic_math: "Biểu thức toán",
  short_answer: "Trả lời ngắn",
  essay: "Tự luận",
};
const cognitiveLevels = [
  ["recognition", "Nhận biết"],
  ["comprehension", "Thông hiểu"],
  ["application", "Vận dụng"],
  ["analysis", "Phân tích"],
];
export default function AssessmentComposerPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const requestedId = searchParams.get("id") || "";
  const [draft, setDraft] = useState(null);
  const [layout, setLayout] = useState(emptyTiptapDoc());
  const [title, setTitle] = useState("");
  const [educationLevel, setEducationLevel] = useState("THPT");
  const [subject, setSubject] = useState("math");
  const [targetProgram, setTargetProgram] = useState("grade_12");
  const [loading, setLoading] = useState(Boolean(requestedId));
  const [status, setStatus] = useState(requestedId ? "Đang tải" : "Bản nháp mới");
  const [error, setError] = useState("");
  const [validation, setValidation] = useState(null);
  const [preview, setPreview] = useState(null);
  const [difficultyAnalysis, setDifficultyAnalysis] = useState(null);
  const [learnerFit, setLearnerFit] = useState(null);
  const [rebalanceProposal, setRebalanceProposal] = useState(null);
  const [difficultyDistribution, setDifficultyDistribution] = useState(distributeDifficulty(0));
  const [blueprintTotalQuestions, setBlueprintTotalQuestions] = useState(1);
  const [blueprintTotalPoints, setBlueprintTotalPoints] = useState("1");
  const [questionTypeConstraints, setQuestionTypeConstraints] = useState({});
  const [cognitiveLevelConstraints, setCognitiveLevelConstraints] = useState({});
  const [includeCognitiveConstraints, setIncludeCognitiveConstraints] = useState(true);
  const [durationMinutes, setDurationMinutes] = useState(45);
  const [coverageConcepts, setCoverageConcepts] = useState("");
  const [coverageSkills, setCoverageSkills] = useState("");
  const [coverageCurriculumNodes, setCoverageCurriculumNodes] = useState("");
  const [abilityMinimum, setAbilityMinimum] = useState("1");
  const [abilityMaximum, setAbilityMaximum] = useState("5");
  const [assessmentPurpose, setAssessmentPurpose] = useState("assigned_assessment");
  const [maximumExposureCount, setMaximumExposureCount] = useState("");
  const [coverageRequired, setCoverageRequired] = useState(true);
  const [saveAsTemplate, setSaveAsTemplate] = useState(false);
  const [templateName, setTemplateName] = useState("");
  const [blueprintTemplates, setBlueprintTemplates] = useState([]);
  const [attemptLimit, setAttemptLimit] = useState(1);
  const [navigation, setNavigation] = useState("free");
  const [shuffleQuestions, setShuffleQuestions] = useState(false);
  const [shuffleOptions, setShuffleOptions] = useState(false);
  const [highStakes, setHighStakes] = useState(false);
  const [scheduledFor, setScheduledFor] = useState("");
  const [publishedAssessmentId, setPublishedAssessmentId] = useState("");
  const [studentIds, setStudentIds] = useState("");
  const [availableFrom, setAvailableFrom] = useState("");
  const [dueAt, setDueAt] = useState("");
  const revisionRef = useRef(0);
  const layoutReadyRef = useRef(false);
  const draggedIndexRef = useRef(null);
  const draftRef = useRef(draft);
  draftRef.current = draft;
  const load = useCallback(async (id) => {
    setLoading(true);
    setError("");
    try {
      const value = await getAssessmentDraft(id);
      setDraft(value);
      setTitle(value.title);
      setEducationLevel(value.context?.education_level || "THPT");
      setSubject(value.context?.subject || "math");
      setTargetProgram(value.context?.target_program || "grade_12");
      setLayout(value.layout_doc);
      setHighStakes(Boolean(value.context?.high_stakes));
      const questionCount = value.questions?.length || 0;
      setBlueprintTotalQuestions(Math.max(1, questionCount));
      setBlueprintTotalPoints(
        String(
          (value.questions || []).reduce((sum, question) => {
            return sum + Number(question.scoring_rule?.points || 1);
          }, 0) || 1,
        ),
      );
      setDifficultyDistribution(distributeDifficulty(questionCount));
      setQuestionTypeConstraints(
        (value.questions || []).reduce((result, question) => {
          result[question.question_type] = (result[question.question_type] || 0) + 1;
          return result;
        }, {}),
      );
      setCognitiveLevelConstraints(
        (value.questions || []).reduce((result, question) => {
          const level = question.cognitive_level || "recognition";
          result[level] = (result[level] || 0) + 1;
          return result;
        }, {}),
      );
      revisionRef.current = value.revision;
      layoutReadyRef.current = false;
      setStatus("Đã tải");
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    if (requestedId) void load(requestedId);
  }, [load, requestedId]);
  useEffect(() => {
    void listBlueprintTemplates()
      .then(setBlueprintTemplates)
      .catch((reason) => setError(messageOf(reason)));
  }, []);
  useEffect(() => {
    const activeDraft = draftRef.current;
    if (!activeDraft) return;
    if (!layoutReadyRef.current) {
      layoutReadyRef.current = true;
      return;
    }
    setStatus("Đang lưu");
    const timer = window.setTimeout(async () => {
      try {
        const updated = await updateAssessmentDraft(activeDraft._id, {
          expected_revision: revisionRef.current,
          title,
          context: {
            ...activeDraft.context,
            high_stakes: highStakes,
          },
          layout_doc: layout,
        });
        revisionRef.current = updated.revision;
        setDraft((current) =>
          current
            ? {
                ...current,
                ...updated,
                questions: current.questions,
              }
            : updated,
        );
        setStatus("Đã lưu");
      } catch (reason) {
        const conflict = reason;
        setStatus(conflict.status === 409 ? "Có thay đổi ở phiên khác" : "Chưa lưu");
        setError(messageOf(reason));
      }
    }, 1200);
    return () => window.clearTimeout(timer);
  }, [draft?._id, highStakes, layout, title]);
  const startDraft = async () => {
    if (!title.trim()) {
      setError("Nhập tên bài đánh giá trước khi tạo bản nháp");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const created = await createAssessmentDraft({
        title: title.trim(),
        context: {
          education_level: educationLevel,
          subject,
          target_program: targetProgram,
          high_stakes: highStakes,
        },
        layout_doc: textDoc("Hướng dẫn làm bài"),
        research_blind_mode: true,
      });
      router.replace(`/giao-vien/de/soan-thao?id=${created._id}`);
      await load(created._id);
    } catch (reason) {
      setError(messageOf(reason));
      setLoading(false);
    }
  };
  const addQuestion = async (source) => {
    if (!draft) return;
    if (source === "import") {
      router.push(`/giao-vien/de/nhap?id=${draft._id}`);
      return;
    }
    if (source === "ai_generated") {
      router.push(`/giao-vien/de/sinh-ai?id=${draft._id}`);
      return;
    }
    setError("");
    try {
      const question = await createQuestionDraft(draft._id, {
        question_type: "single_choice",
        authoring_source: source,
        stem_doc: textDoc("Nhập nội dung câu hỏi"),
        options: [
          { id: "A", content_doc: textDoc("Phương án A") },
          { id: "B", content_doc: textDoc("Phương án B") },
          { id: "C", content_doc: textDoc("Phương án C") },
          { id: "D", content_doc: textDoc("Phương án D") },
        ],
        answer_key: { option_id: "A" },
        solution_doc: emptyTiptapDoc(),
        scoring_rule: { points: 1 },
        curriculum_links: [
          {
            subject: draft.context?.subject || subject,
            target_program: draft.context?.target_program || targetProgram,
          },
        ],
        concept_ids: [],
        skill_ids: [],
        tags: [],
        cognitive_level: "recognition",
        construct: {
          primary_concept: "",
          primary_skill: "",
          learning_objective: "",
          reasoning_steps: 1,
        },
        source_evidence: [],
        locked: false,
      });
      await load(draft._id);
      setStatus(`Đã thêm ${question._id}`);
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const validate = async () => {
    if (!draft) return;
    setValidation(await validateAssessmentDraft(draft._id));
  };
  const showPreview = async () => {
    if (!draft) return;
    setPreview(await previewAssessmentDraft(draft._id));
  };
  const analyzeDifficulty = async () => {
    if (!draft) return;
    try {
      setDifficultyAnalysis(await getAssessmentDifficultyAnalysis(draft._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const analyzeLearnerFit = async () => {
    if (!draft) return;
    try {
      setLearnerFit(
        await getAssessmentLearnerFit(draft._id, [Number(abilityMinimum), Number(abilityMaximum)]),
      );
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const proposeRebalance = async () => {
    if (!draft) return;
    setError("");
    try {
      const proposal = await proposeAssessmentRebalance(draft._id, revisionRef.current);
      setRebalanceProposal(proposal);
      setStatus(
        proposal.status === "infeasible"
          ? "Không tìm thấy phương án cân bằng khả thi"
          : "Đã tạo đề xuất cân bằng",
      );
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const decideRebalance = async (decision) => {
    if (!draft || !rebalanceProposal) return;
    setError("");
    try {
      if (decision === "approve") {
        const approved = await approveAssessmentRebalance(draft._id, String(rebalanceProposal._id));
        setRebalanceProposal((current) => {
          return current
            ? {
                ...current,
                status: "approved",

                applied_revision: approved.assessment_draft?.revision,
              }
            : current;
        });
        await load(draft._id);
        setStatus("Đã áp dụng đề xuất cân bằng");
      } else {
        const rejected = await rejectAssessmentRebalance(draft._id, String(rebalanceProposal._id));
        setRebalanceProposal(rejected);
        setStatus("Đã từ chối đề xuất cân bằng");
      }
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const undoRebalance = async () => {
    if (!draft || !rebalanceProposal) return;
    setError("");
    try {
      await undoAssessmentRebalance(draft._id, String(rebalanceProposal._id));
      setRebalanceProposal((current) =>
        current
          ? {
              ...current,
              status: "undone",
            }
          : current,
      );
      await load(draft._id);
      setStatus("Đã hoàn tác đề xuất cân bằng");
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const buildBlueprint = async () => {
    if (!draft) return;
    const total = blueprintTotalQuestions;
    if (!validDifficultyDistribution(total, difficultyDistribution)) {
      setError("Tổng phân bố năm mức phải bằng số câu hỏi");
      return;
    }
    const conceptConstraints = coverageConcepts
      .split(/[,;\n]+/)
      .map((value) => value.trim())
      .filter(Boolean)
      .map((id) => ({
        dimension: "concept",
        ids: [id],
        minimum_count: 1,
        required: coverageRequired,
      }));
    const skillConstraints = coverageSkills
      .split(/[,;\n]+/)
      .map((value) => value.trim())
      .filter(Boolean)
      .map((id) => ({
        dimension: "skill",
        ids: [id],
        minimum_count: 1,
        required: coverageRequired,
      }));
    const curriculumConstraints = coverageCurriculumNodes
      .split(/[,;\n]+/)
      .map((value) => value.trim())
      .filter(Boolean)
      .map((id) => ({
        dimension: "curriculum_node",
        ids: [id],
        minimum_count: 1,
        required: coverageRequired,
      }));
    const blueprint = await createBlueprint({
      name: templateName.trim() || undefined,
      total_questions: total,
      difficulty_distribution: difficultyDistribution,
      coverage_constraints: [...curriculumConstraints, ...conceptConstraints, ...skillConstraints],
      question_type_constraints: questionTypeConstraints,
      cognitive_level_constraints: includeCognitiveConstraints ? cognitiveLevelConstraints : {},
      target_learner: {
        ...draft.context,
        ability_band: [Number(abilityMinimum), Number(abilityMaximum)],
      },
      duration_minutes: durationMinutes,
      assessment_purpose: assessmentPurpose,
      total_points: Number(blueprintTotalPoints),
      maximum_exposure_count: maximumExposureCount === "" ? null : Number(maximumExposureCount),
      is_template: saveAsTemplate,
    });
    const updated = await updateAssessmentDraft(draft._id, {
      expected_revision: revisionRef.current,
      blueprint_id: blueprint._id,
    });
    revisionRef.current = updated.revision;
    setDraft((current) =>
      current
        ? {
            ...current,
            ...updated,
            questions: current.questions,
          }
        : current,
    );
    if (saveAsTemplate) setBlueprintTemplates(await listBlueprintTemplates());
    setStatus(saveAsTemplate ? "Đã tạo và lưu Blueprint mẫu" : "Đã tạo Blueprint");
  };
  const suggestDistribution = async () => {
    const total = blueprintTotalQuestions;
    try {
      const suggestion = await suggestBlueprintDistribution(total, difficultyDistribution);
      if (suggestion.valid) {
        setDifficultyDistribution(suggestion.suggested_distribution);
        setStatus("Đã nhận gợi ý và đang chờ xác nhận tạo Blueprint");
      } else {
        setError(`Phân bố đang vượt quá ${Math.abs(Number(suggestion.missing_or_excess))} câu`);
      }
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const applyBlueprintTemplate = async (templateId) => {
    if (!draft) return;
    try {
      const blueprint = await cloneBlueprint(templateId);
      const updated = await updateAssessmentDraft(draft._id, {
        expected_revision: revisionRef.current,
        blueprint_id: blueprint._id,
      });
      revisionRef.current = updated.revision;
      setDraft((current) =>
        current
          ? {
              ...current,
              ...updated,
              questions: current.questions,
            }
          : current,
      );
      setBlueprintTotalQuestions(Number(blueprint.total_questions));
      setDifficultyDistribution(
        blueprint.difficulty_distribution ||
          distributeDifficulty(Number(blueprint.total_questions)),
      );
      setQuestionTypeConstraints(blueprint.question_type_constraints || {});
      setCognitiveLevelConstraints(blueprint.cognitive_level_constraints || {});
      setIncludeCognitiveConstraints(
        Object.keys(blueprint.cognitive_level_constraints || {}).length > 0,
      );
      const constraints = Array.isArray(blueprint.coverage_constraints)
        ? blueprint.coverage_constraints
        : [];
      const idsFor = (dimension) =>
        constraints
          .filter((item) => item.dimension === dimension)
          .flatMap((item) => item.ids || [])
          .join(", ");
      setCoverageCurriculumNodes(idsFor("curriculum_node"));
      setCoverageConcepts(idsFor("concept"));
      setCoverageSkills(idsFor("skill"));
      if (constraints.length) setCoverageRequired(constraints.some((item) => item.required));
      setDurationMinutes(Number(blueprint.duration_minutes || 45));
      setBlueprintTotalPoints(String(blueprint.total_points || blueprint.total_questions));
      setAssessmentPurpose(String(blueprint.assessment_purpose || "assigned_assessment"));
      setMaximumExposureCount(
        blueprint.maximum_exposure_count === null || blueprint.maximum_exposure_count === undefined
          ? ""
          : String(blueprint.maximum_exposure_count),
      );
      const abilityBand = blueprint.target_learner?.ability_band;
      if (Array.isArray(abilityBand) && abilityBand.length === 2) {
        setAbilityMinimum(String(abilityBand[0]));
        setAbilityMaximum(String(abilityBand[1]));
      }
      setStatus("Đã nhân bản và áp dụng Blueprint mẫu");
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const publish = async () => {
    if (!draft) return;
    setError("");
    try {
      const check = await validateAssessmentDraft(draft._id);
      setValidation(check);
      if (!check.valid) throw new Error("Cần xử lý toàn bộ blocker trước khi xuất bản");
      const assessment = await createAssessment(draft._id, {
        delivery_mode: "fixed",
        review_answers: true,
        navigation,
        attempt_limit: attemptLimit,
        duration_minutes: durationMinutes,
        shuffle_options: shuffleOptions,
        shuffle_questions: shuffleQuestions,
        allow_review_flags: true,
      });
      const version = await publishAssessment(
        assessment._id,
        draft._id,
        revisionRef.current,
        scheduledFor ? new Date(scheduledFor).toISOString() : undefined,
      );
      setPublishedAssessmentId(assessment._id);
      setStatus(
        version.scheduled_for ? `Đã lên lịch ${version._id}` : `Đã xuất bản ${version._id}`,
      );
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const assign = async () => {
    if (!publishedAssessmentId) return;
    const ids = studentIds
      .split(/[\s,;]+/)
      .map((value) => value.trim())
      .filter(Boolean);
    if (!ids.length) {
      setError("Cần nhập ít nhất một mã học sinh");
      return;
    }
    try {
      const result = await assignAssessment(
        publishedAssessmentId,
        ids,
        availableFrom ? new Date(availableFrom).toISOString() : undefined,
        dueAt ? new Date(dueAt).toISOString() : undefined,
      );
      setStatus(`Đã giao cho ${result.assignments?.length || ids.length} học sinh`);
      setStudentIds("");
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const replaceQuestion = useCallback((updated) => {
    setDraft((current) =>
      current
        ? {
            ...current,

            questions: (current.questions || []).map((question) =>
              question._id === updated._id ? updated : question,
            ),
          }
        : current,
    );
  }, []);
  const reorderQuestions = async (from, to) => {
    if (!draft || from === to) return;
    const order = moveItem(draft.question_order, from, to);
    try {
      const updated = await updateAssessmentDraft(draft._id, {
        expected_revision: revisionRef.current,
        question_order: order,
      });
      revisionRef.current = updated.revision;
      setDraft((current) =>
        current
          ? {
              ...current,
              ...updated,
              questions: moveItem(current.questions || [], from, to),
            }
          : current,
      );
      setStatus("Đã cập nhật thứ tự");
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <div className="min-h-[calc(100dvh-60px)] bg-canvas">
      <header className="sticky top-[60px] z-20 border-b border-border bg-surface/95 px-4 py-3 backdrop-blur md:px-7">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center gap-3">
          <BookOpenCheck className="text-brand" size={22} />
          {draft ? (
            <input
              className="min-w-0 flex-1 bg-transparent text-[18px] font-semibold outline-none"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              aria-label="Tên bài đánh giá"
            />
          ) : (
            <p className="min-w-0 flex-1 text-[18px] font-semibold">Soạn bài đánh giá mới</p>
          )}
          <span className="text-[12px] text-ink-muted">{status}</span>
          <Button variant="secondary" disabled={!draft} onClick={showPreview}>
            Xem như học sinh
          </Button>
          <Button variant="secondary" disabled={!draft} onClick={validate}>
            Kiểm định đề
          </Button>
          <Button disabled={!draft} onClick={publish}>
            Xuất bản
          </Button>
        </div>
      </header>

      <div
        className={`mx-auto grid max-w-[1500px] gap-6 p-4 md:p-7 ${draft ? "xl:grid-cols-[minmax(0,1fr)_320px]" : "max-w-[980px]"}`}
      >
        <div className="space-y-5">
          {!draft && !loading ? (
            <section className="rounded-panel border border-border bg-surface p-6 md:p-8">
              <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">
                Thiết lập bài đánh giá
              </p>
              <h1 className="mt-3 text-[30px] font-semibold tracking-[-0.035em]">
                Bắt đầu một đề kiểm tra có bằng chứng
              </h1>
              <p className="mt-3 max-w-[680px] text-[14px] text-ink-muted">
                Soạn thủ công nhập đề có sẵn hoặc nhận đề xuất từ AI trong cùng một cấu trúc câu hỏi
                có version và kiểm định
              </p>
              <div className="mt-7 grid gap-4 sm:grid-cols-2">
                <label className="text-[12px] font-semibold text-ink-muted sm:col-span-2">
                  Tên bài đánh giá
                  <input
                    className="apple-input mt-1 w-full"
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    placeholder="Ví dụ Kiểm tra cuối chương Hàm số"
                    autoFocus
                  />
                </label>
                <label className="text-[12px] font-semibold text-ink-muted">
                  Cấp học
                  <select
                    className="apple-input mt-1 w-full"
                    value={educationLevel}
                    onChange={(event) => setEducationLevel(event.target.value)}
                  >
                    <option value="THCS">Trung học cơ sở</option>
                    <option value="THPT">Trung học phổ thông</option>
                  </select>
                </label>
                <label className="text-[12px] font-semibold text-ink-muted">
                  Môn học
                  <select
                    className="apple-input mt-1 w-full"
                    value={subject}
                    onChange={(event) => setSubject(event.target.value)}
                  >
                    <option value="math">Toán</option>
                    <option value="physics">Vật lý</option>
                    <option value="chemistry">Hóa học</option>
                    <option value="biology">Sinh học</option>
                    <option value="literature">Ngữ văn</option>
                    <option value="english">Tiếng Anh</option>
                  </select>
                </label>
                <label className="text-[12px] font-semibold text-ink-muted">
                  Chương trình mục tiêu
                  <input
                    className="apple-input mt-1 w-full"
                    value={targetProgram}
                    onChange={(event) => setTargetProgram(event.target.value)}
                    placeholder="Ví dụ grade_12"
                  />
                </label>
                <label className="flex items-center gap-2 self-end rounded-control bg-surface-quiet p-3 text-[12px]">
                  <input
                    type="checkbox"
                    checked={highStakes}
                    onChange={(event) => setHighStakes(event.target.checked)}
                  />
                  Dùng cho quyết định quan trọng
                </label>
              </div>
              <div className="mt-6 flex flex-wrap items-center gap-3">
                <Button onClick={startDraft}>Tạo bản nháp</Button>
                <p className="text-[12px] text-ink-muted">
                  Mọi dự đoán độ khó vẫn phải qua giáo viên kiểm định trước khi xuất bản
                </p>
              </div>
            </section>
          ) : loading ? (
            <div className="skeleton h-80" />
          ) : (
            <>
              <section>
                <div className="mb-2 flex items-center justify-between">
                  <h2 className="text-[14px] font-semibold">Hướng dẫn và bố cục đề</h2>
                  <span className="text-[12px] text-ink-muted">Tiptap JSON v1</span>
                </div>
                <TiptapDocumentEditor
                  value={layout}
                  onChange={setLayout}
                  label="Hướng dẫn và bố cục bài đánh giá"
                  minHeight="min-h-52"
                />
              </section>

              <div className="flex flex-wrap gap-2">
                <Button onClick={() => addQuestion("manual_tiptap")}>
                  <Plus size={16} /> Câu thủ công
                </Button>
                <Button variant="secondary" onClick={() => addQuestion("import")}>
                  <FileUp size={16} /> Nhập từ đề
                </Button>
                <Button variant="secondary" onClick={() => addQuestion("ai_generated")}>
                  <Sparkles size={16} /> AI đề xuất
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => draft && router.push(`/giao-vien/cau-hoi?draft=${draft._id}`)}
                >
                  <Database size={16} /> Ngân hàng câu hỏi
                </Button>
              </div>

              {(draft?.questions || []).map((question, index) => (
                <div
                  key={question._id}
                  draggable
                  onDragStart={() => {
                    draggedIndexRef.current = index;
                  }}
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={() => {
                    if (draggedIndexRef.current !== null)
                      void reorderQuestions(draggedIndexRef.current, index);
                    draggedIndexRef.current = null;
                  }}
                >
                  <div className="mb-1 flex items-center gap-1 text-[11px] text-ink-muted">
                    <GripVertical size={14} /> Kéo để đổi thứ tự
                  </div>
                  <QuestionDraftCard
                    question={question}
                    index={index}
                    researchBlindMode={draft?.research_blind_mode || false}
                    blueprintId={draft?.blueprint_id}
                    highStakes={highStakes}
                    onUpdated={replaceQuestion}
                    onReload={() => (draft ? load(draft._id) : Promise.resolve())}
                  />
                </div>
              ))}
              {preview && (
                <section className="rounded-panel border border-brand bg-brand-soft p-5">
                  <h2 className="font-semibold">Bản xem trước học sinh</h2>
                  <p className="mt-2 text-[13px] text-ink-muted">
                    {preview.title} · {preview.items?.length || 0} câu · không chứa đáp án
                  </p>
                </section>
              )}
              {validation && (
                <section
                  className={`rounded-panel border p-5 ${validation.valid ? "border-brand bg-brand-soft" : "border-danger bg-danger-soft"}`}
                >
                  <h2 className="font-semibold">
                    Kiểm định AssessmentDraft {validation.valid ? "đạt" : "chưa đạt"}
                  </h2>
                  <p className="mt-2 text-[12px]">
                    {validation.issues?.map((issue) => issue.code).join(" · ") ||
                      "Không có blocker"}
                  </p>
                </section>
              )}
            </>
          )}
          {error && (
            <p
              role="alert"
              className="rounded-control bg-danger-soft px-4 py-3 text-[13px] text-danger"
            >
              {error}
            </p>
          )}
        </div>

        {draft && (
          <aside className="space-y-4 xl:sticky xl:top-[132px] xl:self-start">
            <section className="rounded-panel border border-border bg-surface p-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-ink-faint">
                Blueprint
              </p>
              <label className="mt-3 block text-[12px] font-semibold text-ink-muted">
                Tổng số câu mục tiêu
                <input
                  className="apple-input mt-1 w-full"
                  type="number"
                  min="1"
                  max="500"
                  value={blueprintTotalQuestions}
                  onChange={(event) =>
                    setBlueprintTotalQuestions(Math.max(1, Number(event.target.value) || 1))
                  }
                />
              </label>
              <label className="mt-3 block text-[12px] font-semibold text-ink-muted">
                Tổng điểm mục tiêu
                <input
                  className="apple-input mt-1 w-full"
                  type="number"
                  min="0.1"
                  max="10000"
                  step="0.1"
                  value={blueprintTotalPoints}
                  onChange={(event) => setBlueprintTotalPoints(event.target.value)}
                />
              </label>
              <div className="mt-4 grid grid-cols-5 gap-1.5">
                {[1, 2, 3, 4, 5].map((level) => (
                  <div
                    key={level}
                    className="rounded-control bg-surface-quiet px-2 py-3 text-center"
                  >
                    <p className="text-[11px] text-ink-muted">Mức {level}</p>
                    <input
                      className="mt-1 w-full bg-transparent text-center text-[18px] font-semibold outline-none"
                      type="number"
                      min="0"
                      value={difficultyDistribution[String(level)] || 0}
                      onChange={(event) =>
                        setDifficultyDistribution((current) => ({
                          ...current,
                          [String(level)]: Math.max(0, Number(event.target.value) || 0),
                        }))
                      }
                      aria-label={`Số câu mức ${level}`}
                    />
                  </div>
                ))}
              </div>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-surface-quiet">
                <div
                  className="h-full bg-brand transition-[width]"
                  style={{
                    width: `${Math.min(100, (Object.values(difficultyDistribution).reduce((sum, value) => sum + value, 0) / Math.max(1, blueprintTotalQuestions)) * 100)}%`,
                  }}
                />
              </div>
              <p className="mt-2 text-[12px] text-ink-muted">
                Tổng {Object.values(difficultyDistribution).reduce((sum, value) => sum + value, 0)}{" "}
                trên {blueprintTotalQuestions} câu mục tiêu và hiện có{" "}
                {draft?.questions?.length || 0} câu
              </p>
              <button
                type="button"
                className="apple-button-secondary mt-3 w-full"
                disabled={!draft}
                onClick={suggestDistribution}
              >
                Gợi ý phần phân bố còn thiếu
              </button>
              <details className="mt-3 rounded-control border border-border px-3 py-2">
                <summary className="cursor-pointer text-[12px] font-semibold">
                  Phân bố loại câu hỏi
                </summary>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  {questionTypes.map((type) => (
                    <label key={type} className="text-[11px] text-ink-muted">
                      {questionTypeLabels[type]}
                      <input
                        className="apple-input mt-1 w-full"
                        type="number"
                        min="0"
                        max="500"
                        value={questionTypeConstraints[type] || 0}
                        onChange={(event) =>
                          setQuestionTypeConstraints((current) => ({
                            ...current,
                            [type]: Math.max(0, Number(event.target.value) || 0),
                          }))
                        }
                      />
                    </label>
                  ))}
                </div>
              </details>
              <details className="mt-3 rounded-control border border-border px-3 py-2">
                <summary className="cursor-pointer text-[12px] font-semibold">
                  Phân bố mức nhận thức
                </summary>
                <label className="mt-3 flex items-center gap-2 text-[11px] text-ink-muted">
                  <input
                    type="checkbox"
                    checked={includeCognitiveConstraints}
                    onChange={(event) => setIncludeCognitiveConstraints(event.target.checked)}
                  />{" "}
                  Áp dụng ràng buộc nhận thức
                </label>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  {cognitiveLevels.map(([level, label]) => (
                    <label key={level} className="text-[11px] text-ink-muted">
                      {label}
                      <input
                        className="apple-input mt-1 w-full"
                        type="number"
                        min="0"
                        max="500"
                        disabled={!includeCognitiveConstraints}
                        value={cognitiveLevelConstraints[level] || 0}
                        onChange={(event) =>
                          setCognitiveLevelConstraints((current) => ({
                            ...current,
                            [level]: Math.max(0, Number(event.target.value) || 0),
                          }))
                        }
                      />
                    </label>
                  ))}
                </div>
              </details>
              <label className="mt-3 block text-[12px] font-semibold text-ink-muted">
                Concept bắt buộc
                <input
                  className="apple-input mt-1 w-full"
                  value={coverageConcepts}
                  onChange={(event) => setCoverageConcepts(event.target.value)}
                  placeholder="dao_ham cuc_tri"
                />
              </label>
              <label className="mt-3 block text-[12px] font-semibold text-ink-muted">
                Skill bắt buộc
                <input
                  className="apple-input mt-1 w-full"
                  value={coverageSkills}
                  onChange={(event) => setCoverageSkills(event.target.value)}
                  placeholder="differentiate analyze"
                />
              </label>
              <label className="mt-3 block text-[12px] font-semibold text-ink-muted">
                Topic hoặc curriculum node
                <input
                  className="apple-input mt-1 w-full"
                  value={coverageCurriculumNodes}
                  onChange={(event) => setCoverageCurriculumNodes(event.target.value)}
                  placeholder="chapter lesson section"
                />
              </label>
              <label className="mt-3 flex items-center gap-2 text-[12px] font-semibold text-ink-muted">
                <input
                  type="checkbox"
                  checked={coverageRequired}
                  onChange={(event) => setCoverageRequired(event.target.checked)}
                />{" "}
                Coverage là bắt buộc
              </label>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <label className="text-[12px] font-semibold text-ink-muted">
                  Năng lực từ
                  <input
                    className="apple-input mt-1 w-full"
                    type="number"
                    min="1"
                    max="5"
                    step="0.1"
                    value={abilityMinimum}
                    onChange={(event) => setAbilityMinimum(event.target.value)}
                  />
                </label>
                <label className="text-[12px] font-semibold text-ink-muted">
                  Đến
                  <input
                    className="apple-input mt-1 w-full"
                    type="number"
                    min="1"
                    max="5"
                    step="0.1"
                    value={abilityMaximum}
                    onChange={(event) => setAbilityMaximum(event.target.value)}
                  />
                </label>
              </div>
              <label className="mt-3 block text-[12px] font-semibold text-ink-muted">
                Mục đích
                <select
                  className="apple-input mt-1 w-full"
                  value={assessmentPurpose}
                  onChange={(event) => setAssessmentPurpose(event.target.value)}
                >
                  <option value="assigned_assessment">Bài được giao</option>
                  <option value="formative">Đánh giá thường xuyên</option>
                  <option value="summative">Đánh giá tổng kết</option>
                  <option value="research_retest">Kiểm định lại nghiên cứu</option>
                </select>
              </label>
              <label className="mt-3 block text-[12px] font-semibold text-ink-muted">
                Exposure tối đa mỗi câu
                <input
                  className="apple-input mt-1 w-full"
                  type="number"
                  min="0"
                  value={maximumExposureCount}
                  onChange={(event) => setMaximumExposureCount(event.target.value)}
                  placeholder="Không giới hạn"
                />
              </label>
              <label className="mt-3 flex items-center gap-2 text-[12px] font-semibold text-ink-muted">
                <input
                  type="checkbox"
                  checked={saveAsTemplate}
                  onChange={(event) => setSaveAsTemplate(event.target.checked)}
                />{" "}
                Lưu thành Blueprint mẫu
              </label>
              {saveAsTemplate && (
                <label className="mt-2 block text-[12px] font-semibold text-ink-muted">
                  Tên mẫu
                  <input
                    className="apple-input mt-1 w-full"
                    value={templateName}
                    onChange={(event) => setTemplateName(event.target.value)}
                    placeholder="Mẫu kiểm tra chương một"
                  />
                </label>
              )}
              <button
                type="button"
                className="apple-button-secondary mt-4 w-full"
                disabled={!draft}
                onClick={buildBlueprint}
              >
                Tạo Blueprint target hiện tại
              </button>
              <button
                type="button"
                className="apple-button-secondary mt-2 w-full"
                disabled={!draft}
                onClick={analyzeDifficulty}
              >
                Phân tích và đề xuất cân phân bố
              </button>
              <button
                type="button"
                className="apple-button-secondary mt-2 w-full"
                disabled={!draft}
                onClick={analyzeLearnerFit}
              >
                Phân tích phù hợp người học
              </button>
              <button
                type="button"
                className="apple-button-secondary mt-2 w-full"
                disabled={!draft?.blueprint_id}
                onClick={proposeRebalance}
              >
                Đề xuất cân bằng toàn bộ Blueprint
              </button>
              {blueprintTemplates.length > 0 && (
                <details className="mt-3 rounded-control border border-border px-3 py-2">
                  <summary className="cursor-pointer text-[12px] font-semibold">
                    Blueprint mẫu đã lưu
                  </summary>
                  <div className="mt-3 space-y-2">
                    {blueprintTemplates.map((template) => (
                      <div
                        key={template._id}
                        className="flex items-center justify-between gap-2 text-[11px]"
                      >
                        <span>
                          {String(template.name)} · {Number(template.total_questions)} câu
                        </span>
                        <button
                          type="button"
                          className="apple-button-secondary px-2 py-1"
                          onClick={() => void applyBlueprintTemplate(String(template._id))}
                        >
                          Nhân bản và áp dụng
                        </button>
                      </div>
                    ))}
                  </div>
                </details>
              )}
              {difficultyAnalysis && (
                <div className="mt-4 space-y-2 rounded-control bg-surface-quiet p-3 text-[12px]">
                  <p className="font-semibold">Blueprint target</p>
                  <p>
                    {[1, 2, 3, 4, 5]
                      .map((level) => {
                        return `L${level} ${difficultyAnalysis.blueprint_distribution?.[String(level)] || 0}`;
                      })
                      .join(" · ")}
                  </p>
                  <p className="font-semibold">Target từng câu</p>
                  <p>
                    {[1, 2, 3, 4, 5]
                      .map((level) => {
                        return `L${level} ${difficultyAnalysis.target_distribution?.[String(level)] || 0}`;
                      })
                      .join(" · ")}
                  </p>
                  <p className="font-semibold">Ước lượng giáo viên</p>
                  <p>
                    {[1, 2, 3, 4, 5]
                      .map((level) => {
                        return `L${level} ${difficultyAnalysis.teacher_distribution?.[String(level)] || 0}`;
                      })
                      .join(" · ")}
                  </p>
                  <p className="font-semibold">AI dự đoán hiện tại</p>
                  <p>
                    {[1, 2, 3, 4, 5]
                      .map((level) => {
                        return `L${level} ${difficultyAnalysis.predicted_distribution?.[String(level)] || 0}`;
                      })
                      .join(" · ")}
                  </p>
                  <p className="font-semibold">Hiệu chỉnh thực nghiệm</p>
                  <p>
                    {[1, 2, 3, 4, 5]
                      .map((level) => {
                        return `L${level} ${difficultyAnalysis.calibrated_distribution?.[String(level)] || 0}`;
                      })
                      .join(" · ")}
                  </p>
                  <p className="font-semibold">Khoảng thiếu thừa so với Blueprint</p>
                  <p>
                    {difficultyAnalysis.recommendations
                      ?.map(
                        (item) =>
                          `L${item.difficulty_level} ${item.delta > 0 ? "+" : ""}${item.delta}`,
                      )
                      .join(" · ") || "Đã khớp hoặc chưa có Blueprint"}
                  </p>
                  {difficultyAnalysis.unresolved_question_draft_ids?.length > 0 && (
                    <p className="text-warning">
                      Còn {difficultyAnalysis.unresolved_question_draft_ids.length} câu chưa có dự
                      đoán được phép hiển thị
                    </p>
                  )}
                  <p className="text-ink-muted">
                    Đề xuất không tự sửa câu và cần giáo viên chấp nhận
                  </p>
                </div>
              )}
              {learnerFit && (
                <div className="mt-4 space-y-2 rounded-control bg-surface-quiet p-3 text-[12px]">
                  <p className="font-semibold">Mức phù hợp người học</p>
                  <p>
                    Điểm phù hợp {Math.round(Number(learnerFit.expected_fit_overall || 0) * 100)}{" "}
                    phần trăm
                  </p>
                  <p>
                    Xác suất làm đúng dự kiến{" "}
                    {Math.round(Number(learnerFit.expected_probability_correct || 0) * 100)} phần
                    trăm
                  </p>
                  <p>
                    Khoảng thành công{" "}
                    {Math.round(Number(learnerFit.expected_success_range?.[0] || 0) * 100)} đến{" "}
                    {Math.round(Number(learnerFit.expected_success_range?.[1] || 0) * 100)} phần
                    trăm
                  </p>
                  <p>Độ tin cậy {Math.round(Number(learnerFit.confidence || 0) * 100)} phần trăm</p>
                  <p>
                    Dễ quá {learnerFit.categories?.too_easy || 0} · Phù hợp{" "}
                    {learnerFit.categories?.suitable || 0} · Thách thức{" "}
                    {learnerFit.categories?.challenging || 0} · Khó quá{" "}
                    {learnerFit.categories?.too_hard || 0}
                  </p>
                  {learnerFit.per_topic?.map((topic) => (
                    <p key={topic.topic}>
                      {topic.topic} · phù hợp {Math.round(Number(topic.fit_score || 0) * 100)} phần
                      trăm · {topic.item_count} câu
                    </p>
                  ))}
                  {learnerFit.item_level_mismatch?.length > 0 && (
                    <p>
                      Có {learnerFit.item_level_mismatch.length} câu lệch dải mục tiêu cần rà soát
                    </p>
                  )}
                  {learnerFit.low_evidence_warning && (
                    <p className="text-warning">
                      Có dữ liệu độ khó hoặc năng lực chưa đủ mạnh nên kết quả dùng fallback độ tin
                      cậy thấp
                    </p>
                  )}
                  <p className="text-ink-muted">
                    Phân tích không tự thay đổi câu hỏi và cần giáo viên quyết định
                  </p>
                </div>
              )}
              {rebalanceProposal && (
                <div className="mt-4 space-y-2 rounded-control border border-border bg-surface-quiet p-3 text-[12px]">
                  <p className="font-semibold">Đề xuất cân bằng Blueprint</p>
                  <p>Trước {rebalanceProposal.before?.length || 0} câu</p>
                  <p>Sau {rebalanceProposal.after?.length || 0} câu</p>
                  <p>
                    Mục tiêu{" "}
                    {Object.entries(rebalanceProposal.target_effect?.difficulty_distribution || {})
                      .map(([level, count]) => `L${level} ${count}`)
                      .join(" · ")}
                  </p>
                  <p>
                    Kiểm tra construct{" "}
                    {rebalanceProposal.construct_check?.passed ? "đạt" : "chưa đạt"}
                  </p>
                  {rebalanceProposal.why?.length > 0 && (
                    <div>
                      <p className="font-semibold">Lý do chọn</p>
                      {rebalanceProposal.why.map((item) => {
                        return (
                          <p key={item.item_id}>
                            {item.item_id}· {item.reasons?.join(" · ") || "đáp ứng mục tiêu"}
                          </p>
                        );
                      })}
                    </div>
                  )}
                  {rebalanceProposal.infeasibility?.length > 0 && (
                    <div className="text-warning">
                      <p className="font-semibold">Ràng buộc chưa thể đáp ứng</p>
                      {rebalanceProposal.infeasibility.map((gap, index) => {
                        return (
                          <p key={`${gap.code}-${index}`}>
                            {gap.code}· hiện có {gap.actual ?? "không xác định"}· cần{" "}
                            {gap.expected ?? gap.constraint?.minimum_count ?? "không xác định"}
                          </p>
                        );
                      })}
                    </div>
                  )}
                  {rebalanceProposal.status === "proposed" && (
                    <div className="grid grid-cols-2 gap-2 pt-1">
                      <button
                        type="button"
                        className="apple-button-secondary"
                        onClick={() => void decideRebalance("reject")}
                      >
                        Từ chối
                      </button>
                      <button
                        type="button"
                        className="apple-button"
                        onClick={() => void decideRebalance("approve")}
                      >
                        Chấp nhận
                      </button>
                    </div>
                  )}
                  {rebalanceProposal.status === "approved" && (
                    <button
                      type="button"
                      className="apple-button-secondary w-full"
                      onClick={() => void undoRebalance()}
                    >
                      Hoàn tác trước khi xuất bản
                    </button>
                  )}
                  <p className="text-ink-muted">
                    Không có thay đổi nào được áp dụng trước khi giáo viên chấp nhận
                  </p>
                </div>
              )}
            </section>

            <section className="rounded-panel border border-border bg-surface p-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-ink-faint">
                Chính sách làm bài
              </p>
              <div className="mt-3 space-y-3">
                <label className="block text-[12px] font-semibold text-ink-muted">
                  Thời gian phút
                  <input
                    className="apple-input mt-1 w-full"
                    type="number"
                    min="1"
                    max="1440"
                    value={durationMinutes}
                    onChange={(event) =>
                      setDurationMinutes(Math.max(1, Number(event.target.value) || 1))
                    }
                  />
                </label>
                <label className="block text-[12px] font-semibold text-ink-muted">
                  Số lần làm
                  <input
                    className="apple-input mt-1 w-full"
                    type="number"
                    min="1"
                    max="100"
                    value={attemptLimit}
                    onChange={(event) =>
                      setAttemptLimit(Math.max(1, Number(event.target.value) || 1))
                    }
                  />
                </label>
                <label className="block text-[12px] font-semibold text-ink-muted">
                  Điều hướng
                  <select
                    className="apple-input mt-1 w-full"
                    value={navigation}
                    onChange={(event) => setNavigation(event.target.value)}
                  >
                    <option value="free">Tự do</option>
                    <option value="linear">Tuần tự</option>
                  </select>
                </label>
              </div>
              <div className="mt-3 space-y-2 text-[12px]">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={shuffleQuestions}
                    onChange={(event) => setShuffleQuestions(event.target.checked)}
                  />{" "}
                  Trộn thứ tự câu ổn định
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={shuffleOptions}
                    onChange={(event) => setShuffleOptions(event.target.checked)}
                  />{" "}
                  Trộn phương án ổn định
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={highStakes}
                    onChange={(event) => setHighStakes(event.target.checked)}
                  />{" "}
                  Dùng cho quyết định quan trọng
                </label>
                <label className="block font-semibold text-ink-muted">
                  Lên lịch xuất bản
                  <input
                    className="apple-input mt-1 w-full"
                    type="datetime-local"
                    value={scheduledFor}
                    onChange={(event) => setScheduledFor(event.target.value)}
                  />
                </label>
              </div>
            </section>

            {publishedAssessmentId && (
              <section className="rounded-panel border border-border bg-surface p-5">
                <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-ink-faint">
                  Phân phối
                </p>
                <div className="mt-3 space-y-3">
                  <label className="block text-[12px] font-semibold text-ink-muted">
                    Mã học sinh
                    <textarea
                      className="apple-input mt-1 min-h-24 w-full"
                      value={studentIds}
                      onChange={(event) => setStudentIds(event.target.value)}
                      placeholder="Mỗi mã cách nhau bằng dấu phẩy hoặc xuống dòng"
                    />
                  </label>
                  <label className="block text-[12px] font-semibold text-ink-muted">
                    Mở bài
                    <input
                      className="apple-input mt-1 w-full"
                      type="datetime-local"
                      value={availableFrom}
                      onChange={(event) => setAvailableFrom(event.target.value)}
                    />
                  </label>
                  <label className="block text-[12px] font-semibold text-ink-muted">
                    Hạn nộp
                    <input
                      className="apple-input mt-1 w-full"
                      type="datetime-local"
                      value={dueAt}
                      onChange={(event) => setDueAt(event.target.value)}
                    />
                  </label>
                  <button
                    type="button"
                    className="apple-button w-full"
                    onClick={() => void assign()}
                  >
                    Giao bài
                  </button>
                </div>
              </section>
            )}

            <section className="rounded-panel border border-border bg-surface p-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-ink-faint">
                Bốn tín hiệu độ khó
              </p>
              <dl className="mt-3 space-y-3 text-[13px]">
                <div className="flex justify-between">
                  <dt>Target</dt>
                  <dd className="font-semibold">
                    {difficultyAnalysis
                      ? Object.values(difficultyAnalysis.target_distribution || {}).reduce(
                          (sum, value) => sum + Number(value),
                          0,
                        )
                      : 0}{" "}
                    câu
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt>Giáo viên</dt>
                  <dd className="font-semibold">
                    {difficultyAnalysis
                      ? Object.values(difficultyAnalysis.teacher_distribution || {}).reduce(
                          (sum, value) => sum + Number(value),
                          0,
                        )
                      : 0}{" "}
                    câu
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt>AI cold start</dt>
                  <dd className="font-semibold">
                    {difficultyAnalysis
                      ? Object.values(difficultyAnalysis.predicted_distribution || {}).reduce(
                          (sum, value) => sum + Number(value),
                          0,
                        )
                      : 0}{" "}
                    câu
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt>Thực nghiệm</dt>
                  <dd className="font-semibold">
                    {difficultyAnalysis
                      ? Object.values(difficultyAnalysis.calibrated_distribution || {}).reduce(
                          (sum, value) => sum + Number(value),
                          0,
                        )
                      : 0}{" "}
                    câu
                  </dd>
                </div>
              </dl>
            </section>

            <section className="rounded-panel border border-border bg-ink p-5 text-white">
              <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-white/60">
                Không gian AI
              </p>
              <h2 className="mt-3 text-[17px] font-semibold">Đề xuất có kiểm soát</h2>
              <p className="mt-2 text-[12px] leading-relaxed text-white/70">
                AI chỉ tạo proposal và không thay đổi phiên bản đã xuất bản khi chưa có giáo viên
                phê duyệt
              </p>
              <button
                type="button"
                className="mt-4 min-h-10 w-full rounded-control bg-white px-3 text-[13px] font-semibold text-ink"
                onClick={() => router.push(`/giao-vien/de/sinh-ai?id=${draft._id}`)}
              >
                Mở bảng đề xuất
              </button>
            </section>
          </aside>
        )}
      </div>
    </div>
  );
}
