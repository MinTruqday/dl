"use client";

import { useState, useEffect, useCallback } from "react";
import {
  getDiscussionsAPI,
  createDiscussionAPI,
  replyDiscussionAPI,
} from "@/services/social.service";
import { MessageSquare, User, Send, Plus, Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";

interface DiscussionSectionProps {
  documentId: string;
}

export default function Discussion({ documentId }: DiscussionSectionProps) {
  const { user } = useAuth() as any;
  const [discussions, setDiscussions] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState("");
  const { showToast } = useToast();

  const loadDiscussions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getDiscussionsAPI(documentId);
      setDiscussions(data || []);
    } catch (err: any) {
      console.error("Lỗi tải thảo luận:", err);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    loadDiscussions();
  }, [loadDiscussions]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      showToast("Vui lòng đăng nhập để bắt đầu thảo luận.", "error");
      return;
    }
    setSubmitting(true);
    try {
      await createDiscussionAPI(documentId, title, content);
      showToast("Đã đăng thảo luận thành công.", "success");
      setTitle("");
      setContent("");
      setShowForm(false);
      loadDiscussions();
    } catch (e) {
      showToast("Không thể đăng thảo luận lúc này.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleReply = async (discussionId: string) => {
    if (!user) {
      showToast("Vui lòng đăng nhập để phản hồi.", "error");
      return;
    }
    if (!replyContent.trim()) return;
    try {
      await replyDiscussionAPI(discussionId, replyContent);
      setReplyContent("");
      setReplyingTo(null);
      loadDiscussions();
    } catch (e) {
      showToast("Không thể gửi phản hồi.", "error");
    }
  };

  return (
    <div className="mt-20 space-y-12 pb-24 font-sans max-w-5xl mx-auto px-4">
      <div className="flex items-center justify-between border-b border-zinc-100 pb-6">
        <h2 className="text-xl font-bold text-black tracking-tight flex items-center gap-3">
          <MessageSquare className="w-5 h-5 text-zinc-400" />
          Thảo luận cộng đồng
        </h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className={`text-[11px] font-bold border px-6 py-3 flex items-center gap-2 active:scale-95 ${
            showForm
              ? "bg-white border-zinc-200 text-zinc-500"
              : "bg-black border-black text-white "
          }`}
        >
          {showForm ? "Hủy bỏ" : "Tạo thảo luận mới"}
          {!showForm && <Plus className="w-3.5 h-3.5" />}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="bg-white border border-zinc-200 p-10 space-y-8 animate-in slide-in-from-top-4 fade-in "
        >
          <div className="space-y-3">
            <label className="text-[11px] font-bold text-zinc-400">
              Tiêu đề thảo luận
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder=""
              className="w-full bg-white border border-zinc-100 p-4 text-sm font-bold focus:border-black focus:outline-none placeholder:text-zinc-200"
              required
            />
          </div>
          <div className="space-y-3">
            <label className="text-[11px] font-bold text-zinc-400">
              Nội dung chi tiết
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder=""
              className="w-full bg-white border border-zinc-100 p-4 text-sm font-medium focus:border-black focus:outline-none min-h-[160px] placeholder:text-zinc-200"
              required
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="px-10 py-4 bg-black text-white text-[11px] font-bold flex items-center gap-3 active:scale-95"
          >
            {submitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            Đăng thảo luận
          </button>
        </form>
      )}

      <div className="space-y-8">
        {loading ? (
          <div className="space-y-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-40 bg-white animate-pulse border border-zinc-100"
              />
            ))}
          </div>
        ) : discussions.length > 0 ? (
          discussions.map((d) => (
            <div
              key={d.id}
              className="border border-zinc-100 p-8 space-y-6 group bg-white"
            >
              <div className="flex justify-between items-start gap-4">
                <div className="space-y-2 flex-1 min-w-0">
                  <h3 className="text-lg font-bold tracking-tight text-black transition-colors">
                    {d.title}
                  </h3>
                  <div className="flex items-center gap-4">
                    <div className="text-[11px] font-bold text-zinc-400 flex items-center gap-2">
                      <User className="w-3.5 h-3.5" />
                      {d.user_name}
                    </div>
                    <div className="w-1 h-1 bg-zinc-200" />
                    <div className="text-[11px] font-bold text-zinc-300">
                      {new Date(d.created_at).toLocaleDateString("vi-VN")}
                    </div>
                  </div>
                </div>
                <div className="bg-white border border-zinc-100 px-3 py-1.5 text-[10px] font-bold text-zinc-400 ">
                  {d.replies_count} phản hồi
                </div>
              </div>

              <p className="text-sm text-zinc-500 leading-relaxed border-l-2 border-zinc-100 pl-6 py-1">
                {d.content}
              </p>

              <div className="pt-6 border-t border-zinc-50 flex items-center gap-6">
                <button
                  onClick={() =>
                    setReplyingTo(replyingTo === d.id ? null : d.id)
                  }
                  className="text-[11px] font-bold text-black underline-offset-4 decoration-1"
                >
                  {replyingTo === d.id ? "Hủy bỏ" : "Trả lời thảo luận"}
                </button>
              </div>

              {replyingTo === d.id && (
                <div className="mt-6 flex gap-3 animate-in slide-in-from-top-2 ">
                  <input
                    type="text"
                    value={replyContent}
                    onChange={(e) => setReplyContent(e.target.value)}
                    placeholder=""
                    className="flex-1 bg-white border border-zinc-100 px-5 py-3 text-sm font-medium focus:border-black focus:bg-white focus:outline-none "
                    autoFocus
                  />
                  <button
                    onClick={() => handleReply(d.id)}
                    className="bg-black text-white px-8 py-3 text-[11px] font-bold active:scale-95"
                  >
                    Gửi
                  </button>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="py-24 text-center border border-dashed border-zinc-200 bg-white/20">
            <MessageSquare className="w-10 h-10 text-zinc-100 mx-auto mb-4" />
            <p className="text-[11px] font-bold text-zinc-300">
              Chưa có chủ đề thảo luận nào cho tài liệu này.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
