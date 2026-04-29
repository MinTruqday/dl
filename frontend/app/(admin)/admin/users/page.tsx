"use client";

import { useEffect, useState, useCallback } from "react";
import { getToken, API_URL, formatError } from "@/app/lib/api";
import {
  Users,
  Loader2,
  Search,
  Filter,
  ShieldCheck,
  RefreshCcw,
  UserPlus
} from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";
import { Notification } from "@/app/components/NotificationToast";

export default function UsersManagementPage() {
  const { user, isLoading } = useAuth() as any;
  const [users, setUsers] = useState<any[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const headers = { Authorization: `Bearer ${getToken()}` };
      const res = await fetch(`${API_URL}/admin/users`, { headers });
      if (res.ok) {
        const data = await res.json();
        setUsers(data.data || data || []);
      }
    } catch (err: any) {
      console.error("Lỗi tải danh sách người dùng:", err);
    } finally {
      setIsRefreshing(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  useEffect(() => {
    if (!isLoading && user?.role === "admin") {
      fetchData();
    }
  }, [user, isLoading, fetchData]);

  const updateRole = async (userId: string, role: string) => {
    try {
      const res = await fetch(`${API_URL}/admin/users/${userId}/role`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });
      if (res.ok) {
        setNotification({ type: "success", text: "Đã cập nhật quyền hạn." });
        fetchData();
      }
    } catch (err: any) {
      console.error("Lỗi cập nhật quyền:", err);
    }
  };

  const updateStatus = async (userId: string, isActive: boolean) => {
    try {
      const res = await fetch(`${API_URL}/admin/users/${userId}/status`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: isActive }),
      });
      if (res.ok) {
        setNotification({ type: "success", text: isActive ? "Đã khôi phục tài khoản." : "Đã vô hiệu hóa tài khoản." });
        fetchData();
      }
    } catch (err: any) {
      console.error("Lỗi cập nhật trạng thái:", err);
    }
  };

  if (isLoading || !user) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-10 font-sans text-black">
      {notification && (
        <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      <div 
        className="mb-10 border-b border-zinc-100 pb-10 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-4">
            <h1 className="text-5xl font-bold tracking-tighter leading-none">Quản lý nhân sự</h1>
            <p className="text-zinc-400 text-[11px] font-bold uppercase tracking-[0.2em] flex items-center gap-2">
              Danh sách định danh & Quyền hạn hệ thống <ShieldCheck className="w-3.5 h-3.5" />
            </p>
          </div>
          
          <button 
            onClick={fetchData}
            disabled={isRefreshing}
            className="h-14 px-12 bg-black text-white text-[10px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all flex items-center gap-4 shadow-xl shadow-black/5"
          >
            {isRefreshing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCcw className="w-4 h-4" />}
            Đồng bộ dữ liệu
          </button>
        </div>
      </div>

      <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="bg-white border border-zinc-100 overflow-hidden shadow-sm">
             <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-zinc-50/50 border-b border-zinc-100 text-zinc-300 text-[9px] font-bold uppercase tracking-[0.2em]">
                      <th className="px-10 py-6">Thành viên</th>
                      <th className="px-10 py-6">Quyền hạn</th>
                      <th className="px-10 py-6">Trạng thái</th>
                      <th className="px-10 py-6 text-right">Hành động</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-50">
                    {users.map((u: any) => (
                      <tr key={u._id} className="hover:bg-zinc-50/20 transition-colors group">
                        <td className="px-10 py-8">
                            <div className="flex items-center gap-6">
                                <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center border border-zinc-100 font-black text-zinc-200 group-hover:bg-black group-hover:text-white transition-all">
                                    {u.email[0].toUpperCase()}
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="font-bold text-black text-sm tracking-tight">{u.full_name || "Ẩn danh"}</span>
                                    <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{u.email}</span>
                                </div>
                            </div>
                        </td>
                        <td className="px-10 py-8">
                            <select
                                value={u.role}
                                onChange={(e) => updateRole(u._id, e.target.value)}
                                className="bg-transparent border-b border-zinc-100 text-[11px] font-bold uppercase tracking-widest focus:border-black outline-none py-2 cursor-pointer transition-all"
                            >
                                <option value="reader">Độc giả</option>
                                <option value="potential_author">Tác giả tiềm năng</option>
                                <option value="author">Tác giả</option>
                                <option value="moderator">Kiểm duyệt viên</option>
                                <option value="admin">Quản trị viên</option>
                            </select>
                        </td>
                        <td className="px-10 py-8">
                            <div className="flex items-center gap-3">
                                <div className={`w-2 h-2 ${u.is_active ? 'bg-black' : 'bg-zinc-100'}`} />
                                <span className={`text-[10px] font-bold uppercase tracking-widest ${u.is_active ? 'text-black' : 'text-zinc-200'}`}>
                                    {u.is_active ? 'Hoạt động' : 'Đình chỉ'}
                                </span>
                            </div>
                        </td>
                        <td className="px-10 py-8 text-right">
                            <button 
                                onClick={() => updateStatus(u._id, !u.is_active)}
                                className={`px-6 py-3 text-[9px] font-bold uppercase tracking-widest border transition-all ${
                                    u.is_active ? 'text-red-500 border-red-50/50 hover:bg-red-500 hover:text-white' : 'text-black border-black hover:bg-black hover:text-white'
                                }`}
                            >
                                {u.is_active ? 'Vô hiệu hóa' : 'Kích hoạt'}
                            </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
             </div>
          </div>
      </div>
    </div>
  );
}
