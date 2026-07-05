"use client";

import { useEffect, useMemo, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  getDocumentDraftAPI,
  getMyDocumentsAPI,
  saveDocumentDraftAPI,
  updateDocumentAPI,
} from "@/features/content/services/document.service";
import {
  exportToWordAPI,
  compilePreviewAPI
} from "@/features/compilation/services/editorjs.service";
import { API_URL, getAuthHeaders } from "@/features/authentication/services/session.service";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  FileText,
  Save,
  Download,
  Loader2,
  CalendarClock,
  StickyNote,
} from "lucide-react";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
} from "@/shared/components/ui/Modal";
import dynamic from "next/dynamic";
const Editor = dynamic(() => import("@/features/compilation/components/Editor"), {
  ssr: false,
});
import edjsHTML from "editorjs-html";
import { compileLatexPreviewAPI, exportLatexAPI } from "@/features/compilation/services/latex.service";

const customParsers = {
  alert: (block: any) =>
    `<div class="p-4 rounded-[10px] my-4 bg-[#F5F5F7]"><strong>${block.data.type || "Lưu ý"}</strong>: ${block.data.message}</div>`,
  table: (block: any) =>
    `<table class="w-full border-collapse  border-[#D2D2D7] my-4">${(block.data.content || []).map((row: any) => `<tr>${row.map((cell: any) => `<td class=" border-[#D2D2D7] p-2">${cell}</td>`).join("")}</tr>`).join("")}</table>`,
  toggle: (block: any) =>
    `<details class="p-4  border-[#D2D2D7] rounded-[10px] my-4"><summary class="font-semibold cursor-pointer">${block.data.text}</summary><div class="mt-2 text-[14px] text-[#6E6E73]">${block.data.items}</div></details>`,
  checklist: (block: any) =>
    `<ul class="list-none pl-0 my-4">${(block.data.items || []).map((item: any) => `<li class="flex items-start gap-2"><input type="checkbox" ${item.checked ? "checked" : ""} disabled /> <span>${item.text}</span></li>`).join("")}</ul>`,
  nestedChecklist: (block: any) =>
    `<ul class="list-none pl-0 my-4">${(block.data.items || []).map((item: any) => `<li class="flex items-start gap-2"><input type="checkbox" ${item.checked ? "checked" : ""} disabled /> <span>${item.content}</span></li>`).join("")}</ul>`,
  originalQuote: (block: any) =>
    `<blockquote class="-4 border-[#D2D2D7] pl-4 py-2 italic my-4 text-[#6E6E73]">${block.data.text} <br/><cite class="text-[14px] font-semibold mt-2 block">- ${block.data.caption}</cite></blockquote>`,
  divider: () => `<hr class="my-6 border-[#D2D2D7]" />`,
  math: (block: any) =>
    `<div class="p-4 bg-[#F5F5F7] font-mono text-[14px] my-4 overflow-x-auto rounded-[10px]">${block.data.math}</div>`,
  mermaid: (block: any) =>
    `<div class="p-4  border-[#D2D2D7] rounded-[10px] my-4 text-[14px] text-[#6E6E73] italic">[Biểu đồ Mermaid không được hỗ trợ trong xem trước]</div>`,
  attaches: (block: any) =>
    `<div class="p-4  border-[#D2D2D7] rounded-[10px] my-4 flex flex-col gap-1 text-[14px] bg-[#F5F5F7]"><span class="font-semibold text-[#1D1D1F]">${block.data.title || "Tập tin đính kèm"}</span><a href="${block.data.file?.url}" class="text-[#0071E3] hover:underline break-all">${block.data.file?.url}</a></div>`,
  personality: (block: any) =>
    `<div class="p-4  border-[#D2D2D7] rounded-[10px] my-4 flex gap-4 items-center bg-[#F5F5F7]"><img src="${block.data.photo}" class="w-16 h-16 rounded-full object-cover" /><div><div class="font-semibold text-[#1D1D1F]">${block.data.name}</div><div class="text-[14px] text-[#6E6E73]">${block.data.description}</div></div></div>`,
};

