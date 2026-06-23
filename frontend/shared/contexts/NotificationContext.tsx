"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import {
  API_URL,
  getToken,
} from "@/features/auth/services/user_authentication.service";
import {
  getNotificationsAPI,
  markNotificationReadAPI,
} from "@/features/messaging/services/push_notification.service";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "./ToastContext";

interface NotificationItem {
  _id: string;
  message: string;
  is_read: boolean;
  link?: string;
  created_at: string;
}

interface NotificationProps {
  notifications: NotificationItem[];
  unreadCount: number;
  fetchNotifications: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
}

const NotificationContext = createContext<NotificationProps | undefined>(undefined);

export function NotificationProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  const fetchNotifications = useCallback(async () => {
    if (!user) return;
    try {
      const data = await getNotificationsAPI();
      let arr = data.data || data || [];
      if (!Array.isArray(arr)) arr = [];
      setNotifications(arr);
    } catch (e) {
      console.error(e);
    }
  }, [user]);

  const markAsRead = useCallback(async (id: string) => {
    try {
      await markNotificationReadAPI(id);
      setNotifications((prev) =>
        prev.map((n) => (n._id === id ? { ...n, is_read: true } : n)),
      );
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    if (!user) {
      setNotifications([]);
      return;
    }

    fetchNotifications();

    const token = getToken();
    if (!token) return;

    const eventSource = new EventSource(
      `${API_URL}/thong-bao/dong-du-lieu?token=${token}`,
    );

    eventSource.onmessage = (event) => {
      try {
        const newNotif = JSON.parse(event.data);
        setNotifications((prev) => [newNotif, ...prev]);
        showToast(
          newNotif.message || newNotif.body || "Bạn có thông báo mới",
          "info",
        );
      } catch (e) {
        console.error(e);
      }
    };

    eventSource.onerror = (e) => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [user, fetchNotifications, showToast]);

  const unreadCount = Array.isArray(notifications) ? notifications.filter((n) => !n.is_read).length : 0;

  return (
    <NotificationContext.Provider
      value={{ notifications, unreadCount, fetchNotifications, markAsRead }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error(
      "useNotifications must be used within a NotificationProvider",
    );
  }
  return context;
}
