"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { getMyDocumentsAPI } from "@/features/content/services/document_metadata.service";
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
} from "@/features/content/services/collaboration_sync.service";
import {
  UserPlus,
  Mail,
  Check,
  Loader2,
  ChevronRight,
  Shield,
  Trash2,
  Activity,
  UserCheck,
  Search,
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
    } catch (err: any) {
      showToast("Lỗi tải dữ liệu cộng tác", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  const fetchCollaboratorDetails = async () => {
    if (!selectedDocumentId) return;
    try {
      const [
        collabsRes,
        activitiesRes,
        onlineRes,
        memosRes,
        sentInvitesRes,
        statsRes,
        snapshotsRes,
        lockRes,
        tasksRes,
      ] = await Promise.all([
        getCollaboratorsAPI(selectedDocumentId),
        getCollaborationActivitiesAPI(selectedDocumentId),
        getOnlineCollaboratorsAPI(selectedDocumentId),
        getMemosAPI(selectedDocumentId),
        getSentPendingInvitesAPI(selectedDocumentId),
        getContributionStatsAPI(selectedDocumentId),
        getSnapshotsAPI(selectedDocumentId),
        getLockStatusAPI(selectedDocumentId),
        getCollabTasksAPI(selectedDocumentId),
      ]);
      setCollaborators(collabsRes.data || collabsRes || []);
      setActivities(activitiesRes.data || activitiesRes || []);
      setOnlineCollaborators(onlineRes.data || onlineRes || []);
      setMemos(memosRes.data || memosRes || []);
      setSentPendingInvites(sentInvitesRes.data || sentInvitesRes || []);
      setContributionStats(statsRes.data || statsRes || []);
      setSnapshots(snapshotsRes.data || snapshotsRes || []);
      setLockStatus(lockRes.data || lockRes || { is_locked: false });
      setTasks(tasksRes.data || tasksRes || []);
    } catch (err: any) {
      showToast(err.message || "Lỗi tải chi tiết cộng tác", "error");
    }
  };

  const loadOnlineCollaborators = async () => {
    if (!selectedDocumentId) return;
    try {
      const [onlineRes, lockRes] = await Promise.all([
        getOnlineCollaboratorsAPI(selectedDocumentId),
        getLockStatusAPI(selectedDocumentId),
      ]);
      setOnlineCollaborators(onlineRes.data || onlineRes || []);
      setLockStatus(lockRes.data || lockRes || { is_locked: false });
    } catch (err: any) {
      showToast(
        "Không thể tải trạng thái hoạt động: " + (err.message || err),
        "error",
      );
    }
  };

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
    if (doc) {
      setAccessLevel(doc.collab_access_level || "invite_only");
    }

    fetchCollaboratorDetails();
    pingCollaborationStatusAPI(selectedDocumentId).catch(() => {});

    const interval = setInterval(() => {
      pingCollaborationStatusAPI(selectedDocumentId).catch(() => {});
      loadOnlineCollaborators();
    }, 15000);

    return () => clearInterval(interval);
  }, [selectedDocumentId, documents]);

  const handleInvite = async () => {
    if (!selectedDocumentId || !collaboratorEmail) return;
    setActionLoading(true);
    try {
      await inviteCollaboratorAPI(selectedDocumentId, collaboratorEmail, role);
      showToast("Đã gửi lời mời cộng tác thành công.", "success");
      setCollaboratorEmail("");
      loadData();
      fetchCollaboratorDetails();
    } catch (err: any) {
      showToast(
        err.message || "Không thể gửi lời mời cộng tác lúc này",
        "error",
      );
    } finally {
      setActionLoading(false);
    }
  };

  const handleRespond = async (inviteId: string, status: string) => {
    setActionLoading(true);
    try {
      await respondToInviteAPI(inviteId, status);
      showToast(
        status === "ACCEPTED"
          ? "Đã chấp nhận lời mời cộng tác."
          : "Đã từ chối lời mời cộng tác.",
        "success",
      );
      loadData();
      if (selectedDocumentId) fetchCollaboratorDetails();
    } catch (err: any) {
      showToast(err.message || "Xử lý lời mời thất bại", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRemoveCollaborator = async (collaborationId: string) => {
    setActionLoading(true);
    try {
      await removeCollaboratorAPI(collaborationId);
      showToast("Đã xóa cộng tác viên thành công.", "success");
      fetchCollaboratorDetails();
    } catch (err: any) {
      showToast(err.message || "Xóa cộng tác viên thất bại", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleTransferOwnership = async () => {
    if (!selectedDocumentId || !transferId) return;
    setActionLoading(true);
    try {
      await transferOwnershipAPI(selectedDocumentId, transferId);
      showToast(
        `Đã chuyển quyền sở hữu tài liệu thành công tới ${transferName}.`,
        "success",
      );
      setTransferId(null);
      setTransferName("");
      loadData();
      setSelectedDocumentId("");
    } catch (err: any) {
      showToast(err.message || "Chuyển quyền sở hữu thất bại", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateRole = async (collaborationId: string, newRole: string) => {
    try {
      await updateCollaboratorRoleAPI(collaborationId, newRole);
      showToast("Đã cập nhật vai trò cộng tác viên.", "success");
      fetchCollaboratorDetails();
    } catch (err: any) {
      showToast(err.message || "Cập nhật vai trò thất bại.", "error");
    }
  };

  const handleSendMemo = async () => {
    if (!selectedDocumentId || !newMemo.trim()) return;
    try {
      await sendMemoAPI(selectedDocumentId, newMemo.trim());
      setNewMemo("");
      fetchCollaboratorDetails();
    } catch (err: any) {
      showToast(err.message || "Gửi tin nhắn trao đổi thất bại.", "error");
    }
  };

  const handleUpdateAccessLevel = async (level: string) => {
    if (!selectedDocumentId) return;
    try {
      await updateCollabAccessAPI(selectedDocumentId, level);
      setAccessLevel(level);
      showToast("Đã cập nhật cài đặt quyền truy cập.", "success");
      fetchCollaboratorDetails();
    } catch (err: any) {
      showToast(err.message || "Không thể cập nhật quyền truy cập.", "error");
    }
  };

  const handleRevokeInvite = async (inviteId: string) => {
    try {
      await revokeInviteAPI(inviteId);
      showToast("Đã thu hồi lời mời cộng tác thành công.", "success");
      fetchCollaboratorDetails();
    } catch (err: any) {
      showToast(err.message || "Thu hồi lời mời thất bại.", "error");
    }
  };

  const handleCreateSnapshot = async () => {
    if (!selectedDocumentId || !newSnapshotName.trim()) return;
    try {
      await createSnapshotAPI(selectedDocumentId, newSnapshotName.trim());
      showToast("Đã tạo bản sao nháp cộng tác viên biên tập.", "success");
      setNewSnapshotName("");
      fetchCollaboratorDetails();
    } catch (err: any) {
      showToast(err.message || "Tạo bản sao nháp thất bại.", "error");
    }
  };

  const handleAcquireLock = async () => {
    if (!selectedDocumentId) return;
    try {
      await acquireLockAPI(selectedDocumentId);
      showToast("Đã sở hữu khóa biên tập độc quyền.", "success");
      fetchCollaboratorDetails();
    } catch (err: any) {
      showToast(err.message || "Không thể sở hữu khóa biên tập.", "error");
    }
  };

  const handleReleaseLock = async () => {
    if (!selectedDocumentId) return;
    try {
      await releaseLockAPI(selectedDocumentId);
      showToast("Đã nhả khóa biên tập độc quyền.", "success");
      fetchCollaboratorDetails();
    } catch (err: any) {
      showToast(err.message || "Không thể nhả khóa biên tập.", "error");
    }
  };

  const handleGenerateCode = async () => {
    if (!selectedDocumentId) return;
    try {
      const res = await generateInviteCodeAPI(selectedDocumentId);
      setInviteCode(res.data?.invite_code || res.invite_code || "");
      showToast("Tạo mã mời thành công.", "success");
    } catch (err: any) {
      showToast(err.message || "Không thể tạo mã mời.", "error");
    }
  };

  const handleJoinWithCode = async () => {
    if (!joinCodeInput.trim()) return;
    try {
      await joinViaInviteCodeAPI(joinCodeInput.trim());
      showToast("Đã tham gia nhóm cộng tác tài liệu thành công.", "success");
      setJoinCodeInput("");
      loadData();
    } catch (err: any) {
      showToast(err.message || "Mã cộng tác không hợp lệ.", "error");
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
      showToast("Tạo nhiệm vụ cộng tác thành công.", "success");
    } catch (err: any) {
      showToast(err.message || "Không thể tạo nhiệm vụ.", "error");
    }
  };

  const handleToggleTask = async (taskId: string, currentStatus: boolean) => {
    try {
      await updateCollabTaskAPI(taskId, !currentStatus);
      fetchCollaboratorDetails();
    } catch (err: any) {
      showToast(
        err.message || "Không thể cập nhật trạng thái nhiệm vụ.",
        "error",
      );
    }
  };

  const handleViewTaskComments = async (taskId: string) => {
    setActiveTaskId(taskId);
    setActiveTaskCommentText("");
    try {
      const cRes = await getTaskCommentsAPI(taskId);
      setActiveTaskComments(cRes.data || cRes || []);
    } catch (err: any) {
      showToast("Lỗi tải bình luận nhiệm vụ: " + (err.message || err), "error");
    }
  };

  const handleSendTaskComment = async () => {
    if (!activeTaskId || !activeTaskCommentText.trim()) return;
    try {
      await addTaskCommentAPI(activeTaskId, activeTaskCommentText.trim());
      setActiveTaskCommentText("");
      const cRes = await getTaskCommentsAPI(activeTaskId);
      setActiveTaskComments(cRes.data || cRes || []);
    } catch (err: any) {
      showToast("Lỗi gửi bình luận nhiệm vụ: " + (err.message || err), "error");
    }
  };

  const getOnlineStatus = (userId: string) => {
    const found = onlineCollaborators.find((oc) => oc.user_id === userId);
    return found ? found.status : "offline";
  };

  const isOwnerOfSelected = () => {
    if (!selectedDocumentId || !user) return false;
    const doc = documents.find((d) => (d._id || d.id) === selectedDocumentId);
    if (!doc) return false;
    return doc.author_id === (user._id || user.id);
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

  if (isLoading || loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-white">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col gap-6 font-sans text-black selection:bg-black selection:text-white">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold text-black">
            Mã gia nhập nhóm cộng tác
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Mã cộng tác biên tập"
            value={joinCodeInput}
            onChange={(e) => setJoinCodeInput(e.target.value)}
            className="border border-zinc-200 px-4 h-10 text-sm focus:outline-none focus:border-black rounded-xl bg-white placeholder:text-zinc-400 font-sans"
          />
          <button
            onClick={handleJoinWithCode}
            className="px-5 h-10 bg-black text-white text-sm font-medium border border-black rounded-xl hover:bg-zinc-800 transition-colors"
          >
            Gia nhập
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full min-h-0">
        <aside className="lg:col-span-3 flex flex-col space-y-6 overflow-y-auto custom-scrollbar pb-6 pr-2 ">
          <div className="border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm p-6 space-y-4">
            <h2 className="text-sm font-semibold text-black mb-1">
              Cài đặt tài liệu cộng tác
            </h2>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                  Tài liệu hoạt động
                </label>
                <div className="relative">
                  <select
                    value={selectedDocumentId}
                    onChange={(e) => setSelectedDocumentId(e.target.value)}
                    className="w-full h-10 bg-white border border-zinc-200 px-3 text-sm font-medium focus:outline-none focus:border-black appearance-none rounded-xl"
                  >
                    <option value="">Chọn tài liệu biên tập</option>
                    {documents.map((doc) => (
                      <option key={doc._id || doc.id} value={doc._id || doc.id}>
                        {doc.title}
                      </option>
                    ))}
                  </select>
                  <ChevronRight className="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none rotate-90 text-zinc-500" />
                </div>
              </div>

              {selectedDocumentId && isOwnerOfSelected() && (
                <div className="space-y-2 pt-2 border-t border-zinc-100 mt-4">
                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest block mb-2">
                    Quyền truy cập mặc định
                  </label>
                  <div className="flex flex-col gap-2">
                    <button
                      onClick={() => handleUpdateAccessLevel("invite_only")}
                      className={`flex items-center gap-2 p-2 border text-sm font-medium rounded-xl justify-start transition-colors ${
                        accessLevel === "invite_only"
                          ? "bg-zinc-100 text-black border-transparent"
                          : "bg-white text-zinc-500 border-zinc-200 hover:bg-zinc-50"
                      }`}
                    >
                      <Lock className="w-4 h-4" /> Chỉ người được mời
                    </button>
                    <button
                      onClick={() =>
                        handleUpdateAccessLevel("anyone_with_link")
                      }
                      className={`flex items-center gap-2 p-2 border text-sm font-medium rounded-xl justify-start transition-colors ${
                        accessLevel === "anyone_with_link"
                          ? "bg-zinc-100 text-black border-transparent"
                          : "bg-white text-zinc-500 border-zinc-200 hover:bg-zinc-50"
                      }`}
                    >
                      <Globe className="w-4 h-4" /> Bất kỳ ai có liên kết tài
                      liệu
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {selectedDocumentId && (
            <div className="border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between mb-1">
                <h2 className="text-sm font-semibold text-black">
                  Khóa biên tập độc quyền
                </h2>
                <Key className="w-4 h-4 text-zinc-400" />
              </div>
              <div className="space-y-4">
                {lockStatus.is_locked ? (
                  <div className="p-3 bg-zinc-50 border border-zinc-200 text-sm text-zinc-500 rounded-xl">
                    Đang khóa bởi:{" "}
                    <strong className="text-black">
                      {lockStatus.user_name}
                    </strong>
                    {lockStatus.user_id === (user._id || user.id) && (
                      <button
                        onClick={handleReleaseLock}
                        className="w-full mt-3 h-9 bg-white border border-zinc-200 text-black text-sm font-medium rounded-xl flex items-center justify-center gap-2 hover:bg-zinc-50 transition-colors"
                      >
                        Nhả khóa biên tập
                      </button>
                    )}
                  </div>
                ) : (
                  <button
                    onClick={handleAcquireLock}
                    className="w-full h-10 bg-black text-white text-sm font-medium flex items-center justify-center gap-2 rounded-xl hover:bg-zinc-800 transition-colors"
                  >
                    Yêu cầu khóa biên tập độc quyền
                  </button>
                )}
              </div>
            </div>
          )}

          {selectedDocumentId && (
            <div className="border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm p-6 space-y-4">
              <h2 className="text-sm font-semibold text-black mb-1">
                Gửi lời mời cộng tác
              </h2>
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                    Email cộng tác viên
                  </label>
                  <input
                    type="email"
                    placeholder="nguoidung@doclib.com"
                    value={collaboratorEmail}
                    onChange={(e) => setCollaboratorEmail(e.target.value)}
                    className="w-full h-10 bg-white border border-zinc-200 px-3 text-sm font-medium focus:outline-none focus:border-black rounded-xl placeholder:text-zinc-400"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                    Vai trò
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => setRole("editor")}
                      className={`py-2 text-sm font-medium border rounded-xl transition-colors ${
                        role === "editor"
                          ? "bg-zinc-100 text-black border-transparent"
                          : "bg-white text-zinc-500 border-zinc-200 hover:bg-zinc-50"
                      }`}
                    >
                      Biên tập viên
                    </button>
                    <button
                      onClick={() => setRole("viewer")}
                      className={`py-2 text-sm font-medium border rounded-xl transition-colors ${
                        role === "viewer"
                          ? "bg-zinc-100 text-black border-transparent"
                          : "bg-white text-zinc-500 border-zinc-200 hover:bg-zinc-50"
                      }`}
                    >
                      Người xem
                    </button>
                  </div>
                </div>

                <button
                  onClick={handleInvite}
                  disabled={actionLoading || !collaboratorEmail}
                  className="w-full h-10 bg-black text-white text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50 rounded-xl hover:bg-zinc-800 transition-colors"
                >
                  {actionLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    "Gửi lời mời"
                  )}
                </button>
              </div>
            </div>
          )}

          {selectedDocumentId && isOwnerOfSelected() && (
            <div className="border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between mb-1">
                <h2 className="text-sm font-semibold text-black">
                  Mã mời nhanh
                </h2>
                <QrCode className="w-4 h-4 text-zinc-400" />
              </div>
              <div className="space-y-3">
                {inviteCode ? (
                  <div className="flex items-center gap-2 bg-zinc-50 border border-zinc-200 p-2.5 rounded-xl">
                    <span className="font-mono font-bold text-sm tracking-wider flex-1 text-center select-all">
                      {inviteCode}
                    </span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(inviteCode);
                        showToast(
                          "Đã sao chép mã mời nhanh vào bộ nhớ tạm.",
                          "success",
                        );
                      }}
                      className="text-xs font-medium text-black underline hover:text-zinc-500 transition-colors"
                    >
                      Copy
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={handleGenerateCode}
                    className="w-full h-9 bg-white border border-zinc-200 text-black text-sm font-medium rounded-xl hover:bg-zinc-50 transition-colors"
                  >
                    Tạo mã mời
                  </button>
                )}
              </div>
            </div>
          )}

          {selectedDocumentId && sentPendingInvites.length > 0 && (
            <div className="border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm p-6 space-y-4">
              <h2 className="text-sm font-semibold text-black mb-1">
                Lời mời đã gửi (Đang chờ)
              </h2>
              <div className="space-y-3">
                {sentPendingInvites.map((sp) => (
                  <div
                    key={sp._id || sp.id}
                    className="flex items-center justify-between gap-3 text-sm border-b border-zinc-100 pb-2 last:border-0 last:pb-0"
                  >
                    <div className="flex flex-col">
                      <span className="font-semibold text-black">
                        {sp.invitee_id}
                      </span>
                      <span className="text-[10px] font-mono text-zinc-400">
                        Vai trò: {sp.role}
                      </span>
                    </div>
                    <button
                      onClick={() => handleRevokeInvite(sp._id || sp.id)}
                      className="text-xs font-medium text-black underline flex items-center gap-0.5 hover:text-zinc-500 transition-colors"
                    >
                      <X className="w-3 h-3" /> Thu hồi
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedDocumentId && (
            <div className="border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between mb-1">
                <h2 className="text-sm font-semibold text-black">
                  Cộng tác viên hiện tại
                </h2>
                <span className="text-[10px] font-mono text-zinc-400 bg-zinc-100 px-2 py-0.5 rounded-md">
                  {collaborators.length} người
                </span>
              </div>

              {collaborators.length > 0 ? (
                <div className="space-y-4">
                  {collaborators.map((collab) => {
                    const status = getOnlineStatus(collab.user_id);
                    return (
                      <div
                        key={collab.collaboration_id}
                        className="flex flex-col gap-2 border-b border-zinc-100 pb-3 last:border-0 last:pb-0"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-center gap-2">
                            <span
                              className={`w-2 h-2 rounded-xl flex-shrink-0 ${
                                status === "online" ? "bg-black" : "bg-zinc-200"
                              }`}
                            />
                            <div className="flex flex-col">
                              <span className="text-xs font-semibold text-black">
                                {collab.full_name}
                              </span>
                              <span className="text-[9px] font-mono text-zinc-400">
                                {collab.email}
                              </span>
                            </div>
                          </div>

                          {isOwnerOfSelected() ? (
                            <select
                              value={collab.role}
                              onChange={(e) =>
                                handleUpdateRole(
                                  collab.collaboration_id,
                                  e.target.value,
                                )
                              }
                              className="border border-zinc-200 px-2 py-0.5 text-[10px] focus:outline-none focus:border-black rounded-lg bg-white text-zinc-600 font-sans"
                            >
                              <option value="editor">Biên tập viên</option>
                              <option value="viewer">Người xem</option>
                            </select>
                          ) : (
                            <span className="text-[8px] font-mono border border-zinc-200 bg-zinc-50 text-zinc-500 uppercase px-1.5 py-0.5 rounded-lg">
                              {collab.role === "editor"
                                ? "Biên tập viên"
                                : "Người xem"}
                            </span>
                          )}
                        </div>
                        {isOwnerOfSelected() && (
                          <div className="flex gap-3 justify-end mt-1">
                            <button
                              onClick={() => {
                                setTransferId(collab.user_id);
                                setTransferName(collab.full_name);
                              }}
                              className="text-[10px] font-semibold text-zinc-500 flex items-center gap-1 font-sans"
                            >
                              <Shield className="w-3 h-3 text-zinc-400" />{" "}
                              Chuyển sở hữu
                            </button>
                            <button
                              onClick={() =>
                                handleRemoveCollaborator(
                                  collab.collaboration_id,
                                )
                              }
                              className="text-[10px] font-semibold text-black underline underline-offset-2 flex items-center gap-1 font-sans"
                            >
                              <Trash2 className="w-3 h-3 text-zinc-400" /> Xóa
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs text-zinc-400 font-medium py-4 text-center">
                  Chưa có cộng tác viên tham gia biên tập tài liệu này
                </p>
              )}
            </div>
          )}
        </aside>

        <main
          className="lg:col-span-9 space-y-6 overflow-y-auto custom-scrollbar pb-6 pr-2 "
          
        >
          {selectedDocumentId && contributionStats.length > 0 && (
            <div className="border border-zinc-200 bg-zinc-50 rounded-2xl shadow-sm p-5 space-y-4">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="w-5 h-5 text-black" />
                <h2 className="text-lg font-semibold text-black">
                  Phân tích mức độ đóng góp
                </h2>
              </div>
              <div className="space-y-3">
                {contributionStats.map((stat, idx) => {
                  const percent = totalLogs
                    ? (stat.count / totalLogs) * 100
                    : 0;
                  const barColors = [
                    "bg-black",
                    "bg-zinc-600",
                    "bg-zinc-400",
                    "bg-zinc-300",
                  ];
                  const color = barColors[idx % barColors.length];
                  return (
                    <div key={stat.user_name} className="space-y-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span>{stat.user_name}</span>
                        <span className="font-mono">
                          {stat.count} thao tác ({percent.toFixed(0)}%)
                        </span>
                      </div>
                      <div className="w-full h-2 bg-zinc-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${color}`}
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {selectedDocumentId && (
            <div className="border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm p-6 space-y-4">
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-lg font-semibold text-black flex items-center gap-2">
                  <CheckSquare className="w-5 h-5" /> Nhiệm vụ cộng tác viên
                </h2>
              </div>

              <div className="space-y-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Mô tả nhiệm vụ cần cộng tác viên xử lý"
                    value={newTaskDesc}
                    onChange={(e) => setNewTaskDesc(e.target.value)}
                    className="flex-1 border border-zinc-200 px-3 py-2 text-sm focus:outline-none focus:border-black rounded-xl bg-white placeholder:text-zinc-400 font-sans"
                  />
                  <input
                    type="text"
                    placeholder="Giao cho (Tên)"
                    value={newTaskAssigned}
                    onChange={(e) => setNewTaskAssigned(e.target.value)}
                    className="w-40 border border-zinc-200 px-3 py-2 text-sm focus:outline-none focus:border-black rounded-xl bg-white placeholder:text-zinc-400 font-sans"
                  />
                  <button
                    onClick={handleCreateTask}
                    className="px-6 py-2 bg-black text-white text-sm font-medium border border-black rounded-xl hover:bg-zinc-800 transition-colors"
                  >
                    Thêm
                  </button>
                </div>

                {tasks.length > 0 ? (
                  <div className="space-y-3">
                    {tasks.map((task) => (
                      <div
                        key={task.id}
                        className="flex items-start justify-between border border-zinc-200 p-3 bg-zinc-50 rounded-xl"
                      >
                        <div className="flex items-start gap-3">
                          <button
                            onClick={() =>
                              handleToggleTask(task.id, task.is_done)
                            }
                            className="mt-0.5"
                          >
                            {task.is_done ? (
                              <CheckSquare className="w-4 h-4 text-black" />
                            ) : (
                              <Square className="w-4 h-4 text-zinc-400" />
                            )}
                          </button>
                          <div className="flex flex-col gap-0.5">
                            <span
                              className={`text-sm font-medium ${task.is_done ? "line-through text-zinc-400" : "text-black"}`}
                            >
                              {task.task_desc}
                            </span>
                            <span className="text-[10px] text-zinc-400">
                              Người thực hiện:{" "}
                              <strong className="text-zinc-500">
                                {task.assigned_to}
                              </strong>{" "}
                              • Tạo bởi: {task.created_by}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() => handleViewTaskComments(task.id)}
                          className="text-xs font-medium text-black underline flex items-center gap-1 hover:text-zinc-500 transition-colors"
                        >
                          <MessageCircle className="w-3.5 h-3.5 text-zinc-500" />{" "}
                          Thảo luận
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-zinc-400 font-medium py-4 text-center">
                    Chưa có nhiệm vụ phân công cho tài liệu này
                  </p>
                )}
              </div>
            </div>
          )}

          {selectedDocumentId && (
            <div className="border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm p-6 space-y-4">
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-lg font-semibold text-black flex items-center gap-2">
                  <Camera className="w-5 h-5" /> Bản sao lưu nháp biên tập
                </h2>
              </div>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Đặt tên phiên bản lưu trữ (Ví dụ: Nháp trước khi sửa chương 2)"
                    value={newSnapshotName}
                    onChange={(e) => setNewSnapshotName(e.target.value)}
                    className="flex-1 border border-zinc-200 px-3 py-2 text-sm focus:outline-none focus:border-black rounded-xl bg-white placeholder:text-zinc-400 font-sans"
                  />
                  <button
                    onClick={handleCreateSnapshot}
                    className="px-6 py-2 bg-black text-white text-sm font-medium border border-black rounded-xl hover:bg-zinc-800 transition-colors"
                  >
                    Chụp bản nháp
                  </button>
                </div>

                {snapshots.length > 0 ? (
                  <div className="grid sm:grid-cols-2 gap-4">
                    {snapshots.map((snap) => (
                      <div
                        key={snap.id}
                        className="border border-zinc-200 p-3 bg-white space-y-1"
                      >
                        <div className="flex justify-between items-center text-xs font-semibold text-black">
                          <span>{snap.version_name}</span>
                        </div>
                        <div className="text-[10px] text-zinc-400 font-mono flex justify-between">
                          <span>Tạo bởi: {snap.created_by}</span>
                          <span>
                            {new Date(snap.timestamp).toLocaleTimeString(
                              "vi-VN",
                            )}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-zinc-400 font-medium py-4 text-center">
                    Chưa có phiên bản nháp nào được lưu trữ
                  </p>
                )}
              </div>
            </div>
          )}

          <div className="border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-2">
              <h2 className="text-lg font-semibold text-black">
                Lời mời cộng tác nhận được
              </h2>
              <div className="flex flex-wrap items-center gap-3">
                <div className="relative w-40">
                  <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Tìm kiếm"
                    value={inviteSearch}
                    onChange={(e) => setInviteSearch(e.target.value)}
                    className="w-full border border-zinc-200 pl-9 pr-3 h-9 text-xs focus:outline-none focus:border-black rounded-xl bg-white font-sans"
                  />
                </div>
                <select
                  value={inviteFilter}
                  onChange={(e) => setInviteFilter(e.target.value)}
                  className="border border-zinc-200 px-3 h-9 text-xs focus:outline-none focus:border-black rounded-xl bg-white text-zinc-600 font-sans"
                >
                  <option value="all">Tất cả trạng thái</option>
                  <option value="pending">Đang chờ</option>
                  <option value="accepted">Đã nhận</option>
                  <option value="rejected">Đã từ chối</option>
                </select>
              </div>
            </div>

            <div>
              {filteredInvites.length > 0 ? (
                <div className="space-y-4">
                  {filteredInvites.map((invite) => (
                    <div
                      key={invite._id || invite.id}
                      className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border border-zinc-200 bg-white gap-4"
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 border border-zinc-200 bg-zinc-50 flex items-center justify-center shrink-0 rounded-xl">
                          <span className="text-xs font-bold text-black uppercase">
                            {invite.inviter_name?.charAt(0) || "U"}
                          </span>
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-black">
                            {invite.document_title}
                          </h4>
                          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-1 text-[10px] font-medium text-zinc-500">
                            <span>
                              Từ:{" "}
                              <span className="text-black">
                                {invite.inviter_name}
                              </span>
                            </span>
                            <span>•</span>
                            <span>
                              Vai trò:{" "}
                              <span className="text-black uppercase">
                                {invite.role === "editor"
                                  ? "Biên tập"
                                  : "Người xem"}
                              </span>
                            </span>
                            <span>•</span>
                            <span
                              className={`font-semibold uppercase ${
                                invite.status === "PENDING"
                                  ? "text-zinc-500"
                                  : invite.status === "ACCEPTED"
                                    ? "text-black"
                                    : "text-zinc-300"
                              }`}
                            >
                              {invite.status === "PENDING"
                                ? "Chờ duyệt"
                                : invite.status === "ACCEPTED"
                                  ? "Đã nhận"
                                  : "Từ chối"}
                            </span>
                          </div>
                        </div>
                      </div>

                      {invite.status === "PENDING" && (
                        <div className="flex gap-2 shrink-0">
                          <button
                            onClick={() =>
                              handleRespond(invite._id || invite.id, "REJECTED")
                            }
                            className="px-4 py-2 bg-white border border-zinc-200 text-black text-sm font-medium rounded-xl hover:bg-zinc-50 transition-colors"
                          >
                            Từ chối
                          </button>
                          <button
                            onClick={() =>
                              handleRespond(invite._id || invite.id, "ACCEPTED")
                            }
                            className="px-4 py-2 bg-black border border-black text-white text-sm font-medium rounded-xl flex items-center gap-2 hover:bg-zinc-800 transition-colors"
                          >
                            <Check className="w-4 h-4" /> Chấp nhận
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white rounded-2xl">
                  <p className="text-sm font-medium text-zinc-500">
                    Chưa có dữ liệu lời mời
                  </p>
                </div>
              )}
            </div>
          </div>

          {selectedDocumentId && (
            <div className="border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm p-6 space-y-4">
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-lg font-semibold text-black flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" /> Trao đổi cộng tác
                  (Memos)
                </h2>
              </div>

              <div className="space-y-4">
                <div className="h-60 overflow-y-auto border border-zinc-200 bg-zinc-50 p-4 space-y-4 flex flex-col rounded-xl custom-scrollbar">
                  {memos.length > 0 ? (
                    memos.map((memo) => (
                      <div
                        key={memo.id}
                        className="flex flex-col text-sm max-w-[85%] border border-zinc-200 p-3 bg-white rounded-xl shadow-sm"
                      >
                        <div className="flex justify-between items-center mb-1 gap-4">
                          <strong className="text-black font-semibold">
                            {memo.sender_name}
                          </strong>
                          <span className="text-[10px] font-mono text-zinc-400">
                            {new Date(memo.timestamp).toLocaleTimeString(
                              "vi-VN",
                            )}
                          </span>
                        </div>
                        <p className="text-zinc-600 leading-relaxed font-sans">
                          {memo.message}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="flex-1 flex items-center justify-center text-zinc-400 font-sans text-xs">
                      Chưa có trao đổi nội bộ cho tài liệu này
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Nhập nội dung trao đổi cộng tác"
                    value={newMemo}
                    onChange={(e) => setNewMemo(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSendMemo();
                    }}
                    className="flex-1 border border-zinc-200 px-4 h-10 text-sm focus:outline-none focus:border-black rounded-xl bg-white placeholder:text-zinc-400 font-sans"
                  />
                  <button
                    onClick={handleSendMemo}
                    className="px-6 h-10 bg-black text-white text-sm font-medium border border-black rounded-xl hover:bg-zinc-800 transition-colors"
                  >
                    Gửi
                  </button>
                </div>
              </div>
            </div>
          )}

          {selectedDocumentId && (
            <div className="border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm p-6 space-y-6">
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-lg font-semibold text-black flex items-center gap-2">
                  <Activity className="w-5 h-5" /> Nhật ký hoạt động cộng tác
                </h2>
              </div>

              {activities.length > 0 ? (
                <div className="relative pl-6 border-l border-zinc-200 space-y-6">
                  {activities.map((act) => (
                    <div key={act.id} className="relative">
                      <span className="w-2.5 h-2.5 bg-black border border-white absolute -left-[31.5px] top-1.5 rounded-full" />
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex flex-col gap-1">
                          <span className="text-xs font-semibold text-black">
                            {act.user_name} ({act.action})
                          </span>
                          <span className="text-[11px] text-zinc-500 font-sans">
                            {act.details}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-zinc-400 whitespace-nowrap">
                          {new Date(act.timestamp).toLocaleTimeString("vi-VN")}{" "}
                          •{" "}
                          {new Date(act.timestamp).toLocaleDateString("vi-VN")}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-zinc-400 font-medium py-4 text-center">
                  Chưa có nhật ký hoạt động cho tài liệu này
                </p>
              )}
            </div>
          )}
        </main>
      </div>

      <Modal
        isOpen={!!transferId}
        onClose={() => setTransferId(null)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle>Chuyển quyền sở hữu tài liệu</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs font-medium text-zinc-500 leading-relaxed font-sans">
            Bạn có chắc chắn muốn chuyển quyền sở hữu tài liệu biên tập cho{" "}
            <strong className="text-black">{transferName}</strong>? Sau khi
            chuyển nhượng, bạn sẽ được tự động đổi vai trò thành **Cộng tác
            viên** của tài liệu này để bảo lưu khả năng truy cập biên tập.
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setTransferId(null)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-sm font-medium text-black flex items-center justify-center rounded-xl hover:bg-zinc-50 transition-colors"
          >
            Hủy
          </button>
          <button
            onClick={handleTransferOwnership}
            className="flex-1 py-2 bg-black text-white text-sm font-medium border border-black flex items-center justify-center rounded-xl hover:bg-zinc-800 transition-colors"
          >
            Xác nhận
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!activeTaskId}
        onClose={() => setActiveTaskId(null)}
        className="max-w-lg"
      >
        <ModalHeader>
          <ModalTitle>Thảo luận nhiệm vụ cộng tác viên</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="h-60 overflow-y-auto border border-zinc-200 bg-zinc-50 p-4 space-y-3 flex flex-col mb-4 rounded-xl custom-scrollbar">
            {activeTaskComments.length > 0 ? (
              activeTaskComments.map((comment) => (
                <div
                  key={comment.id}
                  className="flex flex-col text-sm max-w-[90%] border border-zinc-200 p-3 bg-white rounded-xl shadow-sm"
                >
                  <div className="flex justify-between items-center mb-1 gap-4">
                    <strong className="text-black font-semibold">
                      {comment.sender_name}
                    </strong>
                    <span className="text-[10px] font-mono text-zinc-400">
                      {new Date(comment.timestamp).toLocaleTimeString("vi-VN")}
                    </span>
                  </div>
                  <p className="text-zinc-600 leading-relaxed font-sans">
                    {comment.comment_text}
                  </p>
                </div>
              ))
            ) : (
              <div className="flex-1 flex items-center justify-center text-zinc-400 font-sans text-xs">
                Chưa có thảo luận nào cho nhiệm vụ này
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Nhập nội dung đóng góp ý kiến cho nhiệm vụ"
              value={activeTaskCommentText}
              onChange={(e) => setActiveTaskCommentText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSendTaskComment();
              }}
              className="flex-1 border border-zinc-200 px-4 h-10 text-sm focus:outline-none focus:border-black rounded-xl bg-white placeholder:text-zinc-400 font-sans"
            />
            <button
              onClick={handleSendTaskComment}
              className="px-6 h-10 bg-black text-white text-sm font-medium border border-black rounded-xl hover:bg-zinc-800 transition-colors"
            >
              Gửi
            </button>
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setActiveTaskId(null)}
            className="w-full py-2 border border-zinc-200 bg-white text-sm font-medium text-black flex items-center justify-center rounded-xl hover:bg-zinc-50 transition-colors"
          >
            Đóng
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
