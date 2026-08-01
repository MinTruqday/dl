"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  createBookmarkFolderAPI,
  deleteBookmarkFolderAPI,
  getBookmarkFoldersAPI,
} from "@/features/content/services/bookmark.service";
import {
  createReadingListAPI,
  getMyReadingListsAPI,
} from "@/features/content/services/library.service";
import {
  clearReadingHistoryAPI,
  deleteReadingHistoryItemAPI,
  getPinnedDocumentsAPI,
  getReadingHistoryAPI,
} from "@/features/content/services/reading.service";
import type { DocumentSummary } from "@/app/_components/DocumentResults";

export type ReadingHistoryItem = {
  document_id: string;
  document_title?: string;
  document_slug?: string;
  author_name?: string;
  cover_url?: string;
  progress_percentage?: number;
  last_read_at?: string;
};

export type BookmarkFolder = {
  _id?: string;
  id?: string;
  name?: string;
  bookmark_ids?: string[];
};
export type ReadingList = {
  _id?: string;
  id?: string;
  name?: string;
  description?: string;
  documents?: string[];
  is_public?: boolean;
};

export function useLibrary() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const [pinned, setPinned] = useState<DocumentSummary[]>([]);
  const [history, setHistory] = useState<ReadingHistoryItem[]>([]);
  const [folders, setFolders] = useState<BookmarkFolder[]>([]);
  const [lists, setLists] = useState<ReadingList[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError("");
    const results = await Promise.allSettled([
      getPinnedDocumentsAPI(),
      getReadingHistoryAPI(0, 100),
      getBookmarkFoldersAPI(),
      getMyReadingListsAPI(),
    ]);
    const values = results.map((result) =>
      result.status === "fulfilled"
        ? result.value?.data || result.value || []
        : [],
    );
    setPinned(Array.isArray(values[0]) ? values[0] : []);
    setHistory(Array.isArray(values[1]) ? values[1] : []);
    setFolders(Array.isArray(values[2]) ? values[2] : []);
    setLists(Array.isArray(values[3]) ? values[3] : []);
    if (results.some((result) => result.status === "rejected"))
      setError("Một phần thư viện chưa tải được");
    setLoading(false);
  }, [user]);

  useEffect(() => {
    if (user) load();
  }, [load, user]);

  const createFolder = async (name: string) =>
    mutate(async () => {
      await createBookmarkFolderAPI(name.trim());
    });
  const createList = async (
    name: string,
    description: string,
    isPublic: boolean,
  ) =>
    mutate(async () => {
      await createReadingListAPI({
        name: name.trim(),
        description: description.trim(),
        is_public: isPublic,
      });
    });
  const deleteFolder = async (id: string) =>
    mutate(async () => {
      await deleteBookmarkFolderAPI(id);
    });
  const clearHistory = async () =>
    mutate(async () => {
      await clearReadingHistoryAPI();
    });
  const deleteHistoryItem = async (id: string) =>
    mutate(async () => {
      await deleteReadingHistoryItemAPI(id);
    });

  async function mutate(action: () => Promise<void>) {
    if (processing) return false;
    setProcessing(true);
    setError("");
    try {
      await action();
      await load();
      return true;
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể cập nhật thư viện",
      );
      return false;
    } finally {
      setProcessing(false);
    }
  }

  return {
    pinned,
    history,
    folders,
    lists,
    loading: authLoading || loading,
    processing,
    error,
    reload: load,
    createFolder,
    createList,
    deleteFolder,
    clearHistory,
    deleteHistoryItem,
  };
}
