"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { CheckCircle2, Copy, Lock, Sparkles, Trash2 } from "lucide-react";
import { Button } from "@/shared/components/ui/Button";
import TiptapDocumentEditor from "../editor/TiptapDocumentEditor";
import {
  deleteQuestionDraft,
  duplicateQuestionDraft,
  freezeQuestionDraft,
  listQuestionVersions,
  predictDifficulty,
  proposeQuestionDraftRevision,
  recordDifficultyTarget,
  recordTeacherEstimate,
  recordValidityReview,
  restoreQuestionDraftVersion,
  updateQuestionDraft,
  validateQuestionDraft,
} from "../services/assessment.service";
import { textDoc } from "../types";
import { questionTypes } from "../lib/assessment.logic.mjs";
const labels = {
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
function messageOf(reason) {
  return reason instanceof Error ? reason.message : "Không thể hoàn tất thao tác";
}
function optionText(doc) {
  const first = doc.content?.[0];
  return first?.content?.map((node) => node.text || "").join("") || "";
}
function answerForType(type, options) {
  if (type === "single_choice") return { option_id: options[0]?.id || "A" };
  if (type === "multiple_choice")
    return {
      option_ids: options[0]?.id ? [options[0].id] : [],
    };
  if (type === "true_false") return { value: true };
  if (type === "matching")
    return { pairs: Object.fromEntries(options.map((option) => [option.id, ""])) };
  if (type === "ordering") return { order: options.map((option) => option.id) };
  if (type === "numeric") return { value: "", tolerance: "0", unit: "" };
  if (type === "essay") return {};
  return { accepted: [] };
}
export default function QuestionDraftCard({
  question,
  index,
  researchBlindMode,
  blueprintId,
  highStakes,
  onUpdated,
  onReload,
}) {
  const [draft, setDraft] = useState({
    ...question,
    tags: question.tags || [],
  });
  const [editVersion, setEditVersion] = useState(0);
  const [saveState, setSaveState] = useState("Đã lưu");
  const [error, setError] = useState("");
  const [teacherEstimate, setTeacherEstimate] = useState("3");
  const [targetDifficulty, setTargetDifficulty] = useState("3");
  const [teacherConfidence, setTeacherConfidence] = useState("medium");
  const [prediction, setPrediction] = useState(null);
  const [validation, setValidation] = useState(null);
  const [versions, setVersions] = useState([]);
  const revisionRef = useRef(question.revision);
  const draftRef = useRef(draft);
  const onUpdatedRef = useRef(onUpdated);
  draftRef.current = draft;
  onUpdatedRef.current = onUpdated;
  useEffect(() => {
    setDraft({
      ...question,
      tags: question.tags || [],
    });
    revisionRef.current = question.revision;
  }, [question]);
  const edit = (updater) => {
    setDraft(updater);
    setEditVersion((current) => current + 1);
  };
  useEffect(() => {
    if (!editVersion) return;
    setSaveState("Đang lưu");
    const timer = window.setTimeout(async () => {
      try {
        const currentDraft = draftRef.current;
        const updated = await updateQuestionDraft(currentDraft._id, {
          expected_revision: revisionRef.current,
          question_type: currentDraft.question_type,
          stem_doc: currentDraft.stem_doc,
          options: currentDraft.options,
          answer_key: currentDraft.answer_key,
          solution_doc: currentDraft.solution_doc,
          scoring_rule: currentDraft.scoring_rule,
          curriculum_links: currentDraft.curriculum_links,
          concept_ids: currentDraft.concept_ids,
          skill_ids: currentDraft.skill_ids,
          tags: currentDraft.tags,
          cognitive_level: currentDraft.cognitive_level,
          construct: currentDraft.construct,
          source_evidence: currentDraft.source_evidence,
          locked: currentDraft.locked,
        });
        revisionRef.current = updated.revision;
        setDraft(updated);
        onUpdatedRef.current(updated);
        setSaveState("Đã lưu");
        setError("");
      } catch (reason) {
        const conflict = reason;
        setSaveState(conflict.status === 409 ? "Có phiên bản mới hơn" : "Chưa lưu");
        setError(messageOf(reason));
      }
    }, 900);
    return () => window.clearTimeout(timer);
  }, [editVersion]);
  const setOptionText = (optionIndex, text) =>
    edit((current) => ({
      ...current,

      options: current.options.map((option, currentIndex) =>
        currentIndex === optionIndex
          ? {
              ...option,
              content_doc: textDoc(text),
            }
          : option,
      ),
    }));
  const setQuestionType = (value) => {
    const questionType = value;
    edit((current) => ({
      ...current,
      question_type: questionType,
      answer_key: answerForType(questionType, current.options),
    }));
  };
  const execute = async (operation, success) => {
    setError("");
    try {
      await operation();
      if (success) setSaveState(success);
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const saveEstimate = () =>
    execute(
      () => recordTeacherEstimate(draft._id, Number(teacherEstimate), teacherConfidence),
      "Đã ghi nhận ước lượng giáo viên",
    );
  const saveTarget = () =>
    execute(
      () => recordDifficultyTarget(draft._id, Number(targetDifficulty), blueprintId),
      "Đã ghi nhận target",
    );
  const runPrediction = (predictionKind) =>
    execute(async () => setPrediction(await predictDifficulty(draft._id, predictionKind)));
  const runValidation = () =>
    execute(async () => setValidation(await validateQuestionDraft(draft._id)));
  const proposeAiRevision = (action) =>
    execute(async () => {
      let instruction = "";
      if (action === "clarify_wording") {
        const value = window.prompt(
          "Nội dung câu hỏi đã làm rõ nhưng giữ nguyên construct",
          optionText(draft.stem_doc),
        );
        if (!value?.trim()) return;
        instruction = value.trim();
      }
      if (action === "regenerate_distractors") {
        const value = window.prompt(
          "JSON phương án nhiễu cần thay thế",
          '{"B":"Phương án nhiễu mới"}',
        );
        if (!value?.trim()) return;
        instruction = value.trim();
      }
      if (action === "change_question_type") {
        const value = window.prompt(
          "Loại câu mới",
          draft.question_type === "single_choice" ? "numeric" : "single_choice",
        );
        if (!value?.trim()) return;
        instruction = value.trim();
      }
      if (
        action === "regenerate_item" &&
        !window.confirm("Tạo proposal sinh lại toàn bộ nội dung câu hỏi")
      )
        return;
      await proposeQuestionDraftRevision(draft._id, action, instruction);
    }, "Đã tạo proposal chờ giáo viên duyệt");
  const reviewValidity = (reviewStatus) =>
    execute(
      async () => {
        const riskText = window.prompt(
          "Risk flags language_bias cultural_context accessibility construct_irrelevant_context differential_opportunity",
          (draft.validity_review?.risk_flags || []).join(","),
        );
        if (riskText === null) return;
        const note = window.prompt(
          "Nhận xét kiểm định công bằng và validity",
          draft.validity_review?.reviewer_note || "",
        );
        if (!note?.trim()) throw new Error("Cần nhận xét kiểm định");
        const updated = await recordValidityReview(
          draft._id,
          reviewStatus,
          riskText
            .split(/[,;\n]+/)
            .map((value) => value.trim())
            .filter(Boolean),
          note.trim(),
        );
        revisionRef.current = updated.revision;
        setDraft(updated);
        onUpdated(updated);
      },
      reviewStatus === "approved" ? "Đã duyệt validity" : "Đã từ chối validity",
    );
  const freeze = () =>
    execute(async () => {
      const frozen = await freezeQuestionDraft(draft._id);
      setDraft((current) => ({
        ...current,
        frozen_version_id: String(frozen._id),
        frozen_revision: Number(frozen.source_draft_revision),
        status: "approved",
      }));
    }, "Đã đóng băng phiên bản");
  const duplicate = () =>
    execute(async () => {
      await duplicateQuestionDraft(draft._id);
      await onReload();
    });
  const remove = () => {
    if (!window.confirm("Xóa câu hỏi khỏi bản nháp")) return;
    void execute(async () => {
      await deleteQuestionDraft(draft._id);
      await onReload();
    });
  };
  const loadVersions = () =>
    execute(async () => {
      if (!draft.question_id) return;
      setVersions(await listQuestionVersions(draft.question_id));
    });
  const restoreVersion = (versionId) => {
    if (!window.confirm(`Khôi phục ${versionId} thành revision bản nháp mới`)) return;
    void execute(async () => {
      const restored = await restoreQuestionDraftVersion(draft._id, versionId);
      revisionRef.current = restored.revision;
      setDraft({
        ...restored,
        tags: restored.tags || [],
      });
      onUpdated(restored);
      setVersions([]);
    }, "Đã khôi phục nội dung thành revision mới");
  };
  const toggleMultiple = (id) =>
    edit((current) => {
      const selected = current.answer_key.option_ids || [];
      return {
        ...current,

        answer_key: {
          option_ids: selected.includes(id)
            ? selected.filter((value) => value !== id)
            : [...selected, id],
        },
      };
    });
  const updateCurriculumLink = (field, value) =>
    edit((current) => ({
      ...current,

      curriculum_links: [
        {
          ...(current.curriculum_links[0] || {}),
          [field]: value,
        },
        ...current.curriculum_links.slice(1),
      ],
    }));
  const predictionReasons = Array.isArray(prediction?.reason_summary)
    ? prediction.reason_summary
    : [];
  const historicalItems = Array.isArray(prediction?.similar_historical_items)
    ? prediction.similar_historical_items
    : [];
  const validationChecks = Array.isArray(validation?.checks) ? validation.checks : [];
  const validationEvidence = Array.isArray(validation?.evidence) ? validation.evidence : [];
  return (
    <article className="rounded-panel border border-border bg-surface shadow-[0_10px_35px_rgba(33,48,42,0.05)]">
      <header className="flex flex-wrap items-center gap-3 border-b border-border px-5 py-4">
        <span className="flex h-8 min-w-8 items-center justify-center rounded-full bg-brand text-[13px] font-bold text-white">
          {index + 1}
        </span>
        <div>
          <h3 className="text-[15px] font-semibold">{labels[draft.question_type]}</h3>
          <p className="text-[12px] text-ink-muted">
            Nguồn {draft.authoring_source} · Phiên bản nháp {draft.revision}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2 text-[12px] text-ink-muted">
          {draft.frozen_version_id && <Lock size={15} aria-label="Đã đóng băng" />}
          <span>{saveState}</span>
          <button
            type="button"
            className="apple-icon-button"
            onClick={duplicate}
            aria-label="Nhân bản câu hỏi"
          >
            <Copy size={16} />
          </button>
          <button
            type="button"
            className="apple-icon-button"
            onClick={remove}
            aria-label="Xóa câu hỏi"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </header>

      <div className="space-y-5 p-5">
        <label className="block text-[12px] font-semibold text-ink-muted">
          Loại câu hỏi
          <select
            className="apple-input mt-1 w-full"
            value={draft.question_type}
            onChange={(event) => setQuestionType(event.target.value)}
          >
            {questionTypes.map((type) => (
              <option key={type} value={type}>
                {labels[type]}
              </option>
            ))}
          </select>
        </label>
        <div>
          <label className="mb-2 block text-[13px] font-semibold">Nội dung câu hỏi</label>
          <TiptapDocumentEditor
            value={draft.stem_doc}
            onChange={(stem_doc) =>
              edit((current) => ({
                ...current,
                stem_doc,
              }))
            }
            label={`Nội dung câu ${index + 1}`}
          />
        </div>

        {["single_choice", "multiple_choice", "matching", "ordering"].includes(
          draft.question_type,
        ) && (
          <fieldset>
            <legend className="mb-2 text-[13px] font-semibold">Phương án và đáp án</legend>
            <div className="grid gap-2 md:grid-cols-2">
              {draft.options.map((option, optionIndex) => {
                const selected =
                  draft.question_type === "single_choice"
                    ? draft.answer_key.option_id === option.id
                    : (draft.answer_key.option_ids || []).includes(option.id);
                return (
                  <label
                    key={option.id}
                    className="flex items-center gap-3 rounded-control border border-border bg-surface-raised px-3 py-2"
                  >
                    {["single_choice", "multiple_choice"].includes(draft.question_type) && (
                      <input
                        type={draft.question_type === "single_choice" ? "radio" : "checkbox"}
                        name={`answer-${draft._id}`}
                        checked={selected}
                        onChange={() =>
                          draft.question_type === "single_choice"
                            ? edit((current) => ({
                                ...current,
                                answer_key: { option_id: option.id },
                              }))
                            : toggleMultiple(option.id)
                        }
                      />
                    )}
                    <span className="text-[13px] font-semibold">{option.id}</span>
                    <input
                      className="min-h-10 flex-1 bg-transparent text-[14px] outline-none"
                      value={optionText(option.content_doc)}
                      onChange={(event) => setOptionText(optionIndex, event.target.value)}
                      aria-label={`Phương án ${option.id}`}
                    />
                    {draft.question_type === "matching" && (
                      <input
                        className="apple-input w-24"
                        aria-label={`Ghép với ${option.id}`}
                        value={String(draft.answer_key.pairs?.[option.id] || "")}
                        onChange={(event) =>
                          edit((current) => ({
                            ...current,

                            answer_key: {
                              pairs: {
                                ...(current.answer_key.pairs || {}),
                                [option.id]: event.target.value,
                              },
                            },
                          }))
                        }
                      />
                    )}
                  </label>
                );
              })}
            </div>
            {draft.question_type === "ordering" && (
              <label className="mt-3 block text-[12px] font-semibold text-ink-muted">
                Thứ tự đúng theo mã phương án
                <input
                  className="apple-input mt-1 w-full"
                  value={(draft.answer_key.order || []).join(",")}
                  onChange={(event) =>
                    edit((current) => ({
                      ...current,

                      answer_key: {
                        order: event.target.value
                          .split(",")
                          .map((value) => value.trim())
                          .filter(Boolean),
                      },
                    }))
                  }
                />
              </label>
            )}
          </fieldset>
        )}

        {draft.question_type === "true_false" && (
          <fieldset>
            <legend className="mb-2 text-[13px] font-semibold">Đáp án đúng</legend>
            <div className="flex gap-4">
              <label>
                <input
                  type="radio"
                  checked={draft.answer_key.value === true}
                  onChange={() =>
                    edit((current) => ({
                      ...current,
                      answer_key: { value: true },
                    }))
                  }
                />{" "}
                Đúng
              </label>
              <label>
                <input
                  type="radio"
                  checked={draft.answer_key.value === false}
                  onChange={() =>
                    edit((current) => ({
                      ...current,
                      answer_key: { value: false },
                    }))
                  }
                />{" "}
                Sai
              </label>
            </div>
          </fieldset>
        )}
        {draft.question_type === "numeric" && (
          <div className="grid gap-3 sm:grid-cols-3">
            <label className="text-[12px] font-semibold text-ink-muted">
              Giá trị đúng
              <input
                className="apple-input mt-1 w-full"
                value={String(draft.answer_key.value || "")}
                onChange={(event) =>
                  edit((current) => ({
                    ...current,

                    answer_key: {
                      ...current.answer_key,
                      value: event.target.value,
                    },
                  }))
                }
              />
            </label>
            <label className="text-[12px] font-semibold text-ink-muted">
              Sai số
              <input
                className="apple-input mt-1 w-full"
                value={String(draft.answer_key.tolerance || "0")}
                onChange={(event) =>
                  edit((current) => ({
                    ...current,

                    answer_key: {
                      ...current.answer_key,
                      tolerance: event.target.value,
                    },
                  }))
                }
              />
            </label>
            <label className="text-[12px] font-semibold text-ink-muted">
              Đơn vị
              <input
                className="apple-input mt-1 w-full"
                value={String(draft.answer_key.unit || "")}
                onChange={(event) =>
                  edit((current) => ({
                    ...current,

                    answer_key: {
                      ...current.answer_key,
                      unit: event.target.value,
                    },
                  }))
                }
              />
            </label>
          </div>
        )}
        {["symbolic_math", "short_answer"].includes(draft.question_type) && (
          <label className="block text-[12px] font-semibold text-ink-muted">
            Đáp án chấp nhận
            <input
              className="apple-input mt-1 w-full"
              value={(draft.answer_key.accepted || []).join(" | ")}
              onChange={(event) =>
                edit((current) => ({
                  ...current,

                  answer_key: {
                    accepted: event.target.value
                      .split("|")
                      .map((value) => value.trim())
                      .filter(Boolean),
                  },
                }))
              }
            />
          </label>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="mb-2 block text-[13px] font-semibold">Lời giải</label>
            <TiptapDocumentEditor
              value={draft.solution_doc}
              onChange={(solution_doc) =>
                edit((current) => ({
                  ...current,
                  solution_doc,
                }))
              }
              label={`Lời giải câu ${index + 1}`}
              minHeight="min-h-28"
            />
          </div>
          <div className="space-y-3">
            <label className="block text-[12px] font-semibold text-ink-muted">
              Điểm
              <input
                className="apple-input mt-1 w-full"
                type="number"
                min="0.1"
                step="0.1"
                value={Number(draft.scoring_rule.points || 1)}
                onChange={(event) =>
                  edit((current) => ({
                    ...current,

                    scoring_rule: {
                      ...current.scoring_rule,
                      points: Number(event.target.value),
                    },
                  }))
                }
              />
            </label>
            <label className="block text-[12px] font-semibold text-ink-muted">
              Mức nhận thức
              <select
                className="apple-input mt-1 w-full"
                value={draft.cognitive_level || "recognition"}
                onChange={(event) =>
                  edit((current) => ({
                    ...current,
                    cognitive_level: event.target.value,
                  }))
                }
              >
                <option value="recognition">Nhận biết</option>
                <option value="comprehension">Thông hiểu</option>
                <option value="application">Vận dụng</option>
                <option value="analysis">Phân tích</option>
              </select>
            </label>
            <label className="flex items-center gap-2 text-[12px] font-semibold text-ink-muted">
              <input
                type="checkbox"
                checked={draft.locked}
                onChange={(event) =>
                  edit((current) => ({
                    ...current,
                    locked: event.target.checked,
                  }))
                }
              />{" "}
              Khóa khỏi thay đổi AI
            </label>
          </div>
        </div>

        <div className="grid gap-3 border-t border-border pt-5 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1fr_auto]">
          <label className="text-[12px] font-semibold text-ink-muted">
            Target
            <select
              className="apple-input mt-1 w-full"
              value={targetDifficulty}
              onChange={(event) => setTargetDifficulty(event.target.value)}
            >
              {[1, 2, 3, 4, 5].map((level) => (
                <option key={level} value={level}>
                  Mức {level}
                </option>
              ))}
            </select>
          </label>
          <label className="text-[12px] font-semibold text-ink-muted">
            Ước lượng giáo viên
            <select
              className="apple-input mt-1 w-full"
              value={teacherEstimate}
              onChange={(event) => setTeacherEstimate(event.target.value)}
            >
              {[1, 2, 3, 4, 5].map((level) => (
                <option key={level} value={level}>
                  Mức {level}
                </option>
              ))}
            </select>
          </label>
          <label className="text-[12px] font-semibold text-ink-muted">
            Độ tự tin
            <select
              className="apple-input mt-1 w-full"
              value={teacherConfidence}
              onChange={(event) => setTeacherConfidence(event.target.value)}
            >
              <option value="low">Thấp</option>
              <option value="medium">Trung bình</option>
              <option value="high">Cao</option>
            </select>
          </label>
          <div className="flex gap-2 self-end">
            <Button variant="secondary" onClick={saveTarget}>
              Lưu target
            </Button>
            <Button variant="secondary" onClick={saveEstimate}>
              Lưu ước lượng
            </Button>
          </div>
        </div>
        <details className="rounded-control border border-border px-3 py-2 text-[12px]">
          <summary className="cursor-pointer font-semibold">Nguồn và provenance</summary>
          <pre className="mt-2 overflow-auto whitespace-pre-wrap text-[11px] text-ink-muted">
            {JSON.stringify(
              { curriculum_links: draft.curriculum_links, source_evidence: draft.source_evidence },
              null,
              2,
            )}
          </pre>
        </details>
        {highStakes && (
          <section className="rounded-control border border-warning bg-warning-soft p-4">
            <p className="text-[13px] font-semibold">Kiểm định công bằng và validity bắt buộc</p>
            <p className="mt-1 text-[12px] text-ink-muted">
              Trạng thái {draft.validity_review?.status || "pending"}
            </p>
            <div className="mt-3 flex gap-2">
              <Button variant="secondary" onClick={() => reviewValidity("approved")}>
                Duyệt validity
              </Button>
              <Button variant="secondary" onClick={() => reviewValidity("rejected")}>
                Từ chối
              </Button>
            </div>
          </section>
        )}
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={runValidation}>
            <CheckCircle2 size={16} /> Kiểm định
          </Button>
          <Button variant="secondary" onClick={() => runPrediction("structured")}>
            <Sparkles size={16} /> Dự đoán có cấu trúc
          </Button>
          <Button variant="secondary" onClick={() => runPrediction("llm_direct")}>
            <Sparkles size={16} /> LLM đánh giá trực tiếp
          </Button>
          <Button
            variant="secondary"
            disabled={draft.locked || saveState !== "Đã lưu"}
            onClick={() => proposeAiRevision("regenerate_item")}
          >
            Sinh lại toàn câu
          </Button>
          <Button
            variant="secondary"
            disabled={draft.locked || saveState !== "Đã lưu"}
            onClick={() => proposeAiRevision("regenerate_distractors")}
          >
            Sinh lại phương án nhiễu
          </Button>
          <Button
            variant="secondary"
            disabled={draft.locked || saveState !== "Đã lưu"}
            onClick={() => proposeAiRevision("change_question_type")}
          >
            Đổi loại câu
          </Button>
          <Button
            variant="secondary"
            disabled={draft.locked || saveState !== "Đã lưu"}
            onClick={() => proposeAiRevision("clarify_wording")}
          >
            Làm rõ wording
          </Button>
          <Button
            variant="secondary"
            disabled={draft.locked || saveState !== "Đã lưu"}
            onClick={() => proposeAiRevision("increase_difficulty")}
          >
            Tăng difficulty
          </Button>
          <Button
            variant="secondary"
            disabled={draft.locked || saveState !== "Đã lưu"}
            onClick={() => proposeAiRevision("decrease_difficulty")}
          >
            Giảm difficulty
          </Button>
          <Link
            className="apple-button-secondary"
            href={`/tro-chuyen?mode=work&prompt=${encodeURIComponent(`Kiểm tra tính đúng giải thích lỗi gợi ý distractor và tạo draft revision cho QuestionDraft ${draft._id} bằng domain tools với construct check`)}`}
          >
            <Sparkles size={16} /> AI kiểm tra và gợi ý distractor
          </Link>
          <Link className="apple-button-secondary" href="/giao-vien/cau-hoi/ra-soat">
            Mở proposal chờ duyệt
          </Link>
          <Button
            onClick={freeze}
            disabled={Boolean(draft.frozen_version_id) && draft.frozen_revision === draft.revision}
          >
            Đóng băng phiên bản
          </Button>
        </div>
        {researchBlindMode && !prediction && (
          <p className="rounded-control bg-warning-soft px-3 py-2 text-[12px] text-warning">
            Chế độ nghiên cứu chỉ hiển thị dự đoán AI sau khi đã ghi nhận ước lượng giáo viên
          </p>
        )}
        <section className="grid gap-3 rounded-control border border-border p-4 md:grid-cols-2">
          <h4 className="font-semibold md:col-span-2">Ánh xạ chương trình và construct</h4>
          <label className="text-[12px] font-semibold text-ink-muted">
            Cấp học
            <input
              className="apple-input mt-1 w-full"
              value={String(draft.curriculum_links[0]?.education_level || "")}
              onChange={(event) => updateCurriculumLink("education_level", event.target.value)}
            />
          </label>
          <label className="text-[12px] font-semibold text-ink-muted">
            Môn học
            <input
              className="apple-input mt-1 w-full"
              value={String(draft.curriculum_links[0]?.subject || "")}
              onChange={(event) => updateCurriculumLink("subject", event.target.value)}
            />
          </label>
          <label className="text-[12px] font-semibold text-ink-muted">
            Chương trình
            <input
              className="apple-input mt-1 w-full"
              value={String(draft.curriculum_links[0]?.target_program || "")}
              onChange={(event) => updateCurriculumLink("target_program", event.target.value)}
            />
          </label>
          <label className="text-[12px] font-semibold text-ink-muted">
            Concept IDs
            <input
              className="apple-input mt-1 w-full"
              value={draft.concept_ids.join(", ")}
              onChange={(event) =>
                edit((current) => ({
                  ...current,

                  concept_ids: event.target.value
                    .split(/[,;]+/)
                    .map((value) => value.trim())
                    .filter(Boolean),
                }))
              }
            />
          </label>
          <label className="text-[12px] font-semibold text-ink-muted">
            Skill IDs
            <input
              className="apple-input mt-1 w-full"
              value={draft.skill_ids.join(", ")}
              onChange={(event) =>
                edit((current) => ({
                  ...current,

                  skill_ids: event.target.value
                    .split(/[,;]+/)
                    .map((value) => value.trim())
                    .filter(Boolean),
                }))
              }
            />
          </label>
          <label className="text-[12px] font-semibold text-ink-muted">
            Tags
            <input
              className="apple-input mt-1 w-full"
              value={(draft.tags || []).join(", ")}
              onChange={(event) =>
                edit((current) => ({
                  ...current,

                  tags: event.target.value
                    .split(/[,;]+/)
                    .map((value) => value.trim())
                    .filter(Boolean),
                }))
              }
            />
          </label>
          <label className="text-[12px] font-semibold text-ink-muted">
            Primary concept
            <input
              className="apple-input mt-1 w-full"
              value={String(draft.construct.primary_concept || "")}
              onChange={(event) =>
                edit((current) => ({
                  ...current,

                  construct: {
                    ...current.construct,
                    primary_concept: event.target.value,
                  },
                }))
              }
            />
          </label>
          <label className="text-[12px] font-semibold text-ink-muted">
            Primary skill
            <input
              className="apple-input mt-1 w-full"
              value={String(draft.construct.primary_skill || "")}
              onChange={(event) =>
                edit((current) => ({
                  ...current,

                  construct: {
                    ...current.construct,
                    primary_skill: event.target.value,
                  },
                }))
              }
            />
          </label>
          <label className="text-[12px] font-semibold text-ink-muted md:col-span-2">
            Learning objective
            <input
              className="apple-input mt-1 w-full"
              value={String(draft.construct.learning_objective || "")}
              onChange={(event) =>
                edit((current) => ({
                  ...current,

                  construct: {
                    ...current.construct,
                    learning_objective: event.target.value,
                  },
                }))
              }
            />
          </label>
        </section>
        {draft.question_id && (
          <details
            className="rounded-control border border-border px-3 py-2 text-[12px]"
            onToggle={(event) => {
              if (event.currentTarget.open && !versions.length) void loadVersions();
            }}
          >
            <summary className="cursor-pointer font-semibold">
              Lịch sử phiên bản và khôi phục bản nháp
            </summary>
            <div className="mt-3 space-y-2">
              {versions.map((version) => (
                <div
                  key={String(version._id)}
                  className="flex items-center justify-between gap-3 rounded-control bg-surface-quiet px-3 py-2"
                >
                  <span>
                    {String(version._id)} · version {String(version.version)}
                  </span>
                  <button
                    type="button"
                    className="apple-button-secondary"
                    onClick={() => restoreVersion(String(version._id))}
                  >
                    Khôi phục thành revision mới
                  </button>
                </div>
              ))}
              {!versions.length && (
                <p className="text-ink-muted">Đang tải hoặc chưa có phiên bản</p>
              )}
            </div>
          </details>
        )}
        {prediction && (
          <section className="space-y-4 rounded-control bg-brand-soft p-4">
            <div className="grid gap-3 sm:grid-cols-4">
              <div>
                <p className="text-[11px] uppercase tracking-wide text-ink-muted">Phương pháp</p>
                <p className="mt-1 text-[15px] font-semibold">
                  {prediction.predictor_kind === "llm_direct" ? "LLM trực tiếp" : "Có cấu trúc"}
                </p>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-wide text-ink-muted">AI dự đoán</p>
                <p className="mt-1 text-[22px] font-semibold">
                  {String(prediction.predicted_difficulty)} · Mức{" "}
                  {String(prediction.ui_difficulty_level)}
                </p>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-wide text-ink-muted">Độ tin cậy</p>
                <p className="mt-1 text-[22px] font-semibold">
                  {Math.round(Number(prediction.confidence) * 100)}%
                </p>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-wide text-ink-muted">
                  Hiệu chỉnh thực nghiệm
                </p>
                <p className="mt-1 text-[15px] font-semibold">
                  {prediction.calibrated_difficulty == null
                    ? "Chưa đủ dữ liệu"
                    : `${String(prediction.calibrated_difficulty)} từ ${String(prediction.calibration_sample_size)} response`}
                </p>
                {prediction.predicted_empirical_gap != null && (
                  <p className="mt-1 text-[11px] text-ink-muted">
                    Gap {String(prediction.predicted_empirical_gap)}{" "}
                    {prediction.calibration_drift_flag ? "có drift" : "không drift"}
                  </p>
                )}
              </div>
            </div>
            {predictionReasons.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">
                  Tóm tắt lý do và feature
                </p>
                <ul className="mt-2 grid gap-1 text-[12px] sm:grid-cols-2">
                  {predictionReasons.map((reason, reasonIndex) => (
                    <li key={`${String(reason)}-${reasonIndex}`}>{String(reason)}</li>
                  ))}
                </ul>
              </div>
            )}
            {historicalItems.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">
                  Câu lịch sử tương tự
                </p>
                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                  {historicalItems.map((item) => (
                    <div
                      key={String(item.question_version_id)}
                      className="rounded-control bg-surface/70 px-3 py-2 text-[11px]"
                    >
                      <p className="font-semibold">{String(item.question_version_id)}</p>
                      <p>
                        Độ khó {String(item.difficulty)} · mẫu {String(item.sample_size)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <details className="rounded-control border border-brand/30 px-3 py-2 text-[11px]">
              <summary className="cursor-pointer font-semibold">
                Feature snapshot và population context
              </summary>
              <pre className="mt-2 overflow-auto whitespace-pre-wrap text-ink-muted">
                {JSON.stringify(
                  {
                    feature_snapshot: prediction.feature_snapshot,
                    calibration_population_context: prediction.calibration_population_context,
                  },
                  null,
                  2,
                )}
              </pre>
            </details>
          </section>
        )}
        {validation && (
          <section className="space-y-3 rounded-control border border-border p-4 text-[12px]">
            <div className="flex items-center justify-between gap-3">
              <p className="font-semibold">Kết quả kiểm định</p>
              <span className="font-semibold">{String(validation.status)}</span>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {validationChecks.map((check, checkIndex) => {
                return (
                  <div
                    key={`${String(check.code)}-${checkIndex}`}
                    className="rounded-control bg-surface-quiet px-3 py-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold">{String(check.code)}</span>
                      <span>{String(check.status || check.severity)}</span>
                    </div>
                    <p className="mt-1 text-[11px] text-ink-muted">
                      Độ tin cậy {Math.round(Number(check.confidence ?? 0) * 100)} phần trăm
                    </p>
                  </div>
                );
              })}
            </div>
            <details className="rounded-control border border-border px-3 py-2">
              <summary className="cursor-pointer font-semibold">
                Bằng chứng và nguồn tham chiếu
              </summary>
              <pre className="mt-2 overflow-auto whitespace-pre-wrap text-[11px] text-ink-muted">
                {JSON.stringify(validationEvidence, null, 2)}
              </pre>
            </details>
          </section>
        )}
        {error && (
          <p
            role="alert"
            className="rounded-control bg-danger-soft px-3 py-2 text-[12px] text-danger"
          >
            {error}
          </p>
        )}
      </div>
    </article>
  );
}
