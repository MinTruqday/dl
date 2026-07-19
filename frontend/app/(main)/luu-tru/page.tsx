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
        <StorageSidebar viewMode={viewMode} setViewMode={setViewMode} />
        <main className="flex-1 min-w-0 space-y-8 pt-6">
          <StorageToolbar
            viewMode={viewMode}
            breadcrumbs={breadcrumbs}
            handleNavigateBreadcrumb={handleNavigateBreadcrumb}
            layout={layout}
            setLayout={setLayout}
            handleUploadClick={handleUploadClick}
            handleUploadClickDoc={handleUploadClickDoc}
            setShowNewFolderModal={setShowNewFolderModal}
            handleDeleteEmptyTrash={handleDeleteEmptyTrash}
          />
