"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { 
  getDocumentsAPI, 
  getTagsCategoriesAPI, 
  getTrendingDocumentsAPI, 
  getAIRecommendationsAPI,
  getFeaturedAuthorsAPI,
  semanticSearchAPI,
  getBannersAPI
} from "@/app/lib/api";
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
  User,
  Zap,
  ArrowRight,
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
  const [error, setError] = useState<string | null>(null);

  const exploreRef = useRef<HTMLDivElement>(null);

  const loadInitialData = useCallback(async () => {
    try {
      const [catData, trendData, recData, authorData, bannerData] = await Promise.all([
        getTagsCategoriesAPI(),
        getTrendingDocumentsAPI(3),
        getAIRecommendationsAPI(4),
        getFeaturedAuthorsAPI(5),
        getBannersAPI()
      ]);
      setCategories(catData.data?.categories || catData.categories || []);
      setTrending(trendData.data || trendData || []);
      setRecommendations(recData.data || recData || []);
      setFeaturedAuthors(authorData.data || authorData || []);
      setBanners(bannerData.data || bannerData || []);
    } catch (err: any) {
      setError("Không thể tải toàn bộ dữ liệu khám phá. Vui lòng thử lại sau.");
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let data;
      if (useSemantic && searchQuery.trim()) {
        data = await semanticSearchAPI(searchQuery);
      } else {
        data = await getDocumentsAPI(searchQuery || undefined, "latest", selectedCategory || undefined);
      }
      setDocuments(data.data || data || []);
    } catch (err: any) {
      setError("Lỗi khi tìm kiếm tài liệu. Vui lòng kiểm tra lại kết nối.");
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, searchQuery, useSemantic]);

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
      }, 6000);
      return () => clearInterval(interval);
    }
  }, [banners.length]);

  const scrollToContent = () => {
    exploreRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-10 py-16 font-sans text-black selection:bg-black selection:text-white">
      <div 
        className="mb-16 relative h-[520px] bg-zinc-950 overflow-hidden transition-all duration-1000 rounded-sm"
        style={{ 
          opacity: visible ? 1 : 0, 
          transform: visible ? "translateY(0)" : "translateY(20px)" 
        }}
      >
        {banners.length > 0 ? (
          banners.map((banner, idx) => (
            <div
              key={idx}
              className={`absolute inset-0 transition-all duration-1000 ease-in-out ${
                idx === activeBanner ? "opacity-100 scale-100" : "opacity-0 scale-110 pointer-events-none"
              }`}
            >
              <img
                src={banner.image_url}
                className="w-full h-full object-cover grayscale opacity-30"
                alt=""
              />
              <div className="absolute inset-0 bg-gradient-to-r from-black via-black/20 to-transparent" />
              <div className="absolute inset-0 flex flex-col justify-center px-20 max-w-4xl space-y-8">
                <div className="flex items-center gap-4 animate-in slide-in-from-left-4 duration-500">
                    <div className="w-8 h-[1px] bg-white/20" />
                    <span className="text-[10px] font-bold text-white/40 tracking-[0.5em] uppercase">
                        Tiêu điểm tri thức
                    </span>
                </div>
                <h2 className="text-7xl font-bold text-white tracking-tighter leading-[0.85] animate-in slide-in-from-left-8 duration-700">
                  {banner.title}
                </h2>
                <p className="text-white/40 text-lg font-medium leading-relaxed max-w-xl animate-in slide-in-from-left-12 duration-1000">
                  {banner.description}
                </p>
                <div className="pt-4 animate-in slide-in-from-left-16 duration-1000">
                  <Link
                    href={banner.link || "#"}
                    className="inline-flex items-center justify-center h-16 px-14 bg-white text-black text-[11px] font-bold uppercase tracking-widest hover:bg-zinc-200 transition-all active:scale-95 w-fit rounded-sm"
                  >
                    Khám phá ngay
                  </Link>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="absolute inset-0 flex items-center px-20 overflow-hidden bg-zinc-950">
            <div className="absolute top-[-10%] right-[-10%] w-[60%] h-[120%] bg-white/[0.02] rotate-12 blur-3xl animate-pulse" />
            <div className="absolute bottom-[-20%] left-[-5%] w-[40%] h-[100%] bg-white/[0.02] -rotate-12 blur-3xl animate-pulse" />
            <div className="relative z-10 max-w-4xl space-y-10">
              <div className="flex items-center gap-4 text-white/20 animate-in fade-in slide-in-from-bottom-2 duration-500">
                <Sparkles className="w-5 h-5" />
                <span className="text-[10px] font-bold tracking-[0.6em] uppercase">Khám phá vũ trụ tri thức</span>
              </div>
              <h2 className="text-8xl font-bold text-white tracking-tighter leading-[0.8] animate-in fade-in slide-in-from-bottom-4 duration-700">
                Mở rộng <br/> <span className="text-white/10 italic">Giới hạn tri thức</span>
              </h2>
              <p className="text-white/30 text-xl font-medium leading-relaxed max-w-2xl animate-in fade-in slide-in-from-bottom-6 duration-1000">
                Hàng ngàn tài liệu, nghiên cứu và bài viết chuyên sâu từ cộng đồng chuyên gia hàng đầu đang chờ đón bạn trong mạng lưới DocLib.
              </p>
              <div className="pt-6 animate-in fade-in slide-in-from-bottom-8 duration-1000">
                <button 
                  onClick={scrollToContent}
                  className="h-16 px-16 bg-white text-black text-[11px] font-bold uppercase tracking-[0.3em] hover:bg-zinc-200 transition-all active:scale-95 rounded-sm"
                >
                  Bắt đầu hành trình
                </button>
              </div>
            </div>
          </div>
        )}

        {banners.length > 1 && (
          <div className="absolute bottom-12 right-20 flex gap-6 z-10">
            {banners.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setActiveBanner(idx)}
                className={`h-[2px] transition-all duration-700 ${
                  idx === activeBanner ? "w-16 bg-white" : "w-8 bg-white/10 hover:bg-white/30"
                }`}
              />
            ))}
          </div>
        )}
      </div>

      <div 
        ref={exploreRef}
        className="mb-20 border-b border-zinc-100 pb-16 flex flex-col gap-12 transition-all duration-1000 delay-150"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-10">
          <div className="space-y-4">
            <h1 className="text-5xl font-bold tracking-tighter uppercase text-black leading-none">Khám phá</h1>
            <p className="text-zinc-300 text-[11px] font-bold uppercase tracking-widest flex items-center gap-4">
              KHÁM PHÁ TRI THỨC MỚI NHẤT <div className="w-1.5 h-1.5 bg-black rounded-full" />
            </p>
          </div>

          <div className="flex items-center gap-8">
            <div className="flex bg-zinc-50/50 p-1.5 border border-zinc-100 rounded-sm">
              <button 
                onClick={() => setViewMode("grid")}
                className={`p-3.5 transition-all active:scale-95 border rounded-sm ${viewMode === "grid" ? "bg-white border-zinc-200" : "border-transparent"}`}
              >
                <LayoutGrid className={`w-4 h-4 ${viewMode === "grid" ? "text-black" : "text-zinc-200"}`} />
              </button>
              <button 
                onClick={() => setViewMode("list")}
                className={`p-3.5 transition-all active:scale-95 border rounded-sm ${viewMode === "list" ? "bg-white border-zinc-200" : "border-transparent"}`}
              >
                <ListIcon className={`w-4 h-4 ${viewMode === "list" ? "text-black" : "text-zinc-200"}`} />
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-col md:flex-row items-center gap-6">
          <div className="relative flex-1 group">
            <Search className="absolute left-8 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-200 group-focus-within:text-black transition-colors stroke-[1.5]" />
            <input 
              type="text"
              placeholder={useSemantic ? "Nhập ý tưởng hoặc câu hỏi để tìm kiếm tri thức..." : "Tìm kiếm tên tài liệu, tác giả hoặc chủ đề tri thức..."}
              className="w-full h-18 pl-18 pr-8 bg-zinc-50/30 border border-zinc-100 focus:bg-white focus:border-black outline-none text-[15px] font-medium transition-all rounded-sm placeholder:text-zinc-200"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button 
            onClick={() => setUseSemantic(!useSemantic)}
            className={`h-18 px-10 flex items-center gap-4 border transition-all active:scale-95 rounded-sm ${useSemantic ? "bg-black text-white border-black shadow-none" : "bg-white text-black border-zinc-100 hover:border-black"}`}
          >
            <Zap className={`w-5 h-5 ${useSemantic ? "text-yellow-400 fill-yellow-400" : "text-zinc-200"}`} />
            <span className="text-[11px] font-bold uppercase tracking-[0.2em]">Tìm kiếm AI</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-20">
        <aside 
          className="lg:col-span-3 space-y-16 transition-all duration-1000 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="space-y-8">
            <div className="flex items-center gap-4 text-[10px] font-bold text-black uppercase tracking-[0.3em] px-1">
              <Filter className="w-4 h-4 text-zinc-200" /> PHÂN LOẠI TRI THỨC
            </div>
            <nav className="flex flex-col gap-2">
              <button
                onClick={() => setSelectedCategory(null)}
                className={`flex items-center justify-between px-8 h-16 text-[10px] font-bold uppercase tracking-widest transition-all border rounded-sm ${
                  !selectedCategory 
                    ? "bg-black text-white border-black" 
                    : "bg-white text-zinc-300 border-zinc-100 hover:bg-zinc-50 hover:text-black"
                }`}
              >
                Tất cả tài liệu
                <ChevronRight className={`w-4 h-4 transition-transform ${!selectedCategory ? "rotate-90" : ""}`} />
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`flex items-center justify-between px-8 h-16 text-[10px] font-bold uppercase tracking-widest transition-all border rounded-sm ${
                    selectedCategory === cat
                      ? "bg-black text-white border-black"
                      : "bg-white text-zinc-300 border-zinc-100 hover:bg-zinc-50 hover:text-black"
                  }`}
                >
                  {cat}
                  <ChevronRight className={`w-4 h-4 transition-transform ${selectedCategory === cat ? "rotate-90" : ""}`} />
                </button>
              ))}
            </nav>
          </div>

          <div className="p-10 border border-zinc-100 bg-zinc-50/20 space-y-10 rounded-sm">
            <div className="flex items-center gap-4 text-[10px] font-bold text-black tracking-[0.3em] uppercase border-b border-zinc-100 pb-6">
              <Activity className="w-4 h-4 text-zinc-200" />
              TIÊU ĐIỂM XU HƯỚNG
            </div>
            <div className="space-y-10">
              {trending.length > 0 ? trending.map((document, i) => (
                <Link key={document._id} href={`/document/${document.slug}`} className="group block space-y-4">
                  <div className="flex items-center gap-4">
                    <span className="text-[10px] font-bold text-zinc-100">0{i + 1}</span>
                    <div className="h-[1px] flex-1 bg-zinc-50 group-hover:bg-black transition-colors duration-500" />
                  </div>
                  <h4 className="text-[15px] font-bold leading-relaxed text-black tracking-tight group-hover:translate-x-2 transition-transform duration-500 uppercase">
                    {document.title}
                  </h4>
                  <div className="flex items-center justify-between text-[9px] font-bold text-zinc-200 uppercase tracking-widest">
                    <span>{document.views || 0} Lượt xem</span>
                    <TrendingUp className="w-3 h-3" />
                  </div>
                </Link>
              )) : (
                <div className="py-12 flex flex-col items-center justify-center gap-6 opacity-10">
                   <TrendingUp className="w-10 h-10 stroke-[1]" />
                   <p className="text-[9px] font-bold uppercase tracking-widest text-center">Đang phân tích dữ liệu</p>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-8">
            <div className="flex items-center gap-4 text-[10px] font-bold text-black uppercase tracking-[0.3em] px-1">
              <User className="w-4 h-4 text-zinc-200" /> TÁC GIẢ NỔI BẬT
            </div>
            <div className="space-y-4">
              {featuredAuthors.map((author) => (
                <Link key={author.id} href={`/authors/${author.slug}`} className="flex items-center gap-6 group p-4 border border-transparent hover:border-zinc-100 transition-all rounded-sm bg-zinc-50/10">
                  <div className="w-12 h-12 rounded-sm bg-zinc-50 border border-zinc-100 overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-700">
                    {author.avatar_url ? (
                      <img src={author.avatar_url} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <User className="w-6 h-6 text-zinc-100 stroke-[1]" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-black uppercase tracking-tight truncate">{author.full_name}</p>
                    <div className="flex items-center gap-2 mt-1.5">
                        <FileText className="w-2.5 h-2.5 text-zinc-200" />
                        <p className="text-[9px] text-zinc-300 font-bold uppercase tracking-widest">{author.document_count} Tác phẩm</p>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-zinc-100 group-hover:text-black transition-all group-hover:translate-x-1" />
                </Link>
              ))}
            </div>
          </div>
        </aside>

        <main 
          className="lg:col-span-9 space-y-24 transition-all duration-1000 delay-500"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {error && (
            <div className="p-10 border border-zinc-100 bg-zinc-50 text-center space-y-6 rounded-sm animate-in fade-in duration-700">
               <p className="text-[13px] font-bold uppercase tracking-widest text-zinc-400">{error}</p>
               <button 
                 onClick={() => { loadInitialData(); loadDocuments(); }}
                 className="px-10 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest active:scale-95 transition-all rounded-sm"
               >
                 Tái thiết lập kết nối
               </button>
            </div>
          )}

          <section className="space-y-12">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-8">
              <div className="flex items-center gap-4">
                <Sparkles className="w-5 h-5 text-zinc-200" />
                <h2 className="text-2xl font-bold uppercase tracking-tight">Gợi ý tri thức</h2>
              </div>
              <Link href="/recommendations" className="text-[10px] font-bold uppercase tracking-[0.3em] text-zinc-300 hover:text-black transition-colors flex items-center gap-3">
                XEM THÊM <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
              {recommendations.length > 0 ? recommendations.map((doc) => (
                <Link key={doc._id} href={`/document/${doc.slug}`} className="flex gap-10 p-10 border border-zinc-100 hover:border-black transition-all duration-700 group rounded-sm bg-white">
                   <div className="w-32 h-44 bg-zinc-50 shrink-0 border border-zinc-50 overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-1000 rounded-sm">
                     {doc.cover_url ? (
                       <img src={doc.cover_url} alt="" className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" />
                     ) : (
                       <div className="w-full h-full flex items-center justify-center">
                         <FileText className="w-12 h-12 text-zinc-100 stroke-[1]" />
                       </div>
                     )}
                   </div>
                   <div className="flex-1 space-y-5 py-2">
                     <span className="text-[9px] font-bold text-zinc-200 uppercase tracking-[0.4em]">{doc.categories?.[0] || "KIẾN THỨC"}</span>
                     <h3 className="text-lg font-bold leading-tight group-hover:translate-x-2 transition-transform duration-700 uppercase tracking-tight">{doc.title}</h3>
                     <p className="text-[13px] text-zinc-300 line-clamp-3 leading-loose font-medium">{doc.description || "Khám phá nội dung chi tiết của thực thể tri thức này trên nền tảng DocLib."}</p>
                     <div className="pt-2 flex items-center gap-4 text-[9px] font-bold text-zinc-200 uppercase tracking-widest">
                        <Clock className="w-3.5 h-3.5" />
                        {new Date(doc.created_at).toLocaleDateString("vi-VN")}
                     </div>
                   </div>
                </Link>
              )) : (
                [1, 2].map((i) => <div key={i} className="h-64 bg-zinc-50/50 border border-zinc-100 animate-pulse rounded-sm" />)
              )}
            </div>
          </section>

          <section className="space-y-12">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-8">
              <div className="flex items-center gap-4">
                <LayoutGrid className="w-5 h-5 text-zinc-200" />
                <h2 className="text-2xl font-bold uppercase tracking-tight">
                  {searchQuery ? `Kết quả: "${searchQuery}"` : "Kho tàng tri thức"}
                </h2>
              </div>
            </div>

            {loading ? (
              <div className={`grid gap-12 ${viewMode === "grid" ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"}`}>
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className={`bg-zinc-50 border border-zinc-100 animate-pulse rounded-sm ${viewMode === "grid" ? "aspect-[3/4.5]" : "h-48"}`} />
                ))}
              </div>
            ) : documents.length > 0 ? (
              <div className={`grid gap-16 ${viewMode === "grid" ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"}`}>
                {documents.map((document) => (
                  <Link
                    key={document._id}
                    href={`/document/${document.slug}`}
                    className={`group animate-in fade-in slide-in-from-bottom-8 duration-1000 ${viewMode === "grid" ? "space-y-6" : "flex gap-12 items-center border border-zinc-50 p-10 bg-white hover:border-black transition-all duration-700 rounded-sm"}`}
                  >
                    <div className={`${viewMode === "grid" ? "aspect-[3/4.5] w-full" : "w-44 h-64 shrink-0"} bg-zinc-50 border border-zinc-100 relative overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-1000 rounded-sm`}>
                      {document.cover_url ? (
                        <img
                          src={document.cover_url}
                          alt=""
                          className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center p-12 text-center">
                          <FileText className="w-16 h-16 text-zinc-50 stroke-[1]" />
                        </div>
                      )}
                      <div className="absolute top-6 left-6 px-3 py-1 bg-black text-white text-[8px] font-bold uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity duration-700">
                          Xem chi tiết
                      </div>
                    </div>
                    <div className={`${viewMode === "grid" ? "space-y-4" : "flex-1 space-y-6"}`}>
                      <div className="flex items-center justify-between border-b border-zinc-50 pb-2">
                        <span className="text-[10px] font-bold text-zinc-200 uppercase tracking-[0.3em]">
                          {document.categories?.[0] || "TRI THỨC"}
                        </span>
                        <span className="text-[9px] font-bold text-zinc-100 flex items-center gap-2">
                          <TrendingUp className="w-3 h-3" /> {document.views || 0}
                        </span>
                      </div>
                      <h3 className={`${viewMode === "grid" ? "text-lg" : "text-2xl"} font-bold leading-tight group-hover:translate-x-2 transition-transform duration-700 text-black uppercase tracking-tight`}>
                        {document.title}
                      </h3>
                      <p className="text-[14px] text-zinc-300 line-clamp-2 leading-relaxed font-medium">
                        {document.description || "Khám phá nội dung chi tiết của thực thể tri thức này trên nền tảng DocLib."}
                      </p>
                      <div className="flex items-center gap-6 pt-2">
                         <div className="flex items-center gap-2 text-[9px] font-bold text-zinc-200 uppercase tracking-widest">
                            <User className="w-3.5 h-3.5" />
                            {document.publisher_name || "DocLib Institutional"}
                         </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="py-60 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/10 rounded-sm">
                <div className="w-32 h-32 border border-zinc-100 bg-white flex items-center justify-center mb-12 rounded-sm rotate-45 group hover:rotate-0 transition-transform duration-1000">
                  <Search className="w-12 h-12 text-zinc-50 stroke-[1] -rotate-45" />
                </div>
                <h2 className="text-3xl font-bold tracking-tighter text-black uppercase mb-6">Thực thể không tồn tại</h2>
                <p className="text-[11px] font-bold text-zinc-200 uppercase tracking-widest text-center max-w-sm leading-loose">
                  Hệ thống không tìm thấy kết quả phù hợp với tham số truy vấn của bạn. Hãy thử thay đổi danh mục hoặc từ khóa.
                </p>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}
