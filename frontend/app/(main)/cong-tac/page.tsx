"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { getMyDocumentsAPI } from "@/features/content/services/document_metadata.service";
import {
 getCollaborationInvitesAPI, inviteCollaboratorAPI, respondToInviteAPI,
 getCollaboratorsAPI, removeCollaboratorAPI, getCollaborationActivitiesAPI,
 transferOwnershipAPI, pingCollaborationStatusAPI, getOnlineCollaboratorsAPI,
 updateCollaboratorRoleAPI, sendMemoAPI, getMemosAPI, updateCollabAccessAPI,
 getSentPendingInvitesAPI, revokeInviteAPI, getContributionStatsAPI,
 createSnapshotAPI, getSnapshotsAPI, acquireLockAPI, releaseLockAPI,
 getLockStatusAPI, generateInviteCodeAPI, joinViaInviteCodeAPI,
 createCollabTaskAPI, getCollabTasksAPI, updateCollabTaskAPI,
 addTaskCommentAPI, getTaskCommentsAPI,
} from "@/features/content/services/collaboration_sync.service";
import { Users, Mail, Check, Loader2, Shield, Trash2, Activity, MessageSquare, Globe, Lock, X, TrendingUp, Camera, Key, QrCode, CheckSquare, Square, MessageCircle, FileText, ChevronRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useToast } from "@/shared/contexts/ToastContext";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from "@/shared/components/ui/Modal";
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
 const [docsData, invitesData] = await Promise.all([ getMyDocumentsAPI(), getCollaborationInvitesAPI() ]);
 setDocuments(docsData.data || docsData || []); setInvites(invitesData.data || invitesData || []);
 } catch (err) { showToast("Lỗi tải dữ liệu", "error"); } finally { setLoading(false); }
 }, [showToast]);

 const fetchCollaboratorDetails = useCallback(async () => {
 if (!selectedDocumentId) return;
 try {
 const [collabs, acts, online, mems, sent, stats, snaps, lock, tasksRes] = await Promise.all([
 getCollaboratorsAPI(selectedDocumentId).catch(() => []), getCollaborationActivitiesAPI(selectedDocumentId).catch(() => []),
 getOnlineCollaboratorsAPI(selectedDocumentId).catch(() => []), getMemosAPI(selectedDocumentId).catch(() => []),
 getSentPendingInvitesAPI(selectedDocumentId).catch(() => []), getContributionStatsAPI(selectedDocumentId).catch(() => []),
 getSnapshotsAPI(selectedDocumentId).catch(() => []), getLockStatusAPI(selectedDocumentId).catch(() => ({is_locked: false})),
 getCollabTasksAPI(selectedDocumentId).catch(() => [])
 ]);
 setCollaborators(collabs.data || collabs || []); setActivities(acts.data || acts || []); setOnlineCollaborators(online.data || online || []);
 setMemos(mems.data || mems || []); setSentPendingInvites(sent.data || sent || []); setContributionStats(stats.data || stats || []);
 setSnapshots(snaps.data || snaps || []); setLockStatus(lock.data || lock || { is_locked: false }); setTasks(tasksRes.data || tasksRes || []);
 } catch (err) { showToast("Lỗi tải chi tiết", "error"); }
 }, [selectedDocumentId, showToast]);

 const loadOnlineCollaborators = useCallback(async () => {
 if (!selectedDocumentId) return;
 try {
 const [online, lock] = await Promise.all([ getOnlineCollaboratorsAPI(selectedDocumentId).catch(() => []), getLockStatusAPI(selectedDocumentId).catch(() => ({is_locked: false})) ]);
 setOnlineCollaborators(online.data || online || []); setLockStatus(lock.data || lock || { is_locked: false });
 } catch (err) {}
 }, [selectedDocumentId]);

 useEffect(() => { if (!isLoading && !user) router.push("/dang-nhap"); if (!isLoading && user) loadData(); }, [isLoading, user, router, loadData]);

 useEffect(() => {
 if (!selectedDocumentId) {
 setCollaborators([]); setActivities([]); setOnlineCollaborators([]); setMemos([]); setSentPendingInvites([]);
 setContributionStats([]); setAccessLevel("invite_only"); setSnapshots([]); setLockStatus({ is_locked: false });
 setInviteCode(""); setTasks([]); return;
 }
 const doc = documents.find((d) => (d._id || d.id) === selectedDocumentId);
 if (doc) setAccessLevel(doc.collab_access_level || "invite_only");
 fetchCollaboratorDetails(); pingCollaborationStatusAPI(selectedDocumentId).catch(() => {});
 const interval = setInterval(() => { pingCollaborationStatusAPI(selectedDocumentId).catch(() => {}); loadOnlineCollaborators(); }, 15000);
 return () => clearInterval(interval);
 }, [selectedDocumentId, documents, fetchCollaboratorDetails, loadOnlineCollaborators]);

 const handleInvite = async () => {
 if (!selectedDocumentId || !collaboratorEmail) return;
 setActionLoading(true);
 try {
 await inviteCollaboratorAPI(selectedDocumentId, collaboratorEmail, role); showToast("Đã gửi lời mời", "success");
 setCollaboratorEmail(""); loadData(); fetchCollaboratorDetails();
 } catch (err) { showToast("Gửi thất bại", "error"); } finally { setActionLoading(false); }
 };

 const handleRespond = async (inviteId: string, status: string) => {
 setActionLoading(true);
 try {
 await respondToInviteAPI(inviteId, status); showToast(status === "ACCEPTED" ? "Đã chấp nhận" : "Đã từ chối", "success");
 loadData(); if (selectedDocumentId) fetchCollaboratorDetails();
 } catch (err) { showToast("Xử lý thất bại", "error"); } finally { setActionLoading(false); }
 };

 const handleRemoveCollaborator = async (collabId: string) => {
 setActionLoading(true);
 try { await removeCollaboratorAPI(collabId); showToast("Đã xóa", "success"); fetchCollaboratorDetails(); }
 catch (err) { showToast("Xóa thất bại", "error"); } finally { setActionLoading(false); }
 };

 const handleTransferOwnership = async () => {
 if (!selectedDocumentId || !transferId) return;
 setActionLoading(true);
 try {
 await transferOwnershipAPI(selectedDocumentId, transferId); showToast(`Đã chuyển cho ${transferName}`, "success");
 setTransferId(null); setTransferName(""); loadData(); setSelectedDocumentId("");
 } catch (err) { showToast("Chuyển thất bại", "error"); } finally { setActionLoading(false); }
 };

 const handleUpdateRole = async (collabId: string, newRole: string) => {
 try { await updateCollaboratorRoleAPI(collabId, newRole); showToast("Đã cập nhật vai trò", "success"); fetchCollaboratorDetails(); }
 catch (err) { showToast("Cập nhật thất bại", "error"); }
 };

 const handleSendMemo = async () => {
 if (!selectedDocumentId || !newMemo.trim()) return;
 try { await sendMemoAPI(selectedDocumentId, newMemo.trim()); setNewMemo(""); fetchCollaboratorDetails(); }
 catch (err) { showToast("Gửi thất bại", "error"); }
 };

 const handleUpdateAccessLevel = async (level: string) => {
 if (!selectedDocumentId) return;
 try { await updateCollabAccessAPI(selectedDocumentId, level); setAccessLevel(level); showToast("Đã cập nhật", "success"); fetchCollaboratorDetails(); }
 catch (err) { showToast("Cập nhật thất bại", "error"); }
 };

 const handleRevokeInvite = async (inviteId: string) => {
 try { await revokeInviteAPI(inviteId); showToast("Đã thu hồi", "success"); fetchCollaboratorDetails(); }
 catch (err) { showToast("Thu hồi thất bại", "error"); }
 };

 const handleCreateSnapshot = async () => {
 if (!selectedDocumentId || !newSnapshotName.trim()) return;
 try { await createSnapshotAPI(selectedDocumentId, newSnapshotName.trim()); showToast("Đã tạo bản sao", "success"); setNewSnapshotName(""); fetchCollaboratorDetails(); }
 catch (err) { showToast("Tạo thất bại", "error"); }
 };

 const handleAcquireLock = async () => {
 if (!selectedDocumentId) return;
 try { await acquireLockAPI(selectedDocumentId); showToast("Đã sở hữu khóa", "success"); fetchCollaboratorDetails(); }
 catch (err) { showToast("Sở hữu thất bại", "error"); }
 };

 const handleReleaseLock = async () => {
 if (!selectedDocumentId) return;
 try { await releaseLockAPI(selectedDocumentId); showToast("Đã nhả khóa", "success"); fetchCollaboratorDetails(); }
 catch (err) { showToast("Nhả khóa thất bại", "error"); }
 };

 const handleGenerateCode = async () => {
 if (!selectedDocumentId) return;
 try { const res = await generateInviteCodeAPI(selectedDocumentId); setInviteCode(res.data?.invite_code || res.invite_code || ""); showToast("Tạo mã thành công", "success"); }
 catch (err) { showToast("Tạo mã thất bại", "error"); }
 };

 const handleJoinWithCode = async () => {
 if (!joinCodeInput.trim()) return;
 try { await joinViaInviteCodeAPI(joinCodeInput.trim()); showToast("Đã tham gia", "success"); setJoinCodeInput(""); loadData(); }
 catch (err) { showToast("Mã không hợp lệ", "error"); }
 };

 const handleCreateTask = async () => {
 if (!selectedDocumentId || !newTaskDesc.trim()) return;
 try { await createCollabTaskAPI(selectedDocumentId, newTaskDesc.trim(), newTaskAssigned); setNewTaskDesc(""); setNewTaskAssigned(""); fetchCollaboratorDetails(); showToast("Đã thêm nhiệm vụ", "success"); }
 catch (err) { showToast("Thêm thất bại", "error"); }
 };

 const handleToggleTask = async (taskId: string, currentStatus: boolean) => {
 try { await updateCollabTaskAPI(taskId, !currentStatus); fetchCollaboratorDetails(); }
 catch (err) { showToast("Lỗi cập nhật", "error"); }
 };

 const handleViewTaskComments = async (taskId: string) => {
 setActiveTaskId(taskId); setActiveTaskCommentText("");
 try { const cRes = await getTaskCommentsAPI(taskId); setActiveTaskComments(cRes.data || cRes || []); }
 catch (err) { showToast("Lỗi tải bình luận", "error"); }
 };

 const handleSendTaskComment = async () => {
 if (!activeTaskId || !activeTaskCommentText.trim()) return;
 try { await addTaskCommentAPI(activeTaskId, activeTaskCommentText.trim()); setActiveTaskCommentText(""); const cRes = await getTaskCommentsAPI(activeTaskId); setActiveTaskComments(cRes.data || cRes || []); }
 catch (err) { showToast("Lỗi gửi", "error"); }
 };

 const getOnlineStatus = (userId: string) => onlineCollaborators.find((oc) => oc.user_id === userId)?.status || "offline";
 const isOwnerOfSelected = () => {
 if (!selectedDocumentId || !user) return false;
 const doc = documents.find((d) => (d._id || d.id) === selectedDocumentId);
 return doc ? doc.author_id === (user._id || user.id) : false;
 };

 const filteredInvites = invites.filter((inv) => {
 const titleMatch = inv.document_title?.toLowerCase().includes(inviteSearch.toLowerCase()) || inv.inviter_name?.toLowerCase().includes(inviteSearch.toLowerCase());
 if (inviteFilter === "all") return titleMatch;
 if (inviteFilter === "pending") return titleMatch && inv.status === "PENDING";
 if (inviteFilter === "accepted") return titleMatch && inv.status === "ACCEPTED";
 if (inviteFilter === "rejected") return titleMatch && inv.status === "REJECTED";
 return titleMatch;
 });

 const totalLogs = contributionStats.reduce((acc, c) => acc + c.count, 0);

 if (loading || isLoading) return <PageLoader />;

 return (
 <div className="w-full max-w-[1200px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] font-sans text-[#1D1D1F] flex flex-col gap-6">
 <div className="grid lg:grid-cols-12 gap-8 flex-1 min-h-0">
 <aside className="lg:col-span-4 flex flex-col space-y-6 overflow-y-auto no-scrollbar pb-6 pr-2">
 <div className="bg-[#F5F5F7] rounded-[18px] p-6 space-y-4">
 <p className="text-[13px] font-medium text-[#6E6E73] mb-4">Gia nhập phiên</p>
 <div className="flex flex-col xl:flex-row items-center gap-2">
 <input type="text" placeholder="Mã gia nhập..." value={joinCodeInput} onChange={(e) => setJoinCodeInput(e.target.value)} className="apple-input w-full" />
 <button onClick={handleJoinWithCode} className="pill-button w-full xl:w-auto shrink-0">Gia nhập</button>
 </div>
 </div>
 <div className="bg-[#F5F5F7] rounded-[18px] p-6 space-y-4">
 <p className="text-[13px] font-medium text-[#6E6E73] mb-4">Tài liệu hoạt động</p>
 <div className="relative">
 <select value={selectedDocumentId} onChange={(e) => setSelectedDocumentId(e.target.value)} className="w-full h-[44px] bg-white  px-4 text-[15px] focus:outline-none focus:border-[#0071E3] appearance-none rounded-[10px]">
 <option value="">Chọn tài liệu biên tập</option>
 {documents.map((doc) => (<option key={doc._id || doc.id} value={doc._id || doc.id}>{doc.title}</option>))}
 </select>
 <ChevronRight className="w-5 h-5 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none rotate-90 text-[#6E6E73]" />
 </div>

 {selectedDocumentId && isOwnerOfSelected() && (
 <div className="space-y-3 pt-4 border-t border-[#E8E8ED]">
 <label className="text-[13px] font-medium text-[#6E6E73]">Quyền truy cập</label>
 <div className="flex flex-col gap-2">
 <button onClick={() => handleUpdateAccessLevel("invite_only")} className={`flex items-center justify-center gap-2 px-4 py-3 text-[14px] font-medium rounded-[10px] transition-colors ${accessLevel === "invite_only" ? "bg-[#0071E3] text-white" : "bg-white text-[#0071E3] font-medium hover:bg-[#E8E8ED]"}`}>Chỉ người được mời</button>
 <button onClick={() => handleUpdateAccessLevel("anyone_with_link")} className={`flex items-center justify-center gap-2 px-4 py-3 text-[14px] font-medium rounded-[10px] transition-colors ${accessLevel === "anyone_with_link" ? "bg-[#0071E3] text-white" : "bg-white text-[#0071E3] font-medium hover:bg-[#E8E8ED]"}`}>Có link tham gia</button>
 </div>
 </div>
 )}
 </div>

 {selectedDocumentId && (
 <div className="bg-[#F5F5F7] rounded-[18px] p-6 space-y-4">
 <p className="text-[13px] font-medium text-[#6E6E73] mb-4">Khóa phiên</p>
 {lockStatus.is_locked ? (
 <div className="p-4 bg-[#FFF0F0] text-[#FF3B30] text-[14px] rounded-[10px]">
 Khóa bởi: <strong className="font-semibold">{lockStatus.user_name}</strong>
 {lockStatus.user_id === (user._id || user.id) && <button onClick={handleReleaseLock} className="mt-3 w-full py-2 bg-white rounded-[10px] font-medium text-[#FF3B30]">Nhả khóa</button>}
 </div>
 ) : <button onClick={handleAcquireLock} className="w-full py-3 bg-[#0071E3] text-white text-[14px] font-medium rounded-[10px] hover:bg-[#005bb5] transition-colors">Yêu cầu khóa độc quyền</button>}
 </div>
 )}

 {selectedDocumentId && (
 <div className="bg-[#F5F5F7] rounded-[18px] p-6 space-y-4">
 <p className="text-[13px] font-medium text-[#6E6E73] mb-4">Mời cộng tác</p>
 <input type="email" placeholder="" value={collaboratorEmail} onChange={(e) => setCollaboratorEmail(e.target.value)} className="apple-input w-full" />
 <div className="flex gap-2">
 <button onClick={() => setRole("editor")} className={`flex-1 py-2 text-[13px] font-medium rounded-[10px] transition-colors ${role === "editor" ? "bg-black text-white" : "bg-white text-[#0071E3] font-medium"}`}>Biên tập</button>
 <button onClick={() => setRole("viewer")} className={`flex-1 py-2 text-[13px] font-medium rounded-[10px] transition-colors ${role === "viewer" ? "bg-black text-white" : "bg-white text-[#0071E3] font-medium"}`}>Người xem</button>
 </div>
 <button onClick={handleInvite} disabled={actionLoading || !collaboratorEmail} className="w-full py-3 bg-[#0071E3] text-white text-[14px] font-medium rounded-[10px] disabled:opacity-50">{actionLoading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Gửi lời mời"}</button>
 </div>
 )}

 {selectedDocumentId && isOwnerOfSelected() && (
 <div className="bg-[#F5F5F7] rounded-[18px] p-6 space-y-4">
 <p className="text-[13px] font-medium text-[#6E6E73] mb-4">Mã mời nhanh</p>
 {inviteCode ? (
 <div className="flex items-center gap-2 bg-white p-3 rounded-[10px] ">
 <span className="font-mono font-bold tracking-wider text-[14px] flex-1 text-center select-all">{inviteCode}</span>
 <button onClick={() => { navigator.clipboard.writeText(inviteCode); showToast("Đã copy mã", "success"); }} className="text-[13px] font-medium text-[#0071E3]">Copy</button>
 </div>
 ) : <button onClick={handleGenerateCode} className="w-full py-3 bg-white text-[14px] font-medium rounded-[10px] ">Tạo mã mời</button>}
 </div>
 )}

 {selectedDocumentId && sentPendingInvites.length > 0 && (
 <div className="bg-[#F5F5F7] rounded-[18px] p-6 space-y-4">
 <p className="text-[13px] font-medium text-[#6E6E73] mb-4">Lời mời đã gửi (chờ)</p>
 <div className="space-y-3">
 {sentPendingInvites.map(sp => (
 <div key={sp._id || sp.id} className="flex justify-between items-center bg-white p-3 rounded-[10px]">
 <div>
 <p className="font-medium text-[14px]">{sp.invitee_id}</p>
 <p className="text-[12px] text-[#6E6E73]">Vai trò: {sp.role}</p>
 </div>
 <button onClick={() => handleRevokeInvite(sp._id || sp.id)} className="text-[13px] text-[#FF3B30]">Thu hồi</button>
 </div>
 ))}
 </div>
 </div>
 )}

 {selectedDocumentId && (
 <div className="bg-[#F5F5F7] rounded-[18px] p-6 space-y-4">
 <div className="flex justify-between items-center"><p className="text-[13px] font-medium text-[#6E6E73] mb-4">Cộng tác viên</p><span className="text-[13px] text-[#6E6E73]">{collaborators.length}</span></div>
 {collaborators.length > 0 ? (
 <div className="space-y-3">
 {collaborators.map(c => {
 const status = getOnlineStatus(c.user_id);
 return (
 <div key={c.collaboration_id} className="bg-white p-4 rounded-[16px]">
 <div className="flex justify-between items-start gap-2">
 <div className="flex items-center gap-2">
 <span className={`w-2 h-2 rounded-full ${status === "online" ? "bg-[#34C759]" : "bg-[#E8E8ED]"}`} />
 <div><p className="text-[14px] font-medium text-[#1D1D1F] leading-tight">{c.full_name}</p><p className="text-[12px] text-[#6E6E73] mt-0.5">{c.email}</p></div>
 </div>
 {isOwnerOfSelected() ? (
 <select value={c.role} onChange={(e) => handleUpdateRole(c.collaboration_id, e.target.value)} className="bg-[#F5F5F7] text-[12px] px-2 py-1 rounded-[8px] outline-none ">
 <option value="editor">Biên tập</option><option value="viewer">Xem</option>
 </select>
 ) : <span className="bg-[#F5F5F7] text-[12px] px-2 py-1 rounded-[8px] text-[#6E6E73]">{c.role === "editor" ? "Biên tập" : "Xem"}</span>}
 </div>
 {isOwnerOfSelected() && (
 <div className="flex justify-end gap-3 mt-3 pt-3 border-t border-[#F5F5F7]">
 <button onClick={() => { setTransferId(c.user_id); setTransferName(c.full_name); }} className="text-[12px] font-medium text-[#0071E3]">Chuyển chủ</button>
 <button onClick={() => handleRemoveCollaborator(c.collaboration_id)} className="text-[12px] font-medium text-[#FF3B30]">Xóa</button>
 </div>
 )}
 </div>
 );
 })}
 </div>
 ) : <EmptyState text="Chưa có ai tham gia" compact={true} />}
 </div>
 )}
 </aside>

 <main className="lg:col-span-8 space-y-6 overflow-y-auto no-scrollbar pb-6">
 <div className="bg-[#F5F5F7] rounded-[18px] p-8 space-y-6">
 <p className="text-[13px] font-medium text-[#6E6E73] mb-4">Thư mời cộng tác</p>
 {filteredInvites.length > 0 ? (
 <div className="grid gap-4">
 {filteredInvites.map(inv => (
 <div key={inv._id || inv.id} className="bg-[#F5F5F7] border-[#E8E8ED] rounded-[18px] p-5 flex flex-col md:flex-row justify-between gap-4 items-start md:items-center">
 <div>
 <h4 className="text-[16px] font-medium text-[#1D1D1F]">{inv.document_title}</h4>
 <p className="text-[13px] text-[#6E6E73] mt-1">Từ: {inv.inviter_name} • Vai trò: {inv.role === "editor" ? "Biên tập" : "Xem"}</p>
 </div>
 {inv.status === "PENDING" && (
 <div className="flex gap-2">
 <button onClick={() => handleRespond(inv._id || inv.id, "REJECTED")} className="px-4 py-2 bg-[#F5F5F7] text-[#1D1D1F] text-[14px] font-medium rounded-[12px]">Từ chối</button>
 <button onClick={() => handleRespond(inv._id || inv.id, "ACCEPTED")} className="px-4 py-2 bg-[#0071E3] text-white text-[14px] font-medium rounded-[12px]">Chấp nhận</button>
 </div>
 )}
 </div>
 ))}
 </div>
 ) : <p className="text-center text-[#6E6E73] text-[15px] py-10">Bạn chưa nhận được lời mời nào.</p>}
 </div>

 {selectedDocumentId && (
 <>
 <div className="bg-[#F5F5F7] rounded-[18px] p-8 space-y-6">
 <h2 className="text-[20px] font-semibold text-[#1D1D1F] flex items-center gap-2"><CheckSquare className="w-5 h-5" /> Nhiệm vụ & Checklist</h2>
 <div className="flex gap-2">
 <input type="text" placeholder="" value={newTaskDesc} onChange={(e) => setNewTaskDesc(e.target.value)} className="apple-input flex-1" />
 <input type="text" placeholder="" value={newTaskAssigned} onChange={(e) => setNewTaskAssigned(e.target.value)} className="apple-input w-32" />
 <button onClick={handleCreateTask} className="pill-button px-6">Thêm</button>
 </div>
 <div className="space-y-3">
 {tasks.map((task) => (
 <div key={task.id} className="bg-[#F5F5F7] p-4 rounded-[16px] flex justify-between items-start gap-4 border-[#E8E8ED]">
 <div className="flex gap-3 items-start">
 <button onClick={() => handleToggleTask(task.id, task.is_done)} className="mt-1">{task.is_done ? <CheckSquare className="w-5 h-5 text-[#34C759]" /> : <Square className="w-5 h-5 text-[#6E6E73]" />}</button>
 <div>
 <p className={`text-[15px] font-medium ${task.is_done ? "line-through text-[#6E6E73]" : "text-[#1D1D1F]"}`}>{task.task_desc}</p>
 <p className="text-[12px] text-[#6E6E73] mt-1">Giao: {task.assigned_to} • Tạo: {task.created_by}</p>
 </div>
 </div>
 <button onClick={() => handleViewTaskComments(task.id)} className="text-[13px] font-medium text-[#0071E3]">Thảo luận</button>
 </div>
 ))}
 </div>
 </div>

 <div className="bg-[#F5F5F7] rounded-[18px] p-8 space-y-6">
 <h2 className="text-[20px] font-semibold text-[#1D1D1F] flex items-center gap-2"><MessageSquare className="w-5 h-5" /> Bảng ghim & Trao đổi</h2>
 <div className="h-64 bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] p-4 overflow-y-auto space-y-4 no-scrollbar">
 {memos.length > 0 ? memos.map(m => (
 <div key={m.id} className="bg-[#F5F5F7] p-4 rounded-[16px] max-w-[85%] ">
 <div className="flex justify-between text-[12px] text-[#6E6E73] mb-2"><span className="font-semibold text-[#1D1D1F]">{m.sender_name}</span><span>{new Date(m.timestamp).toLocaleTimeString("vi-VN")}</span></div>
 <p className="text-[14px] text-[#1D1D1F] leading-relaxed">{m.message}</p>
 </div>
 )) : <p className="text-center text-[#6E6E73] text-[14px] py-10">Bảng tin trống.</p>}
 </div>
 <div className="flex gap-2">
 <input type="text" placeholder="" value={newMemo} onChange={(e) => setNewMemo(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSendMemo()} className="apple-input flex-1" />
 <button onClick={handleSendMemo} className="pill-button px-6">Gửi</button>
 </div>
 </div>
 </>
 )}
 </main>
 </div>

 <Modal isOpen={!!transferId} onClose={() => setTransferId(null)} className="max-w-md bg-[#F5F5F7] rounded-[18px] p-0 -2xl border-none">
 <ModalHeader className="p-6"><ModalTitle className="text-[20px] font-semibold">Chuyển nhượng quyền sở hữu</ModalTitle></ModalHeader>
 <ModalContent className="p-6 pt-0"><p className="text-[15px] text-[#6E6E73]">Bạn muốn chuyển quyền sở hữu tài liệu cho <strong className="text-[#1D1D1F]">{transferName}</strong>? Sau khi chuyển, bạn sẽ chỉ còn quyền cộng tác viên.</p></ModalContent>
 <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3">
 <button onClick={() => setTransferId(null)} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full">Hủy</button>
 <button onClick={handleTransferOwnership} className="pill-button">Xác nhận</button>
 </ModalFooter>
 </Modal>

 <Modal isOpen={!!activeTaskId} onClose={() => setActiveTaskId(null)} className="max-w-xl bg-[#F5F5F7] rounded-[18px] p-0 -2xl border-none">
 <ModalHeader className="p-6"><ModalTitle className="text-[20px] font-semibold">Thảo luận nhiệm vụ</ModalTitle></ModalHeader>
 <ModalContent className="p-6 pt-0 space-y-4">
 <div className="h-64 bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] p-4 overflow-y-auto space-y-4 no-scrollbar">
 {activeTaskComments.length > 0 ? activeTaskComments.map(c => (
 <div key={c.id} className="bg-[#F5F5F7] p-3 rounded-[10px]  max-w-[90%]">
 <div className="flex justify-between text-[11px] text-[#6E6E73] mb-1"><span className="font-semibold text-[#1D1D1F]">{c.sender_name}</span><span>{new Date(c.timestamp).toLocaleTimeString("vi-VN")}</span></div>
 <p className="text-[14px] text-[#1D1D1F]">{c.comment_text}</p>
 </div>
 )) : <EmptyState text="Chưa có bình luận." compact={true} />}
 </div>
 <div className="flex gap-2">
 <input type="text" placeholder="" value={activeTaskCommentText} onChange={(e) => setActiveTaskCommentText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSendTaskComment()} className="apple-input flex-1" />
 <button onClick={handleSendTaskComment} className="pill-button px-6">Gửi</button>
 </div>
 </ModalContent>
 </Modal>
 </div>
 );
}
