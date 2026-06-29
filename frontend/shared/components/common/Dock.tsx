"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/features/auth/contexts/AuthContext";
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
  { id: "explore", label: "Khám phá", href: "/", icon: Search },
  { id: "message", label: "Tin nhắn", href: "/tin-nhan", icon: MessageSquare, requireAuth: true },
  { id: "chat", label: "Trò chuyện", href: "/tro-chuyen", icon: Sparkles, requireAuth: true },
  { id: "library", label: "Thư viện", href: "/thu-vien", icon: Library, requireAuth: true },
  { id: "profile", label: "Hồ sơ", href: "/ho-so", icon: User, requireAuth: true },
  { id: "wallet", label: "Ví", href: "/vi-tien", icon: Wallet, requireAuth: true },
  { id: "settings", label: "Cài đặt", href: "/cai-dat", icon: Settings, requireAuth: true },
  { id: "provision", label: "Sáng tác", href: "/soan-thao", icon: PenTool, roles: ["author", "admin"] },
  { id: "collaboration", label: "Cộng tác", href: "/cong-tac", icon: Users, roles: ["author", "admin"] },
  { id: "storage", label: "Lưu trữ", href: "/luu-tru", icon: FolderOpen, roles: ["author", "admin"] },
  { id: "document", label: "Tài liệu", href: "/tai-lieu", icon: Files, roles: ["admin", "author"] },
  { id: "audit", label: "Kiểm toán", href: "/kiem-toan", icon: Clock, roles: ["moderator", "admin"] },
  { id: "collect", label: "Bộ sưu tập", href: "/bo-suu-tap", icon: Database, roles: ["admin"] },
  { id: "user_manage", label: "Người dùng", href: "/nguoi-dung", icon: Users, roles: ["admin"] },
  { id: "report", label: "Báo cáo", href: "/bao-cao", icon: AlertTriangle, roles: ["admin", "moderator"] },
  { id: "operation", label: "Vận hành", href: "/van-hanh", icon: Shield, roles: ["admin"] },
  { id: "analytics", label: "Phân tích", href: "/phan-tich", icon: BarChart, roles: ["admin", "author"] },
  { id: "finetune", label: "Tinh chỉnh", href: "/tinh-chinh", icon: Brain, roles: ["admin"] },
  { id: "help", label: "Trợ giúp", href: "/tro-giup", icon: HelpCircle, requireAuth: true },
  { id: "notification", label: "Thông báo", href: "/thong-bao", icon: Bell, requireAuth: true },
  { id: "upgrade", label: "Nâng cấp", href: "/nang-cap", icon: ArrowUpCircle, requireAuth: true },
];

export default function Dock() {
  const pathname = usePathname();
  const { user } = useAuth() as any;
  const [mounted, setMounted] = useState(false);

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
    <aside className="fixed left-0 top-[56px] bottom-0 w-[240px] bg-[#F5F5F7] border-r border-[#D2D2D7] overflow-y-auto hide-scrollbar z-[90]">
      <div className="py-6 px-4">
        <div className="space-y-1">
          {availableItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.id}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-[10px] transition-colors ${
                  active
                    ? "bg-white text-[#0071E3] font-medium shadow-sm"
                    : "text-[#1D1D1F] hover:bg-[#E8E8ED]"
                }`}
              >
                <item.icon className={`w-[18px] h-[18px] ${active ? "text-[#0071E3]" : "text-[#6E6E73]"}`} />
                <span className="text-[15px]">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
