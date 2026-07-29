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
import PageHeader from "@/shared/components/common/PageHeader";

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
      showToast("Lỗi trích xuất số liệu vận hành", "error");
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
        !maintenanceMode ? "Kích hoạt chế độ bảo trì hoàn tất" : "Vô hiệu hóa chế độ bảo trì hoàn tất",
        "success",
      );
    } catch (err: any) {
      showToast("Lỗi cấu hình chế độ bảo trì", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const triggerBackup = async () => {
    if (isProcessing) return;
    setIsProcessing(true);
    try {
      await triggerBackupAPI();
      showToast("Khởi tạo yêu cầu sao lưu hệ thống hoàn tất", "success");
    } catch (err: any) {
      showToast("Lỗi khởi tạo tiến trình sao lưu hệ thống", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUpdateQuota = async (role: string) => {
    setIsSavingQuota(role);
    try {
      await updateRoleQuotaAPI(role, quotaConfigs[role]);
      showToast(`Cập nhật hạn mức phân quyền ${role} hoàn tất`, "success");
    } catch (err: any) {
      showToast("Lỗi cập nhật hạn mức phân quyền", "error");
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
        <div className="w-24 h-24 bg-[var(--surface-quiet)] flex items-center justify-center rounded-[var(--radius-panel)]">
          <ShieldAlert className="w-10 h-10 text-[var(--danger)]" />
        </div>
        <div className="space-y-2 max-w-[300px]">
          <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
            Truy cập bị hạn chế
          </p>
          <p className="text-[15px] text-[var(--ink-muted)]">
            Bạn không có quyền quản trị để truy cập trang này.
          </p>
        </div>
      </div>
    );

  return (
    <div className="app-page gap-8">
      <PageHeader title="Vận hành" />
      <div className="flex flex-col md:flex-row md:items-center justify-end gap-4">
        <button
          onClick={fetchData}
          disabled={isRefreshing}
          className="pill-button flex items-center gap-2 bg-[var(--surface-quiet)] text-[var(--ink)] hover:bg-[var(--border)]"
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
        <section className="lg:col-span-2 bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] border-[var(--border)] p-6 flex flex-col gap-6">
          <h2 className="text-[20px] font-semibold text-[var(--ink)] flex items-center gap-2">
            <Server className="w-5 h-5 text-[var(--ink-muted)]" /> Sức khỏe hệ thống
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-[14px] font-medium text-[var(--ink)]">
                  Core API
                </span>
                <div
                  className={`w-2.5 h-2.5 rounded-full ${health?.status === "healthy" ? "bg-[var(--success)]" : "bg-[var(--danger)]"}`}
                />
              </div>
              <p className="text-[13px] text-[var(--ink-muted)]">
                {health?.status === "healthy"
                  ? "Hoạt động ổn định"
                  : "Gặp sự cố"}
              </p>
            </div>
            <div className="bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-[14px] font-medium text-[var(--ink)]">
                  Database
                </span>
                <div
                  className={`w-2.5 h-2.5 rounded-full ${health?.services?.database === "connected" ? "bg-[var(--success)]" : "bg-[var(--danger)]"}`}
                />
              </div>
              <p className="text-[13px] text-[var(--ink-muted)]">MongoDB v7.0</p>
            </div>
            <div className="bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-[14px] font-medium text-[var(--ink)]">
                  Cache
                </span>
                <div
                  className={`w-2.5 h-2.5 rounded-full ${health?.services?.cache === "connected" ? "bg-[var(--success)]" : "bg-[var(--danger)]"}`}
                />
              </div>
              <p className="text-[13px] text-[var(--ink-muted)]">Redis Cloud</p>
            </div>
            <div className="bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-[14px] font-medium text-[var(--ink)]">
                  AI Agent
                </span>
                <div
                  className={`w-2.5 h-2.5 rounded-full ${health?.services?.ai_agent === "healthy" ? "bg-[var(--success)]" : "bg-[var(--danger)]"}`}
                />
              </div>
              <p className="text-[13px] text-[var(--ink-muted)]">RAG Service</p>
            </div>
          </div>
        </section>

        <section className="bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] border-[var(--border)] p-6 flex flex-col gap-6">
          <h2 className="text-[20px] font-semibold text-[var(--ink)] flex items-center gap-2">
            <Shield className="w-5 h-5 text-[var(--ink-muted)]" /> Điều hành
          </h2>
          <div className="flex flex-col gap-4">
            <div className="bg-[#FFF4E5] rounded-[var(--radius-panel)] p-5 border border-[var(--warning)]/20 flex flex-col gap-4">
              <div>
                <h3 className="text-[17px] font-medium text-[var(--warning)]">
                  Bảo trì hệ thống
                </h3>
                <p className="text-[13px] text-[var(--warning)]/80 mt-1">
                  Ngắt kết nối người dùng. Gây gián đoạn.
                </p>
              </div>
              <button
                onClick={toggleMaintenance}
                disabled={isProcessing}
                className={`w-full py-2.5 rounded-full text-[13px] font-medium transition-colors ${maintenanceMode ? "bg-[var(--danger)] text-white" : "bg-white text-[var(--warning)] hover:bg-[var(--warning)]/10"}`}
              >
                {maintenanceMode ? "Tắt bảo trì" : "Bật bảo trì"}
              </button>
            </div>
            <div className="bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] p-5 flex flex-col gap-4">
              <div>
                <h2 className="text-[20px] font-semibold text-[var(--ink)] mb-4">
                  Sao lưu dữ liệu
                </h2>
                <p className="text-[13px] text-[var(--ink-muted)] mt-1">
                  Snapshot toàn bộ DB về kho lạnh.
                </p>
              </div>
              <button
                onClick={triggerBackup}
                disabled={isProcessing}
                className="w-full py-2.5 bg-white text-[var(--brand)] font-medium rounded-full text-[13px] font-medium hover:bg-[var(--border)] "
              >
                Tiến hành sao lưu
              </button>
            </div>
          </div>
        </section>
      </div>

      <section className="bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] border-[var(--border)] p-6 flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <h2 className="text-[20px] font-semibold text-[var(--ink)] flex items-center gap-2">
            <HardDrive className="w-5 h-5 text-[var(--ink-muted)]" /> Kho lưu trữ (MinIO)
          </h2>
          <div className="flex items-center gap-2 bg-[var(--surface-quiet)] px-3 py-1.5 rounded-full">
            <div
              className={`w-2 h-2 rounded-full ${minioStats?.status === "healthy" ? "bg-[var(--success)]" : "bg-[var(--danger)]"}`}
            />
            <span className="text-[12px] font-medium text-[var(--ink-muted)]">
              {minioStats?.status === "healthy" ? "Đã kết nối" : "Mất kết nối"}
            </span>
          </div>
        </div>

        {minioLoading ? (
          <div className="py-10 flex justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-[var(--ink-muted)]" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-[var(--surface-quiet)] md:bg-transparent rounded-[var(--radius-panel)] md:rounded-none p-6 md:p-0 md:pt-6 text-center">
              <p className="text-[13px] text-[var(--ink-muted)] font-medium mb-1">
                Tổng dung lượng
              </p>
              <p className="text-[28px] font-semibold text-[var(--ink)]">
                {formatBytes(minioStats?.total_size_bytes || 0)}
              </p>
            </div>
            <div className="bg-[var(--surface-quiet)] md:bg-transparent rounded-[var(--radius-panel)] md:rounded-none p-6 md:p-0 md:pt-6 text-center">
              <p className="text-[13px] text-[var(--ink-muted)] font-medium mb-1">
                Tổng số tệp
              </p>
              <p className="text-[28px] font-semibold text-[var(--ink)]">
                {minioStats?.total_objects_count || 0}
              </p>
            </div>
            <div className="bg-[var(--surface-quiet)] md:bg-transparent rounded-[var(--radius-panel)] md:rounded-none p-6 md:p-0 md:pt-6 text-center">
              <p className="text-[13px] text-[var(--ink-muted)] font-medium mb-1">
                Số lượng Buckets
              </p>
              <p className="text-[28px] font-semibold text-[var(--ink)]">
                {minioStats?.total_buckets || 0}
              </p>
            </div>
          </div>
        )}
      </section>

      <section className="bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] border-[var(--border)] p-6 flex flex-col gap-6">
        <h2 className="text-[20px] font-semibold text-[var(--ink)] flex items-center gap-2">
          <Zap className="w-5 h-5 text-[var(--ink-muted)]" /> Hạn mức AI
        </h2>
        {quotaLoading ? (
          <div className="py-10 flex justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-[var(--ink-muted)]" />
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
                    className="bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] p-5 flex flex-col gap-4 "
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[14px] font-medium text-[var(--ink)]">
                        {roleLabels[role]}
                      </span>
                      {!isAdmin && (
                        <button
                          onClick={() => handleUpdateQuota(role)}
                          disabled={!!isSavingQuota}
                          className="text-[var(--brand)] hover:text-[var(--brand-hover)] disabled:opacity-50"
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
                        <label className="text-[12px] text-[var(--ink-muted)] mb-1 block">
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
                        <label className="text-[12px] text-[var(--ink-muted)] mb-1 block">
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
