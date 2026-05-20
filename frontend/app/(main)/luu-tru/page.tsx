"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  getArchiveAPI,
  deleteArchiveAPI,
  uploadArchiveAPI,
  uploadDocumentFileAPI as uploadDocumentFile,
  getFileDownloadUrlAPI as getFileDownloadUrl,
  renameArchiveAPI,
  togglePinArchiveAPI,
  restoreArchiveAPI,
  permanentlyDeleteArchiveAPI,
  updateArchiveDescriptionAPI,
  toggleArchiveVisibilityAPI,
  shareArchiveAPI,
  updateArchiveTagsAPI,
} from "@/services/archive.service";
import { getMyProfileAPI } from "@/services/profile.service";
import {
  Loader2,
  Image as ImageIcon,
  FileText,
  Search,
  Pin,
  HardDrive,
} from "lucide-react";
import { useToast } from "@/contexts/Toast";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";

export default function ArchivePage() {
  const { showToast } = useToast();
  const [files, setFiles] = useState<any[]>([]);
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const [renameId, setRenameId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewType, setPreviewType] = useState<string>("");
  const [previewName, setPreviewName] = useState<string>("");

  const [permanentDeleteId, setPermanentDeleteId] = useState<string | null>(null);
  const [descriptionId, setDescriptionId] = useState<string | null>(null);
  const [descriptionValue, setDescriptionValue] = useState<string>("");
  const [dateFilter, setDateFilter] = useState<string>("all");
  const [sizeFilter, setSizeFilter] = useState<string>("all");

  const [shareId, setShareId] = useState<string | null>(null);
  const [shareEmail, setShareEmail] = useState<string>("");
  const [tagsId, setTagsId] = useState<string | null>(null);
  const [tagsValue, setTagsValue] = useState<string>("");

  const fetchArchive = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getArchiveAPI(selectedCategory === "trash" ? "trash" : "all");
      setFiles(data.data || data || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách tệp tin", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast, selectedCategory]);

  useEffect(() => {
    fetchArchive();
  }, [fetchArchive]);

  useEffect(() => {
    getMyProfileAPI()
      .then((data) => setProfile(data.data || data))
      .catch(() => {});
  }, []);

  const processFileUpload = async (file: File) => {
    try {
      const storageData = await uploadDocumentFile(file);
      const filePath = storageData.data?.url || storageData.data?.filename || storageData.url || storageData.filename;
      if (!filePath) throw new Error("Không nhận được đường dẫn tệp tin từ máy chủ");

      const downloadUrlData = await getFileDownloadUrl(filePath);
      const url = downloadUrlData;

      await uploadArchiveAPI({
        filename: file.name,
        type: file.type,
        size_bytes: file.size,
        url: url,
      });

      showToast(`Đã tải lên tệp ${file.name} thành công.`, "success");
    } catch (err: any) {
      showToast(`Tải lên tệp ${file.name} thất bại: ${err.message}`, "error");
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const filesArray = Array.from(e.target.files || []);
    if (filesArray.length === 0) return;
    setUploading(true);
    for (const file of filesArray) {
      await processFileUpload(file);
    }
    setUploading(false);
    fetchArchive();
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const filesArray = Array.from(e.dataTransfer.files || []);
    if (filesArray.length === 0) return;
    setUploading(true);
    for (const file of filesArray) {
      await processFileUpload(file);
    }
    setUploading(false);
    fetchArchive();
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await deleteArchiveAPI(deleteId);
      showToast("Đã di chuyển tệp tin vào thùng rác thành công.", "success");
      fetchArchive();
    } catch (err: any) {
      showToast(err.message || "Di chuyển vào thùng rác thất bại.", "error");
    } finally {
      setDeleteId(null);
    }
  };

  const handleRename = async () => {
    if (!renameId || !renameValue.trim()) return;
    try {
      await renameArchiveAPI(renameId, renameValue);
      showToast("Đã đổi tên tệp tin thành công.", "success");
      fetchArchive();
    } catch (err: any) {
      showToast(err.message || "Đổi tên tệp tin thất bại.", "error");
    } finally {
      setRenameId(null);
      setRenameValue("");
    }
  };

  const handleTogglePin = async (id: string) => {
    try {
      await togglePinArchiveAPI(id);
      showToast("Đã cập nhật trạng thái ghim thành công.", "success");
      fetchArchive();
    } catch (err: any) {
      showToast(err.message || "Ghim tệp tin thất bại.", "error");
    }
  };

  const handleRestore = async (id: string) => {
    try {
      await restoreArchiveAPI(id);
      showToast("Đã khôi phục tệp tin thành công.", "success");
      fetchArchive();
    } catch (err: any) {
      showToast(err.message || "Khôi phục tệp tin thất bại.", "error");
    }
  };

  const handlePermanentDelete = async () => {
    if (!permanentDeleteId) return;
    try {
      await permanentlyDeleteArchiveAPI(permanentDeleteId);
      showToast("Đã xóa vĩnh viễn tệp tin thành công.", "success");
      fetchArchive();
    } catch (err: any) {
      showToast(err.message || "Xóa vĩnh viễn tệp tin thất bại.", "error");
    } finally {
      setPermanentDeleteId(null);
    }
  };

  const handleUpdateDescription = async () => {
    if (!descriptionId) return;
    try {
      await updateArchiveDescriptionAPI(descriptionId, descriptionValue);
      showToast("Đã cập nhật ghi chú thành công.", "success");
      fetchArchive();
    } catch (err: any) {
      showToast(err.message || "Cập nhật ghi chú thất bại.", "error");
    } finally {
      setDescriptionId(null);
      setDescriptionValue("");
    }
  };

  const handleToggleVisibility = async (id: string) => {
    try {
      await toggleArchiveVisibilityAPI(id);
      showToast("Đã cập nhật trạng thái hiển thị thành công.", "success");
      fetchArchive();
    } catch (err: any) {
      showToast(err.message || "Cập nhật hiển thị thất bại.", "error");
    }
  };

  const handleShare = async () => {
    if (!shareId || !shareEmail.trim()) return;
    try {
      await shareArchiveAPI(shareId, shareEmail.trim());
      showToast(`Đã chia sẻ tệp tin thành công tới ${shareEmail}.`, "success");
      fetchArchive();
    } catch (err: any) {
      showToast(err.message || "Chia sẻ tệp tin thất bại.", "error");
    } finally {
      setShareId(null);
      setShareEmail("");
    }
  };

  const handleUpdateTags = async () => {
    if (!tagsId) return;
    try {
      const tagsArray = tagsValue
        .split(",")
        .map((t) => t.trim())
        .filter((t) => t.length > 0);
      await updateArchiveTagsAPI(tagsId, tagsArray);
      showToast("Đã cập nhật nhãn thành công.", "success");
      fetchArchive();
    } catch (err: any) {
      showToast(err.message || "Cập nhật nhãn thất bại.", "error");
    } finally {
      setTagsId(null);
      setTagsValue("");
    }
  };

  const handleCopyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    showToast("Đã sao chép liên kết.", "success");
  };

  const isTextFile = (a: any) => {
    const typeLower = a.type?.toLowerCase() || "";
    const nameLower = a.filename?.toLowerCase() || "";
    return (
      typeLower.includes("text") ||
      typeLower.includes("json") ||
      typeLower.includes("javascript") ||
      nameLower.endsWith(".txt") ||
      nameLower.endsWith(".md") ||
      nameLower.endsWith(".json") ||
      nameLower.endsWith(".csv")
    );
  };

  const handleCopyTextContent = async (url: string) => {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error("Không thể tải tệp tin từ máy chủ");
      const text = await res.text();
      await navigator.clipboard.writeText(text);
      showToast("Đã sao chép nội dung văn bản thành công.", "success");
    } catch (err: any) {
      showToast("Sao chép nội dung thất bại do giới hạn bảo mật.", "error");
    }
  };

  const formatSize = (bytes: number) => {
    if (!bytes || bytes === 0) return "0 KB";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const matchesDate = (createdAtStr: string) => {
    if (dateFilter === "all") return true;
    const createdAt = new Date(createdAtStr);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - createdAt.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (dateFilter === "today") {
      return diffDays <= 1 || createdAt.toDateString() === now.toDateString();
    }
    if (dateFilter === "week") {
      return diffDays <= 7;
    }
    if (dateFilter === "month") {
      return diffDays <= 30;
    }
    return true;
  };

  const matchesSize = (size: number) => {
    if (sizeFilter === "all") return true;
    if (sizeFilter === "small") return size < 1 * 1024 * 1024;
    if (sizeFilter === "medium") return size >= 1 * 1024 * 1024 && size <= 10 * 1024 * 1024;
    if (sizeFilter === "large") return size > 10 * 1024 * 1024;
    return true;
  };

  const isOwner = (a: any) => {
    if (!profile) return true;
    const myId = profile._id || profile.id;
    return a.author_id === myId;
  };

  const filteredFiles = files.filter((a) => {
    const matchesSearch =
      a.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.tags?.some((t: string) => t.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const dateOk = matchesDate(a.created_at);
    const sizeOk = matchesSize(a.size_bytes || 0);

    if (selectedCategory === "all" || selectedCategory === "trash") {
      return matchesSearch && dateOk && sizeOk;
    }
    if (selectedCategory === "image") {
      return matchesSearch && dateOk && sizeOk && a.type?.toLowerCase().includes("image");
    }
    if (selectedCategory === "document") {
      const typeLower = a.type?.toLowerCase() || "";
      const isDoc =
        typeLower.includes("pdf") ||
        typeLower.includes("epub") ||
        typeLower.includes("text") ||
        typeLower.includes("document") ||
        typeLower.includes("word") ||
        typeLower.includes("sheet") ||
        typeLower.includes("office");
      return matchesSearch && dateOk && sizeOk && isDoc;
    }
    if (selectedCategory === "other") {
      const typeLower = a.type?.toLowerCase() || "";
      const isImg = typeLower.includes("image");
      const isDoc =
        typeLower.includes("pdf") ||
        typeLower.includes("epub") ||
        typeLower.includes("text") ||
        typeLower.includes("document") ||
        typeLower.includes("word") ||
        typeLower.includes("sheet") ||
        typeLower.includes("office");
      return matchesSearch && dateOk && sizeOk && !isImg && !isDoc;
    }
    return matchesSearch && dateOk && sizeOk;
  });

  const activeFiles = files.filter(f => !f.is_deleted);
  const imageCount = activeFiles.filter(f => f.type?.toLowerCase().includes("image")).length;
  const docCount = activeFiles.filter(f => {
    const typeLower = f.type?.toLowerCase() || "";
    return typeLower.includes("pdf") || typeLower.includes("epub") || typeLower.includes("text") || typeLower.includes("document") || typeLower.includes("word") || typeLower.includes("sheet") || typeLower.includes("office");
  }).length;
  const otherCount = activeFiles.length - imageCount - docCount;

  const imagePercent = activeFiles.length ? (imageCount / activeFiles.length) * 100 : 0;
  const docPercent = activeFiles.length ? (docCount / activeFiles.length) * 100 : 0;
  const otherPercent = activeFiles.length ? (otherCount / activeFiles.length) * 100 : 0;

  const totalSize = files.reduce((acc, f) => acc + (f.size_bytes || 0), 0);
  const storageLimit = 500 * 1024 * 1024;
  const storagePercentage = Math.min((totalSize / storageLimit) * 100, 100);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white font-sans text-black">
      <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12">
        <header className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl font-semibold text-black">Kho lưu trữ</h1>
            <p className="text-sm text-zinc-500 mt-1">Quản lý hình ảnh và tệp tin đính kèm cho sáng tác</p>
          </div>
          <div className="flex flex-col md:flex-row items-start md:items-end gap-6">
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 border border-zinc-200 px-3 py-1.5 rounded-none bg-zinc-50 text-xs font-mono text-zinc-600">
                <HardDrive className="w-3.5 h-3.5" />
                <span>Đã sử dụng: {formatSize(totalSize)} / 500 MB</span>
              </div>
              <div className="w-48 h-1 bg-zinc-100 border border-zinc-200">
                <div 
                  className="h-full bg-black" 
                  style={{ width: `${storagePercentage}%` }} 
                />
              </div>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={fetchArchive}
                disabled={loading || uploading}
                className="text-sm font-medium text-zinc-500 disabled:opacity-50"
              >
                Đồng bộ dữ liệu
              </button>
            </div>
          </div>
        </header>

        {activeFiles.length > 0 && (
          <div className="mb-6 border border-zinc-200 p-4 bg-zinc-50">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Phân phối định dạng tệp tin</span>
              <div className="flex gap-4 text-[10px] font-mono text-zinc-400">
                <span>Hình ảnh: {imageCount}</span>
                <span>Tài liệu: {docCount}</span>
                <span>Khác: {otherCount}</span>
              </div>
            </div>
            <div className="w-full h-2 bg-zinc-200 flex rounded-none overflow-hidden">
              <div className="h-full bg-black" style={{ width: `${imagePercent}%` }} />
              <div className="h-full bg-zinc-500" style={{ width: `${docPercent}%` }} />
              <div className="h-full bg-zinc-300" style={{ width: `${otherPercent}%` }} />
            </div>
          </div>
        )}

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`mb-8 border border-zinc-200 p-12 text-center ${
            isDragging ? "bg-zinc-50 border-black" : "bg-white"
          }`}
        >
          {uploading ? (
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-black" />
              <p className="text-sm font-medium text-zinc-500">Đang xử lý tệp tin</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4">
              <p className="text-sm font-medium text-zinc-600">Kéo thả tệp tin vào khu vực này, hoặc</p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-6 py-2 bg-black text-white text-xs font-semibold uppercase tracking-wider border border-black"
              >
                Tải lên tệp đính kèm
              </button>
            </div>
          )}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
            multiple
          />
        </div>

        <div className="flex flex-wrap gap-2 mb-6 border-b border-zinc-200 pb-4">
          <button
            onClick={() => setSelectedCategory("all")}
            className={`px-4 py-2 text-xs font-semibold uppercase tracking-wider border ${
              selectedCategory === "all"
                ? "bg-black text-white border-black"
                : "bg-white text-zinc-500 border-zinc-200"
            }`}
          >
            Tất cả
          </button>
          <button
            onClick={() => setSelectedCategory("image")}
            className={`px-4 py-2 text-xs font-semibold uppercase tracking-wider border ${
              selectedCategory === "image"
                ? "bg-black text-white border-black"
                : "bg-white text-zinc-500 border-zinc-200"
            }`}
          >
            Hình ảnh
          </button>
          <button
            onClick={() => setSelectedCategory("document")}
            className={`px-4 py-2 text-xs font-semibold uppercase tracking-wider border ${
              selectedCategory === "document"
                ? "bg-black text-white border-black"
                : "bg-white text-zinc-500 border-zinc-200"
            }`}
          >
            Tài liệu
          </button>
          <button
            onClick={() => setSelectedCategory("other")}
            className={`px-4 py-2 text-xs font-semibold uppercase tracking-wider border ${
              selectedCategory === "other"
                ? "bg-black text-white border-black"
                : "bg-white text-zinc-500 border-zinc-200"
            }`}
          >
            Khác
          </button>
          <button
            onClick={() => setSelectedCategory("trash")}
            className={`px-4 py-2 text-xs font-semibold uppercase tracking-wider border ${
              selectedCategory === "trash"
                ? "bg-black text-white border-black"
                : "bg-white text-zinc-500 border-zinc-200"
            }`}
          >
            Thùng rác
          </button>
        </div>

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-6">
          <div className="relative w-full lg:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <input
              type="text"
              placeholder="Tìm kiếm theo tên, mô tả hoặc nhãn"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full border border-zinc-200 pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-black rounded-none bg-white placeholder:text-zinc-400 font-sans"
            />
          </div>
          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Thời gian</label>
              <select
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="border border-zinc-200 px-3 py-2 text-sm focus:outline-none focus:border-black rounded-none bg-white text-zinc-600 font-sans"
              >
                <option value="all">Tất cả thời gian</option>
                <option value="today">Hôm nay</option>
                <option value="week">7 ngày qua</option>
                <option value="month">30 ngày qua</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Kích thước</label>
              <select
                value={sizeFilter}
                onChange={(e) => setSizeFilter(e.target.value)}
                className="border border-zinc-200 px-3 py-2 text-sm focus:outline-none focus:border-black rounded-none bg-white text-zinc-600 font-sans"
              >
                <option value="all">Tất cả kích thước</option>
                <option value="small">Nhỏ (&lt; 1 MB)</option>
                <option value="medium">Trung bình (1 MB - 10 MB)</option>
                <option value="large">Lớn (&gt; 10 MB)</option>
              </select>
            </div>
            <div className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
              {filteredFiles.length} TỆP TIN
            </div>
          </div>
        </div>

        <div className="border border-zinc-200 bg-white overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[900px]">
            <thead>
              <tr className="border-b border-zinc-200 bg-zinc-50">
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600 w-12"></th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Tên tập tin</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Định dạng / Quyền</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Kích thước</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Ngày tải lên</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {filteredFiles.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-24 text-center">
                    <p className="text-sm font-medium text-zinc-500">Thư viện ảnh và tệp đính kèm hiện đang trống</p>
                  </td>
                </tr>
              ) : (
                filteredFiles.map((a: any) => (
                  <tr key={a._id || a.id} className="border-b border-zinc-200 last:border-0">
                    <td className="py-4 px-6 align-middle">
                      <div className="w-8 h-8 bg-zinc-100 flex items-center justify-center rounded-none">
                        {a.type && a.type.includes("image") ? (
                          <ImageIcon className="w-4 h-4 text-zinc-500" />
                        ) : (
                          <FileText className="w-4 h-4 text-zinc-500" />
                        )}
                      </div>
                    </td>
                    <td className="py-4 px-6 align-middle">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          {a.is_pinned && (
                            <Pin className="w-3.5 h-3.5 text-black flex-shrink-0" />
                          )}
                          <span className="text-sm font-semibold text-black truncate max-w-xs block">
                            {a.filename}
                          </span>
                        </div>
                        {profile && a.author_id !== (profile._id || profile.id) && (
                          <span className="text-[10px] text-zinc-400 font-mono italic">
                            Chia sẻ bởi: {a.owner_email || "Người dùng khác"}
                          </span>
                        )}
                        {a.description ? (
                          <span className="text-xs text-zinc-400 font-mono">
                            {a.description}
                          </span>
                        ) : (
                          isOwner(a) && (
                            <button
                              onClick={() => {
                                setDescriptionId(a._id || a.id);
                                setDescriptionValue("");
                              }}
                              className="text-left text-xs text-zinc-400 underline underline-offset-2 cursor-pointer font-sans"
                            >
                              Thêm ghi chú
                            </button>
                          )
                        )}
                        {a.tags && a.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {a.tags.map((t: string) => (
                              <span key={t} className="text-[9px] font-mono bg-zinc-100 border border-zinc-200 text-zinc-500 px-1.5 py-0.5">
                                {t}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="py-4 px-6 align-middle whitespace-nowrap">
                      <div className="flex flex-col gap-1">
                        <span className="text-xs font-medium text-zinc-500 uppercase tracking-wider bg-zinc-100 px-2 py-1 w-max">
                          {a.type || "UNKNOWN"}
                        </span>
                        <span className="text-[10px] font-mono text-zinc-400">
                          {a.is_public ? "Công khai" : "Riêng tư"}
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-6 align-middle whitespace-nowrap">
                      <span className="text-sm font-mono text-black">
                        {formatSize(a.size_bytes)}
                      </span>
                    </td>
                    <td className="py-4 px-6 align-middle whitespace-nowrap">
                      <span className="text-xs font-medium text-zinc-500">
                        {new Date(a.created_at || Date.now()).toLocaleDateString("vi-VN")}
                      </span>
                    </td>
                    <td className="py-4 px-6 align-middle text-right whitespace-nowrap">
                      <div className="flex justify-end gap-4">
                        {selectedCategory === "trash" ? (
                          <>
                            <button
                              onClick={() => handleRestore(a._id || a.id)}
                              className="text-xs font-semibold text-black underline underline-offset-4"
                            >
                              Khôi phục
                            </button>
                            <button
                              onClick={() => setPermanentDeleteId(a._id || a.id)}
                              className="text-xs font-semibold text-zinc-500"
                            >
                              Xóa vĩnh viễn
                            </button>
                          </>
                        ) : (
                          <>
                            {isTextFile(a) && (
                              <button
                                onClick={() => handleCopyTextContent(a.url)}
                                className="text-xs font-semibold text-zinc-500"
                              >
                                Sao chép nội dung
                              </button>
                            )}
                            <button
                              onClick={() => {
                                setPreviewUrl(a.url);
                                setPreviewType(a.type || "");
                                setPreviewName(a.filename);
                              }}
                              className="text-xs font-semibold text-zinc-500"
                            >
                              Xem
                            </button>
                            {isOwner(a) && (
                              <>
                                <button
                                  onClick={() => {
                                    setShareId(a._id || a.id);
                                    setShareEmail("");
                                  }}
                                  className="text-xs font-semibold text-zinc-500"
                                >
                                  Chia sẻ
                                </button>
                                <button
                                  onClick={() => {
                                    setTagsId(a._id || a.id);
                                    setTagsValue(a.tags?.join(", ") || "");
                                  }}
                                  className="text-xs font-semibold text-zinc-500"
                                >
                                  Nhãn
                                </button>
                                <button
                                  onClick={() => {
                                    setDescriptionId(a._id || a.id);
                                    setDescriptionValue(a.description || "");
                                  }}
                                  className="text-xs font-semibold text-zinc-500"
                                >
                                  Ghi chú
                                </button>
                                <button
                                  onClick={() => handleToggleVisibility(a._id || a.id)}
                                  className="text-xs font-semibold text-zinc-500"
                                >
                                  {a.is_public ? "Khóa" : "Mở khóa"}
                                </button>
                                <button
                                  onClick={() => {
                                    setRenameId(a._id || a.id);
                                    setRenameValue(a.filename);
                                  }}
                                  className="text-xs font-semibold text-zinc-500"
                                >
                                  Đổi tên
                                </button>
                                <button
                                  onClick={() => handleTogglePin(a._id || a.id)}
                                  className="text-xs font-semibold text-zinc-500"
                                >
                                  {a.is_pinned ? "Bỏ ghim" : "Ghim"}
                                </button>
                              </>
                            )}
                            <button
                              onClick={() => handleCopyUrl(a.url)}
                              className="text-xs font-semibold text-zinc-500"
                            >
                              Sao chép link
                            </button>
                            <a
                              href={a.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs font-semibold text-zinc-500"
                            >
                              Tải xuống
                            </a>
                            {isOwner(a) && (
                              <button
                                onClick={() => setDeleteId(a._id || a.id)}
                                className="text-xs font-semibold text-black underline underline-offset-4"
                              >
                                Xóa
                              </button>
                            )}
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
      </div>

      <Modal isOpen={!!deleteId} onClose={() => setDeleteId(null)} className="max-w-md">
        <ModalHeader>
          <ModalTitle>Di chuyển tệp đính kèm vào thùng rác</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs font-medium text-zinc-500 leading-relaxed font-sans">
            Bạn có chắc chắn muốn di chuyển tệp đính kèm này vào thùng rác? Bạn có thể khôi phục lại từ mục thùng rác bất cứ lúc nào.
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setDeleteId(null)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={handleDelete}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black flex items-center justify-center"
          >
            Di chuyển vào thùng rác
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!permanentDeleteId} onClose={() => setPermanentDeleteId(null)} className="max-w-md">
        <ModalHeader>
          <ModalTitle>Xác nhận xóa vĩnh viễn</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs font-medium text-zinc-500 leading-relaxed font-sans">
            Hành động này sẽ xóa vĩnh viễn tệp đính kèm ra khỏi hệ thống và không thể khôi phục lại. Bạn có chắc chắn muốn tiếp tục?
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setPermanentDeleteId(null)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={handlePermanentDelete}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black flex items-center justify-center"
          >
            Xóa vĩnh viễn
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!renameId} onClose={() => setRenameId(null)} className="max-w-md">
        <ModalHeader>
          <ModalTitle>Đổi tên tệp tin</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold text-zinc-600 uppercase tracking-wider">Tên mới</label>
            <input
              type="text"
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              className="w-full border border-zinc-200 px-3 py-2 text-sm focus:outline-none focus:border-black rounded-none bg-white placeholder:text-zinc-400 font-sans"
            />
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setRenameId(null)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={handleRename}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black flex items-center justify-center"
          >
            Lưu thay đổi
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!descriptionId} onClose={() => setDescriptionId(null)} className="max-w-md">
        <ModalHeader>
          <ModalTitle>Ghi chú tệp tin</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold text-zinc-600 uppercase tracking-wider">Mô tả chi tiết</label>
            <textarea
              value={descriptionValue}
              onChange={(e) => setDescriptionValue(e.target.value)}
              rows={3}
              placeholder="Thêm mô tả cho tệp tin này"
              className="w-full border border-zinc-200 px-3 py-2 text-sm focus:outline-none focus:border-black rounded-none bg-white placeholder:text-zinc-400 resize-none font-sans"
            />
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setDescriptionId(null)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={handleUpdateDescription}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black flex items-center justify-center"
          >
            Lưu ghi chú
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!shareId} onClose={() => setShareId(null)} className="max-w-md">
        <ModalHeader>
          <ModalTitle>Chia sẻ tệp tin</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold text-zinc-600 uppercase tracking-wider">Email người nhận</label>
            <input
              type="email"
              value={shareEmail}
              onChange={(e) => setShareEmail(e.target.value)}
              placeholder="nhan-vien@doclib.vn"
              className="w-full border border-zinc-200 px-3 py-2 text-sm focus:outline-none focus:border-black rounded-none bg-white placeholder:text-zinc-400 font-sans"
            />
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setShareId(null)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={handleShare}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black flex items-center justify-center"
          >
            Chia sẻ
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!tagsId} onClose={() => setTagsId(null)} className="max-w-md">
        <ModalHeader>
          <ModalTitle>Nhãn phân loại</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold text-zinc-600 uppercase tracking-wider">Danh sách nhãn</label>
            <input
              type="text"
              value={tagsValue}
              onChange={(e) => setTagsValue(e.target.value)}
              placeholder="Ví dụ: Quan trọng, Chương 1, Bản nháp (phân cách bằng dấu phẩy)"
              className="w-full border border-zinc-200 px-3 py-2 text-sm focus:outline-none focus:border-black rounded-none bg-white placeholder:text-zinc-400 font-sans"
            />
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setTagsId(null)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={handleUpdateTags}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black flex items-center justify-center"
          >
            Lưu nhãn
          </button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={!!previewUrl} onClose={() => setPreviewUrl(null)} className="max-w-3xl">
        <ModalHeader>
          <ModalTitle>{previewName}</ModalTitle>
        </ModalHeader>
        <ModalContent className="flex items-center justify-center min-h-[300px] bg-zinc-50 border border-zinc-200 p-6">
          {previewType.includes("image") ? (
            <img
              src={previewUrl || ""}
              alt={previewName}
              className="max-h-[500px] max-w-full object-contain border border-zinc-200"
            />
          ) : (
            <div className="text-center p-8">
              <FileText className="w-12 h-12 text-zinc-400 mx-auto mb-4" />
              <p className="text-sm font-semibold text-black">Định dạng tệp tin: {previewType}</p>
              <p className="text-xs text-zinc-500 mt-2">Hệ thống chưa hỗ trợ xem trước định dạng này, vui lòng tải xuống để xem chi tiết</p>
            </div>
          )}
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setPreviewUrl(null)}
            className="w-full py-2 bg-black text-white text-xs font-medium border border-black flex items-center justify-center"
          >
            Đóng
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
