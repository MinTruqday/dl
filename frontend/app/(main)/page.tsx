"use client";
import { useEffect, useState, useCallback } from "react";
import {
  getDocumentsAPI,
  getTagsCategoriesAPI,
  getTrendingDocumentsAPI,
  getAIRecommendationsAPI,
} from "@/services/document.service";
import { semanticSearchAPI } from "@/services/search.service";
import { API_URL } from "@/services/auth.service";
import { useAuth } from "@/contexts/AuthContext";
import Link from "next/link";
import {
  Search,
  ChevronRight,
  LayoutGrid,
  List as ListIcon,
} from "lucide-react";

export default function ExplorePage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [trending, setTrending] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [useSemantic, setUseSemantic] = useState(false);

  const loadInitialData = useCallback(async () => {
    try {
      const [catData, trendData, recData] = await Promise.all([
        getTagsCategoriesAPI(),
        getTrendingDocumentsAPI(3),
        getAIRecommendationsAPI(4),
      ]);
      setCategories(catData.data?.categories || catData.categories || []);
      setTrending(trendData.data || trendData || []);
      setRecommendations(recData.data || recData || []);
    } catch (err) {
      console.error("Lỗi tải dữ liệu khám phá:", err);
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      let data;
      if (useSemantic && searchQuery.trim()) {
        data = await semanticSearchAPI(searchQuery);
      } else {
        data = await getDocumentsAPI(
          searchQuery || undefined,
          "latest",
          selectedCategory || undefined,
        );
      }
      setDocuments(data.data || data || []);
    } catch (err) {
      console.error("Lỗi tải tài liệu:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, searchQuery, useSemantic]);

  const { user } = useAuth();

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      loadDocuments();
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [loadDocuments]);

  return (
    <>
      <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
        <div className="mb-10 relative h-[420px] bg-white border border-zinc-200 flex items-center justify-center rounded-sm">
          <p className="text-zinc-300 text-[10px] font-bold uppercase tracking-[0.4em]">
            Liên hệ quảng cáo với DocLib
          </p>
        </div>

        <div className="mb-10 border-b border-zinc-200 pb-10">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="space-y-3">
              <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
                Khám phá
              </h1>
              <p className="text-zinc-400 text-[10px] font-bold uppercase tracking-[0.2em]">
                Tìm kiếm và kết nối với nguồn tri thức mới nhất
              </p>
            </div>

            <div className="flex items-center gap-6">
              <div className="flex border border-zinc-200 p-1 bg-white rounded-sm">
                <button
                  onClick={() => setViewMode("grid")}
                  className={`p-3 border rounded-sm ${viewMode === "grid" ? "bg-black border-black text-white" : "bg-transparent border-transparent text-zinc-300"}`}
                >
                  <LayoutGrid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode("list")}
                  className={`p-3 border rounded-sm ${viewMode === "list" ? "bg-black border-black text-white" : "bg-transparent border-transparent text-zinc-300"}`}
                >
                  <ListIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>


        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          <aside className="lg:col-span-3 space-y-12">
            <div className="space-y-6">
              <div className="text-[10px] font-bold text-black uppercase tracking-[0.2em] px-1">
                Phân loại
              </div>
              <nav className="flex flex-col gap-1.5">
                <button
                  onClick={() => setSelectedCategory(null)}
                  className={`flex items-center justify-between px-6 py-4 text-[10px] font-bold uppercase tracking-widest border rounded-sm ${
                    !selectedCategory
                      ? "bg-black text-white border-black"
                      : "bg-white text-zinc-400 border-zinc-200"
                  }`}
                >
                  Tất cả tài liệu
                  <ChevronRight
                    className={`w-3.5 h-3.5 ${!selectedCategory ? "rotate-90" : ""}`}
                  />
                </button>
                {categories.map((cat) => (
                  <button
                  key={cat}
                  onClick={() => setSelectedCategory(selectedCategory === cat ? null : cat)}
                  className={`flex items-center justify-between px-6 py-4 text-[11px] font-bold uppercase tracking-widest border rounded-sm ${selectedCategory === cat ? "bg-black text-white border-black" : "bg-white text-zinc-400 border-zinc-100"}`}
                >
                  {cat}
                  <ChevronRight className={`w-4 h-4 ${selectedCategory === cat ? "text-white" : "text-zinc-200"}`} />
                </button>
                ))}
              </nav>
            </div>

            <div className="p-8 border border-zinc-200 bg-white rounded-sm">
              <div className="text-[10px] font-bold text-black tracking-[0.2em] uppercase mb-6 border-b border-zinc-100 pb-4">
                Xu hướng
              </div>
              <div className="space-y-6">
                {trending.length > 0 ? (
                  trending.map((document, i) => (
                    <Link
                      key={`trending-${document._id || i}`}
                      href={`/documents/${document.slug}`}
                      className="block space-y-2"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-[10px] font-bold text-zinc-200">
                          0{i + 1}
                        </span>
                        <div className="h-[1px] flex-1 bg-zinc-100" />
                      </div>
                      <h4 className="text-[13px] font-bold leading-tight text-black tracking-tight uppercase">
                        {document.title}
                      </h4>
                      <div className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                        {document.views_count?.toLocaleString("vi-VN") || 0} lượt xem
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="py-4 flex flex-col items-center justify-center gap-3 opacity-20">
                    <p className="text-[9px] font-bold uppercase tracking-widest text-center">
                      Analysis in progress
                    </p>
                  </div>
                )}
              </div>
            </div>
          </aside>

          <main className="lg:col-span-9 space-y-16">
            {recommendations.length > 0 && !searchQuery && (
              <section className="space-y-8">
                <div className="flex items-center gap-3 border-b border-zinc-200 pb-6">
                  <h2 className="text-xl font-bold uppercase tracking-tight">
                    Gợi ý dành riêng cho bạn
                  </h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {recommendations.map((doc, i) => (
                    <Link
                      key={`rec-${doc._id || i}`}
                      href={`/documents/${doc.slug}`}
                      className="flex gap-6 p-6 border border-zinc-200 bg-white rounded-sm"
                    >
                      <div className="w-24 h-32 bg-zinc-100 shrink-0 border border-zinc-200 rounded-sm overflow-hidden grayscale">
                        {doc.cover_url ? (
                          <img
                            src={doc.cover_url}
                            alt=""
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full bg-zinc-50" />
                        )}
                      </div>
                      <div className="flex-1 space-y-3">
                        <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-[0.3em]">
                          {doc.categories?.[0] || "Tài liệu"}
                        </span>
                        <h3 className="text-base font-bold leading-tight uppercase tracking-tight">
                          {doc.title}
                        </h3>
                        <div className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">
                          Tác giả: {doc.author?.full_name || doc.author?.username || "Ẩn danh"}
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </section>
            )}

            <section className="space-y-8">
              <div className="flex items-center justify-between border-b border-zinc-200 pb-6">
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-bold uppercase tracking-tight">
                    {searchQuery
                      ? `Kết quả tìm kiếm cho ${searchQuery}`
                      : "Kho tàng tri thức"}
                  </h2>
                </div>
              </div>

              {loading ? (
                <div
                  className={`grid gap-8 ${viewMode === "grid" ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"}`}
                >
                  {[1, 2, 3, 4, 5, 6].map((i) => (
                    <div
                      key={i}
                      className={`bg-white border border-zinc-200 rounded-sm ${viewMode === "grid" ? "aspect-[3/4]" : "h-32"}`}
                    />
                  ))}
                </div>
              ) : documents.length > 0 ? (
                <div
                  className={`grid gap-10 ${viewMode === "grid" ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"}`}
                >
                  {documents.map((document, i) => (
                    <Link
                      key={`doc-${document._id || i}`}
                      href={`/documents/${document.slug}`}
                      className={`border border-zinc-200 p-6 bg-white rounded-sm ${viewMode === "grid" ? "space-y-5" : "flex gap-8 items-center"}`}
                    >
                      <div
                        className={`${viewMode === "grid" ? "aspect-[3/4] w-full" : "w-32 h-44 shrink-0"} bg-zinc-100 border border-zinc-200 rounded-sm relative overflow-hidden grayscale`}
                      >
                        {document.cover_url ? (
                          <img
                            src={document.cover_url}
                            alt={document.title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full bg-zinc-50" />
                        )}
                        <div className="absolute inset-0 bg-black/0" />
                      </div>
                      <div
                        className={`${viewMode === "grid" ? "space-y-3" : "flex-1 space-y-3"}`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                            {document.categories?.[0] || "Tài liệu"}
                          </span>
                        </div>
                        <h3
                          className={`${viewMode === "grid" ? "text-base" : "text-xl"} font-bold leading-tight text-black tracking-tight uppercase`}
                        >
                          {document.title}
                        </h3>
                        <div className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">
                          Tác giả: {document.author?.full_name || document.author?.username || "Ẩn danh"}
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="py-48 flex flex-col items-center justify-center border border-zinc-200 bg-white rounded-sm">
                  <div className="w-24 h-24 border border-zinc-200 bg-zinc-50 flex items-center justify-center mb-10 rounded-sm" />
                  <h2 className="text-2xl font-bold tracking-tighter text-black mb-4 uppercase">
                    Không tìm thấy thực thể phù hợp
                  </h2>
                  <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest text-center max-w-xs leading-loose">
                    Hãy thay đổi tiêu chí tìm kiếm hoặc khám phá các danh mục khác
                  </p>
                </div>
              )}
            </section>
          </main>
        </div>
      </div>
    </>
  );
}
