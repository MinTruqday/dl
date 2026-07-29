"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { getMyDocumentsAPI } from "@/features/content/services/document.service";
import {
  getCollaborationInvitesAPI,
  inviteCollaboratorAPI,
  respondToInviteAPI,
  getCollaboratorsAPI,
  removeCollaboratorAPI,
  getCollaborationActivitiesAPI,
  transferOwnershipAPI,
  pingCollaborationStatusAPI,
  getOnlineCollaboratorsAPI,
  updateCollaboratorRoleAPI,
  sendMemoAPI,
  getMemosAPI,
  updateCollabAccessAPI,
  getSentPendingInvitesAPI,
  revokeInviteAPI,
  getContributionStatsAPI,
  createSnapshotAPI,
  getSnapshotsAPI,
  acquireLockAPI,
  releaseLockAPI,
  getLockStatusAPI,
  generateInviteCodeAPI,
  joinViaInviteCodeAPI,
  createCollabTaskAPI,
  getCollabTasksAPI,
  updateCollabTaskAPI,
  addTaskCommentAPI,
  getTaskCommentsAPI,
} from "@/features/content/services/collaboration.service";
import { useRouter } from "next/navigation";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
import PageLoader from "@/shared/components/common/PageLoader";
import EmptyState from "@/shared/components/common/EmptyState";
import PageHeader from "@/shared/components/common/PageHeader";

