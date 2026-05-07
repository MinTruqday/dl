"use client";

import React, { useEffect, useState, useCallback } from "react";
import Workspace from "@/components/Workspace";
import { getSocialRankingAPI } from "@/services/social.service";
import { Search, User, ShieldCheck, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useToast } from "@/contexts/ToastContext";

export default function AuthorsPage() {
  const { showToast } = useToast();
  const [authors, setAuthors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [visible, setVisible] = useState(false);
  const router = useRouter();

  const fetchAuthors = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getSocialRankingAPI();
      setAuthors(data.data || data || []);
    } catch (err: any) {
      showToast("Lỗi tải danh sách tác giả", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchAuthors();
  }, [fetchAuthors]);

  const filteredAuthors = authors.filter((a) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (a.username || "").toLowerCase().includes(q) ||
      (a.full_name || "").toLowerCase().includes(q)
    );
  });

  return (
    <Workspace>
      <div className="max-w-6xl mx-auto px-6 py-12 md:py-20 font-sans opacity-100">
        <div className="text-center max-w-2xl mx-auto mb-20 space-y-6">
          <div className="inline-flex items-center px-4 py-1.5 bg-white border border-zinc-100 text-zinc-400 text-[10px] font-bold">
            Khám phá
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tighter text-black">
            Danh sách tác giả
          </h1>
          <p className="text-zinc-500 font-medium leading-relaxed text-sm">
            Kết nối với những cây bút tài năng, theo dõi để cập nhật những tài
            liệu và thông tin mới nhất từ họ.
          </p>
          <div className="relative max-w-md mx-auto mt-10 group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-300" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder=""
              className="w-full h-14 pl-12 pr-4 bg-white border border-zinc-200 rounded-none focus:outline-none focus:border-black focus:bg-white text-sm font-bold placeholder:text-zinc-200"
            />
          </div>
        </div>

        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="bg-white border border-zinc-100 rounded-none h-64"
              />
            ))}
          </div>
        ) : filteredAuthors.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {filteredAuthors.map((author, idx) => (
              <div
                key={author._id}
                className="group relative bg-white border border-zinc-100 rounded-none p-8 flex flex-col items-center text-center cursor-pointer"
                onClick={() =>
                  router.push(`/authors/${author.slug || author._id}`)
                }
              >
                <div className="absolute top-6 left-6 w-10 h-10 bg-white flex items-center justify-center border border-zinc-100 text-[10px] font-bold text-zinc-300 ">
                  #{idx + 1}
                </div>
                <div className="w-28 h-28 rounded-none bg-white border border-zinc-100 overflow-hidden mb-6 relative grayscale">
                  {author.avatar_url ? (
                    <img
                      src={author.avatar_url}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-zinc-200">
                      <User className="w-10 h-10" />
                    </div>
                  )}
                </div>
                <h3 className="text-lg font-bold text-black flex items-center gap-2 mb-2 tracking-tight">
                  {author.username || author.full_name || "Người dùng"}
                  {author.role === "author" && (
                    <ShieldCheck className="w-4 h-4 text-black" />
                  )}
                </h3>
                <p className="text-[12px] text-zinc-400 font-medium mb-6 line-clamp-2 min-h-[40px] leading-relaxed">
                  {author.bio || "Chưa cập nhật nội dung giới thiệu cá nhân."}
                </p>
                <div className="flex items-center gap-6 text-[10px] font-bold text-zinc-300 w-full justify-center pt-8 border-t border-zinc-50">
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-black text-[14px]">
                      {author.followers_count || 0}
                    </span>
                    <span className="text-[9px] font-bold opacity-60">
                      Theo dõi
                    </span>
                  </div>
                  <div className="w-px h-8 bg-zinc-100"></div>
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-black text-[14px]">
                      {author.points || 0}
                    </span>
                    <span className="text-[9px] font-bold opacity-60">
                      Kinh nghiệm
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-32 border border-dashed border-zinc-200 bg-white/20">
            <User className="w-16 h-16 mx-auto mb-6 text-zinc-100" />
            <p className="font-bold text-sm text-zinc-300">
              Không tìm thấy kết quả phù hợp
            </p>
          </div>
        )}
      </div>
    </Workspace>
  );
}
