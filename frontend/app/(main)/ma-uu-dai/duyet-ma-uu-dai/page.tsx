"use client";

import { useEffect, useState, useCallback } from "react";
import { getCouponsAPI, approveCouponAPI } from "@/services/coupon.service";
import { Ticket, Loader2, Check, Ban, Clock, User, Users, UserPlus, Star } from "lucide-react";
import { useToast } from "@/contexts/Toast";

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
    <section className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 space-y-6">
      <div className="mb-2 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-black">Duyệt mã ưu đãi</h2>
        </div>
      </div>

      {loading ? (
        <div className="py-24 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-zinc-400" /></div>
      ) : coupons.length === 0 ? (
        <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white rounded-2xl">
          <p className="text-sm font-medium text-zinc-500">
            Chưa có dữ liệu
          </p>
        </div>
      ) : (
        <div className="grid gap-6">
          {coupons.map((c: any) => (
            <div key={c.id} className="border border-zinc-200 bg-white flex flex-col md:flex-row overflow-hidden rounded-2xl hover:shadow-sm transition-shadow">
              <div className="p-6 bg-zinc-50 border-r border-zinc-200 w-full md:w-64">
                <span className="text-xl font-mono font-bold text-black block">{c.code}</span>
                <p className="text-xs font-bold text-white bg-black px-2 py-0.5 mt-2 inline-block">-{c.discount_percent}%</p>
                <div className="mt-4 flex items-center gap-2 text-[10px] font-bold text-zinc-400 uppercase">
                   <Clock className="w-3 h-3 text-amber-500" /> Pending
                </div>
              </div>
              
              <div className="flex-1 p-6 flex flex-col justify-between">
                <div className="flex justify-between items-start mb-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-[10px] font-medium text-zinc-500">
                      <User className="w-3 h-3" /> Tác giả: <span className="text-black font-semibold">{c.author_id}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-medium text-zinc-500">
                      {c.target_type === "all" ? <Users className="w-3 h-3" /> : c.target_type === "new_user" ? <UserPlus className="w-3 h-3" /> : <Star className="w-3 h-3" />}
                      Đối tượng: <span className="text-black font-semibold uppercase">{c.target_type}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-medium text-zinc-500">
                      <Ticket className="w-3 h-3" /> Lượt dùng tối đa: <span className="text-black font-semibold">{c.max_uses}</span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 pt-4 border-t border-zinc-100">
                  <button onClick={() => handleApprove(c.id, "reject")} className="flex-1 py-2 text-[10px] font-bold text-zinc-500 uppercase tracking-widest hover:bg-zinc-50 rounded-xl transition-colors">Từ chối</button>
                  <button onClick={() => handleApprove(c.id, "approve")} className="flex-1 py-2 bg-black text-white text-[10px] font-bold uppercase tracking-widest border border-black rounded-xl hover:bg-zinc-800 transition-colors">Phê duyệt</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
