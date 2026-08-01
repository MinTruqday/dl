"use client";

import { useCallback, useEffect, useState } from "react";
import {
  StorageItem,
  StorageSearchFilters,
  advancedSearchStorageItemsAPI,
  createFolderAPI,
  createProtectedShareLinkAPI,
  deleteStorageItemAPI,
  downloadZipAPI,
  getRecentStorageItemsAPI,
  getStarredItemsAPI,
  getStorageQuotaAPI,
  listStorageItemsAPI,
  moveToTrashAPI,
  restoreFromTrashAPI,
  searchStorageItemsAPI,
  shareStorageItemAPI,
  toggleStarItemAPI,
  updateStorageItemAPI,
  uploadFileVersionAPI,
  uploadStorageFileAPI,
} from "@/features/cloud/services/storage.service";

export type { StorageItem } from "@/features/cloud/services/storage.service";

export type StorageView = "files" | "recent" | "starred" | "trash";
export function useStorage() {
  const [items, setItems] = useState<StorageItem[]>([]);
  const [path, setPath] = useState<StorageItem[]>([]);
  const [view, setView] = useState<StorageView>("files");
  const [query, setQuery] = useState("");
  const [quota, setQuota] = useState({ used: 0, limit: 0 });
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const folderId = path.at(-1)?._id;
  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [rows, quotaValue] = await Promise.all([
        query.trim()
          ? searchStorageItemsAPI(query.trim())
          : view === "recent"
            ? getRecentStorageItemsAPI(50)
            : view === "starred"
              ? getStarredItemsAPI()
              : listStorageItemsAPI(
                  view === "files" ? folderId : undefined,
                  view === "trash",
                ),
        getStorageQuotaAPI(),
      ]);
      setItems(rows);
      setQuota(quotaValue);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể tải kho lưu trữ",
      );
    } finally {
      setLoading(false);
    }
  }, [query, view, folderId]);
  useEffect(() => void reload(), [reload]);
  const run = async (
    key: string,
    task: () => Promise<unknown>,
    success: string,
  ) => {
    setProcessing(key);
    setError("");
    try {
      await task();
      setNotice(success);
      await reload();
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể hoàn tất thao tác",
      );
      return false;
    } finally {
      setProcessing(null);
    }
  };
  const createFolder = (name: string) =>
    run(
      "folder",
      () => createFolderAPI(name.trim(), folderId),
      "Thư mục đã được tạo",
    );
  const upload = async (files: FileList | File[]) =>
    run(
      "upload",
      async () => {
        for (const file of Array.from(files))
          await uploadStorageFileAPI(file, folderId);
      },
      "Tệp đã được tải lên",
    );
  const rename = (item: StorageItem, name: string) =>
    run(
      "rename",
      () => updateStorageItemAPI(item._id, { name: name.trim() }),
      "Đã đổi tên",
    );
  const share = (item: StorageItem, email: string, role: string) =>
    run(
      "share",
      () => shareStorageItemAPI(item._id, email.trim(), role),
      "Đã cấp quyền truy cập",
    );
  const createProtectedLink = (
    item: StorageItem,
    password: string,
    expiresInHours: number,
  ) =>
    createProtectedShareLinkAPI(
      item._id,
      password.trim() || undefined,
      expiresInHours,
    );
  const uploadVersion = (item: StorageItem, file: File) =>
    run(
      "version",
      () => uploadFileVersionAPI(item._id, file),
      "Đã tải lên phiên bản mới",
    );
  const toggleStar = (item: StorageItem) =>
    run("star", () => toggleStarItemAPI(item._id), "Đã cập nhật dấu sao");
  const remove = (item: StorageItem) =>
    run(
      "delete",
      () =>
        view === "trash"
          ? deleteStorageItemAPI(item._id, true)
          : moveToTrashAPI(item._id),
      view === "trash" ? "Đã xóa vĩnh viễn" : "Đã chuyển vào thùng rác",
    );
  const restore = (item: StorageItem) =>
    run("restore", () => restoreFromTrashAPI(item._id), "Đã khôi phục mục");
  const advancedSearch = async (filters: StorageSearchFilters) => {
    setLoading(true);
    setError("");
    try {
      setItems(await advancedSearchStorageItemsAPI(filters));
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể tìm kiếm tệp",
      );
      return false;
    } finally {
      setLoading(false);
    }
  };
  const downloadSelected = (ids: string[]) =>
    run("download", () => downloadZipAPI(ids), "Đã tạo tệp tải xuống");
  return {
    items,
    path,
    setPath,
    view,
    setView,
    query,
    setQuery,
    quota,
    loading,
    processing,
    error,
    notice,
    clearNotice: () => setNotice(""),
    reload,
    createFolder,
    upload,
    rename,
    share,
    createProtectedLink,
    uploadVersion,
    toggleStar,
    remove,
    restore,
    advancedSearch,
    downloadSelected,
  };
}
