"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getMyDocumentsAPI,
  updateDRMSettingsAPI,
  updateTagsAPI,
  updateDocumentAPI,
  getFoldersAPI,
  transferDocumentAPI,
} from "@/features/content/services/document.service";
import {
  getCollaboratorsAPI,
  inviteCollaboratorAPI,
  removeCollaboratorAPI,
} from "@/features/content/services/collaboration.service";
import { ingestDocumentAPI } from "@/features/agentic_ai/services/ingestion.service";
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
import PageLoader from "@/shared/components/common/PageLoader";
import EmptyState from "@/shared/components/common/EmptyState";

export default function ConfigPage() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [visible, setVisible] = useState(false);

  const selectedDocument = documents.find(
    (d) => (d._id || d.id) === selectedDocumentId,
  );

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

  const [transferUserId, setTransferUserId] = useState("");
  const [isTransferring, setTransferUserIdLoading] = useState(false);
  const [confirmTransfer, setConfirmTransfer] = useState(false);

  const fetchInitData = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const [docsData, foldersData] = await Promise.all([
        getMyDocumentsAPI(),
        getFoldersAPI().catch(() => ({ data: [] })),
      ]);
      const list = docsData.data || docsData || [];
      setDocuments(list);
      setFolders((foldersData as any).data || foldersData || []);
      if (list.length > 0) setSelectedDocumentId(list[0]._id || list[0].id);
    } catch {
      showToast("Không thể tải bộ sưu tập tài liệu", "error");
    } finally {
      setLoadingDocs(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [showToast]);

  useEffect(() => {
    fetchInitData();
  }, [fetchInitData]);

  const fetchCollaborators = useCallback(async () => {
    if (!selectedDocumentId) return;
    setLoadingCollabs(true);
    try {
      setCollaborators(
        (await getCollaboratorsAPI(selectedDocumentId)).data || [],
      );
    } catch {
      setCollaborators([]);
    } finally {
      setLoadingCollabs(false);
    }
  }, [selectedDocumentId]);

  useEffect(() => {
    if (selectedDocument) {
      setDrmCopy(selectedDocument.drm_settings?.disable_copy || false);
      setDrmSearch(selectedDocument.drm_settings?.hide_from_search || false);
      setDocTags(selectedDocument.tags || []);
      fetchCollaborators();
    }
  }, [fetchCollaborators, selectedDocument]);

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
        } catch {
          showToast("Không thể cập nhật danh sách thẻ phân loại", "error");
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
    } catch {
      showToast("Lỗi gỡ bỏ thẻ phân loại", "error");
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
      showToast("Cập nhật cấu hình bảo vệ bản quyền (DRM) hoàn tất", "success");
      fetchInitData();
    } catch {
      showToast("Không thể cập nhật cấu hình bảo vệ bản quyền (DRM)", "error");
    } finally {
      setSavingDrm(false);
    }
  };

  const handleIngestAI = async () => {
    if (!selectedDocumentId) return;
    setIsIngesting(true);
    try {
      await ingestDocumentAPI(selectedDocumentId);
      showToast("Khởi tạo tiến trình đồng bộ vector AI hoàn tất", "success");
    } catch {
      showToast("Lỗi khởi chạy tiến trình đồng bộ vector AI", "error");
    } finally {
      setIsIngesting(false);
    }
  };

  const handleInviteCollab = async () => {
    if (!inviteEmail.trim() || !selectedDocumentId) return;
    try {
      await inviteCollaboratorAPI(selectedDocumentId, inviteEmail.trim());
      showToast("Khởi tạo yêu cầu cấp quyền cộng tác hoàn tất", "success");
      setInviteEmail("");
      fetchCollaborators();
    } catch {
      showToast("Không thể tạo yêu cầu cấp quyền cộng tác", "error");
    }
  };

  const handleRemoveCollab = async (collabId: string) => {
    try {
      await removeCollaboratorAPI(collabId);
      showToast("Thu hồi quyền truy cập cộng tác hoàn tất", "success");
      fetchCollaborators();
    } catch {
      showToast("Lỗi thu hồi quyền truy cập cộng tác", "error");
    }
  };

  const executeTransfer = async () => {
    if (!transferUserId.trim() || !selectedDocumentId) return;
    setTransferUserIdLoading(true);
    try {
      await transferDocumentAPI(selectedDocumentId, transferUserId.trim());
      showToast("Chuyển giao quyền sở hữu tài liệu hoàn tất", "success");
      setTransferUserId("");
      setConfirmTransfer(false);
      fetchInitData();
    } catch {
      showToast("Lỗi chuyển giao quyền sở hữu tài liệu", "error");
    } finally {
      setTransferUserIdLoading(false);
    }
  };

  if (loadingDocs) return <PageLoader />;

  return (
    <div className="flex flex-col h-full font-sans">
      <div
        className={`bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:px-0 md:pt-6 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-6 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`}
        style={{ transitionDelay: "100ms" }}
      >
        <div className="bg-white p-6 rounded-panel flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white rounded-control flex items-center justify-center shrink-0">
              <Settings className="w-6 h-6 text-ink" />
            </div>
            <div>
              <p className="text-[13px] font-medium text-ink-muted mb-4">
                Chọn tác phẩm
              </p>
              <p className="text-[13px] text-ink-muted">
                Tác phẩm cần thiết lập
              </p>
            </div>
          </div>
          <div className="relative w-full sm:w-[320px]">
            <BookOpen className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-ink-muted" />
            <select
              value={selectedDocumentId}
              onChange={(e) => setSelectedDocumentId(e.target.value)}
              className="w-full h-[48px] pl-12 pr-10 text-[15px] font-medium text-ink focus:outline-none focus:border-brand bg-white rounded-control appearance-none transition-colors cursor-pointer"
            >
              {documents.length === 0 && (
                <option value="" disabled>
                  Chưa có tác phẩm
                </option>
              )}
              {documents.map((d) => (
                <option key={d.id || d._id} value={d.id || d._id}>
                  {d.title || "Chưa có tiêu đề"}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted pointer-events-none" />
          </div>
        </div>

        {selectedDocumentId ? (
          <div className="flex-1 min-h-0 pb-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-6">
              <div className="bg-white border border-border p-6 rounded-panel">
                <div className="flex items-center gap-2 mb-4">
                  <Hash className="w-5 h-5 text-ink" />
                  <p className="text-[13px] font-medium text-ink-muted mb-4">
                    Phân loại & Thẻ
                  </p>
                </div>
                <p className="text-[13px] text-ink-muted mb-4">
                  Sử dụng thẻ để phân loại tác phẩm.
                </p>
                <div className="flex flex-wrap gap-2 mb-4 min-h-[32px]">
                  {docTags.map((tag) => (
                    <span
                      key={tag}
                      className="flex items-center gap-1 bg-surface-quiet px-3 py-1.5 text-[13px] font-medium text-ink rounded-control group"
                    >
                      {tag}{" "}
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="text-ink-muted hover:text-danger transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </span>
                  ))}
                  {docTags.length === 0 && (
                    <span className="text-[13px] text-ink-faint">
                      Chưa có thẻ nào
                    </span>
                  )}
                </div>
                <div className="relative">
                  <Tag className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-ink-muted" />
                  <input
                    type="text"
                    value={newTagInput}
                    onChange={(e) => setNewTagInput(e.target.value)}
                    onKeyDown={handleAddTag}
                    placeholder=""
                    className="w-full h-[48px] pl-12 pr-4 text-[15px] rounded-control outline-none focus:border-brand bg-surface-quiet focus:bg-white transition-colors"
                  />
                </div>
              </div>

              <div className="bg-white border border-border p-6 rounded-panel">
                <div className="flex items-center gap-2 mb-4">
                  <Folder className="w-5 h-5 text-ink" />
                  <p className="text-[13px] font-medium text-ink-muted mb-4">
                    Thư mục làm việc
                  </p>
                </div>
                <p className="text-[13px] text-ink-muted mb-4">
                  Di chuyển tác phẩm này vào thư mục.
                </p>
                <div className="relative">
                  <Folder className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-ink-muted" />
                  <select
                    value={selectedDocument?.folder_id || ""}
                    onChange={async (e) => {
                      try {
                        await updateDocumentAPI(selectedDocumentId, {
                          folder_id: e.target.value || null,
                        });
                        showToast("Cập nhật liên kết thư mục hoàn tất", "success");
                        fetchInitData();
                      } catch {
                        showToast("Không thể cập nhật liên kết thư mục", "error");
                      }
                    }}
                    className="w-full h-[48px] pl-12 pr-10 text-[15px] font-medium rounded-control outline-none bg-surface-quiet focus:bg-white focus:border-brand appearance-none transition-colors cursor-pointer"
                  >
                    <option value="">(Thư mục gốc)</option>
                    {folders.map((f) => (
                      <option key={f._id || f.id} value={f._id || f.id}>
                        {f.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted pointer-events-none" />
                </div>
              </div>

              <div className="bg-white border border-border p-6 rounded-panel">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Shield className="w-5 h-5 text-ink" />
                    <p className="text-[13px] font-medium text-ink-muted mb-4">
                      Bảo vệ bản quyền
                    </p>
                  </div>
                  <button
                    onClick={handleSaveDRM}
                    disabled={savingDrm || !selectedDocumentId}
                    className="h-[36px] px-4 bg-brand text-white text-[13px] font-medium rounded-full disabled:opacity-50 transition-colors hover:bg-brand"
                  >
                    {savingDrm ? (
                      <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                    ) : (
                      "Lưu DRM"
                    )}
                  </button>
                </div>
                <div className="space-y-4 bg-surface-quiet p-4 rounded-panel">
                  <label className="flex items-center justify-between cursor-pointer group">
                    <span className="text-[13px] font-medium text-ink">
                      Chống bôi đen & Copy
                    </span>
                    <div
                      className={`w-[48px] h-[28px] rounded-full flex items-center p-1 transition-colors ${drmCopy ? "bg-brand border-brand" : "bg-border border-border"}`}
                    >
                      <div
                        className={`w-5 h-5 bg-white rounded-full transition-transform ${drmCopy ? "translate-x-[20px]" : "translate-x-0"}`}
                      />
                    </div>
                    <input
                      type="checkbox"
                      className="hidden"
                      checked={drmCopy}
                      onChange={(e) => setDrmCopy(e.target.checked)}
                    />
                  </label>
                  <div className="h-px bg-border" />
                  <label className="flex items-center justify-between cursor-pointer group">
                    <span className="text-[13px] font-medium text-ink">
                      Ẩn khỏi tìm kiếm (SEO)
                    </span>
                    <div
                      className={`w-[48px] h-[28px] rounded-full flex items-center p-1 transition-colors ${drmSearch ? "bg-brand border-brand" : "bg-border border-border"}`}
                    >
                      <div
                        className={`w-5 h-5 bg-white rounded-full transition-transform ${drmSearch ? "translate-x-[20px]" : "translate-x-0"}`}
                      />
                    </div>
                    <input
                      type="checkbox"
                      className="hidden"
                      checked={drmSearch}
                      onChange={(e) => setDrmSearch(e.target.checked)}
                    />
                  </label>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-white border border-border p-6 rounded-panel relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                  <Brain className="w-24 h-24" />
                </div>
                <div className="flex items-center gap-2 mb-4 relative z-10">
                  <Brain className="w-5 h-5 text-ink" />
                  <p className="text-[13px] font-medium text-ink-muted mb-4">
                    Trí tuệ nhân tạo
                  </p>
                </div>
                <p className="text-[13px] text-ink-muted mb-4 relative z-10">
                  Đồng bộ nội dung với hệ thống RAG để AI hỗ trợ độc giả.
                </p>
                <button
                  onClick={handleIngestAI}
                  disabled={isIngesting || !selectedDocumentId}
                  className="w-full h-[48px] bg-ink text-white text-[15px] font-medium flex items-center justify-center gap-2 rounded-full disabled:opacity-50 transition-colors hover:bg-ink relative z-10"
                >
                  {isIngesting ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Brain className="w-5 h-5" />
                  )}{" "}
                  Đồng bộ dữ liệu AI
                </button>
              </div>

              <div className="bg-white border border-border p-6 rounded-panel">
                <div className="flex items-center gap-2 mb-4">
                  <Users className="w-5 h-5 text-ink" />
                  <h2 className="text-[20px] font-semibold text-ink mb-4">
                    Cộng tác viên
                  </h2>
                </div>
                <div className="flex gap-2 mb-4">
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder=""
                    className="flex-1 h-[48px] pl-4 pr-4 text-[15px] rounded-control outline-none focus:border-brand bg-surface-quiet focus:bg-white transition-colors"
                  />
                  <button
                    onClick={handleInviteCollab}
                    disabled={!inviteEmail.trim()}
                    className="h-[48px] px-6 bg-brand text-white text-[15px] font-medium rounded-control disabled:opacity-50 flex items-center gap-2 hover:bg-brand transition-colors"
                  >
                    Mời <Send className="w-4 h-4" />
                  </button>
                </div>
                <div className="bg-surface-quiet rounded-panel p-4 max-h-[160px] overflow-y-auto custom-scrollbar">
                  {loadingCollabs ? (
                    <div className="flex justify-center p-4">
                      <Loader2 className="w-6 h-6 animate-spin text-brand" />
                    </div>
                  ) : collaborators.length > 0 ? (
                    <ul className="space-y-2">
                      {collaborators.map((c: any) => (
                        <li
                          key={c.id}
                          className="flex justify-between items-center bg-white p-3 rounded-control"
                        >
                          <div className="flex flex-col">
                            <span className="text-[15px] font-semibold text-ink">
                              {c.email || c.user_id}
                            </span>
                            <span className="text-[13px] text-ink-muted capitalize">
                              {c.role}
                            </span>
                          </div>
                          <button
                            onClick={() => handleRemoveCollab(c.id)}
                            className="w-8 h-8 flex items-center justify-center text-ink-muted hover:text-danger hover:bg-danger-soft rounded-full transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <EmptyState text="Chưa có người cộng tác" compact={true} />
                  )}
                </div>
              </div>

              <div className="bg-danger/10 border-danger/20 p-6 rounded-panel">
                <div className="flex items-center gap-2 mb-2 text-danger">
                  <ArrowRightLeft className="w-5 h-5" />
                  <h3 className="text-[17px] font-medium">Bàn giao tác phẩm</h3>
                </div>
                <p className="text-[13px] text-danger mb-4">
                  Bạn sẽ mất toàn quyền kiểm soát sau khi chuyển.
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={transferUserId}
                    onChange={(e) => setTransferUserId(e.target.value)}
                    placeholder=""
                    className="flex-1 h-[48px] pl-4 pr-4 border-danger/30 text-[15px] rounded-control outline-none focus:border-danger bg-white transition-colors"
                  />
                  <button
                    onClick={() => setConfirmTransfer(true)}
                    disabled={
                      isTransferring ||
                      !selectedDocumentId ||
                      !transferUserId.trim()
                    }
                    className="h-[48px] px-6 bg-danger text-white text-[15px] font-medium rounded-control disabled:opacity-50 hover:bg-danger transition-colors"
                  >
                    Chuyển
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 bg-white rounded-panel p-12 flex flex-col items-center justify-center gap-4 text-center">
            <div className="w-16 h-16 bg-surface-quiet border-border flex items-center justify-center rounded-panel mb-2">
              <Settings className="w-8 h-8 text-ink-faint" />
            </div>
            <p className="text-[15px] text-ink-muted max-w-sm">
              Vui lòng chọn một tác phẩm từ danh sách để định cấu hình
            </p>
          </div>
        )}
      </div>

      <Modal
        isOpen={confirmTransfer}
        onClose={() => setConfirmTransfer(false)}
      >
        <ModalHeader className="bg-danger/10">
          <ModalTitle className="text-danger flex items-center gap-2">
            <ArrowRightLeft className="w-5 h-5" /> Xác nhận chuyển nhượng
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-[15px] font-medium text-ink leading-relaxed bg-surface-quiet p-4 rounded-control">
            Chuyển nhượng tác phẩm cho ID{" "}
            <span className="font-semibold">{transferUserId}</span>
            <br />
            <span className="text-danger font-semibold">
              Hành động này không thể hoàn tác và bạn sẽ mất toàn quyền truy
              cập
            </span>
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setConfirmTransfer(false)}
            className="flex-1 h-[44px] bg-white text-[15px] font-medium text-ink rounded-full hover:bg-border transition-colors"
          >
            Hủy bỏ
          </button>
          <button
            onClick={executeTransfer}
            disabled={isTransferring}
            className="flex-1 h-[44px] bg-danger text-white text-[15px] font-medium rounded-full flex items-center justify-center disabled:opacity-50 hover:bg-danger transition-colors gap-2"
          >
            {isTransferring && <Loader2 className="w-5 h-5 animate-spin" />} Xác
            nhận chuyển
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
