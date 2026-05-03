"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { 
  getDocumentsAPI, 
  getMyDocumentsAPI, 
  uploadDocumentAPI, 
  createDocumentAPI, 
  deleteAuthorDocumentAPI, 
  deleteAdminDocumentAPI,
  getFoldersAPI,
  createFolderAPI,
  deleteFolderAPI,
  lockDocumentAPI,
  toggleStarDocumentAPI
} from "@/services/document.service";
import { API_URL } from "@/services/auth.service";
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
  Sparkles,
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
  ChevronDown,
  MoreVertical,
  ArrowRight
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import Workspace from "@/components/Workspace";
import { 
  Modal, 
  ModalHeader, 
  ModalTitle, 
  ModalDescription, 
  ModalContent, 
  ModalFooter 
} from "@/components/ui/Modal";

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

  const [confirmModal, setConfirmModal] = useState<{ show: boolean; title: string; docId: string; type: "doc" | "folder" } | null>(null);
  const [createDocModal, setCreateDocModal] = useState(false);
  const [createFolderModal, setCreateFolderModal] = useState(false);
  const [lockModal, setLockModal] = useState<{ show: boolean; docId: string } | null>(null);
  const [shareModal, setShareModal] = useState<{ show: boolean; docId: string } | null>(null);

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
    is_protected: false
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

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [docsData, foldersData] = await Promise.all([
        isAdmin ? getDocumentsAPI(searchQuery, undefined, undefined, undefined, currentFolder?._id, filterStar, filterFormat) : getMyDocumentsAPI(),
        getFoldersAPI(currentFolder?._id)
      ]);
      
      let docs = docsData.data || docsData || [];
      if (!isAdmin) {
        if (currentFolder) {
          docs = docs.filter((d: any) => d.folder_id === currentFolder._id);
        } else {
          docs = docs.filter((d: any) => !d.folder_id);
        }
        
        if (filterStar) docs = docs.filter((d: any) => d.is_starred);
        if (filterFormat !== "all") docs = docs.filter((d: any) => d.file_url?.toLowerCase().endsWith(filterFormat));
        if (searchQuery) {
          docs = docs.filter((d: any) => 
            d.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
            (d.publisher_name || "").toLowerCase().includes(searchQuery.toLowerCase())
          );
        }
      }
      
      setDocuments(docs);
      setFolders(foldersData.data || foldersData || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách tri thức", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [isAdmin, searchQuery, currentFolder, filterStar, filterFormat, showToast]);

  useEffect(() => {
    if (!authLoading && user) {
      fetchData();
      setNewDoc(prev => ({ 
        ...prev, 
        publisher_name: isAdmin ? "DocLib" : (user.full_name || "") 
      }));
    }
  }, [user, authLoading, fetchData, isAdmin]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (!newDoc.title) {
        const name = selectedFile.name.split(".")[0];
        setNewDoc(prev => ({ 
          ...prev, 
          title: name, 
          slug: name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "") 
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
        const uploadRes = await uploadDocumentAPI(file);
        const file_url = uploadRes.data.url;

        const submissionData = {
          ...newDoc,
          file_url,
          folder_id: currentFolder?._id || null,
          slug: newDoc.slug || newDoc.title.toLowerCase().replace(/\s+/g, "-") + "-" + Date.now().toString().slice(-4),
          publish_at: newDoc.status === 'scheduled' ? newDoc.publish_at : null
        };

        await createDocumentAPI(submissionData);
        showToast("Đã khởi tạo tài liệu thành công", "success");
        setCreateDocModal(false);
        setNewDoc({ 
          title: "", 
          description: "", 
          slug: "", 
          category: "Chưa phân loại", 
          pages_count: 0, 
          publisher_name: isAdmin ? "DocLib" : (user?.full_name || ""), 
          price_dl: 0, 
          visibility: "public", 
          status: "published", 
          publish_at: "", 
          is_featured: false, 
          is_protected: false 
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
    setPublicUrl(`${window.location.origin}/documents/viewer/${shareModal.docId}${sharePassword ? `?pwd=${sharePassword}` : ""}`);
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
      <div className="flex h-[80vh] items-center justify-center bg-white">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  return (
    <Workspace>
      <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
        
        {/* Modals - Keep existing logic */}
        <Modal isOpen={!!confirmModal} onClose={() => setConfirmModal(null)}>
          <ModalHeader>
            <div className="flex items-center gap-6">
              <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-sm">
                <AlertTriangle className="w-5 h-5 text-black" />
              </div>
              <div>
                <ModalTitle>{confirmModal?.title}</ModalTitle>
                <ModalDescription>Hành động này sẽ xóa vĩnh viễn dữ liệu khỏi hệ thống</ModalDescription>
              </div>
            </div>
          </ModalHeader>
          <ModalFooter className="flex gap-4">
            <button
              onClick={() => setConfirmModal(null)}
              className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black hover:border-black transition-all rounded-sm"
            >
              Hủy bỏ
            </button>
            <button
              onClick={executeDelete}
              className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-[0.98] rounded-sm"
            >
              Xác nhận
            </button>
          </ModalFooter>
        </Modal>

        <Modal isOpen={createDocModal} onClose={() => setCreateDocModal(false)} className="max-w-4xl">
          <ModalHeader>
            <ModalTitle>{isAdmin ? "Thêm tài liệu hệ thống" : "Khởi tạo tri thức mới"}</ModalTitle>
            <ModalDescription>Điền thông tin để bắt đầu quá trình lưu trữ chuyên sâu</ModalDescription>
          </ModalHeader>
          <ModalContent className="grid md:grid-cols-2 gap-12 pt-6">
            <div className="space-y-8">
              <div className="space-y-3">
                <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Tiêu đề tài liệu</label>
                <input 
                  type="text" 
                  value={newDoc.title}
                  onChange={(e) => setNewDoc({...newDoc, title: e.target.value})}
                  className="w-full h-14 border-b border-zinc-100 focus:border-black outline-none font-bold text-lg transition-all placeholder:text-zinc-100" 
                />
              </div>
              <div className="grid grid-cols-2 gap-8">
                <div className="space-y-3">
                  <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Thể loại</label>
                  <select 
                    value={newDoc.category}
                    onChange={(e) => setNewDoc({...newDoc, category: e.target.value})}
                    className="w-full h-12 border-b border-zinc-100 focus:border-black outline-none font-bold uppercase tracking-widest text-[10px] transition-all bg-transparent"
                  >
                    <option value="Chưa phân loại">Chưa phân loại</option>
                    <option value="Giáo trình">Giáo trình</option>
                    <option value="Kỹ thuật">Kỹ thuật</option>
                    <option value="Nghiên cứu">Nghiên cứu</option>
                  </select>
                </div>
                <div className="space-y-3">
                  <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Giá (dl)</label>
                  <input 
                    type="number" 
                    className="w-full h-12 border-b border-zinc-100 focus:border-black outline-none font-bold text-base transition-all"
                    value={newDoc.price_dl}
                    onChange={(e) => setNewDoc({ ...newDoc, price_dl: parseInt(e.target.value) || 0 })}
                  />
                </div>
              </div>
              <div className="space-y-3">
                <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Mô tả tóm lược</label>
                <textarea 
                  value={newDoc.description}
                  onChange={(e) => setNewDoc({...newDoc, description: e.target.value})}
                  className="w-full h-32 border border-zinc-100 p-4 focus:border-black outline-none font-medium text-sm transition-all resize-none rounded-sm leading-relaxed" 
                />
              </div>
            </div>
            <div className="space-y-8">
              <div className="space-y-3">
                <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Thực thể đính kèm</label>
                <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept=".pdf,.epub" />
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className={`border border-zinc-100 p-10 flex flex-col items-center justify-center gap-4 group hover:border-black transition-all cursor-pointer rounded-sm ${file ? 'bg-black text-white' : 'bg-zinc-50/20'}`}
                >
                  <div className={`w-14 h-14 flex items-center justify-center transition-all ${file ? 'bg-white text-black' : 'bg-white text-zinc-100 group-hover:bg-black group-hover:text-white'} rounded-sm`}>
                    {file ? <FileCheck className="w-6 h-6" /> : <Upload className="w-6 h-6" />}
                  </div>
                  <div className="text-center">
                    <p className="text-[10px] font-bold uppercase tracking-widest mb-1 truncate max-w-[200px]">
                      {file ? file.name : "Chọn tệp PDF/EPUB"}
                    </p>
                    <p className={`text-[8px] font-bold uppercase tracking-[0.2em] ${file ? 'text-zinc-500' : 'text-zinc-200'}`}>
                      {file ? `${(file.size / (1024 * 1024)).toFixed(2)} MB` : "Tối đa 50MB"}
                    </p>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-8">
                <div className="space-y-3">
                  <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Hiển thị</label>
                  <select 
                    value={newDoc.visibility}
                    onChange={(e) => setNewDoc({...newDoc, visibility: e.target.value})}
                    className="w-full h-12 border-b border-zinc-100 focus:border-black outline-none font-bold uppercase tracking-widest text-[10px] transition-all bg-transparent"
                  >
                    <option value="public">Công khai</option>
                    <option value="private">Riêng tư</option>
                  </select>
                </div>
                <div className="space-y-3">
                  <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Trạng thái</label>
                  <select 
                    value={newDoc.status}
                    onChange={(e) => setNewDoc({...newDoc, status: e.target.value})}
                    className="w-full h-12 border-b border-zinc-100 focus:border-black outline-none font-bold uppercase tracking-widest text-[10px] transition-all bg-transparent"
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
              onClick={handleCreateDocument}
              disabled={isCreating || !file || !newDoc.title}
              className="w-full h-16 bg-black text-white text-[10px] font-bold uppercase tracking-[0.3em] hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center justify-center gap-4 rounded-sm disabled:opacity-30"
            >
              {isCreating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
              Kích hoạt lưu trữ
            </button>
          </ModalFooter>
        </Modal>

        <Modal isOpen={createFolderModal} onClose={() => setCreateFolderModal(false)}>
          <ModalHeader>
            <ModalTitle>Kiến tạo không gian mới</ModalTitle>
            <ModalDescription>Phân loại tri thức theo cấu trúc thư mục chuyên nghiệp</ModalDescription>
          </ModalHeader>
          <ModalContent>
            <div className="space-y-4">
              <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Tên thư mục</label>
              <input 
                type="text" 
                value={folderName}
                onChange={(e) => setFolderName(e.target.value)}
                autoFocus
                className="w-full h-14 border-b border-zinc-100 focus:border-black outline-none font-bold text-lg transition-all" 
              />
            </div>
          </ModalContent>
          <ModalFooter>
            <button 
              onClick={handleCreateFolder}
              disabled={!folderName}
              className="w-full h-16 bg-black text-white text-[10px] font-bold uppercase tracking-[0.3em] hover:bg-zinc-800 transition-all active:scale-[0.98] rounded-sm disabled:opacity-30"
            >
              Tạo thư mục
            </button>
          </ModalFooter>
        </Modal>

        <Modal isOpen={!!lockModal} onClose={() => setLockModal(null)}>
          <ModalHeader>
            <div className="flex items-center gap-6">
              <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-sm">
                <Lock className="w-5 h-5 text-black" />
              </div>
              <div>
                <ModalTitle>Thiết lập bảo mật</ModalTitle>
                <ModalDescription>Mã hóa đa lớp cho thực thể tri thức</ModalDescription>
              </div>
            </div>
          </ModalHeader>
          <ModalContent>
            <form onSubmit={handleLockDocument} className="space-y-8">
              <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest leading-loose">Mật khẩu sẽ được mã hóa và không thể khôi phục nếu bị thất lạc</p>
              <input 
                type="password" 
                autoFocus
                className="w-full h-16 px-6 bg-zinc-50 border border-zinc-100 text-sm font-bold focus:outline-none focus:border-black focus:bg-white transition-all rounded-sm"
                value={lockPassword}
                onChange={(e) => setLockPassword(e.target.value)}
                required
              />
              <div className="flex gap-4">
                <button type="button" onClick={() => setLockModal(null)} className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black transition-all rounded-sm">Hủy bỏ</button>
                <button type="submit" className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all rounded-sm">Kích hoạt khóa</button>
              </div>
            </form>
          </ModalContent>
        </Modal>

        <Modal isOpen={!!shareModal} onClose={() => setShareModal(null)} className="max-w-2xl">
          <ModalHeader>
            <div className="flex items-center gap-6">
              <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-sm">
                <Globe className="w-5 h-5 text-black" />
              </div>
              <div>
                <ModalTitle>Giao thức chia sẻ</ModalTitle>
                <ModalDescription>Thiết lập quyền truy cập cho cộng đồng</ModalDescription>
              </div>
            </div>
          </ModalHeader>
          <ModalContent className="space-y-10">
            <form onSubmit={handleShareSubmit} className="space-y-8">
              <div className="flex items-center gap-4 bg-zinc-50/50 p-6 rounded-sm border border-zinc-50">
                <input type="checkbox" checked={isPublic} onChange={e => setIsPublic(e.target.checked)} className="w-5 h-5 accent-black cursor-pointer" />
                <label className="text-[10px] font-bold text-black uppercase tracking-widest cursor-pointer">Công khai thực thể tri thức</label>
              </div>
              <div className="grid grid-cols-2 gap-8">
                <div className="space-y-3">
                  <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Mật mã truy cập</label>
                  <input type="password" value={sharePassword} onChange={e=>setSharePassword(e.target.value)} className="w-full h-14 px-4 bg-zinc-50 border border-zinc-100 text-sm font-bold focus:outline-none focus:border-black rounded-sm" />
                </div>
                <div className="space-y-3">
                  <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Thời hạn hiệu lực</label>
                  <select value={shareExpires} onChange={e=>setShareExpires(e.target.value)} className="w-full h-14 px-4 bg-zinc-50 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest focus:outline-none focus:border-black rounded-sm">
                    <option value="1">24 giờ</option>
                    <option value="7">07 ngày</option>
                    <option value="30">30 ngày</option>
                  </select>
                </div>
              </div>
              {publicUrl && (
                <div className="p-10 bg-zinc-50 border border-zinc-100 flex flex-col items-center rounded-sm space-y-8 animate-in fade-in duration-500">
                  <div className="text-[9px] font-bold text-black break-all select-all text-center tracking-widest uppercase bg-white p-4 border border-zinc-100 w-full rounded-sm leading-relaxed">{publicUrl}</div>
                  <div className="p-6 bg-white border border-zinc-100 rounded-sm">
                    <img src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(publicUrl)}`} className="grayscale" alt="QR Code" />
                  </div>
                  <p className="text-[8px] font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-3"><QrCode className="w-4 h-4"/> Quét mã để tiếp cận</p>
                </div>
              )}
              <div className="flex gap-4">
                <button type="button" onClick={() => { setShareModal(null); setPublicUrl(""); }} className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black transition-all rounded-sm">Đóng</button>
                <button type="submit" className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all rounded-sm">Cập nhật giao thức</button>
              </div>
            </form>
          </ModalContent>
        </Modal>

        {/* Header Section */}
        <div 
          className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-300" 
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="space-y-3">
              <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
                Tài liệu & Học liệu
              </h1>
              <p className="text-zinc-400 text-[11px] font-bold uppercase tracking-[0.2em] flex items-center gap-3">
                Kiến tạo không gian tri thức cá nhân hóa <Sparkles className="w-3.5 h-3.5 text-zinc-200" />
              </p>
            </div>
            <div className="flex items-center gap-4">
              <button 
                onClick={() => setCreateFolderModal(true)}
                className="h-16 px-8 border border-zinc-100 text-black text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-50 transition-all active:scale-[0.98] flex items-center gap-3 rounded-sm"
              >
                <FolderPlus className="w-5 h-5" />
                Thư mục
              </button>
              <button 
                onClick={() => setCreateDocModal(true)}
                className="h-16 px-12 bg-black text-white text-[10px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center gap-4 rounded-sm"
              >
                <Plus className="w-5 h-5" />
                Thêm tài liệu
              </button>
            </div>
          </div>
        </div>

        {/* Main Grid Layout */}
        <div className="grid lg:grid-cols-12 gap-12">
          {/* Sidebar Filters */}
          <aside 
            className="lg:col-span-3 space-y-12 transition-all duration-300 delay-75"
            style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
          >
            <div className="space-y-6">
              <div className="flex items-center gap-3 text-[10px] font-bold text-black uppercase tracking-[0.3em] px-1">
                <Search className="w-4 h-4" /> Tìm kiếm tri thức
              </div>
              <div className="relative group">
                <Search className="w-4 h-4 absolute left-5 top-1/2 -translate-y-1/2 text-zinc-200 group-focus-within:text-black transition-colors" />
                <input 
                  type="text"
                  placeholder=""
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full h-14 pl-14 pr-6 bg-white border border-zinc-100 focus:border-black outline-none font-bold text-xs tracking-tight transition-all rounded-sm"
                />
              </div>
            </div>

            <div className="space-y-6">
              <div className="flex items-center gap-3 text-[10px] font-bold text-black uppercase tracking-[0.3em] px-1">
                <Database className="w-4 h-4" /> Lọc dữ liệu
              </div>
              <nav className="flex flex-col gap-1.5">
                <button 
                  onClick={() => setFilterStar(!filterStar)}
                  className={`flex items-center justify-between px-6 py-4 text-[10px] font-bold uppercase tracking-widest border rounded-sm transition-all ${
                    filterStar ? 'bg-black text-white border-black' : 'bg-white text-zinc-400 border-zinc-100 hover:border-zinc-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Star className={`w-4 h-4 ${filterStar ? 'fill-white' : ''}`} /> Yêu thích
                  </div>
                  {filterStar && <X className="w-3 h-3" />}
                </button>
                
                <div className="pt-4 space-y-3">
                  <label className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest px-1">Định dạng tệp</label>
                  <select 
                    value={filterFormat} 
                    onChange={(e) => setFilterFormat(e.target.value)}
                    className="w-full h-12 px-5 border border-zinc-100 bg-white text-[10px] font-bold uppercase tracking-widest outline-none focus:border-black transition-all rounded-sm"
                  >
                    <option value="all">Mọi định dạng</option>
                    <option value="pdf">Tài liệu PDF</option>
                    <option value="epub">Sách EPUB</option>
                  </select>
                </div>
              </nav>
            </div>

            <div className="p-8 border border-zinc-100 bg-zinc-50/20 rounded-sm">
              <p className="text-[10px] font-bold text-zinc-300 leading-relaxed uppercase tracking-tight">
                Hệ thống lưu trữ tri thức DocLib đảm bảo tính toàn vẹn và bảo mật tuyệt đối cho mọi thực thể dữ liệu.
              </p>
            </div>
          </aside>

          {/* Main Content Area */}
          <div 
            className="lg:col-span-9 space-y-8 transition-all duration-300 delay-150"
            style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
          >
            {/* Toolbar: Breadcrumbs & View Options */}
            <div className="flex flex-col md:flex-row gap-6 items-center justify-between bg-zinc-50/30 p-4 border border-zinc-50 rounded-sm">
              <div className="flex items-center gap-3 overflow-x-auto no-scrollbar max-w-full">
                <button 
                  onClick={() => { setCurrentFolder(null); setBreadcrumbs([]); }}
                  className={`flex items-center gap-3 px-4 h-10 text-[9px] font-bold uppercase tracking-widest transition-all rounded-sm border ${!currentFolder ? 'bg-black text-white border-black' : 'bg-white text-zinc-200 border-zinc-100 hover:border-black hover:text-black'}`}
                >
                  <Home className="w-3.5 h-3.5" />
                  Gốc
                </button>
                {breadcrumbs.map((b, idx) => (
                  <div key={b._id} className="flex items-center gap-2 shrink-0">
                    <ChevronRight className="w-3 h-3 text-zinc-100" />
                    <button 
                      onClick={() => {
                        const newBread = breadcrumbs.slice(0, idx + 1);
                        setBreadcrumbs(newBread);
                        setCurrentFolder(newBread[newBread.length - 1]);
                      }}
                      className={`px-4 h-10 text-[9px] font-bold uppercase tracking-widest transition-all rounded-sm border ${idx === breadcrumbs.length - 1 ? 'bg-black text-white border-black' : 'bg-white text-zinc-200 border-zinc-100 hover:border-black hover:text-black'}`}
                    >
                      {b.name}
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-4">
                <div className="flex bg-white p-1 border border-zinc-100 rounded-sm">
                  <button onClick={() => setViewMode("grid")} className={`p-2.5 transition-all rounded-sm ${viewMode === 'grid' ? 'bg-black text-white' : 'text-zinc-200 hover:text-black'}`}><LayoutGrid className="w-3.5 h-3.5"/></button>
                  <button onClick={() => setViewMode("list")} className={`p-2.5 transition-all rounded-sm ${viewMode === 'list' ? 'bg-black text-white' : 'text-zinc-200 hover:text-black'}`}><List className="w-3.5 h-3.5"/></button>
                </div>
                <button 
                  onClick={fetchData}
                  className="h-10 w-10 border border-zinc-100 bg-white flex items-center justify-center text-zinc-200 hover:text-black transition-all rounded-sm"
                >
                  {isRefreshing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* List/Grid Content */}
            {viewMode === "list" ? (
              <div className="bg-white border border-zinc-100 rounded-sm overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-zinc-50/50 border-b border-zinc-100 text-zinc-300 text-[9px] font-bold uppercase tracking-[0.2em]">
                      <th className="px-10 py-6">Thực thể tri thức</th>
                      <th className="px-10 py-6">Phân loại</th>
                      <th className="px-10 py-6">Bảo mật</th>
                      <th className="px-10 py-6 text-right">Hành động</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-50">
                    {folders.map((folder: any) => (
                      <tr 
                        key={folder._id} 
                        className="hover:bg-zinc-50/40 transition-all cursor-pointer group"
                        onClick={() => {
                          setCurrentFolder(folder);
                          setBreadcrumbs([...breadcrumbs, folder]);
                        }}
                      >
                        <td className="px-10 py-8">
                          <div className="flex items-center gap-8">
                            <div className="w-12 h-12 bg-zinc-50 border border-zinc-100 flex items-center justify-center rounded-sm text-zinc-200 group-hover:text-black group-hover:bg-white transition-all">
                              <Folder className="w-5 h-5" />
                            </div>
                            <span className="font-bold text-black text-sm tracking-tight">{folder.name}</span>
                          </div>
                        </td>
                        <td className="px-10 py-8 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Thư mục hệ thống</td>
                        <td className="px-10 py-8">—</td>
                        <td className="px-10 py-8 text-right">
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              setConfirmModal({ show: true, title: "Xóa thư mục?", docId: folder._id, type: "folder" });
                            }}
                            className="h-10 w-10 border border-zinc-100 flex items-center justify-center text-zinc-100 hover:text-red-500 hover:border-red-500 transition-all rounded-sm ml-auto"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {documents.map((doc: any) => (
                      <tr key={doc._id || doc.id} className="hover:bg-zinc-50/20 transition-all group">
                        <td className="px-10 py-8">
                          <div className="flex items-center gap-8">
                            <div className="w-12 h-16 bg-zinc-50 border border-zinc-100 flex items-center justify-center rounded-sm text-zinc-100 group-hover:text-black group-hover:bg-white transition-all">
                              <FileText className="w-5 h-5" />
                            </div>
                            <div className="flex flex-col gap-1.5 min-w-0">
                              <span className="font-bold text-black text-sm tracking-tight truncate max-w-md">{doc.title}</span>
                              <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2">
                                {doc.publisher_name || "DocLib"} <ChevronRight className="w-3 h-3" /> {doc.category || "Tài liệu"}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="px-10 py-8">
                          <span className={`inline-block px-4 py-1.5 text-[9px] font-bold uppercase tracking-widest rounded-sm border ${
                            doc.status === 'published' ? 'bg-black text-white border-black' : 'bg-white text-zinc-300 border-zinc-100'
                          }`}>
                            {doc.status === 'published' ? 'Đã đăng' : 'Bản nháp'}
                          </span>
                        </td>
                        <td className="px-10 py-8">
                          {doc.is_protected ? (
                            <div className="flex items-center gap-2 text-black">
                              <Lock className="w-3.5 h-3.5" />
                              <span className="text-[9px] font-bold uppercase tracking-widest">Đã khóa</span>
                            </div>
                          ) : (
                            <span className="text-zinc-200 text-[9px] font-bold uppercase tracking-widest">Không</span>
                          )}
                        </td>
                        <td className="px-10 py-8 text-right">
                          <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-all">
                            <button 
                              onClick={() => toggleStar(doc._id || doc.id)}
                              className={`h-10 w-10 border flex items-center justify-center transition-all rounded-sm ${doc.is_starred ? 'bg-black border-black text-white' : 'border-zinc-100 text-zinc-200 hover:text-black hover:border-black'}`}
                            >
                              <Star className={`w-3.5 h-3.5 ${doc.is_starred ? 'fill-white' : ''}`} />
                            </button>
                            <button 
                              onClick={() => setLockModal({ show: true, docId: doc._id || doc.id })}
                              className="h-10 w-10 border border-zinc-100 flex items-center justify-center text-zinc-200 hover:text-black hover:border-black transition-all rounded-sm"
                            >
                              <Lock className="w-3.5 h-3.5" />
                            </button>
                            <button 
                              onClick={() => setShareModal({ show: true, docId: doc._id || doc.id })}
                              className="h-10 w-10 border border-zinc-100 flex items-center justify-center text-zinc-200 hover:text-black hover:border-black transition-all rounded-sm"
                            >
                              <Share2 className="w-3.5 h-3.5" />
                            </button>
                            <button 
                              onClick={() => window.open(`/documents/viewer/${doc._id || doc.id}`, '_blank')}
                              className="h-10 w-10 border border-zinc-100 flex items-center justify-center text-zinc-200 hover:text-black hover:border-black transition-all rounded-sm"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </button>
                            <button 
                              onClick={() => setConfirmModal({ show: true, title: "Xóa tài liệu?", docId: doc._id || doc.id, type: "doc" })}
                              className="h-10 w-10 border border-zinc-100 flex items-center justify-center text-zinc-100 hover:text-red-500 hover:border-red-500 transition-all rounded-sm"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {folders.map((folder: any) => (
                  <div 
                    key={folder._id}
                    onClick={() => {
                      setCurrentFolder(folder);
                      setBreadcrumbs([...breadcrumbs, folder]);
                    }}
                    className="bg-white border border-zinc-100 p-8 flex flex-col items-center justify-center gap-6 group hover:border-black transition-all cursor-pointer rounded-sm"
                  >
                    <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 flex items-center justify-center text-zinc-200 group-hover:bg-black group-hover:text-white transition-all rounded-sm">
                      <Folder className="w-6 h-6" />
                    </div>
                    <span className="text-[10px] font-bold text-black uppercase tracking-widest text-center">{folder.name}</span>
                  </div>
                ))}
                {documents.map((doc: any) => (
                  <div 
                    key={doc._id || doc.id}
                    className="bg-white border border-zinc-100 p-8 flex flex-col items-center justify-center gap-6 group hover:border-black transition-all rounded-sm relative"
                  >
                    <div className="absolute top-4 right-4 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-all">
                      <button onClick={() => toggleStar(doc._id || doc.id)} className={`p-2 transition-all ${doc.is_starred ? 'text-black' : 'text-zinc-200 hover:text-black'}`}><Star className={`w-4 h-4 ${doc.is_starred ? 'fill-black' : ''}`}/></button>
                    </div>
                    <div className="w-20 h-28 bg-zinc-50 border border-zinc-100 flex items-center justify-center text-zinc-100 group-hover:bg-white group-hover:text-black transition-all rounded-sm overflow-hidden">
                      <FileText className="w-8 h-8" />
                    </div>
                    <div className="text-center space-y-2">
                      <p className="text-[10px] font-bold text-black uppercase tracking-widest truncate w-full px-2">{doc.title}</p>
                      <p className="text-[8px] font-bold text-zinc-300 uppercase tracking-[0.2em]">{doc.category || "Tài liệu"}</p>
                    </div>
                    <div className="flex gap-2 w-full pt-4 border-t border-zinc-50 opacity-0 group-hover:opacity-100 transition-all">
                      <button 
                        onClick={() => window.open(`/documents/viewer/${doc._id || doc.id}`, '_blank')}
                        className="flex-1 h-10 border border-zinc-100 flex items-center justify-center text-zinc-200 hover:text-black hover:border-black transition-all rounded-sm"
                      ><Eye className="w-4 h-4"/></button>
                      <button 
                        onClick={() => setConfirmModal({ show: true, title: "Xóa tài liệu?", docId: doc._id || doc.id, type: "doc" })}
                        className="flex-1 h-10 border border-zinc-100 flex items-center justify-center text-zinc-100 hover:text-red-500 hover:border-red-500 transition-all rounded-sm"
                      ><Trash2 className="w-4 h-4"/></button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {(documents.length === 0 && folders.length === 0) && (
              <div className="py-48 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-white rounded-sm">
                <div className="w-20 h-20 border border-zinc-100 bg-white flex items-center justify-center mb-10 rounded-sm">
                  <Search className="w-10 h-10 text-zinc-100 stroke-[1]" />
                </div>
                <h2 className="text-3xl font-bold tracking-tighter text-black mb-4 uppercase">
                  Không tìm thấy tri thức
                </h2>
                <p className="text-[10px] font-bold text-zinc-300 mb-10 max-w-xs text-center uppercase tracking-[0.2em] leading-loose">
                  Hiện tại thư mục này không chứa bất kỳ thực thể dữ liệu nào hoặc không khớp với tiêu chí tìm kiếm
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Workspace>
  );
}
