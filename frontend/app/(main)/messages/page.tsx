"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/app/lib/api";
import { MessageSquare, Send, Loader2, User } from "lucide-react";

export default function MessagesPage() {
  const [discussions, setDiscussions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDiscussion, setSelectedDiscussion] = useState<any>(null);
  const [replyContent, setReplyContent] = useState("");
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState("");
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    fetchDiscussions();
  }, []);

  const fetchDiscussions = async () => {
    try {
      const res = await fetch(`${API_URL}/reader/history`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        const history = await res.json();
        const allDiscussions: any[] = [];
        for (const h of history.slice(0, 10)) {
          const discRes = await fetch(`${API_URL}/reader/discussions/${h.book_id}`, {
            headers: { Authorization: `Bearer ${getToken()}` },
          });
          if (discRes.ok) {
            const discs = await discRes.json();
            allDiscussions.push(...discs.map((d: any) => ({ ...d, book_title: h.book_title })));
          }
        }
        setDiscussions(allDiscussions);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const showMsg = (msg: string) => {
    setMessage(msg);
    setTimeout(() => setMessage(""), 3000);
  };

  const sendReply = async () => {
    if (!replyContent.trim() || !selectedDiscussion) return;
    setSending(true);
    try {
      const res = await fetch(`${API_URL}/reader/discussions/${selectedDiscussion.id}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ content: replyContent }),
      });
      if (res.ok) {
        showMsg("Đã gửi tin nhắn");
        setReplyContent("");
        fetchDiscussions();
      }
    } catch (e) {
      showMsg("Không thể gửi");
    }
    setSending(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center animate-in fade-in duration-300">
        <div className="w-10 h-10 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[900px] mx-auto px-6 py-12 bg-white min-h-screen animate-in fade-in duration-300">
      {message && (
        <div className="fixed top-6 right-6 z-50 px-5 py-3 bg-black text-white text-[10px] font-bold tracking-widest animate-in slide-in-from-right-4 duration-300">
          {message}
        </div>
      )}

      <header className="border-b border-black pb-8 mb-10">
        <div className="flex items-center gap-3 mb-2">
          <MessageSquare className="w-5 h-5 text-zinc-400" />
          <span className="text-[10px] font-bold tracking-widest text-zinc-400">Thảo luận</span>
        </div>
        <h1 className="text-4xl font-bold text-black tracking-tighter">Tin nhắn và thảo luận</h1>
      </header>

      {discussions.length === 0 ? (
        <div className="border border-dashed border-border py-20 flex flex-col items-center text-center">
          <MessageSquare className="w-12 h-12 text-zinc-200 mb-4" />
          <p className="text-xs font-bold text-zinc-400 tracking-widest">Chưa có cuộc thảo luận nào</p>
          <p className="text-sm text-zinc-400 mt-2">Tham gia thảo luận trong các tài liệu bạn đang đọc</p>
        </div>
      ) : (
        <div className="space-y-3">
          {discussions.map((d) => (
            <div
              key={d.id}
              onClick={() => setSelectedDiscussion(selectedDiscussion?.id === d.id ? null : d)}
              className={`border p-5 cursor-pointer transition-all ${selectedDiscussion?.id === d.id ? "border-black" : "border-border hover:border-zinc-300"}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <span className="text-sm font-bold text-black">{d.title}</span>
                  {d.book_title && (
                    <span className="text-[10px] text-zinc-400 font-bold tracking-widest ml-3">{d.book_title}</span>
                  )}
                </div>
                <span className="text-[10px] text-zinc-400 font-bold tracking-widest shrink-0">
                  {d.replies_count || 0} phản hồi
                </span>
              </div>
              <p className="text-sm text-zinc-500">{d.content}</p>
              <div className="flex items-center gap-2 mt-3 text-[10px] text-zinc-400">
                <User className="w-3 h-3" />
                <span>{d.user_name}</span>
                <span>{d.created_at ? new Date(d.created_at).toLocaleDateString("vi-VN") : ""}</span>
              </div>

              {selectedDiscussion?.id === d.id && (
                <div className="mt-4 pt-4 border-t border-zinc-100 animate-in fade-in duration-300">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={replyContent}
                      onChange={(e) => setReplyContent(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && sendReply()}
                      placeholder="Trả lời"
                      className="flex-1 px-4 py-2 border border-border text-sm focus:outline-none focus:border-black transition-all"
                    />
                    <button
                      onClick={sendReply}
                      disabled={sending || !replyContent.trim()}
                      className="px-4 py-2 bg-black text-white disabled:bg-zinc-300 transition-all"
                    >
                      {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}