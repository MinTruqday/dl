"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getAllBannersAPI,
  createBannerAPI,
  deleteBannerAPI,
} from "@/features/provision/services/promotional_banner.service";
import { Loader2, Plus, Trash2, Image as ImageIcon, Link as LinkIcon, Hash, RefreshCcw, LayoutTemplate, ShieldAlert } from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";

export default function BannerManagementPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();

  const [isLoading, setIsLoading] = useState(true);
  const [banners, setBanners] = useState<any[]>([]);
  const [newBanner, setNewBanner] = useState({
    title: "",
    image_url: "",
    link_url: "",
    priority: 0,
  });
  const [isAddingBanner, setIsAddingBanner] = useState(false);
  const [visible, setVisible] = useState(false);

  const fetchBanners = useCallback(async () => {
    setIsLoading(true);
    try {
      const bData = await getAllBannersAPI();
      setBanners(bData.data || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách biểu ngữ.", "error");
    } finally {
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [showToast]);

  useEffect(() => {
    if (!authLoading && user?.role === "admin") {
      fetchBanners();
    }
  }, [user, authLoading, fetchBanners]);

  const handleAddBanner = async () => {
    if (!newBanner.title || !newBanner.image_url) {
      showToast("Vui lòng nhập đủ tiêu đề và hình ảnh.", "error");
      return;
    }
    setIsAddingBanner(true);
    try {
      await createBannerAPI(newBanner);
      showToast("Thêm biểu ngữ thành công.", "success");
      setNewBanner({ title: "", image_url: "", link_url: "", priority: 0 });
      fetchBanners();
    } catch (err: any) {
      showToast(err.message || "Lỗi khi thêm biểu ngữ.", "error");
    } finally {
      setIsAddingBanner(false);
    }
  };

  const handleDeleteBanner = async (id: string) => {
    if (!confirm("Xác nhận xoá biểu ngữ này?")) return;
    try {
      await deleteBannerAPI(id);
      showToast("Xoá biểu ngữ thành công.", "success");
      fetchBanners();
    } catch (err: any) {
      showToast(err.message || "Lỗi khi xoá biểu ngữ.", "error");
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-zinc-50">
        <Loader2 className="w-8 h-8 animate-spin text-black" />
      </div>
    );
  }

  if (user?.role !== "admin") {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-6 font-sans bg-zinc-50 px-6 text-center">
        <div className="w-20 h-20 bg-white shadow-sm flex items-center justify-center border border-zinc-100 rounded-3xl">
          <ShieldAlert className="w-8 h-8 text-zinc-400" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold tracking-tight text-zinc-900">
            Truy cập bị hạn chế
          </h2>
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
            Bạn không có quyền quản trị hệ thống
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 min-h-[calc(100dvh-var(--navbar-height))] font-sans text-zinc-900 bg-zinc-50 selection:bg-black selection:text-white">
      <header className="mb-6 md:mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
            Quản lý Biểu ngữ
          </h1>
          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 flex items-center gap-2">
            Cấu hình chiến dịch quảng bá <LayoutTemplate className="w-3.5 h-3.5 text-zinc-400" />
          </p>
        </div>
        <button
          onClick={fetchBanners}
          className="h-11 px-5 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-zinc-900 flex items-center justify-center gap-2 rounded-2xl shadow-sm transition-all duration-200 hover:scale-[1.02]"
        >
          <RefreshCcw className="w-4 h-4" />
          Đồng bộ dữ liệu
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <aside className="lg:col-span-1">
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-6 space-y-6 sticky top-6">
            <div className="border-b border-zinc-100 pb-4 flex items-center gap-2">
              <Plus className="w-4 h-4 text-black" />
              <h3 className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                Thêm Biểu ngữ mới
              </h3>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 ml-1 block">
                  Tiêu đề
                </label>
                <div className="relative">
                  <LayoutTemplate className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    type="text"
                    value={newBanner.title}
                    onChange={(e) =>
                      setNewBanner({ ...newBanner, title: e.target.value })
                    }
                    className="w-full h-11 pl-10 pr-4 border border-zinc-200 text-sm font-bold text-zinc-900 focus:outline-none focus:border-black rounded-2xl bg-white shadow-sm transition-all duration-200"
                    placeholder="Khuyến mãi mùa hè"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 ml-1 block">
                  URL Hình ảnh
                </label>
                <div className="relative">
                  <ImageIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    type="text"
                    value={newBanner.image_url}
                    onChange={(e) =>
                      setNewBanner({
                        ...newBanner,
                        image_url: e.target.value,
                      })
                    }
                    className="w-full h-11 pl-10 pr-4 border border-zinc-200 text-sm font-bold text-zinc-900 focus:outline-none focus:border-black rounded-2xl bg-white shadow-sm transition-all duration-200"
                    placeholder="https://..."
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 ml-1 block">
                  URL Đích (Link)
                </label>
                <div className="relative">
                  <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    type="text"
                    value={newBanner.link_url}
                    onChange={(e) =>
                      setNewBanner({ ...newBanner, link_url: e.target.value })
                    }
                    className="w-full h-11 pl-10 pr-4 border border-zinc-200 text-sm font-bold text-zinc-900 focus:outline-none focus:border-black rounded-2xl bg-white shadow-sm transition-all duration-200"
                    placeholder="https://..."
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 ml-1 block">
                  Độ ưu tiên
                </label>
                <div className="relative">
                  <Hash className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    type="number"
                    value={newBanner.priority}
                    onChange={(e) =>
                      setNewBanner({
                        ...newBanner,
                        priority: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full h-11 pl-10 pr-4 border border-zinc-200 text-sm font-bold text-zinc-900 focus:outline-none focus:border-black rounded-2xl bg-white shadow-sm transition-all duration-200"
                  />
                </div>
              </div>

              <button
                onClick={handleAddBanner}
                disabled={isAddingBanner}
                className="w-full h-11 mt-4 bg-black text-white text-[10px] font-bold uppercase tracking-widest disabled:opacity-50 flex justify-center items-center gap-2 rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
              >
                {isAddingBanner ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4" />
                )}
                Thêm Biểu ngữ
              </button>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-2">
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm overflow-hidden">
            <div className="border-b border-zinc-100 p-6 flex justify-between items-center bg-white/50">
              <h2 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">
                Danh sách Biểu ngữ
              </h2>
              <span className="px-3 py-1 bg-zinc-100 text-zinc-900 text-[10px] font-bold uppercase tracking-widest rounded-xl">
                {banners.length} biểu ngữ
              </span>
            </div>
            
            <div className="divide-y divide-zinc-100 max-h-[600px] overflow-y-auto custom-scrollbar bg-zinc-50/30">
              {banners.length > 0 ? (
                banners.map((banner) => (
                  <div
                    key={banner._id}
                    className="p-5 flex flex-col sm:flex-row gap-5 items-start sm:items-center group transition-all duration-200 hover:bg-white"
                  >
                    <div className="w-full sm:w-48 h-24 shrink-0 bg-zinc-100 border border-zinc-200 rounded-2xl overflow-hidden relative shadow-sm group-hover:shadow-md transition-shadow">
                      {banner.image_url ? (
                        <img
                          src={banner.image_url}
                          alt={banner.title}
                          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiNmNGY0ZjUiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiNhMGEwYTAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
                          }}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <ImageIcon className="w-6 h-6 text-zinc-300" />
                        </div>
                      )}
                      <div className="absolute top-2 right-2 px-2 py-0.5 bg-black/70 backdrop-blur-sm text-white text-[9px] font-bold uppercase tracking-widest rounded-lg">
                        Ưu tiên: {banner.priority}
                      </div>
                    </div>
                    
                    <div className="flex-1 min-w-0 flex flex-col gap-1.5 w-full">
                      <h4 className="text-sm font-bold text-zinc-900 truncate">
                        {banner.title}
                      </h4>
                      <div className="flex items-center gap-1.5 text-zinc-500">
                        <LinkIcon className="w-3.5 h-3.5 shrink-0" />
                        <span className="text-xs truncate font-medium">
                          {banner.link_url || "Không có liên kết đích"}
                        </span>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => handleDeleteBanner(banner._id)}
                      className="w-full sm:w-10 h-10 flex items-center justify-center text-red-500 bg-red-50 border border-red-100 hover:bg-red-500 hover:text-white rounded-xl shrink-0 transition-all duration-200 sm:opacity-0 sm:group-hover:opacity-100 shadow-sm"
                      title="Xoá biểu ngữ"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span className="sm:hidden ml-2 text-xs font-bold uppercase tracking-widest">Xóa</span>
                    </button>
                  </div>
                ))
              ) : (
                <div className="p-12 flex flex-col items-center justify-center text-center">
                  <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
                    <LayoutTemplate className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
                  </div>
                  <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-1">
                    Chưa có biểu ngữ
                  </h3>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                    Bắt đầu thêm biểu ngữ mới để hiển thị trên trang chủ
                  </p>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
