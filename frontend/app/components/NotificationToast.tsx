"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { getToken } from "../lib/api";
import { X } from "lucide-react";

export type NotificationType = "error" | "warning" | "success" | "info";

interface NotificationProps {
  type: NotificationType;
  message: React.ReactNode;
  title?: string;
  className?: string;
}

export function Notification({ type, message, title, className = "" }: NotificationProps) {
  const getStyles = () => {
    switch (type) {
      case "error":
        return "border-l-black bg-white text-red-600 font-bold";
      case "success":
        return "border-l-black bg-white text-green-600";
      case "warning":
        return "border-l-black bg-white text-yellow-600";
      case "info":
      default:
        return "border-l-black bg-white text-zinc-900";
    }
  };

  return (
    <div
      className={`border-l-[6px] p-4 text-sm font-semibold transition-all duration-300 font-sans ${getStyles()} ${className}`}
    >
      {title && <h4 className="font-bold text-base mb-1 tracking-tight">{title}</h4>}
      <div className="leading-relaxed font-medium">
        {typeof message === 'object' && message !== null && !React.isValidElement(message) 
          ? JSON.stringify(message) 
          : message}
      </div>
    </div>
  );
}

type StreamNotification = {
  id: string;
  title: string;
  body: string;
  type?: string;
};

export default function NotificationToast() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<StreamNotification[]>([]);

  useEffect(() => {
    if (!user) return;

    const token = getToken();
    if (!token) return;

    let eventSource: EventSource | null = null;
    let retryCount = 0;
    const MAX_RETRIES = 3;
    let retryTimeout: NodeJS.Timeout | null = null;
    let cancelled = false;
    const API_URL = process.env.NEXT_PUBLIC_API_URL;

    const connect = () => {
      if (cancelled || retryCount >= MAX_RETRIES) return;

      try {
        eventSource = new EventSource(`${API_URL}/notifications/stream?token=${token}`);

        eventSource.addEventListener("connected", () => {
          retryCount = 0;
        });

        eventSource.addEventListener("notification", (e) => {
          try {
            const data = JSON.parse(e.data);
            const newNotif = {
              id: Math.random().toString(36).substring(2, 9),
              title: data.title || "Thông báo",
              body: data.body || "",
              type: data.type || "info",
            };
            setNotifications((prev) => [...prev, newNotif]);

            setTimeout(() => {
              setNotifications((prev) => prev.filter((n) => n.id !== newNotif.id));
            }, 5000);
          } catch (err) {
            console.error("Lỗi phân tích thông báo:", err);
          }
        });

        eventSource.onerror = () => {
          if (eventSource) eventSource.close();
          eventSource = null;
          if (!cancelled && retryCount < MAX_RETRIES) {
            retryCount++;
            retryTimeout = setTimeout(connect, 30000);
          }
        };
      } catch (err) {
        console.error("Lỗi kết nối stream thông báo:", err);
      }
    };

    connect();

    return () => {
      cancelled = true;
      if (eventSource) eventSource.close();
      if (retryTimeout) clearTimeout(retryTimeout);
    };
  }, [user]);

  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-6 right-6 z-[9999] flex flex-col gap-3 max-w-md w-full sm:w-[400px] font-sans pointer-events-none">
      {notifications.map((n) => {
        let typeStyles = "text-yellow-600";
        if (n.type === "error") typeStyles = "text-red-600 font-bold";
        if (n.type === "success") typeStyles = "text-green-600";

        return (
          <div
            key={n.id}
            className={`border-l-[6px] border-l-black border border-zinc-200 p-5 text-sm font-semibold bg-white shadow-sm transition-all animate-in slide-in-from-right-8 fade-in duration-300 pointer-events-auto ${typeStyles}`}
          >
            <div className="flex justify-between items-start gap-4">
              <div className="flex-1">
                {n.title && <h4 className="font-bold text-base mb-1 tracking-tight">{n.title}</h4>}
                <p className="leading-relaxed font-bold">{n.body}</p>
              </div>
              <button
                onClick={() => setNotifications((prev) => prev.filter((x) => x.id !== n.id))}
                className="opacity-40 hover:opacity-100 transition-opacity p-1 -mt-1 -mr-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
