"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  Bookmark, 
  FolderPlus, 
  Grid, 
  MoreVertical, 
  Share2, 
  Plus, 
  Loader2, 
  Search,
  Lock,
  Globe,
  ChevronRight,
  Sparkles,
  Filter,
} from "lucide-react";
import { 
  getReadingListsAPI, 
  createReadingListAPI 
} from "@/services/reading.service";
import Link from "next/link";

export default function CollectionsPage() {
  const [collections, setCollections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<"all" | "public" | "private">("all");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchCollections = useCallback(async () => {
    try {
      const res = await getReadingListsAPI();
      const data = res.data || res;
      setCollections(Array.isArray(data) ? data : []);
    } catch (err: any) {
      console.error("Lỗi tải bộ sưu tập:", err);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  const handleCreateCollection = async () => {
    const name = prompt("Nhập tên bộ sưu tập mới:");
    if (!name || !name.trim()) return;

    const description = prompt("Nhập mô tả (không bắt buộc):") || "";
    const isPublic = confirm("Bạn có muốn đặt bộ sưu tập này ở chế độ công khai không?");

    try {
      const res = await createReadingListAPI({
        name: name.trim(),
        description: description.trim(),
        is_public: isPublic
      });
      if (res) {
        await fetchCollections();
      }
    } catch (err: any) {
      alert("Không thể tạo bộ sưu tập. Vui lòng thử lại sau.");
    }
  };

  useEffect(() => {
    fetchCollections();
  }, [fetchCollections]);

  const filteredCollections = collections.filter(col => {
    const matchesSearch = (col.name || "").toLowerCase().includes(searchQuery.toLowerCase());
    if (activeTab === "all") return matchesSearch;
    if (activeTab === "public") return matchesSearch && col.is_public;
    if (activeTab === "private") return matchesSearch && !col.is_public;
    return matchesSearch;
  });

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      <div 
        className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
              Bộ sưu tập
            </h1>
            <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
              Kho lưu trữ tri thức cá nhân <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
            </p>
          </div>
          
          <button 
            onClick={handleCreateCollection}
            className="h-16 px-12 bg-black text-white text-[11px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all active:scale-95 flex items-center gap-4 rounded-sm"
          >
            <FolderPlus className="w-5 h-5" />
            Tạo danh sách mới
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-12">
        <aside 
          className="lg:col-span-3 space-y-10 transition-all duration-300 delay-75"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="space-y-6">
            <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-[0.2em] px-1">
              <Filter className="w-4 h-4" /> Phân loại
            </div>
            <nav className="flex flex-col gap-1">
              {[
                { id: "all", label: "Tất cả danh sách" },
                { id: "public", label: "Bộ sưu tập công khai" },
                { id: "private", label: "Bộ sưu tập riêng tư" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`text-left px-6 py-4 text-[11px] font-bold uppercase tracking-widest transition-all border rounded-sm ${
                    activeTab === tab.id
                      ? "bg-black text-white border-black"
                      : "bg-white text-zinc-400 border-zinc-100 hover:bg-zinc-50 hover:text-black"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="space-y-6">
            <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-[0.2em] px-1">
              <Search className="w-4 h-4" /> Tìm kiếm
            </div>
            <div className="relative">
              <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-300" />
              <input 
                placeholder="Nhập tên danh sách"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-14 h-14 bg-zinc-50/50 border border-zinc-100 focus:bg-white focus:border-black outline-none transition-all text-xs font-bold rounded-sm"
              />
            </div>
          </div>

          <div className="p-8 border border-zinc-100 bg-zinc-50/30 rounded-sm">
            <p className="text-[10px] font-medium text-zinc-400 leading-relaxed italic">
              "Tổ chức tri thức một cách khoa học giúp bạn tối ưu hóa việc tiếp thu và ứng dụng thông tin."
            </p>
          </div>
        </aside>

        <div 
          className="lg:col-span-9 transition-all duration-300 delay-150"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {filteredCollections.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {filteredCollections.map((col) => (
                <div
                  key={col._id}
                  className="group border border-zinc-100 p-10 bg-white hover:border-black transition-all duration-300 flex flex-col justify-between min-h-[380px] relative overflow-hidden rounded-sm"
                >
                  <div className="absolute -top-10 -right-10 w-40 h-40 bg-zinc-50/50 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                  <div className="relative z-10">
                    <div className="flex justify-between items-start mb-10">
                      <div className="w-16 h-16 border border-zinc-100 bg-zinc-50 flex items-center justify-center grayscale group-hover:grayscale-0 group-hover:bg-black group-hover:text-white group-hover:border-black transition-all duration-300 rounded-sm">
                        <Grid className="w-7 h-7" />
                      </div>
                      <div className="flex gap-1">
                        <button className="p-3 hover:bg-zinc-50 transition-colors rounded-sm">
                          <Share2 className="w-4 h-4 text-zinc-300 group-hover:text-black" />
                        </button>
                        <button className="p-3 hover:bg-zinc-50 transition-colors rounded-sm">
                          <MoreVertical className="w-4 h-4 text-zinc-300 group-hover:text-black" />
                        </button>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-center gap-4">
                        <h3 className="text-2xl font-bold tracking-tighter text-black group-hover:translate-x-1 transition-transform duration-300">
                          {col.name}
                        </h3>
                        {col.is_public ? (
                          <Globe className="w-3.5 h-3.5 text-zinc-200" />
                        ) : (
                          <Lock className="w-3.5 h-3.5 text-zinc-200" />
                        )}
                      </div>
                      <p className="text-sm font-medium text-zinc-400 line-clamp-3 leading-relaxed">
                        {col.description || "Danh sách tri thức này chưa có mô tả chi tiết."}
                      </p>
                    </div>
                  </div>

                  <div className="pt-10 border-t border-zinc-50 mt-10 relative z-10">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 bg-black rounded-sm animate-pulse" />
                        <span className="text-[11px] font-bold tracking-[0.2em] uppercase text-black">
                          {col.documents?.length || 0} Tài liệu
                        </span>
                      </div>
                      <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                        {new Date(col.created_at).toLocaleDateString('vi-VN')}
                      </span>
                    </div>
                    
                    <Link
                      href={`/collections/${col._id}`}
                      className="flex items-center justify-between w-full h-16 px-8 bg-zinc-50 border border-transparent group-hover:border-zinc-100 group-hover:bg-white transition-all duration-300 rounded-sm"
                    >
                      <span className="text-[11px] font-bold tracking-[0.2em] uppercase">Truy cập tri thức</span>
                      <ChevronRight className="w-5 h-5 text-zinc-300 group-hover:text-black group-hover:translate-x-2 transition-all duration-300" />
                    </Link>
                  </div>
                </div>
              ))}
              
              <button 
                onClick={handleCreateCollection}
                className="group border border-dashed border-zinc-200 p-10 flex flex-col items-center justify-center space-y-8 hover:border-black hover:bg-zinc-50/50 transition-all min-h-[380px] active:scale-[0.98] rounded-sm"
              >
                <div className="w-16 h-16 border border-zinc-100 flex items-center justify-center bg-white group-hover:border-black transition-all duration-300 rounded-sm">
                  <Plus className="w-7 h-7 text-zinc-300 group-hover:text-black" />
                </div>
                <div className="text-center">
                  <p className="text-[13px] font-bold text-black tracking-[0.2em] uppercase mb-3">Thêm bộ sưu tập</p>
                  <p className="text-[11px] font-medium text-zinc-400 uppercase tracking-widest">Xây dựng kho tàng của bạn</p>
                </div>
              </button>
            </div>
          ) : (
            <div className="py-48 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/30 rounded-sm">
              <div className="w-24 h-24 border border-zinc-100 bg-white flex items-center justify-center mb-10 rounded-sm">
                <Bookmark className="w-10 h-10 text-zinc-100 stroke-[1]" />
              </div>
              <h2 className="text-3xl font-bold tracking-tighter text-black mb-4">Chưa có bộ sưu tập</h2>
              <p className="text-sm font-medium text-zinc-400 mb-10 max-w-xs text-center uppercase tracking-widest leading-loose">
                Bắt đầu hành trình bằng cách tạo bộ sưu tập đầu tiên.
              </p>
              <button 
                onClick={handleCreateCollection}
                className="h-16 px-14 bg-black text-white text-[11px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all rounded-sm"
              >
                Tạo danh sách ngay
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
