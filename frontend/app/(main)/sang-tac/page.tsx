"use client";

import { useEffect, useMemo, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { getDocumentDraftAPI, getDocumentsAPI, getMyDocumentsAPI, saveDocumentDraftAPI, updateDocumentAPI, softDeleteDocumentAPI, restoreDocumentAPI, getTrashAPI, createDocumentAPI, lockDocumentAPI, unlockDocumentAPI, getFoldersAPI, createFolderAPI, deleteFolderAPI, toggleStarDocumentAPI, transferDocumentAPI, getDocumentAnalyticsAPI, getAcademicMetricsAPI, updateAuthorNoteAPI, updateDRMSettingsAPI, updateTagsAPI, schedulePublishAPI, updateChapterPaywallAPI, updateNSFWAPI, broadcastNotificationAPI } from "@/services/document.service";
import { compileDocumentAPI } from "@/services/compilation.service";
import { exportDocumentPdfAPI, exportDocumentEpubAPI, exportDocumentDocxAPI } from "@/services/export.service";
import { getCommentsByItemAPI, createCommentAPI, deleteCommentAPI } from "@/services/comment.service";
import { inviteCollaboratorAPI, getCollaboratorsAPI, removeCollaboratorAPI } from "@/services/collaboration.service";
import { createCouponAPI, getCouponsAPI } from "@/services/coupon.service";
import { publishDocumentAPI } from "@/services/publication.service";
import { getDocumentVersionsAPI, restoreVersionAPI } from "@/services/version.service";
import { ingestDocumentAPI } from "@/services/rag.service";
import { generateAICoverAPI } from "@/services/inference.service";
import { requestWithdrawalAPI } from "@/services/withdrawal.service";
import { getAuthorRevenueAPI as getRevenueAPI } from "@/services/monetization.service";
import { API_URL } from "@/services/authentication.service";
import { getWalletBalanceAPI as getWalletAPI, getDetailedHistoryAPI as getTransactionsAPI, getAuthorStatsAPI } from "@/services/wallet.service";
import { useAuth } from "@/contexts/Auth";
import { useToast } from "@/contexts/Toast";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";
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
} from "lucide-react";
import dynamic from "next/dynamic";
const Editor = dynamic(() => import("@/components/editor/Editor"), { ssr: false });
import edjsHTML from "editorjs-html";

