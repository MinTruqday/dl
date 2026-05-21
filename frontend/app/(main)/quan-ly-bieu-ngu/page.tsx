"use client";

import { useEffect, useState, useCallback } from "react";
import { getAllBannersAPI, createBannerAPI, deleteBannerAPI } from "@/services/banner.service";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { useAuth } from "@/contexts/Auth";
import { useToast } from "@/contexts/Toast";

export default function BannerManagementPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();

  const [isLoading, setIsLoading] = useState(true);
  const [banners, setBanners] = useState<any[]>([]);
  const [newBanner, setNewBanner] = useState({ title: "", image_url: "", link_url: "", priority: 0 });
  const [isAddingBanner, setIsAddingBanner] = useState(false);

  const fetchBanners = useCallback(async () => {
    setIsLoading(true);
    try {
      const bData = await getAllBannersAPI();
      setBanners(bData.data || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách biểu ngữ.", "error");
    } finally {
      setIsLoading(false);
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
      <div className="flex h-screen items-center justify-center bg-white">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white font-sans text-black">
      <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12">
        <header className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl font-semibold text-black">Quản lý Biểu ngữ</h1>
            <p className="text-sm text-zinc-500 mt-1">Cấu hình các chiến dịch quảng bá và sự kiện</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={fetchBanners}
              className="text-sm font-medium text-zinc-500  "
            >
              Đồng bộ dữ liệu
            </button>
          </div>
        </header>

        <div className="space-y-12 animate-in fade-in ">
          <section>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-1 space-y-4 p-6 border border-zinc-200 bg-white">
                <h3 className="text-xs font-bold text-black uppercase tracking-widest border-b border-zinc-100 pb-2">Thêm Biểu ngữ mới</h3>
                <div className="space-y-3">
                  <div>
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block mb-1">Tiêu đề</label>
                    <input type="text" value={newBanner.title} onChange={e => setNewBanner({...newBanner, title: e.target.value})} className="w-full border border-zinc-200 px-3 py-2 text-xs font-medium focus:outline-none focus:border-black rounded-none" placeholder="Khuyến mãi mùa hè" />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block mb-1">URL Hình ảnh</label>
                    <input type="text" value={newBanner.image_url} onChange={e => setNewBanner({...newBanner, image_url: e.target.value})} className="w-full border border-zinc-200 px-3 py-2 text-xs font-medium focus:outline-none focus:border-black rounded-none" placeholder="https://example.com/image.png" />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block mb-1">URL Đích (Link)</label>
                    <input type="text" value={newBanner.link_url} onChange={e => setNewBanner({...newBanner, link_url: e.target.value})} className="w-full border border-zinc-200 px-3 py-2 text-xs font-medium focus:outline-none focus:border-black rounded-none" placeholder="https://example.com" />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block mb-1">Độ ưu tiên</label>
                    <input type="number" value={newBanner.priority} onChange={e => setNewBanner({...newBanner, priority: parseInt(e.target.value) || 0})} className="w-full border border-zinc-200 px-3 py-2 text-xs font-medium focus:outline-none focus:border-black rounded-none" />
                  </div>
                  <button onClick={handleAddBanner} disabled={isAddingBanner} className="w-full mt-2 h-10 bg-black text-white text-xs font-semibold   disabled:opacity-50 flex justify-center items-center gap-2 rounded-none">
                    {isAddingBanner ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Thêm Biểu ngữ
                  </button>
                </div>
              </div>

              <div className="lg:col-span-2">
                <div className="border border-zinc-200 bg-white">
                  <div className="divide-y divide-zinc-100 max-h-[600px] overflow-y-auto">
                    {banners.length > 0 ? banners.map((banner) => (
                      <div key={banner._id} className="p-4 flex gap-4 items-center group  ">
                        <div className="w-32 h-16 shrink-0 bg-zinc-100 border border-zinc-200">
                          {banner.image_url && <img src={banner.image_url} alt={banner.title} className="w-full h-full object-cover" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-semibold text-black truncate">{banner.title}</h4>
                          <p className="text-xs text-zinc-500 truncate mt-1">Link: {banner.link_url || "Không có"}</p>
                          <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mt-1 block">Ưu tiên: {banner.priority}</span>
                        </div>
                        <button onClick={() => handleDeleteBanner(banner._id)} className="p-2 text-red-500   opacity-0 group- rounded-none shrink-0" title="Xoá biểu ngữ">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    )) : (
                      <div className="p-8 text-center text-sm font-medium text-zinc-500">Chưa có biểu ngữ nào</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
