"use client";

import { useEffect, useState, useCallback } from "react";
import { getToken, API_URL, formatError } from "@/app/lib/api";
import {
  AlertTriangle,
  ShieldCheck,
  Activity,
  Users,
  Database,
  Settings,
  BarChart3,
  CheckCircle2,
  XCircle,
  RefreshCcw,
  Lock,
  Unlock,
  UserPlus,
  CreditCard,
  Loader2,
  Image as ImageIcon,
  Plus,
  Trash2,
  Edit,
  ListTree,
  HardDrive,
  Cpu,
  X,
  ChevronRight,
  Zap,
  LayoutDashboard,
  Terminal,
  Server,
  Filter,
  FileText,
  Eye,
  PlusCircle,
  ShieldAlert,
  UserCheck
} from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";
import { Notification } from "@/app/components/NotificationToast";
import { Button } from "@/components/ui/button";

type AdminTab = "overview" | "users" | "reports" | "applications" | "config" | "collector";

export default function AdminDashboard() {
  const { user, isLoading } = useAuth() as any;
  const [activeTab, setActiveTab] = useState<AdminTab>("overview");
  const [users, setUsers] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [applications, setApplications] = useState<any[]>([]);
  const [payouts, setPayouts] = useState<any[]>([]);
  const [banners, setBanners] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [config, setConfig] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [confirmModal, setConfirmModal] = useState<{ show: boolean; title: string; onConfirm: () => void } | null>(null);
  const [visible, setVisible] = useState(false);
  const [collectionSource, setCollectionSource] = useState("AnnaArchive");
  const [collectionUrl, setCollectionUrl] = useState("");
  const [collectionType, setCollectionType] = useState("list");
  const [collectorStats, setCollectorStats] = useState<any>(null);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const headers = { Authorization: `Bearer ${getToken()}` };

      const baseEndpoints = [
        "users",
        "reports",
        "applications/authors",
        "stats",
        "sys-health",
        "banners",
      ];

      const fetchList = baseEndpoints.map(ep => fetch(`${API_URL}/admin/${ep}`, { headers }));

      if (user?.role === "admin") {
        fetchList.push(
          fetch(`${API_URL}/admin/payouts`, { headers }),
          fetch(`${API_URL}/admin/config`, { headers }),
          fetch(`${API_URL}/admin/audit`, { headers }),
          fetch(`${API_URL}/admin/maintenance`, { headers })
        );
      }

      const results = await Promise.all(fetchList);
      const data = await Promise.all(results.map((r) => (r.ok ? r.json() : null)));

      if (data[0]) setUsers(data[0].data || data[0]);
      if (data[1]) setReports(data[1].data || data[1]);
      if (data[2]) setApplications(data[2].data || data[2]);
      if (data[3]) setStats(data[3].data || data[3]);
      if (data[4]) setHealth(data[4].data || data[4]);
      if (data[5]) setBanners(data[5].data || data[5]);

      if (user?.role === "admin" && data.length > 6) {
        if (data[6]) setPayouts(data[6].data || data[6]);
        if (data[7]) setConfig(data[7].data || data[7]);
        if (data[8]) setAuditLogs(data[8].data || data[8]);
        if (data[9]) setMaintenanceMode(data[9].data?.enabled || data[9].enabled || false);
      }
      if (user?.role === "admin") {
        const statsRes = await fetch(`${API_URL}/collector/stats`, { headers });
        if (statsRes.ok) {
          const statsData = await statsRes.json();
          setCollectorStats(statsData.data || statsData);
        }
      }
    } catch (err: any) {
      console.error("Lỗi tải dữ liệu quản trị:", err);
    } finally {
      setIsRefreshing(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [user?.role]);

  useEffect(() => {
    if (isLoading) return;
    if (!user || (user.role !== "admin" && user.role !== "moderator")) {
      window.location.href = "/";
    } else {
      fetchData();
    }
  }, [user, isLoading, fetchData]);

  const toggleMaintenance = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/maintenance`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !maintenanceMode, message: "Hệ thống đang bảo trì định kỳ" }),
      });
      if (res.ok) {
        setMaintenanceMode(!maintenanceMode);
        setNotification({ type: "success", text: maintenanceMode ? "Đã tắt chế độ bảo trì." : "Hệ thống đã vào trạng thái bảo trì." });
        fetchData();
      }
    } catch (err: any) {
      console.error("Lỗi chuyển chế độ bảo trì:", err);
    }
  };

  const updateRole = async (userId: string, role: string) => {
    try {
      const res = await fetch(`${API_URL}/admin/users/${userId}/role`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });
      if (res.ok) {
        setNotification({ type: "success", text: "Đã cập nhật vai trò người dùng." });
        fetchData();
      }
    } catch (err: any) {
      console.error("Lỗi cập nhật vai trò:", err);
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

  const reviewApplication = async (appId: string, status: string) => {
    try {
      const res = await fetch(`${API_URL}/admin/applications/authors/${appId}/review`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({ status, reason: status === "APPROVED" ? "Đã duyệt" : "Không đủ tiêu chuẩn" }),
      });
      if (res.ok) {
        setNotification({ type: "success", text: "Đã xử lý hồ sơ ứng tuyển." });
        fetchData();
      } else {
        const err = await res.json();
        setNotification({ type: "error", text: formatError(err.detail) || "Lỗi xử lý hồ sơ." });
      }
    } catch (err: any) {
      console.error("Lỗi duyệt hồ sơ:", err);
      setNotification({ type: "error", text: "Lỗi kết nối hệ thống." });
    }
  };

  const reviewPayout = async (payoutId: string, status: string) => {
    try {
      const res = await fetch(`${API_URL}/admin/payouts/${payoutId}/review?status=${status}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        setNotification({ type: "success", text: "Đã phê duyệt yêu cầu thanh toán." });
        fetchData();
      }
    } catch (err: any) {
      console.error("Lỗi phê duyệt thanh toán:", err);
    }
  };

  const updateConfig = async (newConfig: any) => {
    try {
      const res = await fetch(`${API_URL}/admin/config`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify(newConfig),
      });
      if (res.ok) {
        setNotification({ type: "success", text: "Đã cập nhật cấu hình hệ thống." });
        fetchData();
      }
    } catch (err: any) {
      console.error("Lỗi cập nhật cấu hình:", err);
    }
  };

  const toggleAuthorRegistration = () => {
    if (!config) return;
    const newConfig = { ...config, author_application_enabled: !config.author_application_enabled };
    updateConfig(newConfig);
  };

  const deleteBanner = async (id: string) => {
    setConfirmModal({
      show: true,
      title: "Xác nhận xóa banner này?",
      onConfirm: async () => {
        try {
          const res = await fetch(`${API_URL}/admin/banners/${id}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${getToken()}` },
          });
          if (res.ok) {
            setNotification({ type: "success", text: "Đã xóa banner." });
            fetchData();
          }
        } catch (err: any) {
          console.error("Lỗi xóa banner:", err);
        }
        setConfirmModal(null);
      },
    });
  };

    });
  };
  
  const triggerCollection = async () => {
    setIsRefreshing(true);
    try {
        const res = await fetch(`${API_URL}/collector/trigger`, {
            method: "POST",
            headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
            body: JSON.stringify({ 
                source: collectionSource, 
                url: collectionUrl, 
                index_type: collectionType 
            }),
        });
        if (res.ok) {
            setNotification({ type: "success", text: "Yêu cầu thu thập dữ liệu đã được gửi thành công." });
            setCollectionUrl("");
            fetchData();
        } else {
            const err = await res.json();
            setNotification({ type: "error", text: formatError(err.detail) || "Lỗi khi kích hoạt thu thập." });
        }
    } catch (err) {
        console.error("Lỗi thu thập:", err);
    } finally {
        setIsRefreshing(false);
    }
  };

  if (isLoading || !user) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
      </div>
    );
  }

  const tabs = [
    { id: "overview", label: "Tổng quan", icon: BarChart3 },
    { id: "users", label: "Người dùng", icon: Users },
    { id: "reports", label: "Vi phạm", icon: AlertTriangle },
    { id: "applications", label: "Đơn ứng tuyển", icon: UserCheck },
    ...(user?.role === "admin"
      ? [
          { id: "payouts", label: "Thanh toán", icon: CreditCard },
          { id: "collector", label: "Thu thập", icon: Database },
          { id: "audit", label: "Nhật ký", icon: ListTree },
          { id: "config", label: "Cấu hình", icon: Settings },
        ]
      : []),
  ];

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-10 font-sans text-black selection:bg-black selection:text-white">
      {notification && (
        <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      {confirmModal?.show && (
        <div className="fixed inset-0 z-[2000] bg-black/80 flex items-center justify-center p-6 animate-in fade-in duration-300 backdrop-blur-md">
          <div className="bg-white border border-zinc-200 w-full max-w-md animate-in zoom-in-95 duration-300 rounded-none ">
            <div className="p-12 text-center">
              <AlertTriangle className="w-12 h-12 text-black mx-auto mb-8 stroke-[1.5]" />
              <h3 className="text-2xl font-bold mb-4 tracking-tighter">{confirmModal.title}</h3>
              <p className="text-[11px] text-zinc-400 font-bold uppercase tracking-widest mb-10 italic leading-relaxed">Dữ liệu sẽ bị xóa vĩnh viễn khỏi hệ thống.</p>
              <div className="flex gap-4">
                <button
                  onClick={() => setConfirmModal(null)}
                  className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black hover:border-black transition-all"
                >
                  Hủy bỏ
                </button>
                <button
                  onClick={confirmModal.onConfirm}
                  className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-95"
                >
                  Xác nhận xóa
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div 
        className="mb-10 border-b border-zinc-100 pb-10 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black mb-3">
              Quản trị viên
            </h1>
            <div className="flex items-center gap-4">
               <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
                 Root System Control <ShieldCheck className="w-3.5 h-3.5 text-zinc-100" />
               </p>
               {maintenanceMode && (
                 <span className="px-3 py-1 bg-black text-white text-[9px] font-bold uppercase tracking-widest animate-pulse">Maintenance Mode</span>
               )}
            </div>
          </div>
          
          <button 
            onClick={fetchData}
            disabled={isRefreshing}
            className="h-14 px-12 bg-black text-white text-[11px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all active:scale-95 flex items-center gap-4 rounded-none border border-black/5"
          >
            {isRefreshing ? <Loader2 className="w-5 h-5 animate-spin" /> : <RefreshCcw className="w-5 h-5" />}
            Đồng bộ dữ liệu
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-12">
        <aside 
          className="lg:col-span-3 space-y-10 transition-all duration-700 delay-150"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="space-y-6">
            <div className="text-[11px] font-bold text-black uppercase tracking-[0.3em] px-1 flex items-center gap-2">
                <Filter className="w-4 h-4 text-zinc-300" /> Bảng điều khiển
            </div>
            <nav className="flex flex-col gap-1">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as TabType)}
                        className={`flex items-center justify-between px-6 py-4 text-[11px] font-bold uppercase tracking-widest transition-all border ${
                            activeTab === tab.id
                            ? "bg-black text-white border-black border border-black/5"
                            : "bg-white text-zinc-400 border-zinc-100 hover:bg-zinc-50 hover:text-black"
                        }`}
                    >
                        <div className="flex items-center gap-3">
                            <tab.icon className="w-4 h-4" /> {tab.label}
                        </div>
                        <ChevronRight className={`w-3.5 h-3.5 transition-transform ${activeTab === tab.id ? "rotate-90" : ""}`} />
                    </button>
                ))}
            </nav>
          </div>

          <div className="p-8 border border-zinc-100 bg-zinc-50/50 space-y-6">
             <div className="flex items-center gap-4 text-black">
                <Activity className="w-5 h-5" />
                <span className="text-[11px] font-bold uppercase tracking-widest">Sức khỏe hệ thống</span>
             </div>
             <div className="space-y-3">
                <div className="flex justify-between items-center text-[10px] font-bold uppercase">
                    <span className="text-zinc-400">Database</span>
                    <span className={health?.mongodb === 'OK' ? 'text-black' : 'text-red-500'}>{health?.mongodb || 'Wait'}</span>
                </div>
                <div className="flex justify-between items-center text-[10px] font-bold uppercase">
                    <span className="text-zinc-400">Caching</span>
                    <span className={health?.redis === 'OK' ? 'text-black' : 'text-red-500'}>{health?.redis || 'Wait'}</span>
                </div>
                <div className="flex justify-between items-center text-[10px] font-bold uppercase">
                    <span className="text-zinc-400">Status</span>
                    <span className="text-black font-black">{health?.status?.toUpperCase() || 'NORMAL'}</span>
                </div>
             </div>
          </div>
        </aside>

        <main 
          className="lg:col-span-9 transition-all duration-700 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {activeTab === "stats" && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
               <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {[
                  { label: "Thành viên", val: stats?.total_users || 0, icon: Users, sub: "Tổng cộng" },
                  { label: "Tri thức", val: stats?.total_documents || 0, icon: Database, sub: "Tài liệu số" },
                  { label: "Doanh thu", val: (stats?.total_revenue || 0).toLocaleString(), icon: CreditCard, sub: "Tổng dl" },
                  { label: "Hoạt động", val: stats?.active_users_24h || 0, icon: Activity, sub: "Trong 24h" },
                ].map((item, i) => (
                  <div key={i} className="p-8 border border-zinc-100 bg-white group hover:border-black transition-all duration-500">
                    <item.icon className="w-5 h-5 text-zinc-100 group-hover:text-black transition-colors mb-6" />
                    <h3 className="text-3xl font-bold text-black tracking-tighter mb-2">{item.val}</h3>
                    <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{item.label} ({item.sub})</p>
                  </div>
                ))}
              </div>

              <div className="p-12 border border-zinc-100 bg-zinc-50/10 space-y-8">
                 <div className="flex items-center gap-4">
                    <Server className="w-5 h-5" />
                    <h2 className="text-sm font-bold uppercase tracking-widest">Hiệu năng máy chủ</h2>
                 </div>
                 <div className="grid grid-cols-3 gap-10">
                    <div className="space-y-3">
                        <div className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">CPU Usage</div>
                        <div className="h-1 bg-zinc-100 overflow-hidden"><div className="h-full bg-black w-[15%]" /></div>
                        <div className="text-xl font-bold tracking-tighter">15%</div>
                    </div>
                    <div className="space-y-3">
                        <div className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Memory</div>
                        <div className="h-1 bg-zinc-100 overflow-hidden"><div className="h-full bg-black w-[42%]" /></div>
                        <div className="text-xl font-bold tracking-tighter">2.4 GB</div>
                    </div>
                    <div className="space-y-3">
                        <div className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Storage</div>
                        <div className="h-1 bg-zinc-100 overflow-hidden"><div className="h-full bg-black w-[68%]" /></div>
                        <div className="text-xl font-bold tracking-tighter">142 GB</div>
                    </div>
                 </div>
              </div>
            </div>
          )}

          {activeTab === "users" && (
            <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-700">
               <div className="flex items-center gap-6">
                 <h2 className="text-sm font-bold text-black tracking-widest uppercase">Danh sách định danh</h2>
                 <div className="flex-1 h-px bg-zinc-50" />
                 <span className="text-[11px] font-bold text-zinc-300 uppercase tracking-[0.2em]">{users.length} BẢN GHI</span>
               </div>

               <div className="bg-white border border-zinc-100 overflow-hidden">
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
                                    disabled={user.role !== "admin"}
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
                                    className={`h-10 px-6 border text-[9px] font-bold uppercase tracking-widest transition-all ${
                                        u.is_active 
                                        ? "border-zinc-100 text-zinc-300 hover:text-black hover:border-black" 
                                        : "bg-black text-white border-black hover:bg-zinc-800"
                                    }`}
                                >
                                    {u.is_active ? "Suspend" : "Activate"}
                                </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
               </div>
            </div>
          )}

          {activeTab === "moderation" && (
            <div className="space-y-10 animate-in slide-in-from-bottom-4 duration-700">
               <div className="flex items-center gap-6">
                 <h2 className="text-sm font-bold text-black tracking-widest uppercase">Hồ sơ ứng tuyển Tác giả</h2>
                 <div className="flex-1 h-px bg-zinc-50" />
               </div>

               <div className="grid gap-6">
                    {applications.length === 0 ? (
                        <div className="py-40 text-center border border-dashed border-zinc-100 bg-zinc-50/20 text-[10px] font-bold text-zinc-200 uppercase tracking-widest">
                            Không có hồ sơ nào đang chờ
                        </div>
                    ) : (
                        applications.map((app: any) => (
                            <div key={app._id} className="bg-white border border-zinc-100 p-10 hover:border-black transition-all duration-500 flex flex-col gap-8">
                                <div className="flex flex-col md:flex-row justify-between items-start gap-8">
                                    <div className="space-y-2">
                                        <h3 className="text-xl font-bold tracking-tighter">{app.user_name}</h3>
                                        <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{app.user_email}</p>
                                    </div>
                                    <div className="flex items-center gap-3 w-full md:w-auto">
                                        <button 
                                            onClick={() => reviewApplication(app._id, "REJECTED")}
                                            className="flex-1 h-12 px-8 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-red-600 hover:border-red-600 transition-all"
                                        >
                                            Từ chối
                                        </button>
                                        <button 
                                            onClick={() => reviewApplication(app._id, "APPROVED")}
                                            className="flex-1 h-12 px-10 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all"
                                        >
                                            Duyệt hồ sơ
                                        </button>
                                    </div>
                                </div>
                                <div className="p-8 bg-zinc-50 border-l-[4px] border-black italic text-sm text-zinc-500 font-medium leading-relaxed">
                                    "{app.motivation || "Ứng viên chưa cung cấp thông tin giới thiệu."}"
                                </div>
                            </div>
                        ))
                    )}
               </div>
            </div>
          )}

          {activeTab === "banners" && (
            <div className="space-y-10 animate-in slide-in-from-bottom-4 duration-700">
               <div className="flex items-center justify-between gap-6">
                 <h2 className="text-sm font-bold text-black tracking-widest uppercase">Truyền thông & Marketing</h2>
                 <button className="h-14 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-95 flex items-center gap-3">
                    <Plus className="w-5 h-5" /> Thêm Banner
                 </button>
               </div>

               <div className="grid md:grid-cols-2 gap-8">
                    {banners.length === 0 ? (
                        <div className="col-span-full py-40 text-center border border-dashed border-zinc-200 bg-zinc-50/20 text-[10px] font-bold text-zinc-200 uppercase tracking-widest">
                            Chưa có chiến dịch nào được cấu hình
                        </div>
                    ) : (
                        banners.map((b: any) => (
                            <div key={b.id} className="bg-white border border-zinc-100 group hover:border-black transition-all duration-700">
                                <div className="aspect-[16/7] bg-zinc-50 border-b border-zinc-100 overflow-hidden relative">
                                    {b.image_url && <img src={b.image_url} alt="" className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-700" />}
                                    <div className={`absolute top-4 right-4 px-3 py-1 text-[9px] font-bold uppercase border ${b.is_active ? 'bg-black text-white border-black' : 'bg-white text-zinc-300 border-zinc-100'}`}>
                                        {b.is_active ? 'Active' : 'Hidden'}
                                    </div>
                                </div>
                                <div className="p-8 space-y-6">
                                    <h4 className="font-bold text-lg tracking-tight truncate">{b.title}</h4>
                                    <div className="flex gap-2">
                                        <button className="flex-1 h-10 border border-zinc-50 text-[9px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black hover:border-black transition-all">Edit</button>
                                        <button onClick={() => deleteBanner(b.id)} className="flex-1 h-10 border border-zinc-50 text-[9px] font-bold uppercase tracking-widest text-zinc-200 hover:text-red-500 hover:border-red-500 transition-all">Delete</button>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
               </div>
            </div>
          )}

          {activeTab === "payouts" && user.role === "admin" && (
             <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-700">
                <div className="flex items-center gap-6">
                  <h2 className="text-sm font-bold text-black tracking-widest uppercase">Yêu cầu tất toán</h2>
                  <div className="flex-1 h-px bg-zinc-50" />
                </div>
                <div className="bg-white border border-zinc-100 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border-collapse">
                            <thead>
                                <tr className="bg-zinc-50/50 border-b border-zinc-100 text-zinc-300 text-[9px] font-bold uppercase tracking-[0.2em]">
                                    <th className="px-10 py-6">Tác giả</th>
                                    <th className="px-10 py-6">Số tiền</th>
                                    <th className="px-10 py-6">Ngày gửi</th>
                                    <th className="px-10 py-6 text-right">Phê chuẩn</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-50">
                                {payouts.map((p: any) => (
                                    <tr key={p._id} className="hover:bg-zinc-50/20 transition-colors group">
                                        <td className="px-10 py-8">
                                            <div className="flex flex-col gap-1">
                                                <span className="font-bold text-black text-sm tracking-tight">{p.author_name}</span>
                                                <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{p.author_email}</span>
                                            </div>
                                        </td>
                                        <td className="px-10 py-8 font-black text-lg tracking-tighter text-black">{p.amount?.toLocaleString()} <span className="text-[10px] italic">dl</span></td>
                                        <td className="px-10 py-8 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{new Date(p.created_at).toLocaleDateString("vi-VN")}</td>
                                        <td className="px-10 py-8 text-right">
                                            {p.status === "pending" ? (
                                                <div className="flex justify-end gap-3">
                                                    <button onClick={() => reviewPayout(p._id, "rejected")} className="h-10 px-6 border border-zinc-100 text-[9px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black transition-all">Reject</button>
                                                    <button onClick={() => reviewPayout(p._id, "approved")} className="h-10 px-8 bg-black text-white text-[9px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all">Approve</button>
                                                </div>
                                            ) : (
                                                <span className="text-[10px] font-black uppercase tracking-widest text-zinc-200">{p.status}</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
             </div>
          )}

          {activeTab === "applications" && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
               <div className="flex items-center gap-6">
                  <h2 className="text-sm font-bold text-black tracking-widest uppercase">Đơn đăng ký tác giả</h2>
                  <div className="flex-1 h-px bg-zinc-50" />
                  <span className="text-[11px] font-bold text-zinc-300 uppercase tracking-[0.2em]">{applications.length} ĐƠN CHỜ</span>
              </div>

              <div className="bg-white border border-zinc-100 overflow-hidden">
                  <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs border-collapse">
                          <thead>
                              <tr className="bg-zinc-50/50 border-b border-zinc-100 text-zinc-300 text-[9px] font-bold uppercase tracking-[0.2em]">
                                  <th className="px-10 py-6">Người ứng tuyển</th>
                                  <th className="px-10 py-6">Lý do & Động lực</th>
                                  <th className="px-10 py-6">Ngày gửi</th>
                                  <th className="px-10 py-6 text-right">Xử lý</th>
                              </tr>
                          </thead>
                          <tbody className="divide-y divide-zinc-50">
                              {applications.length === 0 ? (
                                  <tr>
                                      <td colSpan={4} className="px-10 py-32 text-center text-[10px] font-bold text-zinc-200 uppercase tracking-widest">Không có đơn ứng tuyển nào</td>
                                  </tr>
                              ) : (
                                  applications.map((app: any) => (
                                      <tr key={app._id} className="hover:bg-zinc-50/20 transition-colors group">
                                          <td className="px-10 py-8">
                                              <div className="flex items-center gap-4">
                                                  <div className="w-10 h-10 bg-black flex items-center justify-center text-white font-bold">
                                                      {app.user_name?.[0]?.toUpperCase() || "U"}
                                                  </div>
                                                  <div className="flex flex-col gap-1">
                                                      <span className="font-bold text-black uppercase tracking-widest text-[10px]">{app.user_name}</span>
                                                      <span className="text-[9px] font-bold text-zinc-300">{app.user_email}</span>
                                                  </div>
                                              </div>
                                          </td>
                                          <td className="px-10 py-8">
                                              <p className="text-[11px] text-zinc-500 font-medium italic line-clamp-2 max-w-md">"{app.motivation}"</p>
                                          </td>
                                          <td className="px-10 py-8">
                                              <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                                                  {new Date(app.created_at).toLocaleDateString("vi-VN")}
                                              </span>
                                          </td>
                                          <td className="px-10 py-8 text-right">
                                              <div className="flex justify-end gap-3">
                                                  <button 
                                                      onClick={() => reviewApplication(app._id, "REJECTED")}
                                                      className="h-9 px-6 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-red-600 hover:border-red-600 transition-all"
                                                  >
                                                      Từ chối
                                                  </button>
                                                  <button 
                                                      onClick={() => reviewApplication(app._id, "APPROVED")}
                                                      className="h-9 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-[0.98]"
                                                  >
                                                      Duyệt ngay
                                                  </button>
                                              </div>
                                          </td>
                                      </tr>
                                  ))
                              )}
                          </tbody>
                      </table>
                  </div>
              </div>
            </div>
          )}

          {activeTab === "audit" && user.role === "admin" && (
            <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-700">
               <div className="flex items-center gap-6">
                 <h2 className="text-sm font-bold text-black tracking-widest uppercase">Nhật ký vận hành</h2>
                 <div className="flex-1 h-px bg-zinc-50" />
               </div>
               <div className="bg-white border border-zinc-100 overflow-hidden">
                   <div className="overflow-x-auto">
                        <table className="w-full text-left text-[11px] border-collapse">
                            <thead>
                                <tr className="bg-zinc-50/50 border-b border-zinc-100 text-zinc-300 text-[9px] font-bold uppercase tracking-[0.2em]">
                                    <th className="px-10 py-6">Thời gian</th>
                                    <th className="px-10 py-6">Thao tác</th>
                                    <th className="px-10 py-6">Đối tượng</th>
                                    <th className="px-10 py-6">Chi tiết</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-50">
                                {auditLogs.map((log: any, i: number) => (
                                    <tr key={i} className="hover:bg-zinc-50/20 transition-colors">
                                        <td className="px-10 py-6 text-zinc-300 font-bold">{new Date(log.timestamp).toLocaleTimeString("vi-VN")}</td>
                                        <td className="px-10 py-6 font-bold text-black uppercase tracking-widest text-[10px]">{log.action}</td>
                                        <td className="px-10 py-6 text-zinc-400 font-bold">{log.actor_id || "System"}</td>
                                        <td className="px-10 py-6 text-zinc-500 font-medium italic truncate max-w-xs">"{log.details || log.message || "-"}"</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                   </div>
               </div>
            </div>
          )}

          {activeTab === "config" && user.role === "admin" && config && (
            <div className="grid lg:grid-cols-12 gap-12 animate-in slide-in-from-bottom-4 duration-700">
                <div className="lg:col-span-7 space-y-10">
                    <div className="bg-white border border-zinc-100 p-12 space-y-10">
                        <div className="space-y-1">
                            <h3 className="text-lg font-bold tracking-tighter uppercase">Kinh tế hệ thống</h3>
                            <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Thiết lập tham số tài chính</p>
                        </div>
                        <div className="grid grid-cols-2 gap-8">
                            <div className="space-y-4">
                                <label className="text-[10px] font-bold text-black uppercase tracking-widest">Hoa hồng (%)</label>
                                <input type="number" value={config.commission_rate * 100} className="w-full h-14 px-6 bg-zinc-50 border border-zinc-100 focus:border-black outline-none font-bold transition-all" />
                            </div>
                            <div className="space-y-4">
                                <label className="text-[10px] font-bold text-black uppercase tracking-widest">Phí rút (dl)</label>
                                <input type="number" value={config.withdrawal_fee_dl || 1000} className="w-full h-14 px-6 bg-zinc-50 border border-zinc-100 focus:border-black outline-none font-bold transition-all" />
                            </div>
                        </div>
                        <div className="pt-6">
                            <button className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all border border-black/5">Cập nhật tài chính</button>
                        </div>
                    </div>

                    <div className="bg-white border border-zinc-100 p-12 space-y-10">
                        <div className="space-y-1">
                            <h3 className="text-lg font-bold tracking-tighter uppercase">Động cơ AI Core</h3>
                            <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Thiết lập mô hình ngôn ngữ</p>
                        </div>
                        <div className="relative group">
                            <select className="w-full h-16 px-6 bg-zinc-50 border border-zinc-100 text-[11px] font-bold uppercase tracking-widest outline-none focus:border-black appearance-none cursor-pointer transition-all">
                                <option value="llama3">LLama 3 (70B) - Phân tích</option>
                                <option value="gpt-4o">GPT-4 Omni - Realtime</option>
                            </select>
                            <Cpu className="absolute right-6 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-300 group-hover:text-black pointer-events-none transition-all" />
                        </div>
                    </div>

                    <div className="bg-white border border-zinc-100 p-12 space-y-10">
                        <div className="space-y-1">
                            <h3 className="text-lg font-bold tracking-tighter uppercase">Cộng đồng</h3>
                            <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Thiết lập quyền hạn thành viên</p>
                        </div>
                        <div className="flex items-center justify-between p-6 bg-zinc-50 border border-zinc-100">
                             <span className="text-[11px] font-bold uppercase tracking-widest">Đăng ký Tác giả</span>
                             <button 
                                onClick={toggleAuthorRegistration}
                                className={`w-12 h-6 transition-all relative ${config?.author_application_enabled ? 'bg-black' : 'bg-zinc-200'}`}
                             >
                                <div className={`absolute top-0.5 w-5 h-5 transition-all bg-white ${config?.author_application_enabled ? 'left-6.5' : 'left-0.5'}`} />
                             </button>
                        </div>
                    </div>
                </div>

                <div className="lg:col-span-5 space-y-10">
                    <div className={`p-10 border transition-all duration-700 ${maintenanceMode ? 'bg-black text-white border-black' : 'bg-white border-zinc-100 text-black'}`}>
                        <div className="flex items-center justify-between mb-8">
                            <h3 className="text-[11px] font-bold uppercase tracking-[0.2em]">Chế độ bảo trì</h3>
                            <button onClick={toggleMaintenance} className={`w-14 h-8 transition-all relative ${maintenanceMode ? 'bg-white' : 'bg-zinc-100'}`}>
                                <div className={`absolute top-1 w-6 h-6 transition-all ${maintenanceMode ? 'bg-black left-7' : 'bg-white left-1'}`} />
                            </button>
                        </div>
                        <p className="text-[10px] font-medium leading-relaxed italic opacity-40">
                            {maintenanceMode ? "Toàn bộ hệ thống đang được khóa để bảo trì định kỳ." : "Hệ thống đang hoạt động ổn định và công khai."}
                        </p>
                    </div>

                    <div className="bg-white border border-zinc-100 p-10 space-y-8">
                         <h3 className="text-[11px] font-bold uppercase tracking-widest">Cơ sở hạ tầng</h3>
                         <div className="grid gap-3">
                            <button className="h-14 border border-zinc-50 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all flex items-center justify-center gap-3">
                                <Database className="w-4 h-4" /> Sao lưu Database
                            </button>
                            <button className="h-14 border border-zinc-50 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all flex items-center justify-center gap-3">
                                <HardDrive className="w-4 h-4" /> Xóa Cache Redis
                            </button>
                         </div>
                    </div>
                </div>
            </div>
          )}

          {activeTab === "collector" && user.role === "admin" && (
            <div className="space-y-12 animate-in slide-in-from-bottom-4 duration-700">
               <div className="flex items-center gap-6">
                  <h2 className="text-sm font-bold text-black tracking-widest uppercase">Trung tâm thu thập dữ liệu</h2>
                  <div className="flex-1 h-px bg-zinc-50" />
               </div>

               <div className="grid lg:grid-cols-2 gap-12">
                  <div className="space-y-10">
                     <div className="bg-white border border-zinc-100 p-12 space-y-10">
                        <div className="space-y-2">
                           <h3 className="text-xl font-bold tracking-tighter uppercase">Kích hoạt tiến trình</h3>
                           <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest leading-relaxed">
                             Tự động hóa việc thu thập tri thức từ các nguồn học thuật uy tín.
                           </p>
                        </div>

                        <div className="space-y-8">
                           <div className="space-y-4">
                              <label className="text-[10px] font-bold text-black uppercase tracking-widest">Nguồn dữ liệu</label>
                              <div className="relative group">
                                 <select 
                                   value={collectionSource}
                                   onChange={(e) => setCollectionSource(e.target.value)}
                                   className="w-full h-14 px-6 bg-zinc-50 border border-zinc-100 text-[11px] font-bold uppercase tracking-widest outline-none focus:border-black appearance-none cursor-pointer transition-all"
                                 >
                                    <option value="AnnaArchive">Anna's Archive</option>
                                    <option value="NXBST">NXB Sự Thật</option>
                                    <option value="NXBGDC">NXB Giáo Dục</option>
                                 </select>
                                 <PlusCircle className="absolute right-6 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-300 group-hover:text-black pointer-events-none transition-all" />
                              </div>
                           </div>

                           {collectionSource === "AnnaArchive" && (
                              <div className="space-y-4">
                                 <label className="text-[10px] font-bold text-black uppercase tracking-widest">Loại chỉ mục</label>
                                 <div className="flex gap-4">
                                    {["list", "detail"].map((type) => (
                                       <button
                                         key={type}
                                         onClick={() => setCollectionType(type)}
                                         className={`flex-1 h-12 border text-[10px] font-bold uppercase tracking-widest transition-all ${
                                           collectionType === type ? 'bg-black text-white border-black' : 'bg-white text-zinc-400 border-zinc-100 hover:text-black hover:border-black'
                                         }`}
                                       >
                                          {type}
                                       </button>
                                    ))}
                                 </div>
                              </div>
                           )}

                           <div className="space-y-4">
                              <label className="text-[10px] font-bold text-black uppercase tracking-widest">Đường dẫn nguồn (URL)</label>
                              <input 
                                type="text"
                                placeholder="https://..."
                                value={collectionUrl}
                                onChange={(e) => setCollectionUrl(e.target.value)}
                                className="w-full h-14 px-6 bg-zinc-50 border border-zinc-100 focus:border-black outline-none font-bold text-sm transition-all"
                              />
                           </div>

                           <button 
                             onClick={triggerCollection}
                             disabled={isRefreshing}
                             className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-95 flex items-center justify-center gap-4"
                           >
                             {isRefreshing ? <Loader2 className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />}
                             Kích hoạt thu thập
                           </button>
                        </div>
                     </div>
                  </div>

                  <div className="space-y-10">
                     <div className="bg-black text-white p-12 space-y-10 border border-black transition-all group">
                        <div className="flex items-center justify-between">
                           <div className="space-y-2">
                              <h3 className="text-xl font-bold tracking-tighter uppercase">Thống kê tri thức</h3>
                              <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Dữ liệu đã thu thập</p>
                           </div>
                           <Database className="w-8 h-8 text-zinc-800 group-hover:text-white transition-all duration-700" />
                        </div>

                        <div className="grid grid-cols-2 gap-12 pt-4">
                           <div className="space-y-1">
                              <div className="text-4xl font-black tracking-tighter">{collectorStats?.total_documents_collected || 0}</div>
                              <div className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Tài liệu đã số hóa</div>
                           </div>
                           <div className="space-y-1">
                              <div className="text-4xl font-black tracking-tighter">{collectorStats?.active_sources?.length || 0}</div>
                              <div className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Nguồn dữ liệu hoạt động</div>
                           </div>
                        </div>
                     </div>

                     <div className="bg-white border border-zinc-100 p-12 space-y-8">
                        <h3 className="text-[11px] font-bold uppercase tracking-widest flex items-center gap-3 text-black">
                           <ShieldAlert className="w-4 h-4" /> Lưu ý an toàn
                        </h3>
                        <div className="space-y-4">
                           <p className="text-[11px] text-zinc-400 font-medium leading-relaxed italic">
                             "Hành động thu thập dữ liệu có thể tốn nhiều tài nguyên mạng và CPU của máy chủ AI Gateway. Hãy đảm bảo URL nguồn là chính xác trước khi kích hoạt."
                           </p>
                           <div className="h-px bg-zinc-50" />
                           <div className="flex items-center gap-3">
                              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                              <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Hệ thống sẵn sàng</span>
                           </div>
                        </div>
                     </div>
                  </div>
               </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
