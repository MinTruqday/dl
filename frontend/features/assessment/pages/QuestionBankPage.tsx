"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  addQuestionBankItemsToDraft,
  archiveQuestionBankItem,
  duplicateQuestionBankItem,
  getQuestionUsage,
  listQuestionBank,
  listQuestionVersions,
} from "../services/assessment.service";


function messageOf(reason: unknown) {
  return reason instanceof Error ? reason.message : "Không thể hoàn tất thao tác";
}


export default function QuestionBankPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const assessmentDraftId = searchParams.get("draft") || "";
  const [questions, setQuestions] = useState<Record<string, any>[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [questionType, setQuestionType] = useState("");
  const [qualityStatus, setQualityStatus] = useState("");
  const [subject, setSubject] = useState("");
  const [targetProgram, setTargetProgram] = useState("");
  const [chapter, setChapter] = useState("");
  const [lesson, setLesson] = useState("");
  const [conceptId, setConceptId] = useState("");
  const [skillId, setSkillId] = useState("");
  const [cognitiveLevel, setCognitiveLevel] = useState("");
  const [authoringSource, setAuthoringSource] = useState("");
  const [minimumConfidence, setMinimumConfidence] = useState("");
  const [minimumPredicted, setMinimumPredicted] = useState("");
  const [maximumPredicted, setMaximumPredicted] = useState("");
  const [minimumCalibrated, setMinimumCalibrated] = useState("");
  const [maximumCalibrated, setMaximumCalibrated] = useState("");
  const [publicationStatus, setPublicationStatus] = useState("");
  const [sortBy, setSortBy] = useState("updated");
  const [sortDirection, setSortDirection] = useState("desc");
  const [details, setDetails] = useState<Record<string, any>>({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setQuestions(await listQuestionBank({
        search,
        question_type: questionType,
        quality_status: qualityStatus,
        subject,
        target_program: targetProgram,
        chapter,
        lesson,
        concept_id: conceptId,
        skill_id: skillId,
        cognitive_level: cognitiveLevel,
        authoring_source: authoringSource,
        minimum_prediction_confidence: minimumConfidence,
        minimum_predicted_difficulty: minimumPredicted,
        maximum_predicted_difficulty: maximumPredicted,
        minimum_calibrated_difficulty: minimumCalibrated,
        maximum_calibrated_difficulty: maximumCalibrated,
        publication_status: publicationStatus,
        sort_by: sortBy,
        sort_direction: sortDirection,
      }));
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setLoading(false);
    }
  }, [authoringSource, chapter, cognitiveLevel, conceptId, lesson, maximumCalibrated, maximumPredicted, minimumCalibrated, minimumConfidence, minimumPredicted, publicationStatus, qualityStatus, questionType, search, skillId, sortBy, sortDirection, subject, targetProgram]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 250);
    return () => window.clearTimeout(timer);
  }, [load]);

  const toggle = (questionId: string) => {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(questionId)) next.delete(questionId);
      else next.add(questionId);
      return next;
    });
  };

  const addSelected = async () => {
    if (!assessmentDraftId || !selected.size) return;
    try {
      await addQuestionBankItemsToDraft(assessmentDraftId, [...selected]);
      router.push(`/giao-vien/de/soan-thao?id=${assessmentDraftId}`);
    } catch (reason) {
      setError(messageOf(reason));
    }
  };

  const duplicate = async (questionId: string) => {
    try {
      await duplicateQuestionBankItem(questionId);
      setMessage("Đã nhân bản câu hỏi thành một item độc lập");
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };

  const archive = async (questionId: string) => {
    if (!window.confirm("Lưu trữ câu hỏi này")) return;
    try {
      await archiveQuestionBankItem(questionId, "Lưu trữ từ ngân hàng câu hỏi");
      setSelected((current) => {
        const next = new Set(current);
        next.delete(questionId);
        return next;
      });
      setMessage("Đã lưu trữ câu hỏi mà không thay đổi các phiên bản đề đã xuất bản");
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };

  const inspect = async (questionId: string) => {
    if (details[questionId]) {
      setDetails((current) => ({ ...current, [questionId]: null }));
      return;
    }
    try {
      const [versions, usage] = await Promise.all([listQuestionVersions(questionId), getQuestionUsage(questionId)]);
      setDetails((current) => ({ ...current, [questionId]: { versions, usage } }));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };

  return (
    <div className="mx-auto max-w-[1450px] space-y-6 p-5 md:p-8">
      <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">Question Bank</p><h1 className="mt-2 text-[30px] font-semibold">Ngân hàng câu hỏi</h1><p className="mt-2 text-[13px] text-ink-muted">Tìm kiếm lọc theo chất lượng theo dõi phiên bản mức sử dụng và exposure</p></div><div className="flex flex-wrap gap-2">{assessmentDraftId && <button type="button" className="apple-button" disabled={!selected.size} onClick={() => void addSelected()}>Thêm {selected.size} câu vào đề</button>}<Link className="apple-button-secondary" href={assessmentDraftId ? `/giao-vien/de/soan-thao?id=${assessmentDraftId}` : "/giao-vien/de/soan-thao"}>Mở Composer</Link></div></div>
      <section className="grid gap-3 rounded-panel border border-border bg-surface p-4 md:grid-cols-[minmax(240px,1fr)_200px_180px_200px]"><input className="apple-input w-full" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Tìm toàn văn nội dung câu hỏi" aria-label="Tìm câu hỏi" /><select className="apple-input" value={questionType} onChange={(event) => setQuestionType(event.target.value)} aria-label="Lọc loại câu"><option value="">Mọi loại câu</option><option value="single_choice">Một đáp án</option><option value="multiple_choice">Nhiều đáp án</option><option value="true_false">Đúng sai</option><option value="numeric">Numeric</option><option value="matching">Ghép đôi</option><option value="ordering">Sắp xếp</option><option value="symbolic_math">Toán ký hiệu</option><option value="short_answer">Trả lời ngắn</option><option value="essay">Tự luận</option></select><select className="apple-input" value={qualityStatus} onChange={(event) => setQualityStatus(event.target.value)} aria-label="Lọc chất lượng"><option value="">Mọi chất lượng</option><option value="PASS">Đạt</option><option value="WARNING">Cảnh báo</option><option value="NEEDS_REVIEW">Cần rà soát</option></select><select className="apple-input" value={sortBy} onChange={(event) => setSortBy(event.target.value)} aria-label="Sắp xếp"><option value="updated">Cập nhật gần nhất</option><option value="predicted_difficulty">Độ khó dự đoán</option><option value="calibrated_difficulty">Độ khó thực nghiệm</option><option value="usage">Mức sử dụng</option><option value="exposure">Exposure</option></select></section>
      <input className="apple-input w-full" value={skillId} onChange={(event) => setSkillId(event.target.value)} placeholder="Lọc theo Skill ID" aria-label="Lọc theo kỹ năng" />
      <details className="rounded-panel border border-border bg-surface p-4"><summary className="cursor-pointer text-[13px] font-semibold">Bộ lọc nâng cao</summary><div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><input className="apple-input" value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="Môn học" /><input className="apple-input" value={targetProgram} onChange={(event) => setTargetProgram(event.target.value)} placeholder="Chương trình mục tiêu" /><input className="apple-input" value={chapter} onChange={(event) => setChapter(event.target.value)} placeholder="Chương" /><input className="apple-input" value={lesson} onChange={(event) => setLesson(event.target.value)} placeholder="Bài học" /><input className="apple-input" value={conceptId} onChange={(event) => setConceptId(event.target.value)} placeholder="Concept ID" /><select className="apple-input" value={cognitiveLevel} onChange={(event) => setCognitiveLevel(event.target.value)}><option value="">Mọi mức nhận thức</option><option value="recognition">Nhận biết</option><option value="comprehension">Thông hiểu</option><option value="application">Vận dụng</option><option value="analysis">Phân tích</option></select><select className="apple-input" value={authoringSource} onChange={(event) => setAuthoringSource(event.target.value)}><option value="">Mọi nguồn</option><option value="manual_tiptap">Thủ công</option><option value="import">Nhập đề</option><option value="ai_generated">AI tạo</option><option value="hybrid">Kết hợp</option></select><select className="apple-input" value={publicationStatus} onChange={(event) => setPublicationStatus(event.target.value)}><option value="">Mọi trạng thái xuất bản</option><option value="published">Đã dùng trong đề xuất bản</option><option value="unpublished">Chưa xuất bản</option></select><input className="apple-input" type="number" min="0" max="1" step="0.05" value={minimumConfidence} onChange={(event) => setMinimumConfidence(event.target.value)} placeholder="Confidence tối thiểu" /><input className="apple-input" type="number" min="1" max="5" step="0.1" value={minimumPredicted} onChange={(event) => setMinimumPredicted(event.target.value)} placeholder="AI từ" /><input className="apple-input" type="number" min="1" max="5" step="0.1" value={maximumPredicted} onChange={(event) => setMaximumPredicted(event.target.value)} placeholder="AI đến" /><input className="apple-input" type="number" min="1" max="5" step="0.1" value={minimumCalibrated} onChange={(event) => setMinimumCalibrated(event.target.value)} placeholder="Empirical từ" /><input className="apple-input" type="number" min="1" max="5" step="0.1" value={maximumCalibrated} onChange={(event) => setMaximumCalibrated(event.target.value)} placeholder="Empirical đến" /><select className="apple-input" value={sortDirection} onChange={(event) => setSortDirection(event.target.value)}><option value="desc">Giảm dần</option><option value="asc">Tăng dần</option></select></div></details>
      {loading && <div className="skeleton h-40" />}
      {!loading && <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{questions.map((item) => { const version = item.current_version || {}; const prediction = item.difficulty_prediction || {}; const calibration = item.calibration || {}; const detail = details[item._id]; return <article key={item._id} className={`rounded-panel border bg-surface p-5 ${selected.has(item._id) ? "border-brand" : "border-border"}`}><div className="flex items-center justify-between gap-3"><label className="flex items-center gap-2 text-[12px] font-semibold"><input type="checkbox" checked={selected.has(item._id)} onChange={() => toggle(item._id)} /> Chọn</label><div className="flex gap-2 text-[11px] uppercase tracking-wide text-ink-muted"><span>{version.question_type}</span><span>v{version.version}</span></div></div><p className="mt-4 line-clamp-3 text-[14px] font-semibold">{version.plain_text_projection || item._id}</p><div className="mt-5 grid grid-cols-2 gap-2 text-[12px]"><span className="rounded-control bg-surface-quiet p-2">AI {prediction.predicted_difficulty ?? "Chưa có"}</span><span className="rounded-control bg-surface-quiet p-2">Empirical {calibration.difficulty ?? "Chưa có"}</span><span className="rounded-control bg-surface-quiet p-2">Dùng {item.usage_count || 0} đề</span><span className="rounded-control bg-surface-quiet p-2">Exposure {item.exposure_count || 0}</span></div><div className="mt-4 flex flex-wrap gap-2"><button type="button" className="apple-button-secondary" onClick={() => void inspect(item._id)}>{detail ? "Ẩn lịch sử" : "Lịch sử"}</button><button type="button" className="apple-button-secondary" onClick={() => void duplicate(item._id)}>Nhân bản</button><button type="button" className="apple-button-secondary text-danger" onClick={() => void archive(item._id)}>Lưu trữ</button></div>{detail && <div className="mt-4 rounded-control bg-surface-quiet p-3 text-[12px]"><p>{detail.versions.length} phiên bản bất biến</p><p className="mt-1">{detail.usage.assessment_versions.length} AssessmentVersion sử dụng</p><p className="mt-1">{detail.usage.exposure_count} lượt exposure</p></div>}<p className="mt-4 text-[11px] text-ink-faint">{version._id}</p></article>; })}</div>}
      {!loading && !questions.length && <p className="rounded-panel border border-border bg-surface p-10 text-center text-ink-muted">Không có câu hỏi phù hợp bộ lọc</p>}
      {message && <p role="status" className="rounded-control bg-brand-soft p-3 text-brand">{message}</p>}
      {error && <p role="alert" className="rounded-control bg-danger-soft p-3 text-danger">{error}</p>}
    </div>
  );
}
