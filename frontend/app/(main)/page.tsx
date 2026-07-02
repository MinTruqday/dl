"use client";
import { useEffect, useState, useCallback } from "react";
import { getDocumentsAPI } from "@/features/content/services/document.service";
import {
  getTagsCategoriesAPI,
  getAIRecommendationsAPI,
  smartSearchAPI,
} from "@/features/content/services/discovery.service";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import Link from "next/link";
import { useToast } from "@/shared/contexts/ToastContext";
import { LayoutGrid, List as ListIcon, List, ChevronRight } from "lucide-react";

export default function ExplorePage() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [useSmart, setUseSmart] = useState(false);

  const { user } = useAuth();

  const loadInitialData = useCallback(async () => {
    try {
      const [catData, recData] = await Promise.all([
        getTagsCategoriesAPI(),
        getAIRecommendationsAPI(4),
      ]);
      setCategories(catData.data?.categories || catData.categories || []);
      setRecommendations(recData.data || recData || []);
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
      className={`bg-[#F5F5F7] rounded-[18px] overflow-hidden animate-pulse ${
        mode === "grid" ? "flex flex-col" : "flex flex-row gap-4 p-4"
      }`}
    >
      <div
        className={`bg-[#D2D2D7] ${mode === "grid" ? "aspect-[4/3] w-full" : "w-6 h-6 shrink-0 rounded-[10px]"}`}
      />
      {mode === "grid" && (
        <div className="p-4 space-y-3">
          <div className="h-3 w-1/3 bg-[#D2D2D7] rounded-full" />
          <div className="h-4 w-full bg-[#D2D2D7] rounded-full" />
          <div className="h-4 w-2/3 bg-[#D2D2D7] rounded-full" />
        </div>
      )}
    </div>
  );

  return (
    <div className="w-full max-w-[1200px] mx-auto px-6 py-6 font-sans text-[#1D1D1F]">
      <div className="flex flex-col md:flex-row gap-6">
        <aside className="w-full md:w-[320px] shrink-0 space-y-6 sticky top-0 h-fit">
          <div className="bg-[#F5F5F7] rounded-[18px] p-6">
            <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
              Phân loại
            </p>
            <nav className="flex flex-col gap-1.5">
              <button
                onClick={() => setSelectedCategory(null)}
                className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${
                  !selectedCategory
                    ? "bg-white text-[#0071E3] font-medium"
                    : "text-[#1D1D1F] hover:bg-[#E8E8ED]"
                }`}
              >
                <span>Tất cả tài liệu</span>
                {!selectedCategory && <ChevronRight className="w-6 h-6" />}
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() =>
                    setSelectedCategory(selectedCategory === cat ? null : cat)
                  }
                  className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${
                    selectedCategory === cat
                      ? "bg-white text-[#0071E3] font-medium"
                      : "text-[#1D1D1F] hover:bg-[#E8E8ED]"
                  }`}
                >
                  <span className="truncate text-left">{cat}</span>
                  {selectedCategory === cat && (
                    <ChevronRight className="w-6 h-6 shrink-0" />
                  )}
                </button>
              ))}
            </nav>
          </div>

          
        </aside>

        <main className="flex-1 min-w-0 space-y-8 pt-6">
          {recommendations.length > 0 && !searchQuery && (
            <section className="bg-[#F5F5F7] rounded-[18px] p-6">
              <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-6">
                Gợi ý dành cho bạn
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {recommendations.map((doc, i) => (
                  <Link
                    key={`rec-${doc._id || i}`}
                    href={`/document/${doc.slug}`}
                    className="flex gap-4 p-4 bg-white rounded-[18px] transition-transform hover:scale-[1.02]"
                  >
                    <div className="w-[88px] h-[88px] shrink-0 bg-[#F5F5F7] rounded-[10px] overflow-hidden">
                      {doc.cover_url ? (
                        <img
                          src={doc.cover_url}
                          alt={doc.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full bg-[#F5F5F7]" />
                      )}
                    </div>
                    <div className="flex-1 flex flex-col min-w-0">
                      <span className="text-[12px] font-medium text-[#0071E3] mb-1">
                        {doc.categories?.[0] || "Tài liệu"}
                      </span>
                      <h3 className="text-[17px] font-medium text-[#1D1D1F] line-clamp-2 leading-snug mb-2">
                        {doc.title}
                      </h3>
                      <div className="mt-auto text-[13px] text-[#6E6E73] truncate">
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

          <section>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
                {searchQuery ? `Kết quả cho "${searchQuery}"` : "Kho nội dung"}
              </h2>
              <div className="flex items-center">
                <div className="flex bg-[#E8E8ED] p-[2px] rounded-full shrink-0">
                  <button
                    onClick={() => setViewMode("grid")}
                    className={`p-1 rounded-full transition-colors ${viewMode === "grid" ? "bg-white text-[#1D1D1F]" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
                  >
                    <LayoutGrid className="w-6 h-6" />
                  </button>
                  <button
                    onClick={() => setViewMode("list")}
                    className={`p-1 rounded-full transition-colors ${viewMode === "list" ? "bg-white text-[#1D1D1F]" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
                  >
                    <List className="w-6 h-6" />
                  </button>
                </div>
              </div>
            </div>

            {loading ? (
              <div
                className={`grid gap-6 ${
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
                className={`grid gap-6 ${
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
                      viewMode === "grid"
                        ? "flex-col"
                        : "flex-row gap-6 p-4 items-center"
                    } bg-[#F5F5F7] rounded-[18px] overflow-hidden transition-transform hover:scale-[1.02]`}
                  >
                    <div
                      className={`${
                        viewMode === "grid"
                          ? "aspect-[4/3] w-full"
                          : "w-[120px] h-[120px] shrink-0 rounded-[10px]"
                      } bg-white relative overflow-hidden`}
                    >
                      {document.cover_url ? (
                        <img
                          src={document.cover_url}
                          alt={document.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full bg-white" />
                      )}
                    </div>

                    <div
                      className={`${
                        viewMode === "grid" ? "p-5" : "flex-1"
                      } flex flex-col gap-2`}
                    >
                      {document.categories &&
                        document.categories.length > 0 && (
                          <div className="flex flex-wrap gap-2 mb-1">
                            {document.categories
                              .slice(0, 1)
                              .map((tag: string, idx: number) => (
                                <span
                                  key={idx}
                                  className="text-[12px] font-medium text-[#0071E3]"
                                >
                                  {tag}
                                </span>
                              ))}
                          </div>
                        )}

                      <h3
                        className={`${
                          viewMode === "grid" ? "text-[17px]" : "text-[20px]"
                        } font-medium text-[#1D1D1F] line-clamp-2 leading-snug`}
                      >
                        {document.title}
                      </h3>

                      <div className="text-[13px] text-[#6E6E73] flex items-center gap-2">
                        <span className="truncate">
                          {document.author?.full_name ||
                            document.author?.username ||
                            "Ẩn danh"}
                        </span>
                        <span>•</span>
                        <span className="shrink-0">
                          {document.created_at
                            ? new Date(document.created_at).toLocaleDateString(
                                "vi-VN",
                              )
                            : "Gần đây"}
                        </span>
                      </div>

                      <div className="flex items-center gap-4 text-[13px] text-[#6E6E73] mt-2">
                        <span>
                          {document.views_count?.toLocaleString("vi-VN") || 0}{" "}
                          lượt xem
                        </span>
                        <span>
                          {document.average_rating?.toFixed(1) || "0.0"} sao
                        </span>
                        <span>{document.chapters_count || 0} chương</span>
                      </div>

                      <div className="mt-4 pt-4 flex items-center justify-between">
                        <span className="text-[15px] font-medium text-[#1D1D1F]">
                          {document.is_premium
                            ? `${document.price || 0} dl`
                            : "Miễn phí"}
                        </span>
                        <span className="text-[15px] text-[#0071E3] font-medium">
                          Xem chi tiết
                        </span>
                      </div>
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
        </main>
      </div>
    </div>
  );
}
