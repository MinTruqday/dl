"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/app/contexts/AuthContext";
import {
  API_URL,
  getToken,
} from "@/app/lib/api";
import {
  Library as LibraryIcon,
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
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

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

  const fetchLibraryData = useCallback(async () => {
    setLoading(true);
    const token = getToken();
    if (!token) return;

    try {
      const [pinnedRes, continueRes, foldersRes] = await Promise.all([
        fetch(`${API_URL}/reader/pinned-documents`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/reader/continue-reading`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/reader/bookmark-folders`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);

      const [pinnedData, continueData, foldersData] = await Promise.all([
        pinnedRes.json(),
        continueRes.json(),
        foldersRes.json(),
      ]);

      if (pinnedRes.ok) setPinnedDocs(pinnedData.data || []);
      if (continueRes.ok) setContinueDocs(continueData.data || []);
      if (foldersRes.ok) setFolders(foldersData.data || []);
    } catch (error) {
      console.error("Lỗi tải thư viện:", error);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  useEffect(() => {
    if (user) fetchLibraryData();
  }, [user, fetchLibraryData]);

  if (authLoading || (loading && !visible)) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      {/* Header Section - Fixed Spacing mb-10 */}
      <header 
        className="mb-10 border-b border-zinc-100 pb-8 flex flex-col md:flex-row md:items-end justify-between gap-8 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div>
          <h1 className="text-5xl font-bold tracking-tighter leading-none text-black mb-3">
            Thư viện
          </h1>
          <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest">
            Personal Knowledge Archive
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex border border-zinc-100 p-1 bg-zinc-50/50">
            <button className="p-2.5 bg-white border border-zinc-200 shadow-sm transition-all">
              <LayoutGrid className="w-4 h-4 text-black" />
            </button>
            <button className="p-2.5 text-zinc-300 hover:text-black transition-all">
              <ListIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        {/* Main Content Area */}
        <div 
          className="lg:col-span-8 space-y-12 transition-all duration-700 delay-150"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {/* Continue Reading Section */}
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold tracking-tighter flex items-center gap-4">
                <Clock className="w-5 h-5 text-zinc-200" /> Đang đọc dở
              </h2>
              <Link href="/history" className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest hover:text-black transition-colors">
                Xem tất cả lịch sử
              </Link>
            </div>
            
            {continueDocs.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {continueDocs.map((doc) => (
                  <Link 
                    key={doc.document_id}
                    href={`/document/${doc.document_slug}`}
                    className="group border border-zinc-100 p-6 bg-white hover:border-black transition-all duration-500 flex flex-col justify-between"
                  >
                    <div className="space-y-4">
                      <div className="aspect-[3/4] bg-zinc-50 border border-zinc-100 overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-700 relative">
                        {doc.cover_url ? (
                          <img src={doc.cover_url} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" alt={doc.document_title} />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-zinc-100">
                            <FileText className="w-10 h-10 stroke-[1]" />
                          </div>
                        )}
                        <div className="absolute bottom-0 left-0 w-full h-1 bg-zinc-100/50">
                          <div className="h-full bg-black transition-all duration-1000" style={{ width: `${doc.progress_percentage}%` }} />
                        </div>
                      </div>
                      <h4 className="font-bold text-sm tracking-tight line-clamp-2 group-hover:underline underline-offset-4 decoration-1">
                        {doc.document_title}
                      </h4>
                    </div>
                    <p className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest mt-4">
                      {doc.progress_percentage}% Hoàn tất
                    </p>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="py-20 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/30">
                <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Không có tài liệu nào đang đọc dở</p>
              </div>
            )}
          </section>

          {/* Bookmark Folders Section */}
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold tracking-tighter flex items-center gap-4">
                <Bookmark className="w-5 h-5 text-zinc-200" /> Thư mục đánh dấu
              </h2>
              <Button variant="outline" className="h-10 px-4 rounded-none text-[10px] font-bold uppercase tracking-widest border-zinc-100 hover:bg-black hover:text-white transition-all">
                <Plus className="w-3.5 h-3.5 mr-2" /> Tạo thư mục
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {folders.length > 0 ? (
                folders.map((folder) => (
                  <Link
                    key={folder.id}
                    href={`/library/folder/${folder.id}`}
                    className="group p-8 border border-zinc-100 bg-white hover:border-black transition-all duration-500 flex items-center justify-between"
                  >
                    <div className="space-y-2">
                      <h4 className="text-lg font-bold tracking-tight text-black group-hover:translate-x-1 transition-transform duration-500">
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
                <div className="md:col-span-2 py-20 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/30">
                  <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Bạn chưa tạo thư mục nào</p>
                </div>
              )}
            </div>
          </section>
        </div>

        {/* Sidebar - Reverted but Fixed Aesthetics */}
        <aside 
          className="lg:col-span-4 space-y-10 transition-all duration-700 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {/* Pinned Documents - No longer black */}
          <div className="border border-zinc-100 bg-zinc-50/50 p-8 space-y-8">
            <div className="space-y-1">
              <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">Tài liệu ghim</h3>
              <p className="text-2xl font-bold tracking-tighter">Truy cập nhanh</p>
            </div>

            <div className="space-y-3">
              {pinnedDocs.length > 0 ? (
                pinnedDocs.map((doc) => (
                  <Link 
                    key={doc.id}
                    href={`/document/${doc.slug}`}
                    className="flex items-center gap-4 p-4 bg-white border border-zinc-100 hover:border-black transition-all group"
                  >
                    <div className="w-10 h-14 bg-zinc-50 border border-zinc-100 shrink-0 overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-500">
                      {doc.cover_url && <img src={doc.cover_url} className="w-full h-full object-cover" alt={doc.title} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-xs font-bold truncate group-hover:underline underline-offset-4 decoration-1">{doc.title}</h4>
                      <p className="text-[8px] font-bold text-zinc-300 uppercase tracking-widest mt-1 italic">Pinned</p>
                    </div>
                  </Link>
                ))
              ) : (
                <div className="py-12 border border-dashed border-zinc-200 flex flex-col items-center justify-center gap-4 bg-white">
                   <Pin className="w-6 h-6 text-zinc-100" />
                   <p className="text-[9px] font-bold text-zinc-200 uppercase tracking-widest">Chưa ghim tài liệu nào</p>
                </div>
              )}
            </div>
          </div>

          {/* Quick Search Widget */}
          <div className="p-8 border border-zinc-100 bg-white space-y-6">
             <div className="space-y-1">
                <h4 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-3">
                  <Search className="w-3.5 h-3.5" /> Tìm trong thư viện
                </h4>
             </div>
             <input 
               type="text" 
               placeholder=""
               className="w-full h-12 bg-zinc-50 border border-zinc-100 px-5 text-[11px] font-bold focus:outline-none focus:border-black transition-all rounded-none"
             />
          </div>

          {/* Minimal Motivation */}
          <div className="p-8 border border-zinc-100 text-center">
             <p className="text-[11px] font-medium italic text-zinc-300 leading-relaxed">
               "Knowledge is the only library you can carry with you everywhere."
             </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
