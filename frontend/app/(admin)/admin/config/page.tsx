"use client";

import { useEffect, useState, useCallback } from "react";
import { getToken, API_URL, formatError } from "@/app/lib/api";
import {
  Settings,
  Loader2,
  RefreshCcw,
  Cpu,
  Database,
  HardDrive,
  Activity,
  ShieldAlert,
  Zap,
  Server
} from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";
import { Notification } from "@/app/components/NotificationToast";

export default function SystemConfigPage() {
  const { user, isLoading } = useAuth() as any;
  const [config, setConfig] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const headers = { Authorization: `Bearer ${getToken()}` };
      const [configRes, healthRes, maintRes] = await Promise.all([
        fetch(`${API_URL}/admin/config`, { headers }),
        fetch(`${API_URL}/admin/sys-health`, { headers }),
        fetch(`${API_URL}/admin/maintenance`, { headers })
      ]);

      if (configRes.ok) setConfig(await configRes.json());
      if (healthRes.ok) setHealth(await healthRes.json());
      if (maintRes.ok) {
        const maintData = await maintRes.json();
        setMaintenanceMode(maintData.data?.enabled || maintData.enabled || false);
      }
    } catch (err: any) {
      console.error("Lỗi tải cấu hình:", err);
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

  const toggleMaintenance = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/maintenance`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !maintenanceMode, message: "Hệ thống đang bảo trì." }),
      });
      if (res.ok) {
        setMaintenanceMode(!maintenanceMode);
        setNotification({ type: "success", text: !maintenanceMode ? "Đã bật chế độ bảo trì." : "Đã tắt chế độ bảo trì." });
      }
    } catch (err: any) {
      console.error("Lỗi chuyển đổi bảo trì:", err);
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
            <h1 className="text-5xl font-bold tracking-tighter leading-none">Hệ thống & Cấu hình</h1>
            <p className="text-zinc-400 text-[11px] font-bold uppercase tracking-[0.2em] flex items-center gap-2">
              Thiết lập tham số lõi & Giám sát hạ tầng <Settings className="w-3.5 h-3.5" />
            </p>
          </div>
          
          <button 
            onClick={fetchData}
            disabled={isRefreshing}
            className="h-14 px-12 bg-black text-white text-[10px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all flex items-center gap-4 shadow-xl shadow-black/5"
          >
            {isRefreshing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCcw className="w-4 h-4" />}
            Kiểm tra trạng thái
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="lg:col-span-8 space-y-10">
              <div className="bg-white border border-zinc-100 p-12 space-y-10 shadow-sm">
                  <div className="space-y-1">
                      <h3 className="text-lg font-bold tracking-tighter uppercase">Kinh tế hệ thống</h3>
                      <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Tham số tài chính trung tâm</p>
                  </div>
                  <div className="grid grid-cols-2 gap-8">
                      <div className="space-y-4">
                          <label className="text-[10px] font-bold text-black uppercase tracking-widest">Hoa hồng (%)</label>
                          <input 
                            type="number" 
                            defaultValue={config?.commission_rate * 100 || 20} 
                            className="w-full h-14 px-6 bg-zinc-50 border border-zinc-100 focus:border-black outline-none font-bold transition-all" 
                          />
                      </div>
                      <div className="space-y-4">
                          <label className="text-[10px] font-bold text-black uppercase tracking-widest">Phí rút (dl)</label>
                          <input 
                            type="number" 
                            defaultValue={config?.withdrawal_fee_dl || 1000} 
                            className="w-full h-14 px-6 bg-zinc-50 border border-zinc-100 focus:border-black outline-none font-bold transition-all" 
                          />
                      </div>
                  </div>
                  <div className="pt-6">
                      <button className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all shadow-xl shadow-black/5">Cập nhật tài chính</button>
                  </div>
              </div>

              <div className="bg-white border border-zinc-100 p-12 space-y-10 shadow-sm">
                  <div className="space-y-1">
                      <h3 className="text-lg font-bold tracking-tighter uppercase">Hạ tầng mạng</h3>
                      <div className="grid grid-cols-2 gap-6 pt-4">
                          <div className="p-6 bg-zinc-50 border border-zinc-100 flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                  <Database className="w-4 h-4 text-zinc-400" />
                                  <span className="text-[10px] font-bold uppercase tracking-widest">MongoDB</span>
                              </div>
                              <span className="text-[10px] font-bold text-green-500 uppercase tracking-widest">Connected</span>
                          </div>
                          <div className="p-6 bg-zinc-50 border border-zinc-100 flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                  <Zap className="w-4 h-4 text-zinc-400" />
                                  <span className="text-[10px] font-bold uppercase tracking-widest">Redis</span>
                              </div>
                              <span className="text-[10px] font-bold text-green-500 uppercase tracking-widest">Active</span>
                          </div>
                      </div>
                  </div>
              </div>
          </div>

          <div className="lg:col-span-4 space-y-10">
              <div className={`p-10 border transition-all duration-700 shadow-sm ${maintenanceMode ? 'bg-black text-white border-black' : 'bg-white border-zinc-100 text-black'}`}>
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

              <div className="bg-white border border-zinc-100 p-10 space-y-8 shadow-sm">
                   <h3 className="text-[11px] font-bold uppercase tracking-widest">Công cụ lõi</h3>
                   <div className="grid gap-3">
                      <button className="h-14 border border-zinc-50 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all flex items-center justify-center gap-3">
                          <HardDrive className="w-4 h-4" /> Sao lưu Database
                      </button>
                      <button className="h-14 border border-zinc-50 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all flex items-center justify-center gap-3">
                          <Activity className="w-4 h-4" /> Reset Cache
                      </button>
                   </div>
              </div>
          </div>
      </div>
    </div>
  );
}
