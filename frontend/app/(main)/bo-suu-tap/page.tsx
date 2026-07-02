"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getCollectorStatsAPI,
  triggerCollectionAPI,
  getCollectorLogsAPI,
  stopCollectionAPI,
} from "@/features/provision/services/data_collection.service";
import {
  Loader2,
  RefreshCcw,
  StopCircle,
  Terminal,
  PlayCircle,
  Database,
  Settings2,
  ShieldAlert,
} from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { useRouter } from "next/navigation";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
import PageLoader from "@/shared/components/common/PageLoader";

export default function CollectorPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const router = useRouter();
  const { showToast } = useToast();

  const [collectorStats, setCollectorStats] = useState<any>(null);
  const [collectionForm, setCollectionForm] = useState({
    source: "",
    pages: 0,
  });
  const [logs, setLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [confirmModal, setConfirmModal] = useState<boolean>(false);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const statsRes = await getCollectorStatsAPI();
      setCollectorStats(statsRes.data || statsRes);
      const logsRes = await getCollectorLogsAPI();
      setLogs(logsRes.data || []);
    } catch (err: any) {
      showToast("Lỗi tải dữ liệu thu thập", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (!authLoading && user && user.role === "admin") {
      interval = setInterval(() => {
        getCollectorLogsAPI()
          .then((res) => setLogs(res.data || []))
          .catch(() => {});
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [user, authLoading]);

  useEffect(() => {
    if (!authLoading && user) {
      if (user.role !== "admin") router.push("/");
      else fetchData();
    }
  }, [user, authLoading, fetchData, router]);

  const handleTriggerCollection = async () => {
    setIsProcessing(true);
    try {
      setIsRefreshing(true);
      await triggerCollectionAPI(collectionForm.source, collectionForm.pages);
      showToast("Đã kích hoạt thu thập", "success");
      setCollectionForm((p) => ({ ...p, pages: 1 }));
      fetchData();
      setConfirmModal(false);
    } catch (err: any) {
      showToast("Lỗi kích hoạt thu thập", "error");
    } finally {
      setIsRefreshing(false);
      setIsProcessing(false);
    }
  };

  const handleStopCollection = async () => {
    setIsProcessing(true);
    try {
      setIsRefreshing(true);
      await stopCollectionAPI();
      showToast("Đã dừng tiến trình", "success");
      fetchData();
    } catch (err: any) {
      showToast("Lỗi dừng tiến trình", "error");
    } finally {
      setIsRefreshing(false);
      setIsProcessing(false);
    }
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
    <div className="w-full max-w-[1200px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] font-sans text-[#1D1D1F] flex flex-col gap-6">
      <div className="flex flex-col md:flex-row gap-6 flex-1 min-h-0">
        <aside className="w-full md:w-[320px] shrink-0 xl:col-span-3 flex flex-col gap-6 overflow-y-auto no-scrollbar pb-6 pr-2">
          <div className="bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] p-6 space-y-4">
            <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
              Giao diện
            </p>
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="w-full py-2 rounded-[10px] bg-white  text-[#1D1D1F] font-medium text-[14px] hover:bg-[#F5F5F7] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isRefreshing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : null}{" "}
              Đồng bộ
            </button>
          </div>
          <section className="bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] p-6 space-y-6">
            <p className="text-[13px] font-medium text-[#6E6E73] mb-4 flex items-center gap-2  ">
              Trạng thái hệ thống
            </p>
            <div className="space-y-4">
              <div className="bg-[#F5F5F7] rounded-[18px] p-5">
                <p className="text-[13px] text-[#6E6E73] mb-2 font-medium">
                  Tài liệu đã thu thập
                </p>
                <p className="text-[32px] font-semibold text-[#1D1D1F]">
                  {collectorStats?.total_documents_collected || 0}
                </p>
              </div>
              <div className="bg-[#F5F5F7] rounded-[18px] p-5">
                <p className="text-[13px] text-[#6E6E73] mb-2 font-medium">
                  Worker Status
                </p>
                <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-full w-fit ">
                  <div
                    className={`w-2.5 h-2.5 rounded-full ${collectorStats?.status === "operational" ? "bg-[#34C759]" : "bg-[#FF3B30]"}`}
                  />
                  <span className="text-[13px] font-medium">
                    {collectorStats?.status === "operational"
                      ? "Đang hoạt động"
                      : "Tạm dừng / Lỗi"}
                  </span>
                </div>
              </div>
              <button
                onClick={handleStopCollection}
                disabled={isProcessing}
                className="w-full py-3 bg-[#FF3B30]/10 text-[#FF3B30] hover:bg-[#FF3B30]/20 font-medium rounded-[16px] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isProcessing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : null}{" "}
                Dừng tiến trình
              </button>
            </div>
          </section>

          <section className="bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] p-6 space-y-6">
            <p className="text-[13px] font-medium text-[#6E6E73] mb-4 flex items-center gap-2  ">
              Khởi tạo nhiệm vụ
            </p>
            <div className="space-y-4">
              <div>
                <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
                  Nguồn dữ liệu
                </label>
                <select
                  value={collectionForm.source}
                  onChange={(e) =>
                    setCollectionForm({
                      ...collectionForm,
                      source: e.target.value,
                    })
                  }
                  className="apple-input w-full bg-[#F5F5F7]"
                >
                  <option value="" disabled>
                    -- Chọn nguồn --
                  </option>
                  <option value="AnnaArchive">Anna's Archive</option>
                  <option value="NXBST">NXB Sự thật</option>
                  <option value="NXBGD">NXB Giáo dục</option>
                  <option value="CTAN">CTAN (TeX)</option>
                </select>
              </div>
              {collectionForm.source && (
                <div>
                  <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
                    Số trang thu thập
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={collectionForm.pages}
                    onChange={(e) => {
                      const v = parseInt(e.target.value);
                      setCollectionForm({
                        ...collectionForm,
                        pages: isNaN(v) ? 0 : v,
                      });
                    }}
                    className="apple-input w-full bg-[#F5F5F7]"
                  />
                </div>
              )}
              {collectionForm.source && (
                <button
                  onClick={() => setConfirmModal(true)}
                  disabled={isRefreshing || isProcessing}
                  className="w-full pill-button mt-2 disabled:opacity-50"
                >
                  Bắt đầu thu thập
                </button>
              )}
            </div>
          </section>
        </aside>

        <main className="flex-1 min-w-0 xl:col-span-9 flex flex-col min-h-0 bg-[#1D1D1F] rounded-[18px] overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-[#333336] bg-[#2A2A2D]">
            <div className="flex items-center gap-4">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-[#FF3B30]"></div>
                <div className="w-3 h-3 rounded-full bg-[#FF9500]"></div>
                <div className="w-3 h-3 rounded-full bg-[#34C759]"></div>
              </div>
              <div className="flex items-center gap-2 bg-[#1D1D1F] px-3 py-1 rounded-[8px] text-[#A1A1A6] text-[12px] font-mono">
                <Terminal className="w-3.5 h-3.5" /> Live Console
              </div>
            </div>
            <div className="text-[12px] font-mono text-[#A1A1A6] flex items-center gap-2">
              <div className="w-2 h-2 bg-[#34C759] rounded-full animate-pulse" />{" "}
              sys.log
            </div>
          </div>
          <div className="flex-1 overflow-y-auto no-scrollbar p-6 font-mono text-[13px] leading-relaxed text-[#D1D1D6] bg-[#1D1D1F]">
            {logs.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center opacity-50">
                <Terminal className="w-10 h-10 mb-3" />
                <p>Waiting for collector events...</p>
              </div>
            ) : (
              <div className="space-y-2">
                {logs.map((log, i) => {
                  const p = log.split(" | ");
                  const t =
                    p.length >= 3
                      ? (p[0].split(" ")[1] || p[0]).substring(0, 8)
                      : "";
                  const l = p.length >= 3 ? p[1].trim() : "LOG";
                  const m =
                    p.length >= 3 ? p.slice(2).join(" | ").trim() : log.trim();
                  let lc = "text-[#A1A1A6]",
                    bgc = "bg-[#333336] text-[#A1A1A6]";
                  if (l === "INFO") {
                    lc = "text-[#32ADE6]";
                    bgc = "bg-[#32ADE6]/10 text-[#32ADE6]";
                  } else if (l === "WARNING") {
                    lc = "text-[#FF9500]";
                    bgc = "bg-[#FF9500]/10 text-[#FF9500]";
                  } else if (l === "ERROR") {
                    lc = "text-[#FF3B30]";
                    bgc = "bg-[#FF3B30]/10 text-[#FF3B30]";
                  } else if (l === "SUCCESS") {
                    lc = "text-[#34C759]";
                    bgc = "bg-[#34C759]/10 text-[#34C759]";
                  }
                  return (
                    <div
                      key={i}
                      className="flex gap-4 items-start hover:bg-[#2A2A2D] p-1 rounded-md transition-colors"
                    >
                      <div className="flex gap-2 items-center w-28 shrink-0">
                        <span className="text-[#6E6E73]">{t}</span>
                        {p.length >= 3 && (
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded ${bgc}`}
                          >
                            {l}
                          </span>
                        )}
                      </div>
                      <span className={`break-words ${lc}`}>{m}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </main>
      </div>

      <Modal
        isOpen={confirmModal}
        onClose={() => !isProcessing && setConfirmModal(false)}
        className="max-w-md bg-[#F5F5F7] rounded-[18px] p-0 -2xl border-none"
      >
        <ModalHeader className="p-6 pb-2">
          <ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">
            Xác nhận thu thập
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="p-6 pt-2">
          <div className="bg-[#F5F5F7] p-4 rounded-[16px] border-[#E8E8ED] mb-4">
            <span className="text-[13px] text-[#6E6E73]">Nguồn thu thập: </span>
            <strong className="text-[#1D1D1F]">{collectionForm.source}</strong>
          </div>
          <p className="text-[14px] text-[#6E6E73] leading-relaxed">
            Hệ thống sẽ bắt đầu thu thập dữ liệu tự động. Quá trình này có thể
            tốn một khoảng thời gian.
          </p>
        </ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3">
          <button
            onClick={() => !isProcessing && setConfirmModal(false)}
            disabled={isProcessing}
            className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full"
          >
            Hủy
          </button>
          <button
            onClick={handleTriggerCollection}
            disabled={isProcessing}
            className="pill-button disabled:opacity-50 flex items-center gap-2"
          >
            {isProcessing && <Loader2 className="w-4 h-4 animate-spin" />} Xác
            nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
