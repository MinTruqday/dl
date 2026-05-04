"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getAuthorCouponsAPI,
  createAuthorCouponAPI,
  toggleCouponStatusAPI,
  deleteCouponAPI,
} from "@/services/coupon.service";
import {
  Ticket,
  Plus,
  Loader2,
  X,
  Trash2,
  Sparkles,
  AlertCircle,
} from "lucide-react";
import { useToast } from "@/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";

export default function AuthorCouponsPage() {
  const { showToast } = useToast();
  const [coupons, setCoupons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [visible, setVisible] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<any | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const [newCoupon, setNewCoupon] = useState({
    code: "",
    discount_percent: 10,
    max_uses: 100,
    is_active: true,
  });

  const fetchCoupons = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAuthorCouponsAPI();
      setCoupons(data.data || data || []);
    } catch (err: any) {
      console.error("Lỗi tải mã giảm giá:", err);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

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
      await createAuthorCouponAPI(newCoupon);
      showToast("Đã tạo mã ưu đãi mới thành công.", "success");
      setShowCreate(false);
      setNewCoupon({
        code: "",
        discount_percent: 10,
        max_uses: 100,
        is_active: true,
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
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      <div
        className="mb-12 border-b border-zinc-100 pb-10 "
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(10px)",
        }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
              Mã ưu đãi
            </h1>
            <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
              Chương trình ưu đãi & Khuyến mãi{" "}
              <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-3 px-6 py-3 bg-white border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-400 rounded-sm">
              <Ticket className="w-4 h-4" /> Công cụ thúc đẩy doanh thu
            </div>
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="h-14 px-12 bg-black text-white text-[11px] font-bold tracking-[0.2em] uppercase active:scale-95 flex items-center gap-4 rounded-sm"
            >
              {showCreate ? (
                <X className="w-5 h-5" />
              ) : (
                <Plus className="w-5 h-5" />
              )}
              {showCreate ? "Đóng lại" : "Tạo mã mới"}
            </button>
          </div>
        </div>
      </div>

      {showCreate && (
        <div className="mb-12 border border-zinc-100 bg-white/20 p-10 md:p-12 animate-in fade-in slide-in-from-top-4 rounded-sm">
          <div className="max-w-2xl space-y-10">
            <h2 className="text-xl font-bold tracking-tight uppercase">
              Thiết lập ưu đãi mới
            </h2>
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">
                  Mã ưu đãi
                </label>
                <input
                  value={newCoupon.code}
                  onChange={(e) =>
                    setNewCoupon({
                      ...newCoupon,
                      code: e.target.value.toUpperCase(),
                    })
                  }
                  placeholder=""
                  className="w-full h-16 px-6 border border-zinc-100 bg-white text-sm font-bold focus:outline-none focus:border-black rounded-sm"
                />
              </div>
              <div className="space-y-4">
                <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">
                  Phần trăm giảm (%)
                </label>
                <input
                  type="number"
                  value={newCoupon.discount_percent}
                  onChange={(e) =>
                    setNewCoupon({
                      ...newCoupon,
                      discount_percent: parseInt(e.target.value) || 0,
                    })
                  }
                  className="w-full h-16 px-6 border border-zinc-100 bg-white text-sm font-bold focus:outline-none focus:border-black rounded-sm"
                />
              </div>
              <div className="space-y-4">
                <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">
                  Số lượt sử dụng tối đa
                </label>
                <input
                  type="number"
                  value={newCoupon.max_uses}
                  onChange={(e) =>
                    setNewCoupon({
                      ...newCoupon,
                      max_uses: parseInt(e.target.value) || 0,
                    })
                  }
                  className="w-full h-16 px-6 border border-zinc-100 bg-white text-sm font-bold focus:outline-none focus:border-black rounded-sm"
                />
              </div>
            </div>
            <button
              onClick={handleCreate}
              disabled={creating}
              className="h-16 px-12 bg-black text-white text-[11px] font-bold uppercase tracking-widest disabled:opacity-50 flex items-center justify-center gap-4 active:scale-[0.98] rounded-sm"
            >
              {creating ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Ticket className="w-5 h-5" />
              )}
              Xác nhận phát hành mã
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-white border border-zinc-100 h-64 animate-pulse rounded-sm"
            />
          ))}
        </div>
      ) : coupons.length > 0 ? (
        <div
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 delay-75"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? "translateY(0)" : "translateY(10px)",
          }}
        >
          {coupons.map((c: any) => (
            <div
              key={c.id}
              className="flex flex-col p-10 border border-zinc-100 bg-white group relative overflow-hidden rounded-sm"
            >
              <div className="flex justify-between items-start mb-10">
                <div className="space-y-2">
                  <span className="text-3xl font-bold text-black tracking-tighter block transition-transform ">
                    {c.code}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                      Mã ưu đãi
                    </span>
                    <div className="w-1 h-1 bg-zinc-100 rounded-sm" />
                    <span className="text-[9px] font-bold text-black uppercase tracking-widest">
                      Giảm {c.discount_percent}%
                    </span>
                  </div>
                </div>
                <div className="flex flex-col gap-2 items-end">
                  <button
                    onClick={() => toggleStatus(c.id)}
                    className={`text-[9px] font-bold px-4 py-1.5 border tracking-widest uppercase rounded-sm ${
                      c.is_active
                        ? "bg-black text-white border-black"
                        : "bg-white border-zinc-100 text-zinc-300 "
                    }`}
                  >
                    {c.is_active ? "Hoạt động" : "Tạm dừng"}
                  </button>
                  <button
                    onClick={() => setDeleteConfirm(c)}
                    className="p-2 text-zinc-200 transition-colors rounded-sm active:scale-95"
                    title="Xóa mã"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="space-y-6 mt-auto">
                <div className="w-full h-1 bg-white overflow-hidden rounded-sm">
                  <div
                    className="bg-black h-full "
                    style={{
                      width: `${(c.used_count / (c.max_uses || 1)) * 100}%`,
                    }}
                  />
                </div>
                <div className="flex justify-between items-end">
                  <div className="text-[10px] font-bold text-black uppercase tracking-widest">
                    {c.used_count} lượt đã dùng
                  </div>
                  <div className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                    Tối đa {c.max_uses}
                  </div>
                </div>
              </div>

              <div className="absolute -top-6 -right-6 opacity-[0.02] transition-opacity pointer-events-none">
                <Ticket className="w-32 h-32 text-black" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-48 text-center border border-dashed border-zinc-200 bg-white/20 rounded-sm">
          <Ticket className="w-16 h-16 text-zinc-100 mx-auto mb-10 stroke-[1]" />
          <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">
            Chưa có chương trình khuyến mãi nào
          </p>
        </div>
      )}
      <Modal
        isOpen={!!deleteConfirm}
        onClose={() => !isDeleting && setDeleteConfirm(null)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle>Xác nhận xóa mã</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-sm font-bold text-zinc-400 uppercase tracking-widest leading-relaxed">
            Bạn có chắc chắn muốn xóa mã ưu đãi "{deleteConfirm?.code}"? Hành động này không thể hoàn tác.
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-4">
          <button
            onClick={() => setDeleteConfirm(null)}
            disabled={isDeleting}
            className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-all disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-all disabled:opacity-50 flex items-center justify-center"
          >
            {isDeleting ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xác nhận xóa"}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
