"use client";

import { useEffect, useState, useCallback } from "react";
import { getCollectorStatsAPI, triggerCollectionAPI, getCollectorLogsAPI } from "@/services/collector.service";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/Auth";
import { useToast } from "@/contexts/Toast";
import { useRouter } from "next/navigation";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";

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
      showToast("Không thể tải trạng thái thu thập.", "error");
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
      await triggerCollectionAPI(
        collectionForm.source,
        collectionForm.pages
      );
      showToast("Đã kích hoạt tiến trình thu thập thành công.", "success");
      setCollectionForm({ ...collectionForm, pages: 1 });
      fetchData();
      setConfirmModal(false);
    } catch (err: any) {
      showToast(
        err.message || "Không thể kích hoạt tiến trình thu thập.",
        "error"
      );
    } finally {
      setIsRefreshing(false);
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
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col font-sans text-black selection:bg-black selection:text-white">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 overflow-y-auto pb-6">
        <aside className="lg:col-span-3 flex flex-col gap-6">
          <section className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 space-y-4">
            <div className="flex items-center justify-between mb-1">
              <div className="text-sm font-semibold text-black">Trạng thái hệ thống</div>
              <button
                onClick={fetchData}
                disabled={isRefreshing}
                className="text-xs font-medium text-zinc-500 hover:text-black transition-colors disabled:opacity-50 flex items-center gap-1.5 bg-zinc-100 hover:bg-zinc-200 px-2 py-1 rounded-md"
              >
                {isRefreshing ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                {isRefreshing ? "Đang tải..." : "Đồng bộ"}
              </button>
            </div>
            <div className="flex flex-col gap-4">
              <div className="border border-zinc-200 bg-zinc-50 rounded-2xl p-5 flex flex-col justify-between h-32">
                <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Tài liệu đã thu thập</p>
                <p className="text-3xl font-bold tracking-tight text-black">
                  {collectorStats?.total_documents_collected || 0}
                </p>
              </div>
              <div className="border border-zinc-200 bg-zinc-50 rounded-2xl p-5 flex flex-col justify-between h-32">
                <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Worker Status</p>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${collectorStats?.status === 'operational' ? 'bg-green-500' : 'bg-red-500'}`} />
                  <p className="text-sm font-bold text-black uppercase">
                    {collectorStats?.status === 'operational' ? 'Đang hoạt động' : 'Tạm dừng / Lỗi'}
                  </p>
                </div>
              </div>
            </div>
          </section>
        </aside>

        <main className="lg:col-span-9 flex flex-col gap-6">
          <section className="bg-[#0a0a0a] border border-zinc-800 rounded-2xl shadow-sm p-5 space-y-3 h-[450px] shrink-0 flex flex-col">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
              </div>
              <div className="text-[10px] font-mono font-medium tracking-widest uppercase text-zinc-500">Tiến trình thu thập</div>
            </div>
            
            <div className="flex-1 overflow-y-auto font-mono text-[11px] sm:text-xs leading-loose text-zinc-300 space-y-1">
              {logs.map((log, index) => {
                const parts = log.split(" | ");
                const time = parts.length >= 3 ? (parts[0].split(" ")[1] || parts[0]).substring(0, 8) : "";
                const level = parts.length >= 3 ? parts[1].trim() : "LOG";
                const msg = parts.length >= 3 ? parts.slice(2).join(" | ").trim() : log.trim();
                
                let levelColor = "text-zinc-400";
                if (level === "INFO") levelColor = "text-blue-400";
                else if (level === "WARNING") levelColor = "text-yellow-400";
                else if (level === "ERROR") levelColor = "text-red-400";
                else if (level === "SUCCESS") levelColor = "text-green-400";

                return (
                  <div key={index} className="flex gap-2 sm:gap-3">
                    <span className="text-zinc-600 shrink-0 w-16">{time}</span>
                    <span className={`${levelColor} shrink-0 w-16 sm:w-20`}>{parts.length >= 3 ? `[${level}]` : ''}</span>
                    <span className="break-words">{msg}</span>
                  </div>
                );
              })}
              <div className="flex gap-2 sm:gap-3 mt-2">
                <span className="text-zinc-600 shrink-0 w-16"></span>
                <span className="text-zinc-500 shrink-0 w-16 sm:w-20"></span>
                <span className="break-words text-zinc-500"><span className="animate-pulse text-white">_</span></span>
              </div>
            </div>
          </section>

          <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 space-y-5">
            <div className="text-sm font-semibold text-black mb-1">Cấu hình thu thập</div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-black">Nguồn dữ liệu</label>
                <select
                  value={collectionForm.source}
                  onChange={(e) => setCollectionForm({ ...collectionForm, source: e.target.value })}
                  className="w-full border border-zinc-200 p-3 text-sm font-medium text-black focus:outline-none focus:border-black rounded-2xl bg-white appearance-none"
                >
                  <option value="" disabled>-- Chọn nguồn dữ liệu --</option>
                  <option value="AnnaArchive">Anna's Archive</option>
                  <option value="NXBST">Nhà xuất bản Chính trị quốc gia Sự thật</option>
                  <option value="NXBGD">Nhà xuất bản Giáo dục Việt Nam</option>
                  <option value="CTAN">CTAN - Comprehensive TeX Archive Network</option>
                </select>
              </div>

              {collectionForm.source && (
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-black">Số trang thu thập</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={collectionForm.pages}
                    onChange={(e) => {
                      const val = parseInt(e.target.value);
                      setCollectionForm({ ...collectionForm, pages: isNaN(val) ? 0 : val });
                    }}
                    className="w-full border border-zinc-200 p-3 text-sm font-medium text-black focus:outline-none focus:border-black rounded-2xl bg-white"
                  />
                </div>
              )}
            </div>

            {collectionForm.source && (
              <button
                onClick={() => setConfirmModal(true)}
                disabled={isRefreshing}
                className="w-full py-3 bg-black text-white text-xs font-semibold uppercase tracking-wider disabled:opacity-50 border border-black rounded-2xl hover:bg-zinc-800 transition-colors"
              >
                Bắt đầu thu thập
              </button>
            )}
          </div>
        </main>
        </div>

      <Modal isOpen={confirmModal} onClose={() => !isProcessing && setConfirmModal(false)} className="max-w-md rounded-2xl">
        <ModalHeader>
          <ModalTitle>Kích hoạt thu thập</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs font-medium text-zinc-500 leading-relaxed">
            Tiến trình thu thập dữ liệu từ nguồn bên ngoài sẽ được khởi tạo. Bạn có chắc chắn?
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => !isProcessing && setConfirmModal(false)}
            disabled={isProcessing}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black disabled:opacity-50 flex items-center justify-center rounded-2xl hover:bg-zinc-50 transition-colors"
          >
            Hủy
          </button>
          <button
            onClick={handleTriggerCollection}
            disabled={isProcessing}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black disabled:opacity-50 flex items-center justify-center gap-2 rounded-2xl hover:bg-zinc-800 transition-colors"
          >
            {isProcessing && <Loader2 className="w-3 h-3 animate-spin" />} Xác nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
