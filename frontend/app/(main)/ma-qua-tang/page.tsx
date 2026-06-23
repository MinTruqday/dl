"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getCouponsAPI,
  createCouponAPI,
  deleteCouponAPI,
  toggleCouponStatusAPI,
} from "@/features/finance/services/discount_coupon.service";
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
  Ban,
  Tag,
  AlertOctagon,
} from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
  ModalDescription,
} from "@/shared/components/ui/Modal";

export default function ManageCouponsPage() {
  const { user } = useAuth() as any;
  const isAdmin = user?.role === "admin";
  const { showToast } = useToast();
  const [coupons, setCoupons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);
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
      setCoupons(list.filter((c: any) => c.status !== "pending" || isAdmin));
    } catch (err: any) {
      showToast("Lỗi tải mã ưu đãi", "error");
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
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



  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setIsDeleting(true);
    try {
      await deleteCouponAPI(deleteConfirm.id || deleteConfirm._id);
      showToast("Đã xóa mã ưu đãi thành công.", "success");
      fetchCoupons();
      setDeleteConfirm(null);
    } catch (err: any) {
      showToast(err.message || "Lỗi xóa mã ưu đãi.", "error");
    } finally {
      setIsDeleting(false);
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

  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-6 shrink-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1 flex items-center gap-2">
              Danh sách ưu đãi
            </h1>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
              Quản lý các mã giảm giá cho độc giả
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex border border-zinc-100 bg-zinc-50/50 rounded-2xl overflow-hidden p-1 shadow-sm">
              <button
                onClick={() => setViewMode("grid")}
                className={`w-9 h-9 flex items-center justify-center rounded-xl transition-all duration-300 ${viewMode === "grid" ? "bg-white text-black shadow-sm" : "bg-transparent text-zinc-400 hover:text-zinc-600"}`}
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode("list")}
                className={`w-9 h-9 flex items-center justify-center rounded-xl transition-all duration-300 ${viewMode === "list" ? "bg-white text-black shadow-sm" : "bg-transparent text-zinc-400 hover:text-zinc-600"}`}
              >
                <ListIcon className="w-4 h-4" />
              </button>
            </div>
            <button
              title="Tạo mã ưu đãi"
              onClick={() => setShowCreate(true)}
              className="h-11 px-4 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl flex items-center gap-2 transition-all hover:scale-[1.02] hover:-translate-y-0.5 shadow-md group"
            >
              <Plus className="w-4 h-4" />
              <span>Tạo mới</span>
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0, transitionDelay: "100ms" }}>
        {loading ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-zinc-50/50 border border-zinc-100 rounded-3xl">
            <Loader2 className="w-8 h-8 animate-spin text-zinc-400 mb-4" />
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Đang tải danh sách...</p>
          </div>
        ) : coupons.length > 0 ? (
          <div
            className={`grid gap-6 pb-6 ${viewMode === "grid" ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"} `}
          >
            {coupons.map((c: any) => (
              <div
                key={c.id}
                className={`relative group flex ${
                  viewMode === "grid" ? "flex-col" : "flex-row gap-6 p-4 items-center"
                } bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-0.5`}
              >
                <div
                  className={`${
                    viewMode === "grid"
                      ? "aspect-[2.5/1] w-full border-b border-zinc-100 rounded-t-3xl"
                      : "w-32 h-24 shrink-0 rounded-2xl border border-zinc-100"
                  } bg-gradient-to-br from-zinc-50 to-white relative overflow-hidden flex flex-col items-center justify-center p-4 text-center`}
                >
                  <div className="absolute top-0 right-0 w-16 h-16 bg-zinc-100 rounded-full blur-2xl opacity-50 -mr-8 -mt-8"></div>
                  <span className="text-lg font-black tracking-widest text-black block truncate max-w-full relative z-10 uppercase">
                    {c.code}
                  </span>
                  <div className="text-[10px] font-bold text-white bg-black px-2.5 py-1 mt-2 inline-block rounded-lg shadow-sm relative z-10 uppercase tracking-widest">
                    Giảm {c.discount_percent}%
                  </div>
                  
                  {viewMode === "grid" && (
                    <div className="absolute bottom-0 left-0 w-full h-1 bg-zinc-100">
                      <div
                        className="h-full bg-black transition-all duration-500"
                        style={{
                          width: `${Math.min(100, (c.used_count / (c.max_uses || 1)) * 100)}%`,
                        }}
                      />
                    </div>
                  )}
                </div>

                <div
                  className={`${
                    viewMode === "grid" ? "p-5" : "flex-1 py-2"
                  } flex flex-col flex-1 gap-4`}
                >
                  <div className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-zinc-400" />
                      <span>
                        Tác giả: <span className="text-black">{c.author_id}</span>
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {c.target_type === "all" ? (
                        <Users className="w-4 h-4 text-zinc-400" />
                      ) : c.target_type === "new_user" ? (
                        <UserPlus className="w-4 h-4 text-zinc-400" />
                      ) : (
                        <Star className="w-4 h-4 text-amber-500" />
                      )}
                      <span>
                        Đối tượng:{" "}
                        <span className="text-black">
                          {c.target_type === "all"
                            ? "Tất cả"
                            : c.target_type === "new_user"
                              ? "Người mới"
                              : "Premium"}
                        </span>
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Ticket className="w-4 h-4 text-zinc-400" />
                      <span>
                        Đã dùng:{" "}
                        <span className="text-black">
                          {c.used_count} / {c.max_uses}
                        </span>
                      </span>
                    </div>
                    {viewMode === "list" && (
                      <div className="flex-1 bg-zinc-100 h-1.5 rounded-full overflow-hidden mt-1">
                        <div
                          className="h-full bg-black transition-all duration-500"
                          style={{
                            width: `${Math.min(100, (c.used_count / (c.max_uses || 1)) * 100)}%`,
                          }}
                        />
                      </div>
                    )}
                  </div>

                  <div
                    className={`mt-auto pt-4 flex items-center justify-between ${
                      viewMode === "grid" ? "border-t border-zinc-100" : ""
                    }`}
                  >
                    <div className="flex items-center gap-1.5">
                      {c.status === "pending" && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-amber-50 text-amber-600 border border-amber-100 text-[9px] font-bold uppercase tracking-widest rounded-lg">
                          <Clock className="w-3 h-3" /> Chờ duyệt
                        </span>
                      )}
                      {c.status === "approved" && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-50 text-green-600 border border-green-100 text-[9px] font-bold uppercase tracking-widest rounded-lg">
                          <Check className="w-3 h-3" /> Đã duyệt
                        </span>
                      )}
                      {c.status === "rejected" && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-50 text-red-600 border border-red-100 text-[9px] font-bold uppercase tracking-widest rounded-lg">
                          <Ban className="w-3 h-3" /> Từ chối
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => toggleStatus(c.id || c._id)}
                      className={`h-8 px-3 text-[9px] font-bold uppercase tracking-widest rounded-xl transition-all shadow-sm flex items-center justify-center ${
                        c.is_active
                          ? "bg-black text-white hover:bg-zinc-800"
                          : "bg-zinc-100 text-zinc-500 hover:bg-zinc-200 border border-zinc-200"
                      }`}
                    >
                      {c.is_active ? "Hoạt động" : "Tạm ngưng"}
                    </button>
                  </div>
                </div>

                <button
                  onClick={() => setDeleteConfirm(c)}
                  className="absolute top-3 right-3 w-8 h-8 flex items-center justify-center bg-white/80 backdrop-blur border border-zinc-200 text-zinc-400 rounded-xl hover:text-red-500 hover:border-red-200 hover:bg-red-50 shadow-sm transition-all duration-300 z-10 opacity-0 group-hover:opacity-100"
                  title="Xóa mã ưu đãi"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-zinc-50/50 border border-zinc-100 rounded-3xl p-12 text-center">
            <div className="w-16 h-16 bg-white border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
              <Ticket className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
            </div>
            <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-1">Chưa có mã ưu đãi</h3>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 max-w-sm">
              Bạn chưa tạo mã ưu đãi nào. Hãy tạo mới để thu hút thêm độc giả.
            </p>
          </div>
        )}
      </div>

      <Modal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        className="max-w-xl rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md p-0 shadow-2xl overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6 bg-zinc-50/50">
          <ModalTitle className="text-sm font-bold tracking-tight text-black flex items-center gap-2">
            <Ticket className="w-5 h-5" /> Thiết lập ưu đãi mới
          </ModalTitle>
          <ModalDescription className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mt-1 ml-7">
            Tạo mã giảm giá cho độc giả
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-700 uppercase tracking-widest">
                  Mã ưu đãi
                </label>
                <div className="relative">
                  <Tag className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    value={newCoupon.code}
                    onChange={(e) =>
                      setNewCoupon({
                        ...newCoupon,
                        code: e.target.value.toUpperCase(),
                      })
                    }
                    placeholder="VD: SUMMER20"
                    className="w-full h-11 pl-10 pr-4 bg-zinc-50 border border-zinc-200 text-xs font-bold uppercase tracking-wider focus:outline-none focus:border-black focus:bg-white transition-colors rounded-2xl shadow-sm"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-700 uppercase tracking-widest">
                  Giảm giá (%)
                </label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 text-sm font-bold">%</div>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={newCoupon.discount_percent}
                    onChange={(e) =>
                      setNewCoupon({
                        ...newCoupon,
                        discount_percent: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full h-11 pl-10 pr-4 bg-zinc-50 border border-zinc-200 text-xs font-bold focus:outline-none focus:border-black focus:bg-white transition-colors rounded-2xl shadow-sm"
                  />
                </div>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-700 uppercase tracking-widest">
                  Lượt dùng tối đa
                </label>
                <div className="relative">
                  <Users className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    type="number"
                    min="1"
                    value={newCoupon.max_uses}
                    onChange={(e) =>
                      setNewCoupon({
                        ...newCoupon,
                        max_uses: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full h-11 pl-10 pr-4 bg-zinc-50 border border-zinc-200 text-xs font-bold focus:outline-none focus:border-black focus:bg-white transition-colors rounded-2xl shadow-sm"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-700 uppercase tracking-widest">
                  Đối tượng áp dụng
                </label>
                <div className="relative">
                  <select
                    value={newCoupon.target_type}
                    onChange={(e) =>
                      setNewCoupon({ ...newCoupon, target_type: e.target.value })
                    }
                    className="w-full h-11 px-4 bg-zinc-50 border border-zinc-200 text-xs font-bold focus:outline-none focus:border-black focus:bg-white transition-colors rounded-2xl shadow-sm appearance-none cursor-pointer"
                  >
                    <option value="all">Tất cả người dùng</option>
                    <option value="new_user">Người dùng mới</option>
                    <option value="subscriber">Người dùng Premium</option>
                  </select>
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-4 h-4 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-blue-50/50 border border-blue-100 rounded-2xl p-4 flex gap-3">
              <Clock className="w-5 h-5 text-blue-500 shrink-0" />
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-blue-800 mb-1">Lưu ý kiểm duyệt</p>
                <p className="text-xs text-blue-600 leading-relaxed font-medium">Mã ưu đãi sau khi tạo sẽ được đưa vào hàng đợi chờ hệ thống phê duyệt trước khi có thể sử dụng.</p>
              </div>
            </div>
          </div>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => setShowCreate(false)}
            className="flex-1 h-11 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-black rounded-2xl hover:bg-zinc-50 transition-all hover:scale-[1.02] shadow-sm"
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleCreate}
            disabled={creating}
            className="flex-1 h-11 bg-black text-white text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 disabled:opacity-50 rounded-2xl hover:bg-zinc-800 transition-all hover:scale-[1.02] shadow-md"
          >
            {creating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              "Phát hành"
            )}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!deleteConfirm}
        onClose={() => !isDeleting && setDeleteConfirm(null)}
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md p-0 shadow-2xl overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6 bg-red-50/50">
          <ModalTitle className="text-sm font-bold tracking-tight text-red-600 flex items-center gap-2">
            <AlertOctagon className="w-5 h-5" /> Xác nhận xóa mã
          </ModalTitle>
          <ModalDescription className="text-[10px] font-bold uppercase tracking-widest text-red-400 mt-1 ml-7">
            Hành động không thể hoàn tác
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <p className="text-xs font-medium text-zinc-700 leading-relaxed bg-zinc-50 border border-zinc-100 p-4 rounded-2xl">
            Bạn có chắc chắn muốn xóa mã ưu đãi <span className="font-bold text-black px-1.5 py-0.5 bg-zinc-200 rounded">{deleteConfirm?.code}</span>? 
            Độc giả sẽ không thể tiếp tục sử dụng mã này.
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => setDeleteConfirm(null)}
            disabled={isDeleting}
            className="flex-1 h-11 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-black rounded-2xl hover:bg-zinc-50 transition-all hover:scale-[1.02] shadow-sm disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="flex-1 h-11 bg-red-600 text-white text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 rounded-2xl hover:bg-red-700 transition-all hover:scale-[1.02] shadow-md disabled:opacity-50"
          >
            {isDeleting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              "Xác nhận xóa"
            )}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
