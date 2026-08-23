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
export default function AssessmentListPage() {
  const [drafts, setDrafts] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();
  const load = useCallback(async () => {
    const [draftValues, assessmentValues] = await Promise.all([
      listAssessmentDrafts(),
      listAssessments(),
    ]);
    setDrafts(draftValues);
    setAssessments(assessmentValues);
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
            Assessments
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
                  Revision {draft.revision} · {draft.status}
                </p>
              </Link>
            ))}
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
                      {assessment.status} · {assessment.current_version_id}
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
          </div>
        </section>
      </div>
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
