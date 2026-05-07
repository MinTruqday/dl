"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  getAuthorAssetsAPI,
  deleteAuthorAssetAPI,
  uploadAuthorAssetAPI,
} from "@/services/asset.service";
import {
  uploadDocumentFile,
  getFileDownloadUrl,
} from "@/services/storage.service";
import {
  Loader2,
  Image as ImageIcon,
  FileText,
  Search,
} from "lucide-react";
import { useToast } from "@/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";

export default function AuthorAssetsPage() {
  const { showToast } = useToast();
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const fetchAssets = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAuthorAssetsAPI();
      setAssets(data.data || data || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách tài nguyên", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  const processFileUpload = async (file: File) => {
    setUploading(true);
    try {
      const storageData = await uploadDocumentFile(file);
      const filePath = storageData.file_path;

      const downloadUrlData = await getFileDownloadUrl(filePath);
      const url = downloadUrlData;

      await uploadAuthorAssetAPI({
        filename: file.name,
        type: file.type,
        size_bytes: file.size,
        url: url,
      });

      showToast("Đã tải lên và đăng ký tài nguyên thành công.", "success");
      fetchAssets();
    } catch (err: any) {
      showToast(err.message || "Tải lên tài nguyên thất bại.", "error");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await processFileUpload(file);
    }
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
    const file = e.dataTransfer.files?.[0];
    if (file) {
      await processFileUpload(file);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await deleteAuthorAssetAPI(deleteId);
      showToast("Đã xóa tài nguyên thành công.", "success");
      fetchAssets();
    } catch (err: any) {
      showToast(err.message || "Xóa tài nguyên thất bại.", "error");
    } finally {
      setDeleteId(null);
    }
  };

  const handleCopyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    showToast("Đã sao chép liên kết.", "success");
  };

  const formatSize = (bytes: number) => {
    if (!bytes || bytes === 0) return "0 KB";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const filteredAssets = assets.filter(
    (a) =>
      a.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.type?.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
            <p className="text-sm text-zinc-500 mt-1">Quản lý tài nguyên và tệp tin đa phương tiện</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={fetchAssets}
              disabled={loading || uploading}
              className="text-sm font-medium text-zinc-500 disabled:opacity-50"
            >
              Đồng bộ dữ liệu
            </button>
          </div>
        </header>

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
                Tải lên tài nguyên
              </button>
            </div>
          )}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
          />
        </div>

        <div className="flex items-center justify-between gap-6 mb-6">
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <input
              type="text"
              placeholder="Tìm kiếm tài nguyên"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full border border-zinc-200 pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-black rounded-none bg-white placeholder:text-zinc-400"
            />
          </div>
          <div className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
            {filteredAssets.length} TỆP TIN
          </div>
        </div>

        <div className="border border-zinc-200 bg-white overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[800px]">
            <thead>
              <tr className="border-b border-zinc-200 bg-zinc-50">
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600 w-12"></th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Tên tập tin</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Định dạng</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Kích thước</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Ngày tải lên</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {filteredAssets.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-24 text-center">
                    <p className="text-sm font-medium text-zinc-500">Kho tài nguyên hiện đang trống</p>
                  </td>
                </tr>
              ) : (
                filteredAssets.map((a: any) => (
                  <tr key={a.id} className="border-b border-zinc-200 last:border-0">
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
                      <span className="text-sm font-semibold text-black truncate max-w-xs block">
                        {a.filename}
                      </span>
                    </td>
                    <td className="py-4 px-6 align-middle whitespace-nowrap">
                      <span className="text-xs font-medium text-zinc-500 uppercase tracking-wider bg-zinc-100 px-2 py-1">
                        {a.type || "UNKNOWN"}
                      </span>
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
                        <button
                          onClick={() => setDeleteId(a.id)}
                          className="text-xs font-semibold text-black underline underline-offset-4"
                        >
                          Xóa
                        </button>
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
          <ModalTitle>Xác nhận xóa tài nguyên</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs font-medium text-zinc-500 leading-relaxed">
            Bạn có chắc chắn muốn xóa tài nguyên này vĩnh viễn? Hành động này không thể hoàn tác.
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
            Xác nhận xóa
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
