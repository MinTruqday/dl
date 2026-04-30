"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/app/contexts/AuthContext";
import {
  getMyDocumentsAPI,
  getCollaborationInvitesAPI,
  inviteCollaboratorAPI,
  respondToInviteAPI,
} from "@/app/lib/api";
import { UserPlus, Mail, Check, X, Loader2, Info, Sparkles, ChevronRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { Notification } from "@/app/components/NotificationToast";

export default function StudioCollabPage() {
  const { user, isLoading } = useAuth() as any;
  const router = useRouter();
  const [documents, setDocuments] = useState<any[]>([]);
  const [invites, setInvites] = useState<any[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [collaboratorEmail, setCollaboratorEmail] = useState("");
  const [role, setRole] = useState("editor");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [docsData, invitesData] = await Promise.all([getMyDocumentsAPI(), getCollaborationInvitesAPI()]);
      setDocuments(docsData.data || docsData || []);
      setInvites(invitesData.data || invitesData || []);
    } catch (err: any) {
      console.error("Lỗi tải dữ liệu cộng tác:", err);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
    if (!isLoading && user) loadData();
  }, [isLoading, user, router, loadData]);

  const handleInvite = async () => {
    if (!selectedDocumentId || !collaboratorEmail) return;
    setActionLoading(true);
    try {
      await inviteCollaboratorAPI(selectedDocumentId, collaboratorEmail, role);
      setNotification({ type: "success", text: "Đã gửi lời mời cộng tác thành công." });
      setCollaboratorEmail("");
      loadData();
    } catch (err: any) {
      setNotification({ type: "error", text: err.message || "Không thể gửi lời mời cộng tác lúc này" });
    } finally {
      setActionLoading(false);
    }
  };

  const handleRespond = async (inviteId: string, status: string) => {
    setActionLoading(true);
    try {
      await respondToInviteAPI(inviteId, status);
      setNotification({
        type: "success",
        text: status === "ACCEPTED" ? "Đã chấp nhận lời mời cộng tác." : "Đã từ chối lời mời cộng tác.",
      });
      loadData();
    } catch (err: any) {
      setNotification({ type: "error", text: err.message || "Xử lý lời mời thất bại" });
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading || loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      {notification && (
        <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      <div 
        className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
              Cộng tác tri thức
            </h1>
            <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
              Quản trị cộng tác & Quyền biên tập <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
            </p>
          </div>
          <div className="hidden md:flex items-center gap-3 px-6 py-3 bg-zinc-50 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-400 rounded-sm">
             <UserPlus className="w-4 h-4" /> Hệ thống làm việc nhóm DocLib
          </div>
        </div>
      </div>

      <div 
        className="grid grid-cols-1 lg:grid-cols-12 gap-16 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <section className="lg:col-span-5 space-y-10">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-10 h-10 bg-black flex items-center justify-center rounded-sm">
              <UserPlus className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-sm font-bold text-black tracking-tight uppercase">Mời cộng tác viên</h2>
          </div>

          <div className="space-y-8 bg-zinc-50/20 p-10 border border-zinc-100 rounded-sm">
            <div className="space-y-3">
              <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">Lựa chọn tài liệu</label>
              <div className="relative group">
                <select
                  value={selectedDocumentId}
                  onChange={(e) => setSelectedDocumentId(e.target.value)}
                  className="w-full h-14 px-5 bg-white border border-zinc-100 rounded-sm text-sm font-bold focus:outline-none focus:border-black transition-all appearance-none cursor-pointer"
                >
                  <option value="">Chọn tài liệu biên tập</option>
                  {documents.map((doc) => (
                    <option key={doc._id || doc.id} value={doc._id || doc.id}>
                      {doc.title}
                    </option>
                  ))}
                </select>
                <div className="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-200 group-hover:text-black transition-colors">
                  <ChevronRight className="w-4 h-4 rotate-90" />
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">Email người nhận</label>
              <div className="relative group">
                <Mail className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-300 group-focus-within:text-black transition-colors" />
                <input
                  type="email"
                  placeholder=""
                  value={collaboratorEmail}
                  onChange={(e) => setCollaboratorEmail(e.target.value)}
                  className="w-full h-14 pl-14 pr-5 bg-white border border-zinc-100 rounded-sm text-sm font-bold focus:outline-none focus:border-black transition-all placeholder:text-zinc-200"
                />
              </div>
            </div>

            <div className="space-y-4">
              <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">Vai trò & Quyền hạn</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setRole("editor")}
                  className={`flex-1 py-4 text-[10px] font-bold border transition-all active:scale-95 rounded-sm ${
                    role === "editor"
                      ? "bg-black text-white border-black"
                      : "bg-white text-zinc-300 border-zinc-100 hover:border-black hover:text-black"
                  }`}
                >
                  Biên tập viên
                </button>
                <button
                  onClick={() => setRole("viewer")}
                  className={`flex-1 py-4 text-[10px] font-bold border transition-all active:scale-95 rounded-sm ${
                    role === "viewer"
                      ? "bg-black text-white border-black"
                      : "bg-white text-zinc-300 border-zinc-100 hover:border-black hover:text-black"
                  }`}
                >
                  Người xem
                </button>
              </div>
            </div>

            <button
              onClick={handleInvite}
              disabled={actionLoading || !selectedDocumentId || !collaboratorEmail}
              className="w-full bg-black text-white py-5 text-[11px] font-bold hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center justify-center gap-3 disabled:opacity-50 rounded-sm uppercase tracking-widest"
            >
              {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Gửi lời mời cộng tác"}
            </button>
          </div>
        </section>

        <section className="lg:col-span-7 space-y-10">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-10 h-10 bg-zinc-50 border border-zinc-100 flex items-center justify-center rounded-sm">
              <Mail className="w-5 h-5 text-zinc-300" />
            </div>
            <h2 className="text-sm font-bold text-black tracking-tight uppercase">Lời mời cộng tác đang chờ</h2>
          </div>

          <div className="grid gap-6">
            {invites.length > 0 ? (
              invites.map((invite) => (
                <div
                  key={invite._id}
                  className="p-8 border border-zinc-100 bg-white hover:border-black transition-all duration-300 flex flex-col md:flex-row md:items-center justify-between gap-8 group rounded-sm"
                >
                    <div className="space-y-2 min-w-0">
                      <h4 className="font-bold text-base text-black tracking-tight truncate group-hover:translate-x-1 transition-transform duration-300">
                        {invite.document_title}
                      </h4>
                      <div className="flex items-center gap-3">
                        <p className="text-[11px] text-zinc-400 font-bold uppercase tracking-widest">Từ: {invite.inviter_name}</p>
                        <div className="w-1 h-1 bg-zinc-100 rounded-sm" />
                        <span className="text-[10px] font-bold px-2 py-0.5 bg-zinc-50 border border-zinc-100 text-zinc-400 rounded-sm uppercase tracking-widest">
                          {invite.role === "editor" ? "Quyền biên tập" : "Quyền xem"}
                        </span>
                      </div>
                    </div>
                  <div className="flex gap-3 shrink-0">
                    <button
                      onClick={() => handleRespond(invite._id, "REJECTED")}
                      className="px-8 py-3 border border-zinc-100 text-zinc-300 hover:text-black hover:border-black text-[10px] font-bold transition-all active:scale-95 rounded-sm uppercase tracking-widest"
                    >
                      Từ chối
                    </button>
                    <button
                      onClick={() => handleRespond(invite._id, "ACCEPTED")}
                      className="px-8 py-3 bg-black text-white hover:bg-zinc-800 text-[10px] font-bold transition-all active:scale-95 rounded-sm uppercase tracking-widest"
                    >
                      Chấp nhận
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-32 text-center border border-dashed border-zinc-200 bg-zinc-50/20 rounded-sm">
                <Mail className="w-12 h-12 mx-auto mb-6 text-zinc-100" />
                <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Hiện không có lời mời cộng tác nào</p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
