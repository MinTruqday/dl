"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { uploadDocumentAPI } from "@/features/cloud/services/upload.service";
import {
  createDocumentAPI,
  createFolderAPI,
  deleteAdminDocumentAPI,
  deleteAuthorDocumentAPI,
  deleteFolderAPI,
  getDocumentsAPI,
  getFoldersAPI,
  getMyDocumentsAPI,
  importDocumentAPI,
  lockDocumentAPI,
  toggleStarDocumentAPI,
  updateDocumentAPI,
} from "@/features/content/services/document.service";

export type FolderRecord = {
  _id?: string;
  id?: string;
  name: string;
  parent_id?: string | null;
};

export function useDocuments() {
  const { user, isLoading: authLoading } = useAuth();
  const [documents, setDocuments] = useState<any[]>([]);
  const [folders, setFolders] = useState<FolderRecord[]>([]);
  const [folderPath, setFolderPath] = useState<FolderRecord[]>([]);
  const [query, setQuery] = useState("");
  const [starred, setStarred] = useState(false);
  const [format, setFormat] = useState("all");
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const currentFolder = folderPath.at(-1);
  const folderId = currentFolder?._id ?? currentFolder?.id;
  const isAdmin = user?.role === "admin";

  const reload = useCallback(async () => {
    if (!user) return setLoading(false);
    setLoading(true);
    setError("");
    try {
      const [documentResponse, folderResponse] = await Promise.all([
        isAdmin
          ? getDocumentsAPI(
              query,
              undefined,
              undefined,
              undefined,
              folderId,
              starred,
              format,
              undefined,
              undefined,
              50,
            )
          : getMyDocumentsAPI(query, "", 50),
        getFoldersAPI(folderId),
      ]);
      let rows = documentResponse.data ?? documentResponse ?? [];
      if (!isAdmin)
        rows = rows.filter((item: any) =>
          folderId
            ? (item.folder_id ?? item.folder) === folderId
            : !(item.folder_id ?? item.folder),
        );
      if (starred) rows = rows.filter((item: any) => item.is_starred);
      if (format !== "all")
        rows = rows.filter((item: any) =>
          String(item.content_format ?? item.file_url ?? "")
            .toLowerCase()
            .includes(format),
        );
      setDocuments(rows);
      setFolders(folderResponse.data ?? folderResponse ?? []);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể tải tài liệu",
      );
    } finally {
      setLoading(false);
    }
  }, [user, isAdmin, query, folderId, starred, format]);
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
  const createDocument = async (input: {
    title: string;
    description: string;
    visibility: string;
    file: File;
  }) => {
    setProcessing("document");
    setError("");
    let createdId = "";
    try {
      const extension =
        input.file.name
          .split(".")
          .pop()
          ?.toLowerCase()
          .replace("md", "markdown")
          .replace("tex", "latex") || "text";
      const slugBase = input.title
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "");
      const created = await createDocumentAPI({
        title: input.title.trim(),
        description: input.description.trim(),
        slug: `${slugBase}-${Date.now().toString().slice(-6)}`,
        category: "Chưa phân loại",
        pages_count: 0,
        publisher_name: user?.full_name || "DocLib",
        visibility: input.visibility,
        file_url: "",
        content_format: extension,
        folder_id: folderId ?? null,
      });
      createdId =
        created.data?._id ?? created.data?.id ?? created._id ?? created.id;
      const uploaded = await uploadDocumentAPI(input.file);
      await updateDocumentAPI(createdId, {
        file_url: uploaded.data?.url ?? uploaded.data?.file_path,
        content_format: uploaded.data?.extension ?? extension,
      });
      setNotice("Tài liệu đã được tạo");
      await reload();
      return true;
    } catch (cause) {
      if (createdId)
        await deleteAuthorDocumentAPI(createdId).catch(() => undefined);
      setError(
        cause instanceof Error ? cause.message : "Không thể tạo tài liệu",
      );
      return false;
    } finally {
      setProcessing(null);
    }
  };
  const createFolder = (name: string) =>
    run(
      "folder",
      () => createFolderAPI(name.trim(), folderId ?? null),
      "Thư mục đã được tạo",
    );
  const importDocument = (file: File) =>
    run(
      "import",
      () => importDocumentAPI(file),
      "Tài liệu đã được nhập",
    );
  const remove = (id: string, type: "document" | "folder") =>
    run(
      "delete",
      () =>
        type === "folder"
          ? deleteFolderAPI(id)
          : isAdmin
            ? deleteAdminDocumentAPI(id)
            : deleteAuthorDocumentAPI(id),
      type === "folder"
        ? "Thư mục đã được xóa"
        : "Tài liệu đã được chuyển vào thùng rác",
    );
  const lock = (id: string, password: string) =>
    run("lock", () => lockDocumentAPI(id, password), "Tài liệu đã được bảo vệ");
  const toggleStar = (id: string) =>
    run("star", () => toggleStarDocumentAPI(id), "Đã cập nhật dấu sao");
  return {
    user,
    authLoading,
    documents,
    folders,
    folderPath,
    setFolderPath,
    query,
    setQuery,
    starred,
    setStarred,
    format,
    setFormat,
    loading,
    processing,
    error,
    notice,
    clearNotice: () => setNotice(""),
    reload,
    createDocument,
    createFolder,
    importDocument,
    remove,
    lock,
    toggleStar,
  };
}
