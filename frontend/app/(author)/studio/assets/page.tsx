"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { 
  getAuthorAssetsAPI, 
  deleteAuthorAssetAPI, 
  uploadAuthorAssetAPI,
  uploadDocumentFile,
  getFileDownloadUrl
} from "@/app/lib/api";
import { 
  FolderOpen, 
  Trash2, 
  Loader2, 
  Image as ImageIcon,
  FileText,
  Search,
  Download,
  Plus,
  Sparkles,
  X
} from "lucide-react";
import { Notification } from "@/app/components/NotificationToast";

export default function AuthorAssetsPage() {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchAssets = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAuthorAssetsAPI();
      setAssets(data.data || data || []);
    } catch (err: any) {
      console.error("Lỗi tải tài nguyên:", err);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

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
        url: url
      });

      setNotification({ type: "success", text: "Đã tải lên và đăng ký tài nguyên thành công." });
      fetchAssets();
    } catch (err: any) {
      setNotification({ type: "error", text: err.message || "Tải lên tài nguyên thất bại." });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDelete = async (assetId: string) => {
    if (!confirm("Bạn có chắc muốn xóa tài nguyên này vĩnh viễn?")) return;
    try {
      await deleteAuthorAssetAPI(assetId);
      setNotification({ type: "success", text: "Đã xóa tài nguyên thành công." });
      fetchAssets();
    } catch (err: any) {
      setNotification({ type: "error", text: err.message || "Xóa tài nguyên thất bại." });
    }
  };

  const filteredAssets = assets.filter(a => 
    a.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (a.type && a.type.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      {notification && (
        <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      <div 
        className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
              Kho lưu trữ
            </h1>
            <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
              Quản trị tài nguyên & Tệp tin <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
            </p>
          </div>
          <div className="flex items-center gap-4">
             <div className="hidden md:flex items-center gap-3 px-6 py-3 bg-zinc-50 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-400 rounded-sm">
                <FolderOpen className="w-4 h-4" /> Thư viện tri thức cá nhân
             </div>
             <button 
               onClick={() => fileInputRef.current?.click()}
               disabled={uploading}
               className="h-14 px-12 bg-black text-white text-[11px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all active:scale-95 flex items-center gap-4 rounded-sm disabled:opacity-50"
             >
               {uploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
               {uploading ? "Đang tải lên" : "Tải tệp mới"}
             </button>
             <input 
               type="file" 
               ref={fileInputRef} 
               onChange={handleFileUpload} 
               className="hidden" 
             />
          </div>
        </div>
      </div>

      <div 
        className="mb-10 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <div className="flex items-center gap-4">
           <div className="relative w-full max-w-2xl">
              <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-300" />
              <input
                type="text"
                placeholder="TÌM KIẾM TẬP TIN TRONG KHO LƯU TRỮ..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-16 pl-16 pr-8 border border-zinc-100 bg-white text-lg font-bold tracking-tight focus:outline-none focus:border-black transition-all rounded-sm placeholder:text-zinc-100"
              />
              {searchTerm && (
                <button 
                  onClick={() => setSearchTerm("")}
                  className="absolute right-6 top-1/2 -translate-y-1/2 text-zinc-300 hover:text-black transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
           </div>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-zinc-50 border border-zinc-100 h-24 animate-pulse rounded-sm" />
          ))}
        </div>
      ) : filteredAssets.length > 0 ? (
        <div 
          className="grid gap-4 transition-all duration-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {filteredAssets.map((a: any) => (
            <div
              key={a.id}
              className="flex items-center justify-between p-8 border border-zinc-100 bg-white hover:border-black transition-all duration-300 group rounded-sm"
            >
              <div className="flex items-center gap-8 min-w-0">
                <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 flex items-center justify-center shrink-0 group-hover:bg-black group-hover:border-black transition-all duration-300 rounded-sm">
                  {a.type && a.type.includes("image") ? (
                    <ImageIcon className="w-6 h-6 text-zinc-200 group-hover:text-white transition-all" />
                  ) : (
                    <FileText className="w-6 h-6 text-zinc-200 group-hover:text-white transition-all" />
                  )}
                </div>
                <div className="min-w-0 flex flex-col space-y-2">
                  <span className="text-xl font-bold text-black truncate tracking-tight group-hover:translate-x-1 transition-transform duration-300">{a.filename}</span>
                  <div className="flex items-center gap-6 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                    <span className="text-black bg-zinc-50 px-2 py-0.5 rounded-sm">{a.type || "Tập tin"}</span>
                    <div className="w-1.5 h-1.5 bg-zinc-100 rounded-full" />
                    <span>
                      {a.size_bytes > 0 ? `${(a.size_bytes / 1024).toFixed(1)} KB` : "0 KB"}
                    </span>
                    <div className="w-1.5 h-1.5 bg-zinc-100 rounded-full" />
                    <span>Đã tải lên {new Date(a.created_at || Date.now()).toLocaleDateString("vi-VN")}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <a 
                  href={a.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="w-14 h-14 flex items-center justify-center text-zinc-200 hover:text-black hover:bg-zinc-50 transition-all active:scale-95 group/down rounded-sm"
                >
                  <Download className="w-5 h-5 group-hover/down:translate-y-0.5 transition-transform" />
                </a>
                <button
                  onClick={() => handleDelete(a.id)}
                  className="w-14 h-14 flex items-center justify-center text-zinc-200 hover:text-red-500 hover:bg-red-50/30 transition-all active:scale-95 group/trash rounded-sm"
                >
                  <Trash2 className="w-5 h-5 group-hover/trash:scale-110 transition-transform" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-48 text-center border border-dashed border-zinc-200 bg-zinc-50/20 rounded-sm">
          <FolderOpen className="w-16 h-16 text-zinc-100 mx-auto mb-10 stroke-[1]" />
          <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">
            {searchTerm ? "Không tìm thấy tập tin phù hợp" : "Kho tài nguyên hiện đang trống"}
          </p>
        </div>
      )}
    </div>
  );
}
