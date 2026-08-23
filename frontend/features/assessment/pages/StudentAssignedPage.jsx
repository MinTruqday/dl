"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { listAssignedAssessments } from "../services/assessment.service";
export default function StudentAssignedPage() {
  const [items, setItems] = useState([]);
  useEffect(() => {
    listAssignedAssessments().then(setItems);
  }, []);
  return (
    <div className="mx-auto max-w-[1200px] space-y-6 p-5 md:p-8">
      <div>
        <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">
          Assigned Assessments
        </p>
        <h1 className="mt-2 text-[30px] font-semibold">Bài được giao</h1>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => {
          const attemptFinished = ["submitted", "completed", "timed_out"].includes(
            item.attempt?.status || "",
          );
          const displayStatus =
            item.status === "pending_manual_scoring"
              ? "Chờ chấm thủ công"
              : item.status === "scored"
                ? "Đã chấm"
                : item.attempt?.status === "active"
                  ? "Đang làm"
                  : item.availability_status === "upcoming"
                    ? "Sắp mở"
                    : item.availability_status === "expired"
                      ? "Đã hết hạn"
                      : "Có thể làm";
          return (
            <article key={item._id} className="rounded-panel border border-border bg-surface p-5">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-brand-soft px-3 py-1 text-[11px] font-semibold text-brand">
                  {displayStatus}
                </span>
                <span className="text-[12px] text-ink-muted">
                  {item.due_at ? new Date(item.due_at).toLocaleString("vi-VN") : "Không giới hạn"}
                </span>
              </div>
              <h2 className="mt-5 text-[18px] font-semibold">
                {item.assessment?.title || item.assessment_version_id}
              </h2>
              <p className="mt-2 text-[12px] text-ink-muted">
                Phiên bản cố định {item.assessment_version_id}
              </p>
              <p className="mt-1 text-[12px] text-ink-muted">
                Môn {String(item.assessment?.target_context?.subject || "Chưa gắn")} · Thời gian{" "}
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
      {!items.length && (
        <p className="rounded-panel border border-border bg-surface p-10 text-center text-ink-muted">
          Chưa có bài được giao
        </p>
      )}
    </div>
  );
}
