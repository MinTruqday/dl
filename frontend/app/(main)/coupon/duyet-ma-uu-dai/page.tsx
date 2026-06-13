"use client";

import { useEffect, useState, useCallback } from "react";
import { getCouponsAPI, approveCouponAPI } from "@/features/finance/services/coupon.service";
import { Ticket, Loader2, Check, Ban, Clock, User, Users, UserPlus, Star } from "lucide-react";
import { useToast } from "@/shared/contexts/Toast";

export default function CouponApprovalPage() {
  const { showToast } = useToast();
  const [coupons, setCoupons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchCoupons = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getCouponsAPI();
      const list = data.data || data || [];
      setCoupons(list.filter((c: any) => c.status === 'pending'));
    } catch (err: any) {
      showToast("Lỗi tải danh sách chờ duyệt", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchCoupons();
  }, [fetchCoupons]);

  const handleApprove = async (id: string, action: "approve" | "reject") => {
    try {
      await approveCouponAPI(id, action);
      showToast(action === "approve" ? "Đã duyệt mã ưu đãi" : "Đã từ chối mã ưu đãi", "success");
      fetchCoupons();
    } catch (err: any) {
      showToast(err.message || "Lỗi xử lý phê duyệt", "error");
    }
  };

  return (
    <section className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-300">
      <div className="mb-2 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-black">Duyệt mã ưu đãi</h2>
      </div>

      {loading ? (
        <div className="grid gap-6 grid-cols-1 animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: '150ms', animationFillMode: 'both' }}>
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-zinc-50 border border-zinc-200 rounded-2xl h-36 w-full animate-pulse"
            />
          ))}
        </div>
      ) : coupons.length === 0 ? (
        <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white rounded-2xl animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: '150ms', animationFillMode: 'both' }}>
          <p className="text-sm font-medium text-zinc-500">
            Chưa có dữ liệu
          </p>
        </div>
      ) : (
        <div className="grid gap-6 grid-cols-1 animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: '150ms', animationFillMode: 'both' }}>
          {coupons.map((c: any) => (
            <div
              key={c.id}
              className="relative group flex flex-row gap-6 p-3 border border-zinc-200 bg-white rounded-2xl hover:border-black transition-all duration-150 overflow-hidden"
            >
              <div
                className="w-24 h-36 shrink-0 rounded-xl bg-zinc-50 border-zinc-200 relative overflow-hidden flex flex-col items-center justify-center p-3 text-center"
              >
                <span className="text-base font-mono font-bold text-black block truncate max-w-full">{c.code}</span>
                <p className="text-[10px] font-bold text-white bg-black px-2 py-0.5 mt-2 inline-block rounded">-{c.discount_percent}%</p>
              </div>

              <div
                className="flex-1 py-1 flex flex-col gap-2"
              >
                <h3
                  className="text-base font-semibold text-black line-clamp-2 leading-snug"
                >
                  Mã: {c.code}
                </h3>
                
                <div className="text-xs text-zinc-500 flex flex-col gap-1">
                  <div className="flex items-center gap-1.5">
                    <User className="w-4 h-4" />
                    <span>Tác giả: <span className="text-black font-medium">{c.author_id}</span></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {c.target_type === "all" ? <Users className="w-4 h-4" /> : c.target_type === "new_user" ? <UserPlus className="w-4 h-4" /> : <Star className="w-4 h-4" />}
                    <span>Đối tượng: <span className="text-black font-medium uppercase">{c.target_type}</span></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Ticket className="w-4 h-4" />
                    <span>Lượt dùng tối đa: <span className="text-black font-medium">{c.max_uses}</span></span>
                  </div>
                </div>

                <div
                  className="mt-auto pt-3 flex items-center justify-between"
                >
                  <span className="text-xs font-semibold text-amber-500 flex items-center gap-1">
                    <Clock className="w-4 h-4" /> Chờ duyệt
                  </span>
                  
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApprove(c.id, "reject")}
                      className="text-[10px] font-semibold text-zinc-500 bg-zinc-100 hover:bg-zinc-200 transition-all duration-150 px-3 py-1.5 rounded-lg uppercase tracking-wider"
                    >
                      Từ chối
                    </button>
                    <button
                      onClick={() => handleApprove(c.id, "approve")}
                      className="text-[10px] font-semibold text-white bg-black hover:bg-zinc-800 transition-all duration-150 px-3 py-1.5 rounded-lg uppercase tracking-wider"
                    >
                      Duyệt
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
