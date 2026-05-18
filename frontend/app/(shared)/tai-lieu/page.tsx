"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { 
  getDocumentsAPI, 
  getMyDocumentsAPI, 
  createDocumentAPI, 
  deleteAuthorDocumentAPI, 
  deleteAdminDocumentAPI,
  getFoldersAPI,
  createFolderAPI,
  deleteFolderAPI,
  lockDocumentAPI,
  toggleStarDocumentAPI
} from "@/services/document.service";
import { uploadDocumentAPI } from "@/services/upload.service";
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
  Home
} from "lucide-react";
import { useAuth } from "@/contexts/Auth";
import { useToast } from "@/contexts/Toast";
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

  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const observerTarget = useRef<HTMLDivElement>(null);

  const fetchData = useCallback(async (isLoadMore = false) => {
    if (isRefreshing || (!hasMore && isLoadMore)) return;
    setIsRefreshing(true);
    
    try {
      const currentCursor = isLoadMore ? cursor : undefined;
      
      const [docsData, foldersData] = await Promise.all([
        isAdmin ? getDocumentsAPI(searchQuery, undefined, undefined, undefined, currentFolder?._id, filterStar, filterFormat, undefined, currentCursor || "", 20) : getMyDocumentsAPI(currentCursor || "", 20),
        !isLoadMore ? getFoldersAPI(currentFolder?._id) : Promise.resolve([])
      ]);
      
      let docs = docsData.data || docsData || [];
      if (!isAdmin) {
        if (currentFolder) docs = docs.filter((d: any) => d.folder_id === currentFolder._id);
        else docs = docs.filter((d: any) => !d.folder_id);
        if (filterStar) docs = docs.filter((d: any) => d.is_starred);
        if (filterFormat !== "all") docs = docs.filter((d: any) => d.file_url?.toLowerCase().endsWith(filterFormat));
        if (searchQuery) docs = docs.filter((d: any) => d.title.toLowerCase().includes(searchQuery.toLowerCase()) || (d.publisher_name || "").toLowerCase().includes(searchQuery.toLowerCase()));
      }
      
      if (docs.length < 20) setHasMore(false);
      else setHasMore(true);
      
      if (docs.length > 0) setCursor(docs[docs.length - 1].id || docs[docs.length - 1]._id);

      setDocuments(prev => isLoadMore ? [...prev, ...docs] : docs);
      if (!isLoadMore) setFolders(foldersData.data || foldersData || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách tài liệu", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [isAdmin, searchQuery, currentFolder, filterStar, filterFormat, cursor, hasMore, showToast, isRefreshing]);

  useEffect(() => {
    if (!authLoading && user) {
      fetchData();
      setNewDoc(prev => ({ 
        ...prev, 
        publisher_name: isAdmin ? "DocLib" : (user.full_name || "") 
      }));
    }
  }, [user, authLoading, isAdmin]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !isRefreshing) {
          fetchData(true);
        }
      },
      { threshold: 0.5 }
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
          content_format: uploadRes.data.extension || file.name.split(".").pop()?.toLowerCase(),
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
    setPublicUrl(`${window.location.origin}/tai-lieu/viewer/${shareModal.docId}${sharePassword ? `?pwd=${sharePassword}` : ""}`);
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
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <Workspace>
      <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
        
        {/* Modals */}
        <Modal isOpen={!!confirmModal} onClose={() => setConfirmModal(null)} className="max-w-md rounded-none border border-zinc-200 bg-white p-0">
          <ModalHeader className="border-b border-zinc-200 p-6">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 border border-zinc-200 bg-zinc-50 flex items-center justify-center rounded-none">
                <AlertTriangle className="w-5 h-5 text-black" />
              </div>
              <div>
                <ModalTitle className="text-sm font-semibold text-black">{confirmModal?.title}</ModalTitle>
                <ModalDescription className="text-xs font-medium text-zinc-500 mt-1">Hành động này sẽ xóa vĩnh viễn dữ liệu khỏi hệ thống</ModalDescription>
              </div>
            </div>
          </ModalHeader>
          <ModalFooter className="flex gap-3 border-t border-zinc-200 p-4 bg-zinc-50">
            <button
              onClick={() => setConfirmModal(null)}
              className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black hover:bg-zinc-50 transition-colors rounded-none"
            >
              Hủy bỏ
            </button>
            <button
              onClick={executeDelete}
              className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium hover:bg-zinc-800 transition-colors rounded-none"
            >
              Xác nhận
            </button>
          </ModalFooter>
        </Modal>

        <Modal isOpen={createDocModal} onClose={() => setCreateDocModal(false)} className="max-w-3xl rounded-none border border-zinc-200 bg-white p-0">
          <ModalHeader className="border-b border-zinc-200 p-6">
            <ModalTitle className="text-sm font-semibold text-black">{isAdmin ? "Thêm tài liệu hệ thống" : "Khởi tạo tài liệu mới"}</ModalTitle>
            <ModalDescription className="text-xs font-medium text-zinc-500 mt-1">Điền thông tin để bắt đầu quá trình lưu trữ chuyên sâu</ModalDescription>
          </ModalHeader>
          <ModalContent className="grid md:grid-cols-2 gap-8 p-6">
            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Tiêu đề tài liệu</label>
                <input 
                  type="text" 
                  value={newDoc.title}
                  onChange={(e) => setNewDoc({...newDoc, title: e.target.value})}
                  className="w-full h-10 px-3 bg-zinc-50 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black transition-colors rounded-none" 
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Thể loại</label>
                  <select 
                    value={newDoc.category}
                    onChange={(e) => setNewDoc({...newDoc, category: e.target.value})}
                    className="w-full h-10 px-3 bg-zinc-50 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black appearance-none transition-colors rounded-none"
                  >
                    <option value="Chưa phân loại">Chưa phân loại</option>
                    <option value="Giáo trình">Giáo trình</option>
                    <option value="Kỹ thuật">Kỹ thuật</option>
                    <option value="Nghiên cứu">Nghiên cứu</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Giá (dl)</label>
                  <input 
                    type="number" 
                    className="w-full h-10 px-3 bg-zinc-50 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black transition-colors rounded-none"
                    value={newDoc.price_dl}
                    onChange={(e) => setNewDoc({ ...newDoc, price_dl: parseInt(e.target.value) || 0 })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Mô tả tóm lược</label>
                <textarea 
                  value={newDoc.description}
                  onChange={(e) => setNewDoc({...newDoc, description: e.target.value})}
                  className="w-full h-24 p-3 bg-zinc-50 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black transition-colors resize-none rounded-none" 
                />
              </div>
            </div>
            
            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Thực thể đính kèm</label>
                <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept=".pdf,.epub,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.txt,.zip,.csv,.json,.md" />
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 hover:border-black p-6 flex flex-col items-center justify-center gap-3 transition-colors cursor-pointer rounded-none"
                >
                  <div className="w-10 h-10 flex items-center justify-center bg-white border border-zinc-200 text-black rounded-none">
                    {file ? <FileCheck className="w-5 h-5" /> : <Upload className="w-5 h-5" />}
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-semibold text-black mb-1 truncate max-w-[200px]">
                      {file ? file.name : "Chọn tệp tin (PDF, EPUB, Office...)"}
                    </p>
                    <p className="text-[10px] font-medium text-zinc-500 uppercase tracking-widest">
                      {file ? `${(file.size / (1024 * 1024)).toFixed(2)} MB` : "Tối đa 50MB"}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Hiển thị</label>
                  <select 
                    value={newDoc.visibility}
                    onChange={(e) => setNewDoc({...newDoc, visibility: e.target.value})}
                    className="w-full h-10 px-3 bg-zinc-50 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black appearance-none transition-colors rounded-none"
                  >
                    <option value="public">Công khai</option>
                    <option value="private">Riêng tư</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Trạng thái</label>
                  <select 
                    value={newDoc.status}
                    onChange={(e) => setNewDoc({...newDoc, status: e.target.value})}
                    className="w-full h-10 px-3 bg-zinc-50 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black appearance-none transition-colors rounded-none"
                  >
                    <option value="published">Xuất bản</option>
                    <option value="draft">Bản nháp</option>
                  </select>
                </div>
              </div>
            </div>
          </ModalContent>
          <ModalFooter className="border-t border-zinc-200 p-4 bg-zinc-50">
            <button 
              onClick={handleCreateDocument}
              disabled={isCreating || !file || !newDoc.title}
              className="w-full py-2 bg-black text-white text-xs font-medium hover:bg-zinc-800 transition-colors flex items-center justify-center gap-2 rounded-none disabled:opacity-50"
            >
              {isCreating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Kích hoạt lưu trữ
            </button>
          </ModalFooter>
        </Modal>

        <Modal isOpen={createFolderModal} onClose={() => setCreateFolderModal(false)} className="max-w-md rounded-none border border-zinc-200 bg-white p-0">
          <ModalHeader className="border-b border-zinc-200 p-6">
            <ModalTitle className="text-sm font-semibold text-black">Kiến tạo không gian mới</ModalTitle>
            <ModalDescription className="text-xs font-medium text-zinc-500 mt-1">Phân loại tài liệu theo cấu trúc thư mục chuyên nghiệp</ModalDescription>
          </ModalHeader>
          <ModalContent className="p-6">
            <div className="space-y-2">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Tên thư mục</label>
              <input 
                type="text" 
                value={folderName}
                onChange={(e) => setFolderName(e.target.value)}
                autoFocus
                className="w-full h-10 px-3 bg-zinc-50 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black transition-colors rounded-none" 
              />
            </div>
          </ModalContent>
          <ModalFooter className="flex gap-3 border-t border-zinc-200 p-4 bg-zinc-50">
            <button
              onClick={() => setCreateFolderModal(false)}
              className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black hover:bg-zinc-50 transition-colors rounded-none"
            >
              Hủy bỏ
            </button>
            <button 
              onClick={handleCreateFolder}
              disabled={!folderName}
              className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium hover:bg-zinc-800 transition-colors rounded-none disabled:opacity-50"
            >
              Tạo thư mục
            </button>
          </ModalFooter>
        </Modal>

        <Modal isOpen={!!lockModal} onClose={() => setLockModal(null)} className="max-w-md rounded-none border border-zinc-200 bg-white p-0">
          <ModalHeader className="border-b border-zinc-200 p-6">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 border border-zinc-200 bg-zinc-50 flex items-center justify-center rounded-none">
                <Lock className="w-5 h-5 text-black" />
              </div>
              <div>
                <ModalTitle className="text-sm font-semibold text-black">Thiết lập bảo mật</ModalTitle>
                <ModalDescription className="text-xs font-medium text-zinc-500 mt-1">Mã hóa đa lớp cho thực thể</ModalDescription>
              </div>
            </div>
          </ModalHeader>
          <ModalContent className="p-6">
            <form id="lock-form" onSubmit={handleLockDocument} className="space-y-4">
              <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest leading-relaxed">Mật khẩu sẽ được mã hóa và không thể khôi phục nếu bị thất lạc</p>
              <input 
                type="password" 
                autoFocus
                className="w-full h-10 px-3 bg-zinc-50 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black transition-colors rounded-none"
                value={lockPassword}
                onChange={(e) => setLockPassword(e.target.value)}
                required
              />
            </form>
          </ModalContent>
          <ModalFooter className="flex gap-3 border-t border-zinc-200 p-4 bg-zinc-50">
            <button type="button" onClick={() => setLockModal(null)} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black hover:bg-zinc-50 transition-colors rounded-none">Hủy bỏ</button>
            <button type="submit" form="lock-form" className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium hover:bg-zinc-800 transition-colors rounded-none">Kích hoạt khóa</button>
          </ModalFooter>
        </Modal>

        <Modal isOpen={!!shareModal} onClose={() => setShareModal(null)} className="max-w-2xl rounded-none border border-zinc-200 bg-white p-0">
          <ModalHeader className="border-b border-zinc-200 p-6">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 border border-zinc-200 bg-zinc-50 flex items-center justify-center rounded-none">
                <Globe className="w-5 h-5 text-black" />
              </div>
              <div>
                <ModalTitle className="text-sm font-semibold text-black">Giao thức chia sẻ</ModalTitle>
                <ModalDescription className="text-xs font-medium text-zinc-500 mt-1">Thiết lập quyền truy cập cho cộng đồng</ModalDescription>
              </div>
            </div>
          </ModalHeader>
          <ModalContent className="p-6 space-y-6">
            <form id="share-form" onSubmit={handleShareSubmit} className="space-y-6">
              <div className="flex items-center gap-3 bg-zinc-50 p-4 border border-zinc-200 rounded-none">
                <input type="checkbox" checked={isPublic} onChange={e => setIsPublic(e.target.checked)} className="w-4 h-4 accent-black cursor-pointer rounded-none" />
                <label className="text-xs font-semibold text-black uppercase tracking-widest cursor-pointer">Công khai tài liệu</label>
              </div>
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Mật mã truy cập</label>
                  <input type="password" value={sharePassword} onChange={e=>setSharePassword(e.target.value)} className="w-full h-10 px-3 bg-zinc-50 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black rounded-none transition-colors" />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Thời hạn hiệu lực</label>
                  <select value={shareExpires} onChange={e=>setShareExpires(e.target.value)} className="w-full h-10 px-3 bg-zinc-50 border border-zinc-200 text-xs font-medium uppercase tracking-widest focus:outline-none focus:border-black rounded-none transition-colors appearance-none">
                    <option value="1">24 giờ</option>
                    <option value="7">07 ngày</option>
                    <option value="30">30 ngày</option>
                  </select>
                </div>
              </div>
              {publicUrl && (
                <div className="p-6 bg-zinc-50 border border-zinc-200 flex flex-col items-center gap-6 animate-in fade-in rounded-none">
                  <div className="text-[10px] font-semibold text-black break-all select-all text-center uppercase tracking-widest bg-white p-3 border border-zinc-200 w-full rounded-none">{publicUrl}</div>
                  <div className="p-4 bg-white border border-zinc-200 rounded-none">
                    <img src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(publicUrl)}`} className="w-32 h-32 grayscale" alt="QR Code" />
                  </div>
                  <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest flex items-center gap-2"><QrCode className="w-4 h-4"/> Quét mã để tiếp cận</p>
                </div>
              )}
            </form>
          </ModalContent>
          <ModalFooter className="flex gap-3 border-t border-zinc-200 p-4 bg-zinc-50">
            <button type="button" onClick={() => { setShareModal(null); setPublicUrl(""); }} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black hover:bg-zinc-50 transition-colors rounded-none">Đóng</button>
            <button type="submit" form="share-form" className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium hover:bg-zinc-800 transition-colors rounded-none">Cập nhật giao thức</button>
          </ModalFooter>
        </Modal>

        {/* Header Section */}
        <div 
          className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6 transition-opacity duration-500" 
          style={{ opacity: visible ? 1 : 0 }}
        >
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold text-black">
              Tài liệu & Học liệu
            </h1>
            <p className="text-zinc-500 text-sm font-medium">
              Kiến tạo không gian nội dung cá nhân hóa
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setCreateFolderModal(true)}
              className="h-10 px-6 border border-zinc-200 bg-white text-black text-xs font-medium hover:bg-zinc-50 transition-colors flex items-center gap-2 rounded-none"
            >
              <FolderPlus className="w-4 h-4" />
              Thư mục
            </button>
            <button 
              onClick={() => setCreateDocModal(true)}
              className="h-10 px-6 bg-black text-white text-xs font-medium hover:bg-zinc-800 transition-colors flex items-center gap-2 rounded-none"
            >
              <Plus className="w-4 h-4" />
              Thêm tài liệu
            </button>
          </div>
        </div>

        {/* Main Grid Layout */}
        <div className="grid lg:grid-cols-12 gap-12 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
          {/* Sidebar Filters */}
          <aside className="lg:col-span-3 space-y-6">
            {/* Search */}
            <div className="border border-zinc-200 bg-white p-6 space-y-4">
              <h3 className="text-xs font-semibold text-black flex items-center gap-2 border-b border-zinc-200 pb-2">
                <Search className="w-4 h-4" /> Tìm kiếm tài liệu
              </h3>
              <input 
                type="text"
                placeholder="Nhập từ khóa"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black transition-colors rounded-none placeholder:text-zinc-400"
              />
            </div>

            {/* Filters */}
            <div className="border border-zinc-200 bg-white p-6 space-y-4">
              <h3 className="text-xs font-semibold text-black flex items-center gap-2 border-b border-zinc-200 pb-2">
                <Database className="w-4 h-4" /> Lọc dữ liệu
              </h3>
              <div className="space-y-3">
                <button 
                  onClick={() => setFilterStar(!filterStar)}
                  className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium border transition-colors rounded-none ${
                    filterStar ? 'bg-black text-white border-black' : 'bg-white text-zinc-500 border-zinc-200 hover:bg-zinc-50 hover:text-black'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Star className="w-4 h-4" /> Yêu thích
                  </div>
                  {filterStar && <X className="w-3 h-3" />}
                </button>
                
                <div className="space-y-2">
                  <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Định dạng tệp</label>
                  <div className="relative">
                    <select 
                      value={filterFormat} 
                      onChange={(e) => setFilterFormat(e.target.value)}
                      className="w-full h-10 px-3 border border-zinc-200 bg-zinc-50 text-xs font-medium outline-none focus:border-black transition-colors rounded-none appearance-none"
                    >
                      <option value="all">Mọi định dạng</option>
                      <option value="pdf">Tài liệu PDF</option>
                      <option value="epub">Sách EPUB</option>
                      <option value="docx">Văn bản Word</option>
                      <option value="xlsx">Bảng tính Excel</option>
                      <option value="pptx">Thuyết trình PPT</option>
                      <option value="zip">Gói nén (ZIP)</option>
                    </select>
                    <ChevronRight className="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none rotate-90 text-zinc-500" />
                  </div>
                </div>
              </div>
            </div>

            <div className="p-6 border border-zinc-200 bg-zinc-50">
              <p className="text-[10px] font-semibold text-zinc-500 leading-relaxed uppercase tracking-widest">
                Hệ thống lưu trữ của DocLib đảm bảo tính toàn vẹn và bảo mật tuyệt đối cho mọi thực thể dữ liệu.
              </p>
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="lg:col-span-9 space-y-6">
            {/* Toolbar: Breadcrumbs & View Options */}
            <div className="border border-zinc-200 bg-white p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
              <div className="flex items-center gap-2 overflow-x-auto no-scrollbar max-w-full">
                <button 
                  onClick={() => { setCurrentFolder(null); setBreadcrumbs([]); }}
                  className={`flex items-center gap-2 px-3 py-1.5 text-xs font-medium transition-colors rounded-none border ${!currentFolder ? 'bg-zinc-100 border-zinc-200 text-black font-semibold' : 'bg-white text-zinc-500 border-transparent hover:bg-zinc-50 hover:border-zinc-200 hover:text-black'}`}
                >
                  <Home className="w-3.5 h-3.5" />
                  Gốc
                </button>
                {breadcrumbs.map((b, idx) => (
                  <div key={b._id} className="flex items-center gap-2 shrink-0">
                    <ChevronRight className="w-3 h-3 text-zinc-400" />
                    <button 
                      onClick={() => {
                        const newBread = breadcrumbs.slice(0, idx + 1);
                        setBreadcrumbs(newBread);
                        setCurrentFolder(newBread[newBread.length - 1]);
                      }}
                      className={`px-3 py-1.5 text-xs font-medium transition-colors rounded-none border ${idx === breadcrumbs.length - 1 ? 'bg-zinc-100 border-zinc-200 text-black font-semibold' : 'bg-white text-zinc-500 border-transparent hover:bg-zinc-50 hover:border-zinc-200 hover:text-black'}`}
                    >
                      {b.name}
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-3">
                <div className="flex bg-zinc-50 border border-zinc-200 p-0.5">
                  <button onClick={() => setViewMode("grid")} className={`p-1.5 transition-colors rounded-none ${viewMode === 'grid' ? 'bg-white border border-zinc-200 text-black' : 'text-zinc-500 hover:text-black'}`}><LayoutGrid className="w-4 h-4"/></button>
                  <button onClick={() => setViewMode("list")} className={`p-1.5 transition-colors rounded-none ${viewMode === 'list' ? 'bg-white border border-zinc-200 text-black' : 'text-zinc-500 hover:text-black'}`}><List className="w-4 h-4"/></button>
                </div>
                <button 
                  onClick={fetchData}
                  className="h-8 w-8 border border-zinc-200 bg-white flex items-center justify-center text-zinc-500 hover:text-black hover:bg-zinc-50 transition-colors rounded-none"
                >
                  {isRefreshing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* List/Grid Content */}
            {viewMode === "list" ? (
              <div className="bg-white border border-zinc-200">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-zinc-50 border-b border-zinc-200 text-black font-semibold">
                      <th className="px-6 py-4">Tài liệu</th>
                      <th className="px-6 py-4">Phân loại</th>
                      <th className="px-6 py-4">Bảo mật</th>
                      <th className="px-6 py-4 text-right">Hành động</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-200">
                    {folders.map((folder: any) => (
                      <tr 
                        key={folder._id} 
                        className="hover:bg-zinc-50 transition-colors cursor-pointer group"
                        onClick={() => {
                          setCurrentFolder(folder);
                          setBreadcrumbs([...breadcrumbs, folder]);
                        }}
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-4">
                            <div className="w-8 h-8 border border-zinc-200 bg-zinc-50 flex items-center justify-center rounded-none shrink-0 text-zinc-400 group-hover:text-black group-hover:bg-white transition-colors">
                              <Folder className="w-4 h-4" />
                            </div>
                            <span className="font-semibold text-black">{folder.name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-zinc-500 font-medium">Thư mục hệ thống</td>
                        <td className="px-6 py-4">—</td>
                        <td className="px-6 py-4 text-right">
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              setConfirmModal({ show: true, title: "Xóa thư mục?", docId: folder._id, type: "folder" });
                            }}
                            className="p-2 text-zinc-400 hover:text-black hover:bg-zinc-100 transition-colors rounded-none inline-flex"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {documents.map((doc: any) => (
                      <tr key={doc._id || doc.id} className="hover:bg-zinc-50 transition-colors group">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-4">
                            <div className="w-8 h-10 border border-zinc-200 bg-zinc-50 flex items-center justify-center rounded-none shrink-0 text-zinc-400 group-hover:text-black group-hover:bg-white transition-colors">
                              <FileText className="w-4 h-4" />
                            </div>
                            <div className="flex flex-col gap-1 min-w-0">
                              <span className="font-semibold text-black truncate max-w-sm">{doc.title}</span>
                              <span className="text-[10px] font-medium text-zinc-500 uppercase flex items-center gap-1.5">
                                {doc.publisher_name || "DocLib"} <ChevronRight className="w-3 h-3" /> {doc.category || "Tài liệu"}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-block px-2 py-1 text-[10px] font-semibold uppercase border rounded-none ${
                            doc.status === 'published' ? 'border-black text-black' : 'border-zinc-300 text-zinc-500'
                          }`}>
                            {doc.status === 'published' ? 'Đã đăng' : 'Bản nháp'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          {doc.is_protected ? (
                            <div className="flex items-center gap-1.5 text-black">
                              <Lock className="w-3.5 h-3.5" />
                              <span className="text-[10px] font-semibold uppercase">Đã khóa</span>
                            </div>
                          ) : (
                            <span className="text-zinc-500 text-[10px] font-medium uppercase">Không</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button 
                              onClick={() => toggleStar(doc._id || doc.id)}
                              className={`p-2 transition-colors rounded-none inline-flex ${doc.is_starred ? 'text-black bg-zinc-100' : 'text-zinc-400 hover:text-black hover:bg-zinc-100'}`}
                            >
                              <Star className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => setLockModal({ show: true, docId: doc._id || doc.id })}
                              className="p-2 text-zinc-400 hover:text-black hover:bg-zinc-100 transition-colors rounded-none inline-flex"
                            >
                              <Lock className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => setShareModal({ show: true, docId: doc._id || doc.id })}
                              className="p-2 text-zinc-400 hover:text-black hover:bg-zinc-100 transition-colors rounded-none inline-flex"
                            >
                              <Share2 className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => window.open(`/tai-lieu/viewer/${doc._id || doc.id}`, '_blank')}
                              className="p-2 text-zinc-400 hover:text-black hover:bg-zinc-100 transition-colors rounded-none inline-flex"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => setConfirmModal({ show: true, title: "Xóa tài liệu?", docId: doc._id || doc.id, type: "doc" })}
                              className="p-2 text-zinc-400 hover:text-black hover:bg-zinc-100 transition-colors rounded-none inline-flex"
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
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-6">
                {folders.map((folder: any) => (
                  <div 
                    key={folder._id}
                    onClick={() => {
                      setCurrentFolder(folder);
                      setBreadcrumbs([...breadcrumbs, folder]);
                    }}
                    className="bg-white border border-zinc-200 p-6 flex flex-col items-center justify-center gap-4 hover:border-black transition-colors cursor-pointer rounded-none group"
                  >
                    <div className="w-12 h-12 border border-zinc-200 bg-zinc-50 flex items-center justify-center text-zinc-400 group-hover:bg-white group-hover:text-black transition-colors rounded-none">
                      <Folder className="w-5 h-5" />
                    </div>
                    <span className="text-xs font-semibold text-black text-center">{folder.name}</span>
                  </div>
                ))}
                {documents.map((doc: any) => (
                  <div 
                    key={doc._id || doc.id}
                    className="bg-white border border-zinc-200 p-4 flex flex-col group hover:border-black transition-colors rounded-none relative"
                  >
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                      <button onClick={() => toggleStar(doc._id || doc.id)} className={`p-1.5 transition-colors bg-white border border-zinc-200 rounded-none ${doc.is_starred ? 'text-black' : 'text-zinc-400 hover:text-black'}`}><Star className="w-3.5 h-3.5" /></button>
                    </div>
                    
                    <div className="flex flex-col items-center gap-4 mb-4">
                      <div className="w-16 h-20 border border-zinc-200 bg-zinc-50 flex items-center justify-center text-zinc-400 group-hover:bg-white group-hover:text-black transition-colors rounded-none mt-2">
                        <FileText className="w-6 h-6" />
                      </div>
                      <div className="text-center w-full">
                        <p className="text-xs font-semibold text-black truncate w-full">{doc.title}</p>
                        <p className="text-[10px] font-medium text-zinc-500 uppercase mt-1">{doc.category || "Tài liệu"}</p>
                      </div>
                    </div>
                    
                    <div className="mt-auto border-t border-zinc-200 pt-3 flex justify-between gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                       <button onClick={() => window.open(`/tai-lieu/viewer/${doc._id || doc.id}`, '_blank')} className="flex-1 py-1.5 text-zinc-400 hover:text-black hover:bg-zinc-50 transition-colors flex justify-center rounded-none"><Eye className="w-4 h-4"/></button>
                       <button onClick={() => setLockModal({ show: true, docId: doc._id || doc.id })} className="flex-1 py-1.5 text-zinc-400 hover:text-black hover:bg-zinc-50 transition-colors flex justify-center rounded-none"><Lock className="w-4 h-4"/></button>
                       <button onClick={() => setShareModal({ show: true, docId: doc._id || doc.id })} className="flex-1 py-1.5 text-zinc-400 hover:text-black hover:bg-zinc-50 transition-colors flex justify-center rounded-none"><Share2 className="w-4 h-4"/></button>
                       <button onClick={() => setConfirmModal({ show: true, title: "Xóa tài liệu?", docId: doc._id || doc.id, type: "doc" })} className="flex-1 py-1.5 text-zinc-400 hover:text-black hover:bg-zinc-50 transition-colors flex justify-center rounded-none"><Trash2 className="w-4 h-4"/></button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {(documents.length === 0 && folders.length === 0) && (
              <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-zinc-50 rounded-none">
                <Search className="w-8 h-8 text-zinc-400 mb-4" />
                <h2 className="text-sm font-semibold text-black mb-1">
                  Không tìm thấy tài liệu
                </h2>
                <p className="text-xs font-medium text-zinc-500 max-w-xs text-center">
                  Hiện tại không có bất kỳ thực thể dữ liệu nào hoặc không khớp với tiêu chí tìm kiếm.
                </p>
              </div>
            )}
            
            {(documents.length > 0 || folders.length > 0) && (
              <div ref={observerTarget} className="h-10 mt-4 flex items-center justify-center">
                {isRefreshing && hasMore && <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />}
              </div>
            )}
          </main>
        </div>
      </div>
    </Workspace>
  );
}
