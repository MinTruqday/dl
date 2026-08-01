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
import {
  Users,
  Mail,
  Check,
  Loader2,
  Shield,
  Trash2,
  Activity,
  MessageSquare,
  Globe,
  Lock,
  X,
  TrendingUp,
  Camera,
  Key,
  QrCode,
  CheckSquare,
  Square,
  MessageCircle,
  FileText,
  ChevronRight,
} from "lucide-react";
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
      showToast("Không thể tải bộ sưu tập tài liệu", "error");
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
      showToast("Không thể tải cấu hình cộng tác", "error");
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
      showToast("Khởi tạo yêu cầu cấp quyền cộng tác hoàn tất", "success");
      setCollaboratorEmail("");
      loadData();
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể tạo yêu cầu cấp quyền cộng tác", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRespond = async (inviteId: string, status: string) => {
    setActionLoading(true);
    try {
      await respondToInviteAPI(inviteId, status);
      showToast(
        status === "ACCEPTED" ? "Xác thực phản hồi chấp thuận hoàn tất" : "Xác thực phản hồi từ chối hoàn tất",
        "success",
      );
      loadData();
      if (selectedDocumentId) fetchCollaboratorDetails();
    } catch (err) {
      showToast("Lỗi xác thực phản hồi yêu cầu", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRemoveCollaborator = async (collabId: string) => {
    setActionLoading(true);
    try {
      await removeCollaboratorAPI(collabId);
      showToast("Thu hồi quyền truy cập cộng tác hoàn tất", "success");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Lỗi thu hồi quyền truy cập cộng tác", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleTransferOwnership = async () => {
    if (!selectedDocumentId || !transferId) return;
    setActionLoading(true);
    try {
      await transferOwnershipAPI(selectedDocumentId, transferId);
      showToast(`Chuyển giao quyền sở hữu cho ${transferName} hoàn tất`, "success");
      setTransferId(null);
      setTransferName("");
      loadData();
      setSelectedDocumentId("");
    } catch (err) {
      showToast("Lỗi chuyển giao quyền sở hữu tài liệu", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateRole = async (collabId: string, newRole: string) => {
    try {
      await updateCollaboratorRoleAPI(collabId, newRole);
      showToast("Cập nhật phân quyền truy cập hoàn tất", "success");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể cập nhật phân quyền truy cập", "error");
    }
  };

  const handleSendMemo = async () => {
    if (!selectedDocumentId || !newMemo.trim()) return;
    try {
      await sendMemoAPI(selectedDocumentId, newMemo.trim());
      setNewMemo("");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể truyền dữ liệu ghi chú", "error");
    }
  };

  const handleUpdateAccessLevel = async (level: string) => {
    if (!selectedDocumentId) return;
    try {
      await updateCollabAccessAPI(selectedDocumentId, level);
      setAccessLevel(level);
      showToast("Cập nhật cấu hình bảo mật hoàn tất", "success");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể cập nhật cấu hình bảo mật", "error");
    }
  };

  const handleRevokeInvite = async (inviteId: string) => {
    try {
      await revokeInviteAPI(inviteId);
      showToast("Hủy bỏ yêu cầu cấp quyền hoàn tất", "success");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Lỗi hủy bỏ yêu cầu cấp quyền", "error");
    }
  };

  const handleCreateSnapshot = async () => {
    if (!selectedDocumentId || !newSnapshotName.trim()) return;
    try {
      await createSnapshotAPI(selectedDocumentId, newSnapshotName.trim());
      showToast("Khởi tạo bản sao lưu dữ liệu hoàn tất", "success");
      setNewSnapshotName("");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể tạo bản sao lưu dữ liệu", "error");
    }
  };

  const handleAcquireLock = async () => {
    if (!selectedDocumentId) return;
    try {
      await acquireLockAPI(selectedDocumentId);
      showToast("Cấp phát khóa phiên độc quyền hoàn tất", "success");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Lỗi cấp phát khóa phiên độc quyền", "error");
    }
  };

  const handleReleaseLock = async () => {
    if (!selectedDocumentId) return;
    try {
      await releaseLockAPI(selectedDocumentId);
      showToast("Giải phóng khóa phiên độc quyền hoàn tất", "success");
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Lỗi giải phóng khóa phiên độc quyền", "error");
    }
  };

  const handleGenerateCode = async () => {
    if (!selectedDocumentId) return;
    try {
      const res = await generateInviteCodeAPI(selectedDocumentId);
      setInviteCode(res.data?.invite_code || res.invite_code || "");
      showToast("Khởi tạo mã phiên truy cập hoàn tất", "success");
    } catch (err) {
      showToast("Không thể tạo mã phiên truy cập", "error");
    }
  };

  const handleJoinWithCode = async () => {
    if (!joinCodeInput.trim()) return;
    try {
      await joinViaInviteCodeAPI(joinCodeInput.trim());
      showToast("Xác thực mã phiên tham gia hoàn tất", "success");
      setJoinCodeInput("");
      loadData();
    } catch (err) {
      showToast("Lỗi xác thực mã phiên tham gia", "error");
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
      showToast("Khởi tạo bản ghi nhiệm vụ hoàn tất", "success");
    } catch (err) {
      showToast("Không thể tạo bản ghi nhiệm vụ", "error");
    }
  };

  const handleToggleTask = async (taskId: string, currentStatus: boolean) => {
    try {
      await updateCollabTaskAPI(taskId, !currentStatus);
      fetchCollaboratorDetails();
    } catch (err) {
      showToast("Không thể cập nhật trạng thái nhiệm vụ", "error");
    }
  };

  const handleViewTaskComments = async (taskId: string) => {
    setActiveTaskId(taskId);
    setActiveTaskCommentText("");
    try {
      const cRes = await getTaskCommentsAPI(taskId);
      setActiveTaskComments(cRes.data || cRes || []);
    } catch (err) {
      showToast("Không thể tải bộ sưu tập phản hồi", "error");
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
      showToast("Không thể truyền dữ liệu phản hồi", "error");
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
    <div className="w-full h-full font-sans text-ink flex flex-col gap-6">
      <div className="flex flex-col md:flex-row gap-6 flex-1 min-h-0">
        <aside className="w-full md:w-[320px] shrink-0 flex flex-col space-y-6 overflow-y-auto no-scrollbar pb-6 pr-2">
          <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-4">
            <p className="text-[13px] font-medium text-ink-muted mb-4">
              Gia nhập phiên
            </p>
            <div className="flex flex-col xl:flex-row items-center gap-2">
              <input
                type="text"
                placeholder=""
                value={joinCodeInput}
                onChange={(e) => setJoinCodeInput(e.target.value)}
                className="apple-input w-full"
              />
              <button
                onClick={handleJoinWithCode}
                className="pill-button w-full xl:w-auto shrink-0"
              >
                Gia nhập
              </button>
            </div>
          </div>
          <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-4">
            <p className="text-[13px] font-medium text-ink-muted mb-4">
              Tài liệu hoạt động
            </p>
            <div className="relative">
              <select
                value={selectedDocumentId}
                onChange={(e) => setSelectedDocumentId(e.target.value)}
                className="w-full h-[44px] bg-white  px-4 text-[15px] focus:outline-none focus:border-brand appearance-none rounded-control"
              >
                <option value="">Chọn tài liệu biên tập</option>
                {documents.map((doc) => (
                  <option key={doc._id || doc.id} value={doc._id || doc.id}>
                    {doc.title}
                  </option>
                ))}
              </select>
              <ChevronRight className="w-5 h-5 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none rotate-90 text-ink-muted" />
            </div>

            {selectedDocumentId && isOwnerOfSelected() && (
              <div className="space-y-3 pt-4">
                <label className="text-[13px] font-medium text-ink-muted">
                  Quyền truy cập
                </label>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => handleUpdateAccessLevel("invite_only")}
                    className={`flex items-center justify-center gap-2 px-4 py-3 text-[14px] font-medium rounded-control transition-colors ${accessLevel === "invite_only" ? "bg-brand text-white" : "bg-white text-brand font-medium hover:bg-border"}`}
                  >
                    Chỉ người được mời
                  </button>
                  <button
                    onClick={() => handleUpdateAccessLevel("anyone_with_link")}
                    className={`flex items-center justify-center gap-2 px-4 py-3 text-[14px] font-medium rounded-control transition-colors ${accessLevel === "anyone_with_link" ? "bg-brand text-white" : "bg-white text-brand font-medium hover:bg-border"}`}
                  >
                    Có link tham gia
                  </button>
                </div>
              </div>
            )}
          </div>

          {selectedDocumentId && (
            <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-4">
              <p className="text-[13px] font-medium text-ink-muted mb-4">
                Khóa phiên
              </p>
              {lockStatus.is_locked ? (
                <div className="p-4 bg-danger-soft text-danger text-[14px] rounded-control">
                  Khóa bởi:{" "}
                  <strong className="font-semibold">
                    {lockStatus.user_name}
                  </strong>
                  {lockStatus.user_id === (user._id || user.id) && (
                    <button
                      onClick={handleReleaseLock}
                      className="mt-3 w-full py-2 bg-white rounded-control font-medium text-danger"
                    >
                      Nhả khóa
                    </button>
                  )}
                </div>
              ) : (
                <button
                  onClick={handleAcquireLock}
                  className="w-full py-3 bg-brand text-white text-[14px] font-medium rounded-control hover:bg-brand transition-colors"
                >
                  Yêu cầu khóa độc quyền
                </button>
              )}
            </div>
          )}

          {selectedDocumentId && (
            <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-4">
              <p className="text-[13px] font-medium text-ink-muted mb-4">
                Mời cộng tác
              </p>
              <input
                type="email"
                placeholder=""
                value={collaboratorEmail}
                onChange={(e) => setCollaboratorEmail(e.target.value)}
                className="apple-input w-full"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => setRole("editor")}
                  className={`flex-1 py-2 text-[13px] font-medium rounded-control transition-colors ${role === "editor" ? "bg-ink text-white" : "bg-white text-brand font-medium"}`}
                >
                  Biên tập
                </button>
                <button
                  onClick={() => setRole("viewer")}
                  className={`flex-1 py-2 text-[13px] font-medium rounded-control transition-colors ${role === "viewer" ? "bg-ink text-white" : "bg-white text-brand font-medium"}`}
                >
                  Người xem
                </button>
              </div>
              <button
                onClick={handleInvite}
                disabled={actionLoading || !collaboratorEmail}
                className="w-full py-3 bg-brand text-white text-[14px] font-medium rounded-control disabled:opacity-50"
              >
                {actionLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                ) : (
                  "Gửi lời mời"
                )}
              </button>
            </div>
          )}

          {selectedDocumentId && isOwnerOfSelected() && (
            <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-4">
              <p className="text-[13px] font-medium text-ink-muted mb-4">
                Mã mời nhanh
              </p>
              {inviteCode ? (
                <div className="flex items-center gap-2 bg-white p-3 rounded-control ">
                  <span className="font-mono font-bold tracking-wider text-[14px] flex-1 text-center select-all">
                    {inviteCode}
                  </span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(inviteCode);
                      showToast("Sao chép mã phiên truy cập vào bộ nhớ tạm hoàn tất", "success");
                    }}
                    className="text-[13px] font-medium text-brand"
                  >
                    Copy
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleGenerateCode}
                  className="w-full py-3 bg-white text-[14px] font-medium rounded-control "
                >
                  Tạo mã mời
                </button>
              )}
            </div>
          )}

          {selectedDocumentId && sentPendingInvites.length > 0 && (
            <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-4">
              <p className="text-[13px] font-medium text-ink-muted mb-4">
                Lời mời đã gửi (chờ)
              </p>
              <div className="space-y-3">
                {sentPendingInvites.map((sp) => (
                  <div
                    key={sp._id || sp.id}
                    className="flex justify-between items-center bg-white p-3 rounded-control"
                  >
                    <div>
                      <p className="font-medium text-[14px]">{sp.invitee_id}</p>
                      <p className="text-[12px] text-ink-muted">
                        Vai trò: {sp.role}
                      </p>
                    </div>
                    <button
                      onClick={() => handleRevokeInvite(sp._id || sp.id)}
                      className="text-[13px] text-danger"
                    >
                      Thu hồi
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedDocumentId && (
            <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-[20px] font-semibold text-ink mb-4">
                  Cộng tác viên
                </h2>
                <span className="text-[13px] text-ink-muted">
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
                        className="bg-white p-4 rounded-panel"
                      >
                        <div className="flex justify-between items-start gap-2">
                          <div className="flex items-center gap-2">
                            <span
                              className={`w-2 h-2 rounded-full ${status === "online" ? "bg-brand" : "bg-border"}`}
                            />
                            <div>
                              <p className="text-[14px] font-medium text-ink leading-tight">
                                {c.full_name}
                              </p>
                              <p className="text-[12px] text-ink-muted mt-0.5">
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
                              className="bg-surface-quiet text-[12px] px-2 py-1 rounded-control outline-none "
                            >
                              <option value="editor">Biên tập</option>
                              <option value="viewer">Xem</option>
                            </select>
                          ) : (
                            <span className="bg-surface-quiet text-[12px] px-2 py-1 rounded-control text-ink-muted">
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
                              className="text-[12px] font-medium text-brand"
                            >
                              Chuyển chủ
                            </button>
                            <button
                              onClick={() =>
                                handleRemoveCollaborator(c.collaboration_id)
                              }
                              className="text-[12px] font-medium text-danger"
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

        <main className="flex-1 min-w-0 space-y-6 overflow-y-auto no-scrollbar pb-6">
          <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-6">
            <h2 className="text-[20px] font-semibold text-ink mb-4">
              Thư mời cộng tác
            </h2>
            {filteredInvites.length > 0 ? (
              <div className="grid gap-4">
                {filteredInvites.map((inv) => (
                  <div
                    key={inv._id || inv.id}
                    className="bg-surface-quiet border-border rounded-panel p-5 flex flex-col md:flex-row justify-between gap-4 items-start md:items-center"
                  >
                    <div>
                      <h4 className="text-[16px] font-medium text-ink">
                        {inv.document_title}
                      </h4>
                      <p className="text-[13px] text-ink-muted mt-1">
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
                          className="px-4 py-2 bg-surface-quiet text-ink text-[14px] font-medium rounded-panel"
                        >
                          Từ chối
                        </button>
                        <button
                          onClick={() =>
                            handleRespond(inv._id || inv.id, "ACCEPTED")
                          }
                          className="px-4 py-2 bg-brand text-white text-[14px] font-medium rounded-panel"
                        >
                          Chấp nhận
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-ink-muted text-[15px] py-10">
                Bạn chưa nhận được lời mời nào.
              </p>
            )}
          </div>

          {selectedDocumentId && (
            <>
              <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-6">
                <h2 className="text-[20px] font-semibold text-ink flex items-center gap-2">
                  <CheckSquare className="w-5 h-5" /> Nhiệm vụ & Checklist
                </h2>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder=""
                    value={newTaskDesc}
                    onChange={(e) => setNewTaskDesc(e.target.value)}
                    className="apple-input flex-1"
                  />
                  <input
                    type="text"
                    placeholder=""
                    value={newTaskAssigned}
                    onChange={(e) => setNewTaskAssigned(e.target.value)}
                    className="apple-input w-32"
                  />
                  <button
                    onClick={handleCreateTask}
                    className="pill-button px-6"
                  >
                    Thêm
                  </button>
                </div>
                <div className="space-y-3">
                  {tasks.map((task) => (
                    <div
                      key={task.id}
                      className="bg-surface-quiet p-4 rounded-panel flex justify-between items-start gap-4 border-border"
                    >
                      <div className="flex gap-3 items-start">
                        <button
                          onClick={() =>
                            handleToggleTask(task.id, task.is_done)
                          }
                          className="mt-1"
                        >
                          {task.is_done ? (
                            <CheckSquare className="w-5 h-5 text-brand" />
                          ) : (
                            <Square className="w-5 h-5 text-ink-muted" />
                          )}
                        </button>
                        <div>
                          <p
                            className={`text-[15px] font-medium ${task.is_done ? "line-through text-ink-muted" : "text-ink"}`}
                          >
                            {task.task_desc}
                          </p>
                          <p className="text-[12px] text-ink-muted mt-1">
                            Giao: {task.assigned_to} • Tạo: {task.created_by}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleViewTaskComments(task.id)}
                        className="text-[13px] font-medium text-brand"
                      >
                        Thảo luận
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-6">
                <h2 className="text-[20px] font-semibold text-ink flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" /> Bảng ghim & Trao đổi
                </h2>
                <div className="h-64 bg-surface-quiet rounded-panel border border-border p-4 overflow-y-auto space-y-4 no-scrollbar">
                  {memos.length > 0 ? (
                    memos.map((m) => (
                      <div
                        key={m.id}
                        className="bg-surface-quiet p-4 rounded-panel max-w-[85%] "
                      >
                        <div className="flex justify-between text-[12px] text-ink-muted mb-2">
                          <span className="font-semibold text-ink">
                            {m.sender_name}
                          </span>
                          <span>
                            {new Date(m.timestamp).toLocaleTimeString("vi-VN")}
                          </span>
                        </div>
                        <p className="text-[14px] text-ink leading-relaxed">
                          {m.message}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-center text-ink-muted text-[14px] py-10">
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
                    className="apple-input flex-1"
                  />
                  <button onClick={handleSendMemo} className="pill-button px-6">
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
          <p className="text-[15px] text-ink-muted">
            Bạn muốn chuyển quyền sở hữu tài liệu cho{" "}
            <strong className="text-ink">{transferName}</strong>? Sau khi
            chuyển, bạn sẽ chỉ còn quyền cộng tác viên.
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setTransferId(null)}
            className="px-5 py-2 text-brand font-medium hover:bg-surface-quiet rounded-full"
          >
            Hủy
          </button>
          <button onClick={handleTransferOwnership} className="pill-button">
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
          <div className="h-64 bg-surface-quiet rounded-panel border border-border p-4 overflow-y-auto space-y-4 no-scrollbar">
            {activeTaskComments.length > 0 ? (
              activeTaskComments.map((c) => (
                <div
                  key={c.id}
                  className="bg-surface-quiet p-3 rounded-control  max-w-[90%]"
                >
                  <div className="flex justify-between text-[11px] text-ink-muted mb-1">
                    <span className="font-semibold text-ink">
                      {c.sender_name}
                    </span>
                    <span>
                      {new Date(c.timestamp).toLocaleTimeString("vi-VN")}
                    </span>
                  </div>
                  <p className="text-[14px] text-ink">{c.comment_text}</p>
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
              className="apple-input flex-1"
            />
            <button
              onClick={handleSendTaskComment}
              className="pill-button px-6"
            >
              Gửi
            </button>
          </div>
        </ModalContent>
      </Modal>
    </div>
  );
}