const edjsParser = edjsHTML();

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
        return parsed.blocks.map((b: any) => b.data?.text || b.data?.code || b.data?.html || "").join("\n");
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
        <div key={idx} className="flex min-h-[28px] border-l-4 border-transparent  ">
          <div className={`flex-1 p-3 border-r border-zinc-200 whitespace-pre-wrap break-all ${row.type === "diff" && row.a ? "bg-red-50 text-red-800 border-l-4 border-red-500 font-semibold" : "text-zinc-600"}`}>
            {row.type === "diff" && row.a ? `- ${row.a}` : row.a}
          </div>
          <div className={`flex-1 p-3 whitespace-pre-wrap break-all ${row.type === "diff" && row.b ? "bg-green-50 text-green-800 border-l-4 border-green-500 font-semibold" : "text-zinc-600"}`}>
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
  const [selectedDocumentId, setSelectedDocumentId] = useState(docIdFromUrl || "");
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
  const [bankInfo, setBankInfo] = useState({ bank_name: "", account_number: "", account_name: "" });
  const [requestingWithdrawal, setRequestingWithdrawal] = useState(false);

  const [selectedChapterIndex, setSelectedChapterIndex] = useState<number | null>(null);
  const [confirmAction, setConfirmAction] = useState<{ type: string; id: string; text: string } | null>(null);
  const [showChapterModal, setShowChapterModal] = useState(false);
  const [newChapterTitle, setNewChapterTitle] = useState("");
  const [visible, setVisible] = useState(false);
  const [generatingCover, setGeneratingCover] = useState(false);
  const [showCreateDocModal, setShowCreateDocModal] = useState(false);
  const [newDocTitle, setNewDocTitle] = useState("");
  const [newDocDescription, setNewDocDescription] = useState("");
  const [newDocPrice, setNewDocPrice] = useState(0);
  const [isCreatingDoc, setIsCreatingDoc] = useState(false);
  const [showEditChapterModal, setShowEditChapterModal] = useState(false);
  const [editingChapterIndex, setEditingChapterIndex] = useState<number | null>(null);
  const [editingChapterTitle, setEditingChapterTitle] = useState("");
  const [lockPassword, setLockPassword] = useState("");
  const [unlockPassword, setUnlockPassword] = useState("");
  const [isLocking, setIsLocking] = useState(false);
  const [folders, setFolders] = useState<any[]>([]);
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({});
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

  const selectedDocument = useMemo(
    () => documents.find((b: any) => (b._id || b.id) === selectedDocumentId) || null,
    [documents, selectedDocumentId]
  );

  const currentChapterContent = useMemo(() => {
    if (selectedChapterIndex !== null && selectedDocument?.chapters?.[selectedChapterIndex]) {
      return selectedDocument.chapters[selectedChapterIndex].content || "";
    }
    return content;
  }, [selectedChapterIndex, selectedDocument, content]);

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
      setDocuments(prev => {
        const existingIdx = prev.findIndex(d => (d as any).id === selectedDocumentId || (d as any)._id === selectedDocumentId);
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
          await updateDocumentAPI(selectedDocumentId, { chapters: newChapters });
        } else if (content) {
          await saveDocumentDraftAPI(selectedDocumentId, content, "html");
        }
        setStatusMsg("Đã lưu bản nháp");
        setTimeout(() => setStatusMsg("Sẵn sàng"), 2000);
      } catch (err) {
        setStatusMsg("Lỗi lưu bản thảo");
      }
    }, 5000);

    return () => clearTimeout(timer);
  }, [content, selectedChapterIndex, selectedDocumentId, selectedDocument?.chapters]);

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
          setDrmSearch(selectedDocument.drm_settings?.hide_from_search || false);
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
  }, [selectedDocumentId, viewMode, loadDraft, fetchStatsData, fetchVersions, fetchTrash]);

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
    setConfirmAction({ type: "delete_doc", id: docId, text: "Bạn có chắc muốn chuyển tài liệu này vào thùng rác?" });
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
    setSelectedVersions(prev => 
      prev.includes(id) ? prev.filter(v => v !== id) : prev.length < 2 ? [...prev, id] : [prev[1], id]
    );
  };

  const handleCompareVersions = async () => {
    if (selectedVersions.length !== 2) return;
    setIsComparing(true);
    try {
      const { getVersionDiffAPI } = await import("@/services/editor.service");
      const data = await getVersionDiffAPI(selectedDocumentId, selectedVersions[0], selectedVersions[1]);
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
  
  const handleGenerateAICover = async () => {
    if (!selectedDocumentId) return;
    setGeneratingCover(true);
    setStatusMsg("Đang tạo ảnh bìa AI");
    try {
      await generateAICoverAPI(selectedDocumentId);
      showToast("Ảnh bìa AI đã được khởi tạo và cập nhật", "success");
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Tạo ảnh bìa thất bại", "error");
    } finally {
      setGeneratingCover(false);
      setStatusMsg("Sẵn sàng");
    }
  };

  const handleSave = async () => {
    if (!selectedDocumentId) return;
    setIsSaving(true);
    setStatusMsg("Đang lưu");
    try {
      await saveDocumentDraftAPI(selectedDocumentId, content, "html");
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

  const handleViewDeepAnalytics = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setLoadingAnalytics(true);
    setShowAnalyticsModal(true);
    try {
      const [analyticsData, academicData] = await Promise.all([
        getDocumentAnalyticsAPI(docId).catch(() => null),
        getAcademicMetricsAPI(docId).catch(() => null)
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

    [newChapters[idx], newChapters[targetIdx]] = [newChapters[targetIdx], newChapters[idx]];

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
    const newChapter = { title: newChapterTitle, content: "Bắt đầu viết chương mới tại đây" };
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
    }
    finally { setLoadingComments(false); }
  };

  const handleReplyComment = async () => {
    if (!replyContent.trim() || !selectedDocumentId) return;
    try {
      await createCommentAPI({
        item_id: selectedDocumentId,
        item_type: "document",
        content: replyContent.trim(),
        parent_id: replyingTo
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
    }
    finally { setLoadingCollabs(false); }
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
        document_id: selectedDocumentId || undefined
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
      await updateAuthorNoteAPI(selectedDocumentId, selectedChapterIndex, authorNote);
      showToast("Đã lưu ghi chú tác giả", "success");
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Lưu ghi chú thất bại", "error");
    } finally { setSavingNote(false); }
  };

  const handleSaveDRM = async () => {
    if (!selectedDocumentId) return;
    setSavingDrm(true);
    try {
      await updateDRMSettingsAPI(selectedDocumentId, { disable_copy: drmCopy, hide_from_search: drmSearch });
      showToast("Đã cập nhật bảo vệ bản quyền", "success");
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Cập nhật DRM thất bại", "error");
    } finally { setSavingDrm(false); }
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
        } catch (err: any) { showToast(err.message || "Thêm thẻ thất bại", "error"); }
      }
    }
  };

  const handleRemoveTag = async (tagToRemove: string) => {
    if (!selectedDocumentId) return;
    const newTags = docTags.filter(t => t !== tagToRemove);
    try {
      await updateTagsAPI(selectedDocumentId, newTags);
      setDocTags(newTags);
      fetchDocuments();
    } catch (err: any) { showToast(err.message || "Xóa thẻ thất bại", "error"); }
  };

  const handleToggleNSFW = async () => {
    if (!selectedDocumentId) return;
    try {
      await updateNSFWAPI(selectedDocumentId, !isNsfw);
      setIsNsfw(!isNsfw);
      fetchDocuments();
      showToast("Đã cập nhật cảnh báo nội dung", "success");
    } catch (err: any) { showToast(err.message || "Cập nhật thất bại", "error"); }
  };

  const handleSchedulePublish = async () => {
    if (!selectedDocumentId || !scheduleDate) return;
    try {
      await schedulePublishAPI(selectedDocumentId, scheduleDate);
      fetchDocuments();
      showToast("Đã lên lịch xuất bản", "success");
    } catch (err: any) { showToast(err.message || "Lên lịch thất bại", "error"); }
  };

  const handleToggleChapterPaywall = async (e: React.MouseEvent, index: number, currentPremium: boolean) => {
    e.stopPropagation();
    if (!selectedDocumentId) return;
    try {
      await updateChapterPaywallAPI(selectedDocumentId, index, !currentPremium);
      loadDraft();
      showToast("Đã cập nhật khóa chương", "success");
    } catch (err: any) { showToast(err.message || "Cập nhật khóa thất bại", "error"); }
  };

  const handleBroadcast = async () => {
    if (!selectedDocumentId || !broadcastMsg.trim()) return;
    setIsBroadcasting(true);
    try {
      await broadcastNotificationAPI(selectedDocumentId, broadcastMsg.trim());
      setBroadcastMsg("");
      showToast("Đã gửi thông báo đến độc giả", "success");
    } catch (err: any) { showToast(err.message || "Gửi thông báo thất bại", "error"); }
    finally { setIsBroadcasting(false); }
  };

  const handleWithdrawal = async () => {
    if (withdrawalAmount <= 0) {
      showToast("Số tiền không hợp lệ", "error");
      return;
    }
    if (!bankInfo.bank_name || !bankInfo.account_number || !bankInfo.account_name) {
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
      });
      showToast("Đã tạo tác phẩm mới thành công", "success");
      setShowCreateDocModal(false);
      setNewDocTitle("");
      setNewDocDescription("");
      setNewDocPrice(0);
      fetchDocuments();
      const newId = result?.data?._id || result?.data?.id || result?._id || result?.id;
      if (newId) setSelectedDocumentId(newId);
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
      setDocuments(prev => prev.map(doc => {
        if ((doc._id || doc.id) === id) {
          return { ...doc, is_starred: !doc.is_starred };
        }
        return doc;
      }));
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
    newChapters[editingChapterIndex] = { ...newChapters[editingChapterIndex], title: editingChapterTitle.trim() };
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
    <div className="flex-1 flex flex-col h-[calc(100vh-var(--navbar-height))] overflow-hidden bg-white selection:bg-black selection:text-white relative font-sans">
      <Modal isOpen={!!confirmAction} onClose={() => setConfirmAction(null)} className="max-w-sm">
        <ModalHeader>
          <ModalTitle>Xác nhận thao tác</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs font-medium text-zinc-500 leading-relaxed">{confirmAction?.text}</p>
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setConfirmAction(null)} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black  flex items-center justify-center">
            Bỏ qua
          </button>
          <button onClick={executeConfirm} className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black  flex items-center justify-center">
            Xác nhận
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={showCreateFolderModal} onClose={() => setShowCreateFolderModal(false)} className="max-w-sm">
        <ModalHeader>
          <ModalTitle>Tạo thư mục mới</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-2">
            <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Tên thư mục</label>
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
          <button onClick={() => setShowCreateFolderModal(false)} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black flex items-center justify-center">
            Hủy
          </button>
          <button onClick={handleCreateFolder} className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black flex items-center justify-center">
            Lưu
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={showAnalyticsModal} onClose={() => setShowAnalyticsModal(false)} className="max-w-2xl">
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
                  <h3 className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">Tương tác độc giả</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Lượt xem</p>
                      <p className="text-lg font-medium text-black">{(selectedAnalytics?.views || 0).toLocaleString()}</p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Thời gian đọc TB</p>
                      <p className="text-lg font-medium text-black">{selectedAnalytics?.avg_read_time || "0 phút"}</p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Lượt lưu</p>
                      <p className="text-lg font-medium text-black">{selectedAnalytics?.saves || 0}</p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Bình luận</p>
                      <p className="text-lg font-medium text-black">{selectedAnalytics?.comments || 0}</p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Đánh giá</p>
                      <p className="text-lg font-medium text-black">{selectedAnalytics?.reviews || 0} ({selectedAnalytics?.avg_rating || 0}/5)</p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Lượt mua</p>
                      <p className="text-lg font-medium text-black">{selectedAnalytics?.purchases || 0}</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">Chỉ số học thuật</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Tổng số từ</p>
                      <p className="text-lg font-medium text-black">{(selectedAcademic?.word_count || 0).toLocaleString()}</p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Độ đọc hiểu</p>
                      <p className="text-lg font-medium text-black">{selectedAcademic?.readability_score || 0}/100</p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Số câu</p>
                      <p className="text-lg font-medium text-black">{selectedAcademic?.sentence_count || 0}</p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-none space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Độ dài câu TB</p>
                      <p className="text-lg font-medium text-black">{selectedAcademic?.avg_sentence_length || 0} từ</p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </ModalContent>
      </Modal>

      <Modal isOpen={showChapterModal} onClose={() => setShowChapterModal(false)} className="max-w-sm">
        <ModalHeader>
          <ModalTitle>Thêm chương mới</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-2">
            <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Tiêu đề chương</label>
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
          <button onClick={() => setShowChapterModal(false)} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black  flex items-center justify-center">
            Hủy
          </button>
          <button onClick={addChapter} className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black  flex items-center justify-center">
            Lưu chương
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={showWithdrawalModal} onClose={() => setShowWithdrawalModal(false)} className="max-w-md">
        <ModalHeader>
          <ModalTitle>Yêu cầu rút tiền</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-4">
             <div className="space-y-1.5">
               <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Số tiền rút (dl)</label>
               <input
                 type="number"
                 value={withdrawalAmount}
                 onChange={(e) => setWithdrawalAmount(parseInt(e.target.value) || 0)}
                 className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white"
               />
             </div>
             <div className="space-y-1.5">
               <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Tên ngân hàng</label>
               <input
                 value={bankInfo.bank_name}
                 onChange={(e) => setBankInfo({ ...bankInfo, bank_name: e.target.value })}
                 className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white"
               />
             </div>
             <div className="space-y-1.5">
               <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Số tài khoản</label>
               <input
                 value={bankInfo.account_number}
                 onChange={(e) => setBankInfo({ ...bankInfo, account_number: e.target.value })}
                 className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white"
               />
             </div>
             <div className="space-y-1.5">
               <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Tên chủ tài khoản</label>
               <input
                 value={bankInfo.account_name}
                 onChange={(e) => setBankInfo({ ...bankInfo, account_name: e.target.value })}
                 className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white"
               />
             </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setShowWithdrawalModal(false)} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black  flex items-center justify-center">
            Hủy
          </button>
          <button 
            onClick={handleWithdrawal} 
            disabled={requestingWithdrawal}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black  flex items-center justify-center gap-2"
          >
            {requestingWithdrawal ? <Loader2 className="w-3 h-3 animate-spin" /> : "Gửi yêu cầu"}
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={showCreateDocModal} onClose={() => setShowCreateDocModal(false)} className="max-w-md">
        <ModalHeader>
          <ModalTitle>Khởi tạo tác phẩm mới</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Tiêu đề tác phẩm</label>
              <input
                value={newDocTitle}
                onChange={(e) => setNewDocTitle(e.target.value)}
                placeholder="Nhập tiêu đề"
                className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black  rounded-none bg-white placeholder:text-zinc-400"
                autoFocus
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Mô tả ngắn</label>
              <textarea
                value={newDocDescription}
                onChange={(e) => setNewDocDescription(e.target.value)}
                placeholder="Giới thiệu ngắn về tác phẩm"
                rows={3}
                className="w-full border border-zinc-200 px-3 py-2 text-xs font-medium focus:outline-none focus:border-black  rounded-none bg-white placeholder:text-zinc-400 resize-none"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Giá bán (dl)</label>
              <input
                type="number"
                value={newDocPrice}
                onChange={(e) => setNewDocPrice(parseInt(e.target.value) || 0)}
                className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white"
              />
            </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setShowCreateDocModal(false)} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black  flex items-center justify-center">
            Hủy
          </button>
          <button
            onClick={handleCreateDocument}
            disabled={isCreatingDoc}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black  flex items-center justify-center gap-2"
          >
            {isCreatingDoc ? <Loader2 className="w-3 h-3 animate-spin" /> : "Tạo tác phẩm"}
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={showEditChapterModal} onClose={() => setShowEditChapterModal(false)} className="max-w-sm">
        <ModalHeader>
          <ModalTitle>Sửa tiêu đề chương</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-2">
            <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Tiêu đề mới</label>
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
          <button onClick={() => setShowEditChapterModal(false)} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black  flex items-center justify-center">
            Hủy
          </button>
          <button onClick={handleSaveChapterTitle} className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black  flex items-center justify-center">
            Lưu tiêu đề
          </button>
        </ModalFooter>
      </Modal>

      <div 
        className="h-14 border-b border-zinc-200 px-6 flex items-center justify-between bg-white shrink-0 z-30  "
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
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
                className="h-full px-4 border border-zinc-200 text-sm font-medium text-zinc-700 disabled:opacity-50 flex items-center gap-2 rounded-none bg-white"
              >
                <Download className="w-3.5 h-3.5" /> Tải xuống
              </button>
              <div className="absolute top-full right-0 mt-1 w-32 bg-white border border-zinc-200 shadow-sm opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                <button
                  onClick={handleExportPDF}
                  className="w-full text-left px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
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
            <div className="flex items-center bg-zinc-50 border border-zinc-200 h-9 px-2">
              <CalendarClock className="w-3.5 h-3.5 text-zinc-400 mr-2" />
              <input
                type="datetime-local"
                value={scheduleDate}
                onChange={(e) => setScheduleDate(e.target.value)}
                className="bg-transparent text-xs outline-none w-auto"
              />
              <button onClick={handleSchedulePublish} className="ml-2 text-xs font-semibold ">Hẹn giờ</button>
            </div>
            <button
              onClick={handleSave}
              disabled={!selectedDocumentId || isSaving}
              className="h-9 px-4 border border-zinc-200 text-sm font-medium text-zinc-700  disabled:opacity-50 flex items-center gap-2 rounded-none bg-white ml-2"
            >
              {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              Lưu bản nháp
            </button>
            <button
              onClick={handlePublish}
              disabled={!selectedDocumentId}
              className="h-9 px-4 bg-black text-white text-sm font-medium  disabled:opacity-50 rounded-none"
            >
              Công bố tác phẩm
            </button>
          </div>
        </div>
      </div>

      <div 
        className="flex flex-1 overflow-hidden   delay-75"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <nav className="w-16 border-r border-zinc-200 flex flex-col items-center py-6 gap-4 shrink-0 bg-white">
          {[
            { mode: "edit", icon: FileText, label: "Soạn thảo" },
            { mode: "stats", icon: BarChart3, label: "Số liệu" },
            { mode: "config", icon: Settings, label: "Cấu hình" },
            { mode: "versions", icon: Clock, label: "Lịch sử" },
            { mode: "comments", icon: MessageSquare, label: "Bình luận" },
            { mode: "trash", icon: Trash2, label: "Thùng rác" },
          ].map((item) => (
            <button
              key={item.mode}
              onClick={() => setViewMode(item.mode as ViewMode)}
              className={`p-3  relative group rounded-none flex items-center justify-center w-12 h-12 ${
                viewMode === item.mode ? "bg-black text-white" : "text-zinc-500"
              }`}
              title={item.label}
            >
              <item.icon className="w-5 h-5" />
              <div className="absolute left-full ml-2 px-2 py-1 bg-black text-white text-xs font-medium whitespace-nowrap opacity-0 pointer-events-none  z-50 rounded-none">
                {item.label}
              </div>
            </button>
          ))}
        </nav>

        <aside className="w-64 border-r border-zinc-200 flex flex-col shrink-0 bg-white animate-in slide-in-from-left  p-6 space-y-12 overflow-y-auto no-scrollbar">
           {viewMode === "edit" ? (
             <>
                <div className="space-y-4">
                   <div className="flex justify-between items-end border-b border-zinc-200 pb-2">
                     <div className="text-sm font-semibold text-black">Cấu trúc nội dung</div>
                   </div>
                   <div className="flex flex-col gap-1">
                     {!selectedDocument?.chapters || selectedDocument.chapters.length === 0 ? (
                       <button 
                         onClick={() => setShowChapterModal(true)}
                         className="py-8 text-center border border-zinc-200 flex flex-col items-center justify-center gap-2 rounded-none bg-zinc-50 w-full"
                       >
                          <Plus className="w-4 h-4 text-zinc-400 " />
                          <p className="text-xs font-medium text-zinc-500 ">Chưa có chương</p>
                       </button>
                     ) : (
                       <>
                        {(() => {
                          const counters = [0, 0, 0, 0, 0, 0, 0];
                          return selectedDocument.chapters.map((ch: any, idx: number) => {
                            const lvl = ch.level || 0;
                            counters[lvl]++;
                            for (let i = lvl + 1; i < counters.length; i++) counters[i] = 0;
                            const numStr = counters.slice(0, lvl + 1).join(".");
                            
                            return (
                              <div
                                key={`chapter-${idx}`}
                                onClick={() => setSelectedChapterIndex(idx)}
                                className={`flex items-center justify-between px-3 py-2 text-sm font-medium border cursor-pointer rounded-none ${
                                  selectedChapterIndex === idx 
                                    ? "bg-black text-white border-black" 
                                    : "bg-white text-zinc-700 border-transparent"
                                }`}
                              >
                                <div className="flex items-center gap-2 min-w-0" style={{ paddingLeft: `${lvl * 16}px` }}>
                                  {lvl > 0 && <CornerDownRight className="w-3.5 h-3.5 text-zinc-300 shrink-0" />}
                                  <span className="text-xs font-medium min-w-[1rem] text-zinc-400 shrink-0">{numStr}</span>
                                  <span className="text-sm truncate">{ch.title}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <button onClick={(e) => handleToggleChapterPaywall(e, idx, ch.is_premium)} className={`p-0.5 rounded-none flex items-center justify-center ${ch.is_premium ? 'text-black' : 'text-zinc-300 '}`} title="Khóa chương (Trả phí)">
                                    <Lock className="w-3 h-3" />
                                  </button>
                                  
                                  <button 
                                    onClick={(e) => { e.stopPropagation(); handleChangeChapterLevel(idx, 1); }} 
                                    className="p-0.5 rounded-none flex items-center justify-center text-zinc-400" 
                                    title="Làm mục nhỏ"
                                  >
                                    <Indent className="w-3 h-3" />
                                  </button>
                                  
                                  <button 
                                    onClick={(e) => { e.stopPropagation(); handleChangeChapterLevel(idx, -1); }} 
                                    disabled={lvl === 0}
                                    className={`p-0.5 rounded-none flex items-center justify-center ${lvl === 0 ? 'text-zinc-200 cursor-not-allowed' : 'text-zinc-400'}`} 
                                    title="Làm mục chính"
                                  >
                                    <Outdent className="w-3 h-3" />
                                  </button>

                                  <button onClick={(e) => { e.stopPropagation(); handleEditChapter(idx); }} className="p-0.5 rounded-none flex items-center justify-center"><Pencil className="w-3 h-3 text-zinc-400" /></button>
                                  <button onClick={(e) => { e.stopPropagation(); moveChapter(idx, "up"); }} className="p-0.5 rounded-none flex items-center justify-center"><ArrowUp className="w-3 h-3 text-zinc-400" /></button>
                                  <button onClick={(e) => { e.stopPropagation(); moveChapter(idx, "down"); }} className="p-0.5 rounded-none flex items-center justify-center"><ArrowDown className="w-3 h-3 text-zinc-400" /></button>
                                  <button onClick={(e) => { e.stopPropagation(); handleDeleteChapter(idx); }} className="p-0.5 rounded-none flex items-center justify-center"><Trash2 className="w-3 h-3 text-zinc-400" /></button>
                                </div>
                              </div>
                            );
                          });
                        })()}
                        <button
                          onClick={() => setShowChapterModal(true)}
                          className="mt-2 flex items-center justify-center py-2.5 border border-dashed border-zinc-200 text-zinc-400  rounded-none"
                        >
                          <Plus className="w-3.5 h-3.5 mr-2" />
                          <span className="text-xs font-medium">Chương mới</span>
                        </button>
                      </>
                     )}
                  </div>
               </div>

               <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-zinc-200 pb-2">
                    <div className="text-sm font-semibold text-black">Tác phẩm khác</div>
                    <button onClick={() => setShowCreateFolderModal(true)} className="p-1">
                      <Folder className="w-3.5 h-3.5 text-zinc-400" />
                    </button>
                  </div>
                  <nav className="flex flex-col gap-1">

                    {folders.map(folder => {
                      const isExpanded = expandedFolders[folder._id || folder.id];
                      const folderDocs = documents.filter(d => d.folder_id === (folder._id || folder.id) && (d.id || d._id) !== selectedDocumentId);
                      
                      return (
                        <div key={folder._id || folder.id} className="flex flex-col">
                          <button
                            onClick={() => setExpandedFolders(p => ({ ...p, [folder._id || folder.id]: !isExpanded }))}
                            className="flex items-center justify-between px-2 py-1.5 text-sm font-medium border border-transparent bg-zinc-50 text-black rounded-none"
                          >
                            <div className="flex items-center gap-2">
                              <Folder className="w-3.5 h-3.5 text-zinc-500" />
                              <span className="truncate">{folder.name}</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span 
                                onClick={async (e) => {
                                  e.stopPropagation();
                                  if (confirm(`Bạn có chắc chắn muốn xóa thư mục "${folder.name}"? Các tác phẩm bên trong sẽ được đưa ra thư mục gốc.`)) {
                                    try {
                                      await deleteFolderAPI(folder._id || folder.id);
                                      showToast("Đã xóa thư mục", "success");
                                      fetchDocuments();
                                    } catch (err: any) {
                                      showToast(err.message || "Không thể xóa thư mục", "error");
                                    }
                                  }
                                }}
                                className="p-0.5 text-zinc-400"
                                title="Xóa thư mục"
                              >
                                <Trash2 className="w-3 h-3" />
                              </span>
                              {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-zinc-400" /> : <ChevronDown className="w-3.5 h-3.5 text-zinc-400" />}
                            </div>
                          </button>
                          {isExpanded && (
                            <div className="pl-4 flex flex-col gap-1 mt-1 border-l border-zinc-200 ml-2">
                              {folderDocs.length === 0 && <div className="px-2 py-1 text-xs text-zinc-400">Trống</div>}
                              {folderDocs.map(doc => (
                                <button
                                  key={doc._id || doc.id}
                                  onClick={() => setSelectedDocumentId(doc._id || doc.id)}
                                  className="flex items-center justify-between px-2 py-1.5 text-sm font-medium border border-transparent bg-white text-zinc-500 rounded-none"
                                >
                                  <div className="flex items-center gap-2 truncate">
                                    <span className="truncate">{doc.title}</span>
                                    {doc.scheduled_publish_at && <CalendarClock className="w-3.5 h-3.5 text-zinc-400 shrink-0" title={`Hẹn giờ: ${new Date(doc.scheduled_publish_at).toLocaleString('vi-VN')}`} />}
                                  </div>
                                  <div onClick={(e) => handleToggleStar(doc._id || doc.id, e)} className="p-0.5">
                                    <Star className={`w-3.5 h-3.5 ${doc.is_starred ? "fill-black text-black" : "text-zinc-300"}`} />
                                  </div>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}


                    {documents.filter((d: any) => !d.folder_id && (d.id || d._id) !== selectedDocumentId).map((doc: any, idx) => (
                      <button
                        key={doc._id || doc.id || `other-doc-${idx}`}
                        onClick={() => setSelectedDocumentId(doc._id || doc.id)}
                        className="flex items-center justify-between px-3 py-2 text-sm font-medium border border-transparent bg-white text-zinc-500 rounded-none"
                      >
                        <div className="flex items-center gap-2 truncate">
                          <span className="truncate">{doc.title}</span>
                          {doc.scheduled_publish_at && <CalendarClock className="w-3.5 h-3.5 text-zinc-400 shrink-0" title={`Hẹn giờ: ${new Date(doc.scheduled_publish_at).toLocaleString('vi-VN')}`} />}
                        </div>
                        <div onClick={(e) => handleToggleStar(doc._id || doc.id, e)} className="p-0.5 ">
                          <Star className={`w-3.5 h-3.5 ${doc.is_starred ? "fill-black text-black" : "text-zinc-300"}`} />
                        </div>
                      </button>
                    ))}
                  </nav>
               </div>
             </>
           ) : (
             <div className="space-y-4">
                <div className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
                  Danh sách tác phẩm
                </div>
                <nav className="flex flex-col gap-1">
                  {documents.map((doc: any, idx) => (
                    <button
                      key={doc._id || doc.id || `doc-list-${idx}`}
                      onClick={() => {
                        setSelectedDocumentId(doc._id || doc.id);
                        setViewMode("edit");
                      }}
                      className={`flex items-center justify-between px-3 py-2 text-sm font-medium border rounded-none   ${
                        selectedDocumentId === (doc._id || doc.id) 
                          ? "bg-zinc-100 text-black border-zinc-300" 
                          : "bg-white text-zinc-500 border-transparent"
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span className="truncate">{doc.title}</span>
                        {doc.scheduled_publish_at && <CalendarClock className="w-3.5 h-3.5 text-zinc-400 shrink-0" title={`Hẹn giờ: ${new Date(doc.scheduled_publish_at).toLocaleString('vi-VN')}`} />}
                      </div>
                      {selectedDocumentId === (doc._id || doc.id) && <ChevronRight className="w-4 h-4" />}
                    </button>
                  ))}
                </nav>
             </div>
           )}
        </aside>

        <main className="flex-1 bg-white overflow-hidden relative border-l border-zinc-200">
           {viewMode === "edit" && (
             <div className="h-full flex flex-col animate-in fade-in ">
                <div className="h-12 border-b border-zinc-200 bg-white px-6 flex items-center justify-between shrink-0">
                   <div className="flex h-full gap-6">
                      {(["edit", "preview", "raw"] as const).map((m) => (
                        <button
                          key={m}
                          onClick={() => setEditorMode(m)}
                          className={`h-full text-sm font-medium  border-b-2 flex items-center ${
                            editorMode === m ? "border-black text-black" : "border-transparent text-zinc-500"
                          }`}
                        >
                          {m === "edit" ? "Soạn thảo" : m === "preview" ? "Xem trước" : "Mã nguồn"}
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
                                  {savingNote ? <Loader2 className="w-3 h-3 animate-spin" /> : "Lưu"}
                                </button>
                              </div>
                            </div>
                          )}
                          <Editor 
                            documentId={selectedDocumentId}
                            initialContent={currentChapterContent} 
                          onSave={(val) => {
                            if (selectedChapterIndex !== null && selectedDocument) {
                              const newChapters = [...(selectedDocument.chapters || [])];
                              newChapters[selectedChapterIndex].content = val;
                            } else {
                              setContent(val);
                            }
                          }} 
                        />
                        </div>
                      ) : editorMode === "preview" ? (
                        <div className="bg-white p-12 border border-zinc-200 rounded-none">
                          <div 
                            className="prose prose-zinc max-w-none font-sans text-base leading-relaxed text-black" 
                            dangerouslySetInnerHTML={{ 
                              __html: (() => {
                                try {
                                  const data = JSON.parse(content);
                                  if (data.blocks) return edjsParser.parse(data).join("");
                                  return content;
                                } catch (e) {
                                  return content;
                                }
                              })()
                            }} 
                          />
                        </div>
                      ) : (
                        <pre className="p-8 bg-zinc-50 border border-zinc-200 text-black text-sm font-mono leading-relaxed overflow-auto min-h-[100vh] rounded-none">
                          {content || "Nội dung hiện đang trống"}
                        </pre>
                      )}
                   </div>
                </div>
             </div>
           )}

           {viewMode === "stats" && (
             <div className="h-full overflow-y-auto p-8 md:p-12 animate-in fade-in  no-scrollbar">
                <div className="max-w-5xl mx-auto space-y-12">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                      { label: "Tổng lượt xem", val: stats?.total_views || 0, icon: Eye },
                      { label: "Kinh nghiệm", val: stats?.total_points || 0, icon: Database },
                      { label: "Doanh thu (dl)", val: revenue?.available_balance || 0, icon: Wallet },
                    ].map((s, i) => (
                      <div key={i} className="bg-white p-6 border border-zinc-200 flex flex-col justify-between h-32 rounded-none">
                        <div className="flex justify-between items-start">
                          <span className="text-sm font-medium text-zinc-500">{s.label}</span>
                          <s.icon className="w-4 h-4 text-zinc-400" />
                        </div>
                        <h4 className="text-3xl font-medium text-black">{s.val.toLocaleString()}</h4>
                      </div>
                    ))}
                  </div>

                  <div className="bg-zinc-50 border border-zinc-200 p-6 flex flex-col md:flex-row items-center gap-4">
                    <div className="flex-1 space-y-1 w-full">
                      <h3 className="text-base font-medium text-black flex items-center gap-2"><RadioTower className="w-4 h-4 text-black" /> Thông báo tới độc giả (Broadcast)</h3>
                      <p className="text-xs text-zinc-500">Gửi thông báo đẩy đến tất cả những người theo dõi tác phẩm này.</p>
                    </div>
                    <div className="flex w-full md:w-auto gap-2">
                      <input type="text" value={broadcastMsg} onChange={(e) => setBroadcastMsg(e.target.value)} placeholder="Nội dung thông báo (VD: Đã cập nhật chương mới!)" className="flex-1 md:w-64 h-10 px-3 text-xs border border-zinc-200 outline-none focus:border-black" />
                      <button onClick={handleBroadcast} disabled={isBroadcasting || !selectedDocumentId || !broadcastMsg.trim()} className="h-10 px-4 bg-black text-white text-xs font-medium flex items-center gap-2 disabled:opacity-50 whitespace-nowrap">
                        {isBroadcasting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Gửi thông báo"}
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                     <button onClick={() => setShowCreateDocModal(true)} className="p-6 border border-zinc-200 bg-white rounded-none flex flex-col items-center justify-center gap-3 h-24">
                       <Plus className="w-5 h-5 text-zinc-400" />
                       <span className="text-sm font-medium text-zinc-700">Tạo tài liệu</span>
                     </button>
                     <button onClick={handleIngestAI} disabled={isIngesting || !selectedDocumentId} className="p-6 border border-zinc-200 bg-white rounded-none flex flex-col items-center justify-center gap-3 h-24 disabled:opacity-50">
                       {isIngesting ? <Loader2 className="w-5 h-5 text-zinc-400 animate-spin" /> : <Brain className="w-5 h-5 text-zinc-400" />}
                       <span className="text-sm font-medium text-zinc-700">Đồng bộ AI</span>
                     </button>
                     <button onClick={() => setViewMode("config")} className="p-6 border border-zinc-200 bg-white rounded-none flex flex-col items-center justify-center gap-3 h-24">
                       <Settings className="w-5 h-5 text-zinc-400" />
                       <span className="text-sm font-medium text-zinc-700">Cấu hình tác phẩm</span>
                     </button>
                  </div>

                  <div className="bg-white border border-zinc-200 rounded-none">
                    <div className="p-6 border-b border-zinc-200 flex justify-between items-center">
                      <h3 className="text-base font-medium text-black">Tác phẩm gần đây</h3>
                      <button 
                        onClick={() => setShowWithdrawalModal(true)}
                        className="h-9 px-4 bg-black text-white text-sm font-medium  rounded-none flex items-center gap-2"
                      >
                        <Banknote className="w-4 h-4" /> Rút tiền doanh thu
                      </button>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-sm">
                        <thead>
                          <tr className="border-b border-zinc-200 text-zinc-500 font-medium">
                            <th className="px-6 py-4 font-medium">Tiêu đề</th>
                            <th className="px-6 py-4 font-medium">Lượt tương tác</th>
                            <th className="px-6 py-4 font-medium">Xếp hạng</th>
                            <th className="px-6 py-4 font-medium text-right">Hành động</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-200">
                          {(stats?.documents || []).map((doc: any, idx: number) => (
                            <tr key={doc.id || `stats-doc-${idx}`} onClick={(e) => handleViewDeepAnalytics(doc.id, e)} className="cursor-pointer">
                              <td className="px-6 py-4 font-medium text-black">{doc.title}</td>
                              <td className="px-6 py-4 text-zinc-600">{doc.views.toLocaleString()}</td>
                              <td className="px-6 py-4">
                                <div className="flex items-center gap-2">
                                  <span className="text-zinc-600 font-medium">{doc.rating.toFixed(1)}</span>
                                </div>
                              </td>
                              <td className="px-6 py-4 text-right"><ChevronRight className="w-4 h-4 ml-auto text-zinc-400 " /></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                  
                  <div className="bg-white border border-zinc-200 rounded-none mt-6">
                    <div className="p-6 border-b border-zinc-200 flex justify-between items-center">
                      <div className="space-y-1">
                        <h3 className="text-base font-medium text-black flex items-center gap-2"><Tag className="w-4 h-4" /> Mã ưu đãi (Coupons)</h3>
                        <p className="text-xs font-medium text-zinc-500">Tạo mã ưu đãi để thúc đẩy doanh thu cho tài liệu có phí.</p>
                      </div>
                    </div>
                    <div className="p-6 border-b border-zinc-200 bg-zinc-50 flex gap-4">
                      <input type="text" value={newCouponCode} onChange={(e) => setNewCouponCode(e.target.value)} placeholder="Mã (VD: TET2025)" className="w-32 h-9 px-3 text-xs border border-zinc-200 uppercase outline-none focus:border-black" />
                      <input type="number" value={newCouponDiscount} onChange={(e) => setNewCouponDiscount(Number(e.target.value))} placeholder="% giảm" className="w-24 h-9 px-3 text-xs border border-zinc-200 outline-none focus:border-black" min={1} max={100} />
                      <input type="number" value={newCouponQuantity} onChange={(e) => setNewCouponQuantity(Number(e.target.value))} placeholder="Số lượng" className="w-24 h-9 px-3 text-xs border border-zinc-200 outline-none focus:border-black" min={1} />
                      <button onClick={handleCreateCoupon} className="h-9 px-4 bg-black text-white text-xs font-medium flex items-center gap-2">Tạo mã</button>
                    </div>
                    <div className="p-6">
                      {coupons.length === 0 ? (
                        <p className="text-xs text-zinc-500 italic">Chưa có mã ưu đãi nào.</p>
                      ) : (
                        <div className="flex flex-wrap gap-3">
                          {coupons.map((c: any) => (
                            <div key={c.id || c._id} className="border border-zinc-200 px-3 py-2 flex items-center gap-3 bg-white">
                              <span className="font-bold text-xs text-black">{c.code}</span>
                              <span className="text-[10px] bg-black text-white px-1.5 py-0.5 font-bold">-{c.discount_percent}%</span>
                              <span className="text-[10px] text-zinc-500 font-medium">Lượt: {c.used_count || 0}/{c.max_uses}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
             </div>
           )}

           {viewMode === "config" && (
             <div className="h-full overflow-y-auto p-8 md:p-12 animate-in fade-in  no-scrollbar">
                <div className="max-w-3xl mx-auto bg-white border border-zinc-200 p-10 space-y-10 rounded-none">
                  

                  <div className="space-y-4">
                    <h2 className="text-xl font-medium text-black flex items-center gap-2"><Hash className="w-5 h-5" /> Phân loại & Thẻ (Tags)</h2>
                    <p className="text-sm font-medium text-zinc-500 leading-relaxed">
                      Sử dụng các thẻ để giúp thuật toán và công cụ tìm kiếm phân loại tác phẩm của bạn tốt hơn.
                    </p>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {docTags.map(tag => (
                        <span key={tag} className="flex items-center gap-1 border border-zinc-200 bg-zinc-50 px-2 py-1 text-xs font-semibold text-black">
                          {tag}
                          <button onClick={() => handleRemoveTag(tag)} className="text-zinc-400 "><X className="w-3 h-3" /></button>
                        </span>
                      ))}
                    </div>
                    <input
                      type="text"
                      value={newTagInput}
                      onChange={(e) => setNewTagInput(e.target.value)}
                      onKeyDown={handleAddTag}
                      placeholder="Nhập tên thẻ và nhấn Enter (VD: TienHiep, HuyenHuyen)"
                      className="w-full max-w-md h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white placeholder:text-zinc-400"
                    />
                  </div>
                  <div className="h-px bg-zinc-200" />


                  <div className="space-y-4">
                    <h2 className="text-xl font-medium text-black flex items-center gap-2"><Folder className="w-5 h-5" /> Thư mục làm việc (Workspace Folder)</h2>
                    <p className="text-sm font-medium text-zinc-500 leading-relaxed">
                      Di chuyển tác phẩm này vào thư mục làm việc để quản lý tài liệu tốt hơn.
                    </p>
                    <div className="flex gap-3 max-w-md">
                      <select
                        value={selectedDocument?.folder_id || ""}
                        onChange={async (e) => {
                          const fId = e.target.value;
                          try {
                            await updateDocumentAPI(selectedDocumentId, { folder_id: fId || null });
                            showToast("Đã di chuyển tác phẩm thành công", "success");
                            fetchDocuments();
                          } catch (err: any) {
                            showToast(err.message || "Không thể di chuyển tác phẩm", "error");
                          }
                        }}
                        className="flex-1 h-10 border border-zinc-200 px-3 text-xs font-semibold rounded-none outline-none bg-white text-black focus:border-black"
                      >
                        <option value="">(Thư mục gốc)</option>
                        {folders.map(f => (
                          <option key={f._id || f.id} value={f._id || f.id}>{f.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="h-px bg-zinc-200" />

                  <div className="space-y-4">
                    <h2 className="text-xl font-medium text-black">Trí tuệ nhân tạo</h2>
                    <p className="text-sm font-medium text-zinc-500 leading-relaxed">
                      Đồng bộ nội dung của bạn với hệ thống RAG để cho phép AI thấu hiểu và hỗ trợ độc giả tốt hơn.
                    </p>
                    <button
                      onClick={handleIngestAI}
                      disabled={isIngesting || !selectedDocumentId}
                      className="h-10 bg-black text-white px-6 text-sm font-medium  flex items-center gap-2 rounded-none disabled:opacity-50 w-fit"
                    >
                      {isIngesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
                      Kích hoạt đồng bộ dữ liệu AI
                    </button>
                  </div>
                  <div className="h-px bg-zinc-200" />
                  
                  <div className="space-y-6">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
                      <div className="space-y-3">
                        <h2 className="text-xl font-medium text-black">Ảnh bìa nghệ thuật</h2>
                        <p className="text-sm font-medium text-zinc-500 leading-relaxed max-w-md">
                          Hệ thống sẽ phân tích nội dung để tạo ra một ảnh bìa nghệ thuật phản ánh đúng linh hồn của tác phẩm.
                        </p>
                      </div>
                      <button
                        onClick={handleGenerateAICover}
                        disabled={generatingCover || !selectedDocumentId}
                        className="h-10 border border-zinc-200 text-black px-6 text-sm font-medium  flex items-center gap-2 rounded-none disabled:opacity-50 whitespace-nowrap"
                      >
                        {generatingCover ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                        {selectedDocument?.cover_url ? "Tái tạo ảnh bìa" : "Tạo ảnh bìa AI"}
                      </button>
                    </div>

                    <div className="relative max-w-[280px] rounded-none overflow-hidden">
                       <div className="aspect-[3/4] bg-zinc-50 border border-zinc-200 relative overflow-hidden  rounded-none flex items-center justify-center">
                          {selectedDocument?.cover_url ? (
                            <img
                              src={selectedDocument.cover_url.startsWith("http") ? selectedDocument.cover_url : `${API_URL}/storage/${selectedDocument.cover_url}`}
                              alt={selectedDocument.title}
                              className="w-full h-full object-cover grayscale  "
                            />
                          ) : (
                            <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center gap-3">
                              <Sparkles className="w-6 h-6 text-zinc-400" />
                              <p className="text-sm font-medium text-zinc-500">Chưa có ảnh bìa</p>
                            </div>
                          )}
                       </div>
                       
                       {selectedDocument?.cover_url && (
                         <div className="absolute top-3 right-3 bg-white border border-zinc-200 px-2 py-1 rounded-none">
                            <p className="text-xs font-medium text-zinc-700">Ảnh AI</p>
                         </div>
                       )}
                    </div>
                  </div>
                  <div className="h-px bg-zinc-200" />
                  <div className="space-y-6">
                    <div className="space-y-3">
                      <h2 className="text-xl font-medium text-black">Bảo mật tác phẩm</h2>
                      <p className="text-sm font-medium text-zinc-500 leading-relaxed max-w-md">
                        Thiết lập mật mã để bảo vệ bản thảo của bạn. Người đọc cần nhập đúng mật mã mới có thể truy cập nội dung.
                      </p>
                    </div>
                    {selectedDocument?.is_locked ? (
                      <div className="space-y-4">
                        <div className="flex items-center gap-3 px-4 py-3 bg-zinc-50 border border-zinc-200 rounded-none">
                          <Lock className="w-4 h-4 text-zinc-500 shrink-0" />
                          <span className="text-sm font-medium text-black">Đã khóa bảo mật</span>
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Nhập mật mã để gỡ bảo mật</label>
                          <input
                            type="password"
                            value={unlockPassword}
                            onChange={(e) => setUnlockPassword(e.target.value)}
                            placeholder="Mật mã hiện tại"
                            className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white placeholder:text-zinc-400"
                          />
                        </div>
                        <button
                          onClick={handleUnlockDocument}
                          disabled={isLocking || !selectedDocumentId}
                          className="h-10 border border-zinc-200 text-black px-6 text-sm font-medium flex items-center gap-2 rounded-none disabled:opacity-50 w-fit"
                        >
                          {isLocking ? <Loader2 className="w-4 h-4 animate-spin" /> : <Unlock className="w-4 h-4" />}
                          Gỡ bảo mật
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="flex items-center gap-3 px-4 py-3 bg-zinc-50 border border-zinc-200 rounded-none">
                          <Unlock className="w-4 h-4 text-zinc-500 shrink-0" />
                          <span className="text-sm font-medium text-zinc-500">Chưa thiết lập bảo mật</span>
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Mật mã bảo vệ mới</label>
                          <input
                            type="password"
                            value={lockPassword}
                            onChange={(e) => setLockPassword(e.target.value)}
                            placeholder="Nhập mật mã"
                            className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white placeholder:text-zinc-400"
                          />
                        </div>
                        <button
                          onClick={handleLockDocument}
                          disabled={isLocking || !selectedDocumentId}
                          className="h-10 bg-black text-white px-6 text-sm font-medium flex items-center gap-2 rounded-none disabled:opacity-50 w-fit"
                        >
                          {isLocking ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                          Thiết lập bảo mật
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="h-px bg-zinc-200" />
                  <div className="space-y-6">
                    <div className="space-y-3">
                      <h2 className="text-xl font-medium text-black">Bàn giao tác phẩm</h2>
                      <p className="text-sm font-medium text-zinc-500 leading-relaxed max-w-md">
                        Bạn sẽ mất toàn quyền kiểm soát tác phẩm này sau khi chuyển nhượng. Hãy đảm bảo nhập đúng mã ID của người nhận.
                      </p>
                    </div>
                    <div className="space-y-4">
                      <div className="space-y-1.5">
                        <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Mã ID người nhận</label>
                        <input
                          type="text"
                          value={transferUserId}
                          onChange={(e) => setTransferUserId(e.target.value)}
                          placeholder="Ví dụ: 60a1b2c3d4e5f6g7h8i9j0k"
                          className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white placeholder:text-zinc-400"
                        />
                      </div>
                      <button
                        onClick={() => setConfirmAction({
                          type: "transfer",
                          id: selectedDocumentId,
                          text: "Bạn có chắc chắn muốn chuyển nhượng tác phẩm này? Hành động này không thể hoàn tác và bạn sẽ mất toàn quyền truy cập.",
                        })}
                        disabled={isTransferring || !selectedDocumentId || !transferUserId.trim()}
                        className="h-10 bg-black text-white px-6 text-sm font-medium flex items-center gap-2 rounded-none disabled:opacity-50 w-fit"
                      >
                        {isTransferring ? <Loader2 className="w-4 h-4 animate-spin" /> : "Chuyển nhượng"}
                      </button>
                    </div>
                  </div>
                  
                  <div className="h-px bg-zinc-200" />
                  
                  <div className="space-y-6">
                    <div className="space-y-3">
                      <h2 className="text-xl font-medium text-black flex items-center gap-2"><Shield className="w-5 h-5" /> Bảo vệ bản quyền (DRM)</h2>
                      <p className="text-sm font-medium text-zinc-500 leading-relaxed max-w-md">
                        Hạn chế người dùng sao chép nội dung trái phép và ẩn tài liệu khỏi công cụ tìm kiếm.
                      </p>
                    </div>
                    <div className="space-y-4">
                      <label className="flex items-center gap-3 cursor-pointer">
                        <div className={`w-10 h-5 border flex items-center p-0.5  ${drmCopy ? 'bg-black border-black' : 'bg-white border-zinc-300'}`}>
                          <div className={`w-4 h-4 bg-white border ${drmCopy ? 'border-black translate-x-5' : 'border-zinc-300 translate-x-0'}  `} />
                        </div>
                        <input type="checkbox" className="hidden" checked={drmCopy} onChange={(e) => setDrmCopy(e.target.checked)} />
                        <span className="text-sm font-medium text-black">Chống bôi đen & Copy</span>
                      </label>
                      <label className="flex items-center gap-3 cursor-pointer">
                        <div className={`w-10 h-5 border flex items-center p-0.5  ${drmSearch ? 'bg-black border-black' : 'bg-white border-zinc-300'}`}>
                          <div className={`w-4 h-4 bg-white border ${drmSearch ? 'border-black translate-x-5' : 'border-zinc-300 translate-x-0'}  `} />
                        </div>
                        <input type="checkbox" className="hidden" checked={drmSearch} onChange={(e) => setDrmSearch(e.target.checked)} />
                        <span className="text-sm font-medium text-black">Ẩn khỏi công cụ tìm kiếm (SEO)</span>
                      </label>
                      <button onClick={handleSaveDRM} disabled={savingDrm || !selectedDocumentId} className="h-10 bg-black text-white px-6 text-sm font-medium flex items-center gap-2 rounded-none disabled:opacity-50 w-fit">
                        {savingDrm ? <Loader2 className="w-4 h-4 animate-spin" /> : "Lưu cài đặt DRM"}
                      </button>
                    </div>
                  </div>

                  <div className="h-px bg-zinc-200" />

                  <div className="space-y-6">
                    <div className="space-y-3">
                      <h2 className="text-xl font-medium text-black flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-red-500" /> Cảnh báo nội dung (NSFW)</h2>
                      <p className="text-sm font-medium text-zinc-500 leading-relaxed max-w-md">
                        Đánh dấu nếu tác phẩm có chứa nội dung nhạy cảm, bạo lực hoặc giới hạn độ tuổi (18+).
                      </p>
                    </div>
                    <div className="space-y-4">
                      <label className="flex items-center gap-3 cursor-pointer">
                        <div className={`w-10 h-5 border flex items-center p-0.5  ${isNsfw ? 'bg-red-500 border-red-500' : 'bg-white border-zinc-300'}`}>
                          <div className={`w-4 h-4 bg-white border ${isNsfw ? 'border-red-500 translate-x-5' : 'border-zinc-300 translate-x-0'}  `} />
                        </div>
                        <input type="checkbox" className="hidden" checked={isNsfw} onChange={handleToggleNSFW} />
                        <span className="text-sm font-medium text-black">Yêu cầu xác nhận độ tuổi trước khi đọc</span>
                      </label>
                    </div>
                  </div>

                  <div className="h-px bg-zinc-200" />

                  <div className="space-y-6">
                    <div className="space-y-3">
                      <h2 className="text-xl font-medium text-black flex items-center gap-2"><Users className="w-5 h-5" /> Đồng sáng tác (Collaboration)</h2>
                      <p className="text-sm font-medium text-zinc-500 leading-relaxed max-w-md">
                        Mời người dùng khác tham gia cùng biên tập tác phẩm.
                      </p>
                    </div>
                    <div className="space-y-4 max-w-md">
                      <div className="flex gap-2">
                        <input
                          type="email"
                          value={inviteEmail}
                          onChange={(e) => setInviteEmail(e.target.value)}
                          placeholder="Email người cộng tác"
                          className="flex-1 h-10 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black  bg-white"
                        />
                        <button onClick={handleInviteCollab} className="h-10 bg-black text-white px-4 text-sm font-medium flex items-center rounded-none whitespace-nowrap">
                          Gửi lời mời
                        </button>
                      </div>
                      {loadingCollabs ? (
                        <div className="flex justify-center p-4"><Loader2 className="w-4 h-4 animate-spin text-zinc-400" /></div>
                      ) : collaborators.length > 0 ? (
                        <ul className="space-y-2 border border-zinc-200 bg-zinc-50 p-4">
                          {collaborators.map((c: any) => (
                            <li key={c.id} className="flex justify-between items-center text-sm font-medium">
                              <span className="text-black">{c.email || c.user_id} <span className="text-zinc-500 text-xs">({c.role})</span></span>
                              <button onClick={() => handleRemoveCollab(c.id)} className="text-red-500  p-1"><Trash2 className="w-3.5 h-3.5" /></button>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-zinc-500 italic">Chưa có người cộng tác nào.</p>
                      )}
                    </div>
                  </div>
                </div>
             </div>
           )}

           {viewMode === "comments" && (
             <div className="h-full overflow-y-auto p-8 md:p-12 animate-in fade-in  no-scrollbar">
                <div className="max-w-3xl mx-auto space-y-8">
                   <div className="bg-white border border-zinc-200 p-8 rounded-none flex items-center justify-between">
                      <div className="space-y-1">
                        <h2 className="text-xl font-medium text-black">Quản lý bình luận</h2>
                        <p className="text-sm font-medium text-zinc-500">
                          Theo dõi và phản hồi bình luận của độc giả trên tất cả các chương.
                        </p>
                      </div>
                   </div>
                   
                   {loadingComments ? (
                     <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-zinc-300" /></div>
                   ) : comments.length === 0 ? (
                     <div className="text-center py-20 border border-zinc-200 bg-white">
                        <MessageSquare className="w-12 h-12 text-zinc-200 mx-auto mb-4" />
                        <p className="text-zinc-500 font-medium">Chưa có bình luận nào cho tác phẩm này.</p>
                     </div>
                   ) : (
                     <div className="space-y-6">
                        {comments.map((comment: any) => (
                          <div key={comment.id || comment._id} className="bg-white border border-zinc-200 p-6 rounded-none space-y-4">
                            <div className="flex justify-between items-start">
                              <div>
                                <span className="font-semibold text-sm text-black">{comment.author?.username || "Ẩn danh"}</span>
                                <span className="text-xs text-zinc-400 ml-2">{new Date(comment.created_at).toLocaleDateString("vi-VN")}</span>
                              </div>
                              <button onClick={() => handleDeleteComment(comment.id || comment._id)} className="text-zinc-400  ">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                            <p className="text-sm text-zinc-700 leading-relaxed">{comment.content}</p>
                            
                            {replyingTo === (comment.id || comment._id) ? (
                              <div className="flex gap-2 mt-4">
                                <input
                                  type="text"
                                  value={replyContent}
                                  onChange={(e) => setReplyContent(e.target.value)}
                                  placeholder="Nhập phản hồi"
                                  className="flex-1 h-9 border border-zinc-200 px-3 text-xs font-medium rounded-none outline-none focus:border-black "
                                  autoFocus
                                />
                                <button onClick={() => setReplyingTo(null)} className="px-3 border border-zinc-200 text-xs font-medium ">Hủy</button>
                                <button onClick={handleReplyComment} className="px-4 bg-black text-white text-xs font-medium">Gửi</button>
                              </div>
                            ) : (
                              <button onClick={() => setReplyingTo(comment.id || comment._id)} className="text-xs font-semibold text-black  mt-2">Phản hồi</button>
                            )}
                          </div>
                        ))}
                     </div>
                   )}
                </div>
             </div>
           )}

           {viewMode === "versions" && (
             <div className="h-full overflow-y-auto p-8 md:p-12 animate-in fade-in  no-scrollbar">
                <div className="max-w-3xl mx-auto space-y-8">
                   <div className="bg-white border border-zinc-200 p-8 rounded-none flex items-center justify-between">
                      <div className="space-y-1">
                        <h2 className="text-xl font-medium text-black">Lịch sử phiên bản</h2>
                        <p className="text-sm font-medium text-zinc-500">
                          {selectedVersions.length === 2 ? "Đã chọn 2 phiên bản để so sánh" : "Chọn tối đa 2 phiên bản để so sánh sự khác biệt"}
                        </p>
                      </div>
                      <div className="flex gap-3">
                        {selectedVersions.length === 2 && (
                          <button 
                            onClick={handleCompareVersions}
                            disabled={isComparing}
                            className="h-10 bg-black text-white px-6 text-sm font-medium  flex items-center gap-2 rounded-none"
                          >
                            {isComparing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
                            So sánh ngay
                          </button>
                        )}
                        <RotateCcw className="w-6 h-6 text-zinc-400" />
                      </div>
                   </div>
                   
                   <div className="space-y-4">
                      {loadingVersions ? (
                        <div className="py-12 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-zinc-400" /></div>
                      ) : versions.length === 0 ? (
                        <div className="bg-zinc-50 border border-zinc-200 p-16 text-center rounded-none flex flex-col items-center justify-center gap-3">
                           <Clock className="w-6 h-6 text-zinc-400" />
                           <p className="text-sm font-medium text-zinc-500">Chưa có phiên bản nào được lưu</p>
                        </div>
                      ) : (
                        versions.map((v) => (
                          <div 
                            key={v.id} 
                            onClick={() => toggleVersionSelection(v.id)}
                            className={`bg-white border p-6 flex items-center justify-between   rounded-none cursor-pointer ${
                              selectedVersions.includes(v.id) ? "border-black ring-1 ring-black" : "border-zinc-200"
                            }`}
                          >
                             <div className="flex items-center gap-4">
                                <div className={`w-10 h-10 flex items-center justify-center rounded-none border ${selectedVersions.includes(v.id) ? "bg-black text-white border-black" : "bg-zinc-50 text-zinc-500 border-zinc-200"}`}>
                                   <Clock className="w-4 h-4" />
                                </div>
                                <div className="space-y-1">
                                   <p className="text-base font-medium text-black">{new Date(v.created_at).toLocaleString("vi-VN")}</p>
                                   <p className="text-sm font-medium text-zinc-500">Lưu bởi: {v.author_name || "Hệ thống"}</p>
                                </div>
                             </div>
                             <div className="flex gap-3">
                                <button 
                                  onClick={(e) => { e.stopPropagation(); handleRestoreVersion(v.id); }}
                                  className="h-9 px-4 border border-zinc-200 text-sm font-medium text-black  rounded-none bg-white"
                                >
                                   Khôi phục
                                </button>
                             </div>
                          </div>
                        ))
                      )}
                   </div>
                </div>
             </div>
           )}

           {viewMode === "trash" && (
             <div className="h-full overflow-y-auto p-8 md:p-12 animate-in fade-in  no-scrollbar">
                <div className="max-w-3xl mx-auto space-y-8">
                   <div className="bg-white border border-zinc-200 p-8 rounded-none flex items-center justify-between">
                      <div className="space-y-1">
                        <h2 className="text-xl font-medium text-black">Thùng rác nội dung</h2>
                        <p className="text-sm font-medium text-zinc-500">Tài liệu đã tạm thời bị gỡ bỏ</p>
                      </div>
                      <Trash2 className="w-6 h-6 text-zinc-400" />
                   </div>
                   
                   <div className="space-y-4">
                      {loadingTrash ? (
                        <div className="py-12 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-zinc-400" /></div>
                      ) : !Array.isArray(trash) || trash.length === 0 ? (
                        <div className="bg-zinc-50 border border-zinc-200 p-16 text-center rounded-none flex flex-col items-center justify-center gap-3">
                           <X className="w-6 h-6 text-zinc-400" />
                           <p className="text-sm font-medium text-zinc-500">Thùng rác trống</p>
                        </div>
                      ) : (
                        trash.map((doc: any) => (
                          <div key={doc._id} className="bg-white border border-zinc-200 p-6 flex items-center justify-between  rounded-none">
                             <div className="flex items-center gap-4">
                                <div className="w-10 h-10 bg-zinc-50 flex items-center justify-center rounded-none border border-zinc-200">
                                   <FileText className="w-4 h-4 text-zinc-500" />
                                </div>
                                <div className="space-y-1">
                                   <p className="text-base font-medium text-black">{doc.title}</p>
                                   <p className="text-sm font-medium text-zinc-500">Ngày xóa: {new Date(doc.updated_at).toLocaleDateString("vi-VN")}</p>
                                </div>
                             </div>
                             <button 
                                onClick={() => handleRestoreDocument(doc._id || doc.id)}
                                className="h-9 px-4 border border-zinc-200 text-sm font-medium text-black  rounded-none flex items-center gap-2"
                             >
                                <RotateCcw className="w-4 h-4" /> Khôi phục
                             </button>
                          </div>
                        ))
                      )}
                   </div>
                </div>
             </div>
           )}

            <Modal isOpen={!!diffData} onClose={() => setDiffData(null)} className="max-w-5xl h-[80vh] flex flex-col">
              <ModalHeader>
                <ModalTitle>So sánh sự khác biệt</ModalTitle>
              </ModalHeader>
              <ModalContent className="flex-1 overflow-hidden p-0 flex flex-col">
                 <div className="flex bg-zinc-50 border-b border-zinc-200 divide-x divide-zinc-200">
                    <div className="flex-1 p-3 text-[10px] font-bold uppercase tracking-widest text-zinc-400">Phiên bản A (Cũ)</div>
                    <div className="flex-1 p-3 text-[10px] font-bold uppercase tracking-widest text-zinc-400">Phiên bản B (Mới)</div>
                 </div>
                 <div className="flex-1 overflow-y-auto bg-white p-0">
                    {diffData ? renderLineDiff(diffData.version_a || "", diffData.version_b || "") : (
                      <div className="p-8 text-center text-zinc-500 text-sm italic">Không có dữ liệu so sánh</div>
                    )}
                 </div>
              </ModalContent>
              <ModalFooter>
                 <button onClick={() => setDiffData(null)} className="px-6 py-2 bg-black text-white text-xs font-medium border border-black ">Đóng cửa sổ</button>
              </ModalFooter>
            </Modal>
        </main>
      </div>
    </div>
  );
}

export default function AuthorStudioPage() {
  return (
    <Suspense fallback={<div className="flex-1 flex items-center justify-center min-h-screen"><Loader2 className="w-8 h-8 animate-spin text-zinc-300" /></div>}>
      <StudioContent />
    </Suspense>
  );
}
