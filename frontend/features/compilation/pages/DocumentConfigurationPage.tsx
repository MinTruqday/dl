"use client";

import { useState } from "react";
import InlineState from "@/shared/components/common/InlineState";
import PageHeader from "@/shared/components/layout/PageHeader";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
import { useDocumentConfiguration } from "../hooks/useDocumentConfiguration";
import DocumentWorkspaceNavigation from "../components/DocumentWorkspaceNavigation";

export default function ConfigurationPage() {
  const state = useDocumentConfiguration();
  useNoticeToast(state.notice);
  const [tag, setTag] = useState("");
  const [email, setEmail] = useState("");
  const [newOwner, setNewOwner] = useState("");
  const [confirmTransfer, setConfirmTransfer] = useState(false);
  if (state.loading && !state.documents.length) return <PageLoader rows={6} />;
  const addTag = () => {
    state.addTag(tag);
    setTag("");
  };
  const invite = async () => {
    if (await state.invite(email)) setEmail("");
  };
  const transfer = async () => {
    if (await state.transfer(newOwner)) {
      setConfirmTransfer(false);
      setNewOwner("");
    }
  };
  return (
    <div className="w-full">
      <DocumentWorkspaceNavigation />
      <PageHeader
        title="Cấu hình tài liệu"
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
            title="Không thể cập nhật tài liệu"
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
      {!state.documentId ? (
        <InlineState
          title={state.documents.length ? "Chọn tài liệu để cấu hình" : "Chưa có tài liệu"}
          detail={state.documents.length ? undefined : "Tạo tài liệu trước khi mở cấu hình"}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-6">
            <section className="rounded-panel border border-border bg-surface p-5">
              <h2 className="text-[17px] font-semibold text-ink">Phân loại</h2>
              <div className="mt-4 flex flex-wrap gap-2">
                {state.tags.map((item) => (
                  <button
                    key={item}
                    onClick={() => state.removeTag(item)}
                    className="rounded-control border border-border bg-surface-quiet px-3 py-2 text-[13px] text-ink"
                  >
                    {item} ×
                  </button>
                ))}
              </div>
              <div className="mt-4 flex gap-2">
                <input
                  value={tag}
                  onChange={(event) => setTag(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") addTag();
                  }}
                  className="apple-input min-w-0 flex-1"
                  maxLength={50}
                />
                <Button
                  variant="secondary"
                  disabled={!tag.trim() || Boolean(state.processing)}
                  onClick={addTag}
                >
                  Thêm thẻ
                </Button>
              </div>
              <label
                htmlFor="document-folder"
                className="mb-2 mt-5 block text-[13px] font-semibold text-ink"
              >
                Thư mục
              </label>
              <select
                id="document-folder"
                value={state.document?.folder_id ?? ""}
                onChange={(event) => state.moveFolder(event.target.value)}
                className="apple-input w-full"
              >
                <option value="">Thư mục gốc</option>
                {state.folders.map((folder) => (
                  <option
                    key={folder._id ?? folder.id}
                    value={folder._id ?? folder.id}
                  >
                    {folder.name}
                  </option>
                ))}
              </select>
            </section>
            <section className="rounded-panel border border-border bg-surface p-5">
              <h2 className="text-[17px] font-semibold text-ink">Dữ liệu AI</h2>
              <p className="mt-2 text-[13px] leading-relaxed text-ink-muted">
                Đồng bộ nội dung đã lưu để hỗ trợ tìm kiếm ngữ nghĩa và hỏi đáp
              </p>
              <Button
                className="mt-4"
                variant="secondary"
                disabled={Boolean(state.processing)}
                onClick={state.ingest}
              >
                {state.processing === "ingest"
                  ? "Đang đồng bộ"
                  : "Đồng bộ nội dung"}
              </Button>
            </section>
          </div>
          <div className="space-y-6">
            <section className="rounded-panel border border-border bg-surface p-5">
              <h2 className="text-[17px] font-semibold text-ink">
                Cộng tác viên
              </h2>
              <div className="mt-4 flex gap-2">
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="apple-input min-w-0 flex-1"
                />
                <Button
                  disabled={!email.trim() || Boolean(state.processing)}
                  onClick={invite}
                >
                  {state.processing === "invite" ? "Đang gửi" : "Mời"}
                </Button>
              </div>
              {state.collaborators.length ? (
                <ul className="mt-4 divide-y divide-border">
                  {state.collaborators.map((person) => {
                    const id = person._id ?? person.id;
                    return (
                      <li
                        key={id}
                        className="flex items-center justify-between gap-4 py-3"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-[14px] font-semibold text-ink">
                            {person.email || person.user_name || person.user_id}
                          </p>
                          <p className="mt-1 text-[12px] text-ink-muted">
                            {person.role || "Cộng tác viên"}
                          </p>
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={Boolean(state.processing)}
                          onClick={() => state.removeCollaborator(id)}
                        >
                          Thu hồi
                        </Button>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <p className="mt-4 text-[13px] text-ink-muted">
                  Chưa có cộng tác viên
                </p>
              )}
            </section>
            <section className="rounded-panel border border-danger/30 bg-surface p-5">
              <h2 className="text-[17px] font-semibold text-danger">
                Chuyển quyền sở hữu
              </h2>
              <p className="mt-2 text-[13px] leading-relaxed text-ink-muted">
                Bạn sẽ mất quyền quản lý tài liệu sau khi hoàn tất
              </p>
              <div className="mt-4 flex gap-2">
                <input
                  value={newOwner}
                  onChange={(event) => setNewOwner(event.target.value)}
                  className="apple-input min-w-0 flex-1"
                  placeholder="Mã người dùng"
                />
                <Button
                  variant="danger"
                  disabled={!newOwner.trim()}
                  onClick={() => setConfirmTransfer(true)}
                >
                  Chuyển
                </Button>
              </div>
            </section>
          </div>
        </div>
      )}
      <Modal isOpen={confirmTransfer} onClose={() => setConfirmTransfer(false)}>
        <ModalHeader>
          <ModalTitle>Xác nhận chuyển quyền</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-[14px] leading-relaxed text-ink-muted">
            Tài liệu sẽ thuộc quyền quản lý của người dùng {newOwner}
          </p>
        </ModalContent>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setConfirmTransfer(false)}>
            Hủy
          </Button>
          <Button
            variant="danger"
            disabled={state.processing === "transfer"}
            onClick={transfer}
          >
            {state.processing === "transfer" ? "Đang chuyển" : "Xác nhận"}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
