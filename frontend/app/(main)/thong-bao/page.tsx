"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  getAnnouncementsAPI,
  markAnnouncementReadAPI,
  markAllAnnouncementsReadAPI,
} from "@/features/notification/services/announcement.service";
import {
  Bell,
  Check,
  ExternalLink,
  Loader2,
  Info,
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

export default function AnnouncementsPage() {
  const { showToast } = useToast();
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState<"all" | "unread">("all");

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await getAnnouncementsAPI();
      setAnnouncements(Array.isArray(res.data) ? res.data : Array.isArray(res) ? res : []);
    } catch (err: any) {
      showToast("Lỗi trích xuất bộ sưu tập thông báo", "error");
    } finally {
      setIsLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleMarkRead = async (id: string) => {
    try {
      await markAnnouncementReadAPI(id);
      setAnnouncements((p) =>
        p.map((n) =>
          n._id === id || n.id === id ? { ...n, is_read: true } : n,
        ),
      );
    } catch (err: any) {
      showToast("Lỗi cập nhật trạng thái thông báo", "error");
    }
  };

  const handleMarkAllRead = async () => {
    setIsProcessing(true);
    try {
      await markAllAnnouncementsReadAPI();
      setAnnouncements((p) => p.map((n) => ({ ...n, is_read: true })));
      showToast("Cập nhật trạng thái toàn bộ thông báo hoàn tất", "success");
    } catch (err: any) {
      showToast("Lỗi cập nhật trạng thái toàn bộ thông báo", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const filteredAnnouncements =
    activeTab === "unread"
      ? announcements.filter((n) => !n.is_read)
      : announcements;

  const getIcon = (type: string, is_read: boolean) => {
    const cls = `w-5 h-5 ${is_read ? "text-[#6E6E73]" : "text-[#0071E3]"}`;
    switch (type) {
      case "system":
        return <Zap className={cls} />;
      case "security":
        return <ShieldCheck className={cls} />;
      case "payment":
        return <CreditCard className={cls} />;
      case "comment":
        return <MessageCircle className={cls} />;
      case "follow":
        return <UserPlus className={cls} />;
      case "document":
        return <BookOpen className={cls} />;
      default:
        return <Bell className={cls} />;
    }
  };

  return (
    <div className="w-full h-full font-sans text-[#1D1D1F] flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-end gap-4">
        <button
          onClick={handleMarkAllRead}
          disabled={isProcessing || !announcements.some((n) => !n.is_read)}
          className="pill-button bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] flex items-center gap-2 disabled:opacity-50"
        >
          {isProcessing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <CheckCircle2 className="w-4 h-4" />
          )}{" "}
          Đánh dấu tất cả đã đọc
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 flex-1 min-h-0">
        <div className="md:col-span-8 flex flex-col h-full bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none border-[#E8E8ED] overflow-hidden">
          <div className="flex bg-[#F5F5F7]/30 md:bg-transparent px-6 md:px-0 pt-4 md:pt-6 gap-6">
            <button
              onClick={() => setActiveTab("all")}
              className={`pb-3 text-[14px] font-medium border-b-2 transition-colors ${activeTab === "all" ? "border-[#1D1D1F] text-[#1D1D1F]" : "border-transparent text-[#6E6E73] hover:text-[#1D1D1F]"}`}
            >
              Tất cả
            </button>
            <button
              onClick={() => setActiveTab("unread")}
              className={`pb-3 text-[14px] font-medium border-b-2 transition-colors flex items-center gap-1.5 ${activeTab === "unread" ? "border-[#1D1D1F] text-[#1D1D1F]" : "border-transparent text-[#6E6E73] hover:text-[#1D1D1F]"}`}
            >
              Chưa đọc{" "}
              {announcements.filter((n) => !n.is_read).length > 0 && (
                <span className="w-1.5 h-1.5 rounded-full bg-[#0071E3] inline-block"></span>
              )}
            </button>
          </div>

          <div className="flex-1 overflow-y-auto no-scrollbar">
            {isLoading ? (
              <div className="h-full flex flex-col items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" />
              </div>
            ) : filteredAnnouncements.length > 0 ? (
              <div className="flex flex-col">
                {filteredAnnouncements.map((n) => (
                  <div
                    key={n._id || n.id}
                    className={`p-6 md:px-0 flex gap-4 transition-colors hover:bg-[#F5F5F7] border-b border-[#F5F5F7] group relative ${n.is_read ? "" : "bg-[#0071E3]/5"}`}
                  >
                    {!n.is_read && (
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#0071E3]"></div>
                    )}
                    <div
                      className={`w-12 h-12 rounded-[10px] flex items-center justify-center shrink-0 transition-colors ${n.is_read ? "bg-[#F5F5F7]" : "bg-[#0071E3]/10"}`}
                    >
                      {getIcon(n.type, n.is_read)}
                    </div>
                    <div className="flex-1 min-w-0 flex flex-col justify-center">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-1">
                        <h3
                          className={`text-[17px] truncate ${n.is_read ? "font-medium text-[#1D1D1F]" : "font-medium text-[#1D1D1F]"}`}
                        >
                          {n.title}
                        </h3>
                        <span className="text-[13px] text-[#6E6E73] shrink-0">
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
                        className={`text-[14px] line-clamp-2 leading-relaxed ${n.is_read ? "text-[#6E6E73]" : "text-[#1D1D1F]"}`}
                      >
                        {n.message || n.body}
                      </p>
                      <div className="mt-3 flex items-center gap-4">
                        {n.link && (
                          <Link
                            href={n.link}
                            className="text-[13px] font-medium text-[#0071E3] flex items-center gap-1.5 hover:underline"
                          >
                            <ExternalLink className="w-3.5 h-3.5" /> Xem chi
                            tiết
                          </Link>
                        )}
                        {!n.is_read && (
                          <button
                            onClick={() => handleMarkRead(n._id || n.id)}
                            className="text-[13px] font-medium text-[#6E6E73] flex items-center gap-1.5 hover:text-[#1D1D1F] transition-colors"
                          >
                            <Check className="w-3.5 h-3.5" /> Đánh dấu đã đọc
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                <div className="w-16 h-16 bg-[#F5F5F7] flex items-center justify-center rounded-[16px] mb-4">
                  <Bell className="w-8 h-8 text-[#C7C7CC]" />
                </div>
                <p className="text-[13px] font-medium text-[#6E6E73] mb-4 mb-1">
                  Hộp thư trống
                </p>
                <p className="text-[14px] text-[#6E6E73]">
                  Bạn không có thông báo nào cần xử lý lúc này.
                </p>
              </div>
            )}
          </div>
        </div>

        <aside className="md:col-span-4 space-y-6 flex flex-col shrink-0">
          <div className="bg-[#0071E3]/5 border border-[#0071E3]/20 rounded-[18px] p-6 space-y-3">
            <h3 className="text-[17px] font-medium text-[#0071E3] flex items-center gap-2">
              <Info className="w-5 h-5" /> Ghi chú hệ thống
            </h3>
            <p className="text-[14px] text-[#0071E3]/80 leading-relaxed">
              Các thông báo sẽ được lưu trữ tự động trong vòng 30 ngày kể từ
              ngày khởi tạo nhằm tối ưu hóa hiệu năng truy xuất của hệ thống lưu
              trữ.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
