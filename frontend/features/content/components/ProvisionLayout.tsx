"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight, PenTool, LayoutTemplate, FileEdit, BarChart3, Settings2, History, MessageSquare, Trash2, ShieldCheck, Sparkles } from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useState, useEffect } from "react";

export default function ProvisionLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user } = useAuth() as any;
  const isAdminOrMod = user?.role === "admin" || user?.role === "moderator";
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  const navItems = [
    { id: "step1", label: "Thông tin sơ bộ", href: "/soan-thao", icon: LayoutTemplate },
    { id: "step2", label: "Kho lưu trữ nháp", href: "/soan-thao/ban-thao", icon: FileEdit },
    { id: "step3", label: "Số liệu", href: "/soan-thao/so-lieu", icon: BarChart3 },
    { id: "step4", label: "Cấu hình", href: "/soan-thao/cau-hinh", icon: Settings2 },
    { id: "step5", label: "Lịch sử", href: "/soan-thao/lich-su", icon: History },
    { id: "step6", label: "Bình luận", href: "/soan-thao/binh-luan", icon: MessageSquare },
    { id: "step7", label: "Thùng rác", href: "/soan-thao/thung-rac", icon: Trash2 },
    ...(isAdminOrMod
      ? [{ id: "step8", label: "Duyệt bản thảo", href: "/soan-thao/duyet-ban-thao", icon: ShieldCheck, highlight: true }]
      : []),
  ];

  const isActive = (href: string) => {
    if (href === "/soan-thao") return pathname === "/soan-thao";
    return pathname.startsWith(href);
  };

  return (
    <div className={`w-full max-w-[1200px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] flex flex-col font-sans text-[#1D1D1F] transition-opacity duration-500 ${visible ? 'opacity-100' : 'opacity-0'}`}>
      <div className="flex flex-1 min-h-0 gap-6">
        <aside className="w-full lg:w-[320px] bg-[#F5F5F7] rounded-[18px] flex flex-col overflow-hidden shrink-0 hidden lg:flex">
          <div className="p-6 flex items-center gap-3 shrink-0">
            <div className="w-10 h-10 bg-[#0071E3] text-white rounded-full flex items-center justify-center shadow-sm">
              <PenTool className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-[17px] font-semibold text-[#1D1D1F]">Sáng tác</h2>
              <p className="text-[13px] text-[#6E6E73]">Content Provision</p>
            </div>
          </div>
          
          <nav className="flex flex-col overflow-y-auto px-4 py-4 gap-1 shrink custom-scrollbar">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  className={`flex items-center justify-between px-4 py-3 rounded-[14px] transition-colors ${
                    active
                      ? item.highlight 
                        ? "bg-[#0071E3] text-white shadow-sm"
                        : "bg-white text-[#1D1D1F] shadow-sm font-medium"
                      : "bg-transparent text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F]"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-5 h-5 ${active ? (item.highlight ? "text-white" : "text-[#1D1D1F]") : "text-[#6E6E73]"} transition-colors`} />
                    <span className="text-[15px]">{item.label}</span>
                  </div>
                  {item.highlight && !active && <Sparkles className="w-4 h-4 text-[#C7C7CC]" />}
                  {active && <ChevronRight className={`w-4 h-4 ${item.highlight ? "text-white opacity-80" : "text-[#6E6E73]"}`} />}
                </Link>
              );
            })}
          </nav>
          
          <div className="mt-auto p-6 border-t border-[#D2D2D7] shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#E8E8ED] flex items-center justify-center overflow-hidden shrink-0 border border-[#D2D2D7]">
                {user?.avatar_url ? (
                  <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-[13px] font-medium text-[#6E6E73]">{user?.email?.charAt(0).toUpperCase() || "U"}</span>
                )}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-[13px] font-medium text-[#1D1D1F] truncate">{user?.name || "Tác giả"}</span>
                <span className="text-[12px] text-[#6E6E73] truncate">
                  {user?.role === "admin" ? "Quản trị viên" : user?.role === "moderator" ? "Kiểm duyệt viên" : "Tác giả xác thực"}
                </span>
              </div>
            </div>
          </div>
        </aside>

        <main className="flex-1 flex flex-col min-w-0 transition-all duration-300">
          <div className="bg-white border border-[#E8E8ED] p-8 rounded-[24px] shadow-sm flex-1 overflow-y-auto custom-scrollbar">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
