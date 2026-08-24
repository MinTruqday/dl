"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { listAssignedAssessments } from "../services/assessment.service";
import {
  finishedAttempt,
  formatDateTime,
  labelStatus,
  labelSubject,
} from "../lib/assessment.presentation";

export default function StudentHistoryPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    listAssignedAssessments()
      .then(setItems)
      .catch((reason) =>
        setError(reason instanceof Error ? reason.message : "Không thể tải lịch sử làm bài"),
      )
      .finally(() => setLoading(false));
  }, []);
  const completed = useMemo(() => items.filter(finishedAttempt), [items]);
  return (
    <div className="mx-auto max-w-[1100px] space-y-6 p-5 md:p-8">
      <div>
        <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">
          Hồ sơ làm bài
        </p>
        <h1 className="mt-2 text-[30px] font-semibold">Lịch sử và kết quả</h1>
        <p className="mt-2 text-[14px] text-ink-muted">
          Chỉ hiển thị các lượt đã nộp hoặc đã kết thúc
        </p>
      </div>
      <section className="hidden overflow-x-auto rounded-panel border border-border bg-surface md:block">
        <table className="w-full min-w-[760px] text-left text-[13px]">
          <thead className="bg-surface-quiet text-ink-muted">
            <tr>
              <th className="p-4">Bài đánh giá</th>
              <th className="p-4">Môn học</th>
              <th className="p-4">Hoàn tất</th>
              <th className="p-4">Trạng thái</th>
              <th className="p-4">Kết quả</th>
            </tr>
          </thead>
          <tbody>
            {completed.map((item) => (
              <tr key={item._id} className="border-t border-border">
                <td className="p-4 font-semibold">
                  {item.assessment?.title || "Bài đánh giá chưa đặt tên"}
                </td>
                <td className="p-4">{labelSubject(item.assessment?.target_context?.subject)}</td>
                <td className="p-4">
                  {formatDateTime(item.attempt?.submitted_at || item.attempt?.updated_at)}
                </td>
                <td className="p-4">{labelStatus(item.attempt?.status)}</td>
                <td className="p-4">
                  <Link
                    className="font-semibold text-brand"
                    href={`/hoc-sinh/ket-qua?id=${item.attempt._id}`}
                  >
                    Xem chi tiết
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && !error && !completed.length && (
          <p className="border-t border-border px-5 py-10 text-center text-ink-muted">
            Chưa có lượt làm bài đã hoàn tất
          </p>
        )}
      </section>
      <section className="space-y-3 md:hidden">
        {completed.map((item) => (
          <article key={item._id} className="rounded-panel border border-border bg-surface p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h2 className="font-semibold">
                  {item.assessment?.title || "Bài đánh giá chưa đặt tên"}
                </h2>
                <p className="mt-1 text-[12px] text-ink-muted">
                  {labelSubject(item.assessment?.target_context?.subject)}
                </p>
              </div>
              <span className="shrink-0 rounded-full bg-brand-soft px-2.5 py-1 text-[11px] font-semibold text-brand">
                {labelStatus(item.attempt?.status)}
              </span>
            </div>
            <p className="mt-4 text-[12px] text-ink-muted">
              Hoàn tất {formatDateTime(item.attempt?.submitted_at || item.attempt?.updated_at)}
            </p>
            <Link
              className="apple-button-secondary mt-4 w-full"
              href={`/hoc-sinh/ket-qua?id=${item.attempt._id}`}
            >
              Xem chi tiết
            </Link>
          </article>
        ))}
        {!loading && !error && !completed.length && (
          <p className="rounded-panel border border-border bg-surface p-8 text-center text-ink-muted">
            Chưa có lượt làm bài đã hoàn tất
          </p>
        )}
      </section>
      {loading && <div className="skeleton h-32" />}
      {error && (
        <p role="alert" className="rounded-control bg-danger-soft p-4 text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
