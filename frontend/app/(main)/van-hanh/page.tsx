"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getSystemHealthAPI,
  getMaintenanceModeAPI,
  toggleMaintenanceModeAPI,
  triggerBackupAPI,
  getMinioStatsAPI,
} from "@/features/provision/services/system_operation.service";
import {
  getGlobalQuotaConfigAPI,
  updateRoleQuotaAPI,
} from "@/features/provision/services/usage_quota.service";
import {
  Loader2,
  Save,
  Server,
  Database,
  Cpu,
  Brain,
  HardDrive,
  RefreshCcw,
  ShieldAlert,
  Archive,
  Zap,
} from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";

export default function OperationDashboard() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();

  const [health, setHealth] = useState<any>(null);
  const [maintenanceMode, setMaintenanceMode] = useState(false);

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [visible, setVisible] = useState(false);

  const [quotaConfigs, setQuotaConfigs] = useState<any>(null);
  const [quotaLoading, setQuotaLoading] = useState(true);
  const [isSavingQuota, setIsSavingQuota] = useState<string | null>(null);

  const [minioStats, setMinioStats] = useState<any>(null);
  const [minioLoading, setMinioLoading] = useState(true);

  const formatBytes = (bytes: number, decimals = 2) => {
    if (!bytes || bytes === 0) return "0 Bytes";
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  };

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    setMinioLoading(true);
    try {
      const [hData, mData, qData, minioData] = await Promise.all([
        getSystemHealthAPI(),
        getMaintenanceModeAPI(),
        getGlobalQuotaConfigAPI(),
        getMinioStatsAPI(),
      ]);

      if (hData) setHealth(hData.data || hData);
      if (mData)
        setMaintenanceMode(mData.data?.enabled || mData.enabled || false);
      if (qData) setQuotaConfigs(qData);
      if (minioData) setMinioStats(minioData.data || minioData);
    } catch (err: any) {
      showToast("Không thể tải dữ liệu hệ thống.", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      setQuotaLoading(false);
      setMinioLoading(false);
      requestAnimationFrame(() => setVisible(true));
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
        !maintenanceMode
          ? "Hệ thống đã vào chế độ bảo trì."
          : "Đã tắt chế độ bảo trì.",
        "success",
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
        [field]: parseInt(value) || 0,
      },
    }));
  };

  const roleLabels: Record<string, string> = {
    BASIC: "Cơ bản",
    PRO: "Nâng cao",
    PREMIUM: "Cao cấp",
    admin: "Quản trị viên",
  };

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
          <ShieldAlert className="w-8 h-8 text-zinc-400" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold tracking-tight text-zinc-900">
            Truy cập bị hạn chế
          </h2>
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
            Bạn không có quyền quản trị hệ thống
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 min-h-[calc(100dvh-var(--navbar-height))] font-sans text-zinc-900 bg-zinc-50 selection:bg-black selection:text-white">
      <header className="mb-6 md:mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
            Hệ thống điều hành
          </h1>
          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
            Terminal quản trị trung tâm DocLib
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={isRefreshing}
          className="h-11 px-5 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-zinc-900 disabled:opacity-50 flex items-center justify-center gap-2 rounded-2xl shadow-sm transition-all duration-200 hover:scale-[1.02]"
        >
          {isRefreshing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCcw className="w-4 h-4" />
          )}
          Đồng bộ dữ liệu
        </button>
      </header>

      <div className="space-y-6 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <section className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm space-y-6">
          <div className="border-b border-zinc-100 pb-4">
            <h2 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
              Sức khỏe hệ thống
            </h2>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
              Trạng thái các dịch vụ cốt lõi
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
            <div className="p-6 border border-zinc-100 bg-zinc-50/50 space-y-4 rounded-3xl shadow-sm transition-all duration-300 hover:border-zinc-200 hover:shadow-md">
              <div className="flex items-center gap-3 border-b border-zinc-100 pb-3">
                <Server className="w-5 h-5 text-black" />
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                  Máy chủ chính
                </span>
              </div>
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full shadow-sm ${health?.status === "healthy" ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"}`}
                  ></div>
                  <span className="text-xs font-bold text-zinc-900 uppercase tracking-widest">
                    {health?.status === "healthy"
                      ? "Hoạt động"
                      : "Gặp sự cố"}
                  </span>
                </div>
                {health?.resources?.cpu_load && (
                  <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                    Tải CPU: {health.resources.cpu_load}
                  </span>
                )}
              </div>
            </div>

            <div className="p-6 border border-zinc-100 bg-zinc-50/50 space-y-4 rounded-3xl shadow-sm transition-all duration-300 hover:border-zinc-200 hover:shadow-md">
              <div className="flex items-center gap-3 border-b border-zinc-100 pb-3">
                <Database className="w-5 h-5 text-black" />
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                  Cơ sở dữ liệu
                </span>
              </div>
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full shadow-sm ${health?.services?.database === "connected" ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"}`}
                  ></div>
                  <span className="text-xs font-bold text-zinc-900 uppercase tracking-widest">
                    {health?.services?.database === "connected"
                      ? "Đã kết nối"
                      : "Mất kết nối"}
                  </span>
                </div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  MongoDB v7.0
                </span>
              </div>
            </div>

            <div className="p-6 border border-zinc-100 bg-zinc-50/50 space-y-4 rounded-3xl shadow-sm transition-all duration-300 hover:border-zinc-200 hover:shadow-md">
              <div className="flex items-center gap-3 border-b border-zinc-100 pb-3">
                <Cpu className="w-5 h-5 text-black" />
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                  Bộ nhớ đệm
                </span>
              </div>
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full shadow-sm ${health?.services?.cache === "connected" ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"}`}
                  ></div>
                  <span className="text-xs font-bold text-zinc-900 uppercase tracking-widest">
                    {health?.services?.cache === "connected"
                      ? "Đã kết nối"
                      : "Lỗi kết nối"}
                  </span>
                </div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  Redis Cloud
                </span>
              </div>
            </div>

            <div className="p-6 border border-zinc-100 bg-zinc-50/50 space-y-4 rounded-3xl shadow-sm transition-all duration-300 hover:border-zinc-200 hover:shadow-md">
              <div className="flex items-center gap-3 border-b border-zinc-100 pb-3">
                <Brain className="w-5 h-5 text-black" />
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                  Trí tuệ nhân tạo
                </span>
              </div>
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full shadow-sm ${health?.services?.ai_agent === "healthy" ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"}`}
                  ></div>
                  <span className="text-xs font-bold text-zinc-900 uppercase tracking-widest">
                    {health?.services?.ai_agent === "healthy"
                      ? "Sẵn sàng"
                      : "Chưa sẵn sàng"}
                  </span>
                </div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  Agentic RAG Service
                </span>
              </div>
            </div>
          </div>
        </section>

        <section className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-100 pb-4">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
                Kho lưu trữ (MinIO)
              </h2>
              <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                Thống kê Object Storage
              </p>
            </div>
            <div className="flex items-center gap-2 bg-zinc-50 px-3 py-1.5 rounded-xl border border-zinc-100 shadow-sm">
              <div
                className={`w-2 h-2 rounded-full shadow-sm ${minioStats?.status === "healthy" ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"}`}
              ></div>
              <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-900">
                {minioStats?.status === "healthy"
                  ? "Đang kết nối"
                  : "Mất kết nối"}
              </span>
            </div>
          </div>

          {minioLoading ? (
            <div className="py-12 flex justify-center bg-zinc-50/50 rounded-3xl border border-zinc-100">
              <Loader2 className="w-8 h-8 animate-spin text-zinc-300" />
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                <div className="p-6 border border-zinc-100 bg-zinc-50/50 space-y-4 rounded-3xl shadow-sm text-center transition-all duration-300 hover:bg-white hover:border-zinc-200">
                  <div className="w-12 h-12 bg-white border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mx-auto mb-2">
                    <HardDrive className="w-5 h-5 text-black" />
                  </div>
                  <div className="text-[10px] font-bold text-zinc-400 tracking-widest uppercase">
                    Tổng dung lượng
                  </div>
                  <div className="text-3xl font-bold tracking-tight text-zinc-900">
                    {formatBytes(minioStats?.total_size_bytes || 0)}
                  </div>
                </div>

                <div className="p-6 border border-zinc-100 bg-zinc-50/50 space-y-4 rounded-3xl shadow-sm text-center transition-all duration-300 hover:bg-white hover:border-zinc-200">
                  <div className="w-12 h-12 bg-white border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mx-auto mb-2">
                    <Archive className="w-5 h-5 text-black" />
                  </div>
                  <div className="text-[10px] font-bold text-zinc-400 tracking-widest uppercase">
                    Tổng số tệp tin
                  </div>
                  <div className="text-3xl font-bold tracking-tight text-zinc-900">
                    {minioStats?.total_objects_count || 0}
                  </div>
                </div>

                <div className="p-6 border border-zinc-100 bg-zinc-50/50 space-y-4 rounded-3xl shadow-sm text-center transition-all duration-300 hover:bg-white hover:border-zinc-200">
                  <div className="w-12 h-12 bg-white border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mx-auto mb-2">
                    <Server className="w-5 h-5 text-black" />
                  </div>
                  <div className="text-[10px] font-bold text-zinc-400 tracking-widest uppercase">
                    Số lượng Buckets
                  </div>
                  <div className="text-3xl font-bold tracking-tight text-zinc-900">
                    {minioStats?.total_buckets || 0}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="p-6 border border-zinc-100 bg-zinc-50/50 space-y-4 rounded-3xl shadow-sm">
                  <div className="text-[10px] font-bold text-zinc-400 tracking-widest uppercase pb-3 border-b border-zinc-100 flex items-center gap-2">
                    <Archive className="w-4 h-4 text-black" />
                    Danh sách Buckets
                  </div>
                  <div className="divide-y divide-zinc-100 max-h-[220px] overflow-y-auto pr-2 custom-scrollbar">
                    {minioStats?.buckets?.length > 0 ? (
                      minioStats.buckets.map((b: any) => (
                        <div
                          key={b.name}
                          className="py-3 flex items-center justify-between"
                        >
                          <div>
                            <span className="text-xs font-bold text-zinc-900 block">
                              {b.name}
                            </span>
                            <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-400 block mt-1">
                              Tạo:{" "}
                              {new Date(b.created_at).toLocaleDateString(
                                "vi-VN",
                              )}
                            </span>
                          </div>
                          <div className="text-right">
                            <span className="text-xs font-bold text-zinc-900 block">
                              {formatBytes(b.size_bytes)}
                            </span>
                            <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500 block mt-1">
                              {b.objects_count} tệp tin
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="py-8 text-center text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                        Không tìm thấy bucket nào
                      </div>
                    )}
                  </div>
                </div>

                <div className="p-6 border border-zinc-100 bg-zinc-50/50 space-y-4 rounded-3xl shadow-sm">
                  <div className="text-[10px] font-bold text-zinc-400 tracking-widest uppercase pb-3 border-b border-zinc-100 flex items-center gap-2">
                    <Database className="w-4 h-4 text-black" />
                    Phân loại dữ liệu
                  </div>
                  <div className="divide-y divide-zinc-100 max-h-[220px] overflow-y-auto pr-2 custom-scrollbar">
                    {minioStats?.categories?.length > 0 ? (
                      minioStats.categories.map((c: any) => (
                        <div
                          key={c.name}
                          className="py-3 flex items-center justify-between"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-2 h-2 bg-black rounded-full shadow-sm"></div>
                            <span className="text-xs font-bold text-zinc-900">
                              {c.name}
                            </span>
                          </div>
                          <div className="text-right">
                            <span className="text-xs font-bold text-zinc-900 block">
                              {formatBytes(c.size_bytes)}
                            </span>
                            <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500 block mt-1">
                              {c.count} tệp tin
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="py-8 text-center text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                        Chưa phân loại được dữ liệu
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>

        <section className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm space-y-6">
          <div className="border-b border-zinc-100 pb-4">
            <h2 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
              Hành động điều hành
            </h2>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
              Công cụ quản trị hệ thống nhanh
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 border border-red-100 bg-red-50/50 space-y-6 rounded-3xl shadow-sm">
              <div className="flex items-start gap-4 border-b border-red-100 pb-4">
                <div className="w-12 h-12 bg-red-100 flex items-center justify-center rounded-2xl shrink-0">
                  <ShieldAlert className="w-6 h-6 text-red-600" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-sm font-bold text-red-600">
                    Chế độ bảo trì
                  </h3>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-red-400/80 leading-relaxed">
                    Ngắt kết nối người dùng để bảo trì hệ thống. Cảnh báo: Gây gián đoạn dịch vụ.
                  </p>
                </div>
              </div>
              <button
                onClick={toggleMaintenance}
                disabled={isProcessing}
                className={`w-full h-11 text-[10px] font-bold uppercase tracking-widest transition-all duration-200 disabled:opacity-50 rounded-2xl flex items-center justify-center shadow-md hover:scale-[1.02] hover:-translate-y-0.5 ${
                  maintenanceMode
                    ? "bg-red-600 text-white border-transparent"
                    : "bg-white text-zinc-900 border border-zinc-200"
                }`}
              >
                {maintenanceMode ? "Tắt bảo trì hệ thống" : "Kích hoạt chế độ bảo trì"}
              </button>
            </div>

            <div className="p-6 border border-zinc-100 bg-zinc-50/50 space-y-6 rounded-3xl shadow-sm">
              <div className="flex items-start gap-4 border-b border-zinc-100 pb-4">
                <div className="w-12 h-12 bg-white border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl shrink-0">
                  <Archive className="w-6 h-6 text-black" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-sm font-bold text-zinc-900">
                    Sao lưu dữ liệu
                  </h3>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 leading-relaxed">
                    Khởi tạo quy trình sao lưu toàn bộ cơ sở dữ liệu và chuyển về kho lưu trữ lạnh.
                  </p>
                </div>
              </div>
              <button
                onClick={triggerBackup}
                disabled={isProcessing}
                className="w-full h-11 bg-black text-white text-[10px] font-bold uppercase tracking-widest border border-transparent transition-all duration-200 disabled:opacity-50 rounded-2xl flex items-center justify-center shadow-md hover:scale-[1.02] hover:-translate-y-0.5"
              >
                Tiến hành sao lưu
              </button>
            </div>
          </div>
        </section>

        <section className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm space-y-6">
          <div className="border-b border-zinc-100 pb-4">
            <h2 className="text-xl font-bold tracking-tight text-zinc-900 mb-1 flex items-center gap-2">
              <Zap className="w-5 h-5 text-black" />
              Hạn mức AI
            </h2>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
              Quản lý tài nguyên RAG Agent theo phân quyền
            </p>
          </div>

          {quotaLoading ? (
            <div className="py-12 flex justify-center bg-zinc-50/50 rounded-3xl border border-zinc-100">
              <Loader2 className="w-8 h-8 animate-spin text-zinc-300" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {Object.keys(quotaConfigs || {})
                .filter((role) => roleLabels[role])
                .sort((a, b) => {
                  const order = ["BASIC", "PRO", "PREMIUM", "admin"];
                  return order.indexOf(a) - order.indexOf(b);
                })
                .map((role) => {
                  const isAdmin = role === "admin";
                  return (
                    <div
                      key={role}
                      className={`p-6 flex flex-col gap-6 rounded-3xl border shadow-sm transition-all duration-300 ${isAdmin ? "bg-zinc-50 border-zinc-200" : "bg-white border-zinc-100 hover:border-zinc-300 hover:shadow-md"}`}
                    >
                      <div className="flex items-center justify-between border-b border-zinc-100 pb-4">
                        <span className="text-xs font-bold text-zinc-900 uppercase tracking-widest">
                          {roleLabels[role] || role}
                        </span>
                        {!isAdmin && (
                          <button
                            onClick={() => handleUpdateQuota(role)}
                            disabled={!!isSavingQuota}
                            className="w-8 h-8 flex items-center justify-center bg-zinc-50 border border-zinc-100 text-black rounded-xl disabled:opacity-50 transition-all duration-200 hover:scale-[1.05] shadow-sm"
                          >
                            {isSavingQuota === role ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Save className="w-3.5 h-3.5" />
                            )}
                          </button>
                        )}
                      </div>

                      <div className="space-y-5">
                        <div className="space-y-2">
                          <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest block ml-1">
                            Lượt yêu cầu / ngày
                          </label>
                          <input
                            type={isAdmin ? "text" : "number"}
                            value={
                              isAdmin
                                ? "Không giới hạn"
                                : quotaConfigs[role].daily_requests
                            }
                            readOnly={isAdmin}
                            onChange={(e) =>
                              !isAdmin &&
                              handleQuotaChange(
                                role,
                                "daily_requests",
                                e.target.value,
                              )
                            }
                            className={`w-full border px-4 py-2.5 text-xs font-bold transition-all duration-200 focus:outline-none rounded-2xl ${isAdmin ? "bg-zinc-100 border-transparent text-zinc-500 cursor-not-allowed" : "bg-zinc-50 border-zinc-200 focus:border-black text-zinc-900 shadow-sm"}`}
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest block ml-1">
                            Token / ngày
                          </label>
                          <input
                            type={isAdmin ? "text" : "number"}
                            value={
                              isAdmin
                                ? "Không giới hạn"
                                : quotaConfigs[role].daily_tokens
                            }
                            readOnly={isAdmin}
                            onChange={(e) =>
                              !isAdmin &&
                              handleQuotaChange(
                                role,
                                "daily_tokens",
                                e.target.value,
                              )
                            }
                            className={`w-full border px-4 py-2.5 text-xs font-bold transition-all duration-200 focus:outline-none rounded-2xl ${isAdmin ? "bg-zinc-100 border-transparent text-zinc-500 cursor-not-allowed" : "bg-zinc-50 border-zinc-200 focus:border-black text-zinc-900 shadow-sm"}`}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
