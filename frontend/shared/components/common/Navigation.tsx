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
      className="fixed top-4 left-4 right-4 z-[100] common-panel font-sans transition-all duration-300"
      style={{ height: "var(--navbar-height)" }}
    >
      <div className="h-full flex items-center justify-between px-4 max-w-[1440px] mx-auto w-full gap-4">
        <Link
          href="/"
          className="text-xl font-bold tracking-tight text-black leading-none flex items-center gap-2 shrink-0 transition-all duration-200 hover:scale-105"
        >
          <div className="w-10 h-10 bg-black flex items-center justify-center text-white text-sm font-bold rounded-2xl shadow-sm">
            dl
          </div>
          <span className="hidden sm:block text-sm font-bold text-black">DocLib</span>
        </Link>

        <form onSubmit={handleSearch} className="flex-1 max-w-xl hidden lg:block">
          <div className="relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 group-focus-within:text-black transition-colors" />
            <input
              type="text"
              placeholder=""
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white border border-zinc-200 rounded-2xl pl-10 pr-10 py-2.5 text-sm font-medium focus:bg-white focus:border-black focus:outline-none placeholder:text-zinc-300 shadow-sm transition-all duration-200"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-black transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>

        <div className="flex items-center gap-2 shrink-0">
          {user ? (
            <>
              <Link
                href="/upgrade"
                className="relative h-11 px-4 flex items-center gap-2 text-black bg-white border border-zinc-200 rounded-2xl shadow-sm transition-all duration-200 hover:scale-105 hover:bg-zinc-50"
                title="Nâng cấp AI"
              >
                <Sparkles className="w-4 h-4 text-amber-500" />
                <span className="text-xs font-bold text-black hidden md:block">Nâng cấp AI</span>
              </Link>
              <Link
                href="/chat"
                className="w-11 h-11 flex items-center justify-center text-zinc-500 bg-white border border-zinc-200 rounded-2xl shadow-sm transition-all duration-200 hover:scale-110 hover:text-black hover:bg-zinc-50"
                title="DocLib AI"
              >
                <MessageCircle className="w-5 h-5" />
              </Link>
              <div className="relative" ref={notifRef}>
                <button
                  onClick={() => setShowNotifications(!showNotifications)}
                  className={`relative w-11 h-11 flex items-center justify-center text-zinc-500 bg-white border border-zinc-200 rounded-2xl shadow-sm transition-all duration-200 hover:scale-110 hover:text-black hover:bg-zinc-50 ${
                    showNotifications ? "bg-zinc-100 text-black shadow-inner" : ""
                  }`}
                  aria-label="Thông báo"
                >
                  <Bell className="w-5 h-5" />
                  {unreadCount > 0 && (
                    <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-black rounded-full" />
                  )}
                </button>

                {showNotifications && (
                  <div className="absolute right-0 mt-4 w-[360px] bg-white border border-zinc-200 z-[200] rounded-3xl shadow-xl animate-in fade-in zoom-in-95 duration-200 p-4">
                    <div className="flex items-center justify-between mb-3 pl-1">
                      <span className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Thông báo</span>
                      {unreadCount > 0 && (
                        <span className="px-2 py-0.5 bg-black text-white text-[10px] font-bold rounded-xl">
                          {unreadCount} mới
                        </span>
                      )}
                    </div>
                    <div className="max-h-[360px] overflow-y-auto -mx-2">
                      {notifications.length > 0 ? (
                        <div className="space-y-1">
                          {notifications.slice(0, 8).map((notif: any) => (
                            <div
                              key={notif._id}
                              className={`px-3 py-3 mx-2 rounded-2xl cursor-pointer transition-colors hover:bg-zinc-50 ${
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
                                    className={`text-sm leading-snug truncate ${
                                      notif.is_read ? "text-zinc-500 font-medium" : "text-black font-semibold"
                                    }`}
                                  >
                                    {notif.message}
                                  </p>
                                  <span className="text-[10px] text-zinc-400 mt-1.5 block font-medium">
                                    {new Date(notif.created_at).toLocaleDateString("vi-VN")}
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="py-12 text-center">
                          <Bell className="w-8 h-8 mx-auto text-zinc-200 mb-3" />
                          <p className="text-xs font-medium text-zinc-400">Không có thông báo mới</p>
                        </div>
                      )}
                    </div>
                    <div className="pt-3 mt-1">
                      <Link
                        href="/notification"
                        onClick={() => setShowNotifications(false)}
                        className="block py-3 text-center text-xs font-bold text-zinc-600 bg-zinc-50 rounded-2xl hover:bg-zinc-100 hover:text-black transition-colors"
                      >
                        Xem tất cả thông báo
                      </Link>
                    </div>
                  </div>
                )}
              </div>

              <div className="relative" ref={userMenuRef}>
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className={`flex items-center gap-3 h-11 px-3 bg-white border border-zinc-200 rounded-2xl shadow-sm transition-all duration-200 hover:scale-105 hover:bg-zinc-50 ${
                    showUserMenu ? "bg-zinc-100 text-black shadow-inner" : ""
                  }`}
                >
                  <div className="w-6 h-6 bg-white border border-zinc-200 text-black flex items-center justify-center relative rounded-xl overflow-hidden shrink-0">
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
                  <div className="hidden sm:flex flex-col items-start min-w-[60px] max-w-[120px]">
                    <span className="text-xs font-semibold text-black truncate w-full leading-tight text-left">
                      {user.full_name || user.username}
                    </span>
                    <span className="text-[10px] font-medium text-zinc-400 leading-tight capitalize mt-0.5">
                      {user.role}
                    </span>
                  </div>
                  <ChevronDown
                    className={`w-4 h-4 text-zinc-400 hidden sm:block shrink-0 transition-transform duration-200 ${showUserMenu ? "rotate-180" : ""}`}
                  />
                </button>

                {showUserMenu && (
                  <div className="absolute right-0 mt-4 w-64 bg-white border border-zinc-200 z-[200] p-4 rounded-3xl shadow-xl animate-in fade-in zoom-in-95 duration-200">
                    <div className="mb-3 pl-1">
                      <p className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Tài khoản</p>
                    </div>
                    <div className="bg-zinc-50 border border-zinc-100 rounded-2xl px-3 py-2.5 mb-3">
                      <p className="text-sm font-semibold truncate text-black">{user.email}</p>
                    </div>
                    <div className="space-y-1">
                      <Link
                        href="/profile"
                        onClick={() => setShowUserMenu(false)}
                        className="flex items-center gap-3 px-3 py-2.5 text-xs font-semibold text-zinc-600 hover:bg-zinc-50 hover:text-black rounded-2xl transition-colors"
                      >
                        <User className="w-4 h-4" />
                        Hồ sơ cá nhân
                      </Link>
                      <Link
                        href="/settings"
                        onClick={() => setShowUserMenu(false)}
                        className="flex items-center gap-3 px-3 py-2.5 text-xs font-semibold text-zinc-600 hover:bg-zinc-50 hover:text-black rounded-2xl transition-colors"
                      >
                        <Monitor className="w-4 h-4" />
                        Cài đặt hệ thống
                      </Link>
                      <div className="h-px bg-zinc-100 my-2 mx-2" />
                      <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 px-3 py-2.5 text-xs font-semibold text-zinc-600 w-full text-left hover:bg-zinc-50 hover:text-black rounded-2xl transition-colors"
                      >
                        <LogOut className="w-4 h-4" />
                        Đăng xuất
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="h-11 px-4 flex items-center justify-center text-xs font-semibold text-black bg-white border border-zinc-200 rounded-2xl shadow-sm transition-all duration-200 hover:scale-105 hover:bg-zinc-50"
              >
                Đăng nhập
              </Link>
              <Link
                href="/register"
                className="h-11 px-4 flex items-center justify-center text-xs font-semibold text-white bg-black rounded-2xl shadow-sm transition-all duration-200 hover:scale-105 hover:bg-zinc-800"
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
