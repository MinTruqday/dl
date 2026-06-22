"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getCollectorStatsAPI,
  triggerCollectionAPI,
  getCollectorLogsAPI,
  stopCollectionAPI,
} from "@/features/provision/services/data_collection.service";
import { Loader2, RefreshCcw, StopCircle, Terminal, PlayCircle, Database, Settings2, ShieldAlert } from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { useRouter } from "next/navigation";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
  ModalDescription,
} from "@/shared/components/ui/Modal";

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
  const [visible, setVisible] = useState(false);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const statsRes = await getCollectorStatsAPI();
      setCollectorStats(statsRes.data || statsRes);
      const logsRes = await getCollectorLogsAPI();
      setLogs(logsRes.data || []);
    } catch (err: any) {
      showToast("Không thể tải trạng thái thu thập.", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
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
      if (user.role !== "admin") {
        router.push("/");
      } else {
        fetchData();
      }
    }
  }, [user, authLoading, fetchData, router]);

  const handleTriggerCollection = async () => {
    setIsProcessing(true);
    try {
      setIsRefreshing(true);
      await triggerCollectionAPI(collectionForm.source, collectionForm.pages);
      showToast("Đã kích hoạt tiến trình thu thập thành công.", "success");
      setCollectionForm({ ...collectionForm, pages: 1 });
      fetchData();
      setConfirmModal(false);
    } catch (err: any) {
      showToast(
        err.message || "Không thể kích hoạt tiến trình thu thập.",
        "error",
      );
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
      showToast("Đã dừng tất cả các tiến trình cào dữ liệu.", "success");
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Không thể dừng tiến trình thu thập.", "error");
    } finally {
      setIsRefreshing(false);
      setIsProcessing(false);
    }
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
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col font-sans text-zinc-900 bg-zinc-50 selection:bg-black selection:text-white">
      <div className="mb-6 md:mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4 shrink-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
            Thu thập dữ liệu
          </h1>
          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 flex items-center gap-2">
            Hệ thống Crawl & Ingest <Database className="w-3.5 h-3.5 text-zinc-400" />
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
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0 overflow-y-auto pb-6 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <aside className="lg:col-span-4 xl:col-span-3 flex flex-col gap-6">
          <section className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-6 space-y-6">
            <div className="border-b border-zinc-100 pb-3 flex items-center gap-2">
              <Settings2 className="w-4 h-4 text-black" />
              <div className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                Trạng thái hệ thống
              </div>
            </div>
            
            <div className="flex flex-col gap-4">
              <div className="border border-zinc-100 bg-zinc-50/50 rounded-3xl p-6 flex flex-col justify-between shadow-sm transition-all duration-300 hover:bg-white hover:border-zinc-200 group">
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-4 group-hover:text-zinc-500 transition-colors">
                  Tài liệu đã thu thập
                </p>
                <div className="flex items-end gap-2">
                  <p className="text-4xl font-bold tracking-tight text-zinc-900">
                    {collectorStats?.total_documents_collected || 0}
                  </p>
                </div>
              </div>
              
              <div className="border border-zinc-100 bg-zinc-50/50 rounded-3xl p-6 flex flex-col justify-between shadow-sm transition-all duration-300 hover:bg-white hover:border-zinc-200">
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-4">
                  Worker Status
                </p>
                <div className="flex items-center gap-3 bg-white border border-zinc-100 p-3 rounded-2xl shadow-sm w-fit">
                  <div
                    className={`w-2 h-2 rounded-full shadow-sm ${collectorStats?.status === "operational" ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"}`}
                  />
                  <p className="text-[10px] font-bold text-zinc-900 uppercase tracking-widest">
                    {collectorStats?.status === "operational"
                      ? "Đang hoạt động"
                      : "Tạm dừng / Lỗi"}
                  </p>
                </div>
              </div>

              <button
                onClick={handleStopCollection}
                disabled={isProcessing}
                className="w-full h-12 bg-red-50 text-red-600 text-[10px] font-bold uppercase tracking-widest disabled:opacity-50 border border-red-100 rounded-2xl hover:bg-red-100 hover:border-red-200 transition-all duration-200 flex items-center justify-center gap-2 shadow-sm hover:scale-[1.02]"
              >
                {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <StopCircle className="w-4 h-4" />}
                Dừng tất cả tiến trình
              </button>
            </div>
          </section>

          <section className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-6 space-y-5">
            <div className="border-b border-zinc-100 pb-3 flex items-center gap-2">
              <PlayCircle className="w-4 h-4 text-black" />
              <div className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                Khởi tạo nhiệm vụ
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 ml-1 block">
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
                  className="w-full h-11 border border-zinc-200 px-4 text-sm font-bold text-zinc-900 focus:outline-none focus:border-black rounded-2xl bg-white shadow-sm appearance-none transition-all duration-200 hover:border-zinc-300"
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
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 ml-1 block">
                    Số trang thu thập
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={collectionForm.pages}
                    onChange={(e) => {
                      const val = parseInt(e.target.value);
                      setCollectionForm({
                        ...collectionForm,
                        pages: isNaN(val) ? 0 : val,
                      });
                    }}
                    className="w-full h-11 border border-zinc-200 px-4 text-sm font-bold text-zinc-900 focus:outline-none focus:border-black rounded-2xl bg-white shadow-sm transition-all duration-200 hover:border-zinc-300"
                  />
                </div>
              )}
            </div>

            {collectionForm.source && (
              <button
                onClick={() => setConfirmModal(true)}
                disabled={isRefreshing || isProcessing}
                className="w-full h-11 mt-2 bg-black text-white text-[10px] font-bold uppercase tracking-widest disabled:opacity-50 rounded-2xl transition-all duration-200 hover:scale-[1.02] shadow-md hover:-translate-y-0.5 flex items-center justify-center gap-2"
              >
                Bắt đầu thu thập
              </button>
            )}
          </section>
        </aside>

        <main className="lg:col-span-8 xl:col-span-9 flex flex-col min-h-[500px]">
          <section className="bg-zinc-950 border border-zinc-800 rounded-3xl shadow-xl flex-1 flex flex-col overflow-hidden relative group">
            <div className="absolute inset-0 bg-gradient-to-b from-zinc-900/50 to-transparent pointer-events-none" />
            
            <div className="flex items-center justify-between border-b border-zinc-800/80 bg-zinc-900/80 backdrop-blur-sm px-4 md:px-6 py-4 z-10">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/80 shadow-[0_0_8px_rgba(239,68,68,0.4)]"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500/80 shadow-[0_0_8px_rgba(234,179,8,0.4)]"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500/80 shadow-[0_0_8px_rgba(34,197,94,0.4)]"></div>
                </div>
                <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-zinc-800/50 rounded-xl border border-zinc-700/50">
                  <Terminal className="w-3.5 h-3.5 text-zinc-400" />
                  <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-zinc-400">
                    Live Console
                  </span>
                </div>
              </div>
              <div className="text-[10px] font-mono font-bold tracking-widest text-zinc-500 flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
                sys.log
              </div>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar font-mono text-[11px] sm:text-xs leading-relaxed text-zinc-300 p-4 md:p-6 z-10">
              {logs.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center opacity-50 text-center">
                  <Terminal className="w-12 h-12 text-zinc-700 mb-4" />
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Waiting for collector events...</p>
                </div>
              ) : (
                <div className="space-y-1.5">
                  {logs.map((log, index) => {
                    const parts = log.split(" | ");
                    const time =
                      parts.length >= 3
                        ? (parts[0].split(" ")[1] || parts[0]).substring(0, 8)
                        : "";
                    const level = parts.length >= 3 ? parts[1].trim() : "LOG";
                    const msg =
                      parts.length >= 3
                        ? parts.slice(2).join(" | ").trim()
                        : log.trim();

                    let levelColor = "text-zinc-500";
                    let bgLevelColor = "bg-zinc-800/50 text-zinc-400 border-zinc-700";
                    if (level === "INFO") {
                      levelColor = "text-blue-400";
                      bgLevelColor = "bg-blue-900/20 text-blue-400 border-blue-900/50";
                    } else if (level === "WARNING") {
                      levelColor = "text-yellow-400";
                      bgLevelColor = "bg-yellow-900/20 text-yellow-400 border-yellow-900/50";
                    } else if (level === "ERROR") {
                      levelColor = "text-red-400";
                      bgLevelColor = "bg-red-900/20 text-red-400 border-red-900/50";
                    } else if (level === "SUCCESS") {
                      levelColor = "text-green-400";
                      bgLevelColor = "bg-green-900/20 text-green-400 border-green-900/50";
                    }

                    return (
                      <div key={index} className="flex flex-col sm:flex-row sm:gap-4 py-1 hover:bg-zinc-800/30 px-2 rounded-lg transition-colors group">
                        <div className="flex gap-3 shrink-0 mb-1 sm:mb-0 items-center">
                          <span className="text-zinc-600 font-bold w-16 group-hover:text-zinc-500 transition-colors">{time}</span>
                          {parts.length >= 3 && (
                            <span className={`text-[9px] font-bold px-2 py-0.5 rounded-md border w-16 text-center ${bgLevelColor}`}>
                              {level}
                            </span>
                          )}
                        </div>
                        <span className={`break-words ${levelColor}`}>{msg}</span>
                      </div>
                    );
                  })}
                  <div className="flex gap-4 py-1 px-2 mt-4 items-center">
                    <span className="text-zinc-600 w-16 font-bold">{new Date().toTimeString().split(' ')[0]}</span>
                    <span className="text-[9px] font-bold px-2 py-0.5 rounded-md border bg-zinc-800/50 text-zinc-500 border-zinc-700 w-16 text-center">
                      WAIT
                    </span>
                    <span className="text-zinc-500 flex items-center">
                      <span className="w-1.5 h-3 bg-zinc-400 animate-pulse ml-1"></span>
                    </span>
                  </div>
                </div>
              )}
            </div>
          </section>
        </main>
      </div>

      <Modal
        isOpen={confirmModal}
        onClose={() => !isProcessing && setConfirmModal(false)}
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md p-0 shadow-xl overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6">
          <ModalTitle className="text-sm font-bold tracking-tight text-zinc-900">
            Kích hoạt thu thập
          </ModalTitle>
          <ModalDescription className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mt-1">
            Nguồn: {collectionForm.source}
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <p className="text-xs font-medium text-zinc-500 leading-relaxed bg-zinc-50 border border-zinc-100 p-4 rounded-2xl">
            Tiến trình thu thập dữ liệu tự động từ nguồn bên ngoài sẽ được khởi tạo. Hệ thống có thể tốn tài nguyên tùy vào số lượng cấu hình.
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => !isProcessing && setConfirmModal(false)}
            disabled={isProcessing}
            className="flex-1 h-11 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-black rounded-2xl disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] shadow-sm"
          >
            Hủy
          </button>
          <button
            onClick={handleTriggerCollection}
            disabled={isProcessing}
            className="flex-1 h-11 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl flex items-center justify-center disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md gap-2"
          >
            {isProcessing && <Loader2 className="w-4 h-4 animate-spin" />} Xác
            nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
