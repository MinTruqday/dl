"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getAdminUsersAPI,
  updateUserRoleAPI,
  updateUserStatusAPI,
} from "@/services/user.service";
import {
  Loader2,
  Search,
  RefreshCcw,
  UserPlus,
  Mail,
  ChevronRight,
  ShieldCheck,
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
      showToast("Không thể tải danh sách nhân sự", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [showToast]);

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
      showToast("Cập nhật quyền hạn thành công", "success");
      fetchData();
      setConfirmModal(null);
    } catch (err: any) {
      showToast(err.message || "Lỗi cập nhật quyền", "error");
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
        confirmModal.value ? "Đã kích hoạt tài khoản" : "Đã vô hiệu hóa tài khoản",
        "success",
      );
      fetchData();
      setConfirmModal(null);
    } catch (err: any) {
      showToast(err.message || "Lỗi cập nhật trạng thái", "error");
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
        <Loader2 className="w-8 h-8 animate-spin text-zinc-300" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white bg-white min-h-screen">
      <div
        className="mb-8 border-b border-zinc-200 pb-6"
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-medium text-black">
              Quản lý nhân sự
            </h1>
            <p className="text-zinc-500 text-sm flex items-center gap-2">
              Hệ thống định danh và phân quyền DocLib
              <ShieldCheck className="w-4 h-4 text-zinc-400" />
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="h-10 px-4 border border-zinc-200 text-black text-sm font-medium flex items-center gap-2 rounded-none disabled:opacity-50"
            >
              {isRefreshing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCcw className="w-4 h-4" />
              )}
              Đồng bộ
            </button>
            <button className="h-10 px-6 bg-black text-white text-sm font-medium flex items-center gap-2 rounded-none">
              <UserPlus className="w-4 h-4" />
              Thêm tài khoản
            </button>
          </div>
        </div>
      </div>

      <div
        className="space-y-6"
      >
        <div className="relative group">
          <div className="absolute left-4 top-1/2 -translate-y-1/2">
            <Search className="w-4 h-4 text-zinc-400" />
          </div>
          <input
            type="text"
            placeholder="Tìm kiếm email hoặc tên thành viên"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-12 pl-12 pr-4 bg-white border border-zinc-200 focus:border-black outline-none text-sm text-black placeholder:text-zinc-400 rounded-none"
          />
        </div>

        <div className="bg-white border border-zinc-200 rounded-none overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-zinc-50 border-b border-zinc-200 text-zinc-600 font-medium">
                  <th className="px-6 py-4 font-medium">Thành viên hệ thống</th>
                  <th className="px-6 py-4 font-medium">Quyền hạn truy cập</th>
                  <th className="px-6 py-4 font-medium">Ngày tham gia</th>
                  <th className="px-6 py-4 font-medium">Trạng thái vận hành</th>
                  <th className="px-6 py-4 font-medium text-right">Quản trị</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200">
                {filteredUsers.map((u: any) => (
                  <tr key={u.id} className="group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-white flex items-center justify-center border border-zinc-200 text-zinc-500 font-medium rounded-none overflow-hidden shrink-0">
                          {u.avatar_url ? (
                            <img
                              src={u.avatar_url}
                              alt=""
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            (u.full_name || u.email || "?")[0].toUpperCase()
                          )}
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="font-medium text-black truncate max-w-[200px]">
                            {u.full_name || "Thành viên DocLib"}
                          </span>
                          <span className="text-xs text-zinc-500 flex items-center gap-1.5 mt-0.5">
                            <Mail className="w-3 h-3" /> {u.email}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="relative inline-block w-full max-w-[160px]">
                        <select
                          value={u.role}
                          onChange={(e) =>
                            setConfirmModal({ type: "role", user: u, value: e.target.value })
                          }
                          className={`w-full bg-transparent text-sm focus:outline-none cursor-pointer appearance-none ${u.role === 'admin' ? 'font-medium text-black' : 'text-zinc-600'}`}
                        >
                          <option value="reader">Độc giả</option>
                          <option value="potential_author">
                            Tác giả tiềm năng
                          </option>
                          <option value="author">Tác giả</option>
                          <option value="moderator">Điều hành viên</option>
                          <option value="admin">Quản trị viên</option>
                        </select>
                        <ChevronRight className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 pointer-events-none" />
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-zinc-600">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString("vi-VN") : "---"}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="inline-block px-2 py-1 border border-zinc-200">
                        <span
                          className={`text-xs font-medium ${u.is_active ? "text-black" : "text-zinc-400"}`}
                        >
                          {u.is_active ? "Đang hoạt động" : "Đã khóa"}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end items-center gap-3">
                        <button
                          onClick={() => setConfirmModal({ type: "status", user: u, value: !u.is_active })}
                          className={`text-sm font-medium ${
                            u.is_active
                              ? "text-zinc-500"
                              : "text-black"
                          }`}
                        >
                          {u.is_active ? "Khóa tài khoản" : "Kích hoạt lại"}
                        </button>
                        <span className="text-zinc-300">|</span>
                        <button className="text-sm font-medium text-zinc-500">
                          Cảnh báo
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filteredUsers.length === 0 && (
                  <tr>
                    <td
                      colSpan={5}
                      className="py-32 text-center"
                    >
                      <div className="flex flex-col items-center gap-4">
                        <Search className="w-8 h-8 text-zinc-300" />
                        <p className="text-sm text-zinc-500">
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
        className="max-w-md rounded-none shadow-none"
      >
        <ModalHeader className="border-b border-zinc-200 pb-4">
          <ModalTitle className="text-lg font-medium text-black">Xác nhận thay đổi</ModalTitle>
        </ModalHeader>
        <ModalContent className="py-6">
          <p className="text-sm text-zinc-600 leading-relaxed">
            {confirmModal?.type === "role" ? 
              `Bạn có chắc chắn muốn thay đổi quyền hạn của "${confirmModal.user.full_name || confirmModal.user.email}" thành "${
                confirmModal.value === "reader" ? "Độc giả" :
                confirmModal.value === "potential_author" ? "Tác giả tiềm năng" :
                confirmModal.value === "author" ? "Tác giả" :
                confirmModal.value === "moderator" ? "Điều hành viên" : "Quản trị viên"
              }"?` :
              `Bạn có chắc chắn muốn ${confirmModal?.value ? "kích hoạt" : "vô hiệu hóa"} tài khoản của "${confirmModal?.user.full_name || confirmModal?.user.email}"?`}
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 pt-4 border-t border-zinc-200">
          <button
            onClick={() => setConfirmModal(null)}
            disabled={isUpdating}
            className="flex-1 h-10 border border-zinc-200 text-sm font-medium text-black rounded-none disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={() => {
              if (confirmModal?.type === "role") handleUpdateRole();
              else if (confirmModal?.type === "status") handleUpdateStatus();
            }}
            disabled={isUpdating}
            className="flex-1 h-10 bg-black text-white text-sm font-medium rounded-none disabled:opacity-50 flex items-center justify-center"
          >
            {isUpdating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Xác nhận thay đổi"}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
