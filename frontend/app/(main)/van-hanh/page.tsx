"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getSystemHealthAPI,
  getMaintenanceModeAPI,
  toggleMaintenanceModeAPI,
  triggerBackupAPI,
} from "@/services/operation.service";
import { getGlobalQuotaConfigAPI, updateRoleQuotaAPI } from "@/services/quota.service";
import { Loader2, Save } from "lucide-react";
import { useAuth } from "@/contexts/Auth";
import { useToast } from "@/contexts/Toast";

export default function OperationDashboard() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();

  const [health, setHealth] = useState<any>(null);
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const [quotaConfigs, setQuotaConfigs] = useState<any>(null);
  const [quotaLoading, setQuotaLoading] = useState(true);
  const [isSavingQuota, setIsSavingQuota] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [hData, mData, qData] = await Promise.all([
        getSystemHealthAPI(),
        getMaintenanceModeAPI(),
        getGlobalQuotaConfigAPI()
      ]);

      if (hData) setHealth(hData.data || hData);
      if (mData) setMaintenanceMode(mData.data?.enabled || mData.enabled || false);
      if (qData) setQuotaConfigs(qData);
    } catch (err: any) {
      showToast("Không thể tải dữ liệu hệ thống.", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      setQuotaLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    if (!authLoading && user?.role === "admin") {
      fetchData();
    }
  }, [user, authLoading, fetchData]);

  const toggleMaintenance = async () => {
    if (isProcessing) return;
    setIsProcessing(true);
    try {
      await toggleMaintenanceModeAPI(!maintenanceMode);
      setMaintenanceMode(!maintenanceMode);
      showToast(
        !maintenanceMode ? "Hệ thống đã vào chế độ bảo trì." : "Đã tắt chế độ bảo trì.",
        "success"
      );
    } catch (err: any) {
      showToast("Lỗi chuyển đổi chế độ bảo trì.", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const triggerBackup = async () => {
    if (isProcessing) return;
    setIsProcessing(true);
    try {
      await triggerBackupAPI();
      showToast("Đã gửi yêu cầu sao lưu hệ thống.", "success");
    } catch (err: any) {
      showToast("Lỗi khi yêu cầu sao lưu.", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUpdateQuota = async (role: string) => {
    setIsSavingQuota(role);
    try {
      await updateRoleQuotaAPI(role, quotaConfigs[role]);
      showToast(`Đã cập nhật hạn mức cho nhóm ${role}.`, "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi khi cập nhật.", "error");
    } finally {
      setIsSavingQuota(null);
    }
  };

  const handleQuotaChange = (role: string, field: string, value: string) => {
    setQuotaConfigs((prev: any) => ({
      ...prev,
      [role]: {
        ...prev[role],
        [field]: parseInt(value) || 0
      }
    }));
  };

  const roleLabels: Record<string, string> = {
    reader: "Độc giả",
    author: "Tác giả",
    moderator: "Kiểm duyệt viên",
    admin: "Quản trị viên"
  };

  if (authLoading || isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white font-sans text-black">
      <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12">
        <header className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl font-semibold text-black">Hệ thống điều hành</h1>
            <p className="text-sm text-zinc-500 mt-1">Terminal quản trị trung tâm DocLib</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="text-sm font-medium text-zinc-500 disabled:opacity-50"
            >
              {isRefreshing ? "Đang đồng bộ" : "Đồng bộ dữ liệu"}
            </button>
          </div>
        </header>

        <div className="space-y-12 mb-16 animate-in fade-in duration-300">
          <div className="space-y-12">
            <section className="space-y-6">
              <h2 className="text-sm font-semibold text-black border-b border-zinc-200 pb-3">Sức khỏe hệ thống</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="p-6 border border-zinc-200 bg-white space-y-4">
                  <div className="text-[10px] font-bold text-zinc-400 tracking-widest uppercase">Máy chủ chính</div>
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-black' : 'bg-red-500'}`}></div>
                      <span className="text-xs font-medium text-black">
                        {health?.status === "healthy" ? "Hoạt động" : "Gặp sự cố"}
                      </span>
                    </div>
                    {health?.resources?.cpu_load && (
                      <span className="text-[10px] text-zinc-500 font-medium">Tải CPU: {health.resources.cpu_load}</span>
                    )}
                  </div>
                </div>

                <div className="p-6 border border-zinc-200 bg-white space-y-4">
                  <div className="text-[10px] font-bold text-zinc-400 tracking-widest uppercase">Cơ sở dữ liệu</div>
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${health?.services?.database === 'connected' ? 'bg-black' : 'bg-red-500'}`}></div>
                      <span className="text-xs font-medium text-black">
                        {health?.services?.database === "connected" ? "Đã kết nối" : "Mất kết nối"}
                      </span>
                    </div>
                    <span className="text-[10px] text-zinc-500 font-medium">MongoDB v7.0</span>
                  </div>
                </div>

                <div className="p-6 border border-zinc-200 bg-white space-y-4">
                  <div className="text-[10px] font-bold text-zinc-400 tracking-widest uppercase">Bộ nhớ đệm</div>
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${health?.services?.cache === 'connected' ? 'bg-black' : 'bg-red-500'}`}></div>
                      <span className="text-xs font-medium text-black">
                        {health?.services?.cache === "connected" ? "Đã kết nối" : "Lỗi kết nối"}
                      </span>
                    </div>
                    <span className="text-[10px] text-zinc-500 font-medium">Redis Cloud</span>
                  </div>
                </div>

                <div className="p-6 border border-zinc-200 bg-white space-y-4">
                  <div className="text-[10px] font-bold text-zinc-400 tracking-widest uppercase">Trí tuệ nhân tạo</div>
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${health?.services?.ai_agent === 'healthy' ? 'bg-black' : 'bg-red-500'}`}></div>
                      <span className="text-xs font-medium text-black">
                        {health?.services?.ai_agent === "healthy" ? "Sẵn sàng" : "Chưa sẵn sàng"}
                      </span>
                    </div>
                    <span className="text-[10px] text-zinc-500 font-medium">Agentic RAG Service</span>
                  </div>
                </div>
              </div>
            </section>

            <section className="space-y-6">
              <h2 className="text-sm font-semibold text-black border-b border-zinc-200 pb-3">Hành động điều hành</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-6 border border-zinc-200 bg-white space-y-6">
                  <div className="space-y-1">
                    <h3 className="text-sm font-semibold text-black">Chế độ bảo trì</h3>
                    <p className="text-xs text-zinc-500 font-medium">Ngắt kết nối người dùng để bảo trì hệ thống</p>
                  </div>
                  <button
                    onClick={toggleMaintenance}
                    disabled={isProcessing}
                    className={`h-10 px-6 text-xs font-semibold border transition-all duration-200 disabled:opacity-50 rounded-none ${
                      maintenanceMode 
                        ? "bg-black text-white border-black" 
                        : "bg-white text-black border-zinc-200 hover:border-black"
                    }`}
                  >
                    {maintenanceMode ? "Tắt bảo trì" : "Bật bảo trì"}
                  </button>
                </div>

                <div className="p-6 border border-zinc-200 bg-white space-y-6">
                  <div className="space-y-1">
                    <h3 className="text-sm font-semibold text-black">Sao lưu dữ liệu</h3>
                    <p className="text-xs text-zinc-500 font-medium">Khởi tạo quy trình sao lưu toàn bộ cơ sở dữ liệu</p>
                  </div>
                  <button
                    onClick={triggerBackup}
                    disabled={isProcessing}
                    className="h-10 px-6 bg-white text-black text-xs font-semibold border border-black hover:bg-black hover:text-white transition-all duration-200 disabled:opacity-50 rounded-none"
                  >
                    Tiến hành sao lưu
                  </button>
                </div>
              </div>
            </section>
          </div>
        </div>

        <div className="space-y-12 animate-in fade-in duration-300">
          <section>
            <div className="flex flex-col gap-1 mb-6">
              <h2 className="text-sm font-semibold text-black border-b border-zinc-200 pb-3 w-full">Hạn mức Trí tuệ nhân tạo (AI Quota)</h2>
              <p className="text-[10px] text-zinc-500 font-medium">Áp dụng cho toàn bộ tính năng: Chat, Tìm kiếm thông minh, Tóm tắt, Phân tích cảm quan và Flashcards</p>
            </div>
            
            {quotaLoading ? (
              <div className="py-12 flex justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
              </div>
            ) : (
              <div className="border border-zinc-200 bg-white overflow-hidden">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px bg-zinc-200">
                  {Object.keys(quotaConfigs || {})
                    .filter(role => roleLabels[role])
                    .sort((a, b) => {
                      const order = ["reader", "author", "moderator", "admin"];
                      return order.indexOf(a) - order.indexOf(b);
                    })
                    .map((role) => {
                      const isAdmin = role === "admin";
                      return (
                        <div key={role} className={`p-6 flex flex-col gap-6 ${isAdmin ? 'bg-zinc-50' : 'bg-white'}`}>
                          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
                            <span className="text-xs font-semibold text-black">
                              {roleLabels[role] || role}
                            </span>
                            {!isAdmin && (
                              <button
                                onClick={() => handleUpdateQuota(role)}
                                disabled={!!isSavingQuota}
                                className="p-1 text-zinc-400 hover:text-black transition-all duration-200 rounded-none disabled:opacity-50"
                              >
                                {isSavingQuota === role ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                              </button>
                            )}
                          </div>

                          <div className="space-y-5">
                            <div className="space-y-2">
                              <label className="text-[10px] font-bold text-zinc-400 tracking-widest block">
                                Lượt yêu cầu / ngày
                              </label>
                              <input
                                type={isAdmin ? "text" : "number"}
                                value={isAdmin ? "Không giới hạn" : quotaConfigs[role].daily_requests}
                                readOnly={isAdmin}
                                onChange={(e) => !isAdmin && handleQuotaChange(role, "daily_requests", e.target.value)}
                                className={`w-full border px-3 py-2 text-xs font-medium focus:outline-none transition-all duration-200 rounded-none ${isAdmin ? 'bg-zinc-100 border-transparent text-zinc-400' : 'bg-zinc-50 border-zinc-200 focus:border-black'}`}
                              />
                            </div>

                            <div className="space-y-2">
                              <label className="text-[10px] font-bold text-zinc-400 tracking-widest block">
                                Token / ngày
                              </label>
                              <input
                                type={isAdmin ? "text" : "number"}
                                value={isAdmin ? "Không giới hạn" : quotaConfigs[role].daily_tokens}
                                readOnly={isAdmin}
                                onChange={(e) => !isAdmin && handleQuotaChange(role, "daily_tokens", e.target.value)}
                                className={`w-full border px-3 py-2 text-xs font-medium focus:outline-none transition-all duration-200 rounded-none ${isAdmin ? 'bg-zinc-100 border-transparent text-zinc-400' : 'bg-zinc-50 border-zinc-200 focus:border-black'}`}
                              />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
