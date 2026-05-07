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
import { getSocialRankingAPI } from "@/services/social.service";

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
        className={`w-8 h-8 shrink-0 flex items-center justify-center font-bold text-sm border ${
          isTop3
            ? "border-black bg-black text-white"
            : "border-zinc-200 bg-zinc-50 text-zinc-500"
        }`}
      >
        {String(index + 1).padStart(2, "0")}
      </div>
    );
  };

  return (
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <div className="mb-8 border-b border-zinc-200 pb-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold text-black">Xếp hạng</h1>
            <p className="text-zinc-500 text-sm font-medium">
              Tôn vinh giá trị nội dung
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <aside className="lg:col-span-3 space-y-12 order-2 lg:order-1 hidden lg:block">
          <div className="space-y-4">
            <div className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
              Danh mục xếp hạng
            </div>
            <nav className="flex flex-col gap-1">
              {[
                { id: "views", label: "Tài liệu xem nhiều nhất", icon: TrendingUp },
                { id: "rating", label: "Tài liệu đánh giá cao", icon: Star },
                { id: "authors", label: "Tác giả nổi bật", icon: Users },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center justify-between px-3 py-2 text-sm font-medium border rounded-none ${
                    activeTab === tab.id
                      ? "bg-zinc-100 text-black border-zinc-300"
                      : "bg-white text-zinc-500 border-transparent"
                  }`}
                >
                  {tab.label}
                  {activeTab === tab.id && <ChevronRight className="w-4 h-4" />}
                </button>
              ))}
            </nav>
          </div>

          <div className="border border-zinc-200 bg-white p-6 space-y-4 rounded-none">
            <h3 className="text-xs font-semibold text-black border-b border-zinc-200 pb-2 flex items-center gap-2">
              Hệ thống dữ liệu
            </h3>
            <div className="space-y-4">
              <div className="flex flex-col">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Cập nhật lần cuối</span>
                <span className="text-xs font-semibold text-black">Vừa xong</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Chu kỳ thống kê</span>
                <span className="text-xs font-semibold text-black">Thời gian thực</span>
              </div>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-9 order-1 lg:order-2">
          <div className="max-w-2xl mx-auto space-y-8">
            <div className="flex lg:hidden mb-6 border border-zinc-200 bg-white rounded-none">
              {[
                { id: "views", label: "Xem nhiều" },
                { id: "rating", label: "Đánh giá" },
                { id: "authors", label: "Tác giả" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex-1 px-4 py-2 text-xs font-medium border-r border-zinc-200 last:border-0 ${
                    activeTab === tab.id
                      ? "bg-zinc-100 text-black"
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
                  <div key={i} className="h-24 bg-zinc-50 border border-zinc-200 animate-pulse rounded-none" />
                ))}
              </div>
            ) : (
              <div className="">
                {((activeTab === "authors" ? data?.top_authors : activeTab === "views" ? data?.top_documents_by_views : data?.top_documents_by_rating) || []).length > 0 ? (
                  <div className="flex flex-col border border-zinc-200 bg-white rounded-none">
                    {activeTab === "views" || activeTab === "rating" ? (
                      ((activeTab === "views" ? data?.top_documents_by_views : data?.top_documents_by_rating) || []).map((document, index) => (
                        <div key={`${document._id}-${index}`} className="flex items-center justify-between p-4 border-b border-zinc-200 last:border-b-0">
                          <div className="flex items-center gap-4">
                            {renderRankNumber(index)}
                            <div className="w-12 h-16 bg-white border border-zinc-200 overflow-hidden shrink-0 flex items-center justify-center">
                              {document.cover_image ? (
                                <img
                                  src={document.cover_image.startsWith("http") ? document.cover_image : `${API_URL}/storage/${document.cover_image}`}
                                  className="w-full h-full object-cover grayscale mix-blend-multiply"
                                  alt={document.title}
                                />
                              ) : (
                                <FileText className="w-5 h-5 text-zinc-400 stroke-[1]" />
                              )}
                            </div>
                            <div className="flex flex-col justify-center">
                              <Link href={`/documents/${document.slug}`} className="text-sm font-semibold text-black line-clamp-1">
                                {document.title}
                              </Link>
                              <span className="text-xs font-medium text-zinc-500 mt-1 line-clamp-1">
                                Tác giả: {document.author?.full_name || "Tác giả ẩn danh"}
                              </span>
                            </div>
                          </div>
                          <div className="flex flex-col items-end shrink-0 pl-4">
                            {activeTab === "views" ? (
                              <>
                                <span className="text-lg font-bold text-black">{document.views_count?.toLocaleString() || 0}</span>
                                <span className="text-[10px] font-medium text-zinc-500">lượt xem</span>
                              </>
                            ) : (
                              <>
                                <span className="text-lg font-bold text-black">{document.rating_avg?.toFixed(1) || "0.0"}</span>
                                <span className="text-[10px] font-medium text-zinc-500">đánh giá</span>
                              </>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      (data?.top_authors || []).map((author, index) => (
                        <Link key={`${author._id}-${index}`} href={`/authors/${author.slug}`} className="flex items-center justify-between p-4 border-b border-zinc-200 last:border-b-0">
                          <div className="flex items-center gap-4">
                            {renderRankNumber(index)}
                            <div className="w-10 h-10 rounded-full bg-zinc-100 border border-zinc-200 overflow-hidden shrink-0 flex items-center justify-center">
                              {author.avatar_url ? (
                                <img
                                  src={author.avatar_url.startsWith("http") ? author.avatar_url : `${API_URL}/storage/${author.avatar_url}`}
                                  className="w-full h-full object-cover grayscale mix-blend-multiply"
                                  alt={author.full_name}
                                />
                              ) : (
                                <span className="font-semibold text-black text-sm">{author.full_name?.[0]?.toUpperCase()}</span>
                              )}
                            </div>
                            <div className="flex flex-col justify-center">
                              <span className="text-sm font-semibold text-black">{author.full_name}</span>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="px-1.5 py-0.5 border border-zinc-200 text-[10px] font-medium text-zinc-500">Tác giả</span>
                              </div>
                            </div>
                          </div>
                          <div className="flex flex-col items-end shrink-0 pl-4">
                            <span className="text-lg font-bold text-black">{author.followers_count?.toLocaleString() || 0}</span>
                            <span className="text-[10px] font-medium text-zinc-500">độc giả</span>
                          </div>
                        </Link>
                      ))
                    )}
                  </div>
                ) : (
                  <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white rounded-none">
                    <Trophy className="w-8 h-8 text-zinc-400 mb-4 stroke-[1]" />
                    <h2 className="text-lg font-semibold text-black mb-2">Chưa có dữ liệu xếp hạng</h2>
                    <p className="text-xs font-medium text-zinc-500 text-center max-w-xs">
                      Hệ thống đang cập nhật dữ liệu, vui lòng quay lại sau.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
