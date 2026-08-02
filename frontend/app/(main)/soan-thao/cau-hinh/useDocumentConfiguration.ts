"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ingestDocumentAPI } from "@/features/agentic_ai/services/ingestion.service";
import {
  getCollaboratorsAPI,
  inviteCollaboratorAPI,
  removeCollaboratorAPI,
} from "@/features/content/services/collaboration.service";
import {
  getFoldersAPI,
  getDocumentDraftAPI,
  getMyDocumentsAPI,
  transferDocumentAPI,
  updateDocumentAPI,
  updateDRMSettingsAPI,
  updateTagsAPI,
} from "@/features/content/services/document.service";

export function useDocumentConfiguration() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [folders, setFolders] = useState<any[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [collaborators, setCollaborators] = useState<any[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [disableCopy, setDisableCopy] = useState(false);
  const [disablePrint, setDisablePrint] = useState(false);
  const [hideFromSearch, setHideFromSearch] = useState(false);
  const [watermarkEnabled, setWatermarkEnabled] = useState(false);
  const [allowInternalAi, setAllowInternalAi] = useState(true);
  const [licenseValidDays, setLicenseValidDays] = useState(30);
  const [maxOpenCount, setMaxOpenCount] = useState(100);
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
      setDocumentId((current) => current || rows[0]?._id || rows[0]?.id || "");
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể tải cấu hình tài liệu",
      );
    } finally {
      setLoading(false);
    }
  }, []);
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
    if (!documentId) return;
    let active = true;
    void getDocumentDraftAPI(documentId)
      .then((response) => {
        if (!active) return;
        const settings = (response.data ?? response).drm_settings ?? {};
        setDisableCopy(Boolean(settings.disable_copy));
        setDisablePrint(Boolean(settings.disable_print));
        setHideFromSearch(Boolean(settings.hide_from_search));
        setWatermarkEnabled(Boolean(settings.watermark_enabled));
        setAllowInternalAi(settings.allow_internal_ai !== false);
        setLicenseValidDays(Number(settings.license_valid_days ?? 30));
        setMaxOpenCount(Number(settings.max_open_count ?? 100));
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
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
      await task();
      setNotice(success);
      if (refresh) await reload();
      return true;
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
  const saveDrm = () =>
    run(
      "drm",
      () =>
        updateDRMSettingsAPI(documentId, {
          disable_copy: disableCopy,
          disable_print: disablePrint,
          hide_from_search: hideFromSearch,
          watermark_enabled: watermarkEnabled,
          allow_internal_ai: allowInternalAi,
          license_valid_days: Math.max(1, Math.min(365, licenseValidDays || 30)),
          max_open_count: Math.max(1, Math.min(10000, maxOpenCount || 100)),
        }),
      "Đã cập nhật bảo vệ nội dung",
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
    disableCopy,
    setDisableCopy,
    disablePrint,
    setDisablePrint,
    hideFromSearch,
    setHideFromSearch,
    watermarkEnabled,
    setWatermarkEnabled,
    allowInternalAi,
    setAllowInternalAi,
    licenseValidDays,
    setLicenseValidDays,
    maxOpenCount,
    setMaxOpenCount,
    loading,
    processing,
    error,
    notice,
    clearNotice: () => setNotice(""),
    reload,
    addTag,
    removeTag,
    moveFolder,
    saveDrm,
    ingest,
    invite,
    removeCollaborator,
    transfer,
  };
}
