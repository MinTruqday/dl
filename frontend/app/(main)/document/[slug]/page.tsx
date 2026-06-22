"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  BookOpen,
  Star,
  Share2,
  AlertCircle,
  ShoppingCart,
  Bookmark,
  Loader2,
  User,
  Lock,
  ShieldCheck,
  Flag,
} from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { getDocumentBySlugAPI } from "@/features/content/services/document_metadata.service";
import { purchaseDocumentAPI } from "@/features/finance/services/account_ledger.service";
import { toggleBookmarkAPI } from "@/features/content/services/document_bookmark.service";

import Comment from "@/features/communication/components/Comment";
import Report from "@/features/provision/components/Report";
import { QRCodeSVG } from "qrcode.react";

export default function DocumentDetailsPage() {
  const params = useParams();
  const slug = params?.slug as string;
  const router = useRouter();
  const { user } = useAuth() as any;
  const { showToast } = useToast();

  const [docData, setDocData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<
    "about" | "chapters" | "preview" | "comments"
  >("about");
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);

  const fetchDocument = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    try {
      const data = await getDocumentBySlugAPI(slug);
      if (data?.data) {
        setDocData(data.data);
        setIsBookmarked(data.data.is_bookmarked || false);
      } else {
        setError("Không thể truy xuất dữ liệu tài liệu");
      }
    } catch (err: any) {
      setError(err.message || "Mất kết nối với hệ thống lưu trữ");
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    fetchDocument();
  }, [fetchDocument]);

  useEffect(() => {
    if (!docData?.drm_settings?.disable_copy) return;
    const preventAction = (e: Event) => e.preventDefault();
    document.addEventListener("contextmenu", preventAction);
    document.addEventListener("copy", preventAction);
    document.addEventListener("selectstart", preventAction);
    return () => {
      document.removeEventListener("contextmenu", preventAction);
      document.removeEventListener("copy", preventAction);
      document.removeEventListener("selectstart", preventAction);
    };
  }, [docData]);

  useEffect(() => {
    if (!docData?.drm_settings?.hide_from_search) return;
    const meta = document.createElement("meta");
    meta.name = "robots";
    meta.content = "noindex";
    document.head.appendChild(meta);
    return () => {
      try {
        document.head.removeChild(meta);
      } catch (err: any) {
        console.warn("Could not remove head meta", err.message || err);
      }
    };
  }, [docData]);

  const handleRead = () => {
    if (!docData) return;
    router.push(`/document/viewer/${docData._id || docData.id}`);
  };

  const handleBookmark = async () => {
    if (!docData) return;
    if (!user) {
      showToast("Vui lòng đăng nhập để lưu tài liệu", "error");
      return;
    }
    try {
      const ok = await toggleBookmarkAPI(docData._id || docData.id);
      if (ok) {
        setIsBookmarked(!isBookmarked);
        showToast(
          isBookmarked ? "Đã gỡ khỏi dấu trang" : "Đã thêm vào dấu trang",
          "success",
        );
      }
    } catch (err: any) {
      showToast("Cập nhật dấu trang thất bại", "error");
    }
  };

  const handlePurchase = async () => {
    if (!docData) return;
    if (!user) {
      showToast("Vui lòng đăng nhập để thực hiện giao dịch", "error");
      return;
    }
    setLoading(true);
    try {
      const res = await purchaseDocumentAPI(docData._id || docData.id);
      if (res.status === 200 || res.status === "purchased") {
        showToast("Giao dịch thành công", "success");
        setTimeout(() => window.location.reload(), 1500);
      } else {
        showToast(
          res.message || "Số dư không đủ để thực hiện giao dịch",
          "error",
        );
      }
    } catch (err: any) {
      showToast("Giao dịch thất bại. Vui lòng thử lại sau", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleShare = () => {
    if (typeof navigator !== "undefined" && navigator.share) {
      navigator
        .share({
          title: docData?.title,
          text: docData?.description,
          url: window.location.href,
        })
        .catch(() => showToast("Không thể thực hiện chia sẻ", "error"));
    } else {
      navigator.clipboard.writeText(window.location.href);
      showToast("Đã sao chép liên kết", "success");
    }
  };

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center font-sans bg-zinc-50">
        <Loader2 className="w-8 h-8 text-black animate-spin" />
      </div>
    );
  }

  if (error || !docData) {
    return (
      <div className="flex h-[80vh] flex-col items-center justify-center gap-6 font-sans bg-zinc-50">
        <AlertCircle className="w-12 h-12 text-zinc-300" />
        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
          {error || "Thực thể không tồn tại"}
        </p>
        <button
          onClick={() => router.back()}
          className="h-11 px-6 bg-black text-white text-xs font-bold uppercase tracking-widest rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-1 shadow-md"
        >
          Quay lại
        </button>
      </div>
    );
  }

  return (
    <>
      <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 font-sans bg-zinc-50 text-zinc-900 selection:bg-zinc-900 selection:text-white min-h-screen">
        {showReportModal && (
          <Report
            itemId={docData._id || docData.id}
            itemType="document"
            onClose={() => setShowReportModal(false)}
          />
        )}

        <div className="flex flex-col md:flex-row gap-8 mb-10 items-start">
          <div className="w-full md:w-64 shrink-0 flex justify-center md:justify-start">
            <div className="w-48 md:w-full aspect-[2/3] border border-zinc-100 bg-white shadow-sm flex items-center justify-center rounded-3xl overflow-hidden relative transition-all duration-300 hover:scale-[1.02] hover:shadow-md">
              {docData.cover_image ? (
                <img
                  src={docData.cover_image}
                  className="w-full h-full object-cover"
                  alt=""
                />
              ) : (
                <div className="flex flex-col items-center gap-4 text-center p-6">
                  <BookOpen className="w-8 h-8 text-zinc-200 stroke-[1.5]" />
                  <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest line-clamp-3">
                    {docData.title}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="flex-1 space-y-6 w-full">
            <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-6 md:p-8 space-y-6">
              <div className="flex flex-wrap items-center gap-3">
                <span className="px-3 py-1.5 bg-zinc-100 text-zinc-900 text-[9px] font-bold uppercase tracking-widest rounded-xl">
                  {docData.category_name || "Nội dung"}
                </span>
              </div>

              <h1 className="font-bold tracking-tight text-zinc-900 text-3xl md:text-4xl leading-tight">
                {docData.title}
              </h1>

              <div className="flex flex-wrap items-center gap-6 text-[10px] text-zinc-400 pt-2 border-t border-zinc-50">
                <button
                  onClick={() =>
                    router.push(
                      `/authors/${docData.author?.slug || docData.author_id}`,
                    )
                  }
                  className="flex items-center gap-3 group transition-all"
                >
                  <div className="w-8 h-8 bg-zinc-50 border border-zinc-100 flex items-center justify-center overflow-hidden rounded-xl shadow-sm group-hover:scale-105 transition-transform">
                    {docData.author?.avatar_url ? (
                      <img
                        src={docData.author.avatar_url}
                        className="w-full h-full object-cover"
                        alt=""
                      />
                    ) : (
                      <User className="w-3.5 h-3.5 text-zinc-400" />
                    )}
                  </div>
                  <div className="flex flex-col items-start gap-0.5">
                    <span className="font-bold uppercase tracking-widest">Tác giả</span>
                    <span className="font-medium text-zinc-900 group-hover:text-black transition-colors">
                      {docData.author?.full_name ||
                        docData.author?.username ||
                        "Cộng tác viên"}
                    </span>
                  </div>
                </button>

                <div className="w-[1px] h-6 bg-zinc-100"></div>

                <div className="flex items-center gap-6">
                  <div className="flex flex-col items-start gap-0.5">
                    <span className="font-bold uppercase tracking-widest">Lượt xem</span>
                    <span className="font-medium text-zinc-900">
                      {docData.view_count?.toLocaleString() || 0}
                    </span>
                  </div>
                  <div className="flex flex-col items-start gap-0.5">
                    <span className="font-bold uppercase tracking-widest">Số trang</span>
                    <span className="font-medium text-zinc-900">
                      {docData.pages_count || "---"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap gap-3 pt-6">
                <button
                  onClick={handleRead}
                  className="h-11 px-6 bg-black text-white text-xs font-bold flex items-center justify-center gap-2 rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-1 shadow-md"
                >
                  <BookOpen className="w-4 h-4" /> Đọc ngay
                </button>
                <button
                  onClick={handleBookmark}
                  className={`h-11 px-6 border flex items-center justify-center gap-2 text-xs font-bold rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-1 ${isBookmarked ? "bg-black text-white border-black shadow-md" : "bg-white text-zinc-900 border-zinc-200 shadow-sm"}`}
                >
                  <Bookmark
                    className={`w-4 h-4 ${isBookmarked ? "fill-current" : ""}`}
                  />{" "}
                  {isBookmarked ? "Đã lưu" : "Lưu"}
                </button>
                {docData.is_premium && (
                  <button
                    onClick={handlePurchase}
                    className="h-11 px-6 bg-white text-zinc-900 border border-zinc-200 text-xs font-bold flex items-center justify-center gap-2 rounded-2xl shadow-sm transition-all duration-200 hover:scale-[1.02] hover:-translate-y-1"
                  >
                    <ShoppingCart className="w-4 h-4" /> Mua tài liệu
                  </button>
                )}
              </div>

              <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest text-zinc-400 pt-4">
                <button
                  onClick={handleShare}
                  className="flex items-center gap-1.5 hover:text-black transition-colors"
                >
                  <Share2 className="w-3.5 h-3.5" /> Chia sẻ
                </button>
                <span className="text-zinc-200">•</span>
                <button
                  onClick={() => setShowReportModal(true)}
                  className="flex items-center gap-1.5 hover:text-black transition-colors"
                >
                  <Flag className="w-3.5 h-3.5" /> Báo cáo
                </button>
              </div>
            </div>

            <div className="p-5 bg-white/90 backdrop-blur-md border border-zinc-100 flex items-start gap-4 rounded-3xl shadow-sm">
              <div className="w-10 h-10 bg-zinc-50 rounded-2xl flex items-center justify-center shrink-0">
                <ShieldCheck className="w-5 h-5 text-zinc-400" />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-zinc-900 uppercase tracking-widest">
                  Hệ thống chứng thực
                </p>
                <p className="text-[10px] font-medium text-zinc-500 uppercase tracking-widest">
                  Tài liệu đã được kiểm định chất lượng và đảm bảo tính toàn vẹn.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm overflow-hidden">
          <div className="border-b border-zinc-100 flex gap-2 p-3 overflow-x-auto no-scrollbar bg-zinc-50/50">
            {[
              { id: "about", label: "Tóm lược" },
              { id: "chapters", label: "Mục lục" },
              { id: "preview", label: "Xem trước" },
              { id: "comments", label: "Thảo luận" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2.5 text-[10px] font-bold uppercase tracking-widest rounded-2xl transition-all duration-200 shrink-0 ${activeTab === tab.id ? "bg-zinc-900 text-white shadow-md hover:scale-[1.02] hover:-translate-y-0.5" : "text-zinc-500 hover:bg-white hover:shadow-sm"}`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="p-6 md:p-8 min-h-[400px]">
            {activeTab === "about" && (
              <div className="space-y-8">
                <div className="prose prose-zinc max-w-none">
                  <div className="text-zinc-900 leading-relaxed text-sm font-medium space-y-6">
                    {docData.description ? (
                      <div
                        dangerouslySetInnerHTML={{
                          __html: docData.description.replace(/\n/g, "<br/>"),
                        }}
                      />
                    ) : (
                      <div className="py-16 text-center bg-zinc-50 rounded-3xl border border-zinc-100 flex flex-col items-center gap-3">
                        <BookOpen className="w-8 h-8 text-zinc-200 stroke-[1.5]" />
                        <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                          Chưa có nội dung tóm lược cho tài liệu này.
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                {docData.tags?.length > 0 && (
                  <div className="pt-8 border-t border-zinc-50 space-y-4">
                    <h4 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                      Từ khóa liên kết
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {docData.tags.map((tag: string, i: number) => (
                        <span
                          key={i}
                          className="px-3 py-1.5 bg-zinc-50 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-500 rounded-xl cursor-pointer hover:bg-zinc-100 transition-colors"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "chapters" && (
              <div className="border border-zinc-100 rounded-3xl overflow-hidden bg-white">
                {docData.chapters && docData.chapters.length > 0 ? (
                  <table className="w-full text-left text-xs">
                    <thead className="bg-zinc-50/50">
                      <tr className="border-b border-zinc-100 text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
                        <th className="px-6 py-4">Chương / Phần</th>
                        <th className="px-6 py-4">Số từ</th>
                        <th className="px-6 py-4 text-right">Trạng thái</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-100">
                      {docData.chapters.map((chapter: any, idx: number) => (
                        <tr key={idx} className="hover:bg-zinc-50/50 transition-colors">
                          <td className="px-6 py-4 font-semibold text-zinc-900">
                            {chapter.title || `Chương ${idx + 1}`}
                          </td>
                          <td className="px-6 py-4 text-zinc-500 font-medium">
                            {chapter.word_count?.toLocaleString() || "---"}
                          </td>
                          <td className="px-6 py-4 text-right">
                            {chapter.is_premium ? (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-zinc-100 rounded-xl text-[9px] font-bold text-zinc-500 uppercase tracking-widest">
                                <Lock className="w-3 h-3" /> Trả phí
                              </span>
                            ) : (
                              <span className="inline-flex px-2.5 py-1 bg-zinc-100 rounded-xl text-[9px] font-bold text-zinc-900 uppercase tracking-widest">
                                Miễn phí
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="py-20 text-center flex flex-col items-center gap-3 bg-zinc-50">
                    <BookOpen className="w-8 h-8 text-zinc-200 stroke-[1.5]" />
                    <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                      Tài liệu này không có mục lục chi tiết.
                    </span>
                  </div>
                )}
              </div>
            )}

            {activeTab === "preview" && (
              <div className="space-y-8">
                {(() => {
                  const isPrivileged =
                    user &&
                    ["admin", "author", "moderator"].includes(
                      user.role?.toLowerCase(),
                    );
                  const hasPaid =
                    docData.has_purchased || !docData.is_premium;
                  const canSeeFull = isPrivileged || hasPaid;
                  const contentToDisplay = docData.content || "";

                  return (
                    <div className="bg-white border border-zinc-100 min-h-[600px] relative rounded-3xl overflow-hidden shadow-sm">
                      <div className="p-8 md:p-12 space-y-8">
                        <article className="prose prose-zinc max-w-none">
                          <div className="text-zinc-900 leading-relaxed text-sm font-medium space-y-6">
                            {docData.content ? (
                              <div
                                dangerouslySetInnerHTML={{
                                  __html: contentToDisplay.replace(
                                    /\n/g,
                                    "<br/><br/>",
                                  ),
                                }}
                              />
                            ) : (
                              <div className="flex flex-col items-center text-center py-24 gap-3 bg-zinc-50 rounded-3xl border border-zinc-100">
                                <Loader2 className="w-8 h-8 text-zinc-300 animate-spin" />
                                <p className="text-xs font-bold text-zinc-900 uppercase tracking-widest mt-2">
                                  Dữ liệu đang được trích xuất
                                </p>
                                <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                                  {docData.description ||
                                    "Nội dung sẽ sớm được cập nhật."}
                                </p>
                              </div>
                            )}
                          </div>
                        </article>
                        {!canSeeFull && (
                          <div className="mt-16 pt-16 flex flex-col items-center text-center space-y-6 relative">
                            <div className="absolute inset-x-0 bottom-0 h-64 bg-gradient-to-t from-white via-white/90 to-transparent pointer-events-none" />
                            <div className="relative z-20 space-y-6 pb-12 w-full max-w-md mx-auto">
                              <div className="w-16 h-16 bg-white shadow-sm border border-zinc-100 flex items-center justify-center mx-auto rounded-2xl">
                                <Lock className="w-6 h-6 text-zinc-400" />
                              </div>
                              <div className="space-y-2 bg-white/80 backdrop-blur-sm p-6 rounded-3xl border border-zinc-100 shadow-sm">
                                <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">
                                  Giới hạn xem trước
                                </h3>
                                <p className="text-[10px] font-medium text-zinc-500 uppercase tracking-widest leading-relaxed">
                                  Bạn đã đọc hết phần xem trước. Mở khóa để
                                  khám phá toàn bộ nội dung.
                                </p>
                                <button
                                  onClick={handlePurchase}
                                  className="mt-4 w-full h-11 bg-black text-white text-xs font-bold rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-1 shadow-md"
                                >
                                  Sở hữu tài liệu
                                </button>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

            {activeTab === "comments" && (
              <div className="bg-white p-6 md:p-8 border border-zinc-100 rounded-3xl shadow-sm">
                <Comment
                  itemId={docData._id || docData.id}
                  itemType="document"
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
