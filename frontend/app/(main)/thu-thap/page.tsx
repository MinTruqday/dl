"use client";

import { useEffect, useState, useCallback } from "react";
import { getCollectorStatsAPI, triggerCollectionAPI } from "@/services/collector.service";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
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
    source: "AnnaArchive",
    url: "",
    index_type: "list",
    target_class: "-1",
  });
  
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [confirmModal, setConfirmModal] = useState<boolean>(false);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const statsRes = await getCollectorStatsAPI();
      setCollectorStats(statsRes.data || statsRes);
    } catch (err: any) {
      showToast("Không thể tải trạng thái thu thập.", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
    }
  }, [showToast]);

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
        collectionForm.url,
        collectionForm.index_type,
        collectionForm.target_class
      );
      showToast("Đã kích hoạt tiến trình thu thập thành công.", "success");
      setCollectionForm({ ...collectionForm, url: "" });
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
    <div className="min-h-screen bg-white font-sans text-black">
      <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12">
        <header className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl font-semibold text-black">Thu thập dữ liệu</h1>
            <p className="text-sm text-zinc-500 mt-1">Hệ thống cào và tự động hóa nguồn dữ liệu</p>
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          <div className="lg:col-span-1 space-y-6">
            <h2 className="text-sm font-semibold text-black">Cấu hình thu thập</h2>
            <div className="border border-zinc-200 bg-white p-6 space-y-5">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-black">Nguồn dữ liệu</label>
                <select
                  value={collectionForm.source}
                  onChange={(e) => setCollectionForm({ ...collectionForm, source: e.target.value })}
                  className="w-full border border-zinc-200 p-3 text-sm font-medium text-black focus:outline-none focus:border-black rounded-none bg-white appearance-none"
                >
                  <option value="AnnaArchive">Anna's Archive</option>
                  <option value="NXBST">Nhà xuất bản Chính trị quốc gia Sự thật</option>
                  <option value="NXBGDC">Nhà xuất bản Giáo dục Việt Nam</option>
                  <option value="CTAN">CTAN - Comprehensive TeX Archive Network</option>
                </select>
              </div>

              {(collectionForm.source === "AnnaArchive" || collectionForm.source === "CTAN") && (
                <>
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-black">Loại chỉ mục</label>
                    <select
                      value={collectionForm.index_type}
                      onChange={(e) => setCollectionForm({ ...collectionForm, index_type: e.target.value })}
                      className="w-full border border-zinc-200 p-3 text-sm font-medium text-black focus:outline-none focus:border-black rounded-none bg-white appearance-none"
                    >
                      <option value="list">Danh sách (List)</option>
                      <option value="detail">Chi tiết (Detail)</option>
                    </select>
                  </div>
                  {collectionForm.index_type === "detail" && (
                    <div className="space-y-2">
                      <label className="text-xs font-semibold text-black">URL mục tiêu</label>
                      <input
                        type="text"
                        value={collectionForm.url}
                        onChange={(e) => setCollectionForm({ ...collectionForm, url: e.target.value })}
                        placeholder="https://www.ctan.org/pkg/..."
                        className="w-full border border-zinc-200 p-3 text-sm font-medium text-black focus:outline-none focus:border-black rounded-none bg-white"
                      />
                    </div>
                  )}
                  {collectionForm.source === "AnnaArchive" && collectionForm.index_type === "list" && (
                    <div className="space-y-2">
                      <label className="text-xs font-semibold text-black">Từ khóa tìm kiếm</label>
                      <input
                        type="text"
                        value={collectionForm.url}
                        onChange={(e) => setCollectionForm({ ...collectionForm, url: e.target.value })}
                        className="w-full border border-zinc-200 p-3 text-sm font-medium text-black focus:outline-none focus:border-black rounded-none bg-white"
                      />
                    </div>
                  )}
                </>
              )}

              {collectionForm.source === "NXBST" && (
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-black">URL chi tiết (Tùy chọn)</label>
                  <input
                    type="text"
                    value={collectionForm.url}
                    onChange={(e) => setCollectionForm({ ...collectionForm, url: e.target.value })}
                    className="w-full border border-zinc-200 p-3 text-sm font-medium text-black focus:outline-none focus:border-black rounded-none bg-white"
                  />
                </div>
              )}


              <button
                onClick={() => setConfirmModal(true)}
                disabled={isRefreshing}
                className="w-full py-3 bg-black text-white text-xs font-semibold uppercase tracking-wider disabled:opacity-50 border border-black rounded-none"
              >
                Bắt đầu thu thập
              </button>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-8">
            <div className="space-y-6">
              <h2 className="text-sm font-semibold text-black">Trạng thái hệ thống</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div className="border border-zinc-200 bg-white p-6 flex flex-col justify-between h-32">
                  <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Tài liệu đã thu thập</p>
                  <p className="text-3xl font-bold tracking-tight text-black">
                    {collectorStats?.total_documents_collected || 0}
                  </p>
                </div>
                <div className="border border-zinc-200 bg-white p-6 flex flex-col justify-between h-32">
                  <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Worker Status</p>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-none ${collectorStats?.status === 'operational' ? 'bg-green-500' : 'bg-red-500'}`} />
                    <p className="text-sm font-bold text-black uppercase">
                      {collectorStats?.status === 'operational' ? 'Đang hoạt động' : 'Tạm dừng / Lỗi'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <h2 className="text-sm font-semibold text-black">Nguồn dữ liệu sẵn dụng</h2>
              <div className="border border-zinc-200 bg-white">
                {[
                  { name: "Anna Archive", type: "Thư viện mở" },
                  { name: "NXB Sự Thật", type: "Chính trị - Pháp luật" },
                  { name: "NXB Giáo Dục", type: "Sách giáo khoa" },
                  { name: "CTAN", type: "LaTeX Packages" },
                ].map((source, i, arr) => (
                  <div key={i} className={`p-4 flex items-center justify-between ${i !== arr.length - 1 ? 'border-b border-zinc-200' : ''}`}>
                    <div className="flex flex-col gap-1">
                      <span className="text-sm font-semibold text-black">{source.name}</span>
                      <span className="text-[10px] font-medium uppercase tracking-widest text-zinc-500">{source.type}</span>
                    </div>
                    <span className="text-xs font-medium text-black border border-black px-2 py-1">HOẠT ĐỘNG</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <Modal isOpen={confirmModal} onClose={() => !isProcessing && setConfirmModal(false)} className="max-w-md">
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
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black disabled:opacity-50 flex items-center justify-center rounded-none"
          >
            Hủy
          </button>
          <button
            onClick={handleTriggerCollection}
            disabled={isProcessing}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black disabled:opacity-50 flex items-center justify-center gap-2 rounded-none"
          >
            {isProcessing && <Loader2 className="w-3 h-3 animate-spin" />} Xác nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
