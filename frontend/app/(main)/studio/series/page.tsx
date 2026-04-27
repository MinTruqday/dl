"use client";

import { useEffect, useState } from "react";
import { getMySeriesAPI, getMyDocumentsAPI, createSeriesAPI } from "@/app/lib/api";
import { Layers, Plus, BookText, Info, CheckCircle2, ChevronRight, LayoutGrid } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AuthorSeriesPage() {
  const [series, setSeries] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [newSeries, setNewSeries] = useState({ title: "", description: "", document_ids: [] as string[] });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sRes, dRes] = await Promise.all([getMySeriesAPI(), getMyDocumentsAPI()]);
      setSeries(sRes || []);
      setDocuments(dRes || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const toggleDocument = (id: string) => {
    setNewSeries(prev => ({
      ...prev,
      document_ids: prev.document_ids.includes(id) 
        ? prev.document_ids.filter(did => did !== id) 
        : [...prev.document_ids, id]
    }));
  };

  const handleCreate = async () => {
    if (!newSeries.title) return;
    try {
      await createSeriesAPI(newSeries);
      setIsCreating(false);
      setNewSeries({ title: "", description: "", document_ids: [] });
      loadData();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 animate-in fade-in duration-500">
      <header className="flex items-center justify-between border-b border-black pb-8 mb-12">
        <div>
           <div className="flex items-center gap-3 mb-2">
              <Layers className="w-5 h-5 text-black" />
              <span className="text-[12px] font-bold tracking-widest text-zinc-400">Quản lý nội dung</span>
           </div>
           <h1 className="text-4xl font-bold text-black tracking-tighter">Bộ sưu tập & Series</h1>
        </div>
        <Button onClick={() => setIsCreating(true)} className="text-[12px] font-bold tracking-widest bg-black h-12 px-8">
           <Plus className="w-4 h-4 mr-2" /> Tạo Series mới
        </Button>
      </header>

      {isCreating && (
        <div className="mb-12 border-2 border-black p-8 bg-zinc-50 space-y-6 animate-in slide-in-from-top-4 duration-300">
           <div className="flex justify-between items-start">
              <h2 className="text-xl font-bold tracking-tighter">Thiết lập Series mới</h2>
              <button onClick={() => setIsCreating(false)} className="text-[12px] font-bold tracking-widest text-zinc-400 hover:text-black">Hủy bỏ</button>
           </div>
           <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                 <div className="space-y-2">
                    <label className="text-[12px] font-bold tracking-widest text-zinc-400">Tiêu đề Series</label>
                    <input 
                       value={newSeries.title}
                       onChange={e => setNewSeries({...newSeries, title: e.target.value})}
                       className="w-full bg-white border border-black p-4 text-sm outline-none focus:ring-1 focus:ring-black"
                       placeholder="VD: Bí mật của Vũ trụ - Phần 1"
                    />
                 </div>
                 <div className="space-y-2">
                    <label className="text-[12px] font-bold tracking-widest text-zinc-400">Mô tả ngắn</label>
                    <textarea 
                       value={newSeries.description}
                       onChange={e => setNewSeries({...newSeries, description: e.target.value})}
                       className="w-full bg-white border border-black p-4 text-sm outline-none h-32 focus:ring-1 focus:ring-black"
                       placeholder="Mô tả nội dung chính của series này"
                    />
                 </div>
              </div>
              <div className="space-y-4">
                 <label className="text-[12px] font-bold tracking-widest text-zinc-400">Chọn tài liệu đưa vào Series ({newSeries.document_ids.length})</label>
                 <div className="h-48 overflow-y-auto border border-zinc-200 bg-white divide-y divide-zinc-100">
                    {documents.map(doc => (
                       <div 
                          key={doc.id} 
                          onClick={() => toggleDocument(doc.id)}
                          className="p-4 flex items-center justify-between cursor-pointer hover:bg-zinc-50"
                       >
                          <span className="text-xs font-bold text-zinc-600 truncate mr-4">{doc.title}</span>
                          {newSeries.document_ids.includes(doc.id) ? (
                             <CheckCircle2 className="w-4 h-4 text-black" />
                          ) : (
                             <div className="w-4 h-4 border border-zinc-200" />
                          )}
                       </div>
                    ))}
                 </div>
              </div>
           </div>
           <div className="pt-4 border-t border-zinc-200">
              <Button onClick={handleCreate} className="w-full md:w-fit px-12 h-12 text-[12px] font-bold tracking-widest">
                 Xác nhận tạo Series
              </Button>
           </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {series.map((s) => (
          <div key={s.id} className="group border border-black p-8 hover:bg-zinc-50 transition-all duration-300 space-y-6">
             <div className="w-12 h-12 bg-black text-white flex items-center justify-center">
                <LayoutGrid className="w-6 h-6" />
             </div>
             <div className="space-y-2">
                <h3 className="text-lg font-bold tracking-tighter line-clamp-1">{s.title}</h3>
                <p className="text-xs text-zinc-500 line-clamp-2 italic">"{s.description || 'Không có mô tả'}"</p>
             </div>
             <div className="pt-6 border-t border-zinc-100 flex items-center justify-between">
                <span className="text-[12px] font-bold tracking-widest text-zinc-400 flex items-center gap-1.5">
                   <BookText className="w-3.5 h-3.5" />
                   {s.document_count} tài liệu
                </span>
                <ChevronRight className="w-4 h-4 text-zinc-300 group-hover:text-black transition-colors" />
             </div>
          </div>
        ))}

        {series.length === 0 && !isCreating && (
           <div className="md:col-span-2 lg:col-span-3 py-32 text-center border border-dashed border-zinc-200 bg-zinc-50/30">
              <Info className="w-8 h-8 text-zinc-200 mx-auto mb-4" />
              <p className="text-[12px] font-bold tracking-widest text-zinc-300">Bạn chưa có bộ sưu tập nào.</p>
           </div>
        )}
      </div>
    </div>
  );
}
