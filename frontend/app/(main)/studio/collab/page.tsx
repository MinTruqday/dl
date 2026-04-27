"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/app/lib/api";
import { Users, Plus, X, Loader2, UserPlus, BookOpen } from "lucide-react";

export default function CollabPage() {
  const [books, setBooks] = useState<any[]>([]);
  const [selectedBookId, setSelectedBookId] = useState("");
  const [targetUserId, setTargetUserId] = useState("");
  const [loading, setLoading] = useState(true);
  const [inviting, setInviting] = useState(false);
  const [message, setMessage] = useState("");
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    fetchBooks();
  }, []);

  const fetchBooks = async () => {
    try {
      const res = await fetch(`${API_URL}/author/books`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) setBooks(await res.json());
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

  const inviteCoauthor = async () => {
    if (!selectedBookId || !targetUserId.trim()) return;
    setInviting(true);
    try {
      const res = await fetch(`${API_URL}/coauthor/invite/${selectedBookId}?target_user_id=${targetUserId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        showMsg("Đã gửi lời mời cộng tác");
        setTargetUserId("");
      } else {
        const data = await res.json();
        showMsg(data.detail || "Gửi lời mời thất bại");
      }
    } catch (e) {
      showMsg("Lỗi kết nối");
    }
    setInviting(false);
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
        <div className="fixed top-6 right-6 z-50 px-5 py-3 bg-black text-white text-[12px] font-bold tracking-widest animate-in slide-in-from-right-4 duration-300">
          {message}
        </div>
      )}

      <header className="border-b border-black pb-8 mb-10">
        <div className="flex items-center gap-3 mb-2">
          <Users className="w-5 h-5 text-zinc-400" />
          <span className="text-[12px] font-bold tracking-widest text-zinc-400">Studio</span>
        </div>
        <h1 className="text-4xl font-bold text-black tracking-tighter">Đồng tác giả</h1>
      </header>

      <div className="border border-border p-6 mb-8">
        <h2 className="text-xs font-bold tracking-widest text-black flex items-center gap-2 mb-6">
          <UserPlus className="w-4 h-4" /> Mời cộng tác viên
        </h2>
        <div className="space-y-4">
          <div>
            <label className="text-[12px] font-bold tracking-widest text-zinc-400 block mb-2">Chọn tài liệu</label>
            <select
              value={selectedBookId}
              onChange={(e) => setSelectedBookId(e.target.value)}
              className="w-full px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all bg-white"
            >
              <option value="">Chọn tài liệu</option>
              {books.map((b) => (
                <option key={b.id} value={b.id}>{b.title}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[12px] font-bold tracking-widest text-zinc-400 block mb-2">ID người dùng cần mời</label>
            <input
              type="text"
              value={targetUserId}
              onChange={(e) => setTargetUserId(e.target.value)}
              placeholder="Nhập User ID"
              className="w-full px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all"
            />
          </div>
          <button
            onClick={inviteCoauthor}
            disabled={inviting || !selectedBookId || !targetUserId.trim()}
            className="w-full py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-all disabled:bg-zinc-300 flex items-center justify-center gap-2"
          >
            {inviting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
            Gửi lời mời
          </button>
        </div>
      </div>

      <div className="border border-border p-6">
        <h2 className="text-xs font-bold tracking-widest text-black flex items-center gap-2 mb-6">
          <BookOpen className="w-4 h-4" /> Tài liệu của bạn
        </h2>
        {books.length === 0 ? (
          <div className="py-12 text-center">
            <BookOpen className="w-12 h-12 text-zinc-200 mx-auto mb-4" />
            <p className="text-xs font-bold text-zinc-400 tracking-widest">Chưa có tài liệu nào</p>
          </div>
        ) : (
          <div className="space-y-2">
            {books.map((b) => (
              <div key={b.id} className="flex items-center justify-between px-4 py-3 border-b border-zinc-50 hover:bg-zinc-50 transition-colors">
                <div>
                  <span className="text-sm font-bold text-black">{b.title}</span>
                  <span className="text-[12px] text-zinc-400 font-bold tracking-widest ml-3">{b.status}</span>
                </div>
                <span className="text-[12px] text-zinc-400 font-bold tracking-widest">{b.chapters_count || 0} chương</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}