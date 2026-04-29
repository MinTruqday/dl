"use client";

import React, { useEffect, useState, useCallback } from "react";
import AppShell from "@/app/components/AppShell";
import { useAuth } from "@/app/contexts/AuthContext";
import { getMySeriesAPI, createSeriesAPI, getMyDocumentsAPI } from "@/app/lib/api";
import { Layers, Plus, Loader2, Info, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { Notification } from "@/app/components/NotificationToast";

export default function StudioSeriesPage() {
  const { user, isLoading } = useAuth() as any;
  const router = useRouter();
  const [series, setSeries] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newSeries, setNewSeries] = useState({ title: "", description: "", document_ids: [] as string[] });
  const [creating, setCreating] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [seriesData, docsData] = await Promise.all([getMySeriesAPI(), getMyDocumentsAPI()]);
      setSeries(seriesData.data || seriesData || []);
      setDocuments(docsData.data || docsData || []);
    } catch (err: any) {
      console.error("Lỗi tải dữ liệu bộ sưu tập:", err);
      setNotification({ type: "error", text: "Không thể kết nối với máy chủ để tải dữ liệu" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
    if (!isLoading && user) {
      loadData();
      requestAnimationFrame(() => setVisible(true));
    }
  }, [isLoading, user, router, loadData]);

  const handleCreate = async () => {
    if (!newSeries.title.trim()) {
      setNotification({ type: "error", text: "Vui lòng điền tiêu đề bộ sưu tập." });
      return;
    }
    setCreating(true);
    try {
      await createSeriesAPI(newSeries);
      setNotification({ type: "success", text: "Đã tạo bộ sưu tập thành công." });
      setShowCreate(false);
      setNewSeries({ title: "", description: "", document_ids: [] });
      loadData();
    } catch (e: any) {
      setNotification({ type: "error", text: e.message || "Không thể tạo bộ sưu tập mới." });
    } finally {
      setCreating(false);
    }
  };

  const toggleDocSelection = (id: string) => {
    setNewSeries((prev) => ({
      ...prev,
      document_ids: prev.document_ids.includes(id)
        ? prev.document_ids.filter((docId) => docId !== id)
        : [...prev.document_ids, id],
    }));
  };

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex h-[80vh] items-center justify-center">
          <Loader2 className="w-10 h-10 animate-spin text-zinc-300" />
        </div>
      </AppShell>
    );
  }

  if (!user) return null;

  return (
    <AppShell>
      <div
        className="max-w-6xl mx-auto px-6 py-12 md:py-20 transition-all duration-300 font-sans"
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(12px)",
        }}
      >
        {notification && (
          <div className="fixed top-24 right-8 z-[100] w-80 animate-in slide-in-from-right-4 duration-300">
            <Notification type={notification.type} message={notification.text} />
          </div>
        )}

        <div className="mb-16 border-b border-zinc-100 pb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold tracking-tighter text-black">Bộ sưu tập</h1>
            <p className="text-[11px] font-bold text-zinc-400">Phân loại tài liệu theo từng nhóm nội dung chuyên sâu</p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className={`px-8 py-4 text-[11px] font-bold transition-all flex items-center gap-2 active:scale-95 ${
              showCreate ? "bg-zinc-50 text-zinc-400 border border-zinc-100" : "bg-black text-white hover:bg-zinc-800"
            }`}
          >
            {showCreate ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
            {showCreate ? "Đóng lại" : "Tạo mới"}
          </button>
        </div>

        {showCreate && (
          <div className="mb-16 border border-zinc-100 bg-zinc-50/20 p-10 md:p-12 animate-in fade-in slide-in-from-top-4 duration-300">
            <h2 className="text-xl font-bold text-black mb-10 tracking-tight">Thông tin bộ sưu tập mới</h2>
            <div className="grid md:grid-cols-2 gap-12">
              <div className="space-y-8">
                <div className="space-y-3">
                  <label className="text-[11px] font-bold text-zinc-400">Tiêu đề</label>
                  <input
                    value={newSeries.title}
                    onChange={(e) => setNewSeries({ ...newSeries, title: e.target.value })}
                    placeholder=""
                    className="w-full h-14 bg-white border border-zinc-100 px-5 text-sm font-bold focus:outline-none focus:border-black transition-all placeholder:text-zinc-200"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[11px] font-bold text-zinc-400">Mô tả</label>
                  <textarea
                    value={newSeries.description}
                    onChange={(e) => setNewSeries({ ...newSeries, description: e.target.value })}
                    placeholder=""
                    className="w-full min-h-[140px] p-5 text-sm font-medium border border-zinc-100 bg-white focus:outline-none focus:border-black transition-all placeholder:text-zinc-200"
                  />
                </div>
                <button
                  onClick={handleCreate}
                  disabled={creating}
                  className="w-full bg-black text-white py-5 text-[11px] font-bold hover:bg-zinc-800 flex items-center justify-center gap-3 active:scale-95 transition-all disabled:opacity-50"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  Xác nhận tạo bộ sưu tập
                </button>
              </div>
              <div className="space-y-6">
                <label className="text-[11px] font-bold text-zinc-400">
                  Lựa chọn tài liệu ({newSeries.document_ids.length})
                </label>
                <div className="max-h-[380px] overflow-y-auto border border-zinc-100 bg-white p-2 space-y-1 scrollbar-thin scrollbar-thumb-zinc-100">
                  {documents.map((doc) => (
                    <div
                      key={doc._id || doc.id}
                      onClick={() => toggleDocSelection(doc._id || doc.id)}
                      className={`flex items-center gap-4 p-4 cursor-pointer transition-all ${
                        newSeries.document_ids.includes(doc._id || doc.id) ? "bg-zinc-50" : "hover:bg-zinc-50/50"
                      }`}
                    >
                      <div
                        className={`w-4 h-4 border border-zinc-200 flex items-center justify-center shrink-0 ${
                          newSeries.document_ids.includes(doc._id || doc.id) ? "bg-black border-black" : "bg-white"
                        }`}
                      >
                        {newSeries.document_ids.includes(doc._id || doc.id) && <div className="w-1.5 h-1.5 bg-white" />}
                      </div>
                      <span className="text-sm font-bold text-black truncate">{doc.title}</span>
                    </div>
                  ))}
                  {documents.length === 0 && (
                    <div className="py-20 text-center">
                      <p className="text-[11px] font-bold text-zinc-300 italic">Danh sách tài liệu trống</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-zinc-50 border border-zinc-100 h-56 animate-pulse" />
            ))}
          </div>
        ) : series.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {series.map((s) => (
              <div
                key={s._id || s.id}
                className="group border border-zinc-100 bg-white p-8 hover:border-black transition-all duration-300 flex flex-col active:scale-[0.98]"
              >
                <div className="flex items-center gap-4 mb-8">
                  <div className="w-12 h-12 bg-zinc-50 border border-zinc-100 flex items-center justify-center group-hover:bg-black group-hover:border-black transition-all duration-300">
                    <Layers className="w-6 h-6 text-zinc-300 group-hover:text-white transition-all" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-lg font-bold text-black truncate tracking-tight">{s.title}</h3>
                    <p className="text-[10px] font-bold text-zinc-300 uppercase">
                      {s.document_ids?.length || 0} tài liệu
                    </p>
                  </div>
                </div>
                <p className="text-[13px] text-zinc-400 font-medium line-clamp-3 mb-10 leading-relaxed flex-1">
                  {s.description || "Chưa có thông tin mô tả cho bộ sưu tập này."}
                </p>
                <button
                  onClick={() => router.push(`/studio/series/${s._id || s.id}`)}
                  className="w-full bg-zinc-50 text-black border border-zinc-100 py-3 text-[10px] font-bold hover:bg-black hover:text-white hover:border-black transition-all"
                >
                  Xem chi tiết
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-40 border border-dashed border-zinc-200 bg-zinc-50/20">
            <Layers className="w-14 h-14 mx-auto mb-6 text-zinc-300" />
            <p className="text-[11px] font-bold text-zinc-300 uppercase">Bạn chưa có bộ sưu tập nào</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
