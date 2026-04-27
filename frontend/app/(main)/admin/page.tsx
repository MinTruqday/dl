"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/app/lib/api";
import { AlertTriangle, ShieldCheck, Activity, Users, Database, Settings, BarChart3, CheckCircle2, XCircle, Info, RefreshCcw, Lock, Unlock, UserPlus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/app/contexts/AuthContext";

type TabType = "stats" | "users" | "moderation" | "config";

export default function AdminDashboard() {
  const { user, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>("stats");
  const [users, setUsers] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [applications, setApplications] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [config, setConfig] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    if (isLoading) return;
    if (!user || (user.role !== "admin" && user.role !== "moderator")) {
      window.location.href = "/";
    } else {
      fetchData();
    }
  }, [user, isLoading]);

  const fetchData = async () => {
    setIsRefreshing(true);
    try {
      const headers = { 'Authorization': `Bearer ${getToken()}` };
      
      const [uRes, rRes, aRes, sRes, cRes, hRes] = await Promise.all([
        fetch(`${API_URL}/admin/users`, { headers }),
        fetch(`${API_URL}/admin/reports`, { headers }),
        fetch(`${API_URL}/admin/applications/authors`, { headers }),
        fetch(`${API_URL}/admin/stats`, { headers }),
        fetch(`${API_URL}/admin/config`, { headers }),
        fetch(`${API_URL}/admin/sys-health`, { headers })
      ]);
      
      if (uRes.ok) setUsers(await uRes.json());
      if (rRes.ok) setReports(await rRes.json());
      if (aRes.ok) setApplications(await aRes.json());
      if (sRes.ok) setStats(await sRes.json());
      if (cRes.ok) setConfig(await cRes.json());
      if (hRes.ok) setHealth(await hRes.json());
    } catch(e) {
      console.error(e);
    } finally {
      setIsRefreshing(false);
    }
  };

  const updateRole = async (userId: string, role: string) => {
    try {
      const res = await fetch(`${API_URL}/admin/users/${userId}/role`, {
        method: "PUT",
        headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ role })
      });
      if (res.ok) fetchData();
    } catch(e) { console.error(e); }
  };

  const updateStatus = async (userId: string, isActive: boolean) => {
    try {
      const res = await fetch(`${API_URL}/admin/users/${userId}/status`, {
        method: "PUT",
        headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: isActive })
      });
      if (res.ok) fetchData();
    } catch(e) { console.error(e); }
  };

  const toggleShadowban = async (userId: string, current: boolean) => {
    try {
      const res = await fetch(`${API_URL}/admin/users/${userId}/shadowban?is_shadowbanned=${!current}`, { 
        method: "PUT", 
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (res.ok) fetchData();
    } catch(e) { console.error(e); }
  };

  const resolveReport = async (reportId: string, action: string) => {
    try {
      const res = await fetch(`${API_URL}/admin/reports/${reportId}/resolve`, {
        method: "POST",
        headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action })
      });
      if (res.ok) fetchData();
    } catch(e) { console.error(e); }
  };

  const reviewApplication = async (appId: string, status: string, reason: string = "Đã duyệt bởi hệ thống") => {
    try {
      const res = await fetch(`${API_URL}/admin/applications/authors/${appId}/review`, {
        method: "PUT",
        headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, reason })
      });
      if (res.ok) fetchData();
    } catch(e) { console.error(e); }
  };

  const updateConfig = async (newConfig: any) => {
    try {
      const res = await fetch(`${API_URL}/admin/config`, {
        method: "PUT",
        headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
      if (res.ok) fetchData();
    } catch(e) { console.error(e); }
  };

  if (isLoading || !user) return null;

  return (
    <div className="container max-w-6xl mx-auto py-8 px-4 min-h-screen bg-background text-foreground font-sans">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-4 border-b border-border">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Quản trị vận hành</h1>
          <p className="text-muted-foreground text-sm mt-1">Chào mừng, {user.role === 'admin' ? 'Quản trị viên' : 'Kiểm duyệt viên'}</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} disabled={isRefreshing} className="w-fit">
          <RefreshCcw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          Làm mới dữ liệu
        </Button>
      </div>

      <div className="flex gap-1 mb-8 overflow-x-auto pb-1 no-scrollbar border-b border-border">
        <button 
          onClick={() => setActiveTab("stats")}
          className={`px-4 py-2 text-sm font-medium transition-all border-b-2 ${activeTab === "stats" ? "border-foreground text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
        >
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" /> Tổng quan
          </div>
        </button>
        <button 
          onClick={() => setActiveTab("users")}
          className={`px-4 py-2 text-sm font-medium transition-all border-b-2 ${activeTab === "users" ? "border-foreground text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
        >
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" /> Người dùng
          </div>
        </button>
        <button 
          onClick={() => setActiveTab("moderation")}
          className={`px-4 py-2 text-sm font-medium transition-all border-b-2 ${activeTab === "moderation" ? "border-foreground text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
        >
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4" /> Kiểm duyệt
          </div>
        </button>
        {user.role === 'admin' && (
          <button 
            onClick={() => setActiveTab("config")}
            className={`px-4 py-2 text-sm font-medium transition-all border-b-2 ${activeTab === "config" ? "border-foreground text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
          >
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4" /> Cấu hình
            </div>
          </button>
        )}
      </div>

      {activeTab === "stats" && (
        <div className="space-y-8 animate-in fade-in duration-300">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-6 border border-border ">
              <p className="text-muted-foreground text-xs font-bold tracking-widest">Tổng người dùng</p>
              <h3 className="text-3xl font-bold mt-2">{stats?.total_users || 0}</h3>
              <div className="flex items-center gap-1 mt-2 text-[12px] text-muted-foreground">
                <Activity className="w-3 h-3" /> {stats?.active_users_24h || 0} hoạt động (24h)
              </div>
            </div>
            <div className="bg-white p-6 border border-border ">
              <p className="text-muted-foreground text-xs font-bold tracking-widest">Tổng tác phẩm</p>
              <h3 className="text-3xl font-bold mt-2">{stats?.total_books || 0}</h3>
            </div>
            <div className="bg-white p-6 border border-border ">
              <p className="text-muted-foreground text-xs font-bold tracking-widest">Doanh thu hệ thống</p>
              <h3 className="text-3xl font-bold mt-2">{stats?.total_revenue?.toLocaleString() || 0} C</h3>
            </div>
            <div className="bg-white p-6 border border-border ">
              <p className="text-muted-foreground text-xs font-bold tracking-widest">Trạng thái API</p>
              <div className="flex items-center gap-2 mt-4">
                <div className={`w-2 h-2 rounded-none ${health?.status === 'healthy' ? 'bg-black' : 'bg-zinc-300'}`} />
                <span className="text-[12px] font-bold tracking-widest">{health?.status || 'Đang kiểm tra'}</span>
              </div>
            </div>
          </div>

          <div className="bg-white border border-border  overflow-hidden">
            <div className="px-6 py-4 border-b border-border bg-muted/30">
              <h3 className="text-sm font-bold flex items-center gap-2 tracking-wider">
                <Database className="w-4 h-4" /> Nhật ký hệ thống
              </h3>
            </div>
            <div className="p-0">
               <div className="flex items-center justify-center py-12 text-muted-foreground text-sm">
                 <p>Tính năng nhật ký chi tiết đang được đồng bộ dữ liệu.</p>
               </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "users" && (
        <div className="bg-white border border-border  overflow-hidden animate-in fade-in duration-300">
          <div className="px-6 py-4 border-b border-border bg-muted/30 flex justify-between items-center">
            <h3 className="text-sm font-bold tracking-wider">Danh sách tài khoản</h3>
            <span className="text-xs text-muted-foreground">{users.length} người dùng</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-muted/10 border-b border-border text-muted-foreground text-[12px] tracking-widest">
                  <th className="px-6 py-4 font-bold">Người dùng</th>
                  <th className="px-6 py-4 font-bold">Vai trò</th>
                  <th className="px-6 py-4 font-bold">Trạng thái</th>
                  <th className="px-6 py-4 font-bold text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u: any) => (
                  <tr key={u._id} className="border-b border-border last:border-0 hover:bg-muted/5 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-none bg-muted flex items-center justify-center font-bold text-xs">
                          {u.email[0].toUpperCase()}
                        </div>
                        <div>
                          <p className="font-bold text-foreground">{u.full_name || 'Chưa đặt tên'}</p>
                          <p className="text-[12px] text-muted-foreground">{u.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {user.role === 'admin' ? (
                        <select 
                          value={u.role} 
                          onChange={(e) => updateRole(u._id, e.target.value)}
                          className="bg-muted/50 border border-border  px-2 py-1 text-xs outline-none focus:border-foreground"
                        >
                          <option value="reader">Reader</option>
                          <option value="author">Author</option>
                          <option value="moderator">Moderator</option>
                          <option value="admin">Quản trị viên</option>
                        </select>
                      ) : (
                        <span className="bg-muted px-2 py-1 rounded text-[12px] font-bold">{u.role}</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1">
                        <span className={`text-[12px] font-bold tracking-widest ${u.is_active ? 'text-black' : 'text-zinc-400'}`}>
                          {u.is_active ? 'ĐANG HOẠT ĐỘNG' : 'ĐÃ TẠM KHÓA'}
                        </span>
                        {u.is_shadowbanned && <span className="text-[13px] text-zinc-500 font-bold tracking-widest">SHADOWBANNED</span>}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                       <div className="flex justify-end gap-2">
                         <Button 
                            variant="outline" 
                            size="sm" 
                            className="h-8 w-8 p-0" 
                            onClick={() => toggleShadowban(u._id, u.is_shadowbanned)}
                            title="Hạn chế người dùng"
                         >
                           {u.is_shadowbanned ? <Unlock className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
                         </Button>
                         <Button 
                            variant={u.is_active ? "secondary" : "default"} 
                            size="sm" 
                            className="h-8 text-[12px] font-bold"
                            onClick={() => updateStatus(u._id, !u.is_active)}
                         >
                           {u.is_active ? "KHÓA" : "MỞ KHÓA"}
                         </Button>
                       </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "moderation" && (
        <div className="space-y-6 animate-in fade-in duration-300">
          <div className="bg-white border border-border  overflow-hidden">
            <div className="px-6 py-4 border-b border-border bg-muted/30 flex items-center justify-between">
              <h3 className="text-sm font-bold flex items-center gap-2 tracking-wider">
                <UserPlus className="w-4 h-4" /> Đơn đăng ký tác giả ({applications.length})
              </h3>
            </div>
            <div className="p-0">
              {applications.length === 0 ? (
                <div className="py-12 text-center text-muted-foreground text-sm">
                  Không có đơn đăng ký nào đang chờ.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm whitespace-nowrap">
                    <thead>
                      <tr className="bg-muted/10 border-b border-border text-muted-foreground text-[12px] tracking-widest">
                        <th className="px-6 py-4 font-bold">Người đăng ký</th>
                        <th className="px-6 py-4 font-bold">Thông tin</th>
                        <th className="px-6 py-4 font-bold text-right">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody>
                      {applications.map((app: any) => (
                        <tr key={app._id} className="border-b border-border last:border-0 hover:bg-muted/5 transition-colors">
                          <td className="px-6 py-4">
                            <p className="font-bold text-foreground">{app.user_name || 'N/A'}</p>
                            <p className="text-[12px] text-muted-foreground">{app.user_email}</p>
                          </td>
                          <td className="px-6 py-4">
                            <p className="text-xs text-foreground italic">"{app.motivation || 'Không có mô tả'}"</p>
                          </td>
                          <td className="px-6 py-4 text-right">
                             <div className="flex justify-end gap-2">
                               <Button variant="outline" size="sm" className="h-8 text-[12px] font-bold" onClick={() => reviewApplication(app._id, 'REJECTED', 'Không đủ tiêu chuẩn')}>TỪ CHỐI</Button>
                               <Button variant="default" size="sm" className="h-8 text-[12px] font-bold" onClick={() => reviewApplication(app._id, 'APPROVED')}>CHẤP THUẬN</Button>
                             </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white border border-border  overflow-hidden">
            <div className="px-6 py-4 border-b border-border bg-muted/30 flex items-center justify-between">
              <h3 className="text-sm font-bold flex items-center gap-2 tracking-wider">
                <AlertTriangle className="w-4 h-4" /> Hàng đợi báo cáo ({reports.length})
              </h3>
            </div>
            <div className="p-0">
              {reports.length === 0 ? (
                <div className="py-12 text-center text-muted-foreground text-sm">
                  Không có nội dung nào bị báo cáo.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm whitespace-nowrap">
                    <thead>
                      <tr className="bg-muted/10 border-b border-border text-muted-foreground text-[12px] tracking-widest">
                        <th className="px-6 py-4 font-bold">Nội dung</th>
                        <th className="px-6 py-4 font-bold">Lý do</th>
                        <th className="px-6 py-4 font-bold text-right">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reports.map((r: any) => (
                        <tr key={r._id} className="border-b border-border last:border-0 hover:bg-muted/5 transition-colors">
                          <td className="px-6 py-4">
                            <span className="bg-muted px-2 py-0.5 rounded text-[12px] font-bold mr-2">{r.item_type}</span>
                            <span className="text-xs text-muted-foreground">{r.item_id}</span>
                          </td>
                          <td className="px-6 py-4">
                            <p className="font-bold text-foreground text-xs">{r.reason}</p>
                            <p className="text-[12px] text-muted-foreground mt-0.5">{r.description || 'Không có mô tả chi tiết'}</p>
                          </td>
                          <td className="px-6 py-4 text-right">
                             <div className="flex justify-end gap-2">
                               <Button variant="outline" size="sm" className="h-8 text-[12px] font-bold" onClick={() => resolveReport(r._id, 'ignore')}>BỎ QUA</Button>
                               <Button variant="destructive" size="sm" className="h-8 text-[12px] font-bold" onClick={() => resolveReport(r._id, 'takedown')}>XÓA BỎ</Button>
                             </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === "config" && user.role === 'admin' && (
        <div className="bg-white border border-border  overflow-hidden animate-in fade-in duration-300">
           <div className="px-6 py-4 border-b border-border bg-muted/30">
              <h3 className="text-sm font-bold tracking-wider">Cấu hình tham số toàn cục</h3>
           </div>
           <div className="p-8 max-w-2xl space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-muted-foreground tracking-widest">Tỉ lệ hoa hồng (0.0 - 1.0)</label>
                  <input 
                    type="number" 
                    step="0.01"
                    value={config?.commission_rate || 0} 
                    onChange={(e) => setConfig({...config, commission_rate: parseFloat(e.target.value)})}
                    className="w-full bg-muted/30 border border-border  px-4 py-2.5 text-sm outline-none focus:border-foreground"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-muted-foreground tracking-widest uppercase">Phí rút tiền cố định</label>
                  <div className="relative">
                    <input 
                      type="number" 
                      value={config?.withdrawal_fee || 0} 
                      onChange={(e) => setConfig({...config, withdrawal_fee: parseInt(e.target.value)})}
                      className="w-full bg-muted/20 border border-border  px-4 py-3 text-sm font-bold outline-none focus:border-foreground"
                    />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-bold text-muted-foreground uppercase">dl</span>
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-muted-foreground tracking-widest">Mô hình AI mặc định</label>
                <select 
                  value={config?.ai_model || "gpt-4o"}
                  onChange={(e) => setConfig({...config, ai_model: e.target.value})}
                  className="w-full bg-muted/30 border border-border  px-4 py-2.5 text-sm outline-none focus:border-foreground appearance-none"
                >
                  <option value="gpt-4o">GPT-4 Omni</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                </select>
              </div>
              <div className="pt-4">
                <Button onClick={() => updateConfig(config)} className="w-full md:w-fit px-8 font-bold text-xs tracking-widest h-11">
                  Lưu cấu hình
                </Button>
              </div>
              <div className="p-4 bg-muted/20 border border-border  flex gap-3">
                <Info className="w-5 h-5 text-muted-foreground shrink-0" />
                <p className="text-[12px] text-muted-foreground leading-relaxed">Các thay đổi về cấu hình sẽ được lưu vào cơ sở dữ liệu và áp dụng ngay lập tức cho các yêu cầu mới mà không cần khởi động lại dịch vụ Docker.</p>
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
