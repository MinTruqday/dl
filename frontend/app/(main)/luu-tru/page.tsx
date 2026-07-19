"use client";

import { useEffect, useState, useRef } from "react";
import { getToken as getAuthToken } from "@/features/authentication/services/session.service";
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
  downloadZipAPI,
} from "@/features/cloud/services/storage.service";
import {
  getMyDocumentsAPI,
  deleteAuthorDocumentAPI,
  lockDocumentAPI,
} from "@/features/content/services/document.service";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Folder,
  File,
  FilePlus,
  FolderPlus,
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
  List,
  LayoutGrid,
  RotateCcw,
  Clock,
  Info,
  Link as LinkIcon,
  Palette,
  Archive,
  Home,
  X,
  Lock,
  Unlock,
} from "lucide-react";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";

export default function StoragePage() {
  const { user } = useAuth() as any;
  const { showToast } = useToast();
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [currentFolderId, setCurrentFolderId] = useState<string | undefined>(
    undefined,
  );
  const [breadcrumbs, setBreadcrumbs] = useState<
    { id?: string; name: string }[]
  >([{ name: "Tất cả" }]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [createFolderOpen, setCreateFolderOpen] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [renameItem, setRenameItem] = useState<StorageItem | null>(null);
  const [newName, setNewName] = useState("");
  const [descItem, setDescItem] = useState<StorageItem | null>(null);
  const [descValue, setDescValue] = useState("");
  const [tagsItem, setTagsItem] = useState<any>(null);
  const [tagsValue, setTagsValue] = useState("");
  const [viewMode, setViewMode] = useState<"files" | "trash" | "recent" | "documents" | "folders" | "published">(
    "files",
  );
  const [moveItem, setMoveItem] = useState<any>(null);
  const [moveTargetId, setMoveTargetId] = useState<string | undefined>(
    undefined,
  );
  const [moveBreadcrumbs, setMoveBreadcrumbs] = useState<
    { id?: string; name: string }[]
  >([{ name: "Tất cả" }]);
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
  const [activeSidebarTab, setActiveSidebarTab] = useState<"info" | "ai">(
    "info",
  );
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<
    { role: string; content: string }[]
  >([]);
  const [quota, setQuota] = useState<{ used: number; limit: number } | null>(
    null,
  );
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [detailsItem, setDetailsItem] = useState<any>(null);
  const [relatedItems, setRelatedItems] = useState<any[]>([]);
  const [colorItem, setColorItem] = useState<any>(null);
  const [colorValue, setColorValue] = useState("");
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [hasMorePublished, setHasMorePublished] = useState(true);
  const [publishedCursor, setPublishedCursor] = useState<string | null>(null);

  const fetchQuota = async () => {
    try {
      setQuota(await getStorageQuotaAPI());
    } catch (e) {}
  };
  useEffect(() => {
    fetchQuota();
  }, []);

  const fetchItems = async (
    folderId?: string,
    mode: typeof viewMode = viewMode,
    isLoadMore = false
  ) => {
    if (!isLoadMore) setLoading(true);
    try {
      if (mode === "published") {
        const currentCursor = isLoadMore ? publishedCursor : undefined;
        const res = await getMyDocumentsAPI("", currentCursor || "", 20);
        let docs = res.data || res || [];
        // Map document structure to generic structure so table can render it or handle it separately
        setHasMorePublished(docs.length >= 20);
        if (docs.length > 0) {
          setPublishedCursor(docs[docs.length - 1].id || docs[docs.length - 1]._id);
        }
        if (isLoadMore) {
          setItems((prev) => [...prev, ...docs]);
        } else {
          setItems(docs);
        }
      } else if (mode === "recent") {
        setItems(await getRecentStorageItemsAPI(20));
      } else if (mode === "documents") {
        setItems(await searchStorageItemsAPI("", "file"));
      } else if (mode === "folders") {
        setItems(await searchStorageItemsAPI("", "folder"));
      } else {
        setItems(await listStorageItemsAPI(folderId, mode === "trash"));
      }
    } catch (e: any) {
      showToast(e.message || "Lỗi truy xuất bộ sưu tập lưu trữ", "error");
    } finally {
      setLoading(false);
    }
  };

  const fetchMoveFolders = async (folderId?: string) => {
    try {
      const data = await listStorageItemsAPI(folderId);
      setMoveFolders(
        data.filter((i) => i.is_folder && i._id !== moveItem?._id),
      );
    } catch (e) {}
  };

  useEffect(() => {
    fetchItems(
      viewMode === "trash" || viewMode === "recent" || viewMode === "documents" || viewMode === "folders" || viewMode === "published"
        ? undefined
        : currentFolderId,
      viewMode,
    );
  }, [currentFolderId, viewMode]);

  useEffect(() => {
  }, [detailsItem, activeSidebarTab]);

  useEffect(() => {
    if (moveItem) fetchMoveFolders(moveTargetId);
  }, [moveTargetId, moveItem]);

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;
    try {
      await createFolderAPI(newFolderName.trim(), currentFolderId);
      showToast("Khởi tạo thư mục hoàn tất", "success");
      setCreateFolderOpen(false);
      setNewFolderName("");
      fetchItems(currentFolderId);
    } catch (e: any) {
      showToast(e.message || "Lỗi khởi tạo thư mục", "error");
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files?.length) return;
    setUploading(true);
    try {
      for (let i = 0; i < files.length; i++)
        await uploadStorageFileAPI(files[i], currentFolderId);
      showToast("Tải lên tệp đa phương tiện hoàn tất", "success");
      fetchItems(currentFolderId);
      fetchQuota();
    } catch (e: any) {
      showToast(e.message || "Lỗi truyền tải tệp đa phương tiện", "error");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (viewMode !== "trash" && viewMode !== "recent") setIsDraggingOver(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
  };
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
    if (viewMode === "trash" || viewMode === "recent") return;
    const files = e.dataTransfer.files;
    if (!files?.length) return;
    setUploading(true);
    try {
      for (let i = 0; i < files.length; i++)
        await uploadStorageFileAPI(files[i], currentFolderId);
      showToast("Tải lên tệp đa phương tiện hoàn tất", "success");
      fetchItems(currentFolderId);
      fetchQuota();
    } catch (e: any) {
      showToast(e.message || "Lỗi truyền tải tệp đa phương tiện", "error");
    } finally {
      setUploading(false);
    }
  };

  const handleNavigate = (folder: StorageItem) => {
    if (folder.is_shortcut && folder.target_id) return;
    setCurrentFolderId(folder._id);
    setBreadcrumbs([...breadcrumbs, { id: folder._id, name: folder.name }]);
  };
  const handleNavigateBreadcrumb = (index: number) => {
    setCurrentFolderId(breadcrumbs[index].id);
    setBreadcrumbs(breadcrumbs.slice(0, index + 1));
  };

  const handleDelete = async (item: StorageItem) => {
    try {
      await deleteStorageItemAPI(item._id, viewMode === "trash");
      showToast(
        viewMode === "trash" ? "Xóa vĩnh viễn dữ liệu hoàn tất" : "Chuyển dữ liệu vào thùng rác hoàn tất",
        "success",
      );
      fetchItems(viewMode === "trash" ? undefined : currentFolderId, viewMode);
      if (viewMode === "trash") fetchQuota();
    } catch (e: any) {
      showToast(e.message || "Lỗi thực thi dữ liệu lưu trữ", "error");
    }
  };

  const handleToggleLock = async (item: StorageItem) => {
    try {
      await updateStorageItemAPI(item._id, { is_public: !item.is_public });
      fetchItems(currentFolderId);
      showToast(
        !item.is_public ? "Thiết lập phân quyền công khai hoàn tất" : "Thiết lập phân quyền riêng tư hoàn tất",
        "success",
      );
    } catch (e: any) {
      showToast(e.message || "Lỗi thiết lập phân quyền", "error");
    }
  };

  const handleRestore = async (item: StorageItem) => {
    try {
      await updateStorageItemAPI(item._id, { is_trashed: false });
      showToast("Khôi phục dữ liệu lưu trữ hoàn tất", "success");
      fetchItems(undefined, "trash");
    } catch (e: any) {
      showToast(e.message || "Lỗi khôi phục dữ liệu lưu trữ", "error");
    }
  };
  const handleMove = async () => {
    if (!moveItem) return;
    try {
      await updateStorageItemAPI(moveItem._id, {
        parent_id: (moveTargetId === undefined ? null : moveTargetId) as any,
      });
      showToast("Di chuyển dữ liệu lưu trữ hoàn tất", "success");
      setMoveItem(null);
      setMoveTargetId(undefined);
      setMoveBreadcrumbs([{ id: "root", name: "Tất cả" }]);
      fetchItems(currentFolderId);
    } catch (e: any) {
      showToast(e.message || "Lỗi di chuyển dữ liệu lưu trữ", "error");
    }
  };
  const handleRename = async () => {
    if (!renameItem || !newName.trim()) return;
    try {
      await updateStorageItemAPI(renameItem._id, { name: newName.trim() });
      showToast("Cập nhật định danh dữ liệu hoàn tất", "success");
      setRenameItem(null);
      setNewName("");
      fetchItems(currentFolderId);
    } catch (e: any) {
      showToast(e.message || "Lỗi cập nhật định danh dữ liệu", "error");
    }
  };
  const handleUpdateDesc = async () => {
    if (!descItem) return;
    try {
      await updateStorageItemAPI(descItem._id, {
        description: descValue.trim(),
      });
      showToast("Cập nhật ghi chú dữ liệu hoàn tất", "success");
      setDescItem(null);
      setDescValue("");
      fetchItems(currentFolderId);
    } catch (e: any) {
      showToast(e.message || "Lỗi cập nhật ghi chú dữ liệu", "error");
    }
  };
  const handleUpdateTags = async () => {
    if (!tagsItem) return;
    try {
      await updateStorageItemAPI(tagsItem._id, {
        tags: tagsValue
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      });
      showToast("Cập nhật phân loại nhãn hoàn tất", "success");
      setTagsItem(null);
      setTagsValue("");
      fetchItems(currentFolderId);
    } catch (e: any) {
      showToast(e.message || "Lỗi cập nhật phân loại nhãn", "error");
    }
  };
  const handleUpdateColor = async () => {
    if (!colorItem) return;
    try {
      await updateStorageItemAPI(colorItem._id, { color: colorValue });
      showToast("Cập nhật nhãn màu hoàn tất", "success");
      setColorItem(null);
      fetchItems(currentFolderId);
    } catch (e: any) {
      showToast(e.message || "Lỗi cập nhật nhãn màu", "error");
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
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/ai/smart-search?q=${encodeURIComponent(searchQuery.trim())}`,
          { headers: { Authorization: `Bearer ${getAuthToken()}` } },
        );
        const data = await res.json();
        if (res.ok && data.data && Array.isArray(data.data))
          setItems(data.data);
        else
          setItems(
            await searchStorageItemsAPI(
              searchQuery.trim(),
              searchType || undefined,
            ),
          );
      } else {
        setItems(
          await searchStorageItemsAPI(
            searchQuery.trim(),
            searchType || undefined,
          ),
        );
      }
    } catch (e: any) {
      showToast(e.message || "Lỗi trích xuất bộ sưu tập tìm kiếm", "error");
    } finally {
      setLoading(false);
    }
  };
  const handleCopy = async (item: StorageItem) => {
    try {
      await copyStorageItemAPI(item._id, currentFolderId);
      showToast("Nhân bản dữ liệu lưu trữ hoàn tất", "success");
      fetchItems(currentFolderId);
    } catch (e: any) {
      showToast(e.message || "Lỗi nhân bản dữ liệu lưu trữ", "error");
    }
  };
  const handleCreateShortcut = async (item: StorageItem) => {
    try {
      await createShortcutAPI(item._id, currentFolderId);
      showToast("Khởi tạo liên kết truy cập nhanh hoàn tất", "success");
      fetchItems(currentFolderId);
    } catch (e: any) {
      showToast(e.message || "Lỗi khởi tạo liên kết truy cập nhanh", "error");
    }
  };
  const handleToggleStar = async (item: StorageItem) => {
    try {
      await updateStorageItemAPI(item._id, { is_starred: !item.is_starred });
      fetchItems(currentFolderId);
    } catch (e: any) {
      showToast(e.message || "Lỗi cập nhật trạng thái lưu trữ", "error");
    }
  };
  const handleTogglePublic = async (item: StorageItem) => {
    try {
      if (!item.is_public) {
        await updateStorageItemAPI(item._id, { is_public: true });
        showToast("Kích hoạt phân quyền chia sẻ công khai hoàn tất", "success");
        fetchItems(currentFolderId);
      } else {
        navigator.clipboard.writeText(
          `${window.location.origin}/storage/share/${item.share_token}`,
        );
        showToast("Sao chép liên kết chia sẻ vào bộ nhớ tạm hoàn tất", "success");
      }
    } catch (e: any) {
      showToast(e.message || "Lỗi kích hoạt phân quyền chia sẻ", "error");
    }
  };
  const handleShareSubmit = async () => {
    if (!shareItem || !shareEmail.trim()) return;
    try {
      await shareStorageItemAPI(shareItem._id, shareEmail.trim(), shareRole);
      showToast("Cấp phát quyền chia sẻ dữ liệu hoàn tất", "success");
      setShareItem(null);
      setShareEmail("");
      setShareRole("viewer");
      fetchItems(currentFolderId);
    } catch (e: any) {
      showToast(e.message || "Lỗi cấp phát quyền chia sẻ dữ liệu", "error");
    }
  };
  const handleZipDownload = async () => {
    if (selectedIds.size === 0) return;
    showToast("Khởi tạo tiến trình nén dữ liệu", "success");
    try {
      await downloadZipAPI(Array.from(selectedIds));
      setSelectedIds(new Set());
    } catch (e: any) {
      showToast(e.message || "Lỗi tiến trình nén dữ liệu", "error");
    }
  };
  const toggleSelect = (id: string) => {
    const n = new Set(selectedIds);
    if (n.has(id)) n.delete(id);
    else n.add(id);
    setSelectedIds(n);
  };
  const handleUploadVersion = async (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const files = e.target.files;
    if (!files?.length || !versionItem) return;
    setUploading(true);
    try {
      await uploadFileVersionAPI(versionItem._id, files[0]);
      showToast("Cập nhật phiên bản dữ liệu hoàn tất", "success");
      setVersionItem(null);
      fetchItems(currentFolderId);
    } catch (e: any) {
      showToast(e.message || "Lỗi cập nhật phiên bản dữ liệu", "error");
    } finally {
      setUploading(false);
      if (versionInputRef.current) versionInputRef.current.value = "";
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 B";
    if (!bytes) return "--";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  return (
    <div className="w-full h-full font-sans text-[#1D1D1F]">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleUpload}
        className="hidden"
        multiple
      />
      <input
        type="file"
        ref={versionInputRef}
        onChange={handleUploadVersion}
        className="hidden"
      />
      <div className="flex flex-col md:flex-row">
        <aside className="w-full md:w-[240px] shrink-0 space-y-6 sticky top-0 h-fit mb-6 md:mb-0 md:mr-6">

          <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0 md:pt-6">
            <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
              Phân loại
            </p>
            <nav className="flex flex-col gap-1.5">
              <button
                onClick={() => setViewMode("files")}
                className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${viewMode === "files" ? "bg-white text-[#0071E3] font-medium" : "text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}
              >
                <span className="truncate text-left">Tất cả</span>
                {viewMode === "files" && <ChevronRight className="w-4 h-4 shrink-0" />}
              </button>
              <button
                onClick={() => setViewMode("recent")}
                className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${viewMode === "recent" ? "bg-white text-[#0071E3] font-medium" : "text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}
              >
                <span className="truncate text-left">Gần đây</span>
                {viewMode === "recent" && <ChevronRight className="w-4 h-4 shrink-0" />}
              </button>
              <button
                onClick={() => setViewMode("documents")}
                className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${viewMode === "documents" ? "bg-white text-[#0071E3] font-medium" : "text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}
              >
                <span className="truncate text-left">Tệp tin</span>
                {viewMode === "documents" && <ChevronRight className="w-4 h-4 shrink-0" />}
              </button>
              <button
                onClick={() => setViewMode("published")}
                className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${viewMode === "published" ? "bg-white text-[#0071E3] font-medium" : "text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}
              >
                <span className="truncate text-left">Tài liệu</span>
                {viewMode === "published" && <ChevronRight className="w-4 h-4 shrink-0" />}
              </button>
              <button
                onClick={() => setViewMode("folders")}
                className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${viewMode === "folders" ? "bg-white text-[#0071E3] font-medium" : "text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}
              >
                <span className="truncate text-left">Thư mục</span>
                {viewMode === "folders" && <ChevronRight className="w-4 h-4 shrink-0" />}
              </button>
              <button
                onClick={() => setViewMode("trash")}
                className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${viewMode === "trash" ? "bg-white text-[#0071E3] font-medium" : "text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}
              >
                <span className="truncate text-left">Thùng rác</span>
                {viewMode === "trash" && <ChevronRight className="w-4 h-4 shrink-0" />}
              </button>
            </nav>
          </div>

          {quota && (
            <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0 md:pt-6 space-y-2">
              <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
                Dung lượng
              </p>
              <div className="flex flex-col">
                <span className="text-[13px] font-medium text-[#6E6E73] mb-1">
                  {formatSize(quota.used)} / {formatSize(quota.limit)}
                </span>
                <div className="w-full h-1.5 bg-[#E8E8ED] rounded-full mt-1 overflow-hidden">
                  <div
                    className="h-full bg-[#0071E3] rounded-full"
                    style={{
                      width: `${Math.min(100, (quota.used / quota.limit) * 100)}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          )}
        </aside>

        <main className="flex-1 min-w-0 space-y-8 pt-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <h2 className="flex items-center gap-2 text-[20px] font-semibold text-[#1D1D1F]">
              {viewMode === "trash" ? (
                <span>Thùng rác</span>
              ) : viewMode === "recent" ? (
                <span>Mở gần đây</span>
              ) : viewMode === "documents" ? (
                <span>Tệp tin</span>
              ) : viewMode === "published" ? (
                <span>Tài liệu</span>
              ) : viewMode === "folders" ? (
                <span>Thư mục</span>
              ) : (
                breadcrumbs.map((crumb, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <button
                      onClick={() => handleNavigateBreadcrumb(idx)}
                      className={`flex items-center gap-1 transition-colors ${idx === breadcrumbs.length - 1 ? "text-[#1D1D1F]" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
                    >
                      {crumb.name}
                    </button>
                    {idx < breadcrumbs.length - 1 && (
                      <ChevronRight className="w-5 h-5 text-[#A1A1A6]" />
                    )}
                  </div>
                ))
              )}
            </h2>
            {["files", "documents", "folders"].includes(viewMode) && (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  {["files", "folders"].includes(viewMode) && (
                    <button
                      onClick={() => setCreateFolderOpen(true)}
                      className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
                      title="Thêm thư mục mới"
                    >
                      <FolderPlus className="w-4 h-4" />
                    </button>
                  )}
                  {["files", "documents"].includes(viewMode) && (
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading}
                      className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors disabled:opacity-50"
                      title="Tải tệp lên"
                    >
                      {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FilePlus className="w-4 h-4" />}
                    </button>
                  )}
                </div>
                {selectedIds.size > 0 && (
                  <button
                    onClick={handleZipDownload}
                    className="px-4 py-2 rounded-full text-[13px] font-medium bg-[#E8E8ED] text-[#1D1D1F] hover:bg-[#D2D2D7] transition-colors flex items-center gap-2"
                  >
                    <Archive className="w-4 h-4" /> ZIP ({selectedIds.size})
                  </button>
                )}
              </div>
            )}
          </div>

          {viewMode === "trash" && (
            <div className="bg-[#F5F5F7] text-[#6E6E73] text-[13px] p-3 rounded-[12px] flex items-center justify-center mb-4">
              <Info className="w-4 h-4 mr-2" /> Các mục trong Thùng rác sẽ bị xóa vĩnh viễn sau 30 ngày.
            </div>
          )}

          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`w-full overflow-x-auto min-h-[400px] transition-colors ${isDraggingOver ? "border border-[#0071E3] bg-[#F5F5F7]/80 rounded-[18px]" : ""}`}
          >
            {loading ? (
              <div className="flex justify-center items-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" />
              </div>
            ) : (
                <table className="w-full text-left border-collapse">
                  <thead>
                  <tr className="text-[13px] text-[#6E6E73] border-b border-[#E8E8ED]">
                    <th className="py-3 px-6 font-medium w-12 text-center"></th>
                    <th className="py-3 px-6 font-medium text-left">Tên</th>
                    {viewMode === "published" ? (
                      <>
                        <th className="py-3 px-6 font-medium text-center hidden md:table-cell">Thể loại</th>
                        <th className="py-3 px-6 font-medium text-center hidden md:table-cell">Giá bán</th>
                      </>
                    ) : (
                      <>
                        <th className="py-3 px-6 font-medium text-center hidden md:table-cell">Loại</th>
                        <th className="py-3 px-6 font-medium text-center hidden md:table-cell">Kích thước</th>
                      </>
                    )}
                    <th className="py-3 px-6 font-medium text-center hidden md:table-cell">Cập nhật</th>
                    <th className="py-3 px-6 font-medium text-center hidden md:table-cell">
                      {viewMode === "published" ? "Trạng thái" : "Bảo mật"}
                    </th>
                    <th className="py-3 px-6 font-medium text-right">
                      Thao tác
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 ? (
                    <tr>
                      <td
                        colSpan={7}
                      >
                        <div className="py-24 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] w-full text-center my-4">
                          <p className="text-[17px] text-[#6E6E73]">Chưa có dữ liệu</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    items.map((item) => (
                      <tr
                        key={item._id}
                        onClick={() => setDetailsItem(item)}
                        className="hover:bg-[#E8E8ED]/60 transition-colors cursor-pointer group"
                      >
                        <td
                          className="py-3 px-6 text-center"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            type="checkbox"
                            checked={selectedIds.has(item._id)}
                            onChange={() => toggleSelect(item._id)}
                            className="w-4 h-4 rounded-[4px] border-[#C7C7CC] accent-[#0071E3]"
                          />
                        </td>
                        <td className="py-3 px-6 max-w-[300px]">
                          <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2 flex-1 min-w-0">
                              {item.is_starred && (
                                <Star className="w-4 h-4 text-[#FF9500] fill-[#FF9500] shrink-0" />
                              )}
                              {item.is_folder ? (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleNavigate(item);
                                  }}
                                  className="text-[14px] font-medium text-[#1D1D1F] hover:text-[#0071E3] truncate"
                                >
                                  {item.name || item.title}
                                </button>
                              ) : viewMode === "published" ? (
                                <a
                                  href={`/tai-lieu/xem-truoc/${item._id || item.id}`}
                                  onClick={(e) => e.stopPropagation()}
                                  target="_blank"
                                  className="text-[14px] font-medium text-[#1D1D1F] hover:text-[#0071E3] truncate"
                                >
                                  {item.name || item.title}
                                </a>
                              ) : (item.name || item.title)?.endsWith('.doclib') ? (
                                <a
                                  href={`/soan-thao?tai-lieu=${item._id || item.id}`}
                                  onClick={(e) => e.stopPropagation()}
                                  target="_blank"
                                  className="text-[14px] font-medium text-[#1D1D1F] hover:text-[#0071E3] truncate"
                                >
                                  {item.name || item.title}
                                </a>
                              ) : item.url ? (
                                <a
                                  href={`/tai-lieu/xem-truoc/${item._id || item.id}?url=${encodeURIComponent(item.url)}&name=${encodeURIComponent(item.name || item.title || "")}`}
                                  target="_blank"
                                  className="text-[14px] font-medium text-[#1D1D1F] hover:text-[#0071E3] truncate"
                                >
                                  {item.name || item.title}
                                </a>
                              ) : (
                                <span className="text-[14px] font-medium text-[#1D1D1F] truncate">
                                  {item.name || item.title}
                                </span>
                              )}
                              {item.versions && item.versions.length > 0 && (
                                <span className="text-[10px] font-medium bg-[#E8E8ED] text-[#6E6E73] px-2 py-0.5 rounded-full shrink-0">
                                  v{item.versions.length + 1}
                                </span>
                              )}
                            </div>
                          </div>
                        </td>
                        {viewMode === "published" ? (
                          <>
                            <td className="py-3 px-6 text-[13px] text-[#6E6E73] text-center hidden md:table-cell">
                              {item.category || "Chưa phân loại"}
                            </td>
                            <td className="py-3 px-6 text-[13px] text-[#6E6E73] text-center hidden md:table-cell font-mono">
                              {item.price_dl || 0} dl
                            </td>
                          </>
                        ) : (
                          <>
                            <td className="py-3 px-6 text-[13px] text-[#6E6E73] text-center hidden md:table-cell">
                              {item.is_folder ? "Thư mục" : "Tài liệu"}
                            </td>
                            <td className="py-3 px-6 text-[13px] text-[#6E6E73] text-center hidden md:table-cell">
                              {item.is_folder ? "--" : formatSize(item.size)}
                            </td>
                          </>
                        )}
                        <td className="py-3 px-6 text-[13px] text-[#6E6E73] text-center hidden md:table-cell">
                          {new Date(item.updated_at || item.created_at || Date.now()).toLocaleDateString(
                            "vi-VN",
                          )}
                        </td>
                        {viewMode === "published" ? (
                          <td className="py-3 px-6 text-[13px] text-center hidden md:table-cell">
                            <span
                              className={`px-2 py-1 rounded-full font-medium ${
                                item.status === "published"
                                  ? "bg-[#34C759]/10 text-[#34C759]"
                                  : "bg-[#FF9F0A]/10 text-[#FF9F0A]"
                              }`}
                            >
                              {item.status === "published" ? "Đã đăng" : "Bản nháp"}
                            </span>
                          </td>
                        ) : (
                          <td 
                            className="py-3 px-6 text-[13px] text-center hidden md:table-cell"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <select
                              value={item.is_public ? "public" : "private"}
                              onChange={(e) => {
                                if ((e.target.value === "public") !== item.is_public) {
                                  handleToggleLock(item);
                                }
                              }}
                              className="bg-transparent text-[#6E6E73] font-medium outline-none cursor-pointer text-center appearance-none"
                            >
                              <option value="public">Công khai</option>
                              <option value="private">Riêng tư</option>
                            </select>
                          </td>
                        )}
                        <td className="py-3 px-6 text-right">
                          <div className="flex justify-end gap-1 transition-opacity">
                            {viewMode === "trash" ? (
                              <div className="relative">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setOpenMenuId(openMenuId === item._id ? null : item._id);
                                  }}
                                  className="p-1.5 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[8px]"
                                >
                                  <MoreVertical className="w-4 h-4" />
                                </button>
                                
                                {openMenuId === item._id && (
                                  <>
                                    <div className="fixed inset-0 z-40" onClick={(e) => { e.stopPropagation(); setOpenMenuId(null); }} />
                                    <div 
                                      className="absolute right-0 top-full mt-1 w-48 bg-white rounded-[12px] shadow-[0_4px_24px_rgba(0,0,0,0.1)] border border-[#E8E8ED] py-2 z-50 flex flex-col"
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleRestore(item);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#0071E3] hover:bg-[#0071E3]/10 text-left"
                                      >
                                        <RotateCcw className="w-4 h-4" /> Khôi phục
                                      </button>
                                      <div className="h-[1px] bg-[#E8E8ED] my-1" />
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleDelete(item);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#FF3B30] hover:bg-[#FF3B30]/10 text-left"
                                      >
                                        <Trash2 className="w-4 h-4" /> Xóa vĩnh viễn
                                      </button>
                                    </div>
                                  </>
                                )}
                              </div>
                            ) : (
                              <div className="relative">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setOpenMenuId(openMenuId === item._id ? null : item._id);
                                  }}
                                  className="p-1.5 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-[8px]"
                                >
                                  <MoreVertical className="w-4 h-4" />
                                </button>
                                
                                {openMenuId === item._id && (
                                  <>
                                    <div className="fixed inset-0 z-40" onClick={(e) => { e.stopPropagation(); setOpenMenuId(null); }} />
                                    <div 
                                      className="absolute right-0 top-full mt-1 w-48 bg-white rounded-[12px] shadow-[0_4px_24px_rgba(0,0,0,0.1)] border border-[#E8E8ED] py-2 z-50 flex flex-col"
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      {viewMode === "published" ? (
                                        <>
                                          <button
                                            onClick={async (e) => {
                                              e.stopPropagation();
                                              try {
                                                await lockDocumentAPI(item._id || item.id);
                                                showToast("Cập nhật trạng thái bảo mật hoàn tất", "success");
                                                fetchItems(undefined, "published");
                                              } catch (err: any) {
                                                showToast(err.message || "Lỗi cập nhật trạng thái bảo mật", "error");
                                              }
                                              setOpenMenuId(null);
                                            }}
                                            className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                          >
                                            {item.is_protected ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                                            {item.is_protected ? "Mở khoá" : "Khóa bảo vệ"}
                                          </button>
                                          <div className="h-[1px] bg-[#E8E8ED] my-1" />
                                          <button
                                            onClick={async (e) => {
                                              e.stopPropagation();
                                              try {
                                                await deleteAuthorDocumentAPI(item._id || item.id);
                                                showToast("Xóa dữ liệu tác phẩm hoàn tất", "success");
                                                fetchItems(undefined, "published");
                                              } catch (err: any) {
                                                showToast(err.message || "Lỗi xóa dữ liệu tác phẩm", "error");
                                              }
                                              setOpenMenuId(null);
                                            }}
                                            className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#FF3B30] hover:bg-[#FF3B30]/10 text-left"
                                          >
                                            <Trash2 className="w-4 h-4" /> Xóa tác phẩm
                                          </button>
                                        </>
                                      ) : (
                                        <>
                                          <button
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handleToggleStar(item);
                                              setOpenMenuId(null);
                                            }}
                                            className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                          >
                                            <Star className={`w-4 h-4 ${item.is_starred ? "text-[#FF9500] fill-[#FF9500]" : ""}`} />
                                            {item.is_starred ? "Bỏ gắn sao" : "Gắn sao"}
                                          </button>
                                          <button
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handleToggleLock(item);
                                              setOpenMenuId(null);
                                            }}
                                            className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                          >
                                            {item.is_public ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                                            {item.is_public ? "Khóa" : "Mở khóa"}
                                          </button>
                                      <button
                                        onClick={() => {
                                          setShareItem(item);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                      >
                                        <Share2 className="w-4 h-4" /> Chia sẻ
                                      </button>
                                      {!item.is_folder && (
                                        <button
                                          onClick={() => {
                                            setVersionItem(item);
                                            versionInputRef.current?.click();
                                            setOpenMenuId(null);
                                          }}
                                          className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                        >
                                          <History className="w-4 h-4" /> Cập nhật bản mới
                                        </button>
                                      )}
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setRenameItem(item);
                                          setNewName(item.name);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                      >
                                        <Edit2 className="w-4 h-4" /> Đổi tên
                                      </button>
                                      <button
                                        onClick={() => {
                                          setMoveItem(item);
                                          setMoveTargetId(undefined);
                                          setMoveBreadcrumbs([{ name: "Tất cả" }]);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7] text-left"
                                      >
                                        <Archive className="w-4 h-4" /> Di chuyển
                                      </button>
                                      <div className="h-[1px] bg-[#E8E8ED] my-1" />
                                      <button
                                        onClick={() => {
                                          handleDelete(item);
                                          setOpenMenuId(null);
                                        }}
                                        className="flex items-center gap-3 px-4 py-2 text-[14px] text-[#FF3B30] hover:bg-[#FF3B30]/10 text-left"
                                      >
                                        <Trash2 className="w-4 h-4" /> Xóa
                                      </button>
                                    </>
                                  )}
                                </div>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}
            {viewMode === "published" && hasMorePublished && (
              <div className="flex justify-center mt-6">
                <button
                  onClick={() => fetchItems(undefined, "published", true)}
                  disabled={loading}
                  className="px-6 py-2 bg-[#0071E3] text-white rounded-full text-[14px] font-medium hover:bg-[#0077ED] transition-colors disabled:opacity-50"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "Tải thêm"}
                </button>
              </div>
            )}
          </div>
        </main>

        <div
          className={`shrink-0 transition-all duration-300 ease-in-out ${
            detailsItem
              ? "w-full md:w-[320px] opacity-100 md:ml-6 mt-6 md:mt-0"
              : "w-0 opacity-0 overflow-hidden"
          }`}
        >
          <aside className="w-full h-full min-h-0 bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] flex flex-col gap-6 overflow-hidden relative">
            <div className="p-6 flex justify-between items-center bg-white sticky top-0 z-10">
              <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-4">
                Chi tiết
              </h2>
              <button
                onClick={() => setDetailsItem(null)}
                className="w-8 h-8 flex items-center justify-center bg-[#F5F5F7] rounded-full text-[#6E6E73] hover:text-[#1D1D1F]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto no-scrollbar p-6 space-y-6 w-full md:w-[320px]">
                <div className="flex flex-col items-center">
                  <div className="w-24 h-24 bg-[#F5F5F7] flex items-center justify-center rounded-[20px] mb-4">
                    {detailsItem?.is_folder ? (
                      <Folder className="w-12 h-12 text-[#1D1D1F]" />
                    ) : (
                      <File className="w-12 h-12 text-[#6E6E73]" />
                    )}
                  </div>
                  <p className="text-[13px] font-medium text-[#6E6E73] mb-4 text-center max-w-full break-words">
                    {detailsItem?.name || detailsItem?.title}
                  </p>
                </div>
                <div className="bg-[#F5F5F7] rounded-[18px] p-5 space-y-3">
                  <div className="flex justify-between items-center text-[14px]">
                    <span className="text-[#6E6E73]">Loại</span>
                    <span className="font-medium">
                      {viewMode === "published"
                        ? "Tác phẩm"
                        : detailsItem?.is_folder
                        ? "Thư mục"
                        : detailsItem?.mime_type || "Tệp tin"}
                    </span>
                  </div>
                  {viewMode === "published" ? (
                    <>
                      <div className="flex justify-between items-center text-[14px]">
                        <span className="text-[#6E6E73]">Thể loại</span>
                        <span className="font-medium">
                          {detailsItem?.category || "Chưa phân loại"}
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-[14px]">
                        <span className="text-[#6E6E73]">Giá bán</span>
                        <span className="font-medium font-mono">
                          {detailsItem?.price_dl || 0} dl
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-[14px]">
                        <span className="text-[#6E6E73]">Trạng thái</span>
                        <span className={`font-medium ${detailsItem?.status === "published" ? "text-[#34C759]" : "text-[#FF9F0A]"}`}>
                          {detailsItem?.status === "published" ? "Đã đăng" : "Bản nháp"}
                        </span>
                      </div>
                    </>
                  ) : (
                    <div className="flex justify-between items-center text-[14px]">
                      <span className="text-[#6E6E73]">Kích thước</span>
                      <span className="font-medium">
                        {detailsItem?.is_folder
                          ? "--"
                          : formatSize(detailsItem?.size || 0)}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between items-center text-[14px]">
                    <span className="text-[#6E6E73]">Tạo lúc</span>
                    <span className="font-medium">
                      {(detailsItem?.created_at || detailsItem?.updated_at) && new Date(detailsItem.created_at || detailsItem.updated_at).toLocaleDateString(
                        "vi-VN",
                      )}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-[14px]">
                    <span className="text-[#6E6E73]">Sửa đổi</span>
                    <span className="font-medium">
                      {detailsItem?.updated_at && new Date(detailsItem.updated_at).toLocaleDateString(
                        "vi-VN",
                      )}
                    </span>
                  </div>
                </div>
                {detailsItem?.description && (
                  <div>
                    <h4 className="text-[14px] font-medium text-[#6E6E73] mb-2">
                      Ghi chú AI
                    </h4>
                    <div className="bg-[#F5F5F7] rounded-[10px] p-4 text-[14px] leading-relaxed">
                      {detailsItem.description}
                    </div>
                  </div>
                )}
                {detailsItem?.tags && detailsItem.tags.length > 0 && (
                  <div>
                    <h4 className="text-[14px] font-medium text-[#6E6E73] mb-2">
                      Nhãn
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {detailsItem.tags.map((t) => (
                        <span
                          key={t}
                          className="px-3 py-1 bg-[#E8E8ED] text-[#1D1D1F] text-[12px] font-medium rounded-full"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
          </aside>
        </div>
      </div>

      <Modal
        isOpen={createFolderOpen}
        onClose={() => setCreateFolderOpen(false)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle>
            Tạo thư mục mới
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <input
            type="text"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            placeholder=""
            className="apple-input w-full bg-white"
            autoFocus
          />
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setCreateFolderOpen(false)}
            className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full"
          >
            Hủy
          </button>
          <button onClick={handleCreateFolder} className="pill-button">
            Tạo
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!renameItem}
        onClose={() => setRenameItem(null)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle>Đổi tên</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder=""
            className="apple-input w-full bg-white"
            autoFocus
          />
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setRenameItem(null)}
            className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full"
          >
            Hủy
          </button>
          <button onClick={handleRename} className="pill-button">
            Lưu
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!shareItem}
        onClose={() => setShareItem(null)}
      >
        <ModalHeader>
          <ModalTitle>
            Chia sẻ {shareItem?.name}
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div>
            <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
              Mời người dùng
            </label>
            <div className="flex gap-2">
              <input
                type="email"
                value={shareEmail}
                onChange={(e) => setShareEmail(e.target.value)}
                placeholder=""
                className="apple-input flex-1 bg-white"
              />
              <select
                value={shareRole}
                onChange={(e) => setShareRole(e.target.value)}
                className="apple-input w-28 bg-white"
              >
                <option value="viewer">Xem</option>
                <option value="editor">Sửa</option>
              </select>
            </div>
            <button
              onClick={handleShareSubmit}
              className="mt-3 w-full pill-button"
            >
              Chia sẻ ngay
            </button>
          </div>
          <div className="pt-4">
            <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
              Liên kết công khai
            </label>
            <button
              onClick={() => handleTogglePublic(shareItem!)}
              className="w-full py-3 bg-white rounded-[10px] text-[14px] font-medium text-[#1D1D1F]  flex items-center justify-center gap-2"
            >
              <Share2 className="w-4 h-4" />
              {shareItem?.is_public
                ? "Sao chép link public"
                : "Tạo link public"}
            </button>
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setShareItem(null)}
            className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full"
          >
            Đóng
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!moveItem}
        onClose={() => setMoveItem(null)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle>
            Chuyển đến
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="max-h-[300px] overflow-y-auto no-scrollbar">
          <div className="flex gap-1 text-[13px] text-[#0071E3] mb-4 overflow-x-auto no-scrollbar whitespace-nowrap">
            {moveBreadcrumbs.map((c, i) => (
              <button
                key={i}
                onClick={() => {
                  setMoveTargetId(c.id);
                  setMoveBreadcrumbs(moveBreadcrumbs.slice(0, i + 1));
                }}
                className="hover:underline"
              >
                {c.name}
                {i < moveBreadcrumbs.length - 1 && " / "}
              </button>
            ))}
          </div>
          <div className="space-y-2">
            {moveFolders.map((f) => (
              <button
                key={f._id}
                onClick={() => {
                  setMoveTargetId(f._id);
                  setMoveBreadcrumbs([
                    ...moveBreadcrumbs,
                    { id: f._id, name: f.name },
                  ]);
                }}
                className="w-full flex items-center gap-3 p-3 bg-white rounded-[10px] hover:bg-[#E8E8ED] transition-colors"
              >
                <Folder className="w-5 h-5 text-[#1D1D1F]" />
                <span className="text-[14px] font-medium truncate">
                  {f.name}
                </span>
              </button>
            ))}
            {moveFolders.length === 0 && (
              <p className="text-center text-[#6E6E73] text-[13px]">
                Không có thư mục con
              </p>
            )}
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setMoveItem(null)}
            className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full"
          >
            Hủy
          </button>
          <button onClick={handleMove} className="pill-button">
            Chuyển tới đây
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
