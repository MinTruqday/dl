"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { BookOpen, Eye, Star, Users, ChevronLeft, UserPlus, UserMinus } from "lucide-react";
import { getToken } from "@/app/lib/api";

export default function AuthorProfilePage() {
  const { slug } = useParams();
  const [author, setAuthor] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    const fetchAuthor = async () => {
      try {
        const res = await fetch(`${API_URL}/guest/authors/${slug}`);
        if (res.ok) {
          const data = await res.json();
          setAuthor(data);
        }
      } catch (e) {
        console.error("Author profile fetch error:", e);
      } finally {
        setLoading(false);
      }
    };
    if (slug) fetchAuthor();
  }, [slug, API_URL]);

  const toggleFollow = async () => {
    if (!author?.id) return;
    setFollowLoading(true);
    try {
      const res = await fetch(`${API_URL}/social/follow/${author.id}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        setIsFollowing(!isFollowing);
      }
    } catch (e) {
      console.error("Follow toggle error:", e);
    } finally {
      setFollowLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center animate-in fade-in duration-300">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-black border-t-transparent rounded-none animate-spin mx-auto mb-4" />
          <span className="text-xs font-bold text-zinc-400 tracking-widest">Đang tải hồ sơ</span>
        </div>
      </div>
    );
  }

  if (!author) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center animate-in fade-in duration-300">
        <h1 className="text-3xl font-bold text-black mb-4">Không tìm thấy tác giả</h1>
        <p className="text-zinc-500 mb-8">Hồ sơ tác giả không tồn tại hoặc đã bị gỡ bỏ.</p>
        <Link href="/" className="px-6 py-3 bg-black text-white  hover:bg-zinc-800 transition-all duration-150">
          Trở về trang chủ
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1000px] mx-auto px-6 lg:px-8 py-12 md:py-20 bg-white min-h-screen animate-in fade-in duration-300">
      <Link href="/" className="inline-flex items-center text-sm font-bold text-zinc-400 hover:text-black mb-8 transition-colors gap-1.5 tracking-tight">
        <ChevronLeft className="w-4 h-4" />
        Quay lại
      </Link>

      <div className="border border-border p-8 md:p-12 mb-12">
        <div className="flex flex-col md:flex-row gap-8 items-start">
          <div className="w-24 h-24 md:w-32 md:h-32 bg-zinc-100 border border-border  flex items-center justify-center shrink-0 overflow-hidden">
            {author.avatar_url ? (
              <img src={author.avatar_url} alt={author.full_name} className="w-full h-full object-cover" />
            ) : (
              <span className="text-3xl font-bold text-zinc-300">{author.full_name?.[0]?.toUpperCase()}</span>
            )}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-[10px] font-bold tracking-widest text-zinc-400">{author.role === "author" ? "Tác giả" : "Người dùng"}</span>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-black tracking-tighter mb-3">{author.full_name}</h1>
            {author.bio && <p className="text-sm text-zinc-500 leading-relaxed max-w-xl mb-6">{author.bio}</p>}
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2 text-zinc-500">
                <Users className="w-4 h-4" />
                <span className="font-bold text-black">{author.followers_count || 0}</span>
                <span>người theo dõi</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-500">
                <BookOpen className="w-4 h-4" />
                <span className="font-bold text-black">{author.books?.length || 0}</span>
                <span>tài liệu</span>
              </div>
            </div>
            <div className="mt-6">
              <button
                onClick={toggleFollow}
                disabled={followLoading}
                className={`inline-flex items-center gap-2 px-6 py-3 text-[10px] font-bold tracking-widest transition-all duration-150 ${
                  isFollowing
                    ? "bg-white text-black border border-black hover:bg-zinc-50"
                    : "bg-black text-white hover:bg-zinc-800"
                }`}
              >
                {isFollowing ? <UserMinus className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
                {isFollowing ? "Đang theo dõi" : "Theo dõi"}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="mb-8">
        <h2 className="text-xl font-bold text-black tracking-tight mb-8 border-b border-border pb-4 flex items-center gap-3">
          <BookOpen className="w-5 h-5" />
          Tài liệu đã xuất bản
        </h2>
        {(!author.books || author.books.length === 0) ? (
          <div className="py-20 text-center border border-dashed border-border">
            <p className="text-xs font-bold text-zinc-400 tracking-widest">Tác giả chưa xuất bản tài liệu nào</p>
          </div>
        ) : (
          <div className="space-y-4">
            {author.books.map((book: any) => (
              <Link
                key={book.id}
                href={`/book/${book.slug}`}
                className="group flex items-center gap-6 p-6 border border-border bg-white hover:border-black transition-all duration-300"
              >
                <div className="w-16 h-24 bg-zinc-50 border border-border flex items-center justify-center shrink-0 overflow-hidden">
                  {book.cover_url ? (
                    <img src={book.cover_url} alt={book.title} className="w-full h-full object-cover" />
                  ) : (
                    <BookOpen className="w-6 h-6 text-zinc-200" strokeWidth={1} />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-bold text-black group-hover:underline underline-offset-4 decoration-2 truncate">{book.title}</h3>
                  {book.description && <p className="text-sm text-zinc-500 mt-1 line-clamp-2">{book.description}</p>}
                  <div className="flex items-center gap-4 mt-3 text-[10px] font-bold text-zinc-400 tracking-widest">
                    <span className="flex items-center gap-1.5"><Eye className="w-3.5 h-3.5" /> {book.views || 0}</span>
                    {book.average_rating && <span className="flex items-center gap-1.5"><Star className="w-3.5 h-3.5" /> {Number(book.average_rating).toFixed(1)}</span>}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
