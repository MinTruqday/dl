"use client";
import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { smartSearchAPI } from "@/features/content/services/content_discovery.service";
import { useRouter } from "next/navigation";
import {
  Bell,
  User,
  Menu,
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

interface NavigationProps {
  onToggleSidebar?: () => void;
}

export default function Navigation({ onToggleSidebar }: NavigationProps) {
  const { user, logoutState } = useAuth() as any;
  const { notifications, unreadCount, markAsRead } = useNotifications();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        notifRef.current &&
        !notifRef.current.contains(event.target as Node)
      ) {
        setShowNotifications(false);
      }
      if (
        userMenuRef.current &&
        !userMenuRef.current.contains(event.target as Node)
      ) {
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
      await smartSearchAPI(searchQuery);
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
    } catch (err: any) {
      console.error("Error smart searching:", err);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <>
      <nav
        className="fixed top-2 left-2 right-2 md:top-4 md:left-4 md:right-4 z-[100] bg-white border border-zinc-200 rounded-2xl shadow-sm font-sans"
        style={{ height: "var(--navbar-height)" }}
      >
        <div className="h-full flex items-center justify-between px-6 max-w-[1440px] mx-auto w-full">
          <div className="flex items-center gap-6">
            {onToggleSidebar && (
              <button
                onClick={onToggleSidebar}
                className="p-2 text-zinc-500 hover:text-black hover:bg-zinc-100 rounded-xl transition-all duration-150"
                aria-label="Mở trình đơn"
              >
                <Menu className="w-5 h-5" />
              </button>
            )}
            <Link
              href="/"
              className="text-xl font-bold tracking-tight text-black leading-none flex items-center gap-2 group "
            >
              <div className="w-8 h-8 bg-black flex items-center justify-center text-white text-xs font-bold rounded-2xl">
                dl
              </div>
              <span className="hidden sm:block">DocLib</span>
            </Link>
          </div>

          <form
            onSubmit={handleSearch}
            className="flex-1 max-w-xl hidden lg:block mx-12 group"
          >
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 group-focus-within:text-black " />
              <input
                type="text"
                placeholder=""
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-white border border-zinc-200 rounded-2xl pl-12 pr-12 py-2 text-sm font-medium transition-all duration-150 focus:bg-white focus:border-black focus:outline-none placeholder:text-zinc-300"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-zinc-400 "
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </form>

          <div className="flex items-center gap-4">
            {user ? (
              <>
                <Link
                  href="/upgrade"
                  className="relative px-3 py-1.5 flex items-center gap-2 text-zinc-600 bg-zinc-100 hover:bg-zinc-200 rounded-xl transition-all duration-150"
                  title="Nâng cấp AI"
                >
                  <Sparkles className="w-4 h-4 text-amber-500" />
                  <span className="text-xs font-bold text-black hidden md:block">Nâng cấp AI</span>
                </Link>
                <Link
                  href="/chat"
                  className="relative p-2 text-zinc-500 hover:text-black hover:bg-zinc-100 rounded-xl transition-all duration-150"
                  title="DocLib AI"
                >
                  <MessageCircle className="w-5 h-5" />
                </Link>
                <div className="relative" ref={notifRef}>
                  <button
                    onClick={() => setShowNotifications(!showNotifications)}
                    className={`relative p-2 text-zinc-500 hover:text-black hover:bg-zinc-100 rounded-xl transition-all duration-150 ${
                      showNotifications ? "bg-zinc-100 text-black" : ""
                    }`}
                    aria-label="Thông báo"
                  >
                    <Bell className="w-5 h-5" />
                    {unreadCount > 0 && (
                      <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-black rounded-full" />
                    )}
                  </button>

                  {showNotifications && (
                    <div className="absolute right-0 mt-3 w-80 bg-white border border-zinc-200  z-[200] rounded-2xl overflow-hidden shadow-sm">
                      <div className="px-5 py-4 border-b border-zinc-200 flex items-center justify-between">
                        <span className="text-sm font-semibold text-black">
                          Thông báo
                        </span>
                        {unreadCount > 0 && (
                          <span className="px-2 py-0.5 bg-black text-white text-[10px] font-semibold rounded-2xl">
                            {unreadCount} mới
                          </span>
                        )}
                      </div>
                      <div className="max-h-[400px] overflow-y-auto">
                        {notifications.length > 0 ? (
                          <div className="divide-y divide-zinc-100">
                            {notifications.slice(0, 8).map((notif: any) => (
                              <div
                                key={notif._id}
                                className={`px-5 py-4 cursor-pointer hover:bg-zinc-50 transition-all duration-150 ${
                                  !notif.is_read
                                    ? "border-l-2 border-l-black ml-[-2px] bg-white"
                                    : "bg-white"
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
                                      className={`text-[13px] leading-relaxed truncate ${notif.is_read ? "text-zinc-500 font-normal" : "text-black font-semibold"}`}
                                    >
                                      {notif.message}
                                    </p>
                                    <span className="text-[10px] text-zinc-400 mt-1 block">
                                      {new Date(
                                        notif.created_at,
                                      ).toLocaleDateString("vi-VN")}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="py-12 text-center">
                            <Bell className="w-8 h-8 mx-auto text-zinc-200 mb-3" />
                            <p className="text-xs font-medium text-zinc-500">
                              Không có thông báo mới
                            </p>
                          </div>
                        )}
                      </div>
                      <Link
                        href="/notification"
                        onClick={() => setShowNotifications(false)}
                        className="block py-3 text-center text-xs font-medium text-zinc-500 border-t border-zinc-200 bg-zinc-50 hover:bg-zinc-100 hover:text-black transition-all duration-150"
                      >
                        Xem tất cả thông báo
                      </Link>
                    </div>
                  )}
                </div>

                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className={`flex items-center gap-3 px-2 py-1.5 text-zinc-500 hover:text-black hover:bg-zinc-100 rounded-xl transition-all duration-150 ${
                      showUserMenu ? "bg-zinc-100 text-black" : ""
                    }`}
                  >
                    <div className="w-8 h-8 bg-white border border-zinc-200 text-black flex items-center justify-center relative rounded-2xl overflow-hidden">
                      {user.avatar_url ? (
                        <img
                          src={user.avatar_url}
                          className="w-full h-full object-cover grayscale"
                          alt=""
                        />
                      ) : (
                        <User className="w-4 h-4" />
                      )}
                      {(user.role === "author" || user.role === "admin") && (
                        <div className="absolute bottom-0 right-0 w-3 h-3 bg-black text-white flex items-center justify-center text-[7px] font-bold">
                          {user.role === "admin" ? "A" : "V"}
                        </div>
                      )}
                    </div>
                    <div className="hidden sm:flex flex-col items-start min-w-[80px]">
                      <span className="text-xs font-semibold text-black truncate max-w-[120px]">
                        {user.full_name || user.username}
                      </span>
                      <span className="text-[10px] font-medium text-zinc-500 leading-none mt-0.5 capitalize">
                        {user.role}
                      </span>
                    </div>
                    <ChevronDown
                      className={`w-3.5 h-3.5 text-zinc-400 hidden sm:block transition-transform duration-150 ${
                        showUserMenu ? "rotate-180 text-black" : ""
                      }`}
                    />
                  </button>

                  {showUserMenu && (
                    <div className="absolute right-0 mt-3 w-56 bg-white border border-zinc-200  z-[200] py-2 rounded-2xl shadow-sm">
                      <div className="px-5 py-3 border-b border-zinc-200 mb-2">
                        <p className="text-[10px] font-semibold text-zinc-400 mb-1 uppercase tracking-wider">
                          Tài khoản
                        </p>
                        <p className="text-sm font-semibold truncate text-black">
                          {user.email}
                        </p>
                      </div>
                      <Link
                        href="/profile"
                        onClick={() => setShowUserMenu(false)}
                        className="flex items-center gap-3 px-5 py-2.5 text-xs font-medium text-zinc-600 hover:bg-zinc-50 hover:text-black transition-all duration-150"
                      >
                        <User className="w-4 h-4" />
                        Hồ sơ cá nhân
                      </Link>
                      <Link
                        href="/settings"
                        onClick={() => setShowUserMenu(false)}
                        className="flex items-center gap-3 px-5 py-2.5 text-xs font-medium text-zinc-600 hover:bg-zinc-50 hover:text-black transition-all duration-150"
                      >
                        <Monitor className="w-4 h-4" />
                        Cài đặt hệ thống
                      </Link>
                      <div className="border-t border-zinc-200 my-2" />
                      <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 px-5 py-2.5 text-xs font-medium text-zinc-600 w-full text-left hover:bg-zinc-50 hover:text-black transition-all duration-150"
                      >
                        <LogOut className="w-4 h-4" />
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
                  className="px-4 py-2 text-sm font-medium text-zinc-600 hover:text-black transition-all duration-150"
                >
                  Đăng nhập
                </Link>
                <Link
                  href="/register"
                  className="px-4 py-2 text-sm font-medium text-white bg-black hover:bg-zinc-800 rounded-2xl transition-all duration-150"
                >
                  Đăng ký
                </Link>
              </div>
            )}
          </div>
        </div>
      </nav>
    </>
  );
}
