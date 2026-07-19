"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  getDocumentsAPI,
  getMyDocumentsAPI,
  createDocumentAPI,
  updateDocumentAPI,
  deleteAuthorDocumentAPI,
  deleteAdminDocumentAPI,
  getFoldersAPI,
  createFolderAPI,
  deleteFolderAPI,
  lockDocumentAPI,
  toggleStarDocumentAPI,
} from "@/features/content/services/document.service";
import { uploadDocumentAPI } from "@/features/cloud/services/upload.service";
import { QRCodeSVG } from "qrcode.react";
import {
  AlertTriangle,
  FileText,
  Eye,
  Trash2,
  RefreshCcw,
  Loader2,
  X,
  Search,
  Upload,
  FileCheck,
  Plus,
  ChevronRight,
  Database,
  Lock,
  Share2,
  Globe,
  QrCode,
  FolderPlus,
  Folder,
  LayoutGrid,
  List,
  Star,
  Home,
} from "lucide-react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
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

  const [confirmModal, setConfirmModal] = useState<{
    show: boolean;
    title: string;
    docId: string;
    type: "doc" | "folder";
  } | null>(null);
  const [createDocModal, setCreateDocModal] = useState(false);
  const [createFolderModal, setCreateFolderModal] = useState(false);
  const [lockModal, setLockModal] = useState<{
    show: boolean;
    docId: string;
  } | null>(null);
  const [shareModal, setShareModal] = useState<{
    show: boolean;
    docId: string;
  } | null>(null);

  const [newDoc, setNewDoc] = useState({
    title: "",
    description: "",
    slug: "",
    category: "Chưa phân loại",
    pages_count: 0,
    publisher_name: "",
    price_dl: 0,
    visibility: "public",
    status: "published",
    publish_at: "",
    is_featured: false,
    is_protected: false,
  });
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
  const [isDraggingOver, setIsDraggingOver] = useState(false);

  const fetchData = useCallback(
    async (isLoadMore = false) => {
      if (isRefreshing || (!hasMore && isLoadMore)) return;
      setIsRefreshing(true);
      try {
        const currentCursor = isLoadMore ? cursor : undefined;
        const [docsData, foldersData] = await Promise.all([
          isAdmin
            ? getDocumentsAPI(
                searchQuery,
                undefined,
                undefined,
                undefined,
                currentFolder?._id,
                filterStar,
                filterFormat,
                undefined,
                currentCursor || "",
                20,
              )
            : getMyDocumentsAPI(searchQuery, currentCursor || "", 20),
          !isLoadMore ? getFoldersAPI(currentFolder?._id) : Promise.resolve([]),
        ]);
        let docs = docsData.data || docsData || [];
        
        // Always filter on the frontend because the API does not support folder_id filtering
        if (currentFolder) {
          const folderId = currentFolder._id || currentFolder.id;
          docs = docs.filter((d: any) => (d.folder_id || d.folder) === folderId);
        } else {
          docs = docs.filter((d: any) => !d.folder_id && !d.folder);
        }
        if (filterStar) docs = docs.filter((d: any) => d.is_starred);
        if (filterFormat !== "all")
          docs = docs.filter((d: any) =>
            d.file_url?.toLowerCase().endsWith(filterFormat),
          );
        if (searchQuery)
          docs = docs.filter(
            (d: any) =>
              d.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
              (d.publisher_name || "")
                .toLowerCase()
                .includes(searchQuery.toLowerCase()),
          );
          
        setHasMore(docs.length >= 20);
        if (docs.length > 0)
          setCursor(docs[docs.length - 1].id || docs[docs.length - 1]._id);
        setDocuments((prev) => (isLoadMore ? [...prev, ...docs] : docs));
        if (!isLoadMore) setFolders(foldersData.data || foldersData || []);
      } catch (err: any) {
        showToast("Lỗi trích xuất danh sách tài liệu từ hệ thống", "error");
      } finally {
        setIsRefreshing(false);
        setIsLoading(false);
      }
    },
    [
      isAdmin,
      searchQuery,
      currentFolder,
      filterStar,
      filterFormat,
      cursor,
      hasMore,
      showToast,
      isRefreshing,
    ],
  );

  useEffect(() => {
    if (!authLoading && user) {
      fetchData();
      setNewDoc((p) => ({
        ...p,
        publisher_name: isAdmin ? "DocLib" : user.full_name || "",
      }));
    }
  }, [user, authLoading, isAdmin, currentFolder, filterStar, filterFormat]);
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isRefreshing)
          fetchData(true);
      },
      { threshold: 0.5 },
    );
    if (observerTarget.current) observer.observe(observerTarget.current);
    return () => observer.disconnect();
  }, [hasMore, isRefreshing, fetchData]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (!newDoc.title) {
        const name = selectedFile.name.split(".")[0];
        setNewDoc((p) => ({
          ...p,
          title: name,
          slug: name
            .toLowerCase()
            .replace(/\s+/g, "-")
            .replace(/[^a-z0-9-]/g, ""),
        }));
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(true);
  };
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selectedFile = e.dataTransfer.files[0];
      setFile(selectedFile);
      const name = selectedFile.name.split(".")[0];
      setNewDoc((p) => ({
        ...p,
        title: p.title || name,
        slug: p.slug || name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, ""),
      }));
      setCreateDocModal(true);
    }
  };

  const handleCreateDocument = async () => {
    if (!newDoc.title || !file) {
      showToast("Thông tin khởi tạo tài liệu không hợp lệ", "error");
      return;
    }
    setIsCreating(true);
    try {
      let ext = file.name.split(".").pop()?.toLowerCase() || "json";
      if (ext === "md") ext = "markdown";
      else if (ext === "tex") ext = "latex";

      const submissionData = {
        ...newDoc,
        file_url: "",
        content_format: ext,
        folder_id: currentFolder?._id || currentFolder?.id || null,
        slug:
          newDoc.slug ||
          newDoc.title.toLowerCase().replace(/\s+/g, "-") +
            "-" +
            Date.now().toString().slice(-4),
        publish_at: newDoc.status === "scheduled" ? newDoc.publish_at : null,
      };
      const createdDoc = await createDocumentAPI(submissionData);
      try {
        const uploadRes = await uploadDocumentAPI(file);
        await updateDocumentAPI(createdDoc.data._id || createdDoc.data.id, {
          file_url: uploadRes.data.url,
          content_format:
            uploadRes.data.extension || submissionData.content_format,
        });
      } catch (uploadErr) {
        await deleteAuthorDocumentAPI(
          createdDoc.data._id || createdDoc.data.id,
        ).catch(() => {});
        throw new Error("Lỗi truyền tải tệp tin lên hệ thống lưu trữ đám mây");
      }
      showToast("Khởi tạo tài liệu mới hoàn tất", "success");
      setCreateDocModal(false);
      setNewDoc({
        title: "",
        description: "",
        slug: "",
        category: "Chưa phân loại",
        pages_count: 0,
        publisher_name: isAdmin ? "DocLib" : user?.full_name || "",
        price_dl: 0,
        visibility: "public",
        status: "published",
        publish_at: "",
        is_featured: false,
        is_protected: false,
      });
      setFile(null);
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Lỗi thực thi nghiệp vụ tài liệu", "error");
    } finally {
      setIsCreating(false);
    }
  };

  const handleCreateFolder = async () => {
    if (!folderName) return;
    try {
      await createFolderAPI(folderName, currentFolder?._id || null);
      showToast("Khởi tạo thư mục mới hoàn tất", "success");
      setCreateFolderModal(false);
      setFolderName("");
      fetchData();
    } catch (err: any) {
      showToast("Lỗi khởi tạo thư mục lưu trữ", "error");
    }
  };
  const executeDelete = async () => {
    if (!confirmModal) return;
    try {
      if (confirmModal.type === "doc") {
        if (isAdmin) await deleteAdminDocumentAPI(confirmModal.docId);
        else await deleteAuthorDocumentAPI(confirmModal.docId);
      } else await deleteFolderAPI(confirmModal.docId);
      showToast("Xóa dữ liệu hoàn tất", "success");
      fetchData();
    } catch (err: any) {
      showToast("Lỗi xóa dữ liệu khỏi hệ thống", "error");
    } finally {
      setConfirmModal(null);
    }
  };
  const handleLockDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lockModal?.docId || !lockPassword) return;
    try {
      await lockDocumentAPI(lockModal.docId, lockPassword);
      showToast("Cập nhật trạng thái bảo mật hoàn tất", "success");
      setLockModal(null);
      setLockPassword("");
      fetchData();
    } catch (err: any) {
      showToast("Lỗi cấu hình bảo mật tài liệu", "error");
    }
  };
  const handleShareSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!shareModal?.docId) return;
    setPublicUrl(
      `${window.location.origin}/tai-lieu/viewer/${shareModal.docId}${sharePassword ? `?pwd=${sharePassword}` : ""}`,
    );
    showToast("Khởi tạo liên kết chia sẻ hoàn tất", "success");
  };
  const toggleStar = async (id: string) => {
    try {
      await toggleStarDocumentAPI(id);
      fetchData();
    } catch (err: any) {
      showToast("Lỗi cập nhật trạng thái dữ liệu", "error");
    }
  };

  if (authLoading || isLoading) return <PageLoader />;

  return (
    <div className="w-full h-full font-sans text-[#1D1D1F]">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />
      <div className="flex flex-col md:flex-row">
        <DocumentSidebar viewMode={viewMode} setViewMode={setViewMode} setFilterStar={setFilterStar} filterFormat={filterFormat} setFilterFormat={setFilterFormat} />

        <main className="flex-1 min-w-0 space-y-8 pt-6">
          <DocumentToolbar
            currentFolder={currentFolder}
            breadcrumbs={breadcrumbs}
            setCurrentFolder={setCurrentFolder}
            setBreadcrumbs={setBreadcrumbs}
            showSearch={showSearch}
            setShowSearch={setShowSearch}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            sortOrder={sortOrder}
            setSortOrder={setSortOrder}
            layout={layout}
            setLayout={setLayout}
            setShowPublishModal={setShowPublishModal}
          />
