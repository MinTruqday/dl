"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  Search,
  Library,
  User,
  Wallet,
  Settings,
  PenTool,
  AlertTriangle,
  Users,
  FolderOpen,
  Clock,
  MessageSquare,
  Database,
  Files,
  Sparkles,
  Shield,
  BarChart,
  Brain,
  HelpCircle,
  Bell,
  ArrowUpCircle,
} from "lucide-react";

export const MENU_ITEMS = [
  { id: "explore", label: "Khám phá", href: "/", icon: Search, group: "chung" },
  { id: "message", label: "Tin nhắn", href: "/tin-nhan", icon: MessageSquare, requireAuth: true, group: "chung" },
  { id: "chat", label: "Trò chuyện", href: "/tro-chuyen", icon: Sparkles, requireAuth: true, group: "chung" },
  { id: "library", label: "Thư viện", href: "/thu-vien", icon: Library, requireAuth: true, group: "chung" },
  { id: "profile", label: "Hồ sơ", href: "/ho-so", icon: User, requireAuth: true, group: "ca_nhan" },
  { id: "wallet", label: "Ví tiền", href: "/vi-tien", icon: Wallet, requireAuth: true, group: "ca_nhan" },
  { id: "settings", label: "Cài đặt", href: "/cai-dat", icon: Settings, requireAuth: true, group: "ca_nhan" },
  { id: "provision", label: "Soạn thảo", href: "/soan-thao", icon: PenTool, roles: ["author", "admin"], group: "sang_tac" },
  { id: "collaboration", label: "Cộng tác", href: "/cong-tac", icon: Users, roles: ["author", "admin"], group: "sang_tac" },
  { id: "storage", label: "Lưu trữ", href: "/luu-tru", icon: FolderOpen, roles: ["author", "admin"], group: "sang_tac" },
  { id: "audit", label: "Kiểm toán", href: "/kiem-toan", icon: Clock, roles: ["moderator", "admin"], group: "he_thong" },
  { id: "collect", label: "Thu thập", href: "/thu-thap", icon: Database, roles: ["admin"], group: "he_thong" },
  { id: "user_manage", label: "Người dùng", href: "/nguoi-dung", icon: Users, roles: ["admin"], group: "he_thong" },
  { id: "report", label: "Báo cáo", href: "/bao-cao", icon: AlertTriangle, roles: ["admin", "moderator"], group: "he_thong" },
  { id: "operation", label: "Vận hành", href: "/van-hanh", icon: Shield, roles: ["admin"], group: "he_thong" },
  { id: "analytics", label: "Phân tích", href: "/phan-tich", icon: BarChart, roles: ["admin", "author"], group: "he_thong" },
  { id: "finetune", label: "Tinh chỉnh", href: "/tinh-chinh", icon: Brain, roles: ["admin"], group: "he_thong" },
  { id: "help", label: "Trợ giúp", href: "/tro-giup", icon: HelpCircle, requireAuth: true, group: "tro_giup" },
  { id: "announcement", label: "Thông báo", href: "/thong-bao", icon: Bell, requireAuth: true, group: "tro_giup" },
  { id: "upgrade", label: "Nâng cấp", href: "/nang-cap", icon: ArrowUpCircle, requireAuth: true, group: "tro_giup" },
];

export default function Dock() {
  const pathname = usePathname();
  const { user } = useAuth() as any;
  const [mounted, setMounted] = useState(false);
  const [hoveredTooltip, setHoveredTooltip] = useState<{ label: string; top: number } | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const getAvailableItems = () => {
    return MENU_ITEMS.filter((item) => {
      if (item.requireAuth && !user) return false;
      if (item.roles) {
        const userRole = (user?.role || "").toLowerCase();
        const normalizedRoles = item.roles.map((r) => r.toLowerCase());
        if (!normalizedRoles.includes(userRole)) return false;
      }
      return true;
    });
  };

  if (!mounted) return null;

  const availableItems = getAvailableItems();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <>
      <aside className="fixed left-0 top-[56px] bottom-0 w-[72px] bg-white/80 backdrop-blur-xl border-r border-[#E8E8ED] overflow-y-auto hide-scrollbar z-[90] hidden lg:block">
        <div className="py-6 px-2">
          <div className="flex flex-col gap-2">
            {availableItems.map((item, index) => {
              const active = isActive(item.href);
              const showSeparator = index > 0 && item.group !== availableItems[index - 1].group;
              
              return (
                <React.Fragment key={item.id}>
                  {showSeparator && (
                    <div className="w-8 h-px bg-[#D2D2D7] mx-auto my-1" />
                  )}
                  <Link
                    href={item.href}
                    onMouseEnter={(e) => {
                      const rect = e.currentTarget.getBoundingClientRect();
                      setHoveredTooltip({ label: item.label, top: rect.top + rect.height / 2 });
                    }}
                    onMouseLeave={() => setHoveredTooltip(null)}
                    className={`flex items-center justify-center w-[48px] h-[48px] rounded-[12px] transition-colors mx-auto ${
                      active
                        ? "bg-[#0071E3] text-white shadow-sm"
                        : "text-[#6E6E73] hover:bg-[#F5F5F7] hover:text-[#1D1D1F]"
                    }`}
                  >
                    <item.icon className="w-[20px] h-[20px] shrink-0" />
                  </Link>
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </aside>

      {hoveredTooltip && (
        <div
          className="fixed left-[84px] z-[9999] px-3 py-1.5 bg-[#1D1D1F] text-white text-[13px] font-medium rounded-[8px] whitespace-nowrap pointer-events-none shadow-lg -translate-y-1/2 animate-in fade-in zoom-in-95 duration-200"
          style={{ top: hoveredTooltip.top }}
        >
          {hoveredTooltip.label}
          <div className="absolute top-1/2 -translate-y-1/2 -left-1 w-2 h-2 bg-[#1D1D1F] rotate-45 rounded-sm"></div>
        </div>
      )}
    </>
  );
}
