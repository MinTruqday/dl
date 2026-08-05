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
  emptyTrashAPI,
  getRecentStorageItemsAPI,
  getSharedWithMeAPI,
  getStarredItemsAPI,
  getStorageQuotaAPI,
  getTrashedItemsAPI,
  listStorageItemsAPI,
  lockStorageItemAPI,
  moveToTrashAPI,
  restoreFromTrashAPI,
  revokeInternalShareAPI,
  rollbackFileVersionAPI,
  searchStorageItemsAPI,
  setStarredAPI,
  setTagsAndColorAPI,
  shareInternalAPI,
  unlockStorageItemAPI,
  updateStorageItemAPI,
  uploadFileVersionAPI,
  uploadStorageFileAPI,
} from "@/features/cloud/services/storage.service";

export type { StorageItem } from "@/features/cloud/services/storage.service";

export type StorageView = "files" | "recent" | "starred" | "shared" | "trash";

export function useStorage() {
  const [items, setItems] = useState<StorageItem[]>([]);
  const [path, setPath] = useState<StorageItem[]>([]);
  const [view, setView] = useState<StorageView>("files");
  const [query, setQuery] = useState("");
  const [selectedTag, setSelectedTag] = useState<string>("");
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
      let rows: StorageItem[] = [];
      if (query.trim()) {
        rows = await searchStorageItemsAPI(query.trim());
      } else if (view === "recent") {
        rows = await getRecentStorageItemsAPI(50);
      } else if (view === "starred") {
        rows = await getStarredItemsAPI();
      } else if (view === "shared") {
        rows = await getSharedWithMeAPI();
      } else if (view === "trash") {
        rows = await getTrashedItemsAPI();
      } else {
        rows = await listStorageItemsAPI(folderId, false);
        if (selectedTag) {
          rows = rows.filter((item) => item.tags?.includes(selectedTag));
        }
      }

      const quotaValue = await getStorageQuotaAPI();
      setItems(rows);
      setQuota(quotaValue);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể tải kho lưu trữ"
      );
    } finally {
      setLoading(false);
    }
  }, [query, view, folderId, selectedTag]);

  useEffect(() => void reload(), [reload]);

  const run = async (
    key: string,
    task: () => Promise<unknown>,
    success: string
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
        cause instanceof Error ? cause.message : "Không thể hoàn tất thao tác"
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
      "Thư mục đã được tạo"
    );

  const upload = async (files: FileList | File[]) =>
    run(
      "upload",
      async () => {
        for (const file of Array.from(files))
          await uploadStorageFileAPI(file, folderId);
      },
      "Tệp đã được tải lên"
    );

  const rename = (item: StorageItem, name: string) =>
    run(
      "rename",
      () => updateStorageItemAPI(item._id, { name: name.trim() }),
      "Đã đổi tên"
    );

  const share = (item: StorageItem, email: string, role: string) =>
    run(
      "share",
      () => shareInternalAPI(item._id, email.trim(), role),
      "Đã cấp quyền truy cập cho người dùng"
    );

  const revokeShare = (item: StorageItem, targetUserId: string) =>
    run(
      "revokeShare",
      () => revokeInternalShareAPI(item._id, targetUserId),
      "Đã thu hồi quyền chia sẻ"
    );

  const createProtectedLink = (
    item: StorageItem,
    password: string,
    expiresInHours: number
  ) =>
    createProtectedShareLinkAPI(
      item._id,
      password.trim() || undefined,
      expiresInHours
    );

  const uploadVersion = (item: StorageItem, file: File) =>
    run(
      "version",
      () => uploadFileVersionAPI(item._id, file),
      "Đã tải lên phiên bản mới"
    );

  const rollbackVersion = (item: StorageItem, versionId: string) =>
    run(
      "rollback",
      () => rollbackFileVersionAPI(item._id, versionId),
      "Đã khôi phục phiên bản được chọn"
    );

  const toggleStar = (item: StorageItem) =>
    run(
      "star",
      () => setStarredAPI(item._id, !item.is_starred),
      item.is_starred ? "Đã gỡ dấu sao" : "Đã thêm vào mục yêu thích"
    );

  const updateTagAndColor = (
    item: StorageItem,
    tags?: string[],
    color?: string
  ) =>
    run(
      "tagColor",
      () => setTagsAndColorAPI(item._id, tags, color),
      "Đã cập nhật nhãn dán và màu sắc"
    );

  const lock = (item: StorageItem) =>
    run("lock", () => lockStorageItemAPI(item._id), "Đã khóa tệp tin");

  const unlock = (item: StorageItem) =>
    run("unlock", () => unlockStorageItemAPI(item._id), "Đã mở khóa tệp tin");

  const remove = (item: StorageItem) =>
    run(
      "delete",
      () =>
        view === "trash"
          ? deleteStorageItemAPI(item._id, true)
          : moveToTrashAPI(item._id),
      view === "trash" ? "Đã xóa vĩnh viễn" : "Đã chuyển vào thùng rác"
    );

  const restore = (item: StorageItem) =>
    run("restore", () => restoreFromTrashAPI(item._id), "Đã khôi phục mục");

  const emptyTrash = () =>
    run("emptyTrash", () => emptyTrashAPI(), "Đã dọn sạch toàn bộ thùng rác");

  const advancedSearch = async (filters: StorageSearchFilters) => {
    setLoading(true);
    setError("");
    try {
      setItems(await advancedSearchStorageItemsAPI(filters));
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể tìm kiếm tệp"
      );
      return false;
    } finally {
      setLoading(false);
    }
  };

  const downloadSelected = (ids: string[]) =>
    run("download", () => downloadZipAPI(ids), "Đã tạo tệp tải xuống ZIP");

  return {
    items,
    path,
    setPath,
    view,
    setView,
    query,
    setQuery,
    selectedTag,
    setSelectedTag,
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
    revokeShare,
    createProtectedLink,
    uploadVersion,
    rollbackVersion,
    toggleStar,
    updateTagAndColor,
    lock,
    unlock,
    remove,
    restore,
    emptyTrash,
    advancedSearch,
    downloadSelected,
  };
}
