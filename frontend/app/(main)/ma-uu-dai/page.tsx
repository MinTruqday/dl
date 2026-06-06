"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getCouponsAPI,
  createCouponAPI,
  toggleCouponStatusAPI,
  deleteCouponAPI,
} from "@/services/coupon.service";
import {
  Ticket,
  Plus,
  Loader2,
  Trash2,
  LayoutGrid,
  List as ListIcon,
  User,
  Users,
  UserPlus,
  Star,
  Clock,
  Check,
  Ban
} from "lucide-react";
import { useAuth } from "@/contexts/Auth";
import { useToast } from "@/contexts/Toast";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";

export default function ManageCouponsPage() {
  const { user } = useAuth() as any;
  const isAdmin = user?.role === "admin";
  const { showToast } = useToast();
  const [coupons, setCoupons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<any | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const [newCoupon, setNewCoupon] = useState({
    code: "",
    discount_percent: 10,
    max_uses: 100,
    is_active: true,
    target_type: "all",
  });

  const fetchCoupons = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getCouponsAPI();
      const list = data.data || data || [];
      setCoupons(list.filter((c: any) => c.status !== 'pending' || isAdmin));
    } catch (err: any) {
      showToast("Lỗi tải mã ưu đãi", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast, isAdmin]);

  useEffect(() => {
    fetchCoupons();
  }, [fetchCoupons]);

  const handleCreate = async () => {
    if (!newCoupon.code.trim()) {
      showToast("Vui lòng nhập mã ưu đãi.", "error");
      return;
    }
    setCreating(true);
    try {
      await createCouponAPI(newCoupon);
      showToast("Đã tạo mã ưu đãi mới thành công.", "success");
      setShowCreate(false);
      setNewCoupon({
        code: "",
        discount_percent: 10,
        max_uses: 100,
        is_active: true,
        target_type: "all",
      });
      fetchCoupons();
    } catch (err: any) {
      showToast(err.message || "Tạo mã ưu đãi thất bại.", "error");
    } finally {
      setCreating(false);
    }
  };

  const toggleStatus = async (id: string) => {
    try {
      await toggleCouponStatusAPI(id);
      showToast("Đã cập nhật trạng thái mã ưu đãi.", "success");
      fetchCoupons();
    } catch (err: any) {
      showToast(err.message || "Lỗi cập nhật trạng thái.", "error");
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setIsDeleting(true);
    try {
      await deleteCouponAPI(deleteConfirm.id);
      showToast("Đã xóa mã ưu đãi thành công.", "success");
      fetchCoupons();
      setDeleteConfirm(null);
    } catch (err: any) {
      showToast(err.message || "Lỗi xóa mã ưu đãi.", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <section className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-300">
      <div className="mb-2 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-black">Danh sách ưu đãi</h2>
        <div className="flex items-center gap-3">
          <button title="Tạo mã ưu đãi" onClick={() => setShowCreate(true)} className="p-1.5 border border-transparent rounded-xl text-zinc-500 hover:text-black hover:bg-zinc-100 transition-all duration-150">
            <Plus className="w-4 h-4" />
          </button>
          <div className="flex border border-zinc-200 bg-zinc-50 rounded-xl overflow-hidden">
            <button onClick={() => setViewMode("grid")} className={`p-1.5 transition-all duration-150 ${viewMode === "grid" ? "bg-white text-black shadow-sm" : "bg-transparent text-zinc-500 hover:text-black"}`}>
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button onClick={() => setViewMode("list")} className={`p-1.5 transition-all duration-150 ${viewMode === "list" ? "bg-white text-black shadow-sm" : "bg-transparent text-zinc-500 hover:text-black"}`}>
              <ListIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className={`grid gap-6 ${viewMode === "grid" ? "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4" : "grid-cols-1"}`}>
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className={`bg-zinc-50 border border-zinc-200 rounded-2xl ${
                viewMode === "grid" ? "aspect-[2/3] w-full" : "h-36 w-full"
              }`}
            />
          ))}
        </div>
      ) : coupons.length > 0 ? (
        <div className={`grid gap-6 ${viewMode === "grid" ? "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4" : "grid-cols-1"} animate-in fade-in slide-in-from-bottom-8 duration-300`} style={{ animationDelay: '150ms', animationFillMode: 'both' }}>
          {coupons.map((c: any) => (
            <div
              key={c.id}
              className={`relative group flex ${viewMode === "grid"
                ? "flex-col"
                : "flex-row gap-6 p-3"
                } border border-zinc-200 bg-white rounded-2xl hover:border-black transition-all duration-150 overflow-hidden`}
            >
              <div
                className={`${viewMode === "grid"
                  ? "aspect-[2/3] w-full border-b border-zinc-200"
                  : "w-24 h-36 shrink-0 rounded-xl"
                  } bg-zinc-50 relative overflow-hidden flex flex-col items-center justify-center p-3 text-center`}
              >
                <span className="text-base font-mono font-bold text-black block truncate max-w-full">{c.code}</span>
                <p className="text-[10px] font-bold text-white bg-black px-2 py-0.5 mt-2 inline-block rounded">-{c.discount_percent}%</p>
                <div className="absolute bottom-0 left-0 w-full h-1 bg-zinc-200">
                  <div
                    className="h-full bg-black"
                    style={{ width: `${(c.used_count / (c.max_uses || 1)) * 100}%` }}
                  />
                </div>
              </div>

              <div
                className={`${viewMode === "grid" ? "p-3" : "flex-1 py-1"
                  } flex flex-col flex-1 gap-2`}
              >
                <h3
                  className={`${viewMode === "grid" ? "text-sm" : "text-base"
                    } font-semibold text-black line-clamp-2 leading-snug`}
                >
                  Mã: {c.code}
                </h3>
                
                <div className="text-xs text-zinc-500 flex flex-col gap-1">
                  <div className="flex items-center gap-1.5">
                    <User className="w-4 h-4" />
                    <span>Người tạo: <span className="text-black font-medium">{c.author_id}</span></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {c.target_type === "all" ? <Users className="w-4 h-4" /> : c.target_type === "new_user" ? <UserPlus className="w-4 h-4" /> : <Star className="w-4 h-4" />}
                    <span>Đối tượng: <span className="text-black font-medium">{c.target_type === "all" ? "Tất cả" : c.target_type === "new_user" ? "Mới" : "Premium"}</span></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Ticket className="w-4 h-4" />
                    <span>Đã dùng: <span className="text-black font-medium">{c.used_count} / {c.max_uses}</span></span>
                  </div>
                </div>

                <div
                  className={`mt-auto pt-3 flex items-center justify-between ${viewMode === "grid" ? "border-t border-zinc-100" : ""
                    }`}
                >
                  <span className="text-xs font-semibold text-black flex items-center gap-1">
                    {c.status === "pending" && <span className="text-amber-500 flex items-center gap-1"><Clock className="w-4 h-4" /> Chờ duyệt</span>}
                    {c.status === "approved" && <span className="text-green-600 flex items-center gap-1"><Check className="w-4 h-4" /> Đã duyệt</span>}
                    {c.status === "rejected" && <span className="text-red-500 flex items-center gap-1"><Ban className="w-4 h-4" /> Từ chối</span>}
                  </span>
                  
                  <button
                    onClick={() => toggleStatus(c.id)}
                    className={`text-[10px] font-semibold transition-all duration-150 px-3 py-1.5 rounded-lg uppercase tracking-wider ${
                      c.is_active
                        ? "bg-black text-white hover:bg-zinc-800"
                        : "bg-zinc-100 text-zinc-500 hover:bg-zinc-200"
                    }`}
                  >
                    {c.is_active ? "Active" : "Paused"}
                  </button>
                </div>
              </div>

              <button
                onClick={() => setDeleteConfirm(c)}
                className="absolute top-2 right-2 p-1.5 bg-white border border-zinc-200 text-zinc-400 rounded-xl hover:text-red-500 hover:border-red-200 shadow-sm transition-all duration-150 z-10"
                title="Xóa mã ưu đãi"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white rounded-2xl animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: '150ms', animationFillMode: 'both' }}>
          <p className="text-sm font-medium text-zinc-500">
            Chưa có dữ liệu
          </p>
        </div>
      )}

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} className="max-w-2xl">
        <ModalHeader><ModalTitle>Thiết lập ưu đãi mới</ModalTitle></ModalHeader>
        <ModalContent className="space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Mã ưu đãi</label>
              <input value={newCoupon.code} onChange={(e) => setNewCoupon({ ...newCoupon, code: e.target.value.toUpperCase() })} placeholder="Ví dụ: SUMMER20" className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-mono font-semibold focus:outline-none focus:border-black rounded-xl" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Giảm (%)</label>
              <input type="number" value={newCoupon.discount_percent} onChange={(e) => setNewCoupon({ ...newCoupon, discount_percent: parseInt(e.target.value) || 0 })} className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black rounded-xl" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Lượt dùng tối đa</label>
              <input type="number" value={newCoupon.max_uses} onChange={(e) => setNewCoupon({ ...newCoupon, max_uses: parseInt(e.target.value) || 0 })} className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black rounded-xl" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Đối tượng</label>
              <select value={newCoupon.target_type} onChange={(e) => setNewCoupon({ ...newCoupon, target_type: e.target.value })} className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black rounded-xl appearance-none cursor-pointer">
                <option value="all">Tất cả người dùng</option>
                <option value="new_user">Người dùng mới</option>
                <option value="subscriber">Người dùng Premium</option>
              </select>
            </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setShowCreate(false)} className="flex-1 h-10 border border-zinc-200 bg-white text-xs font-semibold uppercase tracking-wider rounded-xl hover:bg-zinc-50 transition-colors">Hủy bỏ</button>
          <button onClick={handleCreate} disabled={creating} className="flex-1 h-10 bg-black text-white text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-2 disabled:opacity-50 rounded-xl border border-black hover:bg-zinc-800 transition-colors">{creating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Phát hành"}</button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!deleteConfirm} onClose={() => !isDeleting && setDeleteConfirm(null)} className="max-w-sm rounded-none border border-zinc-200 bg-white p-0">
        <ModalHeader className="border-b border-zinc-200 p-6"><ModalTitle className="text-sm font-semibold text-black">Xác nhận xóa mã</ModalTitle></ModalHeader>
        <ModalContent className="p-6"><p className="text-xs font-medium text-zinc-500 leading-relaxed">Xóa mã "{deleteConfirm?.code}"? Hành động này không thể hoàn tác.</p></ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-200 p-4 bg-zinc-50">
          <button onClick={() => setDeleteConfirm(null)} disabled={isDeleting} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black rounded-xl hover:bg-zinc-50 transition-colors">Hủy bỏ</button>
          <button onClick={handleDelete} disabled={isDeleting} className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium flex items-center justify-center rounded-xl hover:bg-zinc-800 transition-colors">{isDeleting ? <Loader2 className="w-3 h-3 animate-spin" /> : "Xác nhận xóa"}</button>
        </ModalFooter>
      </Modal>
    </section>
  );
}
