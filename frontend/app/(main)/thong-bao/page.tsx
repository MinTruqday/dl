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
} from "lucide-react";
import { useToast } from "@/contexts/ToastContext";
import Link from "next/link";

export default function NotificationsPage() {
  const { showToast } = useToast();
  const [notifications, setNotifications] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState<"all" | "unread">("all");
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
    }
  }, [showToast]);

  const fetchSettings = useCallback(async () => {
    try {
      const res = await getNotificationSettingsAPI();
      if (res && (res.data || res.settings)) {
        setSettings(res.data || res.settings);
      }
    } catch {
      // Silent fail
    }
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
    try {
      const newSettings = { ...settings, [key]: value };
      setSettings(newSettings);
      await updateNotificationSettingsAPI(newSettings);
    } catch {
      showToast("Không thể cập nhật cài đặt", "error");
      setSettings(settings);
    }
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

  const Toggle = ({ checked, onChange }: { checked: boolean; onChange: () => void }) => (
    <button
      type="button"
      onClick={onChange}
      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center border ${
        checked ? "bg-black border-black" : "bg-zinc-200 border-zinc-200"
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-3 w-3 transform bg-white mx-[2px] ${
          checked ? "translate-x-4" : "translate-x-0"
        }`}
      />
    </button>
  );

  return (
    <div className="min-h-screen bg-white font-sans text-black">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <header className="mb-8 border-b border-zinc-200 pb-6 flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-black">
              Thông báo
            </h1>
            <p className="text-sm text-zinc-500 mt-1">
              Trung tâm hoạt động
            </p>
          </div>
          <button
            onClick={handleMarkAllRead}
            disabled={isProcessing || !notifications.some((n) => !n.is_read)}
            className="text-sm font-medium text-zinc-500 disabled:opacity-50"
          >
            {isProcessing ? "Đang xử lý" : "Đánh dấu tất cả đã đọc"}
          </button>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          <div className="md:col-span-2">
            <div className="flex border-b border-zinc-200 mb-6">
              <button
                onClick={() => setActiveTab("all")}
                className={`pb-3 px-4 text-sm font-medium border-b-2 ${
                  activeTab === "all"
                    ? "border-black text-black"
                    : "border-transparent text-zinc-500"
                }`}
              >
                Tất cả
              </button>
              <button
                onClick={() => setActiveTab("unread")}
                className={`pb-3 px-4 text-sm font-medium border-b-2 ${
                  activeTab === "unread"
                    ? "border-black text-black"
                    : "border-transparent text-zinc-500"
                }`}
              >
                Chưa đọc
              </button>
            </div>

            {isLoading ? (
              <div className="py-32 flex justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
              </div>
            ) : filteredNotifications.length > 0 ? (
              <div className="flex flex-col">
                {filteredNotifications.map((n) => (
                  <div
                    key={n._id || n.id}
                    className={`py-5 border-b border-zinc-200 flex gap-4 ${
                      n.is_read ? "" : "border-l-2 border-l-black pl-4 ml-[-2px]"
                    }`}
                  >
                    <div className="w-10 h-10 border border-zinc-200 flex items-center justify-center shrink-0 bg-white">
                      {getIcon(n.type, n.is_read)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-1">
                        <h3
                          className={`text-sm truncate ${
                            n.is_read ? "font-normal text-zinc-600" : "font-semibold text-black"
                          }`}
                        >
                          {n.title}
                        </h3>
                        <span className="text-xs text-zinc-400 shrink-0">
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
                        className={`text-sm line-clamp-2 leading-relaxed ${
                          n.is_read ? "text-zinc-500" : "text-black"
                        }`}
                      >
                        {n.message}
                      </p>

                      <div className="mt-3 flex items-center gap-4">
                        {n.link && (
                          <Link
                            href={n.link}
                            className="text-xs font-medium text-black underline-offset-4 flex items-center gap-1"
                          >
                            <ExternalLink className="w-3 h-3" /> Chi tiết
                          </Link>
                        )}
                        {!n.is_read && (
                          <button
                            onClick={() => handleMarkRead(n._id || n.id)}
                            className="text-xs font-medium text-zinc-500 flex items-center gap-1"
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
              <div className="py-32 flex flex-col items-center justify-center border border-zinc-200 bg-white mt-2">
                <Bell className="w-8 h-8 text-zinc-300 mb-4" />
                <p className="text-sm font-medium text-black">Hộp thư trống</p>
                <p className="text-sm text-zinc-500 mt-1">
                  Bạn chưa có thông báo nào mới.
                </p>
              </div>
            )}
          </div>

          <aside className="space-y-6">
            <div className="border border-zinc-200 bg-white p-6 space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-black flex items-center gap-2 mb-1">
                  <Settings className="w-4 h-4" /> Tùy chọn thông báo
                </h3>
                <p className="text-xs text-zinc-500">
                  Quản lý các loại thông báo bạn muốn nhận
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-black">Bình luận mới</span>
                  <Toggle
                    checked={settings.comments}
                    onChange={() => updateSetting("comments", !settings.comments)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-black">Người theo dõi</span>
                  <Toggle
                    checked={settings.follows}
                    onChange={() => updateSetting("follows", !settings.follows)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-black">Bản tin tóm tắt</span>
                  <Toggle
                    checked={settings.digests}
                    onChange={() => updateSetting("digests", !settings.digests)}
                  />
                </div>
              </div>
            </div>

            <div className="border border-zinc-200 bg-zinc-50 p-6 space-y-3">
              <h3 className="text-sm font-semibold text-black flex items-center gap-2">
                <Info className="w-4 h-4" /> Ghi chú
              </h3>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Thông báo sẽ được lưu trữ trong vòng 30 ngày kể từ ngày khởi tạo
                để tối ưu hóa hiệu năng truy xuất hệ thống.
              </p>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
