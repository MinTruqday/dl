"use client";

import { useEffect, useMemo, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  compileDocumentAPI,
  getDocumentDraftAPI,
  getDocumentsAPI,
  publishDocumentAPI,
  saveDocumentDraftAPI,
  getDocumentVersionsAPI,
  restoreVersionAPI,
  getTrashAPI,
  restoreDocumentAPI,
  softDeleteDocumentAPI,
  getMyDocumentsAPI,
  updateDocumentAPI,
} from "@/services/document.service";
import { getAuthorStatsAPI } from "@/services/wallet.service";
import { getRevenueAPI, requestPayoutDetailedAPI } from "@/services/monetization.service";
import { 
  ingestDocumentAPI, 
  generateAICoverAPI,
  getDocumentSentimentAPI 
} from "@/services/ai.service";
import { getToken, API_URL } from "@/services/auth.service";
import { useAuth } from "@/contexts/AuthContext";
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
} from "lucide-react";
import Editor from "@/components/editor/Editor";
import { useToast } from "@/contexts/ToastContext";

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
};

type ViewMode = "edit" | "stats" | "config" | "versions" | "trash" | "sentiment";
type EditorMode = "edit" | "preview" | "raw";

function StudioContent() {
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const rawDocId = searchParams.get("document");
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
  const [notification, setNotification] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);

  const [stats, setStats] = useState<any>(null);
  const [revenue, setRevenue] = useState<any>(null);

  const [versions, setVersions] = useState<any[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);

  const [trash, setTrash] = useState<any[]>([]);
  const [loadingTrash, setLoadingTrash] = useState(false);

  const [showPayoutModal, setShowPayoutModal] = useState(false);
  const [payoutAmount, setPayoutAmount] = useState(0);
  const [bankInfo, setBankInfo] = useState({ bank_name: "", account_number: "", account_name: "" });
  const [requestingPayout, setRequestingPayout] = useState(false);

  const [confirmAction, setConfirmAction] = useState<{ type: string; id: string; text: string } | null>(null);
  const [showChapterModal, setShowChapterModal] = useState(false);
  const [newChapterTitle, setNewChapterTitle] = useState("");
  const [visible, setVisible] = useState(false);
  const [sentimentData, setSentimentData] = useState<any>(null);
  const [loadingSentiment, setLoadingSentiment] = useState(false);
  const [generatingCover, setGeneratingCover] = useState(false);

  const selectedDocument = useMemo(
    () => documents.find((b) => b._id === selectedDocumentId) || null,
    [documents, selectedDocumentId]
  );

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      let data;
      if (user?.role === "admin") {
        data = await getDocumentsAPI();
      } else {
        data = await getMyDocumentsAPI();
      }
      
      const list = data.data || data || [];
      setDocuments(list);
      
      if (list.length > 0) {
        if (docIdFromUrl) {
          setSelectedDocumentId(docIdFromUrl);
        } else if (!selectedDocumentId) {
          setSelectedDocumentId(list[0]._id);
        }
      }
    } catch {
      showToast("Lỗi tải danh sách tài liệu.", "error");
    } finally {
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [docIdFromUrl, selectedDocumentId, user]);

  const loadDraft = useCallback(async () => {
    if (!selectedDocumentId) return;
    try {
      const data = await getDocumentDraftAPI(selectedDocumentId);
      const draft = data.data || data;
      setContent(draft?.content || "");
      setStatusMsg("Đã tải xong");
    } catch {
      setStatusMsg("Lỗi tải bản nháp");
    }
  }, [selectedDocumentId]);

  const fetchStatsData = useCallback(async () => {
    try {
      const [sRes, rRes] = await Promise.all([
        getAuthorStatsAPI(),
        getRevenueAPI(),
      ]);
      setStats(sRes.data || sRes);
      setRevenue(rRes.data || rRes);
    } catch (err: any) {
      console.error("Lỗi tải thông số:", err);
    }
  }, []);

  const fetchVersions = useCallback(async () => {
    if (!selectedDocumentId) return;
    setLoadingVersions(true);
    try {
      const data = await getDocumentVersionsAPI(selectedDocumentId);
      setVersions(data || []);
    } catch (err: any) {
      console.error("Lỗi tải phiên bản:", err);
    } finally {
      setLoadingVersions(false);
    }
  }, [selectedDocumentId]);

  const fetchTrash = useCallback(async () => {
    setLoadingTrash(true);
    try {
      const data = await getTrashAPI();
      setTrash(data || []);
    } catch (err: any) {
      console.error("Lỗi tải thùng rác:", err);
    } finally {
      setLoadingTrash(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const fetchSentiment = useCallback(async () => {
    if (!selectedDocumentId) return;
    setLoadingSentiment(true);
    try {
      const json = await getDocumentSentimentAPI(selectedDocumentId);
      if (json.data) setSentimentData(json.data);
    } catch (e) {
      console.error("Lỗi lấy dữ liệu cảm quan:", e);
    } finally {
      setLoadingSentiment(false);
    }
  }, [selectedDocumentId]);

  useEffect(() => {
    if (selectedDocumentId) {
      loadDraft();
      if (viewMode === "stats") fetchStatsData();
      if (viewMode === "versions") fetchVersions();
      if (viewMode === "sentiment") fetchSentiment();
    } else {
      setContent("");
    }
    if (viewMode === "trash") fetchTrash();
  }, [selectedDocumentId, viewMode, loadDraft, fetchStatsData, fetchVersions, fetchTrash, fetchSentiment]);

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
      showToast("Đã khôi phục tài liệu thành công.", "success");
      fetchTrash();
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Lỗi khôi phục tài liệu.", "error");
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
        showToast("Đã khôi phục phiên bản thành công.", "success");
        loadDraft();
      } else if (confirmAction.type === "delete_doc") {
        await softDeleteDocumentAPI(confirmAction.id);
        showToast("Đã chuyển tài liệu vào thùng rác.", "success");
        if (selectedDocumentId === confirmAction.id) setSelectedDocumentId("");
        fetchDocuments();
      }
    } catch (e: any) {
      showToast(e.message || "Thao tác thất bại.", "error");
    } finally {
      setConfirmAction(null);
    }
  };

  const handleIngestAI = async () => {
    if (!selectedDocumentId) return;
    setIsIngesting(true);
    setStatusMsg("Đang đồng bộ AI");
    try {
      await ingestDocumentAPI(selectedDocumentId);
      showToast("AI đã được cập nhật tri thức mới.", "success");
    } catch (e: any) {
      showToast(e.message || "Đồng bộ AI thất bại.", "error");
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
      showToast("Ảnh bìa AI đã được khởi tạo và cập nhật.", "success");
      fetchDocuments();
    } catch (e: any) {
      showToast(e.message || "Tạo ảnh bìa thất bại.", "error");
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
      showToast("Đã lưu bản nháp thành công.", "success");
    } catch {
      showToast("Không thể lưu bản nháp.", "error");
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
      showToast("Tài liệu đã được công bố thành công.", "success");
      fetchDocuments();
    } catch {
      showToast("Xuất bản thất bại.", "error");
    } finally {
      setStatusMsg("Sẵn sàng");
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
      fetchDocuments();
    } catch (err: any) {
      console.error("Lỗi thay đổi thứ tự chương:", err);
    }
  };

  const addChapter = async () => {
    if (!newChapterTitle.trim()) return;
    const newChapter = { title: newChapterTitle, content: "Bắt đầu viết chương mới tại đây" };
    const newChapters = [...(selectedDocument?.chapters || []), newChapter];

    try {
      await updateDocumentAPI(selectedDocumentId, { chapters: newChapters });
      showToast("Đã thêm chương mới.", "success");
      setNewChapterTitle("");
      setShowChapterModal(false);
      fetchDocuments();
    } catch (err: any) {
      console.error("Lỗi thêm chương:", err);
    }
  };

  const handlePayout = async () => {
    if (payoutAmount <= 0) {
      showToast("Số tiền không hợp lệ.", "error");
      return;
    }
    if (!bankInfo.bank_name || !bankInfo.account_number || !bankInfo.account_name) {
      showToast("Vui lòng nhập đủ thông tin ngân hàng.", "error");
      return;
    }

    setRequestingPayout(true);
    try {
      await requestPayoutDetailedAPI(payoutAmount, bankInfo);
      showToast("Yêu cầu rút tiền đã được gửi.", "success");
      setShowPayoutModal(false);
      fetchStatsData();
    } catch (e: any) {
      showToast(e.message || "Yêu cầu rút tiền thất bại.", "error");
    } finally {
      setRequestingPayout(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[80vh]">
        <Loader2 className="w-12 h-12 animate-spin text-zinc-100" />
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-var(--navbar-height))] overflow-hidden bg-white selection:bg-black selection:text-white relative font-sans">
      

      {confirmAction && (
        <div className="fixed inset-0 z-[250] flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="absolute inset-0 bg-black/40" onClick={() => setConfirmAction(null)} />
          <div className="bg-white w-full max-w-sm relative border border-zinc-200 p-10 space-y-8 rounded-sm">
            <h3 className="text-sm font-bold tracking-tight uppercase">Xác nhận thao tác</h3>
            <p className="text-xs text-zinc-500 leading-relaxed font-medium italic">"{confirmAction.text}"</p>
            <div className="flex gap-4">
              <button onClick={() => setConfirmAction(null)} className="flex-1 h-12 text-[10px] font-bold uppercase tracking-widest border border-zinc-100 hover:bg-zinc-50 transition-all rounded-sm">
                Bỏ qua
              </button>
              <button onClick={executeConfirm} className="flex-1 h-12 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all rounded-sm">
                Xác nhận
              </button>
            </div>
          </div>
        </div>
      )}

      {showChapterModal && (
        <div className="fixed inset-0 z-[250] flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowChapterModal(false)} />
          <div className="bg-white w-full max-w-sm relative border border-zinc-200 p-10 space-y-8 rounded-sm">
            <h3 className="text-sm font-bold tracking-tight uppercase">Thêm chương mới</h3>
            <input
              value={newChapterTitle}
              onChange={(e) => setNewChapterTitle(e.target.value)}
              placeholder="Nhập tiêu đề chương"
              className="w-full h-14 border border-zinc-100 px-5 font-bold text-xs focus:outline-none focus:border-black transition-all rounded-sm"
              autoFocus
            />
            <div className="flex gap-4">
              <button onClick={() => setShowChapterModal(false)} className="flex-1 h-12 text-[10px] font-bold uppercase tracking-widest border border-zinc-100 hover:bg-zinc-50 transition-all rounded-sm">
                Hủy
              </button>
              <button onClick={addChapter} className="flex-1 h-12 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all rounded-sm">
                Lưu chương
              </button>
            </div>
          </div>
        </div>
      )}

      {showPayoutModal && (
        <div className="fixed inset-0 z-[250] flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowPayoutModal(false)} />
          <div className="bg-white w-full max-w-md relative border border-zinc-200 p-10 space-y-8 rounded-sm">
            <h3 className="text-sm font-bold tracking-tight uppercase">Yêu cầu rút tiền</h3>
            <div className="space-y-4">
               <div className="space-y-2">
                 <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Số tiền rút (dl)</label>
                 <input
                   type="number"
                   value={payoutAmount}
                   onChange={(e) => setPayoutAmount(parseInt(e.target.value) || 0)}
                   className="w-full h-12 border border-zinc-100 px-4 text-sm font-bold rounded-sm outline-none focus:border-black transition-all"
                 />
               </div>
               <div className="space-y-2">
                 <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Tên ngân hàng</label>
                 <input
                   value={bankInfo.bank_name}
                   onChange={(e) => setBankInfo({ ...bankInfo, bank_name: e.target.value })}
                   className="w-full h-12 border border-zinc-100 px-4 text-sm font-bold rounded-sm outline-none focus:border-black transition-all"
                 />
               </div>
               <div className="space-y-2">
                 <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Số tài khoản</label>
                 <input
                   value={bankInfo.account_number}
                   onChange={(e) => setBankInfo({ ...bankInfo, account_number: e.target.value })}
                   className="w-full h-12 border border-zinc-100 px-4 text-sm font-bold rounded-sm outline-none focus:border-black transition-all"
                 />
               </div>
               <div className="space-y-2">
                 <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Tên chủ tài khoản</label>
                 <input
                   value={bankInfo.account_name}
                   onChange={(e) => setBankInfo({ ...bankInfo, account_name: e.target.value })}
                   className="w-full h-12 border border-zinc-100 px-4 text-sm font-bold rounded-sm outline-none focus:border-black transition-all"
                 />
               </div>
            </div>
            <div className="flex gap-4 pt-4">
              <button onClick={() => setShowPayoutModal(false)} className="flex-1 h-12 text-[10px] font-bold uppercase tracking-widest border border-zinc-100 hover:bg-zinc-50 transition-all rounded-sm">
                Hủy
              </button>
              <button 
                onClick={handlePayout} 
                disabled={requestingPayout}
                className="flex-1 h-12 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all rounded-sm flex items-center justify-center gap-2"
              >
                {requestingPayout ? <Loader2 className="w-4 h-4 animate-spin" /> : "Gửi yêu cầu"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div 
        className="h-16 border-b border-zinc-100 px-8 flex items-center justify-between bg-white shrink-0 z-30 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-4">
             <div className="w-8 h-8 bg-black flex items-center justify-center rounded-sm">
                <FileText className="w-4 h-4 text-white" />
             </div>
             <span className="text-sm font-bold tracking-tighter truncate max-w-[200px]">
               {selectedDocument?.title || "Không tên"}
             </span>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest hidden md:block">
            {statusMsg}
          </span>
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={!selectedDocumentId || isSaving}
              className="h-10 px-6 border border-zinc-200 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all disabled:opacity-50 flex items-center gap-2 rounded-sm"
            >
              {isSaving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              Lưu bản nháp
            </button>
            <button
              onClick={handlePublish}
              disabled={!selectedDocumentId}
              className="h-10 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all disabled:opacity-50 active:scale-95 rounded-sm"
            >
              Công bố tác phẩm
            </button>
          </div>
        </div>
      </div>

      <div 
        className="flex flex-1 overflow-hidden transition-all duration-300 delay-75"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <nav className="w-16 border-r border-zinc-100 flex flex-col items-center py-8 gap-6 shrink-0 bg-white">
          {[
            { mode: "edit", icon: FileText, label: "Soạn thảo" },
            { mode: "stats", icon: BarChart3, label: "Số liệu" },
            { mode: "sentiment", icon: Brain, label: "Phân tích AI" },
            { mode: "config", icon: Settings, label: "Cấu hình" },
            { mode: "versions", icon: Clock, label: "Lịch sử" },
            { mode: "trash", icon: Trash2, label: "Thùng rác" },
          ].map((item) => (
            <button
              key={item.mode}
              onClick={() => setViewMode(item.mode as ViewMode)}
              className={`p-3 transition-all relative group rounded-sm ${
                viewMode === item.mode ? "bg-black text-white" : "text-zinc-300 hover:text-black"
              }`}
              title={item.label}
            >
              <item.icon className="w-5 h-5" />
              <div className="absolute left-full ml-4 px-3 py-1.5 bg-black text-white text-[9px] font-bold uppercase tracking-widest whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-all z-50 rounded-sm">
                {item.label}
              </div>
            </button>
          ))}
        </nav>

        <aside className="w-80 border-r border-zinc-100 flex flex-col shrink-0 bg-white animate-in slide-in-from-left duration-300">
           {viewMode === "edit" ? (
             <>
               <div className="p-8 border-b border-zinc-100 bg-zinc-50/20">
                  <div className="flex justify-between items-center mb-8">
                    <h3 className="text-[10px] font-bold text-black uppercase tracking-widest">Cấu trúc nội dung</h3>
                    <button
                      onClick={() => setShowChapterModal(true)}
                      className="text-[10px] font-bold text-black hover:underline flex items-center gap-2"
                    >
                      <Plus className="w-3 h-3" /> Thêm chương
                    </button>
                  </div>
                  <div className="space-y-2">
                    {!selectedDocument?.chapters || selectedDocument.chapters.length === 0 ? (
                      <div className="py-10 text-center border border-dashed border-zinc-100 flex flex-col items-center gap-3 rounded-sm">
                         <Plus className="w-5 h-5 text-zinc-100" />
                         <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Chưa có chương</p>
                      </div>
                    ) : (
                      selectedDocument.chapters.map((ch: any, idx: number) => (
                        <div
                          key={ch.id || idx}
                          className="group flex items-center gap-4 p-4 border border-zinc-100 bg-white hover:border-black cursor-pointer transition-all duration-300 rounded-sm"
                        >
                          <span className="text-[10px] font-bold text-zinc-200 group-hover:text-black w-4 transition-colors">
                            {idx + 1}
                          </span>
                          <span className="text-[11px] font-bold truncate flex-1 text-zinc-500 group-hover:text-black transition-colors tracking-tight">
                            {ch.title}
                          </span>
                          <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-all">
                            <button onClick={(e) => { e.stopPropagation(); moveChapter(idx, "up"); }} className="p-1 hover:bg-zinc-50 rounded-sm"><ArrowUp className="w-2.5 h-2.5 text-zinc-300 hover:text-black" /></button>
                            <button onClick={(e) => { e.stopPropagation(); moveChapter(idx, "down"); }} className="p-1 hover:bg-zinc-50 rounded-sm"><ArrowDown className="w-2.5 h-2.5 text-zinc-300 hover:text-black" /></button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
               </div>
               <div className="flex-1 overflow-y-auto no-scrollbar p-8 space-y-8">
                  <div className="space-y-6">
                    <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Tác phẩm khác</h3>
                    <div className="space-y-3">
                      {documents.filter(d => d._id !== selectedDocumentId).map((doc) => (
                        <button
                          key={doc._id}
                          onClick={() => setSelectedDocumentId(doc._id)}
                          className="w-full text-left p-5 border border-zinc-50 hover:border-black transition-all duration-300 bg-white group rounded-sm"
                        >
                           <p className="text-[11px] font-bold text-zinc-400 group-hover:text-black truncate mb-2 transition-colors">{doc.title}</p>
                           <div className="flex items-center gap-3">
                             <div className={`w-1 h-1 rounded-sm ${doc.status === 'published' ? 'bg-black' : 'bg-zinc-200'}`} />
                             <span className="text-[9px] font-bold text-zinc-200 uppercase tracking-widest">{doc.status === 'published' ? 'XUẤT BẢN' : 'BẢN NHÁP'}</span>
                           </div>
                        </button>
                      ))}
                    </div>
                  </div>
               </div>
             </>
           ) : (
             <div className="p-8">
                <h3 className="text-[10px] font-bold text-black uppercase tracking-widest mb-8">Danh sách tác phẩm</h3>
                <div className="space-y-3">
                  {documents.map((doc) => (
                    <button
                      key={doc._id}
                      onClick={() => setSelectedDocumentId(doc._id)}
                      className={`w-full text-left p-5 border transition-all duration-300 flex flex-col gap-2 rounded-sm ${
                        selectedDocumentId === doc._id ? "bg-black text-white border-black" : "bg-white text-zinc-400 border-zinc-50 hover:border-black hover:text-black"
                      }`}
                    >
                      <span className="text-[11px] font-bold truncate tracking-tight uppercase">{doc.title}</span>
                      <span className="text-[9px] font-bold opacity-40 uppercase tracking-widest italic">{doc.status || "Bản nháp"}</span>
                    </button>
                  ))}
                </div>
             </div>
           )}
        </aside>

        <main className="flex-1 bg-zinc-50/30 overflow-hidden relative">
           {viewMode === "edit" && (
             <div className="h-full flex flex-col animate-in fade-in duration-300">
                <div className="h-12 border-b border-zinc-100 bg-white px-8 flex items-center justify-between shrink-0">
                   <div className="flex h-full">
                      {(["edit", "preview", "raw"] as const).map((m) => (
                        <button
                          key={m}
                          onClick={() => setEditorMode(m)}
                          className={`px-8 h-full text-[9px] font-bold uppercase tracking-widest transition-all border-b-2 ${
                            editorMode === m ? "border-black text-black bg-zinc-50/50" : "border-transparent text-zinc-300 hover:text-black"
                          }`}
                        >
                          {m === "edit" ? "Biên tập" : m === "preview" ? "Trải nghiệm" : "Dữ liệu thô"}
                        </button>
                      ))}
                   </div>
                </div>
                <div className="flex-1 overflow-y-auto p-12 lg:p-20 no-scrollbar">
                   <div className="max-w-4xl mx-auto animate-in slide-in-from-bottom-6 duration-300">
                      {editorMode === "edit" ? (
                        <Editor initialContent={content} onSave={(val) => setContent(val)} />
                      ) : editorMode === "preview" ? (
                        <div className="bg-white p-20 border border-zinc-100 rounded-sm">
                          <div className="prose prose-zinc max-w-none font-sans text-lg leading-relaxed text-zinc-800" dangerouslySetInnerHTML={{ __html: content }} />
                        </div>
                      ) : (
                        <pre className="p-16 bg-zinc-900 text-zinc-500 text-[11px] font-mono leading-relaxed overflow-auto min-h-[100vh] rounded-sm">
                          {content || "Nội dung hiện đang trống"}
                        </pre>
                      )}
                   </div>
                </div>
             </div>
           )}

           {viewMode === "stats" && (
             <div className="h-full overflow-y-auto p-16 animate-in fade-in duration-300 no-scrollbar">
                <div className="max-w-5xl mx-auto space-y-16">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {[
                      { label: "Tầm ảnh hưởng", val: stats?.total_views || 0, icon: Eye, unit: "Lượt xem" },
                      { label: "Mạng lưới độc giả", val: stats?.followers_count || 0, icon: Database, unit: "Độc giả" },
                      { label: "Doanh thu khả dụng", val: revenue?.available_balance || 0, icon: Wallet, unit: "dl" },
                    ].map((s, i) => (
                      <div key={i} className="bg-white p-12 border border-zinc-100 group hover:border-black transition-all duration-300 rounded-sm">
                        <s.icon className="w-6 h-6 text-zinc-100 group-hover:text-black transition-colors mb-10" />
                        <h4 className="text-4xl font-bold tracking-tighter mb-2">{s.val.toLocaleString()} <span className="text-sm text-zinc-200">{s.unit}</span></h4>
                        <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{s.label}</p>
                      </div>
                    ))}
                  </div>

                  <div className="bg-white border border-zinc-100 rounded-sm">
                    <div className="p-10 border-b border-zinc-100 flex justify-between items-center">
                      <h3 className="text-[11px] font-bold text-black uppercase tracking-widest">Chi tiết tác phẩm</h3>
                      <button 
                        onClick={() => setShowPayoutModal(true)}
                        className="h-10 px-6 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all rounded-sm flex items-center gap-2"
                      >
                        <Banknote className="w-3.5 h-3.5" /> Rút tiền doanh thu
                      </button>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-zinc-50 text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                            <th className="px-10 py-6">Tiêu đề tác phẩm</th>
                            <th className="px-10 py-6">Lượt tương tác</th>
                            <th className="px-10 py-6">Xếp hạng</th>
                            <th className="px-10 py-6 text-right">Hành động</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-50">
                          {(stats?.documents || []).map((doc: any) => (
                            <tr key={doc.id} className="hover:bg-zinc-50/50 transition-colors group cursor-pointer">
                              <td className="px-10 py-8 font-bold text-zinc-500 group-hover:text-black transition-colors text-sm uppercase">{doc.title}</td>
                              <td className="px-10 py-8 font-bold text-black">{doc.views.toLocaleString()}</td>
                              <td className="px-10 py-8">
                                <div className="flex items-center gap-2">
                                  <span className="font-bold">{doc.rating.toFixed(1)}</span>
                                  <div className="flex gap-0.5">
                                    {[1, 2, 3, 4, 5].map(star => <div key={star} className={`w-1.5 h-1.5 rounded-sm ${star <= doc.rating ? 'bg-black' : 'bg-zinc-100'}`} />)}
                                  </div>
                                </div>
                              </td>
                              <td className="px-10 py-8 text-right"><ChevronRight className="w-4 h-4 ml-auto text-zinc-200 group-hover:text-black transition-all" /></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
             </div>
           )}

           {viewMode === "config" && (
             <div className="h-full overflow-y-auto p-16 animate-in fade-in duration-300 no-scrollbar">
                <div className="max-w-3xl mx-auto bg-white border border-zinc-100 p-16 space-y-12 rounded-sm">
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold tracking-tight">Trí tuệ nhân tạo</h2>
                    <p className="text-[11px] font-medium text-zinc-400 leading-relaxed italic">
                      Đồng bộ tri thức của bạn với hệ thống RAG để cho phép AI thấu hiểu và hỗ trợ độc giả tốt hơn.
                    </p>
                    <button
                      onClick={handleIngestAI}
                      disabled={isIngesting || !selectedDocumentId}
                      className="h-14 bg-black text-white px-10 text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all flex items-center gap-3 active:scale-[0.98] rounded-sm"
                    >
                      {isIngesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4 text-zinc-400" />}
                      Kích hoạt đồng bộ tri thức AI
                    </button>
                  </div>
                  <div className="h-px bg-zinc-50" />
                  
                  <div className="space-y-8">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
                      <div className="space-y-4">
                        <h2 className="text-2xl font-bold tracking-tight">Ảnh bìa nghệ thuật</h2>
                        <p className="text-[11px] font-medium text-zinc-400 leading-relaxed italic max-w-md">
                          Hệ thống sẽ phân tích nội dung để tạo ra một ảnh bìa nghệ thuật phản ánh đúng linh hồn của tác phẩm.
                        </p>
                      </div>
                      <button
                        onClick={handleGenerateAICover}
                        disabled={generatingCover || !selectedDocumentId}
                        className="h-12 border border-black text-black px-8 text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-50 transition-all flex items-center gap-3 active:scale-[0.98] rounded-sm"
                      >
                        {generatingCover ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                        {selectedDocument?.cover_url ? "Tái tạo ảnh bìa" : "Tạo ảnh bìa AI"}
                      </button>
                    </div>

                    <div className="relative group max-w-[280px] mx-auto lg:mx-0 rounded-sm overflow-hidden">
                       <div className="aspect-[3/4] bg-zinc-50 border border-zinc-100 relative overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-300 rounded-sm">
                          {selectedDocument?.cover_url ? (
                            <img
                              src={selectedDocument.cover_url.startsWith("http") ? selectedDocument.cover_url : `${API_URL}/storage/${selectedDocument.cover_url}`}
                              alt={selectedDocument.title}
                              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                            />
                          ) : (
                            <div className="w-full h-full flex flex-col items-center justify-center p-8 text-center gap-4">
                              <div className="w-12 h-12 bg-white flex items-center justify-center border border-zinc-100 rounded-sm">
                                 <Sparkles className="w-6 h-6 text-zinc-200" />
                              </div>
                              <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Chưa có ảnh bìa</p>
                            </div>
                          )}
                          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-300" />
                       </div>
                       
                       {selectedDocument?.cover_url && (
                         <div className="absolute -bottom-2 -right-2 bg-white border border-zinc-100 p-3 rounded-sm animate-in slide-in-from-top-2 duration-300">
                            <p className="text-[9px] font-bold uppercase tracking-widest text-zinc-400">Ảnh được tạo bởi AI</p>
                         </div>
                       )}
                    </div>
                  </div>
                  <div className="h-px bg-zinc-50" />
                  <div className="py-20 text-center opacity-10">
                     <Settings className="w-16 h-16 mx-auto mb-6" />
                     <p className="text-[10px] font-bold uppercase tracking-widest">Cấu hình nâng cao đang cập nhật</p>
                  </div>
                </div>
             </div>
           )}

           {viewMode === "versions" && (
             <div className="h-full overflow-y-auto p-16 animate-in fade-in duration-300 no-scrollbar">
                <div className="max-w-3xl mx-auto space-y-10">
                   <div className="bg-white border border-zinc-100 p-10 rounded-sm flex items-center justify-between">
                      <div className="space-y-1">
                        <h2 className="text-2xl font-bold tracking-tight uppercase">Lịch sử phiên bản</h2>
                        <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Khôi phục tri thức tại các điểm thời gian</p>
                      </div>
                      <RotateCcw className="w-8 h-8 text-zinc-100 stroke-[1]" />
                   </div>
                   
                   <div className="space-y-4">
                      {loadingVersions ? (
                        <div className="py-24 flex justify-center"><Loader2 className="w-10 h-10 animate-spin text-zinc-100" /></div>
                      ) : versions.length === 0 ? (
                        <div className="bg-white border border-dashed border-zinc-100 p-20 text-center rounded-sm">
                           <Clock className="w-12 h-12 text-zinc-50 mx-auto mb-6" />
                           <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Chưa có phiên bản nào được lưu</p>
                        </div>
                      ) : (
                        versions.map((v) => (
                          <div key={v.id} className="bg-white border border-zinc-100 p-8 flex items-center justify-between group hover:border-black transition-all duration-300 rounded-sm">
                             <div className="flex items-center gap-6">
                                <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-sm">
                                   <Clock className="w-5 h-5 text-zinc-200" />
                                </div>
                                <div className="space-y-1">
                                   <p className="text-sm font-bold text-black uppercase">{new Date(v.created_at).toLocaleString("vi-VN")}</p>
                                   <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Lưu bởi: {v.author_name || "Hệ thống"}</p>
                                </div>
                             </div>
                             <button 
                               onClick={() => handleRestoreVersion(v.id)}
                               className="h-10 px-6 border border-zinc-100 text-[9px] font-bold uppercase tracking-widest hover:bg-black hover:text-white transition-all rounded-sm"
                             >
                                Khôi phục
                             </button>
                          </div>
                        ))
                      )}
                   </div>
                </div>
             </div>
           )}

           {viewMode === "trash" && (
             <div className="h-full overflow-y-auto p-16 animate-in fade-in duration-300 no-scrollbar">
                <div className="max-w-3xl mx-auto space-y-10">
                   <div className="bg-white border border-zinc-100 p-10 rounded-sm flex items-center justify-between">
                      <div className="space-y-1">
                        <h2 className="text-2xl font-bold tracking-tight uppercase">Thùng rác tri thức</h2>
                        <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Tài liệu đã tạm thời bị gỡ bỏ</p>
                      </div>
                      <Trash2 className="w-8 h-8 text-zinc-100 stroke-[1]" />
                   </div>
                   
                   <div className="space-y-4">
                      {loadingTrash ? (
                        <div className="py-24 flex justify-center"><Loader2 className="w-10 h-10 animate-spin text-zinc-100" /></div>
                      ) : trash.length === 0 ? (
                        <div className="bg-white border border-dashed border-zinc-100 p-20 text-center rounded-sm">
                           <X className="w-12 h-12 text-zinc-50 mx-auto mb-6" />
                           <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Thùng rác trống</p>
                        </div>
                      ) : (
                        trash.map((doc) => (
                          <div key={doc._id} className="bg-white border border-zinc-100 p-8 flex items-center justify-between group hover:border-black transition-all duration-300 rounded-sm">
                             <div className="flex items-center gap-6">
                                <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-sm">
                                   <FileText className="w-5 h-5 text-zinc-200" />
                                </div>
                                <div className="space-y-1">
                                   <p className="text-sm font-bold text-black uppercase">{doc.title}</p>
                                   <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Ngày xóa: {new Date(doc.updated_at).toLocaleDateString("vi-VN")}</p>
                                </div>
                             </div>
                             <button 
                               onClick={() => handleRestoreDocument(doc._id)}
                               className="h-10 px-6 border border-zinc-100 text-[9px] font-bold uppercase tracking-widest hover:bg-black hover:text-white transition-all rounded-sm flex items-center gap-2"
                             >
                                <RotateCcw className="w-3 h-3" /> Khôi phục
                             </button>
                          </div>
                        ))
                      )}
                   </div>
                </div>
             </div>
           )}

            {viewMode === "sentiment" && (
              <div className="h-full overflow-y-auto p-16 animate-in fade-in duration-300 no-scrollbar">
                <div className="max-w-4xl mx-auto space-y-12">
                  <div className="bg-white border border-zinc-100 p-12 rounded-sm flex items-center justify-between">
                    <div className="space-y-2">
                      <h2 className="text-3xl font-bold tracking-tighter uppercase">Phân tích cảm quan AI</h2>
                      <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2">
                         <Brain className="w-3.5 h-3.5" /> Thấu hiểu độc giả thông qua trí tuệ nhân tạo
                      </p>
                    </div>
                    <button 
                      onClick={fetchSentiment} 
                      disabled={loadingSentiment}
                      className="h-10 px-6 border border-black text-[10px] font-bold uppercase tracking-widest hover:bg-black hover:text-white transition-all rounded-sm flex items-center gap-2"
                    >
                      {loadingSentiment ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RotateCcw className="w-3.5 h-3.5" />} Làm mới
                    </button>
                  </div>

                  {loadingSentiment ? (
                    <div className="py-40 flex justify-center"><Loader2 className="w-12 h-12 animate-spin text-zinc-100" /></div>
                  ) : sentimentData ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                      <div className="bg-white border border-zinc-100 p-12 rounded-sm space-y-8">
                         <div className="flex items-center justify-between">
                            <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Trạng thái cảm xúc</h3>
                            <span className={`px-4 py-1.5 text-[9px] font-bold uppercase tracking-widest rounded-sm ${sentimentData.sentiment === 'positive' ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-400'}`}>
                              {sentimentData.sentiment === 'positive' ? 'Tích cực' : sentimentData.sentiment === 'negative' ? 'Tiêu cực' : 'Trung lập'}
                            </span>
                         </div>
                         <p className="text-2xl font-bold tracking-tight text-black leading-tight italic">
                           "{sentimentData.summary || "Độc giả đang phản hồi rất tích cực về phong cách hành văn của bạn."}"
                         </p>
                         <div className="pt-6 border-t border-zinc-50">
                            <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest mb-4">Các điểm nhấn chính</p>
                            <div className="space-y-3">
                               {(sentimentData.highlights || ["Cốt truyện lôi cuốn", "Nhân vật phát triển tốt", "Lời văn trau chuốt"]).map((h: string, i: number) => (
                                 <div key={i} className="flex items-center gap-3">
                                    <div className="w-1 h-1 bg-black rounded-sm" />
                                    <span className="text-sm font-medium text-zinc-600">{h}</span>
                                 </div>
                               ))}
                            </div>
                         </div>
                      </div>

                      <div className="bg-white border border-zinc-100 p-12 rounded-sm space-y-10">
                         <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Gợi ý từ AI</h3>
                         <div className="space-y-8">
                            <div className="space-y-4">
                               <p className="text-xs font-bold text-black uppercase tracking-widest">Cần cải thiện</p>
                               <p className="text-sm leading-relaxed text-zinc-500 font-medium italic">
                                 {sentimentData.suggestions || "Nên đẩy nhanh nhịp độ ở các chương giữa để giữ chân độc giả tốt hơn."}
                               </p>
                            </div>
                            <div className="space-y-4">
                               <p className="text-xs font-bold text-black uppercase tracking-widest">Tiềm năng mở rộng</p>
                               <p className="text-sm leading-relaxed text-zinc-500 font-medium italic">
                                 "Khai thác sâu hơn vào quá khứ của nhân vật phụ đang được nhiều độc giả quan tâm."
                               </p>
                            </div>
                         </div>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-white border border-dashed border-zinc-100 p-40 text-center rounded-sm">
                      <Brain className="w-16 h-16 text-zinc-50 mx-auto mb-8 stroke-[1]" />
                      <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Vui lòng chọn tài liệu để bắt đầu phân tích</p>
                    </div>
                  )}
                </div>
              </div>
            )}
        </main>
      </div>
    </div>
  );
}

export default function AuthorStudioPage() {
  return (
    <Suspense fallback={<div className="flex-1 flex items-center justify-center min-h-screen"><Loader2 className="w-12 h-12 animate-spin text-zinc-100" /></div>}>
      <StudioContent />
    </Suspense>
  );
}
