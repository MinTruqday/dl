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
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-zinc-200 pb-4">
        <h2 className="text-sm font-semibold text-black uppercase tracking-widest">Danh sách ưu đãi</h2>
        <div className="flex items-center gap-4">
          <div className="flex border border-zinc-200 bg-white">
            <button onClick={() => setViewMode("grid")} className={`p-2 ${viewMode === "grid" ? "bg-zinc-100 text-black" : "text-zinc-400"}`}><LayoutGrid className="w-4 h-4" /></button>
            <div className="w-[1px] bg-zinc-200" />
            <button onClick={() => setViewMode("list")} className={`p-2 ${viewMode === "list" ? "bg-zinc-100 text-black" : "text-zinc-400"}`}><ListIcon className="w-4 h-4" /></button>
          </div>
          <button onClick={() => setShowCreate(true)} className="h-10 px-6 bg-black text-white text-xs font-semibold uppercase tracking-wider flex items-center gap-2 border border-black  ">
            <Plus className="w-4 h-4" /> Tạo mã mới
          </button>
        </div>
      </div>

      {loading ? (
        <div className={`grid gap-6 ${viewMode === "grid" ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"}`}>
          {[1, 2, 3].map((i) => (<div key={i} className="bg-zinc-50 border border-zinc-200 h-48" />))}
        </div>
      ) : coupons.length > 0 ? (
        <div className={`grid gap-6 ${viewMode === "grid" ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"}`}>
          {coupons.map((c: any) => (
            <div key={c.id} className={`border border-zinc-200 bg-white flex ${viewMode === "grid" ? "flex-col" : "flex-row"}   group`}>
              <div className={`p-6 bg-zinc-50 flex justify-between items-start ${viewMode === "grid" ? "border-b border-zinc-200" : "border-r border-zinc-200 w-64"}`}>
                <div>
                  <span className="text-xl font-mono font-bold text-black block">{c.code}</span>
                  <p className="text-xs font-bold text-white bg-black px-2 py-0.5 mt-2 inline-block">-{c.discount_percent}%</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => toggleStatus(c.id)} className={`px-2 py-1 text-[9px] font-bold uppercase border ${c.is_active ? "bg-black text-white border-black" : "bg-white text-zinc-400 border-zinc-200 "}`}>{c.is_active ? "Active" : "Paused"}</button>
                  <button onClick={() => setDeleteConfirm(c)} className="p-1 border border-zinc-200 bg-white text-zinc-400   "><Trash2 className="w-3 h-3" /></button>
                </div>
              </div>

              <div className="flex-1 flex flex-col">
                <div className="px-6 py-4 border-b border-zinc-100 flex items-center justify-between bg-white text-[9px] font-bold uppercase tracking-tighter">
                  <div className="flex items-center gap-2">
                    {c.status === "pending" && <span className="text-amber-500 flex items-center gap-1"><Clock className="w-3 h-3" /> Pending</span>}
                    {c.status === "approved" && <span className="text-green-600 flex items-center gap-1"><Check className="w-3 h-3" /> Approved</span>}
                    {c.status === "rejected" && <span className="text-red-500 flex items-center gap-1"><Ban className="w-3 h-3" /> Rejected</span>}
                  </div>
                  <div className="flex items-center gap-2 text-zinc-400">
                    {c.target_type === "all" ? <Users className="w-3 h-3" /> : c.target_type === "new_user" ? <UserPlus className="w-3 h-3" /> : <Star className="w-3 h-3" />}
                    <span>{c.target_type === "all" ? "Public" : c.target_type === "new_user" ? "Newbie" : "Premium"}</span>
                  </div>
                </div>

                <div className="p-6 space-y-4">
                  <div className="flex items-center gap-2 text-[10px] font-medium text-zinc-500">
                    <User className="w-3 h-3" /> ID: <span className="text-black font-semibold">{c.author_id}</span>
                  </div>
                  <div>
                    <div className="flex justify-between items-end mb-2 text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
                      <span>Redemption</span>
                      <span className="text-black font-mono">{c.used_count} / {c.max_uses}</span>
                    </div>
                    <div className="w-full h-1 bg-zinc-100"><div className="bg-black h-full " style={{ width: `${(c.used_count / (c.max_uses || 1)) * 100}%` }} /></div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-zinc-50">
          <Ticket className="w-6 h-6 text-zinc-300 mb-3" />
          <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">No promotions found</span>
        </div>
      )}

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} className="max-w-2xl">
        <ModalHeader><ModalTitle>Thiết lập ưu đãi mới</ModalTitle></ModalHeader>
        <ModalContent className="space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Mã ưu đãi</label>
              <input value={newCoupon.code} onChange={(e) => setNewCoupon({ ...newCoupon, code: e.target.value.toUpperCase() })} placeholder="Ví dụ: SUMMER20" className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-mono font-semibold focus:outline-none focus:border-black rounded-none" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Giảm (%)</label>
              <input type="number" value={newCoupon.discount_percent} onChange={(e) => setNewCoupon({ ...newCoupon, discount_percent: parseInt(e.target.value) || 0 })} className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black rounded-none" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Lượt dùng tối đa</label>
              <input type="number" value={newCoupon.max_uses} onChange={(e) => setNewCoupon({ ...newCoupon, max_uses: parseInt(e.target.value) || 0 })} className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black rounded-none" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Đối tượng</label>
              <select value={newCoupon.target_type} onChange={(e) => setNewCoupon({ ...newCoupon, target_type: e.target.value })} className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black rounded-none appearance-none cursor-pointer">
                <option value="all">Tất cả người dùng</option>
                <option value="new_user">Người dùng mới</option>
                <option value="subscriber">Người dùng Premium</option>
              </select>
            </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setShowCreate(false)} className="flex-1 h-10 border border-zinc-200 bg-white text-xs font-semibold uppercase tracking-wider   rounded-none">Hủy bỏ</button>
          <button onClick={handleCreate} disabled={creating} className="flex-1 h-10 bg-black text-white text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-2 disabled:opacity-50   rounded-none border border-black">{creating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Phát hành"}</button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!deleteConfirm} onClose={() => !isDeleting && setDeleteConfirm(null)} className="max-w-sm rounded-none border border-zinc-200 bg-white p-0">
        <ModalHeader className="border-b border-zinc-200 p-6"><ModalTitle className="text-sm font-semibold text-black">Xác nhận xóa mã</ModalTitle></ModalHeader>
        <ModalContent className="p-6"><p className="text-xs font-medium text-zinc-500 leading-relaxed">Xóa mã "{deleteConfirm?.code}"? Hành động này không thể hoàn tác.</p></ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-200 p-4 bg-zinc-50">
          <button onClick={() => setDeleteConfirm(null)} disabled={isDeleting} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black rounded-none">Hủy bỏ</button>
          <button onClick={handleDelete} disabled={isDeleting} className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium flex items-center justify-center rounded-none">{isDeleting ? <Loader2 className="w-3 h-3 animate-spin" /> : "Xác nhận xóa"}</button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
