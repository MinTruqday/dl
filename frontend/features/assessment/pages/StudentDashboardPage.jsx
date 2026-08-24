"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { listAssignedAssessments } from "../services/assessment.service";
import {
  assignmentStatus,
  finishedAttempt,
  formatDateTime,
  labelSubject,
} from "../lib/assessment.presentation";

export default function StudentDashboardPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    listAssignedAssessments()
      .then(setItems)
      .catch((reason) =>
        setError(reason instanceof Error ? reason.message : "Không thể tải tổng quan học tập"),
      )
      .finally(() => setLoading(false));
  }, []);
  const summary = useMemo(() => {
    return {
      available: items.filter(
        (item) => item.availability_status === "available" && !finishedAttempt(item),
      ).length,
      active: items.filter((item) => item.attempt?.status === "active").length,
      finished: items.filter(finishedAttempt).length,
    };
  }, [items]);
  const recent = items.slice(0, 4);
  return (
    <div className="mx-auto max-w-[1200px] space-y-6 p-5 md:p-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">
            Tổng quan học tập
          </p>
          <h1 className="mt-2 text-[30px] font-semibold">Năng lực và tiến độ</h1>
          <p className="mt-2 max-w-2xl text-[14px] text-ink-muted">
            Theo dõi bài cần làm và bằng chứng học tập đã thu được từ các lượt làm bài
          </p>
        </div>
        <Link className="apple-button" href="/hoc-sinh/bai-duoc-giao">
          Mở bài được giao
        </Link>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          ["Cần hoàn thành", summary.available],
          ["Đang thực hiện", summary.active],
          ["Đã hoàn tất", summary.finished],
        ].map(([label, value]) => (
          <section key={label} className="rounded-panel border border-border bg-surface p-5">
            <p className="text-[28px] font-semibold">{value}</p>
            <p className="mt-1 text-[12px] text-ink-muted">{label}</p>
          </section>
        ))}
      </div>
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
        <section className="rounded-panel border border-border bg-surface">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <h2 className="font-semibold">Hoạt động gần đây</h2>
            <Link className="text-[13px] font-semibold text-brand" href="/hoc-sinh/lich-su">
              Xem lịch sử
            </Link>
          </div>
          <div className="divide-y divide-border">
            {recent.map((item) => (
              <article key={item._id} className="flex flex-wrap items-center gap-4 px-5 py-4">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold">
                    {item.assessment?.title || "Bài đánh giá chưa đặt tên"}
                  </p>
                  <p className="mt-1 text-[12px] text-ink-muted">
                    {labelSubject(item.assessment?.target_context?.subject)} · hạn nộp{" "}
                    {formatDateTime(item.due_at, "không giới hạn")}
                  </p>
                </div>
                <span className="rounded-full bg-brand-soft px-3 py-1 text-[11px] font-semibold text-brand">
                  {assignmentStatus(item)}
                </span>
              </article>
            ))}
            {!loading && !error && !recent.length && (
              <p className="px-5 py-10 text-center text-[13px] text-ink-muted">
                Chưa có hoạt động học tập
              </p>
            )}
          </div>
        </section>
        <section className="rounded-panel border border-border bg-surface p-5">
          <h2 className="font-semibold">Bằng chứng năng lực</h2>
          <p className="mt-3 text-[14px] leading-6 text-ink-muted">
            Hệ thống chỉ ước lượng năng lực khi có đủ câu trả lời hợp lệ và dữ liệu hiệu chỉnh phù
            hợp với bối cảnh
          </p>
          <div className="mt-5 rounded-control bg-surface-quiet p-4">
            <p className="text-[12px] font-semibold text-ink">Chưa có đủ bằng chứng để ước lượng</p>
            <p className="mt-2 text-[12px] leading-5 text-ink-muted">
              Hoàn thành thêm bài đánh giá để dữ liệu được tích lũy mà không tạo ra điểm năng lực
              giả
            </p>
          </div>
        </section>
      </div>
      {loading && <div className="skeleton h-32" />}
      {error && (
        <p role="alert" className="rounded-control bg-danger-soft p-4 text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
