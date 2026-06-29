"use client";

import { useEffect, useState, useRef } from "react";
import { getToken as getAuthToken } from "@/features/auth/services/user_authentication.service";
import { StorageItem, listStorageItemsAPI, createFolderAPI, uploadStorageFileAPI, deleteStorageItemAPI, updateStorageItemAPI, searchStorageItemsAPI, copyStorageItemAPI, uploadFileVersionAPI, getRecentStorageItemsAPI, shareStorageItemAPI, getStorageQuotaAPI, createShortcutAPI, downloadZipAPI } from "@/features/content/services/file_storage.service";
import { useToast } from "@/shared/contexts/ToastContext";
import { Folder, File, Upload, Plus, ChevronRight, MoreVertical, Trash2, Edit2, Download, Loader2, Search, Copy, Star, Share2, History, Tag, MessageSquare, Grid, List as ListIcon, Clock, Info, Link as LinkIcon, Palette, Archive, Home, X } from "lucide-react";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from "@/shared/components/ui/Modal";

export default function StoragePage() {
  const { showToast } = useToast();
  const [items, setItems] = useState<StorageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [currentFolderId, setCurrentFolderId] = useState<string | undefined>(undefined);
  const [breadcrumbs, setBreadcrumbs] = useState<{ id?: string; name: string }[]>([{ name: "Lưu trữ gốc" }]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [createFolderOpen, setCreateFolderOpen] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [renameItem, setRenameItem] = useState<StorageItem | null>(null);
  const [newName, setNewName] = useState("");
  const [descItem, setDescItem] = useState<StorageItem | null>(null);
  const [descValue, setDescValue] = useState("");
  const [tagsItem, setTagsItem] = useState<StorageItem | null>(null);
  const [tagsValue, setTagsValue] = useState("");
  const [viewMode, setViewMode] = useState<"files" | "trash" | "recent">("files");
  const [moveItem, setMoveItem] = useState<StorageItem | null>(null);
  const [moveTargetId, setMoveTargetId] = useState<string | undefined>(undefined);
  const [moveBreadcrumbs, setMoveBreadcrumbs] = useState<{ id?: string; name: string }[]>([{ name: "Lưu trữ gốc" }]);
  const [moveFolders, setMoveFolders] = useState<StorageItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchType, setSearchType] = useState<"" | "folder" | "file">("");
  const versionInputRef = useRef<HTMLInputElement>(null);
  const [versionItem, setVersionItem] = useState<StorageItem | null>(null);
  const [layoutMode, setLayoutMode] = useState<"list" | "grid">("list");
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [shareItem, setShareItem] = useState<StorageItem | null>(null);
  const [shareEmail, setShareEmail] = useState("");
  const [shareRole, setShareRole] = useState("viewer");
  const [useAISearch, setUseAISearch] = useState(false);
  const [activeSidebarTab, setActiveSidebarTab] = useState<"info" | "ai">("info");
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [quota, setQuota] = useState<{ used: number; limit: number } | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [detailsItem, setDetailsItem] = useState<StorageItem | null>(null);
  const [relatedItems, setRelatedItems] = useState<StorageItem[]>([]);
  const [colorItem, setColorItem] = useState<StorageItem | null>(null);
  const [colorValue, setColorValue] = useState("");

  const fetchQuota = async () => { try { setQuota(await getStorageQuotaAPI()); } catch (e) {} };
  useEffect(() => { fetchQuota(); }, []);

  const fetchItems = async (folderId?: string, mode: typeof viewMode = viewMode) => {
    setLoading(true);
    try {
      if (mode === "recent") { setItems(await getRecentStorageItemsAPI(20)); }
      else { setItems(await listStorageItemsAPI(folderId, mode === "trash")); }
    } catch (e: any) { showToast(e.message, "error"); } finally { setLoading(false); }
  };

  const fetchMoveFolders = async (folderId?: string) => {
    try { const data = await listStorageItemsAPI(folderId); setMoveFolders(data.filter((i) => i.is_folder && i._id !== moveItem?._id)); }
    catch (e) {}
  };

  useEffect(() => { fetchItems(viewMode === "trash" || viewMode === "recent" ? undefined : currentFolderId, viewMode); }, [currentFolderId, viewMode]);

  useEffect(() => {
    if (detailsItem && activeSidebarTab === "info") {
      import("@/features/content/services/file_storage.service").then((m) => {
        m.getRelatedStorageItemsAPI(detailsItem._id).then((data) => setRelatedItems(data)).catch(() => {});
      });
    }
  }, [detailsItem, activeSidebarTab]);

  useEffect(() => { if (moveItem) fetchMoveFolders(moveTargetId); }, [moveTargetId, moveItem]);

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;
    try { await createFolderAPI(newFolderName.trim(), currentFolderId); showToast("Tạo thành công", "success"); setCreateFolderOpen(false); setNewFolderName(""); fetchItems(currentFolderId); }
    catch (e: any) { showToast(e.message, "error"); }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files; if (!files?.length) return;
    setUploading(true);
    try { for (let i = 0; i < files.length; i++) await uploadStorageFileAPI(files[i], currentFolderId); showToast("Tải lên thành công", "success"); fetchItems(currentFolderId); fetchQuota(); }
    catch (e: any) { showToast(e.message, "error"); } finally { setUploading(false); if (fileInputRef.current) fileInputRef.current.value = ""; }
  };

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); if (viewMode !== "trash" && viewMode !== "recent") setIsDraggingOver(true); };
  const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); setIsDraggingOver(false); };
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault(); setIsDraggingOver(false); if (viewMode === "trash" || viewMode === "recent") return;
    const files = e.dataTransfer.files; if (!files?.length) return;
    setUploading(true);
    try { for (let i = 0; i < files.length; i++) await uploadStorageFileAPI(files[i], currentFolderId); showToast("Tải lên thành công", "success"); fetchItems(currentFolderId); fetchQuota(); }
    catch (e: any) { showToast(e.message, "error"); } finally { setUploading(false); }
  };

  const handleNavigate = (folder: StorageItem) => {
    if (folder.is_shortcut && folder.target_id) return;
    setCurrentFolderId(folder._id); setBreadcrumbs([...breadcrumbs, { id: folder._id, name: folder.name }]);
  };
  const handleNavigateBreadcrumb = (index: number) => { setCurrentFolderId(breadcrumbs[index].id); setBreadcrumbs(breadcrumbs.slice(0, index + 1)); };

  const handleDelete = async (item: StorageItem) => {
    try {
      await deleteStorageItemAPI(item._id, viewMode === "trash");
      showToast(viewMode === "trash" ? "Đã xóa vĩnh viễn" : "Đã chuyển vào thùng rác", "success");
      fetchItems(viewMode === "trash" ? undefined : currentFolderId, viewMode); if (viewMode === "trash") fetchQuota();
    } catch (e: any) { showToast(e.message, "error"); }
  };

  const handleRestore = async (item: StorageItem) => { try { await updateStorageItemAPI(item._id, { is_trashed: false }); showToast("Khôi phục thành công", "success"); fetchItems(undefined, true); } catch (e: any) { showToast(e.message, "error"); } };
  const handleMove = async () => { if (!moveItem) return; try { await updateStorageItemAPI(moveItem._id, { parent_id: (moveTargetId === undefined ? null : moveTargetId) as any }); showToast("Đã chuyển", "success"); setMoveItem(null); setMoveTargetId(undefined); setMoveBreadcrumbs([{ name: "Lưu trữ gốc" }]); fetchItems(currentFolderId); } catch (e: any) { showToast(e.message, "error"); } };
  const handleRename = async () => { if (!renameItem || !newName.trim()) return; try { await updateStorageItemAPI(renameItem._id, { name: newName.trim() }); showToast("Đã đổi tên", "success"); setRenameItem(null); setNewName(""); fetchItems(currentFolderId); } catch (e: any) { showToast(e.message, "error"); } };
  const handleUpdateDesc = async () => { if (!descItem) return; try { await updateStorageItemAPI(descItem._id, { description: descValue.trim() }); showToast("Đã lưu ghi chú", "success"); setDescItem(null); setDescValue(""); fetchItems(currentFolderId); } catch (e: any) { showToast(e.message, "error"); } };
  const handleUpdateTags = async () => { if (!tagsItem) return; try { await updateStorageItemAPI(tagsItem._id, { tags: tagsValue.split(",").map(t => t.trim()).filter(Boolean) }); showToast("Đã lưu nhãn", "success"); setTagsItem(null); setTagsValue(""); fetchItems(currentFolderId); } catch (e: any) { showToast(e.message, "error"); } };
  const handleUpdateColor = async () => { if (!colorItem) return; try { await updateStorageItemAPI(colorItem._id, { color: colorValue }); showToast("Đã đổi màu", "success"); setColorItem(null); fetchItems(currentFolderId); } catch (e: any) { showToast(e.message, "error"); } };
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault(); if (!searchQuery.trim() && !searchType) { fetchItems(currentFolderId); return; }
    setLoading(true);
    try {
      if (useAISearch) {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/ai/smart-search?q=${encodeURIComponent(searchQuery.trim())}`, { headers: { Authorization: `Bearer ${getAuthToken()}` } });
        const data = await res.json();
        if (res.ok && data.data && Array.isArray(data.data)) setItems(data.data);
        else setItems(await searchStorageItemsAPI(searchQuery.trim(), searchType || undefined));
      } else { setItems(await searchStorageItemsAPI(searchQuery.trim(), searchType || undefined)); }
    } catch (e: any) { showToast(e.message, "error"); } finally { setLoading(false); }
  };
  const handleCopy = async (item: StorageItem) => { try { await copyStorageItemAPI(item._id, currentFolderId); showToast("Đã sao chép", "success"); fetchItems(currentFolderId); } catch (e: any) { showToast(e.message, "error"); } };
  const handleCreateShortcut = async (item: StorageItem) => { try { await createShortcutAPI(item._id, currentFolderId); showToast("Đã tạo lối tắt", "success"); fetchItems(currentFolderId); } catch (e: any) { showToast(e.message, "error"); } };
  const handleToggleStar = async (item: StorageItem) => { try { await updateStorageItemAPI(item._id, { is_starred: !item.is_starred }); fetchItems(currentFolderId); } catch (e: any) { showToast(e.message, "error"); } };
  const handleTogglePublic = async (item: StorageItem) => {
    try {
      if (!item.is_public) { await updateStorageItemAPI(item._id, { is_public: true }); showToast("Đã bật chia sẻ công khai", "success"); fetchItems(currentFolderId); }
      else { navigator.clipboard.writeText(`${window.location.origin}/storage/share/${item.share_token}`); showToast("Đã copy link", "success"); }
    } catch (e: any) { showToast(e.message, "error"); }
  };
  const handleShareSubmit = async () => { if (!shareItem || !shareEmail.trim()) return; try { await shareStorageItemAPI(shareItem._id, shareEmail.trim(), shareRole); showToast("Đã chia sẻ", "success"); setShareItem(null); setShareEmail(""); setShareRole("viewer"); fetchItems(currentFolderId); } catch (e: any) { showToast(e.message, "error"); } };
  const handleZipDownload = async () => { if (selectedIds.size === 0) return; showToast("Đang tạo zip", "success"); try { await downloadZipAPI(Array.from(selectedIds)); setSelectedIds(new Set()); } catch (e: any) { showToast(e.message, "error"); } };
  const toggleSelect = (id: string) => { const n = new Set(selectedIds); if (n.has(id)) n.delete(id); else n.add(id); setSelectedIds(n); };
  const handleUploadVersion = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files; if (!files?.length || !versionItem) return;
    setUploading(true);
    try { await uploadFileVersionAPI(versionItem._id, files[0]); showToast("Đã tải lên phiên bản mới", "success"); setVersionItem(null); fetchItems(currentFolderId); }
    catch (e: any) { showToast(e.message, "error"); } finally { setUploading(false); if (versionInputRef.current) versionInputRef.current.value = ""; }
  };

  const formatSize = (bytes: number) => {
    if (!bytes) return "--"; const k = 1024; const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k)); return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] font-sans text-[#1D1D1F] flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-center justify-end gap-4">
        <div className="flex items-center gap-3">
          {quota && (
            <div className="flex flex-col items-end mr-4">
              <span className="text-[13px] font-medium text-[#6E6E73]">{formatSize(quota.used)} / {formatSize(quota.limit)}</span>
              <div className="w-24 h-1.5 bg-[#E8E8ED] rounded-full mt-1 overflow-hidden">
                <div className="h-full bg-[#0071E3] rounded-full" style={{ width: `${Math.min(100, (quota.used / quota.limit) * 100)}%` }} />
              </div>
            </div>
          )}
          {viewMode === "trash" || viewMode === "recent" ? (
            <button onClick={() => setViewMode("files")} className="pill-button bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED]">Trở về thư mục</button>
          ) : (
            <>
              <button onClick={() => setViewMode("recent")} className="pill-button bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] flex items-center gap-2"><Clock className="w-4 h-4"/> Gần đây</button>
              <button onClick={() => setViewMode("trash")} className="pill-button bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] flex items-center gap-2"><Trash2 className="w-4 h-4"/> Thùng rác</button>
              <button onClick={() => setCreateFolderOpen(true)} className="pill-button bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] flex items-center gap-2"><Plus className="w-4 h-4"/> Thư mục mới</button>
              <button onClick={() => fileInputRef.current?.click()} disabled={uploading} className="pill-button flex items-center gap-2 disabled:opacity-50">
                {uploading ? <Loader2 className="w-4 h-4 animate-spin"/> : <Upload className="w-4 h-4"/>} Tải lên
              </button>
            </>
          )}
          <input type="file" ref={fileInputRef} onChange={handleUpload} className="hidden" multiple />
          <input type="file" ref={versionInputRef} onChange={handleUploadVersion} className="hidden" />
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-8 flex-1 min-h-0">
        <main className={`flex flex-col gap-6 h-full min-h-0 ${detailsItem ? "lg:col-span-8" : "lg:col-span-12"}`}>
          <div className="bg-[#F5F5F7] rounded-[24px] p-4 flex flex-col md:flex-row justify-between items-center shadow-sm">
            <div className="flex items-center gap-2 text-[15px] text-[#6E6E73] font-medium px-2">
              {viewMode === "trash" ? <span className="text-[#1D1D1F]">Thùng rác</span> : viewMode === "recent" ? <span className="text-[#1D1D1F]">Mở gần đây</span> : breadcrumbs.map((crumb, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <button onClick={() => handleNavigateBreadcrumb(idx)} className={`flex items-center gap-1 transition-colors ${idx === breadcrumbs.length - 1 ? "text-[#1D1D1F]" : "hover:text-[#1D1D1F]"}`}>
                    {crumb.name === "Lưu trữ gốc" ? <Home className="w-4 h-4" /> : crumb.name}
                  </button>
                  {idx < breadcrumbs.length - 1 && <ChevronRight className="w-4 h-4 text-[#A1A1A6]" />}
                </div>
              ))}
            </div>
            {viewMode === "files" && (
              <form onSubmit={handleSearch} className="flex items-center gap-2 mt-4 md:mt-0">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6E6E73]" />
                  <input type="text" placeholder={useAISearch ? "AI tìm tài liệu..." : "Tìm kiếm theo tên..."} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="apple-input pl-9 pr-4 w-64 text-[14px]" />
                </div>
                <button type="button" onClick={() => setUseAISearch(!useAISearch)} className={`px-3 py-1.5 rounded-[12px] text-[13px] font-semibold transition-colors ${useAISearch ? "bg-[#0071E3] text-white" : "bg-[#E8E8ED] text-[#6E6E73] hover:bg-[#D1D1D6]"}`}>AI</button>
                <select value={searchType} onChange={(e) => setSearchType(e.target.value as any)} className="apple-input px-3 py-1.5 text-[14px] bg-white h-[36px] w-28">
                  <option value="">Tất cả</option>
                  <option value="folder">Thư mục</option>
                  <option value="file">Tệp tin</option>
                </select>
                {selectedIds.size > 0 && <button onClick={handleZipDownload} className="pill-button px-4 py-1.5 h-[36px] text-[13px] bg-[#1D1D1F] flex items-center gap-1"><Archive className="w-3.5 h-3.5"/> ZIP ({selectedIds.size})</button>}
                <div className="flex bg-[#E8E8ED] rounded-[12px] p-0.5 ml-2">
                  <button onClick={() => setLayoutMode("list")} className={`p-1.5 rounded-[10px] transition-colors ${layoutMode === "list" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}><ListIcon className="w-4 h-4" /></button>
                  <button onClick={() => setLayoutMode("grid")} className={`p-1.5 rounded-[10px] transition-colors ${layoutMode === "grid" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}><Grid className="w-4 h-4" /></button>
                </div>
              </form>
            )}
          </div>

          <div onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop} className={`bg-[#F5F5F7] rounded-[24px] border-[#E8E8ED] flex-1 overflow-y-auto no-scrollbar p-2 ${isDraggingOver ? "border-[#0071E3] bg-[#F5F5F7]/50" : ""}`}>
            {loading ? (
              <div className="flex justify-center items-center h-full"><Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" /></div>
            ) : layoutMode === "list" ? (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-[#E8E8ED] text-[13px] text-[#6E6E73]">
                    <th className="py-3 px-6 font-medium w-12"></th>
                    <th className="py-3 px-6 font-medium">Tên</th>
                    <th className="py-3 px-6 font-medium">Kích thước</th>
                    <th className="py-3 px-6 font-medium">Cập nhật</th>
                    <th className="py-3 px-6 font-medium text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 ? (
                    <tr><td colSpan={5} className="py-20 text-center text-[15px] text-[#6E6E73]">Thư mục trống</td></tr>
                  ) : items.map((item) => (
                    <tr key={item._id} onClick={() => setDetailsItem(item)} className="border-b border-[#F5F5F7] hover:bg-[#F5F5F7] transition-colors cursor-pointer group">
                      <td className="py-3 px-6" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center gap-3">
                          <input type="checkbox" checked={selectedIds.has(item._id)} onChange={() => toggleSelect(item._id)} className="w-4 h-4 rounded-[4px] border-[#C7C7CC] accent-[#0071E3]" />
                          <div className="w-9 h-9 bg-[#F5F5F7] rounded-[10px] flex items-center justify-center relative">
                            {item.color && <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-white" style={{ backgroundColor: item.color }} />}
                            {item.is_shortcut ? <LinkIcon className="w-4 h-4 text-[#0071E3]" /> : item.is_folder ? <Folder className="w-4 h-4 text-[#1D1D1F]" /> : <File className="w-4 h-4 text-[#6E6E73]" />}
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-6">
                        <div className="flex items-center gap-2">
                          {item.is_starred && <Star className="w-4 h-4 text-[#FF9500] fill-[#FF9500]" />}
                          {item.is_folder ? <button onClick={(e) => { e.stopPropagation(); handleNavigate(item); }} className="text-[14px] font-medium text-[#1D1D1F] hover:text-[#0071E3] truncate max-w-[200px]">{item.name}</button> : item.url ? <a href={item.url} target="_blank" className="text-[14px] font-medium text-[#1D1D1F] hover:text-[#0071E3] truncate max-w-[200px]">{item.name}</a> : <span className="text-[14px] font-medium text-[#1D1D1F] truncate max-w-[200px]">{item.name}</span>}
                          {item.versions && item.versions.length > 0 && <span className="text-[10px] font-medium bg-[#E8E8ED] text-[#6E6E73] px-2 py-0.5 rounded-full">v{item.versions.length + 1}</span>}
                        </div>
                      </td>
                      <td className="py-3 px-6 text-[13px] text-[#6E6E73]">{item.is_folder ? "--" : formatSize(item.size)}</td>
                      <td className="py-3 px-6 text-[13px] text-[#6E6E73]">{new Date(item.updated_at).toLocaleDateString("vi-VN")}</td>
                      <td className="py-3 px-6 text-right">
                        <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          {viewMode === "trash" ? (
                            <>
                              <button onClick={() => handleRestore(item)} className="p-1.5 text-[#0071E3] hover:bg-[#0071E3]/10 rounded-[8px]">Khôi phục</button>
                              <button onClick={() => handleDelete(item)} className="p-1.5 text-[#FF3B30] hover:bg-[#FF3B30]/10 rounded-[8px]">Xóa</button>
                            </>
                          ) : (
                            <>
                              <button onClick={() => handleToggleStar(item)} className="p-1.5 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[8px]"><Star className={`w-4 h-4 ${item.is_starred ? "text-[#FF9500] fill-[#FF9500]" : ""}`} /></button>
                              <button onClick={() => setShareItem(item)} className="p-1.5 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[8px]"><Share2 className={`w-4 h-4 ${item.is_public ? "text-[#0071E3]" : ""}`} /></button>
                              {!item.is_folder && <button onClick={() => { setVersionItem(item); versionInputRef.current?.click(); }} className="p-1.5 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[8px]"><History className="w-4 h-4" /></button>}
                              <button onClick={(e) => { e.stopPropagation(); setRenameItem(item); setNewName(item.name); }} className="p-1.5 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[8px]"><Edit2 className="w-4 h-4" /></button>
                              <button onClick={() => { setMoveItem(item); setMoveTargetId(undefined); setMoveBreadcrumbs([{ name: "Lưu trữ gốc" }]); }} className="p-1.5 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[8px]"><MoreVertical className="w-4 h-4" /></button>
                              <button onClick={() => handleDelete(item)} className="p-1.5 text-[#6E6E73] hover:bg-[#FF3B30]/10 hover:text-[#FF3B30] rounded-[8px]"><Trash2 className="w-4 h-4" /></button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 p-4">
                {items.map((item) => (
                  <div key={item._id} onClick={() => setDetailsItem(item)} className="group relative bg-[#F5F5F7] border border-transparent hover:border-[#E8E8ED] hover:bg-white hover:shadow-sm rounded-[20px] p-4 flex flex-col items-center justify-between text-center transition-all cursor-pointer">
                    <div className="absolute top-3 left-3 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                      <input type="checkbox" checked={selectedIds.has(item._id)} onChange={() => toggleSelect(item._id)} onClick={(e) => e.stopPropagation()} className="w-4 h-4 rounded-[4px] border-[#C7C7CC] accent-[#0071E3]" />
                    </div>
                    <div className="w-16 h-16 bg-white flex items-center justify-center mb-3 rounded-[14px] shadow-sm relative">
                      {item.color && <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-white" style={{ backgroundColor: item.color }} />}
                      {item.is_shortcut ? <LinkIcon className="w-8 h-8 text-[#0071E3]" /> : item.is_folder ? <Folder className="w-8 h-8 text-[#1D1D1F]" /> : item.mime_type?.startsWith("image/") ? <img src={item.url} alt={item.name} className="w-full h-full object-cover rounded-[14px]" /> : <File className="w-8 h-8 text-[#6E6E73]" />}
                    </div>
                    <div className="w-full">
                      {item.is_folder ? <button onClick={(e) => { e.stopPropagation(); handleNavigate(item); }} className="text-[14px] font-medium text-[#1D1D1F] truncate w-full block">{item.name}</button> : <span className="text-[14px] font-medium text-[#1D1D1F] truncate w-full block">{item.name}</span>}
                      <span className="text-[12px] text-[#6E6E73] mt-1">{item.is_folder ? "--" : formatSize(item.size)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>

        {detailsItem && (
          <aside className="lg:col-span-4 flex flex-col gap-6 h-full min-h-0 bg-[#F5F5F7] rounded-[24px] border-[#E8E8ED] overflow-hidden relative">
            <div className="p-6 border-b border-[#E8E8ED] flex justify-between items-center bg-white sticky top-0 z-10">
              <h2 className="text-[18px] font-semibold text-[#1D1D1F]">Chi tiết</h2>
              <button onClick={() => setDetailsItem(null)} className="w-8 h-8 flex items-center justify-center bg-[#F5F5F7] rounded-full text-[#6E6E73] hover:text-[#1D1D1F]"><X className="w-4 h-4"/></button>
            </div>
            <div className="flex bg-[#F5F5F7] mx-6 mt-4 p-1 rounded-[14px]">
              <button className={`flex-1 py-2 text-[14px] font-medium rounded-[10px] transition-colors ${activeSidebarTab === "info" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73]"}`} onClick={() => setActiveSidebarTab("info")}>Thông tin</button>
              <button className={`flex-1 py-2 text-[14px] font-medium rounded-[10px] transition-colors ${activeSidebarTab === "ai" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73]"}`} onClick={() => setActiveSidebarTab("ai")}>AI Trợ lý</button>
            </div>

            {activeSidebarTab === "info" ? (
              <div className="flex-1 overflow-y-auto no-scrollbar p-6 space-y-6">
                <div className="flex flex-col items-center">
                  <div className="w-24 h-24 bg-[#F5F5F7] flex items-center justify-center rounded-[20px] mb-4">
                    {detailsItem.is_folder ? <Folder className="w-12 h-12 text-[#1D1D1F]" /> : <File className="w-12 h-12 text-[#6E6E73]" />}
                  </div>
                  <h3 className="text-[16px] font-semibold text-[#1D1D1F] text-center max-w-full break-words">{detailsItem.name}</h3>
                </div>
                <div className="bg-[#F5F5F7] rounded-[18px] p-5 space-y-3">
                  <div className="flex justify-between items-center text-[14px]"><span className="text-[#6E6E73]">Loại</span><span className="font-medium">{detailsItem.is_folder ? "Thư mục" : detailsItem.mime_type || "Tệp tin"}</span></div>
                  <div className="flex justify-between items-center text-[14px]"><span className="text-[#6E6E73]">Kích thước</span><span className="font-medium">{detailsItem.is_folder ? "--" : formatSize(detailsItem.size)}</span></div>
                  <div className="flex justify-between items-center text-[14px]"><span className="text-[#6E6E73]">Tạo lúc</span><span className="font-medium">{new Date(detailsItem.created_at).toLocaleDateString("vi-VN")}</span></div>
                  <div className="flex justify-between items-center text-[14px]"><span className="text-[#6E6E73]">Sửa đổi</span><span className="font-medium">{new Date(detailsItem.updated_at).toLocaleDateString("vi-VN")}</span></div>
                </div>
                {detailsItem.description && (
                  <div><h4 className="text-[14px] font-medium text-[#6E6E73] mb-2">Ghi chú AI</h4><div className="bg-[#F5F5F7] rounded-[14px] p-4 text-[14px] leading-relaxed">{detailsItem.description}</div></div>
                )}
                {detailsItem.tags && detailsItem.tags.length > 0 && (
                  <div>
                    <h4 className="text-[14px] font-medium text-[#6E6E73] mb-2">Nhãn</h4>
                    <div className="flex flex-wrap gap-2">{detailsItem.tags.map((t) => (<span key={t} className="px-3 py-1 bg-[#E8E8ED] text-[#1D1D1F] text-[12px] font-medium rounded-full">{t}</span>))}</div>
                  </div>
                )}
                {relatedItems.length > 0 && (
                  <div>
                    <h4 className="text-[14px] font-medium text-[#6E6E73] mb-2">Liên quan</h4>
                    <div className="space-y-2">
                      {relatedItems.map((item) => (
                        <div key={item._id} onClick={() => setDetailsItem(item)} className="flex items-center gap-3 p-3 bg-[#F5F5F7] hover:bg-[#E8E8ED] rounded-[14px] cursor-pointer transition-colors"><File className="w-4 h-4 text-[#6E6E73]" /><span className="text-[14px] font-medium flex-1 truncate">{item.name}</span></div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col flex-1 overflow-hidden p-6 pb-4">
                <div className="flex-1 overflow-y-auto no-scrollbar space-y-4 mb-4">
                  {chatHistory.length === 0 ? <p className="text-center text-[#6E6E73] text-[14px] mt-10">Tôi có thể giúp bạn tìm kiếm nội dung hoặc tóm tắt tài liệu này.</p> : chatHistory.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div className={`p-3 max-w-[85%] rounded-[18px] text-[14px] leading-relaxed ${msg.role === "user" ? "bg-[#0071E3] text-white rounded-tr-[4px]" : "bg-[#F5F5F7] text-[#1D1D1F] rounded-tl-[4px]"}`}>{msg.content}</div>
                    </div>
                  ))}
                </div>
                <form onSubmit={async (e) => {
                  e.preventDefault(); if (!chatInput.trim()) return;
                  const newMsg = { role: "user", content: chatInput.trim() }; setChatHistory(p => [...p, newMsg]); setChatInput("");
                  try {
                    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/chat/chat`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${getAuthToken()}` }, body: JSON.stringify({ query: newMsg.content, document_id: detailsItem._id }) });
                    if (res.ok && res.body) {
                      const reader = res.body.getReader(); const decoder = new TextDecoder("utf-8"); let botMsg = ""; setChatHistory(p => [...p, { role: "bot", content: "" }]);
                      while (true) { const { done, value } = await reader.read(); if (done) break; botMsg += decoder.decode(value, { stream: true }); setChatHistory(p => { const next = [...p]; next[next.length - 1].content = botMsg.replace(/data: /g, "").replace(/\n\n/g, ""); return next; }); }
                    }
                  } catch (e) { setChatHistory(p => [...p, { role: "bot", content: "Lỗi kết nối AI." }]); }
                }} className="flex gap-2">
                  <input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Hỏi AI trợ lý..." className="apple-input flex-1 bg-[#F5F5F7] border-transparent" />
                  <button type="submit" className="pill-button">Gửi</button>
                </form>
              </div>
            )}
          </aside>
        )}
      </div>

      <Modal isOpen={createFolderOpen} onClose={() => setCreateFolderOpen(false)} className="max-w-sm bg-[#F5F5F7] rounded-[24px] p-0 shadow-2xl border-none">
        <ModalHeader className="p-6"><ModalTitle className="text-[20px] font-semibold">Tạo thư mục mới</ModalTitle></ModalHeader>
        <ModalContent className="p-6 pt-0"><input type="text" value={newFolderName} onChange={(e) => setNewFolderName(e.target.value)} placeholder="Nhập tên thư mục" className="apple-input w-full bg-white" autoFocus /></ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3"><button onClick={() => setCreateFolderOpen(false)} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full">Hủy</button><button onClick={handleCreateFolder} className="pill-button">Tạo</button></ModalFooter>
      </Modal>

      <Modal isOpen={!!renameItem} onClose={() => setRenameItem(null)} className="max-w-sm bg-[#F5F5F7] rounded-[24px] p-0 shadow-2xl border-none">
        <ModalHeader className="p-6"><ModalTitle className="text-[20px] font-semibold">Đổi tên</ModalTitle></ModalHeader>
        <ModalContent className="p-6 pt-0"><input type="text" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Tên mới" className="apple-input w-full bg-white" autoFocus /></ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3"><button onClick={() => setRenameItem(null)} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full">Hủy</button><button onClick={handleRename} className="pill-button">Lưu</button></ModalFooter>
      </Modal>

      <Modal isOpen={!!shareItem} onClose={() => setShareItem(null)} className="max-w-md bg-[#F5F5F7] rounded-[24px] p-0 shadow-2xl border-none">
        <ModalHeader className="p-6"><ModalTitle className="text-[20px] font-semibold">Chia sẻ {shareItem?.name}</ModalTitle></ModalHeader>
        <ModalContent className="p-6 pt-0 space-y-6">
          <div>
            <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Mời người dùng</label>
            <div className="flex gap-2"><input type="email" value={shareEmail} onChange={(e) => setShareEmail(e.target.value)} placeholder="Email..." className="apple-input flex-1 bg-white" /><select value={shareRole} onChange={(e) => setShareRole(e.target.value)} className="apple-input w-28 bg-white"><option value="viewer">Xem</option><option value="editor">Sửa</option></select></div>
            <button onClick={handleShareSubmit} className="mt-3 w-full pill-button">Chia sẻ ngay</button>
          </div>
          <div className="pt-4 border-t border-[#E8E8ED]">
            <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">Liên kết công khai</label>
            <button onClick={() => handleTogglePublic(shareItem!)} className="w-full py-3 bg-white rounded-[14px] text-[14px] font-medium text-[#1D1D1F] border border-[#E8E8ED] flex items-center justify-center gap-2"><Share2 className="w-4 h-4"/>{shareItem?.is_public ? "Sao chép link public" : "Tạo link public"}</button>
          </div>
        </ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end"><button onClick={() => setShareItem(null)} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full">Đóng</button></ModalFooter>
      </Modal>

      <Modal isOpen={!!moveItem} onClose={() => setMoveItem(null)} className="max-w-sm bg-[#F5F5F7] rounded-[24px] p-0 shadow-2xl border-none">
        <ModalHeader className="p-6"><ModalTitle className="text-[20px] font-semibold">Chuyển đến</ModalTitle></ModalHeader>
        <ModalContent className="p-6 pt-0 max-h-[300px] overflow-y-auto no-scrollbar">
          <div className="flex gap-1 text-[13px] text-[#0071E3] mb-4 overflow-x-auto no-scrollbar whitespace-nowrap">
            {moveBreadcrumbs.map((c, i) => (<button key={i} onClick={() => { setMoveTargetId(c.id); setMoveBreadcrumbs(moveBreadcrumbs.slice(0, i + 1)); }} className="hover:underline">{c.name}{i < moveBreadcrumbs.length - 1 && " / "}</button>))}
          </div>
          <div className="space-y-2">
            {moveFolders.map(f => (<button key={f._id} onClick={() => { setMoveTargetId(f._id); setMoveBreadcrumbs([...moveBreadcrumbs, { id: f._id, name: f.name }]); }} className="w-full flex items-center gap-3 p-3 bg-white rounded-[14px] hover:bg-[#E8E8ED] transition-colors"><Folder className="w-5 h-5 text-[#1D1D1F]"/><span className="text-[14px] font-medium truncate">{f.name}</span></button>))}
            {moveFolders.length === 0 && <p className="text-center text-[#6E6E73] text-[13px]">Không có thư mục con</p>}
          </div>
        </ModalContent>
        <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3"><button onClick={() => setMoveItem(null)} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full">Hủy</button><button onClick={handleMove} className="pill-button">Chuyển tới đây</button></ModalFooter>
      </Modal>
    </div>
  );
}
