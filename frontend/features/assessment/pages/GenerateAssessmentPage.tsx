"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { assessmentRequest, listAssessmentDrafts } from "../services/assessment.service";
import type { AssessmentDraft } from "../types";
import { distributeDifficulty, questionTypes, validDifficultyDistribution } from "../lib/assessment.logic.mjs";

export default function GenerateAssessmentPage() {
  const requestedId = useSearchParams().get("id") || "";
  const [drafts, setDrafts] = useState<AssessmentDraft[]>([]);
  const [draftId, setDraftId] = useState("");
  const [educationLevel, setEducationLevel] = useState("THPT");
  const [targetProgram, setTargetProgram] = useState("grade_12");
  const [subject, setSubject] = useState("math");
  const [chapterId, setChapterId] = useState("");
  const [lessonId, setLessonId] = useState("");
  const [topic, setTopic] = useState("Đạo hàm");
  const [conceptIds, setConceptIds] = useState("");
  const [skillIds, setSkillIds] = useState("");
  const [questionType, setQuestionType] = useState("single_choice");
  const [count, setCount] = useState(3);
  const [difficulty, setDifficulty] = useState(3);
  const [useDistribution, setUseDistribution] = useState(false);
  const [difficultyDistribution, setDifficultyDistribution] = useState<Record<string, number>>(distributeDifficulty(3));
  const [cognitiveLevel, setCognitiveLevel] = useState("");
  const [intendedPurpose, setIntendedPurpose] = useState("assigned_assessment");
  const [timeConstraint, setTimeConstraint] = useState("45");
  const [abilityMinimum, setAbilityMinimum] = useState("1");
  const [abilityMaximum, setAbilityMaximum] = useState("5");
  const [useTeacherMaterials, setUseTeacherMaterials] = useState(false);
  const [result, setResult] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { listAssessmentDrafts().then((values) => { setDrafts(values); if (requestedId || values[0]) setDraftId(requestedId || values[0]._id); }); }, [requestedId]);
  const generate = async () => {
    setError("");
    try {
      if (useDistribution && !validDifficultyDistribution(count, difficultyDistribution)) throw new Error("Tổng phân bố độ khó phải bằng số câu cần tạo");
      const value = await assessmentRequest<Record<string, any>>(`/assessment-drafts/${draftId}/generate`, { method: "POST", body: JSON.stringify({ idempotency_key: `generate-${crypto.randomUUID()}`, education_level: educationLevel, target_program: targetProgram, subject, chapter_id: chapterId || null, lesson_id: lessonId || null, topic, concept_ids: conceptIds.split(/[,;\n]+/).map((item) => item.trim()).filter(Boolean), skill_ids: skillIds.split(/[,;\n]+/).map((item) => item.trim()).filter(Boolean), question_type: questionType, count, target_difficulty: useDistribution ? null : difficulty, difficulty_distribution: useDistribution ? difficultyDistribution : {}, cognitive_level: cognitiveLevel || null, intended_purpose: intendedPurpose, time_constraint_minutes: Number(timeConstraint) || null, target_learner_band: { minimum: Number(abilityMinimum), maximum: Number(abilityMaximum) }, use_teacher_materials: useTeacherMaterials, source_scope: useTeacherMaterials ? "curriculum_and_owned_material" : "curriculum_only", source_evidence: [] }) });
      setResult(value);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tạo candidate");
    }
  };
  return (
    <div className="mx-auto max-w-[1200px] space-y-6 p-5 md:p-8">
      <div><p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">Constrained Generation</p><h1 className="mt-2 text-[30px] font-semibold">AI tạo câu hỏi</h1><p className="mt-2 text-[13px] text-ink-muted">Mọi câu sinh ra là QuestionDraft cần giáo viên rà soát và không tự xuất bản</p></div>
      <section className="grid gap-4 rounded-panel border border-border bg-surface p-5 md:grid-cols-2"><label className="text-[13px] font-semibold">AssessmentDraft<select className="apple-input mt-2 w-full" value={draftId} onChange={(event) => setDraftId(event.target.value)}>{drafts.map((draft) => <option key={draft._id} value={draft._id}>{draft.title}</option>)}</select></label><label className="text-[13px] font-semibold">Cấp học<input className="apple-input mt-2 w-full" value={educationLevel} onChange={(event) => setEducationLevel(event.target.value)} /></label><label className="text-[13px] font-semibold">Chương trình mục tiêu<input className="apple-input mt-2 w-full" value={targetProgram} onChange={(event) => setTargetProgram(event.target.value)} /></label><label className="text-[13px] font-semibold">Môn học<input className="apple-input mt-2 w-full" value={subject} onChange={(event) => setSubject(event.target.value)} /></label><label className="text-[13px] font-semibold">Chương<input className="apple-input mt-2 w-full" value={chapterId} onChange={(event) => setChapterId(event.target.value)} /></label><label className="text-[13px] font-semibold">Bài học<input className="apple-input mt-2 w-full" value={lessonId} onChange={(event) => setLessonId(event.target.value)} /></label><label className="text-[13px] font-semibold">Chủ đề<input className="apple-input mt-2 w-full" value={topic} onChange={(event) => setTopic(event.target.value)} /></label><label className="text-[13px] font-semibold">Concept IDs<input className="apple-input mt-2 w-full" value={conceptIds} onChange={(event) => setConceptIds(event.target.value)} /></label><label className="text-[13px] font-semibold">Skill IDs<input className="apple-input mt-2 w-full" value={skillIds} onChange={(event) => setSkillIds(event.target.value)} /></label><label className="text-[13px] font-semibold">Loại câu<select className="apple-input mt-2 w-full" value={questionType} onChange={(event) => setQuestionType(event.target.value)}>{questionTypes.map((type) => <option key={type} value={type}>{type}</option>)}</select></label><label className="text-[13px] font-semibold">Số câu<input className="apple-input mt-2 w-full" type="number" min={1} max={50} value={count} onChange={(event) => { const next = Math.max(1, Math.min(50, Number(event.target.value) || 1)); setCount(next); setDifficultyDistribution(distributeDifficulty(next)); }} /></label><label className="text-[13px] font-semibold">Mức nhận thức<select className="apple-input mt-2 w-full" value={cognitiveLevel} onChange={(event) => setCognitiveLevel(event.target.value)}><option value="">Hệ thống đề xuất</option><option value="recognition">Nhận biết</option><option value="comprehension">Thông hiểu</option><option value="application">Vận dụng</option><option value="analysis">Phân tích</option></select></label><label className="text-[13px] font-semibold">Mục đích<select className="apple-input mt-2 w-full" value={intendedPurpose} onChange={(event) => setIntendedPurpose(event.target.value)}><option value="assigned_assessment">Bài được giao</option><option value="formative">Đánh giá thường xuyên</option><option value="summative">Đánh giá tổng kết</option><option value="research_retest">Kiểm định lại nghiên cứu</option></select></label><label className="text-[13px] font-semibold">Thời gian mục tiêu phút<input className="apple-input mt-2 w-full" type="number" min="1" value={timeConstraint} onChange={(event) => setTimeConstraint(event.target.value)} /></label><div className="grid grid-cols-2 gap-3"><label className="text-[13px] font-semibold">Năng lực từ<input className="apple-input mt-2 w-full" type="number" min="1" max="5" step="0.1" value={abilityMinimum} onChange={(event) => setAbilityMinimum(event.target.value)} /></label><label className="text-[13px] font-semibold">Năng lực đến<input className="apple-input mt-2 w-full" type="number" min="1" max="5" step="0.1" value={abilityMaximum} onChange={(event) => setAbilityMaximum(event.target.value)} /></label></div><label className="flex items-center gap-2 text-[13px] font-semibold"><input type="checkbox" checked={useDistribution} onChange={(event) => setUseDistribution(event.target.checked)} /> Dùng phân bố năm mức</label>{useDistribution ? <div className="grid grid-cols-5 gap-2 md:col-span-2">{[1, 2, 3, 4, 5].map((level) => <label key={level} className="text-center text-[12px] font-semibold">Mức {level}<input className="apple-input mt-2 w-full text-center" type="number" min="0" value={difficultyDistribution[String(level)] || 0} onChange={(event) => setDifficultyDistribution((current) => ({ ...current, [String(level)]: Math.max(0, Number(event.target.value) || 0) }))} /></label>)}</div> : <label className="text-[13px] font-semibold">Target difficulty<select className="apple-input mt-2 w-full" value={difficulty} onChange={(event) => setDifficulty(Number(event.target.value))}>{[1, 2, 3, 4, 5].map((level) => <option key={level} value={level}>Mức {level}</option>)}</select></label>}<label className="flex items-center gap-2 text-[13px] font-semibold md:col-span-2"><input type="checkbox" checked={useTeacherMaterials} onChange={(event) => setUseTeacherMaterials(event.target.checked)} /> Dùng curriculum và tài liệu riêng thuộc sở hữu của tôi</label><p className="text-[12px] text-ink-muted md:col-span-2">Phạm vi nguồn {useTeacherMaterials ? "curriculum và tài liệu riêng" : "chỉ curriculum chính thống"}</p><button className="apple-button md:col-span-2" disabled={!draftId || !topic.trim()} onClick={generate}>Tạo candidate có provenance</button></section>
      {error && <p role="alert" className="rounded-control bg-danger-soft p-3 text-danger">{error}</p>}
      {result && <section className="rounded-panel border border-border bg-surface"><h2 className="border-b border-border px-5 py-4 font-semibold">Candidate chờ rà soát</h2><div className="divide-y divide-border">{result.questions?.map((question: any) => <div key={question._id} className="px-5 py-4"><p className="font-semibold">{question._id}</p><p className="mt-1 text-[12px] text-ink-muted">Độ khó dự đoán {question.difficulty_prediction?.predicted_difficulty ?? "Ẩn theo research blind mode"} · trạng thái needs teacher review</p></div>)}</div><div className="p-4"><Link className="apple-button" href={`/giao-vien/de/soan-thao?id=${draftId}`}>Rà soát trong Composer</Link></div></section>}
    </div>
  );
}
