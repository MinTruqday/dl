"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  MoreVertical,
  Share2,
  Plus,
  Loader2,
  Trash2,
  Settings,
  FileText,
  Star,
  Eye,
  ArrowRight,
  Layers,
} from "lucide-react";
import { getSeriesByIdAPI } from "@/services/read.service";
import { API_URL } from "@/services/auth.service";
import Link from "next/link";

export default function SeriesDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [series, setSeries] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);

  const fetchSeriesDetail = useCallback(async () => {
    if (!id) return;
    try {
      const res = await getSeriesByIdAPI(id as string);
      const data = res.data || res;
      setSeries(data);
    } catch (err: any) {
      console.error("Lỗi tải chi tiết chuỗi tri thức:", err);
      router.push("/collection");
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [id, router]);

  useEffect(() => {
    fetchSeriesDetail();
  }, [fetchSeriesDetail]);

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  if (!series) return null;

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      <div
        className="mb-12 flex items-center justify-between transition-all duration-300"
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(10px)",
        }}
      >
        <button
          onClick={() => router.push("/collection")}
          className="flex items-center gap-4 text-[10px] font-bold tracking-[0.2em] uppercase text-zinc-400 hover:text-black transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Quay lại mạng lưới
        </button>

        <div className="flex gap-2">
          <button className="p-3 border border-zinc-100 hover:border-black transition-colors rounded-sm">
            <Share2 className="w-4 h-4" />
          </button>
          <button className="p-3 border border-zinc-100 hover:border-black transition-colors rounded-sm">
            <Settings className="w-4 h-4" />
          </button>
          <button className="p-3 border border-zinc-100 hover:text-red-500 hover:border-red-500 transition-colors rounded-sm">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div
        className="mb-20 border-b border-zinc-100 pb-16 transition-all duration-300 delay-75"
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(10px)",
        }}
      >
        <div className="max-w-4xl space-y-10">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-black text-white flex items-center justify-center rounded-sm">
              <Layers className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <span className="text-[10px] font-bold tracking-[0.4em] uppercase text-zinc-300">
                Chuỗi tri thức chuyên sâu
              </span>
              <h1 className="text-6xl font-bold tracking-tighter leading-[0.9] text-black">
                {series.title}
              </h1>
            </div>
          </div>
          <p className="text-xl font-medium text-zinc-400 leading-relaxed max-w-3xl">
            {series.description || "Thực thể này chưa có nội dung tóm lược hệ thống"}
          </p>
        </div>
      </div>

      <div
        className="w-full transition-all duration-300 delay-150"
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(10px)",
        }}
      >
        <div className="flex items-center justify-between mb-12">
          <div className="flex items-center gap-4">
            <span className="text-[10px] font-bold tracking-[0.2em] uppercase bg-black text-white px-6 py-3 rounded-sm">
              {series.documents?.length || 0} Thực thể liên kết
            </span>
          </div>
          <button className="h-14 px-10 border border-black text-black text-[10px] font-bold tracking-[0.2em] uppercase active:scale-95 rounded-sm flex items-center gap-3 hover:bg-black hover:text-white transition-all">
            <Plus className="w-4 h-4" /> Kết nối tri thức
          </button>
        </div>

        {series.documents?.length > 0 ? (
          <div className="grid grid-cols-1 gap-6">
            {series.documents.map((doc: any, index: number) => (
              <div
                key={doc._id}
                className="group flex items-center gap-10 p-8 border border-zinc-100 bg-white hover:border-black transition-all rounded-sm"
              >
                <div className="text-[10px] font-bold text-zinc-200 w-8 shrink-0 tracking-widest">
                  {(index + 1).toString().padStart(2, "0")}
                </div>

                <div className="w-20 h-24 bg-zinc-50 border border-zinc-100 shrink-0 overflow-hidden rounded-sm transition-all group-hover:grayscale-0 grayscale">
                  {doc.cover_image ? (
                    <img
                      src={doc.cover_image}
                      className="w-full h-full object-cover"
                      alt={doc.title}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <FileText className="w-8 h-8 text-zinc-100" />
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0 space-y-3">
                  <Link
                    href={`/documents/${doc.slug}`}
                    className="text-2xl font-bold text-black hover:underline underline-offset-8 decoration-1 tracking-tighter truncate block"
                  >
                    {doc.title}
                  </Link>
                  <div className="flex items-center gap-8">
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                        Biên soạn: {doc.author?.display_name || "DocLib Contributor"}
                      </span>
                    </div>
                    <div className="flex items-center gap-6">
                      <span className="flex items-center gap-2 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                        <Eye className="w-4 h-4 text-zinc-100" /> {doc.view_count || 0}
                      </span>
                      <span className="flex items-center gap-2 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                        <Star className="w-4 h-4 text-zinc-100" /> {doc.average_rating?.toFixed(1) || "0.0"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Link
                    href={`/documents/${doc.slug}`}
                    className="w-14 h-14 flex items-center justify-center border border-zinc-100 hover:bg-black hover:text-white transition-all rounded-sm"
                  >
                    <ArrowRight className="w-5 h-5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-40 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-white rounded-sm">
            <div className="w-20 h-20 border border-zinc-100 bg-white flex items-center justify-center mb-10 rounded-sm">
              <FileText className="w-8 h-8 text-zinc-100 stroke-[1]" />
            </div>
            <h2 className="text-3xl font-bold tracking-tighter text-black mb-4 uppercase">
              Chuỗi tri thức trống
            </h2>
            <p className="text-[10px] font-bold text-zinc-300 mb-10 max-w-xs text-center uppercase tracking-[0.2em] leading-loose">
              Hãy kết nối những thực thể giá trị để hoàn thiện chuỗi tri thức này
            </p>
            <Link href="/documents">
              <button className="h-16 px-12 bg-black text-white text-[10px] font-bold tracking-[0.3em] uppercase rounded-sm active:scale-95 transition-transform shadow-none">
                Khám phá ngay
              </button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
