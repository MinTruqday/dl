"use client";

import { useState, useEffect, useCallback } from "react";
import { getDocumentReviewsAPI, createDocumentReviewAPI } from "@/services/social.service";
import { Star, User, Send, Loader2, MessageCircle } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";

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
        showToast("Không thể kết nối mạng lưới đánh giá", "error");
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
      showToast("Vui lòng đăng nhập để gửi nhận xét tri thức", "error");
      return;
    }
    setSubmitting(true);
    try {
      await createDocumentReviewAPI(documentId, rating, comment);
      showToast("Đã đăng nhận xét tri thức thành công", "success");
      setComment("");
      setRating(5);
      loadReviews();
    } catch (e) {
      showToast("Gửi nhận xét thất bại, vui lòng thử lại sau", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mt-24 space-y-16 font-sans max-w-6xl mx-auto px-6">
      

      <div className="flex items-center justify-between border-b border-zinc-100 pb-8">
        <div className="flex items-center gap-4">
            <MessageCircle className="w-5 h-5 text-black" />
            <h2 className="text-sm font-bold text-black uppercase tracking-widest">Đánh giá cộng đồng</h2>
        </div>
        <div className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{reviews.length} NHẬN XÉT</div>
      </div>

      {user ? (
        <form
          onSubmit={handleSubmit}
          className="bg-zinc-50/30 border border-zinc-100 p-12 space-y-12 animate-in fade-in duration-500 rounded-sm"
        >
          <div className="space-y-6 text-center md:text-left">
            <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1">Xếp hạng tri thức của bạn</label>
            <div className="flex gap-4 justify-center md:justify-start">
              {[1, 2, 3, 4, 5].map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setRating(s)}
                  className={`p-2 transition-all active:scale-90 ${
                    s <= rating ? "text-black" : "text-zinc-100 hover:text-zinc-200"
                  }`}
                >
                  <Star className={`w-10 h-10 ${s <= rating ? "fill-black" : "fill-none"}`} />
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1">Nội dung nhận xét</label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder=""
              className="w-full bg-white border border-zinc-100 p-8 text-sm font-medium focus:border-black focus:outline-none min-h-[200px] transition-all rounded-sm placeholder:text-zinc-200"
              required
            />
          </div>

          <div className="flex justify-end">
            <button
                type="submit"
                disabled={submitting}
                className="w-full md:w-auto px-16 h-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.4em] hover:bg-zinc-800 transition-all flex items-center justify-center gap-4 active:scale-95 rounded-sm"
            >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Gửi nhận xét hệ thống
            </button>
          </div>
        </form>
      ) : (
        <div className="py-20 border border-dashed border-zinc-100 bg-zinc-50/20 text-center rounded-sm">
          <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Đăng nhập để tham gia mạng lưới đánh giá tri thức</p>
        </div>
      )}

      <div className="space-y-16">
        {loading ? (
          <div className="space-y-10">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-40 bg-zinc-50 animate-pulse border border-zinc-100 rounded-sm" />
            ))}
          </div>
        ) : reviews.length > 0 ? (
          reviews.map((rev) => (
            <div key={rev._id} className="group space-y-8 animate-in fade-in duration-500 pb-16 border-b border-zinc-50 last:border-0">
              <div className="flex items-start justify-between gap-6">
                <div className="flex items-center gap-6">
                  <div className="w-12 h-12 border border-zinc-100 bg-zinc-50 flex items-center justify-center overflow-hidden shrink-0 rounded-sm">
                    {rev.avatar_url ? (
                      <img src={rev.avatar_url} alt="" className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-700" />
                    ) : (
                      <User className="w-6 h-6 text-zinc-100" />
                    )}
                  </div>
                  <div>
                    <div className="text-sm font-bold text-black uppercase tracking-tight">{rev.full_name || "Cộng tác viên ẩn danh"}</div>
                    <div className="flex items-center gap-1.5 mt-2">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`w-3.5 h-3.5 ${i < rev.rating ? "text-black fill-black" : "text-zinc-50"}`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
                <div className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest">
                  {new Date(rev.created_at || Date.now()).toLocaleDateString("vi-VN")}
                </div>
              </div>
              <p className="text-base text-zinc-600 leading-loose pl-18 font-medium max-w-4xl">{rev.comment}</p>
            </div>
          ))
        ) : (
          <div className="py-32 text-center border border-zinc-50 bg-zinc-50/10 rounded-sm">
            <Star className="w-12 h-12 text-zinc-50 mx-auto mb-6 stroke-[1]" />
            <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-[0.3em]">Thực thể này chưa có nhận xét tri thức</p>
          </div>
        )}
      </div>
    </div>
  );
}
