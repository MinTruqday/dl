"use client";
import React, { useState, useEffect, useRef } from "react";
import AppShell from "@/app/components/AppShell";
import { Folder, FileText, Search, Plus, Upload, Trash2, Home, File, Image as ImageIcon, CheckCircle, ChevronRight, Download, Star, Lock, Unlock, Database, Filter, LayoutGrid, List, Tag, Globe, Share2, Archive, DollarSign, Send, History, QrCode } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { formatBytes } from "@/app/lib/utils";
import { 
  getFoldersAPI, getDocumentsAPI, getStorageQuotaAPI, 
  createFolderAPI, uploadDocumentAPI, deleteFolderAPI, 
  deleteDocumentAPI, toggleStarDocumentAPI, lockDocumentAPI,
  monetizeDocumentAPI, transferDocumentAPI, getAuditLogsAPI 
} from "@/app/lib/api";

export default function DocumentsPage() {
  const [currentFolder, setCurrentFolder] = useState<any>(null);
  const [folders, setFolders] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [monetizeDocId, setMonetizeDocId] = useState<string|null>(null);
  const [monetizePrice, setMonetizePrice] = useState<number>(0);
  
  const [transferDocId, setTransferDocId] = useState<string|null>(null);
  const [transferTargetId, setTransferTargetId] = useState<string>("");

  const [auditDocId, setAuditDocId] = useState<string|null>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (document.activeElement?.tagName === "INPUT" || document.activeElement?.tagName === "TEXTAREA") return;
      
      const container = window;
      const step = 200;
      if (e.key === "j") container.scrollBy(0, step);
      if (e.key === "k") container.scrollBy(0, -step);
      if (e.key === "h") container.scrollBy(-step, 0);
      if (e.key === "l") container.scrollBy(step, 0);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const [loading, setLoading] = useState(false);

  const [quota, setQuota] = useState<{used: number, limit: number, percent: number}>({used: 0, limit: 100, percent: 0});
  const [filterStar, setFilterStar] = useState(false);
  const [filterFormat, setFilterFormat] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"grid"|"list">("grid");
  
  const [lockDocId, setLockDocId] = useState<string | null>(null);
  const [lockPassword, setLockPassword] = useState("");

  const [shareDocId, setShareDocId] = useState<string | null>(null);
  const [isPublic, setIsPublic] = useState(false);
  const [sharePassword, setSharePassword] = useState("");
  const [shareExpires, setShareExpires] = useState("7");
  const [publicUrl, setPublicUrl] = useState("");


  const [breadcrumbs, setBreadcrumbs] = useState<any[]>([]);

  const [isFolderModalOpen, setIsFolderModalOpen] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploading, setUploading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

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
        getStorageQuotaAPI().catch(() => ({used:0, limit:100, percent:0}))
      ]);
      setFolders((search || filterStar || filterFormat !== "all") ? [] : fData); 
      setDocuments(dData);
      setQuota(qData);
    } catch (e) {
      console.error(e);
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
      loadData();
    } catch (e) {
      console.error("Failed to create folder");
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
      loadData();
    } catch (e) {
      console.error("Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  
  const handleToggleStar = async (id: string, e: React.MouseEvent) => {
    e.preventDefault(); e.stopPropagation();
    await toggleStarDocumentAPI(id);
    loadData();
  };

  
  const handleBackupZIP = () => {
    window.open(`${process.env.NEXT_PUBLIC_API_URL}/documents/export/backup?user=` + localStorage.getItem("doclib_token"), "_blank");
  };

    const handleMonetize = async (e: React.FormEvent) => {
    e.preventDefault();
    if(monetizeDocId) {
      await monetizeDocumentAPI(monetizeDocId, monetizePrice);
      setMonetizeDocId(null);
      loadData();
    }
  };

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if(transferDocId && transferTargetId) {
      await transferDocumentAPI(transferDocId, transferTargetId);
      setTransferDocId(null);
      loadData();
    }
  };

  const loadAuditLogs = async (id: string) => {
    const logs = await getAuditLogsAPI(id);
    setAuditLogs(logs);
    setAuditDocId(id);
  };

  const handleShareSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if(!shareDocId) return;
    try {
       const API_URL = process.env.NEXT_PUBLIC_API_URL;
       const res = await fetch(API_URL + "/documents/" + shareDocId + "/share?is_public=" + isPublic + "&password=" + sharePassword + "&expires_in_days=" + shareExpires, {
         method: "POST",
         headers: { "Authorization": "Bearer " + localStorage.getItem("token") }
       });
       const data = await res.json();
       setPublicUrl(window.location.origin + "/documents/viewer/" + shareDocId + "?pwd=" + sharePassword);
       
    } catch(e) { console.error(e); }
  }

  const handleLockDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lockDocId || !lockPassword) return;
    try {
      await lockDocumentAPI(lockDocId, lockPassword);
      setLockDocId(null);
      setLockPassword("");
      loadData();
    } catch(err) {
      console.error("Failed to lock document");
    }
  };

  const handleNavigateFolder = (folder: any) => {
    setBreadcrumbs([...breadcrumbs, folder]);
    setCurrentFolder(folder);
    setSearch("");
  };

  const handleBreadcrumbClick = (index: number) => {
    if (index === -1) {
      setBreadcrumbs([]);
      setCurrentFolder(null);
    } else {
      const newBread = breadcrumbs.slice(0, index + 1);
      setBreadcrumbs(newBread);
      setCurrentFolder(newBread[newBread.length - 1]);
    }
    setSearch("");
  };

  const handleDeleteFolder = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if(confirm("Bạn có chắc muốn xóa thư mục này?")) {
      await deleteFolderAPI(id);
      loadData();
    }
  };

  const handleDeleteDoc = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if(confirm("Bạn có chắc muốn xóa tài liệu này?")) {
      await deleteDocumentAPI(id, true);
      loadData();
    }
  };

  const getFileIcon = (fmt: string) => {
    if(['pdf'].includes(fmt)) return <FileText className="text-black font-bold outline-black w-8 h-8" />;
    if(['doc', 'docx'].includes(fmt)) return <FileText className="text-black w-8 h-8" />;
    if(['jpg', 'png', 'jpeg'].includes(fmt)) return <ImageIcon className="text-black w-8 h-8" />;
    return <File className="text-muted-foreground w-8 h-8" />;
  };

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto px-4 py-6 pb-12 w-full">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-sans font-bold text-foreground">Tài liệu & Học liệu</h1>
            <p className="text-muted-foreground mt-1">Quản lý, phân loại và đọc tài liệu cá nhân</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-5 h-5 absolute left-3 top-2.5 text-muted-foreground" />
              <input 
                type="text" 
                placeholder="" 
                className="pl-10 pr-4 py-2 border border-border  text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Button variant="outline"
              onClick={() => setIsFolderModalOpen(true)}
              className="flex items-center gap-2"
            >
              <Plus className="w-5 h-5" /> Thư mục
            </Button>
            
            <Button variant="secondary" onClick={handleBackupZIP}
              className="flex items-center gap-2 px-4 py-2  hover:bg-black  font-medium transition"
            >
              <Archive className="w-5 h-5" /> Sao lưu ZIP
            </Button>
            <Button 
              onClick={() => setIsUploadModalOpen(true)}

              className="flex items-center gap-2 "
            >
              <Upload className="w-5 h-5" /> Tải lên
            </Button>
          </div>
        </div>

        
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6 bg-card p-4  border border-border ">
          <div className="flex items-center gap-4 flex-1">
            <Button variant={!filterStar && filterFormat==="all" ? "default" : "outline"} onClick={() => { setFilterStar(false); setFilterFormat("all"); }} className="px-3 py-1.5 h-auto text-sm font-medium">Tất cả</Button>
            <Button variant={filterStar ? "default" : "outline"} onClick={() => setFilterStar(!filterStar)} className={`px-3 py-1.5 h-auto text-sm font-medium flex items-center gap-1 ${filterStar ? "!bg-black !text-white" : ""}`}><Star className="w-4 h-4"/> Yêu thích</Button>
            
            <div className="h-6 w-px bg-gray-300"></div>
            
            <select value={filterFormat} onChange={(e) => setFilterFormat(e.target.value)} className="text-sm border-border  py-1.5 pl-3 pr-8 focus-visible:ring-ring bg-background text-foreground text-foreground font-medium">
              <option value="all">Mọi định dạng</option>
              <option value="pdf">Định dạng PDF</option>
              <option value="docx">Văn bản Word</option>
              <option value="latex">Mã nguồn LaTeX</option>
              <option value="zip">Tệp nén lưu trữ</option>
            </select>

            <div className="h-6 w-px bg-gray-300 mx-2"></div>
            <Button variant={viewMode === "grid" ? "secondary" : "ghost"} size="icon" onClick={() => setViewMode("grid")} className="h-8 w-8"><LayoutGrid className="w-4 h-4 text-foreground"/></Button>
            <Button variant={viewMode === "list" ? "secondary" : "ghost"} size="icon" onClick={() => setViewMode("list")} className="h-8 w-8"><List className="w-4 h-4 text-foreground"/></Button>
          </div>
          
          <div className="flex items-center gap-3 min-w-[200px]">
            <Database className="w-5 h-5 text-muted-foreground"/>
            <div className="flex-1">
              <div className="flex justify-between text-xs mb-1 font-medium text-gray-600">
                <span>Lưu trữ</span>
                <span>{formatBytes(quota.used)} / 5GB</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-none overflow-hidden">
                <div className={`h-full rounded-none ${quota.percent > 80 ? 'bg-black' : 'bg-black'}`} style={{width: `${Math.max(quota.percent, 1)}%`}}></div>
              </div>
            </div>
          </div>
        </div>

        {!search && (
          <div className="flex items-center gap-2 mb-6 text-sm font-medium text-gray-600 bg-card p-3  border border-border ">
            <Button variant="ghost" size="sm" onClick={() => handleBreadcrumbClick(-1)} className="flex items-center gap-1">
              <Home className="w-4 h-4" /> Gốc
            </Button>
            {breadcrumbs.map((b, idx) => (
              <React.Fragment key={b._id}>
                <ChevronRight className="w-4 h-4 text-muted-foreground" />
                <Button 
                  onClick={() => handleBreadcrumbClick(idx)}
                  className={`hover:text-black ${idx === breadcrumbs.length - 1 ? 'text-black' : ''}`}
                >
                  {b.name}
                </Button>
              </React.Fragment>
            ))}
          </div>
        )}

        {loading ? (
          <div className="text-center py-20 text-muted-foreground">Đang tải dữ liệu</div>
        ) : (
          <div className="space-y-8">
            {folders.length > 0 && (
              <div>
                <h3 className="text-lg font-bold text-foreground mb-4 font-sans">Thư mục</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {folders.map(f => (
                    <div 
                      key={f._id} 
                      onClick={() => handleNavigateFolder(f)}
                      className="bg-card p-4  border border-border  hover: cursor-pointer transition group flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <Folder className="w-8 h-8 text-black fill-zinc-100" />
                        <span className="font-semibold text-foreground group-hover:text-black truncate max-w-[150px]">{f.name}</span>
                      </div>
                      <Button onClick={(e) => handleDeleteFolder(f._id, e)} className="text-muted-foreground hover:text-black font-bold outline-black p-1 opacity-0 group-hover:opacity-100 transition">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(documents.length > 0 || search) && (
              <div>
                <h3 className="text-lg font-bold text-foreground mb-4 font-sans">Tài liệu</h3>
                {documents.length === 0 ? (
                  <div className="bg-card p-10 text-center  border border-border text-muted-foreground ">
                    Không tìm thấy tài liệu nào khớp với "{search}"
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                    {documents.map(d => (
                      <Link href={`/documents/viewer/${d._id}`} key={d._id}>
                        <div className="bg-card p-4  border border-border  hover: hover:-translate-y-1 transition group flex flex-col h-full cursor-pointer relative">
                          <div className="flex justify-between items-start mb-4">
                            {getFileIcon(d.format)}
                            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition z-10">
                              <Button onClick={(e) => handleToggleStar(d._id, e)} className={`p-1.5 rounded-none transition ${d.starred ? 'text-black bg-gray-100 opacity-100' : 'text-muted-foreground hover:text-black bg-background text-foreground hover:bg-gray-100'}`}>
                                <Star className={`w-4 h-4 ${d.starred ? 'fill-black' : ''}`} />
                              </Button>
                              <Button variant="ghost" size="icon" onClick={(e) => { e.preventDefault(); e.stopPropagation(); setLockDocId(d._id); }} className=" hover:text-black hover:bg-gray-100 rounded-none h-8 w-8 transition">
                                {d.password_hash || d.file_url === '/locked' ? <Lock className="w-4 h-4 text-black" /> : <Unlock className="w-4 h-4" />}
                              </Button>
                              
                              <Button variant="ghost" size="icon" onClick={(e) => { e.preventDefault(); e.stopPropagation(); setShareDocId(d._id); setIsPublic(d.is_public || false); }} className=" hover:text-black hover:bg-gray-100 rounded-none h-8 w-8 transition">
                                <Share2 className="w-4 h-4" />
                              </Button>
                                                            <Button variant="ghost" size="icon" onClick={(e) => { e.preventDefault(); e.stopPropagation(); setMonetizeDocId(d._id); setMonetizePrice(d.price || 0); }} className=" hover:text-black hover:bg-zinc-50 rounded-none h-8 w-8 transition">
                                <DollarSign className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="icon" onClick={(e) => { e.preventDefault(); e.stopPropagation(); setTransferDocId(d._id); setTransferTargetId(""); }} className=" hover:text-black hover:bg-zinc-50 rounded-none h-8 w-8 transition">
                                <Send className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="icon" onClick={(e) => { e.preventDefault(); e.stopPropagation(); loadAuditLogs(d._id); }} className=" hover:text-black hover:bg-zinc-50 rounded-none h-8 w-8 transition">
                                <History className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="icon" onClick={(e) => handleDeleteDoc(d._id, e)} className=" hover:text-black font-bold outline-black hover:bg-gray-100 rounded-none h-8 w-8 transition">
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                          <h4 className="font-bold text-foreground leading-tight mb-2 line-clamp-2" title={d.title}>{d.title}</h4>
                          <div className="mt-auto pt-3 border-t border-border flex items-center justify-between text-xs text-muted-foreground font-medium">
                            <span className="bg-gray-100 px-2 py-0.5 rounded text-foreground">{d.format}</span>
                            <span>{formatBytes(d.size)}</span>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            )}

            {folders.length === 0 && documents.length === 0 && !search && (
              <div className="bg-card py-24 px-6 text-center  border border-dashed border-border ">
                <div className="bg-gray-100 w-20 h-20 rounded-none flex items-center justify-center mx-auto mb-6">
                  <Upload className="w-10 h-10 text-black" />
                </div>
                <h2 className="text-xl font-bold font-sans text-foreground mb-2">Chưa có tài liệu nào</h2>
                <p className="text-muted-foreground mb-6 max-w-sm mx-auto">Upload tài liệu PDF, DOCX, EPUB hoặc tạo thư mục mới để bắt đầu tổ chức không gian học tập của bạn.</p>
                <div className="flex justify-center gap-3">
                  <Button onClick={() => setIsUploadModalOpen(true)}>
                    Tải tài liệu lên
                  </Button>
                  <Button variant="outline" onClick={() => setIsFolderModalOpen(true)} className="flex items-center gap-2">
                    <Plus className="w-4 h-4" /> Thư mục trống
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {isFolderModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-card p-6  w-full max-w-md  border border-border">
            <h3 className="text-xl font-bold font-sans text-foreground mb-4">Tạo Thư Mục Mới</h3>
            <form onSubmit={handleCreateFolder}>
              <input 
                type="text" 
                autoFocus
                placeholder="" 
                className="w-full border-border  p-3 text-black mb-6 bg-background text-foreground focus-visible:ring-ring"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                required
              />
              <div className="flex justify-end gap-3 text-sm font-medium">
                <Button variant="secondary" type="button" onClick={() => setIsFolderModalOpen(false)} className="px-4 py-2  transition">Hủy</Button>
                <Button type="submit" className="px-4 py-2  hover:bg-gray-800 transition ">Tạo mới</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isUploadModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card   w-full max-w-lg border border-border overflow-hidden">
            <div className="p-6 border-b border-border bg-background text-foreground/50 flex justify-between items-center">
              <h3 className="text-xl font-bold font-sans text-foreground">Tải Tài Liệu Lên</h3>
              <Button variant="ghost" size="icon" type="button" onClick={() => setIsUploadModalOpen(false)} className="h-8 w-8 text-muted-foreground hover:text-foreground">✕</Button>
            </div>
            <div className="p-6 text-black">
              <form onSubmit={handleFileUpload}>
                <div className="mb-5">
                  <label className="block text-sm font-medium text-foreground mb-2">Tên tài liệu</label>
                  <input 
                    type="text" 
                    placeholder="" 
                    className="w-full border border-border  p-3 bg-background text-foreground focus-visible:ring-ring text-black"
                    value={uploadTitle}
                    onChange={(e) => setUploadTitle(e.target.value)}
                    required
                  />
                </div>
                
                <div className="mb-6">
                  <label className="block text-sm font-medium text-foreground mb-2">Chọn file dữ liệu</label>
                  <div 
                    className={`border-2 border-dashed  p-8 text-center transition-colors cursor-pointer 
                      ${fileToUpload ? 'border-black bg-zinc-50' : 'border-border hover:border-gray-300 bg-background text-foreground'}`}
                    onClick={() => !fileToUpload && fileInputRef.current?.click()}
                  >
                    {fileToUpload ? (
                      <div className="flex flex-col items-center text-center">
                        <CheckCircle className="w-10 h-10 text-black mb-3" />
                        <span className="font-bold text-foreground line-clamp-1">{fileToUpload.name}</span>
                        <span className="text-sm text-muted-foreground mt-1">{formatBytes(fileToUpload.size)}</span>
                        <Button 
                          type="button" 
                          onClick={(e) => { e.stopPropagation(); setFileToUpload(null); setUploadTitle(""); }}
                          className="mt-4 text-black font-bold outline-black text-sm hover:underline font-medium relative z-20 cursor-pointer"
                        >
                          Xóa file
                        </Button>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center">
                        <div className="bg-card p-3 rounded-none  mb-4">
                          <Upload className="w-6 h-6 text-black" />
                        </div>
                        <span className="font-semibold text-foreground">Nhấn để chọn file</span>
                        <span className="text-xs text-muted-foreground mt-2">Đa định dạng (Tối đa 50MB)</span>
                      </div>
                    )}
                    <input 
                      type="file" 
                      ref={fileInputRef} 
                      className="hidden" 
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          setFileToUpload(file);
                          if (!uploadTitle) setUploadTitle(file.name.split('.')[0]);
                        }
                      }}
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 text-sm font-medium pt-4 border-t border-border">
                  <Button variant="secondary" type="button" onClick={() => setIsUploadModalOpen(false)} className="px-5 py-2.5  transition" disabled={uploading}>Hủy</Button>
                  <Button type="submit" 
                    disabled={!fileToUpload || !uploadTitle || uploading} 
                    className="px-6 py-2.5  hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition  flex items-center gap-2 cursor-pointer"
                  >
                    {uploading ? (
                      <>Đang xử lý</>
                    ) : 'Tải lên hoàn tất'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {lockDocId && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card p-6  w-full max-w-sm  border border-border">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-gray-100 p-3 rounded-none"><Lock className="w-6 h-6 text-black" /></div>
              <h3 className="text-xl font-bold font-sans text-foreground">Khóa Tài Liệu</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-6">Mật khẩu được mã hóa một chiều. Bạn không thể lấy lại file nếu quên mật khẩu này.</p>
            <form onSubmit={handleLockDocument}>
              <input 
                type="password" 
                autoFocus
                placeholder="" 
                className="w-full border border-border  p-3 text-black mb-6 bg-background text-foreground focus-visible:ring-ring"
                value={lockPassword}
                onChange={(e) => setLockPassword(e.target.value)}
                required
              />
              <div className="flex justify-end gap-3 text-sm font-medium">
                <Button type="button" onClick={() => { setLockDocId(null); setLockPassword(""); }} className="px-4 py-2.5 text-gray-600 hover:bg-gray-100  transition">Hủy bỏ</Button>
                <Button type="submit" className="px-6 py-2.5  hover:bg-gray-800 transition ">Thiết lập Khóa</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {shareDocId && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card p-6  w-full max-w-sm  border border-border">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-gray-100 p-3 rounded-none"><Globe className="w-6 h-6 text-black" /></div>
              <h3 className="text-xl font-bold font-sans text-foreground">Chia sẻ & Public</h3>
            </div>
            <form onSubmit={handleShareSubmit}>
              <div className="flex items-center gap-2 mb-4">
                <input type="checkbox" checked={isPublic} onChange={e => setIsPublic(e.target.checked)} className="w-4 h-4 text-black focus:ring-black" />
                <label className="text-sm font-medium text-foreground">Công khai tài liệu này</label>
              </div>
              <div className="space-y-3 mb-6">
                 <input type="password" value={sharePassword} onChange={e=>setSharePassword(e.target.value)} placeholder="" className="w-full border border-border  p-2.5 text-sm bg-background text-foreground focus-visible:ring-ring" />
                 <select value={shareExpires} onChange={e=>setShareExpires(e.target.value)} className="w-full border border-border  p-2.5 text-sm bg-background text-foreground focus-visible:ring-ring">
                    <option value="1">Hủy link sau 1 ngày</option>
                    <option value="7">Hủy link sau 7 ngày</option>
                    <option value="30">Hủy link sau 30 ngày</option>
                 </select>
              </div>
                            {publicUrl && (
                 <div className="mb-4 p-4 bg-background text-foreground flex flex-col items-center rounded border border-border">
                   <div className="text-xs text-black break-all select-all mb-3 text-center">{publicUrl}</div>
                    <img src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(publicUrl)}`} alt="QR Code" />
                   <p className="text-xs text-muted-foreground mt-2"><QrCode className="inline w-3 h-3"/> Quét để tải tài liệu</p>
                 </div>
              )}
              <div className="flex justify-end gap-3 text-sm font-medium">
                <Button type="button" onClick={() => { setShareDocId(null); setPublicUrl(""); }} className="px-4 py-2.5 text-gray-600 hover:bg-gray-100  transition">Đóng</Button>
                <Button type="submit" className="px-6 py-2.5  hover:bg-gray-800 transition ">Cập nhật Link</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {monetizeDocId && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card p-6  w-full max-w-sm border border-black">
            <h3 className="text-xl font-bold font-sans mb-4 flex items-center text-black"><DollarSign className="mr-2"/> Thương mại hóa tài liệu</h3>
            <form onSubmit={handleMonetize}>
              <input type="number" min="0" step="1000" value={monetizePrice} onChange={e=>setMonetizePrice(Number(e.target.value))} className="w-full border  p-3 mb-6 bg-background text-foreground border-border" placeholder="" required />
              <div className="flex justify-end gap-3"><Button variant="secondary" type="button" onClick={()=>setMonetizeDocId(null)} >Hủy</Button><Button type="submit" className="px-4 py-2 bg-black text-white rounded-none hover:bg-zinc-800">Lưu thiết lập</Button></div>
            </form>
          </div>
        </div>
      )}

      {transferDocId && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card p-6  w-full max-w-sm border border-black">
            <h3 className="text-xl font-bold font-sans mb-4 flex items-center text-black"><Send className="mr-2"/> Chuyển nhượng quyền sở hữu</h3>
            <form onSubmit={handleTransfer}>
              <input type="text" value={transferTargetId} onChange={e=>setTransferTargetId(e.target.value)} className="w-full border  p-3 mb-6 bg-background text-foreground border-border" placeholder="" required />
              <div className="flex justify-end gap-3"><Button variant="secondary" type="button" onClick={()=>setTransferDocId(null)} >Hủy</Button><Button type="submit" className="px-4 py-2 bg-black text-white rounded-none hover:bg-zinc-800">Xác nhận chuyển</Button></div>
            </form>
          </div>
        </div>
      )}

      {auditDocId && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card p-6  w-full max-w-lg  max-h-[80vh] flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold font-sans flex items-center text-black"><History className="mr-2 w-5 h-5"/> Nhật ký hoạt động</h3>
              <Button variant="ghost" size="icon" onClick={()=>setAuditDocId(null)} className="h-8 w-8 text-muted-foreground hover:text-foreground text-sm">✕</Button>
            </div>
            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
              {auditLogs.length === 0 ? <p className="text-center text-muted-foreground py-10">Chưa có hoạt động nào được ghi nhận.</p> : auditLogs.map(log => (
                 <div key={log.id} className="text-sm p-3 bg-background text-foreground  border border-border">
                    <span className="font-sans text-xs text-muted-foreground block mb-1">{new Date(log.timestamp).toLocaleString("vi-VN")}</span>
                    <strong className="text-foreground">{log.action === 'VIEW' ? 'XEM' : log.action === 'DOWNLOAD' ? 'TẢI VỀ' : log.action}</strong> bởi <span className="text-black font-sans">{log.user_id}</span>
                 </div>
              ))}
            </div>
          </div>
        </div>
      )}

    </AppShell>
  );
}


