"use client";
import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { semanticSearchAPI } from "@/services/search.service";
import { useRouter } from "next/navigation";
import { Bell, User, Menu, LogOut, ChevronDown, Search, X, Monitor } from "lucide-react";
import AiChatPanel from "./AiChatPanel";
import { useAuth } from "@/contexts/AuthContext";
import { useNotifications } from "@/contexts/NotificationContext";

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export default function Navigation({ onToggleSidebar }: NavbarProps) {
  const { user, logoutState } = useAuth() as any;
  const { notifications, unreadCount, markAsRead } = useNotifications();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

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

  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      await semanticSearchAPI(searchQuery);
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
    } catch (err: any) {
      console.error("Lỗi tìm kiếm ngữ nghĩa:", err);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <>
      <nav
        className="fixed top-0 left-0 right-0 z-[100] bg-white border-b border-zinc-100 font-sans animate-in fade-in duration-300"
        style={{ height: "var(--navbar-height)" }}
      >
        <div className="h-full flex items-center justify-between px-6 max-w-[1440px] mx-auto w-full">
          <div className="flex items-center gap-6">
            {onToggleSidebar && (
              <button
                onClick={onToggleSidebar}
                className="p-2.5 text-zinc-400 hover:text-black hover:bg-zinc-50 transition-all active:scale-95"
                aria-label="Mở trình đơn"
              >
                <Menu className="w-5 h-5" />
              </button>
            )}
            <Link
              href="/"
              className="text-2xl font-bold tracking-tighter text-black leading-none flex items-center gap-2 group active:scale-95 transition-transform"
            >
              <div className="w-8 h-8 bg-black flex items-center justify-center text-white text-xs">DL</div>
              <span className="hidden sm:block">DocLib</span>
            </Link>
          </div>

          <form onSubmit={handleSearch} className="flex-1 max-w-xl hidden lg:block group mx-12">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-300 group-focus-within:text-black transition-colors" />
              <input
                type="text"
                placeholder=""
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-zinc-50 border border-zinc-100 rounded-sm pl-12 pr-12 py-3 text-sm font-bold focus:bg-white focus:border-black focus:outline-none transition-all placeholder:text-zinc-200"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-1 hover:bg-zinc-100 transition-all active:scale-90"
                >
                  <X className="w-3.5 h-3.5 text-zinc-400" />
                </button>
              )}
            </div>
          </form>

          <div className="flex items-center gap-2">
            {user ? (
              <>
                <div className="relative" ref={notifRef}>
                  <button
                    onClick={() => setShowNotifications(!showNotifications)}
                    className={`relative p-3 text-zinc-400 hover:bg-zinc-50 hover:text-black transition-all active:scale-95 ${
                      showNotifications ? "bg-zinc-50 text-black" : ""
                    }`}
                    aria-label="Thông báo"
                  >
                    <Bell className="w-5 h-5" />
                    {unreadCount > 0 && (
                      <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-black border border-white rounded-sm" />
                    )}
                  </button>

                  {showNotifications && (
                    <div className="absolute right-0 mt-3 w-80 bg-white border border-zinc-100 overflow-hidden z-[200] animate-in fade-in slide-in-from-top-2 duration-300 rounded-sm">
                      <div className="px-6 py-5 border-b border-zinc-50 flex items-center justify-between bg-zinc-50/20">
                        <span className="text-[11px] font-bold text-black">Thông báo</span>
                        {unreadCount > 0 && (
                          <span className="px-2 py-0.5 bg-black text-white text-[9px] font-bold">{unreadCount} mới</span>
                        )}
                      </div>
                      <div className="max-h-[400px] overflow-y-auto">
                        {notifications.length > 0 ? (
                          <div className="divide-y divide-zinc-50">
                            {notifications.slice(0, 8).map((notif: any) => (
                              <div
                                key={notif._id}
                                className={`px-6 py-5 cursor-pointer transition-colors hover:bg-zinc-50 ${
                                  !notif.is_read ? "bg-zinc-50/30" : ""
                                }`}
                                onClick={() => {
                                  if (!notif.is_read) markAsRead(notif._id);
                                  if (notif.link) router.push(notif.link);
                                  setShowNotifications(false);
                                }}
                              >
                                <div className="flex gap-4 items-start">
                                  {!notif.is_read && <span className="mt-2 w-1.5 h-1.5 bg-black shrink-0" />}
                                  <div className={!notif.is_read ? "" : "pl-5"}>
                                    <p className="text-[13px] text-zinc-700 leading-relaxed font-medium">
                                      {notif.message}
                                    </p>
                                    <span className="text-[10px] text-zinc-300 mt-2 block font-bold">
                                      {new Date(notif.created_at).toLocaleDateString("vi-VN")}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="py-20 text-center">
                            <Bell className="w-10 h-10 mx-auto text-zinc-50 mb-4" />
                            <p className="text-[11px] font-bold text-zinc-300">Không có thông báo mới</p>
                          </div>
                        )}
                      </div>
                      <Link
                        href="/notification"
                        onClick={() => setShowNotifications(false)}
                        className="block py-4 text-center text-[10px] font-bold text-zinc-400 hover:text-black border-t border-zinc-50 bg-zinc-50/20 transition-all hover:bg-zinc-50 active:scale-95"
                      >
                        Xem tất cả thông báo
                      </Link>
                    </div>
                  )}
                </div>

                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className={`flex items-center gap-3 px-3 py-2 text-zinc-400 hover:bg-zinc-50 transition-all active:scale-95 ${
                      showUserMenu ? "bg-zinc-50" : ""
                    }`}
                  >
                    <div className="w-9 h-9 bg-zinc-50 border border-zinc-100 text-black flex items-center justify-center relative group-hover:border-black transition-all rounded-sm overflow-hidden">
                      {user.avatar_url ? (
                        <img src={user.avatar_url} className="w-full h-full object-cover grayscale" alt="" />
                      ) : (
                        <User className="w-5 h-5" />
                      )}
                      {(user.role === "author" || user.role === "admin") && (
                        <div className="absolute -bottom-0 -right-0 w-4 h-4 bg-black text-white flex items-center justify-center text-[8px] font-bold">
                          {user.role === "admin" ? "A" : "V"}
                        </div>
                      )}
                    </div>
                    <div className="hidden sm:flex flex-col items-start min-w-[80px]">
                      <span className="text-[11px] font-bold text-black truncate max-w-[120px]">
                        {user.full_name || user.username}
                      </span>
                      <span className="text-[9px] font-bold text-zinc-300 leading-none mt-0.5">
                        {user.role}
                      </span>
                    </div>
                    <ChevronDown
                      className={`w-3.5 h-3.5 text-zinc-300 hidden sm:block transition-transform duration-300 ${
                        showUserMenu ? "rotate-180 text-black" : ""
                      }`}
                    />
                  </button>

                  {showUserMenu && (
                    <div className="absolute right-0 mt-3 w-64 bg-white border border-zinc-100 overflow-hidden z-[200] py-2 animate-in fade-in slide-in-from-top-2 duration-300 rounded-sm">
                      <div className="px-6 py-5 border-b border-zinc-50 mb-2 bg-zinc-50/20">
                        <p className="text-[10px] font-bold text-zinc-400 mb-1">Tài khoản</p>
                        <p className="text-sm font-bold truncate text-black">{user.email}</p>
                      </div>
                      <Link
                        href="/profile"
                        onClick={() => setShowUserMenu(false)}
                        className="flex items-center gap-4 px-6 py-3.5 text-[11px] font-bold text-zinc-500 hover:text-black hover:bg-zinc-50 transition-all active:scale-95"
                      >
                        <User className="w-4 h-4" />
                        Hồ sơ cá nhân
                      </Link>
                      <Link
                        href="/settings"
                        onClick={() => setShowUserMenu(false)}
                        className="flex items-center gap-4 px-6 py-3.5 text-[11px] font-bold text-zinc-500 hover:text-black hover:bg-zinc-50 transition-all active:scale-95"
                      >
                        <Monitor className="w-4 h-4" />
                        Cài đặt hệ thống
                      </Link>
                      <div className="border-t border-zinc-50 my-2" />
                      <button
                        onClick={handleLogout}
                        className="flex items-center gap-4 px-6 py-3.5 text-[11px] font-bold text-zinc-300 hover:text-black hover:bg-zinc-50 transition-all w-full text-left active:scale-95"
                      >
                        <LogOut className="w-4 h-4" />
                        Đăng xuất tài khoản
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center gap-3 ml-4">
                <Link
                  href="/login"
                  className="px-6 py-3 text-sm font-bold text-zinc-500 hover:text-black transition-all active:scale-95"
                >
                  Đăng nhập
                </Link>
                <Link
                  href="/register"
                  className="px-8 py-3 text-sm font-bold text-white bg-black hover:bg-zinc-800 transition-all active:scale-95 rounded-sm"
                >
                  Đăng ký
                </Link>
              </div>
            )}
          </div>
        </div>
      </nav>

      {user && <AiChatPanel />}
    </>
  );
}