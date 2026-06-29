"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { getDocumentsAPI, getMyDocumentsAPI, createDocumentAPI, updateDocumentAPI, deleteAuthorDocumentAPI, deleteAdminDocumentAPI, getFoldersAPI, createFolderAPI, deleteFolderAPI, lockDocumentAPI, toggleStarDocumentAPI } from "@/features/content/services/document_metadata.service";
import { uploadDocumentAPI } from "@/features/content/services/file_upload.service";
import { QRCodeSVG } from "qrcode.react";
import { AlertTriangle, FileText, Eye, Trash2, RefreshCcw, Loader2, X, Search, Upload, FileCheck, Plus, ChevronRight, Database, Lock, Share2, Globe, QrCode, FolderPlus, Folder, LayoutGrid, List, Star, Home } from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from "@/shared/components/ui/Modal";
import PageLoader from "@/shared/components/common/PageLoader";

export default function DocumentsPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();

  const [documents, setDocuments] = useState<any[]>([]);
  const [folders, setFolders] = useState<any[]>([]);
  const [currentFolder, setCurrentFolder] = useState<any>(null);
  const [breadcrumbs, setBreadcrumbs] = useState<any[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("list");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStar, setFilterStar] = useState(false);
  const [filterFormat, setFilterFormat] = useState("all");

  const [confirmModal, setConfirmModal] = useState<{ show: boolean; title: string; docId: string; type: "doc" | "folder"; } | null>(null);
  const [createDocModal, setCreateDocModal] = useState(false);
  const [createFolderModal, setCreateFolderModal] = useState(false);
  const [lockModal, setLockModal] = useState<{ show: boolean; docId: string; } | null>(null);
  const [shareModal, setShareModal] = useState<{ show: boolean; docId: string; } | null>(null);

  const [newDoc, setNewDoc] = useState({ title: "", description: "", slug: "", category: "Chưa phân loại", pages_count: 0, publisher_name: "", price_dl: 0, visibility: "public", status: "published", publish_at: "", is_featured: false, is_protected: false });
  const [folderName, setFolderName] = useState("");
  const [lockPassword, setLockPassword] = useState("");
  const [sharePassword, setSharePassword] = useState("");
  const [shareExpires, setShareExpires] = useState("7");
  const [isPublic, setIsPublic] = useState(true);
  const [publicUrl, setPublicUrl] = useState("");

  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isCreating, setIsCreating] = useState(false);

  const isAdmin = user?.role === "admin";
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const observerTarget = useRef<HTMLDivElement>(null);

  const fetchData = useCallback(async (isLoadMore = false) => {
    if (isRefreshing || (!hasMore && isLoadMore)) return;
    setIsRefreshing(true);
    try {
      const currentCursor = isLoadMore ? cursor : undefined;
      const [docsData, foldersData] = await Promise.all([
        isAdmin ? getDocumentsAPI(searchQuery, undefined, undefined, undefined, currentFolder?._id, filterStar, filterFormat, undefined, currentCursor || "", 20) : getMyDocumentsAPI(searchQuery, currentCursor || "", 20),
        !isLoadMore ? getFoldersAPI(currentFolder?._id) : Promise.resolve([])
      ]);
      let docs = docsData.data || docsData || [];
      if (!isAdmin) {
        if (currentFolder) docs = docs.filter((d: any) => d.folder_id === currentFolder._id); else docs = docs.filter((d: any) => !d.folder_id);
        if (filterStar) docs = docs.filter((d: any) => d.is_starred);
        if (filterFormat !== "all") docs = docs.filter((d: any) => d.file_url?.toLowerCase().endsWith(filterFormat));
        if (searchQuery) docs = docs.filter((d: any) => d.title.toLowerCase().includes(searchQuery.toLowerCase()) || (d.publisher_name || "").toLowerCase().includes(searchQuery.toLowerCase()));
      }
      setHasMore(docs.length >= 20);
      if (docs.length > 0) setCursor(docs[docs.length - 1].id || docs[docs.length - 1]._id);
      setDocuments(prev => isLoadMore ? [...prev, ...docs] : docs);
      if (!isLoadMore) setFolders(foldersData.data || foldersData || []);
    } catch (err: any) { showToast("Lỗi tải danh sách tài liệu", "error"); } finally { setIsRefreshing(false); setIsLoading(false); }
  }, [isAdmin, searchQuery, currentFolder, filterStar, filterFormat, cursor, hasMore, showToast, isRefreshing]);

  useEffect(() => { if (!authLoading && user) { fetchData(); setNewDoc(p => ({ ...p, publisher_name: isAdmin ? "DocLib" : user.full_name || "" })); } }, [user, authLoading, isAdmin]);
  useEffect(() => {
    const observer = new IntersectionObserver(entries => { if (entries[0].isIntersecting && hasMore && !isRefreshing) fetchData(true); }, { threshold: 0.5 });
    if (observerTarget.current) observer.observe(observerTarget.current);
    return () => observer.disconnect();
  }, [hasMore, isRefreshing, fetchData]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]; setFile(selectedFile);
      if (!newDoc.title) {
        const name = selectedFile.name.split(".")[0];
        setNewDoc(p => ({ ...p, title: name, slug: name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "") }));
      }
    }
  };

  const handleCreateDocument = async () => {
    if (!newDoc.title || !file) { showToast("Vui lòng nhập tiêu đề và chọn tệp", "error"); return; }
    setIsCreating(true);
    try {
      const submissionData = { ...newDoc, file_url: "", content_format: file.name.split(".").pop()?.toLowerCase() || "json", folder_id: currentFolder?._id || null, slug: newDoc.slug || newDoc.title.toLowerCase().replace(/\s+/g, "-") + "-" + Date.now().toString().slice(-4), publish_at: newDoc.status === "scheduled" ? newDoc.publish_at : null };
      const createdDoc = await createDocumentAPI(submissionData);
      try {
        const uploadRes = await uploadDocumentAPI(file);
        await updateDocumentAPI(createdDoc.data._id || createdDoc.data.id, { file_url: uploadRes.data.url, content_format: uploadRes.data.extension || submissionData.content_format });
      } catch (uploadErr) {
        await deleteAuthorDocumentAPI(createdDoc.data._id || createdDoc.data.id).catch(() => {});
        throw new Error("Lỗi tải file");
      }
      showToast("Khởi tạo tài liệu thành công", "success"); setCreateDocModal(false); setNewDoc({ title: "", description: "", slug: "", category: "Chưa phân loại", pages_count: 0, publisher_name: isAdmin ? "DocLib" : user?.full_name || "", price_dl: 0, visibility: "public", status: "published", publish_at: "", is_featured: false, is_protected: false }); setFile(null); fetchData();
    } catch (err: any) { showToast(err.message || "Lỗi hệ thống", "error"); } finally { setIsCreating(false); }
  };

  const handleCreateFolder = async () => { if (!folderName) return; try { await createFolderAPI(folderName, currentFolder?._id || null); showToast("Đã tạo thư mục", "success"); setCreateFolderModal(false); setFolderName(""); fetchData(); } catch (err: any) { showToast("Lỗi tạo thư mục", "error"); } };
  const executeDelete = async () => {
    if (!confirmModal) return;
    try {
      if (confirmModal.type === "doc") { if (isAdmin) await deleteAdminDocumentAPI(confirmModal.docId); else await deleteAuthorDocumentAPI(confirmModal.docId); } else await deleteFolderAPI(confirmModal.docId);
      showToast("Đã xóa thành công", "success"); fetchData();
    } catch (err: any) { showToast("Xóa thất bại", "error"); } finally { setConfirmModal(null); }
  };
  const handleLockDocument = async (e: React.FormEvent) => { e.preventDefault(); if (!lockModal?.docId || !lockPassword) return; try { await lockDocumentAPI(lockModal.docId, lockPassword); showToast("Đã khóa", "success"); setLockModal(null); setLockPassword(""); fetchData(); } catch (err: any) { showToast("Lỗi khóa", "error"); } };
  const handleShareSubmit = async (e: React.FormEvent) => { e.preventDefault(); if (!shareModal?.docId) return; setPublicUrl(`${window.location.origin}/document/viewer/${shareModal.docId}${sharePassword ? `?pwd=${sharePassword}` : ""}`); showToast("Sẵn sàng chia sẻ", "success"); };
  const toggleStar = async (id: string) => { try { await toggleStarDocumentAPI(id); fetchData(); } catch (err: any) { showToast("Lỗi thao tác", "error"); } };

  if (authLoading || isLoading) return <PageLoader />;

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] font-sans text-[#1D1D1F] flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-center justify-end gap-4">
        <div className="flex items-center gap-3">
          <button onClick={() => setCreateFolderModal(true)} className="pill-button bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] flex items-center gap-2"><FolderPlus className="w-4 h-4"/> Thư mục mới</button>
          <button onClick={() => setCreateDocModal(true)} className="pill-button flex items-center gap-2"><Plus className="w-4 h-4"/> Thêm tài liệu</button>
          <div className="flex bg-[#F5F5F7] rounded-[12px] p-0.5">
            <button onClick={() => setViewMode("list")} className={`p-1.5 rounded-[10px] transition-colors ${viewMode === "list" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}><List className="w-4 h-4" /></button>
            <button onClick={() => setViewMode("grid")} className={`p-1.5 rounded-[10px] transition-colors ${viewMode === "grid" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}><LayoutGrid className="w-4 h-4" /></button>
          </div>
          <button onClick={() => fetchData()} className="w-9 h-9 flex items-center justify-center rounded-[12px] bg-[#F5F5F7] text-[#6E6E73] hover:text-[#1D1D1F] transition-colors">{isRefreshing ? <Loader2 className="w-4 h-4 animate-spin"/> : <RefreshCcw className="w-4 h-4"/>}</button>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-8 flex-1 min-h-0">
        <aside className="lg:col-span-3 flex flex-col space-y-6 overflow-y-auto no-scrollbar pb-6 pr-2">
          <div className="bg-[#F5F5F7] rounded-[24px] p-6 space-y-4 shadow-sm">
            <h3 className="text-[17px] font-medium text-[#6E6E73] flex items-center gap-2"><Search className="w-4 h-4" /> Tìm kiếm</h3>
            <input type="text" placeholder="Nhập từ khóa..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="apple-input w-full bg-white" />
          </div>
          <div className="bg-[#F5F5F7] rounded-[24px] p-6 space-y-4 shadow-sm">
            <h3 className="text-[17px] font-medium text-[#6E6E73] flex items-center gap-2"><Database className="w-4 h-4" /> Lọc dữ liệu</h3>
            <button onClick={() => setFilterStar(!filterStar)} className={`w-full py-3 rounded-[14px] flex items-center justify-center gap-2 font-medium text-[14px] transition-colors ${filterStar ? "bg-[#1D1D1F] text-white" : "bg-white text-[#1D1D1F] border border-[#E8E8ED]"}`}><Star className={`w-4 h-4 ${filterStar ? "fill-white" : "text-[#6E6E73]"}`} /> Yêu thích</button>
            <div className="space-y-2 pt-2">
              <label className="text-[13px] font-medium text-[#6E6E73]">Định dạng</label>
              <div className="relative">
                <select value={filterFormat} onChange={(e) => setFilterFormat(e.target.value)} className="w-full h-[44px] bg-white border border-[#E8E8ED] px-4 text-[14px] font-medium focus:outline-none focus:border-[#0071E3] appearance-none rounded-[14px] shadow-sm">
                  <option value="all">Mọi định dạng</option><option value="pdf">PDF</option><option value="docx">Word</option><option value="xlsx">Excel</option><option value="pptx">PowerPoint</option><option value="zip">ZIP</option>
                </select>
                <ChevronRight className="w-5 h-5 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none rotate-90 text-[#6E6E73]" />
              </div>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-9 flex flex-col gap-6 h-full min-h-0 overflow-hidden">
          <div className="bg-[#F5F5F7] rounded-[24px] p-4 flex items-center gap-2 shadow-sm overflow-x-auto no-scrollbar">
            <button onClick={() => { setCurrentFolder(null); setBreadcrumbs([]); }} className={`flex items-center gap-2 px-4 py-2 rounded-[14px] font-medium text-[14px] transition-colors ${!currentFolder ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}><Home className="w-4 h-4"/>Gốc</button>
            {breadcrumbs.map((b, idx) => (
              <div key={b._id} className="flex items-center gap-2 shrink-0">
                <ChevronRight className="w-4 h-4 text-[#A1A1A6]"/>
                <button onClick={() => { const nb = breadcrumbs.slice(0, idx + 1); setBreadcrumbs(nb); setCurrentFolder(nb[nb.length - 1]); }} className={`px-4 py-2 rounded-[14px] font-medium text-[14px] transition-colors ${idx === breadcrumbs.length - 1 ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}>{b.name}</button>
              </div>
            ))}
          </div>

          {viewMode === "list" ? (
            <div className="bg-[#F5F5F7] rounded-[24px] border-[#E8E8ED] flex-1 overflow-y-auto no-scrollbar">
              <table className="w-full text-left">
                <thead className="sticky top-0 bg-white z-10 border-b border-[#E8E8ED]">
                  <tr className="text-[13px] text-[#6E6E73]">
                    <th className="px-6 py-4 font-medium">Tên</th><th className="px-6 py-4 font-medium">Loại</th><th className="px-6 py-4 font-medium">Bảo mật</th><th className="px-6 py-4 font-medium text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {folders.map(folder => (
                    <tr key={folder._id} onClick={() => { setCurrentFolder(folder); setBreadcrumbs([...breadcrumbs, folder]); }} className="border-b border-[#F5F5F7] hover:bg-[#F5F5F7] cursor-pointer transition-colors group">
                      <td className="px-6 py-4"><div className="flex items-center gap-4"><div className="w-10 h-10 bg-white border border-[#E8E8ED] flex items-center justify-center rounded-[12px] text-[#1D1D1F]"><Folder className="w-5 h-5"/></div><span className="font-medium text-[#1D1D1F]">{folder.name}</span></div></td>
                      <td className="px-6 py-4"><span className="text-[12px] bg-[#F5F5F7] text-[#6E6E73] px-3 py-1 rounded-full font-medium">Thư mục</span></td>
                      <td className="px-6 py-4 text-[#6E6E73]">--</td>
                      <td className="px-6 py-4 text-right"><button onClick={(e) => { e.stopPropagation(); setConfirmModal({ show: true, title: "Xóa thư mục?", docId: folder._id, type: "folder" }); }} className="p-2 text-[#6E6E73] hover:text-[#FF3B30] hover:bg-[#FF3B30]/10 rounded-full opacity-0 group-hover:opacity-100 transition-all"><Trash2 className="w-4 h-4"/></button></td>
                    </tr>
                  ))}
                  {documents.map(doc => (
                    <tr key={doc._id || doc.id} className="border-b border-[#F5F5F7] hover:bg-[#F5F5F7] transition-colors group">
                      <td className="px-6 py-4"><div className="flex items-center gap-4"><div className="w-10 h-12 bg-white border border-[#E8E8ED] flex items-center justify-center rounded-[12px] text-[#6E6E73]"><FileText className="w-5 h-5"/></div><div><p className="font-medium text-[#1D1D1F] max-w-sm truncate">{doc.title}</p><p className="text-[12px] text-[#6E6E73] mt-0.5">{doc.publisher_name || "DocLib"} • {doc.category || "Tài liệu"}</p></div></div></td>
                      <td className="px-6 py-4"><span className={`text-[12px] px-3 py-1 rounded-full font-medium ${doc.status === "published" ? "bg-[#E8F3FF] text-[#0071E3]" : "bg-[#F5F5F7] text-[#6E6E73]"}`}>{doc.status === "published" ? "Đã đăng" : "Bản nháp"}</span></td>
                      <td className="px-6 py-4">{doc.is_protected ? <span className="flex items-center gap-1 text-[13px] text-[#1D1D1F]"><Lock className="w-4 h-4"/> Đã khóa</span> : <span className="text-[13px] text-[#6E6E73]">Không</span>}</td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => toggleStar(doc._id || doc.id)} className={`p-2 rounded-[10px] transition-colors ${doc.is_starred ? "text-[#FF9500] bg-[#FF9500]/10" : "text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F]"}`}><Star className={`w-4 h-4 ${doc.is_starred ? "fill-[#FF9500]" : ""}`}/></button>
                          <button onClick={() => setLockModal({ show: true, docId: doc._id || doc.id })} className="p-2 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[10px] transition-colors"><Lock className="w-4 h-4"/></button>
                          <button onClick={() => setShareModal({ show: true, docId: doc._id || doc.id })} className="p-2 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[10px] transition-colors"><Share2 className="w-4 h-4"/></button>
                          <button onClick={() => window.open(`/document/viewer/${doc._id || doc.id}`, "_blank")} className="p-2 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[10px] transition-colors"><Eye className="w-4 h-4"/></button>
                          <button onClick={() => setConfirmModal({ show: true, title: "Xóa tài liệu?", docId: doc._id || doc.id, type: "doc" })} className="p-2 text-[#6E6E73] hover:bg-[#FF3B30]/10 hover:text-[#FF3B30] rounded-[10px] transition-colors"><Trash2 className="w-4 h-4"/></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-6 overflow-y-auto no-scrollbar pb-6 pr-2">
              {folders.map(folder => (
                <div key={folder._id} onClick={() => { setCurrentFolder(folder); setBreadcrumbs([...breadcrumbs, folder]); }} className="bg-[#F5F5F7] border-[#E8E8ED] p-6 flex flex-col items-center justify-center gap-3 cursor-pointer rounded-[24px] hover: transition-shadow group">
                  <div className="w-16 h-16 bg-[#F5F5F7] flex items-center justify-center rounded-[16px] text-[#1D1D1F]"><Folder className="w-8 h-8"/></div>
                  <span className="text-[15px] font-medium text-[#1D1D1F] text-center">{folder.name}</span>
                </div>
              ))}
              {documents.map(doc => (
                <div key={doc._id || doc.id} className="bg-[#F5F5F7] border-[#E8E8ED] p-5 flex flex-col rounded-[24px] hover: transition-shadow group relative">
                  <button onClick={() => toggleStar(doc._id || doc.id)} className="absolute top-4 right-4 z-10 p-2 bg-white/80 backdrop-blur-md rounded-full shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"><Star className={`w-4 h-4 ${doc.is_starred ? "text-[#FF9500] fill-[#FF9500]" : "text-[#6E6E73]"}`}/></button>
                  <div className="flex flex-col items-center gap-4 mb-4 mt-2">
                    <div className="w-24 h-32 bg-[#F5F5F7] flex items-center justify-center rounded-[14px] text-[#A1A1A6] overflow-hidden border border-[#E8E8ED]">
                      {doc.cover_url ? <img src={doc.cover_url} className="w-full h-full object-cover" alt="" /> : <FileText className="w-10 h-10"/>}
                    </div>
                    <div className="text-center w-full px-2">
                      <p className="text-[15px] font-medium text-[#1D1D1F] truncate w-full">{doc.title}</p>
                      <p className="text-[12px] text-[#6E6E73] truncate w-full mt-1">{doc.category || "Tài liệu"}</p>
                    </div>
                  </div>
                  <div className="mt-auto border-t border-[#F5F5F7] pt-4 flex justify-between gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => window.open(`/document/viewer/${doc._id || doc.id}`, "_blank")} className="flex-1 py-2 text-[#6E6E73] bg-[#F5F5F7] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[12px] flex justify-center transition-colors"><Eye className="w-4 h-4"/></button>
                    <button onClick={() => setLockModal({ show: true, docId: doc._id || doc.id })} className="flex-1 py-2 text-[#6E6E73] bg-[#F5F5F7] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[12px] flex justify-center transition-colors"><Lock className="w-4 h-4"/></button>
                    <button onClick={() => setShareModal({ show: true, docId: doc._id || doc.id })} className="flex-1 py-2 text-[#6E6E73] bg-[#F5F5F7] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[12px] flex justify-center transition-colors"><Share2 className="w-4 h-4"/></button>
                    <button onClick={() => setConfirmModal({ show: true, title: "Xóa tài liệu?", docId: doc._id || doc.id, type: "doc" })} className="flex-1 py-2 text-[#FF3B30] bg-[#FF3B30]/10 hover:bg-[#FF3B30]/20 rounded-[12px] flex justify-center transition-colors"><Trash2 className="w-4 h-4"/></button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {documents.length === 0 && folders.length === 0 && !isLoading && (
            <div className="flex-1 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[24px] border-[#E8E8ED]">
              <Search className="w-12 h-12 text-[#C7C7CC] mb-4"/>
              <h2 className="text-[20px] font-medium text-[#1D1D1F]">Không có tài liệu</h2>
              <p className="text-[14px] text-[#6E6E73] mt-2">Thư mục hiện đang trống.</p>
            </div>
          )}

          {isRefreshing && hasMore && <div className="h-10 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-[#6E6E73]"/></div>}
          <div ref={observerTarget} className="h-10"></div>
        </main>
      </div>

      <Modal isOpen={!!confirmModal} onClose={() => setConfirmModal(null)} className="max-w-md bg-[#F5F5F7] rounded-[24px] p-0 shadow-2xl border-none">
        <ModalHeader className="p-6 pb-2"><ModalTitle className="text-[20px] font-semibold text-[#FF3B30] flex items-center gap-2"><AlertTriangle className="w-5 h-5"/> Cảnh báo xóa</ModalTitle></ModalHeader>
        <ModalContent className="p-6 pt-2"><p className="text-[15px] text-[#6E6E73]">Bạn có chắc chắn muốn xóa <strong className="text-[#1D1D1F]">{confirmModal?.title}</strong>? Hành động này không thể hoàn tác.</p></ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3"><button onClick={() => setConfirmModal(null)} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full">Hủy</button><button onClick={executeDelete} className="pill-button bg-[#FF3B30] hover:bg-[#D70015]">Xóa vĩnh viễn</button></ModalFooter>
      </Modal>

      <Modal isOpen={createDocModal} onClose={() => setCreateDocModal(false)} className="max-w-3xl bg-[#F5F5F7] rounded-[24px] p-0 shadow-2xl border-none">
        <ModalHeader className="p-6 border-b border-[#E8E8ED] bg-white rounded-t-[24px]"><ModalTitle className="text-[20px] font-semibold">Khởi tạo tài liệu</ModalTitle></ModalHeader>
        <ModalContent className="p-6 grid md:grid-cols-2 gap-8">
          <div className="space-y-4">
            <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Tiêu đề</label><input type="text" value={newDoc.title} onChange={(e) => setNewDoc({ ...newDoc, title: e.target.value })} className="apple-input w-full bg-white"/></div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Thể loại</label><select value={newDoc.category} onChange={(e) => setNewDoc({ ...newDoc, category: e.target.value })} className="apple-input w-full bg-white"><option value="Chưa phân loại">Chưa phân loại</option><option value="Giáo trình">Giáo trình</option><option value="Kỹ thuật">Kỹ thuật</option><option value="Nghiên cứu">Nghiên cứu</option></select></div>
              <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Giá (dl)</label><input type="number" value={newDoc.price_dl} onChange={(e) => setNewDoc({ ...newDoc, price_dl: parseInt(e.target.value) || 0 })} className="apple-input w-full bg-white"/></div>
            </div>
            <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Mô tả</label><textarea value={newDoc.description} onChange={(e) => setNewDoc({ ...newDoc, description: e.target.value })} className="apple-input w-full bg-white h-24 resize-none p-3 rounded-[16px]"/></div>
          </div>
          <div className="space-y-4">
            <div>
              <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Tệp đính kèm</label>
              <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept=".pdf,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.txt,.zip,.csv,.json,.md" />
              <div onClick={() => fileInputRef.current?.click()} className="h-32 bg-[#F5F5F7] border-[#E8E8ED] rounded-[18px] flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-[#0071E3] transition-colors border-dashed">
                <div className="w-10 h-10 bg-[#F5F5F7] rounded-full flex items-center justify-center text-[#0071E3]">{file ? <FileCheck className="w-5 h-5"/> : <Upload className="w-5 h-5"/>}</div>
                <p className="text-[14px] font-medium text-[#1D1D1F]">{file ? file.name : "Chọn tệp tin"}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Hiển thị</label><select value={newDoc.visibility} onChange={(e) => setNewDoc({ ...newDoc, visibility: e.target.value })} className="apple-input w-full bg-white"><option value="public">Công khai</option><option value="private">Riêng tư</option></select></div>
              <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Trạng thái</label><select value={newDoc.status} onChange={(e) => setNewDoc({ ...newDoc, status: e.target.value })} className="apple-input w-full bg-white"><option value="published">Xuất bản</option><option value="draft">Bản nháp</option></select></div>
            </div>
          </div>
        </ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3"><button onClick={() => setCreateDocModal(false)} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full">Hủy</button><button onClick={handleCreateDocument} disabled={isCreating || !file || !newDoc.title} className="pill-button disabled:opacity-50 flex items-center gap-2">{isCreating ? <Loader2 className="w-4 h-4 animate-spin"/> : "Tải lên"}</button></ModalFooter>
      </Modal>

      <Modal isOpen={createFolderModal} onClose={() => setCreateFolderModal(false)} className="max-w-sm bg-[#F5F5F7] rounded-[24px] p-0 shadow-2xl border-none">
        <ModalHeader className="p-6"><ModalTitle className="text-[20px] font-semibold">Tạo thư mục</ModalTitle></ModalHeader>
        <ModalContent className="p-6 pt-0"><input type="text" value={folderName} onChange={(e) => setFolderName(e.target.value)} placeholder="Tên thư mục" className="apple-input w-full bg-white" autoFocus /></ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3"><button onClick={() => setCreateFolderModal(false)} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full">Hủy</button><button onClick={handleCreateFolder} disabled={!folderName} className="pill-button disabled:opacity-50">Tạo</button></ModalFooter>
      </Modal>

      <Modal isOpen={!!lockModal} onClose={() => setLockModal(null)} className="max-w-sm bg-[#F5F5F7] rounded-[24px] p-0 shadow-2xl border-none">
        <ModalHeader className="p-6"><ModalTitle className="text-[20px] font-semibold flex items-center gap-2"><Lock className="w-5 h-5"/> Khóa tài liệu</ModalTitle></ModalHeader>
        <ModalContent className="p-6 pt-0"><form id="lock-form" onSubmit={handleLockDocument}><input type="password" placeholder="Mật khẩu bảo vệ" value={lockPassword} onChange={(e) => setLockPassword(e.target.value)} className="apple-input w-full bg-white" required autoFocus/></form></ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3"><button onClick={() => setLockModal(null)} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full">Hủy</button><button type="submit" form="lock-form" className="pill-button">Khóa</button></ModalFooter>
      </Modal>

      <Modal isOpen={!!shareModal} onClose={() => setShareModal(null)} className="max-w-md bg-[#F5F5F7] rounded-[24px] p-0 shadow-2xl border-none">
        <ModalHeader className="p-6"><ModalTitle className="text-[20px] font-semibold flex items-center gap-2"><Share2 className="w-5 h-5"/> Chia sẻ tài liệu</ModalTitle></ModalHeader>
        <ModalContent className="p-6 pt-0 space-y-4">
          <form id="share-form" onSubmit={handleShareSubmit} className="space-y-4">
            <div className="flex items-center gap-3 bg-[#F5F5F7] p-4 rounded-[16px] border-[#E8E8ED]"><input type="checkbox" checked={isPublic} onChange={(e) => setIsPublic(e.target.checked)} className="w-5 h-5 rounded-[6px] border-[#C7C7CC] accent-[#0071E3]" /><span className="text-[15px] font-medium">Bật liên kết công khai</span></div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Mật khẩu (Tùy chọn)</label><input type="password" value={sharePassword} onChange={(e) => setSharePassword(e.target.value)} className="apple-input w-full bg-white" /></div>
              <div><label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Thời hạn</label><select value={shareExpires} onChange={(e) => setShareExpires(e.target.value)} className="apple-input w-full bg-white"><option value="1">24 giờ</option><option value="7">7 ngày</option><option value="30">30 ngày</option></select></div>
            </div>
            {publicUrl && (
              <div className="bg-[#F5F5F7] p-6 rounded-[18px] border-[#E8E8ED] flex flex-col items-center gap-4 mt-4">
                <input type="text" readOnly value={publicUrl} className="apple-input w-full text-center bg-[#F5F5F7] text-[#0071E3]" onFocus={e=>e.target.select()} />
                <div className="p-2 bg-white rounded-xl shadow-sm border border-[#E8E8ED]"><QRCodeSVG value={publicUrl} size={100} /></div>
              </div>
            )}
          </form>
        </ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3"><button onClick={() => { setShareModal(null); setPublicUrl(""); }} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full">Đóng</button><button type="submit" form="share-form" className="pill-button">Tạo liên kết</button></ModalFooter>
      </Modal>
    </div>
  );
}
