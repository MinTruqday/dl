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
  Sparkles,
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
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      <header
        className="mb-10 border-b border-zinc-100 pb-8 flex flex-col md:flex-row md:items-end justify-between gap-8"
      >
        <div>
          <h1 className="text-5xl font-bold tracking-tighter leading-none text-black mb-3">
            Thư viện
          </h1>
          <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
            Kho lưu trữ tri thức cá nhân <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
          </p>
        </div>
        <div className="flex items-center gap-4">
          <nav className="flex bg-white border border-zinc-100 p-1 rounded-sm overflow-x-auto no-scrollbar max-w-[600px]">
            {[
              { id: "overview", label: "Tổng quan" },
              { id: "history", label: "Lịch sử" },
              { id: "folders", label: "Thư mục" },
              { id: "lists", label: "Danh sách" },
              ...(canManageSeries ? [{ id: "series", label: "Chuỗi" }] : []),
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id as any)}
                className={`px-6 py-2.5 text-[10px] font-bold uppercase tracking-widest rounded-sm shrink-0 ${
                  activeTab === t.id ? "bg-black text-white" : "text-zinc-400"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
          <div className="w-px h-8 bg-zinc-100 mx-2" />
          <div className="flex border border-zinc-100 p-1 bg-white rounded-sm">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-2.5 rounded-sm ${viewMode === "grid" ? "bg-white border border-zinc-200" : "text-zinc-300"}`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-2.5 rounded-sm ${viewMode === "list" ? "bg-white border border-zinc-200" : "text-zinc-300"}`}
            >
              <ListIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div className="lg:col-span-8 space-y-12">
          {activeTab === "overview" && (
            <>
              <section className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold tracking-tighter flex items-center gap-4">
                    <Clock className="w-5 h-5 text-zinc-200" /> Đang đọc dở
                  </h2>
                  <button
                    onClick={() => setActiveTab("history")}
                    className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest"
                  >
                    Xem toàn bộ lịch sử
                  </button>
                </div>

                {continueDocs.length > 0 ? (
                  <div className={viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" : "space-y-4"}>
                    {continueDocs.map((doc) => (
                      <Link
                        key={doc.document_id}
                        href={`/documents/${doc.document_slug}`}
                        className={`border border-zinc-100 p-6 bg-white flex ${viewMode === "grid" ? "flex-col justify-between" : "items-center gap-6"} rounded-sm`}
                      >
                        <div className={`flex ${viewMode === "grid" ? "flex-col space-y-4" : "items-center gap-6 flex-1"}`}>
                          <div className={`${viewMode === "grid" ? "aspect-[3/4]" : "w-16 h-20"} bg-white border border-zinc-100 overflow-hidden grayscale relative rounded-sm`}>
                            {doc.cover_url ? (
                              <img
                                src={doc.cover_url.startsWith("http") ? doc.cover_url : `${API_URL}/storage/${doc.cover_url}`}
                                className="w-full h-full object-cover"
                                alt={doc.document_title}
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-zinc-100">
                                <FileText className="w-10 h-10 stroke-[1]" />
                              </div>
                            )}
                            <div className="absolute bottom-0 left-0 w-full h-1 bg-zinc-100/50">
                              <div className="h-full bg-black" style={{ width: `${doc.progress_percentage}%` }} />
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="font-bold text-sm tracking-tight line-clamp-2 underline-offset-4 decoration-1">
                              {doc.document_title}
                            </h4>
                            {viewMode === "list" && (
                              <p className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest mt-2">
                                {doc.progress_percentage}% Hoàn tất
                              </p>
                            )}
                          </div>
                        </div>
                        {viewMode === "grid" && (
                          <p className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest mt-4">
                            {doc.progress_percentage}% Hoàn tất
                          </p>
                        )}
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="py-20 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-white rounded-sm">
                    <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                      Không có tài liệu nào phù hợp
                    </p>
                  </div>
                )}
              </section>

              <section className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold tracking-tighter flex items-center gap-4">
                    <Bookmark className="w-5 h-5 text-zinc-200" /> Thư mục và danh sách
                  </h2>
                  <div className="flex items-center gap-4">
                    <button
                      onClick={() => setActiveTab("folders")}
                      className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest"
                    >
                      Tất cả
                    </button>
                    <button
                      onClick={() => {
                        setCreateType("folder");
                        setIsCreateModalOpen(true);
                      }}
                      className="h-10 px-6 rounded-sm text-[10px] font-bold uppercase tracking-widest border border-zinc-100 flex items-center gap-2"
                    >
                      <Plus className="w-3.5 h-3.5" /> Thêm mới
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[...folders.slice(0, 2), ...readingLists.slice(0, 2)].length > 0 ? (
                    [...folders.slice(0, 2), ...readingLists.slice(0, 2)].map((item) => (
                      <Link
                        key={item.id || item._id}
                        href={item.id ? `/library/folder/${item.id}` : `/collection/${item._id}`}
                        className="p-8 border border-zinc-100 bg-white flex items-center justify-between rounded-sm"
                      >
                        <div className="space-y-2">
                          <h4 className="text-lg font-bold tracking-tight text-black">
                            {item.name}
                          </h4>
                          <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                            {item.bookmark_ids?.length || item.documents?.length || 0} Thực thể
                          </p>
                        </div>
                        <ChevronRight className="w-5 h-5 text-zinc-100" />
                      </Link>
                    ))
                  ) : (
                    <div className="md:col-span-2 py-20 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-white rounded-sm">
                      <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                        Chưa có dữ liệu nào
                      </p>
                    </div>
                  )}
                </div>
              </section>
            </>
          )}

          {activeTab === "history" && (
            <section className="space-y-10">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold tracking-tighter flex items-center gap-4">
                  <Clock className="w-5 h-5 text-zinc-200" /> Lịch sử đọc toàn bộ
                </h2>
                <button
                  onClick={() => setIsClearModalOpen(true)}
                  className="h-10 px-6 text-[10px] font-bold text-zinc-400 uppercase tracking-widest border border-zinc-100 rounded-sm"
                >
                  <Trash2 className="w-3.5 h-3.5 mr-2 inline" /> Xóa lịch sử
                </button>
              </div>

              <div className="space-y-4">
                {history.length > 0 ? (
                  history.map((item, idx) => (
                    <div
                      key={item.document_id + idx}
                      className={`flex items-center justify-between p-8 border border-zinc-100 bg-white rounded-sm ${isDeletingHistory === item.document_id ? "opacity-50" : ""}`}
                    >
                      <div className="flex items-center gap-8 flex-1">
                        <div className="w-16 h-20 bg-zinc-50 border border-zinc-100 overflow-hidden grayscale rounded-sm">
                          {item.cover_url && (
                            <img
                              src={item.cover_url.startsWith("http") ? item.cover_url : `${API_URL}/storage/${item.cover_url}`}
                              className="w-full h-full object-cover"
                              alt=""
                            />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-bold text-lg tracking-tight truncate">
                            {item.document_title}
                          </h4>
                          <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest mt-1">
                            Tiến độ: {item.progress_percentage || 0}% • {new Date(item.last_read_at).toLocaleDateString("vi-VN")}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <Link
                          href={`/documents/${item.document_slug}`}
                          className="h-12 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest flex items-center rounded-sm"
                        >
                          Đọc lại
                        </Link>
                        <button
                          onClick={() => handleDeleteHistoryItem(item.document_id)}
                          className="w-12 h-12 border border-zinc-100 flex items-center justify-center text-zinc-200 rounded-sm"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="py-20 text-center border border-dashed border-zinc-100 rounded-sm">
                    <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                      Lịch sử trống
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === "folders" && (
            <section className="space-y-10">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold tracking-tighter flex items-center gap-4">
                  <Bookmark className="w-5 h-5 text-zinc-200" /> Thư mục đã lưu
                </h2>
                <button
                  onClick={() => {
                    setCreateType("folder");
                    setIsCreateModalOpen(true);
                  }}
                  className="h-10 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest flex items-center gap-3 rounded-sm"
                >
                  <Plus className="w-4 h-4" /> Thêm mới
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {folders.length > 0 ? (
                  folders.map((folder) => (
                    <Link
                      key={folder.id}
                      href={`/library/folder/${folder.id}`}
                      className="p-10 border border-zinc-100 bg-white flex flex-col justify-between min-h-[200px] rounded-sm"
                    >
                      <h4 className="text-xl font-bold tracking-tight">{folder.name}</h4>
                      <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                        {folder.bookmark_ids?.length || 0} Tài liệu
                      </p>
                    </Link>
                  ))
                ) : (
                  <div className="md:col-span-2 py-20 text-center border border-dashed border-zinc-100 rounded-sm">
                    <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                      Chưa có thư mục nào phù hợp
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === "lists" && (
            <section className="space-y-10">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold tracking-tighter flex items-center gap-4">
                  <LayoutGrid className="w-5 h-5 text-zinc-200" /> Danh sách bộ sưu tập
                </h2>
                <button
                  onClick={() => {
                    setCreateType("list");
                    setIsCreateModalOpen(true);
                  }}
                  className="h-10 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest flex items-center gap-3 rounded-sm"
                >
                  <Plus className="w-4 h-4" /> Tạo danh sách
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {readingLists.length > 0 ? (
                  readingLists.map((list) => (
                    <div
                      key={list._id}
                      className="border border-zinc-100 p-10 bg-white flex flex-col justify-between min-h-[300px] rounded-sm"
                    >
                      <div className="space-y-4">
                        <div className="flex justify-between items-start">
                          <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-sm">
                            <FolderPlus className="w-5 h-5" />
                          </div>
                          <Share2 className="w-4 h-4 text-zinc-200" />
                        </div>
                        <h4 className="text-xl font-bold tracking-tight">{list.name}</h4>
                        <p className="text-xs text-zinc-400 line-clamp-2">{list.description}</p>
                      </div>
                      <div className="pt-6 border-t border-zinc-50 flex items-center justify-between mt-6">
                        <span className="text-[10px] font-bold uppercase text-black">
                          {list.documents?.length || 0} Thực thể
                        </span>
                        <Link href={`/collection/${list._id}`} className="text-[10px] font-bold uppercase underline">
                          Truy cập
                        </Link>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="md:col-span-2 py-20 text-center border border-dashed border-zinc-100 rounded-sm">
                    <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                      Chưa có danh sách nào
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === "series" && (
            <section className="space-y-10">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold tracking-tighter flex items-center gap-4">
                  <Layers className="w-5 h-5 text-zinc-200" /> Chuỗi tri thức chuyên sâu
                </h2>
                <button
                  onClick={() => {
                    setCreateType("series");
                    setIsCreateModalOpen(true);
                  }}
                  className="h-10 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest flex items-center gap-3 rounded-sm"
                >
                  <Plus className="w-4 h-4" /> Khởi tạo chuỗi
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {series.length > 0 ? (
                  series.map((s) => (
                    <Link
                      key={s._id}
                      href={`/series/${s._id}`}
                      className="border border-zinc-100 p-10 bg-white flex flex-col justify-between min-h-[240px] rounded-sm"
                    >
                      <div className="space-y-4">
                        <Sparkles className="w-6 h-6 text-zinc-200" />
                        <h4 className="text-xl font-bold tracking-tight">{s.title}</h4>
                        <p className="text-xs text-zinc-400 line-clamp-2">{s.description}</p>
                      </div>
                      <div className="flex items-center justify-between mt-6">
                        <span className="text-[10px] font-bold uppercase text-black">
                          {s.documents?.length || 0} Tập
                        </span>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="md:col-span-2 py-20 text-center border border-dashed border-zinc-100 rounded-sm">
                    <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                      Chưa có chuỗi tri thức nào
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}
        </div>

        <aside className="lg:col-span-4 space-y-10">
          <div className="border border-zinc-100 bg-white p-8 space-y-8 rounded-sm">
            <div className="space-y-1">
              <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">
                Tài liệu ghim
              </h3>
              <p className="text-2xl font-bold tracking-tighter">Truy cập nhanh</p>
            </div>

            <div className="space-y-3">
              {pinnedDocs.length > 0 ? (
                pinnedDocs.map((doc) => (
                  <Link
                    key={doc.id}
                    href={`/documents/${doc.slug}`}
                    className="flex items-center gap-4 p-4 bg-white border border-zinc-100 rounded-sm"
                  >
                    <div className="w-10 h-14 bg-white border border-zinc-100 shrink-0 overflow-hidden grayscale rounded-sm">
                      {doc.cover_url && (
                        <img
                          src={doc.cover_url.startsWith("http") ? doc.cover_url : `${API_URL}/storage/${doc.cover_url}`}
                          className="w-full h-full object-cover"
                          alt={doc.title}
                        />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-xs font-bold truncate underline-offset-4 decoration-1">{doc.title}</h4>
                      <p className="text-[8px] font-bold text-zinc-300 uppercase tracking-widest mt-1 italic">Đã ghim</p>
                    </div>
                  </Link>
                ))
              ) : (
                <div className="py-12 border border-dashed border-zinc-200 flex flex-col items-center justify-center gap-4 bg-white rounded-sm">
                  <Pin className="w-6 h-6 text-zinc-100" />
                  <p className="text-[9px] font-bold text-zinc-200 uppercase tracking-widest">Chưa ghim tài liệu nào</p>
                </div>
              )}
            </div>
          </div>
        </aside>
      </div>

      <Modal isOpen={isClearModalOpen} onClose={() => !isClearing && setIsClearModalOpen(false)} className="max-w-md">
        <ModalHeader><ModalTitle>Xóa toàn bộ lịch sử</ModalTitle></ModalHeader>
        <ModalContent>
          <p className="text-sm font-bold text-zinc-400 uppercase tracking-widest leading-relaxed">
            Bạn có chắc chắn muốn xóa toàn bộ lịch sử đọc sách? Hành động này sẽ xóa vĩnh viễn dữ liệu về tiến trình đọc của bạn.
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-4">
          <button onClick={() => setIsClearModalOpen(false)} disabled={isClearing} className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest rounded-sm disabled:opacity-50">
            Hủy bỏ
          </button>
          <button onClick={handleClearHistory} disabled={isClearing} className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-sm disabled:opacity-50 flex items-center justify-center">
            {isClearing ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xác nhận xóa"}
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={isCreateModalOpen} onClose={() => !isCreating && setIsCreateModalOpen(false)} className="max-w-xl">
        <ModalHeader>
          <ModalTitle>
            {createType === "folder" ? "Tạo thư mục mới" : createType === "list" ? "Tạo danh sách mới" : "Khởi tạo chuỗi tri thức"}
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="space-y-8">
          <div className="space-y-3">
            <label className="text-[10px] font-bold text-black uppercase tracking-widest">Tên gọi</label>
            <input
              type="text"
              value={createType === "folder" ? newFolderName : createListForm.name}
              onChange={(e) => createType === "folder" ? setNewFolderName(e.target.value) : setCreateListForm({ ...createListForm, name: e.target.value })}
              className="w-full h-14 bg-white border border-zinc-100 px-6 text-sm font-bold focus:border-black outline-none rounded-sm"
              placeholder=""
            />
          </div>
          {createType !== "folder" && (
            <div className="space-y-3">
              <label className="text-[10px] font-bold text-black uppercase tracking-widest">Mô tả tóm lược</label>
              <textarea
                value={createListForm.description}
                onChange={(e) => setCreateListForm({ ...createListForm, description: e.target.value })}
                className="w-full min-h-[120px] p-6 bg-white border border-zinc-100 text-sm font-medium focus:border-black outline-none rounded-sm resize-none"
                placeholder=""
              />
            </div>
          )}
        </ModalContent>
        <ModalFooter className="flex gap-4">
          <button onClick={() => setIsCreateModalOpen(false)} disabled={isCreating} className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest rounded-sm disabled:opacity-50">
            Hủy bỏ
          </button>
          <button onClick={handleCreate} disabled={isCreating} className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-sm disabled:opacity-50 flex items-center justify-center">
            {isCreating ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xác nhận tạo"}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
