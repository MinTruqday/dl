"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { CornerDownRight, Loader2, MessageSquare, Reply, Send } from "lucide-react";
import { createCommentAPI, getCommentsByItemAPI } from "@/features/content/services/collaboration.service";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";

interface CommentItem {
  _id: string;
  text?: string;
  content?: string;
  path?: string;
  user?: { full_name?: string; avatar_url?: string };
  created_at: string;
}

export default function Comment({ itemId, itemType = "document" }: { itemId: string; itemType?: "document" }) {
  const { user } = useAuth() as any;
  const { showToast } = useToast();
  const [comments, setComments] = useState<CommentItem[]>([]);
  const [newText, setNewText] = useState("");
  const [replyTo, setReplyTo] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const fetchComments = useCallback(async () => {
    try {
      const data = await getCommentsByItemAPI(itemId);
      setComments(Array.isArray(data.data) ? data.data : data || []);
    } catch {
      showToast("Không thể tải thảo luận", "error");
    } finally {
      setLoading(false);
    }
  }, [itemId, showToast]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!user) {
      showToast("Đăng nhập để tham gia thảo luận", "error");
      return;
    }
    if (!newText.trim()) return;
    setSubmitting(true);
    try {
      await createCommentAPI({ item_id: itemId, content: newText.trim(), parent_id: replyTo, item_type: itemType });
      setNewText("");
      setReplyTo(null);
      await fetchComments();
      showToast("Đã gửi phản hồi", "success");
    } catch (error: any) {
      showToast(error.message || "Không thể gửi phản hồi", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mt-12 border-t border-border pt-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <h3 className="flex items-center gap-2 text-[17px] font-semibold text-ink">
          <MessageSquare className="h-4 w-4 text-brand" />
          Thảo luận
        </h3>
        <span className="text-[13px] text-ink-muted">{comments.length} phản hồi</span>
      </div>

      <form onSubmit={handleSubmit} className="mb-8 rounded-panel border border-border bg-surface p-4">
        {replyTo && (
          <div className="mb-3 flex items-center justify-between rounded-control bg-surface-quiet px-3 py-2 text-[13px] text-ink-muted">
            <span>Đang trả lời một phản hồi</span>
            <button type="button" onClick={() => setReplyTo(null)} className="font-medium text-ink">Hủy</button>
          </div>
        )}
        <textarea
          className="min-h-28 w-full resize-y rounded-control border border-border bg-surface px-3 py-3 text-[15px] text-ink outline-none placeholder:text-ink-faint focus:border-brand focus:ring-2 focus:ring-brand-soft"
          placeholder="Viết phản hồi"
          value={newText}
          onChange={(event) => setNewText(event.target.value)}
          disabled={submitting}
        />
        <div className="mt-3 flex justify-end">
          <button type="submit" disabled={submitting || !newText.trim()} className="pill-button gap-2 disabled:cursor-not-allowed disabled:opacity-50">
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            Gửi phản hồi
          </button>
        </div>
      </form>

      <div className="space-y-3">
        {loading && [1, 2].map((item) => <div key={item} className="h-28 animate-pulse rounded-panel border border-border bg-surface-quiet" />)}
        {!loading && comments.length === 0 && (
          <div className="rounded-panel border border-dashed border-border px-4 py-10 text-center text-[14px] text-ink-muted">Chưa có phản hồi</div>
        )}
        {comments.map((comment) => {
          const depth = Math.max(0, (comment.path?.match(/,/g) || []).length - 1);
          const name = comment.user?.full_name || "Độc giả";
          return (
            <article key={comment._id} className={`relative rounded-panel border border-border bg-surface p-4 ${depth ? "ml-5 md:ml-10" : ""}`}>
              {depth > 0 && <CornerDownRight className="absolute -left-7 top-5 hidden h-4 w-4 text-ink-faint md:block" />}
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-full bg-brand-soft text-[13px] font-semibold text-brand">
                  {comment.user?.avatar_url ? <img src={comment.user.avatar_url} alt={name} className="h-full w-full object-cover" /> : name.slice(0, 1).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <span className="text-[14px] font-semibold text-ink">{name}</span>
                    <time className="text-[12px] text-ink-faint">{new Date(comment.created_at).toLocaleDateString("vi-VN")}</time>
                  </div>
                  <p className="mt-2 whitespace-pre-wrap text-[15px] leading-6 text-ink-muted">{comment.text || comment.content}</p>
                  <button onClick={() => setReplyTo(comment._id)} className="mt-3 inline-flex items-center gap-1.5 text-[13px] font-medium text-brand hover:text-brand-hover">
                    <Reply className="h-3.5 w-3.5" />
                    Trả lời
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
