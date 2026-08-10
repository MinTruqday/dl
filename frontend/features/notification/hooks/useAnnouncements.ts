"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getAnnouncementsAPI,
  deleteAnnouncementAPI,
  markAllAnnouncementsReadAPI,
  markAnnouncementReadAPI,
} from "@/features/notification/services/announcement.service";

export type Announcement = {
  _id?: string;
  id?: string;
  title?: string;
  message?: string;
  body?: string;
  link?: string;
  type?: string;
  is_read?: boolean;
  created_at?: string;
};

export function useAnnouncementsPage() {
  const [items, setItems] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await getAnnouncementsAPI();
      const data = response?.data || response || [];
      setItems(Array.isArray(data) ? data : []);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể tải thông báo",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const unread = useMemo(
    () => items.filter((item) => !item.is_read).length,
    [items],
  );

  const markRead = async (id: string) => {
    setError("");
    try {
      await markAnnouncementReadAPI(id);
      setItems((current) =>
        current.map((item) =>
          (item._id || item.id) === id ? { ...item, is_read: true } : item,
        ),
      );
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể cập nhật thông báo",
      );
    }
  };

  const markAllRead = async () => {
    if (!unread || processing) return;
    setProcessing(true);
    setError("");
    try {
      await markAllAnnouncementsReadAPI();
      setItems((current) =>
        current.map((item) => ({ ...item, is_read: true })),
      );
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể cập nhật thông báo",
      );
    } finally {
      setProcessing(false);
    }
  };

  const remove = async (id: string) => {
    setProcessing(true);
    setError("");
    try {
      await deleteAnnouncementAPI(id);
      setItems((current) =>
        current.filter((item) => (item._id || item.id) !== id),
      );
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể xóa thông báo",
      );
    } finally {
      setProcessing(false);
    }
  };

  return {
    items,
    unread,
    loading,
    processing,
    error,
    reload: load,
    markRead,
    markAllRead,
    remove,
  };
}
