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
  CheckCircle2,
  Flag,
} from "lucide-react";
import { useAuth } from "@/contexts/Auth";
import { useToast } from "@/contexts/Toast";
import { getDocumentBySlugAPI } from "@/services/document.service";
import { purchaseDocumentAPI } from "@/services/wallet.service";
import { toggleBookmarkAPI } from "@/services/bookmark.service";
import Review from "@/components/Review";
import Comment from "@/components/Comment";
import Report from "@/components/Report";

export default function DocumentDetailsPage() {
  const params = useParams();
  const slug = params?.slug as string;
  const router = useRouter();
  const { user } = useAuth() as any;
  const { showToast } = useToast();

  const [docData, setDocData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"about" | "chapters" | "preview" | "reviews" | "comments">("about");
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
      } catch (err) {}
    };
  }, [docData]);

  const handleRead = () => {
    if (!docData) return;
    router.push(`/tai-lieu/viewer/${docData._id || docData.id}`);
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
        showToast(isBookmarked ? "Đã gỡ khỏi dấu trang" : "Đã thêm vào dấu trang", "success");
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
        showToast(res.message || "Số dư không đủ để thực hiện giao dịch", "error");
      }
    } catch (err: any) {
      showToast("Giao dịch thất bại. Vui lòng thử lại sau", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleShare = () => {
    if (typeof navigator !== "undefined" && navigator.share) {
      navigator.share({
        title: docData?.title,
        text: docData?.description,
        url: window.location.href,
      }).catch(() => showToast("Không thể thực hiện chia sẻ", "error"));
    } else {
      navigator.clipboard.writeText(window.location.href);
      showToast("Đã sao chép liên kết", "success");
    }
  };

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center font-sans bg-white">
        <Loader2 className="w-8 h-8 text-zinc-300 animate-spin" />
      </div>
    );
  }

  if (error || !docData) {
    return (
      <div className="flex h-[80vh] flex-col items-center justify-center gap-6 font-sans bg-white">
        <AlertCircle className="w-12 h-12 text-zinc-300" />
        <p className="text-sm font-medium text-zinc-500">{error || "Thực thể không tồn tại"}</p>
        <button onClick={() => router.back()} className="h-10 px-6 bg-black text-white text-sm font-medium rounded-none  ">
          Quay lại
        </button>
      </div>
    );
  }

  return (
    <>
      <div className="w-full max-w-5xl mx-auto px-6 py-12 font-sans bg-white text-black selection:bg-black selection:text-white min-h-screen">
        {showReportModal && (
          <Report itemId={docData._id || docData.id} itemType="document" onClose={() => setShowReportModal(false)} />
        )}

        <div className="flex flex-col md:flex-row gap-12 mb-16 items-start">
          <div className="w-full md:w-64 shrink-0 flex justify-center md:justify-start">
            <div className="w-48 md:w-full aspect-[2/3] border border-zinc-200 bg-zinc-50 flex items-center justify-center rounded-none overflow-hidden relative">
              {docData.cover_image ? (
                <img src={docData.cover_image} className="w-full h-full object-cover grayscale" alt="" />
              ) : (
                <div className="flex flex-col items-center gap-4 text-center p-6">
                  <BookOpen className="w-8 h-8 text-zinc-300" />
                  <span className="text-xs font-medium text-zinc-500 line-clamp-3">{docData.title}</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex-1 space-y-8 w-full">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-4">
                <span className="px-3 py-1 bg-black text-white text-xs font-medium rounded-none">
                  {docData.category_name || "Nội dung"}
                </span>
                <div className="flex items-center gap-2 text-sm font-medium text-zinc-500">
                  <Star className="w-4 h-4 text-zinc-300 fill-zinc-300" />
                  <span className="text-black">{docData.average_rating ? docData.average_rating.toFixed(1) : "0.0"}</span>
                  <span className="text-zinc-300">/</span>
                  <span>5.0</span>
                </div>
              </div>

              <h1 className="font-bold tracking-tight text-black text-4xl md:text-5xl leading-tight">
                {docData.title}
              </h1>

              <div className="flex flex-wrap items-center gap-8 text-sm text-zinc-600 pt-2">
                <button onClick={() => router.push(`/authors/${docData.author?.slug || docData.author_id}`)} className="flex items-center gap-3   group">
                  <div className="w-8 h-8 bg-zinc-50 border border-zinc-200 flex items-center justify-center overflow-hidden rounded-none">
                    {docData.author?.avatar_url ? (
                      <img src={docData.author.avatar_url} className="w-full h-full object-cover grayscale" alt="" />
                    ) : (
                      <User className="w-4 h-4 text-zinc-400" />
                    )}
                  </div>
                  <div className="flex flex-col items-start">
                    <span className="text-xs text-zinc-500">Tác giả</span>
                    <span className="font-medium text-black group-">
                      {docData.author?.full_name || docData.author?.username || "Cộng tác viên"}
                    </span>
                  </div>
                </button>

                <div className="flex items-center gap-8">
                  <div className="flex flex-col items-start">
                    <span className="text-xs text-zinc-500">Lượt xem</span>
                    <span className="font-medium text-black">{docData.view_count?.toLocaleString() || 0}</span>
                  </div>
                  <div className="flex flex-col items-start">
                    <span className="text-xs text-zinc-500">Số trang</span>
                    <span className="font-medium text-black">{docData.pages_count || "---"}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-4 border-t border-zinc-200 pt-8">
              <button onClick={handleRead} className="h-12 px-6 bg-black text-white text-sm font-medium flex items-center justify-center gap-2 rounded-none  ">
                <BookOpen className="w-4 h-4" /> Đọc ngay
              </button>
              <button onClick={handleBookmark} className={`h-12 px-6 border flex items-center justify-center gap-2 text-sm font-medium  rounded-none ${isBookmarked ? "bg-black text-white border-black" : "bg-white text-black border-zinc-200 "}`}>
                <Bookmark className={`w-4 h-4 ${isBookmarked ? "fill-current" : ""}`} /> {isBookmarked ? "Đã lưu" : "Lưu"}
              </button>
              {docData.is_premium && (
                <button onClick={handlePurchase} className="h-12 px-6 bg-white text-black border border-zinc-200 text-sm font-medium flex items-center justify-center gap-2 rounded-none  ">
                  <ShoppingCart className="w-4 h-4" /> Mua tài liệu
                </button>
              )}
              <button onClick={() => setActiveTab("reviews")} className="h-12 px-6 border border-zinc-200 bg-white text-black text-sm font-medium flex items-center justify-center gap-2 rounded-none  ">
                <Star className="w-4 h-4" /> Đánh giá
              </button>
            </div>
            
            <div className="flex items-center gap-4 text-sm font-medium text-zinc-500 pt-4">
               <button onClick={handleShare} className="flex items-center gap-2  ">
                 <Share2 className="w-4 h-4" /> Chia sẻ
               </button>
               <span className="text-zinc-300">|</span>
               <button onClick={() => setShowReportModal(true)} className="flex items-center gap-2  ">
                 <Flag className="w-4 h-4" /> Báo cáo
               </button>
            </div>

            <div className="p-4 border border-zinc-200 bg-zinc-50 flex items-start gap-3 rounded-none mt-6">
              <ShieldCheck className="w-5 h-5 text-zinc-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium text-black">Hệ thống chứng thực</p>
                <p className="text-sm text-zinc-600">Tài liệu đã được kiểm định chất lượng và đảm bảo tính toàn vẹn.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-12 items-start">
          <div className="w-full space-y-8">
            <div id="document-tabs" className="border-b border-zinc-200 flex gap-8 overflow-x-auto scrollbar-hide">
              {[
                { id: "about", label: "Tóm lược" },
                { id: "chapters", label: "Mục lục" },
                { id: "preview", label: "Xem trước" },
                { id: "reviews", label: "Đánh giá" },
                { id: "comments", label: "Thảo luận" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`pb-4 text-sm font-medium relative shrink-0  ${activeTab === tab.id ? "text-black" : "text-zinc-500 "}`}
                >
                  {tab.label}
                  {activeTab === tab.id && <div className="absolute bottom-[-1px] left-0 right-0 h-[1px] bg-black" />}
                </button>
              ))}
            </div>

            <div className="min-h-[400px]">
              {activeTab === "about" && (
                <div className="space-y-8">
                  <div className="prose prose-zinc max-w-none">
                    <div className="text-black leading-relaxed text-base space-y-6">
                      {docData.description ? (
                        <div dangerouslySetInnerHTML={{ __html: docData.description.replace(/\n/g, "<br/>") }} />
                      ) : (
                        <div className="py-12 text-center text-zinc-500 text-sm border border-dashed border-zinc-200">
                          Chưa có nội dung tóm lược cho tài liệu này.
                        </div>
                      )}
                    </div>
                  </div>
                  {docData.tags?.length > 0 && (
                    <div className="pt-8 border-t border-zinc-200 space-y-4">
                      <h4 className="text-sm font-medium text-zinc-500">Từ khóa liên kết</h4>
                      <div className="flex flex-wrap gap-2">
                        {docData.tags.map((tag: string, i: number) => (
                          <span key={i} className="px-3 py-1 bg-zinc-50 border border-zinc-200 text-sm font-medium text-zinc-600 rounded-none cursor-pointer  ">#{tag}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === "chapters" && (
                <div className="space-y-0 border border-zinc-200 rounded-none overflow-hidden">
                  {docData.chapters && docData.chapters.length > 0 ? (
                    <table className="w-full text-left text-sm border-collapse">
                      <thead>
                        <tr className="bg-zinc-50 border-b border-zinc-200 text-zinc-600 font-medium">
                          <th className="px-6 py-4 font-medium">Chương / Phần</th>
                          <th className="px-6 py-4 font-medium">Số từ</th>
                          <th className="px-6 py-4 font-medium text-right">Trạng thái</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-200">
                        {docData.chapters.map((chapter: any, idx: number) => (
                          <tr key={idx} className=" ">
                            <td className="px-6 py-4 font-medium text-black">{chapter.title || `Chương ${idx + 1}`}</td>
                            <td className="px-6 py-4 text-zinc-600">{chapter.word_count?.toLocaleString() || "---"}</td>
                            <td className="px-6 py-4 text-right">
                              {chapter.is_premium ? (
                                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-500">
                                  <Lock className="w-3 h-3" /> Trả phí
                                </span>
                              ) : (
                                <span className="text-xs font-medium text-black">Miễn phí</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div className="py-16 text-center text-zinc-500 text-sm border border-zinc-200 bg-zinc-50">
                      Tài liệu này không có mục lục chi tiết.
                    </div>
                  )}
                </div>
              )}

              {activeTab === "preview" && (
                <div className="space-y-8">
                  {(() => {
                    const isPrivileged = user && ["admin", "author", "moderator"].includes(user.role?.toLowerCase());
                    const hasPaid = docData.has_purchased || !docData.is_premium;
                    const canSeeFull = isPrivileged || hasPaid;
                    const previewLimit = docData.preview_pages || 5;
                    const contentToDisplay = canSeeFull ? docData.content : (docData.content || "").slice(0, previewLimit * 1000);

                    return (
                      <div className="bg-white border border-zinc-200 min-h-[600px] relative rounded-none">
                        <div className="p-8 md:p-16 space-y-8">
                          <article className="prose prose-zinc max-w-none">
                            <div className="text-black leading-relaxed text-base space-y-6">
                              {docData.content ? (
                                <div dangerouslySetInnerHTML={{ __html: contentToDisplay.replace(/\n/g, "<br/><br/>") }} />
                              ) : (
                                <div className="space-y-6 text-center py-20">
                                  <p className="text-lg font-medium text-black">Dữ liệu đang được trích xuất.</p>
                                  <p className="text-zinc-500 text-sm">{docData.description || "Nội dung sẽ sớm được cập nhật."}</p>
                                </div>
                              )}
                            </div>
                          </article>
                          {!canSeeFull && (
                            <div className="mt-20 pt-20 border-t border-zinc-200 flex flex-col items-center text-center space-y-8 relative">
                              <div className="absolute inset-x-0 bottom-0 h-64 bg-gradient-to-t from-white via-white/80 to-transparent pointer-events-none" />
                              <div className="relative z-20 space-y-6 pb-16">
                                <div className="w-16 h-16 bg-zinc-50 border border-zinc-200 flex items-center justify-center mx-auto rounded-none">
                                  <Lock className="w-6 h-6 text-zinc-400" />
                                </div>
                                <div className="space-y-2">
                                  <h3 className="text-xl font-bold text-black">Giới hạn xem trước</h3>
                                  <p className="text-sm text-zinc-500 max-w-md mx-auto">Bạn đã đọc hết phần xem trước. Mở khóa để khám phá toàn bộ nội dung.</p>
                                </div>
                                <button onClick={handlePurchase} className="h-12 px-8 bg-black text-white text-sm font-medium rounded-none  ">Sở hữu tài liệu</button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}

              {activeTab === "reviews" && (
                <div className="bg-white border border-zinc-200 p-8 rounded-none">
                  <Review documentId={docData._id || docData.id} />
                </div>
              )}
              {activeTab === "comments" && (
                <div className="bg-white p-8 border border-zinc-200 rounded-none">
                  <Comment itemId={docData._id || docData.id} itemType="document" />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
