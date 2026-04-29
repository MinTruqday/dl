"use client";

import { useEffect, useState, useCallback } from "react";
import { getToken } from "@/app/lib/api";
import { MessageSquare, CornerDownRight, Reply, Send } from "lucide-react";

interface User {
  id: string;
  display_name: string;
  avatar_url?: string;
}

interface Comment {
  _id: string;
  text: string;
  path: string;
  user: User;
  created_at: string;
}

export default function NestedComments({ itemId }: { itemId: string }) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newText, setNewText] = useState("");
  const [replyTo, setReplyTo] = useState<string | null>(null);

  const fetchComments = useCallback(async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/items/${itemId}/comments`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        const data = await res.json();
        setComments(Array.isArray(data.data) ? data.data : []);
      }
    } catch (err: any) {
      console.error("Lỗi tải bình luận:", err);
    }
  }, [itemId]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newText.trim()) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/items/${itemId}/comments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({
          item_id: itemId,
          item_type: "document",
          text: newText,
          parent_id: replyTo,
        }),
      });
      if (res.ok) {
        setNewText("");
        setReplyTo(null);
        fetchComments();
      }
    } catch (err: any) {
      console.error("Lỗi gửi bình luận:", err);
    }
  };

  return (
    <div className="mt-12 border-t border-zinc-200 pt-12 animate-in fade-in duration-300 font-sans">
      <h3 className="text-xl font-bold mb-6 flex items-center gap-2 tracking-tight text-black">
        <MessageSquare className="w-5 h-5" />
        Bình luận cộng đồng
      </h3>

      <form onSubmit={handleSubmit} className="mb-10 bg-zinc-50 p-6 border border-zinc-200">
        <textarea
          className="w-full border border-zinc-200 p-4 bg-white focus:border-black outline-none transition-all text-sm font-medium resize-none min-h-[100px] placeholder:text-zinc-300"
          placeholder=""
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
        />
        <div className="flex justify-between items-center mt-4">
          {replyTo && (
            <button
              type="button"
              onClick={() => setReplyTo(null)}
              className="text-[12px] font-bold text-zinc-400 hover:text-black transition-colors"
            >
              Hủy phản hồi
            </button>
          )}
          <button
            type="submit"
            className="bg-black text-white px-6 py-2.5 ml-auto text-[12px] font-bold hover:bg-zinc-800 transition-all flex items-center gap-2 active:scale-[0.98]"
          >
            Gửi bình luận
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>

      <div className="space-y-6">
        {comments.map((c) => {
          const depth = (c.path.match(/,/g) || []).length - 1;
          return (
            <div
              key={c._id}
              className={`border border-zinc-200 p-5 bg-white transition-all hover:border-black relative group animate-in fade-in slide-in-from-bottom-2 duration-300 ${
                depth > 0 ? "ml-6 sm:ml-12 border-l-4 border-l-zinc-100" : ""
              }`}
            >
              {depth > 0 && (
                <CornerDownRight className="absolute -left-6 top-6 w-4 h-4 text-zinc-200 hidden sm:block" />
              )}
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 bg-zinc-100 flex items-center justify-center text-[12px] font-bold text-black border border-zinc-200">
                    {c.user?.display_name?.[0] || "N"}
                  </div>
                  <span className="font-bold text-[12px] text-black tracking-tight">
                    {c.user?.display_name || "Độc giả ẩn danh"}
                  </span>
                </div>
                <span className="text-[11px] text-zinc-400 font-bold">
                  {new Date(c.created_at).toLocaleDateString("vi-VN")}
                </span>
              </div>
              <p className="text-zinc-600 text-sm leading-relaxed font-medium">{c.text}</p>
              <button
                onClick={() => setReplyTo(c._id)}
                className="text-[11px] font-bold text-zinc-400 hover:text-black mt-4 flex items-center gap-1.5 transition-colors"
              >
                <Reply className="w-3 h-3" />
                Phản hồi
              </button>
            </div>
          );
        })}
        {comments.length === 0 && (
          <div className="text-center py-16 border border-dashed border-zinc-200 bg-zinc-50/30">
            <p className="text-[11px] font-bold text-zinc-400">Chưa có bình luận nào. Hãy là người đầu tiên!</p>
          </div>
        )}
      </div>
    </div>
  );
}
