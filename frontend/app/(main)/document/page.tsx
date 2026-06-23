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
} from "@/features/content/services/document_metadata.service";
import { uploadDocumentAPI } from "@/features/content/services/file_upload.service";
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
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
import Link from "next/link";

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
  const [visible, setVisible] = useState(false);
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
        if (!isAdmin) {
          if (currentFolder)
            docs = docs.filter((d: any) => d.folder_id === currentFolder._id);
          else docs = docs.filter((d: any) => !d.folder_id);
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
        }

        if (docs.length < 20) setHasMore(false);
        else setHasMore(true);

        if (docs.length > 0)
          setCursor(docs[docs.length - 1].id || docs[docs.length - 1]._id);

        setDocuments((prev) => (isLoadMore ? [...prev, ...docs] : docs));
        if (!isLoadMore) setFolders(foldersData.data || foldersData || []);
      } catch (err: any) {
        showToast("Không thể tải danh sách tài liệu", "error");
      } finally {
        setIsRefreshing(false);
        setIsLoading(false);
        requestAnimationFrame(() => setVisible(true));
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
      setNewDoc((prev) => ({
        ...prev,
        publisher_name: isAdmin ? "DocLib" : user.full_name || "",
      }));
    }
  }, [user, authLoading, isAdmin]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isRefreshing) {
          fetchData(true);
        }
      },
      { threshold: 0.5 },
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => observer.disconnect();
  }, [hasMore, isRefreshing, fetchData]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (!newDoc.title) {
        const name = selectedFile.name.split(".")[0];
        setNewDoc((prev) => ({
          ...prev,
          title: name,
          slug: name
            .toLowerCase()
            .replace(/\s+/g, "-")
            .replace(/[^a-z0-9-]/g, ""),
        }));
      }
    }
  };

  const handleCreateDocument = async () => {
    if (!newDoc.title || !file) {
      showToast("Vui lòng nhập tiêu đề và chọn tệp tin", "error");
      return;
    }

    setIsCreating(true);
    try {
      const submissionData = {
        ...newDoc,
        file_url: "",
        content_format: file.name.split(".").pop()?.toLowerCase() || "json",
        folder_id: currentFolder?._id || null,
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
        const file_url = uploadRes.data.url;
        await updateDocumentAPI(createdDoc.data._id || createdDoc.data.id, {
          file_url,
          content_format:
            uploadRes.data.extension || submissionData.content_format,
        });
      } catch (uploadErr: any) {
        await deleteAuthorDocumentAPI(
          createdDoc.data._id || createdDoc.data.id,
        ).catch(() => {});
        throw new Error("Lỗi tải lên tệp tin, đã hủy tạo tài liệu");
      }

      showToast("Đã khởi tạo tài liệu thành công", "success");
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
      showToast(err.message || "Lỗi hệ thống khi khởi tạo", "error");
    } finally {
      setIsCreating(false);
    }
  };

  const handleCreateFolder = async () => {
    if (!folderName) return;
    try {
      await createFolderAPI(folderName, currentFolder?._id || null);
      showToast("Đã kiến tạo thư mục mới", "success");
      setCreateFolderModal(false);
      setFolderName("");
      fetchData();
    } catch (err: any) {
      showToast("Không thể tạo thư mục", "error");
    }
  };

  const executeDelete = async () => {
    if (!confirmModal) return;
    try {
      if (confirmModal.type === "doc") {
        if (isAdmin) {
          await deleteAdminDocumentAPI(confirmModal.docId);
        } else {
          await deleteAuthorDocumentAPI(confirmModal.docId);
        }
      } else {
        await deleteFolderAPI(confirmModal.docId);
      }
      showToast("Đã loại bỏ thực thể khỏi hệ thống", "success");
      fetchData();
    } catch (err: any) {
      showToast("Thao tác thất bại", "error");
    } finally {
      setConfirmModal(null);
    }
  };

  const handleLockDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lockModal?.docId || !lockPassword) return;
    try {
      await lockDocumentAPI(lockModal.docId, lockPassword);
      showToast("Đã thiết lập bảo mật đa lớp", "success");
      setLockModal(null);
      setLockPassword("");
      fetchData();
    } catch (err: any) {
      showToast("Thiết lập bảo mật thất bại", "error");
    }
  };

  const handleShareSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!shareModal?.docId) return;
    setPublicUrl(
      `${window.location.origin}/document/viewer/${shareModal.docId}${sharePassword ? `?pwd=${sharePassword}` : ""}`,
    );
    showToast("Giao thức chia sẻ đã sẵn sàng", "success");
  };

  const toggleStar = async (id: string) => {
    try {
      await toggleStarDocumentAPI(id);
      fetchData();
    } catch (err: any) {
      showToast("Thao tác thất bại", "error");
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-zinc-50">
        <Loader2 className="w-8 h-8 animate-spin text-black" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col gap-6 font-sans text-zinc-900 selection:bg-zinc-900 selection:text-white bg-zinc-50">
      <Modal
        isOpen={!!confirmModal}
        onClose={() => setConfirmModal(null)}
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md shadow-xl p-0 overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 border border-zinc-100 bg-white shadow-sm flex items-center justify-center rounded-2xl">
              <AlertTriangle className="w-5 h-5 text-red-500" />
            </div>
            <div>
              <ModalTitle className="text-sm font-bold text-black tracking-tight">
                {confirmModal?.title}
              </ModalTitle>
              <ModalDescription className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mt-1">
                Hành động này sẽ xóa vĩnh viễn dữ liệu khỏi hệ thống
              </ModalDescription>
            </div>
          </div>
        </ModalHeader>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => setConfirmModal(null)}
            className="flex-1 h-10 border border-zinc-200 bg-white text-xs font-bold text-black rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:bg-zinc-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={executeDelete}
            className="flex-1 h-10 bg-black text-white text-xs font-bold rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
          >
            Xác nhận
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={createDocModal}
        onClose={() => setCreateDocModal(false)}
        className="max-w-3xl rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md shadow-xl p-0 overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6">
          <ModalTitle className="text-sm font-bold text-black tracking-tight">
            {isAdmin ? "Thêm tài liệu hệ thống" : "Khởi tạo tài liệu mới"}
          </ModalTitle>
          <ModalDescription className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mt-1">
            Điền thông tin để bắt đầu quá trình lưu trữ chuyên sâu
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="grid md:grid-cols-2 gap-8 p-6">
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                Tiêu đề tài liệu
              </label>
              <input
                type="text"
                value={newDoc.title}
                onChange={(e) =>
                  setNewDoc({ ...newDoc, title: e.target.value })
                }
                className="w-full h-11 px-4 bg-white border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black rounded-2xl shadow-sm transition-all"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                  Thể loại
                </label>
                <div className="relative">
                  <select
                    value={newDoc.category}
                    onChange={(e) =>
                      setNewDoc({ ...newDoc, category: e.target.value })
                    }
                    className="w-full h-11 px-4 bg-white border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black appearance-none rounded-2xl shadow-sm transition-all"
                  >
                    <option value="Chưa phân loại">Chưa phân loại</option>
                    <option value="Giáo trình">Giáo trình</option>
                    <option value="Kỹ thuật">Kỹ thuật</option>
                    <option value="Nghiên cứu">Nghiên cứu</option>
                  </select>
                  <ChevronRight className="w-4 h-4 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none rotate-90 text-zinc-400" />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                  Giá (dl)
                </label>
                <input
                  type="number"
                  className="w-full h-11 px-4 bg-white border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black rounded-2xl shadow-sm transition-all"
                  value={newDoc.price_dl}
                  onChange={(e) =>
                    setNewDoc({
                      ...newDoc,
                      price_dl: parseInt(e.target.value) || 0,
                    })
                  }
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                Mô tả tóm lược
              </label>
              <textarea
                value={newDoc.description}
                onChange={(e) =>
                  setNewDoc({ ...newDoc, description: e.target.value })
                }
                className="w-full h-24 p-4 bg-white border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black resize-none rounded-2xl shadow-sm transition-all"
              />
            </div>
          </div>

          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                Thực thể đính kèm
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
                className="border border-zinc-200 bg-white shadow-sm p-8 flex flex-col items-center justify-center gap-4 cursor-pointer rounded-3xl transition-all hover:border-black hover:bg-zinc-50 group"
              >
                <div className="w-12 h-12 flex items-center justify-center bg-white border border-zinc-100 shadow-sm text-black rounded-2xl group-hover:scale-110 transition-transform">
                  {file ? (
                    <FileCheck className="w-5 h-5" />
                  ) : (
                    <Upload className="w-5 h-5" />
                  )}
                </div>
                <div className="text-center">
                  <p className="text-sm font-bold text-black mb-1 truncate max-w-[200px]">
                    {file ? file.name : "Chọn tệp tin (PDF, Office...)"}
                  </p>
                  <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                    {file
                      ? `${(file.size / (1024 * 1024)).toFixed(2)} MB`
                      : "Tối đa 50MB"}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                  Hiển thị
                </label>
                <div className="relative">
                  <select
                    value={newDoc.visibility}
                    onChange={(e) =>
                      setNewDoc({ ...newDoc, visibility: e.target.value })
                    }
                    className="w-full h-11 px-4 bg-white border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black appearance-none rounded-2xl shadow-sm transition-all"
                  >
                    <option value="public">Công khai</option>
                    <option value="private">Riêng tư</option>
                  </select>
                  <ChevronRight className="w-4 h-4 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none rotate-90 text-zinc-400" />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                  Trạng thái
                </label>
                <div className="relative">
                  <select
                    value={newDoc.status}
                    onChange={(e) =>
                      setNewDoc({ ...newDoc, status: e.target.value })
                    }
                    className="w-full h-11 px-4 bg-white border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black appearance-none rounded-2xl shadow-sm transition-all"
                  >
                    <option value="published">Xuất bản</option>
                    <option value="draft">Bản nháp</option>
                  </select>
                  <ChevronRight className="w-4 h-4 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none rotate-90 text-zinc-400" />
                </div>
              </div>
            </div>
          </div>
        </ModalContent>
        <ModalFooter className="border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={handleCreateDocument}
            disabled={isCreating || !file || !newDoc.title}
            className="w-full h-11 bg-black text-white text-xs font-bold flex items-center justify-center gap-2 rounded-2xl disabled:opacity-50 transition-all duration-200 hover:scale-[1.01] hover:-translate-y-0.5 shadow-md"
          >
            {isCreating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            Kích hoạt lưu trữ
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={createFolderModal}
        onClose={() => setCreateFolderModal(false)}
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md shadow-xl p-0 overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6">
          <ModalTitle className="text-sm font-bold text-black tracking-tight">
            Kiến tạo không gian mới
          </ModalTitle>
          <ModalDescription className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mt-1">
            Phân loại tài liệu theo cấu trúc thư mục chuyên nghiệp
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <div className="space-y-2">
            <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
              Tên thư mục
            </label>
            <input
              type="text"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              autoFocus
              className="w-full h-11 px-4 bg-white border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black rounded-2xl shadow-sm transition-all"
            />
          </div>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => setCreateFolderModal(false)}
            className="flex-1 h-10 border border-zinc-200 bg-white text-xs font-bold text-black rounded-2xl transition-all duration-200 hover:scale-[1.02]"
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleCreateFolder}
            disabled={!folderName}
            className="flex-1 h-10 bg-black text-white text-xs font-bold rounded-2xl disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
          >
            Tạo thư mục
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!lockModal}
        onClose={() => setLockModal(null)}
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md shadow-xl p-0 overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 border border-zinc-100 bg-white shadow-sm flex items-center justify-center rounded-2xl">
              <Lock className="w-5 h-5 text-black" />
            </div>
            <div>
              <ModalTitle className="text-sm font-bold text-black tracking-tight">
                Thiết lập bảo mật
              </ModalTitle>
              <ModalDescription className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mt-1">
                Mã hóa đa lớp cho thực thể
              </ModalDescription>
            </div>
          </div>
        </ModalHeader>
        <ModalContent className="p-6">
          <form
            id="lock-form"
            onSubmit={handleLockDocument}
            className="space-y-4"
          >
            <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest leading-relaxed">
              Mật khẩu sẽ được mã hóa và không thể khôi phục nếu bị thất lạc
            </p>
            <input
              type="password"
              autoFocus
              className="w-full h-11 px-4 bg-white border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black rounded-2xl shadow-sm transition-all"
              value={lockPassword}
              onChange={(e) => setLockPassword(e.target.value)}
              required
            />
          </form>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            type="button"
            onClick={() => setLockModal(null)}
            className="flex-1 h-10 border border-zinc-200 bg-white text-xs font-bold text-black rounded-2xl transition-all duration-200 hover:scale-[1.02]"
          >
            Hủy bỏ
          </button>
          <button
            type="submit"
            form="lock-form"
            className="flex-1 h-10 bg-black text-white text-xs font-bold rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
          >
            Kích hoạt khóa
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!shareModal}
        onClose={() => setShareModal(null)}
        className="max-w-xl rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md shadow-xl p-0 overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 border border-zinc-100 bg-white shadow-sm flex items-center justify-center rounded-2xl">
              <Globe className="w-5 h-5 text-black" />
            </div>
            <div>
              <ModalTitle className="text-sm font-bold text-black tracking-tight">
                Giao thức chia sẻ
              </ModalTitle>
              <ModalDescription className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mt-1">
                Thiết lập quyền truy cập công khai
              </ModalDescription>
            </div>
          </div>
        </ModalHeader>
        <ModalContent className="p-6 space-y-6">
          <form
            id="share-form"
            onSubmit={handleShareSubmit}
            className="space-y-6"
          >
            <div className="flex items-center gap-3 bg-white p-4 border border-zinc-200 rounded-2xl shadow-sm">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                className="w-4 h-4 accent-black cursor-pointer rounded-xl"
              />
              <label className="text-[10px] font-bold text-black uppercase tracking-widest cursor-pointer">
                Công khai tài liệu
              </label>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                  Mật mã truy cập
                </label>
                <input
                  type="password"
                  value={sharePassword}
                  onChange={(e) => setSharePassword(e.target.value)}
                  className="w-full h-11 px-4 bg-white border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black rounded-2xl shadow-sm transition-all"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                  Thời hạn hiệu lực
                </label>
                <div className="relative">
                  <select
                    value={shareExpires}
                    onChange={(e) => setShareExpires(e.target.value)}
                    className="w-full h-11 px-4 bg-white border border-zinc-200 text-[10px] font-bold uppercase tracking-widest focus:outline-none focus:border-black rounded-2xl appearance-none shadow-sm transition-all"
                  >
                    <option value="1">24 giờ</option>
                    <option value="7">07 ngày</option>
                    <option value="30">30 ngày</option>
                  </select>
                  <ChevronRight className="w-4 h-4 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none rotate-90 text-zinc-400" />
                </div>
              </div>
            </div>
            {publicUrl && (
              <div className="p-6 bg-zinc-50 border border-zinc-100 flex flex-col items-center gap-6 rounded-3xl">
                <div className="text-[10px] font-bold text-black break-all select-all text-center uppercase tracking-widest bg-white p-4 border border-zinc-100 w-full rounded-2xl shadow-sm">
                  {publicUrl}
                </div>
                <div className="p-4 bg-white border border-zinc-100 rounded-2xl shadow-sm">
                  <QRCodeSVG value={publicUrl} size={128} />
                </div>
                <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                  <QrCode className="w-4 h-4" /> Quét mã để tiếp cận
                </p>
              </div>
            )}
          </form>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            type="button"
            onClick={() => {
              setShareModal(null);
              setPublicUrl("");
            }}
            className="flex-1 h-10 border border-zinc-200 bg-white text-xs font-bold text-black rounded-2xl transition-all duration-200 hover:scale-[1.02]"
          >
            Đóng
          </button>
          <button
            type="submit"
            form="share-form"
            className="flex-1 h-10 bg-black text-white text-xs font-bold rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
          >
            Cập nhật giao thức
          </button>
        </ModalFooter>
      </Modal>

      <div
        className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full min-h-0"
        style={{ opacity: visible ? 1 : 0 }}
      >
        <aside className="lg:col-span-3 flex flex-col gap-5 overflow-y-auto custom-scrollbar pb-6 pr-2">
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-6 space-y-4">
            <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
              <Search className="w-3.5 h-3.5" /> Tìm kiếm tài liệu
            </h3>
            <input
              type="text"
              placeholder="Nhập từ khóa"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full h-11 bg-white border border-zinc-200 px-4 text-sm font-medium focus:outline-none focus:border-black rounded-2xl placeholder:text-zinc-400 transition-all shadow-sm"
            />
          </div>

          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-6 space-y-4">
            <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
              <Database className="w-3.5 h-3.5" /> Lọc dữ liệu
            </h3>
            <div className="space-y-4">
              <button
                onClick={() => setFilterStar(!filterStar)}
                className={`w-full flex items-center justify-between px-4 py-3 text-[10px] font-bold uppercase tracking-widest rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 ${
                  filterStar
                    ? "bg-black text-white shadow-md"
                    : "bg-white text-zinc-600 border border-zinc-200 hover:bg-zinc-50"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Star
                    className={`w-4 h-4 ${filterStar ? "fill-current" : ""}`}
                  />{" "}
                  Yêu thích
                </div>
                {filterStar && <X className="w-4 h-4" />}
              </button>

              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                  Định dạng tệp
                </label>
                <div className="relative">
                  <select
                    value={filterFormat}
                    onChange={(e) => setFilterFormat(e.target.value)}
                    className="w-full h-11 px-4 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest outline-none focus:border-black rounded-2xl appearance-none transition-all shadow-sm"
                  >
                    <option value="all">Mọi định dạng</option>
                    <option value="pdf">Tài liệu PDF</option>
                    <option value="docx">Văn bản Word</option>
                    <option value="xlsx">Bảng tính Excel</option>
                    <option value="pptx">Thuyết trình PPT</option>
                    <option value="zip">Gói nén (ZIP)</option>
                  </select>
                  <ChevronRight className="w-4 h-4 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none rotate-90 text-zinc-400" />
                </div>
              </div>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-9 flex flex-col gap-6 h-full min-h-0 overflow-hidden">
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="flex items-center gap-2 overflow-x-auto no-scrollbar max-w-full px-2">
              <button
                onClick={() => {
                  setCurrentFolder(null);
                  setBreadcrumbs([]);
                }}
                className={`flex items-center gap-2 px-3 py-2 text-[10px] font-bold uppercase tracking-widest rounded-xl transition-all ${!currentFolder ? "bg-zinc-900 text-white shadow-md" : "bg-white text-zinc-500 hover:bg-zinc-50"}`}
              >
                <Home className="w-3.5 h-3.5" />
                Gốc
              </button>
              {breadcrumbs.map((b, idx) => (
                <div key={b._id} className="flex items-center gap-2 shrink-0">
                  <ChevronRight className="w-3 h-3 text-zinc-300" />
                  <button
                    onClick={() => {
                      const newBread = breadcrumbs.slice(0, idx + 1);
                      setBreadcrumbs(newBread);
                      setCurrentFolder(newBread[newBread.length - 1]);
                    }}
                    className={`px-3 py-2 text-[10px] font-bold uppercase tracking-widest rounded-xl transition-all ${idx === breadcrumbs.length - 1 ? "bg-zinc-900 text-white shadow-md" : "bg-white text-zinc-500 hover:bg-zinc-50"}`}
                  >
                    {b.name}
                  </button>
                </div>
              ))}
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setCreateFolderModal(true)}
                className="flex items-center gap-2 border border-zinc-200 px-4 py-2.5 text-[10px] font-bold uppercase tracking-widest rounded-2xl bg-white text-black hover:bg-zinc-50 transition-all duration-200 hover:scale-[1.02]"
              >
                <FolderPlus className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Thư mục</span>
              </button>
              <button
                onClick={() => setCreateDocModal(true)}
                className="flex items-center gap-2 px-4 py-2.5 text-[10px] font-bold uppercase tracking-widest rounded-2xl bg-black text-white transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
              >
                <Plus className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Thêm tài liệu</span>
              </button>
              <div className="w-[1px] h-6 bg-zinc-200 mx-1"></div>
              <div className="flex bg-zinc-50 border border-zinc-200 p-0.5 rounded-2xl">
                <button
                  onClick={() => setViewMode("grid")}
                  className={`p-2 rounded-xl transition-all duration-200 hover:scale-110 ${viewMode === "grid" ? "bg-white text-black shadow-sm" : "text-zinc-400 bg-transparent"}`}
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setViewMode("list")}
                  className={`p-2 rounded-xl transition-all duration-200 hover:scale-110 ${viewMode === "list" ? "bg-white text-black shadow-sm" : "text-zinc-400 bg-transparent"}`}
                >
                  <List className="w-3.5 h-3.5" />
                </button>
              </div>
              <button
                onClick={fetchData}
                className="p-2.5 border border-zinc-200 bg-white flex items-center justify-center text-zinc-500 rounded-xl hover:bg-zinc-50 hover:text-black transition-all"
              >
                {isRefreshing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCcw className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {viewMode === "list" ? (
            <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm overflow-hidden flex flex-col flex-1 min-h-0">
              <div className="overflow-y-auto custom-scrollbar flex-1">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-zinc-50/90 backdrop-blur-sm z-10">
                    <tr className="border-b border-zinc-100 text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
                      <th className="px-6 py-4">Tài liệu</th>
                      <th className="px-6 py-4">Phân loại</th>
                      <th className="px-6 py-4">Bảo mật</th>
                      <th className="px-6 py-4 text-right">Hành động</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-50">
                    {folders.map((folder: any) => (
                      <tr
                        key={folder._id}
                        className="hover:bg-zinc-50 cursor-pointer group transition-colors"
                        onClick={() => {
                          setCurrentFolder(folder);
                          setBreadcrumbs([...breadcrumbs, folder]);
                        }}
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-10 bg-white border border-zinc-100 shadow-sm flex items-center justify-center rounded-xl shrink-0 text-zinc-400 group-hover:text-black group-hover:scale-110 transition-all duration-300">
                              <Folder className="w-4 h-4" />
                            </div>
                            <span className="font-bold text-zinc-900">
                              {folder.name}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                          Thư mục hệ thống
                        </td>
                        <td className="px-6 py-4 text-zinc-300">—</td>
                        <td className="px-6 py-4 text-right">
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
                            className="p-2 text-zinc-300 hover:text-red-500 hover:bg-red-50 rounded-xl inline-flex transition-colors opacity-0 group-hover:opacity-100"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {documents.map((doc: any) => (
                      <tr
                        key={doc._id || doc.id}
                        className="hover:bg-zinc-50 group transition-colors"
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-12 bg-white border border-zinc-100 shadow-sm flex items-center justify-center rounded-xl shrink-0 text-zinc-400 group-hover:text-black transition-all">
                              <FileText className="w-4 h-4" />
                            </div>
                            <div className="flex flex-col gap-1 min-w-0">
                              <span className="font-semibold text-zinc-900 truncate max-w-sm">
                                {doc.title}
                              </span>
                              <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-1.5">
                                {doc.publisher_name || "DocLib"}{" "}
                                <ChevronRight className="w-3 h-3 text-zinc-300" />{" "}
                                {doc.category || "Tài liệu"}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`inline-block px-2.5 py-1 text-[9px] font-bold uppercase tracking-widest rounded-xl ${
                              doc.status === "published"
                                ? "bg-zinc-900 text-white shadow-sm"
                                : "bg-zinc-100 text-zinc-500"
                            }`}
                          >
                            {doc.status === "published"
                              ? "Đã đăng"
                              : "Bản nháp"}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          {doc.is_protected ? (
                            <div className="flex items-center gap-1.5 text-black">
                              <Lock className="w-3.5 h-3.5" />
                              <span className="text-[9px] font-bold uppercase tracking-widest">
                                Đã khóa
                              </span>
                            </div>
                          ) : (
                            <span className="text-zinc-400 text-[9px] font-bold uppercase tracking-widest">
                              Không
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => toggleStar(doc._id || doc.id)}
                              className={`p-2 rounded-xl inline-flex transition-colors ${doc.is_starred ? "text-yellow-500 bg-yellow-50" : "text-zinc-400 hover:text-black hover:bg-white border border-transparent hover:border-zinc-200"}`}
                            >
                              <Star
                                className={`w-4 h-4 ${doc.is_starred ? "fill-current" : ""}`}
                              />
                            </button>
                            <button
                              onClick={() =>
                                setLockModal({
                                  show: true,
                                  docId: doc._id || doc.id,
                                })
                              }
                              className="p-2 text-zinc-400 hover:text-black hover:bg-white border border-transparent hover:border-zinc-200 rounded-xl inline-flex transition-colors"
                            >
                              <Lock className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() =>
                                setShareModal({
                                  show: true,
                                  docId: doc._id || doc.id,
                                })
                              }
                              className="p-2 text-zinc-400 hover:text-black hover:bg-white border border-transparent hover:border-zinc-200 rounded-xl inline-flex transition-colors"
                            >
                              <Share2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() =>
                                window.open(
                                  `/document/viewer/${doc._id || doc.id}`,
                                  "_blank",
                                )
                              }
                              className="p-2 text-zinc-400 hover:text-black hover:bg-white border border-transparent hover:border-zinc-200 rounded-xl inline-flex transition-colors"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() =>
                                setConfirmModal({
                                  show: true,
                                  title: "Xóa tài liệu?",
                                  docId: doc._id || doc.id,
                                  type: "doc",
                                })
                              }
                              className="p-2 text-zinc-400 hover:text-red-500 hover:bg-red-50 border border-transparent hover:border-red-100 rounded-xl inline-flex transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-5 overflow-y-auto custom-scrollbar pb-6 pr-2">
              {folders.map((folder: any) => (
                <div
                  key={folder._id}
                  onClick={() => {
                    setCurrentFolder(folder);
                    setBreadcrumbs([...breadcrumbs, folder]);
                  }}
                  className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 flex flex-col items-center justify-center gap-4 cursor-pointer rounded-3xl shadow-sm transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1 hover:shadow-md hover:border-zinc-200 group"
                >
                  <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center text-zinc-400 rounded-2xl group-hover:text-black group-hover:scale-110 transition-all duration-300">
                    <Folder className="w-6 h-6" />
                  </div>
                  <span className="text-xs font-bold text-zinc-900 text-center">
                    {folder.name}
                  </span>
                </div>
              ))}
              {documents.map((doc: any) => (
                <div
                  key={doc._id || doc.id}
                  className="bg-white/90 backdrop-blur-md border border-zinc-100 p-5 flex flex-col rounded-3xl shadow-sm transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1 hover:shadow-md hover:border-zinc-200 group relative"
                >
                  <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <button
                      onClick={() => toggleStar(doc._id || doc.id)}
                      className={`p-1.5 bg-white border rounded-xl shadow-sm hover:scale-110 transition-all ${doc.is_starred ? "text-yellow-500 border-yellow-200 bg-yellow-50" : "text-zinc-400 border-zinc-100 hover:text-black"}`}
                    >
                      <Star
                        className={`w-3.5 h-3.5 ${doc.is_starred ? "fill-current" : ""}`}
                      />
                    </button>
                  </div>

                  <div className="flex flex-col items-center gap-4 mb-4 mt-2">
                    <div className="w-20 h-24 bg-zinc-50 shadow-sm flex items-center justify-center text-zinc-300 rounded-xl group-hover:text-black transition-colors border border-zinc-100 overflow-hidden relative">
                      {doc.cover_url ? (
                         <img src={doc.cover_url} className="w-full h-full object-cover" alt="" />
                      ) : (
                         <FileText className="w-8 h-8 stroke-[1.5]" />
                      )}
                    </div>
                    <div className="text-center w-full px-2 space-y-1">
                      <p className="text-xs font-semibold text-zinc-900 truncate w-full">
                        {doc.title}
                      </p>
                      <p className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest truncate w-full">
                        {doc.category || "Tài liệu"}
                      </p>
                    </div>
                  </div>

                  <div className="mt-auto border-t border-zinc-50 pt-3 flex justify-between gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() =>
                        window.open(
                          `/document/viewer/${doc._id || doc.id}`,
                          "_blank",
                        )
                      }
                      className="flex-1 py-2 text-zinc-400 bg-zinc-50 hover:text-black hover:bg-zinc-100 rounded-xl transition-all flex justify-center"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() =>
                        setLockModal({ show: true, docId: doc._id || doc.id })
                      }
                      className="flex-1 py-2 text-zinc-400 bg-zinc-50 hover:text-black hover:bg-zinc-100 rounded-xl transition-all flex justify-center"
                    >
                      <Lock className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() =>
                        setShareModal({ show: true, docId: doc._id || doc.id })
                      }
                      className="flex-1 py-2 text-zinc-400 bg-zinc-50 hover:text-black hover:bg-zinc-100 rounded-xl transition-all flex justify-center"
                    >
                      <Share2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() =>
                        setConfirmModal({
                          show: true,
                          title: "Xóa tài liệu?",
                          docId: doc._id || doc.id,
                          type: "doc",
                        })
                      }
                      className="flex-1 py-2 text-zinc-400 bg-zinc-50 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all flex justify-center"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {documents.length === 0 && folders.length === 0 && (
            <div className="py-24 flex flex-col items-center justify-center border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm gap-4">
              <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm rounded-2xl flex items-center justify-center">
                <Search className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
              </div>
              <div className="text-center">
                <h2 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-1">
                  Không tìm thấy tài liệu
                </h2>
                <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest max-w-xs mx-auto">
                  Hiện tại không có bất kỳ thực thể dữ liệu nào hoặc không khớp với tiêu chí.
                </p>
              </div>
            </div>
          )}

          {(documents.length > 0 || folders.length > 0) && (
            <div
              ref={observerTarget}
              className="h-10 mt-2 flex items-center justify-center"
            >
              {isRefreshing && hasMore && (
                <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
