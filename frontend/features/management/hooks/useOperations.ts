"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  getAdminConfigAPI,
  getMaintenanceModeAPI,
  getMinioStatsAPI,
  getOperationMetricsAPI,
  getSystemHealthAPI,
  toggleMaintenanceModeAPI,
  triggerBackupAPI,
  updateAdminConfigAPI,
} from "@/features/management/services/health.service";
import {
  getGlobalQuotaConfigAPI,
  updateRoleQuotaAPI,
} from "@/features/usage/services/quota.service";
import {
  getMcpServersAPI,
  probeMcpServerAPI,
  registerMcpServerAPI,
} from "@/features/agentic_ai/services/mcp.service";

export function useOperations() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const allowed = String(user?.role || "").toLowerCase() === "admin";
  const [health, setHealth] = useState<any>({});
  const [metrics, setMetrics] = useState<any>({});
  const [storage, setStorage] = useState<any>({});
  const [config, setConfig] = useState<any>({ registration_enabled: true });
  const [maintenance, setMaintenance] = useState(false);
  const [quotas, setQuotas] = useState<Record<string, any>>({});
  const [mcpServers, setMcpServers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    if (!allowed) {
      setLoading(false);
      return;
    }
    setLoading(true);
    const results = await Promise.allSettled([
      getSystemHealthAPI(),
      getOperationMetricsAPI(),
      getMinioStatsAPI(),
      getAdminConfigAPI(),
      getMaintenanceModeAPI(),
      getGlobalQuotaConfigAPI(),
      getMcpServersAPI(),
    ]);
    const value = (index: number) =>
      results[index].status === "fulfilled"
        ? (results[index] as PromiseFulfilledResult<any>).value?.data ||
          (results[index] as PromiseFulfilledResult<any>).value ||
          {}
        : {};
    setHealth(value(0));
    setMetrics(value(1));
    setStorage(value(2));
    setConfig(value(3));
    setMaintenance(Boolean(value(4).enabled));
    setQuotas(value(5));
    setMcpServers(Array.isArray(value(6)) ? value(6) : []);
    setError(
      results.some((result) => result.status === "rejected")
        ? "Một phần dữ liệu vận hành chưa tải được"
        : "",
    );
    setLoading(false);
  }, [allowed]);

  useEffect(() => {
    load();
  }, [load]);

  async function mutate(
    name: string,
    action: () => Promise<any>,
    success: string,
  ) {
    if (processing) return false;
    setProcessing(name);
    setError("");
    setNotice("");
    try {
      await action();
      setNotice(success);
      return true;
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể cập nhật vận hành",
      );
      return false;
    } finally {
      setProcessing("");
    }
  }

  const toggleMaintenance = async () => {
    const next = !maintenance;
    if (
      await mutate(
        "maintenance",
        () => toggleMaintenanceModeAPI(next),
        next ? "Đã bật chế độ bảo trì" : "Đã tắt chế độ bảo trì",
      )
    )
      setMaintenance(next);
  };
  const backup = () =>
    mutate("backup", triggerBackupAPI, "Đã khởi chạy sao lưu");
  const toggleRegistration = async () => {
    const next = !config.registration_enabled;
    if (
      await mutate(
        "registration",
        () => updateAdminConfigAPI({ registration_enabled: next }),
        next ? "Đã mở đăng ký" : "Đã đóng đăng ký",
      )
    )
      setConfig((value: any) => ({ ...value, registration_enabled: next }));
  };
  const updateQuota = async (role: string, values: any) => {
    const success = await mutate(
      `quota-${role}`,
      () => updateRoleQuotaAPI(role, values),
      `Đã lưu hạn mức ${role}`,
    );
    if (success) setQuotas((current) => ({ ...current, [role]: values }));
    return success;
  };
  const registerMcp = async (values: {
    name: string;
    description: string;
    server_type: "sse" | "streamable_http" | "stdio";
    url?: string;
    command?: string;
    args?: string[];
    auth_token?: string;
  }) => {
    const success = await mutate(
      "mcp-register",
      () => registerMcpServerAPI(values),
      "Đã kết nối MCP",
    );
    if (success) await load();
    return success;
  };
  const probeMcp = async (id: string) => {
    const success = await mutate(
      `mcp-${id}`,
      () => probeMcpServerAPI(id),
      "Đã kiểm tra MCP",
    );
    await load();
    return success;
  };

  return {
    health,
    metrics,
    storage,
    config,
    maintenance,
    quotas,
    mcpServers,
    allowed,
    loading: authLoading || loading,
    processing,
    error,
    notice,
    reload: load,
    toggleMaintenance,
    backup,
    toggleRegistration,
    updateQuota,
    registerMcp,
    probeMcp,
  };
}
