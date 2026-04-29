"use client";

import React, { useState, useEffect, useCallback } from "react";
import AppShell from "@/app/components/AppShell";
import { getNotificationsAPI, markNotificationAsReadAPI } from "@/app/lib/api";
import { Bell, Check, Clock, ExternalLink, Loader2, Info } from "lucide-react";
import Link from "next/link";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getNotificationsAPI();
      setNotifications(data || []);
    } catch (err: any) {
      console.error("Lỗi tải thông báo:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleMarkRead = async (id: string) => {
    try {
      await markNotificationAsReadAPI(id);
      setNotifications(notifications.map((n) => (n._id === id ? { ...n, is_read: true } : n)));
    } catch (err: any) {
      console.error("Lỗi đánh dấu thông báo:", err);
    }
  };

  const markAllRead = async () => {
    // Assuming there's an API for this or we just loop
    try {
      // API call placeholder if exists: await markAllNotificationsAsReadAPI();
      setNotifications(notifications.map((n) => ({ ...n, is_read: true })));
    } catch (err: any) {
      console.error("Lỗi đánh dấu thông báo:", err);
    }
  };

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto px-6 py-12 md:py-20 animate-in fade-in duration-300 font-sans">
        <div className="mb-16 border-b border-zinc-100 pb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-4xl font-bold tracking-tighter text-black">Thông báo</h1>
            <p className="text-[11px] font-bold text-zinc-400 mt-3">Cập nhật những hoạt động mới nhất từ DocLib</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={markAllRead}
              className="text-[10px] font-bold text-zinc-400 hover:text-black hover:border-black transition-all px-6 py-3 border border-zinc-100 active:scale-95"
            >
              Đánh dấu tất cả đã đọc
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="py-32 flex justify-center">
            <Loader2 className="w-10 h-10 animate-spin text-zinc-300" />
          </div>
        ) : notifications.length > 0 ? (
          <div className="space-y-6">
            {notifications.map((n) => (
              <div
                key={n._id}
                className={`group p-8 border transition-all duration-300 flex gap-8 ${
                  n.is_read
                    ? "bg-white border-zinc-100 opacity-50"
                    : "bg-zinc-50 border-black hover:bg-white"
                }`}
              >
                <div
                  className={`w-14 h-14 flex items-center justify-center shrink-0 border ${
                    n.is_read ? "bg-white border-zinc-100 text-zinc-300" : "bg-black border-black text-white"
                  }`}
                >
                  <Bell className="w-6 h-6" />
                </div>
                <div className="flex-1 space-y-3 min-w-0">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <h3 className="text-sm font-bold tracking-tight text-black truncate">{n.title}</h3>
                    <span className="text-[10px] font-bold text-zinc-400 flex items-center gap-2 shrink-0">
                      <Clock className="w-3.5 h-3.5" />
                      {new Date(n.created_at).toLocaleString("vi-VN")}
                    </span>
                  </div>
                  <p className="text-sm text-zinc-500 leading-relaxed font-medium">{n.message}</p>

                  <div className="pt-3 flex items-center gap-6">
                    {n.link && (
                      <Link
                        href={n.link}
                        className="text-[10px] font-bold flex items-center gap-2 text-black hover:underline underline-offset-4 decoration-1"
                      >
                        <ExternalLink className="w-4 h-4" /> Xem chi tiết
                      </Link>
                    )}
                    {!n.is_read && (
                      <button
                        onClick={() => handleMarkRead(n._id)}
                        className="text-[10px] font-bold flex items-center gap-2 text-zinc-400 hover:text-black transition-colors"
                      >
                        <Check className="w-4 h-4" /> Đánh dấu đã đọc
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-40 flex flex-col items-center justify-center border border-dashed border-zinc-200 bg-zinc-50/20">
            <Info className="w-12 h-12 text-zinc-100 mb-6" />
            <p className="text-[11px] font-bold text-zinc-300">Bạn chưa có thông báo nào</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
