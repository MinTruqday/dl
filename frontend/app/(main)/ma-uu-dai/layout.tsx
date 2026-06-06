"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight, Ticket, Activity, Users } from "lucide-react";
import { useAuth } from "@/contexts/Auth";
import { useEffect, useState } from "react";
import { getCouponsAPI } from "@/services/coupon.service";

export default function PromotionLayout({
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
    { id: "all", label: "Tất cả mã ưu đãi", href: "/ma-uu-dai" },
    ...(isAdmin ? [{ id: "pending", label: "Duyệt mã ưu đãi", href: "/ma-uu-dai/duyet-ma-uu-dai", badge: stats.pendingCount }] : []),
  ];

  const isActive = (href: string) => {
    if (href === "/ma-uu-dai") return pathname === "/ma-uu-dai";
    return pathname === href;
  };

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col gap-6 font-sans text-black selection:bg-black selection:text-white overflow-hidden">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        <aside className="lg:col-span-3 space-y-6 overflow-y-auto max-h-full pr-1 shrink-0">
          <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 space-y-4 animate-in fade-in slide-in-from-bottom-8 duration-300">
            <div className="text-sm font-semibold text-black mb-1">
              Phân loại
            </div>
            <nav className="flex flex-col gap-1.5">
              {navItems.map((item) => (
                <Link
                  key={item.id}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-150 ${
                    isActive(item.href)
                      ? "bg-zinc-100 text-black"
                      : "bg-white text-zinc-500 hover:bg-zinc-50 hover:text-black"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {item.label}
                    {item.badge !== undefined && item.badge > 0 && (
                      <span className="text-[10px] bg-black text-white px-1.5 py-0.5 font-bold rounded-md">
                        {item.badge}
                      </span>
                    )}
                  </div>
                  {isActive(item.href) && <ChevronRight className="w-4 h-4" />}
                </Link>
              ))}
            </nav>
          </div>

          <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 space-y-4 animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: '100ms', animationFillMode: 'both' }}>
            <div className="text-sm font-semibold text-black mb-1">
              Thống kê nhanh
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-zinc-50 border border-zinc-200 flex items-center justify-center rounded-xl">
                  <Activity className="w-4 h-4 text-zinc-400" />
                </div>
                <div>
                  <div className="text-[10px] font-bold text-zinc-400 uppercase">Tổng lượt dùng</div>
                  <div className="text-sm font-bold text-black">{stats.totalUsed} lượt</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-zinc-50 border border-zinc-200 flex items-center justify-center rounded-xl">
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

        <main className="lg:col-span-9 space-y-6 overflow-y-auto max-h-full pr-1">
          {children}
        </main>
      </div>
    </div>
  );
}
