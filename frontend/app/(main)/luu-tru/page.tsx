"use client";

import { useEffect, useState, useRef } from "react";
import { 
  StorageItem, 
  listStorageItemsAPI, 
  createFolderAPI, 
  uploadStorageFileAPI,
  deleteStorageItemAPI,
  updateStorageItemAPI,
  searchStorageItemsAPI,
  copyStorageItemAPI,
  uploadFileVersionAPI,
  getRecentStorageItemsAPI,
  shareStorageItemAPI,
  getStorageQuotaAPI,
  createShortcutAPI,
  downloadZipAPI
} from "@/services/storage.service";
import { useToast } from "@/contexts/Toast";
import { 
  Folder, 
  File, 
  Upload, 
  Plus, 
  ChevronRight, 
  MoreVertical, 
  Trash2, 
  Edit2, 
  Download,
  Loader2,
  Search,
  Copy,
  Star,
  Share2,
  History,
  Tag,
  MessageSquare,
  Grid,
  List as ListIcon,
  Clock,
  Info,
  Link,
  Palette,
  Archive
} from "lucide-react";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from "@/components/ui/Modal";

export default function StoragePage() {
  const { showToast } = useToast();
  const [items, setItems] = useState<StorageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [currentFolderId, setCurrentFolderId] = useState<string | undefined>(undefined);
  const [breadcrumbs, setBreadcrumbs] = useState<{id?: string, name: string}[]>([{ name: "Kho lưu trữ gốc" }]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [createFolderOpen, setCreateFolderOpen] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");

  const [renameItem, setRenameItem] = useState<StorageItem | null>(null);
  const [newName, setNewName] = useState("");

  const [descItem, setDescItem] = useState<StorageItem | null>(null);
  const [descValue, setDescValue] = useState("");

  const [tagsItem, setTagsItem] = useState<StorageItem | null>(null);
  const [tagsValue, setTagsValue] = useState("");

  const [viewMode, setViewMode] = useState<'files' | 'trash' | 'recent'>('files');
  const [moveItem, setMoveItem] = useState<StorageItem | null>(null);
  const [moveTargetId, setMoveTargetId] = useState<string | undefined>(undefined);
  const [moveBreadcrumbs, setMoveBreadcrumbs] = useState<{id?: string, name: string}[]>([{ name: "Kho lưu trữ gốc" }]);
  const [moveFolders, setMoveFolders] = useState<StorageItem[]>([]);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchType, setSearchType] = useState<'' | 'folder' | 'file'>('');
  const versionInputRef = useRef<HTMLInputElement>(null);
  const [versionItem, setVersionItem] = useState<StorageItem | null>(null);

  const [layoutMode, setLayoutMode] = useState<'list' | 'grid'>('list');
  const [isDraggingOver, setIsDraggingOver] = useState(false);

  const [shareItem, setShareItem] = useState<StorageItem | null>(null);
  const [shareEmail, setShareEmail] = useState("");
  const [shareRole, setShareRole] = useState("viewer");

  const [useAISearch, setUseAISearch] = useState(false);
  const [activeSidebarTab, setActiveSidebarTab] = useState<'info' | 'ai'>('info');
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<{role: string, content: string}[]>([]);

  const [quota, setQuota] = useState<{used: number, limit: number} | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [detailsItem, setDetailsItem] = useState<StorageItem | null>(null);
  const [relatedItems, setRelatedItems] = useState<StorageItem[]>([]);
  
  const [colorItem, setColorItem] = useState<StorageItem | null>(null);
  const [colorValue, setColorValue] = useState("");

  const fetchQuota = async () => {
    try {
      const q = await getStorageQuotaAPI();
      setQuota(q);
    } catch (e: any) { showToast(e.message || "Lỗi tải thông tin dung lượng", "error"); }
  };

  useEffect(() => { fetchQuota(); }, []);

  const fetchItems = async (folderId?: string, mode: typeof viewMode = viewMode) => {
    setLoading(true);
    try {
      if (mode === 'recent') {
        const data = await getRecentStorageItemsAPI(20);
        setItems(data);
      } else {
        const isTrashed = mode === 'trash';
        const data = await listStorageItemsAPI(folderId, isTrashed);
        setItems(data);
      }
    } catch (error: any) {
      showToast(error.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const fetchMoveFolders = async (folderId?: string) => {
    try {
      const data = await listStorageItemsAPI(folderId);
      setMoveFolders(data.filter(item => item.is_folder && item._id !== moveItem?._id));
    } catch (error: any) {
      showToast(error.message || "Lỗi tải danh sách thư mục", "error");
    }
  };

  useEffect(() => {
    fetchItems(viewMode === 'trash' || viewMode === 'recent' ? undefined : currentFolderId, viewMode);
  }, [currentFolderId, viewMode]);

  useEffect(() => {
    if (detailsItem && activeSidebarTab === 'info') {
      import('@/services/storage.service').then(m => {
        m.getRelatedStorageItemsAPI(detailsItem._id)
         .then(data => setRelatedItems(data))
         .catch(err => console.error(err));
      });
    }
  }, [detailsItem, activeSidebarTab]);

  useEffect(() => {
    if (moveItem) {
      fetchMoveFolders(moveTargetId);
    }
  }, [moveTargetId, moveItem]);

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;
    try {
      await createFolderAPI(newFolderName.trim(), currentFolderId);
      showToast("Tạo thư mục thành công", "success");
      setCreateFolderOpen(false);
      setNewFolderName("");
      fetchItems(currentFolderId);
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    setUploading(true);
    try {
      for (let i = 0; i < files.length; i++) {
        await uploadStorageFileAPI(files[i], currentFolderId);
      }
      showToast("Tải lên thành công", "success");
      fetchItems(currentFolderId);
      fetchQuota();
    } catch (error: any) {
      showToast(error.message, "error");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (viewMode !== 'trash' && viewMode !== 'recent') {
      setIsDraggingOver(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
    if (viewMode === 'trash' || viewMode === 'recent') return;
    
    const files = e.dataTransfer.files;
    if (!files || files.length === 0) return;
    
    setUploading(true);
    try {
      for (let i = 0; i < files.length; i++) {
        await uploadStorageFileAPI(files[i], currentFolderId);
      }
      showToast("Tải lên thành công", "success");
      fetchItems(currentFolderId);
    } catch (error: any) {
      showToast(error.message, "error");
    } finally {
      setUploading(false);
    }
  };

  const handleNavigate = (folder: StorageItem) => {
    if (folder.is_shortcut && folder.target_id) {
      return;
    }
    setCurrentFolderId(folder._id);
    setBreadcrumbs([...breadcrumbs, { id: folder._id, name: folder.name }]);
  };

  const handleNavigateBreadcrumb = (index: number) => {
    const crumb = breadcrumbs[index];
    setCurrentFolderId(crumb.id);
    setBreadcrumbs(breadcrumbs.slice(0, index + 1));
  };

  const handleDelete = async (item: StorageItem) => {
    if (viewMode === 'trash') {
      if (!window.confirm(`Bạn có chắc muốn xóa vĩnh viễn ${item.name}?`)) return;
      try {
        await deleteStorageItemAPI(item._id, true);
        showToast("Đã xóa vĩnh viễn", "success");
        fetchItems(undefined, true);
        fetchQuota();
      } catch (error: any) {
        showToast(error.message, "error");
      }
    } else {
      if (!window.confirm(`Bạn có chắc muốn đưa ${item.name} vào thùng rác?`)) return;
      try {
        await deleteStorageItemAPI(item._id, false);
        showToast("Đã đưa vào thùng rác", "success");
        fetchItems(currentFolderId, false);
      } catch (error: any) {
        showToast(error.message, "error");
      }
    }
  };

  const handleRestore = async (item: StorageItem) => {
    try {
      await updateStorageItemAPI(item._id, { is_trashed: false });
      showToast("Khôi phục thành công", "success");
      fetchItems(undefined, true);
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const handleMove = async () => {
    if (!moveItem) return;
    try {
      const payloadParentId = moveTargetId === undefined ? null : moveTargetId;
      await updateStorageItemAPI(moveItem._id, { parent_id: payloadParentId as any });
      showToast("Di chuyển thành công", "success");
      setMoveItem(null);
      setMoveTargetId(undefined);
      setMoveBreadcrumbs([{ name: "Kho lưu trữ gốc" }]);
      fetchItems(currentFolderId);
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const handleRename = async () => {
    if (!renameItem || !newName.trim()) return;
    try {
      await updateStorageItemAPI(renameItem._id, { name: newName.trim() });
      showToast("Đổi tên thành công", "success");
      setRenameItem(null);
      setNewName("");
      fetchItems(currentFolderId);
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const handleUpdateDesc = async () => {
    if (!descItem) return;
    try {
      await updateStorageItemAPI(descItem._id, { description: descValue.trim() });
      showToast("Cập nhật ghi chú thành công", "success");
      setDescItem(null);
      setDescValue("");
      fetchItems(currentFolderId);
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const handleUpdateTags = async () => {
    if (!tagsItem) return;
    try {
      const tagsArray = tagsValue.split(",").map(t => t.trim()).filter(t => t.length > 0);
      await updateStorageItemAPI(tagsItem._id, { tags: tagsArray });
      showToast("Cập nhật nhãn thành công", "success");
      setTagsItem(null);
      setTagsValue("");
      fetchItems(currentFolderId);
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const handleUpdateColor = async () => {
    if (!colorItem) return;
    try {
      await updateStorageItemAPI(colorItem._id, { color: colorValue });
      showToast("Cập nhật màu thành công", "success");
      setColorItem(null);
      fetchItems(currentFolderId);
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() && !searchType) {
      fetchItems(currentFolderId);
      return;
    }
    setLoading(true);
    try {
      if (useAISearch) {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/ai/tim-kiem-thong-minh?q=${encodeURIComponent(searchQuery.trim())}`, {
          headers: { Authorization: `Bearer ${getAuthToken()}` }
        });
        const data = await res.json();
        if (res.ok && data.data && Array.isArray(data.data)) {
          setItems(data.data);
        } else {
          const normalData = await searchStorageItemsAPI(searchQuery.trim(), searchType || undefined);
          setItems(normalData);
        }
      } else {
        const data = await searchStorageItemsAPI(searchQuery.trim(), searchType || undefined);
        setItems(data);
      }
    } catch (error: any) {
      showToast(error.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (item: StorageItem) => {
    try {
      await copyStorageItemAPI(item._id, currentFolderId);
      showToast("Sao chép thành công", "success");
      fetchItems(currentFolderId);
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const handleCreateShortcut = async (item: StorageItem) => {
    try {
      await createShortcutAPI(item._id, currentFolderId);
      showToast("Đã tạo lối tắt", "success");
      fetchItems(currentFolderId);
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const handleToggleStar = async (item: StorageItem) => {
    try {
      await updateStorageItemAPI(item._id, { is_starred: !item.is_starred });
      fetchItems(currentFolderId);
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const handleTogglePublic = async (item: StorageItem) => {
    try {
      if (!item.is_public) {
        await updateStorageItemAPI(item._id, { is_public: true });
        showToast("Đã bật chia sẻ liên kết công khai.", "success");
        fetchItems(currentFolderId);
      } else {
        const link = `${window.location.origin}/api/luu-tru/chia-se/${item.share_token}`;
        navigator.clipboard.writeText(link);
        showToast("Đã copy liên kết công khai", "success");
      }
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const handleShareSubmit = async () => {
    if (!shareItem || !shareEmail.trim()) return;
    try {
      await shareStorageItemAPI(shareItem._id, shareEmail.trim(), shareRole);
      showToast("Đã chia sẻ tệp tin thành công", "success");
      setShareItem(null);
      setShareEmail("");
      setShareRole("viewer");
      fetchItems(currentFolderId);
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const handleZipDownload = async () => {
    if (selectedIds.size === 0) return;
    showToast("Đang chuẩn bị file Zip", "success");
    try {
      await downloadZipAPI(Array.from(selectedIds));
      setSelectedIds(new Set());
    } catch (error: any) {
      showToast(error.message, "error");
    }
  };

  const toggleSelect = (id: string) => {
    const newSet = new Set(selectedIds);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedIds(newSet);
  };

  const handleUploadVersion = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !versionItem) return;
    
    setUploading(true);
    try {
      await uploadFileVersionAPI(versionItem._id, files[0]);
      showToast("Tải lên phiên bản mới thành công", "success");
      setVersionItem(null);
      fetchItems(currentFolderId);
    } catch (error: any) {
      showToast(error.message, "error");
    } finally {
      setUploading(false);
      if (versionInputRef.current) versionInputRef.current.value = "";
    }
  };

  const formatSize = (bytes: number) => {
    if (!bytes) return "--";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  return (
    <div className="min-h-screen bg-white text-black font-sans flex overflow-hidden">
      <div className="flex-1 p-6 md:p-12 overflow-y-auto">
      <header className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
        <div>
          <div className="flex items-center gap-4 mb-2">
            <h1 className="text-3xl font-semibold">Kho lưu trữ</h1>
            {quota && (
              <div className="flex items-center gap-2 px-3 py-1 bg-zinc-100 border border-zinc-200 text-xs font-mono">
                <span>{formatSize(quota.used)} / {formatSize(quota.limit)}</span>
                <div className="w-20 h-1 bg-zinc-200">
                  <div className="h-full bg-black" style={{ width: `${Math.min(100, (quota.used / quota.limit) * 100)}%` }} />
                </div>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm text-zinc-600">
            {viewMode === 'trash' ? (
              <span className="font-semibold text-black">Thùng rác</span>
            ) : viewMode === 'recent' ? (
              <span className="font-semibold text-black">Gần đây</span>
            ) : (
              breadcrumbs.map((crumb, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <button 
                    onClick={() => handleNavigateBreadcrumb(idx)}
                    className={`${idx === breadcrumbs.length - 1 ? 'font-semibold text-black' : 'underline underline-offset-4'}`}
                  >
                    {crumb.name}
                  </button>
                  {idx < breadcrumbs.length - 1 && <ChevronRight className="w-4 h-4" />}
                </div>
              ))
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-4 items-center">
          {viewMode === 'trash' || viewMode === 'recent' ? (
            <button 
              onClick={() => setViewMode('files')}
              className="flex items-center gap-2 border border-black px-4 py-2 text-sm font-semibold uppercase bg-white text-black"
            >
              Quay lại
            </button>
          ) : (
            <>
              <button 
                onClick={() => setViewMode('recent')}
                className="flex items-center gap-2 border border-zinc-200 px-4 py-2 text-sm font-semibold uppercase bg-zinc-50 text-black"
              >
                <Clock className="w-4 h-4" />
                Gần đây
              </button>
              <button 
                onClick={() => setViewMode('trash')}
                className="flex items-center gap-2 border border-zinc-200 px-4 py-2 text-sm font-semibold uppercase bg-zinc-50 text-black"
              >
                <Trash2 className="w-4 h-4" />
                Thùng rác
              </button>
              <button 
                onClick={() => setCreateFolderOpen(true)}
                className="flex items-center gap-2 border border-black px-4 py-2 text-sm font-semibold uppercase bg-white text-black"
              >
                <Plus className="w-4 h-4" />
                Thư mục
              </button>
              <button 
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="flex items-center gap-2 border border-black px-4 py-2 text-sm font-semibold uppercase bg-black text-white disabled:opacity-50"
              >
                {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                Tải lên
              </button>
            </>
          )}
          <input type="file" ref={fileInputRef} onChange={handleUpload} className="hidden" multiple />
          <input type="file" ref={versionInputRef} onChange={handleUploadVersion} className="hidden" />
        </div>
      </header>

      {viewMode === 'files' && (
        <div className="mb-6 flex gap-2 items-center flex-wrap">
          <form onSubmit={handleSearch} className="flex gap-2 flex-1 min-w-[300px]">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
              <input 
                type="text" 
                placeholder={useAISearch ? "Hỏi AI tìm tài liệu" : "Tìm kiếm theo tên"}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full border border-zinc-200 pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-black font-sans"
              />
            </div>
            <button 
              type="button"
              onClick={() => setUseAISearch(!useAISearch)}
              className={`px-3 py-2 text-sm font-semibold border ${useAISearch ? 'border-black bg-black text-white' : 'border-zinc-200 bg-zinc-50 text-zinc-600'}`}
              title="Tìm kiếm ngữ nghĩa bằng AI"
            >
              AI
            </button>
            <select 
              value={searchType}
              onChange={(e) => setSearchType(e.target.value as any)}
              className="border border-zinc-200 px-4 py-2 text-sm focus:outline-none focus:border-black font-sans bg-white"
            >
              <option value="">Tất cả loại</option>
              <option value="folder">Thư mục</option>
              <option value="file">Tệp tin</option>
            </select>
            <button type="submit" className="px-4 py-2 bg-black text-white text-sm font-semibold border border-black">
              Tìm
            </button>
          </form>
          
          {selectedIds.size > 0 && (
            <button 
              onClick={handleZipDownload}
              className="flex items-center gap-2 border border-black bg-black text-white px-4 py-2 text-sm font-semibold ml-4"
            >
              <Archive className="w-4 h-4" />
              Tải xuống ZIP ({selectedIds.size})
            </button>
          )}

          <div className="flex border border-zinc-200 bg-white ml-auto">
            <button 
              onClick={() => setLayoutMode('list')} 
              className={`p-2 ${layoutMode === 'list' ? 'bg-black text-white' : 'text-zinc-500 hover:text-black'}`}
            >
              <ListIcon className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setLayoutMode('grid')} 
              className={`p-2 border-l border-zinc-200 ${layoutMode === 'grid' ? 'bg-black text-white' : 'text-zinc-500 hover:text-black'}`}
            >
              <Grid className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      <div 
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative ${isDraggingOver ? 'after:content-[""] after:absolute after:inset-0 after:border-2 after:border-dashed after:border-black after:bg-black/5 after:z-10' : ''}`}
      >
      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-300" />
        </div>
      ) : layoutMode === 'list' ? (
        <div className="border border-zinc-200 bg-white">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-zinc-200 bg-zinc-50">
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600 w-12"></th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Tên</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Kích thước</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Ngày cập nhật</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-sm text-zinc-500">
                    Thư mục này đang trống
                  </td>
                </tr>
              ) : (
                items.map(item => (
                  <tr key={item._id} className="border-b border-zinc-200 last:border-0 hover:bg-zinc-50 cursor-pointer" onClick={() => setDetailsItem(item)}>
                    <td className="py-4 px-6 align-middle" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center gap-3">
                        <input 
                          type="checkbox" 
                          checked={selectedIds.has(item._id)}
                          onChange={() => toggleSelect(item._id)}
                          className="w-4 h-4 accent-black"
                        />
                        <div className="w-8 h-8 bg-zinc-100 flex items-center justify-center relative">
                          {item.color && (
                            <div className="absolute top-0 right-0 w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                          )}
                          {item.is_shortcut ? <Link className="w-4 h-4 text-blue-500" /> : item.is_folder ? <Folder className="w-4 h-4 text-black" /> : <File className="w-4 h-4 text-zinc-500" />}
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6 align-middle">
                      <div className="flex items-center gap-2">
                        {item.is_starred && <Star className="w-4 h-4 text-black fill-black flex-shrink-0" />}
                        {item.is_folder ? (
                          <button 
                            onClick={(e) => { e.stopPropagation(); handleNavigate(item); }}
                            className="text-sm font-semibold underline underline-offset-4 text-left"
                          >
                            {item.name}
                          </button>
                        ) : item.url ? (
                          <a 
                            href={item.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-sm font-medium underline underline-offset-4"
                          >
                            {item.name}
                          </a>
                        ) : (
                          <span className="text-sm font-medium">{item.name}</span>
                        )}
                        {item.versions && item.versions.length > 0 && (
                          <span className="text-[10px] font-mono text-zinc-500 bg-zinc-100 px-1 border border-zinc-200">
                            v{item.versions.length + 1}
                          </span>
                        )}
                      </div>
                      {(item.description || (item.tags && item.tags.length > 0)) && (
                        <div className="flex flex-col gap-1 mt-1 ml-6">
                          {item.description && <span className="text-[11px] text-zinc-500 font-mono">{item.description}</span>}
                          {item.tags && item.tags.length > 0 && (
                            <div className="flex gap-1 flex-wrap">
                              {item.tags.map(t => <span key={t} className="text-[9px] bg-zinc-100 px-1 border border-zinc-200 text-zinc-500 font-mono">{t}</span>)}
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="py-4 px-6 align-middle text-sm font-mono text-zinc-600">
                      {item.is_folder ? "--" : formatSize(item.size)}
                    </td>
                    <td className="py-4 px-6 align-middle text-xs text-zinc-500">
                      {new Date(item.updated_at).toLocaleDateString('vi-VN')}
                    </td>
                    <td className="py-4 px-6 align-middle text-right">
                      <div className="flex justify-end gap-3">
                        {viewMode === 'trash' ? (
                          <>
                            <button 
                              onClick={() => handleRestore(item)}
                              className="text-xs font-semibold text-black underline underline-offset-4"
                            >
                              Khôi phục
                            </button>
                            <button 
                              onClick={() => handleDelete(item)}
                              className="text-xs font-semibold text-zinc-500"
                            >
                              Xóa vĩnh viễn
                            </button>
                          </>
                        ) : (
                          <>
                            <button 
                              onClick={() => handleToggleStar(item)}
                              className="text-xs font-semibold text-zinc-500"
                              title="Yêu thích"
                            >
                              {item.is_starred ? <Star className="w-4 h-4 text-black fill-black" /> : <Star className="w-4 h-4" />}
                            </button>
                            <button 
                              onClick={() => setShareItem(item)}
                              className="text-xs font-semibold text-zinc-500"
                              title="Chia sẻ"
                            >
                              <Share2 className={`w-4 h-4 ${item.is_public ? 'text-black' : ''}`} />
                            </button>
                            {!item.is_folder && (
                              <button 
                                onClick={() => {
                                  setVersionItem(item);
                                  versionInputRef.current?.click();
                                }}
                                className="text-xs font-semibold text-zinc-500"
                                title="Cập nhật phiên bản mới"
                              >
                                <History className="w-4 h-4" />
                              </button>
                            )}
                            <button 
                              onClick={() => handleCopy(item)}
                              className="text-xs font-semibold text-zinc-500"
                              title="Sao chép"
                            >
                              <Copy className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => {
                                setDescItem(item);
                                setDescValue(item.description || "");
                              }}
                              className="text-xs font-semibold text-zinc-500"
                              title="Ghi chú"
                            >
                              <MessageSquare className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => {
                                setTagsItem(item);
                                setTagsValue(item.tags ? item.tags.join(", ") : "");
                              }}
                              className="text-xs font-semibold text-zinc-500"
                              title="Nhãn"
                            >
                              <Tag className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={(e) => { e.stopPropagation(); handleCreateShortcut(item); }}
                              className="text-xs font-semibold text-zinc-500"
                              title="Tạo lối tắt"
                            >
                              <Link className="w-4 h-4" />
                            </button>
                            {item.is_folder && (
                              <button 
                                onClick={(e) => { e.stopPropagation(); setColorItem(item); setColorValue(item.color || ""); }}
                                className="text-xs font-semibold text-zinc-500"
                                title="Đổi màu"
                              >
                                <Palette className="w-4 h-4" />
                              </button>
                            )}
                            <button 
                              onClick={(e) => { e.stopPropagation(); setDetailsItem(item); }}
                              className="text-xs font-semibold text-zinc-500"
                              title="Chi tiết"
                            >
                              <Info className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                setRenameItem(item);
                                setNewName(item.name);
                              }}
                              className="text-xs font-semibold text-zinc-500"
                              title="Đổi tên"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => {
                                setMoveItem(item);
                                setMoveTargetId(undefined);
                                setMoveBreadcrumbs([{ name: "Kho lưu trữ gốc" }]);
                              }}
                              className="text-xs font-semibold text-zinc-500"
                              title="Di chuyển"
                            >
                              <MoreVertical className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => handleDelete(item)}
                              className="text-xs font-semibold text-black"
                              title="Xóa"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
          {items.map(item => (
            <div key={item._id} className="border border-zinc-200 bg-white p-4 flex flex-col items-center justify-between text-center relative group hover:bg-zinc-50 cursor-pointer" onClick={() => setDetailsItem(item)}>
              <div className="absolute top-2 left-2 z-10">
                <input 
                  type="checkbox" 
                  checked={selectedIds.has(item._id)}
                  onChange={() => toggleSelect(item._id)}
                  onClick={(e) => e.stopPropagation()}
                  className="w-4 h-4 accent-black"
                />
              </div>
              <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                <button onClick={(e) => { e.stopPropagation(); setShareItem(item); }} className="p-1 bg-white border border-zinc-200">
                  <Share2 className="w-3 h-3 text-zinc-600" />
                </button>
                <button onClick={(e) => { e.stopPropagation(); handleToggleStar(item); }} className="p-1 bg-white border border-zinc-200">
                  <Star className={`w-3 h-3 ${item.is_starred ? 'text-black fill-black' : 'text-zinc-600'}`} />
                </button>
                <button onClick={(e) => { e.stopPropagation(); handleDelete(item); }} className="p-1 bg-white border border-zinc-200">
                  <Trash2 className="w-3 h-3 text-zinc-600" />
                </button>
              </div>
              <div className="w-16 h-16 bg-zinc-100 flex flex-col items-center justify-center mb-4 border border-zinc-200 relative">
                {item.color && (
                  <div className="absolute top-0 right-0 w-3 h-3 rounded-full translate-x-1/3 -translate-y-1/3" style={{ backgroundColor: item.color }} />
                )}
                {item.is_shortcut ? <Link className="w-8 h-8 text-blue-500" /> : item.is_folder ? <Folder className="w-8 h-8 text-black" /> : item.mime_type?.startsWith("image/") ? (
                  <img src={item.url} alt={item.name} className="w-full h-full object-cover" />
                ) : <File className="w-8 h-8 text-zinc-500" />}
              </div>
              <div className="w-full">
                {item.is_folder ? (
                  <button onClick={() => handleNavigate(item)} className="text-sm font-semibold block w-full truncate">{item.name}</button>
                ) : item.url ? (
                  <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold block w-full truncate">{item.name}</a>
                ) : (
                  <span className="text-sm font-semibold block w-full truncate">{item.name}</span>
                )}
                <span className="text-xs text-zinc-500">{item.is_folder ? "--" : formatSize(item.size)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
      </div>

      <Modal isOpen={createFolderOpen} onClose={() => setCreateFolderOpen(false)}>
        <ModalHeader>
          <ModalTitle>Tạo thư mục mới</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <input 
            type="text" 
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            placeholder="Tên thư mục"
            className="w-full border border-zinc-200 p-3 text-sm focus:outline-none focus:border-black font-sans"
            autoFocus
          />
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setCreateFolderOpen(false)} className="px-4 py-2 text-sm border border-zinc-200 bg-white">Hủy</button>
          <button onClick={handleCreateFolder} className="px-4 py-2 text-sm border border-black bg-black text-white">Tạo</button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!shareItem} onClose={() => setShareItem(null)}>
        <ModalHeader>
          <ModalTitle>Chia sẻ: {shareItem?.name}</ModalTitle>
        </ModalHeader>
        <ModalContent className="flex flex-col gap-4">
          <div>
            <label className="block text-xs font-semibold mb-2">Chia sẻ qua Email</label>
            <div className="flex flex-col md:flex-row gap-2">
              <input 
                type="email" 
                value={shareEmail}
                onChange={(e) => setShareEmail(e.target.value)}
                placeholder="Nhập email người dùng"
                className="flex-1 border border-zinc-200 p-2 text-sm focus:outline-none focus:border-black font-sans"
              />
              <select 
                value={shareRole}
                onChange={(e) => setShareRole(e.target.value)}
                className="border border-zinc-200 px-4 py-2 text-sm focus:outline-none focus:border-black bg-white"
              >
                <option value="viewer">Chỉ xem</option>
                <option value="editor">Chỉnh sửa</option>
              </select>
            </div>
            <button 
              onClick={handleShareSubmit} 
              className="mt-3 px-4 py-2 w-full text-sm border border-black bg-black text-white font-semibold"
            >
              Chia sẻ
            </button>
          </div>
          <div className="border-t border-zinc-200 pt-4 mt-2">
            <label className="block text-xs font-semibold mb-2">Truy cập công khai (Public Link)</label>
            <button 
              onClick={() => handleTogglePublic(shareItem!)}
              className="flex items-center gap-2 border border-zinc-200 px-4 py-2 text-sm font-semibold w-full bg-zinc-50"
            >
              <Share2 className="w-4 h-4" />
              {shareItem?.is_public ? 'Sao chép liên kết công khai' : 'Tạo liên kết công khai'}
            </button>
          </div>
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setShareItem(null)} className="px-4 py-2 text-sm border border-zinc-200 bg-white">Đóng</button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!renameItem} onClose={() => setRenameItem(null)}>
        <ModalHeader>
          <ModalTitle>Đổi tên</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <input 
            type="text" 
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Tên mới"
            className="w-full border border-zinc-200 p-3 text-sm focus:outline-none focus:border-black font-sans"
            autoFocus
          />
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setRenameItem(null)} className="px-4 py-2 text-sm border border-zinc-200 bg-white">Hủy</button>
          <button onClick={handleRename} className="px-4 py-2 text-sm border border-black bg-black text-white">Lưu</button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!descItem} onClose={() => setDescItem(null)}>
        <ModalHeader>
          <ModalTitle>Ghi chú</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <textarea 
            value={descValue}
            onChange={(e) => setDescValue(e.target.value)}
            placeholder="Nhập ghi chú"
            className="w-full border border-zinc-200 p-3 text-sm focus:outline-none focus:border-black font-sans min-h-[100px]"
            autoFocus
          />
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setDescItem(null)} className="px-4 py-2 text-sm border border-zinc-200 bg-white">Hủy</button>
          <button onClick={handleUpdateDesc} className="px-4 py-2 text-sm border border-black bg-black text-white">Lưu</button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!tagsItem} onClose={() => setTagsItem(null)}>
        <ModalHeader>
          <ModalTitle>Nhãn (Tags)</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <input 
            type="text" 
            value={tagsValue}
            onChange={(e) => setTagsValue(e.target.value)}
            placeholder="tag1, tag2, tag3"
            className="w-full border border-zinc-200 p-3 text-sm focus:outline-none focus:border-black font-sans"
            autoFocus
          />
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setTagsItem(null)} className="px-4 py-2 text-sm border border-zinc-200 bg-white">Hủy</button>
          <button onClick={handleUpdateTags} className="px-4 py-2 text-sm border border-black bg-black text-white">Lưu</button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!moveItem} onClose={() => setMoveItem(null)}>
        <ModalHeader>
          <ModalTitle>Di chuyển: {moveItem?.name}</ModalTitle>
        </ModalHeader>
        <ModalContent className="max-h-[50vh] overflow-y-auto">
          <div className="flex items-center gap-2 text-sm text-zinc-600 mb-4 pb-2 border-b border-zinc-200">
            {moveBreadcrumbs.map((crumb, idx) => (
              <div key={idx} className="flex items-center gap-1">
                <button 
                  onClick={() => {
                    setMoveTargetId(crumb.id);
                    setMoveBreadcrumbs(moveBreadcrumbs.slice(0, idx + 1));
                  }}
                  className={`${idx === moveBreadcrumbs.length - 1 ? 'font-semibold text-black' : 'underline underline-offset-4'}`}
                >
                  {crumb.name}
                </button>
                {idx < moveBreadcrumbs.length - 1 && <ChevronRight className="w-3 h-3" />}
              </div>
            ))}
          </div>
          {moveFolders.length === 0 ? (
            <div className="text-sm text-zinc-500 py-4 text-center">Không có thư mục con nào ở đây</div>
          ) : (
            <div className="flex flex-col gap-2">
              {moveFolders.map(folder => (
                <button
                  key={folder._id}
                  onClick={() => {
                    setMoveTargetId(folder._id);
                    setMoveBreadcrumbs([...moveBreadcrumbs, { id: folder._id, name: folder.name }]);
                  }}
                  className="flex items-center gap-3 p-3 border border-zinc-200 text-left hover:border-black hover:bg-zinc-50 transition-colors"
                >
                  <Folder className="w-4 h-4 text-black" />
                  <span className="text-sm font-medium">{folder.name}</span>
                </button>
              ))}
            </div>
          )}
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setMoveItem(null)} className="px-4 py-2 text-sm border border-zinc-200 bg-white">Hủy</button>
          <button onClick={handleMove} className="px-4 py-2 text-sm border border-black bg-black text-white">Di chuyển đến đây</button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!colorItem} onClose={() => setColorItem(null)}>
        <ModalHeader>
          <ModalTitle>Đổi màu thư mục</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="flex gap-2 flex-wrap">
            {['#000000', '#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#71717a'].map(color => (
              <button
                key={color}
                onClick={() => setColorValue(color)}
                className={`w-8 h-8 rounded-full border-2 ${colorValue === color ? 'border-black' : 'border-transparent'}`}
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
          <button onClick={() => setColorValue("")} className="mt-4 text-xs font-semibold underline">Bỏ màu</button>
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setColorItem(null)} className="px-4 py-2 text-sm border border-zinc-200 bg-white">Hủy</button>
          <button onClick={handleUpdateColor} className="px-4 py-2 text-sm border border-black bg-black text-white">Lưu</button>
        </ModalFooter>
      </Modal>

      </div>
      
      {detailsItem && (
        <div className="w-[320px] bg-zinc-50 border-l border-zinc-200 flex flex-col overflow-y-auto">
          <div className="p-4 border-b border-zinc-200 flex justify-between items-center bg-white sticky top-0">
            <h2 className="font-semibold text-lg flex items-center gap-2">
              <Info className="w-5 h-5" /> Chi tiết
            </h2>
            <button onClick={() => setDetailsItem(null)} className="text-zinc-500 hover:text-black font-semibold">✕</button>
          </div>
          
          <div className="flex border-b border-zinc-200">
            <button 
              className={`flex-1 py-3 text-sm font-semibold border-b-2 ${activeSidebarTab === 'info' ? 'border-black text-black' : 'border-transparent text-zinc-500'}`}
              onClick={() => setActiveSidebarTab('info')}
            >
              Thông tin
            </button>
            <button 
              className={`flex-1 py-3 text-sm font-semibold border-b-2 ${activeSidebarTab === 'ai' ? 'border-black text-black' : 'border-transparent text-zinc-500'}`}
              onClick={() => setActiveSidebarTab('ai')}
            >
              AI Trợ lý
            </button>
          </div>
          
          {activeSidebarTab === 'info' ? (
            <div className="flex flex-col flex-1 overflow-y-auto">
              <div className="p-6 flex flex-col items-center justify-center border-b border-zinc-200 bg-white">
                <div className="w-24 h-24 bg-zinc-100 flex items-center justify-center mb-4 border border-zinc-200">
                  {detailsItem.is_shortcut ? <Link className="w-10 h-10 text-blue-500" /> : detailsItem.is_folder ? <Folder className="w-10 h-10 text-black" /> : detailsItem.mime_type?.startsWith("image/") ? (
                    <img src={detailsItem.url} alt={detailsItem.name} className="w-full h-full object-cover" />
                  ) : <File className="w-10 h-10 text-zinc-500" />}
                </div>
                <h3 className="font-semibold text-center break-all">{detailsItem.name}</h3>
                {detailsItem.is_duplicate && (
                  <span className="mt-2 inline-block px-2 py-1 bg-zinc-100 text-black text-[10px] font-bold uppercase border border-black">
                    Phát hiện trùng lặp
                  </span>
                )}
              </div>

              <div className="p-6 flex flex-col gap-4 text-sm">
                <div className="flex justify-between items-center bg-zinc-50 p-2 border border-zinc-200">
                  <span className="text-xs font-semibold text-zinc-600">Trạng thái AI</span>
                  {detailsItem.ai_processed ? (
                    <span className="text-[10px] bg-black text-white px-2 py-1 uppercase font-semibold">Đã xử lý</span>
                  ) : (
                    <span className="text-[10px] bg-zinc-200 text-zinc-600 px-2 py-1 uppercase font-semibold">Đang chờ</span>
                  )}
                </div>
                <div>
                  <span className="block text-xs font-semibold text-zinc-500 mb-1">Loại</span>
                  <span className="font-mono bg-zinc-200 px-2 py-1 text-xs">
                    {detailsItem.is_folder ? 'Thư mục' : detailsItem.mime_type || 'Tệp tin'}
                  </span>
                </div>
                <div>
                  <span className="block text-xs font-semibold text-zinc-500 mb-1">Kích thước</span>
                  <span>{detailsItem.is_folder ? '--' : formatSize(detailsItem.size)}</span>
                </div>
                <div>
                  <span className="block text-xs font-semibold text-zinc-500 mb-1">Ngày tạo</span>
                  <span>{new Date(detailsItem.created_at).toLocaleString('vi-VN')}</span>
                </div>
                <div>
                  <span className="block text-xs font-semibold text-zinc-500 mb-1">Cập nhật lần cuối</span>
                  <span>{new Date(detailsItem.updated_at).toLocaleString('vi-VN')}</span>
                </div>
                
                {detailsItem.description && (
                  <div>
                    <span className="block text-xs font-semibold text-zinc-500 mb-1">Ghi chú (Tóm tắt AI)</span>
                    <span className="font-mono text-zinc-700 bg-zinc-100 p-2 block border border-zinc-200">
                      {detailsItem.description}
                    </span>
                  </div>
                )}
                
                {detailsItem.environment_ready && (
                  <div>
                    <span className="block text-xs font-semibold text-zinc-500 mb-1">Môi trường biên dịch (AI)</span>
                    <span className="font-mono text-black bg-zinc-100 px-2 py-1 border border-zinc-300 text-xs font-semibold inline-block">
                      SẴN SÀNG
                    </span>
                  </div>
                )}
                
                {detailsItem.tags && detailsItem.tags.length > 0 && (
                  <div>
                    <span className="block text-xs font-semibold text-zinc-500 mb-1">Nhãn (AI đề xuất)</span>
                    <div className="flex gap-2 flex-wrap">
                      {detailsItem.tags.map(t => (
                        <span key={t} className={`text-[10px] px-2 py-1 font-mono border ${t === 'VIOLATION_FLAGGED' ? 'bg-black border-black text-white font-bold' : 'bg-zinc-100 border-zinc-300 text-zinc-600'}`}>
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {detailsItem.entities && (Object.keys(detailsItem.entities).length > 0) && (
                  <div className="border border-zinc-200 bg-zinc-50 p-3 mt-2">
                    <span className="block text-xs font-semibold text-black mb-2 uppercase">Thực thể (AI trích xuất)</span>
                    <div className="flex flex-col gap-2">
                      {detailsItem.entities.people && detailsItem.entities.people.length > 0 && (
                        <div>
                          <span className="text-[10px] text-zinc-500 uppercase font-semibold">Nhân vật / Người: </span>
                          <span className="text-xs font-mono">{detailsItem.entities.people.join(", ")}</span>
                        </div>
                      )}
                      {detailsItem.entities.organizations && detailsItem.entities.organizations.length > 0 && (
                        <div>
                          <span className="text-[10px] text-zinc-500 uppercase font-semibold">Tổ chức: </span>
                          <span className="text-xs font-mono">{detailsItem.entities.organizations.join(", ")}</span>
                        </div>
                      )}
                      {detailsItem.entities.dates && detailsItem.entities.dates.length > 0 && (
                        <div>
                          <span className="text-[10px] text-zinc-500 uppercase font-semibold">Ngày tháng: </span>
                          <span className="text-xs font-mono">{detailsItem.entities.dates.join(", ")}</span>
                        </div>
                      )}
                      {detailsItem.entities.amounts && detailsItem.entities.amounts.length > 0 && (
                        <div>
                          <span className="text-[10px] text-zinc-500 uppercase font-semibold">Số tiền: </span>
                          <span className="text-xs font-mono">{detailsItem.entities.amounts.join(", ")}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {detailsItem.broken_links && detailsItem.broken_links.length > 0 && (
                  <div className="border border-black bg-zinc-100 p-3 mt-2">
                    <span className="block text-xs font-bold text-black mb-2 uppercase">Cảnh báo liên kết hỏng</span>
                    <ul className="list-disc pl-4 text-xs font-mono text-black">
                      {detailsItem.broken_links.map((link, idx) => (
                        <li key={idx}>{link}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {detailsItem.versions && detailsItem.versions.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-zinc-200">
                    <span className="block text-xs font-semibold text-zinc-500 mb-3">Lịch sử phiên bản</span>
                    <div className="flex flex-col gap-3 relative before:content-[''] before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-[2px] before:bg-zinc-200">
                      <div className="flex gap-3 relative z-10">
                        <div className="w-6 h-6 rounded-full bg-black flex-shrink-0 flex items-center justify-center text-white text-[10px] border-2 border-white">
                          {detailsItem.versions.length + 1}
                        </div>
                        <div className="flex flex-col">
                          <span className="font-semibold text-sm">Bản hiện tại</span>
                          <span className="text-xs text-zinc-500">{new Date(detailsItem.updated_at).toLocaleString('vi-VN')}</span>
                          <a href={detailsItem.url} target="_blank" className="text-xs text-blue-500 hover:underline mt-1">Tải xuống</a>
                        </div>
                      </div>
                      {detailsItem.versions.slice().reverse().map((v, i) => (
                        <div key={v.version_id} className="flex gap-3 relative z-10">
                          <div className="w-6 h-6 rounded-full bg-zinc-300 flex-shrink-0 flex items-center justify-center text-white text-[10px] border-2 border-white">
                            {detailsItem.versions!.length - i}
                          </div>
                          <div className="flex flex-col">
                            <span className="font-semibold text-sm text-zinc-600">Bản cũ</span>
                            <span className="text-xs text-zinc-500">{new Date(v.created_at).toLocaleString('vi-VN')}</span>
                            <span className="text-xs text-zinc-500">{formatSize(v.size)}</span>
                            <a href={v.url} target="_blank" className="text-xs text-blue-500 hover:underline mt-1">Tải xuống</a>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {relatedItems.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-zinc-200">
                    <span className="block text-xs font-semibold text-zinc-500 mb-3">Tài liệu liên quan (AI)</span>
                    <div className="flex flex-col gap-2">
                      {relatedItems.map(item => (
                        <div key={item._id} className="p-2 border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 cursor-pointer flex items-center gap-2" onClick={() => setDetailsItem(item)}>
                          <File className="w-4 h-4 text-zinc-400" />
                          <span className="text-xs font-semibold truncate flex-1">{item.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex flex-col flex-1 bg-white">
              <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4 text-sm font-sans">
                {chatHistory.length === 0 ? (
                  <div className="text-zinc-500 text-center italic mt-10">
                    Hỏi tôi bất cứ điều gì về tài liệu "{detailsItem.name}".
                  </div>
                ) : (
                  chatHistory.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`p-3 max-w-[85%] border ${msg.role === 'user' ? 'bg-black text-white border-black' : 'bg-zinc-100 text-black border-zinc-200'}`}>
                        {msg.content}
                      </div>
                    </div>
                  ))
                )}
              </div>
              <div className="p-4 border-t border-zinc-200">
                <form 
                  onSubmit={async (e) => {
                    e.preventDefault();
                    if (!chatInput.trim()) return;
                    const newMsg = { role: 'user', content: chatInput.trim() };
                    setChatHistory(prev => [...prev, newMsg]);
                    setChatInput("");
                    
                    try {
                      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/ai/tro-chuyen`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
                        body: JSON.stringify({ query: newMsg.content, document_id: detailsItem._id })
                      });
                      if (res.ok) {
                        const reader = res.body?.getReader();
                        const decoder = new TextDecoder("utf-8");
                        let botMsg = "";
                        setChatHistory(prev => [...prev, { role: 'bot', content: "" }]);
                        
                        if (reader) {
                          while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;
                            botMsg += decoder.decode(value, { stream: true });
                            setChatHistory(prev => {
                              const next = [...prev];
                              next[next.length - 1].content = botMsg.replace(/data: /g, "").replace(/\n\n/g, "");
                              return next;
                            });
                          }
                        }
                      } else {
                        setChatHistory(prev => [...prev, { role: 'bot', content: "Xin lỗi, hiện tại không thể kết nối tới máy chủ AI." }]);
                      }
                    } catch (e) {
                      setChatHistory(prev => [...prev, { role: 'bot', content: "Đã xảy ra lỗi hệ thống." }]);
                    }
                  }}
                  className="flex gap-2"
                >
                  <input 
                    type="text" 
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Nhập câu hỏi" 
                    className="flex-1 border border-zinc-200 p-2 text-sm focus:outline-none focus:border-black"
                  />
                  <button type="submit" className="bg-black text-white px-3 py-2 text-sm font-semibold border border-black">Gửi</button>
                </form>
                <div className="mt-3 flex gap-2">
                  <button 
                    type="button" 
                    className="flex-1 border border-zinc-200 bg-zinc-50 py-1 text-xs font-semibold text-zinc-600 hover:text-black"
                    onClick={async () => {
                      setChatHistory(prev => [...prev, { role: 'user', content: 'Hãy tạo một bản dịch tài liệu này sang tiếng Việt.' }]);
                      try {
                        const { translateStorageDocumentAPI } = await import('@/services/storage.service');
                        await translateStorageDocumentAPI(detailsItem._id, "vi");
                        setChatHistory(prev => [...prev, { role: 'bot', content: 'Tuyệt vời, tôi đã tạo xong một bản dịch tiếng Việt cho tài liệu này và lưu vào cùng thư mục.' }]);
                        fetchItems(currentFolderId);
                      } catch (err: any) {
                        setChatHistory(prev => [...prev, { role: 'bot', content: 'Xin lỗi, không thể dịch tài liệu lúc này.' }]);
                      }
                    }}
                  >
                    Dịch sang Tiếng Việt
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
