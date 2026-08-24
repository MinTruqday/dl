"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { getDocumentDraftAPI } from "../services/document.service";

function labelIndexing(value) {
  if (value === "indexed") return "Đã lập chỉ mục";
  if (value === "failed") return "Lập chỉ mục thất bại";
  if (value === "indexing") return "Đang lập chỉ mục";
  return "Đang chờ lập chỉ mục";
}

function contentText(document) {
  if (document.extracted_text) return document.extracted_text;
  if (typeof document.content === "string") return document.content;
  if (document.content) return JSON.stringify(document.content, null, 2);
  return "Tài liệu chưa có nội dung trích xuất để xem trước";
}

export default function TeacherMaterialPreviewPage({ documentId }) {
  const [document, setDocument] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getDocumentDraftAPI(documentId)
      .then((response) => setDocument(response.data ?? response))
      .catch((reason) =>
        setError(reason instanceof Error ? reason.message : "Không thể tải tài liệu"),
      );
  }, [documentId]);
  if (error)
    return (
      <div className="mx-auto max-w-4xl space-y-4 p-8">
        <p role="alert" className="rounded-control bg-danger-soft p-4 text-danger">
          {error}
        </p>
        <Link className="apple-button-secondary" href="/giao-vien/tai-lieu">
          Quay lại tài liệu
        </Link>
      </div>
    );
  if (!document)
    return (
      <div className="mx-auto max-w-4xl p-8">
        <div className="skeleton h-80" />
      </div>
    );
  const metadata = document.education_metadata || {};
  const indexingStatus = document.indexing_status || (document.is_indexed ? "indexed" : "queued");
  return (
    <div className="mx-auto max-w-5xl space-y-6 p-5 md:p-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">
            Tài liệu giáo viên
          </p>
          <h1 className="mt-2 text-[30px] font-semibold">{document.title}</h1>
          <p className="mt-2 text-[13px] text-ink-muted">
            {metadata.subject || "Chưa gắn môn"} ·{" "}
            {metadata.target_program || "Chưa gắn chương trình"} · {labelIndexing(indexingStatus)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {document.file_url && (
            <a className="apple-button" href={document.file_url} target="_blank" rel="noreferrer">
              Mở tệp gốc
            </a>
          )}
          <Link className="apple-button-secondary" href="/giao-vien/tai-lieu">
            Quay lại
          </Link>
        </div>
      </div>
      <section className="grid gap-3 rounded-panel border border-border bg-surface p-5 text-[13px] sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="text-ink-muted">Loại nguồn</p>
          <p className="mt-1 font-semibold">Tài liệu bổ trợ của giáo viên</p>
        </div>
        <div>
          <p className="text-ink-muted">Mức thẩm quyền</p>
          <p className="mt-1 font-semibold">Bổ trợ</p>
        </div>
        <div>
          <p className="text-ink-muted">Chương hoặc bài</p>
          <p className="mt-1 font-semibold">
            {metadata.chapter_id || metadata.lesson_id || "Chưa ánh xạ"}
          </p>
        </div>
        <div>
          <p className="text-ink-muted">Cập nhật</p>
          <p className="mt-1 font-semibold">
            {document.updated_at
              ? new Date(document.updated_at).toLocaleString("vi-VN")
              : "Chưa có"}
          </p>
        </div>
      </section>
      <section className="rounded-panel border border-border bg-surface">
        <div className="border-b border-border px-5 py-4">
          <h2 className="font-semibold">Nội dung đã trích xuất</h2>
          <p className="mt-1 text-[12px] text-ink-muted">
            Nội dung này là dữ liệu thực được dùng cho tìm kiếm và ánh xạ
          </p>
        </div>
        <pre className="max-h-[65dvh] overflow-auto whitespace-pre-wrap break-words p-5 font-sans text-[14px] leading-7 text-ink">
          {contentText(document)}
        </pre>
      </section>
    </div>
  );
}
