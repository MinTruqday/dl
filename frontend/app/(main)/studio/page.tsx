"use client";

import { useEffect, useMemo, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { compileDocumentAPI, getDocumentDraftAPI, getDocumentsAPI, publishDocumentAPI, saveDocumentDraftAPI, updateDocumentAPI } from "@/services/document.service";
import { requestPayoutDetailedAPI } from "@/services/monetization.service";
import { API_URL } from "@/services/auth.service";
import { getWalletBalanceAPI as getWalletAPI, getDetailedHistoryAPI as getTransactionsAPI } from "@/services/wallet.service";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
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
  const { showToast } = useToast();
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
      showToast("Lỗi tải danh sách tài liệu", "error");
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

  useEffect(() => {
    if (selectedDocumentId) {
      loadDraft();
      if (viewMode === "stats") fetchStatsData();
      if (viewMode === "versions") fetchVersions();
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
      }
    } catch (e: any) {
      showToast(e.message || "Thao tác thất bại", "error");
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
      showToast("AI đã được cập nhật tri thức mới", "success");
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
    } catch {
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
    } catch {
      showToast("Xuất bản thất bại", "error");
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
      showToast("Đã thêm chương mới", "success");
      setNewChapterTitle("");
      setShowChapterModal(false);
      fetchDocuments();
    } catch (err: any) {
      console.error("Lỗi thêm chương:", err);
    }
  };

  const handlePayout = async () => {
    if (payoutAmount <= 0) {
      showToast("Số tiền không hợp lệ", "error");
      return;
    }
    if (!bankInfo.bank_name || !bankInfo.account_number || !bankInfo.account_name) {
      showToast("Vui lòng nhập đủ thông tin ngân hàng", "error");
      return;
    }

    setRequestingPayout(true);
    try {
      await requestPayoutDetailedAPI(payoutAmount, bankInfo);
      showToast("Yêu cầu rút tiền đã được gửi", "success");
      setShowPayoutModal(false);
      fetchStatsData();
    } catch (e: any) {
      showToast(e.message || "Yêu cầu rút tiền thất bại", "error");
    } finally {
      setRequestingPayout(false);
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
      {confirmAction && (
        <div className="fixed inset-0 z-[250] flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="absolute inset-0 bg-black/40" onClick={() => setConfirmAction(null)} />
          <div className="bg-white w-full max-w-sm relative border border-zinc-200 p-6 space-y-6 rounded-none shadow-none">
            <h3 className="text-lg font-medium text-black">Xác nhận thao tác</h3>
            <p className="text-sm text-zinc-600 leading-relaxed">{confirmAction.text}</p>
            <div className="flex gap-3">
              <button onClick={() => setConfirmAction(null)} className="flex-1 h-10 text-sm font-medium border border-zinc-200 hover:bg-zinc-50 transition-colors rounded-none text-black">
                Bỏ qua
              </button>
              <button onClick={executeConfirm} className="flex-1 h-10 bg-black text-white text-sm font-medium hover:bg-zinc-800 transition-colors rounded-none">
                Xác nhận
              </button>
            </div>
          </div>
        </div>
      )}

      {showChapterModal && (
        <div className="fixed inset-0 z-[250] flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowChapterModal(false)} />
          <div className="bg-white w-full max-w-sm relative border border-zinc-200 p-6 space-y-6 rounded-none shadow-none">
            <h3 className="text-lg font-medium text-black">Thêm chương mới</h3>
            <input
              value={newChapterTitle}
              onChange={(e) => setNewChapterTitle(e.target.value)}
              placeholder="Nhập tiêu đề chương"
              className="w-full h-10 border border-zinc-200 px-3 text-sm font-medium focus:outline-none focus:border-black transition-colors rounded-none placeholder:text-zinc-400 text-black"
              autoFocus
            />
            <div className="flex gap-3">
              <button onClick={() => setShowChapterModal(false)} className="flex-1 h-10 text-sm font-medium border border-zinc-200 hover:bg-zinc-50 transition-colors rounded-none text-black">
                Hủy
              </button>
              <button onClick={addChapter} className="flex-1 h-10 bg-black text-white text-sm font-medium hover:bg-zinc-800 transition-colors rounded-none">
                Lưu chương
              </button>
            </div>
          </div>
        </div>
      )}

      {showPayoutModal && (
        <div className="fixed inset-0 z-[250] flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowPayoutModal(false)} />
          <div className="bg-white w-full max-w-md relative border border-zinc-200 p-6 space-y-6 rounded-none shadow-none">
            <h3 className="text-lg font-medium text-black">Yêu cầu rút tiền</h3>
            <div className="space-y-4">
               <div className="space-y-1.5">
                 <label className="text-xs font-medium text-zinc-500">Số tiền rút (dl)</label>
                 <input
                   type="number"
                   value={payoutAmount}
                   onChange={(e) => setPayoutAmount(parseInt(e.target.value) || 0)}
                   className="w-full h-10 border border-zinc-200 px-3 text-sm font-medium rounded-none outline-none focus:border-black transition-colors text-black"
                 />
               </div>
               <div className="space-y-1.5">
                 <label className="text-xs font-medium text-zinc-500">Tên ngân hàng</label>
                 <input
                   value={bankInfo.bank_name}
                   onChange={(e) => setBankInfo({ ...bankInfo, bank_name: e.target.value })}
                   className="w-full h-10 border border-zinc-200 px-3 text-sm font-medium rounded-none outline-none focus:border-black transition-colors text-black"
                 />
               </div>
               <div className="space-y-1.5">
                 <label className="text-xs font-medium text-zinc-500">Số tài khoản</label>
                 <input
                   value={bankInfo.account_number}
                   onChange={(e) => setBankInfo({ ...bankInfo, account_number: e.target.value })}
                   className="w-full h-10 border border-zinc-200 px-3 text-sm font-medium rounded-none outline-none focus:border-black transition-colors text-black"
                 />
               </div>
               <div className="space-y-1.5">
                 <label className="text-xs font-medium text-zinc-500">Tên chủ tài khoản</label>
                 <input
                   value={bankInfo.account_name}
                   onChange={(e) => setBankInfo({ ...bankInfo, account_name: e.target.value })}
                   className="w-full h-10 border border-zinc-200 px-3 text-sm font-medium rounded-none outline-none focus:border-black transition-colors text-black"
                 />
               </div>
            </div>
            <div className="flex gap-3 pt-2">
              <button onClick={() => setShowPayoutModal(false)} className="flex-1 h-10 text-sm font-medium border border-zinc-200 hover:bg-zinc-50 transition-colors rounded-none text-black">
                Hủy
              </button>
              <button 
                onClick={handlePayout} 
                disabled={requestingPayout}
                className="flex-1 h-10 bg-black text-white text-sm font-medium hover:bg-zinc-800 transition-colors rounded-none flex items-center justify-center gap-2"
              >
                {requestingPayout ? <Loader2 className="w-4 h-4 animate-spin" /> : "Gửi yêu cầu"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div 
        className="h-14 border-b border-zinc-200 px-6 flex items-center justify-between bg-white shrink-0 z-30 transition-all duration-300"
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
            <button
              onClick={handleSave}
              disabled={!selectedDocumentId || isSaving}
              className="h-9 px-4 border border-zinc-200 text-sm font-medium text-zinc-700 hover:border-black hover:text-black transition-colors disabled:opacity-50 flex items-center gap-2 rounded-none bg-white"
            >
              {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              Lưu bản nháp
            </button>
            <button
              onClick={handlePublish}
              disabled={!selectedDocumentId}
              className="h-9 px-4 bg-black text-white text-sm font-medium hover:bg-zinc-800 transition-colors disabled:opacity-50 active:scale-95 rounded-none"
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
        <nav className="w-16 border-r border-zinc-200 flex flex-col items-center py-6 gap-4 shrink-0 bg-white">
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
              className={`p-3 transition-colors relative group rounded-none flex items-center justify-center w-12 h-12 ${
                viewMode === item.mode ? "bg-black text-white" : "text-zinc-500 hover:text-black hover:bg-zinc-50"
              }`}
              title={item.label}
            >
              <item.icon className="w-5 h-5" />
              <div className="absolute left-full ml-2 px-2 py-1 bg-black text-white text-xs font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-all z-50 rounded-none">
                {item.label}
              </div>
            </button>
          ))}
        </nav>

        <aside className="w-64 border-r border-zinc-200 flex flex-col shrink-0 bg-white animate-in slide-in-from-left duration-300">
           {viewMode === "edit" ? (
             <>
               <div className="p-6 border-b border-zinc-200 bg-white">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-sm font-medium text-black">Cấu trúc nội dung</h3>
                    <button
                      onClick={() => setShowChapterModal(true)}
                      className="text-sm font-medium text-zinc-500 hover:text-black flex items-center gap-1 transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" /> Thêm chương
                    </button>
                  </div>
                  <div className="space-y-2">
                    {!selectedDocument?.chapters || selectedDocument.chapters.length === 0 ? (
                      <div className="py-8 text-center border border-zinc-200 flex flex-col items-center gap-2 rounded-none bg-zinc-50">
                         <Plus className="w-4 h-4 text-zinc-400" />
                         <p className="text-xs font-medium text-zinc-500">Chưa có chương</p>
                      </div>
                    ) : (
                      selectedDocument.chapters.map((ch: any, idx: number) => (
                        <div
                          key={ch.id || idx}
                          className="group flex items-center gap-2 p-2 border border-zinc-200 bg-white hover:border-black cursor-pointer transition-colors rounded-none"
                        >
                          <span className="text-xs font-medium text-zinc-400 group-hover:text-black w-4 transition-colors">
                            {idx + 1}
                          </span>
                          <span className="text-sm font-medium truncate flex-1 text-zinc-700 group-hover:text-black transition-colors">
                            {ch.title}
                          </span>
                          <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-all">
                            <button onClick={(e) => { e.stopPropagation(); moveChapter(idx, "up"); }} className="p-0.5 hover:bg-zinc-100 rounded-none"><ArrowUp className="w-3 h-3 text-zinc-400 hover:text-black" /></button>
                            <button onClick={(e) => { e.stopPropagation(); moveChapter(idx, "down"); }} className="p-0.5 hover:bg-zinc-100 rounded-none"><ArrowDown className="w-3 h-3 text-zinc-400 hover:text-black" /></button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
               </div>
               <div className="flex-1 overflow-y-auto no-scrollbar p-6 space-y-6">
                  <div className="space-y-4">
                    <h3 className="text-sm font-medium text-zinc-500">Tác phẩm khác</h3>
                    <div className="space-y-2">
                      {documents.filter(d => d._id !== selectedDocumentId).map((doc) => (
                        <button
                          key={doc._id}
                          onClick={() => setSelectedDocumentId(doc._id)}
                          className="w-full text-left p-4 border border-zinc-200 hover:border-black transition-colors bg-white group rounded-none flex flex-col gap-1"
                        >
                           <p className="text-sm font-medium text-zinc-700 group-hover:text-black truncate transition-colors">{doc.title}</p>
                           <div className="flex items-center gap-2">
                             <div className={`w-1.5 h-1.5 rounded-none ${doc.status === 'published' ? 'bg-black' : 'bg-zinc-300'}`} />
                             <span className="text-xs font-medium text-zinc-500">{doc.status === 'published' ? 'Xuất bản' : 'Bản nháp'}</span>
                           </div>
                        </button>
                      ))}
                    </div>
                  </div>
               </div>
             </>
           ) : (
             <div className="p-6">
                <h3 className="text-sm font-medium text-black mb-4">Danh sách tác phẩm</h3>
                <div className="space-y-2">
                  {documents.map((doc) => (
                    <button
                      key={doc._id}
                      onClick={() => setSelectedDocumentId(doc._id)}
                      className={`w-full text-left p-4 border transition-colors flex flex-col gap-1 rounded-none ${
                        selectedDocumentId === doc._id ? "bg-black text-white border-black" : "bg-white text-zinc-700 border-zinc-200 hover:border-black hover:text-black"
                      }`}
                    >
                      <span className="text-sm font-medium truncate">{doc.title}</span>
                      <span className={`text-xs font-medium ${selectedDocumentId === doc._id ? "text-zinc-300" : "text-zinc-500"}`}>{doc.status === 'published' ? 'Xuất bản' : 'Bản nháp'}</span>
                    </button>
                  ))}
                </div>
             </div>
           )}
        </aside>

        <main className="flex-1 bg-white overflow-hidden relative border-l border-zinc-200">
           {viewMode === "edit" && (
             <div className="h-full flex flex-col animate-in fade-in duration-300">
                <div className="h-12 border-b border-zinc-200 bg-white px-6 flex items-center justify-between shrink-0">
                   <div className="flex h-full gap-6">
                      {(["edit", "preview", "raw"] as const).map((m) => (
                        <button
                          key={m}
                          onClick={() => setEditorMode(m)}
                          className={`h-full text-sm font-medium transition-colors border-b-2 flex items-center ${
                            editorMode === m ? "border-black text-black" : "border-transparent text-zinc-500 hover:text-black"
                          }`}
                        >
                          {m === "edit" ? "Biên tập" : m === "preview" ? "Trải nghiệm" : "Dữ liệu thô"}
                        </button>
                      ))}
                   </div>
                </div>
                <div className="flex-1 overflow-y-auto p-2 lg:p-4 no-scrollbar bg-zinc-50/30">
                   <div className="w-full animate-in fade-in duration-300">
                      {editorMode === "edit" ? (
                        <Editor initialContent={content} onSave={(val) => setContent(val)} />
                      ) : editorMode === "preview" ? (
                        <div className="bg-white p-12 border border-zinc-200 rounded-none">
                          <div className="prose prose-zinc max-w-none font-sans text-base leading-relaxed text-black" dangerouslySetInnerHTML={{ __html: content }} />
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
             <div className="h-full overflow-y-auto p-8 md:p-12 animate-in fade-in duration-300 no-scrollbar">
                <div className="max-w-5xl mx-auto space-y-12">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                      { label: "Tổng lượt xem", val: stats?.total_views || 0, icon: Eye },
                      { label: "Mạng lưới độc giả", val: stats?.followers_count || 0, icon: Database },
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

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                     <button className="p-6 border border-zinc-200 bg-white hover:border-black transition-colors rounded-none flex flex-col items-center justify-center gap-3 h-24 group">
                       <Plus className="w-5 h-5 text-zinc-400 group-hover:text-black transition-colors" />
                       <span className="text-sm font-medium text-zinc-700">Tạo tài liệu</span>
                     </button>
                     <button className="p-6 border border-zinc-200 bg-white hover:border-black transition-colors rounded-none flex flex-col items-center justify-center gap-3 h-24 group">
                       <Brain className="w-5 h-5 text-zinc-400 group-hover:text-black transition-colors" />
                       <span className="text-sm font-medium text-zinc-700">Công cụ AI</span>
                     </button>
                     <button className="p-6 border border-zinc-200 bg-white hover:border-black transition-colors rounded-none flex flex-col items-center justify-center gap-3 h-24 group">
                       <Banknote className="w-5 h-5 text-zinc-400 group-hover:text-black transition-colors" />
                       <span className="text-sm font-medium text-zinc-700">Quản lý mã giảm giá</span>
                     </button>
                  </div>

                  <div className="bg-white border border-zinc-200 rounded-none">
                    <div className="p-6 border-b border-zinc-200 flex justify-between items-center">
                      <h3 className="text-base font-medium text-black">Tác phẩm gần đây</h3>
                      <button 
                        onClick={() => setShowPayoutModal(true)}
                        className="h-9 px-4 bg-black text-white text-sm font-medium hover:bg-zinc-800 transition-colors rounded-none flex items-center gap-2"
                      >
                        <Banknote className="w-4 h-4" /> Rút tiền doanh thu
                      </button>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-sm">
                        <thead>
                          <tr className="border-b border-zinc-200 text-zinc-500 font-medium">
                            <th className="px-6 py-4 font-medium">Tiêu đề tác phẩm</th>
                            <th className="px-6 py-4 font-medium">Lượt tương tác</th>
                            <th className="px-6 py-4 font-medium">Xếp hạng</th>
                            <th className="px-6 py-4 font-medium text-right">Hành động</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-200">
                          {(stats?.documents || []).map((doc: any) => (
                            <tr key={doc.id} className="hover:bg-zinc-50 transition-colors group cursor-pointer">
                              <td className="px-6 py-4 font-medium text-black">{doc.title}</td>
                              <td className="px-6 py-4 text-zinc-600">{doc.views.toLocaleString()}</td>
                              <td className="px-6 py-4">
                                <div className="flex items-center gap-2">
                                  <span className="text-zinc-600 font-medium">{doc.rating.toFixed(1)}</span>
                                </div>
                              </td>
                              <td className="px-6 py-4 text-right"><ChevronRight className="w-4 h-4 ml-auto text-zinc-400 group-hover:text-black transition-colors" /></td>
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
             <div className="h-full overflow-y-auto p-8 md:p-12 animate-in fade-in duration-300 no-scrollbar">
                <div className="max-w-3xl mx-auto bg-white border border-zinc-200 p-10 space-y-10 rounded-none">
                  <div className="space-y-4">
                    <h2 className="text-xl font-medium text-black">Trí tuệ nhân tạo</h2>
                    <p className="text-sm font-medium text-zinc-500 leading-relaxed">
                      Đồng bộ tri thức của bạn với hệ thống RAG để cho phép AI thấu hiểu và hỗ trợ độc giả tốt hơn.
                    </p>
                    <button
                      onClick={handleIngestAI}
                      disabled={isIngesting || !selectedDocumentId}
                      className="h-10 bg-black text-white px-6 text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center gap-2 rounded-none disabled:opacity-50 w-fit"
                    >
                      {isIngesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
                      Kích hoạt đồng bộ tri thức AI
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
                        className="h-10 border border-zinc-200 text-black px-6 text-sm font-medium hover:border-black hover:bg-zinc-50 transition-colors flex items-center gap-2 rounded-none disabled:opacity-50 whitespace-nowrap"
                      >
                        {generatingCover ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                        {selectedDocument?.cover_url ? "Tái tạo ảnh bìa" : "Tạo ảnh bìa AI"}
                      </button>
                    </div>

                    <div className="relative group max-w-[280px] rounded-none overflow-hidden">
                       <div className="aspect-[3/4] bg-zinc-50 border border-zinc-200 relative overflow-hidden group-hover:border-black transition-colors rounded-none flex items-center justify-center">
                          {selectedDocument?.cover_url ? (
                            <img
                              src={selectedDocument.cover_url.startsWith("http") ? selectedDocument.cover_url : `${API_URL}/storage/${selectedDocument.cover_url}`}
                              alt={selectedDocument.title}
                              className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500"
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
                  <div className="py-12 text-center">
                     <Settings className="w-8 h-8 text-zinc-300 mx-auto mb-4" />
                     <p className="text-sm font-medium text-zinc-500">Cấu hình nâng cao đang cập nhật</p>
                  </div>
                </div>
             </div>
           )}

           {viewMode === "versions" && (
             <div className="h-full overflow-y-auto p-8 md:p-12 animate-in fade-in duration-300 no-scrollbar">
                <div className="max-w-3xl mx-auto space-y-8">
                   <div className="bg-white border border-zinc-200 p-8 rounded-none flex items-center justify-between">
                      <div className="space-y-1">
                        <h2 className="text-xl font-medium text-black">Lịch sử phiên bản</h2>
                        <p className="text-sm font-medium text-zinc-500">Khôi phục tri thức tại các điểm thời gian</p>
                      </div>
                      <RotateCcw className="w-6 h-6 text-zinc-400" />
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
                          <div key={v.id} className="bg-white border border-zinc-200 p-6 flex items-center justify-between group hover:border-black transition-colors rounded-none">
                             <div className="flex items-center gap-4">
                                <div className="w-10 h-10 bg-zinc-50 flex items-center justify-center rounded-none border border-zinc-200">
                                   <Clock className="w-4 h-4 text-zinc-500" />
                                </div>
                                <div className="space-y-1">
                                   <p className="text-base font-medium text-black">{new Date(v.created_at).toLocaleString("vi-VN")}</p>
                                   <p className="text-sm font-medium text-zinc-500">Lưu bởi: {v.author_name || "Hệ thống"}</p>
                                </div>
                             </div>
                             <button 
                               onClick={() => handleRestoreVersion(v.id)}
                               className="h-9 px-4 border border-zinc-200 text-sm font-medium text-black hover:bg-black hover:text-white transition-colors rounded-none"
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
             <div className="h-full overflow-y-auto p-8 md:p-12 animate-in fade-in duration-300 no-scrollbar">
                <div className="max-w-3xl mx-auto space-y-8">
                   <div className="bg-white border border-zinc-200 p-8 rounded-none flex items-center justify-between">
                      <div className="space-y-1">
                        <h2 className="text-xl font-medium text-black">Thùng rác tri thức</h2>
                        <p className="text-sm font-medium text-zinc-500">Tài liệu đã tạm thời bị gỡ bỏ</p>
                      </div>
                      <Trash2 className="w-6 h-6 text-zinc-400" />
                   </div>
                   
                   <div className="space-y-4">
                      {loadingTrash ? (
                        <div className="py-12 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-zinc-400" /></div>
                      ) : trash.length === 0 ? (
                        <div className="bg-zinc-50 border border-zinc-200 p-16 text-center rounded-none flex flex-col items-center justify-center gap-3">
                           <X className="w-6 h-6 text-zinc-400" />
                           <p className="text-sm font-medium text-zinc-500">Thùng rác trống</p>
                        </div>
                      ) : (
                        trash.map((doc) => (
                          <div key={doc._id} className="bg-white border border-zinc-200 p-6 flex items-center justify-between group hover:border-black transition-colors rounded-none">
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
                               onClick={() => handleRestoreDocument(doc._id)}
                               className="h-9 px-4 border border-zinc-200 text-sm font-medium text-black hover:bg-black hover:text-white transition-colors rounded-none flex items-center gap-2"
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

           {viewMode === "sentiment" && (
             <div className="h-full overflow-y-auto p-8 md:p-12 animate-in fade-in duration-300 no-scrollbar">
                <div className="max-w-3xl mx-auto bg-white border border-zinc-200 p-16 text-center space-y-8 rounded-none">
                   <Brain className="w-12 h-12 text-zinc-400 mx-auto" />
                   <div className="space-y-3">
                      <h2 className="text-2xl font-medium text-black">Phân tích cảm quan AI</h2>
                      <p className="text-sm font-medium text-zinc-500 leading-relaxed max-w-md mx-auto">
                        AI sẽ đọc và phân tích tông giọng, cảm xúc và phản hồi của độc giả để giúp bạn tối ưu hóa nội dung.
                      </p>
                   </div>
                   <div className="py-12 border border-zinc-200 bg-zinc-50 rounded-none">
                      <p className="text-sm font-medium text-zinc-500">Tính năng đang được hiệu chuẩn</p>
                   </div>
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
    <Suspense fallback={<div className="flex-1 flex items-center justify-center min-h-screen"><Loader2 className="w-8 h-8 animate-spin text-zinc-300" /></div>}>
      <StudioContent />
    </Suspense>
  );
}
