"use client";
import { useEffect, useState, useCallback } from "react";
import { 
  getDocumentsAPI, 
  getTagsCategoriesAPI, 
  getTrendingDocumentsAPI, 
  getAIRecommendationsAPI,
  getFeaturedAuthorsAPI,
  semanticSearchAPI,
  API_URL 
} from "@/app/lib/api";
import { useAuth } from "@/app/contexts/AuthContext";
import Link from "next/link";
import { 
  Search, 
  Filter, 
  TrendingUp, 
  ChevronRight, 
  Sparkles,
  LayoutGrid,
  List as ListIcon,
  FileText,
  Activity,
  Zap,
  User,
  Clock
} from "lucide-react";

export default function ExplorePage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [trending, setTrending] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [featuredAuthors, setFeaturedAuthors] = useState<any[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [banners, setBanners] = useState<any[]>([]);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [useSemantic, setUseSemantic] = useState(false);
  const [activeBanner, setActiveBanner] = useState(0);
  const [visible, setVisible] = useState(false);

  const loadInitialData = useCallback(async () => {
    try {
      const [catData, trendData, recData, authorData] = await Promise.all([
        getTagsCategoriesAPI(),
        getTrendingDocumentsAPI(3),
        getAIRecommendationsAPI(4),
        getFeaturedAuthorsAPI(5)
      ]);
      setCategories(catData.data?.categories || catData.categories || []);
      setTrending(trendData.data || trendData || []);
      setRecommendations(recData.data || recData || []);
      setFeaturedAuthors(authorData.data || authorData || []);
      
      const bannerRes = await fetch(`${API_URL}/guest/banners`);
      if (bannerRes.ok) {
        const data = await bannerRes.json();
        setBanners(data.data || []);
      }
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
        data = await getDocumentsAPI(searchQuery || undefined, "latest", selectedCategory || undefined);
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
    requestAnimationFrame(() => setVisible(true));
  }, [loadInitialData]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      loadDocuments();
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [loadDocuments]);

  useEffect(() => {
    if (banners.length > 1) {
      const interval = setInterval(() => {
        setActiveBanner((prev) => (prev + 1) % banners.length);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [banners.length]);

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      <div 
        className="mb-12 relative h-[400px] bg-zinc-900 overflow-hidden group transition-all duration-300"
        style={{ 
          opacity: visible ? 1 : 0, 
          transform: visible ? "translateY(0)" : "translateY(20px)" 
        }}
      >
        {banners.length > 0 ? (
          banners.map((banner, idx) => (
            <div
              key={idx}
              className={`absolute inset-0 transition-all duration-300 ease-in-out ${
                idx === activeBanner ? "opacity-100 scale-100" : "opacity-0 scale-110 pointer-events-none"
              }`}
            >
              <img
                src={banner.image_url}
                className="w-full h-full object-cover grayscale opacity-40"
                alt=""
              />
              <div className="absolute inset-0 bg-gradient-to-r from-black via-black/40 to-transparent" />
              <div className="absolute inset-0 flex flex-col justify-center px-16 max-w-4xl space-y-6">
                <span className="text-[10px] font-bold text-white/40 tracking-[0.4em] uppercase animate-in slide-in-from-left-4 duration-300">
                  Tiêu điểm tri thức
                </span>
                <h2 className="text-6xl font-bold text-white tracking-tighter leading-[0.9] animate-in slide-in-from-left-8 duration-300">
                  {banner.title}
                </h2>
                <p className="text-white/60 text-lg font-medium leading-relaxed max-w-xl animate-in slide-in-from-left-12 duration-300">
                  {banner.description}
                </p>
                <div className="animate-in slide-in-from-left-16 duration-300">
                  <Link
                    href={banner.link || "#"}
                    className="inline-flex items-center justify-center h-14 px-12 bg-white text-black text-sm font-bold hover:bg-zinc-200 transition-all active:scale-95 w-fit border border-white"
                  >
                    Khám phá ngay
                  </Link>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="absolute inset-0 flex items-center px-16 overflow-hidden">
            <div className="absolute inset-0 bg-zinc-950">
               <div className="absolute top-[-10%] right-[-10%] w-[60%] h-[120%] bg-white/[0.03] rotate-12 blur-3xl animate-pulse" />
               <div className="absolute bottom-[-20%] left-[-5%] w-[40%] h-[100%] bg-white/[0.03] -rotate-12 blur-3xl animate-pulse" />
            </div>
            <div className="relative z-10 max-w-3xl space-y-6">
              <div className="flex items-center gap-3 text-white/20 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <Sparkles className="w-4 h-4" />
                <span className="text-[10px] font-bold tracking-[0.6em] uppercase">Khám phá vũ trụ tri thức</span>
              </div>
              <h2 className="text-7xl font-bold text-white tracking-tighter leading-[0.9] animate-in fade-in slide-in-from-bottom-4 duration-300">
                Mở rộng <br/> <span className="text-white/20 italic">Giới hạn tri thức</span>
              </h2>
              <p className="text-white/40 text-lg font-medium leading-relaxed max-w-xl animate-in fade-in slide-in-from-bottom-6 duration-300">
                Hàng ngàn tài liệu, nghiên cứu và bài viết chuyên sâu từ cộng đồng chuyên gia hàng đầu đang chờ đón bạn.
              </p>
              <div className="pt-2 animate-in fade-in slide-in-from-bottom-8 duration-300">
                <button className="h-14 px-12 bg-white text-black text-sm font-bold hover:bg-zinc-200 transition-all active:scale-95 border border-white">
                  Bắt đầu hành trình
                </button>
              </div>
            </div>
          </div>
        )}

        {banners.length > 1 && (
          <div className="absolute bottom-10 right-16 flex gap-4 z-10">
            {banners.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setActiveBanner(idx)}
                className={`h-1 transition-all duration-300 ${
                  idx === activeBanner ? "w-12 bg-white" : "w-6 bg-white/20 hover:bg-white/40"
                }`}
              />
            ))}
          </div>
        )}
      </div>

      <div 
        className="mb-12 border-b border-zinc-100 pb-10 flex flex-col md:flex-row md:items-end justify-between gap-8 transition-all duration-300 delay-150"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <div className="space-y-3">
          <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">Khám phá</h1>
          <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest">
            Khám phá tri thức mới nhất
          </p>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex border border-zinc-100 p-1 bg-zinc-50/50">
            <button 
              onClick={() => setViewMode("grid")}
              className={`p-3 transition-all active:scale-95 border ${viewMode === "grid" ? "bg-white border-zinc-200" : "border-transparent"}`}
            >
              <LayoutGrid className={`w-4 h-4 ${viewMode === "grid" ? "text-black" : "text-zinc-300"}`} />
            </button>
            <button 
              onClick={() => setViewMode("list")}
              className={`p-3 transition-all active:scale-95 border ${viewMode === "list" ? "bg-white border-zinc-200" : "border-transparent"}`}
            >
              <ListIcon className={`w-4 h-4 ${viewMode === "list" ? "text-black" : "text-zinc-300"}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="mb-12 transition-all duration-300 delay-200" style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}>
        <div className="flex flex-col md:flex-row items-center gap-6">
          <div className="relative flex-1 group">
            <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-300 group-focus-within:text-black transition-colors" />
            <input 
              type="text"
              placeholder={useSemantic ? "Nhập ý tưởng để tìm kiếm tri thức bằng AI" : "Tìm kiếm tên tài liệu hoặc chủ đề tri thức"}
              className="w-full h-14 pl-14 pr-6 bg-zinc-50/50 border border-zinc-100 focus:bg-white focus:border-black outline-none text-sm font-medium transition-all"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button 
            onClick={() => setUseSemantic(!useSemantic)}
            className={`h-14 px-8 flex items-center gap-3 border transition-all active:scale-95 ${useSemantic ? "bg-black text-white border-black" : "bg-white text-black border-zinc-100 hover:border-black"}`}
          >
            <Zap className={`w-4 h-4 ${useSemantic ? "text-yellow-400 fill-yellow-400" : "text-zinc-300"}`} />
            <span className="text-[11px] font-bold uppercase tracking-widest">Tìm kiếm AI</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <aside 
          className="lg:col-span-3 space-y-12 transition-all duration-300 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="space-y-6">
            <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-[0.2em] px-1">
              <Filter className="w-4 h-4 text-zinc-300" /> Phân loại
            </div>
            <nav className="flex flex-col gap-1">
              <button
                onClick={() => setSelectedCategory(null)}
                className={`flex items-center justify-between px-6 py-4 text-[11px] font-bold uppercase tracking-widest transition-all border ${
                  !selectedCategory 
                    ? "bg-black text-white border-black" 
                    : "bg-white text-zinc-400 border-zinc-100 hover:bg-zinc-50 hover:text-black"
                }`}
              >
                Tất cả tài liệu
                <ChevronRight className={`w-3.5 h-3.5 transition-transform ${!selectedCategory ? "rotate-90" : ""}`} />
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`flex items-center justify-between px-6 py-4 text-[11px] font-bold uppercase tracking-widest transition-all border ${
                    selectedCategory === cat
                      ? "bg-black text-white border-black"
                      : "bg-white text-zinc-400 border-zinc-100 hover:bg-zinc-50 hover:text-black"
                  }`}
                >
                  {cat}
                  <ChevronRight className={`w-3.5 h-3.5 transition-transform ${selectedCategory === cat ? "rotate-90" : ""}`} />
                </button>
              ))}
            </nav>
          </div>

          <div className="p-8 border border-zinc-100 bg-zinc-50/50 space-y-8">
            <div className="flex items-center gap-3 text-[11px] font-bold text-black tracking-[0.2em] uppercase">
              <Activity className="w-4 h-4 text-zinc-300" />
              Xu hướng
            </div>
            <div className="space-y-6">
              {trending.length > 0 ? trending.map((document, i) => (
                <Link key={document._id} href={`/document/${document.slug}`} className="group block space-y-2">
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] font-bold text-black/20">0{i + 1}</span>
                    <div className="h-[1px] flex-1 bg-zinc-100 group-hover:bg-black transition-colors" />
                  </div>
                  <h4 className="text-[14px] font-bold leading-tight group-hover:underline underline-offset-4 decoration-1 text-black tracking-tight uppercase">
                    {document.title}
                  </h4>
                  <div className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                    {document.views_count || 0} Lượt xem
                  </div>
                </Link>
              )) : (
                <div className="py-4 flex flex-col items-center justify-center gap-3 opacity-20">
                   <TrendingUp className="w-6 h-6" />
                   <p className="text-[9px] font-bold uppercase tracking-widest text-center">Đang phân tích</p>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-[0.2em] px-1">
              <User className="w-4 h-4 text-zinc-300" /> Tác giả tiêu điểm
            </div>
            <div className="space-y-3">
              {featuredAuthors.map((author) => (
                <Link key={author.id} href={`/authors/${author.slug}`} className="flex items-center gap-4 group p-3 border border-transparent hover:border-zinc-100 transition-all bg-zinc-50/30">
                  <div className="w-10 h-10 bg-zinc-100 border border-zinc-100 overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-300">
                    {author.avatar_url ? (
                      <img src={author.avatar_url} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <User className="w-5 h-5 text-zinc-300 stroke-[1]" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-bold text-black uppercase tracking-tight truncate">{author.full_name}</p>
                    <p className="text-[9px] text-zinc-400 font-bold uppercase tracking-widest mt-0.5">{author.document_count || 0} Tác phẩm</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          <div className="p-8 border border-zinc-100 text-center">
             <p className="text-[11px] font-medium italic text-zinc-400 leading-relaxed">
               "Hành trình vạn dặm bắt đầu từ một trang sách"
             </p>
          </div>
        </aside>

        <main 
          className="lg:col-span-9 space-y-12 transition-all duration-300 delay-500"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {recommendations.length > 0 && !searchQuery && (
            <section className="space-y-8">
              <div className="flex items-center gap-3 border-b border-zinc-100 pb-6">
                <Sparkles className="w-5 h-5 text-zinc-300" />
                <h2 className="text-xl font-bold uppercase tracking-tight">Gợi ý dành riêng cho bạn</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {recommendations.map((doc) => (
                  <Link key={doc._id} href={`/document/${doc.slug}`} className="flex gap-6 p-6 border border-zinc-100 hover:border-black transition-all group bg-white">
                    <div className="w-24 h-32 bg-zinc-50 shrink-0 border border-zinc-100 overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-300">
                      {doc.cover_url ? (
                        <img src={doc.cover_url} alt="" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <FileText className="w-8 h-8 text-zinc-200 stroke-[1]" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 space-y-3">
                      <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-[0.3em]">{doc.categories?.[0] || "Tri thức"}</span>
                      <h3 className="text-base font-bold leading-tight group-hover:underline underline-offset-4 decoration-1 uppercase tracking-tight">{doc.title}</h3>
                      <div className="flex items-center gap-4 text-[9px] font-bold text-zinc-300 uppercase tracking-widest pt-1">
                        <Clock className="w-3 h-3" />
                        {new Date(doc.created_at).toLocaleDateString("vi-VN")}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}

          <section className="space-y-8">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-6">
              <div className="flex items-center gap-3">
                <LayoutGrid className="w-5 h-5 text-zinc-300" />
                <h2 className="text-xl font-bold uppercase tracking-tight">
                  {searchQuery ? `Kết quả: ${searchQuery}` : "Kho tàng tri thức"}
                </h2>
              </div>
            </div>

            {loading ? (
              <div className={`grid gap-8 ${viewMode === "grid" ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"}`}>
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className={`bg-zinc-50 border border-zinc-100 animate-pulse ${viewMode === "grid" ? "aspect-[3/4]" : "h-32"}`} />
                ))}
              </div>
            ) : documents.length > 0 ? (
              <div className={`grid gap-10 ${viewMode === "grid" ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"}`}>
                {documents.map((document) => (
                  <Link
                    key={document._id}
                    href={`/document/${document.slug}`}
                    className={`group animate-in fade-in slide-in-from-bottom-4 duration-300 ${viewMode === "grid" ? "space-y-5" : "flex gap-8 items-center border border-zinc-100 p-6 bg-white hover:border-black transition-all"}`}
                  >
                    <div className={`${viewMode === "grid" ? "aspect-[3/4] w-full" : "w-32 h-44 shrink-0"} bg-zinc-50 border border-zinc-100 relative overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-300`}>
                      {document.cover_url ? (
                        <img
                          src={document.cover_url}
                          alt={document.title}
                          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center p-8 text-center">
                          <FileText className="w-10 h-10 text-zinc-100 stroke-[1]" />
                        </div>
                      )}
                      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-300" />
                    </div>
                    <div className={`${viewMode === "grid" ? "space-y-3" : "flex-1 space-y-3"}`}>
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                          {document.categories?.[0] || "Knowledge"}
                        </span>
                        <span className="text-[10px] font-bold text-zinc-300 flex items-center gap-1.5">
                          <TrendingUp className="w-3 h-3" /> {document.views_count || 0}
                        </span>
                      </div>
                      <h3 className={`${viewMode === "grid" ? "text-base" : "text-xl"} font-bold leading-tight group-hover:underline underline-offset-4 decoration-1 text-black tracking-tight uppercase`}>
                        {document.title}
                      </h3>
                      <p className="text-[13px] text-zinc-400 line-clamp-2 leading-relaxed font-medium">
                        {document.description || "Khám phá nội dung chi tiết của tài liệu này trên DocLib"}
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="py-48 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/30">
                <div className="w-24 h-24 border border-zinc-100 bg-white flex items-center justify-center mb-10">
                  <Search className="w-10 h-10 text-zinc-100 stroke-[1]" />
                </div>
                <h2 className="text-2xl font-bold tracking-tighter text-black mb-4 uppercase">Không tìm thấy kết quả</h2>
                <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest text-center max-w-xs leading-loose">
                  Hãy thử thay đổi danh mục hoặc từ khóa để tìm kiếm tri thức khác
                </p>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}