"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getCollectorStatsAPI,
  triggerCollectionAPI,
  getCollectorLogsAPI,
  stopCollectionAPI,
} from "@/features/management/services/collection.service";
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
import { useAuth } from "@/features/authentication/contexts/AuthContext";
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
  const [collectionForm, setCollectionForm] = useState<{
    source: string;
    pages: number | string;
  }>({
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
      setLogs(Array.isArray(logsRes) ? logsRes : (logsRes.data || []));
    } catch (err: any) {
      showToast("Không thể tải cấu hình thu thập", "error");
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
          .then((res) => setLogs(Array.isArray(res) ? res : (res.data || [])))
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
      await triggerCollectionAPI(collectionForm.source, collectionForm.pages as any);
      showToast("Khởi tạo tiến trình thu thập hoàn tất", "success");
      setCollectionForm((p) => ({ ...p, pages: 1 }));
      fetchData();
      setConfirmModal(false);
    } catch (err: any) {
      showToast("Không thể tạo tiến trình thu thập", "error");
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
      showToast("Hủy bỏ tiến trình thu thập hoàn tất", "success");
      fetchData();
    } catch (err: any) {
      showToast("Lỗi hủy bỏ tiến trình thu thập", "error");
    } finally {
      setIsRefreshing(false);
      setIsProcessing(false);
    }
  };

  if (authLoading || isLoading) return <PageLoader />;
  if (user?.role !== "admin")
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-56px)] gap-6 font-sans text-center">
        <div className="w-24 h-24 bg-surface-quiet flex items-center justify-center rounded-panel">
          <ShieldAlert className="w-10 h-10 text-danger" />
        </div>
        <div className="space-y-2 max-w-[300px]">
          <p className="text-[13px] font-medium text-ink-muted mb-4">
            Truy cập bị hạn chế
          </p>
          <p className="text-[15px] text-ink-muted">
            Bạn không có quyền quản trị để truy cập trang này.
          </p>
        </div>
      </div>
    );

  return (
    <div className="w-full h-full font-sans text-ink flex flex-col gap-6">
      <div className="flex flex-col md:flex-row gap-6 flex-1 min-h-0">
        <aside className="w-full md:w-[320px] shrink-0 xl:col-span-3 flex flex-col bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none overflow-hidden">
          <div className="overflow-y-auto no-scrollbar p-6 md:px-0 md:pt-6 flex flex-col flex-1 gap-8">
            <div>
              <p className="text-[13px] text-ink-muted font-medium mb-4">Tài liệu đã thu thập</p>
              <p className="text-[32px] font-semibold text-ink">
                {collectorStats?.total_documents_collected || 0}
              </p>
            </div>

            <div>
              <p className="text-[13px] text-ink-muted font-medium mb-4">
                Trạng thái hoạt động
              </p>
              <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-full w-fit">
                <div
                  className={`w-2.5 h-2.5 rounded-full ${collectorStats?.status === "operational" ? "bg-brand" : collectorStats?.status === "paused" ? "bg-warning" : "bg-danger"}`}
                />
                <span className="text-[13px] font-medium">
                  {collectorStats?.status === "operational"
                    ? "Hoạt động"
                    : collectorStats?.status === "paused"
                    ? "Tạm dừng"
                    : "Lỗi"}
                </span>
              </div>
              <button
                onClick={handleStopCollection}
                disabled={isProcessing}
                className="w-full py-3 bg-danger/10 text-danger hover:bg-danger/20 font-medium rounded-panel transition-colors flex items-center justify-center gap-2 disabled:opacity-50 mt-4"
              >
                {isProcessing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : null}{" "}
                Dừng tiến trình
              </button>
            </div>

            <div>
              <p className="text-[13px] font-medium text-ink-muted mb-4">
                Khởi tạo nhiệm vụ
              </p>
              <div className="space-y-4">
                <div>
                  <label className="text-[13px] font-medium text-ink-muted mb-2 block">
                    Nguồn dữ liệu
                  </label>
                  <select
                    value={collectionForm.source}
                    onChange={(e) =>
                      setCollectionForm({
                        ...collectionForm,
                        source: e.target.value,
                        pages: e.target.value === "CTAN" ? "a" : 1,
                      })
                    }
                    className="apple-input w-full bg-white"
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
                {collectionForm.source === "CTAN" ? (
                  <div>
                    <label className="text-[13px] font-medium text-ink-muted mb-2 block">
                      Vần
                    </label>
                    <select
                      value={collectionForm.pages || ""}
                      onChange={(e) =>
                        setCollectionForm({
                          ...collectionForm,
                          pages: e.target.value as any,
                        })
                      }
                      className="apple-input w-full bg-white"
                    >
                      <option value="" disabled>-- Chọn vần --</option>
                      {Array.from({ length: 26 }, (_, i) => String.fromCharCode(97 + i)).map(char => (
                        <option key={char} value={char}>{char.toUpperCase()}</option>
                      ))}
                    </select>
                  </div>
                ) : collectionForm.source ? (
                  <div>
                    <label className="text-[13px] font-medium text-ink-muted mb-2 block">
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
                      className="apple-input w-full bg-white"
                    />
                  </div>
                ) : null}
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
            </div>
          </div>
        </aside>

        <main className="flex-1 min-w-0 xl:col-span-9 flex flex-col min-h-0 gap-4">
          <div className="flex justify-end">
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="p-2 bg-surface-quiet text-ink hover:bg-border rounded-full transition-colors disabled:opacity-50 flex-shrink-0 w-8 h-8 flex items-center justify-center"
              title="Đồng bộ"
            >
              <RefreshCcw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
            </button>
          </div>
          <div className="flex-1 bg-ink rounded-panel overflow-hidden flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-ink bg-ink">
              <div className="flex items-center gap-4">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-danger"></div>
                  <div className="w-3 h-3 rounded-full bg-warning"></div>
                  <div className="w-3 h-3 rounded-full bg-brand"></div>
                </div>
                <div className="flex items-center gap-2 bg-ink px-3 py-1 rounded-control text-ink-faint text-[12px] font-mono">
                  <Terminal className="w-3.5 h-3.5" /> Live Console
                </div>
              </div>
              <div className="text-[12px] font-mono text-ink-faint flex items-center gap-2">
                <div className="w-2 h-2 bg-brand rounded-full animate-pulse" />{" "}
                sys.log
              </div>
            </div>
            <div className="flex-1 overflow-y-auto no-scrollbar p-6 font-mono text-[13px] leading-relaxed text-border bg-ink">
            {logs.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center opacity-50">
                <Terminal className="w-10 h-10 mb-3" />
          <p>Đang chờ sự kiện thu thập</p>
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
                  let lc = "text-ink-faint",
                    bgc = "bg-ink text-ink-faint";
                  if (l === "INFO") {
                    lc = "text-brand";
                    bgc = "bg-brand/10 text-brand";
                  } else if (l === "WARNING") {
                    lc = "text-warning";
                    bgc = "bg-warning/10 text-warning";
                  } else if (l === "ERROR") {
                    lc = "text-danger";
                    bgc = "bg-danger/10 text-danger";
                  } else if (l === "SUCCESS") {
                    lc = "text-brand";
                    bgc = "bg-brand/10 text-brand";
                  }
                  return (
                    <div
                      key={i}
                      className="flex gap-4 items-start hover:bg-ink p-1 rounded-md transition-colors"
                    >
                      <div className="flex gap-2 items-center w-28 shrink-0">
                        <span className="text-ink-muted">{t}</span>
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
          </div>
        </main>
      </div>

      <Modal
        isOpen={confirmModal}
        onClose={() => !isProcessing && setConfirmModal(false)}
      >
        <ModalHeader>
          <ModalTitle>
            Xác nhận thu thập
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="bg-surface-quiet p-4 rounded-panel border border-border mb-4">
            <span className="text-[13px] text-ink-muted">Nguồn thu thập: </span>
            <strong className="text-ink">{collectionForm.source}</strong>
          </div>
          <p className="text-[14px] text-ink-muted leading-relaxed">
            Hệ thống sẽ bắt đầu thu thập dữ liệu tự động. Quá trình này có thể
            tốn một khoảng thời gian.
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => !isProcessing && setConfirmModal(false)}
            disabled={isProcessing}
            className="px-5 py-2 text-brand font-medium hover:bg-surface-quiet rounded-full"
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
