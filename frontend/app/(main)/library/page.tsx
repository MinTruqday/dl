"use client";

import { useEffect, useState, useCallback } from "react";
import { getLibraryAPI, getToken } from "@/app/lib/api";
import Link from "next/link";
import { ToastContainer } from "@/app/components/Toast";
import { 
  BookOpen, 
  Tag, 
  Settings, 
  Plus, 
  FolderSync, 
  Bookmark, 
  Trash2, 
  ListFilter, 
  LayoutGrid, 
  Clock, 
  ChevronRight 
} from "lucide-react";

export default function Library() {
  const [readingList, setReadingList] = useState<any[]>([]);
  const [labels, setLabels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [toasts, setToasts] = useState<any[]>([]);
  const [isLabelModalOpen, setIsLabelModalOpen] = useState(false);
  const [newLabelName, setNewLabelName] = useState("");

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  }, []);

  useEffect(() => {
    fetchLibrary();
  }, []);

  const fetchLibrary = async () => {
    try {
      const data = await getLibraryAPI();
      setReadingList(data || []);
      
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/reader/labels`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) setLabels(await res.json());
      
    } catch (error) {
       showToast("Không thể tải thư viện", "error");
    } finally {
       setLoading(false);
    }
  };

  const createLabel = async () => {
    if (!newLabelName.trim()) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/reader/labels`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ name: newLabelName }),
      });
      if (res.ok) {
        setIsLabelModalOpen(false);
        setNewLabelName("");
        showToast("Tạo nhãn thành công", "success");
        fetchLibrary();
      } else {
        showToast("Đã xảy ra lỗi khi tạo nhãn", "error");
      }
    } catch (error) {
        showToast("Mất kết nối", "error");
    }
  };

  return (
    <div className="w-full bg-white min-h-screen">
      <ToastContainer toasts={toasts} removeToast={(id) => setToasts(prev => prev.filter(t => t.id !== id))} />

      {isLabelModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center animate-in fade-in duration-300">
            <div className="bg-white p-8  w-full max-w-md border border-black animate-in zoom-in-95 duration-300">
                <div className="flex items-center gap-3 mb-6">
                    <Tag className="w-6 h-6 text-black" />
                    <h3 className="text-xl font-bold tracking-tighter">Thêm nhãn dán mới</h3>
                </div>
                <p className="text-sm text-zinc-500 mb-8 font-medium leading-relaxed">Phân loại kho tri thức của bạn bằng các nhãn chủ đề để tối ưu hóa việc quản lý và tìm kiếm.</p>
                <div className="space-y-6">
                    <div>
                        <label className="block text-[12px] font-bold tracking-widest text-zinc-400 mb-2">Tên nhãn dán</label>
                        <input 
                            type="text" 
                            placeholder="Nhập nhãn dán" 
                            className="w-full text-sm font-bold p-4 border border-border  focus:border-black outline-none transition-all bg-zinc-50 focus:bg-white tracking-tight"
                            value={newLabelName}
                            onChange={(e) => setNewLabelName(e.target.value)}
                            autoFocus
                        />
                    </div>
                </div>
                <div className="flex gap-3 justify-end mt-10">
                    <button onClick={() => setIsLabelModalOpen(false)} className="px-6 py-3 text-[13px] font-bold text-zinc-400 hover:text-black tracking-widest transition-colors">Hủy</button>
                    <button onClick={createLabel} className="px-8 py-3 text-[13px] font-bold bg-black text-white  hover:bg-zinc-800 transition-all tracking-widest">Lưu</button>
                </div>
            </div>
        </div>
      )}

      <main className="max-w-6xl w-full mx-auto p-6 md:p-12 flex flex-col gap-12 animate-in fade-in duration-300">
        <header className="flex justify-between items-end border-b border-black pb-8">
            <div>
                <div className="flex items-center gap-3 mb-2">
                    <LayoutGrid className="w-5 h-5 text-black" />
                    <span className="text-[13px] font-bold tracking-[0.2em] text-zinc-400">Không gian cá nhân</span>
                </div>
                <h1 className="text-4xl font-bold text-black tracking-tighter flex items-center gap-4">
                    Tủ sách tri thức
                </h1>
                <p className="text-zinc-500 mt-3 font-medium text-sm">Quản lý các tài liệu đã lưu và tiến độ đọc của bạn.</p>
            </div>
            <button className="text-zinc-400 hover:text-black transition-all p-3 border border-border hover:border-black ">
                <Settings className="w-5 h-5" />
            </button>
        </header>

        {loading ? (
            <div className="py-32 flex flex-col items-center justify-center border border-dashed border-border  bg-zinc-50/30">
                <FolderSync className="w-12 h-12 mb-6 animate-spin text-zinc-300" strokeWidth={1} />
                <span className="text-xs font-bold text-zinc-400 tracking-widest">Đang đồng bộ thư viện</span>
            </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-12">
            <aside className="md:col-span-3 flex flex-col gap-6">
                <div className="bg-zinc-50 border border-border p-6 ">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xs font-bold tracking-widest text-black flex items-center gap-2">
                            <ListFilter className="w-4 h-4" />
                            Nhãn dán chủ đề
                        </h3>
                        <button onClick={() => setIsLabelModalOpen(true)} className="p-1.5 bg-white border border-border text-black  hover:bg-black hover:text-white hover:border-black transition-all">
                            <Plus className="w-3.5 h-3.5" />
                        </button>
                    </div>
                    
                    <ul className="space-y-1">
                        {labels.length === 0 ? (
                            <li className="text-[12px] text-zinc-400 font-bold tracking-widest py-4 border-t border-zinc-100 italic">Không có nhãn nào</li>
                        ) : labels.map((lb: any) => (
                            <li key={lb._id} className="flex justify-between items-center group cursor-pointer py-3 border-b border-zinc-100 last:border-0 hover:border-black transition-colors">
                                <span className="text-xs font-bold text-zinc-600 group-hover:text-black tracking-tight flex items-center gap-2.5">
                                    <Tag className="w-3.5 h-3.5 text-zinc-300 group-hover:text-black transition-colors" /> {lb.name}
                                </span>
                                <button className="opacity-0 group-hover:opacity-100 p-1 text-zinc-400 hover:text-black transition-all"><Trash2 className="w-3 h-3" /></button>
                            </li>
                        ))}
                    </ul>
                </div>
            </aside>

            <div className="md:col-span-9 flex flex-col gap-12">
                <section>
                    <div className="flex items-center justify-between mb-8">
                        <h2 className="text-xl font-bold text-black tracking-tight flex items-center gap-3">
                            <Clock className="w-5 h-5" />
                            Đang nghiên cứu
                        </h2>
                        <span className="text-[12px] font-bold text-zinc-400 tracking-widest">{readingList.length} DANH SÁCH</span>
                    </div>
                    
                    {readingList.length === 0 ? (
                        <div className="bg-zinc-50 border-dashed border border-border  p-16 text-center">
                            <BookOpen className="w-10 h-10 text-zinc-200 mx-auto mb-4" strokeWidth={1} />
                            <p className="text-xs font-bold text-zinc-400 tracking-widest">Hiện chưa có danh sách tài liệu nào</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                            {readingList.map((list: any) => (
                                <div key={list._id} className="block group cursor-pointer">
                                    <div className="bg-white border border-border p-6  transition-all duration-300 group-hover:border-black relative overflow-hidden">
                                        <div className="flex justify-between items-start mb-6">
                                            <div className="p-3 bg-zinc-50 border border-border text-black  group-hover:bg-black group-hover:text-white transition-all">
                                                <Bookmark className="w-5 h-5" />
                                            </div>
                                            <div className="flex flex-col items-end">
                                                <span className="text-[13px] font-bold tracking-widest text-black bg-zinc-100 px-2 py-1  mb-2">DANH SÁCH</span>
                                                <span className="text-[12px] font-bold text-zinc-400 tracking-tight">{list.is_public ? "Công khai" : "Riêng tư"}</span>
                                            </div>
                                        </div>
                                        <h3 className="font-bold text-black text-lg line-clamp-2 leading-tight tracking-tight group-hover:underline underline-offset-4 decoration-2">{list.name}</h3>
                                        <p className="text-xs text-zinc-500 mt-2 line-clamp-2 font-medium">{list.description || "Không có mô tả"}</p>
                                        <div className="mt-8 pt-6 border-t border-zinc-50 flex justify-between items-center text-[12px] font-bold tracking-widest text-zinc-400">
                                            <span>{list.books?.length || 0} TÀI LIỆU</span>
                                            <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </section>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
