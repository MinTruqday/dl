"use client";

import { useState } from "react";
import DocumentResults from "@/shared/components/documents/DocumentResults";
import InlineState from "@/shared/components/common/InlineState";
import PageHeader from "@/shared/components/layout/PageHeader";
import SegmentedTabs from "@/shared/components/navigation/SegmentedTabs";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
import { FolderList, ReadingListRows } from "../components/LibraryCollections";
import LibraryHistory from "../components/LibraryHistory";
import { useLibrary } from "../hooks/useLibrary";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";

type LibraryTab = "history" | "folders" | "lists";

export default function LibraryPage() {
  const [tab, setTab] = useState<LibraryTab>("history");
  const [createOpen, setCreateOpen] = useState(false);
  const [clearOpen, setClearOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isPublic, setIsPublic] = useState(true);
  const library = useLibrary();
  useNoticeToast(library.notice);

  if (library.loading) return <PageLoader rows={6} />;

  const submitCreate = async () => {
    if (!name.trim()) return;
    const success =
      tab === "folders"
        ? await library.createFolder(name)
        : await library.createList(name, description, isPublic);
    if (success) {
      setCreateOpen(false);
      setName("");
      setDescription("");
      setIsPublic(true);
    }
  };

  const clearHistory = async () => {
    const success = await library.clearHistory();
    if (success) setClearOpen(false);
  };

  return (
    <div className="w-full">
      <PageHeader
        title="Thư viện"
      />

      {library.error && (
        <div className="mb-6">
          <InlineState
            title="Một phần thư viện chưa sẵn sàng"
            detail={library.error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={library.reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}

      {library.pinned.length > 0 && (
        <section className="mb-9" aria-labelledby="pinned-title">
          <h2
            id="pinned-title"
            className="mb-4 text-[18px] font-semibold text-ink"
          >
            Đã ghim
          </h2>
          <DocumentResults documents={library.pinned} compact />
        </section>
      )}

      <div className="mb-5">
        <SegmentedTabs<LibraryTab>
          label="Nội dung thư viện"
          value={tab}
          onChange={setTab}
          tabs={[
            { id: "history", label: "Lịch sử" },
            { id: "folders", label: "Thư mục" },
            { id: "lists", label: "Danh sách" },
          ]}
        />
      </div>

      <section aria-labelledby="library-section-title">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2
              id="library-section-title"
              className="text-[18px] font-semibold text-ink"
            >
              {tab === "history"
                ? "Lịch sử"
                : tab === "folders"
                  ? "Thư mục"
                  : "Danh sách"}
            </h2>
            <p className="mt-1 text-[13px] text-ink-muted">
              {tab === "history"
                ? `${library.history.length} mục`
                : tab === "folders"
                  ? `${library.folders.length} mục`
                  : `${library.lists.length} mục`}
            </p>
          </div>
          {tab === "history" && library.history.length > 0 ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setClearOpen(true)}
              disabled={library.processing}
            >
              Xóa lịch sử
            </Button>
          ) : tab !== "history" ? (
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              {tab === "folders" ? "Tạo thư mục" : "Tạo danh sách"}
            </Button>
          ) : null}
        </div>

        {tab === "history" && (
          <LibraryHistory
            history={library.history}
            processing={library.processing}
            onDelete={library.deleteHistoryItem}
          />
        )}
        {tab === "folders" && (
          <FolderList
            folders={library.folders}
            processing={library.processing}
            onDelete={library.deleteFolder}
          />
        )}
        {tab === "lists" && <ReadingListRows lists={library.lists} />}
      </section>

      <Modal
        isOpen={createOpen}
        onClose={() => !library.processing && setCreateOpen(false)}
      >
        <ModalHeader>
          <ModalTitle>
            {tab === "folders" ? "Tạo thư mục" : "Tạo danh sách đọc"}
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-5">
            <div>
              <label
                htmlFor="collection-name"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Tên
              </label>
              <input
                id="collection-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="apple-input w-full"
                maxLength={100}
                autoFocus
              />
            </div>
            {tab === "lists" && (
              <>
                <div>
                  <label
                    htmlFor="collection-description"
                    className="mb-2 block text-[13px] font-semibold text-ink"
                  >
                    Mô tả
                  </label>
                  <textarea
                    id="collection-description"
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    className="apple-input min-h-24 w-full resize-y"
                    maxLength={500}
                  />
                </div>
                <label className="flex items-center gap-3 text-[13px] text-ink">
                  <input
                    type="checkbox"
                    checked={isPublic}
                    onChange={(event) => setIsPublic(event.target.checked)}
                    className="h-4 w-4 accent-[hsl(var(--brand))]"
                  />
                  Cho phép người khác xem danh sách
                </label>
              </>
            )}
          </div>
        </ModalContent>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => setCreateOpen(false)}
            disabled={library.processing}
          >
            Hủy
          </Button>
          <Button
            onClick={submitCreate}
            disabled={library.processing || !name.trim()}
          >
            {library.processing ? "Đang tạo" : "Tạo"}
          </Button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={clearOpen}
        onClose={() => !library.processing && setClearOpen(false)}
      >
        <ModalHeader>
          <ModalTitle>Xóa lịch sử đọc</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-[14px] leading-relaxed text-ink-muted">
            Toàn bộ lịch sử đọc và tiến độ đã lưu sẽ bị xóa khỏi tài khoản
          </p>
        </ModalContent>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => setClearOpen(false)}
            disabled={library.processing}
          >
            Hủy
          </Button>
          <Button
            variant="danger"
            onClick={clearHistory}
            disabled={library.processing}
          >
            {library.processing ? "Đang xóa" : "Xóa lịch sử"}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
