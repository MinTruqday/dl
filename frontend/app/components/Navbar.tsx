"use client";
import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { removeToken } from "@/app/lib/api";
import { useRouter } from "next/navigation";
import { Bell, User, Menu, LogOut, ChevronDown, Search, X, Moon, Sun, Monitor } from "lucide-react";
import { semanticSearchAPI } from "@/app/lib/api";
import AiChatPanel from "./AiChatPanel";
import { useAuth } from "@/app/contexts/AuthContext";
import { useTheme } from "@/app/contexts/ThemeContext";

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export default function Navbar({ onToggleSidebar }: NavbarProps) {
  const { user } = useAuth() as any;
  const { theme, setTheme } = useTheme();
  const [notifications, setNotifications] = useState<any[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (user) {
      fetchNotifications();
    }
  }, [user]);

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

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem("doclib_token") || localStorage.getItem("token");
      if (!token) return;
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/notifications`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setNotifications(await res.json());
    } catch(e) { console.error(e); }
  };

  const markAsRead = async (id: string) => {
    try {
      const token = localStorage.getItem("doclib_token") || localStorage.getItem("token");
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/notifications/${id}/read`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotifications((prev) =>
        prev.map((n) => (n._id === id ? { ...n, is_read: true } : n))
      );
    } catch(e) { console.error(e); }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const handleLogout = () => {
    removeToken();
    router.push("/login");
  };

  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || !user) return;
    setIsSearching(true);
    try {
      const results = await semanticSearchAPI(searchQuery);

      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <>
      <nav
        className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200"
        style={{ height: "var(--navbar-height)" }}
      >
        <div className="h-full flex items-center justify-between px-4 max-w-[1400px] mx-auto w-full">
          <div className="flex items-center gap-3">
            {onToggleSidebar && (
              <button
                onClick={onToggleSidebar}
                className="p-2  text-gray-500 hover:bg-gray-100 hover:text-gray-900 transition-colors"
                aria-label="Toggle sidebar"
              >
                <Menu className="w-[18px] h-[18px]" />
              </button>
            )}
            <Link
              href="/"
              className="text-xl font-bold tracking-tight text-gray-900 font-sans leading-none mr-4"
            >
              DocLib
            </Link>
          </div>


          {user && (
            <form onSubmit={handleSearch} className="flex-1 max-w-md hidden md:block group">
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 group-focus-within:text-black transition-colors" />
                <input 
                   type="text" 
                   placeholder="Tìm kiếm tri thức" 
                   value={searchQuery}
                   onChange={(e) => setSearchQuery(e.target.value)}
                   className="w-full bg-zinc-50 border border-zinc-100 rounded-none pl-11 pr-4 py-2.5 text-sm focus:bg-white focus:border-zinc-300 focus:ring-4 focus:ring-zinc-100 focus:outline-none transition-all font-medium"
                />
                {searchQuery && (
                   <button type="button" onClick={() => setSearchQuery("")} className="absolute right-3.5 top-1/2 -translate-y-1/2">
                      <X className="w-3.5 h-3.5 text-zinc-400 hover:text-black" />
                   </button>
                )}
              </div>
            </form>
          )}

          <div className="flex items-center gap-1">
            {user ? (
              <>
                <div className="relative" ref={notifRef}>
                  <button
                    onClick={() => setShowNotifications(!showNotifications)}
                    className={`relative p-2.5 text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900 transition-all rounded-none ${showNotifications ? 'bg-zinc-50 text-zinc-900' : ''}`}
                    aria-label="Thông báo"
                  >
                    <Bell className="w-[18px] h-[18px]" />
                    {unreadCount > 0 && (
                      <span className="absolute top-2 right-2 w-2 h-2 bg-black rounded-none border-2 border-white" />
                    )}
                  </button>

                  {showNotifications && (
                    <div className="absolute right-0 mt-2 w-80 bg-white rounded-none border border-zinc-100 overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                      <div className="px-5 py-4 border-b border-zinc-50 flex items-center justify-between bg-zinc-50/50">
                        <span className="text-sm font-bold text-zinc-900 font-sans">
                          Thông báo
                        </span>
                        {unreadCount > 0 && (
                          <span className="px-2 py-0.5 bg-zinc-900 text-white text-[9px] font-black  rounded-none">
                            {unreadCount} mới
                          </span>
                        )}
                      </div>
                      <div className="max-h-80 overflow-y-auto">
                        {notifications.length > 0 ? (
                          <div className="divide-y divide-zinc-50">
                            {notifications.slice(0, 5).map((notif: any) => (
                              <div
                                key={notif._id}
                                className={`px-5 py-4 cursor-pointer transition-colors hover:bg-zinc-50 ${
                                  !notif.is_read ? "bg-zinc-50/40" : ""
                                }`}
                                onClick={() => {
                                  if (!notif.is_read) markAsRead(notif._id);
                                  if (notif.link) router.push(notif.link);
                                  setShowNotifications(false);
                                }}
                              >
                                <div className="flex gap-3 items-start">
                                  {!notif.is_read && (
                                    <span className="mt-1.5 w-1.5 h-1.5 rounded-none bg-black shrink-0" />
                                  )}
                                  <div className={!notif.is_read ? "" : "pl-4"}>
                                    <p className="text-sm text-zinc-800 leading-relaxed font-medium">
                                      {notif.message}
                                    </p>
                                    <span className="text-[10px] text-zinc-400 mt-1.5 block font-bold  tracking-tight">
                                      {new Date(notif.created_at).toLocaleDateString("vi-VN")}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="py-12 text-center">
                            <Bell className="w-8 h-8 mx-auto text-zinc-100 mb-3" />
                            <p className="text-xs font-bold text-zinc-400 tracking-widest">Không có thông báo</p>
                          </div>
                        )}
                      </div>
                      <Link 
                         href="/notifications" 
                         onClick={() => setShowNotifications(false)}
                         className="block py-4 text-center text-[10px] font-black  tracking-[0.2em] text-zinc-400 hover:text-black border-t border-zinc-50 bg-zinc-50/50 transition-all hover:bg-zinc-100"
                      >
                         Xem tất cả
                      </Link>
                    </div>
                  )}
                </div>

                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-none text-zinc-700 hover:bg-zinc-50 transition-all ${showUserMenu ? 'bg-zinc-50' : ''}`}
                  >
                    <div className="w-8 h-8 rounded-none bg-black flex items-center justify-center relative border border-white/10">
                      <User className="w-4 h-4 text-white" />
                      {user.role === 'AUTHOR' && (
                         <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-white border border-black rounded-none flex items-center justify-center">
                            <span className="text-[7px] font-black">V</span>
                         </div>
                      )}
                    </div>
                    <span className="text-xs font-black  tracking-widest text-zinc-900 hidden sm:block max-w-[120px] truncate">
                      {user.display_name || user.full_name}
                    </span>
                    <ChevronDown className={`w-3 h-3 text-zinc-400 hidden sm:block transition-transform duration-200 ${showUserMenu ? 'rotate-180' : ''}`} />
                  </button>

                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-60 bg-white rounded-none border border-zinc-100 overflow-hidden z-50 py-2 animate-in fade-in slide-in-from-top-2 duration-200">
                      <div className="px-5 py-4 border-b border-zinc-50 mb-2 bg-zinc-50/30">
                         <p className="text-[9px] font-black  tracking-widest text-zinc-400 mb-1">Tài khoản tri thức</p>
                         <p className="text-sm font-bold truncate text-zinc-900">{user.email}</p>
                      </div>
                      <Link
                        href="/profile"
                        onClick={() => setShowUserMenu(false)}
                        className="flex items-center gap-3 px-5 py-3 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors font-semibold"
                      >
                        <User className="w-4 h-4 text-zinc-400" />
                        Hồ sơ cá nhân
                      </Link>
                      <Link
                        href="/settings"
                        onClick={() => setShowUserMenu(false)}
                        className="flex items-center gap-3 px-5 py-3 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors font-semibold"
                      >
                        <Monitor className="w-4 h-4 text-zinc-400" />
                        Cài đặt
                      </Link>
                      <div className="border-t border-zinc-50 my-2" />
                      <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 px-5 py-3 text-sm text-black hover:bg-zinc-50 transition-colors w-full text-left font-bold"
                      >
                        <LogOut className="w-4 h-4 text-zinc-400" />
                        Đăng xuất tài khoản
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="px-4 py-2 text-sm font-bold text-zinc-600 hover:text-zinc-900 transition-colors"
                >
                  Đăng nhập
                </Link>
                <Link
                  href="/register"
                  className="px-5 py-2.5 text-sm font-bold text-white bg-zinc-900 rounded-none hover:bg-zinc-800 transition-all"
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