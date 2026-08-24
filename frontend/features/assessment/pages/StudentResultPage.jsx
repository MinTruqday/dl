"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { getAttemptResult } from "../services/assessment.service";
import TiptapReadOnly from "../editor/TiptapReadOnly";
import { labelStatus } from "../lib/assessment.presentation";

function formatAnswer(value) {
  if (value === null || value === undefined || value === "") return "Chưa trả lời";
  if (Array.isArray(value)) return value.map(formatAnswer).join(", ");
  if (typeof value !== "object") return String(value);
  if (value.option_id) return `Phương án ${value.option_id}`;
  if (value.option_ids) return `Các phương án ${value.option_ids.join(", ")}`;
  if (value.value !== undefined) return String(value.value);
  if (value.text !== undefined) return String(value.text);
  return Object.values(value).map(formatAnswer).filter(Boolean).join(" · ");
}
export default function StudentResultPage() {
  const attemptId = useSearchParams().get("id") || "";
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (attemptId)
      getAttemptResult(attemptId)
        .then(setResult)
        .catch((reason) =>
          setError(reason instanceof Error ? reason.message : "Không thể tải kết quả"),
        );
  }, [attemptId]);
  if (!attemptId)
    return (
      <div role="alert" className="space-y-4 p-10 text-center">
        <p className="text-danger">Chưa chọn lượt làm bài</p>
        <Link className="apple-button" href="/hoc-sinh/bai-duoc-giao">
          Quay lại bài được giao
        </Link>
      </div>
    );
  if (error)
    return (
      <div role="alert" className="p-10 text-center text-danger">
        {error}
      </div>
    );
  if (!result) return <div className="p-10 text-center text-ink-muted">Đang tải kết quả</div>;
  return (
    <div className="mx-auto max-w-3xl space-y-6 p-5 md:p-8">
      <div className="rounded-panel border border-border bg-surface p-8 text-center">
        <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">
          Kết quả bài đánh giá
        </p>
        <h1 className="mt-4 text-[38px] font-semibold">
          {result.total_score} trên {result.total_possible_score}
        </h1>
        <p className="mt-2 text-[13px] text-ink-muted">Trạng thái {labelStatus(result.status)}</p>
        {result.pending_scores > 0 && (
          <p className="mt-3 rounded-control bg-warning-soft p-3 text-warning">
            Có {result.pending_scores} câu đang chờ chấm thủ công
          </p>
        )}
      </div>
      <section className="rounded-panel border border-border bg-surface p-5">
        <h2 className="font-semibold">Chính sách hiển thị kết quả</h2>
        <p className="mt-2 text-[13px] text-ink-muted">
          {result.review_answers
            ? "Giáo viên cho phép xem đáp án và lời giải"
            : "Đáp án và giải thích đang được ẩn theo chính sách giáo viên"}
        </p>
      </section>
      {result.review_answers && (
        <section className="rounded-panel border border-border bg-surface">
          <h2 className="border-b border-border px-5 py-4 font-semibold">Rà soát câu trả lời</h2>
          <div className="divide-y divide-border">
            {(result.responses || []).map((response, index) => (
              <article key={response.question_version_id} className="space-y-3 px-5 py-4">
                <div className="flex justify-between gap-3">
                  <p className="font-semibold">Câu {index + 1}</p>
                  <p className={response.is_correct ? "text-brand" : "text-danger"}>
                    {response.score_status === "pending_review"
                      ? "Chờ chấm"
                      : response.is_correct
                        ? "Đúng"
                        : "Sai"}
                  </p>
                </div>
                {response.stem_doc && (
                  <TiptapReadOnly value={response.stem_doc} label={`Nội dung câu ${index + 1}`} />
                )}
                <div className="grid gap-3 rounded-control bg-surface-quiet p-4 text-[13px] sm:grid-cols-2">
                  <div>
                    <p className="text-ink-muted">Câu trả lời của bạn</p>
                    <p className="mt-1 font-semibold">{formatAnswer(response.submitted_answer)}</p>
                  </div>
                  <div>
                    <p className="text-ink-muted">Đáp án</p>
                    <p className="mt-1 font-semibold">{formatAnswer(response.answer_key)}</p>
                  </div>
                </div>
                {response.solution_doc && (
                  <TiptapReadOnly
                    value={response.solution_doc}
                    label={`Lời giải câu ${index + 1}`}
                  />
                )}
              </article>
            ))}
          </div>
        </section>
      )}
      <Link className="apple-button" href="/hoc-sinh/bai-duoc-giao">
        Quay lại bài được giao
      </Link>
    </div>
  );
}
