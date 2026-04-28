"use client";
import { useEffect, useState } from "react";
import { Documentmark, FolderPlus, Grid, List as ListIcon, MoreVertical, DocumentOpen, Share2, Plus } from "lucide-react";
import { Button } from "@/app/components/ui/Button";
import Link from "next/link";

export default function CollectionsPage() {
  const [collections, setCollections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCollections = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/reader/collections`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('doclib_token')}` }
        });
        if (res.ok) {
          const data = await res.json();
          setCollections(data.collections || []);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchCollections();
  }, []);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 animate-in fade-in duration-500">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-black pb-8 mb-12">
        <div>
           <div className="flex items-center gap-3 mb-2">
              <Documentmark className="w-5 h-5 text-black" />
              <span className="text-[10px] font-bold tracking-widest text-zinc-400">Thư viện cá nhân</span>
           </div>
           <h1 className="text-4xl font-black text-black tracking-tighter">Bộ sưu tập của tôi</h1>
        </div>
        <Button className="text-[10px] font-bold tracking-widest bg-black h-12 px-8">
           <FolderPlus className="w-4 h-4 mr-2" /> Tạo bộ sưu tập
        </Button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {collections.map((col) => (
          <div key={col.id} className="group border border-black p-8 hover:bg-zinc-50 transition-all duration-300 space-y-6 relative">
             <div className="flex justify-between items-start">
                <div className="w-16 h-16 border-2 border-black bg-white flex items-center justify-center -mt-12 group-hover:bg-black group-hover:text-white transition-colors">
                   <Grid className="w-8 h-8" />
                </div>
                <div className="flex gap-2">
                   <button className="p-2 hover:bg-zinc-100 transition-colors"><Share2 className="w-4 h-4" /></button>
                   <button className="p-2 hover:bg-zinc-100 transition-colors"><MoreVertical className="w-4 h-4" /></button>
                </div>
             </div>
             
             <div className="space-y-2">
                <div className="flex items-center gap-2">
                   <h3 className="text-lg font-black tracking-tighter">{col.title}</h3>
                   {!col.is_public && <div className="w-2 h-2 rounded-none bg-zinc-200" title="Riêng tư" />}
                </div>
                <p className="text-[10px] font-bold text-zinc-400 tracking-widest flex items-center gap-2">
                   <DocumentOpen className="w-3.5 h-3.5" /> {col.document_count} tài liệu đã lưu
                </p>
             </div>

              <div className="pt-6 border-t border-zinc-100 space-y-4">
                 <div className="flex items-center justify-between">
                    <Link href={`/collections/${col.id}`} className="text-[10px] font-bold tracking-widest text-black hover:underline underline-offset-4 decoration-2">
                       Xem chi tiết
                    </Link>
                    <span className={`text-[9px] font-bold px-2 py-0.5 border ${col.is_public ? 'border-black text-black' : 'border-zinc-100 text-zinc-400'}`}>
                       {col.is_public ? 'Công khai' : 'Riêng tư'}
                    </span>
                 </div>
                 <div className="flex items-center justify-between pt-2">
                    <div className="flex -space-x-2">
                       {[1, 2].map(i => (
                          <div key={i} className="w-6 h-6  border border-black bg-white text-[8px] font-black flex items-center justify-center">U{i}</div>
                       ))}
                       <div className="w-6 h-6  border border-black bg-zinc-100 text-[8px] font-black flex items-center justify-center hover:bg-black hover:text-white cursor-pointer">+</div>
                    </div>
                    <span className="text-[8px] font-bold tracking-widest text-zinc-400">Cộng tác viên</span>
                 </div>
              </div>
          </div>
        ))}

        <button className="border border-dashed border-zinc-200 p-8 flex flex-col items-center justify-center space-y-4 hover:border-black hover:bg-zinc-50/50 transition-all min-h-[250px]">
           <div className="w-12 h-12 rounded-none border border-zinc-200 flex items-center justify-center">
              <Plus className="w-6 h-6 text-zinc-300" />
           </div>
           <p className="text-[10px] font-bold tracking-widest text-zinc-400">Thêm danh sách mới</p>
        </button>
      </div>
    </div>
  );
}


