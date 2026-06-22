"use client";
import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { smartSearchAPI } from "@/features/content/services/content_discovery.service";
import { useRouter } from "next/navigation";
import {
  Bell,
  User,
  LogOut,
  ChevronDown,
  Search,
  X,
  Monitor,
  MessageCircle,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useNotifications } from "@/shared/contexts/NotificationContext";

export default function Navigation() {
  const { user, logoutState } = useAuth() as any;
  const { notifications, unreadCount, markAsRead } = useNotifications();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    logoutState();
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      await smartSearchAPI(searchQuery);
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <nav
      className="fixed top-2 left-2 right-2 md:top-4 md:left-4 md:right-4 z-[100] bg-white/90 backdrop-blur-md border border-zinc-200/60 rounded-3xl shadow-sm font-sans"
      style={{ height: "var(--navbar-height)" }}
    >
      <div className="h-full flex items-center justify-between px-4 max-w-[1440px] mx-auto w-full gap-4">
        <Link
          href="/"
          className="text-xl font-bold tracking-tight text-black leading-none flex items-center gap-2 shrink-0"
        >
          <div className="w-8 h-8 bg-zinc-900 flex items-center justify-center text-white text-xs font-bold rounded-2xl">
            dl
          </div>
          <span className="hidden sm:block text-sm font-bold text-zinc-900">DocLib</span>
        </Link>

        <form onSubmit={handleSearch} className="flex-1 max-w-xl hidden lg:block">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400" />
            <input
              type="text"
              placeholder=""
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-zinc-50 border border-zinc-200 rounded-2xl pl-9 pr-9 py-2 text-sm font-medium focus:bg-white focus:border-zinc-400 focus:outline-none placeholder:text-zinc-300"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-400"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </form>

        <div className="flex items-center gap-2 shrink-0">
          {user ? (
            <>
              <Link
                href="/upgrade"
                className="relative px-3 py-1.5 flex items-center gap-1.5 text-zinc-600 bg-zinc-100 rounded-2xl"
                title="Nâng cấp AI"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                <span className="text-xs font-bold text-zinc-900 hidden md:block">Nâng cấp AI</span>
              </Link>
              <Link
                href="/chat"
                className="p-2 text-zinc-500 rounded-2xl bg-zinc-50 border border-zinc-100"
                title="DocLib AI"
              >
                <MessageCircle className="w-4 h-4" />
              </Link>
              <div className="relative" ref={notifRef}>
                <button
                  onClick={() => setShowNotifications(!showNotifications)}
                  className={`relative p-2 text-zinc-500 rounded-2xl border ${
                    showNotifications
                      ? "bg-zinc-100 border-zinc-200 text-zinc-900"
                      : "bg-zinc-50 border-zinc-100"
                  }`}
                  aria-label="Thông báo"
                >
                  <Bell className="w-4 h-4" />
                  {unreadCount > 0 && (
                    <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-zinc-900 rounded-full" />
                  )}
                </button>

                {showNotifications && (
                  <div className="absolute right-0 mt-2 w-80 bg-white/95 backdrop-blur-md border border-zinc-200 z-[200] rounded-3xl overflow-hidden shadow-xl">
                    <div className="px-5 py-4 border-b border-zinc-100 flex items-center justify-between">
                      <span className="text-sm font-semibold text-zinc-900">Thông báo</span>
                      {unreadCount > 0 && (
                        <span className="px-2 py-0.5 bg-zinc-900 text-white text-[10px] font-bold rounded-xl">
                          {unreadCount} mới
                        </span>
                      )}
                    </div>
                    <div className="max-h-[360px] overflow-y-auto">
                      {notifications.length > 0 ? (
                        <div className="divide-y divide-zinc-50">
                          {notifications.slice(0, 8).map((notif: any) => (
                            <div
                              key={notif._id}
                              className={`px-5 py-3.5 cursor-pointer ${
                                !notif.is_read ? "bg-zinc-50" : "bg-white"
                              }`}
                              onClick={() => {
                                if (!notif.is_read) markAsRead(notif._id);
                                if (notif.link) router.push(notif.link);
                                setShowNotifications(false);
                              }}
                            >
                              <div className="flex gap-3 items-start">
                                <div className="flex-1 min-w-0">
                                  <p
                                    className={`text-[13px] leading-snug truncate ${
                                      notif.is_read ? "text-zinc-500 font-normal" : "text-zinc-900 font-semibold"
                                    }`}
                                  >
                                    {notif.message}
                                  </p>
                                  <span className="text-[10px] text-zinc-400 mt-1 block">
                                    {new Date(notif.created_at).toLocaleDateString("vi-VN")}
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="py-12 text-center">
                          <Bell className="w-7 h-7 mx-auto text-zinc-200 mb-3" />
                          <p className="text-xs font-medium text-zinc-400">Không có thông báo mới</p>
                        </div>
                      )}
                    </div>
                    <Link
                      href="/notification"
                      onClick={() => setShowNotifications(false)}
                      className="block py-3 text-center text-xs font-medium text-zinc-500 border-t border-zinc-100 bg-zinc-50 rounded-b-3xl"
                    >
                      Xem tất cả thông báo
                    </Link>
                  </div>
                )}
              </div>

              <div className="relative" ref={userMenuRef}>
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className={`flex items-center gap-2 px-2 py-1.5 rounded-2xl border ${
                    showUserMenu ? "bg-zinc-100 border-zinc-200" : "bg-zinc-50 border-zinc-100"
                  }`}
                >
                  <div className="w-6 h-6 bg-white border border-zinc-200 text-zinc-900 flex items-center justify-center relative rounded-xl overflow-hidden">
                    {user.avatar_url ? (
                      <img
                        src={user.avatar_url}
                        className="w-full h-full object-cover grayscale"
                        alt=""
                      />
                    ) : (
                      <User className="w-3.5 h-3.5" />
                    )}
                  </div>
                  <div className="hidden sm:flex flex-col items-start">
                    <span className="text-[11px] font-semibold text-zinc-900 truncate max-w-[100px] leading-tight">
                      {user.full_name || user.username}
                    </span>
                    <span className="text-[9px] font-medium text-zinc-400 leading-tight capitalize">
                      {user.role}
                    </span>
                  </div>
                  <ChevronDown
                    className={`w-3 h-3 text-zinc-400 hidden sm:block ${showUserMenu ? "rotate-180" : ""}`}
                  />
                </button>

                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-52 bg-white/95 backdrop-blur-md border border-zinc-200 z-[200] py-2 rounded-3xl shadow-xl">
                    <div className="px-4 py-3 border-b border-zinc-100 mb-1">
                      <p className="text-[9px] font-bold text-zinc-400 mb-1 uppercase tracking-widest">Tài khoản</p>
                      <p className="text-xs font-semibold truncate text-zinc-900">{user.email}</p>
                    </div>
                    <Link
                      href="/profile"
                      onClick={() => setShowUserMenu(false)}
                      className="flex items-center gap-3 px-4 py-2.5 text-xs font-medium text-zinc-600"
                    >
                      <User className="w-3.5 h-3.5" />
                      Hồ sơ cá nhân
                    </Link>
                    <Link
                      href="/settings"
                      onClick={() => setShowUserMenu(false)}
                      className="flex items-center gap-3 px-4 py-2.5 text-xs font-medium text-zinc-600"
                    >
                      <Monitor className="w-3.5 h-3.5" />
                      Cài đặt hệ thống
                    </Link>
                    <div className="border-t border-zinc-100 my-1.5" />
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-3 px-4 py-2.5 text-xs font-medium text-zinc-600 w-full text-left"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      Đăng xuất
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="px-3 py-1.5 text-xs font-medium text-zinc-600 bg-zinc-50 border border-zinc-200 rounded-2xl"
              >
                Đăng nhập
              </Link>
              <Link
                href="/register"
                className="px-3 py-1.5 text-xs font-medium text-white bg-zinc-900 rounded-2xl"
              >
                Đăng ký
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
