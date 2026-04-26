"use client";

import React, { useEffect, useState } from "react";
import AppShell from "@/app/components/AppShell";
import { 
  Plus, 
  Layers, 
  ChevronRight, 
  BookOpen, 
  Trash2, 
  Save,
  AlertCircle
} from "lucide-react";
import Link from "next/link";
import { getToken } from "@/app/lib/api";

export default function SeriesManagementPage() {
  const [seriesList, setSeriesList] = useState<any[]>([]);
  const [myBooks, setMyBooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newSeries, setNewSeries] = useState({ title: "", description: "", book_ids: [] as string[] });
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    fetchData();
  }, [API_URL]);

  const fetchData = async () => {
    const token = getToken();
    try {
      const [sRes, bRes] = await Promise.all([
        fetch(`${API_URL}/author/series`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/author/books`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      if (sRes.ok) setSeriesList(await sRes.json());
      if (bRes.ok) setMyBooks(await bRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newSeries.title) return;
    const token = getToken();
    try {
      const res = await fetch(`${API_URL}/author/series`, {
        method: "POST",
        headers: { 
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(newSeries)
      });
      if (res.ok) {
        setToastMsg("Đã tạo series thành công.");
        setShowCreate(false);
        setNewSeries({ title: "", description: "", book_ids: [] });
        fetchData();
      }
    } catch (e) {
      setToastMsg("Lỗi khi tạo series.");
    }
  };

  if (loading) return <AppShell><div className="flex items-center justify-center min-h-screen"><div className="w-8 h-8 border-2 border-black border-t-transparent animate-spin" /></div></AppShell>;

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto px-6 py-12 animate-in fade-in duration-500">
        <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-4xl font-bold tracking-tighter text-zinc-900 mb-2">Series tài liệu</h1>
            <p className="text-zinc-500 text-sm tracking-widest font-bold">Gộp các tài liệu liên kết thành chuỗi</p>
          </div>
          <button 
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-2 bg-zinc-900 text-white px-6 py-3 text-[10px] font-bold tracking-widest hover:bg-zinc-800 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Tạo Series mới
          </button>
        </header>

        {showCreate && (
          <div className="mb-12 p-8 border border-zinc-900 animate-in slide-in-from-top-4 duration-300">
            <h2 className="text-lg font-bold mb-6 tracking-tight">Cấu hình Series mới</h2>
            <div className="space-y-6">
              <div>
                <label className="block text-[10px] font-bold tracking-widest text-zinc-400 mb-2">Tên Series</label>
                <input 
                  type="text" 
                  value={newSeries.title}
                  onChange={(e) => setNewSeries({...newSeries, title: e.target.value})}
                  className="w-full p-4 border border-zinc-200 focus:border-zinc-900 outline-none text-sm" 
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold tracking-widest text-zinc-400 mb-2">Mô tả</label>
                <textarea 
                  rows={3} 
                  value={newSeries.description}
                  onChange={(e) => setNewSeries({...newSeries, description: e.target.value})}
                  className="w-full p-4 border border-zinc-200 focus:border-zinc-900 outline-none text-sm" 
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold tracking-widest text-zinc-400 mb-4">Chọn tài liệu vào Series</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[200px] overflow-y-auto p-2 border border-zinc-100">
                  {myBooks.map(book => (
                    <label key={book.id} className="flex items-center gap-3 p-3 border border-zinc-50 hover:bg-zinc-50 cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={newSeries.book_ids.includes(book.id)}
                        onChange={(e) => {
                          const ids = e.target.checked 
                            ? [...newSeries.book_ids, book.id] 
                            : newSeries.book_ids.filter(id => id !== book.id);
                          setNewSeries({...newSeries, book_ids: ids});
                        }}
                        className="w-4 h-4 accent-zinc-900" 
                      />
                      <span className="text-xs font-bold truncate">{book.title}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex gap-4 pt-4">
                <button 
                  onClick={handleCreate}
                  className="px-8 py-4 bg-zinc-900 text-white text-[10px] font-bold tracking-widest hover:bg-zinc-800 flex items-center gap-2"
                >
                  <Save className="w-4 h-4" /> Xác nhận tạo
                </button>
                <button 
                  onClick={() => setShowCreate(false)}
                  className="px-8 py-4 border border-zinc-200 text-[10px] font-bold tracking-widest hover:border-zinc-900"
                >
                  Hủy bỏ
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-4">
          {seriesList.length === 0 ? (
            <div className="p-4 border border-black bg-zinc-50 text-black text-sm text-center">
              <Layers className="w-12 h-12 text-zinc-300 mx-auto mb-4" />
              <p className="text-black text-xs font-bold tracking-widest">Bạn chưa có series nào</p>
            </div>
          ) : (
            seriesList.map((series) => (
              <div key={series.id} className="group p-8 border border-zinc-200 hover:border-zinc-900 transition-all duration-300">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-zinc-900 tracking-tight">{series.title}</h3>
                    <p className="text-zinc-500 text-xs mt-1">{series.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="p-2 text-zinc-400 hover:text-zinc-900"><Layers className="w-4 h-4" /></button>
                    <button className="p-2 text-zinc-400 hover:text-black"><Trash2 className="w-4 h-4" /></button>
                  </div>
                </div>
                <div className="flex items-center gap-6 mt-6">
                  <div className="flex items-center gap-2 text-[10px] font-bold text-zinc-400 tracking-widest">
                    <BookOpen className="w-4 h-4" />
                    {series.book_count} tài liệu
                  </div>
                  <Link 
                    href={`/author/series/${series.id}`}
                    className="ml-auto text-[10px] font-bold tracking-widest text-zinc-900 flex items-center gap-1 group-hover:gap-2 transition-all"
                  >
                    Quản lý chuỗi <ChevronRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {toastMsg && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-zinc-900 text-white px-6 py-3 text-[10px] font-bold tracking-widest shadow-xl animate-in slide-in-from-bottom-2 duration-300">
          {toastMsg}
        </div>
      )}
    </AppShell>
  );
}
