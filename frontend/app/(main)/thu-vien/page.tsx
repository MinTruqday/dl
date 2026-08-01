"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  getBookmarkFoldersAPI,
  createBookmarkFolderAPI,
} from "@/features/content/services/bookmark.service";
import {
  createReadingListAPI,
  getMyReadingListsAPI as getReadingListsAPI,
} from "@/features/content/services/library.service";
import {
  getPinnedDocumentsAPI,
  getReadingHistoryAPI,
  clearReadingHistoryAPI,
  deleteReadingHistoryItemAPI,
} from "@/features/content/services/reading.service";
import { API_URL } from "@/features/authentication/services/session.service";
import {
  LayoutGrid,
  List as ListIcon,
  List,
  Layers,
  FolderPlus,
  Loader2,
  FileText,
  Trash2,
  ChevronRight,
  Search,
  X,
  Combine,
  Sparkles,
  Plus,
} from "lucide-react";
import Link from "next/link";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
import { useToast } from "@/shared/contexts/ToastContext";
import EmptyState from "@/shared/components/common/EmptyState";

export default function LibraryPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();

  const [pinnedDocs, setPinnedDocs] = useState<any[]>([]);
  const [continueDocs, setContinueDocs] = useState<any[]>([]);
  const [folders, setFolders] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [readingLists, setReadingLists] = useState<any[]>([]);

  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [activeTab, setActiveTab] = useState<"history" | "folders" | "lists">(
    "history",
  );

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createType, setCreateType] = useState<"folder" | "list">("folder");
  const [newFolderName, setNewFolderName] = useState("");
  const [createListForm, setCreateListForm] = useState({
    name: "",
    description: "",
    is_public: true,
  });

  const [isCreating, setIsCreating] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);
  const [isDeletingHistory, setIsDeletingHistory] = useState<string | null>(
    null,
  );

  const fetchLibraryData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const [pinnedRes, foldersRes, historyRes, listsRes] = await Promise.all([
        getPinnedDocumentsAPI().catch(() => ({ data: [] })),
        getBookmarkFoldersAPI().catch(() => ({ data: [] })),
        getReadingHistoryAPI().catch(() => ({ data: [] })),
        getReadingListsAPI().catch(() => ({ data: [] })),
      ]);

      const historyData = historyRes?.data || historyRes || [];
      setPinnedDocs(pinnedRes?.data || pinnedRes || []);
      setFolders(foldersRes?.data || foldersRes || []);
      setHistory(historyData);
      setContinueDocs(
        historyData
          .filter(
            (item: any) =>
              item.progress_percentage > 0 && item.progress_percentage < 100,
          )
          .slice(0, 4),
      );
      setReadingLists(listsRes?.data || listsRes || []);
    } catch (error) {
      showToast("Không thể tải hệ thống kho lưu trữ", "error");
    } finally {
      setLoading(false);
    }
  }, [user, showToast]);

  useEffect(() => {
    if (user) fetchLibraryData();
  }, [user, fetchLibraryData]);

  const handleCreate = async () => {
    setIsCreating(true);
    try {
      if (createType === "folder") {
        if (!newFolderName.trim()) return;
        await createBookmarkFolderAPI(newFolderName.trim());
      } else {
        if (!createListForm.name.trim()) return;
        await createReadingListAPI({
          name: createListForm.name.trim(),
          description: createListForm.description.trim(),
          is_public: createListForm.is_public,
        });
      }
      await fetchLibraryData();
      setIsCreateModalOpen(false);
      setNewFolderName("");
      setCreateListForm({ name: "", description: "", is_public: true });
      showToast("Khởi tạo phân vùng lưu trữ hoàn tất", "success");
    } catch (err: any) {
      showToast("Không thể tạo phân vùng lưu trữ", "error");
    } finally {
      setIsCreating(false);
    }
  };

  const handleClearHistory = async () => {
    setIsClearing(true);
    try {
      await clearReadingHistoryAPI();
      setHistory([]);
      setContinueDocs([]);
      setIsClearModalOpen(false);
      showToast("Làm sạch lịch sử truy cập hoàn tất", "success");
    } catch (err: any) {
      showToast("Lỗi làm sạch lịch sử truy cập", "error");
    } finally {
      setIsClearing(false);
    }
  };

  const handleDeleteHistoryItem = async (documentId: string) => {
    setIsDeletingHistory(documentId);
    try {
      await deleteReadingHistoryItemAPI(documentId);
      setHistory((prev) =>
        prev.filter((item) => item.document_id !== documentId),
      );
      setContinueDocs((prev) =>
        prev.filter((item) => item.document_id !== documentId),
      );
      showToast("Xóa bản ghi lịch sử hoàn tất", "success");
    } catch (err: any) {
      showToast("Lỗi xóa bản ghi lịch sử", "error");
    } finally {
      setIsDeletingHistory(null);
    }
  };

  if (
    authLoading ||
    (loading &&
      history.length === 0 &&
      folders.length === 0 &&
      readingLists.length === 0 &&
      pinnedDocs.length === 0)
  ) {
    return (
      <div className="w-full max-w-[1200px] mx-auto px-6 md:px-0 py-6 min-h-[calc(100dvh-56px)] font-sans">
        <div className="flex flex-col lg:flex-row gap-8">
          <aside className="w-full md:w-[320px] shrink-0 space-y-6">
            <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 h-[250px] animate-pulse" />
            <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 h-[300px] animate-pulse" />
          </aside>
          <main className="flex-1 space-y-8 pt-6">
            <div className="h-8 w-48 bg-surface-quiet rounded-full mb-6 animate-pulse" />
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
              {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                <div key={i} className="bg-surface-quiet rounded-panel overflow-hidden animate-pulse flex flex-col">
                  <div className="bg-border aspect-[4/3] w-full" />
                  <div className="p-4 space-y-3">
                    <div className="h-3 w-1/3 bg-border rounded-full" />
                    <div className="h-4 w-full bg-border rounded-full" />
                    <div className="h-4 w-2/3 bg-border rounded-full" />
                  </div>
                </div>
              ))}
            </div>
          </main>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: "history", label: "Lịch sử đọc" },
    { id: "folders", label: "Thư mục dấu trang" },
    { id: "lists", label: "Danh sách đọc" },
  ];

  return (
    <div className="w-full h-full flex flex-col font-sans text-ink">
      <div className="flex flex-col lg:flex-row gap-8">
        <aside className="w-full md:w-[320px] shrink-0 space-y-6 sticky top-0 h-fit">
          <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6">
            <p className="text-[13px] font-medium text-ink-muted mb-4">
              Quản lý thư viện
            </p>
            <nav className="flex flex-col gap-1.5">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id as any)}
                  className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-control transition-colors ${activeTab === t.id ? "bg-white text-brand font-medium" : "text-ink hover:bg-border"}`}
                >
                  <span className="truncate text-left">{t.label}</span>
                  {activeTab === t.id && <ChevronRight className="w-4 h-4 shrink-0" />}
                </button>
              ))}
            </nav>
          </div>

          <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6">
            <h2 className="text-[20px] font-semibold text-ink">
              Tài liệu đã ghim
            </h2>
            <div className="flex flex-col gap-3">
              {pinnedDocs.length > 0 ? (
                pinnedDocs.map((doc, i) => (
                  <Link
                    key={`pinned-${doc.id || i}`}
                    href={`/tai-lieu/${doc.slug}`}
                    className="flex gap-4 items-center group p-2 -mx-2 rounded-panel hover:bg-white transition-colors"
                  >
                    <div className="w-12 h-12 bg-white rounded-control overflow-hidden shrink-0">
                      {doc.cover_url ? (
                        <img
                          src={
                            doc.cover_url.startsWith("http")
                              ? doc.cover_url
                              : `${API_URL}/tai-len/luu-tru/${doc.cover_url}`
                          }
                          className="w-full h-full object-cover"
                          alt={doc.title}
                        />
                      ) : (
                        <div className="w-full h-full bg-white" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-[15px] font-medium text-ink line-clamp-2 leading-[1.3] group-hover:text-brand transition-colors">
                        {doc.title}
                      </h4>
                    </div>
                  </Link>
                ))
              ) : (
                <div className="py-12 flex flex-col items-center justify-center bg-surface-quiet rounded-panel w-full text-center">
                  <p className="text-[15px] text-ink-muted">Chưa có dữ liệu</p>
                </div>
              )}
            </div>
          </div>
        </aside>

        <main className="flex-1 min-w-0 space-y-8 pt-6">
          {activeTab === "history" && continueDocs.length > 0 && (
            <section>
              <h2 className="text-[20px] font-semibold text-ink">
                Đang đọc
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {continueDocs.map((doc) => (
                  <Link
                    key={doc.document_id}
                    href={`/tai-lieu/${doc.document_slug}`}
                    className="flex flex-col bg-surface-quiet rounded-panel overflow-hidden transition-transform hover:scale-[1.02]"
                  >
                    <div className="aspect-[4/3] w-full bg-white relative overflow-hidden">
                      {doc.cover_url ? (
                        <img
                          src={
                            doc.cover_url.startsWith("http")
                              ? doc.cover_url
                              : `${API_URL}/tai-len/luu-tru/${doc.cover_url}`
                          }
                          className="w-full h-full object-cover"
                          alt={doc.document_title}
                        />
                      ) : (
                        <div className="w-full h-full bg-white" />
                      )}
                      <div className="absolute bottom-0 left-0 w-full h-1 bg-[rgba(0,0,0,0.1)]">
                        <div
                          className="h-full bg-brand"
                          style={{ width: `${doc.progress_percentage}%` }}
                        />
                      </div>
                    </div>
                    <div className="p-5 flex flex-col gap-2">
                      <h3 className="text-[17px] font-medium text-ink line-clamp-2 leading-snug">
                        {doc.document_title}
                      </h3>
                      <p className="text-[13px] text-ink-muted">
                        {doc.progress_percentage}% hoàn thành
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {activeTab === "history" && (
            <section>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-[20px] font-semibold text-ink">
                  Lịch sử
                </h2>
                <div className="flex items-center gap-4">
                  {history.length > 0 && (
                    <button
                      onClick={() => setIsClearModalOpen(true)}
                      className="text-[13px] text-brand hover:underline"
                    >
                      Xóa tất cả
                    </button>
                  )}
                  <div className="flex bg-border p-[2px] rounded-full shrink-0">
                    <button
                      onClick={() => setViewMode("grid")}
                      className={`p-1 rounded-full transition-colors ${viewMode === "grid" ? "bg-white text-brand" : "text-ink-muted hover:text-ink"}`}
                    >
                      <LayoutGrid className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setViewMode("list")}
                      className={`p-1 rounded-full transition-colors ${viewMode === "list" ? "bg-white text-brand" : "text-ink-muted hover:text-ink"}`}
                    >
                      <List className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>

              {history.length > 0 ? (
                <div
                  className={`grid gap-6 ${viewMode === "grid" ? "grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5" : "grid-cols-1"}`}
                >
                  {history.map((item, idx) => (
                    <div
                      key={item.document_id + idx}
                      className={`group relative flex ${
                        viewMode === "grid"
                          ? "flex-col"
                          : "flex-row gap-6 p-4 items-center"
                      } bg-surface-quiet rounded-panel overflow-hidden transition-transform hover:scale-[1.02] ${isDeletingHistory === item.document_id ? "opacity-50" : ""}`}
                    >
                      <Link
                        href={`/tai-lieu/${item.document_slug}`}
                        className={`${
                          viewMode === "grid"
                            ? "aspect-[4/3] w-full"
                            : "w-[120px] h-[120px] shrink-0 rounded-control"
                        } bg-white relative overflow-hidden`}
                      >
                        {item.cover_url ? (
                          <img
                            src={
                              item.cover_url.startsWith("http")
                                ? item.cover_url
                                : `${API_URL}/tai-len/luu-tru/${item.cover_url}`
                            }
                            alt={item.document_title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full bg-white" />
                        )}
                        <div className="absolute bottom-0 left-0 w-full h-1 bg-[rgba(0,0,0,0.1)]">
                          <div
                            className="h-full bg-brand"
                            style={{
                              width: `${item.progress_percentage || 0}%`,
                            }}
                          />
                        </div>
                      </Link>

                      <div
                        className={`${
                          viewMode === "grid" ? "p-5" : "flex-1"
                        } flex flex-col gap-2`}
                      >
                        <Link href={`/tai-lieu/${item.document_slug}`}>
                          <h3
                            className={`${
                              viewMode === "grid" ? "text-[17px]" : "text-[20px]"
                            } font-medium text-ink line-clamp-2 leading-snug`}
                          >
                            {item.document_title}
                          </h3>
                        </Link>
                        <p className="text-[13px] text-ink-muted">
                          {item.progress_percentage || 0}% hoàn thành
                        </p>
                      </div>

                      <button
                        onClick={() =>
                          handleDeleteHistoryItem(item.document_id)
                        }
                        className={`absolute ${viewMode === "grid" ? "top-2 right-2" : "top-1/2 -translate-y-1/2 right-4"} p-2 bg-white rounded-full text-ink-muted hover:text-danger opacity-0 group-hover:opacity-100 transition-opacity z-10 shadow-sm`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-24 flex flex-col items-center justify-center bg-surface-quiet rounded-panel w-full text-center">
                  <p className="text-[17px] text-ink-muted">Chưa có dữ liệu</p>
                </div>
              )}
            </section>
          )}

          {activeTab === "folders" && (
            <section>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-[20px] font-semibold text-ink">
                  Thư mục dấu trang
                </h2>
                <button
                  onClick={() => {
                    setCreateType("folder");
                    setIsCreateModalOpen(true);
                  }}
                  className="p-2 bg-brand rounded-full text-white hover:bg-brand-hover transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              {folders.length > 0 ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
                  {folders.map((folder) => (
                    <Link
                      key={folder.id}
                      href={`/library/folder/${folder.id}`}
                      className="flex flex-col bg-surface-quiet rounded-panel overflow-hidden transition-transform hover:scale-[1.02]"
                    >
                      <div className="aspect-[4/3] w-full bg-white flex items-center justify-center">
                        <FolderPlus className="w-12 h-12 text-brand" />
                      </div>
                      <div className="p-5 flex flex-col gap-2">
                        <h3 className="text-[17px] font-medium text-ink line-clamp-1">
                          {folder.name}
                        </h3>
                        <p className="text-[13px] text-ink-muted">
                          {folder.bookmark_ids?.length || 0} mục
                        </p>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="py-24 flex flex-col items-center justify-center bg-surface-quiet rounded-panel w-full text-center">
                  <p className="text-[17px] text-ink-muted">Chưa có dữ liệu</p>
                </div>
              )}
            </section>
          )}

          {activeTab === "lists" && (
            <section>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-[20px] font-semibold text-ink">
                  Danh sách đọc
                </h2>
                <button
                  onClick={() => {
                    setCreateType("list");
                    setIsCreateModalOpen(true);
                  }}
                  className="p-2 bg-brand rounded-full text-white hover:bg-brand-hover transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              {readingLists.length > 0 ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
                  {readingLists.map((list) => (
                    <Link
                      key={list._id}
                      href={`/collection/${list._id}`}
                      className="flex flex-col bg-surface-quiet rounded-panel overflow-hidden transition-transform hover:scale-[1.02]"
                    >
                      <div className="aspect-[4/3] w-full bg-white flex items-center justify-center">
                        <Layers className="w-12 h-12 text-brand" />
                      </div>
                      <div className="p-5 flex flex-col gap-2">
                        <h3 className="text-[17px] font-medium text-ink line-clamp-1">
                          {list.name}
                        </h3>
                        <p className="text-[13px] text-ink-muted">
                          {list.documents?.length || 0} tài liệu
                        </p>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="py-24 flex flex-col items-center justify-center bg-surface-quiet rounded-panel w-full text-center">
                  <p className="text-[17px] text-ink-muted">Chưa có dữ liệu</p>
                </div>
              )}
            </section>
          )}
        </main>
      </div>

      <Modal
        isOpen={isClearModalOpen}
        onClose={() => !isClearing && setIsClearModalOpen(false)}
      >
        <ModalHeader>
          <ModalTitle>
            Xóa lịch sử
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="text-[15px] text-ink-muted">
          Bạn có chắc chắn muốn xóa toàn bộ lịch sử đọc Hành động này không thể hoàn tác
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setIsClearModalOpen(false)}
            disabled={isClearing}
            className="px-4 py-2 rounded-full text-[15px] text-brand hover:bg-surface-quiet transition-colors font-medium"
          >
            Hủy
          </button>
          <button
            onClick={handleClearHistory}
            disabled={isClearing}
            className="px-4 py-2 bg-danger text-white rounded-full text-[15px] font-medium hover:bg-danger transition-colors"
          >
            {isClearing ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xóa"}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => !isCreating && setIsCreateModalOpen(false)}
      >
        <ModalHeader>
          <ModalTitle>
            {createType === "folder" ? "Tạo thư mục" : "Tạo danh sách đọc"}
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <input
            type="text"
            value={
              createType === "folder" ? newFolderName : createListForm.name
            }
            onChange={(e) =>
              createType === "folder"
                ? setNewFolderName(e.target.value)
                : setCreateListForm({ ...createListForm, name: e.target.value })
            }
            className="apple-input w-full"
            placeholder=""
          />
          {createType !== "folder" && (
            <textarea
              value={createListForm.description}
              onChange={(e) =>
                setCreateListForm({
                  ...createListForm,
                  description: e.target.value,
                })
              }
              className="apple-input w-full min-h-[100px] py-3 resize-none"
              placeholder=""
            />
          )}
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setIsCreateModalOpen(false)}
            disabled={isCreating}
            className="px-4 py-2 rounded-full text-[15px] text-brand hover:bg-surface-quiet transition-colors font-medium"
          >
            Hủy
          </button>
          <button
            onClick={handleCreate}
            disabled={isCreating}
            className="pill-button"
          >
            {isCreating ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              "Tạo mới"
            )}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
