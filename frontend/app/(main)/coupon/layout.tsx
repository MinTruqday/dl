"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight, Ticket, Activity, Users, ShieldCheck } from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useEffect, useState } from "react";
import { getCouponsAPI } from "@/features/finance/services/discount_coupon.service";

export default function PromotionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { user } = useAuth() as any;
  const isAdmin = user?.role === "admin";
  const [stats, setStats] = useState({
    totalUsed: 0,
    activeCount: 0,
    pendingCount: 0,
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const data = await getCouponsAPI();
      const list = data.data || data || [];
      setStats({
        totalUsed: list.reduce(
          (acc: number, c: any) => acc + (c.used_count || 0),
          0,
        ),
        activeCount: list.filter(
          (c: any) => c.is_active && c.status === "approved",
        ).length,
        pendingCount: list.filter((c: any) => c.status === "pending").length,
      });
    } catch (err) {
      console.error(err);
    }
  };

  const navItems = [
    { id: "all", label: "Tất cả mã ưu đãi", href: "/coupon", icon: Ticket },
    ...(isAdmin
      ? [
          {
            id: "pending",
            label: "Duyệt mã ưu đãi",
            href: "/coupon/duyet-ma-uu-dai",
            badge: stats.pendingCount,
            icon: ShieldCheck
          },
        ]
      : []),
  ];

  const isActive = (href: string) => {
    if (href === "/coupon") return pathname === "/coupon";
    return pathname === href;
  };

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col gap-6 font-sans text-black selection:bg-black selection:text-white overflow-hidden">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        <aside className="lg:col-span-3 space-y-6 overflow-y-auto custom-scrollbar max-h-full pr-1 shrink-0">
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-6 space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <Ticket className="w-4 h-4 text-black" />
              <div className="text-[10px] font-bold text-zinc-900 uppercase tracking-widest">
                Quản lý mã ưu đãi
              </div>
            </div>
            <nav className="flex flex-col gap-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.id}
                    href={item.href}
                    className={`flex items-center justify-between px-4 py-3 text-xs font-bold uppercase tracking-wider rounded-2xl transition-all duration-300 group ${
                      active
                        ? "bg-black text-white shadow-md"
                        : "bg-white text-zinc-500 hover:bg-zinc-50 hover:text-black border border-transparent hover:border-zinc-200"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className={`w-4 h-4 ${active ? "text-white" : "text-zinc-400 group-hover:text-black"}`} />
                      {item.label}
                    </div>
                    <div className="flex items-center gap-2">
                      {item.badge !== undefined && item.badge > 0 && (
                        <span className={`text-[9px] px-1.5 py-0.5 font-bold rounded-md flex items-center justify-center min-w-[20px] ${
                          active ? "bg-white/20 text-white" : "bg-orange-100 text-orange-600"
                        }`}>
                          {item.badge}
                        </span>
                      )}
                      {active && <ChevronRight className="w-4 h-4 opacity-50" />}
                    </div>
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-6 space-y-6">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-black" />
              <div className="text-[10px] font-bold text-zinc-900 uppercase tracking-widest">
                Thống kê nhanh
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center gap-4 group">
                <div className="w-10 h-10 bg-zinc-50 border border-zinc-100 flex items-center justify-center rounded-2xl group-hover:bg-black group-hover:text-white transition-colors">
                  <Activity className="w-4 h-4 text-zinc-400 group-hover:text-white" />
                </div>
                <div>
                  <div className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest mb-0.5">
                    Tổng lượt dùng
                  </div>
                  <div className="text-sm font-bold text-black tracking-tight">
                    {stats.totalUsed.toLocaleString()} <span className="text-xs text-zinc-400 font-medium">lượt</span>
                  </div>
                </div>
              </div>
              
              <div className="h-px bg-zinc-100 w-full" />
              
              <div className="flex items-center gap-4 group">
                <div className="w-10 h-10 bg-zinc-50 border border-zinc-100 flex items-center justify-center rounded-2xl group-hover:bg-black group-hover:text-white transition-colors">
                  <Users className="w-4 h-4 text-zinc-400 group-hover:text-white" />
                </div>
                <div>
                  <div className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest mb-0.5">
                    Mã đang hoạt động
                  </div>
                  <div className="text-sm font-bold text-black tracking-tight">
                    {stats.activeCount.toLocaleString()} <span className="text-xs text-zinc-400 font-medium">mã</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-9 flex flex-col min-h-0">
          {children}
        </main>
      </div>
    </div>
  );
}
