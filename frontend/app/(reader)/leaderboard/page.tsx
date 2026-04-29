"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Trophy, Star, TrendingUp, Users, ChevronRight, User, FileText, Filter, Sparkles, Award } from "lucide-react";
import { API_URL, getToken } from "@/app/lib/api";

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
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const headers: any = {};
        const token = getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${API_URL}/analytics/leaderboard`, { headers });
        if (!res.ok) throw new Error("Failed to fetch leaderboard");
        const json = await res.json();
        setData(json.data || json);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
        requestAnimationFrame(() => setVisible(true));
      }
    };

    fetchLeaderboard();
  }, []);

  const renderRankNumber = (index: number) => {
    let style = "bg-zinc-50 border-zinc-100 text-zinc-300";
    if (index === 0) style = "bg-black text-white border-black";
    else if (index === 1) style = "bg-zinc-800 text-white border-zinc-800";
    else if (index === 2) style = "bg-zinc-500 text-white border-zinc-500";

    return (
      <div className={`w-10 h-10 shrink-0 flex items-center justify-center font-bold text-[13px] border transition-all ${style}`}>
        {index + 1}
      </div>
    );
  };

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      {/* Header - Premium Standard */}
      <div 
        className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
              Vinh danh
            </h1>
            <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
              Knowledge Hall of Fame <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
            </p>
          </div>
          <div className="hidden md:flex items-center gap-3 px-6 py-3 bg-zinc-50 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-400">
             <Award className="w-4 h-4" /> Tôn vinh giá trị tri thức
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-12">
        {/* Sidebar Controls */}
        <aside 
          className="lg:col-span-3 space-y-10 transition-all duration-700 delay-150"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="space-y-6">
            <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-[0.2em] px-1">
              <Trophy className="w-4 h-4 text-zinc-300" /> Xếp hạng theo
            </div>
            <nav className="flex flex-col gap-1">
              {[
                { id: "views", label: "Xem nhiều nhất", icon: TrendingUp },
                { id: "rating", label: "Đánh giá tốt nhất", icon: Star },
                { id: "authors", label: "Tác giả nổi bật", icon: Users },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center justify-between px-6 py-4 text-[11px] font-bold uppercase tracking-widest transition-all border ${
                    activeTab === tab.id
                      ? "bg-black text-white border-black"
                      : "bg-white text-zinc-400 border-zinc-100 hover:bg-zinc-50 hover:text-black"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <tab.icon className="w-4 h-4" /> {tab.label}
                  </div>
                  <ChevronRight className={`w-3.5 h-3.5 transition-transform ${activeTab === tab.id ? "rotate-90" : ""}`} />
                </button>
              ))}
            </nav>
          </div>

          <div className="p-8 border border-zinc-100 bg-zinc-50/30 space-y-4">
             <div className="text-[10px] font-bold text-black uppercase tracking-widest mb-2">Thống kê hệ thống</div>
             <div className="space-y-3">
                <div className="flex justify-between text-[11px] font-medium">
                   <span className="text-zinc-400">Thời gian cập nhật:</span>
                   <span className="text-black font-bold">10 phút trước</span>
                </div>
                <div className="flex justify-between text-[11px] font-medium">
                   <span className="text-zinc-400">Chu kỳ:</span>
                   <span className="text-black font-bold uppercase tracking-widest text-[9px]">Hàng tháng</span>
                </div>
             </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <div 
          className="lg:col-span-9 transition-all duration-700 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {loading ? (
            <div className="grid grid-cols-1 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-24 border border-zinc-100 bg-white animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              {((activeTab === "authors" ? data?.top_authors : (activeTab === "views" ? data?.top_documents_by_views : data?.top_documents_by_rating)) || []).length > 0 ? (
                <div className="space-y-4">
                  {(activeTab === "views" || activeTab === "rating") ? (
                    ((activeTab === "views" ? data?.top_documents_by_views : data?.top_documents_by_rating) || []).map((document, index) => (
                      <div
                        key={`${document._id}-${index}`}
                        className="group flex items-center justify-between p-6 border border-zinc-100 bg-white hover:border-black transition-all duration-700"
                      >
                        <div className="flex items-center gap-10">
                          {renderRankNumber(index)}
                          <div className="relative w-16 h-20 bg-zinc-50 border border-zinc-100 overflow-hidden shrink-0 grayscale group-hover:grayscale-0 transition-all duration-700">
                            {document.cover_image ? (
                              <img
                                src={document.cover_image.startsWith("http") ? document.cover_image : `${API_URL}/storage/${document.cover_image}`}
                                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                                alt={document.title}
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-zinc-100">
                                <FileText className="w-8 h-8 stroke-[1]" />
                              </div>
                            )}
                          </div>
                          <div className="space-y-2">
                            <Link
                              href={`/document/${document.slug}`}
                              className="text-lg font-bold text-black group-hover:underline underline-offset-4 decoration-1 tracking-tight block"
                            >
                              {document.title}
                            </Link>
                            <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                              Tác giả: <span className="text-black group-hover:translate-x-1 transition-transform">{document.author?.display_name || "Vô danh"}</span>
                            </p>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="flex items-center justify-end gap-3 mb-2">
                            {activeTab === "views" ? (
                              <div className="flex items-center gap-2 text-black font-bold text-2xl tracking-tighter">
                                <TrendingUp className="w-5 h-5 text-zinc-100" />
                                {document.views_count?.toLocaleString() || 0}
                              </div>
                            ) : (
                              <div className="flex items-center gap-2 text-black font-bold text-2xl tracking-tighter">
                                <Star className="w-5 h-5 text-zinc-100" />
                                {document.rating_avg?.toFixed(1) || 0}
                              </div>
                            )}
                          </div>
                          <div className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                            {activeTab === "views" ? "Tổng lượt xem" : "Điểm đánh giá"}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {(data?.top_authors || []).map((author, index) => (
                        <Link
                          key={`${author._id}-${index}`}
                          href={`/profile/${author.slug}`}
                          className="group flex items-center justify-between p-6 border border-zinc-100 bg-white hover:border-black transition-all duration-700"
                        >
                          <div className="flex items-center gap-6">
                            {renderRankNumber(index)}
                            <div className="relative w-14 h-14 border border-zinc-100 overflow-hidden shrink-0 bg-zinc-50 grayscale group-hover:grayscale-0 transition-all duration-700">
                              {author.avatar_url ? (
                                <img
                                  src={author.avatar_url.startsWith("http") ? author.avatar_url : `${API_URL}/storage/${author.avatar_url}`}
                                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                                  alt={author.display_name}
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center font-bold text-xs text-zinc-200">
                                  {author.display_name?.[0]}
                                </div>
                              )}
                            </div>
                            <div className="space-y-1">
                              <h3 className="text-base font-bold text-black tracking-tight group-hover:translate-x-1 transition-transform">
                                {author.display_name}
                              </h3>
                              <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                                <Users className="w-3 h-3 inline mr-1" /> {author.followers_count?.toLocaleString() || 0} Độc giả
                              </p>
                            </div>
                          </div>
                          <ChevronRight className="w-5 h-5 text-zinc-100 group-hover:text-black transition-colors" />
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-48 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/30">
                  <Trophy className="w-16 h-16 text-zinc-100 mb-10 stroke-[1]" />
                  <h2 className="text-2xl font-bold tracking-tighter text-black mb-4">Bảng xếp hạng đang trống</h2>
                  <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest text-center max-w-xs leading-loose">
                    Dữ liệu đang được đồng bộ. Hãy quay lại sau để xem những cá nhân xuất sắc nhất.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
