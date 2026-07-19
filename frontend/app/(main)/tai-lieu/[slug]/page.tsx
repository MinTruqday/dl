"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  BookOpen,
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
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { getDocumentBySlugAPI } from "@/features/content/services/document.service";
import { toggleBookmarkAPI } from "@/features/content/services/bookmark.service";
import { purchaseDocumentAPI } from "@/features/payment/services/monetization.service";
import Comment from "@/features/content/components/Comment";
import Report from "@/features/management/components/Report";
import { getToken } from "@/features/authentication/services/session.service";
import PageLoader from "@/shared/components/common/PageLoader";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function DocumentDetailsPage() {
  const params = useParams();
  const slug = params?.slug as string;
  const router = useRouter();
  const { user } = useAuth() as any;
  const { showToast } = useToast();

  const [docData, setDocData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"about" | "chapters" | "comments">(
    "about",
  );
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [decryptedContent, setDecryptedContent] = useState<string>("");

  useEffect(() => {
    if (!docData) return;
    if (docData.content_fragments && Array.isArray(docData.content_fragments)) {
      const decrypt = async () => {
        try {
          const token = getToken();
          const docId = docData._id || docData.id;
          const keyRes = await fetch(
            `${API_URL}/tai-lieu/${docId}/khoa-giai-ma`,
            { headers: token ? { Authorization: `Bearer ${token}` } : {} },
          );
          if (!keyRes.ok) throw new Error("Key fetch failed");
          const keyData = await keyRes.json();
          const keyRaw = atob(keyData.data.key);
          const keyBytes = new Uint8Array(keyRaw.length);
          for (let i = 0; i < keyRaw.length; i++)
            keyBytes[i] = keyRaw.charCodeAt(i);
          const cryptoKey = await window.crypto.subtle.importKey(
            "raw",
            keyBytes,
            { name: "AES-GCM" },
            false,
            ["decrypt"],
          );
          let fullText = "";
          for (const frag of docData.content_fragments) {
            const fragRaw = atob(frag);
            const fragBytes = new Uint8Array(fragRaw.length);
            for (let i = 0; i < fragRaw.length; i++)
              fragBytes[i] = fragRaw.charCodeAt(i);
            const iv = fragBytes.slice(0, 12);
            const ct = fragBytes.slice(12);
            const decrypted = await window.crypto.subtle.decrypt(
              { name: "AES-GCM", iv: iv },
              cryptoKey,
              ct,
            );
            fullText += new TextDecoder().decode(decrypted);
          }
          setDecryptedContent(fullText);
        } catch (err) {
          setDecryptedContent(
            "Lỗi giải mã hoặc chứng thực bảo mật không hoàn tất",
          );
        }
      };
      decrypt();
    } else {
      setDecryptedContent(
        docData.content || docData.description || "Không có nội dung hiển thị",
      );
    }
  }, [docData]);

  const fetchDocument = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    try {
      const data = await getDocumentBySlugAPI(slug);
      if (data?.data) {
        setDocData(data.data);
        setIsBookmarked(data.data.is_bookmarked || false);
      } else {
        setError("Lỗi trích xuất thông tin chi tiết tài liệu");
      }
    } catch (err: any) {
      setError("Mất kết nối đến máy chủ lưu trữ dữ liệu");
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    fetchDocument();
  }, [fetchDocument]);

  const handleRead = () => {
    if (!docData) return;
    router.push(`/tai-lieu/xem-truoc/${docData._id || docData.id}`);
  };

  const handleBookmark = async () => {
    if (!docData) return;
    if (!user) {
      showToast("Yêu cầu xác thực tài khoản để thực hiện chức năng này", "error");
      return;
    }
    try {
      await toggleBookmarkAPI(docData._id || docData.id);
      setIsBookmarked(!isBookmarked);
      showToast(
        isBookmarked ? "Gỡ đánh dấu trang hoàn tất" : "Thêm đánh dấu trang hoàn tất",
        "success",
      );
    } catch (err: any) {
      showToast("Lỗi cập nhật trạng thái dấu trang", "error");
    }
  };

  const handlePurchase = async () => {
    if (!docData) return;
    if (!user) {
      showToast("Yêu cầu xác thực tài khoản để thực hiện giao dịch", "error");
      return;
    }
    setIsPurchasing(true);
    try {
      await purchaseDocumentAPI(docData._id || docData.id);
      showToast("Giao dịch thanh toán tài liệu hoàn tất", "success");
      setDocData({ ...docData, has_purchased: true });
    } catch (err: any) {
      showToast(err.message || "Giao dịch thanh toán không hoàn tất", "error");
    } finally {
      setIsPurchasing(false);
    }
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    showToast("Sao chép liên kết vào bộ nhớ tạm hoàn tất", "success");
  };

  if (loading) return <PageLoader />;
  if (error || !docData)
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-[#F5F5F7]">
        <AlertCircle className="w-12 h-12 text-[#FF3B30]" />
        <p className="text-[#6E6E73]">{error || "Tài liệu không tồn tại"}</p>
        <button
          onClick={() => router.back()}
          className="px-6 py-2 bg-[#0071E3] text-white rounded-full text-[15px] font-medium mt-4"
        >
          Quay lại
        </button>
      </div>
    );

  return (
    <div className="w-full h-full py-6 font-sans text-[#1D1D1F]">
      {showReportModal && (
        <Report
          itemId={docData._id || docData.id}
          itemType="document"
          onClose={() => setShowReportModal(false)}
        />
      )}

      <div className="flex flex-col md:flex-row gap-12 mb-12">
        <div className="w-full md:w-[320px] shrink-0">
          <div className="aspect-[3/4] w-full rounded-[18px] overflow-hidden bg-[#F5F5F7] ">
            {docData.cover_url || docData.cover_image ? (
              <img
                src={docData.cover_url || docData.cover_image}
                className="w-full h-full object-cover"
                alt={docData.title}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <BookOpen className="w-12 h-12 text-[#C7C7CC]" />
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 flex flex-col justify-center">
          <span className="text-[13px] font-medium text-[#0071E3] mb-4 block uppercase tracking-wide">
            {docData.category_name || "Tài liệu"}
          </span>
          <h1 className="text-[32px] md:text-[40px] font-semibold text-[#1D1D1F] leading-tight mb-6">
            {docData.title}
          </h1>

          <div className="flex items-center gap-4 mb-8 pb-8 ">
            <div className="w-12 h-12 rounded-full overflow-hidden bg-[#F5F5F7] ">
              {docData.author?.avatar_url ? (
                <img
                  src={docData.author.avatar_url}
                  className="w-full h-full object-cover"
                  alt=""
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <User className="w-6 h-6 text-[#6E6E73]" />
                </div>
              )}
            </div>
            <div>
              <p className="text-[13px] text-[#6E6E73] mb-1">Tác giả</p>
              <p className="text-[15px] font-medium text-[#1D1D1F]">
                {docData.author?.full_name ||
                  docData.author?.username ||
                  docData.author_name ||
                  "Ẩn danh"}
              </p>
            </div>
            <div className="w-px h-10 bg-[#E8E8ED] mx-4"></div>
            <div>
              <p className="text-[13px] text-[#6E6E73] mb-1">Lượt xem</p>
              <p className="text-[15px] font-medium text-[#1D1D1F]">
                {docData.views_count?.toLocaleString() || docData.views || 0}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <button
              onClick={handleRead}
              className="h-12 px-8 bg-[#0071E3] text-white text-[15px] font-medium rounded-full hover:bg-[#0077ED] transition-colors flex items-center gap-2"
            >
              <BookOpen className="w-5 h-5" /> Đọc ngay
            </button>
            {docData.is_premium && !docData.has_purchased && (
              <button
                onClick={handlePurchase}
                disabled={isPurchasing}
                className="h-12 px-8 bg-[#F5F5F7] text-[#1D1D1F] text-[15px] font-medium rounded-full hover:bg-[#E8E8ED] transition-colors flex items-center gap-2"
              >
                <ShoppingCart className="w-5 h-5" />{" "}
                {isPurchasing
                  ? "Đang xử lý..."
                  : `Mua với ${docData.price_dl || 0} dl`}
              </button>
            )}
            <button
              onClick={handleBookmark}
              className={`w-12 h-12 flex items-center justify-center rounded-full transition-colors ${isBookmarked ? "bg-[#0071E3] text-white" : "bg-[#F5F5F7] text-[#6E6E73] hover:bg-[#E8E8ED]"}`}
            >
              <Bookmark
                className={`w-5 h-5 ${isBookmarked ? "fill-current" : ""}`}
              />
            </button>
            <button
              onClick={handleShare}
              className="w-12 h-12 flex items-center justify-center rounded-full bg-[#F5F5F7] text-[#6E6E73] hover:bg-[#E8E8ED] transition-colors"
            >
              <Share2 className="w-5 h-5" />
            </button>
            <button
              onClick={() => setShowReportModal(true)}
              className="w-12 h-12 flex items-center justify-center rounded-full bg-[#F5F5F7] text-[#6E6E73] hover:bg-[#E8E8ED] transition-colors"
            >
              <Flag className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        <div className="w-full md:w-[240px] shrink-0">
          <div className="flex flex-col gap-2">
            {[
              { id: "about", label: "Tóm lược" },
              { id: "chapters", label: "Mục lục" },
              { id: "comments", label: "Thảo luận" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`text-left px-5 py-3 rounded-[10px] text-[15px] font-medium transition-colors ${activeTab === tab.id ? "bg-[#F5F5F7] text-[#1D1D1F]" : "text-[#6E6E73] hover:bg-[#F5F5F7]"}`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 bg-[#F5F5F7] md:bg-transparent border-[#E8E8ED] rounded-[18px] md:rounded-none p-8 md:px-0 md:pt-8 min-h-[400px]">
          {activeTab === "about" && (
            <div className="space-y-6">
              <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
                Tóm lược nội dung
              </p>
              <div className="prose prose-zinc max-w-none text-[#1D1D1F] text-[15px] leading-relaxed">
                {docData.description ? (
                  <div
                    dangerouslySetInnerHTML={{
                      __html: docData.description.replace(/\n/g, "<br/>"),
                    }}
                  />
                ) : (
                  <p className="text-[#6E6E73]">Chưa có thông tin tóm tắt.</p>
                )}
              </div>
              {docData.tags?.length > 0 && (
                <div className="pt-6 mt-6">
                  <h3 className="text-[17px] font-medium text-[#6E6E73] mb-4">
                    Từ khóa
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {docData.tags.map((tag: string, i: number) => (
                      <span
                        key={i}
                        className="px-4 py-2 bg-[#F5F5F7] text-[#1D1D1F] text-[13px] rounded-full"
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
            <div className="space-y-4">
              <p className="text-[13px] font-medium text-[#6E6E73] mb-4 mb-6">
                Mục lục chi tiết
              </p>
              {docData.chapters && docData.chapters.length > 0 ? (
                <div className="divide-y divide-[#E8E8ED]">
                  {docData.chapters.map((chapter: any, idx: number) => (
                    <div
                      key={idx}
                      className="py-4 flex items-center justify-between"
                    >
                      <div>
                        <p className="text-[15px] font-medium text-[#1D1D1F]">
                          {chapter.title || `Chương ${idx + 1}`}
                        </p>
                        <p className="text-[13px] text-[#6E6E73] mt-1">
                          {chapter.word_count?.toLocaleString() || "---"} từ
                        </p>
                      </div>
                      {chapter.is_premium ? (
                        <span className="flex items-center gap-1.5 px-3 py-1 bg-[#F5F5F7] text-[#6E6E73] text-[12px] font-medium rounded-full">
                          <Lock className="w-3.5 h-3.5" /> Trả phí
                        </span>
                      ) : (
                        <span className="px-3 py-1 bg-[#EAF8ED] text-[#34C759] text-[12px] font-medium rounded-full">
                          Miễn phí
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[#6E6E73]">
                  Tài liệu này không có cấu trúc chương.
                </p>
              )}
            </div>
          )}

          {activeTab === "comments" && (
            <div>
              <p className="text-[13px] font-medium text-[#6E6E73] mb-4 mb-6">
                Thảo luận
              </p>
              <Comment itemId={docData._id || docData.id} itemType="document" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
