"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Trophy, Star, TrendingUp, Users, DocumentOpen, ChevronRight, User } from "lucide-react";

interface LeaderboardDocument {
  _id: string;
  title: string;
  slug: string;
  cover_image?: string;
  author: {
    _id: string;
    display_name: string;
    slug: string;
  };
  views_count: number;
  rating_avg: number;
}

interface LeaderboardData {
  top_documents_by_views: LeaderboardDocument[];
  top_documents_by_rating: LeaderboardDocument[];
  top_authors: any[];
}

export default function LeaderboardPage() {
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"views" | "rating" | "authors">("views");

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/analytics/leaderboard`);
        if (!res.ok) throw new Error("Failed to fetch leaderboard");
        const json = await res.json();
        setData(json);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    fetchLeaderboard();
  }, []);

  const renderRankNumber = (index: number) => {
    let style = "bg-white border-border text-zinc-300";
    if (index === 0) style = "bg-black text-white border-black scale-110";
    else if (index === 1) style = "bg-zinc-800 text-white border-zinc-800";
    else if (index === 2) style = "bg-zinc-500 text-white border-zinc-500";

    return (
      <div className={`w-10 h-10 shrink-0 flex items-center justify-center  font-black text-sm border transition-all ${style}`}>
        {String(index + 1).padStart(2, '0')}
      </div>
    );
  };

  return (
    <div className="w-full max-w-[1000px] mx-auto px-6 lg:px-8 py-12 md:py-20 bg-white min-h-screen animate-in fade-in duration-300">
      <div className="mb-16 border-b border-black pb-12">
        <div className="flex items-center gap-3 mb-4">
           <Trophy className="w-6 h-6 text-black" />
           <span className="text-[11px] font-black tracking-[0.3em] text-zinc-400">Vinh danh tri thức</span>
        </div>
        <h1 className="text-4xl md:text-6xl font-bold tracking-tighter text-black mb-6">
          Bảng xếp hạng
        </h1>
        <p className="text-zinc-500 text-base md:text-lg leading-relaxed font-medium max-w-2xl">
          Nơi tôn vinh các tài liệu chuẩn mực và những tác giả có đóng góp xuất sắc nhất cho hệ sinh thái tri thức DocLib.
        </p>
      </div>

      <div className="flex flex-wrap gap-1 mb-12 bg-zinc-50 p-1 border border-border ">
        <button
          onClick={() => setActiveTab("views")}
          className={`flex-1 flex items-center justify-center gap-2.5 px-6 py-3  text-[10px] font-bold tracking-widest transition-all ${
            activeTab === "views"
              ? "bg-black text-white"
              : "text-zinc-400 hover:text-black hover:bg-white"
          }`}
        >
          <TrendingUp className="w-3.5 h-3.5" />
          Xem nhiều nhất
        </button>
        <button
          onClick={() => setActiveTab("rating")}
          className={`flex-1 flex items-center justify-center gap-2.5 px-6 py-3  text-[10px] font-bold tracking-widest transition-all ${
            activeTab === "rating"
              ? "bg-black text-white"
              : "text-zinc-400 hover:text-black hover:bg-white"
          }`}
        >
          <Star className="w-3.5 h-3.5" />
          Đánh giá tốt nhất
        </button>
        <button
          onClick={() => setActiveTab("authors")}
          className={`flex-1 flex items-center justify-center gap-2.5 px-6 py-3  text-[10px] font-bold tracking-widest transition-all ${
            activeTab === "authors"
              ? "bg-black text-white"
              : "text-zinc-400 hover:text-black hover:bg-white"
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          Tác giả nổi bật
        </button>
      </div>

      <div className="w-full">
        {loading ? (
          <div className="space-y-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="flex items-center gap-6 p-6 border border-border bg-white animate-pulse">
                <div className="w-10 h-10 bg-zinc-100 shrink-0"></div>
                <div className="w-16 h-20 bg-zinc-50 shrink-0"></div>
                <div className="flex-1">
                  <div className="h-4 bg-zinc-100 w-1/3 mb-3"></div>
                  <div className="h-3 bg-zinc-50 w-1/4"></div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            {(activeTab === "views" || activeTab === "rating") ? (
              <div className="space-y-4">
                {((activeTab === "views" ? data?.top_documents_by_views : data?.top_documents_by_rating) || []).map((document, index) => (
                  <div
                    key={document._id}
                    className="group flex flex-col sm:flex-row sm:items-center gap-6 p-6 border border-border bg-white hover:border-black transition-all duration-300 relative"
                  >
                    <div className="flex items-center gap-6">
                      {renderRankNumber(index)}
                      <div className="relative w-16 h-24 bg-zinc-50 border border-border  overflow-hidden flex items-center justify-center shrink-0 grayscale group-hover:grayscale-0 transition-all duration-500">
                        {document.cover_image ? (
                          <img
                            src={document.cover_image.startsWith("http") ? document.cover_image : `${process.env.NEXT_PUBLIC_API_URL}/storage/${document.cover_image}`}
                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                            alt={document.title}
                          />
                        ) : (
                          <DocumentOpen className="w-6 h-6 text-zinc-200" strokeWidth={1} />
                        )}
                      </div>
                    </div>

                    <div className="flex-1 min-w-0">
                      <Link
                        href={`/document/${document.slug}`}
                        className="text-xl font-bold text-black hover:underline underline-offset-4 decoration-2 transition-all line-clamp-1 tracking-tight"
                      >
                        {document.title}
                      </Link>
                      <p className="text-zinc-500 mt-2 text-sm font-medium">
                        Tác giả:{" "}
                        <Link href={`/profile/${document.author?.slug}`} className="text-black font-bold hover:bg-black hover:text-white px-1.5 py-0.5 transition-all">
                          {document.author?.display_name || "Vô danh"}
                        </Link>
                      </p>
                    </div>

                    <div className="shrink-0 flex flex-col items-end">
                      {activeTab === "views" ? (
                        <div className="flex items-center gap-2 text-black font-black text-lg">
                          <TrendingUp className="w-4 h-4 text-zinc-300" />
                          {document.views_count?.toLocaleString() || 0}
                          <span className="text-[9px] tracking-widest text-zinc-400 font-bold ml-1">Lượt xem</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-black font-black text-lg">
                          <Star className="w-4 h-4 text-zinc-300" />
                          {document.rating_avg?.toFixed(1) || 0}
                          <span className="text-[9px] tracking-widest text-zinc-400 font-bold ml-1">Đánh giá</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="absolute right-0 top-0 bottom-0 w-1 bg-black opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                ))}
                
                {(!data?.top_documents_by_views?.length && activeTab === "views") && (
                  <div className="py-32 text-center border border-dashed border-border  bg-zinc-50/30">
                    <p className="text-xs font-bold text-zinc-400 tracking-widest">Dữ liệu thống kê lượt xem đang được cập nhật</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(data?.top_authors || []).map((author, index) => (
                  <Link
                    key={author._id}
                    href={`/profile/${author.slug}`}
                    className="group flex items-center gap-6 p-6 border border-border bg-white hover:border-black transition-all duration-300"
                  >
                    {renderRankNumber(index)}
                    <div className="relative w-16 h-16  border border-border overflow-hidden shrink-0 bg-zinc-50 grayscale group-hover:grayscale-0 transition-all duration-500">
                      {author.avatar_url ? (
                        <img
                          src={author.avatar_url.startsWith("http") ? author.avatar_url : `${process.env.NEXT_PUBLIC_API_URL}/storage/${author.avatar_url}`}
                          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                          alt={author.display_name}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <User className="w-6 h-6 text-zinc-200" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-black text-black tracking-tight group-hover:underline underline-offset-4 decoration-2 truncate transition-all">
                        {author.display_name}
                      </h3>
                      <div className="flex items-center gap-2 mt-2 text-[10px] font-bold text-zinc-400 tracking-widest">
                        <Users className="w-3.5 h-3.5" />
                        <span>{author.followers_count || 0} Độc giả</span>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-zinc-200 group-hover:text-black transition-colors" />
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      
      <div className="mt-20 py-12 border-t border-zinc-100 flex justify-center">
         <div className="text-center max-w-sm">
            <span className="text-[10px] font-black tracking-[0.3em] text-zinc-300 block mb-4">DocLib Excellence</span>
            <p className="text-xs text-zinc-400 font-medium leading-relaxed italic">
              "Thành tựu vĩ đại nhất của một tác giả không phải là số lượt xem, mà là giá trị tri thức để lại cho cộng đồng."
            </p>
         </div>
      </div>
    </div>
  );
}
