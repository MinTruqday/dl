"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  ArrowLeft, 
  BookOpen, 
  MoreVertical, 
  Share2, 
  Plus, 
  Loader2, 
  Trash2, 
  Settings,
  FileText,
  Star,
  Eye,
  Sparkles,
  ChevronRight
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { API_URL, getToken } from "@/app/lib/api";
import Link from "next/link";

export default function CollectionDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [collection, setCollection] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);

  const fetchCollectionDetail = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/reader/lists/${id}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        const json = await res.json();
        const data = json.data || json;
        setCollection(data);
      } else {
        router.push("/collections");
      }
    } catch (err: any) {
      console.error("Lỗi tải chi tiết bộ sưu tập:", err);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [id, router]);

  useEffect(() => {
    fetchCollectionDetail();
  }, [fetchCollectionDetail]);

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
      </div>
    );
  }

  if (!collection) return null;

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      {/* Navigation & Actions */}
      <div 
        className="mb-12 flex items-center justify-between transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <button 
          onClick={() => router.push("/collections")}
          className="flex items-center gap-3 text-[10px] font-bold tracking-widest uppercase text-zinc-400 hover:text-black transition-all group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          Quay lại bộ sưu tập
        </button>

        <div className="flex gap-2">
          <button className="p-3 border border-zinc-100 hover:border-black transition-all">
            <Share2 className="w-4 h-4" />
          </button>
          <button className="p-3 border border-zinc-100 hover:border-black transition-all">
            <Settings className="w-4 h-4" />
          </button>
          <button className="p-3 border border-zinc-100 hover:border-red-500 hover:text-red-500 transition-all">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Header Section */}
      <div 
        className="mb-16 border-b border-zinc-100 pb-12 transition-all duration-700 delay-150"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div className="max-w-4xl">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-2 h-2 bg-black rounded-none" />
            <span className="text-[10px] font-bold tracking-[0.5em] uppercase text-zinc-400">Collection Details</span>
          </div>
          <h1 className="text-6xl font-bold tracking-tighter leading-none text-black mb-8">
            {collection.name}
          </h1>
          <p className="text-lg font-medium text-zinc-400 leading-relaxed italic">
            {collection.description || "Không có mô tả cho bộ sưu tập này."}
          </p>
        </div>
      </div>

      {/* Content Grid */}
      <div 
        className="w-full transition-all duration-700 delay-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <div className="flex items-center justify-between mb-10">
          <div className="flex items-center gap-4">
            <span className="text-[10px] font-bold tracking-widest uppercase bg-black text-white px-4 py-2">
              {collection.documents_detailed?.length || 0} TÀI LIỆU TRONG DANH SÁCH
            </span>
          </div>
          <Button className="h-12 px-8 bg-zinc-50 text-black border border-zinc-100 hover:bg-black hover:text-white hover:border-black text-[10px] font-bold tracking-widest uppercase transition-all active:scale-95">
            <Plus className="w-4 h-4 mr-2" /> Thêm tài liệu
          </Button>
        </div>

        {collection.documents_detailed?.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {collection.documents_detailed.map((doc: any, index: number) => (
              <div 
                key={doc._id}
                className="group flex items-center gap-8 p-6 border border-zinc-100 bg-white hover:border-black transition-all duration-500"
              >
                <div className="text-[10px] font-bold text-zinc-200 w-6 shrink-0">
                  {(index + 1).toString().padStart(2, '0')}
                </div>
                
                <div className="w-16 h-20 bg-zinc-50 border border-zinc-100 shrink-0 overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-700">
                  {doc.cover_url ? (
                    <img src={doc.cover_url} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" alt={doc.title} />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <FileText className="w-6 h-6 text-zinc-100" />
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <Link 
                    href={`/document/${doc.slug}`}
                    className="text-lg font-bold text-black hover:underline underline-offset-8 decoration-1 tracking-tight truncate block"
                  >
                    {doc.title}
                  </Link>
                  <div className="flex items-center gap-6 mt-2">
                    <div className="flex items-center gap-2">
                      <div className="w-1 h-1 bg-zinc-300" />
                      <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Tác giả: {doc.author_name || "Vô danh"}</span>
                    </div>
                    <div className="flex items-center gap-4">
                       <span className="flex items-center gap-1.5 text-[10px] font-bold text-zinc-300">
                         <Eye className="w-3.5 h-3.5" /> {doc.views_count || 0}
                       </span>
                       <span className="flex items-center gap-1.5 text-[10px] font-bold text-zinc-300">
                         <Star className="w-3.5 h-3.5" /> {doc.rating_avg?.toFixed(1) || 0}
                       </span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-all">
                   <button className="p-3 border border-zinc-100 hover:bg-zinc-50 transition-all">
                     <Share2 className="w-4 h-4" />
                   </button>
                   <button className="p-3 border border-zinc-100 hover:bg-zinc-50 transition-all">
                     <MoreVertical className="w-4 h-4" />
                   </button>
                </div>
                
                <Link 
                  href={`/document/${doc.slug}`}
                  className="w-12 h-12 flex items-center justify-center border border-zinc-100 group-hover:bg-black group-hover:text-white group-hover:border-black transition-all"
                >
                  <ChevronRight className="w-5 h-5" />
                </Link>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-32 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/30">
            <div className="w-20 h-20 border border-zinc-100 bg-white flex items-center justify-center mb-8">
              <FileText className="w-8 h-8 text-zinc-100" />
            </div>
            <h2 className="text-2xl font-bold tracking-tighter text-black mb-3">Bộ sưu tập này đang trống</h2>
            <p className="text-sm font-medium text-zinc-400 mb-8 max-w-xs text-center">
              Hãy thêm những tài liệu giá trị vào đây để xây dựng kho tàng tri thức của riêng bạn.
            </p>
            <Link href="/">
              <Button className="h-14 px-12 bg-black text-white text-[11px] font-bold tracking-widest uppercase hover:bg-zinc-800 transition-all shadow-xl">
                Khám phá tài liệu ngay
              </Button>
            </Link>
          </div>
        )}
      </div>

    </div>
  );
}
