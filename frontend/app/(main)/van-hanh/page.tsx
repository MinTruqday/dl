"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getSystemHealthAPI,
  getMaintenanceModeAPI,
  toggleMaintenanceModeAPI,
  triggerBackupAPI,
  getMinioStatsAPI,
} from "@/features/management/services/health.service";
import {
  getGlobalQuotaConfigAPI,
  updateRoleQuotaAPI,
} from "@/features/usage/services/quota.service";
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
  Shield,
} from "lucide-react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import PageLoader from "@/shared/components/common/PageLoader";

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

  const [minioStats, setMinioStats] = useState<any>(null);
  const [minioLoading, setMinioLoading] = useState(true);

  const formatBytes = (bytes: number, decimals = 2) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
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
      showToast("Lỗi tải dữ liệu", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      setQuotaLoading(false);
      setMinioLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    if (!authLoading && user?.role === "admin") fetchData();
  }, [user, authLoading, fetchData]);

  const toggleMaintenance = async () => {
    if (isProcessing) return;
    setIsProcessing(true);
    try {
      await toggleMaintenanceModeAPI(!maintenanceMode);
      setMaintenanceMode(!maintenanceMode);
      showToast(
        !maintenanceMode ? "Đã bật bảo trì" : "Đã tắt bảo trì",
        "success",
      );
    } catch (err: any) {
      showToast("Lỗi chế độ bảo trì", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const triggerBackup = async () => {
    if (isProcessing) return;
    setIsProcessing(true);
    try {
      await triggerBackupAPI();
      showToast("Đã yêu cầu sao lưu", "success");
    } catch (err: any) {
      showToast("Lỗi sao lưu", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUpdateQuota = async (role: string) => {
    setIsSavingQuota(role);
    try {
      await updateRoleQuotaAPI(role, quotaConfigs[role]);
      showToast(`Cập nhật hạn mức ${role} thành công`, "success");
    } catch (err: any) {
      showToast("Lỗi cập nhật hạn mức", "error");
    } finally {
      setIsSavingQuota(null);
    }
  };

  const handleQuotaChange = (role: string, field: string, value: string) => {
    setQuotaConfigs((p: any) => ({
      ...p,
      [role]: { ...p[role], [field]: parseInt(value) || 0 },
    }));
  };

  const roleLabels: Record<string, string> = {
    BASIC: "Cơ bản",
    PRO: "Nâng cao",
    PREMIUM: "Cao cấp",
    admin: "Quản trị viên",
  };

  if (authLoading || isLoading) return <PageLoader />;
  if (user?.role !== "admin")
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-56px)] gap-6 font-sans text-center">
        <div className="w-24 h-24 bg-[#F5F5F7] flex items-center justify-center rounded-[18px]">
          <ShieldAlert className="w-10 h-10 text-[#FF3B30]" />
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
    <div className="w-full max-w-[1200px] mx-auto px-6 py-6 font-sans text-[#1D1D1F] flex flex-col gap-8">
      <div className="flex flex-col md:flex-row md:items-center justify-end gap-4">
        <button
          onClick={fetchData}
          disabled={isRefreshing}
          className="pill-button flex items-center gap-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED]"
        >
          {isRefreshing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCcw className="w-4 h-4" />
          )}{" "}
          Đồng bộ
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="lg:col-span-2 bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] p-6 flex flex-col gap-6">
          <h2 className="text-[20px] font-semibold text-[#1D1D1F] flex items-center gap-2">
            <Server className="w-5 h-5 text-[#6E6E73]" /> Sức khỏe hệ thống
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-[#F5F5F7] rounded-[18px] p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-[14px] font-medium text-[#1D1D1F]">
                  Core API
                </span>
                <div
                  className={`w-2.5 h-2.5 rounded-full ${health?.status === "healthy" ? "bg-[#34C759]" : "bg-[#FF3B30]"}`}
                />
              </div>
              <p className="text-[13px] text-[#6E6E73]">
                {health?.status === "healthy"
                  ? "Hoạt động ổn định"
                  : "Gặp sự cố"}
              </p>
            </div>
            <div className="bg-[#F5F5F7] rounded-[18px] p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-[14px] font-medium text-[#1D1D1F]">
                  Database
                </span>
                <div
                  className={`w-2.5 h-2.5 rounded-full ${health?.services?.database === "connected" ? "bg-[#34C759]" : "bg-[#FF3B30]"}`}
                />
              </div>
              <p className="text-[13px] text-[#6E6E73]">MongoDB v7.0</p>
            </div>
            <div className="bg-[#F5F5F7] rounded-[18px] p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-[14px] font-medium text-[#1D1D1F]">
                  Cache
                </span>
                <div
                  className={`w-2.5 h-2.5 rounded-full ${health?.services?.cache === "connected" ? "bg-[#34C759]" : "bg-[#FF3B30]"}`}
                />
              </div>
              <p className="text-[13px] text-[#6E6E73]">Redis Cloud</p>
            </div>
            <div className="bg-[#F5F5F7] rounded-[18px] p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-[14px] font-medium text-[#1D1D1F]">
                  AI Agent
                </span>
                <div
                  className={`w-2.5 h-2.5 rounded-full ${health?.services?.ai_agent === "healthy" ? "bg-[#34C759]" : "bg-[#FF3B30]"}`}
                />
              </div>
              <p className="text-[13px] text-[#6E6E73]">RAG Service</p>
            </div>
          </div>
        </section>

        <section className="bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] p-6 flex flex-col gap-6">
          <h2 className="text-[20px] font-semibold text-[#1D1D1F] flex items-center gap-2">
            <Shield className="w-5 h-5 text-[#6E6E73]" /> Điều hành
          </h2>
          <div className="flex flex-col gap-4">
            <div className="bg-[#FFF4E5] rounded-[18px] p-5 border border-[#FF9500]/20 flex flex-col gap-4">
              <div>
                <h3 className="text-[17px] font-medium text-[#FF9500]">
                  Bảo trì hệ thống
                </h3>
                <p className="text-[13px] text-[#FF9500]/80 mt-1">
                  Ngắt kết nối người dùng. Gây gián đoạn.
                </p>
              </div>
              <button
                onClick={toggleMaintenance}
                disabled={isProcessing}
                className={`w-full py-2.5 rounded-full text-[13px] font-medium transition-colors ${maintenanceMode ? "bg-[#FF3B30] text-white" : "bg-white text-[#FF9500] hover:bg-[#FF9500]/10"}`}
              >
                {maintenanceMode ? "Tắt bảo trì" : "Bật bảo trì"}
              </button>
            </div>
            <div className="bg-[#F5F5F7] rounded-[18px] p-5 flex flex-col gap-4">
              <div>
                <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-4">
                  Sao lưu dữ liệu
                </h2>
                <p className="text-[13px] text-[#6E6E73] mt-1">
                  Snapshot toàn bộ DB về kho lạnh.
                </p>
              </div>
              <button
                onClick={triggerBackup}
                disabled={isProcessing}
                className="w-full py-2.5 bg-white text-[#0071E3] font-medium rounded-full text-[13px] font-medium hover:bg-[#E8E8ED] "
              >
                Tiến hành sao lưu
              </button>
            </div>
          </div>
        </section>
      </div>

      <section className="bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] p-6 flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <h2 className="text-[20px] font-semibold text-[#1D1D1F] flex items-center gap-2">
            <HardDrive className="w-5 h-5 text-[#6E6E73]" /> Kho lưu trữ (MinIO)
          </h2>
          <div className="flex items-center gap-2 bg-[#F5F5F7] px-3 py-1.5 rounded-full">
            <div
              className={`w-2 h-2 rounded-full ${minioStats?.status === "healthy" ? "bg-[#34C759]" : "bg-[#FF3B30]"}`}
            />
            <span className="text-[12px] font-medium text-[#6E6E73]">
              {minioStats?.status === "healthy" ? "Đã kết nối" : "Mất kết nối"}
            </span>
          </div>
        </div>

        {minioLoading ? (
          <div className="py-10 flex justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-[#6E6E73]" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-[#F5F5F7] rounded-[18px] p-6 text-center">
              <p className="text-[13px] text-[#6E6E73] font-medium mb-1">
                Tổng dung lượng
              </p>
              <p className="text-[28px] font-semibold text-[#1D1D1F]">
                {formatBytes(minioStats?.total_size_bytes || 0)}
              </p>
            </div>
            <div className="bg-[#F5F5F7] rounded-[18px] p-6 text-center">
              <p className="text-[13px] text-[#6E6E73] font-medium mb-1">
                Tổng số tệp
              </p>
              <p className="text-[28px] font-semibold text-[#1D1D1F]">
                {minioStats?.total_objects_count || 0}
              </p>
            </div>
            <div className="bg-[#F5F5F7] rounded-[18px] p-6 text-center">
              <p className="text-[13px] text-[#6E6E73] font-medium mb-1">
                Số lượng Buckets
              </p>
              <p className="text-[28px] font-semibold text-[#1D1D1F]">
                {minioStats?.total_buckets || 0}
              </p>
            </div>
          </div>
        )}
      </section>

      <section className="bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] p-6 flex flex-col gap-6">
        <h2 className="text-[20px] font-semibold text-[#1D1D1F] flex items-center gap-2">
          <Zap className="w-5 h-5 text-[#6E6E73]" /> Hạn mức AI
        </h2>
        {quotaLoading ? (
          <div className="py-10 flex justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-[#6E6E73]" />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {Object.keys(quotaConfigs || {})
              .filter((r) => roleLabels[r])
              .sort(
                (a, b) =>
                  ["BASIC", "PRO", "PREMIUM", "admin"].indexOf(a) -
                  ["BASIC", "PRO", "PREMIUM", "admin"].indexOf(b),
              )
              .map((role) => {
                const isAdmin = role === "admin";
                return (
                  <div
                    key={role}
                    className="bg-[#F5F5F7] rounded-[18px] p-5 flex flex-col gap-4 "
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[14px] font-medium text-[#1D1D1F]">
                        {roleLabels[role]}
                      </span>
                      {!isAdmin && (
                        <button
                          onClick={() => handleUpdateQuota(role)}
                          disabled={!!isSavingQuota}
                          className="text-[#0071E3] hover:text-[#0077ED] disabled:opacity-50"
                        >
                          {isSavingQuota === role ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Save className="w-4 h-4" />
                          )}
                        </button>
                      )}
                    </div>
                    <div className="space-y-3">
                      <div>
                        <label className="text-[12px] text-[#6E6E73] mb-1 block">
                          Yêu cầu / ngày
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
                          className="apple-input w-full bg-white text-[13px]"
                        />
                      </div>
                      <div>
                        <label className="text-[12px] text-[#6E6E73] mb-1 block">
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
                          className="apple-input w-full bg-white text-[13px]"
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
  );
}
