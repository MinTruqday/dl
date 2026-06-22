"use client";
import { useEffect, useState, useCallback } from "react";
import { getDocumentsAPI } from "@/features/content/services/document_metadata.service";
import {
  getTagsCategoriesAPI,
  getTrendingDocumentsAPI,
  getAIRecommendationsAPI,
  smartSearchAPI,
} from "@/features/content/services/content_discovery.service";
import { getActiveBannersAPI } from "@/features/provision/services/promotional_banner.service";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import Link from "next/link";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  LayoutGrid,
  List as ListIcon,
  Eye,
  Star,
  BookOpen,
  TrendingUp,
  Sparkles,
  ChevronRight,
} from "lucide-react";

export default function ExplorePage() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<any[]>([]);
  const [trending, setTrending] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [useSmart, setUseSmart] = useState(false);
  const [banners, setBanners] = useState<any[]>([]);

  const { user } = useAuth();

  const loadInitialData = useCallback(async () => {
    try {
      const [catData, trendData, recData, bannerData] = await Promise.all([
        getTagsCategoriesAPI(),
        getTrendingDocumentsAPI(5),
        getAIRecommendationsAPI(4),
        getActiveBannersAPI().catch(() => ({ data: [] })),
      ]);
      setCategories(catData.data?.categories || catData.categories || []);
      setTrending(trendData.data || trendData || []);
      setRecommendations(recData.data || recData || []);
      setBanners(bannerData.data || bannerData || []);
    } catch (err) {
      showToast("Lỗi tải dữ liệu khám phá", "error");
    }
  }, [showToast]);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      let data;
      if (useSmart && searchQuery.trim()) {
        data = await smartSearchAPI(searchQuery);
      } else {
        data = await getDocumentsAPI(
          searchQuery || undefined,
          "latest",
          selectedCategory || undefined,
        );
      }
      setDocuments(data.data || data || []);
    } catch (err) {
      showToast("Lỗi tải danh sách tài liệu", "error");
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, searchQuery, useSmart, showToast]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      loadDocuments();
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [loadDocuments]);

  const SkeletonCard = ({ mode }: { mode: "grid" | "list" }) => (
    <div
      className={`bg-white border border-zinc-100 rounded-2xl overflow-hidden animate-pulse ${
        mode === "grid" ? "flex flex-col" : "flex flex-row gap-4 p-3"
      }`}
    >
      <div className={`bg-zinc-100 ${mode === "grid" ? "aspect-[2/3] w-full" : "w-20 h-28 shrink-0 rounded-xl"}`} />
      {mode === "grid" && (
        <div className="p-3 space-y-2">
          <div className="h-2 w-1/3 bg-zinc-100 rounded-full" />
          <div className="h-3 w-full bg-zinc-100 rounded-full" />
          <div className="h-3 w-2/3 bg-zinc-100 rounded-full" />
        </div>
      )}
    </div>
  );

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 font-sans text-zinc-900 selection:bg-zinc-900 selection:text-white">
      {banners.length > 0 && (
        <div className="mb-6 relative h-[120px] md:h-[180px] bg-white border border-zinc-100 flex items-center justify-center rounded-3xl overflow-hidden shadow-sm">
          <a
            href={banners[0].link_url || "#"}
            target="_blank"
            rel="noreferrer"
            className="w-full h-full block"
          >
            {banners[0].image_url ? (
              <img
                src={banners[0].image_url}
                alt={banners[0].title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center gap-2 bg-gradient-to-br from-zinc-50 to-zinc-100">
                <p className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Quảng cáo</p>
                <p className="text-base font-bold text-zinc-800">{banners[0].title}</p>
              </div>
            )}
          </a>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <aside className="lg:col-span-3 space-y-4">
          <div className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5">
            <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Phân loại</p>
            <nav className="flex flex-col gap-1">
              <button
                onClick={() => setSelectedCategory(null)}
                className={`flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 ${
                  !selectedCategory
                    ? "bg-zinc-900 text-white shadow-md"
                    : "text-zinc-500 hover:bg-zinc-50"
                }`}
              >
                <span>Tất cả tài liệu</span>
                {!selectedCategory && <ChevronRight className="w-3.5 h-3.5" />}
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() =>
                    setSelectedCategory(selectedCategory === cat ? null : cat)
                  }
                  className={`flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 ${
                    selectedCategory === cat
                      ? "bg-zinc-900 text-white shadow-md"
                      : "text-zinc-500 hover:bg-zinc-50"
                  }`}
                >
                  <span className="truncate text-left">{cat}</span>
                  {selectedCategory === cat && <ChevronRight className="w-3.5 h-3.5 shrink-0" />}
                </button>
              ))}
            </nav>
          </div>

          {trending.length > 0 && (
            <div className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-3.5 h-3.5 text-zinc-400" />
                <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Xu hướng</p>
              </div>
              <div className="flex flex-col gap-1">
                {trending.map((document, i) => (
                  <Link
                    key={`trending-${document._id || i}`}
                    href={`/document/${document.slug}`}
                    className="flex gap-3 items-start px-2 py-2.5 rounded-2xl transition-all duration-200 hover:scale-105 hover:-translate-y-1 hover:bg-zinc-50 hover:shadow-sm"
                  >
                    <span className="text-xs font-bold text-zinc-300 w-4 text-center shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    <div className="space-y-0.5 flex-1 min-w-0">
                      <h4 className="text-xs font-semibold text-zinc-800 line-clamp-2 leading-snug">
                        {document.title}
                      </h4>
                      <div className="text-[10px] font-medium text-zinc-400 flex items-center gap-1">
                        <Eye className="w-2.5 h-2.5" />
                        {document.views_count?.toLocaleString("vi-VN") || 0}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </aside>

        <main className="lg:col-span-9 space-y-5">
          {recommendations.length > 0 && !searchQuery && (
            <section className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <h2 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Gợi ý dành cho bạn</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {recommendations.map((doc, i) => (
                  <Link
                    key={`rec-${doc._id || i}`}
                    href={`/document/${doc.slug}`}
                    className="flex gap-3 p-3 border border-zinc-100 bg-white rounded-2xl shadow-sm transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1 hover:shadow-md"
                  >
                    <div className="w-16 h-22 shrink-0 bg-zinc-200 rounded-xl overflow-hidden relative" style={{ height: "88px" }}>
                      {doc.cover_url ? (
                        <img
                          src={doc.cover_url}
                          alt={doc.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full bg-zinc-200" />
                      )}
                    </div>
                    <div className="flex-1 flex flex-col gap-1 min-w-0">
                      <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-wider truncate">
                        {doc.categories?.[0] || "Tài liệu"}
                      </span>
                      <h3 className="text-xs font-semibold text-zinc-900 line-clamp-2 leading-snug">
                        {doc.title}
                      </h3>
                      <div className="mt-auto text-[10px] font-medium text-zinc-400 truncate">
                        {doc.author?.full_name || doc.author?.username || "Ẩn danh"}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}

          <section className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
              <h2 className="text-sm font-bold text-zinc-900">
                {searchQuery ? `Kết quả cho "${searchQuery}"` : "Kho nội dung"}
              </h2>
              <div className="flex items-center gap-2">
                <div className="flex border border-zinc-200 bg-zinc-50 rounded-2xl overflow-hidden p-0.5 gap-0.5">
                  <button
                    onClick={() => setViewMode("grid")}
                    className={`p-1.5 rounded-xl transition-all duration-200 hover:scale-110 ${
                      viewMode === "grid"
                        ? "bg-white text-zinc-900 shadow-sm"
                        : "bg-transparent text-zinc-400"
                    }`}
                  >
                    <LayoutGrid className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => setViewMode("list")}
                    className={`p-1.5 rounded-xl transition-all duration-200 hover:scale-110 ${
                      viewMode === "list"
                        ? "bg-white text-zinc-900 shadow-sm"
                        : "bg-transparent text-zinc-400"
                    }`}
                  >
                    <ListIcon className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>

            {loading ? (
              <div
                className={`grid gap-5 ${
                  viewMode === "grid"
                    ? "grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
                    : "grid-cols-1"
                }`}
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                  <SkeletonCard key={i} mode={viewMode} />
                ))}
              </div>
            ) : documents.length > 0 ? (
              <div
                className={`grid gap-5 ${
                  viewMode === "grid"
                    ? "grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
                    : "grid-cols-1"
                }`}
              >
                {documents.map((document, i) => (
                  <Link
                    key={`doc-${document._id || i}`}
                    href={`/document/${document.slug}`}
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
                      {document.cover_url ? (
                        <img
                          src={document.cover_url}
                          alt={document.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full bg-zinc-100" />
                      )}
                    </div>

                    <div
                      className={`${
                        viewMode === "grid" ? "p-3" : "flex-1 py-0.5"
                      } flex flex-col flex-1 gap-1.5`}
                    >
                      {document.categories && document.categories.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {document.categories.slice(0, 2).map((tag: string, idx: number) => (
                            <span
                              key={idx}
                              className="px-1.5 py-0.5 text-[9px] font-bold text-zinc-400 bg-zinc-100 rounded-lg uppercase tracking-wide"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      <h3
                        className={`${
                          viewMode === "grid" ? "text-xs" : "text-sm"
                        } font-semibold text-zinc-900 line-clamp-2 leading-snug`}
                      >
                        {document.title}
                      </h3>

                      <div className="text-[10px] text-zinc-400 flex items-center gap-1">
                        <span className="truncate font-medium text-zinc-600">
                          {document.author?.full_name || document.author?.username || "Ẩn danh"}
                        </span>
                        <span className="text-zinc-200">•</span>
                        <span className="shrink-0">
                          {document.created_at
                            ? new Date(document.created_at).toLocaleDateString("vi-VN")
                            : "Gần đây"}
                        </span>
                      </div>

                      <div className="flex items-center gap-2.5 text-[10px] text-zinc-400">
                        <div className="flex items-center gap-0.5">
                          <Eye className="w-3 h-3" />
                          <span>{document.views_count?.toLocaleString("vi-VN") || 0}</span>
                        </div>
                        <div className="flex items-center gap-0.5">
                          <Star className="w-3 h-3" />
                          <span>{document.average_rating?.toFixed(1) || "0.0"}</span>
                        </div>
                        <div className="flex items-center gap-0.5">
                          <BookOpen className="w-3 h-3" />
                          <span>{document.chapters_count || 0}</span>
                        </div>
                      </div>

                      <div
                        className={`mt-auto pt-2 flex items-center justify-between ${
                          viewMode === "grid" ? "border-t border-zinc-50" : ""
                        }`}
                      >
                        <span className="text-[10px] font-bold text-zinc-900">
                          {document.is_premium ? `${document.price || 0} dl` : "Miễn phí"}
                        </span>
                        <span className="text-[9px] font-bold text-zinc-500 bg-zinc-100 px-2.5 py-1 rounded-xl uppercase tracking-widest">
                          Xem
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="py-20 flex flex-col items-center justify-center border border-zinc-100 bg-zinc-50 rounded-2xl gap-3">
                <BookOpen className="w-8 h-8 text-zinc-200 stroke-[1.5]" />
                <p className="text-xs font-medium text-zinc-400">Chưa có dữ liệu</p>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}
