"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  ChevronRight,
  PenTool,
  LayoutTemplate,
  FileEdit,
  BarChart3,
  Settings2,
  History,
  MessageSquare,
  Trash2,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";

export default function ProvisionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { user } = useAuth() as any;
  const isAdminOrMod = user?.role === "admin" || user?.role === "moderator";

  const navItems = [
    { id: "step1", label: "Khởi tạo", href: "/soan-thao" },
    { id: "step2", label: "Bản nháp", href: "/soan-thao/ban-thao" },
    { id: "step5", label: "Lịch sử", href: "/soan-thao/lich-su" },
    { id: "step7", label: "Thùng rác", href: "/soan-thao/thung-rac" },
  ];

  const isActive = (href: string) => {
    if (href === "/soan-thao") return pathname === "/soan-thao";
    return pathname.startsWith(href);
  };

  return (
    <div className="w-full max-w-[1200px] mx-auto px-6 py-6 min-h-[calc(100dvh-56px)] flex flex-col font-sans text-[#1D1D1F]">
      <div className="grid md:grid-cols-12 gap-8">
        <aside className="md:col-span-4 xl:col-span-4 space-y-6">
          <div className="bg-[#F5F5F7] rounded-[18px] p-6">
            <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
              Soạn thảo
            </p>
            <nav className="flex flex-col gap-1.5">
              {navItems.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.id}
                    href={item.href}
                    className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${active ? "bg-white text-[#0071E3] font-medium" : "text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}
                  >
                    <span className="truncate text-left">{item.label}</span>
                    {active && <ChevronRight className="w-4 h-4 shrink-0" />}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="bg-[#F5F5F7] rounded-[18px] p-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-[10px] bg-[#E8E8ED] flex items-center justify-center overflow-hidden shrink-0">
                {user?.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt="Avatar"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-[14px] font-medium text-[#1D1D1F]">
                    {user?.name?.charAt(0).toUpperCase() || "T"}
                  </span>
                )}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-[14px] font-medium text-[#1D1D1F] truncate">
                  {user?.name || "Tác giả"}
                </span>
                <span className="text-[12px] text-[#6E6E73] truncate">
                  {user?.role === "admin"
                    ? "Quản trị viên"
                    : user?.role === "moderator"
                      ? "Kiểm duyệt viên"
                      : "Tác giả xác thực"}
                </span>
              </div>
            </div>
          </div>
        </aside>

        <main className="md:col-span-8 xl:col-span-8 space-y-6">
          <div className="flex-1 overflow-y-auto no-scrollbar">{children}</div>
        </main>
      </div>
    </div>
  );
}
