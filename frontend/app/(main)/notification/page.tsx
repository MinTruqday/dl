"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  getNotificationsAPI,
  markNotificationReadAPI,
  markAllNotificationsReadAPI,
  getNotificationSettingsAPI,
  updateNotificationSettingsAPI,
} from "@/services/notification.service";
import {
  Bell,
  Check,
  Clock,
  ExternalLink,
  Loader2,
  Info,
  Settings,
  Trash2,
  Archive,
  Filter,
  CheckCheck,
  Zap,
  Sparkles,
  ShieldCheck,
  CreditCard,
  MessageCircle,
  UserPlus,
  BookOpen,
} from "lucide-react";
import { useToast } from "@/contexts/ToastContext";
import Link from "next/link";
export default function NotificationsPage() {
  const { showToast } = useToast();
  const [notifications, setNotifications] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);

  const [visible, setVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<"all" | "unread">("all");

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await getNotificationsAPI();
      setNotifications(res.data || res || []);
    } catch (err: any) {
      showToast("Không thể kết nối với trung tâm thông báo.", "error");
    } finally {
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleMarkRead = async (id: string) => {
    try {
      await markNotificationReadAPI(id);
      setNotifications((prev) =>
        prev.map((n) =>
          n._id === id || n.id === id ? { ...n, is_read: true } : n,
        ),
      );
    } catch (err: any) {
      showToast("Lỗi thao tác thông báo.", "error");
    }
  };

  const handleMarkAllRead = async () => {
    setIsProcessing(true);
    try {
      await markAllNotificationsReadAPI();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      showToast("Đã đánh dấu tất cả đã đọc.", "success");
    } catch (err: any) {
      showToast("Không thể cập nhật trạng thái toàn cục.", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const filteredNotifications =
    activeTab === "unread"
      ? notifications.filter((n) => !n.is_read)
      : notifications;

  const getIcon = (type: string) => {
    switch (type) {
      case "system":
        return <Zap className="w-5 h-5" />;
      case "security":
        return <ShieldCheck className="w-5 h-5" />;
      case "payment":
        return <CreditCard className="w-5 h-5" />;
      case "comment":
        return <MessageCircle className="w-5 h-5" />;
      case "follow":
        return <UserPlus className="w-5 h-5" />;
      case "document":
        return <BookOpen className="w-5 h-5" />;
      default:
        return <Bell className="w-5 h-5" />;
    }
  };

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">

      <header
        className="mb-12 border-b border-zinc-100 pb-10 flex flex-col md:flex-row md:items-end justify-between gap-8 "
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(10px)",
        }}
      >
        <div className="space-y-4">
          <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
            Thông báo
          </h1>
          <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
            Centralized Activity Log{" "}
            <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
          </p>
        </div>

        <div className="flex items-center gap-4">
          <nav className="flex bg-white border border-zinc-100 p-1 rounded-sm">
            <button
              onClick={() => setActiveTab("all")}
              className={`px-8 py-3 text-[10px] font-bold uppercase tracking-widest rounded-sm ${activeTab === "all" ? "bg-white text-black border border-zinc-100" : "text-zinc-400 "}`}
            >
              Tất cả
            </button>
            <button
              onClick={() => setActiveTab("unread")}
              className={`px-8 py-3 text-[10px] font-bold uppercase tracking-widest rounded-sm ${activeTab === "unread" ? "bg-white text-black border border-zinc-100" : "text-zinc-400 "}`}
            >
              Chưa đọc
            </button>
          </nav>
          <button
            onClick={handleMarkAllRead}
            disabled={isProcessing || !notifications.some((n) => !n.is_read)}
            className="h-14 px-8 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest flex items-center gap-3 active:scale-[0.98] disabled:opacity-30 rounded-sm"
          >
            {isProcessing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <CheckCheck className="w-4 h-4" />
            )}
            Đọc tất cả
          </button>
        </div>
      </header>

      <div className="grid lg:grid-cols-12 gap-12">
        <div
          className="lg:col-span-8 space-y-6 delay-150"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? "translateY(0)" : "translateY(10px)",
          }}
        >
          {isLoading ? (
            <div className="py-40 flex flex-col items-center gap-6">
              <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
              <span className="text-[11px] font-bold text-zinc-200 uppercase tracking-[0.3em]">
                Đang đồng bộ trung tâm dữ liệu
              </span>
            </div>
          ) : filteredNotifications.length > 0 ? (
            <div className="space-y-4">
              {filteredNotifications.map((n) => (
                <div
                  key={n._id || n.id}
                  className={`group p-10 border flex gap-10 rounded-sm ${
                    n.is_read
                      ? "bg-white border-zinc-50 opacity-40 grayscale "
                      : "bg-white border-black "
                  }`}
                >
                  <div
                    className={`w-16 h-16 flex items-center justify-center shrink-0 border rounded-sm ${
                      n.is_read
                        ? "bg-white border-zinc-100 text-zinc-200"
                        : "bg-black border-black text-white"
                    }`}
                  >
                    {getIcon(n.type)}
                  </div>
                  <div className="flex-1 space-y-5 min-w-0">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <h3 className="text-xl font-bold tracking-tighter text-black truncate">
                        {n.title}
                      </h3>
                      <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-3 shrink-0">
                        <Clock className="w-4 h-4" />
                        {new Date(n.created_at).toLocaleString("vi-VN")}
                      </span>
                    </div>
                    <p className="text-base text-zinc-500 leading-relaxed font-medium selection:bg-black selection:text-white">
                      {n.message}
                    </p>

                    <div className="pt-5 flex items-center gap-10 border-t border-zinc-50/50">
                      {n.link && (
                        <Link
                          href={n.link}
                          className="text-[11px] font-bold uppercase tracking-widest flex items-center gap-3 text-black underline-offset-8 decoration-1"
                        >
                          <ExternalLink className="w-4 h-4" /> Chi tiết hoạt
                          động
                        </Link>
                      )}
                      {!n.is_read && (
                        <button
                          onClick={() => handleMarkRead(n._id || n.id)}
                          className="text-[11px] font-bold uppercase tracking-widest flex items-center gap-3 text-zinc-300 transition-colors"
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
            <div className="py-40 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-white rounded-sm space-y-8">
              <div className="w-20 h-20 bg-white border border-zinc-100 flex items-center justify-center rounded-sm">
                <Bell className="w-10 h-10 text-zinc-100 stroke-[1]" />
              </div>
              <div className="text-center space-y-2">
                <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-[0.2em]">
                  Hệ thống ghi nhận trạng thái rỗng
                </p>
                <p className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest italic">
                  Bạn chưa nhận được thông báo mới nào
                </p>
              </div>
            </div>
          )}
        </div>

        <aside
          className="hidden lg:col-span-4 lg:flex flex-col gap-10 delay-300"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? "translateY(0)" : "translateY(10px)",
          }}
        >
          <div className="p-10 border border-zinc-100 space-y-10 rounded-sm">
            <div className="space-y-4">
              <div className="text-[11px] font-bold text-black uppercase tracking-[0.3em] flex items-center gap-3">
                <Settings className="w-4 h-4 text-zinc-300" /> Cấu hình truyền
                tin
              </div>
              <p className="text-[12px] font-medium text-zinc-400 leading-relaxed">
                Tùy chỉnh cách thức DocLib tương tác và gửi cảnh báo quan trọng
                đến định danh của bạn.
              </p>
            </div>

            <button
              onClick={() => (window.location.href = "/settings")}
              className="w-full h-14 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] active:scale-[0.98] flex items-center justify-center gap-4 rounded-sm"
            >
              Thiết lập thông báo
            </button>
          </div>

          <div className="p-10 bg-white border border-zinc-100 space-y-8 rounded-sm">
            <div className="flex items-center gap-3">
              <Info className="w-4 h-4 text-black" />
              <span className="text-[11px] font-bold uppercase tracking-widest text-black">
                Ghi chú vận hành
              </span>
            </div>
            <p className="text-[12px] font-medium text-zinc-400 italic leading-relaxed">
              Thông báo sẽ được lưu trữ trong vòng 30 ngày kể từ ngày khởi tạo
              để tối ưu hóa hiệu năng truy xuất hệ thống.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
