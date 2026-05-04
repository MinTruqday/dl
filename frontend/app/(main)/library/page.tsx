"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  getBookmarkFoldersAPI,
  createBookmarkFolderAPI,
  getPinnedDocumentsAPI,
  getContinueReadingAPI,
  getReadingHistoryAPI,
  clearReadingHistoryAPI,
  deleteReadingHistoryItemAPI,
  getReadingListsAPI,
  createReadingListAPI,
  getMySeriesAPI,
  createSeriesAPI,
} from "@/services/read.service";
import { API_URL } from "@/services/auth.service";
import {
  LayoutGrid,
  List as ListIcon,
  Layers,
  FolderPlus,
  Share2,
  Loader2,
  Clock,
  Bookmark,
  Pin,
  Plus,
  FileText,
  Trash2,
  ChevronRight,
  User as UserIcon,
  Search,
} from "lucide-react";
import Link from "next/link";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";
import { useToast } from "@/contexts/ToastContext";

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
  const [series, setSeries] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [activeTab, setActiveTab] = useState<
    "overview" | "history" | "folders" | "lists" | "series"
  >("overview");
  
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createType, setCreateType] = useState<"folder" | "list" | "series">("folder");
  const [newFolderName, setNewFolderName] = useState("");
  const [createListForm, setCreateListForm] = useState({
    name: "",
    description: "",
    is_public: true,
  });
  
  const [isCreating, setIsCreating] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);
  const [isDeletingHistory, setIsDeletingHistory] = useState<string | null>(null);

  const canManageSeries = useMemo(() => {
    const role = user?.role?.toLowerCase() || "";
    return ["author", "moderator", "admin"].includes(role);
  }, [user]);

  const fetchLibraryData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const [pinnedRes, continueRes, foldersRes, historyRes, listsRes, seriesRes] = await Promise.all([
        getPinnedDocumentsAPI().catch(() => ({ data: [] })),
        getContinueReadingAPI().catch(() => ({ data: [] })),
        getBookmarkFoldersAPI().catch(() => ({ data: [] })),
        getReadingHistoryAPI().catch(() => ({ data: [] })),
        getReadingListsAPI().catch(() => ({ data: [] })),
        canManageSeries
          ? getMySeriesAPI().catch(() => ({ data: [] }))
          : Promise.resolve({ data: [] }),
      ]);

      setPinnedDocs(pinnedRes?.data || pinnedRes || []);
      setContinueDocs(continueRes?.data || continueRes || []);
      setFolders(foldersRes?.data || foldersRes || []);
      setHistory(historyRes?.data || historyRes || []);
      setReadingLists(listsRes?.data || listsRes || []);
      setSeries(seriesRes?.data || seriesRes || []);
    } catch (error) {
      showToast("Không thể kết nối tới kho lưu trữ", "error");
    } finally {
      setLoading(false);
      setVisible(true);
    }
  }, [user, canManageSeries, showToast]);

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
      } else if (createType === "series") {
        if (!createListForm.name.trim()) return;
        await createSeriesAPI({
          title: createListForm.name.trim(),
          description: createListForm.description.trim(),
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
      setHistory((prev) => prev.filter((item) => item.document_id !== documentId));
      setContinueDocs((prev) => prev.filter((item) => item.document_id !== documentId));
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
    { id: "overview", label: "Tổng quan" },
    { id: "history", label: "Lịch sử đọc" },
    { id: "folders", label: "Thư mục lưu trữ" },
    { id: "lists", label: "Danh sách đọc" },
    ...(canManageSeries ? [{ id: "series", label: "Chuỗi tri thức" }] : []),
  ];

  return (
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <div className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-black">Thư viện</h1>
          <p className="text-zinc-500 text-sm font-medium">
            Quản lý tài liệu và kho lưu trữ tri thức cá nhân
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex border border-zinc-200 bg-white rounded-none overflow-x-auto no-scrollbar max-w-full">
            {tabs.map((t, i) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id as any)}
                className={`px-4 py-2 text-xs font-medium transition-colors duration-150 shrink-0 ${
                  i !== tabs.length - 1 ? "border-r border-zinc-200" : ""
                } ${
                  activeTab === t.id
                    ? "bg-zinc-100 text-black"
                    : "text-zinc-500 hover:text-black hover:bg-zinc-50"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="flex border border-zinc-200 bg-white rounded-none">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-2 transition-colors ${viewMode === "grid" ? "bg-zinc-100 text-black" : "text-zinc-500 hover:text-black hover:bg-zinc-50"}`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <div className="w-px bg-zinc-200" />
            <button
              onClick={() => setViewMode("list")}
              className={`p-2 transition-colors ${viewMode === "list" ? "bg-zinc-100 text-black" : "text-zinc-500 hover:text-black hover:bg-zinc-50"}`}
            >
              <ListIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div className="lg:col-span-9 space-y-12">
          {activeTab === "overview" && (
            <>
              <section className="space-y-6">
                <div className="flex items-center justify-between border-b border-zinc-200 pb-3">
                  <h2 className="text-sm font-semibold text-black flex items-center gap-2">
                    <Clock className="w-4 h-4" /> Đang đọc
                  </h2>
                  <button
                    onClick={() => setActiveTab("history")}
                    className="text-xs font-medium text-zinc-500 hover:text-black transition-colors"
                  >
                    Xem toàn bộ lịch sử
                  </button>
                </div>

                {continueDocs.length > 0 ? (
                  <div className={viewMode === "grid" ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4" : "flex flex-col gap-3"}>
                    {continueDocs.map((doc) => (
                      <Link
                        key={doc.document_id}
                        href={`/documents/${doc.document_slug}`}
                        className={`border border-zinc-200 bg-white group hover:bg-zinc-50 transition-colors ${viewMode === "grid" ? "flex flex-col" : "flex items-start gap-4 p-4"}`}
                      >
                        <div className={`${viewMode === "grid" ? "aspect-[3/4] border-b border-zinc-200" : "w-16 h-20 border border-zinc-200"} bg-zinc-50 overflow-hidden relative shrink-0`}>
                          {doc.cover_url ? (
                            <img
                              src={doc.cover_url.startsWith("http") ? doc.cover_url : `${API_URL}/storage/${doc.cover_url}`}
                              className="w-full h-full object-cover grayscale mix-blend-multiply"
                              alt={doc.document_title}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <FileText className="w-6 h-6 text-zinc-400 stroke-[1]" />
                            </div>
                          )}
                          <div className="absolute bottom-0 left-0 w-full h-1 bg-zinc-200">
                            <div className="h-full bg-black" style={{ width: `${doc.progress_percentage}%` }} />
                          </div>
                        </div>
                        <div className={`flex-1 min-w-0 ${viewMode === "grid" ? "p-3" : "flex flex-col justify-center h-20"}`}>
                          <h4 className="text-xs font-semibold text-black line-clamp-2 group-hover:underline">
                            {doc.document_title}
                          </h4>
                          <p className="text-[10px] font-medium text-zinc-500 mt-1">
                            {doc.progress_percentage}% hoàn tất
                          </p>
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 flex flex-col items-center justify-center border border-dashed border-zinc-200 bg-zinc-50">
                    <p className="text-xs font-medium text-zinc-500">
                      Chưa có tài liệu đang đọc
                    </p>
                  </div>
                )}
              </section>

              <section className="space-y-6">
                <div className="flex items-center justify-between border-b border-zinc-200 pb-3">
                  <h2 className="text-sm font-semibold text-black flex items-center gap-2">
                    <Bookmark className="w-4 h-4" /> Thư mục và danh sách
                  </h2>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setActiveTab("folders")}
                      className="text-xs font-medium text-zinc-500 hover:text-black transition-colors"
                    >
                      Xem tất cả
                    </button>
                    <button
                      onClick={() => {
                        setCreateType("folder");
                        setIsCreateModalOpen(true);
                      }}
                      className="h-8 px-3 bg-black text-white text-xs font-medium flex items-center gap-1.5 hover:bg-zinc-800 transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" /> Tạo mới
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[...folders.slice(0, 2), ...readingLists.slice(0, 2)].length > 0 ? (
                    [...folders.slice(0, 2), ...readingLists.slice(0, 2)].map((item) => (
                      <Link
                        key={item.id || item._id}
                        href={item.id ? `/library/folder/${item.id}` : `/collection/${item._id}`}
                        className="p-4 border border-zinc-200 bg-white flex flex-col justify-between hover:bg-zinc-50 transition-colors"
                      >
                        <div className="space-y-1">
                          <div className="flex justify-between items-start">
                            <h4 className="text-sm font-semibold text-black line-clamp-1">{item.name}</h4>
                            <ChevronRight className="w-4 h-4 text-zinc-400 shrink-0" />
                          </div>
                          {(item as any).description && (
                            <p className="text-xs text-zinc-500 line-clamp-2">{(item as any).description}</p>
                          )}
                        </div>
                        <div className="pt-4 mt-4 border-t border-zinc-200 flex items-center justify-between">
                          <span className="text-xs font-medium text-zinc-500">
                            {item.bookmark_ids?.length || item.documents?.length || 0} tài liệu
                          </span>
                          <span className="text-[10px] font-semibold text-zinc-500 uppercase">
                            {(item as any).is_public === undefined ? 'Lưu trữ' : ((item as any).is_public ? 'Công khai' : 'Riêng tư')}
                          </span>
                        </div>
                      </Link>
                    ))
                  ) : (
                    <div className="md:col-span-2 py-12 flex flex-col items-center justify-center border border-dashed border-zinc-200 bg-zinc-50">
                      <p className="text-xs font-medium text-zinc-500">
                        Chưa có thư mục hoặc danh sách nào
                      </p>
                    </div>
                  )}
                </div>
              </section>
            </>
          )}

          {activeTab === "history" && (
            <section className="space-y-6">
              <div className="flex items-center justify-between border-b border-zinc-200 pb-3">
                <h2 className="text-sm font-semibold text-black flex items-center gap-2">
                  <Clock className="w-4 h-4" /> Lịch sử đọc toàn bộ
                </h2>
                <button
                  onClick={() => setIsClearModalOpen(true)}
                  className="text-xs font-medium text-zinc-500 hover:text-black transition-colors flex items-center gap-1.5"
                >
                  <Trash2 className="w-3.5 h-3.5" /> Xóa lịch sử
                </button>
              </div>

              <div className={viewMode === "grid" ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4" : "flex flex-col gap-3"}>
                {history.length > 0 ? (
                  history.map((item, idx) => (
                    <div
                      key={item.document_id + idx}
                      className={`border border-zinc-200 bg-white group hover:bg-zinc-50 transition-colors relative ${isDeletingHistory === item.document_id ? "opacity-50" : ""} ${viewMode === "grid" ? "flex flex-col" : "flex items-start gap-4 p-4"}`}
                    >
                      <Link href={`/documents/${item.document_slug}`} className={`block ${viewMode === "grid" ? "aspect-[3/4] border-b border-zinc-200" : "w-16 h-20 border border-zinc-200"} bg-zinc-50 overflow-hidden relative shrink-0`}>
                        {item.cover_url ? (
                          <img
                            src={item.cover_url.startsWith("http") ? item.cover_url : `${API_URL}/storage/${item.cover_url}`}
                            className="w-full h-full object-cover grayscale mix-blend-multiply"
                            alt=""
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <FileText className="w-6 h-6 text-zinc-400 stroke-[1]" />
                          </div>
                        )}
                        <div className="absolute bottom-0 left-0 w-full h-1 bg-zinc-200">
                          <div className="h-full bg-black" style={{ width: `${item.progress_percentage || 0}%` }} />
                        </div>
                      </Link>
                      <div className={`flex-1 min-w-0 flex flex-col justify-between ${viewMode === "grid" ? "p-3" : "h-20"}`}>
                        <div>
                          <Link href={`/documents/${item.document_slug}`}>
                            <h4 className="text-xs font-semibold text-black line-clamp-2 group-hover:underline">
                              {item.document_title}
                            </h4>
                          </Link>
                          <p className="text-[10px] font-medium text-zinc-500 mt-1">
                            Tiến độ: {item.progress_percentage || 0}%
                          </p>
                        </div>
                        {viewMode === "list" && (
                          <p className="text-[10px] font-medium text-zinc-400">
                            Cập nhật: {new Date(item.last_read_at).toLocaleDateString("vi-VN")}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={() => handleDeleteHistoryItem(item.document_id)}
                        className="absolute top-2 right-2 p-1.5 bg-white border border-zinc-200 text-zinc-400 hover:text-black opacity-0 group-hover:opacity-100 transition-all"
                        title="Xóa khỏi lịch sử"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="py-12 text-center border border-dashed border-zinc-200 bg-zinc-50 col-span-full">
                    <p className="text-xs font-medium text-zinc-500">Lịch sử đọc trống</p>
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === "folders" && (
            <section className="space-y-6">
              <div className="flex items-center justify-between border-b border-zinc-200 pb-3">
                <h2 className="text-sm font-semibold text-black flex items-center gap-2">
                  <Bookmark className="w-4 h-4" /> Thư mục lưu trữ
                </h2>
                <button
                  onClick={() => {
                    setCreateType("folder");
                    setIsCreateModalOpen(true);
                  }}
                  className="h-8 px-3 bg-black text-white text-xs font-medium flex items-center gap-1.5 hover:bg-zinc-800 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" /> Tạo thư mục
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {folders.length > 0 ? (
                  folders.map((folder) => (
                    <Link
                      key={folder.id}
                      href={`/library/folder/${folder.id}`}
                      className="p-4 border border-zinc-200 bg-white flex flex-col justify-between hover:bg-zinc-50 transition-colors h-32"
                    >
                      <div className="flex justify-between items-start">
                        <h4 className="text-sm font-semibold text-black line-clamp-2">{folder.name}</h4>
                        <ChevronRight className="w-4 h-4 text-zinc-400 shrink-0" />
                      </div>
                      <div className="pt-3 border-t border-zinc-200 flex items-center justify-between mt-auto">
                        <span className="text-xs font-medium text-zinc-500">
                          {folder.bookmark_ids?.length || 0} tài liệu
                        </span>
                        <span className="text-[10px] font-semibold text-zinc-500 uppercase">
                          Lưu trữ
                        </span>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="md:col-span-3 py-12 text-center border border-dashed border-zinc-200 bg-zinc-50">
                    <p className="text-xs font-medium text-zinc-500">
                      Chưa có thư mục nào
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === "lists" && (
            <section className="space-y-6">
              <div className="flex items-center justify-between border-b border-zinc-200 pb-3">
                <h2 className="text-sm font-semibold text-black flex items-center gap-2">
                  <ListIcon className="w-4 h-4" /> Danh sách đọc
                </h2>
                <button
                  onClick={() => {
                    setCreateType("list");
                    setIsCreateModalOpen(true);
                  }}
                  className="h-8 px-3 bg-black text-white text-xs font-medium flex items-center gap-1.5 hover:bg-zinc-800 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" /> Tạo danh sách
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {readingLists.length > 0 ? (
                  readingLists.map((list) => (
                    <Link
                      key={list._id}
                      href={`/collection/${list._id}`}
                      className="p-4 border border-zinc-200 bg-white flex flex-col justify-between hover:bg-zinc-50 transition-colors min-h-[140px]"
                    >
                      <div className="space-y-1">
                        <div className="flex justify-between items-start">
                          <h4 className="text-sm font-semibold text-black line-clamp-2">{list.name}</h4>
                          <ChevronRight className="w-4 h-4 text-zinc-400 shrink-0" />
                        </div>
                        {list.description && (
                          <p className="text-xs text-zinc-500 line-clamp-2">{list.description}</p>
                        )}
                      </div>
                      <div className="pt-3 border-t border-zinc-200 flex items-center justify-between mt-4">
                        <span className="text-xs font-medium text-zinc-500">
                          {list.documents?.length || 0} tài liệu
                        </span>
                        <span className="text-[10px] font-semibold text-black uppercase">
                          {list.is_public ? 'Công khai' : 'Riêng tư'}
                        </span>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="md:col-span-3 py-12 text-center border border-dashed border-zinc-200 bg-zinc-50">
                    <p className="text-xs font-medium text-zinc-500">
                      Chưa có danh sách nào
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === "series" && (
            <section className="space-y-6">
              <div className="flex items-center justify-between border-b border-zinc-200 pb-3">
                <h2 className="text-sm font-semibold text-black flex items-center gap-2">
                  <Layers className="w-4 h-4" /> Chuỗi tri thức chuyên sâu
                </h2>
                <button
                  onClick={() => {
                    setCreateType("series");
                    setIsCreateModalOpen(true);
                  }}
                  className="h-8 px-3 bg-black text-white text-xs font-medium flex items-center gap-1.5 hover:bg-zinc-800 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" /> Khởi tạo chuỗi
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {series.length > 0 ? (
                  series.map((s) => (
                    <Link
                      key={s._id}
                      href={`/series/${s._id}`}
                      className="p-4 border border-zinc-200 bg-white flex flex-col justify-between hover:bg-zinc-50 transition-colors min-h-[140px]"
                    >
                      <div className="space-y-1">
                        <div className="flex justify-between items-start">
                          <h4 className="text-sm font-semibold text-black line-clamp-2">{s.title}</h4>
                          <ChevronRight className="w-4 h-4 text-zinc-400 shrink-0" />
                        </div>
                        {s.description && (
                          <p className="text-xs text-zinc-500 line-clamp-2">{s.description}</p>
                        )}
                      </div>
                      <div className="pt-3 border-t border-zinc-200 flex items-center justify-between mt-4">
                        <span className="text-xs font-medium text-zinc-500">
                          {s.documents?.length || 0} tập
                        </span>
                        <span className="text-[10px] font-semibold text-black uppercase">
                          Chuỗi
                        </span>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="md:col-span-3 py-12 text-center border border-dashed border-zinc-200 bg-zinc-50">
                    <p className="text-xs font-medium text-zinc-500">
                      Chưa có chuỗi tri thức nào
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}
        </div>

        <aside className="lg:col-span-3 space-y-6">
          <div className="border border-zinc-200 bg-white p-6 space-y-6">
            <h3 className="text-sm font-semibold text-black border-b border-zinc-200 pb-3 flex items-center gap-2">
              <Pin className="w-4 h-4" /> Tài liệu đã ghim
            </h3>

            <div className="space-y-3">
              {pinnedDocs.length > 0 ? (
                pinnedDocs.map((doc) => (
                  <Link
                    key={doc.id}
                    href={`/documents/${doc.slug}`}
                    className="flex items-start gap-3 p-3 bg-zinc-50 border border-zinc-200 hover:border-black transition-colors group"
                  >
                    <div className="w-10 h-14 bg-white border border-zinc-200 shrink-0 overflow-hidden relative">
                      {doc.cover_url ? (
                        <img
                          src={doc.cover_url.startsWith("http") ? doc.cover_url : `${API_URL}/storage/${doc.cover_url}`}
                          className="w-full h-full object-cover grayscale mix-blend-multiply"
                          alt={doc.title}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <FileText className="w-4 h-4 text-zinc-400 stroke-[1]" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-xs font-semibold text-black line-clamp-2 group-hover:underline">{doc.title}</h4>
                      <p className="text-[10px] font-medium text-zinc-500 mt-1">Truy cập nhanh</p>
                    </div>
                  </Link>
                ))
              ) : (
                <div className="py-8 border border-dashed border-zinc-200 flex flex-col items-center justify-center gap-2 bg-zinc-50">
                  <Pin className="w-4 h-4 text-zinc-400" />
                  <p className="text-[10px] font-medium text-zinc-500">Chưa ghim tài liệu</p>
                </div>
              )}
            </div>
          </div>
        </aside>
      </div>

      <Modal isOpen={isClearModalOpen} onClose={() => !isClearing && setIsClearModalOpen(false)} className="max-w-sm rounded-none border border-zinc-200 bg-white p-0">
        <ModalHeader className="border-b border-zinc-200 p-6">
          <ModalTitle className="text-sm font-semibold text-black">Xóa toàn bộ lịch sử</ModalTitle>
        </ModalHeader>
        <ModalContent className="p-6">
          <p className="text-xs font-medium text-zinc-500 leading-relaxed">
            Bạn có chắc chắn muốn xóa toàn bộ lịch sử đọc sách? Hành động này sẽ xóa vĩnh viễn dữ liệu về tiến trình đọc của bạn.
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-200 p-4 bg-zinc-50">
          <button onClick={() => setIsClearModalOpen(false)} disabled={isClearing} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black hover:bg-zinc-50 transition-colors disabled:opacity-50">
            Hủy bỏ
          </button>
          <button onClick={handleClearHistory} disabled={isClearing} className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium hover:bg-zinc-800 transition-colors disabled:opacity-50 flex items-center justify-center">
            {isClearing ? <Loader2 className="w-3 h-3 animate-spin" /> : "Xác nhận xóa"}
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={isCreateModalOpen} onClose={() => !isCreating && setIsCreateModalOpen(false)} className="max-w-md rounded-none border border-zinc-200 bg-white p-0">
        <ModalHeader className="border-b border-zinc-200 p-6">
          <ModalTitle className="text-sm font-semibold text-black">
            {createType === "folder" ? "Tạo thư mục lưu trữ" : createType === "list" ? "Tạo danh sách đọc" : "Khởi tạo chuỗi tri thức"}
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Tên gọi</label>
            <input
              type="text"
              value={createType === "folder" ? newFolderName : createListForm.name}
              onChange={(e) => createType === "folder" ? setNewFolderName(e.target.value) : setCreateListForm({ ...createListForm, name: e.target.value })}
              className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:border-black outline-none transition-colors"
              placeholder=""
            />
          </div>
          {createType !== "folder" && (
            <div className="space-y-2">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Mô tả tóm lược</label>
              <textarea
                value={createListForm.description}
                onChange={(e) => setCreateListForm({ ...createListForm, description: e.target.value })}
                className="w-full min-h-[100px] p-3 bg-zinc-50 border border-zinc-200 text-xs font-medium focus:border-black outline-none resize-none transition-colors"
                placeholder=""
              />
            </div>
          )}
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-200 p-4 bg-zinc-50">
          <button onClick={() => setIsCreateModalOpen(false)} disabled={isCreating} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black hover:bg-zinc-50 transition-colors disabled:opacity-50">
            Hủy bỏ
          </button>
          <button onClick={handleCreate} disabled={isCreating} className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium hover:bg-zinc-800 transition-colors disabled:opacity-50 flex items-center justify-center">
            {isCreating ? <Loader2 className="w-3 h-3 animate-spin" /> : "Xác nhận tạo"}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
