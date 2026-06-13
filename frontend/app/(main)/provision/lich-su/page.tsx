"use client";

import { useEffect, useState } from "react";
import { getMyDocumentsAPI } from "@/features/content/services/document.service";
import {
  getDocumentVersionsAPI,
  restoreVersionAPI,
} from "@/features/content/services/version.service";
import { useToast } from "@/shared/contexts/Toast";
import { Loader2, Clock, Eye, RotateCcw } from "lucide-react";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";

function renderLineDiff(textA: string, textB: string) {
  const cleanText = (txt: string) => {
    if (!txt) return "";
    try {
      const parsed = JSON.parse(txt);
      if (parsed.blocks) {
        return parsed.blocks
          .map((b: any) => b.data?.text || b.data?.code || b.data?.html || "")
          .join("\n");
      }
    } catch (err: any) {}
    return txt.replace(/<[^>]*>/g, "");
  };

  const aClean = cleanText(textA);
  const bClean = cleanText(textB);

  const linesA = aClean.split("\n");
  const linesB = bClean.split("\n");

  const maxLength = Math.max(linesA.length, linesB.length);
  const diffRows = [];

  for (let i = 0; i < maxLength; i++) {
    const lineA = linesA[i] || "";
    const lineB = linesB[i] || "";
    if (lineA === lineB) {
      diffRows.push({ type: "equal", a: lineA, b: lineB });
    } else {
      diffRows.push({ type: "diff", a: lineA, b: lineB });
    }
  }

  return (
    <div className="flex flex-col font-mono text-xs divide-y divide-zinc-100 w-full overflow-x-auto">
      {diffRows.map((row, idx) => (
        <div
          key={idx}
          className="flex min-h-[28px] border-l-4 border-transparent"
        >
          <div
            className={`flex-1 p-3 border-r border-zinc-200 whitespace-pre-wrap break-all ${row.type === "diff" && row.a ? "bg-red-50 text-red-800 border-l-4 border-red-500 font-semibold" : "text-zinc-600"}`}
          >
            {row.type === "diff" && row.a ? `- ${row.a}` : row.a}
          </div>
          <div
            className={`flex-1 p-3 whitespace-pre-wrap break-all ${row.type === "diff" && row.b ? "bg-green-50 text-green-800 border-l-4 border-green-500 font-semibold" : "text-zinc-600"}`}
          >
            {row.type === "diff" && row.b ? `+ ${row.b}` : row.b}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function HistoryPage() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [loadingDocs, setLoadingDocs] = useState(true);

  const [versions, setVersions] = useState<any[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);

  const [diffData, setDiffData] = useState<any>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [confirmRestore, setConfirmRestore] = useState<string | null>(null);

  useEffect(() => {
    fetchInitData();
  }, []);

  const fetchInitData = async () => {
    setLoadingDocs(true);
    try {
      const docsData = await getMyDocumentsAPI();
      const list = docsData.data || docsData || [];
      setDocuments(list);
      if (list.length > 0) {
        setSelectedDocumentId(list[0]._id || list[0].id);
      }
    } catch (e: any) {
      showToast("Lỗi tải danh sách tác phẩm", "error");
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    if (selectedDocumentId) {
      fetchVersions();
      setSelectedVersions([]);
    } else {
      setVersions([]);
    }
  }, [selectedDocumentId]);

  const fetchVersions = async () => {
    setLoadingVersions(true);
    try {
      const data = await getDocumentVersionsAPI(selectedDocumentId);
      setVersions(data || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách phiên bản", "error");
      setVersions([]);
    } finally {
      setLoadingVersions(false);
    }
  };

  const toggleVersionSelection = (id: string) => {
    setSelectedVersions((prev) =>
      prev.includes(id)
        ? prev.filter((v) => v !== id)
        : prev.length < 2
          ? [...prev, id]
          : [prev[1], id],
    );
  };

  const handleCompareVersions = async () => {
    if (selectedVersions.length !== 2) return;
    setIsComparing(true);
    try {
      const { getVersionDiffAPI } =
        await import("@/features/editor/services/editor.service");
      const data = await getVersionDiffAPI(
        selectedDocumentId,
        selectedVersions[0],
        selectedVersions[1],
      );
      setDiffData(data);
    } catch (err: any) {
      showToast(err.message || "Không thể so sánh phiên bản", "error");
    } finally {
      setIsComparing(false);
    }
  };

  const executeRestore = async () => {
    if (!confirmRestore) return;
    try {
      await restoreVersionAPI(confirmRestore);
      showToast("Đã khôi phục phiên bản thành công", "success");
      setConfirmRestore(null);
      fetchVersions();
    } catch (e: any) {
      showToast(e.message || "Khôi phục thất bại", "error");
    }
  };

  if (loadingDocs) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div
        className="bg-white border border-zinc-200 p-6 rounded-2xl shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-in fade-in slide-in-from-bottom-8 duration-300"
        style={{ animationDelay: "150ms", animationFillMode: "both" }}
      >
        <div className="space-y-1">
          <h2 className="text-xl font-medium text-black flex items-center gap-2">
            <Clock className="w-5 h-5" /> Lịch sử phiên bản
          </h2>
          <p className="text-sm font-medium text-zinc-500">
            Khôi phục hoặc so sánh nội dung cũ
          </p>
        </div>
        <select
          value={selectedDocumentId}
          onChange={(e) => setSelectedDocumentId(e.target.value)}
          className="w-full sm:w-64 h-10 border border-zinc-200 px-3 text-sm outline-none bg-white rounded-xl focus:border-black"
        >
          {documents.map((d) => (
            <option key={d.id || d._id} value={d.id || d._id}>
              {d.title}
            </option>
          ))}
        </select>
      </div>

      {selectedDocumentId ? (
        <div
          className="bg-white border border-zinc-200 p-8 rounded-2xl shadow-sm space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-300"
          style={{ animationDelay: "150ms", animationFillMode: "both" }}
        >
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-500">
              {selectedVersions.length === 2
                ? "Đã chọn 2 phiên bản để so sánh"
                : "Chọn tối đa 2 phiên bản để so sánh sự khác biệt"}
            </p>
            <div className="flex gap-3">
              {selectedVersions.length === 2 && (
                <button
                  onClick={handleCompareVersions}
                  disabled={isComparing}
                  className="h-10 bg-black text-white px-6 text-sm font-medium rounded-xl flex items-center gap-2 hover:bg-zinc-800 transition-colors"
                >
                  {isComparing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                  So sánh ngay
                </button>
              )}
            </div>
          </div>

          <div className="space-y-4">
            {loadingVersions ? (
              <div className="py-12 flex justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
              </div>
            ) : versions.length === 0 ? (
              <div className="bg-zinc-50 border border-zinc-200 p-16 text-center rounded-2xl flex flex-col items-center justify-center gap-3">
                <Clock className="w-6 h-6 text-zinc-400" />
                <p className="text-sm font-medium text-zinc-500">
                  Chưa có phiên bản nào được lưu
                </p>
              </div>
            ) : (
              versions.map((v) => (
                <div
                  key={v.id}
                  onClick={() => toggleVersionSelection(v.id)}
                  className={`bg-white border p-6 flex items-center justify-between rounded-2xl cursor-pointer transition-all ${
                    selectedVersions.includes(v.id)
                      ? "border-black ring-1 ring-black shadow-sm"
                      : "border-zinc-200 hover:border-zinc-300"
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`w-10 h-10 flex items-center justify-center rounded-xl border ${selectedVersions.includes(v.id) ? "bg-black text-white border-black" : "bg-zinc-50 text-zinc-500 border-zinc-200"}`}
                    >
                      <Clock className="w-4 h-4" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-base font-medium text-black">
                        {new Date(v.created_at).toLocaleString("vi-VN")}
                      </p>
                      <p className="text-sm font-medium text-zinc-500">
                        Lưu bởi: {v.author_name || "Hệ thống"}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setConfirmRestore(v.id);
                      }}
                      className="h-9 px-4 border border-zinc-200 text-sm font-medium text-black rounded-xl bg-white hover:bg-zinc-50 transition-colors flex items-center gap-2"
                    >
                      <RotateCcw className="w-4 h-4" /> Khôi phục
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white border border-zinc-200 p-16 rounded-2xl flex flex-col items-center justify-center gap-4 text-center">
          <Clock className="w-8 h-8 text-zinc-300" />
          <p className="text-sm font-medium text-zinc-500">
            Vui lòng chọn một tác phẩm để xem lịch sử
          </p>
        </div>
      )}

      <Modal
        isOpen={!!confirmRestore}
        onClose={() => setConfirmRestore(null)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle>Khôi phục phiên bản</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs font-medium text-zinc-500 leading-relaxed">
            Bạn có chắc muốn khôi phục về phiên bản này? Nội dung hiện tại sẽ bị
            ghi đè và bạn sẽ mất các thay đổi mới nhất.
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setConfirmRestore(null)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black rounded-xl"
          >
            Hủy
          </button>
          <button
            onClick={executeRestore}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black rounded-xl"
          >
            Khôi phục
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!diffData}
        onClose={() => setDiffData(null)}
        className="max-w-5xl h-[80vh] flex flex-col"
      >
        <ModalHeader>
          <ModalTitle>So sánh sự khác biệt</ModalTitle>
        </ModalHeader>
        <ModalContent className="flex-1 overflow-hidden p-0 flex flex-col">
          <div className="flex bg-zinc-50 border-b border-zinc-200 divide-x divide-zinc-200">
            <div className="flex-1 p-3 text-[10px] font-bold uppercase tracking-widest text-zinc-400">
              Phiên bản A (Cũ)
            </div>
            <div className="flex-1 p-3 text-[10px] font-bold uppercase tracking-widest text-zinc-400">
              Phiên bản B (Mới)
            </div>
          </div>
          <div className="flex-1 overflow-y-auto bg-white p-0">
            {diffData ? (
              renderLineDiff(diffData.version_a || "", diffData.version_b || "")
            ) : (
              <div className="p-8 text-center text-zinc-500 text-sm italic">
                Không có dữ liệu so sánh
              </div>
            )}
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setDiffData(null)}
            className="px-6 py-2 bg-black text-white text-xs font-medium rounded-xl"
          >
            Đóng cửa sổ
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
