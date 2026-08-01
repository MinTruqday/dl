"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useRef, useState } from "react";
import type EditorJS from "@editorjs/editorjs";
import InlineState from "@/app/_components/InlineState";
import SegmentedTabs from "@/app/_components/SegmentedTabs";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
import { renderEditorPreview } from "./editorPreview";
import EditorTextToolsModal from "./EditorTextToolsModal";
import { useEditorWorkspace } from "./useEditorWorkspace";

const StandardEditor = dynamic(
  () => import("@/features/compilation/components/StandardEditor"),
  { ssr: false },
);
const LatexEditor = dynamic(
  () => import("@/features/compilation/components/LatexEditor"),
  { ssr: false },
);
const DocumentCommandPalette = dynamic(
  () => import("@/features/compilation/components/DocumentCommandPalette"),
  { ssr: false },
);

export default function EditorWorkspace() {
  const editor = useEditorWorkspace();
  const [exportOpen, setExportOpen] = useState(false);
  const [toolsOpen, setToolsOpen] = useState(false);
  const [commandsOpen, setCommandsOpen] = useState(false);
  const editorRef = useRef<EditorJS | null>(null);

  if (editor.loading) return <PageLoader rows={8} />;

  if (!editor.documents.length) {
    return (
      <div className="p-6">
        <InlineState
          title="Chưa có bản thảo"
          detail="Tạo tài liệu trước khi mở trình soạn thảo"
          action={
            <Link href="/soan-thao/khoi-tao" className="pill-button">
              Tạo tài liệu
            </Link>
          }
        />
      </div>
    );
  }

  const chooseExport = async (format: "pdf" | "docx" | "protected") => {
    setExportOpen(false);
    await editor.exportFile(format);
  };

  return (
    <div className="flex min-h-[calc(100dvh-60px)] flex-col bg-surface">
      <header className="flex min-h-[56px] flex-wrap items-center gap-3 border-b border-border px-4 py-2 md:px-6">
        <label className="min-w-0 flex-1 sm:max-w-[320px]">
          <span className="sr-only">Tài liệu</span>
          <select
            value={editor.documentId}
            onChange={(event) => editor.setDocumentId(event.target.value)}
            className="apple-input h-10 min-h-10 w-full py-1.5 text-[14px] font-semibold"
          >
            {editor.documents.map((document) => {
              const id = document._id || document.id || "";
              return (
                <option key={id} value={id}>
                  {document.title || "Chưa đặt tên"}
                </option>
              );
            })}
          </select>
        </label>

        <span className="text-[12px] text-ink-muted" role="status">
          {editor.status}
        </span>

        <div className="ml-auto flex items-center gap-2">
          <Button size="sm" variant="secondary" onClick={() => setToolsOpen(true)}>
            Công cụ văn bản
          </Button>
          {editor.selectedDocument?.content_format !== "doclibx" && (
            <Button size="sm" variant="secondary" onClick={() => setCommandsOpen(true)}>
              Chức năng tài liệu
            </Button>
          )}
          <Button
            size="sm"
            variant="secondary"
            disabled={editor.exporting}
            onClick={() => setExportOpen(true)}
          >
            Xuất tệp
          </Button>
          <Button size="sm" disabled={editor.saving} onClick={editor.save}>
            {editor.saving ? "Đang lưu" : "Lưu"}
          </Button>
          <Button size="sm" variant="secondary" onClick={editor.publish}>
            Xuất bản
          </Button>
        </div>
      </header>

      <div className="flex flex-wrap items-center gap-3 border-b border-border bg-surface-raised px-4 py-2 md:px-6">
        <SegmentedTabs
          label="Chế độ soạn thảo"
          value={editor.mode}
          onChange={editor.setMode}
          tabs={[
            { id: "edit", label: "Soạn thảo" },
            { id: "preview", label: "Xem trước" },
            { id: "source", label: "Mã nguồn" },
          ]}
        />
        <nav className="ml-auto flex items-center gap-1 text-[13px]">
          <Link
            href="/soan-thao"
            className="rounded-control px-3 py-2 font-semibold text-ink-muted hover:bg-surface-quiet hover:text-ink"
          >
            Quản lý
          </Link>
          <Link
            href={`/soan-thao/cau-hinh?tai-lieu=${editor.documentId}`}
            className="rounded-control px-3 py-2 font-semibold text-ink-muted hover:bg-surface-quiet hover:text-ink"
          >
            Cấu hình
          </Link>
          <Link
            href={`/soan-thao/binh-luan?tai-lieu=${editor.documentId}`}
            className="rounded-control px-3 py-2 font-semibold text-ink-muted hover:bg-surface-quiet hover:text-ink"
          >
            Bình luận
          </Link>
          <Link
            href={`/soan-thao/lich-su?tai-lieu=${editor.documentId}`}
            className="rounded-control px-3 py-2 font-semibold text-ink-muted hover:bg-surface-quiet hover:text-ink"
          >
            Phiên bản
          </Link>
          <Link
            href={`/soan-thao/so-lieu?tai-lieu=${editor.documentId}`}
            className="rounded-control px-3 py-2 font-semibold text-ink-muted hover:bg-surface-quiet hover:text-ink"
          >
            Số liệu
          </Link>
        </nav>
      </div>

      {editor.error && (
        <div className="px-4 pt-4 md:px-6">
          <InlineState
            title="Không thể hoàn tất thao tác"
            detail={editor.error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={editor.reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}

      {editor.notice && (
        <div className="px-4 pt-4 md:px-6">
          <InlineState
            title={editor.notice}
            action={
              <Button variant="ghost" onClick={editor.clearNotice}>
                Đóng
              </Button>
            }
          />
        </div>
      )}

      <main className="min-h-0 flex-1 overflow-auto bg-canvas p-3 md:p-6">
        <div className="mx-auto min-h-full max-w-[960px] border border-border bg-surface">
          {editor.mode === "edit" && (
            <div className="min-h-[calc(100dvh-190px)] p-5 md:p-8">
              {editor.selectedDocument?.content_format === "doclibx" ? (
                <LatexEditor
                  documentId={editor.documentId}
                  initialContent={editor.content}
                  onChange={editor.setContent}
                />
              ) : (
                <StandardEditor
                  documentId={editor.documentId}
                  initialContent={editor.content}
                  onSave={editor.setContent}
                  editorRef={editorRef}
                />
              )}
            </div>
          )}

          {editor.mode === "preview" && (
            <article className="min-h-[calc(100dvh-190px)] p-6 md:p-10">
              {editor.selectedDocument?.content_format === "doclibx" ? (
                editor.previewing ? (
                  <PageLoader rows={7} />
                ) : editor.previewUrl ? (
                  <iframe
                    src={editor.previewUrl}
                    title="Bản xem trước tài liệu"
                    className="h-[calc(100dvh-240px)] min-h-[600px] w-full border-0"
                  />
                ) : (
                  <InlineState title="Chưa có bản xem trước" />
                )
              ) : editor.content ? (
                <div
                  className="prose prose-zinc max-w-none text-[16px] leading-relaxed text-ink"
                  dangerouslySetInnerHTML={{
                    __html: renderEditorPreview(editor.content),
                  }}
                />
              ) : (
                <InlineState title="Bản thảo đang trống" />
              )}
            </article>
          )}

          {editor.mode === "source" && (
            <pre className="min-h-[calc(100dvh-190px)] overflow-auto whitespace-pre-wrap p-6 font-mono text-[13px] leading-relaxed text-ink md:p-8">
              {editor.content || "Trống"}
            </pre>
          )}
        </div>
      </main>

      <Modal
        isOpen={exportOpen}
        onClose={() => setExportOpen(false)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle>Xuất tài liệu</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="divide-y divide-border border-y border-border">
            <button
              type="button"
              onClick={() => chooseExport("pdf")}
              className="flex w-full items-center justify-between py-3 text-left text-[14px] font-semibold hover:text-brand"
            >
              PDF
              <span className="text-[12px] font-normal text-ink-muted">
                pdf
              </span>
            </button>
            {editor.selectedDocument?.content_format !== "doclibx" && (
              <button
                type="button"
                onClick={() => chooseExport("docx")}
                className="flex w-full items-center justify-between py-3 text-left text-[14px] font-semibold hover:text-brand"
              >
                Word
                <span className="text-[12px] font-normal text-ink-muted">
                  docx
                </span>
              </button>
            )}
            <button
              type="button"
              onClick={() => chooseExport("protected")}
              className="flex w-full items-center justify-between py-3 text-left text-[14px] font-semibold hover:text-brand"
            >
              Tệp bảo vệ
              <span className="text-[12px] font-normal text-ink-muted">
                doclib
              </span>
            </button>
          </div>
        </ModalContent>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setExportOpen(false)}>
            Đóng
          </Button>
        </ModalFooter>
      </Modal>
      <EditorTextToolsModal open={toolsOpen} close={() => setToolsOpen(false)} content={editor.content} />
      <DocumentCommandPalette
        open={commandsOpen}
        close={() => setCommandsOpen(false)}
        editorRef={editorRef}
        onSave={editor.setContent}
      />
    </div>
  );
}
