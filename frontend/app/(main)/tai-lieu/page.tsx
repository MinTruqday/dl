"use client";

import Link from "next/link";
import { useState } from "react";
import { Lock, Star, Trash2 } from "lucide-react";
import InlineState from "@/app/_components/InlineState";
import PageHeader from "@/app/_components/PageHeader";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import {
  ConfirmDeleteModal,
  CreateDocumentModal,
  ImportDocumentModal,
  TextModal,
} from "./DocumentModals";
import { FolderRecord, useDocuments } from "./useDocuments";

type Target = { id: string; type: "document" | "folder" } | null;
export default function DocumentsPage() {
  const state = useDocuments();
  const [createOpen, setCreateOpen] = useState(false);
  const [folderOpen, setFolderOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [lockTarget, setLockTarget] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Target>(null);
  if (state.authLoading || (state.loading && !state.user))
    return <PageLoader rows={7} />;
  if (!state.user)
    return (
      <InlineState
        title="Cần đăng nhập"
        detail="Đăng nhập để quản lý tài liệu"
      />
    );
  const openFolder = (folder: FolderRecord) =>
    state.setFolderPath([...state.folderPath, folder]);
  const remove = async () => {
    if (deleteTarget) {
      await state.remove(deleteTarget.id, deleteTarget.type);
      setDeleteTarget(null);
    }
  };
  return (
    <div className="w-full">
      <PageHeader
        title="Tài liệu"
        actions={
          <>
            <Button variant="secondary" onClick={() => setFolderOpen(true)}>
              Tạo thư mục
            </Button>
            <Button variant="secondary" onClick={() => setImportOpen(true)}>
              Nhập tài liệu
            </Button>
            <Button onClick={() => setCreateOpen(true)}>Tạo tài liệu</Button>
          </>
        }
        meta={
          <nav
            className="flex flex-wrap items-center gap-2"
            aria-label="Đường dẫn thư mục"
          >
            <button
              onClick={() => state.setFolderPath([])}
              className="font-semibold text-ink hover:text-brand"
            >
              Gốc
            </button>
            {state.folderPath.map((folder, index) => (
              <span
                key={folder._id ?? folder.id}
                className="flex items-center gap-2"
              >
                <span>/</span>
                <button
                  onClick={() =>
                    state.setFolderPath(state.folderPath.slice(0, index + 1))
                  }
                  className="hover:text-brand"
                >
                  {folder.name}
                </button>
              </span>
            ))}
          </nav>
        }
      />
      {state.error && (
        <div className="mb-6">
          <InlineState
            title="Không thể xử lý tài liệu"
            detail={state.error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={state.reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}
      {state.notice && (
        <div className="mb-6">
          <InlineState
            title={state.notice}
            action={
              <Button variant="ghost" onClick={state.clearNotice}>
                Đóng
              </Button>
            }
          />
        </div>
      )}
      <div className="mb-5 flex flex-col gap-3 rounded-panel border border-border bg-surface p-4 sm:flex-row">
        <input
          aria-label="Tìm tài liệu"
          value={state.query}
          onChange={(event) => state.setQuery(event.target.value)}
          className="apple-input min-w-0 flex-1"
          placeholder="Tìm theo tên"
        />
        <select
          aria-label="Định dạng"
          value={state.format}
          onChange={(event) => state.setFormat(event.target.value)}
          className="apple-input"
        >
          <option value="all">Mọi định dạng</option>
          <option value="pdf">PDF</option>
          <option value="markdown">Markdown</option>
          <option value="latex">LaTeX</option>
          <option value="docx">DOCX</option>
        </select>
        <label className="flex items-center gap-2 px-2 text-[13px] font-semibold text-ink">
          <input
            type="checkbox"
            checked={state.starred}
            onChange={(event) => state.setStarred(event.target.checked)}
            className="h-4 w-4 accent-[hsl(var(--brand))]"
          />
          Có dấu sao
        </label>
      </div>
      {state.loading ? (
        <PageLoader rows={6} />
      ) : !state.folders.length && !state.documents.length ? (
        <InlineState
          title="Thư mục đang trống"
          detail="Tạo tài liệu hoặc thư mục để bắt đầu"
        />
      ) : (
        <div className="overflow-hidden rounded-panel border border-border bg-surface">
          <ul>
            {state.folders.map((folder) => {
              const id = folder._id ?? folder.id ?? "";
              return (
                <li
                  key={id}
                  className="flex items-center justify-between gap-4 border-b border-border px-5 py-4"
                >
                  <button
                    onClick={() => openFolder(folder)}
                    className="min-w-0 truncate text-left text-[14px] font-semibold text-ink hover:text-brand"
                  >
                    {folder.name}
                  </button>
                  <Button
                    size="icon"
                    variant="ghost"
                    aria-label="Xóa thư mục"
                    onClick={() => setDeleteTarget({ id, type: "folder" })}
                  >
                    <Trash2 size={16} />
                  </Button>
                </li>
              );
            })}
            {state.documents.map((document) => {
              const id = document._id ?? document.id;
              return (
                <li
                  key={id}
                  className="flex flex-col gap-4 border-b border-border px-5 py-4 last:border-b-0 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <Link
                      href={`/tai-lieu/xem-truoc/${id}`}
                      className="block truncate text-[14px] font-semibold text-ink hover:text-brand"
                    >
                      {document.title || "Chưa đặt tên"}
                    </Link>
                    <p className="mt-1 text-[12px] text-ink-muted">
                      {document.content_format || "Tài liệu"} ·{" "}
                      {document.status || "draft"} ·{" "}
                      {document.visibility || "private"}
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label="Đánh dấu sao"
                      onClick={() => state.toggleStar(id)}
                    >
                      <Star
                        size={16}
                        fill={document.is_starred ? "currentColor" : "none"}
                      />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label="Bảo vệ tài liệu"
                      onClick={() => setLockTarget(id)}
                    >
                      <Lock size={16} />
                    </Button>
                    <Link
                      href={`/soan-thao/chinh-sua?tai-lieu=${id}`}
                      className="secondary-button"
                    >
                      Soạn thảo
                    </Link>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label="Xóa tài liệu"
                      onClick={() => setDeleteTarget({ id, type: "document" })}
                    >
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
      <CreateDocumentModal
        open={createOpen}
        close={() => setCreateOpen(false)}
        processing={state.processing}
        submit={state.createDocument}
      />
      <ImportDocumentModal
        open={importOpen}
        close={() => setImportOpen(false)}
        processing={state.processing}
        submit={state.importDocument}
      />
      <TextModal
        open={folderOpen}
        close={() => setFolderOpen(false)}
        processing={state.processing}
        title="Tạo thư mục"
        label="Tên thư mục"
        action="Tạo"
        submit={state.createFolder}
      />
      <TextModal
        open={Boolean(lockTarget)}
        close={() => setLockTarget("")}
        processing={state.processing}
        title="Bảo vệ tài liệu"
        label="Mật khẩu"
        action="Bảo vệ"
        secret
        submit={(password) => state.lock(lockTarget, password)}
      />
      <ConfirmDeleteModal
        open={Boolean(deleteTarget)}
        close={() => setDeleteTarget(null)}
        processing={state.processing}
        submit={remove}
      />
    </div>
  );
}
