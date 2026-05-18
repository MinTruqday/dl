"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight, Ticket, Activity, Users } from "lucide-react";
import { useAuth } from "@/contexts/Auth";
import { useEffect, useState } from "react";
import { getCouponsAPI } from "@/services/coupon.service";

export default function MaGiamGiaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { user } = useAuth() as any;
  const isAdmin = user?.role === "admin";
  const [stats, setStats] = useState({ totalUsed: 0, activeCount: 0, pendingCount: 0 });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const data = await getCouponsAPI();
      const list = data.data || data || [];
      setStats({
        totalUsed: list.reduce((acc: number, c: any) => acc + (c.used_count || 0), 0),
        activeCount: list.filter((c: any) => c.is_active && c.status === 'approved').length,
        pendingCount: list.filter((c: any) => c.status === 'pending').length,
      });
    } catch (err) { console.error(err); }
  };

  const navItems = [
    { id: "all", label: "Tất cả mã ưu đãi", href: "/ma-giam-gia" },
    ...(isAdmin ? [{ id: "pending", label: "Duyệt mã giảm giá", href: "/ma-giam-gia/duyet-ma-giam-gia", badge: stats.pendingCount }] : []),
  ];

  const isActive = (href: string) => {
    if (href === "/ma-giam-gia") return pathname === "/ma-giam-gia";
    return pathname === href;
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
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <aside className="lg:col-span-3 space-y-12">
          <div className="space-y-4">
            <div className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
              Phân loại
            </div>
            <nav className="flex flex-col gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.id}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2.5 text-sm font-medium border rounded-none transition-colors ${
                    isActive(item.href)
                      ? "bg-zinc-100 text-black border-zinc-300"
                      : "bg-white text-zinc-500 border-transparent hover:bg-zinc-50"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {item.label}
                    {item.badge !== undefined && item.badge > 0 && (
                      <span className="text-[10px] bg-black text-white px-1.5 py-0.5 font-bold">
                        {item.badge}
                      </span>
                    )}
                  </div>
                  {isActive(item.href) && <ChevronRight className="w-4 h-4" />}
                </Link>
              ))}
            </nav>
          </div>

          <div className="space-y-4">
            <div className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
              Thống kê nhanh
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-zinc-50 border border-zinc-200 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-zinc-400" />
                </div>
                <div>
                  <div className="text-[10px] font-bold text-zinc-400 uppercase">Tổng lượt dùng</div>
                  <div className="text-sm font-bold text-black">{stats.totalUsed} lượt</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-zinc-50 border border-zinc-200 flex items-center justify-center">
                  <Users className="w-4 h-4 text-zinc-400" />
                </div>
                <div>
                  <div className="text-[10px] font-bold text-zinc-400 uppercase">Mã đang chạy</div>
                  <div className="text-sm font-bold text-black">{stats.activeCount} mã</div>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-9">{children}</main>
      </div>
    </div>
  );
}
