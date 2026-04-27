"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { BookOpen, Eye, Star, Lock, ChevronLeft, Tag, Flag } from "lucide-react";
import ReviewSection from "@/app/components/ReviewSection";

export default function BookPreviewPage() {
  const { bookId } = useParams();
  const [preview, setPreview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        const res = await fetch(`${API_URL}/guest/books/${bookId}/preview`);
        if (res.ok) {
          setPreview(await res.json());
        }
      } catch (e) {
        console.error("Preview fetch error:", e);
      } finally {
        setLoading(false);
      }
    };
    if (bookId) fetchPreview();
  }, [bookId, API_URL]);

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center animate-in fade-in duration-300">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-black border-t-transparent rounded-none animate-spin mx-auto mb-4" />
          <span className="text-xs font-bold text-zinc-400 tracking-widest">Đang tải bản xem trước</span>
        </div>
      </div>
    );
  }

  if (!preview) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center animate-in fade-in duration-300">
        <h1 className="text-3xl font-bold text-black mb-4">Không tìm thấy tài liệu</h1>
        <Link href="/" className="px-6 py-3 bg-black text-white  hover:bg-zinc-800 transition-all">
          Trở về trang chủ
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[900px] mx-auto px-6 lg:px-8 py-12 md:py-16 bg-white min-h-screen animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <Link href="/" className="inline-flex items-center text-sm font-bold text-zinc-400 hover:text-black transition-colors gap-1.5 tracking-tight">
          <ChevronLeft className="w-4 h-4" />
          Quay lại
        </Link>
        <button 
          onClick={async () => {
            const reason = prompt("Lý do báo cáo tài liệu này:");
            if (!reason) return;
            try {
               const res = await fetch(`${API_URL}/social/posts/${bookId}/report?reason=${encodeURIComponent(reason)}`, { 
                 method: "POST", 
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('doclib_token')}` } 
               });
               if (res.ok) alert("Cảm ơn bạn đã báo cáo. Chúng tôi sẽ xem xét sớm nhất có thể.");
            } catch (e) {
               console.error(e);
            }
          }}
          className="text-[12px] font-bold tracking-widest text-zinc-400 hover:text-black transition-colors flex items-center gap-1.5"
        >
          <Flag className="w-3.5 h-3.5" /> Báo cáo vi phạm
        </button>
      </div>

      <div className="border border-border p-8 md:p-12 mb-8">
        <div className="flex flex-col md:flex-row gap-8">
          <div className="w-full md:w-48 h-64 bg-zinc-50 border border-border flex items-center justify-center shrink-0 overflow-hidden">
            {preview.cover_url ? (
              <img src={preview.cover_url} alt={preview.title} className="w-full h-full object-cover" />
            ) : (
              <BookOpen className="w-12 h-12 text-zinc-200" strokeWidth={1} />
            )}
          </div>
          <div className="flex-1">
            <span className="text-[12px] font-bold tracking-widest text-zinc-400 block mb-2">Bản xem trước</span>
            <h1 className="text-3xl md:text-4xl font-bold text-black tracking-tighter mb-4">{preview.title}</h1>
            <p className="text-sm text-zinc-500 leading-relaxed mb-6">{preview.description}</p>
            <div className="flex flex-wrap items-center gap-4 text-[12px] font-bold text-zinc-400 tracking-widest mb-6">
              <span className="flex items-center gap-1.5"><Eye className="w-3.5 h-3.5" /> {preview.views || 0} lượt xem</span>
              {preview.average_rating && <span className="flex items-center gap-1.5"><Star className="w-3.5 h-3.5" /> {Number(preview.average_rating).toFixed(1)}</span>}
              <span className="flex items-center gap-1.5"><BookOpen className="w-3.5 h-3.5" /> {preview.total_chapters || 0} chương</span>
            </div>
            {preview.tags && preview.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {preview.tags.map((tag: string, i: number) => (
                  <span key={i} className="px-3 py-1 bg-zinc-100 text-zinc-600 text-[12px] font-bold tracking-widest border border-border flex items-center gap-1.5">
                    <Tag className="w-3 h-3" /> {tag}
                  </span>
                ))}
              </div>
            )}
            <div className="flex flex-wrap gap-4 mt-8 pt-6 border-t border-zinc-100">
               <button className="px-6 py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-all flex items-center gap-2">
                  <Star className="w-4 h-4 fill-white" /> Ủng hộ tác giả
               </button>
               <button className="px-6 py-3 border-2 border-black text-[12px] font-bold tracking-widest hover:bg-zinc-50 transition-all">
                  Theo dõi gói hội viên
               </button>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <h2 className="text-lg font-bold text-black tracking-tight border-b border-border pb-4">Nội dung xem trước</h2>
        {preview.preview_chapters && preview.preview_chapters.length > 0 ? (
          preview.preview_chapters.map((ch: any, i: number) => (
            <div key={i} className="border border-border p-6 md:p-8 animate-in fade-in slide-in-from-bottom-2 duration-300" style={{ animationDelay: `${i * 100}ms` }}>
              <h3 className="text-base font-bold text-black mb-4">{ch.title || `Chương ${i + 1}`}</h3>
              <div className="prose prose-sm prose-zinc max-w-none text-zinc-600 leading-relaxed">
                <p className="whitespace-pre-wrap">{ch.content}</p>
              </div>
              {ch.is_preview && (
                <div className="mt-6 pt-4 border-t border-border flex items-center gap-2 text-zinc-400">
                  <Lock className="w-4 h-4" />
                  <span className="text-[12px] font-bold tracking-widest">Nội dung giới hạn trong bản xem trước</span>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="py-16 text-center border border-dashed border-border">
            <p className="text-xs font-bold text-zinc-400 tracking-widest">Chưa có nội dung xem trước</p>
          </div>
        )}
      </div>

      {bookId && <ReviewSection bookId={bookId as string} />}

      <div className="mt-12 border border-black p-8 text-center">
        <h3 className="text-xl font-bold text-black mb-3 tracking-tight">Đọc toàn bộ tài liệu</h3>
        <p className="text-sm text-zinc-500 mb-6">Đăng ký hoặc đăng nhập để truy cập toàn bộ nội dung tài liệu này.</p>
        <div className="flex justify-center gap-4">
          <Link href="/login" className="px-8 py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-all">
            Đăng nhập
          </Link>
          <Link href="/register" className="px-8 py-3 bg-white text-black border border-black text-[12px] font-bold tracking-widest hover:bg-zinc-50 transition-all">
            Đăng ký
          </Link>
        </div>
      </div>
    </div>
  );
}
