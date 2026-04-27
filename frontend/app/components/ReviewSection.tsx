"use client";

import { useState, useEffect } from "react";
import { getBookReviewsAPI, createBookReviewAPI } from "@/app/lib/api";
import { Star, User, Send, StarHalf } from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";

interface ReviewSectionProps {
  bookId: string;
}

export default function ReviewSection({ bookId }: ReviewSectionProps) {
  const { user } = useAuth() as any;
  const [reviews, setReviews] = useState<any[]>([]);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadReviews();
  }, [bookId]);

  const loadReviews = async () => {
    setLoading(true);
    try {
      const data = await getBookReviewsAPI(bookId);
      setReviews(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setSubmitting(true);
    try {
      await createBookReviewAPI(bookId, rating, comment);
      setComment("");
      setRating(5);
      loadReviews();
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mt-16 space-y-12">
      <div className="flex items-center justify-between border-b border-zinc-100 pb-4">
        <h2 className="text-lg font-bold text-black tracking-tight">Đánh giá cộng đồng</h2>
        <div className="text-[12px] font-bold text-zinc-400  tracking-widest">{reviews.length} đánh giá</div>
      </div>

      {user ? (
        <form onSubmit={handleSubmit} className="bg-zinc-50 border border-border p-8 space-y-6">
          <div className="space-y-4">
            <label className="text-[12px] font-bold  tracking-widest text-zinc-400">Xếp hạng của bạn</label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setRating(s)}
                  className={`p-1 transition-colors ${s <= rating ? 'text-black' : 'text-zinc-200 hover:text-zinc-300'}`}
                >
                  <Star className="w-6 h-6 fill-current" />
                </button>
              ))}
            </div>
          </div>
          
          <div className="space-y-4">
             <label className="text-[12px] font-bold  tracking-widest text-zinc-400">Nội dung đánh giá</label>
             <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Chia sẻ cảm nhận của bạn về tài liệu này"
                className="w-full bg-white border border-border  p-4 text-sm focus:border-black focus:outline-none min-h-[120px] transition-all"
                required
             />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full md:w-auto px-8 py-3 bg-black text-white text-[12px] font-bold  tracking-widest hover:bg-zinc-800 transition-all flex items-center justify-center gap-2"
          >
            {submitting ? "Đang gửi" : (
              <>
                Gửi đánh giá
                <Send className="w-3 h-3" />
              </>
            )}
          </button>
        </form>
      ) : (
        <div className="p-8 border border-dashed border-border bg-zinc-50/50 text-center">
           <p className="text-xs font-bold text-zinc-400  tracking-widest">Đăng nhập để tham gia đánh giá</p>
        </div>
      )}

      <div className="space-y-8">
        {loading ? (
          <div className="space-y-6">
            {[1, 2].map((i) => (
              <div key={i} className="h-32 bg-zinc-50 animate-pulse border border-border" />
            ))}
          </div>
        ) : reviews.length > 0 ? (
          reviews.map((rev) => (
            <div key={rev._id} className="group space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8  bg-zinc-100 border border-border flex items-center justify-center overflow-hidden shrink-0">
                    {rev.avatar_url ? (
                       <img src={rev.avatar_url} alt={rev.full_name} className="w-full h-full object-cover" />
                    ) : (
                       <User className="w-4 h-4 text-zinc-300" />
                    )}
                  </div>
                  <div>
                    <div className="text-[12px] font-bold tracking-widest">{rev.full_name}</div>
                    <div className="flex items-center gap-1 mt-0.5">
                      {[...Array(5)].map((_, i) => (
                        <Star key={i} className={`w-2.5 h-2.5 ${i < rev.rating ? 'text-black fill-current' : 'text-zinc-200'}`} />
                      ))}
                    </div>
                  </div>
                </div>
                <div className="text-[13px] font-bold tracking-widest text-zinc-300">
                   {new Date(rev.created_at || Date.now()).toLocaleDateString("vi-VN")}
                </div>
              </div>
              <p className="text-sm text-zinc-600 leading-relaxed pl-11">
                {rev.comment}
              </p>
            </div>
          ))
        ) : (
          <div className="py-12 text-center text-zinc-300">
             <p className="text-[12px] font-bold tracking-widest">Chưa có đánh giá nào</p>
          </div>
        )}
      </div>
    </div>
  );
}
