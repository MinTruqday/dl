"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getAdminUsersAPI,
  updateUserRoleAPI,
  updateUserStatusAPI,
  deleteUserAPI,
} from "@/features/provision/services/user_profile.service";
import {
  Loader2,
  Search,
  RefreshCcw,
  UserPlus,
  Mail,
  ChevronRight,
  ShieldCheck,
  Lock,
  Unlock,
  AlertTriangle,
  MoreVertical,
  Trash2,
} from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";

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
  const [openDropdownId, setOpenDropdownId] = useState<string | null>(null);

  const handleDeleteUser = async (user: any) => {
    if (!window.confirm(`Xác nhận đưa tài khoản ${user.email} vào thùng rác?`))
      return;
    setIsUpdating(true);
    try {
      await deleteUserAPI(user._id);
      showToast("Xóa tài khoản thành công", "success");
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Lỗi xóa tài khoản", "error");
    } finally {
      setIsUpdating(false);
    }
  };

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
      await updateUserRoleAPI(confirmModal.user._id, confirmModal.value);
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
      await updateUserStatusAPI(confirmModal.user._id, confirmModal.value);
      showToast(
        confirmModal.value
          ? "Đã kích hoạt tài khoản"
          : "Đã vô hiệu hóa tài khoản",
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
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col gap-6 font-sans text-black selection:bg-black selection:text-white">
      <div className="flex flex-col gap-6 h-full min-h-0">
        <div className="border border-zinc-200 bg-white rounded-3xl shadow-sm p-5 flex flex-col md:flex-row gap-4 items-center justify-between shrink-0">
          <div className="relative w-full md:w-96">
            <div className="absolute left-4 top-1/2 -translate-y-1/2">
              <Search className="w-4 h-4 text-zinc-400" />
            </div>
            <input
              type="text"
              placeholder="Tìm kiếm email hoặc tên thành viên"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full h-10 pl-11 pr-4 bg-zinc-50 border border-zinc-200 focus:border-black outline-none text-sm text-black placeholder:text-zinc-400 rounded-xl transition-colors"
            />
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="h-10 px-4 border border-zinc-200 bg-white hover:bg-zinc-50 text-black text-sm font-medium flex items-center gap-2 rounded-xl disabled:opacity-50 transition-colors"
            >
              {isRefreshing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCcw className="w-4 h-4" />
              )}
              <span className="hidden sm:inline">Đồng bộ</span>
            </button>
            <button className="h-10 px-6 bg-black hover:bg-zinc-800 text-white text-sm font-medium flex items-center gap-2 rounded-xl transition-colors">
              <UserPlus className="w-4 h-4" />
              <span className="hidden sm:inline">Thêm tài khoản</span>
            </button>
          </div>
        </div>

        <div className="bg-white border border-zinc-200 rounded-3xl shadow-sm overflow-hidden flex flex-col flex-1 min-h-0">
          <div className="overflow-y-auto custom-scrollbar flex-1">
            <table className="w-full text-left text-sm border-collapse">
              <thead className="sticky top-0 bg-zinc-50/90 backdrop-blur-sm z-10">
                <tr className="border-b border-zinc-200 text-zinc-600 font-medium">
                  <th className="w-[30%] px-6 py-4 font-medium whitespace-nowrap">
                    Thành viên hệ thống
                  </th>
                  <th className="w-[20%] px-6 py-4 font-medium whitespace-nowrap">
                    Quyền hạn truy cập
                  </th>
                  <th className="w-[20%] px-6 py-4 font-medium whitespace-nowrap">
                    Ngày tham gia
                  </th>
                  <th className="w-[20%] px-6 py-4 font-medium whitespace-nowrap">
                    Trạng thái vận hành
                  </th>
                  <th className="w-[10%] px-6 py-4 font-medium text-right whitespace-nowrap">
                    Quản trị
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200">
                {filteredUsers.map((u: any) => (
                  <tr key={u._id} className="group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-zinc-100 flex items-center justify-center text-zinc-500 font-medium rounded-xl overflow-hidden shrink-0">
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
                            setConfirmModal({
                              type: "role",
                              user: u,
                              value: e.target.value,
                            })
                          }
                          className={`w-full bg-transparent text-sm focus:outline-none cursor-pointer appearance-none ${u.role === "admin" ? "font-medium text-black" : "text-zinc-600"}`}
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
                        {u.created_at
                          ? new Date(u.created_at).toLocaleDateString("vi-VN")
                          : "---"}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="inline-flex items-center gap-2 px-2.5 py-1.5 bg-white border border-zinc-200 rounded-xl shadow-sm">
                        <div
                          className={`w-2 h-2 rounded-full ${u.is_active ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500"}`}
                        ></div>
                        <span
                          className={`text-[11px] font-bold uppercase tracking-widest ${u.is_active ? "text-black" : "text-red-500"}`}
                        >
                          {u.is_active ? "Hoạt động" : "Tạm khóa"}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="relative inline-block text-left">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setOpenDropdownId(
                              openDropdownId === u._id ? null : u._id,
                            );
                          }}
                          className="p-1.5 text-zinc-400 hover:text-black hover:bg-zinc-100 rounded-full transition-colors"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>

                        {openDropdownId === u._id && (
                          <>
                            <div
                              className="fixed inset-0 z-40"
                              onClick={(e) => {
                                e.stopPropagation();
                                setOpenDropdownId(null);
                              }}
                            />
                            <div className="absolute right-0 top-full mt-1 w-44 p-1.5 bg-white border border-zinc-200 rounded-2xl shadow-lg z-50">
                              <button
                                className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-100 rounded-xl transition-colors flex items-center gap-2"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setOpenDropdownId(null);
                                  setConfirmModal({
                                    type: "status",
                                    user: u,
                                    value: !u.is_active,
                                  });
                                }}
                              >
                                {u.is_active ? (
                                  <Lock className="w-3.5 h-3.5 text-zinc-500" />
                                ) : (
                                  <Unlock className="w-3.5 h-3.5 text-zinc-500" />
                                )}
                                {u.is_active ? "Khóa tài khoản" : "Kích hoạt"}
                              </button>
                              <button
                                className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-100 rounded-xl transition-colors flex items-center gap-2"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setOpenDropdownId(null);
                                  showToast(
                                    "Tính năng cảnh báo đang được phát triển",
                                    "error",
                                  );
                                }}
                              >
                                <AlertTriangle className="w-3.5 h-3.5 text-zinc-500" />
                                Cảnh báo
                              </button>
                              <button
                                className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-xl transition-colors flex items-center gap-2"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setOpenDropdownId(null);
                                  handleDeleteUser(u);
                                }}
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                                Xóa dữ liệu
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {filteredUsers.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-32 text-center">
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
        className="max-w-md rounded-3xl border border-zinc-200 bg-white p-0 shadow-xl overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-200 pb-4">
          <ModalTitle className="text-lg font-medium text-black">
            Xác nhận thay đổi
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="py-6">
          <p className="text-sm text-zinc-600 leading-relaxed">
            {confirmModal?.type === "role"
              ? `Bạn có chắc chắn muốn thay đổi quyền hạn của "${confirmModal.user.full_name || confirmModal.user.email}" thành "${
                  confirmModal.value === "reader"
                    ? "Độc giả"
                    : confirmModal.value === "potential_author"
                      ? "Tác giả tiềm năng"
                      : confirmModal.value === "author"
                        ? "Tác giả"
                        : confirmModal.value === "moderator"
                          ? "Điều hành viên"
                          : "Quản trị viên"
                }"?`
              : `Bạn có chắc chắn muốn ${confirmModal?.value ? "kích hoạt" : "vô hiệu hóa"} tài khoản của "${confirmModal?.user.full_name || confirmModal?.user.email}"?`}
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 p-4 bg-zinc-50 border-t border-zinc-200">
          <button
            onClick={() => setConfirmModal(null)}
            disabled={isUpdating}
            className="flex-1 h-10 border border-zinc-200 bg-white text-sm font-medium text-black rounded-xl hover:bg-zinc-50 transition-colors disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={() => {
              if (confirmModal?.type === "role") handleUpdateRole();
              else if (confirmModal?.type === "status") handleUpdateStatus();
            }}
            disabled={isUpdating}
            className="flex-1 h-10 bg-black hover:bg-zinc-800 text-white text-sm font-medium rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center"
          >
            {isUpdating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              "Xác nhận"
            )}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
