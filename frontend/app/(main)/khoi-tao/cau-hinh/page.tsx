"use client";

import { useEffect, useState } from "react";
import { getMyDocumentsAPI, updateDRMSettingsAPI, updateTagsAPI, updateNSFWAPI, updateDocumentAPI, getFoldersAPI, transferDocumentAPI } from "@/services/document.service";
import { getCollaboratorsAPI, inviteCollaboratorAPI, removeCollaboratorAPI } from "@/services/collaboration.service";
import { createCouponAPI, getCouponsAPI } from "@/services/coupon.service";
import { ingestDocumentAPI } from "@/services/rag.service";
import { API_URL } from "@/services/authentication.service";
import { useToast } from "@/contexts/Toast";
import { Loader2, Settings, Hash, Folder, Brain, Sparkles, Lock, Unlock, Shield, AlertTriangle, Users, Trash2, Tag, X } from "lucide-react";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from "@/components/ui/Modal";

export default function ConfigPage() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [loadingDocs, setLoadingDocs] = useState(true);

  const selectedDocument = documents.find(d => (d._id || d.id) === selectedDocumentId);

  // States from Config
  const [docTags, setDocTags] = useState<string[]>([]);
  const [newTagInput, setNewTagInput] = useState("");
  const [folders, setFolders] = useState<any[]>([]);
  const [isIngesting, setIsIngesting] = useState(false);
  const [isNsfw, setIsNsfw] = useState(false);
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
        getFoldersAPI().catch(() => ({ data: [] }))
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
    }
  };

  useEffect(() => {
    if (selectedDocument) {
      setDrmCopy(selectedDocument.drm_settings?.disable_copy || false);
      setDrmSearch(selectedDocument.drm_settings?.hide_from_search || false);
      setDocTags(selectedDocument.tags || []);
      setIsNsfw(selectedDocument.is_nsfw || false);
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
    } catch (err: any) { setCollaborators([]); }
    finally { setLoadingCollabs(false); }
  };

  const fetchCoupons = async () => {
    try {
      const data = await getCouponsAPI();
      setCoupons(data.data || data || []);
    } catch (err: any) { setCoupons([]); }
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
        } catch (err: any) { showToast(err.message || "Thêm thẻ thất bại", "error"); }
      }
    }
  };

  const handleRemoveTag = async (tagToRemove: string) => {
    if (!selectedDocumentId) return;
    const newTags = docTags.filter(t => t !== tagToRemove);
    try {
      await updateTagsAPI(selectedDocumentId, newTags);
      setDocTags(newTags);
      fetchInitData();
    } catch (err: any) { showToast(err.message || "Xóa thẻ thất bại", "error"); }
  };

  const handleToggleNSFW = async () => {
    if (!selectedDocumentId) return;
    try {
      await updateNSFWAPI(selectedDocumentId, !isNsfw);
      setIsNsfw(!isNsfw);
      fetchInitData();
      showToast("Đã cập nhật cảnh báo nội dung", "success");
    } catch (err: any) { showToast(err.message || "Cập nhật thất bại", "error"); }
  };

  const handleSaveDRM = async () => {
    if (!selectedDocumentId) return;
    setSavingDrm(true);
    try {
      await updateDRMSettingsAPI(selectedDocumentId, { disable_copy: drmCopy, hide_from_search: drmSearch });
      showToast("Đã cập nhật bảo vệ bản quyền", "success");
      fetchInitData();
    } catch (e: any) { showToast(e.message || "Cập nhật DRM thất bại", "error"); }
    finally { setSavingDrm(false); }
  };

  const handleIngestAI = async () => {
    if (!selectedDocumentId) return;
    setIsIngesting(true);
    try {
      await ingestDocumentAPI(selectedDocumentId);
      showToast("AI đã cập nhật nội dung mới", "success");
    } catch (e: any) { showToast(e.message || "Đồng bộ AI thất bại", "error"); }
    finally { setIsIngesting(false); }
  };;

  const handleInviteCollab = async () => {
    if (!inviteEmail.trim() || !selectedDocumentId) return;
    try {
      await inviteCollaboratorAPI(selectedDocumentId, inviteEmail.trim());
      showToast("Đã gửi lời mời cộng tác", "success");
      setInviteEmail("");
      fetchCollaborators();
    } catch (e: any) { showToast(e.message || "Gửi lời mời thất bại", "error"); }
  };

  const handleRemoveCollab = async (collabId: string) => {
    try {
      await removeCollaboratorAPI(collabId);
      showToast("Đã xóa cộng tác viên", "success");
      fetchCollaborators();
    } catch (e: any) { showToast(e.message || "Xóa cộng tác viên thất bại", "error"); }
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
        document_id: selectedDocumentId || undefined
      });
      showToast("Đã tạo mã ưu đãi", "success");
      setNewCouponCode("");
      fetchCoupons();
    } catch (e: any) { showToast(e.message || "Tạo mã ưu đãi thất bại", "error"); }
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
    } catch (e: any) { showToast(e.message || "Chuyển nhượng tác phẩm thất bại", "error"); }
    finally { setTransferUserIdLoading(false); }
  };

  if (loadingDocs) {
    return <div className="flex justify-center py-24"><Loader2 className="w-8 h-8 animate-spin text-zinc-400" /></div>;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="bg-white border border-zinc-200 p-6 rounded-2xl shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: '150ms', animationFillMode: 'both' }}>
        <div className="space-y-1">
          <h2 className="text-xl font-medium text-black flex items-center gap-2"><Settings className="w-5 h-5" /> Cấu hình tác phẩm</h2>
          <p className="text-sm font-medium text-zinc-500">Quản lý và tinh chỉnh các cài đặt cho tài liệu</p>
        </div>
        <select 
          value={selectedDocumentId} 
          onChange={e => setSelectedDocumentId(e.target.value)}
          className="w-full sm:w-64 h-10 border border-zinc-200 px-3 text-sm outline-none bg-white rounded-xl focus:border-black"
        >
          {documents.map(d => (
            <option key={d.id || d._id} value={d.id || d._id}>{d.title}</option>
          ))}
        </select>
      </div>

      {selectedDocumentId ? (
        <div className="bg-white border border-zinc-200 p-8 md:p-10 space-y-10 rounded-2xl shadow-sm animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: '150ms', animationFillMode: 'both' }}>
          
          <div className="space-y-4">
            <h2 className="text-xl font-medium text-black flex items-center gap-2"><Hash className="w-5 h-5" /> Phân loại & Thẻ (Tags)</h2>
            <p className="text-sm font-medium text-zinc-500 leading-relaxed">Sử dụng các thẻ để giúp thuật toán và công cụ tìm kiếm phân loại tác phẩm của bạn tốt hơn.</p>
            <div className="flex flex-wrap gap-2 mb-2">
              {docTags.map(tag => (
                <span key={tag} className="flex items-center gap-1 border border-zinc-200 bg-zinc-50 px-2 py-1 text-xs font-semibold text-black rounded-xl">
                  {tag}
                  <button onClick={() => handleRemoveTag(tag)} className="text-zinc-400 hover:text-black transition-colors"><X className="w-3 h-3" /></button>
                </span>
              ))}
            </div>
            <input
              type="text"
              value={newTagInput}
              onChange={(e) => setNewTagInput(e.target.value)}
              onKeyDown={handleAddTag}
              placeholder="Nhập tên thẻ và nhấn Enter (VD: TienHiep, HuyenHuyen)"
              className="w-full max-w-md h-10 border border-zinc-200 px-3 text-xs font-medium rounded-xl outline-none focus:border-black bg-white placeholder:text-zinc-400"
            />
          </div>
          
          <div className="h-px bg-zinc-200" />

          <div className="space-y-4">
            <h2 className="text-xl font-medium text-black flex items-center gap-2"><Folder className="w-5 h-5" /> Thư mục làm việc</h2>
            <p className="text-sm font-medium text-zinc-500 leading-relaxed">Di chuyển tác phẩm này vào thư mục làm việc để quản lý tài liệu tốt hơn.</p>
            <div className="flex gap-3 max-w-md">
              <select
                value={selectedDocument?.folder_id || ""}
                onChange={async (e) => {
                  const fId = e.target.value;
                  try {
                    await updateDocumentAPI(selectedDocumentId, { folder_id: fId || null });
                    showToast("Đã di chuyển tác phẩm thành công", "success");
                    fetchInitData();
                  } catch (err: any) { showToast("Không thể di chuyển", "error"); }
                }}
                className="flex-1 h-10 border border-zinc-200 px-3 text-xs font-semibold rounded-xl outline-none bg-white text-black focus:border-black"
              >
                <option value="">(Thư mục gốc)</option>
                {folders.map(f => (
                  <option key={f._id || f.id} value={f._id || f.id}>{f.name}</option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="h-px bg-zinc-200" />

          <div className="space-y-4">
            <h2 className="text-xl font-medium text-black flex items-center gap-2"><Brain className="w-5 h-5" /> Trí tuệ nhân tạo</h2>
            <p className="text-sm font-medium text-zinc-500 leading-relaxed">Đồng bộ nội dung với hệ thống RAG để AI thấu hiểu và hỗ trợ độc giả tốt hơn.</p>
            <button
              onClick={handleIngestAI}
              disabled={isIngesting || !selectedDocumentId}
              className="h-10 bg-black text-white px-6 text-sm font-medium flex items-center gap-2 rounded-xl disabled:opacity-50 w-fit"
            >
              {isIngesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
              Kích hoạt đồng bộ dữ liệu AI
            </button>
          </div>
          
          
          <div className="h-px bg-zinc-200" />
          
          <div className="space-y-6">
            <div className="space-y-3">
              <h2 className="text-xl font-medium text-black flex items-center gap-2"><Shield className="w-5 h-5" /> Bảo vệ bản quyền (DRM)</h2>
              <p className="text-sm font-medium text-zinc-500 leading-relaxed max-w-md">Hạn chế sao chép trái phép và ẩn khỏi công cụ tìm kiếm.</p>
            </div>
            <div className="space-y-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <div className={`w-10 h-5 border rounded-full flex items-center p-0.5 transition-colors ${drmCopy ? 'bg-black border-black' : 'bg-zinc-200 border-zinc-300'}`}>
                  <div className={`w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${drmCopy ? 'translate-x-5' : 'translate-x-0'}`} />
                </div>
                <input type="checkbox" className="hidden" checked={drmCopy} onChange={(e) => setDrmCopy(e.target.checked)} />
                <span className="text-sm font-medium text-black">Chống bôi đen & Copy</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <div className={`w-10 h-5 border rounded-full flex items-center p-0.5 transition-colors ${drmSearch ? 'bg-black border-black' : 'bg-zinc-200 border-zinc-300'}`}>
                  <div className={`w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${drmSearch ? 'translate-x-5' : 'translate-x-0'}`} />
                </div>
                <input type="checkbox" className="hidden" checked={drmSearch} onChange={(e) => setDrmSearch(e.target.checked)} />
                <span className="text-sm font-medium text-black">Ẩn khỏi công cụ tìm kiếm (SEO)</span>
              </label>
              <button onClick={handleSaveDRM} disabled={savingDrm || !selectedDocumentId} className="h-10 bg-black text-white px-6 text-sm font-medium flex items-center gap-2 rounded-xl disabled:opacity-50 w-fit">
                {savingDrm ? <Loader2 className="w-4 h-4 animate-spin" /> : "Lưu cài đặt DRM"}
              </button>
            </div>
          </div>

          <div className="h-px bg-zinc-200" />

          <div className="space-y-6">
            <div className="space-y-3">
              <h2 className="text-xl font-medium text-black flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-red-500" /> Cảnh báo nội dung (NSFW)</h2>
              <p className="text-sm font-medium text-zinc-500 leading-relaxed max-w-md">Đánh dấu nếu tác phẩm có chứa nội dung nhạy cảm, bạo lực hoặc giới hạn độ tuổi (18+).</p>
            </div>
            <div className="space-y-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <div className={`w-10 h-5 border rounded-full flex items-center p-0.5 transition-colors ${isNsfw ? 'bg-red-500 border-red-500' : 'bg-zinc-200 border-zinc-300'}`}>
                  <div className={`w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${isNsfw ? 'translate-x-5' : 'translate-x-0'}`} />
                </div>
                <input type="checkbox" className="hidden" checked={isNsfw} onChange={handleToggleNSFW} />
                <span className="text-sm font-medium text-black">Yêu cầu xác nhận độ tuổi trước khi đọc</span>
              </label>
            </div>
          </div>

          <div className="h-px bg-zinc-200" />

          <div className="space-y-6">
            <div className="space-y-3">
              <h2 className="text-xl font-medium text-black flex items-center gap-2"><Users className="w-5 h-5" /> Đồng sáng tác (Collaboration)</h2>
              <p className="text-sm font-medium text-zinc-500 leading-relaxed max-w-md">Mời người dùng khác tham gia cùng biên tập tác phẩm.</p>
            </div>
            <div className="space-y-4 max-w-md">
              <div className="flex gap-2">
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="Email người cộng tác"
                  className="flex-1 h-10 border border-zinc-200 px-3 text-xs font-medium rounded-xl outline-none focus:border-black bg-white"
                />
                <button onClick={handleInviteCollab} className="h-10 bg-black text-white px-4 text-sm font-medium flex items-center rounded-xl whitespace-nowrap">
                  Gửi lời mời
                </button>
              </div>
              {loadingCollabs ? (
                <div className="flex justify-center p-4"><Loader2 className="w-4 h-4 animate-spin text-zinc-400" /></div>
              ) : collaborators.length > 0 ? (
                <ul className="space-y-2 border border-zinc-200 bg-zinc-50 p-4 rounded-xl">
                  {collaborators.map((c: any) => (
                    <li key={c.id} className="flex justify-between items-center text-sm font-medium">
                      <span className="text-black">{c.email || c.user_id} <span className="text-zinc-500 text-xs">({c.role})</span></span>
                      <button onClick={() => handleRemoveCollab(c.id)} className="text-red-500 p-1 hover:bg-red-50 rounded-lg"><Trash2 className="w-3.5 h-3.5" /></button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-zinc-500 italic">Chưa có người cộng tác nào.</p>
              )}
            </div>
          </div>

          <div className="h-px bg-zinc-200" />

          <div className="space-y-6">
            <div className="space-y-3">
              <h2 className="text-xl font-medium text-black flex items-center gap-2"><Tag className="w-5 h-5" /> Mã ưu đãi (Coupons)</h2>
              <p className="text-sm font-medium text-zinc-500 leading-relaxed max-w-md">Tạo mã ưu đãi để thúc đẩy doanh thu cho tài liệu có phí.</p>
            </div>
            <div className="flex flex-wrap gap-4 items-center bg-zinc-50 p-4 rounded-xl border border-zinc-200">
              <input type="text" value={newCouponCode} onChange={(e) => setNewCouponCode(e.target.value)} placeholder="Mã (VD: TET2025)" className="w-32 h-10 px-3 text-xs border border-zinc-200 rounded-xl uppercase outline-none focus:border-black bg-white" />
              <input type="number" value={newCouponDiscount} onChange={(e) => setNewCouponDiscount(Number(e.target.value))} placeholder="% giảm" className="w-24 h-10 px-3 text-xs border border-zinc-200 rounded-xl outline-none focus:border-black bg-white" min={1} max={100} />
              <input type="number" value={newCouponQuantity} onChange={(e) => setNewCouponQuantity(Number(e.target.value))} placeholder="Số lượng" className="w-24 h-10 px-3 text-xs border border-zinc-200 rounded-xl outline-none focus:border-black bg-white" min={1} />
              <button onClick={handleCreateCoupon} className="h-10 px-4 bg-black text-white text-xs font-medium flex items-center rounded-xl">Tạo mã</button>
            </div>
            <div className="pt-2">
              {coupons.length === 0 ? (
                <p className="text-xs text-zinc-500 italic">Chưa có mã ưu đãi nào.</p>
              ) : (
                <div className="flex flex-wrap gap-3">
                  {coupons.map((c: any) => (
                    <div key={c.id || c._id} className="border border-zinc-200 px-3 py-2 flex items-center gap-3 bg-white rounded-xl shadow-sm">
                      <span className="font-bold text-xs text-black">{c.code}</span>
                      <span className="text-[10px] bg-black text-white px-1.5 py-0.5 font-bold rounded-md">-{c.discount_percent}%</span>
                      <span className="text-[10px] text-zinc-500 font-medium">Lượt: {c.used_count || 0}/{c.max_uses}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="h-px bg-zinc-200" />
          
          <div className="space-y-6">
            <div className="space-y-3">
              <h2 className="text-xl font-medium text-black">Bàn giao tác phẩm</h2>
              <p className="text-sm font-medium text-zinc-500 leading-relaxed max-w-md">Bạn sẽ mất toàn quyền kiểm soát tác phẩm này sau khi chuyển nhượng. Hãy đảm bảo nhập đúng mã ID của người nhận.</p>
            </div>
            <div className="space-y-4">
              <div className="space-y-1.5 max-w-md">
                <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Mã ID người nhận</label>
                <input
                  type="text"
                  value={transferUserId}
                  onChange={(e) => setTransferUserId(e.target.value)}
                  placeholder="Ví dụ: 60a1b2c3d4e5f6g7h8i9j0k"
                  className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-xl outline-none focus:border-black bg-white placeholder:text-zinc-400"
                />
              </div>
              <button
                onClick={() => setConfirmTransfer(true)}
                disabled={isTransferring || !selectedDocumentId || !transferUserId.trim()}
                className="h-10 bg-black text-white px-6 text-sm font-medium flex items-center gap-2 rounded-xl disabled:opacity-50 w-fit"
              >
                {isTransferring ? <Loader2 className="w-4 h-4 animate-spin" /> : "Chuyển nhượng"}
              </button>
            </div>
          </div>

        </div>
      ) : (
        <div className="bg-white border border-zinc-200 p-16 rounded-2xl flex flex-col items-center justify-center gap-4 text-center">
          <Settings className="w-8 h-8 text-zinc-300" />
          <p className="text-sm font-medium text-zinc-500">Vui lòng chọn một tác phẩm để định cấu hình</p>
        </div>
      )}

      <Modal isOpen={confirmTransfer} onClose={() => setConfirmTransfer(false)} className="max-w-sm">
        <ModalHeader>
          <ModalTitle>Xác nhận chuyển nhượng</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs font-medium text-zinc-500 leading-relaxed">Bạn có chắc chắn muốn chuyển nhượng tác phẩm này? Hành động này không thể hoàn tác và bạn sẽ mất toàn quyền truy cập.</p>
        </ModalContent>
        <ModalFooter>
          <button onClick={() => setConfirmTransfer(false)} className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black rounded-xl">Hủy</button>
          <button onClick={executeTransfer} className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black rounded-xl">Xác nhận</button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
