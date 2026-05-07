"use client";
import { useEffect, useState, useCallback } from "react";
import {
  getDocumentsAPI,
  getTagsCategoriesAPI,
  getTrendingDocumentsAPI,
  getAIRecommendationsAPI,
} from "@/services/document.service";
import { semanticSearchAPI } from "@/services/search.service";
import { useAuth } from "@/contexts/AuthContext";
import Link from "next/link";
import { useToast } from "@/contexts/ToastContext";
import {
  ChevronRight,
  LayoutGrid,
  List as ListIcon,
  Eye,
  Star,
  BookOpen,
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
      showToast("Lỗi tải dữ liệu khám phá", "error");
    }
  }, [showToast]);

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
      showToast("Lỗi tải danh sách tài liệu", "error");
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, searchQuery, useSemantic, showToast]);

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
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <div className="mb-10 relative h-[120px] md:h-[200px] bg-zinc-50 border border-zinc-200 flex items-center justify-center rounded-none">
        <p className="text-zinc-500 text-sm font-medium">
          Liên hệ quảng cáo với DocLib
        </p>
      </div>

      <div className="mb-8 border-b border-zinc-200 pb-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-3xl font-semibold text-black">Khám phá</h1>
            <p className="text-zinc-500 text-sm font-medium">
              Tìm kiếm và kết nối với nguồn nội dung mới nhất
            </p>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex border border-zinc-200 bg-white rounded-none">
              <button
                onClick={() => setViewMode("grid")}
                className={`p-2 ${
                  viewMode === "grid"
                    ? "bg-zinc-100 text-black"
                    : "bg-transparent text-zinc-500"
                }`}
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <div className="w-[1px] bg-zinc-200" />
              <button
                onClick={() => setViewMode("list")}
                className={`p-2 ${
                  viewMode === "list"
                    ? "bg-zinc-100 text-black"
                    : "bg-transparent text-zinc-500"
                }`}
              >
                <ListIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <aside className="lg:col-span-3 space-y-12">
          <div className="space-y-4">
            <div className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
              Phân loại
            </div>
            <nav className="flex flex-col gap-1">
              <button
                onClick={() => setSelectedCategory(null)}
                className={`flex items-center justify-between px-3 py-2 text-sm font-medium border rounded-none ${
                  !selectedCategory
                    ? "bg-zinc-100 text-black border-zinc-300"
                    : "bg-white text-zinc-500 border-transparent"
                }`}
              >
                Tất cả tài liệu
                {!selectedCategory && <ChevronRight className="w-4 h-4" />}
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() =>
                    setSelectedCategory(selectedCategory === cat ? null : cat)
                  }
                  className={`flex items-center justify-between px-3 py-2 text-sm font-medium border rounded-none ${
                    selectedCategory === cat
                      ? "bg-zinc-100 text-black border-zinc-300"
                      : "bg-white text-zinc-500 border-transparent"
                  }`}
                >
                  {cat}
                  {selectedCategory === cat && (
                    <ChevronRight className="w-4 h-4" />
                  )}
                </button>
              ))}
            </nav>
          </div>

          <div className="space-y-4">
            <div className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
              Xu hướng
            </div>
            <div className="flex flex-col gap-4">
              {trending.length > 0 ? (
                trending.map((document, i) => (
                  <Link
                    key={`trending-${document._id || i}`}
                    href={`/documents/${document.slug}`}
                    className="flex gap-3 group"
                  >
                    <span className="text-sm font-semibold text-zinc-400 w-4">
                      {i + 1}
                    </span>
                    <div className="space-y-1">
                      <h4 className="text-sm font-medium text-black line-clamp-2 leading-snug">
                        {document.title}
                      </h4>
                      <div className="text-xs font-medium text-zinc-500">
                        {document.views_count?.toLocaleString("vi-VN") || 0}{" "}
                        lượt xem
                      </div>
                    </div>
                  </Link>
                ))
              ) : (
                <div className="py-4 flex items-center justify-center">
                  <p className="text-sm font-medium text-zinc-500">
                    Đang phân tích
                  </p>
                </div>
              )}
            </div>
          </div>
        </aside>

        <main className="lg:col-span-9 space-y-12">
          {recommendations.length > 0 && !searchQuery && (
            <section className="space-y-6">
              <div className="border-b border-zinc-200 pb-2">
                <h2 className="text-lg font-semibold text-black">
                  Gợi ý dành riêng cho bạn
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {recommendations.map((doc, i) => (
                  <Link
                    key={`rec-${doc._id || i}`}
                    href={`/documents/${doc.slug}`}
                    className="flex gap-4 p-4 border border-zinc-200 bg-white rounded-none"
                  >
                    <div className="w-20 h-28 shrink-0 bg-zinc-100 border border-zinc-200 overflow-hidden relative">
                      {doc.cover_url ? (
                        <img
                          src={doc.cover_url}
                          alt={doc.title}
                          className="w-full h-full object-cover grayscale mix-blend-multiply"
                        />
                      ) : (
                        <div className="w-full h-full bg-zinc-100" />
                      )}
                    </div>
                    <div className="flex-1 flex flex-col space-y-2">
                      <span className="text-xs font-medium text-zinc-500">
                        {doc.categories?.[0] || "Tài liệu"}
                      </span>
                      <h3 className="text-sm font-semibold text-black line-clamp-2 leading-snug">
                        {doc.title}
                      </h3>
                      <div className="mt-auto text-xs font-medium text-zinc-500">
                        {doc.author?.full_name ||
                          doc.author?.username ||
                          "Ẩn danh"}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}

          <section className="space-y-6">
            <div className="border-b border-zinc-200 pb-2 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-black">
                {searchQuery
                  ? `Kết quả tìm kiếm cho "${searchQuery}"`
                  : "Kho nội dung"}
              </h2>
            </div>

            {loading ? (
              <div
                className={`grid gap-6 ${
                  viewMode === "grid"
                    ? "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
                    : "grid-cols-1"
                }`}
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                  <div
                    key={i}
                    className={`bg-zinc-50 border border-zinc-200 ${
                      viewMode === "grid" ? "aspect-[2/3]" : "h-32"
                    }`}
                  />
                ))}
              </div>
            ) : documents.length > 0 ? (
              <div
                className={`grid gap-6 ${
                  viewMode === "grid"
                    ? "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
                    : "grid-cols-1"
                }`}
              >
                {documents.map((document, i) => (
                  <Link
                    key={`doc-${document._id || i}`}
                    href={`/documents/${document.slug}`}
                    className={`group flex ${
                      viewMode === "grid"
                        ? "flex-col"
                        : "flex-row gap-6 p-4"
                    } border border-zinc-200 bg-white rounded-none`}
                  >
                    <div
                      className={`${
                        viewMode === "grid"
                          ? "aspect-[2/3] w-full border-b"
                          : "w-24 h-36 shrink-0 border"
                      } border-zinc-200 bg-zinc-100 relative overflow-hidden`}
                    >
                      {document.cover_url ? (
                        <img
                          src={document.cover_url}
                          alt={document.title}
                          className="w-full h-full object-cover grayscale mix-blend-multiply"
                        />
                      ) : (
                        <div className="w-full h-full bg-zinc-100" />
                      )}
                    </div>

                    <div
                      className={`${
                        viewMode === "grid" ? "p-3" : "flex-1 py-1"
                      } flex flex-col flex-1 gap-2`}
                    >
                      {document.categories && document.categories.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {document.categories
                            .slice(0, 3)
                            .map((tag: string, idx: number) => (
                              <span
                                key={idx}
                                className="px-1.5 py-0.5 text-[10px] font-medium text-zinc-600 border border-zinc-200 bg-white"
                              >
                                {tag}
                              </span>
                            ))}
                        </div>
                      )}

                      <h3
                        className={`${
                          viewMode === "grid" ? "text-sm" : "text-base"
                        } font-semibold text-black line-clamp-2 leading-snug`}
                      >
                        {document.title}
                      </h3>

                      <div className="text-xs text-zinc-500 flex items-center gap-1.5">
                        <span className="truncate text-black font-medium">
                          {document.author?.full_name ||
                            document.author?.username ||
                            "Ẩn danh"}
                        </span>
                        <span>•</span>
                        <span className="shrink-0">
                          {document.created_at
                            ? new Date(document.created_at).toLocaleDateString(
                                "vi-VN"
                              )
                            : "Gần đây"}
                        </span>
                      </div>

                      <div className="flex items-center gap-3 text-xs text-zinc-500">
                        <div className="flex items-center gap-1">
                          <Eye className="w-3.5 h-3.5" />
                          <span>
                            {document.views_count?.toLocaleString("vi-VN") || 0}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Star className="w-3.5 h-3.5" />
                          <span>
                            {document.average_rating?.toFixed(1) || "0.0"}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <BookOpen className="w-3.5 h-3.5" />
                          <span>{document.chapters_count || 0}</span>
                        </div>
                      </div>

                      <div
                        className={`mt-auto pt-3 flex items-center justify-between ${
                          viewMode === "grid" ? "border-t border-zinc-100" : ""
                        }`}
                      >
                        <span className="text-xs font-semibold text-black">
                          {document.is_premium
                            ? `${document.price || 0} dl`
                            : "Miễn phí"}
                        </span>
                        <div className="text-xs font-semibold text-black border border-black px-3 py-1.5 uppercase tracking-wider">
                          Xem
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white">
                <p className="text-sm font-medium text-black mb-2">
                  Không tìm thấy tài liệu phù hợp
                </p>
                <p className="text-xs text-zinc-500">
                  Hãy thay đổi tiêu chí tìm kiếm hoặc khám phá các danh mục khác.
                </p>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}
