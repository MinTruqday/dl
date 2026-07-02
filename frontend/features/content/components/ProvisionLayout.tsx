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
import { useState, useEffect } from "react";

export default function ProvisionLayout({
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
    { id: "step1", label: "Thông tin sơ bộ", href: "/soan-thao" },
    { id: "step2", label: "Kho lưu trữ nháp", href: "/soan-thao/ban-thao" },
    { id: "step3", label: "Số liệu", href: "/soan-thao/so-lieu" },
    { id: "step4", label: "Cấu hình", href: "/soan-thao/cau-hinh" },
    { id: "step5", label: "Lịch sử", href: "/soan-thao/lich-su" },
    { id: "step6", label: "Bình luận", href: "/soan-thao/binh-luan" },
    { id: "step7", label: "Thùng rác", href: "/soan-thao/thung-rac" },
    ...(isAdminOrMod
      ? [
          {
            id: "step8",
            label: "Duyệt bản thảo",
            href: "/soan-thao/duyet-ban-thao",
            highlight: true,
          },
        ]
      : []),
  ];

  const isActive = (href: string) => {
    if (href === "/soan-thao") return pathname === "/soan-thao";
    return pathname.startsWith(href);
  };

  return (
    <div
      className={`w-full max-w-[1200px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] font-sans text-[#1D1D1F] flex flex-col gap-6 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`}
    >
      <div className="flex flex-col md:flex-row gap-6 flex-1 min-h-0">
        <aside className="w-full md:w-[320px] shrink-0 flex flex-col space-y-6 overflow-y-auto no-scrollbar pb-6 pr-2">
          <div className="bg-[#F5F5F7] rounded-[18px] p-6 space-y-4">
            <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
              Sáng tác
            </p>
            <div className="flex flex-col gap-2">
              {navItems.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.id}
                    href={item.href}
                    className={`flex items-center justify-between px-4 py-3 rounded-[10px] transition-colors ${active ? (item.highlight ? "bg-[#1D1D1F] text-white" : "bg-white text-[#0071E3] font-medium") : "bg-transparent text-[#6E6E73] hover:bg-white hover:text-[#1D1D1F]"}`}
                  >
                    <span className="text-[14px]">{item.label}</span>
                  </Link>
                );
              })}
            </div>
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

        <main className="flex-1 min-w-0 flex flex-col min-h-0">
          <div className="flex-1 overflow-y-auto no-scrollbar">{children}</div>
        </main>
      </div>
    </div>
  );
}
