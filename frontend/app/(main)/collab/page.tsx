"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { getMyDocumentsAPI } from "@/services/document.service";
import {
  getCollaborationInvitesAPI,
  inviteCollaboratorAPI,
  respondToInviteAPI,
} from "@/services/collaboration.service";
import {
  UserPlus,
  Mail,
  Check,
  Loader2,
  ChevronRight,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useToast } from "@/contexts/ToastContext";

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
  const [visible, setVisible] = useState(false);

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

  useEffect(() => {
    if (!isLoading && !user) router.push("/dang-nhap");
    if (!isLoading && user) loadData();
  }, [isLoading, user, router, loadData]);

  const handleInvite = async () => {
    if (!selectedDocumentId || !collaboratorEmail) return;
    setActionLoading(true);
    try {
      await inviteCollaboratorAPI(selectedDocumentId, collaboratorEmail, role);
      showToast("Đã gửi lời mời cộng tác thành công.", "success");
      setCollaboratorEmail("");
      loadData();
    } catch (err: any) {
      showToast(
        err.message || "Không thể gửi lời mời cộng tác lúc này",
        "error"
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
        "success"
      );
      loadData();
    } catch (err: any) {
      showToast(err.message || "Xử lý lời mời thất bại", "error");
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading || loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-white">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <div className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-black">Cộng tác nội dung</h1>
          <p className="text-zinc-500 text-sm font-medium">
            Quản trị cộng tác và phân quyền biên tập tài liệu
          </p>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-12">
        <aside className="lg:col-span-4 space-y-6">
          <div className="border border-zinc-200 bg-white p-6 space-y-6">
            <h2 className="text-sm font-semibold text-black border-b border-zinc-200 pb-3 flex items-center gap-2">
              <UserPlus className="w-4 h-4" /> Gửi lời mời cộng tác
            </h2>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                  Tài liệu
                </label>
                <div className="relative">
                  <select
                    value={selectedDocumentId}
                    onChange={(e) => setSelectedDocumentId(e.target.value)}
                    className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black appearance-none rounded-none"
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

              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                  Email cộng tác viên
                </label>
                <input
                  type="email"
                  placeholder="nguoidung@doclib.com"
                  value={collaboratorEmail}
                  onChange={(e) => setCollaboratorEmail(e.target.value)}
                  className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black rounded-none placeholder:text-zinc-400"
                />
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                  Vai trò
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setRole("editor")}
                    className={`py-2 text-xs font-medium border rounded-none ${
                      role === "editor"
                        ? "bg-black text-white border-black"
                        : "bg-white text-zinc-500 border-zinc-200"
                    }`}
                  >
                    Biên tập viên
                  </button>
                  <button
                    onClick={() => setRole("viewer")}
                    className={`py-2 text-xs font-medium border rounded-none ${
                      role === "viewer"
                        ? "bg-black text-white border-black"
                        : "bg-white text-zinc-500 border-zinc-200"
                    }`}
                  >
                    Người xem
                  </button>
                </div>
              </div>
            </div>

            <button
              onClick={handleInvite}
              disabled={actionLoading || !selectedDocumentId || !collaboratorEmail}
              className="w-full h-10 bg-black text-white text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-2 disabled:opacity-50 rounded-none border border-black"
            >
              {actionLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Gửi lời mời"
              )}
            </button>
          </div>
        </aside>

        <main className="lg:col-span-8">
          <div className="border border-zinc-200 bg-white p-8">
            <div className="border-b border-zinc-200 pb-4 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-black flex items-center gap-2">
                  <Mail className="w-4 h-4" /> Lời mời đang chờ
                </h3>
                <p className="text-xs text-zinc-500 font-medium mt-1">
                  Danh sách yêu cầu cộng tác tài liệu
                </p>
              </div>
              <span className="text-xs font-semibold text-black">
                {invites.length} yêu cầu
              </span>
            </div>

            <div className="pt-4">
              {invites.length > 0 ? (
                <div className="space-y-4">
                  {invites.map((invite) => (
                    <div
                      key={invite._id}
                      className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border border-zinc-200 bg-zinc-50 gap-4"
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 border border-zinc-200 bg-white flex items-center justify-center shrink-0 rounded-none">
                          <span className="text-xs font-bold text-black uppercase">
                            {invite.inviter_name?.charAt(0) || "U"}
                          </span>
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-black">
                            {invite.document_title}
                          </h4>
                          <p className="text-[10px] font-medium text-zinc-500 mt-1">
                            Từ: <span className="text-black">{invite.inviter_name}</span> • Vai trò:{" "}
                            <span className="text-black uppercase">
                              {invite.role === "editor"
                                ? "Biên tập viên"
                                : "Người xem"}
                            </span>
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2 shrink-0">
                        <button
                          onClick={() => handleRespond(invite._id, "REJECTED")}
                          className="px-4 py-2 bg-white border border-zinc-200 text-black text-xs font-medium rounded-none"
                        >
                          Từ chối
                        </button>
                        <button
                          onClick={() => handleRespond(invite._id, "ACCEPTED")}
                          className="px-4 py-2 bg-black border border-black text-white text-xs font-medium rounded-none flex items-center gap-2"
                        >
                          <Check className="w-3 h-3" /> Chấp nhận
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-12 flex flex-col items-center justify-center gap-2 bg-zinc-50 border border-dashed border-zinc-200 rounded-none">
                  <Mail className="w-5 h-5 text-zinc-400 mb-2" />
                  <span className="text-xs font-semibold text-black">
                    Không có lời mời nào
                  </span>
                  <span className="text-[10px] font-medium text-zinc-500">
                    Bạn hiện không có yêu cầu cộng tác đang chờ xử lý
                  </span>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