export default function StudioCollabPage() {
  const { user, isLoading } = useAuth() as any;
  const { showToast } = useToast();
  const router = useRouter();

  const [documents, setDocuments] = useState<any[]>([]);
  const [invites, setInvites] = useState<any[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [collaboratorEmail, setCollaboratorEmail] = useState("");
  const [role, setRole] = useState("editor");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const [collaborators, setCollaborators] = useState<any[]>([]);
  const [activities, setActivities] = useState<any[]>([]);
  const [onlineCollaborators, setOnlineCollaborators] = useState<any[]>([]);
  const [memos, setMemos] = useState<any[]>([]);
  const [newMemo, setNewMemo] = useState("");
  const [accessLevel, setAccessLevel] = useState("invite_only");
  const [sentPendingInvites, setSentPendingInvites] = useState<any[]>([]);
  const [contributionStats, setContributionStats] = useState<any[]>([]);
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [newSnapshotName, setNewSnapshotName] = useState("");
  const [lockStatus, setLockStatus] = useState<any>({ is_locked: false });
  const [inviteCode, setInviteCode] = useState("");
  const [joinCodeInput, setJoinCodeInput] = useState("");
  const [tasks, setTasks] = useState<any[]>([]);
  const [newTaskDesc, setNewTaskDesc] = useState("");
  const [newTaskAssigned, setNewTaskAssigned] = useState("");

  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [activeTaskComments, setActiveTaskComments] = useState<any[]>([]);
  const [activeTaskCommentText, setActiveTaskCommentText] = useState("");

  const [transferId, setTransferId] = useState<string | null>(null);
  const [transferName, setTransferName] = useState<string>("");
  const [inviteSearch, setInviteSearch] = useState<string>("");
  const [inviteFilter, setInviteFilter] = useState<string>("all");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [docsData, invitesData] = await Promise.all([
        getMyDocumentsAPI(),
        getCollaborationInvitesAPI(),
      ]);
      setDocuments(docsData.data || docsData || []);
      setInvites(invitesData.data || invitesData || []);
    } catch (err) {
      showToast("Không thể tải tài liệu", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  const fetchCollaboratorDetails = useCallback(async () => {
    if (!selectedDocumentId) return;
    try {
      const [collabs, acts, online, mems, sent, stats, snaps, lock, tasksRes] =
        await Promise.all([
          getCollaboratorsAPI(selectedDocumentId).catch(() => []),
          getCollaborationActivitiesAPI(selectedDocumentId).catch(() => []),
          getOnlineCollaboratorsAPI(selectedDocumentId).catch(() => []),
          getMemosAPI(selectedDocumentId).catch(() => []),
          getSentPendingInvitesAPI(selectedDocumentId).catch(() => []),
          getContributionStatsAPI(selectedDocumentId).catch(() => []),
          getSnapshotsAPI(selectedDocumentId).catch(() => []),
          getLockStatusAPI(selectedDocumentId).catch(() => ({
            is_locked: false,
          })),
          getCollabTasksAPI(selectedDocumentId).catch(() => []),
        ]);
      setCollaborators(collabs.data || collabs || []);
      setActivities(acts.data || acts || []);
      setOnlineCollaborators(online.data || online || []);
      setMemos(mems.data || mems || []);
      setSentPendingInvites(sent.data || sent || []);
      setContributionStats(stats.data || stats || []);
      setSnapshots(snaps.data || snaps || []);
      setLockStatus(lock.data || lock || { is_locked: false });
      setTasks(tasksRes.data || tasksRes || []);
    } catch (err) {
      showToast("Không thể tải thông tin cộng tác", "error");
    }
  }, [selectedDocumentId, showToast]);

  const loadOnlineCollaborators = useCallback(async () => {
    if (!selectedDocumentId) return;
    try {
      const [online, lock] = await Promise.all([
        getOnlineCollaboratorsAPI(selectedDocumentId).catch(() => []),
        getLockStatusAPI(selectedDocumentId).catch(() => ({
          is_locked: false,
        })),
      ]);
      setOnlineCollaborators(online.data || online || []);
      setLockStatus(lock.data || lock || { is_locked: false });
    } catch (err) {}
  }, [selectedDocumentId]);

  useEffect(() => {
    if (!isLoading && !user) router.push("/dang-nhap");
    if (!isLoading && user) loadData();
  }, [isLoading, user, router, loadData]);

  useEffect(() => {
    if (!selectedDocumentId) {
      setCollaborators([]);
      setActivities([]);
      setOnlineCollaborators([]);
      setMemos([]);
      setSentPendingInvites([]);
      setContributionStats([]);
      setAccessLevel("invite_only");
      setSnapshots([]);
      setLockStatus({ is_locked: false });
      setInviteCode("");
      setTasks([]);
      return;
    }
    const doc = documents.find((d) => (d._id || d.id) === selectedDocumentId);
    if (doc) setAccessLevel(doc.collab_access_level || "invite_only");
    fetchCollaboratorDetails();
    pingCollaborationStatusAPI(selectedDocumentId).catch(() => {});
    const interval = setInterval(() => {
      pingCollaborationStatusAPI(selectedDocumentId).catch(() => {});
      loadOnlineCollaborators();
    }, 15000);
    return () => clearInterval(interval);
  }, [
    selectedDocumentId,
    documents,
    fetchCollaboratorDetails,
    loadOnlineCollaborators,
  ]);

  const handleInvite = async () => {
    if (!selectedDocumentId || !collaboratorEmail) return;
    setActionLoading(true);
    try {
      await inviteCollaboratorAPI(selectedDocumentId, collaboratorEmail, role);
      showToast("Đã gửi lời mời", "success");
      setCollaboratorEmail("");
      loadData();
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể gửi lời mời", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRespond = async (inviteId: string, status: string) => {
    setActionLoading(true);
    try {
      await respondToInviteAPI(inviteId, status);
      showToast(
        status === "ACCEPTED" ? "Đã chấp nhận lời mời" : "Đã từ chối lời mời",
        "success",
      );
      loadData();
      if (selectedDocumentId) fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể phản hồi lời mời", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRemoveCollaborator = async (collabId: string) => {
    setActionLoading(true);
    try {
      await removeCollaboratorAPI(collabId);
      showToast("Đã xoá cộng tác viên", "success");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể xoá cộng tác viên", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleTransferOwnership = async () => {
    if (!selectedDocumentId || !transferId) return;
    setActionLoading(true);
    try {
      await transferOwnershipAPI(selectedDocumentId, transferId);
      showToast(`Đã chuyển quyền sở hữu cho ${transferName}`, "success");
      setTransferId(null);
      setTransferName("");
      loadData();
      setSelectedDocumentId("");
    } catch (err) {
      showToast("Không thể chuyển quyền sở hữu", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateRole = async (collabId: string, newRole: string) => {
    try {
      await updateCollaboratorRoleAPI(collabId, newRole);
      showToast("Đã cập nhật vai trò", "success");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể cập nhật vai trò", "error");
    }
  };

  const handleSendMemo = async () => {
    if (!selectedDocumentId || !newMemo.trim()) return;
    try {
      await sendMemoAPI(selectedDocumentId, newMemo.trim());
      setNewMemo("");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể gửi ghi chú", "error");
    }
  };

  const handleUpdateAccessLevel = async (level: string) => {
    if (!selectedDocumentId) return;
    try {
      await updateCollabAccessAPI(selectedDocumentId, level);
      setAccessLevel(level);
      showToast("Đã cập nhật quyền truy cập", "success");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể cập nhật quyền truy cập", "error");
    }
  };

  const handleRevokeInvite = async (inviteId: string) => {
    try {
      await revokeInviteAPI(inviteId);
      showToast("Đã thu hồi lời mời", "success");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể thu hồi lời mời", "error");
    }
  };

  const handleCreateSnapshot = async () => {
    if (!selectedDocumentId || !newSnapshotName.trim()) return;
    try {
      await createSnapshotAPI(selectedDocumentId, newSnapshotName.trim());
      showToast("Đã tạo bản chụp", "success");
      setNewSnapshotName("");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể tạo bản chụp", "error");
    }
  };

  const handleAcquireLock = async () => {
    if (!selectedDocumentId) return;
    try {
      await acquireLockAPI(selectedDocumentId);
      showToast("Đã khoá phiên", "success");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể khoá phiên", "error");
    }
  };

  const handleReleaseLock = async () => {
    if (!selectedDocumentId) return;
    try {
      await releaseLockAPI(selectedDocumentId);
      showToast("Đã mở khoá phiên", "success");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể mở khoá phiên", "error");
    }
  };

  const handleGenerateCode = async () => {
    if (!selectedDocumentId) return;
    try {
      const res = await generateInviteCodeAPI(selectedDocumentId);
      setInviteCode(res.data?.invite_code || res.invite_code || "");
      showToast("Đã tạo mã mời", "success");
    } catch (err) {
      showToast("Không thể tạo mã mời", "error");
    }
  };

  const handleJoinWithCode = async () => {
    if (!joinCodeInput.trim()) return;
    try {
      await joinViaInviteCodeAPI(joinCodeInput.trim());
      showToast("Đã tham gia phiên", "success");
      setJoinCodeInput("");
      loadData();
    } catch (err) {
      showToast("Mã mời không hợp lệ", "error");
    }
  };

  const handleCreateTask = async () => {
    if (!selectedDocumentId || !newTaskDesc.trim()) return;
    try {
      await createCollabTaskAPI(
        selectedDocumentId,
        newTaskDesc.trim(),
        newTaskAssigned,
      );
      setNewTaskDesc("");
      setNewTaskAssigned("");
      fetchCollaboratorDetails();
      showToast("Đã thêm nhiệm vụ", "success");
    } catch (err) {
      showToast("Không thể thêm nhiệm vụ", "error");
    }
  };

  const handleToggleTask = async (taskId: string, currentStatus: boolean) => {
    try {
      await updateCollabTaskAPI(taskId, !currentStatus);
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể cập nhật nhiệm vụ", "error");
    }
  };

  const handleViewTaskComments = async (taskId: string) => {
    setActiveTaskId(taskId);
    setActiveTaskCommentText("");
    try {
      const cRes = await getTaskCommentsAPI(taskId);
      setActiveTaskComments(cRes.data || cRes || []);
    } catch (err) {
      showToast("Không thể tải thảo luận", "error");
    }
  };

  const handleSendTaskComment = async () => {
    if (!activeTaskId || !activeTaskCommentText.trim()) return;
    try {
      await addTaskCommentAPI(activeTaskId, activeTaskCommentText.trim());
      setActiveTaskCommentText("");
      const cRes = await getTaskCommentsAPI(activeTaskId);
      setActiveTaskComments(cRes.data || cRes || []);
    } catch (err) {
      showToast("Không thể gửi phản hồi", "error");
    }
  };

  const getOnlineStatus = (userId: string) =>
    onlineCollaborators.find((oc) => oc.user_id === userId)?.status ||
    "offline";
  const isOwnerOfSelected = () => {
    if (!selectedDocumentId || !user) return false;
    const doc = documents.find((d) => (d._id || d.id) === selectedDocumentId);
    return doc ? doc.author_id === (user._id || user.id) : false;
  };

  const filteredInvites = invites.filter((inv) => {
    const titleMatch =
      inv.document_title?.toLowerCase().includes(inviteSearch.toLowerCase()) ||
      inv.inviter_name?.toLowerCase().includes(inviteSearch.toLowerCase());
    if (inviteFilter === "all") return titleMatch;
    if (inviteFilter === "pending")
      return titleMatch && inv.status === "PENDING";
    if (inviteFilter === "accepted")
      return titleMatch && inv.status === "ACCEPTED";
    if (inviteFilter === "rejected")
      return titleMatch && inv.status === "REJECTED";
    return titleMatch;
  });

  const totalLogs = contributionStats.reduce((acc, c) => acc + c.count, 0);

  if (loading || isLoading) return <PageLoader />;

  return (
    <div className="app-page gap-6">
      <PageHeader title="Cộng tác" />
      <div className="grid min-h-0 flex-1 gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="flex min-w-0 flex-col gap-4">
          <div className="surface p-5 space-y-4">
            <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
              Gia nhập phiên
            </p>
            <div className="flex flex-col xl:flex-row items-center gap-2">
              <input
                type="text"
                placeholder=""
                value={joinCodeInput}
                onChange={(e) => setJoinCodeInput(e.target.value)}
                className="field-control w-full"
              />
              <button
                onClick={handleJoinWithCode}
                className="button-primary w-full xl:w-auto shrink-0"
              >
                Gia nhập
              </button>
            </div>
          </div>
          <div className="surface p-5 space-y-4">
            <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
              Tài liệu hoạt động
            </p>
            <div className="relative">
              <select
                value={selectedDocumentId}
                onChange={(e) => setSelectedDocumentId(e.target.value)}
                className="field-control w-full"
              >
                <option value="">Chọn tài liệu biên tập</option>
                {documents.map((doc) => (
                  <option key={doc._id || doc.id} value={doc._id || doc.id}>
                    {doc.title}
                  </option>
                ))}
              </select>
            </div>

            {selectedDocumentId && isOwnerOfSelected() && (
              <div className="space-y-3 pt-4">
                <label className="text-[13px] font-medium text-[var(--ink-muted)]">
                  Quyền truy cập
                </label>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => handleUpdateAccessLevel("invite_only")}
                    className={`flex items-center justify-center gap-2 px-4 py-3 text-[14px] font-medium rounded-[var(--radius-control)] transition-colors ${accessLevel === "invite_only" ? "bg-[var(--brand)] text-white" : "bg-white text-[var(--brand)] font-medium hover:bg-[var(--border)]"}`}
                  >
                    Chỉ người được mời
                  </button>
                  <button
                    onClick={() => handleUpdateAccessLevel("anyone_with_link")}
                    className={`flex items-center justify-center gap-2 px-4 py-3 text-[14px] font-medium rounded-[var(--radius-control)] transition-colors ${accessLevel === "anyone_with_link" ? "bg-[var(--brand)] text-white" : "bg-white text-[var(--brand)] font-medium hover:bg-[var(--border)]"}`}
                  >
                    Có link tham gia
                  </button>
                </div>
              </div>
            )}
          </div>

          {selectedDocumentId && (
            <div className="surface p-5 space-y-4">
              <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
                Khóa phiên
              </p>
              {lockStatus.is_locked ? (
                <div className="rounded-[var(--radius-control)] bg-[var(--danger-soft)] p-4 text-[14px] text-[var(--danger)]">
                  Khóa bởi:{" "}
                  <strong className="font-semibold">
                    {lockStatus.user_name}
                  </strong>
                  {lockStatus.user_id === (user._id || user.id) && (
                    <button
                      onClick={handleReleaseLock}
                      className="mt-3 w-full py-2 bg-white rounded-[var(--radius-control)] font-medium text-[var(--danger)]"
                    >
                      Nhả khóa
                    </button>
                  )}
                </div>
              ) : (
                <button
                  onClick={handleAcquireLock}
                  className="button-primary w-full"
                >
                  Yêu cầu khóa độc quyền
                </button>
              )}
            </div>
          )}

          {selectedDocumentId && (
            <div className="surface p-5 space-y-4">
              <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
                Mời cộng tác
              </p>
              <input
                type="email"
                placeholder=""
                value={collaboratorEmail}
                onChange={(e) => setCollaboratorEmail(e.target.value)}
                className="field-control w-full"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => setRole("editor")}
                  className={`flex-1 rounded-[var(--radius-control)] py-2 text-[13px] font-medium transition-colors ${role === "editor" ? "bg-[var(--brand)] text-white" : "bg-[var(--surface)] text-[var(--ink-muted)]"}`}
                >
                  Biên tập
                </button>
                <button
                  onClick={() => setRole("viewer")}
                  className={`flex-1 rounded-[var(--radius-control)] py-2 text-[13px] font-medium transition-colors ${role === "viewer" ? "bg-[var(--brand)] text-white" : "bg-[var(--surface)] text-[var(--ink-muted)]"}`}
                >
                  Người xem
                </button>
              </div>
              <button
                onClick={handleInvite}
                disabled={actionLoading || !collaboratorEmail}
                className="button-primary w-full"
              >
                {actionLoading ? "Đang gửi" : "Gửi lời mời"}
              </button>
            </div>
          )}

          {selectedDocumentId && isOwnerOfSelected() && (
            <div className="surface p-5 space-y-4">
              <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
                Mã mời nhanh
              </p>
              {inviteCode ? (
                <div className="flex items-center gap-2 bg-white p-3 rounded-[var(--radius-control)] ">
                  <span className="font-mono font-bold tracking-wider text-[14px] flex-1 text-center select-all">
                    {inviteCode}
                  </span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(inviteCode);
                      showToast("Đã sao chép mã mời", "success");
                    }}
                    className="text-[13px] font-medium text-[var(--brand)]"
                  >
                    Sao chép
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleGenerateCode}
                  className="w-full py-3 bg-white text-[14px] font-medium rounded-[var(--radius-control)] "
                >
                  Tạo mã mời
                </button>
              )}
            </div>
          )}

          {selectedDocumentId && sentPendingInvites.length > 0 && (
            <div className="surface p-5 space-y-4">
              <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
                Lời mời đã gửi (chờ)
              </p>
              <div className="space-y-3">
                {sentPendingInvites.map((sp) => (
                  <div
                    key={sp._id || sp.id}
                    className="flex justify-between items-center bg-white p-3 rounded-[var(--radius-control)]"
                  >
                    <div>
                      <p className="font-medium text-[14px]">{sp.invitee_id}</p>
                      <p className="text-[12px] text-[var(--ink-muted)]">
                        Vai trò: {sp.role}
                      </p>
                    </div>
                    <button
                      onClick={() => handleRevokeInvite(sp._id || sp.id)}
                      className="text-[13px] text-[var(--danger)]"
                    >
                      Thu hồi
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedDocumentId && (
            <div className="surface p-5 space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-[20px] font-semibold text-[var(--ink)] mb-4">
                  Cộng tác viên
                </h2>
                <span className="text-[13px] text-[var(--ink-muted)]">
                  {collaborators.length}
                </span>
              </div>
              {collaborators.length > 0 ? (
                <div className="space-y-3">
                  {collaborators.map((c) => {
                    const status = getOnlineStatus(c.user_id);
                    return (
                      <div
                        key={c.collaboration_id}
                        className="bg-white p-4 rounded-[var(--radius-workspace)]"
                      >
                        <div className="flex justify-between items-start gap-2">
                          <div className="flex items-center gap-2">
                            <span
                              className={`w-2 h-2 rounded-full ${status === "online" ? "bg-[var(--success)]" : "bg-[var(--border)]"}`}
                            />
                            <div>
                              <p className="text-[14px] font-medium text-[var(--ink)] leading-tight">
                                {c.full_name}
                              </p>
                              <p className="text-[12px] text-[var(--ink-muted)] mt-0.5">
                                {c.email}
                              </p>
                            </div>
                          </div>
                          {isOwnerOfSelected() ? (
                            <select
                              value={c.role}
                              onChange={(e) =>
                                handleUpdateRole(
                                  c.collaboration_id,
                                  e.target.value,
                                )
                              }
                              className="bg-[var(--surface-quiet)] text-[12px] px-2 py-1 rounded-[var(--radius-control)] outline-none "
                            >
                              <option value="editor">Biên tập</option>
                              <option value="viewer">Xem</option>
                            </select>
                          ) : (
                            <span className="bg-[var(--surface-quiet)] text-[12px] px-2 py-1 rounded-[var(--radius-control)] text-[var(--ink-muted)]">
                              {c.role === "editor" ? "Biên tập" : "Xem"}
                            </span>
                          )}
                        </div>
                        {isOwnerOfSelected() && (
                          <div className="flex justify-end gap-3 mt-3 pt-3">
                            <button
                              onClick={() => {
                                setTransferId(c.user_id);
                                setTransferName(c.full_name);
                              }}
                              className="text-[12px] font-medium text-[var(--brand)]"
                            >
                              Chuyển chủ
                            </button>
                            <button
                              onClick={() =>
                                handleRemoveCollaborator(c.collaboration_id)
                              }
                              className="text-[12px] font-medium text-[var(--danger)]"
                            >
                              Xóa
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <EmptyState text="Chưa có ai tham gia" compact={true} />
              )}
            </div>
          )}
        </aside>

        <main className="min-w-0 space-y-6 pb-6">
          <div className="surface p-5 space-y-6">
            <h2 className="text-[20px] font-semibold text-[var(--ink)] mb-4">
              Thư mời cộng tác
            </h2>
            {filteredInvites.length > 0 ? (
              <div className="grid gap-4">
                {filteredInvites.map((inv) => (
                  <div
                    key={inv._id || inv.id}
                    className="bg-[var(--surface-quiet)] border-[var(--border)] rounded-[var(--radius-panel)] p-5 flex flex-col md:flex-row justify-between gap-4 items-start md:items-center"
                  >
                    <div>
                      <h4 className="text-[16px] font-medium text-[var(--ink)]">
                        {inv.document_title}
                      </h4>
                      <p className="text-[13px] text-[var(--ink-muted)] mt-1">
                        Từ: {inv.inviter_name} • Vai trò:{" "}
                        {inv.role === "editor" ? "Biên tập" : "Xem"}
                      </p>
                    </div>
                    {inv.status === "PENDING" && (
                      <div className="flex gap-2">
                        <button
                          onClick={() =>
                            handleRespond(inv._id || inv.id, "REJECTED")
                          }
                          className="px-4 py-2 bg-[var(--surface-quiet)] text-[var(--ink)] text-[14px] font-medium rounded-[var(--radius-panel)]"
                        >
                          Từ chối
                        </button>
                        <button
                          onClick={() =>
                            handleRespond(inv._id || inv.id, "ACCEPTED")
                          }
                          className="px-4 py-2 bg-[var(--brand)] text-white text-[14px] font-medium rounded-[var(--radius-panel)]"
                        >
                          Chấp nhận
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-[var(--ink-muted)] text-[15px] py-10">
                Bạn chưa nhận được lời mời nào.
              </p>
            )}
          </div>

          {selectedDocumentId && (
            <>
              <div className="surface p-5 space-y-6">
                <h2 className="text-[20px] font-semibold text-[var(--ink)]">
                  Nhiệm vụ
                </h2>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder=""
                    value={newTaskDesc}
                    onChange={(e) => setNewTaskDesc(e.target.value)}
                    className="field-control flex-1"
                  />
                  <input
                    type="text"
                    placeholder=""
                    value={newTaskAssigned}
                    onChange={(e) => setNewTaskAssigned(e.target.value)}
                    className="field-control w-32"
                  />
                  <button
                    onClick={handleCreateTask}
                    className="button-primary px-6"
                  >
                    Thêm
                  </button>
                </div>
                <div className="space-y-3">
                  {tasks.map((task) => (
                    <div
                      key={task.id}
                      className="bg-[var(--surface-quiet)] p-4 rounded-[var(--radius-workspace)] flex justify-between items-start gap-4 border-[var(--border)]"
                    >
                      <div className="flex gap-3 items-start">
                        <button
                          onClick={() =>
                            handleToggleTask(task.id, task.is_done)
                          }
                          className="mt-1 flex size-5 items-center justify-center"
                          aria-label={
                            task.is_done
                              ? "Đánh dấu chưa hoàn thành"
                              : "Đánh dấu hoàn thành"
                          }
                        >
                          <span
                            className={`size-4 rounded-[4px] border ${
                              task.is_done
                                ? "border-[var(--brand)] bg-[var(--brand)]"
                                : "border-[var(--border-strong)] bg-[var(--surface)]"
                            }`}
                          />
                        </button>
                        <div>
                          <p
                            className={`text-[15px] font-medium ${task.is_done ? "line-through text-[var(--ink-muted)]" : "text-[var(--ink)]"}`}
                          >
                            {task.task_desc}
                          </p>
                          <p className="text-[12px] text-[var(--ink-muted)] mt-1">
                            Giao: {task.assigned_to} • Tạo: {task.created_by}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleViewTaskComments(task.id)}
                        className="text-[13px] font-medium text-[var(--brand)]"
                      >
                        Thảo luận
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="surface p-5 space-y-6">
                <h2 className="text-[20px] font-semibold text-[var(--ink)]">
                  Trao đổi
                </h2>
                <div className="h-64 bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] border-[var(--border)] p-4 overflow-y-auto space-y-4 no-scrollbar">
                  {memos.length > 0 ? (
                    memos.map((m) => (
                      <div
                        key={m.id}
                        className="bg-[var(--surface-quiet)] p-4 rounded-[var(--radius-workspace)] max-w-[85%] "
                      >
                        <div className="flex justify-between text-[12px] text-[var(--ink-muted)] mb-2">
                          <span className="font-semibold text-[var(--ink)]">
                            {m.sender_name}
                          </span>
                          <span>
                            {new Date(m.timestamp).toLocaleTimeString("vi-VN")}
                          </span>
                        </div>
                        <p className="text-[14px] text-[var(--ink)] leading-relaxed">
                          {m.message}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-center text-[var(--ink-muted)] text-[14px] py-10">
                      Bảng tin trống.
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder=""
                    value={newMemo}
                    onChange={(e) => setNewMemo(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendMemo()}
                    className="field-control flex-1"
                  />
                  <button onClick={handleSendMemo} className="button-primary px-6">
                    Gửi
                  </button>
                </div>
              </div>
            </>
          )}
        </main>
      </div>

      <Modal
        isOpen={!!transferId}
        onClose={() => setTransferId(null)}
      >
        <ModalHeader>
          <ModalTitle>
            Chuyển nhượng quyền sở hữu
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-[15px] text-[var(--ink-muted)]">
            Bạn muốn chuyển quyền sở hữu tài liệu cho{" "}
            <strong className="text-[var(--ink)]">{transferName}</strong>? Sau khi
            chuyển, bạn sẽ chỉ còn quyền cộng tác viên.
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setTransferId(null)}
            className="px-5 py-2 text-[var(--brand)] font-medium hover:bg-[var(--surface-quiet)] rounded-full"
          >
            Hủy
          </button>
          <button onClick={handleTransferOwnership} className="button-primary">
            Xác nhận
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!activeTaskId}
        onClose={() => setActiveTaskId(null)}
        className="max-w-xl"
      >
        <ModalHeader>
          <ModalTitle>
            Thảo luận nhiệm vụ
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="h-64 bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] border-[var(--border)] p-4 overflow-y-auto space-y-4 no-scrollbar">
            {activeTaskComments.length > 0 ? (
              activeTaskComments.map((c) => (
                <div
                  key={c.id}
                  className="bg-[var(--surface-quiet)] p-3 rounded-[var(--radius-control)]  max-w-[90%]"
                >
                  <div className="flex justify-between text-[11px] text-[var(--ink-muted)] mb-1">
                    <span className="font-semibold text-[var(--ink)]">
                      {c.sender_name}
                    </span>
                    <span>
                      {new Date(c.timestamp).toLocaleTimeString("vi-VN")}
                    </span>
                  </div>
                  <p className="text-[14px] text-[var(--ink)]">{c.comment_text}</p>
                </div>
              ))
            ) : (
              <EmptyState text="Chưa có bình luận." compact={true} />
            )}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder=""
              value={activeTaskCommentText}
              onChange={(e) => setActiveTaskCommentText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendTaskComment()}
              className="field-control flex-1"
            />
            <button
              onClick={handleSendTaskComment}
              className="button-primary px-6"
            >
              Gửi
            </button>
          </div>
        </ModalContent>
      </Modal>
    </div>
  );
}
