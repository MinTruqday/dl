"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";

type Notification = {
  id: string;
  title: string;
  body: string;
};

export default function NotificationToast() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    if (!user) return;

    const token = localStorage.getItem("doclib_token") || localStorage.getItem("token");
    if (!token) return;

    let eventSource: EventSource | null = null;
    const API_URL = process.env.NEXT_PUBLIC_API_URL;

    try {
      eventSource = new EventSource(`${API_URL}/notifications/stream?token=${token}`);

      eventSource.addEventListener("connected", (e) => {
      });

      eventSource.addEventListener("notification", (e) => {
        try {
          const data = JSON.parse(e.data);
          const newNotif = {
            id: Math.random().toString(),
            title: data.title || "Thông báo",
            body: data.body || "",
          };
          setNotifications((prev) => [...prev, newNotif]);
          
          setTimeout(() => {
            setNotifications((prev) => prev.filter(n => n.id !== newNotif.id));
          }, 5000);
        } catch (err) {}
      });

      eventSource.onerror = (err) => {
        console.error("SSE Error:", err);
        if (eventSource) eventSource.close();
      };
    } catch(err) {
    }

    return () => {
      if (eventSource) eventSource.close();
    };
  }, [user]);

  if (notifications.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {notifications.map((n) => (
        <div key={n.id} className="bg-black font-sans text-white p-4   opacity-90 transition-all flex flex-col min-w-[250px]">
          <h4 className="font-bold text-md mb-1">{n.title}</h4>
          <p className="text-sm">{n.body}</p>
        </div>
      ))}
    </div>
  );
}
