"use client";

import { useEffect, useState, useCallback } from "react";
import { getAdminUsersAPI, updateUserRoleAPI, updateUserStatusAPI, deleteUserAPI } from "@/features/provision/services/user_profile.service";
import { Loader2, Search, RefreshCcw, UserPlus, Mail, ChevronRight, Lock, Unlock, AlertTriangle, MoreVertical, Trash2, Users } from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from "@/shared/components/ui/Modal";

export default function UsersManagementPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();
  const [users, setUsers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [confirmModal, setConfirmModal] = useState<{ type: "role" | "status"; user: any; value: any; } | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [openDropdownId, setOpenDropdownId] = useState<string | null>(null);

  const handleDeleteUser = async (user: any) => {
    if (!window.confirm(`Xác nhận đưa tài khoản ${user.email} vào thùng rác?`)) return;
    setIsUpdating(true);
    try { await deleteUserAPI(user._id); showToast("Xóa tài khoản thành công", "success"); fetchData(); } catch (err: any) { showToast(err.message || "Lỗi xóa tài khoản", "error"); } finally { setIsUpdating(false); }
  };

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try { const data = await getAdminUsersAPI(); setUsers(data.data || data || []); } catch (err: any) { showToast("Lỗi tải danh sách nhân sự", "error"); } finally { setIsRefreshing(false); setIsLoading(false); }
  }, [showToast]);

  useEffect(() => { if (!authLoading && user?.role === "admin") { fetchData(); } }, [user, authLoading, fetchData]);

  const handleUpdateRole = async () => {
    if (!confirmModal) return; setIsUpdating(true);
    try { await updateUserRoleAPI(confirmModal.user._id, confirmModal.value); showToast("Cập nhật quyền hạn thành công", "success"); fetchData(); setConfirmModal(null); } catch (err: any) { showToast(err.message || "Lỗi cập nhật quyền", "error"); } finally { setIsUpdating(false); }
  };

  const handleUpdateStatus = async () => {
    if (!confirmModal) return; setIsUpdating(true);
    try { await updateUserStatusAPI(confirmModal.user._id, confirmModal.value); showToast(confirmModal.value ? "Đã kích hoạt tài khoản" : "Đã vô hiệu hóa tài khoản", "success"); fetchData(); setConfirmModal(null); } catch (err: any) { showToast(err.message || "Lỗi cập nhật trạng thái", "error"); } finally { setIsUpdating(false); }
  };

  const filteredUsers = users.filter(u => u.email?.toLowerCase().includes(searchQuery.toLowerCase()) || (u.full_name || "").toLowerCase().includes(searchQuery.toLowerCase()));

  if (authLoading || isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" /></div>;
  if (user?.role !== "admin") return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-56px)] gap-6 font-sans text-center">
      <div className="w-24 h-24 bg-[#F5F5F7] flex items-center justify-center rounded-[24px]"><AlertTriangle className="w-10 h-10 text-[#FF9500]" /></div>
      <div className="space-y-2 max-w-[300px]"><h2 className="text-[20px] font-semibold text-[#1D1D1F]">Truy cập bị hạn chế</h2><p className="text-[15px] text-[#6E6E73]">Bạn không có quyền quản trị để truy cập trang này.</p></div>
    </div>
  );

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] font-sans text-[#1D1D1F] flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-center justify-end gap-4">

        <div className="flex items-center gap-3">
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6E6E73]" />
            <input type="text" placeholder="Tìm kiếm..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="apple-input w-full pl-9 bg-[#F5F5F7] border-transparent" />
          </div>
          <button onClick={fetchData} disabled={isRefreshing} className="w-10 h-10 flex items-center justify-center bg-[#F5F5F7] text-[#1D1D1F] rounded-[12px] hover:bg-[#E8E8ED] transition-colors">{isRefreshing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCcw className="w-4 h-4" />}</button>
          <button className="pill-button flex items-center gap-2 bg-[#0071E3] text-white hover:bg-[#0077ED]"><UserPlus className="w-4 h-4" /> Thêm mới</button>
        </div>
      </div>

      <div className="bg-white rounded-[24px] border border-[#E8E8ED] shadow-sm flex-1 overflow-y-auto no-scrollbar">
        <table className="w-full text-left text-[14px]">
          <thead className="sticky top-0 bg-white z-10">
            <tr className="border-b border-[#E8E8ED] text-[13px] text-[#6E6E73]">
              <th className="px-6 py-4 font-medium w-[35%]">Thành viên</th>
              <th className="px-6 py-4 font-medium w-[20%]">Quyền hạn</th>
              <th className="px-6 py-4 font-medium w-[20%]">Tham gia</th>
              <th className="px-6 py-4 font-medium w-[15%]">Trạng thái</th>
              <th className="px-6 py-4 font-medium text-right w-[10%]">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.map(u => (
              <tr key={u._id} className="border-b border-[#F5F5F7] hover:bg-[#F5F5F7] transition-colors group">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-[#F5F5F7] text-[#1D1D1F] flex items-center justify-center font-semibold rounded-full overflow-hidden shrink-0 border border-[#E8E8ED]">
                      {u.avatar_url ? <img src={u.avatar_url} alt="" className="w-full h-full object-cover" /> : (u.full_name || u.email || "?")[0].toUpperCase()}
                    </div>
                    <div className="flex flex-col">
                      <span className="font-medium text-[#1D1D1F] truncate max-w-[200px]">{u.full_name || "Thành viên DocLib"}</span>
                      <span className="text-[12px] text-[#6E6E73] flex items-center gap-1 mt-0.5"><Mail className="w-3 h-3" /> {u.email}</span>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="relative inline-block w-full max-w-[150px]">
                    <select value={u.role} onChange={(e) => setConfirmModal({ type: "role", user: u, value: e.target.value })} className={`w-full bg-[#F5F5F7] h-[32px] px-3 text-[13px] font-medium rounded-full focus:outline-none appearance-none transition-colors border border-transparent hover:border-[#E8E8ED] ${u.role === "admin" ? "text-[#0071E3] bg-[#E8F3FF]" : "text-[#1D1D1F]"}`}>
                      <option value="reader">Độc giả</option><option value="potential_author">Tác giả tiềm năng</option><option value="author">Tác giả</option><option value="moderator">Điều hành</option><option value="admin">Quản trị</option>
                    </select>
                    <ChevronRight className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6E6E73] pointer-events-none" />
                  </div>
                </td>
                <td className="px-6 py-4 text-[#6E6E73]">{u.created_at ? new Date(u.created_at).toLocaleDateString("vi-VN") : "---"}</td>
                <td className="px-6 py-4">
                  <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[12px] font-medium ${u.is_active ? "bg-[#E8F5E9] text-[#34C759]" : "bg-[#FF3B30]/10 text-[#FF3B30]"}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${u.is_active ? "bg-[#34C759]" : "bg-[#FF3B30]"}`}></div>
                    {u.is_active ? "Hoạt động" : "Tạm khóa"}
                  </div>
                </td>
                <td className="px-6 py-4 text-right relative">
                  <button onClick={(e) => { e.stopPropagation(); setOpenDropdownId(openDropdownId === u._id ? null : u._id); }} className="p-2 text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors opacity-0 group-hover:opacity-100"><MoreVertical className="w-4 h-4" /></button>
                  {openDropdownId === u._id && (
                    <>
                      <div className="fixed inset-0 z-40" onClick={() => setOpenDropdownId(null)} />
                      <div className="absolute right-6 top-10 mt-1 w-44 bg-white border border-[#E8E8ED] rounded-[14px] shadow-lg z-50 overflow-hidden py-1">
                        <button onClick={(e) => { e.stopPropagation(); setOpenDropdownId(null); setConfirmModal({ type: "status", user: u, value: !u.is_active }); }} className="w-full text-left px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors flex items-center gap-2">{u.is_active ? <Lock className="w-4 h-4 text-[#6E6E73]" /> : <Unlock className="w-4 h-4 text-[#6E6E73]" />} {u.is_active ? "Khóa tài khoản" : "Kích hoạt"}</button>
                        <button onClick={(e) => { e.stopPropagation(); setOpenDropdownId(null); showToast("Tính năng đang phát triển", "error"); }} className="w-full text-left px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-[#6E6E73]" /> Cảnh báo</button>
                        <div className="w-full h-[1px] bg-[#E8E8ED] my-1"></div>
                        <button onClick={(e) => { e.stopPropagation(); setOpenDropdownId(null); handleDeleteUser(u); }} className="w-full text-left px-4 py-2 text-[14px] text-[#FF3B30] hover:bg-[#FF3B30]/10 transition-colors flex items-center gap-2"><Trash2 className="w-4 h-4" /> Xóa dữ liệu</button>
                      </div>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {filteredUsers.length === 0 && (
              <tr>
                <td colSpan={5} className="py-24 text-center">
                  <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                    <div className="w-16 h-16 bg-[#F5F5F7] rounded-[16px] flex items-center justify-center mb-4"><Search className="w-8 h-8 text-[#C7C7CC]" /></div>
                    <h2 className="text-[17px] font-medium text-[#1D1D1F] mb-1">Không tìm thấy</h2>
                    <p className="text-[14px] text-[#6E6E73]">Thử với một từ khóa khác.</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <Modal isOpen={!!confirmModal} onClose={() => !isUpdating && setConfirmModal(null)} className="max-w-md bg-[#F5F5F7] rounded-[24px] p-0 shadow-2xl border-none">
        <ModalHeader className="p-6 pb-2"><ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">Xác nhận thay đổi</ModalTitle></ModalHeader>
        <ModalContent className="p-6 pt-2">
          <p className="text-[15px] text-[#6E6E73] leading-relaxed">
            {confirmModal?.type === "role" ? `Thay đổi quyền hạn của "${confirmModal.user.full_name || confirmModal.user.email}" thành "${confirmModal.value === "reader" ? "Độc giả" : confirmModal.value === "potential_author" ? "Tác giả tiềm năng" : confirmModal.value === "author" ? "Tác giả" : confirmModal.value === "moderator" ? "Điều hành viên" : "Quản trị viên"}"?` : `Bạn có chắc chắn muốn ${confirmModal?.value ? "kích hoạt" : "vô hiệu hóa"} tài khoản của "${confirmModal?.user.full_name || confirmModal?.user.email}"?`}
          </p>
        </ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3"><button onClick={() => setConfirmModal(null)} disabled={isUpdating} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full disabled:opacity-50">Hủy</button><button onClick={() => { if (confirmModal?.type === "role") handleUpdateRole(); else if (confirmModal?.type === "status") handleUpdateStatus(); }} disabled={isUpdating} className="pill-button disabled:opacity-50 flex items-center gap-2">{isUpdating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Xác nhận"}</button></ModalFooter>
      </Modal>
    </div>
  );
}
