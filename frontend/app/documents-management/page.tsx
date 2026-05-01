"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { 
  getDocumentsAPI, 
  getMyDocumentsAPI, 
  uploadDocumentAPI, 
  createDocumentAPI, 
  deleteAuthorDocumentAPI, 
  deleteAdminDocumentAPI,
  API_URL 
} from "@/app/lib/api";
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
  ShieldCheck,
  Plus,
  Sparkles,
  ChevronRight,
  Database
} from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";
import { Notification } from "@/app/components/NotificationToast";
import AppShell from "@/app/components/AppShell";

export default function DocumentManagementPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const [documents, setDocuments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [confirmModal, setConfirmModal] = useState<{ show: boolean; title: string; docId: string } | null>(null);
  const [createDocModal, setCreateDocModal] = useState(false);
  
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
    is_protected: true
  });
  
  const [visible, setVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isCreating, setIsCreating] = useState(false);

  const isAdmin = user?.role === "admin";

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      let data;
      if (isAdmin) {
        data = await getDocumentsAPI();
      } else {
        data = await getMyDocumentsAPI();
      }
      setDocuments(data.data || data || []);
    } catch (err: any) {
      console.error("Lỗi tải kho tài liệu:", err);
      setNotification({ type: "error", text: "Không thể tải danh sách tài liệu." });
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [isAdmin]);

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
      setNotification({ type: "error", text: "Vui lòng nhập tiêu đề và chọn tệp tin." });
      return;
    }

    setIsCreating(true);
    try {
        const uploadRes = await uploadDocumentAPI(file);
        const file_url = uploadRes.data.url;

        const submissionData = {
          ...newDoc,
          file_url,
          slug: newDoc.slug || newDoc.title.toLowerCase().replace(/\s+/g, "-") + "-" + Date.now().toString().slice(-4),
          publish_at: newDoc.status === 'scheduled' ? newDoc.publish_at : null
        };

        await createDocumentAPI(submissionData);
        setNotification({ type: "success", text: "Đã khởi tạo tài liệu mới thành công." });
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
          is_protected: true 
        });
        setFile(null);
        fetchData();
    } catch (err: any) {
        setNotification({ type: "error", text: err.message || "Lỗi hệ thống khi tạo tài liệu." });
    } finally {
        setIsCreating(false);
    }
  };

  const executeDelete = async () => {
    if (!confirmModal) return;
    try {
        if (isAdmin) {
          await deleteAdminDocumentAPI(confirmModal.docId);
        } else {
          await deleteAuthorDocumentAPI(confirmModal.docId);
        }
        setNotification({ type: "success", text: "Đã xóa tài liệu khỏi hệ thống." });
        fetchData();
    } catch (err: any) {
        setNotification({ type: "error", text: err.message || "Không thể xóa tài liệu." });
    } finally {
        setConfirmModal(null);
    }
  };

  const filteredDocuments = documents.filter(doc => 
    doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (doc.publisher_name || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (authLoading || isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-white">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  return (
    <AppShell>
      <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
        {notification && (
          <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
            <Notification type={notification.type} message={notification.text} />
          </div>
        )}

        {confirmModal?.show && (
          <div className="fixed inset-0 z-[2000] bg-black/40 flex items-center justify-center p-6 animate-in fade-in duration-300 backdrop-blur-sm">
            <div className="bg-white border border-zinc-200 w-full max-w-sm p-10 space-y-8 rounded-sm">
              <div className="text-center space-y-4">
                <AlertTriangle className="w-12 h-12 text-black mx-auto stroke-[1]" />
                <h3 className="text-sm font-bold tracking-tight uppercase">{confirmModal.title}</h3>
                <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest leading-relaxed">Hành động này sẽ xóa vĩnh viễn dữ liệu khỏi hệ thống.</p>
              </div>
              <div className="flex gap-4">
                <button
                  onClick={() => setConfirmModal(null)}
                  className="flex-1 h-12 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black hover:border-black transition-all rounded-sm"
                >
                  Hủy bỏ
                </button>
                <button
                  onClick={executeDelete}
                  className="flex-1 h-12 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-[0.98] rounded-sm"
                >
                  Xác nhận
                </button>
              </div>
            </div>
          </div>
        )}

        {createDocModal && (
          <div className="fixed inset-0 z-[2000] bg-black/40 flex items-center justify-center p-6 animate-in fade-in duration-300 backdrop-blur-sm">
            <div className="bg-white w-full max-w-4xl border border-zinc-200 rounded-sm overflow-hidden flex flex-col max-h-[90vh]">
                  <div className="p-10 border-b border-zinc-100 flex justify-between items-center bg-white">
                      <h3 className="text-3xl font-bold tracking-tighter uppercase">{isAdmin ? "Thêm tài liệu hệ thống" : "Khởi tạo tài liệu mới"}</h3>
                      <button 
                          onClick={() => setCreateDocModal(false)} 
                          className="text-zinc-200 hover:text-black transition-colors"
                      >
                          <X className="w-8 h-8 stroke-[1]" />
                      </button>
                  </div>
                  
                  <div className="flex-1 overflow-y-auto p-12 space-y-12 no-scrollbar">
                      <div className="grid md:grid-cols-2 gap-12">
                          <div className="space-y-10">
                              <div className="space-y-4">
                                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Tiêu đề tài liệu</label>
                                  <input 
                                      type="text" 
                                      value={newDoc.title}
                                      onChange={(e) => setNewDoc({...newDoc, title: e.target.value})}
                                      placeholder="Nhập tên tài liệu"
                                      className="w-full h-16 border-b border-zinc-100 focus:border-black outline-none font-bold text-xl transition-all placeholder:text-zinc-100" 
                                  />
                              </div>

                              <div className="grid grid-cols-2 gap-8">
                                  <div className="space-y-4">
                                      <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Thể loại</label>
                                      <select 
                                          value={newDoc.category}
                                          onChange={(e) => setNewDoc({...newDoc, category: e.target.value})}
                                          className="w-full h-14 border-b border-zinc-100 focus:border-black outline-none font-bold uppercase tracking-widest text-[11px] transition-all cursor-pointer appearance-none bg-transparent"
                                      >
                                          <option value="Chưa phân loại">Chưa phân loại</option>
                                          <option value="Giáo trình">Giáo trình</option>
                                          <option value="Tiểu thuyết">Tiểu thuyết</option>
                                          <option value="Kỹ thuật">Kỹ thuật</option>
                                          <option value="Kinh tế">Kinh tế</option>
                                          <option value="Nghiên cứu">Nghiên cứu</option>
                                      </select>
                                  </div>
                                  <div className="space-y-4">
                                      <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Giá bán (dl)</label>
                                      <input 
                                          type="number" 
                                          className="w-full h-14 border-b border-zinc-100 focus:border-black outline-none font-bold text-lg transition-all"
                                          value={newDoc.price_dl}
                                          onChange={(e) => setNewDoc({ ...newDoc, price_dl: parseInt(e.target.value) || 0 })}
                                      />
                                  </div>
                              </div>

                              <div className="space-y-4">
                                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Mô tả tác phẩm</label>
                                  <textarea 
                                      value={newDoc.description}
                                      onChange={(e) => setNewDoc({...newDoc, description: e.target.value})}
                                      placeholder="Nhập mô tả tóm tắt về nội dung tài liệu"
                                      className="w-full h-40 border border-zinc-100 p-6 focus:border-black outline-none font-medium text-sm transition-all resize-none no-scrollbar leading-relaxed rounded-sm" 
                                  />
                              </div>
                          </div>

                          <div className="space-y-10">
                              <div className="space-y-4">
                                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Tệp đính kèm (PDF/EPUB)</label>
                                  <input 
                                      type="file" 
                                      ref={fileInputRef} 
                                      onChange={handleFileChange} 
                                      className="hidden" 
                                      accept=".pdf,.epub"
                                  />
                                  <div 
                                      onClick={() => fileInputRef.current?.click()}
                                      className={`border border-zinc-100 p-12 flex flex-col items-center justify-center gap-6 group hover:border-black transition-all cursor-pointer rounded-sm ${file ? 'bg-black text-white' : 'bg-zinc-50/20'}`}
                                  >
                                      <div className={`w-20 h-20 flex items-center justify-center transition-all ${file ? 'bg-white text-black' : 'bg-white text-zinc-100 group-hover:bg-black group-hover:text-white'} rounded-sm`}>
                                          {file ? <FileCheck className="w-8 h-8" /> : <Upload className="w-8 h-8" />}
                                      </div>
                                      <div className="text-center">
                                          <p className="text-[11px] font-bold uppercase tracking-widest mb-1">
                                              {file ? file.name : "Nhấp để chọn tệp tin"}
                                          </p>
                                          <p className={`text-[9px] font-bold uppercase tracking-[0.2em] italic ${file ? 'text-zinc-500' : 'text-zinc-200'}`}>
                                              {file ? `${(file.size / (1024 * 1024)).toFixed(2)} MB` : "Tối đa 50MB"}
                                          </p>
                                      </div>
                                  </div>
                              </div>

                              <div className="grid grid-cols-2 gap-8">
                                  <div className="space-y-4">
                                      <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Hiển thị</label>
                                      <select 
                                          value={newDoc.visibility}
                                          onChange={(e) => setNewDoc({...newDoc, visibility: e.target.value})}
                                          className="w-full h-14 border-b border-zinc-100 focus:border-black outline-none font-bold uppercase tracking-widest text-[11px] transition-all cursor-pointer appearance-none bg-transparent"
                                      >
                                          <option value="public">Công khai</option>
                                          <option value="private">Riêng tư</option>
                                      </select>
                                  </div>
                                  <div className="space-y-4">
                                      <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Tình trạng</label>
                                      <select 
                                          value={newDoc.status}
                                          onChange={(e) => setNewDoc({...newDoc, status: e.target.value})}
                                          className="w-full h-14 border-b border-zinc-100 focus:border-black outline-none font-bold uppercase tracking-widest text-[11px] transition-all cursor-pointer appearance-none bg-transparent"
                                      >
                                          <option value="published">Xuất bản</option>
                                          <option value="draft">Bản nháp</option>
                                      </select>
                                  </div>
                              </div>
                          </div>
                      </div>
                  </div>

                  <div className="p-10 bg-zinc-50/50 border-t border-zinc-100">
                      <button 
                          onClick={handleCreateDocument}
                          disabled={isCreating || !file || !newDoc.title}
                          className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.3em] hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center justify-center gap-4 rounded-sm disabled:opacity-30"
                      >
                          {isCreating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
                          Khởi tạo ngay
                      </button>
                  </div>
            </div>
          </div>
        )}

      <div 
        className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
              Kho tài liệu
            </h1>
            <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
              Quản trị tài liệu & Lưu trữ tri thức <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
            </p>
          </div>
          <div className="flex items-center gap-4">
             <div className="hidden md:flex items-center gap-3 px-6 py-3 bg-zinc-50 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-400 rounded-sm">
                <Database className="w-4 h-4" /> Hệ thống lưu trữ DocLib
             </div>
             <button 
               onClick={fetchData}
               disabled={isRefreshing}
               className="h-14 px-8 border border-zinc-100 text-black text-[11px] font-bold uppercase hover:bg-zinc-50 transition-all active:scale-[0.98] flex items-center gap-4 rounded-sm"
             >
               {isRefreshing ? <Loader2 className="w-5 h-5 animate-spin" /> : <RefreshCcw className="w-5 h-5" />}
             </button>
             <button 
               onClick={() => setCreateDocModal(true)}
               className="h-14 px-12 bg-black text-white text-[11px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center gap-4 rounded-sm"
             >
               <Plus className="w-5 h-5" />
               Thêm tài liệu
             </button>
          </div>
        </div>
      </div>

        <div 
          className="transition-all duration-300 delay-75 space-y-10" 
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
            <div className="relative group">
                <div className="absolute left-6 top-1/2 -translate-y-1/2">
                    <Search className="w-5 h-5 text-zinc-200 group-focus-within:text-black transition-colors" />
                </div>
                <input 
                  type="text"
                  placeholder="Tìm kiếm theo tiêu đề hoặc tác giả"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full h-16 pl-16 pr-8 bg-white border border-zinc-100 focus:border-black outline-none font-bold text-lg tracking-tight transition-all placeholder:text-zinc-100 rounded-sm"
                />
            </div>

            <div className="bg-white border border-zinc-100 overflow-hidden rounded-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-zinc-50/50 border-b border-zinc-100 text-zinc-300 text-[9px] font-bold uppercase tracking-[0.2em]">
                      <th className="px-10 py-6">Tài liệu / Tác giả</th>
                      <th className="px-10 py-6 text-center">Tương tác</th>
                      <th className="px-10 py-6">Trạng thái</th>
                      <th className="px-10 py-6 text-right">Hành động</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-50">
                    {filteredDocuments.map((doc: any) => (
                      <tr key={doc._id || doc.id} className="hover:bg-zinc-50/20 transition-all duration-300 group">
                        <td className="px-10 py-10">
                            <div className="flex items-center gap-8">
                                <div className="w-14 h-20 bg-zinc-50 border border-zinc-100 flex items-center justify-center rounded-sm shrink-0">
                                    <FileText className="w-6 h-6 text-zinc-100 group-hover:text-black transition-colors" />
                                </div>
                                <div className="flex flex-col gap-2 min-w-0">
                                    <span className="font-bold text-black text-base tracking-tighter truncate max-w-md">{doc.title}</span>
                                    <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2">
                                        {doc.publisher_name || "DocLib"} <ChevronRight className="w-3 h-3" /> {doc.category || "Tài liệu"}
                                    </span>
                                </div>
                            </div>
                        </td>
                        <td className="px-10 py-10 text-center">
                            <div className="flex flex-col gap-1">
                                <span className="font-bold text-black text-lg">{(doc.views || 0).toLocaleString()}</span>
                                <span className="text-[9px] font-bold text-zinc-200 uppercase tracking-widest">Lượt xem</span>
                            </div>
                        </td>
                        <td className="px-10 py-10">
                            <span className={`inline-block px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded-sm border ${
                                doc.status === 'published' ? 'bg-black text-white border-black' : 
                                'bg-white text-zinc-300 border-zinc-100'
                            }`}>
                                {doc.status === 'published' ? 'Đã đăng' : 'Bản nháp'}
                            </span>
                        </td>
                        <td className="px-10 py-10 text-right">
                            <div className="flex justify-end gap-3">
                                <button 
                                    onClick={() => window.open(`/documents/viewer/${doc._id || doc.id}`, '_blank')}
                                    className="h-12 w-12 border border-zinc-100 flex items-center justify-center text-zinc-200 hover:text-black hover:border-black transition-all rounded-sm"
                                    title="Xem tài liệu"
                                >
                                    <Eye className="w-4 h-4" />
                                </button>
                                <button 
                                    onClick={() => setConfirmModal({ show: true, title: "Xác nhận xóa tài liệu?", docId: doc._id || doc.id })}
                                    className="h-12 w-12 border border-zinc-100 flex items-center justify-center text-zinc-100 hover:text-red-500 hover:border-red-500 transition-all rounded-sm"
                                    title="Xóa tài liệu"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </td>
                      </tr>
                    ))}
                    {filteredDocuments.length === 0 && (
                        <tr>
                            <td colSpan={4} className="py-48 text-center border-dashed border-2 border-zinc-50 rounded-sm">
                                <div className="flex flex-col items-center gap-6">
                                    <Search className="w-16 h-16 text-zinc-50 stroke-[1]" />
                                    <p className="text-[11px] font-bold text-zinc-200 uppercase tracking-[0.2em]">Không tìm thấy tài liệu phù hợp</p>
                                </div>
                            </td>
                        </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
        </div>
      </div>
    </AppShell>
  );
}
