"use client";

import Link from "next/link";
import EmptyState from "@/shared/components/common/EmptyState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import InlineState from "@/shared/components/common/InlineState";
import PageHeader from "@/shared/components/layout/PageHeader";
import { useComposerDocuments } from "../hooks/useComposerDocuments";
import ComposerNavigation from "./ComposerNavigation";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
import { useState } from "react";

type ComposerDocumentListProps = {
  source: "drafts" | "trash";
};

function formatDate(value?: string) {
  if (!value) return "Chưa ghi nhận";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Chưa ghi nhận";
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export default function ComposerDocumentList({
  source,
}: ComposerDocumentListProps) {
  const state = useComposerDocuments(source);
  const { documents, loading, error, restoringId, processingId, reload, restore } = state;
  useNoticeToast(state.notice);
  const [renameTarget, setRenameTarget] = useState<{ id: string; title: string } | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; title: string } | null>(null);
  const isTrash = source === "trash";

  if (loading) return <PageLoader rows={5} />;

  return (
    <div className="w-full">
      <ComposerNavigation />
      <PageHeader
        title={isTrash ? "Thùng rác" : "Bản thảo"}
        actions={
          !isTrash && (
            <Link href="/soan-thao/khoi-tao" className="pill-button">
              Tạo tài liệu
            </Link>
          )
        }
        meta={`${documents.length} tài liệu`}
      />

      {error && (
        <div className="mb-6">
          <InlineState
            title="Không thể hoàn tất yêu cầu"
            detail={error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}

      {documents.length === 0 ? (
        <EmptyState
          text={isTrash ? "Thùng rác đang trống" : "Chưa có bản thảo"}
          actionLabel={isTrash ? undefined : "Tạo tài liệu"}
          actionHref={isTrash ? undefined : "/soan-thao/khoi-tao"}
        />
      ) : (
        <div className="overflow-hidden rounded-panel border border-border bg-surface">
          <div className="hidden min-h-11 grid-cols-[minmax(0,1fr)_12rem_15rem] items-center gap-4 border-b border-border bg-surface-quiet px-4 text-[12px] font-semibold text-ink-muted sm:grid">
            <span>Tài liệu</span>
            <span>Cập nhật</span>
            <span className="text-right">Thao tác</span>
          </div>
          <div className="divide-y divide-border">
            {documents.map((document) => {
              const id = document._id || document.id || "";
              return (
                <div
                  key={id}
                  className="grid min-h-16 gap-3 px-4 py-3 sm:grid-cols-[minmax(0,1fr)_12rem_15rem] sm:items-center sm:gap-4"
                >
                  <div className="min-w-0">
                    {isTrash ? (
                      <p className="truncate font-semibold text-ink">
                        {document.title || "Tài liệu chưa có tiêu đề"}
                      </p>
                    ) : (
                      <Link
                        href={`/soan-thao/chinh-sua?tai-lieu=${id}`}
                        className="block truncate font-semibold text-ink hover:text-brand"
                      >
                        {document.title || "Tài liệu chưa có tiêu đề"}
                      </Link>
                    )}
                    <p className="mt-1 text-[12px] text-ink-faint sm:hidden">
                      {formatDate(document.updated_at || document.created_at)}
                    </p>
                  </div>
                  <p className="hidden text-[13px] text-ink-muted sm:block">
                    {formatDate(document.updated_at || document.created_at)}
                  </p>
                  <div className="flex flex-wrap justify-start gap-1 sm:justify-end">
                    {isTrash ? (
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={restoringId === id}
                        onClick={() => restore(id)}
                      >
                        {restoringId === id ? "Đang khôi phục" : "Khôi phục"}
                      </Button>
                    ) : (
                      <>
                        <Link
                          href={`/soan-thao/chinh-sua?tai-lieu=${id}`}
                          className="inline-flex min-h-9 items-center rounded-control px-3 text-[13px] font-semibold text-brand hover:bg-brand-soft"
                        >
                          Mở
                        </Link>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={processingId === id}
                          onClick={() => setRenameTarget({ id, title: document.title || "" })}
                        >
                          Đổi tên
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-danger"
                          disabled={processingId === id}
                          onClick={() => setDeleteTarget({ id, title: document.title || "Tài liệu chưa có tiêu đề" })}
                        >
                          Xóa
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      <Modal isOpen={Boolean(renameTarget)} onClose={() => !processingId && setRenameTarget(null)}>
        <ModalHeader><ModalTitle>Đổi tên bản thảo</ModalTitle></ModalHeader>
        <ModalContent>
          <label htmlFor="draft-title" className="mb-2 block text-[13px] font-semibold text-ink">Tên tài liệu</label>
          <input
            id="draft-title"
            className="apple-input w-full"
            value={renameTarget?.title || ""}
            maxLength={300}
            onChange={(event) => setRenameTarget((target) => target ? { ...target, title: event.target.value } : target)}
            autoFocus
          />
        </ModalContent>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setRenameTarget(null)}>Hủy</Button>
          <Button
            disabled={!renameTarget?.title.trim() || Boolean(processingId)}
            onClick={async () => {
              if (renameTarget && await state.rename(renameTarget.id, renameTarget.title)) setRenameTarget(null);
            }}
          >
            Lưu
          </Button>
        </ModalFooter>
      </Modal>
      <Modal isOpen={Boolean(deleteTarget)} onClose={() => !processingId && setDeleteTarget(null)}>
        <ModalHeader><ModalTitle>Chuyển vào thùng rác?</ModalTitle></ModalHeader>
        <ModalContent>
          <p className="text-[14px] leading-relaxed text-ink-muted">
            “{deleteTarget?.title}” sẽ được chuyển vào thùng rác và có thể khôi phục sau.
          </p>
        </ModalContent>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setDeleteTarget(null)}>Hủy</Button>
          <Button
            variant="danger"
            disabled={Boolean(processingId)}
            onClick={async () => {
              if (deleteTarget && await state.remove(deleteTarget.id)) setDeleteTarget(null);
            }}
          >
            Xóa
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
