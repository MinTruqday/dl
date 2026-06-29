"use client";
import React, { useState, useEffect, useRef } from "react";
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
  Ticket,
  FolderOpen,
  Clock,
  MessageSquare,
  Database,
  Files,
  Presentation,
  Sparkles,
  Shield,
  MoreHorizontal,
  Pin,
  PinOff,
  BarChart,
  Brain,
  HelpCircle,
  Bell,
  ArrowUpCircle,
} from "lucide-react";

export const MENU_ITEMS = [
  { id: "explore", label: "Khám phá", href: "/", icon: Search },
  { id: "message", label: "Tin nhắn", href: "/message", icon: MessageSquare, requireAuth: true },
  { id: "chat", label: "Trò chuyện", href: "/chat", icon: Sparkles, requireAuth: true },
  { id: "library", label: "Thư viện", href: "/library", icon: Library, requireAuth: true },
  { id: "profile", label: "Hồ sơ", href: "/profile", icon: User, requireAuth: true },
  { id: "wallet", label: "Ví", href: "/wallet", icon: Wallet, requireAuth: true },
  { id: "settings", label: "Cài đặt", href: "/settings", icon: Settings, requireAuth: true },
  { id: "provision", label: "Sáng tác", href: "/provision", icon: PenTool, roles: ["author", "admin"] },

  { id: "collaboration", label: "Hợp tác", href: "/collaboration", icon: Users, roles: ["author", "admin"] },
  { id: "storage", label: "Kho lưu trữ", href: "/storage", icon: FolderOpen, roles: ["author", "admin"] },
  { id: "document", label: "Kho tài liệu", href: "/document", icon: Files, roles: ["admin", "author"] },
  { id: "audit", label: "Nhật ký hệ thống", href: "/audit", icon: Clock, roles: ["moderator", "admin"] },
  { id: "collect", label: "Thu thập dữ liệu", href: "/collect", icon: Database, roles: ["admin"] },
  { id: "user_manage", label: "Quản lý người dùng", href: "/user", icon: Users, roles: ["admin"] },
  { id: "report", label: "Báo cáo vi phạm", href: "/report", icon: AlertTriangle, roles: ["admin", "moderator"] },
  { id: "operation", label: "Vận hành hệ thống", href: "/operation", icon: Shield, roles: ["admin"] },

  { id: "analytics", label: "Thống kê", href: "/analytics", icon: BarChart, roles: ["admin", "author"] },
  { id: "finetune", label: "Huấn luyện AI", href: "/finetune", icon: Brain, roles: ["admin"] },
  { id: "help", label: "Trung tâm hỗ trợ", href: "/help", icon: HelpCircle, requireAuth: true },
  { id: "notification", label: "Thông báo", href: "/notification", icon: Bell, requireAuth: true },
  { id: "upgrade", label: "Nâng cấp", href: "/upgrade", icon: ArrowUpCircle, requireAuth: true },
];

const DEFAULT_PINNED = ["explore", "message", "chat"];

