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
      `${window.location.origin}/tai-lieu/xem-truoc/${shareModal.docId}${sharePassword ? `?pwd=${sharePassword}` : ""}`,
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
        <aside className="w-full md:w-[240px] shrink-0 space-y-6 sticky top-0 h-fit mb-6 md:mb-0 md:mr-6">
          <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0 md:pt-6">
            <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
              Phân loại
            </p>
            <nav className="flex flex-col gap-1.5">
              <button
                onClick={() => { setViewMode("list"); setFilterStar(false); setFilterFormat("all"); }}
                className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors bg-white text-[#0071E3] font-medium`}
              >
                <span className="truncate text-left">Tất cả tài liệu</span>
                <ChevronRight className="w-4 h-4 shrink-0" />
              </button>
            </nav>
          </div>

          <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0 md:pt-6 space-y-2">
            <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
              Lọc định dạng
            </p>
            <div className="relative">
              <select
                value={filterFormat}
                onChange={(e) => setFilterFormat(e.target.value)}
                className="w-full h-[44px] bg-[#F5F5F7] md:bg-white px-4 text-[14px] font-medium focus:outline-none focus:border-[#0071E3] appearance-none rounded-[10px] border border-transparent focus:bg-white transition-colors"
              >
                <option value="all">Mọi định dạng</option>
                <option value="pdf">PDF</option>
                <option value="docx">Word</option>
                <option value="xlsx">Excel</option>
                <option value="pptx">PowerPoint</option>
                <option value="zip">ZIP</option>
              </select>
              <ChevronRight className="w-5 h-5 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none rotate-90 text-[#6E6E73]" />
            </div>
          </div>
        </aside>

        <main className="flex-1 min-w-0 space-y-8 pt-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <h2 className="flex items-center gap-2 text-[20px] font-semibold text-[#1D1D1F]">
              {!currentFolder && breadcrumbs.length === 0 ? (
                <span>Gốc</span>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setCurrentFolder(null);
                      setBreadcrumbs([]);
                    }}
                    className={`flex items-center gap-1 transition-colors hover:text-[#1D1D1F] text-[#6E6E73]`}
                  >
                    Gốc
                  </button>
                  <ChevronRight className="w-5 h-5 text-[#A1A1A6]" />
                  {breadcrumbs.map((crumb, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          const nb = breadcrumbs.slice(0, idx + 1);
                          setBreadcrumbs(nb);
                          setCurrentFolder(nb[nb.length - 1]);
                        }}
                        className={`flex items-center gap-1 transition-colors ${idx === breadcrumbs.length - 1 ? "text-[#1D1D1F]" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
                      >
                        {crumb.name}
                      </button>
                      {idx < breadcrumbs.length - 1 && (
                        <ChevronRight className="w-5 h-5 text-[#A1A1A6]" />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </h2>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => fetchData()}
                  className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
                  title="Làm mới"
                >
                  {isRefreshing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <RefreshCcw className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={() => setCreateFolderModal(true)}
                  className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
                  title="Thêm thư mục mới"
                >
                  <FolderPlus className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setCreateDocModal(true)}
                  className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
                  title="Thêm tài liệu"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <div
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`w-full overflow-x-auto min-h-[400px] transition-colors rounded-[18px] ${isDraggingOver ? "border-2 border-dashed border-[#0071E3] bg-[#0071E3]/5" : ""}`}
          >
            {isLoading ? (
              <div className="flex justify-center items-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" />
              </div>
            ) : viewMode === "list" ? (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="text-[13px] text-[#6E6E73] border-b border-[#E8E8ED]">
                    <th className="py-3 px-6 font-medium text-left">Tên</th>
                    <th className="py-3 px-6 font-medium text-center hidden md:table-cell">Thể loại</th>
                    <th className="py-3 px-6 font-medium text-center hidden md:table-cell">Bảo mật</th>
                    <th className="py-3 px-6 font-medium text-center hidden md:table-cell">Trạng thái</th>
                    <th className="py-3 px-6 font-medium text-right whitespace-nowrap">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {folders.length === 0 && documents.length === 0 ? (
                    <tr>
                      <td colSpan={5}>
                        <div className="py-24 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] w-full text-center my-4">
                          <p className="text-[17px] text-[#6E6E73]">Chưa có dữ liệu</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    <>
                      {folders.map((folder) => (
                        <tr
                          key={folder._id}
                          onClick={() => {
                            setCurrentFolder(folder);
                            setBreadcrumbs([...breadcrumbs, folder]);
                          }}
                          className="hover:bg-[#E8E8ED]/60 transition-colors cursor-pointer group border-b border-[#F5F5F7] last:border-0"
                        >
                          <td className="py-3 px-6 max-w-[300px]">
                            <div className="flex items-center gap-3">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setCurrentFolder(folder);
                                  setBreadcrumbs([...breadcrumbs, folder]);
                                }}
                                className="font-medium text-[#1D1D1F] hover:text-[#0071E3] truncate text-left"
                              >
                                {folder.name}
                              </button>
                            </div>
                          </td>
                          <td className="py-3 px-6 text-center hidden md:table-cell">
                            <span className="text-[12px] bg-[#F5F5F7] text-[#6E6E73] px-3 py-1 rounded-full font-medium">Thư mục</span>
                          </td>
                          <td className="py-3 px-6 text-center hidden md:table-cell text-[#6E6E73]">--</td>
                          <td className="py-3 px-6 text-center hidden md:table-cell text-[#6E6E73]">--</td>
                          <td className="py-3 px-6 text-right">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setConfirmModal({
                                  show: true,
                                  title: "Xóa thư mục?",
                                  docId: folder._id,
                                  type: "folder",
                                });
                              }}
                              className="p-2 text-[#6E6E73] hover:text-[#FF3B30] hover:bg-[#FF3B30]/10 rounded-full opacity-0 group-hover:opacity-100 transition-all"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                      {documents.map((doc) => (
                        <tr
                          key={doc._id || doc.id}
                          onClick={() => window.open(`/tai-lieu/xem-truoc/${doc._id || doc.id}`, "_blank")}
                          className="hover:bg-[#E8E8ED]/60 transition-colors cursor-pointer group border-b border-[#F5F5F7] last:border-0"
                        >
                          <td className="py-3 px-6 max-w-[300px]">
                            <div className="flex items-center gap-3">
                              <div className="flex flex-col min-w-0">
                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                  {doc.is_starred && <Star className="w-4 h-4 text-[#FF9500] fill-[#FF9500] shrink-0" />}
                                  <p className="font-medium text-[#1D1D1F] hover:text-[#0071E3] truncate">{doc.title}</p>
                                </div>
                                <p className="text-[12px] text-[#6E6E73] mt-0.5">{doc.publisher_name || "DocLib"}</p>
                              </div>
                            </div>
                          </td>
                          <td className="py-3 px-6 text-center hidden md:table-cell">
                            <span className="text-[13px] text-[#6E6E73]">{doc.category || "Tài liệu"}</span>
                          </td>
                          <td className="py-3 px-6 text-center hidden md:table-cell">
                            {doc.is_protected ? (
                              <span className="inline-flex items-center justify-center gap-1 text-[13px] text-[#1D1D1F] bg-[#F5F5F7] px-3 py-1 rounded-full">
                                <Lock className="w-3 h-3" /> Đã khóa
                              </span>
                            ) : (
                              <span className="text-[13px] text-[#6E6E73]">Không</span>
                            )}
                          </td>
                          <td className="py-3 px-6 text-center hidden md:table-cell">
                            <span className={`text-[12px] px-3 py-1 rounded-full font-medium inline-block ${doc.status === "published" ? "bg-[#E8F3FF] text-[#0071E3]" : "bg-[#F5F5F7] text-[#6E6E73]"}`}>
                              {doc.status === "published" ? "Đã đăng" : "Bản nháp"}
                            </span>
                          </td>
                          <td className="py-3 px-6 text-right">
                            <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={(e) => { e.stopPropagation(); toggleStar(doc._id || doc.id); }}
                                className={`p-2 rounded-full transition-colors ${doc.is_starred ? "text-[#FF9500] bg-[#FF9500]/10" : "text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F]"}`}
                              >
                                <Star className={`w-4 h-4 ${doc.is_starred ? "fill-[#FF9500]" : ""}`} />
                              </button>
                              <button
                                onClick={(e) => { e.stopPropagation(); setLockModal({ show: true, docId: doc._id || doc.id }); }}
                                className="p-2 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-full transition-colors"
                              >
                                <Lock className="w-4 h-4" />
                              </button>
                              <button
                                onClick={(e) => { e.stopPropagation(); setShareModal({ show: true, docId: doc._id || doc.id }); }}
                                className="p-2 text-[#6E6E73] hover:bg-[#E8E8ED] hover:text-[#1D1D1F] rounded-full transition-colors"
                              >
                                <Share2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setConfirmModal({
                                    show: true,
                                    title: "Xóa tài liệu?",
                                    docId: doc._id || doc.id,
                                    type: "doc",
                                  });
                                }}
                                className="p-2 text-[#6E6E73] hover:bg-[#FF3B30]/10 hover:text-[#FF3B30] rounded-full transition-colors"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </>
                  )}
                </tbody>
              </table>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
                {folders.map((folder) => (
                  <div
                    key={folder._id}
                    onClick={() => {
                      setCurrentFolder(folder);
                      setBreadcrumbs([...breadcrumbs, folder]);
                    }}
                    className="group bg-white border border-[#E8E8ED] hover:border-[#0071E3] hover:shadow-sm rounded-[18px] p-4 flex flex-col items-center justify-center text-center cursor-pointer transition-all aspect-square relative"
                  >
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col gap-1 z-10">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setConfirmModal({
                            show: true,
                            title: "Xóa thư mục?",
                            docId: folder._id,
                            type: "folder",
                          });
                        }}
                        className="p-1.5 text-[#6E6E73] hover:bg-[#FF3B30]/10 hover:text-[#FF3B30] rounded-full bg-white shadow-sm"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                    <Folder className="w-12 h-12 text-[#0071E3] fill-[#0071E3]/10 mb-3" />
                    <span className="font-medium text-[#1D1D1F] text-[14px] line-clamp-2 w-full px-2">{folder.name}</span>
                    <span className="text-[12px] text-[#6E6E73] mt-1">Thư mục</span>
                  </div>
                ))}
                {documents.map((doc) => (
                  <div
                    key={doc._id || doc.id}
                    onClick={() => window.open(`/tai-lieu/xem-truoc/${doc._id || doc.id}`, "_blank")}
                    className="group bg-white border border-[#E8E8ED] hover:border-[#0071E3] hover:shadow-sm rounded-[18px] p-4 flex flex-col items-center justify-center text-center cursor-pointer transition-all aspect-[3/4] relative"
                  >
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col gap-1 z-10">
                      <button
                        onClick={(e) => { e.stopPropagation(); toggleStar(doc._id || doc.id); }}
                        className={`p-1.5 rounded-full bg-white shadow-sm transition-colors ${doc.is_starred ? "text-[#FF9500]" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
                      >
                        <Star className={`w-3 h-3 ${doc.is_starred ? "fill-[#FF9500]" : ""}`} />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setConfirmModal({
                            show: true,
                            title: "Xóa tài liệu?",
                            docId: doc._id || doc.id,
                            type: "doc",
                          });
                        }}
                        className="p-1.5 text-[#6E6E73] hover:bg-[#FF3B30]/10 hover:text-[#FF3B30] rounded-full bg-white shadow-sm"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                    {doc.is_starred && (
                      <div className="absolute top-2 left-2 group-hover:hidden">
                        <Star className="w-4 h-4 text-[#FF9500] fill-[#FF9500]" />
                      </div>
                    )}
                    <div className="w-full flex-1 bg-[#F5F5F7] rounded-[12px] flex flex-col items-center justify-center mb-3 text-[#6E6E73] overflow-hidden">
                      {doc.cover_url ? (
                        <img src={doc.cover_url} alt="Cover" className="w-full h-full object-cover" />
                      ) : (
                        <FileText className="w-12 h-12 mb-2 opacity-50" />
                      )}
                    </div>
                    <span className="font-medium text-[#1D1D1F] text-[14px] line-clamp-2 w-full px-1">{doc.title}</span>
                    <span className="text-[12px] text-[#6E6E73] mt-1 line-clamp-1 w-full px-1">{doc.publisher_name || "DocLib"}</span>
                  </div>
                ))}
              </div>
            )}
            
            {hasMore && (
              <div ref={observerTarget} className="h-10 w-full" />
            )}
          </div>
        </main>
      </div>
      <Modal
        isOpen={!!confirmModal}
        onClose={() => setConfirmModal(null)}
      >
        <ModalHeader>
          <ModalTitle className="text-[#FF3B30] flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" /> Cảnh báo xóa
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-[15px] text-[#6E6E73]">
            Bạn có chắc chắn muốn xóa{" "}
            <strong className="text-[#1D1D1F]">{confirmModal?.title}</strong>?
            Hành động này không thể hoàn tác.
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setConfirmModal(null)}
            className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full"
          >
            Hủy
          </button>
          <button
            onClick={executeDelete}
            className="pill-button bg-[#FF3B30] hover:bg-[#D70015]"
          >
            Xóa vĩnh viễn
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={createDocModal}
        onClose={() => setCreateDocModal(false)}
        className="max-w-3xl"
      >
        <ModalHeader>
          <ModalTitle>
            Khởi tạo tài liệu
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="grid md:grid-cols-2 gap-8">
          <div className="space-y-4">
            <div>
              <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
                Tiêu đề
              </label>
              <input
                type="text"
                value={newDoc.title}
                onChange={(e) =>
                  setNewDoc({ ...newDoc, title: e.target.value })
                }
                className="apple-input w-full bg-white"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
                  Thể loại
                </label>
                <select
                  value={newDoc.category}
                  onChange={(e) =>
                    setNewDoc({ ...newDoc, category: e.target.value })
                  }
                  className="apple-input w-full bg-white"
                >
                  <option value="Chưa phân loại">Chưa phân loại</option>
                  <option value="Giáo trình">Giáo trình</option>
                  <option value="Kỹ thuật">Kỹ thuật</option>
                  <option value="Nghiên cứu">Nghiên cứu</option>
                </select>
              </div>
              <div>
                <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
                  Giá (dl)
                </label>
                <input
                  type="number"
                  value={newDoc.price_dl}
                  onChange={(e) =>
                    setNewDoc({
                      ...newDoc,
                      price_dl: parseInt(e.target.value) || 0,
                    })
                  }
                  className="apple-input w-full bg-white"
                />
              </div>
            </div>
            <div>
              <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
                Mô tả
              </label>
              <textarea
                value={newDoc.description}
                onChange={(e) =>
                  setNewDoc({ ...newDoc, description: e.target.value })
                }
                className="apple-input w-full bg-white h-24 resize-none p-3 rounded-[16px]"
              />
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
                Tệp đính kèm
              </label>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden"
                accept=".pdf,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.txt,.zip,.csv,.json,.md"
              />
              <div
                onClick={() => fileInputRef.current?.click()}
                className="h-32 bg-[#F5F5F7] border-[#E8E8ED] rounded-[18px] flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-[#0071E3] transition-colors border-dashed"
              >
                <div className="w-10 h-10 bg-[#F5F5F7] rounded-full flex items-center justify-center text-[#0071E3]">
                  {file ? (
                    <FileCheck className="w-5 h-5" />
                  ) : (
                    <Upload className="w-5 h-5" />
                  )}
                </div>
                <p className="text-[14px] font-medium text-[#1D1D1F]">
                  {file ? file.name : "Chọn tệp tin"}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
                  Hiển thị
                </label>
                <select
                  value={newDoc.visibility}
                  onChange={(e) =>
                    setNewDoc({ ...newDoc, visibility: e.target.value })
                  }
                  className="apple-input w-full bg-white"
                >
                  <option value="public">Công khai</option>
                  <option value="private">Riêng tư</option>
                </select>
              </div>
              <div>
                <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
                  Trạng thái
                </label>
                <select
                  value={newDoc.status}
                  onChange={(e) =>
                    setNewDoc({ ...newDoc, status: e.target.value })
                  }
                  className="apple-input w-full bg-white"
                >
                  <option value="published">Xuất bản</option>
                  <option value="draft">Bản nháp</option>
                </select>
              </div>
            </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setCreateDocModal(false)}
            className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full"
          >
            Hủy
          </button>
          <button
            onClick={handleCreateDocument}
            disabled={isCreating || !file || !newDoc.title}
            className="pill-button disabled:opacity-50 flex items-center gap-2"
          >
            {isCreating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              "Tải lên"
            )}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={createFolderModal}
        onClose={() => setCreateFolderModal(false)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle>
            Tạo thư mục
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <input
            type="text"
            value={folderName}
            onChange={(e) => setFolderName(e.target.value)}
            placeholder=""
            className="apple-input w-full bg-white"
            autoFocus
          />
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setCreateFolderModal(false)}
            className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full"
          >
            Hủy
          </button>
          <button
            onClick={handleCreateFolder}
            disabled={!folderName}
            className="pill-button disabled:opacity-50"
          >
            Tạo
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!lockModal}
        onClose={() => setLockModal(null)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle className="flex items-center gap-2">
            <Lock className="w-5 h-5" /> Khóa tài liệu
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <form id="lock-form" onSubmit={handleLockDocument}>
            <input
              type="password"
              placeholder=""
              value={lockPassword}
              onChange={(e) => setLockPassword(e.target.value)}
              className="apple-input w-full bg-white"
              required
              autoFocus
            />
          </form>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setLockModal(null)}
            className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full"
          >
            Hủy
          </button>
          <button type="submit" form="lock-form" className="pill-button">
            Khóa
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!shareModal}
        onClose={() => setShareModal(null)}
      >
        <ModalHeader>
          <ModalTitle className="flex items-center gap-2">
            <Share2 className="w-5 h-5" /> Chia sẻ tài liệu
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <form
            id="share-form"
            onSubmit={handleShareSubmit}
            className="space-y-4"
          >
            <div className="flex items-center gap-3 bg-[#F5F5F7] p-4 rounded-[16px] border-[#E8E8ED]">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                className="w-5 h-5 rounded-[6px] border-[#C7C7CC] accent-[#0071E3]"
              />
              <span className="text-[15px] font-medium">
                Bật liên kết công khai
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
                  Mật khẩu (Tùy chọn)
                </label>
                <input
                  type="password"
                  value={sharePassword}
                  onChange={(e) => setSharePassword(e.target.value)}
                  className="apple-input w-full bg-white"
                />
              </div>
              <div>
                <label className="text-[13px] font-medium text-[#6E6E73] mb-2 block">
                  Thời hạn
                </label>
                <select
                  value={shareExpires}
                  onChange={(e) => setShareExpires(e.target.value)}
                  className="apple-input w-full bg-white"
                >
                  <option value="1">24 giờ</option>
                  <option value="7">7 ngày</option>
                  <option value="30">30 ngày</option>
                </select>
              </div>
            </div>
            {publicUrl && (
              <div className="bg-[#F5F5F7] p-6 rounded-[18px] border-[#E8E8ED] flex flex-col items-center gap-4 mt-4">
                <input
                  type="text"
                  readOnly
                  value={publicUrl}
                  className="apple-input w-full text-center bg-[#F5F5F7] text-[#0071E3]"
                  onFocus={(e) => e.target.select()}
                />
                <div className="p-2 bg-white rounded-xl ">
                  <QRCodeSVG value={publicUrl} size={100} />
                </div>
              </div>
            )}
          </form>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => {
              setShareModal(null);
              setPublicUrl("");
            }}
            className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full"
          >
            Đóng
          </button>
          <button type="submit" form="share-form" className="pill-button">
            Tạo liên kết
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
