"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Trophy,
  Star,
  TrendingUp,
  Users,
  ChevronRight,
  FileText,
  Sparkles,
  Clock,
  Calendar,
} from "lucide-react";
import { API_URL } from "@/services/authentication.service";
import { getSocialRankingAPI } from "@/services/rank.service";

interface LeaderboardDocument {
  _id: string;
  title: string;
  slug: string;
  cover_image?: string;
  author: {
    _id: string;
    full_name: string;
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
        const json = await getSocialRankingAPI();
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
    const isTop3 = index < 3;
    return (
      <div
        className={`w-8 h-8 shrink-0 flex items-center justify-center font-bold text-sm border ${isTop3
            ? "border-black bg-black text-white"
            : "border-zinc-200 bg-zinc-50 text-zinc-500"
          }`}
      >
        {String(index + 1).padStart(2, "0")}
      </div>
    );
  };

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 font-sans text-black selection:bg-black selection:text-white">

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <aside className="lg:col-span-3 space-y-6 order-2 lg:order-1 hidden lg:block">
          <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 space-y-4">
            <div className="text-sm font-semibold text-black mb-1">
              Danh mục xếp hạng
            </div>
            <nav className="flex flex-col gap-1">
              {[
                { id: "views", label: "Tài liệu xem nhiều nhất" },
                { id: "rating", label: "Tài liệu đánh giá cao" },
                { id: "authors", label: "Tác giả nổi bật" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-2xl transition-colors ${activeTab === tab.id
                      ? "bg-zinc-100 text-black"
                      : "bg-white text-zinc-500 hover:bg-zinc-50"
                    }`}
                >
                  {tab.label}
                  {activeTab === tab.id && <ChevronRight className="w-4 h-4" />}
                </button>
              ))}
            </nav>
          </div>
          <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 space-y-4">
            <div className="text-[11px] font-bold text-zinc-400 uppercase tracking-[0.1em] mb-1">
              Hệ thống dữ liệu
            </div>
            <div className="flex flex-col gap-4">
              <div className="flex flex-col border-l-2 border-black pl-3 py-1">
                <span className="text-xs font-semibold text-black">Cập nhật thời gian thực</span>
              </div>
              <div className="flex flex-col border-l-2 border-zinc-200 pl-3 py-1">
                <span className="text-xs font-semibold text-black">Đồng bộ hàng ngày</span>
              </div>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-9 order-1 lg:order-2 flex flex-col gap-4">
            <div className="flex lg:hidden border border-zinc-200 bg-white rounded-2xl overflow-hidden shadow-sm">
              {[
                { id: "views", label: "Xem nhiều" },
                { id: "rating", label: "Đánh giá" },
                { id: "authors", label: "Tác giả" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex-1 px-4 py-2 text-[10px] font-bold uppercase tracking-wider border-r border-zinc-200 last:border-0 ${activeTab === tab.id
                      ? "bg-black text-white"
                      : "text-zinc-500"
                    }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {loading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-24 bg-zinc-50 border border-zinc-200 animate-pulse rounded-2xl" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {((activeTab === "authors" ? data?.top_authors : activeTab === "views" ? data?.top_documents_by_views : data?.top_documents_by_rating) || []).length > 0 ? (
                  <>
                    {activeTab === "views" || activeTab === "rating" ? (
                      ((activeTab === "views" ? data?.top_documents_by_views : data?.top_documents_by_rating) || []).map((document, index) => (
                        <div key={`${document._id}-${index}`} className="group flex items-center justify-between p-4 border border-zinc-200 bg-white rounded-2xl hover:border-black transition-colors shadow-sm">
                          <div className="flex items-center gap-6">
                            <div className="relative">
                              {renderRankNumber(index)}
                            </div>
                            <div className="w-14 h-20 bg-zinc-100 rounded-xl overflow-hidden shrink-0 flex items-center justify-center">
                              {document.cover_image ? (
                                <img
                                  src={document.cover_image.startsWith("http") ? document.cover_image : `${API_URL}/storage/${document.cover_image}`}
                                  className="w-full h-full object-cover grayscale mix-blend-multiply group-  "
                                  alt={document.title}
                                />
                              ) : (
                                <FileText className="w-6 h-6 text-zinc-400 stroke-[1]" />
                              )}
                            </div>
                            <div className="flex flex-col gap-1">
                              <div className="flex flex-wrap gap-1">
                                <span className="px-1.5 py-0.5 border border-zinc-200 bg-zinc-100 rounded-md text-[9px] font-bold text-zinc-500 uppercase tracking-tighter">Tài liệu</span>
                              </div>
                              <Link href={`/tai-lieu/${document.slug}`} className="text-sm font-bold text-black line-clamp-1  decoration-2">
                                {document.title}
                              </Link>
                              <span className="text-[11px] font-medium text-zinc-500">
                                {document.author?.full_name || "Tác giả ẩn danh"}
                              </span>
                            </div>
                          </div>
                          <div className="flex flex-col items-end shrink-0 pl-6 border-l border-zinc-100">
                            {activeTab === "views" ? (
                              <>
                                <span className="text-base font-black text-black leading-none">{document.views_count?.toLocaleString() || 0}</span>
                                <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest mt-1">Lượt xem</span>
                              </>
                            ) : (
                              <>
                                <span className="text-base font-black text-black leading-none">{document.rating_avg?.toFixed(1) || "0.0"}</span>
                                <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest mt-1">Đánh giá</span>
                              </>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      (data?.top_authors || []).map((author, index) => (
                        <Link key={`${author._id}-${index}`} href={`/authors/${author.slug}`} className="group flex items-center justify-between p-4 border border-zinc-200 bg-white rounded-2xl hover:border-black transition-colors shadow-sm">
                          <div className="flex items-center gap-6">
                            {renderRankNumber(index)}
                            <div className="w-12 h-12 rounded-2xl bg-zinc-100 border border-zinc-200 overflow-hidden shrink-0 flex items-center justify-center">
                              {author.avatar_url ? (
                                <img
                                  src={author.avatar_url.startsWith("http") ? author.avatar_url : `${API_URL}/storage/${author.avatar_url}`}
                                  className="w-full h-full object-cover grayscale mix-blend-multiply group-  "
                                  alt={author.full_name}
                                />
                              ) : (
                                <span className="font-bold text-black text-base">{author.full_name?.[0]?.toUpperCase()}</span>
                              )}
                            </div>
                            <div className="flex flex-col gap-1">
                              <span className="text-sm font-bold text-black group- decoration-2">{author.full_name}</span>
                              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Tác giả nổi bật</span>
                            </div>
                          </div>
                          <div className="flex flex-col items-end shrink-0 pl-6 border-l border-zinc-100">
                            <span className="text-base font-black text-black leading-none">{author.popularity_score?.toLocaleString() || 0}</span>
                            <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest mt-1">Lượt xem</span>
                          </div>
                        </Link>
                      ))
                    )}
                  </>
                ) : (
                  <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white rounded-2xl shadow-sm">
                    <p className="text-sm font-medium text-zinc-500">Chưa có dữ liệu</p>
                  </div>
                )}
              </div>
            )}
        </main>
      </div>
    </div>
  );
}
