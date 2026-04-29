"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { getToken, API_URL } from "@/app/lib/api";
import {
  AlertTriangle,
  FileText,
  PlusCircle,
  Eye,
  Trash2,
  RefreshCcw,
  Loader2,
  X,
  Search,
  Upload,
  FileCheck,
  ShieldCheck,
  Plus
} from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";
import { Notification } from "@/app/components/NotificationToast";
import AppShell from "@/app/components/AppShell";

export default function DocumentManagementPage() {
  const { user, isLoading } = useAuth() as any;
  const [documents, setDocuments] = useState<any[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [confirmModal, setConfirmModal] = useState<{ show: boolean; title: string; onConfirm: () => void } | null>(null);
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

  const isAdmin = user?.role === "admin";

  const fetchData = useCallback(async () => {
    if (!user) return;
    setIsRefreshing(true);
    try {
      const headers = { Authorization: `Bearer ${getToken()}` };
      const endpoint = isAdmin ? `${API_URL}/admin/documents` : `${API_URL}/author/documents`;
      const res = await fetch(endpoint, { headers });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.data || data);
      }
    } catch (err: any) {
      console.error("Lỗi tải kho tài liệu:", err);
    } finally {
      setIsRefreshing(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [user, isAdmin]);

  useEffect(() => {
    if (isLoading) return;
    if (!user || (user.role !== "admin" && user.role !== "author")) {
      window.location.href = "/";
    } else {
      fetchData();
      if (user.role === "admin") {
        setNewDoc(prev => ({ ...prev, publisher_name: "DocLib" }));
      } else {
        setNewDoc(prev => ({ ...prev, publisher_name: user.full_name || "" }));
      }
    }
  }, [user, isLoading, fetchData]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      if (!newDoc.title) {
        const name = e.target.files[0].name.split(".")[0];
        setNewDoc(prev => ({ ...prev, title: name, slug: name.toLowerCase().replace(/\s+/g, "-") }));
      }
    }
  };

  const [isCreating, setIsCreating] = useState(false);

  const handleCreateDocument = async () => {
    if (!newDoc.title || !file) {
      setNotification({ type: "error", text: "Vui lòng nhập tiêu đề và chọn tệp tin." });
      return;
    }

    setIsCreating(true);
    try {
        let file_url = "";
        const formData = new FormData();
        formData.append("file", file);
        
        const uploadRes = await fetch(`${API_URL}/upload/document`, {
            method: "POST",
            headers: { Authorization: `Bearer ${getToken()}` },
            body: formData
        });
        
        if (uploadRes.ok) {
            const uploadData = await uploadRes.json();
            file_url = uploadData.data.url;
            console.log("File uploaded successfully");
        } else {
            setNotification({ type: "error", text: "Lỗi tải tệp tin lên hệ thống." });
            setIsCreating(false);
            return;
        }

        const submissionData = {
          ...newDoc,
          file_url,
          slug: newDoc.slug || newDoc.title.toLowerCase().replace(/\s+/g, "-") + "-" + Date.now().toString().slice(-4),
          publish_at: newDoc.status === 'scheduled' ? newDoc.publish_at : null
        };

        console.log("Submitting document data:", submissionData);

        const endpoint = isAdmin ? `${API_URL}/admin/documents` : `${API_URL}/documents/`;
        const res = await fetch(endpoint, {
            method: "POST",
            headers: { 
                Authorization: `Bearer ${getToken()}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(submissionData),
        });

        if (res.ok) {
            setNotification({ type: "success", text: "Đã tạo tài liệu mới thành công." });
            setCreateDocModal(false);
            setNewDoc({ title: "", description: "", slug: "", category: "Chưa phân loại", pages_count: 0, publisher_name: isAdmin ? "DocLib" : (user?.full_name || ""), price_dl: 0, visibility: "public", status: "published", publish_at: "", is_featured: false, is_protected: true });
            setFile(null);
            fetchData();
        } else {
            const error = await res.json();
            setNotification({ type: "error", text: error.message || "Không thể tạo tài liệu." });
        }
    } catch (err) {
        console.error("Lỗi tạo tài liệu:", err);
        setNotification({ type: "error", text: "Lỗi hệ thống khi tạo tài liệu." });
    } finally {
        setIsCreating(false);
    }
  };

  const deleteDocument = async (docId: string) => {
    setConfirmModal({
        show: true,
        title: "Xác nhận xóa tài liệu này?",
        onConfirm: async () => {
            try {
                const endpoint = isAdmin ? `${API_URL}/admin/documents/${docId}` : `${API_URL}/author/documents/${docId}`;
                const res = await fetch(endpoint, {
                    method: "DELETE",
                    headers: { Authorization: `Bearer ${getToken()}` },
                });
                if (res.ok) {
                    setNotification({ type: "success", text: "Đã xóa tài liệu khỏi hệ thống." });
                    fetchData();
                }
            } catch (err) {
                console.error("Lỗi xóa tài liệu:", err);
            }
            setConfirmModal(null);
        }
    });
  };

  const filteredDocuments = documents.filter(doc => 
    doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (doc.publisher_name || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading || !user) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
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

        {/* Confirmation Modal */}
        {confirmModal?.show && (
          <div className="fixed inset-0 z-[2000] bg-black/80 flex items-center justify-center p-6 animate-in fade-in duration-300 backdrop-blur-md">
            <div className="bg-white border border-zinc-200 w-full max-w-md animate-in zoom-in-95 duration-300 rounded-none shadow-2xl">
              <div className="p-12 text-center">
                <AlertTriangle className="w-12 h-12 text-black mx-auto mb-8 stroke-[1.5]" />
                <h3 className="text-2xl font-bold mb-4 tracking-tighter">{confirmModal.title}</h3>
                <p className="text-[11px] text-zinc-400 font-bold uppercase tracking-widest mb-12 italic leading-relaxed">Dữ liệu sẽ bị xóa vĩnh viễn khỏi các phân vùng lưu trữ.</p>
                <div className="flex gap-4">
                  <button
                    onClick={() => setConfirmModal(null)}
                    className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black hover:border-black transition-all"
                  >
                    Hủy bỏ
                  </button>
                  <button
                    onClick={confirmModal.onConfirm}
                    className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-95"
                  >
                    Xác nhận xóa
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Creation Modal - RESTORED ADMIN VERSION */}
        {createDocModal && (
          <div className="fixed inset-0 z-[2000] bg-black/80 flex items-center justify-center p-6 animate-in fade-in duration-500 backdrop-blur-md">
            <div className="bg-white w-full max-w-3xl animate-in zoom-in-95 duration-500 rounded-none shadow-[0_0_100px_rgba(0,0,0,0.2)] overflow-hidden flex flex-col max-h-[92vh]">
                  <div className="p-10 border-b border-zinc-50 relative">
                      <button 
                          onClick={() => setCreateDocModal(false)} 
                          className="absolute right-10 top-1/2 -translate-y-1/2 text-zinc-200 hover:text-black transition-colors"
                      >
                          <X className="w-8 h-8 stroke-[1]" />
                      </button>
                      <h3 className="text-3xl font-bold tracking-tighter uppercase">{isAdmin ? "Thêm tài liệu hệ thống" : "Khởi tạo tài liệu mới"}</h3>
                  </div>
                  
                  <div className="flex-1 overflow-y-auto p-10 space-y-12 no-scrollbar">
                      <div className="space-y-8">
                          <div className="space-y-4">
                              <label className="text-xs font-bold text-black uppercase tracking-widest">Tiêu đề tài liệu</label>
                              <input 
                                  type="text" 
                                  value={newDoc.title}
                                  onChange={(e) => setNewDoc({...newDoc, title: e.target.value})}
                                  placeholder="Nhập tên tài liệu"
                                  className="w-full h-16 px-6 bg-white border border-zinc-100 focus:border-black outline-none font-bold text-lg transition-all" 
                              />
                          </div>

                          <div className="grid grid-cols-2 gap-10">
                              <div className="space-y-4">
                                  <label className="text-xs font-bold text-black uppercase tracking-widest">Đường dẫn</label>
                                  <input 
                                      type="text" 
                                      value={newDoc.slug}
                                      onChange={(e) => setNewDoc({...newDoc, slug: e.target.value})}
                                      placeholder="duong-dan-tai-lieu"
                                      className="w-full h-16 px-6 bg-white border border-zinc-100 focus:border-black outline-none font-bold transition-all text-sm" 
                                  />
                              </div>
                              <div className="space-y-4">
                                  <label className="text-xs font-bold text-black uppercase tracking-widest">Người đăng</label>
                                  <input 
                                      type="text" 
                                      value={newDoc.publisher_name}
                                      onChange={(e) => !isAdmin && setNewDoc({...newDoc, publisher_name: e.target.value})}
                                      readOnly={isAdmin}
                                      className={`w-full h-16 px-6 bg-white border border-zinc-100 outline-none font-bold transition-all ${isAdmin ? 'text-zinc-300 bg-zinc-50' : 'focus:border-black'}`} 
                                  />
                              </div>
                          </div>

                          <div className="grid grid-cols-3 gap-10">
                              <div className="space-y-4">
                                  <label className="text-xs font-bold text-black uppercase tracking-widest">Thể loại</label>
                                  <select 
                                      value={newDoc.category}
                                      onChange={(e) => setNewDoc({...newDoc, category: e.target.value})}
                                      className="w-full h-16 px-6 bg-white border border-zinc-100 focus:border-black outline-none font-bold uppercase tracking-widest text-[11px] transition-all cursor-pointer appearance-none"
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
                                  <label className="text-xs font-bold text-black uppercase tracking-widest">Số trang</label>
                                  <input 
                                      type="number" 
                                      className="w-full h-16 bg-white border border-zinc-100 px-6 text-sm font-bold focus:outline-none focus:border-black transition-all"
                                      value={newDoc.pages_count}
                                      onChange={(e) => setNewDoc({ ...newDoc, pages_count: parseInt(e.target.value) || 0 })}
                                  />
                              </div>
                              <div className="space-y-4">
                                  <label className="text-xs font-bold text-black uppercase tracking-widest">Giá bán</label>
                                  <input 
                                      type="number" 
                                      className="w-full h-16 bg-white border border-zinc-100 px-6 text-sm font-bold focus:outline-none focus:border-black transition-all"
                                      value={newDoc.price_dl}
                                      onChange={(e) => setNewDoc({ ...newDoc, price_dl: parseInt(e.target.value) || 0 })}
                                  />
                              </div>
                          </div>

                          <div className="grid grid-cols-2 gap-10">
                              <div className="space-y-4">
                                  <label className="text-xs font-bold text-black uppercase tracking-widest">Trạng thái xuất bản</label>
                                  <select 
                                      value={newDoc.status}
                                      onChange={(e) => setNewDoc({...newDoc, status: e.target.value})}
                                      className="w-full h-16 px-6 bg-white border border-zinc-100 focus:border-black outline-none font-bold uppercase tracking-widest text-[11px] transition-all cursor-pointer appearance-none"
                                  >
                                      <option value="published">Công khai ngay</option>
                                      <option value="draft">Bản nháp</option>
                                      <option value="scheduled">Hẹn giờ đăng</option>
                                  </select>
                              </div>
                              <div className="space-y-4">
                                  <label className="text-xs font-bold text-black uppercase tracking-widest">Thời gian đăng</label>
                                  <input 
                                      type="datetime-local" 
                                      disabled={newDoc.status !== 'scheduled'}
                                      className={`w-full h-16 px-6 bg-white border border-zinc-100 outline-none font-bold text-sm transition-all ${newDoc.status === 'scheduled' ? 'focus:border-black' : 'opacity-30 cursor-not-allowed'}`}
                                      value={newDoc.publish_at}
                                      onChange={(e) => setNewDoc({ ...newDoc, publish_at: e.target.value })}
                                  />
                              </div>
                          </div>

                          <div className="grid grid-cols-2 gap-10">
                              <div className="flex items-center justify-between p-6 border border-zinc-100">
                                  <div className="space-y-1">
                                      <p className="text-xs font-bold uppercase tracking-widest">Bảo vệ chống sao chép</p>
                                      <p className="text-[9px] text-zinc-400 font-bold uppercase">Ngăn chặn tải về và copy</p>
                                  </div>
                                  <button 
                                      onClick={() => setNewDoc({...newDoc, is_protected: !newDoc.is_protected})}
                                      className={`w-12 h-6 transition-all relative ${newDoc.is_protected ? 'bg-black' : 'bg-zinc-100'}`}
                                  >
                                      <div className={`absolute top-1 w-4 h-4 bg-white transition-all ${newDoc.is_protected ? 'right-1' : 'left-1'}`} />
                                  </button>
                              </div>
                              <div className="flex items-center justify-between p-6 border border-zinc-100">
                                  <div className="space-y-1">
                                      <p className="text-xs font-bold uppercase tracking-widest">Nổi bật</p>
                                      <p className="text-[9px] text-zinc-400 font-bold uppercase">Ưu tiên hiển thị</p>
                                  </div>
                                  <button 
                                      onClick={() => setNewDoc({...newDoc, is_featured: !newDoc.is_featured})}
                                      className={`w-12 h-6 transition-all relative ${newDoc.is_featured ? 'bg-black' : 'bg-zinc-100'}`}
                                  >
                                      <div className={`absolute top-1 w-4 h-4 bg-white transition-all ${newDoc.is_featured ? 'right-1' : 'left-1'}`} />
                                  </button>
                              </div>
                          </div>
                      </div>

                      <div className="space-y-4">
                          <label className="text-xs font-bold text-black uppercase tracking-widest">Tệp đính kèm (PDF/EPUB)</label>
                          <input 
                              type="file" 
                              ref={fileInputRef} 
                              onChange={handleFileChange} 
                              className="hidden" 
                              accept=".pdf,.epub"
                          />
                          <div 
                              onClick={() => fileInputRef.current?.click()}
                              className={`border border-zinc-100 p-10 flex flex-col items-center justify-center gap-6 group hover:border-black transition-all cursor-pointer ${file ? 'bg-black text-white' : 'bg-zinc-50/20'}`}
                          >
                              <div className={`w-20 h-20 flex items-center justify-center transition-all shadow-sm ${file ? 'bg-white text-black' : 'bg-white text-zinc-300 group-hover:bg-black group-hover:text-white'}`}>
                                  {file ? <FileCheck className="w-8 h-8" /> : <Upload className="w-8 h-8" />}
                              </div>
                              <div className="text-center">
                                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] mb-1">
                                      {file ? file.name : "Nhấp để tải lên hoặc kéo thả"}
                                  </p>
                                  <p className={`text-[9px] font-bold uppercase tracking-widest italic ${file ? 'text-zinc-400' : 'text-zinc-300'}`}>
                                      {file ? `${(file.size / (1024 * 1024)).toFixed(2)} MB` : "Tối đa 50MB per file"}
                                  </p>
                              </div>
                          </div>
                      </div>

                      <div className="space-y-4">
                          <label className="text-xs font-bold text-black uppercase tracking-widest">Mô tả tóm tắt</label>
                          <textarea 
                              value={newDoc.description}
                              onChange={(e) => setNewDoc({...newDoc, description: e.target.value})}
                              className="w-full h-48 p-8 bg-white border border-zinc-100 focus:border-black outline-none font-medium text-sm transition-all resize-none no-scrollbar leading-relaxed" 
                          />
                      </div>
                  </div>

                  <div className="p-10 bg-white border-t border-zinc-50">
                      <button 
                          onClick={handleCreateDocument}
                          disabled={isCreating}
                          className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] hover:bg-zinc-800 transition-all shadow-xl shadow-black/10 active:scale-[0.98] flex items-center justify-center gap-4"
                      >
                          {isCreating ? (
                              <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Đang khởi tạo
                              </>
                          ) : "Khởi tạo tài liệu ngay"}
                      </button>
                  </div>
            </div>
          </div>
        )}

        {/* Main UI Header */}
        <div 
          className="mb-10 border-b border-zinc-100 pb-10 transition-all duration-700"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
        >
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="space-y-3">
              <h1 className="text-5xl font-bold tracking-tighter leading-none text-black mb-3">
                Kho tài liệu
              </h1>
              <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
                ROOT KNOWLEDGE REPOSITORY <ShieldCheck className="w-3.5 h-3.5 text-zinc-100" />
              </p>
            </div>
            
            <div className="flex items-center gap-4">
                <button 
                  onClick={fetchData}
                  disabled={isRefreshing}
                  className="h-14 px-8 border border-zinc-100 text-black text-[11px] font-bold uppercase hover:bg-zinc-50 transition-all active:scale-95 flex items-center gap-4"
                >
                  {isRefreshing ? <Loader2 className="w-5 h-5 animate-spin" /> : <RefreshCcw className="w-5 h-5" />}
                </button>
                <button 
                  onClick={() => setCreateDocModal(true)}
                  className="h-14 px-12 bg-black text-white text-[11px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all active:scale-95 flex items-center gap-4 rounded-none shadow-xl shadow-black/5"
                >
                  <Plus className="w-5 h-5" />
                  Thêm tài liệu mới
                </button>
            </div>
          </div>
        </div>

        <div className="transition-all duration-700 delay-300" style={{ opacity: visible ? 1 : 0 }}>
            <div className="relative group mb-10">
                <div className="absolute left-6 top-1/2 -translate-y-1/2">
                    <Search className="w-5 h-5 text-zinc-300 group-focus-within:text-black transition-colors" />
                </div>
                <input 
                  type="text"
                  placeholder=""
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full h-16 pl-16 pr-8 bg-white border border-zinc-100 focus:border-black outline-none font-bold text-lg tracking-tight transition-all placeholder:text-zinc-100"
                />
            </div>

            <div className="bg-white border border-zinc-100 overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-zinc-50/50 border-b border-zinc-100 text-zinc-300 text-[9px] font-bold uppercase tracking-[0.2em]">
                      <th className="px-10 py-6">Tài liệu / Tác giả</th>
                      <th className="px-10 py-6 text-center">Lượt xem</th>
                      <th className="px-10 py-6">Trạng thái</th>
                      <th className="px-10 py-6 text-right">Hành động</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-50">
                    {filteredDocuments.map((doc: any) => (
                      <tr key={doc._id} className="hover:bg-zinc-50/20 transition-colors group">
                        <td className="px-10 py-8">
                            <div className="flex items-center gap-6">
                                <div className="w-12 h-16 bg-zinc-50 border border-zinc-100 flex items-center justify-center">
                                    <FileText className="w-5 h-5 text-zinc-100 group-hover:text-black transition-colors" />
                                </div>
                                <div className="flex flex-col gap-1 max-w-xs">
                                    <span className="font-bold text-black text-sm tracking-tight truncate">{doc.title}</span>
                                    <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                                        {doc.publisher_name || "DocLib"}
                                    </span>
                                </div>
                            </div>
                        </td>
                        <td className="px-10 py-8 text-center font-bold text-black">{doc.views || 0}</td>
                        <td className="px-10 py-8">
                            <span className={`inline-block px-3 py-1 text-[9px] font-bold uppercase tracking-widest border ${
                                doc.status === 'published' ? 'bg-green-50 text-green-600 border-green-100' : 
                                doc.status === 'draft' ? 'bg-yellow-50 text-yellow-600 border-yellow-100' :
                                'bg-red-50 text-red-600 border-red-100'
                            }`}>
                                {doc.status || 'draft'}
                            </span>
                        </td>
                        <td className="px-10 py-8 text-right">
                            <div className="flex justify-end gap-2">
                                <button 
                                    onClick={() => window.location.href = `/documents/viewer/${doc._id}`}
                                    className="h-10 w-10 border border-zinc-50 flex items-center justify-center text-zinc-300 hover:text-black hover:border-black transition-all"
                                >
                                    <Eye className="w-4 h-4" />
                                </button>
                                <button 
                                    onClick={() => deleteDocument(doc._id)}
                                    className="h-10 w-10 border border-zinc-100 flex items-center justify-center text-zinc-200 hover:text-red-500 hover:border-red-500 transition-all"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </td>
                      </tr>
                    ))}
                    {filteredDocuments.length === 0 && (
                        <tr>
                            <td colSpan={4} className="py-40 text-center text-[10px] font-bold text-zinc-200 uppercase tracking-widest">
                                Không tìm thấy tài liệu phù hợp
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
