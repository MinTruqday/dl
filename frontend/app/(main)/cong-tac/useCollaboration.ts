"use client";

import { useCallback, useEffect, useState } from "react";
import { getMyDocumentsAPI } from "@/features/content/services/document.service";
import {
  acquireLockAPI,
  createCollabTaskAPI,
  createSnapshotAPI,
  generateInviteCodeAPI,
  getCollabTasksAPI,
  getCollaborationActivitiesAPI,
  getCollaborationInvitesAPI,
  getCollaboratorsAPI,
  getLockStatusAPI,
  getMemosAPI,
  getOnlineCollaboratorsAPI,
  getSnapshotsAPI,
  inviteCollaboratorAPI,
  joinViaInviteCodeAPI,
  pingCollaborationStatusAPI,
  releaseLockAPI,
  removeCollaboratorAPI,
  respondToInviteAPI,
  sendMemoAPI,
  updateCollabAccessAPI,
  updateCollabTaskAPI,
  updateCollaboratorRoleAPI,
} from "@/features/content/services/collaboration.service";

export function useCollaboration() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [invites, setInvites] = useState<any[]>([]);
  const [collaborators, setCollaborators] = useState<any[]>([]);
  const [online, setOnline] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [activities, setActivities] = useState<any[]>([]);
  const [memos, setMemos] = useState<any[]>([]);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [lock, setLock] = useState<any>({ is_locked: false });
  const [inviteCode, setInviteCode] = useState("");
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    Promise.all([getMyDocumentsAPI(), getCollaborationInvitesAPI()])
      .then(([documentResponse, inviteResponse]) => {
        const rows = documentResponse.data ?? documentResponse ?? [];
        setDocuments(rows);
        setDocumentId(rows[0]?._id ?? rows[0]?.id ?? "");
        setInvites(inviteResponse.data ?? inviteResponse ?? []);
      })
      .catch((cause) =>
        setError(
          cause instanceof Error
            ? cause.message
            : "Không thể tải không gian cộng tác",
        ),
      )
      .finally(() => setLoading(false));
  }, []);
  const reload = useCallback(async () => {
    if (!documentId) return;
    setLoading(true);
    setError("");
    try {
      const results = await Promise.all([
        getCollaboratorsAPI(documentId),
        getOnlineCollaboratorsAPI(documentId),
        getCollabTasksAPI(documentId),
        getCollaborationActivitiesAPI(documentId),
        getMemosAPI(documentId),
        getSnapshotsAPI(documentId),
        getLockStatusAPI(documentId),
      ]);
      const value = (result: any) => result.data ?? result ?? [];
      setCollaborators(value(results[0]));
      setOnline(value(results[1]));
      setTasks(value(results[2]));
      setActivities(value(results[3]));
      setMemos(value(results[4]));
      setSnapshots(value(results[5]));
      setLock(value(results[6]));
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể tải dữ liệu cộng tác",
      );
    } finally {
      setLoading(false);
    }
  }, [documentId]);
  useEffect(() => void reload(), [reload]);
  useEffect(() => {
    if (!documentId) return;
    void pingCollaborationStatusAPI(documentId);
    const timer = window.setInterval(
      () => void pingCollaborationStatusAPI(documentId).catch(() => undefined),
      30000,
    );
    return () => window.clearInterval(timer);
  }, [documentId]);
  const run = async (
    key: string,
    task: () => Promise<any>,
    success: string,
    refresh = true,
  ) => {
    setProcessing(key);
    setError("");
    try {
      const response = await task();
      setNotice(success);
      if (refresh) await reload();
      return response;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể hoàn tất thao tác",
      );
      return null;
    } finally {
      setProcessing(null);
    }
  };
  const invite = (email: string, role: string) =>
    run(
      "invite",
      () => inviteCollaboratorAPI(documentId, email.trim(), role),
      "Đã gửi lời mời",
    );
  const respond = async (id: string, status: string) => {
    await run(
      "respond",
      () => respondToInviteAPI(id, status),
      "Đã phản hồi lời mời",
      false,
    );
    const response = await getCollaborationInvitesAPI();
    setInvites(response.data ?? response ?? []);
  };
  const remove = (id: string) =>
    run("remove", () => removeCollaboratorAPI(id), "Đã thu hồi quyền cộng tác");
  const updateRole = (id: string, role: string) =>
    run(
      "role",
      () => updateCollaboratorRoleAPI(id, role),
      "Đã cập nhật vai trò",
    );
  const createTask = (description: string, assignedTo: string) =>
    run(
      "task",
      () =>
        createCollabTaskAPI(documentId, description.trim(), assignedTo.trim()),
      "Đã tạo công việc",
    );
  const toggleTask = (id: string, done: boolean) =>
    run("task", () => updateCollabTaskAPI(id, done), "Đã cập nhật công việc");
  const sendMemo = (message: string) =>
    run(
      "memo",
      () => sendMemoAPI(documentId, message.trim()),
      "Đã gửi ghi chú",
    );
  const snapshot = (name: string) =>
    run(
      "snapshot",
      () => createSnapshotAPI(documentId, name.trim()),
      "Đã tạo bản chụp",
    );
  const toggleLock = () =>
    run(
      "lock",
      () =>
        lock.is_locked
          ? releaseLockAPI(documentId)
          : acquireLockAPI(documentId),
      lock.is_locked ? "Đã mở khóa phiên" : "Đã khóa phiên",
    );
  const updateAccess = (level: string) =>
    run(
      "access",
      () => updateCollabAccessAPI(documentId, level),
      "Đã cập nhật quyền truy cập",
    );
  const generateCode = async () => {
    const response = await run(
      "code",
      () => generateInviteCodeAPI(documentId),
      "Đã tạo mã mời",
      false,
    );
    setInviteCode(
      response?.data?.invite_code ??
        response?.data?.code ??
        response?.invite_code ??
        response?.code ??
        "",
    );
  };
  const join = (code: string) =>
    run(
      "join",
      () => joinViaInviteCodeAPI(code.trim()),
      "Đã tham gia tài liệu",
    );
  return {
    documents,
    documentId,
    setDocumentId,
    invites,
    collaborators,
    online,
    tasks,
    activities,
    memos,
    snapshots,
    lock,
    inviteCode,
    loading,
    processing,
    error,
    notice,
    clearNotice: () => setNotice(""),
    reload,
    invite,
    respond,
    remove,
    updateRole,
    createTask,
    toggleTask,
    sendMemo,
    snapshot,
    toggleLock,
    updateAccess,
    generateCode,
    join,
  };
}
