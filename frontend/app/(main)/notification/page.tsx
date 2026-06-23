"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  getNotificationsAPI,
  markNotificationReadAPI,
  markAllNotificationsReadAPI,
} from "@/features/communication/services/push_notification.service";
import {
  Bell,
  Check,
  ExternalLink,
  Loader2,
  Info,
  Settings,
  Zap,
  ShieldCheck,
  CreditCard,
  MessageCircle,
  UserPlus,
  BookOpen,
  CheckCircle2,
} from "lucide-react";
import { useToast } from "@/shared/contexts/ToastContext";
import Link from "next/link";

export default function NotificationsPage() {
  const { showToast } = useToast();
  const [notifications, setNotifications] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState<"all" | "unread">("all");
  const [visible, setVisible] = useState(false);
  const [settings, setSettings] = useState({
    comments: true,
    follows: true,
    digests: true,
  });

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await getNotificationsAPI();
      setNotifications(res.data || res || []);
    } catch (err: any) {
      showToast("Không thể kết nối với trung tâm thông báo", "error");
    } finally {
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [showToast]);

  const fetchSettings = useCallback(async () => {
    // API cài đặt đã bị gỡ bỏ ở Backend
    setSettings({
      comments: true,
      follows: true,
      digests: true,
    });
  }, []);

  useEffect(() => {
    fetchData();
    fetchSettings();
  }, [fetchData, fetchSettings]);

  const handleMarkRead = async (id: string) => {
    try {
      await markNotificationReadAPI(id);
      setNotifications((prev) =>
        prev.map((n) =>
          n._id === id || n.id === id ? { ...n, is_read: true } : n,
        ),
      );
    } catch (err: any) {
      showToast("Lỗi thao tác thông báo", "error");
    }
  };

  const handleMarkAllRead = async () => {
    setIsProcessing(true);
    try {
      await markAllNotificationsReadAPI();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      showToast("Đã đánh dấu tất cả đã đọc", "success");
    } catch (err: any) {
      showToast("Không thể cập nhật trạng thái", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const updateSetting = async (key: string, value: boolean) => {
    // Không thao tác API do backend đã loại bỏ
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const filteredNotifications =
    activeTab === "unread"
      ? notifications.filter((n) => !n.is_read)
      : notifications;

  const getIcon = (type: string, is_read: boolean) => {
    const className = `w-4 h-4 ${is_read ? "text-zinc-400" : "text-black"}`;
    switch (type) {
      case "system":
        return <Zap className={className} />;
      case "security":
        return <ShieldCheck className={className} />;
      case "payment":
        return <CreditCard className={className} />;
      case "comment":
        return <MessageCircle className={className} />;
      case "follow":
        return <UserPlus className={className} />;
      case "document":
        return <BookOpen className={className} />;
      default:
        return <Bell className={className} />;
    }
  };

  const Toggle = ({
    checked,
    onChange,
  }: {
    checked: boolean;
    onChange: () => void;
  }) => (
    <button
      type="button"
      onClick={onChange}
      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-200 ease-in-out border-2 border-transparent ${
        checked ? "bg-black" : "bg-zinc-200"
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
          checked ? "translate-x-4" : "translate-x-0"
        }`}
      />
    </button>
  );

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col font-sans text-black selection:bg-black selection:text-white">
      <div className="border-b border-zinc-100 pb-4 mb-6 shrink-0 flex items-end justify-between transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1 flex items-center gap-2">
            Thông báo
          </h1>
          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Trung tâm hoạt động và tin tức mới nhất</p>
        </div>
        <button
          onClick={handleMarkAllRead}
          disabled={isProcessing || !notifications.some((n) => !n.is_read)}
          className="h-10 px-4 bg-white border border-zinc-200 text-[10px] font-bold uppercase tracking-widest rounded-xl disabled:opacity-50 transition-all hover:bg-zinc-50 hover:border-zinc-300 shadow-sm flex items-center gap-2"
        >
          {isProcessing ? (
            <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Đang xử lý</>
          ) : (
            <><CheckCircle2 className="w-3.5 h-3.5" /> Đánh dấu tất cả đã đọc</>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 flex-1 min-h-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0, transitionDelay: "100ms" }}>
        <div className="md:col-span-8 flex flex-col h-full bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm overflow-hidden">
          <div className="flex border-b border-zinc-100 bg-zinc-50/50 shrink-0 px-6 pt-4">
            <button
              onClick={() => setActiveTab("all")}
              className={`pb-3 px-2 mr-6 text-[10px] font-bold uppercase tracking-widest border-b-2 transition-colors ${
                activeTab === "all"
                  ? "border-black text-black"
                  : "border-transparent text-zinc-400 hover:text-zinc-600"
              }`}
            >
              Tất cả
            </button>
            <button
              onClick={() => setActiveTab("unread")}
              className={`pb-3 px-2 text-[10px] font-bold uppercase tracking-widest border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === "unread"
                  ? "border-black text-black"
                  : "border-transparent text-zinc-400 hover:text-zinc-600"
              }`}
            >
              Chưa đọc
              {notifications.filter((n) => !n.is_read).length > 0 && (
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500 inline-block"></span>
              )}
            </button>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {isLoading ? (
              <div className="h-full flex flex-col items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-zinc-300 mb-4" />
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Đang tải thông báo...</p>
              </div>
            ) : filteredNotifications.length > 0 ? (
              <div className="flex flex-col divide-y divide-zinc-50">
                {filteredNotifications.map((n) => (
                  <div
                    key={n._id || n.id}
                    className={`p-6 flex gap-4 transition-colors hover:bg-zinc-50/50 group relative ${
                      n.is_read ? "" : "bg-orange-50/30"
                    }`}
                  >
                    {!n.is_read && (
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-orange-500 rounded-r"></div>
                    )}
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 border transition-all ${
                      n.is_read ? "bg-zinc-50 border-zinc-100" : "bg-white border-orange-100 shadow-sm"
                    }`}>
                      {getIcon(n.type, n.is_read)}
                    </div>
                    <div className="flex-1 min-w-0 flex flex-col justify-center">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-1.5">
                        <h3
                          className={`text-sm tracking-tight truncate ${
                            n.is_read
                              ? "font-medium text-zinc-600"
                              : "font-bold text-zinc-900"
                          }`}
                        >
                          {n.title}
                        </h3>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 shrink-0">
                          {new Date(n.created_at).toLocaleString("vi-VN", {
                            hour: "2-digit",
                            minute: "2-digit",
                            day: "2-digit",
                            month: "2-digit",
                            year: "numeric",
                          })}
                        </span>
                      </div>
                      <p
                        className={`text-xs line-clamp-2 leading-relaxed ${
                          n.is_read ? "text-zinc-500" : "text-zinc-700 font-medium"
                        }`}
                      >
                        {n.message || n.body}
                      </p>

                      <div className="mt-3 flex items-center gap-4">
                        {n.link && (
                          <Link
                            href={n.link}
                            className="text-[10px] font-bold uppercase tracking-widest text-black flex items-center gap-1.5 hover:underline underline-offset-4 decoration-zinc-300"
                          >
                            <ExternalLink className="w-3 h-3" /> Xem chi tiết
                          </Link>
                        )}
                        {!n.is_read && (
                          <button
                            onClick={() => handleMarkRead(n._id || n.id)}
                            className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 flex items-center gap-1.5 hover:text-black transition-colors"
                          >
                            <Check className="w-3 h-3" /> Đánh dấu đã đọc
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
                  <Bell className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
                </div>
                <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-1">Hộp thư trống</h3>
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 max-w-sm">
                  Bạn không có thông báo nào cần xử lý lúc này.
                </p>
              </div>
            )}
          </div>
        </div>

        <aside className="md:col-span-4 space-y-6 flex flex-col shrink-0">

          <div className="bg-blue-50/50 border border-blue-100 rounded-3xl p-6 space-y-3 shadow-sm">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-blue-800 flex items-center gap-2">
              <Info className="w-4 h-4" /> Ghi chú hệ thống
            </h3>
            <p className="text-xs font-medium text-blue-600 leading-relaxed">
              Các thông báo sẽ được lưu trữ tự động trong vòng 30 ngày kể từ ngày khởi tạo 
              nhằm tối ưu hóa hiệu năng truy xuất của hệ thống lưu trữ.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
