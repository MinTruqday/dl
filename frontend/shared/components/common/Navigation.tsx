"use client";
import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { smartSearchAPI } from "@/features/content/services/content_discovery.service";
import { useRouter } from "next/navigation";
import {
  Bell,
  Search,
  X,
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
      router.push(`/tim-kiem?q=${encodeURIComponent(searchQuery)}`);
    } catch (err: any) {
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-[100] w-full bg-white/80 backdrop-blur-xl border-b border-[#E8E8ED] transition-all duration-300"
      style={{ height: "56px" }}
    >
      <div className="h-full flex items-center justify-between px-6 w-full gap-4 max-w-[1200px] mx-auto">
        <Link
          href="/"
          className="text-lg font-semibold tracking-tight text-[#1D1D1F] leading-none flex items-center gap-2 shrink-0 transition-opacity hover:opacity-80"
        >
          <span>DocLib</span>
        </Link>

        <form onSubmit={handleSearch} className="flex-1 max-w-xl hidden lg:block relative">
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6E6E73] transition-colors group-focus-within:text-[#0071E3]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#F5F5F7] border border-transparent rounded-[10px] pl-9 pr-9 py-1 text-[13px] focus:bg-white focus:border-[#0071E3] focus:outline-none transition-all duration-200"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6E6E73] hover:text-[#1D1D1F] transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </form>

        <div className="flex items-center gap-4 shrink-0">
          {user ? (
            <>
              <div className="relative" ref={notifRef}>
                <button
                  onClick={() => setShowNotifications(!showNotifications)}
                  className={`relative flex items-center justify-center transition-opacity hover:opacity-80 ${
                    showNotifications ? "text-[#0071E3]" : "text-[#1D1D1F]"
                  }`}
                  aria-label="Thông báo"
                >
                  <Bell className="w-[18px] h-[18px]" />
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-[8px] h-[8px] bg-[#0071E3] rounded-full" />
                  )}
                </button>

                {showNotifications && (
                  <div className="absolute right-0 mt-4 w-[360px] bg-white border border-[#D2D2D7] z-[200] rounded-[18px] shadow-2xl p-4">
                    <div className="flex items-center justify-between mb-4 px-2">
                      <span className="text-[13px] font-semibold text-[#1D1D1F]">Thông báo</span>
                      {unreadCount > 0 && (
                        <span className="text-[12px] text-[#0071E3] font-medium">
                          {unreadCount} mới
                        </span>
                      )}
                    </div>
                    <div className="max-h-[360px] overflow-y-auto">
                      {notifications.length > 0 ? (
                        <div className="space-y-1">
                          {notifications.slice(0, 8).map((notif: any) => (
                            <div
                              key={notif._id}
                              className={`px-3 py-3 rounded-[10px] cursor-pointer transition-colors hover:bg-[#F5F5F7] ${
                                !notif.is_read ? "bg-[#F5F5F7]" : "bg-white"
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
                                    className={`text-[13px] leading-snug ${
                                      notif.is_read ? "text-[#6E6E73]" : "text-[#1D1D1F] font-medium"
                                    }`}
                                  >
                                    {notif.message}
                                  </p>
                                  <span className="text-[11px] text-[#6E6E73] mt-1 block">
                                    {new Date(notif.created_at).toLocaleDateString("vi-VN")}
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="py-8 text-center">
                          <p className="text-[13px] text-[#6E6E73]">Không có thông báo mới</p>
                        </div>
                      )}
                    </div>
                    <div className="pt-3 mt-2 border-t border-[#D2D2D7]">
                      <Link
                        href="/thong-bao"
                        onClick={() => setShowNotifications(false)}
                        className="block text-center text-[13px] text-[#0071E3] hover:underline"
                      >
                        Xem tất cả
                      </Link>
                    </div>
                  </div>
                )}
              </div>

              <div className="relative" ref={userMenuRef}>
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center justify-center transition-opacity hover:opacity-80"
                >
                  <div className="w-[24px] h-[24px] bg-[#F5F5F7] rounded-full overflow-hidden shrink-0 border border-[#D2D2D7]">
                    {user.avatar_url ? (
                      <img
                        src={user.avatar_url}
                        className="w-full h-full object-cover"
                        alt=""
                      />
                    ) : (
                      <div className="w-full h-full bg-[#1D1D1F]" />
                    )}
                  </div>
                </button>

                {showUserMenu && (
                  <div className="absolute right-0 mt-4 w-[240px] bg-white border border-[#D2D2D7] z-[200] p-4 rounded-[18px] shadow-2xl">
                    <div className="mb-4 px-2">
                      <p className="text-[15px] font-semibold text-[#1D1D1F]">{user.full_name || user.username}</p>
                      <p className="text-[13px] text-[#6E6E73]">{user.email}</p>
                    </div>
                    <div className="space-y-1">
                      <Link
                        href="/ho-so"
                        onClick={() => setShowUserMenu(false)}
                        className="block px-3 py-2 text-[15px] text-[#1D1D1F] hover:bg-[#F5F5F7] rounded-[10px] transition-colors"
                      >
                        Hồ sơ
                      </Link>
                      <Link
                        href="/cai-dat"
                        onClick={() => setShowUserMenu(false)}
                        className="block px-3 py-2 text-[15px] text-[#1D1D1F] hover:bg-[#F5F5F7] rounded-[10px] transition-colors"
                      >
                        Cài đặt
                      </Link>
                      <div className="h-px bg-[#D2D2D7] my-2 mx-2" />
                      <button
                        onClick={handleLogout}
                        className="block w-full text-left px-3 py-2 text-[15px] text-[#FF3B30] hover:bg-[#F5F5F7] rounded-[10px] transition-colors"
                      >
                        Đăng xuất
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center gap-4">
              <Link
                href="/dang-nhap"
                className="text-[13px] text-[#1D1D1F] hover:text-[#0071E3] transition-colors"
              >
                Đăng nhập
              </Link>
              <Link
                href="/dang-ky"
                className="text-[13px] bg-[#0071E3] text-white px-3 py-1.5 rounded-[980px] hover:bg-[#0055C6] transition-colors"
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
