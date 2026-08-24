"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  archiveAssessment,
  cloneAssessment,
  exportAssessmentVersion,
  listAssessmentDrafts,
  listAssessments,
  unpublishAssessment,
} from "../services/assessment.service";
import { labelStatus } from "../lib/assessment.presentation";
export default function AssessmentListPage() {
  const [drafts, setDrafts] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [draftValues, assessmentValues] = await Promise.all([
        listAssessmentDrafts(),
        listAssessments(),
      ]);
      setDrafts(draftValues);
      setAssessments(assessmentValues);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tải bài đánh giá");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);
  const clone = async (assessmentId) => {
    const draft = await cloneAssessment(assessmentId);
    router.push(`/giao-vien/de/soan-thao?id=${draft._id}`);
  };
  const archive = async (assessmentId) => {
    if (!window.confirm("Lưu trữ bài đánh giá này")) return;
    await archiveAssessment(assessmentId, "Lưu trữ từ danh sách bài đánh giá");
    setMessage("Đã lưu trữ bài đánh giá");
    await load();
  };
  const unpublish = async (assessmentId) => {
    if (!window.confirm("Hủy xuất bản phiên bản chưa có lượt làm")) return;
    await unpublishAssessment(assessmentId, "Hủy xuất bản từ danh sách bài đánh giá");
    setMessage("Đã hủy xuất bản");
    await load();
  };
  const exportVersion = async (versionId, format) => {
    setError("");
    try {
      await exportAssessmentVersion(versionId, format);
      setMessage(`Đã xuất ${format.toUpperCase()}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể xuất bài đánh giá");
    }
  };
  return (
    <div className="mx-auto max-w-[1300px] space-y-6 p-5 md:p-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">
            Quản lý đề kiểm tra
          </p>
          <h1 className="mt-2 text-[30px] font-semibold">Bài đánh giá</h1>
        </div>
        <div className="flex gap-2">
          <Link className="apple-button-secondary" href="/giao-vien/de/nhap">
            Nhập đề
          </Link>
          <Link className="apple-button-secondary" href="/giao-vien/de/sinh-ai">
            AI tạo đề
          </Link>
          <Link className="apple-button" href="/giao-vien/de/soan-thao">
            Soạn đề
          </Link>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-panel border border-border bg-surface">
          <h2 className="border-b border-border px-5 py-4 font-semibold">Bản nháp</h2>
          <div className="divide-y divide-border">
            {drafts.map((draft) => (
              <Link
                key={draft._id}
                href={`/giao-vien/de/soan-thao?id=${draft._id}`}
                className="block px-5 py-4 hover:bg-surface-quiet"
              >
                <p className="font-semibold">{draft.title}</p>
                <p className="mt-1 text-[12px] text-ink-muted">
                  Phiên bản chỉnh sửa {draft.revision} · {labelStatus(draft.status)}
                </p>
              </Link>
            ))}
            {!loading && !drafts.length && (
              <p className="px-5 py-10 text-center text-[13px] text-ink-muted">Chưa có bản nháp</p>
            )}
          </div>
        </section>
        <section className="rounded-panel border border-border bg-surface">
          <h2 className="border-b border-border px-5 py-4 font-semibold">
            Đã xuất bản và đã lên lịch
          </h2>
          <div className="divide-y divide-border">
            {assessments
              .filter((item) => ["published", "scheduled"].includes(item.status))
              .map((assessment) => (
                <article key={assessment._id} className="px-5 py-4">
                  <Link
                    href={`/giao-vien/hieu-chinh?id=${assessment._id}`}
                    className="block hover:text-brand"
                  >
                    <p className="font-semibold">{assessment.title || assessment._id}</p>
                    <p className="mt-1 text-[12px] text-ink-muted">
                      {labelStatus(assessment.status)} · Phiên bản đã khóa
                    </p>
                  </Link>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="apple-button-secondary"
                      onClick={() => void clone(assessment._id)}
                    >
                      Nhân bản
                    </button>
                    {assessment.current_version_id && (
                      <>
                        <button
                          type="button"
                          className="apple-button-secondary"
                          onClick={() => void exportVersion(assessment.current_version_id, "pdf")}
                        >
                          Xuất PDF
                        </button>
                        <button
                          type="button"
                          className="apple-button-secondary"
                          onClick={() => void exportVersion(assessment.current_version_id, "docx")}
                        >
                          Xuất DOCX
                        </button>
                      </>
                    )}
                    <button
                      type="button"
                      className="apple-button-secondary"
                      onClick={() => void unpublish(assessment._id)}
                    >
                      Hủy xuất bản
                    </button>
                    <button
                      type="button"
                      className="apple-button-secondary text-danger"
                      onClick={() => void archive(assessment._id)}
                    >
                      Lưu trữ
                    </button>
                  </div>
                </article>
              ))}
            {!loading &&
              !assessments.some((item) => ["published", "scheduled"].includes(item.status)) && (
                <p className="px-5 py-10 text-center text-[13px] text-ink-muted">
                  Chưa có bài đã xuất bản hoặc lên lịch
                </p>
              )}
          </div>
        </section>
      </div>
      {loading && <div className="skeleton h-32" />}
      {message && (
        <p role="status" className="rounded-control bg-brand-soft p-3 text-brand">
          {message}
        </p>
      )}
      {error && (
        <p role="alert" className="rounded-control bg-danger-soft p-3 text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
