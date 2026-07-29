"use client";
import {
  streamAiChatAPI,
  createAiSessionAPI,
  deleteAiSessionAPI,
  getAiSessionAPI,
  getAiSessionsAPI,
  getUserInstructionsAPI,
  saveUserInstructionsAPI,
  clearUserInstructionsAPI,
  updateAiSessionTitleAPI,
} from "@/features/agentic_ai/services/interaction.service";
import { uploadChatAttachmentAPI } from "@/features/cloud/services/upload.service";
import { useSearchParams } from "next/navigation";
import { useCallback, useState, useEffect, useRef } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github.css";

import {
  X,
  Send,
  Zap,
  Paperclip,
  Image as ImageIcon,
  FileText,
  Loader2,
  Maximize2,
  Edit2,
  Trash2,
  Plus as PlusIcon,
  MoreVertical,
  ArrowRight,
  Activity,
  Folder,
  ChevronDown,
} from "lucide-react";
import { usePayOS } from "@payos/payos-checkout";
import {
  getMyQuotaAPI,
  QuotaUsage,
} from "@/features/usage/services/quota.service";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";

function PayOSEmbedded({ checkoutUrl }: { checkoutUrl: string }) {
  const elementId = useRef("payos-" + Math.random().toString(36).substring(7));
  const { open, exit } = usePayOS({
    RETURN_URL: window.location.origin + "/vi-tien",
    ELEMENT_ID: elementId.current,
    CHECKOUT_URL: checkoutUrl,
    embedded: true,
  } as any);

  useEffect(() => {
    open();
    return () => {
      if (exit) exit();
    };
  }, [open, exit]);

  return (
    <div
      id={elementId.current}
      className="w-full min-h-[450px] border-[var(--border)] rounded-[var(--radius-panel)] my-4 bg-[var(--surface-quiet)] overflow-hidden"
    ></div>
  );
}

