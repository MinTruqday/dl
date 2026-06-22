"use client";

import { useEffect, useState } from "react";
import {
  getMyDocumentsAPI,
  updateDRMSettingsAPI,
  updateTagsAPI,
  updateDocumentAPI,
  getFoldersAPI,
  transferDocumentAPI,
} from "@/features/content/services/document_metadata.service";
import {
  getCollaboratorsAPI,
  inviteCollaboratorAPI,
  removeCollaboratorAPI,
} from "@/features/content/services/collaboration_sync.service";
import {
  createCouponAPI,
  getCouponsAPI,
} from "@/features/finance/services/discount_coupon.service";
import { ingestDocumentAPI } from "@/features/ai/services/rag_pipeline.service";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Loader2,
  Settings,
  Hash,
  Folder,
  Brain,
  Shield,
  Users,
  Trash2,
  Tag,
  X,
  BookOpen,
  Plus,
  Send,
  Ticket,
  ArrowRightLeft,
  ChevronDown,
} from "lucide-react";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
  ModalDescription,
} from "@/shared/components/ui/Modal";

export default function ConfigPage() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [visible, setVisible] = useState(false);

  const selectedDocument = documents.find(
    (d) => (d._id || d.id) === selectedDocumentId,
  );

  // States from Config
  const [docTags, setDocTags] = useState<string[]>([]);
  const [newTagInput, setNewTagInput] = useState("");
  const [folders, setFolders] = useState<any[]>([]);
  const [isIngesting, setIsIngesting] = useState(false);

  const [drmCopy, setDrmCopy] = useState(false);
  const [drmSearch, setDrmSearch] = useState(false);
  const [savingDrm, setSavingDrm] = useState(false);

  const [collaborators, setCollaborators] = useState<any[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [loadingCollabs, setLoadingCollabs] = useState(false);

  const [coupons, setCoupons] = useState<any[]>([]);
  const [newCouponCode, setNewCouponCode] = useState("");
  const [newCouponDiscount, setNewCouponDiscount] = useState(10);
  const [newCouponQuantity, setNewCouponQuantity] = useState(50);

  const [transferUserId, setTransferUserId] = useState("");
  const [isTransferring, setTransferUserIdLoading] = useState(false);
  const [confirmTransfer, setConfirmTransfer] = useState(false);

  useEffect(() => {
    fetchInitData();
  }, []);

  const fetchInitData = async () => {
    setLoadingDocs(true);
    try {
      const [docsData, foldersData] = await Promise.all([
        getMyDocumentsAPI(),
        getFoldersAPI().catch(() => ({ data: [] })),
      ]);
      const list = docsData.data || docsData || [];
      const folderList = (foldersData as any).data || foldersData || [];

      setDocuments(list);
      setFolders(folderList);

      if (list.length > 0) {
        setSelectedDocumentId(list[0]._id || list[0].id);
      }
    } catch (e: any) {
      showToast("Lỗi tải danh sách tác phẩm", "error");
    } finally {
      setLoadingDocs(false);
      requestAnimationFrame(() => setVisible(true));
    }
  };

  useEffect(() => {
    if (selectedDocument) {
      setDrmCopy(selectedDocument.drm_settings?.disable_copy || false);
      setDrmSearch(selectedDocument.drm_settings?.hide_from_search || false);
      setDocTags(selectedDocument.tags || []);

      fetchCollaborators();
      fetchCoupons();
    }
  }, [selectedDocumentId, selectedDocument]);

  const fetchCollaborators = async () => {
    if (!selectedDocumentId) return;
    setLoadingCollabs(true);
    try {
      const data = await getCollaboratorsAPI(selectedDocumentId);
      setCollaborators(data.data || data || []);
    } catch (err: any) {
      setCollaborators([]);
    } finally {
      setLoadingCollabs(false);
    }
  };

  const fetchCoupons = async () => {
    try {
      const data = await getCouponsAPI();
      setCoupons(data.data || data || []);
    } catch (err: any) {
      setCoupons([]);
    }
  };

  const handleAddTag = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && newTagInput.trim() && selectedDocumentId) {
      const tag = newTagInput.trim();
      if (!docTags.includes(tag)) {
        const newTags = [...docTags, tag];
        try {
          await updateTagsAPI(selectedDocumentId, newTags);
          setDocTags(newTags);
          setNewTagInput("");
          fetchInitData();
        } catch (err: any) {
          showToast(err.message || "Thêm thẻ thất bại", "error");
        }
      }
    }
  };

  const handleRemoveTag = async (tagToRemove: string) => {
    if (!selectedDocumentId) return;
    const newTags = docTags.filter((t) => t !== tagToRemove);
    try {
      await updateTagsAPI(selectedDocumentId, newTags);
      setDocTags(newTags);
      fetchInitData();
    } catch (err: any) {
      showToast(err.message || "Xóa thẻ thất bại", "error");
    }
  };

  const handleSaveDRM = async () => {
    if (!selectedDocumentId) return;
    setSavingDrm(true);
    try {
      await updateDRMSettingsAPI(selectedDocumentId, {
        disable_copy: drmCopy,
        hide_from_search: drmSearch,
      });
      showToast("Đã cập nhật bảo vệ bản quyền", "success");
      fetchInitData();
    } catch (e: any) {
      showToast(e.message || "Cập nhật DRM thất bại", "error");
    } finally {
      setSavingDrm(false);
    }
  };

  const handleIngestAI = async () => {
    if (!selectedDocumentId) return;
    setIsIngesting(true);
    try {
      await ingestDocumentAPI(selectedDocumentId);
      showToast("AI đã cập nhật nội dung mới", "success");
    } catch (e: any) {
      showToast(e.message || "Đồng bộ AI thất bại", "error");
    } finally {
      setIsIngesting(false);
    }
  };

  const handleInviteCollab = async () => {
    if (!inviteEmail.trim() || !selectedDocumentId) return;
    try {
      await inviteCollaboratorAPI(selectedDocumentId, inviteEmail.trim());
      showToast("Đã gửi lời mời cộng tác", "success");
      setInviteEmail("");
      fetchCollaborators();
    } catch (e: any) {
      showToast(e.message || "Gửi lời mời thất bại", "error");
    }
  };

  const handleRemoveCollab = async (collabId: string) => {
    try {
      await removeCollaboratorAPI(collabId);
      showToast("Đã xóa cộng tác viên", "success");
      fetchCollaborators();
    } catch (e: any) {
      showToast(e.message || "Xóa cộng tác viên thất bại", "error");
    }
  };

  const handleCreateCoupon = async () => {
    if (!newCouponCode.trim()) {
      showToast("Vui lòng nhập mã ưu đãi", "error");
      return;
    }
    try {
      await createCouponAPI({
        code: newCouponCode.trim(),
        discount_percent: newCouponDiscount,
        max_uses: newCouponQuantity,
        document_id: selectedDocumentId || undefined,
      });
      showToast("Đã tạo mã ưu đãi", "success");
      setNewCouponCode("");
      fetchCoupons();
    } catch (e: any) {
      showToast(e.message || "Tạo mã ưu đãi thất bại", "error");
    }
  };

  const executeTransfer = async () => {
    if (!transferUserId.trim() || !selectedDocumentId) return;
    setTransferUserIdLoading(true);
    try {
      await transferDocumentAPI(selectedDocumentId, transferUserId.trim());
      showToast("Đã chuyển nhượng tác phẩm thành công", "success");
      setTransferUserId("");
      setConfirmTransfer(false);
      fetchInitData();
    } catch (e: any) {
      showToast(e.message || "Chuyển nhượng tác phẩm thất bại", "error");
    } finally {
      setTransferUserIdLoading(false);
    }
  };

  if (loadingDocs) {
    return (
      <div className="h-full min-h-[400px] flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400 mb-4" />
        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Đang tải cấu hình...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-zinc-100 pb-4 mb-6 shrink-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
          Cấu hình tác phẩm
        </h1>
        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
          Quản lý và tinh chỉnh các cài đặt cho tài liệu
        </p>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-6 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0, transitionDelay: "100ms" }}>
        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 rounded-3xl shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0 transition-all duration-300 hover:border-zinc-200">
          <div className="space-y-1.5 flex items-center gap-3">
            <div className="w-10 h-10 bg-zinc-50 border border-zinc-100 rounded-2xl flex items-center justify-center shrink-0">
              <Settings className="w-5 h-5 text-black" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">
                Chọn tác phẩm
              </h2>
              <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                Tác phẩm cần thiết lập
              </p>
            </div>
          </div>
          <div className="relative w-full sm:w-72">
            <BookOpen className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <select
              value={selectedDocumentId}
              onChange={(e) => setSelectedDocumentId(e.target.value)}
              className="w-full h-11 pl-10 pr-10 border border-zinc-200 text-sm font-bold text-zinc-900 focus:outline-none focus:border-black bg-zinc-50 focus:bg-white rounded-2xl appearance-none transition-all duration-200 shadow-sm cursor-pointer"
            >
              {documents.length === 0 && <option value="" disabled>Chưa có tác phẩm</option>}
              {documents.map((d) => (
                <option key={d.id || d._id} value={d.id || d._id}>
                  {d.title || "Chưa có tiêu đề"}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 pointer-events-none" />
          </div>
        </div>

        {selectedDocumentId ? (
          <div className="flex-1 min-h-0 pb-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Left Column */}
            <div className="space-y-6">
              
              {/* Phân loại & Thẻ */}
              <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 rounded-3xl shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center gap-2 mb-4">
                  <Hash className="w-4 h-4 text-black" />
                  <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">Phân loại & Thẻ</h3>
                </div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-4 leading-relaxed">
                  Sử dụng thẻ để phân loại tác phẩm.
                </p>
                <div className="flex flex-wrap gap-2 mb-4 min-h-[32px]">
                  {docTags.map((tag) => (
                    <span
                      key={tag}
                      className="flex items-center gap-1 border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest text-zinc-700 rounded-lg group"
                    >
                      {tag}
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="text-zinc-400 group-hover:text-red-500 transition-colors"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                  {docTags.length === 0 && (
                    <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Chưa có thẻ nào</span>
                  )}
                </div>
                <div className="relative">
                  <Tag className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    type="text"
                    value={newTagInput}
                    onChange={(e) => setNewTagInput(e.target.value)}
                    onKeyDown={handleAddTag}
                    placeholder="Nhập tên thẻ & Enter (VD: TIENHIEP)"
                    className="w-full h-11 pl-10 pr-4 border border-zinc-200 text-xs font-bold rounded-2xl outline-none focus:border-black bg-zinc-50 focus:bg-white transition-all shadow-sm"
                  />
                </div>
              </div>

              {/* Thư mục làm việc */}
              <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 rounded-3xl shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center gap-2 mb-4">
                  <Folder className="w-4 h-4 text-black" />
                  <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">Thư mục làm việc</h3>
                </div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-4 leading-relaxed">
                  Di chuyển tác phẩm này vào thư mục.
                </p>
                <div className="relative">
                  <Folder className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <select
                    value={selectedDocument?.folder_id || ""}
                    onChange={async (e) => {
                      const fId = e.target.value;
                      try {
                        await updateDocumentAPI(selectedDocumentId, {
                          folder_id: fId || null,
                        });
                        showToast("Đã di chuyển tác phẩm thành công", "success");
                        fetchInitData();
                      } catch (err: any) {
                        showToast("Không thể di chuyển", "error");
                      }
                    }}
                    className="w-full h-11 pl-10 pr-10 border border-zinc-200 text-sm font-bold rounded-2xl outline-none bg-zinc-50 focus:bg-white focus:border-black appearance-none transition-all shadow-sm cursor-pointer"
                  >
                    <option value="">(Thư mục gốc)</option>
                    {folders.map((f) => (
                      <option key={f._id || f.id} value={f._id || f.id}>
                        {f.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 pointer-events-none" />
                </div>
              </div>

              {/* DRM */}
              <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 rounded-3xl shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-black" />
                    <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">Bảo vệ bản quyền</h3>
                  </div>
                  <button
                    onClick={handleSaveDRM}
                    disabled={savingDrm || !selectedDocumentId}
                    className="h-8 px-4 bg-black text-white text-[9px] font-bold uppercase tracking-widest rounded-xl disabled:opacity-50 transition-all hover:scale-105 shadow-sm"
                  >
                    {savingDrm ? <Loader2 className="w-3 h-3 animate-spin mx-auto" /> : "Lưu DRM"}
                  </button>
                </div>
                <div className="space-y-4 bg-zinc-50 p-4 rounded-2xl border border-zinc-100">
                  <label className="flex items-center justify-between cursor-pointer group">
                    <span className="text-[10px] font-bold text-zinc-700 uppercase tracking-widest">Chống bôi đen & Copy</span>
                    <div className={`w-10 h-5 border rounded-full flex items-center p-0.5 transition-colors ${drmCopy ? "bg-black border-black" : "bg-white border-zinc-300"}`}>
                      <div className={`w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${drmCopy ? "translate-x-5" : "translate-x-0 bg-zinc-300"}`} />
                    </div>
                    <input type="checkbox" className="hidden" checked={drmCopy} onChange={(e) => setDrmCopy(e.target.checked)} />
                  </label>
                  <div className="h-px bg-zinc-200" />
                  <label className="flex items-center justify-between cursor-pointer group">
                    <span className="text-[10px] font-bold text-zinc-700 uppercase tracking-widest">Ẩn khỏi tìm kiếm (SEO)</span>
                    <div className={`w-10 h-5 border rounded-full flex items-center p-0.5 transition-colors ${drmSearch ? "bg-black border-black" : "bg-white border-zinc-300"}`}>
                      <div className={`w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${drmSearch ? "translate-x-5" : "translate-x-0 bg-zinc-300"}`} />
                    </div>
                    <input type="checkbox" className="hidden" checked={drmSearch} onChange={(e) => setDrmSearch(e.target.checked)} />
                  </label>
                </div>
              </div>

            </div>

            {/* Right Column */}
            <div className="space-y-6">

              {/* AI */}
              <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 rounded-3xl shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                  <Brain className="w-24 h-24" />
                </div>
                <div className="flex items-center gap-2 mb-4 relative z-10">
                  <Brain className="w-4 h-4 text-black" />
                  <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">Trí tuệ nhân tạo</h3>
                </div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-4 leading-relaxed relative z-10">
                  Đồng bộ nội dung với hệ thống RAG để AI hỗ trợ độc giả.
                </p>
                <button
                  onClick={handleIngestAI}
                  disabled={isIngesting || !selectedDocumentId}
                  className="w-full h-11 bg-black text-white text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 rounded-2xl disabled:opacity-50 transition-all hover:scale-[1.02] shadow-md relative z-10"
                >
                  {isIngesting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Brain className="w-4 h-4" />
                  )}
                  Đồng bộ dữ liệu AI
                </button>
              </div>

              {/* Collaboration */}
              <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 rounded-3xl shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center gap-2 mb-4">
                  <Users className="w-4 h-4 text-black" />
                  <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">Cộng tác viên</h3>
                </div>
                
                <div className="flex gap-2 mb-4">
                  <div className="relative flex-1">
                    <input
                      type="email"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      placeholder="Email người cộng tác..."
                      className="w-full h-11 pl-4 pr-4 border border-zinc-200 text-xs font-bold rounded-2xl outline-none focus:border-black bg-zinc-50 focus:bg-white transition-all shadow-sm"
                    />
                  </div>
                  <button
                    onClick={handleInviteCollab}
                    disabled={!inviteEmail.trim()}
                    className="h-11 px-4 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl disabled:opacity-50 flex items-center gap-2 shadow-sm hover:scale-105 transition-transform"
                  >
                    Mời <Send className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="bg-zinc-50 border border-zinc-100 rounded-2xl p-4 max-h-[160px] overflow-y-auto custom-scrollbar">
                  {loadingCollabs ? (
                    <div className="flex justify-center p-4">
                      <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
                    </div>
                  ) : collaborators.length > 0 ? (
                    <ul className="space-y-3">
                      {collaborators.map((c: any) => (
                        <li key={c.id} className="flex justify-between items-center bg-white p-2.5 rounded-xl border border-zinc-100 shadow-sm">
                          <div className="flex flex-col">
                            <span className="text-xs font-bold text-black">{c.email || c.user_id}</span>
                            <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">{c.role}</span>
                          </div>
                          <button
                            onClick={() => handleRemoveCollab(c.id)}
                            className="w-8 h-8 flex items-center justify-center text-zinc-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="text-center p-4">
                      <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Chưa có người cộng tác</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Coupons */}
              <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 rounded-3xl shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center gap-2 mb-4">
                  <Ticket className="w-4 h-4 text-black" />
                  <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">Mã ưu đãi</h3>
                </div>
                
                <div className="grid grid-cols-3 gap-2 mb-4">
                  <input
                    type="text"
                    value={newCouponCode}
                    onChange={(e) => setNewCouponCode(e.target.value)}
                    placeholder="MÃ"
                    className="col-span-1 h-10 px-3 text-xs font-bold border border-zinc-200 rounded-xl uppercase outline-none focus:border-black bg-zinc-50"
                  />
                  <input
                    type="number"
                    value={newCouponDiscount}
                    onChange={(e) => setNewCouponDiscount(Number(e.target.value))}
                    placeholder="%"
                    className="col-span-1 h-10 px-3 text-xs font-bold border border-zinc-200 rounded-xl outline-none focus:border-black bg-zinc-50"
                    min={1} max={100}
                  />
                  <input
                    type="number"
                    value={newCouponQuantity}
                    onChange={(e) => setNewCouponQuantity(Number(e.target.value))}
                    placeholder="SL"
                    className="col-span-1 h-10 px-3 text-xs font-bold border border-zinc-200 rounded-xl outline-none focus:border-black bg-zinc-50"
                    min={1}
                  />
                  <button
                    onClick={handleCreateCoupon}
                    className="col-span-3 h-10 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-xl shadow-sm hover:bg-zinc-800 transition-colors"
                  >
                    Tạo mã ưu đãi
                  </button>
                </div>

                <div className="bg-zinc-50 border border-zinc-100 rounded-2xl p-4 max-h-[160px] overflow-y-auto custom-scrollbar">
                  {coupons.length === 0 ? (
                    <div className="text-center p-4">
                      <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Chưa có mã ưu đãi</p>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-2">
                      {coupons.map((c: any) => (
                        <div key={c.id || c._id} className="bg-white border border-zinc-100 p-2.5 rounded-xl shadow-sm flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-xs text-black bg-zinc-100 px-2 py-1 rounded-md">{c.code}</span>
                            <span className="text-[9px] bg-black text-white px-1.5 py-0.5 font-bold uppercase tracking-widest rounded-md">-{c.discount_percent}%</span>
                          </div>
                          <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">
                            Lượt: {c.used_count || 0}/{c.max_uses}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Transfer */}
              <div className="bg-red-50/50 border border-red-100 p-6 rounded-3xl shadow-sm">
                <div className="flex items-center gap-2 mb-2 text-red-600">
                  <ArrowRightLeft className="w-4 h-4" />
                  <h3 className="text-sm font-bold uppercase tracking-widest">Bàn giao tác phẩm</h3>
                </div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-red-400 mb-4 leading-relaxed">
                  Bạn sẽ mất toàn quyền kiểm soát sau khi chuyển.
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={transferUserId}
                    onChange={(e) => setTransferUserId(e.target.value)}
                    placeholder="Mã ID người nhận..."
                    className="flex-1 h-11 pl-4 pr-4 border border-red-200 text-xs font-bold rounded-2xl outline-none focus:border-red-500 bg-white shadow-sm"
                  />
                  <button
                    onClick={() => setConfirmTransfer(true)}
                    disabled={isTransferring || !selectedDocumentId || !transferUserId.trim()}
                    className="h-11 px-4 bg-red-600 text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl disabled:opacity-50 hover:bg-red-700 transition-colors shadow-sm"
                  >
                    Chuyển
                  </button>
                </div>
              </div>

            </div>
          </div>
        ) : (
          <div className="flex-1 bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl p-12 flex flex-col items-center justify-center gap-4 text-center shadow-sm">
            <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-2">
              <Settings className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
            </div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 max-w-xs">
              Vui lòng chọn một tác phẩm từ danh sách để định cấu hình
            </p>
          </div>
        )}
      </div>

      <Modal
        isOpen={confirmTransfer}
        onClose={() => setConfirmTransfer(false)}
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md p-0 shadow-xl overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6 bg-red-50/50">
          <ModalTitle className="text-sm font-bold tracking-tight text-red-600 flex items-center gap-2">
            <ArrowRightLeft className="w-5 h-5" /> Xác nhận chuyển nhượng
          </ModalTitle>
          <ModalDescription className="text-[10px] font-bold uppercase tracking-widest text-red-400 mt-1 ml-7">
            Hành động nguy hiểm
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <p className="text-xs font-medium text-zinc-700 leading-relaxed bg-zinc-50 border border-zinc-100 p-4 rounded-2xl">
            Bạn có chắc chắn muốn chuyển nhượng tác phẩm này cho ID <span className="font-bold text-black">{transferUserId}</span>? 
            <br/><br/>
            <span className="text-red-500 font-bold">Hành động này không thể hoàn tác và bạn sẽ mất toàn quyền truy cập.</span>
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => setConfirmTransfer(false)}
            className="flex-1 h-11 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-black rounded-2xl transition-all hover:scale-[1.02] shadow-sm"
          >
            Hủy bỏ
          </button>
          <button
            onClick={executeTransfer}
            disabled={isTransferring}
            className="flex-1 h-11 text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl flex items-center justify-center disabled:opacity-50 transition-all hover:scale-[1.02] shadow-md gap-2 bg-red-600 hover:bg-red-700"
          >
            {isTransferring && <Loader2 className="w-4 h-4 animate-spin" />}
            Xác nhận chuyển
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