export default function Dock() {
  const pathname = usePathname();
  const { user } = useAuth() as any;
  const [pinnedIds, setPinnedIds] = useState<string[]>(DEFAULT_PINNED);
  const [mounted, setMounted] = useState(false);
  const [showLaunchpad, setShowLaunchpad] = useState(false);
  const launchpadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem("doclib_dock_pinned");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setPinnedIds(parsed);
        }
      } catch (e) {}
    }
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (launchpadRef.current && !launchpadRef.current.contains(event.target as Node)) {
        setShowLaunchpad(false);
      }
    };
    if (showLaunchpad) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showLaunchpad]);

  const togglePin = (id: string) => {
    setPinnedIds((prev) => {
      let next;
      if (prev.includes(id)) {
        next = prev.filter((p) => p !== id);
      } else {
        next = [...prev, id];
      }
      localStorage.setItem("doclib_dock_pinned", JSON.stringify(next));
      return next;
    });
  };

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
  const pinnedItems = availableItems.filter((item) => pinnedIds.includes(item.id));
  const unpinnedItems = availableItems.filter((item) => !pinnedIds.includes(item.id));

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <>
      <div className="fixed top-1/2 -translate-y-1/2 left-4 z-[100] flex">
        <nav className="common-panel p-2 flex flex-col items-center gap-2 transition-all duration-300">
          {pinnedItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.id}
                href={item.href}
                className={`relative group flex items-center justify-center w-12 h-12 rounded-2xl transition-all duration-200 hover:scale-110 ${
                  active ? "bg-zinc-100 text-black shadow-inner" : "bg-white text-zinc-500 hover:bg-zinc-50 hover:text-black border border-zinc-100"
                }`}
              >
                <item.icon className={`w-5 h-5 transition-all duration-200 ${active ? "scale-110" : ""}`} />
                {/* Tooltip */}
                <div className="absolute left-14 top-1/2 -translate-y-1/2 scale-0 group-hover:scale-100 transition-transform origin-left bg-black text-white text-[10px] font-bold px-2.5 py-1.5 rounded-xl whitespace-nowrap shadow-md z-[200]">
                  {item.label}
                  <div className="absolute top-1/2 -translate-y-1/2 -left-1 border-4 border-transparent border-r-black"></div>
                </div>
                {/* Indicator dot */}
                {active && (
                  <div className="absolute top-1/2 -translate-y-1/2 -left-1.5 w-1 h-1 bg-black rounded-full" />
                )}
              </Link>
            );
          })}
          
          {/* Divider */}
          {pinnedItems.length > 0 && <div className="h-px w-8 bg-zinc-200 my-1" />}

          {/* More button */}
          <div className="relative">
            <button
              onClick={() => setShowLaunchpad((v) => !v)}
              className={`relative group flex items-center justify-center w-12 h-12 rounded-2xl transition-all duration-200 hover:scale-110 ${
                showLaunchpad ? "bg-zinc-100 text-black shadow-inner" : "bg-white text-zinc-500 hover:bg-zinc-50 hover:text-black border border-zinc-100"
              }`}
            >
              <MoreHorizontal className="w-5 h-5" />
              {/* Tooltip */}
              <div className={`absolute left-14 top-1/2 -translate-y-1/2 transition-transform origin-left bg-black text-white text-[10px] font-bold px-2.5 py-1.5 rounded-xl whitespace-nowrap shadow-md z-[200] ${showLaunchpad ? "scale-0" : "scale-0 group-hover:scale-100"}`}>
                Tất cả tính năng
                <div className="absolute top-1/2 -translate-y-1/2 -left-1 border-4 border-transparent border-r-black"></div>
              </div>
            </button>

            {/* Launchpad Popover */}
            {showLaunchpad && (
              <div
                ref={launchpadRef}
                className="absolute left-16 bottom-0 w-[320px] sm:w-[400px] common-panel p-4 grid grid-cols-4 sm:grid-cols-5 gap-3 animate-in fade-in slide-in-from-left-4 duration-200"
              >
                <div className="col-span-full mb-2">
                  <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest pl-1">
                    Tất cả tính năng
                  </h3>
                </div>
                {availableItems.map((item) => {
                  const isPinned = pinnedIds.includes(item.id);
                  const active = isActive(item.href);
                  return (
                    <div key={item.id} className="relative flex flex-col items-center gap-1 group">
                      <Link
                        href={item.href}
                        onClick={() => setShowLaunchpad(false)}
                        className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-transform hover:scale-105 border ${
                          active ? "bg-zinc-100 border-zinc-200 text-black" : "bg-white border-zinc-100 text-zinc-600 hover:bg-zinc-50 hover:text-black"
                        }`}
                      >
                        <item.icon className="w-5 h-5" />
                      </Link>
                      <span className="text-[9px] font-medium text-zinc-500 text-center leading-tight max-w-full truncate px-1">
                        {item.label}
                      </span>
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          togglePin(item.id);
                        }}
                        className={`absolute -top-2 -right-2 p-1 rounded-full shadow-sm border transition-opacity opacity-0 group-hover:opacity-100 ${
                          isPinned ? "bg-zinc-100 border-zinc-200 text-zinc-500 hover:text-red-500" : "bg-black border-black text-white"
                        }`}
                      >
                        {isPinned ? <PinOff className="w-3 h-3" /> : <Pin className="w-3 h-3" />}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </nav>
      </div>
    </>
  );
}
