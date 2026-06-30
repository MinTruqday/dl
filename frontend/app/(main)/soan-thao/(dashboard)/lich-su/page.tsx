"use client";

import { useEffect, useState } from "react";
import { getMyDocumentsAPI } from "@/features/content/services/document_metadata.service";
import { getDocumentVersionsAPI, restoreVersionAPI } from "@/features/content/services/version_history.service";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2, Clock, RotateCcw, BookOpen, GitCompare, History, CheckCircle2 } from "lucide-react";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter, ModalDescription } from "@/shared/components/ui/Modal";
import PageLoader from "@/shared/components/common/PageLoader";

function renderLineDiff(textA: string, textB: string) {
  const cleanText = (txt: string) => {
    if (!txt) return "";
    try {
      const parsed = JSON.parse(txt);
      if (parsed.blocks) return parsed.blocks.map((b: any) => b.data?.text || b.data?.code || b.data?.html || "").join("\n");
    } catch {}
    return txt.replace(/<[^>]*>/g, "");
  };
  const linesA = cleanText(textA).split("\n"), linesB = cleanText(textB).split("\n");
  const diffRows = [];
  for (let i = 0; i < Math.max(linesA.length, linesB.length); i++) {
    const lineA = linesA[i] || "", lineB = linesB[i] || "";
    diffRows.push({ type: lineA === lineB ? "equal" : "diff", a: lineA, b: lineB });
  }
  return (
    <div className="flex flex-col font-mono text-[13px] divide-y divide-[#E8E8ED] w-full overflow-x-auto custom-scrollbar bg-white">
      {diffRows.map((row, idx) => (
        <div key={idx} className="flex min-h-[32px] group hover:bg-[#F5F5F7] transition-colors">
          <div className="w-10 shrink-0 bg-[#F5F5F7] border-r border-[#E8E8ED] flex items-center justify-center text-[12px] text-[#6E6E73]">{idx + 1}</div>
          <div className={`flex-1 p-3 border-r border-[#E8E8ED] whitespace-pre-wrap break-all ${row.type === "diff" && row.a ? "bg-[#FF3B30]/10 text-[#FF3B30] border-l-2 border-l-[#FF3B30] font-medium" : "text-[#1D1D1F]"}`}>
            {row.type === "diff" && row.a ? <span className="text-[#FF3B30] select-none mr-2">-</span> : null}{row.a}
          </div>
          <div className={`flex-1 p-3 whitespace-pre-wrap break-all ${row.type === "diff" && row.b ? "bg-[#34C759]/10 text-[#34C759] border-l-2 border-l-[#34C759] font-medium" : "text-[#1D1D1F]"}`}>
            {row.type === "diff" && row.b ? <span className="text-[#34C759] select-none mr-2">+</span> : null}{row.b}
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

  useEffect(() => { fetchInitData(); }, []);

  const fetchInitData = async () => {
    setLoadingDocs(true);
    try {
      const docsData = await getMyDocumentsAPI();
      const list = docsData.data || docsData || [];
      setDocuments(list);
      if (list.length > 0) setSelectedDocumentId(list[0]._id || list[0].id);
    } catch { showToast("Lỗi tải danh sách tác phẩm", "error"); } finally { setLoadingDocs(false); requestAnimationFrame(() => setVisible(true)); }
  };

  useEffect(() => { if (selectedDocumentId) { fetchVersions(); setSelectedVersions([]); } else setVersions([]); }, [selectedDocumentId]);

  const fetchVersions = async () => {
    setLoadingVersions(true);
    try { setVersions(await getDocumentVersionsAPI(selectedDocumentId) || []); } catch { showToast("Không thể tải danh sách phiên bản", "error"); setVersions([]); } finally { setLoadingVersions(false); }
  };

  const toggleVersionSelection = (id: string) => setSelectedVersions((prev) => prev.includes(id) ? prev.filter((v) => v !== id) : prev.length < 2 ? [...prev, id] : [prev[1], id]);

  const handleCompareVersions = async () => {
    if (selectedVersions.length !== 2) return;
    setIsComparing(true);
    try {
      const { getVersionDiffAPI } = await import("@/features/editor/services/document_editing.service");
      setDiffData(await getVersionDiffAPI(selectedDocumentId, selectedVersions[0], selectedVersions[1]));
    } catch (err: any) { showToast(err.message || "Không thể so sánh phiên bản", "error"); } finally { setIsComparing(false); }
  };

  const executeRestore = async () => {
    if (!confirmRestore) return;
    try {
      await restoreVersionAPI(confirmRestore);
      showToast("Đã khôi phục phiên bản thành công", "success"); setConfirmRestore(null); fetchVersions();
    } catch (e: any) { showToast(e.message || "Khôi phục thất bại", "error"); }
  };

  if (loadingDocs) return (
    <PageLoader />
  );

  return (
    <div className="flex flex-col h-full font-sans">
      <div className={`flex-1 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-6 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`} style={{ transitionDelay: "100ms" }}>
        <div className="bg-[#F5F5F7] border border-[#E8E8ED] p-6 rounded-[24px] flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white border border-[#E8E8ED] rounded-[14px] flex items-center justify-center shrink-0">
              <BookOpen className="w-6 h-6 text-[#1D1D1F]" />
            </div>
            <div>
              <h2 className="text-[20px] font-semibold text-[#1D1D1F]">Chọn tác phẩm</h2>
              <p className="text-[13px] text-[#6E6E73]">Xem lịch sử của tài liệu cụ thể</p>
            </div>
          </div>
          <div className="relative w-full sm:w-[320px]">
            <BookOpen className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6E6E73]" />
            <select value={selectedDocumentId} onChange={(e) => setSelectedDocumentId(e.target.value)} className="w-full h-[48px] pl-12 pr-4 border border-[#E8E8ED] text-[15px] font-medium text-[#1D1D1F] focus:outline-none focus:border-[#0071E3] bg-white rounded-[14px] appearance-none transition-colors cursor-pointer">
              {documents.length === 0 && <option value="" disabled>Chưa có tác phẩm</option>}
              {documents.map((d) => <option key={d.id || d._id} value={d.id || d._id}>{d.title || "Chưa có tiêu đề"}</option>)}
            </select>
          </div>
        </div>

        {selectedDocumentId ? (
          <div className="flex-1 min-h-0 flex flex-col bg-[#F5F5F7] border-[#E8E8ED] rounded-[24px] overflow-hidden pb-6">
            <div className="border-b border-[#E8E8ED] p-6 bg-[#F5F5F7] flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
              <div>
                <h2 className="text-[20px] font-semibold text-[#1D1D1F] flex items-center gap-2 mb-1"><History className="w-5 h-5" /> Danh sách phiên bản</h2>
                <p className="text-[13px] text-[#6E6E73]">{selectedVersions.length === 2 ? "Đã chọn đủ 2 phiên bản để so sánh" : "Bạn có thể chọn 2 phiên bản bất kỳ để xem sự khác biệt"}</p>
              </div>
              <button onClick={handleCompareVersions} disabled={selectedVersions.length !== 2 || isComparing} className={`h-[44px] px-6 text-[15px] font-medium rounded-full flex items-center justify-center gap-2 transition-colors ${selectedVersions.length === 2 ? "bg-[#0071E3] text-white hover:bg-[#0077ED]" : "bg-[#F5F5F7] text-[#C7C7CC] cursor-not-allowed border border-[#E8E8ED]"}`}>
                {isComparing ? <Loader2 className="w-5 h-5 animate-spin" /> : <GitCompare className="w-5 h-5" />} So sánh
              </button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
              {loadingVersions ? (
                <div className="h-full flex flex-col items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-[#0071E3] mb-4" /><p className="text-[13px] font-medium text-[#6E6E73]">Đang tải dữ liệu...</p></div>
              ) : versions.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-12"><div className="w-16 h-16 bg-[#F5F5F7] border border-[#E8E8ED] flex items-center justify-center rounded-[18px] mb-4"><History className="w-8 h-8 text-[#C7C7CC]" /></div><h3 className="text-[17px] font-medium text-[#1D1D1F] mb-2">Chưa có phiên bản</h3><p className="text-[15px] text-[#6E6E73] max-w-sm">Tác phẩm này chưa có phiên bản nào được lưu lại trong lịch sử.</p></div>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  {versions.map((v) => {
                    const isSelected = selectedVersions.includes(v.id);
                    return (
                      <div key={v.id} onClick={() => toggleVersionSelection(v.id)} className={`flex flex-col sm:flex-row sm:items-center justify-between p-6 rounded-[24px] transition-all cursor-pointer relative overflow-hidden group ${isSelected ? "bg-[#0071E3]/5 border-[#0071E3]" : "bg-[#F5F5F7] border-[#E8E8ED] hover:"}`}>
                        {isSelected && <div className="absolute top-0 left-0 w-1.5 h-full bg-[#0071E3]" />}
                        <div className="flex items-center gap-4 mb-4 sm:mb-0 ml-2">
                          <div className={`w-12 h-12 flex items-center justify-center rounded-[14px] shrink-0 transition-colors ${isSelected ? "bg-[#0071E3] text-white" : "bg-[#F5F5F7] text-[#6E6E73] border border-[#E8E8ED]"}`}>
                            {isSelected ? <CheckCircle2 className="w-6 h-6" /> : <Clock className="w-6 h-6" />}
                          </div>
                          <div className="space-y-1">
                            <h4 className={`text-[15px] font-semibold ${isSelected ? "text-[#0071E3]" : "text-[#1D1D1F]"}`}>{new Date(v.created_at).toLocaleString("vi-VN")}</h4>
                            <p className="text-[13px] text-[#6E6E73] flex items-center gap-1.5"><span>Tác giả:</span><span className="font-medium text-[#1D1D1F]">{v.author_name || "Hệ thống"}</span></p>
                          </div>
                        </div>
                        <button onClick={(e) => { e.stopPropagation(); setConfirmRestore(v.id); }} className="h-[44px] px-6 bg-white border border-[#E8E8ED] text-[13px] font-medium text-[#1D1D1F] rounded-full hover:bg-[#F5F5F7] transition-all flex items-center justify-center gap-2 sm:opacity-0 sm:group-hover:opacity-100">
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
          <div className="flex-1 bg-[#F5F5F7] border border-[#E8E8ED] rounded-[24px] p-12 flex flex-col items-center justify-center gap-4 text-center">
            <div className="w-16 h-16 bg-[#F5F5F7] border-[#E8E8ED] flex items-center justify-center rounded-[18px] mb-2"><History className="w-8 h-8 text-[#C7C7CC]" /></div>
            <p className="text-[15px] text-[#6E6E73] max-w-sm">Vui lòng chọn một tác phẩm từ danh sách để xem lịch sử phiên bản</p>
          </div>
        )}
      </div>

      <Modal isOpen={!!confirmRestore} onClose={() => setConfirmRestore(null)} className="max-w-md rounded-[24px] border-[#E8E8ED] bg-[#F5F5F7] p-0 shadow-lg overflow-hidden">
        <ModalHeader className="border-b border-[#E8E8ED] p-6 bg-[#FF9F0A]/10">
          <ModalTitle className="text-[17px] font-semibold text-[#FF9F0A] flex items-center gap-2"><RotateCcw className="w-5 h-5" /> Xác nhận khôi phục</ModalTitle>
          <ModalDescription className="text-[13px] text-[#FF9F0A] mt-2 ml-7">Thay thế nội dung hiện tại</ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <p className="text-[15px] font-medium text-[#1D1D1F] leading-relaxed bg-[#F5F5F7] border border-[#E8E8ED] p-4 rounded-[14px]">
            Bạn có chắc chắn muốn khôi phục về phiên bản này? <br/><br/>
            <span className="font-semibold text-[#FF3B30]">Nội dung hiện tại sẽ bị ghi đè và bạn sẽ mất các thay đổi mới nhất chưa được lưu.</span>
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-[#E8E8ED] p-6 bg-[#F5F5F7]">
          <button onClick={() => setConfirmRestore(null)} className="flex-1 h-[44px] bg-white border border-[#E8E8ED] text-[15px] font-medium text-[#1D1D1F] rounded-full transition-colors hover:bg-[#E8E8ED]">Hủy bỏ</button>
          <button onClick={executeRestore} className="flex-1 h-[44px] bg-[#FF9F0A] text-white text-[15px] font-medium rounded-full flex items-center justify-center transition-colors hover:bg-[#E08D00]">Xác nhận</button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!diffData} onClose={() => setDiffData(null)} className="max-w-[90vw] md:max-w-5xl h-[85vh] rounded-[24px] border-[#E8E8ED] bg-[#F5F5F7] p-0 shadow-lg flex flex-col overflow-hidden">
        <ModalHeader className="border-b border-[#E8E8ED] p-6 shrink-0 bg-[#F5F5F7]">
          <ModalTitle className="text-[17px] font-semibold text-[#1D1D1F] flex items-center gap-2"><GitCompare className="w-5 h-5" /> So sánh sự khác biệt</ModalTitle>
        </ModalHeader>
        <ModalContent className="flex-1 overflow-hidden p-0 flex flex-col bg-white">
          <div className="flex border-b border-[#E8E8ED] shrink-0 bg-white">
            <div className="flex-1 p-4 bg-[#FF3B30]/10 flex flex-col"><span className="text-[13px] font-medium text-[#FF3B30] mb-1">Phiên bản A (Cũ)</span><span className="text-[12px] font-mono text-[#6E6E73] truncate">{diffData?.old_version_id || "A"}</span></div>
            <div className="w-px bg-[#E8E8ED] shrink-0" />
            <div className="flex-1 p-4 bg-[#34C759]/10 flex flex-col"><span className="text-[13px] font-medium text-[#34C759] mb-1">Phiên bản B (Mới)</span><span className="text-[12px] font-mono text-[#6E6E73] truncate">{diffData?.new_version_id || "B"}</span></div>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar p-0 bg-white">
            {diffData ? renderLineDiff(diffData.version_a || "", diffData.version_b || "") : (
              <div className="h-full flex flex-col items-center justify-center p-12 text-center"><GitCompare className="w-12 h-12 text-[#C7C7CC] mb-4" /><p className="text-[15px] font-medium text-[#6E6E73]">Không có dữ liệu so sánh</p></div>
            )}
          </div>
        </ModalContent>
        <ModalFooter className="border-t border-[#E8E8ED] p-6 shrink-0 bg-[#F5F5F7] flex justify-end">
          <button onClick={() => setDiffData(null)} className="h-[44px] px-8 bg-[#0071E3] text-white text-[15px] font-medium rounded-full transition-colors hover:bg-[#0077ED]">Đóng cửa sổ</button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
