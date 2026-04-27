"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Search, BookOpen, Clock, Inbox, Tag, ChevronRight, ChevronLeft, Sparkles, Mail, AlertCircle, X, Users } from "lucide-react";
import { getBooksAPI, getToken } from "@/app/lib/api";
import { useAuth } from "@/app/contexts/AuthContext";

interface DocLibBook {
  _id: string;
  title: string;
  slug: string;
  description: string;
  author_id: string;
  cover_url?: string;
  tags?: string[];
  created_at?: string;
}

export default function DiscoverPage() {
  const { user, loading: authLoading } = useAuth() as any;
  const [books, setBooks] = useState<DocLibBook[]>([]);
  const [search, setSearch] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [sortBy, setSortBy] = useState("latest");
  const [loading, setLoading] = useState(true);
  const [newsletterEmail, setNewsletterEmail] = useState("");
  const [newsletterMsg, setNewsletterMsg] = useState("");
  const [systemNotices, setSystemNotices] = useState<any[]>([]);
  const [dismissedNotices, setDismissedNotices] = useState<string[]>([]);
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    let isMounted = true;
    const loadBooks = async () => {
      setLoading(true);
      try {
        const data = await getBooksAPI(search, sortBy);
        if (isMounted && Array.isArray(data)) {
          setBooks(data);
        }
      } catch (e) {
        console.error(e);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    
    const timer = setTimeout(() => {
      loadBooks();
    }, 400); 
    
    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [search, sortBy]);

  useEffect(() => {
    const fetchExtras = async () => {
      try {
        const noticesRes = await fetch(`${API_URL}/guest/system-notices`);
        if (noticesRes.ok) setSystemNotices(await noticesRes.json());
      } catch (e) {
        console.error("Failed to fetch extras:", e);
      }
    };
    fetchExtras();
  }, [API_URL]);

  const subscribeNewsletter = async () => {
    if (!newsletterEmail.trim()) return;
    try {
      const res = await fetch(`${API_URL}/guest/newsletter/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: newsletterEmail }),
      });
      const data = await res.json();
      if (res.ok) {
        setNewsletterMsg(data.message || "Đăng ký thành công");
        setNewsletterEmail("");
      } else {
        setNewsletterMsg(data.detail || "Không thể đăng ký");
      }
    } catch {
      setNewsletterMsg("Mất kết nối");
    }
  };

  const filteredBooks = books.filter(b => tagFilter ? (b.tags || []).includes(tagFilter) : true);
  const allTags = Array.from(new Set(books.flatMap(b => b.tags || [])));

  const [activeBanner, setActiveBanner] = useState(0);
  const banners = [
    { title: "Khám phá tri thức", desc: "Tìm kiếm và nghiên cứu các tác phẩm học thuật chuẩn mực.", bg: "bg-black", text: "text-white" },
    { title: "Thư viện mở", desc: "Hệ thống lưu trữ và chia sẻ tài liệu số phi tập trung.", bg: "bg-zinc-100", text: "text-black" },
    { title: "Sáng tác tự do", desc: "Nền tảng hỗ trợ tác giả xuất bản và tối ưu hóa doanh thu.", bg: "bg-zinc-800", text: "text-white" },
    { title: "Kết nối cộng đồng", desc: "Trao đổi, thảo luận và cùng nhau xây dựng kho tàng kiến thức.", bg: "bg-zinc-200", text: "text-black" },
    { title: "Minh bạch & an toàn", desc: "Đảm bảo quyền sở hữu trí tuệ trên nền tảng công nghệ mới.", bg: "bg-zinc-900", text: "text-white" }
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveBanner((prev) => (prev + 1) % banners.length);
    }, 6000);
    return () => clearInterval(interval);
  }, [banners.length]);

  return (
    <div className="w-full max-w-[1200px] mx-auto px-6 lg:px-8 py-10 md:py-16 bg-white min-h-full animate-in fade-in duration-300">

      {systemNotices.filter(n => !dismissedNotices.includes(n.id)).map(notice => (
        <div key={notice.id} className={`mb-4 flex items-center justify-between gap-4 px-5 py-3 border text-sm font-medium animate-in slide-in-from-top-2 duration-300 ${
          notice.severity === "warning" ? "border-zinc-400 bg-zinc-50 text-black" : "border-border bg-white text-zinc-600"
        }`}>
          <div className="flex items-center gap-3">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{notice.title}: {notice.content}</span>
          </div>
          <button onClick={() => setDismissedNotices(prev => [...prev, notice.id])} className="text-zinc-400 hover:text-black transition-colors shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}

      <div className="mb-12 md:mb-16 relative overflow-hidden border border-zinc-100 h-[220px] md:h-[320px] bg-zinc-50 rounded-none">
        {banners.map((banner, idx) => (
          <div
            key={idx}
            className={`absolute inset-0 transition-all duration-500 ease-in-out flex flex-col justify-center px-10 md:px-20 ${banner.bg} ${banner.text} ${idx === activeBanner ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-12 pointer-events-none'}`}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-1 bg-current opacity-30" />
              <span className="text-[12px] font-bold tracking-wider opacity-70">Tiêu điểm hôm nay</span>
            </div>
            <h1 className="text-3xl md:text-5xl font-bold tracking-tighter mb-5 leading-tight">
              {banner.title}
            </h1>
            <p className="text-sm md:text-lg opacity-70 max-w-xl font-medium leading-relaxed">
              {banner.desc}
            </p>
          </div>
        ))}
        
        <div className="absolute bottom-8 left-10 md:left-20 flex gap-3 z-10">
          {banners.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setActiveBanner(idx)}
              className={`h-1 transition-all duration-300  ${idx === activeBanner ? 'w-10 bg-current' : 'w-4 bg-current/20 hover:bg-current/40'}`}
              aria-label={`Slide ${idx + 1}`}
            />
          ))}
        </div>

        <div className="absolute bottom-8 right-10 md:right-20 flex gap-2 z-10">
          <button 
            onClick={() => setActiveBanner(prev => (prev - 1 + banners.length) % banners.length)}
            className="p-2 border border-current/20 hover:bg-current/5 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button 
            onClick={() => setActiveBanner(prev => (prev + 1) % banners.length)}
            className="p-2 border border-current/20 hover:bg-current/5 transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {user && (
        <div className="flex flex-col sm:flex-row gap-4 mb-12 w-full animate-in fade-in duration-500">
          <div className="relative flex-1 group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-zinc-400 group-focus-within:text-black transition-colors" />
            </div>
            <input
              type="text"
              className="block w-full pl-12 pr-4 py-4 border border-zinc-100 rounded-none bg-zinc-50/50 text-black placeholder:text-zinc-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-zinc-50 focus:border-zinc-300 transition-all sm:text-base font-semibold"
              placeholder="Tìm kiếm tài liệu, chủ đề hoặc từ khóa"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          
          <div className="flex gap-3 shrink-0">
            <select
              className="block h-full px-6 py-4 border border-zinc-100 rounded-none bg-zinc-50/50 text-black font-bold text-xs tracking-widest focus:outline-none focus:border-black transition-all cursor-pointer hover:bg-white"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="latest">Mới nhất</option>
              <option value="oldest">Cũ nhất</option>
            </select>
          </div>
        </div>
      )}

      {allTags.length > 0 && (
        <div className="flex gap-2 mb-12 border-b border-border pb-8 overflow-x-auto hide-scrollbar whitespace-nowrap">
          <button
            onClick={() => setTagFilter("")}
            className={`px-6 py-2.5 text-[13px] font-bold tracking-wider transition-all border shrink-0 ${tagFilter === "" ? 'bg-black text-white border-black' : 'bg-white text-zinc-400 border-zinc-100 hover:border-black hover:text-black'}`}
          >
            Tất cả
          </button>
          {allTags.map(tag => (
            <button
              key={tag}
              onClick={() => setTagFilter(tag)}
              className={`px-6 py-2.5 rounded-none text-[12px] font-bold tracking-widest transition-all border shrink-0 ${tagFilter === tag ? 'bg-black text-white border-black' : 'bg-white text-zinc-400 border-zinc-100 hover:border-black hover:text-black'}`}
            >
              {tag}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="flex flex-col  border border-border bg-white overflow-hidden animate-pulse">
              <div className="aspect-[3/4] bg-zinc-100" />
              <div className="p-6">
                <div className="h-4 bg-zinc-200  w-3/4 mb-4" />
                <div className="h-3 bg-zinc-100  w-full mb-2" />
                <div className="h-3 bg-zinc-100  w-2/3" />
              </div>
            </div>
          ))}
        </div>
      ) : filteredBooks.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
          {filteredBooks.map((book) => (
            <Link 
            key={book._id} 
            href={`/book/${book.slug}`}
            className="group flex flex-col rounded-none border border-zinc-100 bg-white overflow-hidden hover:border-zinc-400 transition-all duration-300"
          >
              <div className="relative aspect-[3/4] bg-zinc-50 flex items-center justify-center border-b border-border overflow-hidden">
                {book.cover_url ? (
                  <img 
                    src={book.cover_url} 
                    alt={book.title} 
                    className="w-full h-full object-cover transition-transform duration-500 grayscale group-hover:grayscale-0"
                  />
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <BookOpen className="w-12 h-12 text-zinc-200 transition-all duration-500 group-hover:text-black" strokeWidth={1} />
                    <span className="text-[12px] font-bold text-zinc-300 tracking-wider group-hover:text-black transition-colors">Tài liệu</span>
                  </div>
                )}
              </div>
              <div className="p-6 flex-1 flex flex-col">
                <h3 className="font-bold text-black text-lg leading-tight line-clamp-1 group-hover:underline underline-offset-4 decoration-2 transition-all">
                  {book.title}
                </h3>
                <p className="text-sm text-zinc-500 line-clamp-2 mt-3 flex-1 leading-relaxed font-medium">
                  {book.description || "Tác giả chưa cung cấp mô tả cho tài liệu này."}
                </p>
                <div className="mt-6 flex items-center justify-between pt-5 border-t border-zinc-50 text-[12px] font-bold tracking-widest text-zinc-400">
                  <span className="flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5" />
                    {book.created_at ? new Date(book.created_at).toLocaleDateString('vi-VN') : 'Mới nhất'}
                  </span>
                  {book.tags && book.tags.length > 0 && (
                    <span className="flex items-center gap-2 px-2.5 py-1 bg-zinc-100 text-black ">
                      <Tag className="w-3 h-3" />
                      {book.tags[0]}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-32 px-4 text-center border border-dashed border-border bg-zinc-50/30">
          <div className="w-20 h-20 flex items-center justify-center bg-white border border-border mb-8">
            <Inbox className="w-10 h-10 text-zinc-300" strokeWidth={1} />
          </div>
          <h3 className="text-xl font-bold text-black mb-3 tracking-tight">Không tìm thấy kết quả</h3>
          <p className="text-zinc-500 max-w-sm text-sm font-medium leading-relaxed">
            Chúng tôi không tìm thấy tài liệu nào khớp với yêu cầu của bạn. Hãy thử tìm kiếm bằng các từ khóa khác hoặc xóa bộ lọc.
          </p>
        </div>
      )}
      
      <div className="mt-20 border-t border-black pt-12 flex flex-col md:flex-row justify-between items-start gap-8">
        <div className="max-w-md">
          <div className="flex items-center gap-3 mb-4">
             <Sparkles className="w-6 h-6 text-black" />
             <h4 className="text-lg font-bold tracking-tighter">DocLib</h4>
          </div>
          <p className="text-sm text-zinc-500 font-medium leading-relaxed mb-6">
            Nền tảng tri thức mở hàng đầu dành cho cộng đồng học thuật và sáng tạo.
          </p>
          <div className="flex gap-2">
            <input
              type="email"
              placeholder="Email để nhận bản tin"
              className="flex-1 px-4 py-3 border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black transition-all"
              value={newsletterEmail}
              onChange={(e) => setNewsletterEmail(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") subscribeNewsletter(); }}
            />
            <button onClick={subscribeNewsletter} className="px-4 py-3 bg-black text-white hover:bg-zinc-800 transition-all">
              <Mail className="w-4 h-4" />
            </button>
          </div>
          {newsletterMsg && <p className="text-[12px] text-zinc-400 mt-3 font-bold tracking-widest">{newsletterMsg}</p>}
        </div>
        <div className="flex gap-12">
          <div className="flex flex-col gap-3">
             <span className="text-[12px] font-bold tracking-widest text-black">Khám phá</span>
             <Link href="/library" className="text-sm text-zinc-500 hover:text-black transition-colors font-medium">Thư viện</Link>
             <Link href="/leaderboard" className="text-sm text-zinc-500 hover:text-black transition-colors font-medium">Xếp hạng</Link>
             <Link href="/feed" className="text-sm text-zinc-500 hover:text-black transition-colors font-medium">Cộng đồng</Link>
          </div>
          <div className="flex flex-col gap-3">
             <span className="text-[12px] font-bold tracking-widest text-black">Hỗ trợ</span>
             <Link href="/terms" className="text-sm text-zinc-500 hover:text-black transition-colors font-medium">Điều khoản</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
