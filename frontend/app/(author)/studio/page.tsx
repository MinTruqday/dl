"use client";

import { useEffect, useMemo, useState, useCallback, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  compileDocumentAPI,
  getDocumentDraftAPI,
  getDocumentsAPI,
  publishDocumentAPI,
  saveDocumentDraftAPI,
  getToken,
  API_URL,
  ingestDocumentAPI,
  getDocumentVersionsAPI,
  restoreVersionAPI,
  getTrashAPI,
  restoreDocumentAPI,
  softDeleteDocumentAPI,
  requestPayoutDetailedAPI,
  generateAICoverAPI,
  getMyDocumentsAPI,
} from "@/app/lib/api";
import { useAuth } from "@/app/contexts/AuthContext";
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
  RefreshCcw,
  Sparkles,
  Loader2,
  ChevronRight,
  Database,
  ArrowUp,
  ArrowDown,
  X,
  RotateCcw,
  AlertCircle,
  Banknote,
  LayoutDashboard,
  ChevronLeft,
  Search,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import TiptapEditor from "@/app/components/editor/TiptapEditor";
import { Notification } from "@/app/components/NotificationToast";

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

type ViewMode = "edit" | "stats" | "config" | "versions" | "trash";
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
      setNotification({ type: "error", text: "Lỗi tải danh sách tài liệu." });
    } finally {
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [docIdFromUrl, selectedDocumentId]);

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

  const fetchStats = useCallback(async () => {
    try {
      const headers = { Authorization: `Bearer ${getToken()}` };
      const [sRes, rRes] = await Promise.all([
        fetch(`${API_URL}/analytics/author/stats`, { headers }),
        fetch(`${API_URL}/wallet/revenue`, { headers }),
      ]);
      if (sRes.ok) setStats((await sRes.json()).data);
      if (rRes.ok) setRevenue((await rRes.json()).data);
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
  }, []);

  useEffect(() => {
    if (selectedDocumentId) {
      loadDraft();
      if (viewMode === "stats") fetchStats();
      if (viewMode === "versions") fetchVersions();
    } else {
      setContent("");
    }
    if (viewMode === "trash") fetchTrash();
  }, [selectedDocumentId, viewMode, loadDraft, fetchStats, fetchVersions, fetchTrash]);

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
      setNotification({ type: "success", text: "Đã khôi phục tài liệu thành công." });
      fetchTrash();
      fetchDocuments();
    } catch (e: any) {
      setNotification({ type: "error", text: e.message || "Lỗi khôi phục tài liệu." });
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
        setNotification({ type: "success", text: "Đã khôi phục phiên bản thành công." });
        loadDraft();
      } else if (confirmAction.type === "delete_doc") {
        await softDeleteDocumentAPI(confirmAction.id);
        setNotification({ type: "success", text: "Đã chuyển tài liệu vào thùng rác." });
        if (selectedDocumentId === confirmAction.id) setSelectedDocumentId("");
        fetchDocuments();
      }
    } catch (e: any) {
      setNotification({ type: "error", text: e.message || "Thao tác thất bại." });
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
      setNotification({ type: "success", text: "AI đã được cập nhật tri thức mới." });
    } catch (e: any) {
      setNotification({ type: "error", text: e.message || "Đồng bộ AI thất bại." });
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
      setNotification({ type: "success", text: "Ảnh bìa AI đã được khởi tạo và cập nhật." });
      fetchDocuments();
    } catch (e: any) {
      setNotification({ type: "error", text: e.message || "Tạo ảnh bìa thất bại." });
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
      setNotification({ type: "success", text: "Đã lưu bản nháp thành công." });
    } catch {
      setNotification({ type: "error", text: "Không thể lưu bản nháp." });
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
      setNotification({ type: "success", text: "Tài liệu đã được công bố thành công." });
      fetchDocuments();
    } catch {
      setNotification({ type: "error", text: "Xuất bản thất bại." });
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
      const res = await fetch(`${API_URL}/documents/${selectedDocumentId}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({ chapters: newChapters }),
      });
      if (res.ok) {
        setStatusMsg("Đã thay đổi thứ tự");
        fetchDocuments();
      }
    } catch (err: any) {
      console.error("Lỗi thao tác dữ liệu:", err);
    }
  };

  const addChapter = async () => {
    if (!newChapterTitle.trim()) return;
    const newChapter = { title: newChapterTitle, content: "Bắt đầu viết chương mới tại đây" };
    const newChapters = [...(selectedDocument?.chapters || []), newChapter];

    try {
      const res = await fetch(`${API_URL}/documents/${selectedDocumentId}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({ chapters: newChapters }),
      });
      if (res.ok) {
        setNotification({ type: "success", text: "Đã thêm chương mới." });
        setNewChapterTitle("");
        setShowChapterModal(false);
        fetchDocuments();
      }
    } catch (err: any) {
      console.error("Lỗi thao tác dữ liệu:", err);
    }
  };

  const updateDocumentConfig = async (updates: any) => {
    try {
      const res = await fetch(`${API_URL}/documents/${selectedDocumentId}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });
      if (res.ok) {
        setNotification({ type: "success", text: "Cấu hình đã được lưu." });
        fetchDocuments();
      }
    } catch (err: any) {
      console.error("Lỗi thao tác dữ liệu:", err);
    }
  };

  const handlePayout = async () => {
    if (payoutAmount <= 0) {
      setNotification({ type: "error", text: "Số tiền không hợp lệ." });
      return;
    }
    if (!bankInfo.bank_name || !bankInfo.account_number || !bankInfo.account_name) {
      setNotification({ type: "error", text: "Vui lòng nhập đủ thông tin ngân hàng." });
      return;
    }

    setRequestingPayout(true);
    try {
      await requestPayoutDetailedAPI(payoutAmount, bankInfo);
      setNotification({ type: "success", text: "Yêu cầu rút tiền đã được gửi." });
      setShowPayoutModal(false);
      fetchStats();
    } catch (e: any) {
      setNotification({ type: "error", text: e.message || "Yêu cầu rút tiền thất bại." });
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
    <div className="flex-1 flex flex-col h-[calc(100vh-var(--navbar-height))] overflow-hidden bg-white selection:bg-black selection:text-white relative">
      {/* Notifications & Modals */}
      {notification && (
        <div className="fixed top-24 right-8 z-[200] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmAction && (
        <div className="fixed inset-0 z-[250] flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="absolute inset-0 bg-black/40" onClick={() => setConfirmAction(null)} />
          <div className="bg-white w-full max-w-sm relative border border-zinc-200 p-10 space-y-8 shadow-2xl">
            <h3 className="text-sm font-bold tracking-tight uppercase">Xác nhận thao tác</h3>
            <p className="text-xs text-zinc-500 leading-relaxed font-medium italic">"{confirmAction.text}"</p>
            <div className="flex gap-4">
              <button onClick={() => setConfirmAction(null)} className="flex-1 h-12 text-[10px] font-bold uppercase tracking-widest border border-zinc-100 hover:bg-zinc-50 transition-all">
                Bỏ qua
              </button>
              <button onClick={executeConfirm} className="flex-1 h-12 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all">
                Xác nhận
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chapter Modal */}
      {showChapterModal && (
        <div className="fixed inset-0 z-[250] flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowChapterModal(false)} />
          <div className="bg-white w-full max-w-sm relative border border-zinc-200 p-10 space-y-8 shadow-2xl">
            <h3 className="text-sm font-bold tracking-tight uppercase">Thêm chương mới</h3>
            <input
              value={newChapterTitle}
              onChange={(e) => setNewChapterTitle(e.target.value)}
              placeholder=""
              className="w-full h-14 border border-zinc-100 px-5 font-bold text-xs focus:outline-none focus:border-black transition-all"
              autoFocus
            />
            <div className="flex gap-4">
              <button onClick={() => setShowChapterModal(false)} className="flex-1 h-12 text-[10px] font-bold uppercase tracking-widest border border-zinc-100 hover:bg-zinc-50 transition-all">
                Hủy
              </button>
              <button onClick={addChapter} className="flex-1 h-12 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all">
                Lưu chương
              </button>
            </div>
          </div>
        </div>
      )}

      {/* IDE Toolbar - Premium Standard */}
      <div className="h-16 border-b border-zinc-100 px-8 flex items-center justify-between bg-white shrink-0 z-30">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-4">
             <div className="w-8 h-8 bg-black flex items-center justify-center">
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
              className="h-10 px-6 border border-zinc-200 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {isSaving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              Lưu
            </button>
            <button
              onClick={handlePublish}
              disabled={!selectedDocumentId}
              className="h-10 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all disabled:opacity-50 active:scale-95"
            >
              Công bố
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Vertical Menu */}
        <nav className="w-16 border-r border-zinc-100 flex flex-col items-center py-8 gap-6 shrink-0 bg-white">
          {[
            { mode: "edit", icon: FileText, label: "Soạn thảo" },
            { mode: "stats", icon: BarChart3, label: "Số liệu" },
            { mode: "config", icon: Settings, label: "Cấu hình" },
            { mode: "versions", icon: Clock, label: "Lịch sử" },
            { mode: "trash", icon: Trash2, label: "Thùng rác" },
          ].map((item) => (
            <button
              key={item.mode}
              onClick={() => setViewMode(item.mode as ViewMode)}
              className={`p-3 transition-all relative group ${
                viewMode === item.mode ? "bg-black text-white" : "text-zinc-300 hover:text-black"
              }`}
              title={item.label}
            >
              <item.icon className="w-5 h-5" />
              <div className="absolute left-full ml-4 px-3 py-1.5 bg-black text-white text-[9px] font-bold uppercase tracking-widest whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-all z-50">
                {item.label}
              </div>
            </button>
          ))}
        </nav>

        {/* Navigation Sidebar (Chapters / List) */}
        <aside className="w-80 border-r border-zinc-100 flex flex-col shrink-0 bg-white animate-in slide-in-from-left duration-500">
           {viewMode === "edit" ? (
             <>
               <div className="p-8 border-b border-zinc-100 bg-zinc-50/20">
                  <div className="flex justify-between items-center mb-8">
                    <h3 className="text-[10px] font-bold text-black uppercase tracking-widest">Cấu trúc nội dung</h3>
                    <button
                      onClick={() => setShowChapterModal(true)}
                      className="text-[10px] font-bold text-black hover:underline flex items-center gap-2"
                    >
                      <Plus className="w-3 h-3" /> THÊM
                    </button>
                  </div>
                  <div className="space-y-2">
                    {!selectedDocument?.chapters || selectedDocument.chapters.length === 0 ? (
                      <div className="py-10 text-center border border-dashed border-zinc-100 flex flex-col items-center gap-3">
                         <Plus className="w-5 h-5 text-zinc-100" />
                         <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Chưa có chương</p>
                      </div>
                    ) : (
                      selectedDocument.chapters.map((ch: any, idx: number) => (
                        <div
                          key={ch.id || idx}
                          className="group flex items-center gap-4 p-4 border border-zinc-100 bg-white hover:border-black cursor-pointer transition-all duration-300"
                        >
                          <span className="text-[10px] font-bold text-zinc-200 group-hover:text-black w-4 transition-colors">
                            {idx + 1}
                          </span>
                          <span className="text-[11px] font-bold truncate flex-1 text-zinc-500 group-hover:text-black transition-colors tracking-tight">
                            {ch.title}
                          </span>
                          <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-all">
                            <button onClick={(e) => { e.stopPropagation(); moveChapter(idx, "up"); }} className="p-1 hover:bg-zinc-50"><ArrowUp className="w-2.5 h-2.5 text-zinc-300 hover:text-black" /></button>
                            <button onClick={(e) => { e.stopPropagation(); moveChapter(idx, "down"); }} className="p-1 hover:bg-zinc-50"><ArrowDown className="w-2.5 h-2.5 text-zinc-300 hover:text-black" /></button>
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
                          className="w-full text-left p-5 border border-zinc-50 hover:border-black transition-all duration-500 bg-white group"
                        >
                           <p className="text-[11px] font-bold text-zinc-400 group-hover:text-black truncate mb-2 transition-colors">{doc.title}</p>
                           <div className="flex items-center gap-3">
                             <div className={`w-1 h-1 ${doc.status === 'published' ? 'bg-black' : 'bg-zinc-200'}`} />
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
                <h3 className="text-[10px] font-bold text-black uppercase tracking-widest mb-8">Danh sách tài liệu</h3>
                <div className="space-y-3">
                  {documents.map((doc) => (
                    <button
                      key={doc._id}
                      onClick={() => setSelectedDocumentId(doc._id)}
                      className={`w-full text-left p-5 border transition-all duration-500 flex flex-col gap-2 ${
                        selectedDocumentId === doc._id ? "bg-black text-white border-black" : "bg-white text-zinc-400 border-zinc-50 hover:border-black hover:text-black"
                      }`}
                    >
                      <span className="text-[11px] font-bold truncate tracking-tight">{doc.title}</span>
                      <span className="text-[9px] font-bold opacity-40 uppercase tracking-widest">{doc.status || "draft"}</span>
                    </button>
                  ))}
                </div>
             </div>
           )}
        </aside>

        {/* Main Editor Area */}
        <main className="flex-1 bg-zinc-50/30 overflow-hidden relative">
           {viewMode === "edit" && (
             <div className="h-full flex flex-col animate-in fade-in duration-700">
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
                   <div className="max-w-4xl mx-auto shadow-2xl shadow-black/5 animate-in slide-in-from-bottom-6 duration-700">
                      {editorMode === "edit" ? (
                        <TiptapEditor initialContent={content} onSave={(val) => setContent(val)} />
                      ) : editorMode === "preview" ? (
                        <div className="bg-white p-20 border border-zinc-100">
                          <div className="prose prose-zinc max-w-none font-sans text-lg leading-relaxed text-zinc-800" dangerouslySetInnerHTML={{ __html: content }} />
                        </div>
                      ) : (
                        <pre className="p-16 bg-zinc-900 text-zinc-500 text-[11px] font-mono leading-relaxed overflow-auto min-h-[100vh]">
                          {content || "Nội dung hiện đang trống"}
                        </pre>
                      )}
                   </div>
                </div>
             </div>
           )}

           {viewMode === "stats" && (
             <div className="h-full overflow-y-auto p-16 animate-in fade-in duration-700 no-scrollbar">
                <div className="max-w-5xl mx-auto space-y-16">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {[
                      { label: "Ảnh hưởng", val: stats?.total_views || 0, icon: Eye, unit: "Lượt xem" },
                      { label: "Mạng lưới", val: stats?.followers_count || 0, icon: Database, unit: "Độc giả" },
                      { label: "Thu nhập", val: revenue?.available_balance || 0, icon: Wallet, unit: "dl" },
                    ].map((s, i) => (
                      <div key={i} className="bg-white p-12 border border-zinc-100 group hover:border-black transition-all duration-700">
                        <s.icon className="w-6 h-6 text-zinc-100 group-hover:text-black transition-colors mb-10" />
                        <h4 className="text-4xl font-bold tracking-tighter mb-2">{s.val.toLocaleString()} <span className="text-sm text-zinc-200">{s.unit}</span></h4>
                        <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{s.label}</p>
                      </div>
                    ))}
                  </div>

                  <div className="bg-white border border-zinc-100">
                    <div className="p-10 border-b border-zinc-100 flex justify-between items-center">
                      <h3 className="text-[11px] font-bold text-black uppercase tracking-widest">Chi tiết tác phẩm</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-zinc-50 text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                            <th className="px-10 py-6">Tiêu đề</th>
                            <th className="px-10 py-6">Tương tác</th>
                            <th className="px-10 py-6">Đánh giá</th>
                            <th className="px-10 py-6 text-right">Chi tiết</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-50">
                          {stats?.documents?.map((doc: any) => (
                            <tr key={doc.id} className="hover:bg-zinc-50/50 transition-colors group cursor-pointer">
                              <td className="px-10 py-8 font-bold text-zinc-500 group-hover:text-black transition-colors text-sm">{doc.title}</td>
                              <td className="px-10 py-8 font-bold text-black">{doc.views.toLocaleString()}</td>
                              <td className="px-10 py-8">
                                <div className="flex items-center gap-2">
                                  <span className="font-bold">{doc.rating.toFixed(1)}</span>
                                  <div className="flex gap-0.5">
                                    {[1, 2, 3, 4, 5].map(star => <div key={star} className={`w-1 h-1 ${star <= doc.rating ? 'bg-black' : 'bg-zinc-100'}`} />)}
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
             <div className="h-full overflow-y-auto p-16 animate-in fade-in duration-700 no-scrollbar">
                <div className="max-w-3xl mx-auto bg-white border border-zinc-100 p-16 space-y-12 shadow-2xl shadow-black/5">
                  <div className="space-y-6">
                    <h2 className="text-2xl font-bold tracking-tight">Trí tuệ nhân tạo</h2>
                    <p className="text-[11px] font-medium text-zinc-400 leading-relaxed italic">
                      Đồng bộ tri thức của bạn với hệ thống RAG để cho phép AI thấu hiểu và hỗ trợ độc giả tốt hơn.
                    </p>
                    <button
                      onClick={handleIngestAI}
                      disabled={isIngesting || !selectedDocumentId}
                      className="h-14 bg-black text-white px-10 text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all flex items-center gap-3 active:scale-[0.98]"
                    >
                      {isIngesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4 text-zinc-400" />}
                      Kích hoạt đồng bộ tri thức
                    </button>
                  </div>
                  <div className="h-px bg-zinc-50" />
                  
                  <div className="space-y-8">
                    <div className="flex justify-between items-end">
                      <div className="space-y-4">
                        <h2 className="text-2xl font-bold tracking-tight">Ảnh bìa AI</h2>
                        <p className="text-[11px] font-medium text-zinc-400 leading-relaxed italic max-w-md">
                          Hệ thống sẽ phân tích nội dung để tạo ra một ảnh bìa nghệ thuật phản ánh đúng linh hồn của tác phẩm.
                        </p>
                      </div>
                      <button
                        onClick={handleGenerateAICover}
                        disabled={generatingCover || !selectedDocumentId}
                        className="h-12 border border-black text-black px-8 text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-50 transition-all flex items-center gap-3 active:scale-[0.98]"
                      >
                        {generatingCover ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                        {selectedDocument?.cover_url ? "Tái tạo ảnh bìa" : "Tạo ảnh bìa bằng AI"}
                      </button>
                    </div>

                    <div className="relative group max-w-[280px] mx-auto lg:mx-0">
                       <div className="aspect-[3/4] bg-zinc-50 border border-zinc-100 relative overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-1000 shadow-2xl shadow-black/5">
                          {selectedDocument?.cover_url ? (
                            <img
                              src={selectedDocument.cover_url}
                              alt={selectedDocument.title}
                              className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
                            />
                          ) : (
                            <div className="w-full h-full flex flex-col items-center justify-center p-8 text-center gap-4">
                              <div className="w-12 h-12 bg-white flex items-center justify-center border border-zinc-100">
                                 <Sparkles className="w-6 h-6 text-zinc-200" />
                              </div>
                              <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Chưa có ảnh bìa</p>
                            </div>
                          )}
                          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-1000" />
                       </div>
                       
                       {selectedDocument?.cover_url && (
                         <div className="absolute -bottom-4 -right-4 bg-white border border-zinc-100 p-4 shadow-xl animate-in slide-in-from-top-2 duration-700">
                            <p className="text-[9px] font-bold uppercase tracking-widest text-zinc-400">AI Generated Standard</p>
                         </div>
                       )}
                    </div>
                  </div>
                  <div className="h-px bg-zinc-50" />
                  {/* Additional config options would go here */}
                  <div className="py-20 text-center opacity-10">
                     <Settings className="w-16 h-16 mx-auto mb-6" />
                     <p className="text-[10px] font-bold uppercase tracking-widest">Cấu hình nâng cao đang cập nhật</p>
                  </div>
                </div>
             </div>
           )}

           {/* Other modes: versions, trash would follow similar premium patterns */}
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
