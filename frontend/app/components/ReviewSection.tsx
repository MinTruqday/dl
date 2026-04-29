"use client";

import { useState, useEffect, useCallback } from "react";
import { getDocumentReviewsAPI, createDocumentReviewAPI } from "@/app/lib/api";
import { Star, User, Send, Loader2 } from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";
import { Notification } from "@/app/components/NotificationToast";

interface ReviewSectionProps {
  documentId: string;
}

export default function ReviewSection({ documentId }: ReviewSectionProps) {
  const { user } = useAuth() as any;
  const [reviews, setReviews] = useState<any[]>([]);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadReviews = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getDocumentReviewsAPI(documentId);
      setReviews(Array.isArray(res.data) ? res.data : []);
    } catch (err: any) {
      console.error("Lỗi tải đánh giá:", err);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    loadReviews();
  }, [loadReviews]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setNotification({ type: "error", text: "Vui lòng đăng nhập để gửi đánh giá." });
      return;
    }
    setSubmitting(true);
    try {
      await createDocumentReviewAPI(documentId, rating, comment);
      setNotification({ type: "success", text: "Đã đăng đánh giá thành công." });
      setComment("");
      setRating(5);
      loadReviews();
    } catch (e) {
      setNotification({ type: "error", text: "Gửi đánh giá thất bại, vui lòng thử lại." });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mt-20 space-y-12 font-sans max-w-5xl mx-auto px-4">
      {notification && (
        <div className="fixed top-24 right-8 z-[100] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      <div className="flex items-center justify-between border-b border-zinc-100 pb-6">
        <h2 className="text-xl font-bold text-black tracking-tight">Đánh giá cộng đồng</h2>
        <div className="text-[11px] font-bold text-zinc-300">{reviews.length} đánh giá</div>
      </div>

      {user ? (
        <form
          onSubmit={handleSubmit}
          className="bg-zinc-50 border border-zinc-200 p-10 space-y-10 animate-in fade-in duration-500"
        >
          <div className="space-y-6 text-center md:text-left">
            <label className="text-[11px] font-bold text-zinc-400">Xếp hạng của bạn</label>
            <div className="flex gap-2 justify-center md:justify-start">
              {[1, 2, 3, 4, 5].map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setRating(s)}
                  className={`p-1.5 transition-all active:scale-90 ${
                    s <= rating ? "text-black" : "text-zinc-200 hover:text-zinc-300"
                  }`}
                >
                  <Star className={`w-8 h-8 ${s <= rating ? "fill-black" : "fill-none"}`} />
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <label className="text-[11px] font-bold text-zinc-400">Nội dung đánh giá</label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder=""
              className="w-full bg-white border border-zinc-100 p-5 text-sm font-medium focus:border-black focus:outline-none min-h-[160px] transition-all placeholder:text-zinc-200"
              required
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full md:w-auto px-10 py-4 bg-black text-white text-[11px] font-bold hover:bg-zinc-800 transition-all flex items-center justify-center gap-3 active:scale-95"
          >
            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Gửi đánh giá
          </button>
        </form>
      ) : (
        <div className="p-12 border border-dashed border-zinc-200 bg-zinc-50/20 text-center">
          <p className="text-[11px] font-bold text-zinc-300">Đăng nhập để tham gia đánh giá</p>
        </div>
      )}

      <div className="space-y-12">
        {loading ? (
          <div className="space-y-8">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-zinc-50 animate-pulse border border-zinc-100" />
            ))}
          </div>
        ) : reviews.length > 0 ? (
          reviews.map((rev) => (
            <div key={rev._id} className="group space-y-6 animate-in fade-in duration-500">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 border border-zinc-100 bg-zinc-50 flex items-center justify-center overflow-hidden shrink-0">
                    {rev.avatar_url ? (
                      <img src={rev.avatar_url} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <User className="w-5 h-5 text-zinc-200" />
                    )}
                  </div>
                  <div>
                    <div className="text-[13px] font-bold text-black tracking-tight">{rev.full_name}</div>
                    <div className="flex items-center gap-1 mt-1">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`w-3 h-3 ${i < rev.rating ? "text-black fill-black" : "text-zinc-100"}`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
                <div className="text-[11px] font-bold text-zinc-200">
                  {new Date(rev.created_at || Date.now()).toLocaleDateString("vi-VN")}
                </div>
              </div>
              <p className="text-sm text-zinc-500 leading-relaxed pl-14 font-medium">{rev.comment}</p>
            </div>
          ))
        ) : (
          <div className="py-24 text-center">
            <Star className="w-10 h-10 text-zinc-50 mx-auto mb-4" />
            <p className="text-[11px] font-bold text-zinc-300">Chưa có đánh giá nào</p>
          </div>
        )}
      </div>
    </div>
  );
}
