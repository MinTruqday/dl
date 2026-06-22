"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight, PenTool, LayoutTemplate, FileEdit, BarChart3, Settings2, History, MessageSquare, Trash2, ShieldCheck, Sparkles } from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useState, useEffect } from "react";

export default function CreationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { user } = useAuth() as any;
  const isAdminOrMod = user?.role === "admin" || user?.role === "moderator";
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  const navItems = [
    { id: "step1", label: "Thông tin sơ bộ", href: "/provision", icon: LayoutTemplate },
    { id: "step2", label: "Kho lưu trữ nháp", href: "/provision/ban-thao", icon: FileEdit },
    { id: "step3", label: "Số liệu", href: "/provision/so-lieu", icon: BarChart3 },
    { id: "step4", label: "Cấu hình", href: "/provision/cau-hinh", icon: Settings2 },
    { id: "step5", label: "Lịch sử", href: "/provision/lich-su", icon: History },
    { id: "step6", label: "Bình luận", href: "/provision/binh-luan", icon: MessageSquare },
    { id: "step7", label: "Thùng rác", href: "/provision/thung-rac", icon: Trash2 },
    ...(isAdminOrMod
      ? [
          {
            id: "step8",
            label: "Duyệt bản thảo",
            href: "/provision/duyet-ban-thao",
            icon: ShieldCheck,
            highlight: true,
          },
        ]
      : []),
  ];

  const isActive = (href: string) => {
    if (href === "/provision") return pathname === "/provision";
    return pathname.startsWith(href);
  };

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 h-[calc(100dvh-var(--navbar-height))] font-sans text-zinc-900 bg-zinc-50 selection:bg-black selection:text-white flex flex-col transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
      <div className="grid lg:grid-cols-12 gap-6 flex-1 min-h-0">
        <aside className="lg:col-span-4 xl:col-span-3 flex flex-col gap-6 min-h-0">
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-5 md:p-6 flex flex-col flex-1 min-h-0">
            <div className="border-b border-zinc-100 pb-4 mb-4 flex items-center gap-3 shrink-0">
              <div className="w-10 h-10 bg-black text-white rounded-2xl flex items-center justify-center shadow-md">
                <PenTool className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold tracking-tight text-zinc-900">Sáng tác</h2>
                <p className="text-[9px] font-bold uppercase tracking-widest text-zinc-400">Content Provision</p>
              </div>
            </div>
            
            <nav className="flex flex-col gap-1.5 overflow-y-auto custom-scrollbar flex-1 pr-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.id}
                    href={item.href}
                    className={`flex items-center justify-between px-4 py-3 rounded-2xl transition-all duration-200 group ${
                      active
                        ? item.highlight 
                          ? "bg-black text-white shadow-md scale-[1.02]"
                          : "bg-white border border-zinc-200 text-zinc-900 shadow-sm scale-[1.02]"
                        : "bg-transparent text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={`w-4 h-4 ${active ? (item.highlight ? "text-white" : "text-black") : "text-zinc-400 group-hover:text-zinc-600"} transition-colors`} />
                      <span className={`text-[11px] font-bold uppercase tracking-wider ${active ? "" : ""}`}>
                        {item.label}
                      </span>
                    </div>
                    {item.highlight && !active && (
                      <Sparkles className="w-3.5 h-3.5 text-zinc-300" />
                    )}
                    {active && (
                      <ChevronRight className={`w-4 h-4 ${item.highlight ? "opacity-50" : "text-zinc-300"}`} />
                    )}
                  </Link>
                );
              })}
            </nav>
            
            <div className="mt-4 pt-4 border-t border-zinc-100 shrink-0">
              <div className="bg-zinc-50 border border-zinc-100 rounded-2xl p-4 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-zinc-200 flex items-center justify-center overflow-hidden shrink-0">
                  {user?.avatar_url ? (
                    <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-[10px] font-bold uppercase">{user?.email?.charAt(0) || "U"}</span>
                  )}
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-[10px] font-bold text-zinc-900 uppercase tracking-widest truncate">
                    {user?.name || "Tác giả"}
                  </span>
                  <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest truncate">
                    {user?.role === "admin" ? "Quản trị viên" : user?.role === "moderator" ? "Kiểm duyệt viên" : "Tác giả xác thực"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-8 xl:col-span-9 h-full min-h-0 flex flex-col transition-all duration-300">
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm flex-1 overflow-y-auto custom-scrollbar">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
