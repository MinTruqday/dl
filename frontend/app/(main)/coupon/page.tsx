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
      showToast("Lỗi tải mã giảm giá", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

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
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <div className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-black">Mã ưu đãi</h1>
          <p className="text-zinc-500 text-sm font-medium">
            Quản lý chương trình khuyến mãi và công cụ thúc đẩy doanh thu
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="h-10 px-6 bg-black text-white text-xs font-semibold uppercase tracking-wider flex items-center gap-2 rounded-none border border-black"
        >
          {showCreate ? (
            <X className="w-4 h-4" />
          ) : (
            <Plus className="w-4 h-4" />
          )}
          {showCreate ? "Đóng lại" : "Tạo mã mới"}
        </button>
      </div>

      {showCreate && (
        <div className="mb-8 border border-zinc-200 bg-white p-8">
          <div className="max-w-3xl space-y-6">
            <h2 className="text-sm font-semibold text-black border-b border-zinc-200 pb-3">
              Thiết lập ưu đãi mới
            </h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
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
                  placeholder="Ví dụ: SUMMER20"
                  className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-mono font-semibold focus:outline-none focus:border-black rounded-none placeholder:text-zinc-400 placeholder:font-sans"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
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
                  className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black rounded-none"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                  Số lượt tối đa
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
                  className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black rounded-none"
                />
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <button
                onClick={handleCreate}
                disabled={creating}
                className="h-10 px-8 bg-black text-white text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-2 disabled:opacity-50 rounded-none border border-black"
              >
                {creating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  "Xác nhận phát hành"
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-zinc-50 border border-zinc-200 h-48 rounded-none"
            />
          ))}
        </div>
      ) : coupons.length > 0 ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {coupons.map((c: any) => (
            <div
              key={c.id}
              className="border border-zinc-200 bg-white flex flex-col rounded-none"
            >
              <div className="p-6 border-b border-zinc-200 flex justify-between items-start bg-zinc-50">
                <div>
                  <span className="text-lg font-mono font-bold text-black block">
                    {c.code}
                  </span>
                  <p className="text-xs font-semibold text-black mt-1">
                    Giảm {c.discount_percent}%
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => toggleStatus(c.id)}
                    className={`px-3 py-1.5 text-[10px] font-semibold uppercase border rounded-none ${
                      c.is_active
                        ? "bg-black text-white border-black"
                        : "bg-white text-zinc-500 border-zinc-200"
                    }`}
                  >
                    {c.is_active ? "Hoạt động" : "Tạm dừng"}
                  </button>
                  <button
                    onClick={() => setDeleteConfirm(c)}
                    className="p-1.5 border border-zinc-200 bg-white text-zinc-400 rounded-none"
                    title="Xóa mã"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div className="p-6 space-y-4 flex-1 flex flex-col justify-end">
                <div>
                  <div className="flex justify-between items-end mb-2">
                    <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                      Tiến độ sử dụng
                    </span>
                    <span className="text-[10px] font-bold text-black">
                      {c.used_count} / {c.max_uses} lượt
                    </span>
                  </div>
                  <div className="w-full h-1 bg-zinc-100 rounded-none overflow-hidden">
                    <div
                      className="bg-black h-full"
                      style={{
                        width: `${(c.used_count / (c.max_uses || 1)) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-zinc-50 rounded-none">
          <Ticket className="w-6 h-6 text-zinc-400 mb-3" />
          <span className="text-xs font-medium text-zinc-500">
            Chưa có chương trình khuyến mãi nào
          </span>
        </div>
      )}

      <Modal
        isOpen={!!deleteConfirm}
        onClose={() => !isDeleting && setDeleteConfirm(null)}
        className="max-w-sm rounded-none border border-zinc-200 bg-white p-0"
      >
        <ModalHeader className="border-b border-zinc-200 p-6">
          <ModalTitle className="text-sm font-semibold text-black">
            Xác nhận xóa mã
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="p-6">
          <p className="text-xs font-medium text-zinc-500 leading-relaxed">
            Bạn có chắc chắn muốn xóa mã ưu đãi "{deleteConfirm?.code}"? Hành
            động này không thể hoàn tác.
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-200 p-4 bg-zinc-50">
          <button
            onClick={() => setDeleteConfirm(null)}
            disabled={isDeleting}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black disabled:opacity-50 rounded-none"
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium disabled:opacity-50 flex items-center justify-center rounded-none"
          >
            {isDeleting ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              "Xác nhận xóa"
            )}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
