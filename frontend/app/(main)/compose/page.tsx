"use client";

import { useEffect, useMemo, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  getDocumentDraftAPI,
  getDocumentsAPI,
  getMyDocumentsAPI,
  saveDocumentDraftAPI,
  updateDocumentAPI,
  softDeleteDocumentAPI,
  restoreDocumentAPI,
  getTrashAPI,
  createDocumentAPI,
  lockDocumentAPI,
  unlockDocumentAPI,
  getFoldersAPI,
  createFolderAPI,
  deleteFolderAPI,
  toggleStarDocumentAPI,
  transferDocumentAPI,
  getDocumentAnalyticsAPI,
  getAcademicMetricsAPI,
  updateAuthorNoteAPI,
  updateDRMSettingsAPI,
  updateTagsAPI,
  schedulePublishAPI,
  updateChapterPaywallAPI,
  updateNSFWAPI,
  broadcastNotificationAPI,
} from "@/features/content/services/document.service";
import { compileDocumentAPI } from "@/features/editor/services/compilation.service";
import {
  exportDocumentPdfAPI,
  exportDocumentEpubAPI,
  exportDocumentDocxAPI,
} from "@/features/provision/services/export.service";
import {
  getCommentsByItemAPI,
  createCommentAPI,
  deleteCommentAPI,
} from "@/features/communication/services/comment.service";
import {
  inviteCollaboratorAPI,
  getCollaboratorsAPI,
  removeCollaboratorAPI,
} from "@/features/content/services/collaboration.service";
import {
  createCouponAPI,
  getCouponsAPI,
} from "@/features/finance/services/coupon.service";
import { publishDocumentAPI } from "@/features/content/services/publication.service";
import {
  getDocumentVersionsAPI,
  restoreVersionAPI,
} from "@/features/content/services/version.service";
import { ingestDocumentAPI } from "@/features/ai/services/rag.service";
import { requestWithdrawalAPI } from "@/features/finance/services/withdrawal.service";
import { getAuthorRevenueAPI as getRevenueAPI } from "@/features/finance/services/monetization.service";
import { API_URL } from "@/features/auth/services/authentication.service";
import {
  getWalletBalanceAPI as getWalletAPI,
  getDetailedHistoryAPI as getTransactionsAPI,
  getAuthorStatsAPI,
} from "@/features/finance/services/wallet.service";
import { useAuth } from "@/features/auth/contexts/Auth";
import { useToast } from "@/shared/contexts/Toast";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
import {
  FileText,
  Settings,
  BarChart3,
  Wallet,
  Save,
  Eye,
  Clock,
  Plus,
  Trash2,
  Sparkles,
  Loader2,
  ChevronRight,
  Database,
  ArrowUp,
  ArrowDown,
  X,
  RotateCcw,
  Banknote,
  Brain,
  Pencil,
  Lock,
  Unlock,
  Folder,
  ChevronDown,
  ChevronUp,
  Star,
  Download,
  MessageSquare,
  Users,
  Tag,
  StickyNote,
  Shield,
  Hash,
  CalendarClock,
  RadioTower,
  Indent,
  Outdent,
  CornerDownRight,
  AlertTriangle,
} from "lucide-react";
import dynamic from "next/dynamic";
const Editor = dynamic(() => import("@/features/editor/components/Editor"), {
  ssr: false,
});
import edjsHTML from "editorjs-html";
import { compileLatexPreviewAPI } from "@/features/editor/services/latex.service";

const customParsers = {
  alert: (block: any) =>
    `<div class="p-4 rounded-md border my-4 bg-zinc-50 border-zinc-200"><strong>${block.data.type || "Lưu ý"}</strong>: ${block.data.message}</div>`,
  table: (block: any) =>
    `<table class="w-full border-collapse border border-zinc-200 my-4">${(block.data.content || []).map((row: any) => `<tr>${row.map((cell: any) => `<td class="border border-zinc-200 p-2">${cell}</td>`).join("")}</tr>`).join("")}</table>`,
  toggle: (block: any) =>
    `<details class="p-4 border border-zinc-200 rounded-md my-4"><summary class="font-semibold cursor-pointer">${block.data.text}</summary><div class="mt-2 text-sm text-zinc-600">${block.data.items}</div></details>`,
  checklist: (block: any) =>
    `<ul class="list-none pl-0 my-4">${(block.data.items || []).map((item: any) => `<li class="flex items-start gap-2"><input type="checkbox" ${item.checked ? "checked" : ""} disabled /> <span>${item.text}</span></li>`).join("")}</ul>`,
  nestedChecklist: (block: any) =>
    `<ul class="list-none pl-0 my-4">${(block.data.items || []).map((item: any) => `<li class="flex items-start gap-2"><input type="checkbox" ${item.checked ? "checked" : ""} disabled /> <span>${item.content}</span></li>`).join("")}</ul>`,
  originalQuote: (block: any) =>
    `<blockquote class="border-l-4 border-zinc-300 pl-4 py-2 italic my-4 text-zinc-600">${block.data.text} <br/><cite class="text-sm font-semibold mt-2 block">- ${block.data.caption}</cite></blockquote>`,
  divider: () => `<hr class="my-6 border-zinc-200" />`,
  math: (block: any) =>
    `<div class="p-4 bg-zinc-50 font-mono text-sm my-4 overflow-x-auto border border-zinc-200 rounded-md">${block.data.math}</div>`,
  mermaid: (block: any) =>
    `<div class="p-4 border border-zinc-200 rounded-md my-4 text-sm text-zinc-500 italic">[Biểu đồ Mermaid không được hỗ trợ trong xem trước]</div>`,
  attaches: (block: any) =>
    `<div class="p-4 border border-zinc-200 rounded-md my-4 flex flex-col gap-1 text-sm bg-zinc-50"><span class="font-semibold text-zinc-900">${block.data.title || "Tập tin đính kèm"}</span><a href="${block.data.file?.url}" class="text-blue-600 hover:underline break-all">${block.data.file?.url}</a></div>`,
  personality: (block: any) =>
    `<div class="p-4 border border-zinc-200 rounded-md my-4 flex gap-4 items-center bg-zinc-50"><img src="${block.data.photo}" class="w-16 h-16 rounded-full object-cover" /><div><div class="font-semibold text-zinc-900">${block.data.name}</div><div class="text-sm text-zinc-600">${block.data.description}</div></div></div>`,
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
      if (!supportedTypes.includes(b.type)) {
        return {
          type: "paragraph",
          data: {
            text: `<div class="p-4 border border-red-200 bg-red-50 text-red-600 text-sm my-4 rounded-md"><strong>Khối chưa hỗ trợ xem trước:</strong> ${b.type}</div>`,
          },
        };
      }
      return b;
    }),
  };
  return edjsParser.parse(sanitizedData).join("");
};

