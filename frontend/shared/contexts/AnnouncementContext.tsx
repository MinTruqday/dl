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
} from "@/features/authentication/services/session.service";
import {
  getAnnouncementsAPI,
  markAnnouncementReadAPI,
} from "@/features/notification/services/announcement.service";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "./ToastContext";

interface AnnouncementItem {
  _id: string;
  message: string;
  is_read: boolean;
  link?: string;
  created_at: string;
}

interface AnnouncementProps {
  announcements: AnnouncementItem[];
  unreadCount: number;
  fetchAnnouncements: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
}

const AnnouncementContext = createContext<AnnouncementProps | undefined>(
  undefined,
);

export function AnnouncementProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [announcements, setAnnouncements] = useState<AnnouncementItem[]>([]);

  const fetchAnnouncements = useCallback(async () => {
    if (!user) return;
    try {
      const data = await getAnnouncementsAPI();
      let arr = data.data || data || [];
      if (!Array.isArray(arr)) arr = [];
      setAnnouncements(arr);
    } catch (e) {
      console.error("Error fetching global announcements:", e);
    }
  }, [user]);

  const markAsRead = useCallback(async (id: string) => {
    try {
      await markAnnouncementReadAPI(id);
      setAnnouncements((prev) =>
        prev.map((n) => (n._id === id ? { ...n, is_read: true } : n)),
      );
    } catch (e) {
      console.error("Error marking announcement as read:", e);
    }
  }, []);

  useEffect(() => {
    if (!user) {
      setAnnouncements([]);
      return;
    }

    fetchAnnouncements();

    const interval = setInterval(() => {
      fetchAnnouncements();
    }, 30000);

    return () => {
      clearInterval(interval);
    };
  }, [user, fetchAnnouncements]);

  const unreadCount = Array.isArray(announcements)
    ? announcements.filter((n) => !n.is_read).length
    : 0;

  return (
    <AnnouncementContext.Provider
      value={{ announcements, unreadCount, fetchAnnouncements, markAsRead }}
    >
      {children}
    </AnnouncementContext.Provider>
  );
}

export function useAnnouncements() {
  const context = useContext(AnnouncementContext);
  if (!context) {
    throw new Error(
      "useAnnouncements must be used within a AnnouncementProvider",
    );
  }
  return context;
}
