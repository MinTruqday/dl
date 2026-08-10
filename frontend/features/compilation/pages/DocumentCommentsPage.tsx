"use client";

import { useState } from "react";
import InlineState from "@/shared/components/common/InlineState";
import PageHeader from "@/shared/components/layout/PageHeader";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";
import { useDocumentComments } from "../hooks/useDocumentComments";
import DocumentWorkspaceNavigation from "../components/DocumentWorkspaceNavigation";

export default function CommentsPage() {
  const state = useDocumentComments();
  useNoticeToast(state.notice);
  const [content, setContent] = useState("");
  const send = async () => {
    if (await state.reply(content)) setContent("");
  };
  if (state.loading && !state.documents.length) return <PageLoader rows={5} />;
  return (
    <div className="w-full">
      <DocumentWorkspaceNavigation />
      <PageHeader
        title="Bình luận"
        meta={
          <label className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center sm:gap-3">
            <span className="font-semibold text-ink">Tài liệu</span>
            <select
              value={state.documentId}
              onChange={(event) => state.setDocumentId(event.target.value)}
              className="apple-input w-full min-w-0 sm:min-w-64"
            >
              <option value="">Chọn tài liệu</option>
              {state.documents.map((document) => (
                <option
                  key={document._id ?? document.id}
                  value={document._id ?? document.id}
                >
                  {document.title || "Chưa đặt tên"}
                </option>
              ))}
            </select>
          </label>
        }
      />
      {state.error && (
        <div className="mb-6">
          <InlineState
            title="Không thể tải bình luận"
            detail={state.error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={state.loadComments}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}
      {!state.documentId ? (
        <InlineState
          title={state.documents.length ? "Chọn tài liệu để xem bình luận" : "Chưa có tài liệu"}
          detail={state.documents.length ? undefined : "Tạo tài liệu trước khi quản lý bình luận"}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-[17px] font-semibold text-ink">Phản hồi</h2>
              <span className="text-[12px] text-ink-muted">
                {state.comments.length} bình luận
              </span>
            </div>
            {state.loading ? (
              <PageLoader rows={4} />
            ) : state.comments.length ? (
              <ul className="overflow-hidden rounded-panel border border-border bg-surface">
                {state.comments.map((comment) => {
                  const id = comment._id ?? comment.id ?? "";
                  return (
                    <li
                      key={id}
                      className="border-b border-border p-5 last:border-b-0"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="text-[13px] font-semibold text-ink">
                            {comment.author?.full_name ||
                              comment.author?.username ||
                              "Người đọc"}
                          </p>
                          <p className="mt-1 text-[12px] text-ink-muted">
                            {new Date(comment.created_at).toLocaleString(
                              "vi-VN",
                            )}
                          </p>
                        </div>
                        <Button
                          size="sm"
                          variant="secondary"
                          disabled={state.processing}
                          onClick={() => state.resolve(id)}
                        >
                          Giải quyết
                        </Button>
                      </div>
                      <p className="mt-4 whitespace-pre-wrap text-[14px] leading-relaxed text-ink">
                        {comment.content}
                      </p>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <InlineState
                title="Chưa có bình luận"
              />
            )}
          </section>
          <aside>
            <h2 className="mb-3 text-[17px] font-semibold text-ink">
              Thêm phản hồi
            </h2>
            <div className="rounded-panel border border-border bg-surface p-5">
              <label
                htmlFor="comment-content"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Nội dung
              </label>
              <textarea
                id="comment-content"
                value={content}
                onChange={(event) => setContent(event.target.value)}
                className="apple-input min-h-32 w-full resize-y"
                maxLength={2000}
              />
              <Button
                className="mt-4 w-full"
                disabled={!content.trim() || state.processing}
                onClick={send}
              >
                {state.processing ? "Đang gửi" : "Gửi bình luận"}
              </Button>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