const edjsParser = edjsHTML(customParsers);
const safeParseEditorJs = (data: any) => {
  if (!data || !data.blocks) return "";
  const supportedTypes = [
    "paragraph",
    "header",
    "list",
    "quote",
    "image",
    "delimiter",
    ...Object.keys(customParsers),
  ];
  const sanitizedData = {
    ...data,
    blocks: data.blocks.map((b: any) => {
      if (!supportedTypes.includes(b.type))
        return {
          type: "paragraph",
          data: {
            text: `<div class="p-4 bg-[#FFF0F0] text-[#FF3B30] text-[14px] my-4 rounded-[10px]">Khối chưa hỗ trợ xem trước: ${b.type}</div>`,
          },
        };
      return b;
    }),
  };
  const parsed = edjsParser.parse(sanitizedData);
  return Array.isArray(parsed) ? parsed.join("") : parsed;
};

function StudioContent() {
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const { showToast } = useToast();
  const rawDocId = searchParams.get("tai-lieu");
  const docIdFromUrl = rawDocId && rawDocId !== "undefined" ? rawDocId : "";

  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState(
    docIdFromUrl || "",
  );
  const [editorMode, setEditorMode] = useState<"edit" | "preview" | "raw">(
    "edit",
  );
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState("Sẵn sàng");
  const [isExporting, setIsExporting] = useState(false);
  const [scheduleDate, setScheduleDate] = useState("");
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);
  const [isPreviewCompiling, setIsPreviewCompiling] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);

  const selectedDocument = useMemo(
    () =>
      documents.find((b: any) => (b._id || b.id) === selectedDocumentId) ||
      null,
    [documents, selectedDocumentId],
  );

  useEffect(() => {
    let currentUrl: string | null = null;
    if (
      editorMode === "preview" &&
      selectedDocument?.content_format === "latex"
    ) {
      setIsPreviewCompiling(true);
      compileLatexPreviewAPI(content, false)
        .then((blob) => {
          currentUrl = URL.createObjectURL(blob);
          setPreviewPdfUrl(currentUrl);
        })
        .catch((err: any) =>
          showToast(
            "Lỗi biên dịch: " + (err.message || "Lỗi không xác định"),
            "error",
          ),
        )
        .finally(() => setIsPreviewCompiling(false));
    }
    return () => {
      if (currentUrl) URL.revokeObjectURL(currentUrl);
      setPreviewPdfUrl(null);
    };
  }, [editorMode, selectedDocument?.content_format, content, showToast]);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getMyDocumentsAPI();
      const list = data.data || data || [];
      setDocuments(list);
      if (list.length > 0 && !selectedDocumentId)
        setSelectedDocumentId(list[0]._id || list[0].id);
    } catch (err: any) {
      showToast("Lỗi tải danh sách tài liệu", "error");
    } finally {
      setIsLoading(false);
    }
  }, [selectedDocumentId, showToast]);

  const loadDraft = useCallback(async () => {
    if (!selectedDocumentId) return;
    try {
      const data = await getDocumentDraftAPI(selectedDocumentId);
      setContent(data.data?.content || data?.content || "");
      setStatusMsg("Đã tải xong");
    } catch (e: any) {
      setStatusMsg("Lỗi tải bản nháp");
    }
  }, [selectedDocumentId]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);
  useEffect(() => {
    if (selectedDocumentId) loadDraft();
    else setContent("");
  }, [selectedDocumentId, loadDraft]);

  useEffect(() => {
    if (!selectedDocumentId) return;
    const timer = setTimeout(async () => {
      setStatusMsg("Đang lưu bản nháp...");
      try {
        await saveDocumentDraftAPI(
          selectedDocumentId,
          content,
          selectedDocument?.content_format || "json",
        );
        setStatusMsg("Đã lưu bản nháp");
        setTimeout(() => setStatusMsg("Sẵn sàng"), 2000);
      } catch (err) {
        setStatusMsg("Lỗi lưu bản thảo");
      }
    }, 5000);
    return () => clearTimeout(timer);
  }, [content, selectedDocumentId, selectedDocument?.content_format]);

  const handleSave = async () => {
    if (!selectedDocumentId) return;
    setIsSaving(true);
    setStatusMsg("Đang lưu...");
    try {
      await saveDocumentDraftAPI(
        selectedDocumentId,
        content,
        selectedDocument?.content_format || "json",
      );
      showToast("Đã lưu bản nháp thành công", "success");
    } catch (err: any) {
      showToast("Không thể lưu bản nháp", "error");
    } finally {
      setIsSaving(false);
      setStatusMsg("Sẵn sàng");
    }
  };

  const handlePublish = async () => {
    if (!selectedDocumentId) return;
    setStatusMsg("Đang xuất bản");
    try {
      await compileDocumentAPI(selectedDocumentId);
      await publishDocumentAPI(selectedDocumentId);
      showToast("Tài liệu đã được công bố", "success");
      fetchDocuments();
    } catch (err: any) {
      showToast("Xuất bản thất bại", "error");
      setStatusMsg("Sẵn sàng");
    }
  };

  const handleExportPDF = async () => {
    if (!selectedDocumentId || !content) return;
    setIsExporting(true);
    setStatusMsg("Đang tạo PDF...");
    try {
      let blob;
      if (selectedDocument?.content_format === "latex") {
        blob = await exportLatexAPI(content, "pdf");
      } else {
        blob = await compilePreviewAPI(content, false);
      }
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${selectedDocument?.title || "ban-thao"}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showToast("Tải PDF thành công", "success");
    } catch (e: any) {
      showToast("Lỗi tạo PDF", "error");
    } finally {
      setIsExporting(false);
      setStatusMsg("Sẵn sàng");
    }
  };

  const handleExportDOCX = async () => {
    if (!selectedDocumentId || !content) return;
    setIsExporting(true);
    setStatusMsg("Đang tạo DOCX...");
    try {
      let blob;
      if (selectedDocument?.content_format === "latex") {
        blob = await exportLatexAPI(content, "docx");
      } else {
        blob = await exportToWordAPI(content);
      }
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${selectedDocument?.title || "ban-thao"}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showToast("Tải DOCX thành công", "success");
    } catch (e: any) {
      showToast("Lỗi tạo DOCX", "error");
    } finally {
      setIsExporting(false);
      setStatusMsg("Sẵn sàng");
    }
  };

  const handleExportDRM = async () => {
    if (!selectedDocumentId) return;
    setIsExporting(true);
    setStatusMsg("Đang tạo tệp bảo mật...");
    try {
      const res = await fetch(`${API_URL}/ket-xuat/${selectedDocumentId}/drm`, {
        headers: getAuthHeaders(),
      });
      if (!res.ok) throw new Error("Xuất DRM thất bại");
      
      const contentDisposition = res.headers.get('content-disposition');
      let filename = `${selectedDocument?.title || "ban-thao"}.doclib`;
      if (contentDisposition && contentDisposition.includes('filename="TaiLieuBaoMat.pdf"')) {
        filename = `${selectedDocument?.title || "ban-thao"}.pdf`;
      }
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showToast("Tải tệp bảo mật thành công", "success");
    } catch (e: any) {
      showToast("Lỗi tạo tệp bảo mật", "error");
    } finally {
      setIsExporting(false);
      setStatusMsg("Sẵn sàng");
    }
  };

  if (isLoading)
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[80vh]">
        <Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" />
      </div>
    );

  return (
    <div className="w-full max-w-[1200px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] font-sans text-[#1D1D1F] flex flex-col gap-6">
      <div className="flex flex-col md:flex-row gap-6 flex-1 min-h-0">
        <main className="flex-1 min-w-0 flex flex-col min-h-0 bg-[#F5F5F7] rounded-[18px] overflow-hidden">
          <div className="h-[60px] px-6 flex items-center justify-between shrink-0 border-b border-[#E8E8ED]">
            <div className="flex items-center gap-6 h-full">
              <div className="flex flex-col max-w-[240px] border-r border-[#E8E8ED] pr-6 justify-center h-full">
                <span
                  className="text-[14px] font-semibold text-[#1D1D1F] truncate"
                  title={selectedDocument?.title || "Bản thảo chưa đặt tên"}
                >
                  {selectedDocument?.title || "Bản thảo chưa đặt tên"}
                </span>
                <span className="text-[12px] text-[#6E6E73] truncate">{statusMsg}</span>
              </div>
              <div className="flex items-center gap-2 h-full">
                {(["edit", "preview", "raw"] as const).map((m) => (
                  <button
                    key={m}
                    onClick={() => setEditorMode(m)}
                    className={`h-full px-4 text-[14px] font-medium flex items-center transition-colors ${editorMode === m ? "text-[#1D1D1F] border-b-2 border-[#1D1D1F]" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
                  >
                    {m === "edit"
                      ? "Soạn thảo"
                      : m === "preview"
                        ? "Xem trước"
                        : "Mã nguồn"}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowExportModal(true)}
                disabled={!selectedDocumentId || isExporting}
                className="px-3 py-1.5 text-[13px] font-medium rounded-full bg-white text-[#1D1D1F] hover:bg-[#E8E8ED] transition-colors disabled:opacity-50 flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" /> Xuất
              </button>
              <button
                onClick={handleSave}
                disabled={!selectedDocumentId || isSaving}
                className="px-3 py-1.5 text-[13px] font-medium rounded-full bg-white text-[#0071E3] hover:bg-[#E8E8ED] transition-colors disabled:opacity-50 flex items-center gap-1.5"
              >
                <Save className="w-3.5 h-3.5" /> {isSaving ? "Đang lưu" : "Lưu nháp"}
              </button>
              <button
                onClick={handlePublish}
                disabled={!selectedDocumentId}
                className="px-3 py-1.5 text-[13px] font-medium rounded-full bg-[#0071E3] text-white hover:bg-[#0077ED] transition-colors disabled:opacity-50 flex items-center gap-1.5"
              >
                Phát hành
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto bg-white p-8">
            {editorMode === "edit" ? (
              <div className="h-full">
                <Editor
                  documentId={selectedDocumentId}
                  initialContent={content}
                  contentFormat={selectedDocument?.content_format || "json"}
                  onSave={(val) => setContent(val)}
                />
              </div>
            ) : editorMode === "preview" ? (
              <div className="min-h-full max-w-[800px] mx-auto">
                {selectedDocument?.content_format === "latex" ? (
                  isPreviewCompiling ? (
                    <div className="flex flex-col items-center justify-center h-full min-h-[400px]">
                      <Loader2 className="w-8 h-8 animate-spin text-[#6E6E73] mb-4" />
                      <p className="text-[14px] text-[#6E6E73]">
                        Biên dịch LaTeX...
                      </p>
                    </div>
                  ) : previewPdfUrl ? (
                    <iframe
                      src={previewPdfUrl}
                      className="w-full h-[800px] rounded-[18px]"
                      title="Preview"
                    />
                  ) : (
                    <div className="text-center text-[#6E6E73] mt-12">
                      Chưa có dữ liệu PDF.
                    </div>
                  )
                ) : (
                  <div
                    className="prose prose-zinc max-w-none font-sans text-[16px] leading-relaxed text-[#1D1D1F]"
                    dangerouslySetInnerHTML={{
                      __html: (() => {
                        try {
                          const data = JSON.parse(content);
                          if (data.blocks) return safeParseEditorJs(data);
                          return content;
                        } catch (e) {
                          return content;
                        }
                      })(),
                    }}
                  />
                )}
              </div>
            ) : (
              <pre className="p-6 bg-[#F5F5F7] text-[#1D1D1F] text-[13px] font-mono whitespace-pre-wrap rounded-[18px]">
                {content || "Trống"}
              </pre>
            )}
          </div>
        </main>
      </div>

      <Modal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle>
            Xuất tài liệu
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="space-y-3">
          <button
            onClick={() => { setShowExportModal(false); handleExportPDF(); }}
            className="w-full text-left px-4 py-3 text-[15px] font-medium rounded-[10px] bg-white text-[#1D1D1F] hover:bg-[#E8E8ED] transition-colors flex items-center justify-between"
          >
            Định dạng PDF (.pdf)
          </button>
          {selectedDocument?.content_format !== "latex" && (
            <button
              onClick={() => { setShowExportModal(false); handleExportDOCX(); }}
              className="w-full text-left px-4 py-3 text-[15px] font-medium rounded-[10px] bg-white text-[#1D1D1F] hover:bg-[#E8E8ED] transition-colors flex items-center justify-between"
            >
              Định dạng Word (.docx)
            </button>
          )}
          <button
            onClick={() => { setShowExportModal(false); handleExportDRM(); }}
            className="w-full text-left px-4 py-3 text-[15px] font-medium rounded-[10px] bg-white text-[#1D1D1F] hover:bg-[#E8E8ED] transition-colors flex items-center justify-between"
          >
            Định dạng Bảo mật (.doclib)
          </button>
        </ModalContent>
      </Modal>
    </div>
  );
}

export default function AuthorStudioPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex items-center justify-center min-h-[80vh]">
          <Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" />
        </div>
      }
    >
      <StudioContent />
    </Suspense>
  );
}
