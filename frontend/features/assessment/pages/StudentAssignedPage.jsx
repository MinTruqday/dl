"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { listAssignedAssessments } from "../services/assessment.service";
import {
  assignmentStatus,
  finishedAttempt,
  formatDateTime,
  labelSubject,
} from "../lib/assessment.presentation";
export default function StudentAssignedPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    listAssignedAssessments()
      .then(setItems)
      .catch((reason) =>
        setError(reason instanceof Error ? reason.message : "Không thể tải bài được giao"),
      )
      .finally(() => setLoading(false));
  }, []);
  return (
    <div className="mx-auto max-w-[1200px] space-y-6 p-5 md:p-8">
      <div>
        <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">
          Danh sách được giao
        </p>
        <h1 className="mt-2 text-[30px] font-semibold">Bài được giao</h1>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => {
          const attemptFinished = finishedAttempt(item);
          const displayStatus = assignmentStatus(item);
          return (
            <article key={item._id} className="rounded-panel border border-border bg-surface p-5">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-brand-soft px-3 py-1 text-[11px] font-semibold text-brand">
                  {displayStatus}
                </span>
                <span className="text-[12px] text-ink-muted">
                  {formatDateTime(item.due_at, "Không giới hạn")}
                </span>
              </div>
              <h2 className="mt-5 text-[18px] font-semibold">
                {item.assessment?.title || item.assessment_version_id}
              </h2>
              <p className="mt-2 text-[12px] text-ink-muted">
                Phiên bản đã được khóa khi giáo viên giao bài
              </p>
              <p className="mt-1 text-[12px] text-ink-muted">
                Môn {labelSubject(item.assessment?.target_context?.subject)} · Thời gian{" "}
                {String(
                  item.attempt?.policy_snapshot?.duration_minutes ||
                    item.assessment?.delivery_policy?.duration_minutes ||
                    "Không giới hạn",
                )}{" "}
                phút
              </p>
              {attemptFinished && item.attempt ? (
                <Link
                  className="apple-button mt-5"
                  href={`/hoc-sinh/ket-qua?id=${item.attempt._id}`}
                >
                  Xem kết quả
                </Link>
              ) : item.availability_status === "upcoming" ||
                item.availability_status === "expired" ? (
                <button className="apple-button mt-5" disabled>
                  {displayStatus}
                </button>
              ) : (
                <Link
                  className="apple-button mt-5"
                  href={`/hoc-sinh/lam-bai?id=${item.assessment_id}&assignment=${item._id}`}
                >
                  {item.attempt?.status === "active" ? "Tiếp tục làm bài" : "Bắt đầu làm bài"}
                </Link>
              )}
            </article>
          );
        })}
      </div>
      {error && (
        <p
          role="alert"
          className="rounded-panel border border-danger bg-surface p-10 text-center text-danger"
        >
          {error}
        </p>
      )}
      {loading && (
        <p className="rounded-panel border border-border bg-surface p-10 text-center text-ink-muted">
          Đang tải bài được giao
        </p>
      )}
      {!loading && !error && !items.length && (
        <p className="rounded-panel border border-border bg-surface p-10 text-center text-ink-muted">
          Chưa có bài được giao
        </p>
      )}
    </div>
  );
}
