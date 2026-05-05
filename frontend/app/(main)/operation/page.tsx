"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getSystemHealthAPI,
  getMaintenanceModeAPI,
  toggleMaintenanceModeAPI,
  getCollectorStatsAPI,
  triggerBackupAPI,
  getAuthorApplicationsAPI,
  reviewAuthorApplicationAPI,
} from "@/services/operation.service";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";

export default function OperationDashboard() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();

  const [health, setHealth] = useState<any>(null);
  const [collectorStats, setCollectorStats] = useState<any>(null);
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [applications, setApplications] = useState<any[]>([]);
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [hData, cData, mData, aData] = await Promise.all([
        getSystemHealthAPI(),
        getCollectorStatsAPI(),
        getMaintenanceModeAPI(),
        getAuthorApplicationsAPI(),
      ]);

      if (hData) setHealth(hData.data || hData);
      if (cData) setCollectorStats(cData.data || cData);
      if (mData) setMaintenanceMode(mData.data?.enabled || mData.enabled || false);
      if (aData) setApplications(aData.data || aData);
    } catch (err: any) {
      showToast("Không thể tải dữ liệu hệ thống.", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
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

  const createApiKey = () => {
    showToast("Đã tạo API Key mới.", "success");
  };

  const reviewApplication = async (appId: string, status: string) => {
    if (isProcessing) return;
    setIsProcessing(true);
    try {
      await reviewAuthorApplicationAPI(
        appId,
        status,
        status === "APPROVED" ? "Đã duyệt" : "Không đủ tiêu chuẩn"
      );
      showToast(status === "APPROVED" ? "Đã duyệt hồ sơ." : "Đã từ chối hồ sơ.", "success");
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Lỗi xử lý hồ sơ.", "error");
    } finally {
      setIsProcessing(false);
    }
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
              className="text-sm font-medium text-zinc-500 hover:text-black transition-colors disabled:opacity-50"
            >
              {isRefreshing ? "Đang đồng bộ" : "Đồng bộ dữ liệu"}
            </button>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-zinc-200 border border-zinc-200 mb-12">
          <div className="bg-white p-6 flex flex-col justify-between h-32">
             <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Sức khỏe hệ thống</span>
                <span className="text-[10px] font-bold text-black border border-black px-2 py-1 uppercase">
                  {health?.status || "HEALTHY"}
                </span>
             </div>
             <div className="flex items-center gap-6 text-sm font-medium text-black">
                <span className="flex items-center gap-2">
                  <span className="text-zinc-400 text-xs uppercase tracking-widest">DB</span>
                  {health?.mongodb || "OK"}
                </span>
                <span className="flex items-center gap-2">
                  <span className="text-zinc-400 text-xs uppercase tracking-widest">Cache</span>
                  {health?.redis || "OK"}
                </span>
             </div>
          </div>
          
          <div className="bg-white p-6 flex flex-col justify-between h-32">
             <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Chỉ số thu thập</span>
             </div>
             <p className="text-3xl font-bold tracking-tight text-black">
               {collectorStats?.total_documents_collected || 0} <span className="text-sm font-medium text-zinc-500">tài liệu</span>
             </p>
          </div>
          
          <div className="bg-white p-6 flex flex-col justify-between h-32">
             <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Chế độ bảo trì</span>
             </div>
             <button
                onClick={toggleMaintenance}
                disabled={isProcessing}
                className={`w-full py-2 text-xs font-bold uppercase tracking-widest transition-colors disabled:opacity-50 border border-transparent ${
                  maintenanceMode ? "bg-black text-white hover:bg-zinc-800" : "bg-zinc-200 text-black hover:bg-zinc-300"
                }`}
             >
                {maintenanceMode ? "Đang bật bảo trì" : "Bật chế độ bảo trì"}
             </button>
          </div>
          
          <div className="bg-white p-6 flex flex-col justify-between h-32">
             <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Sao lưu dữ liệu</span>
             </div>
             <button
                onClick={triggerBackup}
                disabled={isProcessing}
                className="w-full py-2 bg-white text-black text-xs font-bold uppercase tracking-widest border border-black hover:bg-zinc-50 transition-colors disabled:opacity-50"
             >
                Tiến hành sao lưu
             </button>
          </div>
        </div>

        <div className="space-y-12">
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-black">Hồ sơ ứng tuyển Tác giả</h2>
            </div>
            <div className="border border-zinc-200 bg-white overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[800px]">
                <thead>
                  <tr className="border-b border-zinc-200 bg-zinc-50">
                    <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Người ứng tuyển</th>
                    <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Động lực & Lý do</th>
                    <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Ngày gửi</th>
                    <th className="py-3 px-6 text-xs font-semibold text-zinc-600 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {applications.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-24 text-center">
                        <p className="text-sm font-medium text-zinc-500">Không có hồ sơ chờ duyệt</p>
                      </td>
                    </tr>
                  ) : (
                    applications.map((app) => (
                      <tr key={app._id} className="border-b border-zinc-200 last:border-0 hover:bg-zinc-50 transition-colors">
                        <td className="py-4 px-6 align-top">
                          <div className="flex flex-col gap-1">
                            <span className="text-[10px] font-bold text-black uppercase tracking-widest">{app.user_name}</span>
                            <span className="text-xs text-zinc-500 font-mono">{app.user_email}</span>
                          </div>
                        </td>
                        <td className="py-4 px-6 align-top max-w-sm">
                          <p className="text-xs text-zinc-600 line-clamp-2">"{app.motivation}"</p>
                        </td>
                        <td className="py-4 px-6 align-top whitespace-nowrap">
                          <span className="text-xs font-medium text-zinc-500">
                            {new Date(app.created_at).toLocaleDateString("vi-VN")}
                          </span>
                        </td>
                        <td className="py-4 px-6 align-top text-right whitespace-nowrap">
                          <div className="flex justify-end gap-4">
                            <button
                              onClick={() => reviewApplication(app._id, "REJECTED")}
                              disabled={isProcessing}
                              className="text-xs font-semibold text-zinc-500 hover:text-black transition-colors disabled:opacity-50"
                            >
                              Từ chối
                            </button>
                            <button
                              onClick={() => reviewApplication(app._id, "APPROVED")}
                              disabled={isProcessing}
                              className="text-xs font-semibold text-black hover:underline underline-offset-4 disabled:opacity-50"
                            >
                              Duyệt
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-black">Khóa API (API Keys)</h2>
              <button
                onClick={createApiKey}
                className="text-xs font-semibold text-black hover:underline underline-offset-4"
              >
                Tạo khóa mới
              </button>
            </div>
            <div className="border border-zinc-200 bg-white overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[800px]">
                <thead>
                  <tr className="border-b border-zinc-200 bg-zinc-50">
                    <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Khóa truy cập</th>
                    <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Phân quyền</th>
                    <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Trạng thái</th>
                    <th className="py-3 px-6 text-xs font-semibold text-zinc-600 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {apiKeys.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-24 text-center">
                        <p className="text-sm font-medium text-zinc-500">Chưa có khóa API nào được tạo</p>
                      </td>
                    </tr>
                  ) : (
                    apiKeys.map((key: any, idx) => (
                      <tr key={idx} className="border-b border-zinc-200 last:border-0 hover:bg-zinc-50 transition-colors">
                        <td className="py-4 px-6 align-top">
                          <span className="text-sm font-mono text-black">{key.token}</span>
                        </td>
                        <td className="py-4 px-6 align-top">
                          <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">{key.role}</span>
                        </td>
                        <td className="py-4 px-6 align-top whitespace-nowrap">
                          <span className="text-[10px] font-bold text-black border border-black px-2 py-1 uppercase tracking-widest">Hoạt động</span>
                        </td>
                        <td className="py-4 px-6 align-top text-right">
                          <button className="text-xs font-semibold text-zinc-500 hover:text-black transition-colors">
                            Thu hồi
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
