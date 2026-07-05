"use client";

import { useEffect, useState } from "react";
import { getMyDocumentsAPI } from "@/features/content/services/document.service";
import {
  getDocumentVersionsAPI,
  restoreVersionAPI,
} from "@/features/content/services/version.service";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Loader2,
  Clock,
  RotateCcw,
  BookOpen,
  GitCompare,
  History,
  CheckCircle2,
  Plus,
} from "lucide-react";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
  ModalDescription,
} from "@/shared/components/ui/Modal";
import PageLoader from "@/shared/components/common/PageLoader";

function renderLineDiff(textA: string, textB: string) {
  const cleanText = (txt: string) => {
    if (!txt) return "";
    try {
      const parsed = JSON.parse(txt);
      if (parsed.blocks)
        return parsed.blocks
          .map((b: any) => b.data?.text || b.data?.code || b.data?.html || "")
          .join("\n");
    } catch {}
    return txt.replace(/<[^>]*>/g, "");
  };
  const linesA = cleanText(textA).split("\n"),
    linesB = cleanText(textB).split("\n");
  const diffRows = [];
  for (let i = 0; i < Math.max(linesA.length, linesB.length); i++) {
    const lineA = linesA[i] || "",
      lineB = linesB[i] || "";
    diffRows.push({
      type: lineA === lineB ? "equal" : "diff",
      a: lineA,
      b: lineB,
    });
  }
  return (
    <div className="flex flex-col font-mono text-[13px] divide-y divide-[#E8E8ED] w-full overflow-x-auto custom-scrollbar bg-white">
      {diffRows.map((row, idx) => (
        <div
          key={idx}
          className="flex min-h-[32px] group hover:bg-[#F5F5F7] transition-colors"
        >
          <div className="w-10 shrink-0 bg-[#F5F5F7] border-[#E8E8ED] flex items-center justify-center text-[12px] text-[#6E6E73]">
            {idx + 1}
          </div>
          <div
            className={`flex-1 p-3 border-[#E8E8ED] whitespace-pre-wrap break-all ${row.type === "diff" && row.a ? "bg-[#FF3B30]/10 text-[#FF3B30] -2 -[#FF3B30] font-medium" : "text-[#1D1D1F]"}`}
          >
            {row.type === "diff" && row.a ? (
              <span className="text-[#FF3B30] select-none mr-2">-</span>
            ) : null}
            {row.a}
          </div>
          <div
            className={`flex-1 p-3 whitespace-pre-wrap break-all ${row.type === "diff" && row.b ? "bg-[#34C759]/10 text-[#34C759] -2 -[#34C759] font-medium" : "text-[#1D1D1F]"}`}
          >
            {row.type === "diff" && row.b ? (
              <span className="text-[#34C759] select-none mr-2">+</span>
            ) : null}
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
  const [showSelectModal, setShowSelectModal] = useState(false);

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
      if (list.length > 0) setSelectedDocumentId(list[0]._id || list[0].id);
    } catch {
      showToast("Lỗi tải danh sách tác phẩm", "error");
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    if (selectedDocumentId) {
      fetchVersions();
      setSelectedVersions([]);
    } else setVersions([]);
  }, [selectedDocumentId]);

  const fetchVersions = async () => {
    setLoadingVersions(true);
    try {
      setVersions((await getDocumentVersionsAPI(selectedDocumentId)) || []);
    } catch {
      showToast("Không thể tải danh sách phiên bản", "error");
      setVersions([]);
    } finally {
      setLoadingVersions(false);
    }
  };

  const toggleVersionSelection = (id: string) =>
    setSelectedVersions((prev) =>
      prev.includes(id)
        ? prev.filter((v) => v !== id)
        : prev.length < 2
          ? [...prev, id]
          : [prev[1], id],
    );

  const handleCompareVersions = async () => {
    if (selectedVersions.length !== 2) return;
    setIsComparing(true);
    try {
      const { getVersionDiffAPI } =
        await import("@/features/compilation/services/editorjs.service");
      setDiffData(
        await getVersionDiffAPI(
          selectedDocumentId,
          selectedVersions[0],
          selectedVersions[1],
        ),
      );
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

  if (loadingDocs) return <PageLoader />;

  return (
    <div className="bg-[#F5F5F7] rounded-[18px] p-6 space-y-6 font-sans text-[#1D1D1F] flex flex-col h-full">
      <div className="flex items-center justify-between shrink-0">
        <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
          Lịch sử
        </h2>
        <button
          onClick={() => setShowSelectModal(true)}
          className="p-2 bg-[#0071E3] rounded-full text-white hover:bg-[#0055C6] transition-colors"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {selectedDocumentId && versions.length > 0 ? (
        <div className="flex-1 min-h-[400px] flex flex-col bg-white rounded-[18px] overflow-hidden pb-6 border border-[#E8E8ED]">
          <div className="p-6 border-b border-[#E8E8ED] flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
            <div>
              <h2 className="text-[17px] font-semibold text-[#1D1D1F] flex items-center gap-2 mb-1">
                <History className="w-5 h-5" /> Danh sách phiên bản
              </h2>
              <p className="text-[13px] text-[#6E6E73]">
                {selectedVersions.length === 2
                  ? "Đã chọn đủ 2 phiên bản để so sánh"
                  : "Bạn có thể chọn 2 phiên bản bất kỳ để xem sự khác biệt"}
              </p>
            </div>
            <button
              onClick={handleCompareVersions}
              disabled={selectedVersions.length !== 2 || isComparing}
              className={`h-[44px] px-6 text-[15px] font-medium rounded-full flex items-center justify-center gap-2 transition-colors ${selectedVersions.length === 2 ? "bg-[#0071E3] text-white hover:bg-[#0077ED]" : "bg-[#F5F5F7] text-[#C7C7CC] cursor-not-allowed "}`}
            >
              {isComparing ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <GitCompare className="w-5 h-5" />
              )}{" "}
              So sánh
            </button>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
            {loadingVersions ? (
              <div className="grid grid-cols-1 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="flex items-center gap-4 p-6 rounded-[18px] bg-white border border-[#E8E8ED] animate-pulse">
                    <div className="w-12 h-12 bg-[#D2D2D7] rounded-[10px] shrink-0" />
                    <div className="space-y-2 flex-1">
                      <div className="h-4 bg-[#D2D2D7] rounded-full w-48" />
                      <div className="h-3 bg-[#D2D2D7] rounded-full w-32" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {versions.map((v) => {
                  const isSelected = selectedVersions.includes(v.id);
                  return (
                    <div
                      key={v.id}
                      onClick={() => toggleVersionSelection(v.id)}
                      className={`flex flex-col sm:flex-row sm:items-center justify-between p-6 rounded-[18px] transition-all cursor-pointer relative overflow-hidden group ${isSelected ? "bg-[#F5F5F7] border-[#0071E3] ring-1 ring-[#0071E3]" : "bg-[#F5F5F7] border border-transparent hover:ring-1 hover:ring-[#E8E8ED]"}`}
                    >
                      {isSelected && (
                        <div className="absolute top-0 left-0 w-1.5 h-full bg-[#0071E3]" />
                      )}
                      <div className="flex items-center gap-4 mb-4 sm:mb-0 ml-2">
                        <div
                          className={`w-12 h-12 flex items-center justify-center rounded-[10px] shrink-0 transition-colors ${isSelected ? "bg-[#0071E3] text-white" : "bg-white text-[#6E6E73] border border-[#E8E8ED]"}`}
                        >
                          {isSelected ? (
                            <CheckCircle2 className="w-6 h-6" />
                          ) : (
                            <Clock className="w-6 h-6" />
                          )}
                        </div>
                        <div className="space-y-1">
                          <h4
                            className={`text-[15px] font-semibold ${isSelected ? "text-[#0071E3]" : "text-[#1D1D1F]"}`}
                          >
                            {new Date(v.created_at).toLocaleString("vi-VN")}
                          </h4>
                          <p className="text-[13px] text-[#6E6E73] flex items-center gap-1.5">
                            <span>Tác giả:</span>
                            <span className="font-medium text-[#1D1D1F]">
                              {v.author_name || "Hệ thống"}
                            </span>
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setConfirmRestore(v.id);
                        }}
                        className="h-[44px] px-6 bg-white text-[13px] font-medium text-[#1D1D1F] rounded-full border border-[#E8E8ED] hover:bg-[#F5F5F7] transition-all flex items-center justify-center gap-2 sm:opacity-0 sm:group-hover:opacity-100"
                      >
                        <RotateCcw className="w-4 h-4" /> Khôi phục
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="py-24 flex flex-col items-center justify-center w-full text-center">
          <p className="text-[17px] text-[#6E6E73]">Chưa có dữ liệu</p>
        </div>
      )}

      <Modal
        isOpen={showSelectModal}
        onClose={() => setShowSelectModal(false)}
      >
        <ModalHeader>
          <ModalTitle>
            Chọn tác phẩm
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="space-y-4">
          <div className="max-h-[300px] overflow-y-auto space-y-2">
            {documents.length === 0 ? (
              <p className="text-center text-[13px] text-[#6E6E73] py-6">
                Chưa có tác phẩm
              </p>
            ) : (
              documents.map((d) => (
                <div
                  key={d.id || d._id}
                  onClick={() => {
                    setSelectedDocumentId(d.id || d._id);
                    setShowSelectModal(false);
                  }}
                  className={`p-4 bg-white rounded-[10px] cursor-pointer transition-colors ${selectedDocumentId === (d.id || d._id) ? "border-[#0071E3] border" : "hover:"}`}
                >
                  <span className="text-[15px] font-medium text-[#1D1D1F]">
                    {d.title || "Chưa có tiêu đề"}
                  </span>
                </div>
              ))
            )}
          </div>
        </ModalContent>
      </Modal>

      <Modal
        isOpen={!!confirmRestore}
        onClose={() => setConfirmRestore(null)}
      >
        <ModalHeader className="bg-[#FF9F0A]/10">
          <ModalTitle className="text-[#FF9F0A] flex items-center gap-2">
            <RotateCcw className="w-5 h-5" /> Xác nhận khôi phục
          </ModalTitle>
          <ModalDescription className="text-[#FF9F0A] ml-7">
            Thay thế nội dung hiện tại
          </ModalDescription>
        </ModalHeader>
        <ModalContent>
          <p className="text-[15px] font-medium text-[#1D1D1F] leading-relaxed bg-[#F5F5F7] p-4 rounded-[10px]">
            Bạn có chắc chắn muốn khôi phục về phiên bản này? <br />
            <br />
            <span className="font-semibold text-[#FF3B30]">
              Nội dung hiện tại sẽ bị ghi đè và bạn sẽ mất các thay đổi mới nhất
              chưa được lưu.
            </span>
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setConfirmRestore(null)}
            className="flex-1 h-[44px] bg-white text-[15px] font-medium text-[#1D1D1F] rounded-full transition-colors hover:bg-[#E8E8ED]"
          >
            Hủy bỏ
          </button>
          <button
            onClick={executeRestore}
            className="flex-1 h-[44px] bg-[#FF9F0A] text-white text-[15px] font-medium rounded-full flex items-center justify-center transition-colors hover:bg-[#E08D00]"
          >
            Xác nhận
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!diffData}
        onClose={() => setDiffData(null)}
        className="max-w-[90vw] md:max-w-5xl h-[85vh] flex flex-col overflow-hidden"
      >
        <ModalHeader className="shrink-0 bg-[#F5F5F7]">
          <ModalTitle className="flex items-center gap-2">
            <GitCompare className="w-5 h-5" /> So sánh sự khác biệt
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="flex-1 overflow-hidden flex flex-col">
          <div className="flex shrink-0 bg-white">
            <div className="flex-1 p-4 bg-[#FF3B30]/10 flex flex-col">
              <span className="text-[13px] font-medium text-[#FF3B30] mb-1">
                Phiên bản A (Cũ)
              </span>
              <span className="text-[12px] font-mono text-[#6E6E73] truncate">
                {diffData?.old_version_id || "A"}
              </span>
            </div>
            <div className="w-px bg-[#E8E8ED] shrink-0" />
            <div className="flex-1 p-4 bg-[#34C759]/10 flex flex-col">
              <span className="text-[13px] font-medium text-[#34C759] mb-1">
                Phiên bản B (Mới)
              </span>
              <span className="text-[12px] font-mono text-[#6E6E73] truncate">
                {diffData?.new_version_id || "B"}
              </span>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar p-0 bg-white">
            {diffData ? (
              renderLineDiff(diffData.version_a || "", diffData.version_b || "")
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                <GitCompare className="w-12 h-12 text-[#C7C7CC] mb-4" />
                <p className="text-[15px] font-medium text-[#6E6E73]">
                  Không có dữ liệu so sánh
                </p>
              </div>
            )}
          </div>
        </ModalContent>
        <ModalFooter className="shrink-0">
          <button
            onClick={() => setDiffData(null)}
            className="h-[44px] px-8 bg-[#0071E3] text-white text-[15px] font-medium rounded-full transition-colors hover:bg-[#0077ED]"
          >
            Đóng cửa sổ
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
