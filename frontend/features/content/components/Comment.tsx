"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getCommentsByItemAPI,
  createCommentAPI,
} from "@/features/content/services/collaboration.service";
import {
  MessageSquare,
  CornerDownRight,
  Reply,
  Send,
  Loader2,
  User,
} from "lucide-react";
import { useToast } from "@/shared/contexts/ToastContext";
import { useAuth } from "@/features/authentication/contexts/AuthContext";

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
    <div className="mt-16 animate-in fade-in font-sans">
      <div className="flex items-center justify-between border-b border-zinc-100 pb-8 mb-12">
        <div className="flex items-center gap-4">
          <MessageSquare className="w-5 h-5 text-black" />
          <h3 className="text-sm font-bold text-black uppercase tracking-widest">
            Thảo luận tài liệu
          </h3>
        </div>
        <div className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
          {comments.length} PHẢN HỒI
        </div>
      </div>

      <form
        onSubmit={handleSubmit}
        className="mb-16 bg-white p-10 border border-zinc-100 rounded-sm"
      >
        <textarea
          className="w-full border border-zinc-100 p-6 bg-white focus:border-black outline-none text-sm font-medium resize-none min-h-[140px] rounded-sm placeholder:text-zinc-200"
          placeholder=""
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
          disabled={submitting}
        />
        <div className="flex justify-between items-center mt-6">
          {replyTo ? (
            <button
              type="button"
              onClick={() => setReplyTo(null)}
              className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-4 py-2 border border-dashed border-zinc-100 rounded-sm"
            >
              Hủy phản hồi
            </button>
          ) : (
            <div />
          )}
          <button
            type="submit"
            disabled={submitting || !newText.trim()}
            className="bg-black text-white px-12 h-14 text-[11px] font-bold uppercase tracking-[0.3em] flex items-center gap-4 active:scale-95 rounded-sm disabled:opacity-50"
          >
            {submitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            Gửi thảo luận
          </button>
        </div>
      </form>

      <div className="space-y-8">
        {loading && comments.length === 0 ? (
          <div className="space-y-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-32 bg-white animate-pulse border border-zinc-100 rounded-sm"
              />
            ))}
          </div>
        ) : (
          comments.map((c) => {
            const depth = (c.path.match(/,/g) || []).length - 1;
            return (
              <div
                key={c._id}
                className={`border border-zinc-100 p-8 bg-white relative group animate-in fade-in slide-in-from-bottom-2 rounded-sm ${
                  depth > 0 ? "ml-8 md:ml-16 border-l-4 border-l-black/5" : ""
                }`}
              >
                {depth > 0 && (
                  <CornerDownRight className="absolute -left-8 top-8 w-5 h-5 text-zinc-100 hidden md:block" />
                )}
                <div className="flex justify-between items-center mb-6">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-white flex items-center justify-center text-[11px] font-bold text-black border border-zinc-100 rounded-sm overflow-hidden">
                      {c.user?.avatar_url ? (
                        <img
                          src={c.user.avatar_url}
                          className="w-full h-full object-cover grayscale"
                          alt=""
                        />
                      ) : (
                        <User className="w-4 h-4 text-zinc-200" />
                      )}
                    </div>
                    <div>
                      <span className="font-bold text-sm text-black uppercase tracking-tight">
                        {c.user?.full_name || "Độc giả"}
                      </span>
                      <div className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest mt-1">
                        {new Date(c.created_at).toLocaleDateString("vi-VN")}
                      </div>
                    </div>
                  </div>
                </div>
                <p className="text-zinc-600 text-base leading-loose font-medium max-w-5xl">
                  {c.text || c.content}
                </p>
                <div className="flex justify-end mt-4">
                  <button
                    onClick={() => {
                      setReplyTo(c._id);
                      window.scrollTo({ top: 0, behavior: "smooth" });
                    }}
                    className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2 opacity-0  "
                  >
                    <Reply className="w-3.5 h-3.5" />
                    Phản hồi
                  </button>
                </div>
              </div>
            );
          })
        )}
        {!loading && comments.length === 0 && (
          <div className="text-center py-24 border border-dashed border-zinc-100 bg-white/10 rounded-sm">
            <MessageSquare className="w-12 h-12 text-zinc-50 mx-auto mb-6 stroke-[1]" />
            <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-[0.3em]">
              Chưa có thảo luận nào cho thực thể này
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
