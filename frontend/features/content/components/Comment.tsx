"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getCommentsByItemAPI,
  createCommentAPI,
} from "@/features/content/services/collaboration.service";
import { useToast } from "@/shared/contexts/ToastContext";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import EmptyState from "@/shared/components/common/EmptyState";

interface CommentUser {
  id: string;
  full_name: string;
  avatar_url?: string;
}

interface Comment {
  _id: string;
  text: string;
  content?: string;
  path: string;
  user: CommentUser;
  created_at: string;
}

interface CommentProps {
  itemId: string;
  itemType?: "document";
}

export default function Comment({
  itemId,
  itemType = "document",
}: CommentProps) {
  const { user } = useAuth() as any;
  const [comments, setComments] = useState<Comment[]>([]);
  const [newText, setNewText] = useState("");
  const [replyTo, setReplyTo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const { showToast } = useToast();

  const fetchComments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getCommentsByItemAPI(itemId);
      setComments(Array.isArray(data.data) ? data.data : data || []);
    } catch (err: any) {
      showToast("Lỗi kết nối hệ thống phân phối thảo luận", "error");
    } finally {
      setLoading(false);
    }
  }, [itemId]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      showToast("Lỗi thiếu hụt phân quyền tham gia thảo luận", "error");
      return;
    }
    if (!newText.trim()) return;

    setSubmitting(true);
    try {
      await createCommentAPI({
        item_id: itemId,
        content: newText,
        parent_id: replyTo,
        item_type: itemType,
      });
      setNewText("");
      setReplyTo(null);
      showToast("Khởi tạo luồng thảo luận mới hoàn tất", "success");
      fetchComments();
    } catch (err: any) {
      showToast(err.message || "Lỗi khởi tạo luồng thảo luận", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mt-12">
      <div className="mb-6 flex items-center justify-between border-b border-[var(--border)] pb-4">
        <h3 className="text-[17px] font-semibold text-[var(--ink)]">
          Thảo luận
        </h3>
        <span className="text-[13px] text-[var(--ink-muted)]">
          {comments.length} phản hồi
        </span>
      </div>

      <form
        onSubmit={handleSubmit}
        className="surface mb-8 p-5"
      >
        <textarea
          className="field-control min-h-28 w-full resize-none"
          placeholder=""
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
          disabled={submitting}
        />
        <div className="mt-4 flex items-center justify-between">
          {replyTo ? (
            <button
              type="button"
              onClick={() => setReplyTo(null)}
              className="button-secondary"
            >
              Hủy phản hồi
            </button>
          ) : (
            <div />
          )}
          <button
            type="submit"
            disabled={submitting || !newText.trim()}
            className="button-primary disabled:opacity-50"
          >
            {submitting ? "Đang gửi" : "Gửi phản hồi"}
          </button>
        </div>
      </form>

      <div className="space-y-8">
        {loading && comments.length === 0 ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-28 rounded-[var(--radius-panel)] border border-[var(--border)] bg-[var(--surface)]"
              />
            ))}
          </div>
        ) : (
          comments.map((c) => {
            const depth = (c.path.match(/,/g) || []).length - 1;
            return (
              <div
                key={c._id}
                className={`surface group relative p-5 ${
                  depth > 0 ? "ml-6 border-l-2 border-l-[var(--border-strong)] md:ml-12" : ""
                }`}
              >
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex size-9 items-center justify-center overflow-hidden rounded-[var(--radius-control)] bg-[var(--surface-quiet)] text-[12px] font-semibold text-[var(--ink)]">
                      {c.user?.avatar_url ? (
                        <img
                          src={c.user.avatar_url}
                          className="h-full w-full object-cover"
                          alt=""
                        />
                      ) : (
                        (c.user?.full_name || "Đ").slice(0, 1).toUpperCase()
                      )}
                    </div>
                    <div>
                      <span className="text-[14px] font-semibold text-[var(--ink)]">
                        {c.user?.full_name || "Độc giả"}
                      </span>
                      <div className="mt-0.5 text-[12px] text-[var(--ink-muted)]">
                        {new Date(c.created_at).toLocaleDateString("vi-VN")}
                      </div>
                    </div>
                  </div>
                </div>
                <p className="max-w-5xl text-[15px] leading-7 text-[var(--ink)]">
                  {c.text || c.content}
                </p>
                <div className="flex justify-end mt-4">
                  <button
                    onClick={() => {
                      setReplyTo(c._id);
                      window.scrollTo({ top: 0, behavior: "smooth" });
                    }}
                    className="text-[13px] font-medium text-[var(--brand)]"
                  >
                    Phản hồi
                  </button>
                </div>
              </div>
            );
          })
        )}
        {!loading && comments.length === 0 && (
          <EmptyState compact text="Chưa có phản hồi" />
        )}
      </div>
    </div>
  );
}
