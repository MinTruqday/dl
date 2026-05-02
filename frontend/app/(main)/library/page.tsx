"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  getBookmarkFoldersAPI,
  createBookmarkFolderAPI,
  getPinnedDocumentsAPI,
  getContinueReadingAPI,
} from "@/services/read.service";
import { API_URL } from "@/services/auth.service";
import {
  Bookmark,
  Pin,
  Clock,
  ChevronRight,
  Plus,
  Loader2,
  FileText,
  Search,
  LayoutGrid,
  List as ListIcon,
  Sparkles,
} from "lucide-react";
import Link from "next/link";

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
  const [pinnedDocs, setPinnedDocs] = useState<PinnedDocument[]>([]);
  const [continueDocs, setContinueDocs] = useState<ContinueReading[]>([]);
  const [folders, setFolders] = useState<BookmarkFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const fetchLibraryData = useCallback(async () => {
    setLoading(true);
    try {
      const [pinnedRes, continueRes, foldersRes] = await Promise.all([
        getPinnedDocumentsAPI(),
        getContinueReadingAPI(),
        getBookmarkFoldersAPI(),
      ]);

      setPinnedDocs(pinnedRes.data || pinnedRes || []);
      setContinueDocs(continueRes.data || continueRes || []);
      setFolders(foldersRes.data || foldersRes || []);
    } catch (error) {
      console.error("Lỗi tải thư viện:", error);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  const handleCreateFolder = async () => {
    const name = prompt("Nhập tên thư mục mới:");
    if (!name || !name.trim()) return;

    try {
      const res = await createBookmarkFolderAPI(name.trim());
      if (res) {
        await fetchLibraryData();
      }
    } catch (err: any) {
      alert("Không thể tạo thư mục. Vui lòng thử lại sau.");
    }
  };

  useEffect(() => {
    if (user) fetchLibraryData();
  }, [user, fetchLibraryData]);

  const filteredFolders = folders.filter(f => 
    f.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredContinueDocs = continueDocs.filter(d => 
    d.document_title.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
        className="mb-10 border-b border-zinc-100 pb-8 flex flex-col md:flex-row md:items-end justify-between gap-8 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
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
          <div className="flex border border-zinc-100 p-1 bg-zinc-50/50 rounded-sm">
            <button 
              onClick={() => setViewMode("grid")}
              className={`p-2.5 transition-all rounded-sm ${viewMode === "grid" ? "bg-white border border-zinc-200" : "text-zinc-300 hover:text-black"}`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setViewMode("list")}
              className={`p-2.5 transition-all rounded-sm ${viewMode === "list" ? "bg-white border border-zinc-200" : "text-zinc-300 hover:text-black"}`}
            >
              <ListIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div 
          className="lg:col-span-8 space-y-12 transition-all duration-300 delay-75"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold tracking-tighter flex items-center gap-4">
                <Clock className="w-5 h-5 text-zinc-200" /> Đang đọc dở
              </h2>
              <Link href="/history" className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest hover:text-black transition-colors">
                Xem toàn bộ lịch sử
              </Link>
            </div>
            
            {filteredContinueDocs.length > 0 ? (
              <div className={viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" : "space-y-4"}>
                {filteredContinueDocs.map((doc) => (
                  <Link 
                    key={doc.document_id}
                    href={`/documents/${doc.document_slug}`}
                    className={`group border border-zinc-100 p-6 bg-white hover:border-black transition-all duration-300 flex ${viewMode === "grid" ? "flex-col justify-between" : "items-center gap-6"} rounded-sm`}
                  >
                    <div className={`flex ${viewMode === "grid" ? "flex-col space-y-4" : "items-center gap-6 flex-1"}`}>
                      <div className={`${viewMode === "grid" ? "aspect-[3/4]" : "w-16 h-20"} bg-zinc-50 border border-zinc-100 overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-300 relative rounded-sm`}>
                        {doc.cover_url ? (
                          <img 
                            src={doc.cover_url.startsWith("http") ? doc.cover_url : `${API_URL}/storage/${doc.cover_url}`} 
                            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110" 
                            alt={doc.document_title} 
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-zinc-100">
                            <FileText className="w-10 h-10 stroke-[1]" />
                          </div>
                        )}
                        <div className="absolute bottom-0 left-0 w-full h-1 bg-zinc-100/50">
                          <div className="h-full bg-black transition-all duration-500" style={{ width: `${doc.progress_percentage}%` }} />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-bold text-sm tracking-tight line-clamp-2 group-hover:underline underline-offset-4 decoration-1">
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
              <div className="py-20 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/30 rounded-sm">
                <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Không có tài liệu nào phù hợp</p>
              </div>
            )}
          </section>

          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold tracking-tighter flex items-center gap-4">
                <Bookmark className="w-5 h-5 text-zinc-200" /> Thư mục đánh dấu
              </h2>
              <button 
                onClick={handleCreateFolder}
                className="h-10 px-6 rounded-sm text-[10px] font-bold uppercase tracking-widest border border-zinc-100 hover:bg-black hover:text-white transition-all flex items-center gap-2"
              >
                <Plus className="w-3.5 h-3.5" /> Tạo thư mục
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredFolders.length > 0 ? (
                filteredFolders.map((folder) => (
                  <Link
                    key={folder.id}
                    href={`/library/folder/${folder.id}`}
                    className="group p-8 border border-zinc-100 bg-white hover:border-black transition-all duration-300 flex items-center justify-between rounded-sm"
                  >
                    <div className="space-y-2">
                      <h4 className="text-lg font-bold tracking-tight text-black group-hover:translate-x-1 transition-transform duration-300">
                        {folder.name}
                      </h4>
                      <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                        {folder.bookmark_ids.length} Tài liệu đã lưu
                      </p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-zinc-100 group-hover:text-black transition-colors" />
                  </Link>
                ))
              ) : (
                <div className="md:col-span-2 py-20 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/30 rounded-sm">
                  <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Chưa có thư mục nào</p>
                </div>
              )}
            </div>
          </section>
        </div>

        <aside 
          className="lg:col-span-4 space-y-10 transition-all duration-300 delay-150"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="border border-zinc-100 bg-zinc-50/50 p-8 space-y-8 rounded-sm">
            <div className="space-y-1">
              <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">Tài liệu ghim</h3>
              <p className="text-2xl font-bold tracking-tighter">Truy cập nhanh</p>
            </div>

            <div className="space-y-3">
              {pinnedDocs.length > 0 ? (
                pinnedDocs.map((doc) => (
                  <Link 
                    key={doc.id}
                    href={`/documents/${doc.slug}`}
                    className="flex items-center gap-4 p-4 bg-white border border-zinc-100 hover:border-black transition-all group rounded-sm"
                  >
                    <div className="w-10 h-14 bg-zinc-50 border border-zinc-100 shrink-0 overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-300 rounded-sm">
                      {doc.cover_url && (
                        <img 
                          src={doc.cover_url.startsWith("http") ? doc.cover_url : `${API_URL}/storage/${doc.cover_url}`} 
                          className="w-full h-full object-cover" 
                          alt={doc.title} 
                        />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-xs font-bold truncate group-hover:underline underline-offset-4 decoration-1">{doc.title}</h4>
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

          <div className="p-8 border border-zinc-100 bg-white space-y-6 rounded-sm">
             <div className="space-y-1">
                <h4 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-3">
                  <Search className="w-3.5 h-3.5" /> Tìm trong thư viện
                </h4>
             </div>
             <input 
               type="text" 
               placeholder="Nhập từ khóa"
               value={searchQuery}
               onChange={(e) => setSearchQuery(e.target.value)}
               className="w-full h-12 bg-zinc-50 border border-zinc-100 px-5 text-[11px] font-bold outline-none focus:border-black transition-all rounded-sm"
             />
          </div>

          <div className="p-8 border border-zinc-100 text-center rounded-sm">
             <p className="text-[11px] font-medium italic text-zinc-300 leading-relaxed">
               "Kiến thức là thư viện duy nhất bạn có thể mang theo mọi nơi."
             </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
