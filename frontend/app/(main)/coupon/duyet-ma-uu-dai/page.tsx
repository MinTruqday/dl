"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getCouponsAPI,
} from "@/features/finance/services/discount_coupon.service";
import {
  Ticket,
  Loader2,
  Check,
  Ban,
  Clock,
  User,
  Users,
  UserPlus,
  Star,
  ShieldCheck,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { useToast } from "@/shared/contexts/ToastContext";

export default function CouponApprovalPage() {
  const { showToast } = useToast();
  const [coupons, setCoupons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);

  const fetchCoupons = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getCouponsAPI();
      const list = data.data || data || [];
      setCoupons(list.filter((c: any) => c.status === "pending"));
    } catch (err: any) {
      showToast("Lỗi tải danh sách chờ duyệt", "error");
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [showToast]);

  useEffect(() => {
    fetchCoupons();
  }, [fetchCoupons]);



  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-6 shrink-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1 flex items-center gap-2">
              Duyệt mã ưu đãi
            </h1>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
              Kiểm duyệt các mã giảm giá trước khi phát hành
            </p>
          </div>
          {coupons.length > 0 && (
            <div className="px-3 py-1.5 bg-orange-50 border border-orange-100 rounded-xl flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></div>
              <span className="text-[9px] font-bold uppercase tracking-widest text-orange-700">{coupons.length} chờ duyệt</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0, transitionDelay: "100ms" }}>
        {loading ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-zinc-50/50 border border-zinc-100 rounded-3xl">
            <Loader2 className="w-8 h-8 animate-spin text-zinc-400 mb-4" />
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Đang đồng bộ dữ liệu...</p>
          </div>
        ) : coupons.length === 0 ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-zinc-50/50 border border-zinc-100 rounded-3xl p-12 text-center">
            <div className="w-16 h-16 bg-white border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
              <ShieldCheck className="w-8 h-8 text-green-500 stroke-[1.5]" />
            </div>
            <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-2">Hàng đợi trống</h3>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 max-w-sm">
              Tất cả mã ưu đãi đã được xử lý. Không có mã nào đang chờ phê duyệt.
            </p>
          </div>
        ) : (
          <div className="grid gap-6 grid-cols-1 pb-6">
            {coupons.map((c: any) => (
              <div
                key={c.id}
                className="relative group flex flex-col sm:flex-row gap-6 p-5 border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl hover:shadow-md transition-all duration-300 hover:-translate-y-0.5"
              >
                <div className="w-full sm:w-40 h-28 shrink-0 rounded-2xl bg-gradient-to-br from-orange-50 to-orange-100/50 border border-orange-100 relative overflow-hidden flex flex-col items-center justify-center p-3 text-center">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-orange-200 rounded-full blur-2xl opacity-40 -mr-10 -mt-10"></div>
                  <span className="text-xl font-black tracking-widest text-orange-900 block truncate max-w-full relative z-10 uppercase">
                    {c.code}
                  </span>
                  <div className="text-[10px] font-bold text-white bg-orange-600 px-2.5 py-1 mt-2 inline-block rounded-lg shadow-sm relative z-10 uppercase tracking-widest">
                    Giảm {c.discount_percent}%
                  </div>
                </div>

                <div className="flex-1 py-1 flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold text-zinc-900 line-clamp-1">
                      Mã giảm giá: {c.code}
                    </h3>
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-50 text-amber-600 border border-amber-100 text-[9px] font-bold uppercase tracking-widest rounded-lg">
                      <Clock className="w-3.5 h-3.5" /> Chờ duyệt
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-x-6 gap-y-2 mt-2">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-lg bg-zinc-50 border border-zinc-100 flex items-center justify-center">
                        <User className="w-3.5 h-3.5 text-zinc-400" />
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Người tạo</span>
                        <span className="text-xs font-bold text-zinc-900">{c.author_id}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-lg bg-zinc-50 border border-zinc-100 flex items-center justify-center">
                        {c.target_type === "all" ? (
                          <Users className="w-3.5 h-3.5 text-zinc-400" />
                        ) : c.target_type === "new_user" ? (
                          <UserPlus className="w-3.5 h-3.5 text-zinc-400" />
                        ) : (
                          <Star className="w-3.5 h-3.5 text-amber-500" />
                        )}
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Đối tượng</span>
                        <span className="text-xs font-bold text-zinc-900 uppercase">
                          {c.target_type === "all" ? "Tất cả" : c.target_type === "new_user" ? "Người mới" : "Premium"}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-lg bg-zinc-50 border border-zinc-100 flex items-center justify-center">
                        <Ticket className="w-3.5 h-3.5 text-zinc-400" />
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Lượt dùng</span>
                        <span className="text-xs font-bold text-zinc-900">{c.max_uses}</span>
                      </div>
                    </div>
                  </div>


                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