function RecommendedDocsCards({ payloadStr }: { payloadStr: string }) {
  try {
    const data = JSON.parse(payloadStr);
    const recs = data.recommendations || [];
    if (!Array.isArray(recs) || recs.length === 0) return null;

    return (
      <div className="my-4 p-4 rounded-[var(--radius-panel)] bg-[var(--surface-quiet)] border border-[var(--border)]">
        <div className="flex items-center gap-2 font-semibold text-[15px] text-[var(--ink)] mb-3">
          <FileText className="w-4 h-4 text-[var(--brand)]" />
          <span>Tài liệu gợi ý dành cho bạn:</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {recs.map((item: any, idx: number) => (
            <div
              key={idx}
              className="p-3.5 rounded-[var(--radius-panel)] bg-white border border-[var(--border)] hover:border-[var(--brand)] transition-all flex flex-col justify-between"
            >
              <div>
                <h4 className="font-semibold text-[14px] text-[var(--ink)] line-clamp-2 mb-1">
                  {item.title}
                </h4>
                <p className="text-[12px] text-[var(--ink-muted)] line-clamp-2 mb-2">
                  {item.summary}
                </p>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-[var(--surface-quiet)] mt-auto">
                <span className="text-[12px] font-medium text-[var(--brand)]">
                  {item.price_dl > 0 ? `${item.price_dl} DL` : "Miễn phí"}
                </span>
                <a
                  href={item.url}
                  className="px-2.5 py-1 rounded-full bg-[var(--brand)] text-white text-[12px] font-medium hover:bg-[var(--brand-hover)] transition-colors flex items-center gap-1"
                  target="_blank"
                  rel="noreferrer"
                >
                  <span>Xem ngay</span>
                  <ArrowRight className="w-3 h-3" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  } catch (e) {
    return null;
  }
}

function InteractiveMindmapCanvas({ payloadStr }: { payloadStr: string }) {
  const [collapsedNodes, setCollapsedNodes] = useState<Record<string, boolean>>({});
  const [zoom, setZoom] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);

  try {
    const data = JSON.parse(payloadStr);
    const tree = data.tree || {};
    const root = tree.root;
    if (!root) return null;

    const toggleNode = (id: string) => {
      setCollapsedNodes((prev) => ({ ...prev, [id]: !prev[id] }));
    };

    return (
      <div
        className={`my-4 p-5 rounded-[var(--radius-panel)] bg-[var(--surface-quiet)] border border-[var(--border)] transition-all ${
          isFullscreen ? "fixed inset-4 z-50 overflow-auto bg-white shadow-2xl" : ""
        }`}
      >
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-3 mb-4">
          <div className="flex items-center gap-2 font-semibold text-[15px] text-[var(--ink)]">
            <Activity className="w-4.5 h-4.5 text-[var(--brand)]" />
            <span>{tree.title || "Sơ đồ tư duy"}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setZoom((z) => Math.max(0.7, z - 0.1))}
              className="px-2.5 py-1 rounded-full bg-white border border-[var(--border)] text-[12px] font-medium text-[var(--ink)] hover:bg-[var(--surface-quiet)]"
            >
              -
            </button>
            <span className="text-[12px] font-medium text-[var(--ink-muted)]">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={() => setZoom((z) => Math.min(1.5, z + 0.1))}
              className="px-2.5 py-1 rounded-full bg-white border border-[var(--border)] text-[12px] font-medium text-[var(--ink)] hover:bg-[var(--surface-quiet)]"
            >
              +
            </button>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-1.5 rounded-full bg-white border border-[var(--border)] text-[var(--ink-muted)] hover:text-[var(--ink)] hover:bg-[var(--surface-quiet)]"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div
          className="overflow-x-auto py-4 transition-transform duration-200 origin-top"
          style={{ transform: `scale(${zoom})` }}
        >
          <div className="flex flex-col items-center">
            <div className="px-6 py-3 rounded-full bg-[var(--brand)] text-white font-bold text-[16px] shadow-md mb-8 cursor-pointer hover:bg-[var(--brand-hover)] transition-colors">
              {root.name}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
              {(root.children || []).map((branch: any) => {
                const isCollapsed = collapsedNodes[branch.id];
                return (
                  <div
                    key={branch.id}
                    className="flex flex-col rounded-[var(--radius-workspace)] bg-white border border-[var(--border)] p-4 shadow-sm"
                  >
                    <div
                      onClick={() => toggleNode(branch.id)}
                      className="flex items-center justify-between font-semibold text-[14px] text-[var(--ink)] cursor-pointer border-b border-[var(--surface-quiet)] pb-2 mb-3"
                    >
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-[var(--brand)]" />
                        {branch.name}
                      </span>
                      <ChevronDown
                        className={`w-4 h-4 text-[var(--ink-muted)] transition-transform ${
                          isCollapsed ? "-rotate-90" : ""
                        }`}
                      />
                    </div>

                    {!isCollapsed && (
                      <ul className="space-y-2">
                        {(branch.children || []).map((sub: any) => (
                          <li
                            key={sub.id}
                            className="text-[13px] text-[var(--ink-muted)] flex items-center gap-2 pl-2 py-1 rounded-[var(--radius-control)] hover:bg-[var(--surface-quiet)] transition-colors"
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-[#AEAEB2]" />
                            <span>{sub.name}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    );
  } catch (e) {
    return null;
  }
}

function CustomInstructionsModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const [instructions, setInstructions] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      getUserInstructionsAPI()
        .then((res) => {
          setInstructions(res.data?.instructions || "");
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveUserInstructionsAPI(instructions);
      showToast("Cập nhật chỉ dẫn cá nhân thành công", "success");
      onClose();
    } catch (e: any) {
      showToast(e.message || "Lỗi lưu chỉ dẫn cá nhân", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleClear = async () => {
    try {
      await clearUserInstructionsAPI();
      setInstructions("");
      showToast("Đã xóa chỉ dẫn cá nhân", "success");
    } catch (e: any) {
      showToast(e.message || "Lỗi xóa chỉ dẫn", "error");
    }
  };

  const presets = [
    "Thêm phần tóm tắt TL;DR ở đầu mỗi phản hồi",
    "Trình bày danh sách bằng định dạng gạch đầu dòng",
    "Trả lời bằng tiếng Việt ngắn gọn, đi thẳng vào trọng tâm",
    "Ưu tiên kèm theo mã nguồn Python/TypeScript khi giải thích",
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalHeader>
        <ModalTitle>Chỉ dẫn cá nhân</ModalTitle>
      </ModalHeader>
      <ModalContent>
        {loading ? (
          <p className="py-8 text-center text-[14px] text-[var(--ink-muted)]">
            Đang tải chỉ dẫn
          </p>
        ) : (
          <div className="space-y-5">
            <div>
              <label className="mb-2 block text-[13px] font-medium text-[var(--ink)]">
                Chỉ dẫn mẫu
              </label>
              <div className="flex flex-wrap gap-2">
                {presets.map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() =>
                      setInstructions((prev) =>
                        prev ? `${prev}\n- ${preset}` : `- ${preset}`
                      )
                    }
                    className="rounded-[var(--radius-control)] border border-[var(--border)] bg-[var(--surface-quiet)] px-2.5 py-1.5 text-left text-[12px] text-[var(--ink)] hover:border-[var(--brand)]"
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </div>

            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              rows={5}
              className="field-control w-full resize-none"
            />

            <div>
              <button
                onClick={handleClear}
                type="button"
                className="text-[13px] font-medium text-[var(--danger)]"
              >
                Xóa chỉ dẫn
              </button>
            </div>
          </div>
        )}
      </ModalContent>
      <ModalFooter>
        <button onClick={onClose} type="button" className="button-secondary">
          Hủy
        </button>
        <button
          onClick={handleSave}
          disabled={saving || loading}
          type="button"
          className="button-primary disabled:opacity-50"
        >
          {saving ? "Đang lưu" : "Lưu chỉ dẫn"}
        </button>
      </ModalFooter>
    </Modal>
  );
}

function QuotaIndicator() {
  const [usage, setUsage] = useState<QuotaUsage | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchQuota = async () => {
    try {
      const data = await getMyQuotaAPI();
      setUsage(data);
    } catch (err) {
      console.error("Error loading quota info:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuota();
    const interval = setInterval(fetchQuota, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !usage) return null;

  const reqPercent = Math.min(
    100,
    (usage.used_requests / usage.limit_requests) * 100,
  );
  const tokenPercent = Math.min(
    100,
    (usage.used_tokens / usage.limit_tokens) * 100,
  );

  return (
    <div className="flex flex-col gap-3 p-4 bg-[var(--surface-quiet)]  rounded-[var(--radius-panel)]">
      <div className="flex items-center gap-2">
        <Activity className="w-4 h-4 text-[var(--brand)]" />
        <span className="text-[12px] font-semibold text-[var(--ink)]">
          Hạn mức sử dụng ngày
        </span>
      </div>

      <div className="space-y-3">
        <div className="space-y-1.5">
          <div className="flex justify-between text-[11px] font-medium text-[var(--ink-muted)]">
            <span>Yêu cầu</span>
            <span>
              {usage.used_requests} / {usage.limit_requests}
            </span>
          </div>
          <div className="h-1.5 w-full bg-[var(--border)] rounded-full overflow-hidden">
            <div
              className={`h-full ${reqPercent > 90 ? "bg-[var(--danger)]" : "bg-[var(--brand)]"}`}
              style={{ width: `${reqPercent}%` }}
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between text-[11px] font-medium text-[var(--ink-muted)]">
            <span>Token</span>
            <span>
              {usage.used_tokens.toLocaleString()} /{" "}
              {usage.limit_tokens.toLocaleString()}
            </span>
          </div>
          <div className="h-1.5 w-full bg-[var(--border)] rounded-full overflow-hidden">
            <div
              className={`h-full ${tokenPercent > 90 ? "bg-[var(--danger)]" : "bg-[var(--brand)]"}`}
              style={{ width: `${tokenPercent}%` }}
            />
          </div>
        </div>
      </div>

      {(reqPercent >= 100 || tokenPercent >= 100) && (
        <p className="text-[12px] font-semibold text-[var(--danger)] mt-1">
          Đã đạt giới hạn hôm nay
        </p>
      )}
    </div>
  );
}

const nodeDescriptions: Record<string, string> = {
  contextualize_question: "Phân tích bối cảnh hội thoại",
  route_question: "Định tuyến yêu cầu",
  route_query: "Định tuyến chuyên môn",
  retrieve_db: "Tìm kiếm trong DocLib",
  retrieve_internet: "Tìm kiếm thông tin mở rộng",
  grade_documents: "Thẩm định độ tin cậy của dữ liệu",
  transform_query: "Tinh chỉnh chiến lược tìm kiếm",
  generate: "Tổng hợp câu trả lời",
  generate_direct: "Phản hồi trực tiếp",
  grade_generation: "Kiểm tra tính xác thực",
  billing: "Kết nối hệ thống tài chính",
  workspace: "Truy cập thư viện",
  multi: "Đồng bộ dữ liệu đa nguồn",
  rag: "Tổng hợp thông tin",
  chat: "Trò chuyện trực tiếp",
};

const UserMessage = ({ content }: { content: string }) => {
  const [expanded, setExpanded] = useState(false);
  const isLong = content.length > 400 || content.split('\n').length > 8;
  
  let displayContent = content;
  if (!expanded && isLong) {
    displayContent = content.split('\n').slice(0, 8).join('\n');
    if (displayContent.length > 400) {
      displayContent = displayContent.slice(0, 400);
    }
    displayContent += " [còn tiếp]";
  }

  return (
    <div className="bg-[var(--brand)] text-white px-5 py-3.5 rounded-[var(--radius-workspace)] rounded-tr-[4px]">
      <p className="text-[15px] whitespace-pre-wrap leading-relaxed min-w-0 break-words">
        {displayContent}
      </p>
      {isLong && (
        <button 
          onClick={() => setExpanded(!expanded)} 
          className="mt-2 text-[13px] text-white/80 hover:text-white font-medium underline"
        >
          {expanded ? "Thu gọn" : "Xem thêm"}
        </button>
      )}
    </div>
  );
};

const ThoughtTimer = ({ isRunning }: { isRunning: boolean }) => {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    let interval: any;
    if (isRunning) {
      interval = setInterval(() => setSeconds(s => s + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  if (!isRunning && seconds === 0) return <span>Đã suy nghĩ xong</span>;
  if (!isRunning) return <span>Đã suy nghĩ trong {seconds} giây</span>;
  return <span>Đang suy nghĩ trong {seconds} giây</span>;
};

export default function TroChuyenPage() {
  const [view, setView] = useState<"chat" | "history">("chat");
  const [thinking, setThinking] = useState(false);
  const [messages, setMessages] = useState<
    { id?: string; role: string; content: string; thoughts?: string[]; attachments?: { image?: string; file?: string; folder?: string }; isThinkingEnabled?: boolean }[]
  >([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showAttachments, setShowAttachments] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [openDropdownId, setOpenDropdownId] = useState<string | null>(null);
  const [editingTitleId, setEditingTitleId] = useState<string | null>(null);
  const [editingTitleValue, setEditingTitleValue] = useState("");
  const [showInstructionsModal, setShowInstructionsModal] = useState(false);

  const { showToast } = useToast();
  const searchParams = useSearchParams();
  const documentId = searchParams.get("tai-lieu");

  const [selectedFile, setSelectedFile] = useState<{
    name: string;
    data: string;
    fileObj?: File;
  } | null>(null);
  const [selectedImage, setSelectedImage] = useState<{
    name: string;
    data: string;
    fileObj?: File;
  } | null>(null);
  const [selectedFolder, setSelectedFolder] = useState<{
    name: string;
    data: string;
  } | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const mirrorRef = useRef<HTMLTextAreaElement>(null);
  const { user } = useAuth() as any;
  const currentUserId = user?.id || user?._id;

  const fetchHistory = useCallback(async () => {
    try {
      if (!currentUserId) return;
      const data = await getAiSessionsAPI();
      setSessions(data.data || data || []);
    } catch {
      showToast("Không thể tải lịch sử trò chuyện", "error");
    }
  }, [currentUserId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  if (!user) return null;

  const handleAttach = () => {
    setShowAttachments(!showAttachments);
  };

  const handleToggleThinking = (e: React.ChangeEvent<HTMLInputElement>) => {
    setThinking(e.target.checked);
    if (!e.target.checked) {
      setSelectedFile(null);
      setSelectedImage(null);
      setShowAttachments(false);
    }
  };

  const handleFileUpload = async (
    e: React.ChangeEvent<HTMLInputElement>,
    type: "image" | "file" | "folder",
  ) => {
    if (type === "folder") {
      const files = Array.from(e.target.files || []);
      if (!files.length) return;

      let combinedText = "";
      for (const file of files) {
        if (!file.type.startsWith("image/") && !file.type.startsWith("video/")) {
          try {
            const text = await file.text();
            combinedText += `\n\n--- ${file.webkitRelativePath || file.name} ---\n${text}`;
          } catch (err) {}
        }
      }
      
      const blob = new Blob([combinedText], { type: "text/plain" });
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          const folderName = files[0].webkitRelativePath ? files[0].webkitRelativePath.split('/')[0] : "Thư mục";
          setSelectedFolder({ name: folderName, data: event.target.result as string });
          setShowAttachments(false);
        }
      };
      reader.readAsDataURL(blob);
      e.target.value = "";
      return;
    }

    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      if (event.target?.result) {
        const data = event.target.result as string;
        if (type === "image") setSelectedImage({ name: file.name, data, fileObj: file });
        if (type === "file") setSelectedFile({ name: file.name, data, fileObj: file });
        setShowAttachments(false);
      }
    };
    reader.readAsDataURL(file);
    e.target.value = "";
  };

  const handleSubmit = async (e?: React.FormEvent, retryText?: string) => {
    if (e) e.preventDefault();
    const userMessage = retryText || input.trim();
    if ((!userMessage && !selectedImage && !selectedFile && !selectedFolder) || isSending) return;

    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const data = await createAiSessionAPI(undefined, userMessage);
          sessionId = data.data?._id || data._id;
          setCurrentSessionId(sessionId);
          fetchHistory();
      } catch {
        showToast("Không thể tạo cuộc trò chuyện", "error");
      }
    }

    if (retryText) {
      setMessages((prev) => {
        const editIdx = prev.findIndex((m) => m.id === editingMessageId);
        return editIdx >= 0 ? prev.slice(0, editIdx) : prev;
      });
    }

    const attachments: { image?: string; file?: string; folder?: string } = {};
    if (selectedImage) attachments.image = selectedImage.data;
    if (selectedFile) attachments.file = selectedFile.name;
    if (selectedFolder) attachments.folder = selectedFolder.name;

    const msgId = Date.now().toString();
    setMessages((prev) => [
      ...prev,
      { 
        id: msgId, 
        role: "user", 
        content: userMessage,
        ...(Object.keys(attachments).length > 0 ? { attachments } : {})
      },
    ]);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setIsSending(true);
    setEditingMessageId(null);
    setShowAttachments(false);

    try {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: thinking ? "<think>\n" : "", thoughts: [], isThinkingEnabled: thinking },
      ]);

      let uploadedFileUrl = "";
      if (selectedImage?.fileObj) {
        try {
          const res = await uploadChatAttachmentAPI(selectedImage.fileObj);
          uploadedFileUrl = res.data.url;
        } catch (e: any) {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1].content = e.message || "Lỗi truyền tải tệp ảnh lên máy chủ";
            return updated;
          });
          setIsSending(false);
          return;
        }
      } else if (selectedFile?.fileObj) {
        try {
          const res = await uploadChatAttachmentAPI(selectedFile.fileObj);
          uploadedFileUrl = res.data.url;
        } catch (e: any) {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1].content = e.message || "Lỗi truyền tải tệp tin lên máy chủ";
            return updated;
          });
          setIsSending(false);
          return;
        }
      }

      const res = await streamAiChatAPI({
        query: userMessage,
        thinking,
        session_id: sessionId,
        conversation_history: messages.slice(-8),
        user_id: user?.id || user?._id || "guest",
        document_ids: documentId ? [documentId] : [],
        image_data: selectedImage?.data,
        file_data: selectedFile?.data,
        folder_data: selectedFolder?.data,
        attachments: uploadedFileUrl ? [{
          url: uploadedFileUrl,
          filename: selectedImage?.name || selectedFile?.name || "attachment"
        }] : [],
      });

      setSelectedFile(null);
      setSelectedImage(null);
      setSelectedFolder(null);

      if (!res.ok) {
        let errorText = "Máy chủ AI không phản hồi, vui lòng thử lại sau";
        if (res.status === 429)
          errorText =
            "Tài khoản đã vượt quá hạn mức sử dụng (Quota Exceeded). Vui lòng nâng cấp gói dịch vụ để tiếp tục";
        else {
          try {
            const errJson = await res.json();
            errorText = errJson.message || errJson.detail || errorText;
          } catch (e) {}
        }
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].content = errorText;
          return updated;
        });
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) return;
      const decoder = new TextDecoder("utf-8");
      let fullText = thinking ? "<think>\n" : "";
      let isDone = false;
      let buffer = "";

      while (!isDone) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const ev of lines) {
          if (!ev.trim()) continue;
          const eventLines = ev.split("\n");
          let type = "";
          let data = "";
          for (const line of eventLines) {
            if (line.startsWith("event:"))
              type = line.replace("event:", "").trim();
            else if (line.startsWith("data:"))
              data = line.replace("data:", "").trim();
          }

          if (type === "status" && data) {
            try {
              const parsed = JSON.parse(data);
              let nodeVi = parsed.node;
              if (typeof nodeVi === "object" && nodeVi !== null) {
                if (nodeVi.agent && nodeVi.task)
                  nodeVi = `Tác vụ: ${nodeVi.task} (${nodeVi.agent})`;
                else nodeVi = JSON.stringify(nodeVi);
              } else {
                nodeVi = nodeDescriptions[nodeVi] || nodeVi;
              }
              setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = { ...updated[updated.length - 1] };
                if (
                  lastMsg.role === "assistant" &&
                  !lastMsg.thoughts?.includes(nodeVi)
                ) {
                  lastMsg.thoughts = [...(lastMsg.thoughts || []), nodeVi];
                }
                updated[updated.length - 1] = lastMsg;
                return updated;
              });
            } catch (e) {}
          } else if (type === "plan" && data) {
            try {
              JSON.parse(data);
              setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = { ...updated[updated.length - 1] };
                if (
                  lastMsg.role === "assistant" &&
                  !lastMsg.thoughts?.includes("Tiếp nhận và phân tích yêu cầu")
                ) {
                  lastMsg.thoughts = [
                    ...(lastMsg.thoughts || []),
                    "Tiếp nhận và phân tích yêu cầu",
                  ];
                }
                updated[updated.length - 1] = lastMsg;
                return updated;
              });
            } catch (e) {}
          } else if (type === "tool" && data) {
            try {
              const parsed = JSON.parse(data);
              const agentNames: Record<string, string> = {
                KnowledgeAgent: "Tìm kiếm tài liệu trong DocLib",
                SearchEngine: "Tìm kiếm thông tin mở rộng",
                CodeInterpreter: "Phân tích dữ liệu",
                ActionAgent: "Thực hiện thao tác",
                DraftGenerator: "Định dạng nội dung",
                ReasoningAgent: "Suy luận và đánh giá",
                code_interpreter: "Phân tích dữ liệu",
                search_engine: "Tìm kiếm thông tin mở rộng",
                action_agent: "Thực hiện thao tác",
                draft_generator: "Định dạng nội dung",
                knowledge_agent: "Tìm kiếm tài liệu trong DocLib",
                reasoning_agent: "Suy luận và đánh giá",
              };
              const actionName = agentNames[parsed.agent] || "Xử lý thông tin";
              const toolMsg = `Đã ${actionName.toLowerCase()}`;
              setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = { ...updated[updated.length - 1] };
                if (
                  lastMsg.role === "assistant" &&
                  !lastMsg.thoughts?.includes(toolMsg)
                ) {
                  lastMsg.thoughts = [...(lastMsg.thoughts || []), toolMsg];
                }
                updated[updated.length - 1] = lastMsg;
                return updated;
              });
            } catch (e) {}
          } else if (type === "message" && data) {
            try {
              const parsed = JSON.parse(data);
              fullText += parsed.chunk;
              setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = { ...updated[updated.length - 1] };
                if (lastMsg.role === "assistant") lastMsg.content = fullText;
                updated[updated.length - 1] = lastMsg;
                return updated;
              });
            } catch (e) {}
          } else if (type === "done" || data === "[DONE]") {
            isDone = true;
          } else if (type === "error" && data) {
            setMessages((prev) => {
              const updated = [...prev];
              const lastMsg = { ...updated[updated.length - 1] };
              lastMsg.content = "Lỗi thực thi luồng dữ liệu phản hồi từ AI";
              updated[updated.length - 1] = lastMsg;
              return updated;
            });
          } else if (!type && data) {
            try {
              const parsed = JSON.parse(data);
              if (parsed.error) {
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastMsg = { ...updated[updated.length - 1] };
                  lastMsg.content = parsed.error;
                  updated[updated.length - 1] = lastMsg;
                  return updated;
                });
                isDone = true;
              } else if (parsed.chunk) {
                fullText += parsed.chunk;
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastMsg = { ...updated[updated.length - 1] };
                  if (lastMsg.role === "assistant") lastMsg.content = fullText;
                  updated[updated.length - 1] = lastMsg;
                  return updated;
                });
              }
            } catch (e) {}
          }
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (lastMsg.role === "assistant" && !lastMsg.content) {
          lastMsg.content = "Mất kết nối Stream API đến máy chủ AI";
        }
        return updated;
      });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="w-full h-full flex flex-col font-sans text-[var(--ink)]">
      <div className="flex flex-1 min-h-0 gap-6">
        <aside className="w-full lg:w-[320px] bg-[var(--surface-quiet)] md:bg-transparent rounded-[var(--radius-panel)] md:rounded-none flex flex-col overflow-hidden shrink-0 hidden lg:flex">
          <div className="px-6 md:px-0 pt-6 pb-4 flex items-center justify-between shrink-0">
            <h2 className="text-[20px] font-semibold text-[var(--ink)]">
              Lịch sử
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowInstructionsModal(true)}
                className="p-2 bg-[var(--surface-quiet)] text-[var(--ink)] hover:bg-[var(--border)] rounded-full transition-colors"
                title="Tùy chỉnh chỉ dẫn cá nhân"
              >
                <Edit2 className="w-4 h-4 text-[var(--brand)]" />
              </button>
              <button
                onClick={() => (window.location.href = "/nang-cap")}
                className="px-3 py-1.5 text-[13px] font-medium bg-[var(--brand)] text-white rounded-full hover:bg-[var(--brand-hover)] transition-colors shadow-sm"
              >
                Nâng cấp
              </button>
              <button
                onClick={() => {
                  setCurrentSessionId(null);
                  setMessages([]);
                }}
                className="p-2 bg-[var(--surface-quiet)] text-[var(--ink)] hover:bg-[var(--border)] rounded-full transition-colors"
                title="Cuộc trò chuyện mới"
              >
                <PlusIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="overflow-y-auto px-6 md:px-0 pb-6 flex flex-col gap-2 shrink custom-scrollbar">
            {sessions.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center bg-[var(--surface-quiet)] rounded-[var(--radius-panel)]">
                <p className="text-[17px] font-medium text-[var(--ink-muted)]">
                  Chưa có dữ liệu
                </p>
              </div>
            ) : (
              sessions.map((s) => (
                <div
                  key={s._id}
                  className={`p-3 rounded-[var(--radius-panel)] cursor-pointer transition-colors ${currentSessionId === s._id ? "bg-white border border-transparent shadow-[0_1px_2px_rgba(0,0,0,0.05)]" : "border border-transparent hover:bg-[var(--border)]"}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div
                      className="flex-1 min-w-0 cursor-pointer"
                      onClick={async () => {
                        setCurrentSessionId(s._id);
                        setView("chat");
                        try {
                            const data = await getAiSessionAPI(s._id);
                            const msgs = data.data ? data.data.messages : data.messages;
                            const mapped = (msgs || []).map(
                              (m: any) => ({
                                id: m.id || m._id || Math.random().toString(),
                                role: m.role || "user",
                                content: m.content || "",
                                thoughts: m.thoughts || [],
                                attachments: m.attachments || {},
                                isThinkingEnabled: m.isThinkingEnabled !== undefined ? m.isThinkingEnabled : ((m.thoughts && m.thoughts.length > 0) || (m.content && m.content.startsWith("<think>"))),
                              }),
                            );
                            setMessages(mapped);
                        } catch {
                          showToast("Không thể mở cuộc trò chuyện", "error");
                        }
                      }}
                    >
                      {editingTitleId === s._id ? (
                        <input
                          autoFocus
                          value={editingTitleValue}
                          onChange={(e) => setEditingTitleValue(e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                          onBlur={() => setEditingTitleId(null)}
                          onKeyDown={async (e) => {
                            if (e.key === "Enter") {
                              e.preventDefault();
                              e.stopPropagation();
                              if (!editingTitleValue.trim()) return;
                              try {
                                await updateAiSessionTitleAPI(
                                  s._id,
                                  editingTitleValue,
                                );
                                  fetchHistory();
                                  setEditingTitleId(null);
                              } catch {
                                showToast("Không thể đổi tên cuộc trò chuyện", "error");
                              }
                            } else if (e.key === "Escape") {
                              setEditingTitleId(null);
                            }
                          }}
                          className="w-full text-[15px] font-medium text-[var(--ink)] bg-[var(--surface-quiet)] border border-[var(--brand)] rounded-[var(--radius-control)] px-2 py-1 outline-none"
                        />
                      ) : (
                        <p className="text-[15px] font-medium text-[var(--ink)] truncate">
                          {s.title}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <p className="text-[12px] text-[var(--ink-muted)] whitespace-nowrap">
                        {new Date(s.updated_at).toLocaleDateString("vi-VN")}
                      </p>
                      <div className="relative">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setOpenDropdownId(
                              openDropdownId === s._id ? null : s._id,
                            );
                          }}
                          className="p-1.5 text-[var(--ink-muted)] hover:text-[var(--ink)] hover:bg-[var(--surface-quiet)] rounded-full transition-colors"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>
                        {openDropdownId === s._id && (
                          <>
                            <div
                              className="fixed inset-0 z-40"
                              onClick={(e) => {
                                e.stopPropagation();
                                setOpenDropdownId(null);
                              }}
                            />
                            <div className="absolute right-0 top-full mt-1 w-36 p-1.5 bg-white  rounded-[var(--radius-panel)] z-50">
                              <button
                                className="w-full text-left px-3 py-2 text-[13px] text-[var(--ink)] hover:bg-[var(--surface-quiet)] rounded-[var(--radius-control)] transition-colors flex items-center gap-2"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setOpenDropdownId(null);
                                  setEditingTitleId(s._id);
                                  setEditingTitleValue(s.title);
                                }}
                              >
                                <Edit2 className="w-3.5 h-3.5" /> Đổi tên
                              </button>
                              <button
                                onClick={async (e) => {
                                  e.stopPropagation();
                                  setOpenDropdownId(null);
                                  try {
                                    await deleteAiSessionAPI(s._id);
                                      if (currentSessionId === s._id) {
                                        setCurrentSessionId(null);
                                        setMessages([]);
                                      }
                                      fetchHistory();
                                  } catch {
                                    showToast("Không thể xóa cuộc trò chuyện", "error");
                                  }
                                }}
                                className="w-full text-left px-3 py-2 text-[13px] text-[var(--danger)] hover:bg-[#FFEBEB] rounded-[var(--radius-control)] transition-colors flex items-center gap-2"
                              >
                                <Trash2 className="w-3.5 h-3.5" /> Xóa
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
            <QuotaIndicator />
          </div>
        </aside>

        <main className="flex-1 flex flex-col min-w-0 h-full bg-[var(--surface-quiet)] md:bg-transparent rounded-[var(--radius-workspace)] md:rounded-none relative overflow-hidden">
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto flex flex-col min-h-0 custom-scrollbar relative"
          >
            {messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
                <p className="text-[24px] font-semibold text-[var(--ink)]">
                  Xin chào, {user.full_name}
                </p>
                <p className="text-[15px] text-[var(--ink-muted)] mt-2 leading-relaxed max-w-sm">
                  Tôi có thể giúp gì cho bạn hôm nay?
                </p>
              </div>
            ) : (
              <div className="flex flex-col w-full px-8 md:px-0 py-6 md:pt-6 gap-6">
                {messages.map((msg, idx) => {
                  if (msg.role === "user") {
                    return (
                      <div key={idx} className="flex justify-end">
                        <div className="max-w-[85%] flex flex-col gap-2 items-end">
                          {msg.attachments?.image && (
                            <img
                              src={msg.attachments.image}
                              alt="Attachment"
                              className="max-w-[240px] max-h-[240px] object-cover rounded-[var(--radius-workspace)] border border-[var(--border)]"
                            />
                          )}
                          {msg.attachments?.file && (
                            <div className="flex items-center gap-2 bg-white px-4 py-2.5 rounded-[var(--radius-panel)] border border-[var(--border)] shadow-sm">
                              <FileText className="w-5 h-5 text-[var(--brand)]" />
                              <span className="text-[14px] font-medium text-[var(--ink)]">
                                {msg.attachments.file}
                              </span>
                            </div>
                          )}
                          {msg.attachments?.folder && (
                            <div className="flex items-center gap-2 bg-white px-4 py-2.5 rounded-[var(--radius-panel)] border border-[var(--border)] shadow-sm">
                              <Folder className="w-5 h-5 text-[var(--warning)]" />
                              <span className="text-[14px] font-medium text-[var(--ink)]">
                                {msg.attachments.folder}
                              </span>
                            </div>
                          )}
                          {msg.content && <UserMessage content={msg.content} />}
                        </div>
                      </div>
                    );
                  }

                  const displayContent = msg.isThinkingEnabled ? msg.content : msg.content.replace(/<think>[\s\S]*?(?:<\/think>|$)/g, "");
                  const cleanText = displayContent.replace(/<think>[\s\S]*?(?:<\/think>|$)/g, "").trim();
                  const segments = displayContent
                    .split(/(<think>[\s\S]*?(?:<\/think>|$))/g)
                    .filter((s) => s.trim() !== "");
                  
                  const isLastAssistant = idx === messages.length - 1 && msg.role === "assistant";

                  return (
                    <div key={idx} className="flex justify-start">
                      <div className="w-full">
                        <div className="py-2 w-full relative group">
                          {msg.isThinkingEnabled && msg.thoughts && msg.thoughts.length > 0 && (
                            <div className="mb-3 mt-1">
                              <details className="group/details bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] overflow-hidden border border-[var(--border)]" open={isSending && idx === messages.length - 1}>
                                <summary className="flex items-center gap-2 px-4 py-2.5 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-transparent group-open/details:border-[var(--border)] transition-colors">
                                  <div className="flex-1 flex items-center gap-2">
                                    <Activity className="w-4 h-4 text-[var(--brand)]" />
                                    <span className="text-[14px] font-semibold text-[var(--ink)]">
                                      Quá trình xử lý
                                    </span>
                                  </div>
                                  <ChevronDown className="w-4 h-4 text-[var(--ink-muted)] transition-transform duration-200 group-open/details:rotate-180" />
                                </summary>
                                <div className="px-4 py-3 bg-white text-[14px] text-[var(--ink-muted)] border-t border-[var(--border)] flex flex-col gap-2">
                                  {msg.thoughts.map((t, tIdx) => (
                                    <div key={tIdx} className="flex gap-2 items-start">
                                      <div className="mt-1">
                                        {(isSending && idx === messages.length - 1 && tIdx === msg.thoughts!.length - 1) ? (
                                          <Loader2 className="w-3.5 h-3.5 text-[var(--brand)] animate-spin" />
                                        ) : (
                                          <div className="w-1.5 h-1.5 rounded-full bg-[var(--success)] mt-1" />
                                        )}
                                      </div>
                                      <span className="text-[14px] text-[var(--ink)] leading-relaxed">{t}</span>
                                    </div>
                                  ))}
                                </div>
                              </details>
                            </div>
                          )}
                          {segments.map((segment, sIdx) => {
                            if (segment.startsWith("<think>")) {
                              const thinkContent = segment.replace(/^<think>/, "").replace(/<\/think>$/, "").trim();
                              
                              return (
                                <div key={sIdx} className="mb-3 mt-1">
                                  <details className="group/details bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] overflow-hidden border border-[var(--border)]" open={isSending && idx === messages.length - 1 && sIdx === segments.length - 1}>
                                    <summary className="flex items-center gap-2 px-4 py-2.5 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-transparent group-open/details:border-[var(--border)] transition-colors">
                                      <div className="flex-1 flex items-center gap-2">
                                        <Activity className="w-4 h-4 text-[var(--brand)]" />
                                        <span className="text-[14px] font-semibold text-[var(--ink)]">
                                          <ThoughtTimer isRunning={isSending && idx === messages.length - 1 && sIdx === segments.length - 1} />
                                        </span>
                                      </div>
                                      <ChevronDown className="w-4 h-4 text-[var(--ink-muted)] transition-transform duration-200 group-open/details:rotate-180" />
                                    </summary>
                                    <div className="px-4 py-3 bg-white text-[14px] text-[var(--ink-muted)] border-t border-[var(--border)]">
                                      {thinkContent ? (
                                        <div className="prose prose-sm max-w-none prose-zinc prose-p:leading-relaxed text-[var(--ink-muted)]">
                                          <ReactMarkdown
                                            remarkPlugins={[remarkGfm, remarkMath]}
                                            rehypePlugins={[rehypeKatex, rehypeHighlight]}
                                          >
                                            {thinkContent}
                                          </ReactMarkdown>
                                        </div>
                                      ) : (
                                        <div className="flex gap-2 items-center py-1">
                                          <Loader2 className="w-4 h-4 text-[var(--brand)] animate-spin" />
                                          <span className="text-[14px] text-[var(--ink-muted)] font-medium animate-pulse">
                                            Đang kích hoạt không gian suy luận
                                          </span>
                                        </div>
                                      )}
                                    </div>
                                  </details>
                                </div>
                              );
                            }

                            let docPayloadStr = "";
                            let mindmapPayloadStr = "";
                            let displaySegment = segment;
                            const payloadEnd = "</agentic-payload>";
                            const docPayloadStart = '<agentic-payload kind="RECOMMENDED_DOCS_PAYLOAD">';
                            const mindmapPayloadStart = '<agentic-payload kind="MINDMAP_PAYLOAD">';
                            if (segment.includes(docPayloadStart)) {
                              const parts = segment.split(docPayloadStart);
                              displaySegment = parts[0];
                              const endParts = parts[1]?.split(payloadEnd);
                              if (endParts) docPayloadStr = endParts[0];
                            }
                            if (displaySegment.includes(mindmapPayloadStart)) {
                              const parts = displaySegment.split(mindmapPayloadStart);
                              displaySegment = parts[0];
                              const endParts = parts[1]?.split(payloadEnd);
                              if (endParts) mindmapPayloadStr = endParts[0];
                            }

                            return (
                              <div key={sIdx}>
                                <ReactMarkdown
                                  remarkPlugins={[remarkGfm, remarkMath]}
                                  rehypePlugins={[rehypeKatex, rehypeHighlight]}
                                  className="prose prose-sm max-w-none prose-zinc prose-p:text-[15px] prose-p:text-[var(--ink)] prose-p:leading-relaxed prose-code:bg-[var(--surface-quiet)] prose-code:text-[var(--danger)] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-[6px] prose-pre:bg-[var(--ink)] prose-pre:rounded-[var(--radius-panel)]"
                                  components={{
                                    a: ({ href, children, ...props }) => {
                                      if (
                                        href &&
                                        (href.includes("payos.vn") ||
                                          href.includes("pay.payos.vn"))
                                      ) {
                                        return <PayOSEmbedded checkoutUrl={href} />;
                                      }
                                      return (
                                        <a
                                          href={href}
                                          className="text-[var(--brand)] font-medium hover:underline"
                                          target="_blank"
                                          rel="noreferrer"
                                          {...props}
                                        >
                                          {children}
                                        </a>
                                      );
                                    },
                                  }}
                                >
                                  {displaySegment}
                                </ReactMarkdown>
                                {docPayloadStr && <RecommendedDocsCards payloadStr={docPayloadStr} />}
                                {mindmapPayloadStr && <InteractiveMindmapCanvas payloadStr={mindmapPayloadStr} />}
                              </div>
                            );


                          })}

                          {!cleanText && segments.length === 0 && (
                            <div className="flex gap-1.5 h-6 items-center">
                              <div className="w-2 h-2 rounded-full bg-[var(--border-strong)] animate-pulse" />
                              <div
                                className="w-2 h-2 rounded-full bg-[var(--border-strong)] animate-pulse"
                                style={{ animationDelay: "0.2s" }}
                              />
                              <div
                                className="w-2 h-2 rounded-full bg-[var(--border-strong)] animate-pulse"
                                style={{ animationDelay: "0.4s" }}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="shrink-0 px-6 pb-6 pt-2 md:px-0 md:pb-0">
            <div className="w-full relative bg-white border border-[var(--border-strong)] focus-within:border-[var(--brand)] transition-colors rounded-[var(--radius-workspace)] p-2">
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept=".txt,.md,.json,.pdf,.docx,.doc,.xlsx,.xls,.pptx,.zip,.csv"
                onChange={(e) => {
                  handleFileUpload(e, "file");
                  setShowAttachments(false);
                }}
              />
              <input
                type="file"
                ref={imageInputRef}
                className="hidden"
                accept="image/*"
                onChange={(e) => {
                  handleFileUpload(e, "image");
                  setShowAttachments(false);
                }}
              />

              <input
                type="file"
                ref={folderInputRef}
                className="hidden"
                {...({
                  webkitdirectory: "",
                  directory: "",
                } as Record<string, string>)}
                multiple
                onChange={(e) => {
                  handleFileUpload(e, "folder");
                  setShowAttachments(false);
                }}
              />

              {showAttachments && (
                <div className="absolute bottom-full left-0 mb-2 w-40 bg-white rounded-[var(--radius-panel)] py-2 z-50 shadow-[0_4px_24px_rgba(0,0,0,0.08)] border border-[var(--border)]">
                  <button
                    onClick={() => {
                      fileInputRef.current?.click();
                      setShowAttachments(false);
                    }}
                    className="w-full text-left px-4 py-2.5 text-[15px] font-medium text-[var(--ink)] hover:bg-[var(--surface-quiet)] transition-colors flex items-center gap-3"
                  >
                    <FileText className="w-5 h-5 text-[var(--brand)]" /> Tài liệu
                  </button>
                  <button
                    onClick={() => {
                      imageInputRef.current?.click();
                      setShowAttachments(false);
                    }}
                    className="w-full text-left px-4 py-2.5 text-[15px] font-medium text-[var(--ink)] hover:bg-[var(--surface-quiet)] transition-colors flex items-center gap-3"
                  >
                    <ImageIcon className="w-5 h-5 text-[var(--success)]" /> Hình ảnh
                  </button>
                  {user?.ai_tier === "PREMIUM" && (
                    <button
                      onClick={() => {
                        folderInputRef.current?.click();
                        setShowAttachments(false);
                      }}
                      className="w-full text-left px-4 py-2.5 text-[15px] font-medium text-[var(--ink)] hover:bg-[var(--surface-quiet)] transition-colors flex items-center gap-3"
                    >
                      <Folder className="w-5 h-5 text-[var(--warning)]" /> Thư mục
                    </button>
                  )}
                </div>
              )}

              {(selectedFile || selectedImage || selectedFolder) && (
                <div className="flex gap-4 px-2 pt-2 pb-3 overflow-x-auto scrollbar-none">
                  {selectedImage && (
                    <div className="relative group shrink-0">
                      <img
                        src={selectedImage.data}
                        alt=""
                        className="h-16 w-16 object-cover rounded-[var(--radius-panel)] border border-[var(--border)]"
                      />
                      <button
                        onClick={() => setSelectedImage(null)}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-[var(--surface-quiet)] text-[var(--ink-muted)] hover:text-[var(--ink)] flex items-center justify-center rounded-full shadow-sm"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                  {selectedFile && (
                    <div className="relative group shrink-0 h-16 px-4 bg-[var(--surface-quiet)] border border-[var(--border)] flex items-center gap-3 rounded-[var(--radius-panel)]">
                      <FileText className="w-5 h-5 text-[var(--brand)] shrink-0" />
                      <span className="text-[13px] font-medium text-[var(--ink)] truncate max-w-[150px]">
                        {selectedFile.name}
                      </span>
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-[var(--surface-quiet)] text-[var(--ink-muted)] hover:text-[var(--ink)] flex items-center justify-center rounded-full shadow-sm border border-[var(--border)]"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}

                  {selectedFolder && (
                    <div className="relative group shrink-0">
                      <div className="flex items-center gap-3 px-4 py-3 bg-[var(--surface-quiet)] rounded-[var(--radius-workspace)] border border-[var(--border)]">
                        <Folder className="w-6 h-6 text-[var(--warning)]" />
                        <span className="text-[14px] font-medium text-[var(--ink)] max-w-[150px] truncate">
                          {selectedFolder.name}
                        </span>
                      </div>
                      <button
                        onClick={() => setSelectedFolder(null)}
                        className="absolute -top-2 -right-2 bg-white text-[var(--ink-muted)] hover:text-[var(--ink)] p-1.5 rounded-full shadow-[0_2px_8px_rgba(0,0,0,0.1)] border border-[var(--border)] transition-colors z-10 opacity-0 group-hover:opacity-100"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              )}

              <form onSubmit={handleSubmit} className="relative flex w-full">
                <textarea
                  ref={mirrorRef}
                  className="absolute top-0 left-0 w-full min-h-[56px] text-[17px] leading-[24px] font-medium font-sans opacity-0 invisible pointer-events-none -z-10 resize-none"
                  aria-hidden="true"
                  rows={1}
                  tabIndex={-1}
                  readOnly
                />
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => {
                    const newValue = e.target.value;
                    setInput(newValue);
                    const el = e.target;
                    const mirror = mirrorRef.current;
                    if (!mirror) return;
                    
                    mirror.value = newValue;
                    
                    const baseClass = "absolute top-0 left-0 w-full min-h-[56px] text-[17px] leading-[24px] font-medium font-sans opacity-0 invisible pointer-events-none -z-10 resize-none";
                    mirror.className = `${baseClass} py-[16px] pl-[56px] pr-[180px]`;
                    mirror.style.height = "auto";
                    
                    const singleLineScrollHeight = mirror.scrollHeight;
                    const multiLine = singleLineScrollHeight > 56;
                    const shouldExpand = multiLine || newValue.includes('\n');
                    
                    setIsExpanded(shouldExpand);
                    
                    if (shouldExpand) {
                       mirror.className = `${baseClass} px-4 pt-4 pb-[56px]`;
                       mirror.style.height = "auto";
                       el.style.height = `${Math.min(mirror.scrollHeight, 200)}px`;
                    } else {
                       el.style.height = "56px";
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      if (!isSending && (input.trim() || selectedImage || selectedFile)) {
                        handleSubmit(e as any);
                      }
                    }
                  }}
                  placeholder=""
                  disabled={isSending}
                  rows={1}
                  className={`w-full min-h-[56px] text-[17px] leading-[24px] bg-transparent outline-none font-medium text-[var(--ink)] placeholder:text-[var(--ink-muted)] resize-none overflow-y-auto custom-scrollbar transition-colors duration-200 ${
                    isExpanded
                      ? "px-4 pt-4 pb-[56px]"
                      : "py-[16px] pl-[56px] pr-[180px]"
                  }`}
                  style={{ maxHeight: "200px" }}
                />
                
                <div className="absolute bottom-0 left-0 right-0 h-[56px] px-1 flex items-center justify-between pointer-events-none">
                  <div className="pointer-events-auto">
                    <button
                      type="button"
                      onClick={handleAttach}
                      className="text-[var(--ink-muted)] shrink-0 rounded-full w-10 h-10 flex items-center justify-center hover:bg-[var(--surface-quiet)] hover:text-[var(--ink)] transition-colors"
                    >
                      <PlusIcon className="w-5 h-5" />
                    </button>
                  </div>
                  <div className="flex items-center gap-2 pointer-events-auto">
                    <label
                      className={`flex h-10 items-center gap-2 ${user?.ai_tier !== "PREMIUM" && user?.role !== "admin" ? "cursor-not-allowed opacity-50" : "cursor-pointer"} group shrink-0 select-none`}
                    >
                      <span className="text-[14px] font-medium text-[var(--ink-muted)] select-none">
                        Suy nghĩ
                      </span>
                      <div className="relative inline-flex items-center">
                        <input
                          type="checkbox"
                          checked={thinking}
                          onChange={handleToggleThinking}
                          disabled={
                            user?.ai_tier !== "PREMIUM" && user?.role !== "admin"
                          }
                          className="sr-only"
                        />
                        <div 
                          className={`w-11 h-6 rounded-full transition-colors duration-200 flex items-center px-[2px] shrink-0 outline-none select-none ${
                            thinking ? "bg-[var(--success)]" : "bg-[var(--border-strong)]"
                          }`}
                        >
                          <div 
                            className={`w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-200 ${
                              thinking ? "translate-x-5" : "translate-x-0"
                            }`} 
                          />
                        </div>
                      </div>
                    </label>
                    <button
                      type="submit"
                      disabled={
                        isSending ||
                        (!input.trim() && !selectedImage && !selectedFile && !selectedFolder)
                      }
                      className="w-10 h-10 shrink-0 bg-[var(--brand)] text-white flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed rounded-full transition-colors hover:bg-[var(--brand-hover)]"
                    >
                      {isSending ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <ArrowRight className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                </div>
              </form>
            </div>
            <div className="mt-1 text-center mb-1">
              <span className="text-[12px] italic text-[var(--ink-muted)]">
                * DocLib Metis là trí tuệ nhân tạo và có thể mắc sai lầm
              </span>
            </div>
          </div>
        </main>
      </div>
      <CustomInstructionsModal
        isOpen={showInstructionsModal}
        onClose={() => setShowInstructionsModal(false)}
      />
    </div>
  );
}
