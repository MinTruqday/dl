"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";

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
        return "border-[#B91C1C] text-[#B91C1C] bg-red-50/30";
      case "warning":
        return "border-[#B45309] text-[#B45309] bg-amber-50/30";
      case "success":
        return "border-[#047857] text-[#047857] bg-emerald-50/30";
      case "info":
      default:
        return "border-black text-black bg-[#F4F4F5]/50";
    }
  };

  return (
    <div className={`border-l-[6px] p-4 text-sm font-semibold transition-all duration-300 shadow-sm ${getStyles()} ${className}`}>
      {title && <h4 className="font-bold text-base mb-1 uppercase tracking-tight">{title}</h4>}
      <div className="leading-relaxed">{message}</div>
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

    const token = localStorage.getItem("doclib_token") || localStorage.getItem("token");
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
              id: Math.random().toString(),
              title: data.title || "Thông báo",
              body: data.body || "",
              type: data.type || "info"
            };
            setNotifications((prev) => [...prev, newNotif]);
            
            setTimeout(() => {
              setNotifications((prev) => prev.filter(n => n.id !== newNotif.id));
            }, 5000);
          } catch (err) {}
        });

        eventSource.onerror = () => {
          if (eventSource) eventSource.close();
          eventSource = null;
          if (!cancelled && retryCount < MAX_RETRIES) {
            retryCount++;
            retryTimeout = setTimeout(connect, 30000); // Retry after 30s
          }
        };
      } catch(err) {}
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
    <div className="fixed top-4 right-4 z-[9999] flex flex-col gap-3 max-w-md w-full sm:w-[400px]">
      {notifications.map((n: any) => {
        let typeStyles = "border-black text-black bg-white";
        if (n.type === "error") typeStyles = "border-[#B91C1C] text-[#B91C1C] bg-red-50/50";
        if (n.type === "warning") typeStyles = "border-[#B45309] text-[#B45309] bg-amber-50/50";
        if (n.type === "success") typeStyles = "border-[#047857] text-[#047857] bg-emerald-50/50";

        return (
          <div key={n.id} className={`border-l-[6px] p-5 text-sm font-semibold shadow-2xl backdrop-blur-sm transition-all animate-in slide-in-from-right-full duration-500 ${typeStyles}`}>
            <div className="flex justify-between items-start gap-4">
              <div className="flex-1">
                {n.title && <h4 className="font-bold text-base mb-1 uppercase tracking-tight">{n.title}</h4>}
                <p className="leading-relaxed">{n.body}</p>
              </div>
              <button 
                onClick={() => setNotifications(prev => prev.filter(x => x.id !== n.id))}
                className="opacity-40 hover:opacity-100 transition-opacity p-1 -mt-1 -mr-1"
              >
                <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11.7816 4.03157C12.0062 3.80702 12.0062 3.44295 11.7816 3.2184C11.5571 2.99385 11.193 2.99385 10.9685 3.2184L7.50005 6.68682L4.03164 3.2184C3.80708 2.99385 3.44301 2.99385 3.21846 3.2184C2.99391 3.44295 2.99391 3.80702 3.21846 4.03157L6.68688 7.49999L3.21846 10.9684C2.99391 11.193 2.99391 11.557 3.21846 11.7816C3.44301 12.0061 3.80708 12.0061 4.03164 11.7816L7.50005 8.31316L10.9685 11.7816C11.193 12.0061 11.5571 12.0061 11.7816 11.7816C12.0062 11.557 12.0062 11.193 11.7816 10.9684L8.31322 7.49999L11.7816 4.03157Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
                </svg>
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
