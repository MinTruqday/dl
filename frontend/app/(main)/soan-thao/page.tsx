"use client";

import { useEffect, useMemo, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { getDocumentDraftAPI, getMyDocumentsAPI, saveDocumentDraftAPI, updateDocumentAPI } from "@/features/content/services/document_metadata.service";
import { compileDocumentAPI } from "@/features/editor/services/document_compilation.service";
import { publishDocumentAPI } from "@/features/content/services/publication_process.service";
import { exportDocumentPdfAPI, exportDocumentDocxAPI } from "@/features/provision/services/data_export.service";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { FileText, Save, Download, Loader2, CalendarClock, StickyNote } from "lucide-react";
import dynamic from "next/dynamic";
const Editor = dynamic(() => import("@/features/editor/components/Editor"), { ssr: false });
import edjsHTML from "editorjs-html";
import { compileLatexPreviewAPI } from "@/features/editor/services/latex_compilation.service";

const customParsers = {
  alert: (block: any) => `<div class="p-4 rounded-[14px] my-4 bg-[#F5F5F7]"><strong>${block.data.type || "Lưu ý"}</strong>: ${block.data.message}</div>`,
  table: (block: any) => `<table class="w-full border-collapse border border-[#D2D2D7] my-4">${(block.data.content || []).map((row: any) => `<tr>${row.map((cell: any) => `<td class="border border-[#D2D2D7] p-2">${cell}</td>`).join("")}</tr>`).join("")}</table>`,
  toggle: (block: any) => `<details class="p-4 border border-[#D2D2D7] rounded-[14px] my-4"><summary class="font-semibold cursor-pointer">${block.data.text}</summary><div class="mt-2 text-[14px] text-[#6E6E73]">${block.data.items}</div></details>`,
  checklist: (block: any) => `<ul class="list-none pl-0 my-4">${(block.data.items || []).map((item: any) => `<li class="flex items-start gap-2"><input type="checkbox" ${item.checked ? "checked" : ""} disabled /> <span>${item.text}</span></li>`).join("")}</ul>`,
  nestedChecklist: (block: any) => `<ul class="list-none pl-0 my-4">${(block.data.items || []).map((item: any) => `<li class="flex items-start gap-2"><input type="checkbox" ${item.checked ? "checked" : ""} disabled /> <span>${item.content}</span></li>`).join("")}</ul>`,
  originalQuote: (block: any) => `<blockquote class="border-l-4 border-[#D2D2D7] pl-4 py-2 italic my-4 text-[#6E6E73]">${block.data.text} <br/><cite class="text-[14px] font-semibold mt-2 block">- ${block.data.caption}</cite></blockquote>`,
  divider: () => `<hr class="my-6 border-[#D2D2D7]" />`,
  math: (block: any) => `<div class="p-4 bg-[#F5F5F7] font-mono text-[14px] my-4 overflow-x-auto rounded-[14px]">${block.data.math}</div>`,
  mermaid: (block: any) => `<div class="p-4 border border-[#D2D2D7] rounded-[14px] my-4 text-[14px] text-[#6E6E73] italic">[Biểu đồ Mermaid không được hỗ trợ trong xem trước]</div>`,
  attaches: (block: any) => `<div class="p-4 border border-[#D2D2D7] rounded-[14px] my-4 flex flex-col gap-1 text-[14px] bg-[#F5F5F7]"><span class="font-semibold text-[#1D1D1F]">${block.data.title || "Tập tin đính kèm"}</span><a href="${block.data.file?.url}" class="text-[#0071E3] hover:underline break-all">${block.data.file?.url}</a></div>`,
  personality: (block: any) => `<div class="p-4 border border-[#D2D2D7] rounded-[14px] my-4 flex gap-4 items-center bg-[#F5F5F7]"><img src="${block.data.photo}" class="w-16 h-16 rounded-full object-cover" /><div><div class="font-semibold text-[#1D1D1F]">${block.data.name}</div><div class="text-[14px] text-[#6E6E73]">${block.data.description}</div></div></div>`,
};

const edjsParser = edjsHTML(customParsers);
const safeParseEditorJs = (data: any) => {
  if (!data || !data.blocks) return "";
  const supportedTypes = ["paragraph", "header", "list", "quote", "image", "delimiter", ...Object.keys(customParsers)];
  const sanitizedData = { ...data, blocks: data.blocks.map((b: any) => {
    if (!supportedTypes.includes(b.type)) return { type: "paragraph", data: { text: `<div class="p-4 bg-[#FFF0F0] text-[#FF3B30] text-[14px] my-4 rounded-[14px]">Khối chưa hỗ trợ xem trước: ${b.type}</div>` } };
    return b;
  }) };
  return edjsParser.parse(sanitizedData).join("");
};

function StudioContent() {
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const { showToast } = useToast();
  const rawDocId = searchParams.get("tai-lieu");
  const docIdFromUrl = rawDocId && rawDocId !== "undefined" ? rawDocId : "";

  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState(docIdFromUrl || "");
  const [editorMode, setEditorMode] = useState<"edit" | "preview" | "raw">("edit");
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState("Sẵn sàng");
  const [isExporting, setIsExporting] = useState(false);
  const [scheduleDate, setScheduleDate] = useState("");
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);
  const [isPreviewCompiling, setIsPreviewCompiling] = useState(false);

  const selectedDocument = useMemo(() => documents.find((b: any) => (b._id || b.id) === selectedDocumentId) || null, [documents, selectedDocumentId]);

  useEffect(() => {
    let currentUrl: string | null = null;
    if (editorMode === "preview" && selectedDocument?.content_format === "latex") {
      setIsPreviewCompiling(true);
      compileLatexPreviewAPI(content, false)
        .then((blob) => { currentUrl = URL.createObjectURL(blob); setPreviewPdfUrl(currentUrl); })
        .catch((err: any) => showToast("Lỗi biên dịch: " + (err.message || "Lỗi không xác định"), "error"))
        .finally(() => setIsPreviewCompiling(false));
    }
    return () => { if (currentUrl) URL.revokeObjectURL(currentUrl); setPreviewPdfUrl(null); };
  }, [editorMode, selectedDocument?.content_format, content, showToast]);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getMyDocumentsAPI();
      const list = data.data || data || [];
      setDocuments(list);
      if (list.length > 0 && !selectedDocumentId) setSelectedDocumentId(list[0]._id || list[0].id);
    } catch (err: any) {
      showToast("Lỗi tải danh sách tài liệu", "error");
    } finally { setIsLoading(false); }
  }, [selectedDocumentId, showToast]);

  const loadDraft = useCallback(async () => {
    if (!selectedDocumentId) return;
    try {
      const data = await getDocumentDraftAPI(selectedDocumentId);
      setContent(data.data?.content || data?.content || "");
      setStatusMsg("Đã tải xong");
    } catch (e: any) { setStatusMsg("Lỗi tải bản nháp"); }
  }, [selectedDocumentId]);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);
  useEffect(() => { if (selectedDocumentId) loadDraft(); else setContent(""); }, [selectedDocumentId, loadDraft]);

  useEffect(() => {
    if (!selectedDocumentId) return;
    const timer = setTimeout(async () => {
      setStatusMsg("Đang lưu bản nháp...");
      try {
        await saveDocumentDraftAPI(selectedDocumentId, content, selectedDocument?.content_format || "json");
        setStatusMsg("Đã lưu bản nháp");
        setTimeout(() => setStatusMsg("Sẵn sàng"), 2000);
      } catch (err) { setStatusMsg("Lỗi lưu bản thảo"); }
    }, 5000);
    return () => clearTimeout(timer);
  }, [content, selectedDocumentId, selectedDocument?.content_format]);

  const handleSave = async () => {
    if (!selectedDocumentId) return;
    setIsSaving(true); setStatusMsg("Đang lưu...");
    try {
      await saveDocumentDraftAPI(selectedDocumentId, content, selectedDocument?.content_format || "json");
      showToast("Đã lưu bản nháp thành công", "success");
    } catch (err: any) { showToast("Không thể lưu bản nháp", "error"); } finally { setIsSaving(false); setStatusMsg("Sẵn sàng"); }
  };

  const handlePublish = async () => {
    if (!selectedDocumentId) return;
    setStatusMsg("Đang xuất bản...");
    try {
      await compileDocumentAPI(selectedDocumentId);
      await publishDocumentAPI(selectedDocumentId);
      showToast("Tài liệu đã được công bố", "success");
      fetchDocuments();
    } catch (err: any) { showToast("Xuất bản thất bại", "error"); setStatusMsg("Sẵn sàng"); }
  };

  const handleExportPDF = async () => {
    if (!selectedDocumentId) return;
    setIsExporting(true); setStatusMsg("Đang tạo PDF...");
    try {
      const blob = await exportDocumentPdfAPI(selectedDocumentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = `${selectedDocument?.title || "ban-thao"}.pdf`; document.body.appendChild(a); a.click(); a.remove(); window.URL.revokeObjectURL(url);
      showToast("Tải PDF thành công", "success");
    } catch (e: any) { showToast("Lỗi tạo PDF", "error"); } finally { setIsExporting(false); setStatusMsg("Sẵn sàng"); }
  };

  const handleExportDOCX = async () => {
    if (!selectedDocumentId) return;
    setIsExporting(true); setStatusMsg("Đang tạo DOCX...");
    try {
      const blob = await exportDocumentDocxAPI(selectedDocumentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = `${selectedDocument?.title || "ban-thao"}.docx`; document.body.appendChild(a); a.click(); a.remove(); window.URL.revokeObjectURL(url);
      showToast("Tải DOCX thành công", "success");
    } catch (e: any) { showToast("Lỗi tạo DOCX", "error"); } finally { setIsExporting(false); setStatusMsg("Sẵn sàng"); }
  };

  if (isLoading) return <div className="flex-1 flex flex-col items-center justify-center min-h-[80vh]"><Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" /></div>;

  return (
    <div className="w-full max-w-[1200px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] flex flex-col gap-6 text-[#1D1D1F]">
      <div className="h-[64px] bg-white rounded-[24px] px-6 flex items-center justify-between shadow-sm border border-[#E8E8ED] shrink-0">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-[#F5F5F7] flex items-center justify-center rounded-full"><FileText className="w-5 h-5 text-[#1D1D1F]" /></div>
          <span className="text-[17px] font-semibold text-[#1D1D1F] truncate max-w-[200px] md:max-w-[400px]">
            {selectedDocument?.title || "Bản thảo chưa đặt tên"}
          </span>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-[13px] text-[#6E6E73] hidden md:block">{statusMsg}</span>
          <div className="flex items-center gap-3">
            <div className="relative group flex items-center h-10">
              <button disabled={!selectedDocumentId || isExporting} className="h-full px-5 text-[14px] font-medium text-[#1D1D1F] flex items-center gap-2 rounded-full bg-[#F5F5F7] hover:bg-[#E8E8ED] transition-colors disabled:opacity-50">
                <Download className="w-4 h-4" /> Xuất bản sao
              </button>
              <div className="absolute top-full right-0 mt-2 w-40 bg-white border border-[#E8E8ED] shadow-sm rounded-[14px] opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 overflow-hidden">
                <button disabled={isExporting} onClick={handleExportPDF} className="w-full text-left px-4 py-3 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] disabled:opacity-50">Định dạng PDF</button>
                <div className="w-full h-px bg-[#E8E8ED]"></div>
                <button onClick={handleExportDOCX} className="w-full text-left px-4 py-3 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7]">Định dạng Word</button>
              </div>
            </div>
            
            <button onClick={handleSave} disabled={!selectedDocumentId || isSaving} className="h-10 px-5 text-[14px] font-medium text-[#1D1D1F] flex items-center gap-2 rounded-full bg-[#F5F5F7] hover:bg-[#E8E8ED] transition-colors disabled:opacity-50">
              {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Lưu nháp
            </button>
            <button onClick={handlePublish} disabled={!selectedDocumentId} className="pill-button h-10 px-6">Phát hành</button>
          </div>
        </div>
      </div>

      <div className="flex-1 w-full flex flex-col bg-white border border-[#E8E8ED] rounded-[24px] shadow-sm overflow-hidden">
        <div className="h-[48px] bg-[#F5F5F7] px-6 flex items-center border-b border-[#E8E8ED] gap-2 shrink-0">
          {(["edit", "preview", "raw"] as const).map((m) => (
            <button key={m} onClick={() => setEditorMode(m)} className={`h-full px-4 text-[14px] font-medium flex items-center transition-colors border-b-2 ${editorMode === m ? "border-[#1D1D1F] text-[#1D1D1F]" : "border-transparent text-[#6E6E73] hover:text-[#1D1D1F]"}`}>
              {m === "edit" ? "Soạn thảo" : m === "preview" ? "Xem trước" : "Mã nguồn"}
            </button>
          ))}
        </div>
        
        <div className="flex-1 overflow-y-auto bg-white p-8">
          {editorMode === "edit" ? (
            <div className="h-full">
              <Editor documentId={selectedDocumentId} initialContent={content} contentFormat={selectedDocument?.content_format || "json"} onSave={(val) => setContent(val)} />
            </div>
          ) : editorMode === "preview" ? (
            <div className="min-h-full max-w-[800px] mx-auto">
              {selectedDocument?.content_format === "latex" ? (
                isPreviewCompiling ? (
                  <div className="flex flex-col items-center justify-center h-full min-h-[400px]"><Loader2 className="w-8 h-8 animate-spin text-[#6E6E73] mb-4" /><p className="text-[14px] text-[#6E6E73]">Biên dịch LaTeX...</p></div>
                ) : previewPdfUrl ? (
                  <iframe src={previewPdfUrl} className="w-full h-[800px] border border-[#E8E8ED] rounded-[18px]" title="Preview" />
                ) : <div className="text-center text-[#6E6E73] mt-12">Chưa có dữ liệu PDF.</div>
              ) : (
                <div className="prose prose-zinc max-w-none font-sans text-[16px] leading-relaxed text-[#1D1D1F]" dangerouslySetInnerHTML={{ __html: (() => { try { const data = JSON.parse(content); if (data.blocks) return safeParseEditorJs(data); return content; } catch (e) { return content; } })() }} />
              )}
            </div>
          ) : (
            <pre className="p-6 bg-[#F5F5F7] text-[#1D1D1F] text-[13px] font-mono whitespace-pre-wrap rounded-[18px]">{content || "Trống"}</pre>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AuthorStudioPage() {
  return (
    <Suspense fallback={<div className="flex-1 flex items-center justify-center min-h-[80vh]"><Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" /></div>}>
      <StudioContent />
    </Suspense>
  );
}
