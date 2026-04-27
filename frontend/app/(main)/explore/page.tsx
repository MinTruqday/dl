"use client";

import { useEffect, useState } from "react";
import { getBooksAPI, getTrendingBooksAPI, getTagsCategoriesAPI } from "@/app/lib/api";
import Link from "next/link";
import { Search, Filter, TrendingUp, Grid, List as ListIcon, ChevronRight } from "lucide-react";

export default function ExplorePage() {
  const [books, setBooks] = useState<any[]>([]);
  const [trending, setTrending] = useState<any[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    loadBooks();
  }, [selectedCategory]);

  const loadInitialData = async () => {
    try {
      const [catData, trendData] = await Promise.all([
        getTagsCategoriesAPI(),
        getTrendingBooksAPI(3)
      ]);
      setCategories(catData.categories || []);
      setTrending(trendData || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadBooks = async () => {
    setLoading(true);
    try {
      const data = await getBooksAPI(undefined, "latest", selectedCategory || undefined);
      setBooks(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-[1400px] mx-auto px-6 py-12">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight leading-none">Khám phá tri thức</h1>
          <p className="text-muted-foreground text-sm font-medium tracking-wide">Tìm kiếm tri thức thông qua các danh mục và xu hướng mới nhất.</p>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="flex border border-border  p-1 bg-muted/20">
            <button className="p-2 bg-white border border-border shadow-sm"><Grid className="w-4 h-4" /></button>
            <button className="p-2 hover:bg-white/50 transition-colors"><ListIcon className="w-4 h-4 text-muted-foreground" /></button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-12">
        <aside className="space-y-8">
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-[12px] font-bold tracking-widest text-muted-foreground">
              <Filter className="w-3 h-3" />
              Danh mục
            </div>
            <div className="flex flex-col gap-1">
              <button 
                onClick={() => setSelectedCategory(null)}
                className={`text-left px-4 py-2.5 text-sm font-bold transition-all border ${!selectedCategory ? 'bg-black text-white border-black' : 'hover:bg-zinc-100 border-transparent'}`}
              >
                Tất cả tài liệu
              </button>
              {categories.map((cat) => (
                <button 
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`text-left px-4 py-2.5 text-sm font-bold transition-all border ${selectedCategory === cat ? 'bg-black text-white border-black' : 'hover:bg-zinc-100 border-transparent'}`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          <div className="p-6 bg-zinc-50 border border-border space-y-4">
             <div className="flex items-center gap-2 text-[12px] font-bold tracking-widest text-muted-foreground">
                <TrendingUp className="w-3 h-3" />
                Xu hướng
             </div>
             <div className="space-y-4">
                {trending.map((book, i) => (
                   <Link key={book._id} href={`/preview?slug=${book.slug}`} className="group cursor-pointer block">
                      <div className="text-[12px] font-bold text-zinc-400 mb-1">0{i+1}</div>
                      <h4 className="text-xs font-bold leading-tight group-hover:underline underline-offset-4">{book.title}</h4>
                   </Link>
                ))}
             </div>
          </div>
        </aside>

        <main>
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="aspect-[3/4] bg-zinc-100 animate-pulse border border-border" />
              ))}
            </div>
          ) : books.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {books.map((book) => (
                <Link key={book._id} href={`/preview?slug=${book.slug}`} className="group space-y-4">
                  <div className="aspect-[3/4] bg-zinc-100 border border-border relative overflow-hidden">
                    {book.cover_url ? (
                      <img src={book.cover_url} alt={book.title} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-[12px] font-bold text-zinc-400 tracking-widest p-12 text-center">
                        {book.title}
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-300" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                       <span className="text-[13px] font-bold tracking-widest text-zinc-400">{book.categories?.[0] || "Tổng hợp"}</span>
                       <span className="text-[13px] font-bold tracking-widest text-zinc-400">{book.views || 0} lượt xem</span>
                    </div>
                    <h3 className="text-sm font-bold leading-tight group-hover:underline underline-offset-4 decoration-1">{book.title}</h3>
                    <p className="text-[13px] text-muted-foreground line-clamp-2 leading-relaxed">{book.description}</p>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="h-[400px] flex flex-col items-center justify-center text-center border border-dashed border-border bg-zinc-50/50 p-12">
               <div className="w-12 h-12 bg-zinc-100 flex items-center justify-center mb-4">
                  <Search className="w-5 h-5 text-zinc-300" />
               </div>
               <h3 className="text-sm font-bold tracking-widest mb-1">Không tìm thấy kết quả</h3>
               <p className="text-xs text-muted-foreground">Thử thay đổi danh mục hoặc từ khóa tìm kiếm của bạn.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
