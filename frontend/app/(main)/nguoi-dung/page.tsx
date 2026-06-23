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
  Lock,
  Unlock,
  AlertTriangle,
  MoreVertical,
  Trash2,
  Users,
} from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
  ModalDescription,
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
      <div className="flex h-[80vh] items-center justify-center bg-zinc-50">
        <Loader2 className="w-8 h-8 animate-spin text-black" />
      </div>
    );
  }

  if (user?.role !== "admin") {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-6 font-sans bg-zinc-50 px-6 text-center">
        <div className="w-20 h-20 bg-white shadow-sm flex items-center justify-center border border-zinc-100 rounded-3xl">
          <AlertTriangle className="w-8 h-8 text-zinc-400" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold tracking-tight text-zinc-900">
            Truy cập bị hạn chế
          </h2>
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
            Bạn không có quyền quản trị để xem trang này
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col gap-6 font-sans text-zinc-900 bg-zinc-50 selection:bg-black selection:text-white">
      <div className="flex flex-col gap-6 h-full min-h-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-4 md:p-5 flex flex-col md:flex-row gap-4 items-center justify-between shrink-0">
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="w-10 h-10 bg-zinc-50 border border-zinc-100 rounded-2xl flex items-center justify-center shrink-0 shadow-sm hidden md:flex">
              <Users className="w-4 h-4 text-black" />
            </div>
            <div className="relative w-full md:w-80">
              <div className="absolute left-4 top-1/2 -translate-y-1/2">
                <Search className="w-4 h-4 text-zinc-400" />
              </div>
              <input
                type="text"
                placeholder="Tìm kiếm thành viên..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-11 pl-11 pr-4 bg-white border border-zinc-200 focus:border-black outline-none text-sm font-medium text-zinc-900 placeholder:text-zinc-400 rounded-2xl shadow-sm transition-all"
              />
            </div>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto">
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="h-11 px-5 border border-zinc-200 bg-white hover:bg-zinc-50 text-zinc-900 text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 rounded-2xl disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] shadow-sm flex-1 md:flex-none"
            >
              {isRefreshing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCcw className="w-4 h-4" />
              )}
              <span className="hidden sm:inline">Đồng bộ</span>
            </button>
            <button className="h-11 px-6 bg-black text-white text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md flex-1 md:flex-none">
              <UserPlus className="w-4 h-4" />
              <span className="hidden sm:inline">Tạo mới</span>
            </button>
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm overflow-hidden flex flex-col flex-1 min-h-0">
          <div className="overflow-y-auto custom-scrollbar flex-1">
            <table className="w-full text-left text-sm border-collapse">
              <thead className="sticky top-0 bg-white/95 backdrop-blur-sm z-10">
                <tr className="border-b border-zinc-100 text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
                  <th className="w-[30%] px-6 py-4 whitespace-nowrap">
                    Thành viên hệ thống
                  </th>
                  <th className="w-[20%] px-6 py-4 whitespace-nowrap">
                    Quyền hạn
                  </th>
                  <th className="w-[20%] px-6 py-4 whitespace-nowrap">
                    Ngày tham gia
                  </th>
                  <th className="w-[20%] px-6 py-4 whitespace-nowrap">
                    Trạng thái
                  </th>
                  <th className="w-[10%] px-6 py-4 text-right whitespace-nowrap">
                    Hành động
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-50">
                {filteredUsers.map((u: any) => (
                  <tr key={u._id} className="group hover:bg-zinc-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-white border border-zinc-100 shadow-sm flex items-center justify-center text-zinc-500 font-bold rounded-2xl overflow-hidden shrink-0 group-hover:scale-110 transition-transform duration-300">
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
                          <span className="font-bold text-zinc-900 truncate max-w-[200px]">
                            {u.full_name || "Thành viên DocLib"}
                          </span>
                          <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-400 flex items-center gap-1.5 mt-1">
                            <Mail className="w-3 h-3 text-zinc-300" /> {u.email}
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
                          className={`w-full bg-zinc-50 border border-zinc-100 h-9 px-3 text-[10px] font-bold uppercase tracking-widest rounded-xl focus:outline-none focus:border-zinc-300 cursor-pointer appearance-none transition-all ${u.role === "admin" ? "text-black shadow-sm" : "text-zinc-600"}`}
                        >
                          <option value="reader">Độc giả</option>
                          <option value="potential_author">
                            Tác giả tiềm năng
                          </option>
                          <option value="author">Tác giả</option>
                          <option value="moderator">Điều hành viên</option>
                          <option value="admin">Quản trị viên</option>
                        </select>
                        <ChevronRight className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400 pointer-events-none" />
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                        {u.created_at
                          ? new Date(u.created_at).toLocaleDateString("vi-VN")
                          : "---"}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className={`inline-flex items-center gap-2 px-3 py-1.5 border rounded-xl shadow-sm ${u.is_active ? "bg-white border-zinc-100" : "bg-red-50 border-red-100"}`}>
                        <div
                          className={`w-1.5 h-1.5 rounded-full ${u.is_active ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"}`}
                        ></div>
                        <span
                          className={`text-[9px] font-bold uppercase tracking-widest ${u.is_active ? "text-zinc-900" : "text-red-600"}`}
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
                          className="p-2 text-zinc-400 hover:text-black hover:bg-white border border-transparent hover:border-zinc-200 rounded-xl transition-all shadow-sm opacity-0 group-hover:opacity-100"
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
                            <div className="absolute right-0 top-full mt-2 w-48 p-2 bg-white/95 backdrop-blur-md border border-zinc-100 rounded-2xl shadow-xl z-50">
                              <button
                                className="w-full text-left px-3 py-2.5 text-[10px] font-bold uppercase tracking-widest text-zinc-600 hover:text-black hover:bg-zinc-50 rounded-xl transition-colors flex items-center gap-2.5"
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
                                  <Lock className="w-3.5 h-3.5 text-zinc-400" />
                                ) : (
                                  <Unlock className="w-3.5 h-3.5 text-zinc-400" />
                                )}
                                {u.is_active ? "Khóa tài khoản" : "Kích hoạt"}
                              </button>
                              <button
                                className="w-full text-left px-3 py-2.5 text-[10px] font-bold uppercase tracking-widest text-zinc-600 hover:text-black hover:bg-zinc-50 rounded-xl transition-colors flex items-center gap-2.5"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setOpenDropdownId(null);
                                  showToast(
                                    "Tính năng cảnh báo đang được phát triển",
                                    "error",
                                  );
                                }}
                              >
                                <AlertTriangle className="w-3.5 h-3.5 text-zinc-400" />
                                Cảnh báo
                              </button>
                              <div className="w-full h-[1px] bg-zinc-100 my-1"></div>
                              <button
                                className="w-full text-left px-3 py-2.5 text-[10px] font-bold uppercase tracking-widest text-red-500 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors flex items-center gap-2.5"
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
                      <div className="flex flex-col items-center justify-center bg-white border border-zinc-100 rounded-3xl p-12 max-w-sm mx-auto shadow-sm">
                        <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
                          <Search className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
                        </div>
                        <h2 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-1">Không tìm thấy</h2>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                          Thử với một từ khóa khác
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
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md p-0 shadow-xl overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6">
          <ModalTitle className="text-sm font-bold text-black tracking-tight">
            Xác nhận thay đổi
          </ModalTitle>
          <ModalDescription className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mt-1">
            Hành động này có thể ảnh hưởng đến truy cập hệ thống
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 leading-relaxed">
            {confirmModal?.type === "role"
              ? `Thay đổi quyền hạn của "${confirmModal.user.full_name || confirmModal.user.email}" thành "${
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
        <ModalFooter className="flex gap-3 p-5 bg-zinc-50/50 border-t border-zinc-100 rounded-b-3xl">
          <button
            onClick={() => setConfirmModal(null)}
            disabled={isUpdating}
            className="flex-1 h-11 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-black rounded-2xl hover:bg-zinc-50 transition-all duration-200 hover:scale-[1.02] shadow-sm disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={() => {
              if (confirmModal?.type === "role") handleUpdateRole();
              else if (confirmModal?.type === "status") handleUpdateStatus();
            }}
            disabled={isUpdating}
            className="flex-1 h-11 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md disabled:opacity-50 flex items-center justify-center gap-2"
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
