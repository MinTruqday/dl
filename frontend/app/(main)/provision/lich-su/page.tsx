"use client";

import { useEffect, useState } from "react";
import { getMyDocumentsAPI } from "@/features/content/services/document_metadata.service";
import {
  getDocumentVersionsAPI,
  restoreVersionAPI,
} from "@/features/content/services/version_history.service";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2, Clock, Eye, RotateCcw, BookOpen, GitCompare, History, CheckCircle2 } from "lucide-react";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
  ModalDescription,
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
    <div className="flex flex-col font-mono text-xs divide-y divide-zinc-100 w-full overflow-x-auto custom-scrollbar">
      {diffRows.map((row, idx) => (
        <div
          key={idx}
          className="flex min-h-[32px] group hover:bg-zinc-50 transition-colors"
        >
          <div className="w-8 shrink-0 bg-zinc-50 border-r border-zinc-100 flex items-center justify-center text-[9px] text-zinc-400 group-hover:text-zinc-500">
            {idx + 1}
          </div>
          <div
            className={`flex-1 p-3 border-r border-zinc-100 whitespace-pre-wrap break-all ${row.type === "diff" && row.a ? "bg-red-50/50 text-red-900 border-l-2 border-l-red-500 font-medium" : "text-zinc-600"}`}
          >
            {row.type === "diff" && row.a ? <span className="text-red-500 select-none mr-2">-</span> : null}
            {row.a}
          </div>
          <div
            className={`flex-1 p-3 whitespace-pre-wrap break-all ${row.type === "diff" && row.b ? "bg-green-50/50 text-green-900 border-l-2 border-l-green-500 font-medium" : "text-zinc-600"}`}
          >
            {row.type === "diff" && row.b ? <span className="text-green-500 select-none mr-2">+</span> : null}
            {row.b}
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
  const [visible, setVisible] = useState(false);

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
      requestAnimationFrame(() => setVisible(true));
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
        await import("@/features/editor/services/document_editing.service");
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
      <div className="h-full min-h-[400px] flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400 mb-4" />
        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Đang tải lịch sử...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-zinc-100 pb-4 mb-6 shrink-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
          Lịch sử phiên bản
        </h1>
        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
          Khôi phục hoặc so sánh sự thay đổi của nội dung qua từng thời điểm
        </p>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-6 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0, transitionDelay: "100ms" }}>
        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 rounded-3xl shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0 transition-all duration-300 hover:border-zinc-200">
          <div className="space-y-1.5 flex items-center gap-3">
            <div className="w-10 h-10 bg-zinc-50 border border-zinc-100 rounded-2xl flex items-center justify-center shrink-0">
              <BookOpen className="w-5 h-5 text-black" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">
                Chọn tác phẩm
              </h2>
              <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                Xem lịch sử của tài liệu cụ thể
              </p>
            </div>
          </div>
          <div className="relative w-full sm:w-72">
            <BookOpen className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <select
              value={selectedDocumentId}
              onChange={(e) => setSelectedDocumentId(e.target.value)}
              className="w-full h-11 pl-10 pr-4 border border-zinc-200 text-sm font-bold text-zinc-900 focus:outline-none focus:border-black bg-zinc-50 focus:bg-white rounded-2xl appearance-none transition-all duration-200 shadow-sm cursor-pointer"
            >
              {documents.length === 0 && <option value="" disabled>Chưa có tác phẩm</option>}
              {documents.map((d) => (
                <option key={d.id || d._id} value={d.id || d._id}>
                  {d.title || "Chưa có tiêu đề"}
                </option>
              ))}
            </select>
          </div>
        </div>

        {selectedDocumentId ? (
          <div className="flex-1 min-h-0 flex flex-col bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm overflow-hidden pb-6">
            <div className="border-b border-zinc-100 p-6 bg-zinc-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
              <div>
                <h2 className="text-sm font-bold text-zinc-900 uppercase tracking-widest flex items-center gap-2 mb-1">
                  <History className="w-4 h-4 text-black" />
                  Danh sách phiên bản
                </h2>
                <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                  {selectedVersions.length === 2
                    ? "Đã chọn đủ 2 phiên bản để so sánh"
                    : "Bạn có thể chọn 2 phiên bản bất kỳ để xem sự khác biệt"}
                </p>
              </div>
              
              <button
                onClick={handleCompareVersions}
                disabled={selectedVersions.length !== 2 || isComparing}
                className={`h-11 px-6 text-[10px] font-bold uppercase tracking-widest rounded-2xl flex items-center justify-center gap-2 transition-all duration-300 shadow-sm ${
                  selectedVersions.length === 2
                    ? "bg-black text-white hover:bg-zinc-800 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
                    : "bg-zinc-100 text-zinc-400 cursor-not-allowed border border-zinc-200"
                }`}
              >
                {isComparing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <GitCompare className="w-4 h-4" />
                )}
                So sánh phiên bản
              </button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
              {loadingVersions ? (
                <div className="h-full flex flex-col items-center justify-center">
                  <Loader2 className="w-8 h-8 animate-spin text-zinc-300 mb-4" />
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Đang tải dữ liệu...</p>
                </div>
              ) : versions.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-12">
                  <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
                    <History className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
                  </div>
                  <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-1">Chưa có phiên bản</h3>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 max-w-sm">
                    Tác phẩm này chưa có phiên bản nào được lưu lại trong lịch sử.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  {versions.map((v) => {
                    const isSelected = selectedVersions.includes(v.id);
                    return (
                      <div
                        key={v.id}
                        onClick={() => toggleVersionSelection(v.id)}
                        className={`flex flex-col sm:flex-row sm:items-center justify-between p-5 rounded-2xl transition-all duration-300 cursor-pointer shadow-sm relative overflow-hidden group ${
                          isSelected
                            ? "bg-zinc-50 border-2 border-black"
                            : "bg-white border border-zinc-200 hover:border-zinc-300 hover:shadow-md hover:-translate-y-0.5"
                        }`}
                      >
                        {isSelected && (
                          <div className="absolute top-0 left-0 w-1.5 h-full bg-black"></div>
                        )}
                        <div className="flex items-center gap-4 mb-4 sm:mb-0 ml-1">
                          <div
                            className={`w-12 h-12 flex items-center justify-center rounded-xl shrink-0 transition-colors ${
                              isSelected ? "bg-black text-white shadow-md" : "bg-zinc-50 text-zinc-400 border border-zinc-100 group-hover:bg-zinc-100 group-hover:text-zinc-600"
                            }`}
                          >
                            {isSelected ? <CheckCircle2 className="w-5 h-5" /> : <Clock className="w-5 h-5" />}
                          </div>
                          <div className="space-y-1.5">
                            <h4 className={`text-sm font-bold uppercase tracking-wider ${isSelected ? "text-zinc-900" : "text-zinc-700 group-hover:text-black"}`}>
                              {new Date(v.created_at).toLocaleString("vi-VN")}
                            </h4>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 flex items-center gap-1.5">
                              <span>Tác giả:</span>
                              <span className="text-zinc-900">{v.author_name || "Hệ thống"}</span>
                            </p>
                          </div>
                        </div>
                        
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setConfirmRestore(v.id);
                          }}
                          className="h-10 px-5 bg-white border border-zinc-200 text-[10px] font-bold uppercase tracking-widest text-zinc-600 rounded-xl hover:bg-black hover:text-white hover:border-black transition-all flex items-center justify-center gap-2 sm:opacity-0 sm:group-hover:opacity-100 shadow-sm"
                        >
                          <RotateCcw className="w-3.5 h-3.5" /> Khôi phục
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl p-12 flex flex-col items-center justify-center gap-4 text-center shadow-sm">
            <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-2">
              <History className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
            </div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 max-w-xs">
              Vui lòng chọn một tác phẩm từ danh sách để xem lịch sử phiên bản
            </p>
          </div>
        )}
      </div>

      <Modal
        isOpen={!!confirmRestore}
        onClose={() => setConfirmRestore(null)}
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md p-0 shadow-xl overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6 bg-orange-50/50">
          <ModalTitle className="text-sm font-bold tracking-tight text-orange-600 flex items-center gap-2">
            <RotateCcw className="w-5 h-5" /> Xác nhận khôi phục
          </ModalTitle>
          <ModalDescription className="text-[10px] font-bold uppercase tracking-widest text-orange-400 mt-1 ml-7">
            Thay thế nội dung hiện tại
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <p className="text-xs font-medium text-zinc-700 leading-relaxed bg-zinc-50 border border-zinc-100 p-4 rounded-2xl">
            Bạn có chắc chắn muốn khôi phục về phiên bản này? 
            <br/><br/>
            <span className="font-bold">Nội dung hiện tại sẽ bị ghi đè và bạn sẽ mất các thay đổi mới nhất chưa được lưu.</span>
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => setConfirmRestore(null)}
            className="flex-1 h-11 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-black rounded-2xl transition-all hover:scale-[1.02] shadow-sm"
          >
            Hủy bỏ
          </button>
          <button
            onClick={executeRestore}
            className="flex-1 h-11 text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl flex items-center justify-center transition-all hover:scale-[1.02] shadow-md gap-2 bg-orange-600 hover:bg-orange-700"
          >
            Xác nhận
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!diffData}
        onClose={() => setDiffData(null)}
        className="max-w-[90vw] md:max-w-5xl h-[85vh] rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md p-0 shadow-2xl flex flex-col overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-5 shrink-0 bg-white/50">
          <ModalTitle className="text-sm font-bold tracking-tight flex items-center gap-2">
            <GitCompare className="w-5 h-5" /> So sánh sự khác biệt
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="flex-1 overflow-hidden p-0 flex flex-col bg-white">
          <div className="flex border-b border-zinc-100 shrink-0">
            <div className="flex-1 p-4 bg-red-50/30 flex flex-col">
              <span className="text-[10px] font-bold uppercase tracking-widest text-red-600 mb-1">Phiên bản A (Cũ)</span>
              <span className="text-xs font-mono text-zinc-500 truncate">{diffData?.old_version_id || "A"}</span>
            </div>
            <div className="w-px bg-zinc-200 shrink-0"></div>
            <div className="flex-1 p-4 bg-green-50/30 flex flex-col">
              <span className="text-[10px] font-bold uppercase tracking-widest text-green-600 mb-1">Phiên bản B (Mới)</span>
              <span className="text-xs font-mono text-zinc-500 truncate">{diffData?.new_version_id || "B"}</span>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar p-0 bg-white">
            {diffData ? (
              renderLineDiff(diffData.version_a || "", diffData.version_b || "")
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                <GitCompare className="w-12 h-12 text-zinc-200 mb-4" />
                <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Không có dữ liệu so sánh</p>
              </div>
            )}
          </div>
        </ModalContent>
        <ModalFooter className="border-t border-zinc-100 p-4 shrink-0 bg-zinc-50/50 flex justify-end">
          <button
            onClick={() => setDiffData(null)}
            className="h-10 px-6 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-xl transition-all hover:bg-zinc-800 shadow-sm"
          >
            Đóng cửa sổ
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
