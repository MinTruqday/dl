"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { getAttemptResult } from "../services/assessment.service";
import TiptapReadOnly from "../editor/TiptapReadOnly";
export default function StudentResultPage() {
    const attemptId = useSearchParams().get("id") || "";
    const [result, setResult] = useState(null);
    const [error, setError] = useState("");
    useEffect(() => { if (attemptId)
        getAttemptResult(attemptId).then(setResult).catch((reason) => setError(reason instanceof Error ? reason.message : "Không thể tải kết quả")); }, [attemptId]);
    if (error)
        return <div role="alert" className="p-10 text-center text-danger">{error}</div>;
    if (!result)
        return <div className="p-10 text-center text-ink-muted">Đang tải kết quả</div>;
    return <div className="mx-auto max-w-3xl space-y-6 p-5 md:p-8"><div className="rounded-panel border border-border bg-surface p-8 text-center"><p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">Kết quả bài đánh giá</p><h1 className="mt-4 text-[38px] font-semibold">{result.total_score} trên {result.total_possible_score}</h1><p className="mt-2 text-[13px] text-ink-muted">Trạng thái {result.status}</p>{result.pending_scores > 0 && <p className="mt-3 rounded-control bg-warning-soft p-3 text-warning">Có {result.pending_scores} câu đang chờ chấm thủ công</p>}</div><section className="rounded-panel border border-border bg-surface p-5"><h2 className="font-semibold">Chính sách hiển thị kết quả</h2><p className="mt-2 text-[13px] text-ink-muted">{result.review_answers ? "Giáo viên cho phép xem đáp án và lời giải" : "Đáp án và giải thích đang được ẩn theo chính sách giáo viên"}</p></section>{result.review_answers && <section className="rounded-panel border border-border bg-surface"><h2 className="border-b border-border px-5 py-4 font-semibold">Rà soát câu trả lời</h2><div className="divide-y divide-border">{(result.responses || []).map((response, index) => <article key={response.question_version_id} className="space-y-3 px-5 py-4"><div className="flex justify-between gap-3"><p className="font-semibold">Câu {index + 1}</p><p className={response.is_correct ? "text-brand" : "text-danger"}>{response.score_status === "pending_review" ? "Chờ chấm" : response.is_correct ? "Đúng" : "Sai"}</p></div><p className="text-[12px] text-ink-muted">Câu trả lời {JSON.stringify(response.submitted_answer)} · Đáp án {JSON.stringify(response.answer_key)}</p>{response.solution_doc && <TiptapReadOnly value={response.solution_doc} label={`Lời giải câu ${index + 1}`}/>}</article>)}</div></section>}<Link className="apple-button" href="/hoc-sinh/bai-duoc-giao">Quay lại bài được giao</Link></div>;
}
