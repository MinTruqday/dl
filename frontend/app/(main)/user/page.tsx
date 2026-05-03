"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getAdminUsersAPI,
  updateUserRoleAPI,
  updateUserStatusAPI,
} from "@/services/user.service";
import {
  Users,
  Loader2,
  Search,
  Filter,
  ShieldCheck,
  RefreshCcw,
  UserPlus,
  Mail,
  MoreVertical,
  ChevronRight,
  ShieldAlert,
  Shield,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";

export default function UsersManagementPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();
  const [users, setUsers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [visible, setVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [confirmModal, setConfirmModal] = useState<{
    type: "role" | "status";
    user: any;
    value: any;
  } | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await getAdminUsersAPI();
      setUsers(data.data || data || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách nhân sự.", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  useEffect(() => {
    if (!authLoading && user?.role === "admin") {
      fetchData();
    }
  }, [user, authLoading, fetchData]);

  const handleUpdateRole = async () => {
    if (!confirmModal) return;
    setIsUpdating(true);
    try {
      await updateUserRoleAPI(confirmModal.user.id, confirmModal.value);
      showToast("Cập nhật quyền hạn thành công.", "success");
      fetchData();
      setConfirmModal(null);
    } catch (err: any) {
      showToast(err.message || "Lỗi cập nhật quyền.", "error");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleUpdateStatus = async () => {
    if (!confirmModal) return;
    setIsUpdating(true);
    try {
      await updateUserStatusAPI(confirmModal.user.id, confirmModal.value);
      showToast(
        confirmModal.value ? "Đã kích hoạt tài khoản." : "Đã vô hiệu hóa tài khoản.",
        "success",
      );
      fetchData();
      setConfirmModal(null);
    } catch (err: any) {
      showToast(err.message || "Lỗi cập nhật trạng thái.", "error");
    } finally {
      setIsUpdating(false);
    }
  };

  const filteredUsers = users.filter(
    (u) =>
      u.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (u.full_name || "").toLowerCase().includes(searchQuery.toLowerCase()),
  );

  if (authLoading || isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-white">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      <div
        className="mb-12 border-b border-zinc-100 pb-10 "
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(10px)",
        }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-4">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
              Quản lý nhân sự
            </h1>
            <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
              Hệ thống định danh & Phân quyền DocLib{" "}
              <ShieldCheck className="w-3.5 h-3.5 text-zinc-100" />
            </p>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="h-14 px-8 border border-zinc-100 text-black text-[11px] font-bold uppercase active:scale-[0.98] flex items-center gap-4 rounded-sm"
            >
              {isRefreshing ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <RefreshCcw className="w-5 h-5" />
              )}
              Đồng bộ
            </button>
            <button className="h-14 px-12 bg-black text-white text-[11px] font-bold tracking-[0.2em] uppercase active:scale-[0.98] flex items-center gap-4 rounded-sm">
              <UserPlus className="w-5 h-5" />
              Thêm tài khoản
            </button>
          </div>
        </div>
      </div>

      <div
        className=" delay-75 space-y-10"
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(10px)",
        }}
      >
        <div className="relative group">
          <div className="absolute left-6 top-1/2 -translate-y-1/2">
            <Search className="w-5 h-5 text-zinc-200 group-focus-within:text-black transition-colors" />
          </div>
          <input
            type="text"
            placeholder=""
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-16 pl-16 pr-8 bg-white border border-zinc-100 focus:border-black outline-none font-bold text-lg tracking-tight placeholder:text-zinc-100 rounded-sm"
          />
        </div>

        <div className="bg-white border border-zinc-100 rounded-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-white border-b border-zinc-100 text-zinc-300 text-[9px] font-bold uppercase tracking-[0.2em]">
                  <th className="px-10 py-6">Thành viên hệ thống</th>
                  <th className="px-10 py-6">Quyền hạn truy cập</th>
                  <th className="px-10 py-6">Trạng thái vận hành</th>
                  <th className="px-10 py-6 text-right">Quản trị</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-50">
                {filteredUsers.map((u: any) => (
                  <tr key={u.id} className=" group">
                    <td className="px-10 py-10">
                      <div className="flex items-center gap-8">
                        <div className="w-14 h-14 bg-white flex items-center justify-center border border-zinc-100 font-black text-zinc-200 rounded-sm overflow-hidden">
                          {u.avatar_url ? (
                            <img
                              src={u.avatar_url}
                              alt=""
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            (u.full_name || u.email)[0].toUpperCase()
                          )}
                        </div>
                        <div className="flex flex-col gap-2 min-w-0">
                          <span className="font-bold text-black text-base tracking-tighter truncate max-w-xs">
                            {u.full_name || "Thành viên DocLib"}
                          </span>
                          <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2">
                            <Mail className="w-3 h-3" /> {u.email}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="px-10 py-10">
                      <div className="relative inline-block w-full max-w-[200px]">
                        <select
                          value={u.role}
                          onChange={(e) =>
                            setConfirmModal({ type: "role", user: u, value: e.target.value })
                          }
                          className="w-full bg-transparent border-b border-zinc-100 text-[10px] font-bold uppercase tracking-widest focus:border-black outline-none py-3 cursor-pointer appearance-none  "
                        >
                          <option value="reader">Độc giả</option>
                          <option value="potential_author">
                            Tác giả tiềm năng
                          </option>
                          <option value="author">Tác giả</option>
                          <option value="moderator">Điều hành viên</option>
                          <option value="admin">Quản trị viên</option>
                        </select>
                        <ChevronRight className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 text-zinc-200 pointer-events-none transition-colors" />
                      </div>
                    </td>
                    <td className="px-10 py-10">
                      <div className="flex items-center gap-4">
                        <div
                          className={`w-2.5 h-2.5 rounded-full ${u.is_active ? "bg-black scale-110" : "bg-zinc-100"}`}
                        />
                        <span
                          className={`text-[10px] font-bold uppercase tracking-widest transition-colors ${u.is_active ? "text-black" : "text-zinc-200"}`}
                        >
                          {u.is_active ? "Đang hoạt động" : "Đã vô hiệu hóa"}
                        </span>
                      </div>
                    </td>
                    <td className="px-10 py-10 text-right">
                      <div className="flex justify-end gap-3">
                        <button
                          onClick={() => setConfirmModal({ type: "status", user: u, value: !u.is_active })}
                          className={`h-11 px-8 text-[9px] font-bold uppercase tracking-[0.2em] border rounded-sm active:scale-95 transition-transform ${
                            u.is_active
                              ? "text-zinc-300 border-zinc-100"
                              : "text-black border-black"
                          }`}
                        >
                          {u.is_active ? "Khóa tài khoản" : "Kích hoạt lại"}
                        </button>
                        <button className="h-11 w-11 border border-zinc-100 flex items-center justify-center text-zinc-100 rounded-sm">
                          <MoreVertical className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filteredUsers.length === 0 && (
                  <tr>
                    <td
                      colSpan={4}
                      className="py-48 text-center border-dashed border-2 border-zinc-50 rounded-sm"
                    >
                      <div className="flex flex-col items-center gap-6">
                        <Search className="w-16 h-16 text-zinc-50 stroke-[1]" />
                        <p className="text-[11px] font-bold text-zinc-200 uppercase tracking-[0.2em]">
                          Không tìm thấy thành viên phù hợp
                        </p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <Modal
        isOpen={!!confirmModal}
        onClose={() => !isUpdating && setConfirmModal(null)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle>Xác nhận thay đổi</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-sm font-bold text-zinc-400 uppercase tracking-widest leading-relaxed">
            {confirmModal?.type === "role" ? 
              `Bạn có chắc chắn muốn thay đổi quyền hạn của "${confirmModal.user.full_name || confirmModal.user.email}" thành "${confirmModal.value}"?` :
              `Bạn có chắc chắn muốn ${confirmModal?.value ? "kích hoạt" : "vô hiệu hóa"} tài khoản của "${confirmModal?.user.full_name || confirmModal?.user.email}"?`}
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-4">
          <button
            onClick={() => setConfirmModal(null)}
            disabled={isUpdating}
            className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-all disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={() => {
              if (confirmModal?.type === "role") handleUpdateRole();
              else if (confirmModal?.type === "status") handleUpdateStatus();
            }}
            disabled={isUpdating}
            className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-all disabled:opacity-50 flex items-center justify-center"
          >
            {isUpdating ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xác nhận thay đổi"}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
