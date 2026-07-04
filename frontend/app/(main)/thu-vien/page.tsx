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
import { multiDocSynthesisAPI } from "@/features/agentic_ai/services/interaction.service";
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
import ReactMarkdown from "react-markdown";
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
  const [isSynthesisOpen, setIsSynthesisOpen] = useState(false);

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
      showToast("Không thể kết nối tới kho lưu trữ", "error");
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
      showToast("Khởi tạo thành công", "success");
    } catch (err: any) {
      showToast("Lỗi khởi tạo", "error");
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
      showToast("Đã làm sạch lịch sử", "success");
    } catch (err: any) {
      showToast("Lỗi làm sạch", "error");
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
      showToast("Đã xóa mục lịch sử", "success");
    } catch (err: any) {
      showToast("Lỗi xóa mục", "error");
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
      <div className="w-full max-w-[1200px] mx-auto px-6 py-6 min-h-[calc(100dvh-56px)] font-sans">
        <div className="flex flex-col lg:flex-row gap-8">
          <aside className="w-full md:w-[320px] shrink-0 space-y-6">
            <div className="bg-[#F5F5F7] rounded-[18px] p-6 h-[250px] animate-pulse" />
            <div className="bg-[#F5F5F7] rounded-[18px] p-6 h-[300px] animate-pulse" />
          </aside>
          <main className="flex-1 space-y-8 pt-6">
            <div className="h-8 w-48 bg-[#F5F5F7] rounded-full mb-6 animate-pulse" />
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
              {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                <div key={i} className="bg-[#F5F5F7] rounded-[18px] overflow-hidden animate-pulse flex flex-col">
                  <div className="bg-[#D2D2D7] aspect-[4/3] w-full" />
                  <div className="p-4 space-y-3">
                    <div className="h-3 w-1/3 bg-[#D2D2D7] rounded-full" />
                    <div className="h-4 w-full bg-[#D2D2D7] rounded-full" />
                    <div className="h-4 w-2/3 bg-[#D2D2D7] rounded-full" />
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
    <div className="w-full max-w-[1200px] mx-auto px-6 py-6 min-h-[calc(100dvh-56px)] font-sans text-[#1D1D1F]">
      <div className="flex flex-col lg:flex-row gap-8">
        <aside className="w-full md:w-[320px] shrink-0 space-y-6 sticky top-0 h-fit">
          <div className="bg-[#F5F5F7] rounded-[18px] p-6">
            <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
              Quản lý thư viện
            </p>
            <nav className="flex flex-col gap-1.5">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id as any)}
                  className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${activeTab === t.id ? "bg-white text-[#0071E3] font-medium" : "text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}
                >
                  <span className="truncate text-left">{t.label}</span>
                  {activeTab === t.id && <ChevronRight className="w-4 h-4 shrink-0" />}
                </button>
              ))}
              <div className="pt-4 mt-2">
                <button
                  onClick={() => setIsSynthesisOpen(true)}
                  className="pill-button w-full flex items-center justify-center gap-2"
                >
                  Tổng hợp AI
                </button>
              </div>
            </nav>
          </div>

          <div className="bg-[#F5F5F7] rounded-[18px] p-6">
            <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
              Tài liệu đã ghim
            </h2>
            <div className="flex flex-col gap-3">
              {pinnedDocs.length > 0 ? (
                pinnedDocs.map((doc, i) => (
                  <Link
                    key={`pinned-${doc.id || i}`}
                    href={`/document/${doc.slug}`}
                    className="flex gap-4 items-center group p-2 -mx-2 rounded-[12px] hover:bg-white transition-colors"
                  >
                    <div className="w-12 h-12 bg-white rounded-[8px] overflow-hidden shrink-0">
                      {doc.cover_url ? (
                        <img
                          src={
                            doc.cover_url.startsWith("http")
                              ? doc.cover_url
                              : `${API_URL}/storage/${doc.cover_url}`
                          }
                          className="w-full h-full object-cover"
                          alt={doc.title}
                        />
                      ) : (
                        <div className="w-full h-full bg-white" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-[15px] font-medium text-[#1D1D1F] line-clamp-2 leading-[1.3] group-hover:text-[#0071E3] transition-colors">
                        {doc.title}
                      </h4>
                    </div>
                  </Link>
                ))
              ) : (
                <div className="py-12 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] w-full text-center">
                  <p className="text-[15px] text-[#6E6E73]">Chưa có dữ liệu</p>
                </div>
              )}
            </div>
          </div>
        </aside>

        <main className="flex-1 min-w-0 space-y-8 pt-6">
          {activeTab === "history" && continueDocs.length > 0 && (
            <section>
              <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
                Đang đọc
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {continueDocs.map((doc) => (
                  <Link
                    key={doc.document_id}
                    href={`/document/${doc.document_slug}`}
                    className="flex flex-col bg-[#F5F5F7] rounded-[18px] overflow-hidden transition-transform hover:scale-[1.02]"
                  >
                    <div className="aspect-[4/3] w-full bg-white relative overflow-hidden">
                      {doc.cover_url ? (
                        <img
                          src={
                            doc.cover_url.startsWith("http")
                              ? doc.cover_url
                              : `${API_URL}/storage/${doc.cover_url}`
                          }
                          className="w-full h-full object-cover"
                          alt={doc.document_title}
                        />
                      ) : (
                        <div className="w-full h-full bg-white" />
                      )}
                      <div className="absolute bottom-0 left-0 w-full h-1 bg-[rgba(0,0,0,0.1)]">
                        <div
                          className="h-full bg-[#0071E3]"
                          style={{ width: `${doc.progress_percentage}%` }}
                        />
                      </div>
                    </div>
                    <div className="p-5 flex flex-col gap-2">
                      <h3 className="text-[17px] font-medium text-[#1D1D1F] line-clamp-2 leading-snug">
                        {doc.document_title}
                      </h3>
                      <p className="text-[13px] text-[#6E6E73]">
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
                <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
                  Lịch sử
                </h2>
                <div className="flex items-center gap-4">
                  {history.length > 0 && (
                    <button
                      onClick={() => setIsClearModalOpen(true)}
                      className="text-[13px] text-[#0071E3] hover:underline"
                    >
                      Xóa tất cả
                    </button>
                  )}
                  <div className="flex bg-[#E8E8ED] p-[2px] rounded-full shrink-0">
                    <button
                      onClick={() => setViewMode("grid")}
                      className={`p-1 rounded-full transition-colors ${viewMode === "grid" ? "bg-white text-[#0071E3]" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
                    >
                      <LayoutGrid className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setViewMode("list")}
                      className={`p-1 rounded-full transition-colors ${viewMode === "list" ? "bg-white text-[#0071E3]" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
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
                      } bg-[#F5F5F7] rounded-[18px] overflow-hidden transition-transform hover:scale-[1.02] ${isDeletingHistory === item.document_id ? "opacity-50" : ""}`}
                    >
                      <Link
                        href={`/document/${item.document_slug}`}
                        className={`${
                          viewMode === "grid"
                            ? "aspect-[4/3] w-full"
                            : "w-[120px] h-[120px] shrink-0 rounded-[10px]"
                        } bg-white relative overflow-hidden`}
                      >
                        {item.cover_url ? (
                          <img
                            src={
                              item.cover_url.startsWith("http")
                                ? item.cover_url
                                : `${API_URL}/storage/${item.cover_url}`
                            }
                            alt={item.document_title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full bg-white" />
                        )}
                        <div className="absolute bottom-0 left-0 w-full h-1 bg-[rgba(0,0,0,0.1)]">
                          <div
                            className="h-full bg-[#0071E3]"
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
                        <Link href={`/document/${item.document_slug}`}>
                          <h3
                            className={`${
                              viewMode === "grid" ? "text-[17px]" : "text-[20px]"
                            } font-medium text-[#1D1D1F] line-clamp-2 leading-snug`}
                          >
                            {item.document_title}
                          </h3>
                        </Link>
                        <p className="text-[13px] text-[#6E6E73]">
                          {item.progress_percentage || 0}% hoàn thành
                        </p>
                      </div>

                      <button
                        onClick={() =>
                          handleDeleteHistoryItem(item.document_id)
                        }
                        className={`absolute ${viewMode === "grid" ? "top-2 right-2" : "top-1/2 -translate-y-1/2 right-4"} p-2 bg-white rounded-full text-[#6E6E73] hover:text-[#FF3B30] opacity-0 group-hover:opacity-100 transition-opacity z-10 shadow-sm`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-24 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] w-full text-center">
                  <p className="text-[17px] text-[#6E6E73]">Chưa có dữ liệu</p>
                </div>
              )}
            </section>
          )}

          {activeTab === "folders" && (
            <section>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
                  Thư mục dấu trang
                </h2>
                <button
                  onClick={() => {
                    setCreateType("folder");
                    setIsCreateModalOpen(true);
                  }}
                  className="p-2 bg-[#0071E3] rounded-full text-white hover:bg-[#0055C6] transition-colors"
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
                      className="flex flex-col bg-[#F5F5F7] rounded-[18px] overflow-hidden transition-transform hover:scale-[1.02]"
                    >
                      <div className="aspect-[4/3] w-full bg-white flex items-center justify-center">
                        <FolderPlus className="w-12 h-12 text-[#0071E3]" />
                      </div>
                      <div className="p-5 flex flex-col gap-2">
                        <h3 className="text-[17px] font-medium text-[#1D1D1F] line-clamp-1">
                          {folder.name}
                        </h3>
                        <p className="text-[13px] text-[#6E6E73]">
                          {folder.bookmark_ids?.length || 0} mục
                        </p>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="py-24 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] w-full text-center">
                  <p className="text-[17px] text-[#6E6E73]">Chưa có dữ liệu</p>
                </div>
              )}
            </section>
          )}

          {activeTab === "lists" && (
            <section>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
                  Danh sách đọc
                </h2>
                <button
                  onClick={() => {
                    setCreateType("list");
                    setIsCreateModalOpen(true);
                  }}
                  className="p-2 bg-[#0071E3] rounded-full text-white hover:bg-[#0055C6] transition-colors"
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
                      className="flex flex-col bg-[#F5F5F7] rounded-[18px] overflow-hidden transition-transform hover:scale-[1.02]"
                    >
                      <div className="aspect-[4/3] w-full bg-white flex items-center justify-center">
                        <Layers className="w-12 h-12 text-[#0071E3]" />
                      </div>
                      <div className="p-5 flex flex-col gap-2">
                        <h3 className="text-[17px] font-medium text-[#1D1D1F] line-clamp-1">
                          {list.name}
                        </h3>
                        <p className="text-[13px] text-[#6E6E73]">
                          {list.documents?.length || 0} tài liệu
                        </p>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="py-24 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] w-full text-center">
                  <p className="text-[17px] text-[#6E6E73]">Chưa có dữ liệu</p>
                </div>
              )}
            </section>
          )}
        </main>
      </div>

      <Modal
        isOpen={isClearModalOpen}
        onClose={() => !isClearing && setIsClearModalOpen(false)}
        className="max-w-sm rounded-[18px] bg-[#F5F5F7] p-0 border-none"
      >
        <ModalHeader className="p-6">
          <ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">
            Xóa lịch sử
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="px-6 pb-6 text-[15px] text-[#6E6E73]">
          Bạn có chắc chắn muốn xóa toàn bộ lịch sử đọc Hành động này không thể hoàn tác
        </ModalContent>
        <ModalFooter className="px-6 py-4 flex justify-end gap-3 bg-white rounded-b-[18px]">
          <button
            onClick={() => setIsClearModalOpen(false)}
            disabled={isClearing}
            className="px-4 py-2 rounded-full text-[15px] text-[#0071E3] hover:bg-[#F5F5F7] transition-colors font-medium"
          >
            Hủy
          </button>
          <button
            onClick={handleClearHistory}
            disabled={isClearing}
            className="px-4 py-2 bg-[#FF3B30] text-white rounded-full text-[15px] font-medium hover:bg-[#D70015] transition-colors"
          >
            {isClearing ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xóa"}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => !isCreating && setIsCreateModalOpen(false)}
        className="max-w-md rounded-[18px] bg-[#F5F5F7] p-0 border-none"
      >
        <ModalHeader className="p-6">
          <ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">
            {createType === "folder" ? "Tạo thư mục" : "Tạo danh sách đọc"}
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="px-6 space-y-4">
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
        <ModalFooter className="px-6 py-4 flex justify-end gap-3 bg-white rounded-b-[18px]">
          <button
            onClick={() => setIsCreateModalOpen(false)}
            disabled={isCreating}
            className="px-4 py-2 rounded-full text-[15px] text-[#0071E3] hover:bg-[#F5F5F7] transition-colors font-medium"
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

      <LibraryAISynthesisModal
        isOpen={isSynthesisOpen}
        onClose={() => setIsSynthesisOpen(false)}
        availableDocuments={[
          ...pinnedDocs,
          ...continueDocs,
          ...history.slice(0, 20),
        ]}
      />
    </div>
  );
}

function LibraryAISynthesisModal({
  isOpen,
  onClose,
  availableDocuments,
}: {
  isOpen: boolean;
  onClose: () => void;
  availableDocuments: any[];
}) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const { showToast } = useToast();

  if (!isOpen) return null;

  const handleSynthesize = async () => {
    if (selectedIds.length === 0)
      return showToast("Chọn ít nhất một tài liệu", "info");
    if (!query.trim()) return showToast("Nhập câu hỏi tổng hợp", "info");
    setLoading(true);
    setResult(null);
    try {
      const data = await multiDocSynthesisAPI(selectedIds, query);
      setResult(data.synthesis);
    } catch (err: any) {
      showToast("Tổng hợp thất bại", "error");
    } finally {
      setLoading(false);
    }
  };

  const toggleDoc = (id: string) =>
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    );

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[rgba(0,0,0,0.4)] p-6">
      <div className="bg-[#F5F5F7] w-full max-w-5xl h-[85vh] rounded-[18px] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-8 py-4 bg-white border-b border-[#D2D2D7]">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-[#0071E3] rounded-full flex items-center justify-center">
              <Combine className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
                Tổng hợp AI
              </h2>
              <p className="text-[13px] text-[#6E6E73]">
                Phân tích dữ liệu từ thư viện cá nhân
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-[#6E6E73] hover:bg-[#F5F5F7] rounded-full transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          <div className="w-[320px] bg-white border-r border-[#D2D2D7] flex flex-col">
            <div className="p-4 border-b border-[#D2D2D7]">
              <span className="text-[13px] font-medium text-[#6E6E73]">
                Chọn tài liệu ({selectedIds.length})
              </span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-2 hide-scrollbar">
              {availableDocuments.map((doc) => (
                <button
                  key={doc.document_id || doc.id}
                  onClick={() => toggleDoc(doc.document_id || doc.id)}
                  className={`w-full flex items-center gap-3 p-3 rounded-[12px] transition-colors text-left ${selectedIds.includes(doc.document_id || doc.id) ? "bg-[#0071E3] text-white" : "bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}
                >
                  <FileText className="w-5 h-5 shrink-0" />
                  <span className="text-[14px] font-medium line-clamp-2">
                    {doc.document_title || doc.title}
                  </span>
                </button>
              ))}
              {availableDocuments.length === 0 && (
                <p className="text-[13px] text-[#6E6E73] text-center py-10">
                  Không có tài liệu
                </p>
              )}
            </div>
          </div>

          <div className="flex-1 flex flex-col bg-[#F5F5F7]">
            <div className="p-6 bg-white border-b border-[#D2D2D7]">
              <div className="relative flex items-center">
                <Search className="absolute left-4 w-5 h-5 text-[#6E6E73]" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSynthesize()}
                  placeholder=""
                  className="w-full bg-[#F5F5F7] border border-transparent rounded-[980px] pl-12 pr-[120px] py-3 text-[15px] focus:outline-none focus:border-[#D2D2D7]"
                />
                <button
                  onClick={handleSynthesize}
                  disabled={loading || selectedIds.length === 0}
                  className="absolute right-2 pill-button h-auto py-2 px-6 disabled:opacity-50"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    "Tổng hợp"
                  )}
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-8 relative">
              {loading ? (
                <div className="h-full flex flex-col items-center justify-center">
                  <Combine className="w-12 h-12 text-[#0071E3] animate-pulse mb-4" />
                  <p className="text-[15px] text-[#6E6E73]">
                    Đang phân tích {selectedIds.length} tài liệu
                  </p>
                </div>
              ) : result ? (
                <div className="bg-white p-8 rounded-[18px]">
                  <ReactMarkdown className="prose prose-zinc max-w-none text-[15px] leading-relaxed">
                    {result}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <Sparkles className="w-12 h-12 text-[#D2D2D7] mb-4" />
                  <p className="text-[15px] text-[#6E6E73]">
                    Chọn tài liệu và đặt câu hỏi để nhận tổng hợp từ AI
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
