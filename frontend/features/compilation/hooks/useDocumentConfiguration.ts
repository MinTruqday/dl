"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ingestDocumentAPI } from "@/features/agentic_ai/services/ingestion.service";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  getCollaboratorsAPI,
  inviteCollaboratorAPI,
  removeCollaboratorAPI,
} from "@/features/collaboration/services/collaboration.service";
import {
  getFoldersAPI,
  getMyDocumentsAPI,
  transferDocumentAPI,
  updateDocumentAPI,
  updateTagsAPI,
} from "@/features/content/services/document.service";

export function useDocumentConfiguration() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const requestedDocumentId = searchParams.get("tai-lieu") || "";
  const [documents, setDocuments] = useState<any[]>([]);
  const [folders, setFolders] = useState<any[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [collaborators, setCollaborators] = useState<any[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const document = useMemo(
    () => documents.find((item) => (item._id ?? item.id) === documentId),
    [documents, documentId],
  );

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [documentResponse, folderResponse] = await Promise.all([
        getMyDocumentsAPI(),
        getFoldersAPI(),
      ]);
      const rows = documentResponse.data ?? documentResponse ?? [];
      setDocuments(rows);
      setFolders(folderResponse.data ?? folderResponse ?? []);
      setDocumentId((current) => {
        const candidate = current || requestedDocumentId;
        return rows.some((item: any) => (item._id ?? item.id) === candidate)
          ? candidate
          : "";
      });
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể tải cấu hình tài liệu",
      );
    } finally {
      setLoading(false);
    }
  }, [requestedDocumentId]);
  useEffect(() => void reload(), [reload]);

  const loadCollaborators = useCallback(async () => {
    if (!documentId) return setCollaborators([]);
    try {
      const response = await getCollaboratorsAPI(documentId);
      setCollaborators(response.data ?? response ?? []);
    } catch {
      setCollaborators([]);
    }
  }, [documentId]);
  useEffect(() => {
    setTags(document?.tags ?? []);
    void loadCollaborators();
  }, [document, documentId, loadCollaborators]);

  const run = async (
    key: string,
    task: () => Promise<unknown>,
    success: string,
    refresh = true,
  ) => {
    setProcessing(key);
    setError("");
    setNotice("");
    try {
      const result = await task();
      setNotice(success);
      if (refresh) await reload();
      return result ?? true;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể cập nhật tài liệu",
      );
      return false;
    } finally {
      setProcessing(null);
    }
  };
  const saveTags = async (next: string[]) => {
    if (
      await run(
        "tags",
        () => updateTagsAPI(documentId, next),
        "Đã cập nhật thẻ",
      )
    )
      setTags(next);
  };
  const addTag = (tag: string) => {
    const normalized = tag.trim();
    if (normalized && !tags.includes(normalized))
      void saveTags([...tags, normalized]);
  };
  const removeTag = (tag: string) =>
    void saveTags(tags.filter((item) => item !== tag));
  const moveFolder = (folderId: string) =>
    run(
      "folder",
      () => updateDocumentAPI(documentId, { folder_id: folderId || null }),
      "Đã chuyển thư mục",
    );
  const ingest = () =>
    run(
      "ingest",
      () => ingestDocumentAPI(documentId),
      "Đã bắt đầu đồng bộ dữ liệu AI",
      false,
    );
  const invite = async (email: string) => {
    const result = await run(
      "invite",
      () => inviteCollaboratorAPI(documentId, email.trim()),
      "Đã gửi lời mời",
      false,
    );
    if (result) await loadCollaborators();
    return result;
  };
  const removeCollaborator = async (id: string) => {
    const result = await run(
      "collaborator",
      () => removeCollaboratorAPI(id),
      "Đã thu hồi quyền cộng tác",
      false,
    );
    if (result) await loadCollaborators();
  };
  const transfer = (userId: string) =>
    run(
      "transfer",
      () => transferDocumentAPI(documentId, userId.trim()),
      "Đã chuyển quyền sở hữu",
    );
  return {
    documents,
    folders,
    documentId,
    setDocumentId,
    document,
    collaborators,
    tags,
    loading,
    processing,
    error,
    notice,
    clearNotice: () => setNotice(""),
    reload,
    addTag,
    removeTag,
    moveFolder,
    ingest,
    invite,
    removeCollaborator,
    transfer,
  };
}
