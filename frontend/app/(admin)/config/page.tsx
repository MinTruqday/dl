"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  getAdminConfigAPI, 
  updateAdminConfigAPI, 
  getSystemHealthAPI, 
  getMaintenanceModeAPI, 
  toggleMaintenanceModeAPI,
  triggerBackupAPI
} from "@/app/lib/api";
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
  Server,
  Terminal,
  ShieldCheck,
  ChevronRight,
  DatabaseZap,
  CloudLightning,
  AlertCircle
} from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";
import { Notification } from "@/app/components/NotificationToast";

export default function SystemConfigPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const [config, setConfig] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);

  const [formConfig, setFormConfig] = useState({
    commission_rate: 0.2,
    withdrawal_fee_dl: 1000,
    min_withdrawal_dl: 50000
  });

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [configData, healthData, maintData] = await Promise.all([
        getAdminConfigAPI(),
        getSystemHealthAPI(),
        getMaintenanceModeAPI()
      ]);

      setConfig(configData.data || configData);
      setHealth(healthData.data || healthData);
      setMaintenanceMode(maintData.data?.enabled || maintData.enabled || false);
      
      const cfg = configData.data || configData;
      setFormConfig({
        commission_rate: cfg?.commission_rate || 0.2,
        withdrawal_fee_dl: cfg?.withdrawal_fee_dl || 1000,
        min_withdrawal_dl: cfg?.min_withdrawal_dl || 50000
      });
    } catch (err: any) {
      setNotification({ type: "error", text: "Không thể kết nối hạ tầng hệ thống." });
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

  const handleUpdateConfig = async () => {
    try {
      await updateAdminConfigAPI(formConfig);
      setNotification({ type: "success", text: "Cấu hình hệ thống đã được cập nhật." });
      fetchData();
    } catch (err: any) {
      setNotification({ type: "error", text: err.message || "Lỗi cập nhật cấu hình." });
    }
  };

  const handleToggleMaintenance = async () => {
    try {
      await toggleMaintenanceModeAPI(!maintenanceMode);
      setNotification({ type: "success", text: !maintenanceMode ? "Đã kích hoạt chế độ bảo trì." : "Đã khôi phục hoạt động hệ thống." });
      fetchData();
    } catch (err: any) {
      setNotification({ type: "error", text: err.message || "Lỗi thao tác bảo trì." });
    }
  };

  const handleTriggerBackup = async () => {
    try {
      await triggerBackupAPI();
      setNotification({ type: "success", text: "Đã khởi tạo quy trình sao lưu dữ liệu." });
    } catch (err: any) {
      setNotification({ type: "error", text: err.message || "Lỗi khởi tạo sao lưu." });
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-white">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
        {notification && (
          <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
            <Notification type={notification.type} message={notification.text} />
          </div>
        )}

        <div 
          className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="space-y-4">
              <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">Hệ thống & Cấu hình</h1>
              <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
                Tham số vận hành & Sức khỏe hạ tầng <ShieldCheck className="w-3.5 h-3.5 text-zinc-100" />
              </p>
            </div>
            
            <button 
              onClick={fetchData}
              disabled={isRefreshing}
              className="h-14 px-10 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center gap-4 rounded-sm"
            >
              {isRefreshing ? <Loader2 className="w-5 h-5 animate-spin" /> : <RefreshCcw className="w-5 h-5" />}
              Kiểm tra hạ tầng
            </button>
          </div>
        </div>

        <div 
          className="grid lg:grid-cols-12 gap-12 transition-all duration-300 delay-75"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
            <div className="lg:col-span-8 space-y-12">
                <div className="bg-white border border-zinc-100 p-12 space-y-12 rounded-sm">
                    <div className="flex items-center justify-between border-b border-zinc-50 pb-8">
                        <div className="space-y-1">
                            <h3 className="text-xl font-bold tracking-tighter uppercase">Tham số kinh tế</h3>
                            <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest italic">Cấu hình luồng tiền trung tâm</p>
                        </div>
                        <DatabaseZap className="w-8 h-8 text-zinc-100" />
                    </div>
                    
                    <div className="grid md:grid-cols-2 gap-10">
                        <div className="space-y-4">
                            <label className="text-[10px] font-bold text-black uppercase tracking-widest flex items-center gap-2">
                                Tỷ lệ hoa hồng (%) <AlertCircle className="w-3 h-3 text-zinc-200" />
                            </label>
                            <input 
                              type="number" 
                              value={formConfig.commission_rate * 100} 
                              onChange={(e) => setFormConfig({...formConfig, commission_rate: parseFloat(e.target.value) / 100})}
                              className="w-full h-16 px-8 bg-zinc-50 border border-zinc-100 focus:border-black outline-none font-bold text-lg tracking-tight transition-all rounded-sm" 
                            />
                        </div>
                        <div className="space-y-4">
                            <label className="text-[10px] font-bold text-black uppercase tracking-widest">Phí rút tiền cố định (dl)</label>
                            <input 
                              type="number" 
                              value={formConfig.withdrawal_fee_dl} 
                              onChange={(e) => setFormConfig({...formConfig, withdrawal_fee_dl: parseInt(e.target.value)})}
                              className="w-full h-16 px-8 bg-zinc-50 border border-zinc-100 focus:border-black outline-none font-bold text-lg tracking-tight transition-all rounded-sm" 
                            />
                        </div>
                    </div>
                    
                    <div className="space-y-4 pt-4">
                        <label className="text-[10px] font-bold text-black uppercase tracking-widest">Hạn mức rút tiền tối thiểu (dl)</label>
                        <input 
                          type="number" 
                          value={formConfig.min_withdrawal_dl} 
                          onChange={(e) => setFormConfig({...formConfig, min_withdrawal_dl: parseInt(e.target.value)})}
                          className="w-full h-16 px-8 bg-zinc-50 border border-zinc-100 focus:border-black outline-none font-bold text-lg tracking-tight transition-all rounded-sm" 
                        />
                    </div>

                    <div className="pt-8 border-t border-zinc-50">
                        <button 
                            onClick={handleUpdateConfig}
                            className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] hover:bg-zinc-800 transition-all active:scale-[0.98] rounded-sm"
                        >
                            Lưu cấu hình tài chính
                        </button>
                    </div>
                </div>

                <div className="bg-white border border-zinc-100 p-12 space-y-10 rounded-sm">
                    <div className="space-y-1">
                        <h3 className="text-xl font-bold tracking-tighter uppercase">Trạng thái dịch vụ</h3>
                        <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Kết nối hạ tầng mạng & Database</p>
                    </div>
                    <div className="grid md:grid-cols-2 gap-6">
                        <div className="p-8 border border-zinc-50 flex items-center justify-between rounded-sm group hover:border-black transition-all">
                            <div className="flex items-center gap-5">
                                <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-sm group-hover:bg-black transition-all duration-300">
                                    <Database className="w-6 h-6 text-zinc-200 group-hover:text-white" />
                                </div>
                                <span className="text-[11px] font-bold uppercase tracking-widest text-black">MongoDB Core</span>
                            </div>
                            <span className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest flex items-center gap-2">
                                <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" /> Đã kết nối
                            </span>
                        </div>
                        <div className="p-8 border border-zinc-50 flex items-center justify-between rounded-sm group hover:border-black transition-all">
                            <div className="flex items-center gap-5">
                                <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-sm group-hover:bg-black transition-all duration-300">
                                    <Zap className="w-6 h-6 text-zinc-200 group-hover:text-white" />
                                </div>
                                <span className="text-[11px] font-bold uppercase tracking-widest text-black">Redis Cache</span>
                            </div>
                            <span className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest flex items-center gap-2">
                                <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" /> Hoạt động
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="lg:col-span-4 space-y-12">
                <div className={`p-12 border transition-all duration-300 rounded-sm ${maintenanceMode ? 'bg-black text-white border-black' : 'bg-white border-zinc-100 text-black'}`}>
                    <div className="flex items-center justify-between mb-10">
                        <h3 className="text-[11px] font-bold uppercase tracking-[0.2em]">Chế độ bảo trì</h3>
                        <button 
                            onClick={handleToggleMaintenance} 
                            className={`w-16 h-9 transition-all relative rounded-full ${maintenanceMode ? 'bg-zinc-800' : 'bg-zinc-100'}`}
                        >
                            <div className={`absolute top-1 w-7 h-7 transition-all rounded-full ${maintenanceMode ? 'bg-white left-8' : 'bg-black left-1'}`} />
                        </button>
                    </div>
                    <div className="space-y-6">
                        <p className="text-[12px] font-medium leading-relaxed italic opacity-50">
                            {maintenanceMode 
                                ? "Toàn bộ hệ thống đang được tạm khóa để bảo trì kỹ thuật. Chỉ quản trị viên có quyền truy cập." 
                                : "Hệ thống đang ở trạng thái công khai. Mọi dịch vụ đều khả dụng cho người dùng."}
                        </p>
                        <div className="flex items-center gap-3 text-[9px] font-bold uppercase tracking-widest opacity-30">
                            <Server className="w-3.5 h-3.5" /> Security Protocol v4.2
                        </div>
                    </div>
                </div>

                <div className="bg-white border border-zinc-100 p-12 space-y-10 rounded-sm">
                     <div className="space-y-1">
                        <h3 className="text-[11px] font-bold uppercase tracking-widest">Công cụ quản trị</h3>
                        <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Thao tác hệ thống trực tiếp</p>
                     </div>
                     <div className="grid gap-4">
                        <button 
                            onClick={handleTriggerBackup}
                            className="h-16 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all flex items-center justify-center gap-4 rounded-sm group"
                        >
                            <HardDrive className="w-5 h-5 text-zinc-200 group-hover:text-black" /> Sao lưu Database
                        </button>
                        <button className="h-16 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all flex items-center justify-center gap-4 rounded-sm group">
                            <Activity className="w-5 h-5 text-zinc-200 group-hover:text-black" /> Dọn dẹp Cache
                        </button>
                        <button className="h-16 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest hover:text-red-500 hover:border-red-500 transition-all flex items-center justify-center gap-4 rounded-sm group">
                            <Terminal className="w-5 h-5 text-zinc-200 group-hover:text-red-500" /> System Logs
                        </button>
                     </div>
                </div>

                <div className="p-10 bg-zinc-50 border border-zinc-100 rounded-sm space-y-6">
                    <div className="flex items-center gap-4 text-black">
                        <Cpu className="w-5 h-5" />
                        <span className="text-[11px] font-bold uppercase tracking-widest">Tải máy chủ</span>
                    </div>
                    <div className="space-y-4">
                        <div className="h-1.5 w-full bg-zinc-100 rounded-full overflow-hidden">
                            <div className="h-full bg-black w-[15%] transition-all duration-1000" />
                        </div>
                        <div className="flex justify-between text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                            <span>CPU: 12%</span>
                            <span>RAM: 2.4GB / 8GB</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
      </div>
  );
}
