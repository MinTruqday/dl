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
import { getSeriesByIdAPI } from "@/services/reading.service";
import { API_URL } from "@/services/authentication.service";
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
      console.error("Error loading series details:", err);
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
        <Loader2 className="w-10 h-10 animate-spin text-zinc-300" />
      </div>
    );
  }

  if (!series) return null;

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      <div
        className="mb-12 flex items-center justify-between animate-in fade-in slide-in-from-bottom-8 duration-300"
      >
        <button
          onClick={() => router.push("/collection")}
          className="flex items-center gap-4 text-[10px] font-bold tracking-[0.2em] uppercase text-zinc-400"
        >
          <ArrowLeft className="w-4 h-4" />
          Quay lại bộ sưu tập
        </button>

        <div className="flex gap-2">
          <button className="p-3 border border-zinc-100 rounded-none">
            <Share2 className="w-4 h-4" />
          </button>
          <button className="p-3 border border-zinc-100 rounded-none">
            <Settings className="w-4 h-4" />
          </button>
          <button className="p-3 border border-zinc-100 text-zinc-400 rounded-none">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div
        className="mb-20 border-b border-zinc-100 pb-16 animate-in fade-in slide-in-from-bottom-8 duration-300"
        style={{ animationDelay: '150ms', animationFillMode: 'both' }}
      >
        <div className="max-w-4xl space-y-10">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-black text-white flex items-center justify-center rounded-none">
              <Layers className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <span className="text-[10px] font-bold tracking-[0.4em] uppercase text-zinc-300">
                Chuỗi nội dung chuyên sâu
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
        className="w-full animate-in fade-in slide-in-from-bottom-8 duration-300"
        style={{ animationDelay: '300ms', animationFillMode: 'both' }}
      >
        <div className="flex items-center justify-between mb-12">
          <div className="flex items-center gap-4">
            <span className="text-[10px] font-bold tracking-[0.2em] uppercase bg-black text-white px-6 py-3 rounded-none">
              {series.documents?.length || 0} Thực thể liên kết
            </span>
          </div>
          <button className="h-14 px-10 border border-black text-black text-[10px] font-bold tracking-[0.2em] uppercase rounded-none flex items-center gap-3">
            <Plus className="w-4 h-4" /> Kết nối nội dung
          </button>
        </div>

        {series.documents?.length > 0 ? (
          <div className="grid grid-cols-1 gap-6">
            {series.documents.map((doc: any, index: number) => (
              <div
                key={doc._id}
                className="group flex items-center gap-10 p-8 border border-zinc-100 bg-white rounded-none"
              >
                <div className="text-[10px] font-bold text-zinc-200 w-8 shrink-0 tracking-widest">
                  {(index + 1).toString().padStart(2, "0")}
                </div>

                <div className="w-20 h-24 bg-zinc-50 border border-zinc-100 shrink-0 overflow-hidden rounded-none grayscale">
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
                    href={`/tai-lieu/${doc.slug}`}
                    className="text-2xl font-bold text-black tracking-tighter truncate block"
                  >
                    {doc.title}
                  </Link>
                  <div className="flex items-center gap-8">
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                        Biên soạn: {doc.author?.full_name || "DocLib Contributor"}
                      </span>
                    </div>
                    <div className="flex items-center gap-6">
                      <span className="flex items-center gap-2 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                        <Eye className="w-4 h-4 text-zinc-300" /> {doc.view_count || 0}
                      </span>
                      <span className="flex items-center gap-2 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                        <Star className="w-4 h-4 text-zinc-300" /> {doc.average_rating?.toFixed(1) || "0.0"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Link
                    href={`/tai-lieu/${doc.slug}`}
                    className="w-14 h-14 flex items-center justify-center border border-zinc-100 rounded-none"
                  >
                    <ArrowRight className="w-5 h-5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-40 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-white rounded-none">
            <div className="w-20 h-20 border border-zinc-100 bg-white flex items-center justify-center mb-10 rounded-none">
              <FileText className="w-8 h-8 text-zinc-300 stroke-[1]" />
            </div>
            <h2 className="text-3xl font-bold tracking-tighter text-black mb-4 uppercase">
              Chuỗi nội dung trống
            </h2>
            <p className="text-[10px] font-bold text-zinc-300 mb-10 max-w-xs text-center uppercase tracking-[0.2em] leading-loose">
              Hãy kết nối các thực thể giá trị để hoàn thiện chuỗi nội dung này
            </p>
            <Link href="/tai-lieu">
              <button className="h-16 px-12 bg-black text-white text-[10px] font-bold tracking-[0.3em] uppercase rounded-none">
                Khám phá ngay
              </button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
