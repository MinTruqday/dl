import { useToast } from "@/contexts/ToastContext";
"use client";

import React, { useState, useEffect, useRef } from "react";
import Workspace from "@/components/Workspace";
import { 
  Folder, FileText, Search, Plus, Upload, Trash2, Home, File, 
  Image as ImageIcon, CheckCircle, ChevronRight, Download, Star, 
  Lock, Unlock, Database, Filter, LayoutGrid, List, Tag, Globe, 
  Share2, Archive, DollarSign, Send, History, QrCode, ShieldAlert,
  Loader2, MoreHorizontal, Settings, Info
} from "lucide-react";
import Link from "next/link";
import { getToken, API_URL } from "@/services/auth.service";
import { 
  getFoldersAPI, 
  getDocumentsAPI, 
  createFolderAPI, 
  uploadDocumentAPI, 
  deleteFolderAPI, 
  deleteDocumentAPI, 
  toggleStarDocumentAPI, 
  lockDocumentAPI, 
  monetizeDocumentAPI, 
  transferDocumentAPI, 
  getAuditLogsAPI 
} from "@/services/document.service";
import { getStorageQuotaAPI } from "@/services/storage.service";
import { formatBytes } from "@/app/lib/utils";

export default function DocumentsPage() {
  const [currentFolder, setCurrentFolder] = useState<any>(null);
  const [folders, setFolders] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [quota, setQuota] = useState<{used: number, limit: number, percent: number}>({used: 0, limit: 5000000000, percent: 0});
  const [filterStar, setFilterStar] = useState(false);
  const [filterFormat, setFilterFormat] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"grid"|"list">("grid");
  const [breadcrumbs, setBreadcrumbs] = useState<any[]>([]);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const [isFolderModalOpen, setIsFolderModalOpen] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [lockDocId, setLockDocId] = useState<string | null>(null);
  const [lockPassword, setLockPassword] = useState("");
  const [shareDocId, setShareDocId] = useState<string | null>(null);
  const [isPublic, setIsPublic] = useState(false);
  const [sharePassword, setSharePassword] = useState("");
  const [shareExpires, setShareExpires] = useState("7");
  const [publicUrl, setPublicUrl] = useState("");
  const [monetizeDocId, setMonetizeDocId] = useState<string|null>(null);
  const [monetizePrice, setMonetizePrice] = useState<number>(0);
  const [transferDocId, setTransferDocId] = useState<string|null>(null);
  const [transferTargetId, setTransferTargetId] = useState<string>("");
  const [auditDocId, setAuditDocId] = useState<string|null>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, [currentFolder, search, filterStar, filterFormat]);

  const loadData = async () => {
    setLoading(true);
    try {
      const folderId = currentFolder ? currentFolder._id : undefined;
      const [fData, dData, qData] = await Promise.all([
        getFoldersAPI(search ? undefined : folderId),
        getDocumentsAPI(folderId, search, filterStar, filterFormat),
        getStorageQuotaAPI().catch(() => ({used: 0, limit: 5000000000, percent: 0}))
      ]);
      setFolders((search || filterStar || filterFormat !== "all") ? [] : fData); 
      setDocuments(dData);
      setQuota(qData);
    } catch (e) {
        showToast("Không thể kết nối mạng lưới dữ liệu DocLib", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFolderName.trim()) return;
    try {
      await createFolderAPI(newFolderName, currentFolder ? currentFolder._id : null);
      setIsFolderModalOpen(false);
      setNewFolderName("");
      showToast("Đã tạo thư mục lưu trữ mới", "success");
      loadData();
    } catch (e) {
      showToast("Giao thức tạo thư mục thất bại", "error");
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileToUpload || !uploadTitle.trim()) return;
    setUploading(true);
    try {
      await uploadDocumentAPI(fileToUpload, uploadTitle, currentFolder ? currentFolder._id : null, []);
      setIsUploadModalOpen(false);
      setFileToUpload(null);
      setUploadTitle("");
      showToast("Đã tích hợp tài liệu vào hệ thống", "success");
      loadData();
    } catch (e) {
      showToast("Giao thức tải lên thất bại", "error");
    } finally {
      setUploading(false);
    }
  };

  const handleToggleStar = async (id: string, e: React.MouseEvent) => {
    e.preventDefault(); e.stopPropagation();
    try {
        await toggleStarDocumentAPI(id);
        loadData();
    } catch (err) {
        showToast("Giao thức đánh dấu thất bại", "error");
    }
  };

  const handleLockDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lockDocId || !lockPassword) return;
    try {
      await lockDocumentAPI(lockDocId, lockPassword);
      setLockDocId(null);
      setLockPassword("");
      showToast("Đã thiết lập lớp bảo mật cho thực thể", "success");
      loadData();
    } catch(err) {
      showToast("Giao thức bảo mật thất bại", "error");
    }
  };

  const handleShareSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if(!shareDocId) return;
    try {
       const token = getToken();
       const res = await fetch(`${API_URL}/documents/${shareDocId}/share?is_public=${isPublic}&password=${sharePassword}&expires_in_days=${shareExpires}`, {
         method: "POST",
         headers: { "Authorization": `Bearer ${token}` }
       });
       if (res.ok) {
           setPublicUrl(`${window.location.origin}/documents/viewer/${shareDocId}?pwd=${sharePassword}`);
           showToast("Giao thức chia sẻ đã được kích hoạt", "success");
       }
    } catch(e) { 
        showToast("Giao thức chia sẻ thất bại", "error");
    }
  }

  const handleDeleteFolder = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
        await deleteFolderAPI(id);
        showToast("Đã loại bỏ thư mục khỏi hệ thống", "success");
        loadData();
    } catch (err) {
        showToast("Giao thức xóa thư mục thất bại", "error");
    }
  };

  const handleDeleteDoc = async (id: string, e: React.MouseEvent) => {
    e.preventDefault(); e.stopPropagation();
    try {
        await deleteDocumentAPI(id, true);
        showToast("Đã loại bỏ tài liệu khỏi hệ thống", "success");
        loadData();
    } catch (err) {
        showToast("Giao thức xóa tài liệu thất bại", "error");
    }
  };

  const getFileIcon = (fmt: string) => {
    const className = "w-10 h-10 text-black stroke-[1.5]";
    if(['pdf'].includes(fmt)) return <FileText className={className} />;
    if(['doc', 'docx'].includes(fmt)) return <FileText className={className} />;
    if(['jpg', 'png', 'jpeg'].includes(fmt)) return <ImageIcon className={className} />;
    return <File className={className} />;
  };

  return (
    <Workspace>
      <div className="max-w-7xl mx-auto px-10 py-12 pb-24 w-full font-sans">
        

        <div className="flex flex-col md:flex-row md:items-end justify-between gap-12 mb-20 border-b border-zinc-100 pb-16">
          <div className="space-y-4">
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-black flex items-center justify-center rounded-sm">
                    <Database className="w-6 h-6 text-white" />
                </div>
                <h1 className="text-2xl font-bold text-black uppercase tracking-widest">Tài liệu & Học liệu</h1>
            </div>
            <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest leading-loose max-w-lg">Quản lý, phân loại và kiến tạo không gian tri thức cá nhân hóa</p>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="relative group">
              <Search className="w-4 h-4 absolute left-5 top-5 text-zinc-300 group-focus-within:text-black transition-all" />
              <input 
                type="text" 
                placeholder="" 
                className="w-80 pl-14 h-14 bg-zinc-50/50 border border-zinc-100 text-[11px] font-bold uppercase tracking-widest focus:outline-none focus:border-black focus:bg-white transition-all rounded-sm placeholder:text-zinc-200"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button
              onClick={() => setIsFolderModalOpen(true)}
              className="h-14 px-8 border border-zinc-100 flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest hover:border-black hover:bg-zinc-50 transition-all active:scale-95 rounded-sm"
            >
              <Plus className="w-4 h-4" /> Thư mục
            </button>
            <button 
              onClick={() => setIsUploadModalOpen(true)}
              className="h-14 px-10 bg-black text-white flex items-center gap-4 text-[10px] font-bold uppercase tracking-[0.3em] hover:bg-zinc-800 transition-all active:scale-95 rounded-sm"
            >
              <Upload className="w-4 h-4" /> Tải lên
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-12 mb-16">
          <div className="flex items-center gap-6">
            <button 
                onClick={() => { setFilterStar(false); setFilterFormat("all"); }} 
                className={`px-8 h-12 text-[10px] font-bold uppercase tracking-widest transition-all rounded-sm border ${!filterStar && filterFormat==="all" ? "bg-black text-white border-black" : "bg-white text-zinc-300 border-zinc-100 hover:border-black hover:text-black"}`}
            >
                Tất cả
            </button>
            <button 
                onClick={() => setFilterStar(!filterStar)} 
                className={`px-8 h-12 text-[10px] font-bold uppercase tracking-widest transition-all rounded-sm border flex items-center gap-3 ${filterStar ? "bg-black text-white border-black" : "bg-white text-zinc-300 border-zinc-100 hover:border-black hover:text-black"}`}
            >
                <Star className={`w-3.5 h-3.5 ${filterStar ? "fill-white" : ""}`} /> Yêu thích
            </button>
            
            <div className="h-6 w-px bg-zinc-100 mx-4"></div>
            
            <select 
                value={filterFormat} 
                onChange={(e) => setFilterFormat(e.target.value)} 
                className="h-12 border border-zinc-100 px-6 text-[10px] font-bold uppercase tracking-widest focus:outline-none focus:border-black transition-all rounded-sm bg-white text-black"
            >
              <option value="all">Mọi định dạng</option>
              <option value="pdf">Định dạng PDF</option>
              <option value="docx">Văn bản Word</option>
              <option value="latex">Mã nguồn LaTeX</option>
            </select>
          </div>
          
          <div className="flex items-center gap-8 min-w-[320px]">
            <div className="flex-1 space-y-3">
              <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest text-zinc-400 px-1">
                <span>Dung lượng lưu trữ</span>
                <span>{formatBytes(quota.used)} / {formatBytes(quota.limit)}</span>
              </div>
              <div className="h-1 bg-zinc-50 rounded-full overflow-hidden">
                <div className="h-full bg-black transition-all duration-1000" style={{width: `${Math.max(quota.percent, 2)}%`}}></div>
              </div>
            </div>
            <div className="flex bg-zinc-50 p-1 border border-zinc-100 rounded-sm">
                <button onClick={() => setViewMode("grid")} className={`p-2.5 transition-all rounded-sm ${viewMode === 'grid' ? 'bg-black text-white' : 'text-zinc-200 hover:text-black'}`}><LayoutGrid className="w-4 h-4"/></button>
                <button onClick={() => setViewMode("list")} className={`p-2.5 transition-all rounded-sm ${viewMode === 'list' ? 'bg-black text-white' : 'text-zinc-200 hover:text-black'}`}><List className="w-4 h-4"/></button>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 mb-16 p-4 bg-zinc-50/20 border border-zinc-50 rounded-sm overflow-x-auto scrollbar-none">
            <button onClick={() => { setCurrentFolder(null); setBreadcrumbs([]); }} className="p-2 text-zinc-300 hover:text-black transition-all active:scale-90"><Home className="w-4 h-4" /></button>
            {breadcrumbs.map((b, idx) => (
              <React.Fragment key={b._id}>
                <ChevronRight className="w-3.5 h-3.5 text-zinc-100" />
                <button 
                  onClick={() => {
                      const newBread = breadcrumbs.slice(0, idx + 1);
                      setBreadcrumbs(newBread);
                      setCurrentFolder(newBread[newBread.length - 1]);
                  }}
                  className={`text-[10px] font-bold uppercase tracking-widest transition-all px-4 py-2 rounded-sm ${idx === breadcrumbs.length - 1 ? 'bg-black text-white' : 'text-zinc-300 hover:text-black hover:bg-zinc-50'}`}
                >
                  {b.name}
                </button>
              </React.Fragment>
            ))}
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-40 gap-10">
              <Loader2 className="w-12 h-12 animate-spin text-zinc-100 stroke-[1]" />
              <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-[0.5em]">Đang truy xuất mạng lưới tri thức</p>
          </div>
        ) : (
          <div className="space-y-24">
            {folders.length > 0 && (
              <div className="space-y-10">
                <div className="flex items-center gap-4 border-l-4 border-black pl-6">
                    <h3 className="text-sm font-bold text-black uppercase tracking-widest">Hệ thống thư mục</h3>
                    <div className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest">{folders.length} ĐƠN VỊ</div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                  {folders.map(f => (
                    <div 
                      key={f._id} 
                      onClick={() => { setBreadcrumbs([...breadcrumbs, f]); setCurrentFolder(f); }}
                      className="group bg-white p-10 border border-zinc-100 hover:border-black transition-all duration-500 cursor-pointer rounded-sm relative"
                    >
                      <div className="flex items-center gap-6">
                        <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-sm transition-all group-hover:bg-black group-hover:rotate-12">
                            <Folder className="w-6 h-6 text-zinc-200 group-hover:text-white" />
                        </div>
                        <span className="text-[13px] font-bold text-black uppercase tracking-tight truncate flex-1">{f.name}</span>
                      </div>
                      <button onClick={(e) => handleDeleteFolder(f._id, e)} className="absolute top-6 right-6 p-2 text-zinc-100 hover:text-black transition-all opacity-0 group-hover:opacity-100">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(documents.length > 0 || search) && (
              <div className="space-y-10">
                <div className="flex items-center gap-4 border-l-4 border-black pl-6">
                    <h3 className="text-sm font-bold text-black uppercase tracking-widest">Kho lưu trữ tri thức</h3>
                    <div className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest">{documents.length} THỰC THỂ</div>
                </div>
                {documents.length === 0 ? (
                  <div className="py-40 text-center border border-dashed border-zinc-100 rounded-sm">
                    <Search className="w-12 h-12 text-zinc-50 mx-auto mb-8 stroke-[1]" />
                    <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest px-10">Không tìm thấy thực thể tri thức tương ứng với truy vấn</p>
                  </div>
                ) : (
                  <div className={viewMode === 'grid' ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-8" : "space-y-4"}>
                    {documents.map(d => (
                      <Link href={`/documents/viewer/${d._id}`} key={d._id} className="block">
                        <div className={`group bg-white border border-zinc-100 hover:border-black transition-all duration-700 relative rounded-sm ${viewMode === 'grid' ? 'p-10 h-full flex flex-col' : 'p-6 flex items-center gap-10'}`}>
                          <div className={viewMode === 'grid' ? "flex justify-between items-start mb-8" : "shrink-0"}>
                            {getFileIcon(d.format)}
                            <div className={`flex gap-3 opacity-0 group-hover:opacity-100 transition-all duration-500 z-20 ${viewMode === 'grid' ? '' : 'absolute right-6 top-1/2 -translate-y-1/2'}`}>
                                <button onClick={(e) => handleToggleStar(d._id, e)} className={`p-2.5 rounded-sm border transition-all ${d.starred ? 'bg-black text-white border-black' : 'bg-white text-zinc-200 border-zinc-100 hover:border-black hover:text-black'}`}>
                                    <Star className={`w-3.5 h-3.5 ${d.starred ? 'fill-white' : ''}`} />
                                </button>
                                <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); setLockDocId(d._id); }} className="p-2.5 bg-white text-zinc-200 border border-zinc-100 hover:border-black hover:text-black rounded-sm transition-all">
                                    {d.password_hash ? <Lock className="w-3.5 h-3.5 text-black" /> : <Unlock className="w-3.5 h-3.5" />}
                                </button>
                                <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); setShareDocId(d._id); setIsPublic(d.is_public || false); }} className="p-2.5 bg-white text-zinc-200 border border-zinc-100 hover:border-black hover:text-black rounded-sm transition-all">
                                    <Share2 className="w-3.5 h-3.5" />
                                </button>
                                <button onClick={(e) => handleDeleteDoc(d._id, e)} className="p-2.5 bg-white text-zinc-200 border border-zinc-100 hover:text-black hover:border-black rounded-sm transition-all">
                                    <Trash2 className="w-3.5 h-3.5" />
                                </button>
                            </div>
                          </div>
                          
                          <div className={viewMode === 'grid' ? "flex-1 mb-8" : "flex-1 min-w-0"}>
                            <h4 className="text-[13px] font-bold text-black uppercase tracking-tight leading-relaxed line-clamp-2 mb-2" title={d.title}>{d.title}</h4>
                            {viewMode === 'list' && (
                                <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{formatBytes(d.size)} • {new Date(d.created_at || Date.now()).toLocaleDateString("vi-VN")}</p>
                            )}
                          </div>

                          <div className={viewMode === 'grid' ? "pt-6 border-t border-zinc-50 flex items-center justify-between" : "hidden md:flex items-center gap-6 pr-48"}>
                            <span className="text-[9px] font-bold uppercase tracking-widest bg-zinc-50 px-3 py-1.5 text-zinc-400 group-hover:bg-black group-hover:text-white transition-all rounded-sm">{d.format}</span>
                            <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-300">{formatBytes(d.size)}</span>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            )}

            {folders.length === 0 && documents.length === 0 && !search && (
              <div className="py-60 text-center border border-dashed border-zinc-100 bg-zinc-50/10 rounded-sm">
                <div className="w-24 h-24 bg-zinc-50 flex items-center justify-center mx-auto mb-10 rounded-sm">
                  <Upload className="w-10 h-10 text-zinc-200 stroke-[1.5]" />
                </div>
                <h2 className="text-xl font-bold text-black uppercase tracking-widest mb-4">Hệ thống tri thức rỗng</h2>
                <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest max-w-lg mx-auto leading-loose mb-12">Khởi tạo không gian lưu trữ bằng cách tải lên các thực thể tri thức đa định dạng hoặc tạo đơn vị thư mục mới</p>
                <div className="flex justify-center gap-6">
                  <button onClick={() => setIsUploadModalOpen(true)} className="h-16 px-12 bg-black text-white text-[11px] font-bold uppercase tracking-[0.3em] hover:bg-zinc-800 transition-all active:scale-95 rounded-sm">Tải lên ngay</button>
                  <button onClick={() => setIsFolderModalOpen(true)} className="h-16 px-12 border border-zinc-100 text-[11px] font-bold uppercase tracking-[0.3em] hover:border-black transition-all active:scale-95 rounded-sm">Tạo thư mục</button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modals are updated to match the premium rounded-sm / monochromatic style */}
      {isFolderModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[1200] flex items-center justify-center p-6 animate-in fade-in duration-300">
          <div className="bg-white p-12 w-full max-w-lg border border-zinc-100 rounded-sm animate-in zoom-in-95 duration-300">
            <h3 className="text-sm font-bold text-black uppercase tracking-widest mb-10">Kiến tạo thư mục tri thức</h3>
            <form onSubmit={handleCreateFolder}>
              <input 
                type="text" 
                autoFocus
                className="w-full h-16 px-6 bg-zinc-50 border border-zinc-100 text-sm font-bold focus:outline-none focus:border-black focus:bg-white transition-all rounded-sm mb-10"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                required
              />
              <div className="flex justify-end gap-6">
                <button type="button" onClick={() => setIsFolderModalOpen(false)} className="h-14 px-8 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black transition-all">Hủy bỏ</button>
                <button type="submit" className="h-14 px-10 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-95 rounded-sm">Xác nhận tạo</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isUploadModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[1200] flex items-center justify-center p-6 animate-in fade-in duration-300">
          <div className="bg-white w-full max-w-2xl border border-zinc-100 rounded-sm animate-in zoom-in-95 duration-300 overflow-hidden">
            <div className="p-10 border-b border-zinc-100 flex justify-between items-center bg-zinc-50/30">
              <h3 className="text-sm font-bold text-black uppercase tracking-widest">Tích hợp thực thể tri thức</h3>
              <button onClick={() => setIsUploadModalOpen(false)} className="p-2 text-zinc-300 hover:text-black transition-all">✕</button>
            </div>
            <div className="p-12">
              <form onSubmit={handleFileUpload} className="space-y-10">
                <div className="space-y-3">
                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1">Danh xưng thực thể</label>
                  <input 
                    type="text" 
                    className="w-full h-16 px-6 bg-zinc-50 border border-zinc-100 text-sm font-bold focus:outline-none focus:border-black focus:bg-white transition-all rounded-sm"
                    value={uploadTitle}
                    onChange={(e) => setUploadTitle(e.target.value)}
                    required
                  />
                </div>
                
                <div className="space-y-3">
                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1">Giao thức tải tệp</label>
                  <div 
                    className={`border-2 border-dashed h-60 flex flex-col items-center justify-center transition-all cursor-pointer rounded-sm
                      ${fileToUpload ? 'border-black bg-zinc-50' : 'border-zinc-100 hover:border-black bg-zinc-50/20'}`}
                    onClick={() => !fileToUpload && fileInputRef.current?.click()}
                  >
                    {fileToUpload ? (
                      <div className="flex flex-col items-center gap-6 p-10">
                        <CheckCircle className="w-10 h-10 text-black" />
                        <div className="text-center">
                            <span className="text-[12px] font-bold text-black uppercase tracking-tight block max-w-md truncate">{fileToUpload.name}</span>
                            <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest mt-2 block">{formatBytes(fileToUpload.size)}</span>
                        </div>
                        <button 
                          type="button" 
                          onClick={(e) => { e.stopPropagation(); setFileToUpload(null); setUploadTitle(""); }}
                          className="text-[10px] font-bold text-zinc-300 hover:text-black uppercase tracking-widest underline underline-offset-8"
                        >
                          Hủy bỏ tệp này
                        </button>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center gap-6">
                        <div className="w-16 h-16 bg-white border border-zinc-100 flex items-center justify-center rounded-sm">
                          <Upload className="w-6 h-6 text-zinc-200" />
                        </div>
                        <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Kéo thả hoặc nhấn để chọn thực thể tri thức</span>
                      </div>
                    )}
                    <input type="file" ref={fileInputRef} className="hidden" onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) { setFileToUpload(file); if (!uploadTitle) setUploadTitle(file.name.split('.')[0]); }
                    }} />
                  </div>
                </div>

                <div className="flex justify-end gap-6 pt-6 border-t border-zinc-50">
                  <button type="button" onClick={() => setIsUploadModalOpen(false)} className="h-14 px-8 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black transition-all" disabled={uploading}>Hủy bỏ</button>
                  <button type="submit" disabled={!fileToUpload || !uploadTitle || uploading} className="h-14 px-12 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 disabled:opacity-30 transition-all flex items-center gap-4 active:scale-95 rounded-sm">
                    {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ImageIcon className="w-4 h-4" />}
                    Kích hoạt tải lên
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {lockDocId && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[1200] flex items-center justify-center p-6 animate-in fade-in duration-300">
          <div className="bg-white p-12 w-full max-w-md border border-zinc-100 rounded-sm animate-in zoom-in-95 duration-300">
            <div className="flex items-center gap-6 mb-10">
              <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-sm"><Lock className="w-5 h-5 text-black" /></div>
              <h3 className="text-sm font-bold text-black uppercase tracking-widest">Thiết lập bảo mật</h3>
            </div>
            <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest leading-loose mb-10 px-1">Mật khẩu sẽ được mã hóa đa lớp. Nội dung sẽ không thể truy cập nếu đánh mất mật mã này.</p>
            <form onSubmit={handleLockDocument}>
              <input 
                type="password" 
                autoFocus
                className="w-full h-16 px-6 bg-zinc-50 border border-zinc-100 text-sm font-bold focus:outline-none focus:border-black focus:bg-white transition-all rounded-sm mb-10"
                value={lockPassword}
                onChange={(e) => setLockPassword(e.target.value)}
                required
              />
              <div className="flex justify-end gap-6">
                <button type="button" onClick={() => { setLockDocId(null); setLockPassword(""); }} className="h-14 px-8 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black transition-all">Hủy bỏ</button>
                <button type="submit" className="h-14 px-12 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-95 rounded-sm">Kích hoạt khóa</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {shareDocId && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[1200] flex items-center justify-center p-6 animate-in fade-in duration-300">
          <div className="bg-white p-12 w-full max-w-lg border border-zinc-100 rounded-sm animate-in zoom-in-95 duration-300">
            <div className="flex items-center gap-6 mb-12">
              <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-sm"><Globe className="w-5 h-5 text-black" /></div>
              <h3 className="text-sm font-bold text-black uppercase tracking-widest">Giao thức chia sẻ</h3>
            </div>
            <form onSubmit={handleShareSubmit} className="space-y-10">
              <div className="flex items-center gap-4 bg-zinc-50/50 p-6 rounded-sm border border-zinc-50">
                <input type="checkbox" checked={isPublic} onChange={e => setIsPublic(e.target.checked)} className="w-5 h-5 accent-black cursor-pointer" />
                <label className="text-[11px] font-bold text-black uppercase tracking-widest cursor-pointer">Công khai thực thể tri thức</label>
              </div>
              <div className="space-y-6">
                 <div className="space-y-3">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1">Mật mã truy cập (Nếu cần)</label>
                    <input type="password" value={sharePassword} onChange={e=>setSharePassword(e.target.value)} className="w-full h-16 px-6 bg-zinc-50 border border-zinc-100 text-sm font-bold focus:outline-none focus:border-black rounded-sm" />
                 </div>
                 <div className="space-y-3">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1">Thời hạn hiệu lực</label>
                    <select value={shareExpires} onChange={e=>setShareExpires(e.target.value)} className="w-full h-16 px-6 bg-zinc-50 border border-zinc-100 text-[11px] font-bold uppercase tracking-widest focus:outline-none focus:border-black rounded-sm">
                        <option value="1">Hết hạn sau 24 giờ</option>
                        <option value="7">Hết hạn sau 07 ngày</option>
                        <option value="30">Hết hạn sau 30 ngày</option>
                    </select>
                 </div>
              </div>
              {publicUrl && (
                 <div className="p-10 bg-zinc-50/50 border border-zinc-100 flex flex-col items-center rounded-sm space-y-8 animate-in fade-in duration-500">
                    <div className="text-[10px] font-bold text-black break-all select-all text-center tracking-widest uppercase bg-white p-4 border border-zinc-100 w-full rounded-sm">{publicUrl}</div>
                    <div className="p-6 bg-white border border-zinc-100 rounded-sm">
                        <img src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(publicUrl)}`} className="grayscale" alt="QR Code" />
                    </div>
                    <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2"><QrCode className="w-3 h-3"/> Quét mã để tiếp cận thực thể</p>
                 </div>
              )}
              <div className="flex justify-end gap-6 pt-6 border-t border-zinc-50">
                <button type="button" onClick={() => { setShareDocId(null); setPublicUrl(""); }} className="h-14 px-8 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black transition-all">Đóng</button>
                <button type="submit" className="h-14 px-12 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-95 rounded-sm">Cập nhật giao thức</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </Workspace>
  );
}
