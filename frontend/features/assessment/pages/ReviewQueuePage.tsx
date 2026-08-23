"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { archiveQuestionBankItem, assessmentRequest, getReviewQueue } from "../services/assessment.service";

export default function ReviewQueuePage() {
  const [data, setData] = useState<Record<string, any>>({ questions: [], question_revisions: [], draft_revisions: [] });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const load = () => getReviewQueue().then(setData).catch((reason) => setError(reason instanceof Error ? reason.message : "Không thể tải hàng đợi rà soát"));
  useEffect(() => { void load(); }, []);
  const decide = async (path: string) => {
    const reviewerNote = window.prompt("Nhận xét của giáo viên cho quyết định này", "Đã rà soát trong Review Queue");
    if (reviewerNote === null) return;
    setBusy(path);
    setError("");
    try {
      await assessmentRequest(path, { method: "POST", body: JSON.stringify({ reviewer_note: reviewerNote.trim() }) });
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể lưu quyết định rà soát");
    } finally {
      setBusy("");
    }
  };
  const lock = async (question: Record<string, any>) => {
    setBusy(`lock-${question._id}`);
    setError("");
    try {
      await assessmentRequest(`/question-drafts/${question._id}`, {
        method: "PATCH",
        body: JSON.stringify({ expected_revision: question.revision, locked: true }),
      });
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể khóa câu hỏi");
    } finally {
      setBusy("");
    }
  };
  const archive = async (question: Record<string, any>) => {
    if (!question.question_id || !window.confirm("Lưu trữ câu hỏi khỏi ngân hàng")) return;
    setBusy(`archive-${question._id}`);
    setError("");
    try {
      await archiveQuestionBankItem(question.question_id, "Lưu trữ từ Review Queue");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể lưu trữ câu hỏi");
    } finally {
      setBusy("");
    }
  };
  return (
    <div className="mx-auto max-w-[1250px] space-y-6 p-5 md:p-8">
      <div><p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">Human in the loop</p><h1 className="mt-2 text-[30px] font-semibold">Danh sách chờ rà soát</h1></div>
      {error && <p role="alert" className="rounded-control bg-danger-soft p-3 text-danger">{error}</p>}
      <section className="rounded-panel border border-border bg-surface"><h2 className="border-b border-border px-5 py-4 font-semibold">Câu hỏi cần quyết định</h2><div className="divide-y divide-border">{data.questions.map((question: any) => <div key={question._id} className="flex flex-wrap items-center gap-3 px-5 py-4"><div className="min-w-0 flex-1"><p className="font-semibold">{question._id}</p><p className="mt-1 text-[12px] text-ink-muted">{question.authoring_source} · {question.status} · độ tin cậy parse {question.parse_confidence ?? "không áp dụng"} · validation {question.validation?.status || "chưa chạy"}</p>{question.review_reason_codes?.length > 0 && <p className="mt-1 text-[12px] text-warning">Lý do {question.review_reason_codes.join(" · ")}</p>}</div><Link className="apple-button-secondary" href={`/giao-vien/de/soan-thao?id=${question.assessment_draft_id}`}>Sửa thủ công</Link><Link className="apple-button-secondary" href={`/tro-chuyen?mode=work&prompt=${encodeURIComponent(`Điều tra QuestionDraft ${question._id} rồi chỉ tạo đề xuất sửa đổi có construct check`)}`}>Yêu cầu AI sửa</Link><button className="apple-button-secondary" disabled={Boolean(busy) || question.locked} onClick={() => void lock(question)}>{question.locked ? "Đã khóa AI" : "Khóa khỏi AI"}</button>{question.question_id && <button className="apple-button-secondary" disabled={Boolean(busy)} onClick={() => void archive(question)}>Lưu trữ</button>}<button className="apple-button-secondary" disabled={Boolean(busy)} onClick={() => decide(`/question-drafts/${question._id}/reject`)}>Từ chối</button><button className="apple-button" disabled={Boolean(busy)} onClick={() => decide(`/question-drafts/${question._id}/approve`)}>Phê duyệt</button></div>)}</div></section>
      <section className="rounded-panel border border-border bg-surface"><h2 className="border-b border-border px-5 py-4 font-semibold">Đề xuất sửa đổi version</h2><div className="divide-y divide-border">{data.question_revisions.map((proposal: any) => <div key={proposal._id} className="space-y-3 px-5 py-4"><div className="flex flex-wrap items-center gap-3"><div className="min-w-0 flex-1"><p className="font-semibold">Lý do {proposal.reason_codes?.join(" · ")}</p><p className="mt-1 text-[12px] text-ink-muted">Target effect {proposal.target_difficulty ?? "chưa đặt"} · Construct {proposal.construct_check?.passed ? "đạt" : "chưa đạt"} · Evidence {proposal.evidence_ids?.length || 0}</p></div><button className="apple-button-secondary" disabled={Boolean(busy)} onClick={() => decide(`/revisions/${proposal._id}/reject`)}>Từ chối</button><button className="apple-button" disabled={Boolean(busy) || !proposal.construct_check?.passed} onClick={() => decide(`/revisions/${proposal._id}/approve`)}>Tạo version mới</button></div><details className="rounded-control border border-border p-3 text-[12px]"><summary className="cursor-pointer font-semibold">Before After Why Target Effect Construct Check</summary><div className="mt-3 grid gap-3 lg:grid-cols-2"><pre className="overflow-auto whitespace-pre-wrap rounded-control bg-surface-quiet p-3">{JSON.stringify({ before: proposal.original_version, why: proposal.reason_codes, target_effect: proposal.target_difficulty }, null, 2)}</pre><pre className="overflow-auto whitespace-pre-wrap rounded-control bg-surface-quiet p-3">{JSON.stringify({ after: proposal.proposed_version, construct_check: proposal.construct_check }, null, 2)}</pre></div></details></div>)}</div></section>
      <section className="rounded-panel border border-border bg-surface"><h2 className="border-b border-border px-5 py-4 font-semibold">Đề xuất sửa bản nháp</h2><div className="divide-y divide-border">{data.draft_revisions.map((proposal: any) => <div key={proposal._id} className="space-y-3 px-5 py-4"><div className="flex flex-wrap items-center gap-3"><div className="min-w-0 flex-1"><p className="font-semibold">{proposal.action}</p><p className="mt-1 text-[12px] text-ink-muted">Construct {proposal.construct_check?.passed ? "đạt" : "chưa đạt"}</p></div><button className="apple-button-secondary" disabled={Boolean(busy)} onClick={() => decide(`/draft-revisions/${proposal._id}/reject`)}>Từ chối</button><button className="apple-button" disabled={Boolean(busy) || !proposal.construct_check?.passed} onClick={() => decide(`/draft-revisions/${proposal._id}/approve`)}>Áp dụng vào bản nháp</button></div><details className="rounded-control border border-border p-3 text-[12px]"><summary className="cursor-pointer font-semibold">So sánh trước và sau</summary><div className="mt-3 grid gap-3 lg:grid-cols-2"><pre className="overflow-auto whitespace-pre-wrap rounded-control bg-surface-quiet p-3">{JSON.stringify(proposal.before, null, 2)}</pre><pre className="overflow-auto whitespace-pre-wrap rounded-control bg-surface-quiet p-3">{JSON.stringify(proposal.after, null, 2)}</pre></div></details></div>)}</div></section>
    </div>
  );
}