type StudioDocument = {
  _id: string;
  title: string;
  slug: string;
  status?: string;
  content?: string;
  price_dl?: number;
  visibility?: string;
  chapters?: any[];
  cover_url?: string;
  is_locked?: boolean;
  folder_id?: string;
  is_starred?: boolean;
  drm_settings?: { disable_copy?: boolean; hide_from_search?: boolean };
  tags?: string[];
  publish_at?: string;
  scheduled_publish_at?: string;
  is_nsfw?: boolean;
};

type ViewMode = "edit" | "stats" | "config" | "versions" | "trash" | "comments";
type EditorMode = "edit" | "preview" | "raw";

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
    } catch (err: any) {
      console.warn("Could not extract plain text", err.message || err);
    }
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
      diffRows.push({
        type: "equal",
        a: lineA,
        b: lineB,
      });
    } else {
      diffRows.push({
        type: "diff",
        a: lineA,
        b: lineB,
      });
    }
  }

  return (
    <div className="flex flex-col font-mono text-xs divide-y divide-zinc-100 w-full overflow-x-auto">
      {diffRows.map((row, idx) => (
        <div
          key={idx}
          className="flex min-h-[28px] border-l-4 border-transparent  "
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

function StudioContent() {
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const { showToast } = useToast();
  const rawDocId = searchParams.get("tai-lieu");
  const docIdFromUrl = rawDocId && rawDocId !== "undefined" ? rawDocId : "";

  const [documents, setDocuments] = useState<StudioDocument[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState(
    docIdFromUrl || "",
  );
  const [viewMode, setViewMode] = useState<ViewMode>("edit");
  const [editorMode, setEditorMode] = useState<EditorMode>("edit");
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [statusMsg, setStatusMsg] = useState("Sẵn sàng");

  const [stats, setStats] = useState<any>(null);
  const [revenue, setRevenue] = useState<any>(null);

  const [versions, setVersions] = useState<any[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);

  const [trash, setTrash] = useState<any[]>([]);
  const [loadingTrash, setLoadingTrash] = useState(false);
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
  const [diffData, setDiffData] = useState<any>(null);
  const [isComparing, setIsComparing] = useState(false);

  const [showWithdrawalModal, setShowWithdrawalModal] = useState(false);
  const [withdrawalAmount, setWithdrawalAmount] = useState(0);
  const [bankInfo, setBankInfo] = useState({
    bank_name: "",
    account_number: "",
    account_name: "",
  });
  const [requestingWithdrawal, setRequestingWithdrawal] = useState(false);

  const [selectedChapterIndex, setSelectedChapterIndex] = useState<
    number | null
  >(null);
  const [confirmAction, setConfirmAction] = useState<{
    type: string;
    id: string;
    text: string;
  } | null>(null);
  const [showChapterModal, setShowChapterModal] = useState(false);
  const [newChapterTitle, setNewChapterTitle] = useState("");
  const [visible, setVisible] = useState(false);
  const [showCreateDocModal, setShowCreateDocModal] = useState(false);
  const [newDocTitle, setNewDocTitle] = useState("");
  const [newDocDescription, setNewDocDescription] = useState("");
  const [newDocPrice, setNewDocPrice] = useState(0);
  const [newDocFormat, setNewDocFormat] = useState("json");
  const [isCreatingDoc, setIsCreatingDoc] = useState(false);
  const [showEditChapterModal, setShowEditChapterModal] = useState(false);
  const [editingChapterIndex, setEditingChapterIndex] = useState<number | null>(
    null,
  );
  const [editingChapterTitle, setEditingChapterTitle] = useState("");
  const [lockPassword, setLockPassword] = useState("");
  const [unlockPassword, setUnlockPassword] = useState("");
  const [isLocking, setIsLocking] = useState(false);
  const [folders, setFolders] = useState<any[]>([]);
  const [expandedFolders, setExpandedFolders] = useState<
    Record<string, boolean>
  >({});
  const [showCreateFolderModal, setShowCreateFolderModal] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [transferUserId, setTransferUserId] = useState("");
  const [isTransferring, setIsTransferring] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [selectedAnalytics, setSelectedAnalytics] = useState<any>(null);
  const [selectedAcademic, setSelectedAcademic] = useState<any>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [comments, setComments] = useState<any[]>([]);
  const [loadingComments, setLoadingComments] = useState(false);
  const [replyContent, setReplyContent] = useState("");
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [collaborators, setCollaborators] = useState<any[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [loadingCollabs, setLoadingCollabs] = useState(false);
  const [coupons, setCoupons] = useState<any[]>([]);
  const [newCouponCode, setNewCouponCode] = useState("");
  const [newCouponDiscount, setNewCouponDiscount] = useState(10);
  const [newCouponQuantity, setNewCouponQuantity] = useState(50);
  const [authorNote, setAuthorNote] = useState("");
  const [savingNote, setSavingNote] = useState(false);
  const [drmCopy, setDrmCopy] = useState(false);
  const [drmSearch, setDrmSearch] = useState(false);
  const [savingDrm, setSavingDrm] = useState(false);
  const [docTags, setDocTags] = useState<string[]>([]);
  const [newTagInput, setNewTagInput] = useState("");
  const [scheduleDate, setScheduleDate] = useState("");
  const [isNsfw, setIsNsfw] = useState(false);
  const [broadcastMsg, setBroadcastMsg] = useState("");
  const [isBroadcasting, setIsBroadcasting] = useState(false);

  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);
  const [isPreviewCompiling, setIsPreviewCompiling] = useState(false);

  const selectedDocument = useMemo(
    () =>
      documents.find((b: any) => (b._id || b.id) === selectedDocumentId) ||
      null,
    [documents, selectedDocumentId],
  );

  const currentChapterContent = useMemo(() => {
    if (
      selectedChapterIndex !== null &&
      selectedDocument?.chapters?.[selectedChapterIndex]
    ) {
      return selectedDocument.chapters[selectedChapterIndex].content || "";
    }
    return content;
  }, [selectedChapterIndex, selectedDocument, content]);

  useEffect(() => {
    let currentUrl: string | null = null;

    if (
      editorMode === "preview" &&
      selectedDocument?.content_format === "latex"
    ) {
      setIsPreviewCompiling(true);
      compileLatexPreviewAPI(currentChapterContent, false)
        .then((blob) => {
          currentUrl = URL.createObjectURL(blob);
          setPreviewPdfUrl(currentUrl);
        })
        .catch((err: any) => {
          showToast(
            "Lỗi biên dịch: " + (err.message || "Lỗi không xác định"),
            "error",
          );
        })
        .finally(() => {
          setIsPreviewCompiling(false);
        });
    }

    return () => {
      if (currentUrl) {
        URL.revokeObjectURL(currentUrl);
      }
      setPreviewPdfUrl(null);
    };
  }, [
    editorMode,
    selectedDocument?.content_format,
    currentChapterContent,
    showToast,
  ]);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      let data;
      let foldersData = await getFoldersAPI().catch(() => ({ data: [] }));
      if (user?.role === "admin") {
        data = await getDocumentsAPI();
      } else {
        data = await getMyDocumentsAPI();
      }

      const list = data.data || data || [];
      const folderList = (foldersData as any).data || foldersData || [];
      setDocuments(list);
      setFolders(folderList);

      if (list.length > 0) {
        if (docIdFromUrl) {
          setSelectedDocumentId(docIdFromUrl);
        } else if (!selectedDocumentId) {
          setSelectedDocumentId(list[0]._id || list[0].id);
        }
      }
    } catch (err: any) {
      console.error(err.message || err);
      showToast("Lỗi tải danh sách tài liệu", "error");
    } finally {
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [docIdFromUrl, selectedDocumentId, user, showToast]);

  const loadDraft = useCallback(async () => {
    if (!selectedDocumentId) return;
    try {
      const data = await getDocumentDraftAPI(selectedDocumentId);
      const draft = data.data || data;
      setContent(draft?.content || "");
      setDocuments((prev) => {
        const existingIdx = prev.findIndex(
          (d) =>
            (d as any).id === selectedDocumentId ||
            (d as any)._id === selectedDocumentId,
        );
        if (existingIdx === -1) {
          return [draft, ...prev];
        } else {
          const newDocs = [...prev];
          newDocs[existingIdx] = draft;
          return newDocs;
        }
      });
      setStatusMsg("Đã tải xong");
    } catch (e: any) {
      setStatusMsg("Lỗi tải bản nháp");
      showToast("Không thể tải bản thảo", "error");
    }
  }, [selectedDocumentId, showToast]);

  const fetchStatsData = useCallback(async () => {
    try {
      const sRes = await getAuthorStatsAPI();
      const data = sRes.data || sRes;
      setStats(data);
      setRevenue(data);
    } catch (err: any) {
      showToast("Không thể tải số liệu thống kê", "error");
    }
  }, [showToast]);

  const fetchVersions = useCallback(async () => {
    if (!selectedDocumentId) return;
    setLoadingVersions(true);
    try {
      const data = await getDocumentVersionsAPI(selectedDocumentId);
      setVersions(data || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách phiên bản", "error");
    } finally {
      setLoadingVersions(false);
    }
  }, [selectedDocumentId, showToast]);

  const fetchTrash = useCallback(async () => {
    setLoadingTrash(true);
    try {
      const data = await getTrashAPI();
      setTrash(data.data || data || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách thùng rác", "error");
    } finally {
      setLoadingTrash(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  useEffect(() => {
    if (!selectedDocumentId) return;

    const timer = setTimeout(async () => {
      setStatusMsg("Đang lưu bản nháp");
      try {
        if (selectedChapterIndex !== null && selectedDocument) {
          const newChapters = [...(selectedDocument.chapters || [])];
          await updateDocumentAPI(selectedDocumentId, {
            chapters: newChapters,
          });
        } else if (content) {
          await saveDocumentDraftAPI(
            selectedDocumentId,
            content,
            selectedDocument?.content_format || "json",
          );
        }
        setStatusMsg("Đã lưu bản nháp");
        setTimeout(() => setStatusMsg("Sẵn sàng"), 2000);
      } catch (err) {
        setStatusMsg("Lỗi lưu bản thảo");
      }
    }, 5000);

    return () => clearTimeout(timer);
  }, [
    content,
    selectedChapterIndex,
    selectedDocumentId,
    selectedDocument?.chapters,
  ]);

  useEffect(() => {
    if (selectedDocumentId) {
      loadDraft();
      if (viewMode === "stats") fetchStatsData();
      if (viewMode === "versions") fetchVersions();
      if (viewMode === "comments") fetchComments();
      if (viewMode === "config") {
        fetchCollaborators();
        fetchCoupons();
        if (selectedDocument) {
          setDrmCopy(selectedDocument.drm_settings?.disable_copy || false);
          setDrmSearch(
            selectedDocument.drm_settings?.hide_from_search || false,
          );
          setDocTags(selectedDocument.tags || []);
          setIsNsfw(selectedDocument.is_nsfw || false);
        }
      }
      if (viewMode === "edit" && selectedDocument) {
        setScheduleDate(selectedDocument.publish_at || "");
      }
    } else {
      setContent("");
    }
    if (viewMode === "trash") fetchTrash();
  }, [
    selectedDocumentId,
    viewMode,
    loadDraft,
    fetchStatsData,
    fetchVersions,
    fetchTrash,
  ]);

  const handleRestoreVersion = async (versionId: string) => {
    setConfirmAction({
      type: "restore_version",
      id: versionId,
      text: "Bạn có chắc muốn khôi phục về phiên bản này? Nội dung hiện tại sẽ bị ghi đè.",
    });
  };

  const handleRestoreDocument = async (docId: string) => {
    try {
      await restoreDocumentAPI(docId);
      showToast("Đã khôi phục tài liệu thành công", "success");
      fetchTrash();
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Lỗi khôi phục tài liệu", "error");
    }
  };

  const handleSoftDelete = async (docId: string) => {
    setConfirmAction({
      type: "delete_doc",
      id: docId,
      text: "Bạn có chắc muốn chuyển tài liệu này vào thùng rác?",
    });
  };

  const executeConfirm = async () => {
    if (!confirmAction) return;
    try {
      if (confirmAction.type === "restore_version") {
        await restoreVersionAPI(confirmAction.id);
        showToast("Đã khôi phục phiên bản thành công", "success");
        loadDraft();
      } else if (confirmAction.type === "delete_doc") {
        await softDeleteDocumentAPI(confirmAction.id);
        showToast("Đã chuyển tài liệu vào thùng rác", "success");
        if (selectedDocumentId === confirmAction.id) setSelectedDocumentId("");
        fetchDocuments();
      } else if (confirmAction.type === "delete_chapter") {
        const chapterIdx = parseInt(confirmAction.id);
        const newChapters = [...(selectedDocument?.chapters || [])];
        newChapters.splice(chapterIdx, 1);
        await updateDocumentAPI(selectedDocumentId, { chapters: newChapters });
        showToast("Đã xóa chương thành công", "success");
        if (selectedChapterIndex === chapterIdx) setSelectedChapterIndex(null);
        loadDraft();
      } else if (confirmAction.type === "transfer") {
        await handleTransferOwnership();
      }
    } catch (e: any) {
      showToast(e.message || "Thao tác thất bại", "error");
    } finally {
      setConfirmAction(null);
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

  const handleIngestAI = async () => {
    if (!selectedDocumentId) return;
    setIsIngesting(true);
    setStatusMsg("Đang đồng bộ AI");
    try {
      await ingestDocumentAPI(selectedDocumentId);
      showToast("AI đã cập nhật nội dung mới", "success");
    } catch (e: any) {
      showToast(e.message || "Đồng bộ AI thất bại", "error");
    } finally {
      setIsIngesting(false);
      setStatusMsg("Sẵn sàng");
    }
  };

  const handleSave = async () => {
    if (!selectedDocumentId) return;
    setIsSaving(true);
    setStatusMsg("Đang lưu");
    try {
      await saveDocumentDraftAPI(
        selectedDocumentId,
        content,
        selectedDocument?.content_format || "json",
      );
      showToast("Đã lưu bản nháp thành công", "success");
    } catch (err: any) {
      console.error(err.message || err);
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
      showToast("Tài liệu đã được công bố thành công", "success");
      fetchDocuments();
    } catch (err: any) {
      console.error(err.message || err);
      showToast("Xuất bản thất bại", "error");
      setStatusMsg("Sẵn sàng");
    }
  };

  const handleExportPDF = async () => {
    if (!selectedDocumentId) return;
    setIsExporting(true);
    setStatusMsg("Đang tạo tệp PDF");
    try {
      const blob = await exportDocumentPdfAPI(selectedDocumentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${selectedDocument?.title || "ban-thao"}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showToast("Đã tải xuống thành công", "success");
    } catch (e: any) {
      showToast(e.message || "Xuất bản sao thất bại", "error");
    } finally {
      setIsExporting(false);
      setStatusMsg("Sẵn sàng");
    }
  };

  const handleExportEPUB = async () => {
    if (!selectedDocumentId) return;
    setIsExporting(true);
    setStatusMsg("Đang tạo tệp EPUB");
    try {
      const blob = await exportDocumentEpubAPI(selectedDocumentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${selectedDocument?.title || "ban-thao"}.epub`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showToast("Đã tải xuống thành công", "success");
    } catch (e: any) {
      showToast(e.message || "Xuất bản sao thất bại", "error");
    } finally {
      setIsExporting(false);
      setStatusMsg("Sẵn sàng");
    }
  };

  const handleExportDOCX = async () => {
    if (!selectedDocumentId) return;
    setIsExporting(true);
    setStatusMsg("Đang tạo tệp Word");
    try {
      const blob = await exportDocumentDocxAPI(selectedDocumentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${selectedDocument?.title || "ban-thao"}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showToast("Đã tải xuống thành công", "success");
    } catch (e: any) {
      showToast(e.message || "Xuất bản sao thất bại", "error");
    } finally {
      setIsExporting(false);
      setStatusMsg("Sẵn sàng");
    }
  };

  const handleViewDeepAnalytics = async (
    docId: string,
    e: React.MouseEvent,
  ) => {
    e.stopPropagation();
    setLoadingAnalytics(true);
    setShowAnalyticsModal(true);
    try {
      const [analyticsData, academicData] = await Promise.all([
        getDocumentAnalyticsAPI(docId).catch(() => null),
        getAcademicMetricsAPI(docId).catch(() => null),
      ]);
      setSelectedAnalytics(analyticsData?.data || analyticsData);
      setSelectedAcademic(academicData?.data || academicData);
    } catch (err: any) {
      showToast("Không thể tải chi tiết", "error");
    } finally {
      setLoadingAnalytics(false);
    }
  };

  const moveChapter = async (idx: number, direction: "up" | "down") => {
    if (!selectedDocument || !selectedDocument.chapters) return;
    const newChapters = [...selectedDocument.chapters];
    const targetIdx = direction === "up" ? idx - 1 : idx + 1;
    if (targetIdx < 0 || targetIdx >= newChapters.length) return;

    [newChapters[idx], newChapters[targetIdx]] = [
      newChapters[targetIdx],
      newChapters[idx],
    ];

    try {
      await updateDocumentAPI(selectedDocumentId, { chapters: newChapters });
      setStatusMsg("Đã thay đổi thứ tự");
      loadDraft();
    } catch (err: any) {
      showToast("Không thể thay đổi thứ tự chương", "error");
    }
  };

  const handleChangeChapterLevel = async (idx: number, delta: number) => {
    if (!selectedDocument || !selectedDocument.chapters) return;
    const newChapters = [...selectedDocument.chapters];
    const currentLevel = newChapters[idx].level || 0;

    let newLevel = Math.max(0, currentLevel + delta);
    if (newLevel === currentLevel) return;

    newChapters[idx] = { ...newChapters[idx], level: newLevel };

    try {
      await updateDocumentAPI(selectedDocumentId, { chapters: newChapters });
      loadDraft();
    } catch (err: any) {
      showToast("Không thể thay đổi cấp độ chương", "error");
    }
  };

  const addChapter = async () => {
    if (!newChapterTitle.trim()) return;
    const newChapter = {
      title: newChapterTitle,
      content: "Bắt đầu viết chương mới tại đây",
    };
    const newChapters = [...(selectedDocument?.chapters || []), newChapter];

    try {
      await updateDocumentAPI(selectedDocumentId, { chapters: newChapters });
      showToast("Đã thêm chương mới", "success");
      setNewChapterTitle("");
      setShowChapterModal(false);
      loadDraft();
    } catch (err: any) {
      showToast("Lỗi thêm chương mới", "error");
    }
  };

  const fetchComments = async () => {
    if (!selectedDocumentId) return;
    setLoadingComments(true);
    try {
      const data = await getCommentsByItemAPI(selectedDocumentId);
      setComments(data.data || data || []);
    } catch (err: any) {
      console.warn("Failed to load comments:", err.message || err);
      setComments([]);
    } finally {
      setLoadingComments(false);
    }
  };

  const handleReplyComment = async () => {
    if (!replyContent.trim() || !selectedDocumentId) return;
    try {
      await createCommentAPI({
        item_id: selectedDocumentId,
        item_type: "document",
        content: replyContent.trim(),
        parent_id: replyingTo,
      });
      showToast("Đã gửi phản hồi", "success");
      setReplyContent("");
      setReplyingTo(null);
      fetchComments();
    } catch (e: any) {
      showToast(e.message || "Gửi phản hồi thất bại", "error");
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    try {
      await deleteCommentAPI(commentId);
      showToast("Đã xóa bình luận", "success");
      fetchComments();
    } catch (e: any) {
      showToast(e.message || "Xóa bình luận thất bại", "error");
    }
  };

  const fetchCollaborators = async () => {
    if (!selectedDocumentId) return;
    setLoadingCollabs(true);
    try {
      const data = await getCollaboratorsAPI(selectedDocumentId);
      setCollaborators(data.data || data || []);
    } catch (err: any) {
      console.warn("Failed to load collabs:", err.message || err);
      setCollaborators([]);
    } finally {
      setLoadingCollabs(false);
    }
  };

  const handleInviteCollab = async () => {
    if (!inviteEmail.trim() || !selectedDocumentId) return;
    try {
      await inviteCollaboratorAPI(selectedDocumentId, inviteEmail.trim());
      showToast("Đã gửi lời mời cộng tác", "success");
      setInviteEmail("");
      fetchCollaborators();
    } catch (e: any) {
      showToast(e.message || "Gửi lời mời thất bại", "error");
    }
  };

  const handleRemoveCollab = async (collabId: string) => {
    try {
      await removeCollaboratorAPI(collabId);
      showToast("Đã xóa cộng tác viên", "success");
      fetchCollaborators();
    } catch (e: any) {
      showToast(e.message || "Xóa cộng tác viên thất bại", "error");
    }
  };

  const fetchCoupons = async () => {
    try {
      const data = await getCouponsAPI();
      setCoupons(data.data || data || []);
    } catch (err: any) {
      console.warn("Failed to load coupons:", err.message || err);
      setCoupons([]);
    }
  };

  const handleCreateCoupon = async () => {
    if (!newCouponCode.trim()) {
      showToast("Vui lòng nhập mã ưu đãi", "error");
      return;
    }
    try {
      await createCouponAPI({
        code: newCouponCode.trim(),
        discount_percent: newCouponDiscount,
        max_uses: newCouponQuantity,
        document_id: selectedDocumentId || undefined,
      });
      showToast("Đã tạo mã ưu đãi", "success");
      setNewCouponCode("");
      fetchCoupons();
    } catch (e: any) {
      showToast(e.message || "Tạo mã ưu đãi thất bại", "error");
    }
  };

  const handleSaveAuthorNote = async () => {
    if (selectedChapterIndex === null || !selectedDocumentId) return;
    setSavingNote(true);
    try {
      await updateAuthorNoteAPI(
        selectedDocumentId,
        selectedChapterIndex,
        authorNote,
      );
      showToast("Đã lưu ghi chú tác giả", "success");
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Lưu ghi chú thất bại", "error");
    } finally {
      setSavingNote(false);
    }
  };

  const handleSaveDRM = async () => {
    if (!selectedDocumentId) return;
    setSavingDrm(true);
    try {
      await updateDRMSettingsAPI(selectedDocumentId, {
        disable_copy: drmCopy,
        hide_from_search: drmSearch,
      });
      showToast("Đã cập nhật bảo vệ bản quyền", "success");
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Cập nhật DRM thất bại", "error");
    } finally {
      setSavingDrm(false);
    }
  };

  const handleAddTag = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && newTagInput.trim() && selectedDocumentId) {
      const tag = newTagInput.trim();
      if (!docTags.includes(tag)) {
        const newTags = [...docTags, tag];
        try {
          await updateTagsAPI(selectedDocumentId, newTags);
          setDocTags(newTags);
          setNewTagInput("");
          fetchDocuments();
        } catch (err: any) {
          showToast(err.message || "Thêm thẻ thất bại", "error");
        }
      }
    }
  };

  const handleRemoveTag = async (tagToRemove: string) => {
    if (!selectedDocumentId) return;
    const newTags = docTags.filter((t) => t !== tagToRemove);
    try {
      await updateTagsAPI(selectedDocumentId, newTags);
      setDocTags(newTags);
      fetchDocuments();
    } catch (err: any) {
      showToast(err.message || "Xóa thẻ thất bại", "error");
    }
  };

  const handleToggleNSFW = async () => {
    if (!selectedDocumentId) return;
    try {
      await updateNSFWAPI(selectedDocumentId, !isNsfw);
      setIsNsfw(!isNsfw);
      fetchDocuments();
      showToast("Đã cập nhật cảnh báo nội dung", "success");
    } catch (err: any) {
      showToast(err.message || "Cập nhật thất bại", "error");
    }
  };

  const handleSchedulePublish = async () => {
    if (!selectedDocumentId || !scheduleDate) return;
    try {
      await schedulePublishAPI(selectedDocumentId, scheduleDate);
      fetchDocuments();
      showToast("Đã lên lịch xuất bản", "success");
    } catch (err: any) {
      showToast(err.message || "Lên lịch thất bại", "error");
    }
  };

  const handleToggleChapterPaywall = async (
    e: React.MouseEvent,
    index: number,
    currentPremium: boolean,
  ) => {
    e.stopPropagation();
    if (!selectedDocumentId) return;
    try {
      await updateChapterPaywallAPI(selectedDocumentId, index, !currentPremium);
      loadDraft();
      showToast("Đã cập nhật khóa chương", "success");
    } catch (err: any) {
      showToast(err.message || "Cập nhật khóa thất bại", "error");
    }
  };

  const handleBroadcast = async () => {
    if (!selectedDocumentId || !broadcastMsg.trim()) return;
    setIsBroadcasting(true);
    try {
      await broadcastNotificationAPI(selectedDocumentId, broadcastMsg.trim());
      setBroadcastMsg("");
      showToast("Đã gửi thông báo đến độc giả", "success");
    } catch (err: any) {
      showToast(err.message || "Gửi thông báo thất bại", "error");
    } finally {
      setIsBroadcasting(false);
    }
  };

  const handleWithdrawal = async () => {
    if (withdrawalAmount <= 0) {
      showToast("Số tiền không hợp lệ", "error");
      return;
    }
    if (
      !bankInfo.bank_name ||
      !bankInfo.account_number ||
      !bankInfo.account_name
    ) {
      showToast("Vui lòng nhập đủ thông tin ngân hàng", "error");
      return;
    }

    setRequestingWithdrawal(true);
    try {
      await requestWithdrawalAPI(withdrawalAmount, bankInfo);
      showToast("Yêu cầu rút tiền đã được gửi", "success");
      setShowWithdrawalModal(false);
      fetchStatsData();
    } catch (e: any) {
      showToast(e.message || "Yêu cầu rút tiền thất bại", "error");
    } finally {
      setRequestingWithdrawal(false);
    }
  };

  const handleCreateDocument = async () => {
    if (!newDocTitle.trim()) {
      showToast("Vui lòng nhập tiêu đề tác phẩm", "error");
      return;
    }
    setIsCreatingDoc(true);
    try {
      const result = await createDocumentAPI({
        title: newDocTitle.trim(),
        description: newDocDescription.trim(),
        price_dl: newDocPrice,
        content_format: newDocFormat,
      });
      showToast("Đã tạo tác phẩm mới thành công", "success");
      setShowCreateDocModal(false);
      setNewDocTitle("");
      setNewDocDescription("");
      setNewDocPrice(0);
      setNewDocFormat("json");
      const newDoc = result?.data || result;
      if (newDoc) {
        setDocuments((prev) => {
          const exists = prev.find(
            (d) => (d._id || d.id) === (newDoc._id || newDoc.id),
          );
          if (exists) return prev;
          return [newDoc, ...prev];
        });
        setSelectedDocumentId(newDoc._id || newDoc.id);
      }
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Không thể tạo tác phẩm mới", "error");
    } finally {
      setIsCreatingDoc(false);
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) {
      showToast("Vui lòng nhập tên thư mục", "error");
      return;
    }
    try {
      await createFolderAPI(newFolderName.trim());
      showToast("Đã tạo thư mục", "success");
      setNewFolderName("");
      setShowCreateFolderModal(false);
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Không thể tạo thư mục", "error");
    }
  };

  const handleToggleStar = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await toggleStarDocumentAPI(id);
      setDocuments((prev) =>
        prev.map((doc) => {
          if ((doc._id || doc.id) === id) {
            return { ...doc, is_starred: !doc.is_starred };
          }
          return doc;
        }),
      );
    } catch (e: any) {
      showToast(e.message || "Không thể gắn sao tác phẩm", "error");
    }
  };

  const handleTransferOwnership = async () => {
    if (!transferUserId.trim() || !selectedDocumentId) {
      showToast("Vui lòng nhập mã ID người nhận", "error");
      return;
    }
    setIsTransferring(true);
    try {
      await transferDocumentAPI(selectedDocumentId, transferUserId.trim());
      showToast("Đã chuyển nhượng tác phẩm thành công", "success");
      setTransferUserId("");
      setSelectedDocumentId("");
      setViewMode("edit");
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Chuyển nhượng tác phẩm thất bại", "error");
    } finally {
      setIsTransferring(false);
    }
  };

  const handleDeleteChapter = (idx: number) => {
    setConfirmAction({
      type: "delete_chapter",
      id: String(idx),
      text: "Bạn có chắc muốn xóa chương này? Nội dung chương sẽ bị mất vĩnh viễn.",
    });
  };

  const handleEditChapter = (idx: number) => {
    if (!selectedDocument?.chapters?.[idx]) return;
    setEditingChapterIndex(idx);
    setEditingChapterTitle(selectedDocument.chapters[idx].title);
    setShowEditChapterModal(true);
  };

  const handleSaveChapterTitle = async () => {
    if (editingChapterIndex === null || !selectedDocument?.chapters) return;
    if (!editingChapterTitle.trim()) {
      showToast("Tiêu đề chương không được để trống", "error");
      return;
    }
    const newChapters = [...selectedDocument.chapters];
    newChapters[editingChapterIndex] = {
      ...newChapters[editingChapterIndex],
      title: editingChapterTitle.trim(),
    };
    try {
      await updateDocumentAPI(selectedDocumentId, { chapters: newChapters });
      showToast("Đã cập nhật tiêu đề chương", "success");
      setShowEditChapterModal(false);
      setEditingChapterIndex(null);
      setEditingChapterTitle("");
      loadDraft();
    } catch (e: any) {
      showToast(e.message || "Cập nhật tiêu đề thất bại", "error");
    }
  };

  const handleLockDocument = async () => {
    if (!selectedDocumentId || !lockPassword.trim()) {
      showToast("Vui lòng nhập mật mã bảo vệ", "error");
      return;
    }
    setIsLocking(true);
    try {
      await lockDocumentAPI(selectedDocumentId, lockPassword);
      showToast("Đã thiết lập bảo mật cho tác phẩm", "success");
      setLockPassword("");
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Thiết lập bảo mật thất bại", "error");
    } finally {
      setIsLocking(false);
    }
  };

  const handleUnlockDocument = async () => {
    if (!selectedDocumentId || !unlockPassword.trim()) {
      showToast("Vui lòng nhập mật mã để gỡ bảo mật", "error");
      return;
    }
    setIsLocking(true);
    try {
      await unlockDocumentAPI(selectedDocumentId, unlockPassword);
      showToast("Đã gỡ bảo mật cho tác phẩm", "success");
      setUnlockPassword("");
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Mật mã không chính xác", "error");
    } finally {
      setIsLocking(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[80vh]">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-300" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col gap-6 bg-[#fafafa] selection:bg-black selection:text-white relative font-sans">
      <Modal
        isOpen={!!confirmAction}
        onClose={() => setConfirmAction(null)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle>Xác nhận thao tác</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs font-medium text-zinc-500 leading-relaxed">
            {confirmAction?.text}
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setConfirmAction(null)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black  flex items-center justify-center"
          >
            Bỏ qua
          </button>
          <button
            onClick={executeConfirm}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black  flex items-center justify-center"
          >
            Xác nhận
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={showCreateFolderModal}
        onClose={() => setShowCreateFolderModal(false)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle>Tạo thư mục mới</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-2">
            <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
              Tên thư mục
            </label>
            <input
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="Nhập tên thư mục"
              className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black  rounded-none bg-white placeholder:text-zinc-400"
              autoFocus
            />
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setShowCreateFolderModal(false)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={handleCreateFolder}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black flex items-center justify-center"
          >
            Lưu
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={showAnalyticsModal}
        onClose={() => setShowAnalyticsModal(false)}
        className="max-w-2xl"
      >
        <ModalHeader>
          <ModalTitle>Phân tích & Chỉ số học thuật</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-6 max-h-[60vh] overflow-y-auto pr-2 no-scrollbar">
            {loadingAnalytics ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
              </div>
            ) : (
              <>
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
                    Tương tác độc giả
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Lượt xem
                      </p>
                      <p className="text-lg font-medium text-black">
                        {(selectedAnalytics?.views || 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Thời gian đọc TB
                      </p>
                      <p className="text-lg font-medium text-black">
                        {selectedAnalytics?.avg_read_time || "0 phút"}
                      </p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Lượt lưu
                      </p>
                      <p className="text-lg font-medium text-black">
                        {selectedAnalytics?.saves || 0}
                      </p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Bình luận
                      </p>
                      <p className="text-lg font-medium text-black">
                        {selectedAnalytics?.comments || 0}
                      </p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Đánh giá
                      </p>
                      <p className="text-lg font-medium text-black">
                        {selectedAnalytics?.reviews || 0} (
                        {selectedAnalytics?.avg_rating || 0}/5)
                      </p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Lượt mua
                      </p>
                      <p className="text-lg font-medium text-black">
                        {selectedAnalytics?.purchases || 0}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
                    Chỉ số học thuật
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Tổng số từ
                      </p>
                      <p className="text-lg font-medium text-black">
                        {(selectedAcademic?.word_count || 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Độ đọc hiểu
                      </p>
                      <p className="text-lg font-medium text-black">
                        {selectedAcademic?.readability_score || 0}/100
                      </p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Số câu
                      </p>
                      <p className="text-lg font-medium text-black">
                        {selectedAcademic?.sentence_count || 0}
                      </p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Độ dài câu TB
                      </p>
                      <p className="text-lg font-medium text-black">
                        {selectedAcademic?.avg_sentence_length || 0} từ
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </ModalContent>
      </Modal>

      <Modal
        isOpen={showChapterModal}
        onClose={() => setShowChapterModal(false)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle>Thêm chương mới</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-2">
            <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
              Tiêu đề chương
            </label>
            <input
              value={newChapterTitle}
              onChange={(e) => setNewChapterTitle(e.target.value)}
              placeholder="Nhập tiêu đề"
              className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black  rounded-none bg-white placeholder:text-zinc-400"
              autoFocus
            />
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setShowChapterModal(false)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black  flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={addChapter}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black  flex items-center justify-center"
          >
            Lưu chương
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={showWithdrawalModal}
        onClose={() => setShowWithdrawalModal(false)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle>Yêu cầu rút tiền</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                Số tiền rút (dl)
              </label>
              <input
                type="number"
                value={withdrawalAmount}
                onChange={(e) =>
                  setWithdrawalAmount(parseInt(e.target.value) || 0)
                }
                className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                Tên ngân hàng
              </label>
              <input
                value={bankInfo.bank_name}
                onChange={(e) =>
                  setBankInfo({ ...bankInfo, bank_name: e.target.value })
                }
                className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                Số tài khoản
              </label>
              <input
                value={bankInfo.account_number}
                onChange={(e) =>
                  setBankInfo({ ...bankInfo, account_number: e.target.value })
                }
                className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                Tên chủ tài khoản
              </label>
              <input
                value={bankInfo.account_name}
                onChange={(e) =>
                  setBankInfo({ ...bankInfo, account_name: e.target.value })
                }
                className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white"
              />
            </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setShowWithdrawalModal(false)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black  flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={handleWithdrawal}
            disabled={requestingWithdrawal}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black  flex items-center justify-center gap-2"
          >
            {requestingWithdrawal ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              "Gửi yêu cầu"
            )}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={showCreateDocModal}
        onClose={() => setShowCreateDocModal(false)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle>Khởi tạo tác phẩm mới</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                Tiêu đề tác phẩm
              </label>
              <input
                value={newDocTitle}
                onChange={(e) => setNewDocTitle(e.target.value)}
                placeholder="Nhập tiêu đề"
                className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black  rounded-none bg-white placeholder:text-zinc-400"
                autoFocus
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                Mô tả ngắn
              </label>
              <textarea
                value={newDocDescription}
                onChange={(e) => setNewDocDescription(e.target.value)}
                placeholder="Giới thiệu ngắn về tác phẩm"
                rows={3}
                className="w-full border border-zinc-200 px-3 py-2 text-xs font-medium focus:outline-none focus:border-black  rounded-none bg-white placeholder:text-zinc-400 resize-none"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                Giá bán (dl)
              </label>
              <input
                type="number"
                value={newDocPrice}
                onChange={(e) => setNewDocPrice(parseInt(e.target.value) || 0)}
                className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                Loại trình soạn thảo
              </label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="docFormat"
                    value="json"
                    checked={newDocFormat === "json"}
                    onChange={(e) => setNewDocFormat(e.target.value)}
                    className="accent-black w-4 h-4 cursor-pointer"
                  />
                  <span className="text-xs font-medium text-black">
                    Soạn thảo chuẩn (Khối)
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="docFormat"
                    value="latex"
                    checked={newDocFormat === "latex"}
                    onChange={(e) => setNewDocFormat(e.target.value)}
                    className="accent-black w-4 h-4 cursor-pointer"
                  />
                  <span className="text-xs font-medium text-black">
                    Soạn thảo LaTeX (Mã nguồn)
                  </span>
                </label>
              </div>
            </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setShowCreateDocModal(false)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black  flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={handleCreateDocument}
            disabled={isCreatingDoc}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black  flex items-center justify-center gap-2"
          >
            {isCreatingDoc ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              "Tạo tác phẩm"
            )}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={showEditChapterModal}
        onClose={() => setShowEditChapterModal(false)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle>Sửa tiêu đề chương</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-2">
            <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
              Tiêu đề mới
            </label>
            <input
              value={editingChapterTitle}
              onChange={(e) => setEditingChapterTitle(e.target.value)}
              placeholder="Nhập tiêu đề chương"
              className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black  rounded-none bg-white placeholder:text-zinc-400"
              autoFocus
            />
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setShowEditChapterModal(false)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black  flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={handleSaveChapterTitle}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black  flex items-center justify-center"
          >
            Lưu tiêu đề
          </button>
        </ModalFooter>
      </Modal>

      <div className="h-16 border border-zinc-200 px-6 flex items-center justify-between bg-white rounded-2xl shadow-sm shrink-0 z-30 animate-in fade-in slide-in-from-bottom-8 duration-300">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-black flex items-center justify-center rounded-none">
              <FileText className="w-4 h-4 text-white" />
            </div>
            <span className="text-base font-medium text-black truncate max-w-[200px]">
              {selectedDocument?.title || "Không tên"}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-zinc-500 hidden md:block">
            {statusMsg}
          </span>
          <div className="flex gap-3">
            <div className="relative group flex items-center h-9">
              <button
                disabled={!selectedDocumentId || isExporting}
                className="h-full px-4 border border-zinc-200 text-sm font-medium text-zinc-700 disabled:opacity-50 flex items-center gap-2 rounded-xl bg-white transition-colors hover:bg-zinc-50"
              >
                <Download className="w-3.5 h-3.5" /> Tải xuống
              </button>
              <div className="absolute top-full right-0 mt-1 w-32 bg-white border border-zinc-200 shadow-sm opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                <button
                  disabled={isExporting}
                  onClick={handleExportPDF}
                  className="w-full text-left px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
                >
                  Định dạng PDF
                </button>
                <button
                  onClick={handleExportEPUB}
                  className="w-full text-left px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50 border-t border-zinc-100"
                >
                  Định dạng EPUB
                </button>
                <button
                  onClick={handleExportDOCX}
                  className="w-full text-left px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50 border-t border-zinc-100"
                >
                  Định dạng Word
                </button>
              </div>
            </div>
            <div className="flex items-center bg-zinc-50 border border-zinc-200 rounded-xl h-9 px-2">
              <CalendarClock className="w-3.5 h-3.5 text-zinc-400 mr-2" />
              <input
                type="datetime-local"
                value={scheduleDate}
                onChange={(e) => setScheduleDate(e.target.value)}
                className="bg-transparent text-xs outline-none w-auto"
              />
              <button
                onClick={handleSchedulePublish}
                className="ml-2 text-xs font-semibold "
              >
                Hẹn giờ
              </button>
            </div>
            <button
              onClick={handleSave}
              disabled={!selectedDocumentId || isSaving}
              className="h-9 px-4 border border-zinc-200 text-sm font-medium text-zinc-700 disabled:opacity-50 flex items-center gap-2 rounded-xl bg-white ml-2 transition-colors hover:bg-zinc-50"
            >
              {isSaving ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Save className="w-3.5 h-3.5" />
              )}
              Lưu bản nháp
            </button>
            <button
              onClick={handlePublish}
              disabled={!selectedDocumentId}
              className="h-9 px-4 bg-black text-white text-sm font-medium disabled:opacity-50 rounded-xl transition-colors hover:bg-zinc-800"
            >
              Phát hành
            </button>
          </div>
        </div>
      </div>

      <div
        className="flex flex-1 overflow-hidden w-full animate-in fade-in slide-in-from-bottom-8 duration-300"
        style={{ animationDelay: "150ms", animationFillMode: "both" }}
      >
        <main className="flex-1 w-full flex flex-col bg-white overflow-hidden relative border border-zinc-200 rounded-2xl shadow-sm">
          <div className="h-12 border-b border-zinc-200 bg-white px-4 lg:px-6 flex items-center justify-between shrink-0">
            <div className="flex items-center h-full gap-4 lg:gap-6">
              {(["edit", "preview", "raw"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setEditorMode(m)}
                  className={`h-full text-sm font-medium border-b-2 flex items-center ${
                    editorMode === m
                      ? "border-black text-black"
                      : "border-transparent text-zinc-500"
                  }`}
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
          <div className="flex-1 overflow-y-auto no-scrollbar bg-white">
            <div className="w-full h-full animate-in fade-in ">
              {editorMode === "edit" ? (
                <div className="flex flex-col h-full">
                  {selectedChapterIndex !== null && (
                    <div className="border-b border-zinc-200 bg-zinc-50 px-8 py-4">
                      <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest flex items-center gap-2 mb-2">
                        <StickyNote className="w-3 h-3" /> Lời tác giả
                      </label>
                      <div className="flex gap-3">
                        <textarea
                          value={authorNote}
                          onChange={(e) => setAuthorNote(e.target.value)}
                          placeholder="Ghi chú dành cho độc giả ở đầu chương"
                          rows={2}
                          className="flex-1 border border-zinc-200 px-3 py-2 text-sm focus:outline-none focus:border-black  rounded-none bg-white placeholder:text-zinc-400 resize-none"
                        />
                        <button
                          onClick={handleSaveAuthorNote}
                          disabled={savingNote}
                          className="h-full px-4 bg-black text-white text-xs font-medium  disabled:opacity-50 rounded-none shrink-0"
                        >
                          {savingNote ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            "Lưu"
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                  <Editor
                    documentId={selectedDocumentId}
                    initialContent={currentChapterContent}
                    contentFormat={selectedDocument?.content_format || "json"}
                    onSave={(val) => {
                      if (selectedChapterIndex !== null && selectedDocument) {
                        const newChapters = [
                          ...(selectedDocument.chapters || []),
                        ];
                        newChapters[selectedChapterIndex].content = val;
                      } else {
                        setContent(val);
                      }
                    }}
                  />
                </div>
              ) : editorMode === "preview" ? (
                <div className="bg-white p-12 min-h-full">
                  {selectedDocument?.content_format === "latex" ? (
                    isPreviewCompiling ? (
                      <div className="flex flex-col items-center justify-center h-full text-zinc-500 min-h-[400px]">
                        <Loader2 className="w-8 h-8 animate-spin mb-4" />
                        <p className="text-sm">
                          Đang biên dịch mã nguồn LaTeX...
                        </p>
                      </div>
                    ) : previewPdfUrl ? (
                      <iframe
                        src={previewPdfUrl}
                        className="w-full h-[calc(100vh-200px)] min-h-[800px] border-0 rounded-md shadow-sm"
                        title="Preview PDF"
                      />
                    ) : (
                      <div className="text-zinc-500 text-center italic mt-12 min-h-[400px]">
                        Không có dữ liệu PDF để hiển thị.
                      </div>
                    )
                  ) : (
                    <div
                      className="prose prose-zinc max-w-none font-sans text-base leading-relaxed text-black"
                      dangerouslySetInnerHTML={{
                        __html: (() => {
                          try {
                            const data = JSON.parse(
                              currentChapterContent || content,
                            );
                            if (data.blocks) return safeParseEditorJs(data);
                            return currentChapterContent || content;
                          } catch (e) {
                            return currentChapterContent || content;
                          }
                        })(),
                      }}
                    />
                  )}
                </div>
              ) : (
                <pre className="p-8 bg-zinc-50 text-black text-sm font-mono leading-relaxed overflow-auto min-h-full">
                  {content || "Nội dung hiện đang trống"}
                </pre>
              )}
            </div>
          </div>
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
                  renderLineDiff(
                    diffData.version_a || "",
                    diffData.version_b || "",
                  )
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
                className="px-6 py-2 bg-black text-white text-xs font-medium border border-black "
              >
                Đóng cửa sổ
              </button>
            </ModalFooter>
          </Modal>
        </main>
      </div>
    </div>
  );
}

export default function AuthorStudioPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex items-center justify-center min-h-screen">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-300" />
        </div>
      }
    >
      <StudioContent />
    </Suspense>
  );
}
