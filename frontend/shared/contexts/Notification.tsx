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
} from "@/features/auth/services/authentication.service";
import {
  getNotificationsAPI,
  markNotificationReadAPI,
} from "@/features/communication/services/notification.service";
import { useAuth } from "./Auth";
import { useToast } from "./Toast";

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

const Notification = createContext<NotificationProps | undefined>(undefined);

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
      setNotifications(data.data || data || []);
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
      `${API_URL}/notification/dong-du-lieu?token=${token}`,
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

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <Notification.Provider
      value={{ notifications, unreadCount, fetchNotifications, markAsRead }}
    >
      {children}
    </Notification.Provider>
  );
}

export function useNotifications() {
  const context = useContext(Notification);
  if (!context) {
    throw new Error(
      "useNotifications must be used within a NotificationProvider",
    );
  }
  return context;
}
