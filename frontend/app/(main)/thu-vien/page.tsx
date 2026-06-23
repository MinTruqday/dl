"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import {
  getBookmarkFoldersAPI,
  createBookmarkFolderAPI,
} from "@/features/content/services/document_bookmark.service";
import {
  createReadingListAPI,
  getMyReadingListsAPI as getReadingListsAPI,
} from "@/features/content/services/personal_library.service";
import {
  getPinnedDocumentsAPI,
  getReadingHistoryAPI,
  clearReadingHistoryAPI,
  deleteReadingHistoryItemAPI,
} from "@/features/content/services/reading_progress.service";
import { API_URL } from "@/features/auth/services/user_authentication.service";
import {
  LayoutGrid,
  List as ListIcon,
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
import { multiDocSynthesisAPI } from "@/features/ai/services/agentic_ai.service";
import ReactMarkdown from "react-markdown";

interface PinnedDocument {
  id: string;
  title: string;
  slug: string;
  cover_url?: string;
}

interface ContinueReading {
  document_id: string;
  document_title: string;
  document_slug: string;
  cover_url?: string;
  progress_percentage: number;
  last_read_at?: string;
}

interface BookmarkFolder {
  id: string;
  name: string;
  bookmark_ids: string[];
}

export default function LibraryPage() {
  const { user, isLoading: authLoading } = useAuth();
  const { showToast } = useToast();

  const [pinnedDocs, setPinnedDocs] = useState<PinnedDocument[]>([]);
  const [continueDocs, setContinueDocs] = useState<ContinueReading[]>([]);
  const [folders, setFolders] = useState<BookmarkFolder[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [readingLists, setReadingLists] = useState<any[]>([]);

  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [activeTab, setActiveTab] = useState<
    "history" | "folders" | "lists"
  >("history");

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createType, setCreateType] = useState<"folder" | "list">(
    "folder",
  );
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
      const [pinnedRes, foldersRes, historyRes, listsRes] =
        await Promise.all([
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
      setVisible(true);
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
      } else if (createType === "list") {
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

  if (authLoading || (loading && !visible)) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  const tabs = [
    { id: "history", label: "Lịch sử đọc" },
    { id: "folders", label: "Thư mục dấu trang" },
    { id: "lists", label: "Danh sách đọc" },
  ];

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 min-h-[calc(100dvh-var(--navbar-height))] font-sans text-zinc-900 selection:bg-zinc-900 selection:text-white">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <aside className="lg:col-span-3 space-y-4">
          <div className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5 space-y-4">
            <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">
              Quản lý thư viện
            </p>
            <nav className="flex flex-col gap-1">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id as any)}
                  className={`flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 ${
                    activeTab === t.id
                      ? "bg-zinc-900 text-white shadow-md"
                      : "text-zinc-500 hover:bg-zinc-50"
                  }`}
                >
                  <span>{t.label}</span>
                  {activeTab === t.id && <ChevronRight className="w-3.5 h-3.5 shrink-0" />}
                </button>
              ))}
              <div className="pt-2">
                <button
                  onClick={() => setIsSynthesisOpen(true)}
                  className="w-full flex items-center justify-center gap-2 h-11 text-xs font-bold text-white bg-black rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md mt-2"
                >
                  <Combine className="w-4 h-4" />
                  Tổng hợp AI
                </button>
              </div>
            </nav>
          </div>

          <div className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5">
            <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">
              Tài liệu đã ghim
            </p>
            <div className="flex flex-col gap-1">
              {pinnedDocs.length > 0 ? (
                pinnedDocs.map((doc, i) => (
                  <Link
                    key={`pinned-${doc.id || i}`}
                    href={`/document/${doc.slug}`}
                    className="flex gap-3 items-start px-2 py-2.5 rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 hover:bg-zinc-50 hover:shadow-sm"
                  >
                    <div className="w-10 h-14 bg-zinc-100 rounded-xl shrink-0 overflow-hidden relative">
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
                        <div className="w-full h-full flex items-center justify-center">
                          <FileText className="w-4 h-4 text-zinc-400 stroke-[1]" />
                        </div>
                      )}
                    </div>
                    <div className="space-y-0.5 flex-1 min-w-0">
                      <h4 className="text-xs font-semibold text-zinc-800 line-clamp-2 leading-snug">
                        {doc.title}
                      </h4>
                      <p className="text-[10px] font-medium text-zinc-400">
                        Truy cập nhanh
                      </p>
                    </div>
                  </Link>
                ))
              ) : (
                <div className="py-4 flex items-center justify-center">
                  <p className="text-[10px] font-medium text-zinc-400">
                    Chưa có tài liệu
                  </p>
                </div>
              )}
            </div>
          </div>
        </aside>

        <main className="lg:col-span-9 space-y-5">
          {activeTab === "history" && continueDocs.length > 0 && (
            <section className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <h2 className="text-sm font-bold text-zinc-900">Đang đọc</h2>
                <div className="flex items-center gap-2">
                  <div className="flex border border-zinc-200 bg-zinc-50 rounded-2xl overflow-hidden p-0.5 gap-0.5">
                    <button
                      onClick={() => setViewMode("grid")}
                      className={`p-1.5 rounded-xl transition-all duration-200 hover:scale-110 ${viewMode === "grid" ? "bg-white text-zinc-900 shadow-sm" : "bg-transparent text-zinc-400"}`}
                    >
                      <LayoutGrid className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => setViewMode("list")}
                      className={`p-1.5 rounded-xl transition-all duration-200 hover:scale-110 ${viewMode === "list" ? "bg-white text-zinc-900 shadow-sm" : "bg-transparent text-zinc-400"}`}
                    >
                      <ListIcon className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>

              <div
                className={`grid gap-5 ${
                  viewMode === "grid"
                    ? "grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
                    : "grid-cols-1"
                }`}
              >
                {continueDocs.map((doc) => (
                  <Link
                    key={doc.document_id}
                    href={`/document/${doc.document_slug}`}
                    className={`flex ${
                      viewMode === "grid" ? "flex-col" : "flex-row gap-5 p-3"
                    } border border-zinc-100 bg-white rounded-2xl overflow-hidden shadow-sm transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1 hover:shadow-md hover:border-zinc-200`}
                  >
                    <div
                      className={`${
                        viewMode === "grid"
                          ? "aspect-[2/3] w-full border-b border-zinc-100"
                          : "w-20 h-28 shrink-0 rounded-xl"
                      } bg-zinc-100 relative overflow-hidden`}
                    >
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
                        <div className="w-full h-full flex items-center justify-center bg-zinc-100">
                          <FileText className="w-8 h-8 text-zinc-300 stroke-[1]" />
                        </div>
                      )}
                      <div className="absolute bottom-0 left-0 w-full h-1 bg-zinc-200">
                        <div
                          className="h-full bg-black"
                          style={{ width: `${doc.progress_percentage}%` }}
                        />
                      </div>
                    </div>
                    <div
                      className={`${
                        viewMode === "grid" ? "p-3" : "flex-1 py-0.5"
                      } flex flex-col flex-1 gap-1.5`}
                    >
                      <h3
                        className={`${
                          viewMode === "grid" ? "text-xs" : "text-sm"
                        } font-semibold text-zinc-900 line-clamp-2 leading-snug`}
                      >
                        {doc.document_title}
                      </h3>
                      <div className="text-[10px] text-zinc-400 flex items-center gap-1">
                        <span className="truncate font-medium text-zinc-600">
                          Tiến độ đọc
                        </span>
                        <span className="text-zinc-200">•</span>
                        <span className="shrink-0 text-black font-bold">
                          {doc.progress_percentage}%
                        </span>
                      </div>
                      <div
                        className={`mt-auto pt-2 flex items-center justify-between ${
                          viewMode === "grid" ? "border-t border-zinc-50" : ""
                        }`}
                      >
                        <span className="text-[10px] font-bold text-zinc-900">
                          Đang đọc
                        </span>
                        <span className="text-[9px] font-bold text-zinc-500 bg-zinc-100 px-2.5 py-1 rounded-xl uppercase tracking-widest">
                          Tiếp tục
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {activeTab === "history" && (
            <section className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <h2 className="text-sm font-bold text-zinc-900">
                  Lịch sử đọc
                </h2>
                <div className="flex items-center gap-2">
                  <button
                    title="Xóa toàn bộ"
                    onClick={() => setIsClearModalOpen(true)}
                    className="p-1.5 rounded-xl text-zinc-400 hover:text-red-500 hover:bg-red-50 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <div className="flex border border-zinc-200 bg-zinc-50 rounded-2xl overflow-hidden p-0.5 gap-0.5">
                    <button
                      onClick={() => setViewMode("grid")}
                      className={`p-1.5 rounded-xl transition-all duration-200 hover:scale-110 ${viewMode === "grid" ? "bg-white text-zinc-900 shadow-sm" : "bg-transparent text-zinc-400"}`}
                    >
                      <LayoutGrid className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => setViewMode("list")}
                      className={`p-1.5 rounded-xl transition-all duration-200 hover:scale-110 ${viewMode === "list" ? "bg-white text-zinc-900 shadow-sm" : "bg-transparent text-zinc-400"}`}
                    >
                      <ListIcon className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>

              <div
                className={`grid gap-5 ${
                  viewMode === "grid"
                    ? "grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
                    : "grid-cols-1"
                }`}
              >
                {history.length > 0 ? (
                  history.map((item, idx) => (
                    <div
                      key={item.document_id + idx}
                      className={`relative group flex ${
                        viewMode === "grid" ? "flex-col" : "flex-row gap-5 p-3"
                      } border border-zinc-100 bg-white rounded-2xl overflow-hidden shadow-sm transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1 hover:shadow-md hover:border-zinc-200 ${
                        isDeletingHistory === item.document_id
                          ? "opacity-50"
                          : ""
                      }`}
                    >
                      <Link
                        href={`/document/${item.document_slug}`}
                        className={`${
                          viewMode === "grid"
                            ? "aspect-[2/3] w-full border-b border-zinc-100"
                            : "w-20 h-28 shrink-0 rounded-xl"
                        } bg-zinc-100 relative overflow-hidden block`}
                      >
                        {item.cover_url ? (
                          <img
                            src={
                              item.cover_url.startsWith("http")
                                ? item.cover_url
                                : `${API_URL}/storage/${item.cover_url}`
                            }
                            className="w-full h-full object-cover"
                            alt=""
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center bg-zinc-100">
                            <FileText className="w-8 h-8 text-zinc-300 stroke-[1]" />
                          </div>
                        )}
                        <div className="absolute bottom-0 left-0 w-full h-1 bg-zinc-200">
                          <div
                            className="h-full bg-black"
                            style={{
                              width: `${item.progress_percentage || 0}%`,
                            }}
                          />
                        </div>
                      </Link>
                      <div
                        className={`${
                          viewMode === "grid" ? "p-3" : "flex-1 py-0.5"
                        } flex flex-col flex-1 gap-1.5`}
                      >
                        <Link href={`/document/${item.document_slug}`}>
                          <h3
                            className={`${
                              viewMode === "grid" ? "text-xs" : "text-sm"
                            } font-semibold text-zinc-900 line-clamp-2 leading-snug group-hover:underline`}
                          >
                            {item.document_title}
                          </h3>
                        </Link>
                        <div className="text-[10px] text-zinc-400 flex items-center gap-1">
                          <span className="truncate font-medium text-zinc-600">
                            Tiến độ
                          </span>
                          <span className="text-zinc-200">•</span>
                          <span className="shrink-0 text-black font-bold">
                            {item.progress_percentage || 0}%
                          </span>
                        </div>
                        <div
                          className={`mt-auto pt-2 flex items-center justify-between ${
                            viewMode === "grid"
                              ? "border-t border-zinc-50"
                              : ""
                          }`}
                        >
                          <span className="text-[10px] font-bold text-zinc-900">
                            Đã xem
                          </span>
                          <Link href={`/document/${item.document_slug}`}>
                            <span className="text-[9px] font-bold text-zinc-500 bg-zinc-100 px-2.5 py-1 rounded-xl uppercase tracking-widest hover:bg-zinc-200 transition-colors">
                              Đọc lại
                            </span>
                          </Link>
                        </div>
                      </div>
                      <button
                        onClick={() =>
                          handleDeleteHistoryItem(item.document_id)
                        }
                        className="absolute top-2 right-2 p-1.5 bg-white border border-zinc-200 text-zinc-400 rounded-xl hover:text-red-500 hover:border-red-200 shadow-sm transition-colors z-10 opacity-0 group-hover:opacity-100"
                        title="Xóa khỏi lịch sử"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="col-span-full py-20 flex flex-col items-center justify-center border border-zinc-100 bg-zinc-50 rounded-2xl gap-3">
                    <FileText className="w-8 h-8 text-zinc-200 stroke-[1.5]" />
                    <p className="text-xs font-medium text-zinc-400">
                      Chưa có dữ liệu
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === "folders" && (
            <section className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <h2 className="text-sm font-bold text-zinc-900">
                  Thư mục lưu trữ
                </h2>
                <div className="flex items-center gap-2">
                  <button
                    title="Tạo thư mục"
                    onClick={() => {
                      setCreateType("folder");
                      setIsCreateModalOpen(true);
                    }}
                    className="p-1.5 rounded-xl text-zinc-500 hover:text-black hover:bg-zinc-100 transition-all"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="grid gap-5 grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                {folders.length > 0 ? (
                  folders.map((folder) => (
                    <Link
                      key={folder.id}
                      href={`/library/folder/${folder.id}`}
                      className="group flex flex-col border border-zinc-100 bg-white rounded-2xl overflow-hidden shadow-sm transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1 hover:shadow-md hover:border-zinc-200"
                    >
                      <div className="aspect-[2/3] w-full border-b border-zinc-100 bg-zinc-50 relative overflow-hidden flex items-center justify-center">
                        <FolderPlus className="w-12 h-12 text-zinc-300 stroke-[1]" />
                      </div>
                      <div className="p-3 flex flex-col flex-1 gap-1.5">
                        <h3 className="text-xs font-semibold text-zinc-900 line-clamp-2 leading-snug">
                          {folder.name}
                        </h3>
                        <div className="text-[10px] text-zinc-400 flex items-center gap-1">
                          <span className="truncate text-black font-medium">
                            Dấu trang
                          </span>
                        </div>
                        <div className="mt-auto pt-2 flex items-center justify-between border-t border-zinc-50">
                          <span className="text-[10px] font-bold text-zinc-900">
                            {folder.bookmark_ids?.length || 0} tài liệu
                          </span>
                          <span className="text-[9px] font-bold text-zinc-500 bg-zinc-100 px-2.5 py-1 rounded-xl uppercase tracking-widest hover:bg-zinc-200 transition-colors">
                            Mở
                          </span>
                        </div>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="col-span-full py-20 flex flex-col items-center justify-center border border-zinc-100 bg-zinc-50 rounded-2xl gap-3">
                    <FolderPlus className="w-8 h-8 text-zinc-200 stroke-[1.5]" />
                    <p className="text-xs font-medium text-zinc-400">
                      Chưa có dữ liệu
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === "lists" && (
            <section className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <h2 className="text-sm font-bold text-zinc-900">
                  Danh sách đọc
                </h2>
                <div className="flex items-center gap-2">
                  <button
                    title="Tạo danh sách"
                    onClick={() => {
                      setCreateType("list");
                      setIsCreateModalOpen(true);
                    }}
                    className="p-1.5 rounded-xl text-zinc-500 hover:text-black hover:bg-zinc-100 transition-all"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="grid gap-5 grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                {readingLists.length > 0 ? (
                  readingLists.map((list) => (
                    <Link
                      key={list._id}
                      href={`/collection/${list._id}`}
                      className="group flex flex-col border border-zinc-100 bg-white rounded-2xl overflow-hidden shadow-sm transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1 hover:shadow-md hover:border-zinc-200"
                    >
                      <div className="aspect-[2/3] w-full border-b border-zinc-100 bg-zinc-50 relative overflow-hidden flex flex-col items-center justify-center p-6 text-center">
                        {list.description ? (
                          <p className="text-[10px] font-medium text-zinc-400 italic line-clamp-6 group-hover:text-black transition-colors duration-500">
                            "{list.description}"
                          </p>
                        ) : (
                          <Layers className="w-12 h-12 text-zinc-300 stroke-[1]" />
                        )}
                      </div>
                      <div className="p-3 flex flex-col flex-1 gap-1.5">
                        <h3 className="text-xs font-semibold text-zinc-900 line-clamp-2 leading-snug">
                          {list.name}
                        </h3>
                        <div className="text-[10px] text-zinc-400 flex items-center gap-1">
                          <span className="truncate text-black font-medium">
                            {list.is_public ? "Công khai" : "Riêng tư"}
                          </span>
                        </div>
                        <div className="mt-auto pt-2 flex items-center justify-between border-t border-zinc-50">
                          <span className="text-[10px] font-bold text-zinc-900">
                            {list.documents?.length || 0} tài liệu
                          </span>
                          <span className="text-[9px] font-bold text-zinc-500 bg-zinc-100 px-2.5 py-1 rounded-xl uppercase tracking-widest hover:bg-zinc-200 transition-colors">
                            Mở
                          </span>
                        </div>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="col-span-full py-20 flex flex-col items-center justify-center border border-zinc-100 bg-zinc-50 rounded-2xl gap-3">
                    <Layers className="w-8 h-8 text-zinc-200 stroke-[1.5]" />
                    <p className="text-xs font-medium text-zinc-400">
                      Chưa có dữ liệu
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}

        </main>
      </div>

      <Modal
        isOpen={isClearModalOpen}
        onClose={() => !isClearing && setIsClearModalOpen(false)}
        className="max-w-sm bg-white/95 backdrop-blur-md rounded-3xl shadow-xl border border-zinc-100"
      >
        <ModalHeader className="border-b border-zinc-100 px-6 py-5">
          <ModalTitle className="text-sm font-bold text-black tracking-tight">Xóa toàn bộ lịch sử</ModalTitle>
        </ModalHeader>
        <ModalContent className="px-6 py-5">
          <p className="text-xs font-medium text-zinc-500 leading-relaxed">
            Bạn có chắc chắn muốn xóa toàn bộ lịch sử đọc sách? Hành động này sẽ
            xóa vĩnh viễn dữ liệu về tiến trình đọc của bạn.
          </p>
        </ModalContent>
        <ModalFooter className="px-6 py-5 border-t border-zinc-100 bg-zinc-50/50 rounded-b-3xl flex justify-end gap-3">
          <button
            onClick={() => setIsClearModalOpen(false)}
            disabled={isClearing}
            className="px-6 h-10 border border-zinc-200 bg-white text-xs font-bold text-black rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:bg-zinc-50 disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleClearHistory}
            disabled={isClearing}
            className="px-6 h-10 bg-black text-white text-xs font-bold rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isClearing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              "Xác nhận xóa"
            )}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => !isCreating && setIsCreateModalOpen(false)}
        className="max-w-md bg-white/95 backdrop-blur-md rounded-3xl shadow-xl border border-zinc-100"
      >
        <ModalHeader className="border-b border-zinc-100 px-6 py-5">
          <ModalTitle className="text-sm font-bold text-black tracking-tight">
            {createType === "folder"
              ? "Tạo thư mục lưu trữ"
              : "Tạo danh sách đọc"}
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="px-6 py-5 space-y-4">
          <div className="space-y-2">
            <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1">
              Tên gọi
            </label>
            <input
              type="text"
              value={
                createType === "folder" ? newFolderName : createListForm.name
              }
              onChange={(e) =>
                createType === "folder"
                  ? setNewFolderName(e.target.value)
                  : setCreateListForm({
                      ...createListForm,
                      name: e.target.value,
                    })
              }
              className="w-full h-11 bg-white border border-zinc-200 rounded-2xl px-4 text-sm font-medium focus:border-black focus:outline-none shadow-sm transition-all"
              placeholder=""
            />
          </div>
          {createType !== "folder" && (
            <div className="space-y-2">
              <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1">
                Mô tả tóm lược
              </label>
              <textarea
                value={createListForm.description}
                onChange={(e) =>
                  setCreateListForm({
                    ...createListForm,
                    description: e.target.value,
                  })
                }
                className="w-full min-h-[100px] p-4 bg-white border border-zinc-200 rounded-2xl text-sm font-medium focus:border-black focus:outline-none resize-none shadow-sm transition-all"
                placeholder=""
              />
            </div>
          )}
        </ModalContent>
        <ModalFooter className="px-6 py-5 border-t border-zinc-100 bg-zinc-50/50 rounded-b-3xl flex justify-end gap-3">
          <button
            onClick={() => setIsCreateModalOpen(false)}
            disabled={isCreating}
            className="px-6 h-10 border border-zinc-200 bg-white text-xs font-bold text-black rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:bg-zinc-50 disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleCreate}
            disabled={isCreating}
            className="px-6 h-10 bg-black text-white text-xs font-bold rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isCreating ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              "Xác nhận tạo"
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

interface LibraryAISynthesisModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableDocuments: any[];
}

function LibraryAISynthesisModal({
  isOpen,
  onClose,
  availableDocuments,
}: LibraryAISynthesisModalProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const { showToast } = useToast();

  if (!isOpen) return null;

  const handleSynthesize = async () => {
    if (selectedIds.length === 0) {
      showToast("Vui lòng chọn ít nhất một tài liệu", "info");
      return;
    }
    if (!query.trim()) {
      showToast("Vui lòng nhập câu hỏi tổng hợp", "info");
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      const data = await multiDocSynthesisAPI(selectedIds, query);
      setResult(data.synthesis);
    } catch (err: any) {
      showToast(err.message || "Tổng hợp thất bại", "error");
    } finally {
      setLoading(false);
    }
  };

  const toggleDoc = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    );
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white/95 backdrop-blur-md w-full max-w-5xl h-[85vh] border border-zinc-100 flex flex-col overflow-hidden rounded-3xl shadow-2xl">
        <div className="flex items-center justify-between px-8 py-5 border-b border-zinc-100 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-black rounded-2xl flex items-center justify-center shadow-sm">
              <Combine className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-bold uppercase tracking-widest text-black">
                Tổng hợp đa tài liệu AI
              </h3>
              <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest mt-0.5">
                Phân tích chéo dữ liệu từ thư viện cá nhân
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-zinc-400 hover:text-black hover:bg-zinc-100 rounded-xl transition-all">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          <div className="w-80 border-r border-zinc-100 bg-zinc-50/50 flex flex-col">
            <div className="p-5 border-b border-zinc-100">
              <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                Chọn tài liệu nguồn ({selectedIds.length})
              </span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {availableDocuments.map((doc) => (
                <button
                  key={doc.document_id || doc.id}
                  onClick={() => toggleDoc(doc.document_id || doc.id)}
                  className={`w-full flex items-start gap-3 p-3 text-left rounded-2xl border transition-all duration-200 ${
                    selectedIds.includes(doc.document_id || doc.id)
                      ? "bg-black text-white border-black shadow-md hover:scale-[1.02]"
                      : "bg-white text-black border-zinc-200 shadow-sm hover:scale-[1.02] hover:border-zinc-300"
                  }`}
                >
                  <FileText className={`w-4 h-4 mt-0.5 shrink-0 ${selectedIds.includes(doc.document_id || doc.id) ? "text-white" : "text-zinc-400"}`} />
                  <span className="text-xs font-semibold line-clamp-2 leading-tight">
                    {doc.document_title || doc.title}
                  </span>
                </button>
              ))}
              {availableDocuments.length === 0 && (
                <p className="text-[11px] text-zinc-400 text-center py-10 font-medium">
                  Không có tài liệu nào khả dụng để tổng hợp
                </p>
              )}
            </div>
          </div>

          <div className="flex-1 flex flex-col bg-white">
            <div className="p-6 border-b border-zinc-100">
              <div className="relative">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Nhập câu hỏi tổng hợp (ví dụ: 'Tìm điểm chung giữa các bài viết này')"
                  className="w-full h-14 pl-12 pr-32 bg-white border border-zinc-200 rounded-2xl focus:outline-none focus:border-black text-sm font-medium shadow-sm transition-all"
                  onKeyDown={(e) => e.key === "Enter" && handleSynthesize()}
                />
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
                <button
                  onClick={handleSynthesize}
                  disabled={loading || selectedIds.length === 0}
                  className="absolute right-2 top-1/2 -translate-y-1/2 h-10 px-5 bg-black text-white text-xs font-bold uppercase tracking-widest rounded-xl transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:hover:scale-100"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    "Tổng hợp"
                  )}
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-8 relative">
              {loading ? (
                <div className="h-full flex flex-col items-center justify-center gap-6">
                  <div className="relative">
                    <div className="w-16 h-16 bg-zinc-50 rounded-2xl flex items-center justify-center shadow-inner">
                      <Combine className="w-8 h-8 text-black animate-pulse" />
                    </div>
                    <Sparkles className="absolute -top-3 -right-3 w-6 h-6 text-zinc-400 animate-bounce" />
                  </div>
                  <div className="text-center space-y-2">
                    <p className="text-xs font-bold uppercase tracking-widest text-black">
                      Đang liên kết dữ liệu
                    </p>
                    <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                      Hệ thống đang quét nội dung từ {selectedIds.length} tài liệu...
                    </p>
                  </div>
                </div>
              ) : result ? (
                <div className="prose prose-zinc max-w-none text-sm leading-relaxed">
                  <div className="flex items-center gap-3 mb-8 pb-4 border-b border-zinc-100">
                    <div className="w-8 h-8 bg-black rounded-xl flex items-center justify-center shadow-sm">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <h4 className="text-xs font-bold uppercase tracking-widest text-black">
                      Báo cáo tổng hợp từ AI
                    </h4>
                  </div>
                  <ReactMarkdown>{result}</ReactMarkdown>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center opacity-40">
                  <Combine className="w-12 h-12 mb-4 text-zinc-300 stroke-[1.5]" />
                  <p className="text-xs font-bold text-zinc-400 uppercase tracking-widest max-w-sm">
                    Chọn các tài liệu nguồn và đặt câu hỏi để AI phân tích tổng hợp.
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
