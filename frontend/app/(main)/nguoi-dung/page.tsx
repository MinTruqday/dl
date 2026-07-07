"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  getUsersAPI,
  updateUserRoleAPI,
  updateUserStatusAPI,
  deleteUserAPI,
  createUserAPI,
} from "@/features/management/services/profile.service";
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
  X
} from "lucide-react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
import PageLoader from "@/shared/components/common/PageLoader";

export default function UsersManagementPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();
  const [users, setUsers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [showSearch, setShowSearch] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [viewMode, setViewMode] = useState<"all" | "reader" | "author" | "admin">("all");
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newUserForm, setNewUserForm] = useState({
    email: "",
    full_name: "",
    password: "",
    role: "reader",
  });

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

  const handleCreateUser = async () => {
    if (!newUserForm.email || !newUserForm.password || !newUserForm.full_name) {
      showToast("Vui lòng điền đầy đủ thông tin", "error");
      return;
    }
    setIsCreating(true);
    try {
      await createUserAPI(newUserForm);
      showToast("Tạo người dùng thành công", "success");
      setCreateModalOpen(false);
      setNewUserForm({ email: "", full_name: "", password: "", role: "reader" });
      fetchData();
    } catch (e: any) {
      showToast(e.message || "Lỗi tạo người dùng", "error");
    } finally {
      setIsCreating(false);
    }
  };

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await getUsersAPI(100, 0);
      setUsers(data.data || data || []);
    } catch (err: any) {
      showToast("Lỗi tải danh sách nhân sự", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
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

  useEffect(() => {
    if (showSearch && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [showSearch]);

  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      u.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (u.full_name || "").toLowerCase().includes(searchQuery.toLowerCase());
    
    let matchesView = true;
    const role = u.role || "reader";
    if (viewMode === "reader") matchesView = role === "reader";
    if (viewMode === "author") matchesView = role === "author";
    if (viewMode === "admin") matchesView = role === "admin" || role === "moderator";
    
    return matchesSearch && matchesView;
  });

  if (authLoading || isLoading) return <PageLoader />;
  if (user?.role !== "admin")
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-56px)] gap-6 font-sans text-center">
        <div className="w-24 h-24 bg-[#F5F5F7] flex items-center justify-center rounded-[18px]">
          <AlertTriangle className="w-10 h-10 text-[#FF9500]" />
        </div>
        <div className="space-y-2 max-w-[300px]">
          <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
            Truy cập bị hạn chế
          </p>
          <p className="text-[15px] text-[#6E6E73]">
            Bạn không có quyền quản trị để truy cập trang này.
          </p>
        </div>
      </div>
    );

  return (
    <div className="w-full h-full font-sans text-[#1D1D1F]">
      <div className="flex flex-col">
        <main className="flex-1 min-w-0 space-y-8 pt-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex-1">
              {!showSearch ? (
                <div className="relative inline-block w-fit">
                  <select
                    value={viewMode}
                    onChange={(e) => setViewMode(e.target.value as any)}
                    className="w-full bg-transparent h-10 pr-8 text-[20px] font-semibold text-[#1D1D1F] focus:outline-none appearance-none cursor-pointer"
                  >
                    <option value="all">Tất cả</option>
                    <option value="reader">Độc giả</option>
                    <option value="author">Tác giả</option>
                    <option value="admin">Quản trị viên</option>
                  </select>
                  <ChevronRight className="absolute right-0 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6E6E73] pointer-events-none rotate-90" />
                </div>
              ) : (
                <div className="relative w-full max-w-md">
                  <input
                    ref={searchInputRef}
                    type="text"
                    placeholder="Tìm kiếm email, tên..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-[#F5F5F7] h-10 px-4 pr-10 text-[15px] rounded-full focus:outline-none focus:ring-2 focus:ring-[#0071E3]/20 transition-all border border-transparent focus:border-[#0071E3]/20"
                  />
                  <button
                    onClick={() => {
                      setShowSearch(false);
                      setSearchQuery("");
                    }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-[#6E6E73] hover:text-[#1D1D1F] rounded-full transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              {!showSearch && (
                <button
                  onClick={() => setShowSearch(true)}
                  className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
                  title="Tìm kiếm"
                >
                  <Search className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={fetchData}
                disabled={isRefreshing}
                className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors disabled:opacity-50"
                title="Làm mới"
              >
                <RefreshCcw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
              </button>
              <button
                onClick={() => setCreateModalOpen(true)}
                className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
                title="Thêm mới"
              >
                <UserPlus className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="w-full overflow-x-auto min-h-[400px] transition-colors">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="text-[13px] text-[#6E6E73] border-b border-[#E8E8ED]">
                  <th className="py-3 px-6 font-medium whitespace-nowrap text-center">Tên tài khoản</th>
                  <th className="py-3 px-6 font-medium whitespace-nowrap text-center">Email</th>
                  <th className="py-3 px-6 font-medium whitespace-nowrap text-center">Tên hiển thị</th>
                  <th className="py-3 px-6 font-medium whitespace-nowrap text-center">Quyền hạn</th>
                  <th className="py-3 px-6 font-medium whitespace-nowrap text-center hidden lg:table-cell">Tham gia</th>
                  <th className="py-3 px-6 font-medium whitespace-nowrap text-center hidden md:table-cell">Trạng thái</th>
                  <th className="py-3 px-6 font-medium whitespace-nowrap text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={7}>
                      <div className="py-24 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] w-full text-center my-4">
                        <p className="text-[17px] text-[#6E6E73]">Chưa có dữ liệu</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((u) => (
                    <tr
                      key={u._id}
                      className="hover:bg-[#E8E8ED]/60 transition-colors group cursor-default"
                    >
                      <td className="py-3 px-6 text-center">
                        <span className="font-medium text-[14px] text-[#1D1D1F]">@{u.slug || u._id?.substring(0,8)}</span>
                      </td>
                      <td className="py-3 px-6 text-center">
                        <span className="text-[14px] text-[#6E6E73]">
                          {u.email}
                        </span>
                      </td>
                      <td className="py-3 px-6 text-center">
                        <span className="font-medium text-[14px] text-[#1D1D1F] truncate max-w-[200px] inline-block">
                          {u.full_name || "Thành viên DocLib"}
                        </span>
                      </td>
                      <td className="py-3 px-6 text-center">
                        <div className="relative inline-block w-full max-w-[150px] text-left">
                          <select
                            value={u.role || "reader"}
                            onChange={(e) =>
                              setConfirmModal({
                                type: "role",
                                user: u,
                                value: e.target.value,
                              })
                            }
                            className={`w-full bg-transparent h-[32px] px-2 text-[13px] font-medium rounded-md focus:outline-none appearance-none transition-colors hover:bg-[#D2D2D7]/50 ${u.role === "admin" ? "text-[#0071E3]" : "text-[#1D1D1F]"}`}
                          >
                            <option value="reader">Độc giả</option>
                            <option value="author">Tác giả</option>
                            <option value="moderator">Điều hành</option>
                            <option value="admin">Quản trị</option>
                          </select>
                          <ChevronRight className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6E6E73] pointer-events-none" />
                        </div>
                      </td>
                      <td className="py-3 px-6 text-[#6E6E73] text-[13px] hidden md:table-cell text-center">
                        {u.created_at
                          ? new Date(u.created_at).toLocaleDateString("vi-VN")
                          : "---"}
                      </td>
                      <td className="py-3 px-6 hidden md:table-cell text-center">
                        <div
                          className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-[12px] font-medium whitespace-nowrap ${u.is_active ? "bg-[#E8F5E9] text-[#34C759]" : "bg-[#FF3B30]/10 text-[#FF3B30]"}`}
                        >
                          {u.is_active ? "Hoạt động" : "Tạm khóa"}
                        </div>
                      </td>
                      <td className="py-3 px-6 text-right relative">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setOpenDropdownId(
                              openDropdownId === u._id ? null : u._id,
                            );
                          }}
                          className="p-2 text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#D2D2D7]/50 rounded-full transition-colors opacity-0 group-hover:opacity-100"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>
                        {openDropdownId === u._id && (
                          <>
                            <div
                              className="fixed inset-0 z-40"
                              onClick={() => setOpenDropdownId(null)}
                            />
                            <div className="absolute right-6 top-10 mt-1 w-44 bg-white shadow-[0_4px_24px_rgba(0,0,0,0.08)] border border-[#E8E8ED] rounded-[10px] z-50 overflow-hidden py-1">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setOpenDropdownId(null);
                                  setConfirmModal({
                                    type: "status",
                                    user: u,
                                    value: !u.is_active,
                                  });
                                }}
                                className="w-full text-left px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors flex items-center gap-2"
                              >
                                {u.is_active ? (
                                  <Lock className="w-4 h-4 text-[#6E6E73]" />
                                ) : (
                                  <Unlock className="w-4 h-4 text-[#6E6E73]" />
                                )}{" "}
                                {u.is_active ? "Khóa tài khoản" : "Kích hoạt"}
                              </button>
                              <div className="w-full h-[1px] bg-[#E8E8ED] my-1"></div>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setOpenDropdownId(null);
                                  handleDeleteUser(u);
                                }}
                                className="w-full text-left px-4 py-2 text-[14px] text-[#FF3B30] hover:bg-[#FF3B30]/10 transition-colors flex items-center gap-2"
                              >
                                <Trash2 className="w-4 h-4" /> Xóa dữ liệu
                              </button>
                            </div>
                          </>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </main>
      </div>

      <Modal
        isOpen={!!confirmModal}
        onClose={() => !isUpdating && setConfirmModal(null)}
      >
        <ModalHeader>
          <ModalTitle>Xác nhận thay đổi</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-[15px] text-[#6E6E73] leading-relaxed">
            {confirmModal?.type === "role"
              ? `Thay đổi quyền hạn của "${confirmModal.user.full_name || confirmModal.user.email}" thành "${confirmModal.value === "reader" ? "Độc giả" : confirmModal.value === "author" ? "Tác giả" : confirmModal.value === "moderator" ? "Điều hành viên" : "Quản trị viên"}"?`
              : `Bạn có chắc chắn muốn ${confirmModal?.value ? "kích hoạt" : "vô hiệu hóa"} tài khoản của "${confirmModal?.user.full_name || confirmModal?.user.email}"?`}
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setConfirmModal(null)}
            disabled={isUpdating}
            className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full disabled:opacity-50"
          >
            Hủy
          </button>
          <button
            onClick={() => {
              if (confirmModal?.type === "role") handleUpdateRole();
              else if (confirmModal?.type === "status") handleUpdateStatus();
            }}
            disabled={isUpdating}
            className="pill-button disabled:opacity-50 flex items-center gap-2"
          >
            {isUpdating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Xác nhận"}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={createModalOpen}
        onClose={() => !isCreating && setCreateModalOpen(false)}
      >
        <ModalHeader>
          <ModalTitle>Thêm người dùng mới</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-4 text-[#1D1D1F]">
            <div>
              <label className="block text-[13px] font-medium text-[#6E6E73] mb-1">Họ và tên</label>
              <input
                type="text"
                placeholder="Nhập họ và tên"
                value={newUserForm.full_name}
                onChange={(e) => setNewUserForm({ ...newUserForm, full_name: e.target.value })}
                className="w-full bg-[#F5F5F7] h-10 px-4 text-[15px] rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[#0071E3]/20 transition-all border border-transparent focus:border-[#0071E3]/20"
              />
            </div>
            <div>
              <label className="block text-[13px] font-medium text-[#6E6E73] mb-1">Email đăng nhập</label>
              <input
                type="email"
                placeholder="example@doclib.com"
                value={newUserForm.email}
                onChange={(e) => setNewUserForm({ ...newUserForm, email: e.target.value })}
                className="w-full bg-[#F5F5F7] h-10 px-4 text-[15px] rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[#0071E3]/20 transition-all border border-transparent focus:border-[#0071E3]/20"
              />
            </div>
            <div>
              <label className="block text-[13px] font-medium text-[#6E6E73] mb-1">Mật khẩu</label>
              <input
                type="password"
                placeholder="Mật khẩu ít nhất 6 ký tự"
                value={newUserForm.password}
                onChange={(e) => setNewUserForm({ ...newUserForm, password: e.target.value })}
                className="w-full bg-[#F5F5F7] h-10 px-4 text-[15px] rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[#0071E3]/20 transition-all border border-transparent focus:border-[#0071E3]/20"
              />
            </div>
            <div>
              <label className="block text-[13px] font-medium text-[#6E6E73] mb-1">Quyền hạn</label>
              <div className="relative inline-block w-full">
                <select
                  value={newUserForm.role}
                  onChange={(e) => setNewUserForm({ ...newUserForm, role: e.target.value })}
                  className="w-full bg-[#F5F5F7] h-10 px-4 pr-10 text-[15px] rounded-[10px] focus:outline-none appearance-none transition-all border border-transparent focus:border-[#0071E3]/20"
                >
                  <option value="reader">Độc giả</option>
                  <option value="author">Tác giả</option>
                  <option value="moderator">Điều hành</option>
                  <option value="admin">Quản trị viên</option>
                </select>
                <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6E6E73] pointer-events-none" />
              </div>
            </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setCreateModalOpen(false)}
            disabled={isCreating}
            className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full disabled:opacity-50"
          >
            Hủy
          </button>
          <button
            onClick={handleCreateUser}
            disabled={isCreating}
            className="pill-button disabled:opacity-50 flex items-center gap-2"
          >
            {isCreating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Thêm mới"}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
