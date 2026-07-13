"use client";
import { streamAiChatAPI } from "@/features/agentic_ai/services/interaction.service";
import { uploadChatAttachmentAPI } from "@/features/cloud/services/upload.service";
import {
  getToken,
  API_URL,
} from "@/features/authentication/services/session.service";
import { useSearchParams } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";

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
      className="w-full min-h-[450px] border-[#E8E8ED] rounded-[18px] my-4 bg-[#F5F5F7] overflow-hidden"
    ></div>
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
    <div className="flex flex-col gap-3 p-4 bg-[#F5F5F7]  rounded-[18px]">
      <div className="flex items-center gap-2">
        <Activity className="w-4 h-4 text-[#0071E3]" />
        <span className="text-[12px] font-semibold text-[#1D1D1F]">
          Hạn mức sử dụng ngày
        </span>
      </div>

      <div className="space-y-3">
        <div className="space-y-1.5">
          <div className="flex justify-between text-[11px] font-medium text-[#6E6E73]">
            <span>Yêu cầu</span>
            <span>
              {usage.used_requests} / {usage.limit_requests}
            </span>
          </div>
          <div className="h-1.5 w-full bg-[#E8E8ED] rounded-full overflow-hidden">
            <div
              className={`h-full ${reqPercent > 90 ? "bg-[#FF3B30]" : "bg-[#0071E3]"}`}
              style={{ width: `${reqPercent}%` }}
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between text-[11px] font-medium text-[#6E6E73]">
            <span>Token</span>
            <span>
              {usage.used_tokens.toLocaleString()} /{" "}
              {usage.limit_tokens.toLocaleString()}
            </span>
          </div>
          <div className="h-1.5 w-full bg-[#E8E8ED] rounded-full overflow-hidden">
            <div
              className={`h-full ${tokenPercent > 90 ? "bg-[#FF3B30]" : "bg-[#0071E3]"}`}
              style={{ width: `${tokenPercent}%` }}
            />
          </div>
        </div>
      </div>

      {(reqPercent >= 100 || tokenPercent >= 100) && (
        <p className="text-[12px] font-semibold text-[#FF3B30] mt-1">
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
    displayContent += "...";
  }

  return (
    <div className="bg-[#0071E3] text-white px-5 py-3.5 rounded-[20px] rounded-tr-[4px]">
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
    { id?: string; role: string; content: string; thoughts?: string[]; attachments?: { image?: string; file?: string; folder?: string } }[]
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

  const fetchHistory = async () => {
    try {
      const token = getToken();
      const userId = user?.id || user?._id;
      if (!userId) return;
      const res = await fetch(`${API_URL}/lich-su?user_id=${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data.data || data || []);
      }
    } catch (err) {
      console.error("Error loading chat history:", err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

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
        const token = getToken();
        const userId = user?.id || user?._id;
        const res = await fetch(`${API_URL}/lich-su`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ first_query: userMessage, user_id: userId }),
        });
        if (res.ok) {
          const data = await res.json();
          sessionId = data.data?._id || data._id;
          setCurrentSessionId(sessionId);
          fetchHistory();
        }
      } catch (err) {}
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
        { role: "assistant", content: thinking ? "<think>\n" : "", thoughts: [] },
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
      let fullText = "";
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
    <div className="w-full h-full flex flex-col font-sans text-[#1D1D1F]">
      <div className="flex flex-1 min-h-0 gap-6">
        <aside className="w-full lg:w-[320px] bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none flex flex-col overflow-hidden shrink-0 hidden lg:flex">
          <div className="px-6 md:px-0 pt-6 pb-4 flex items-center justify-between shrink-0">
            <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
              Lịch sử
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => (window.location.href = "/nang-cap")}
                className="px-3 py-1.5 text-[13px] font-medium bg-[#0071E3] text-white rounded-full hover:bg-[#0055C6] transition-colors shadow-sm"
              >
                Nâng cấp
              </button>
              <button
                onClick={() => {
                  setCurrentSessionId(null);
                  setMessages([]);
                }}
                className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
                title="Cuộc trò chuyện mới"
              >
                <PlusIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="overflow-y-auto px-6 md:px-0 pb-6 flex flex-col gap-2 shrink custom-scrollbar">
            {sessions.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px]">
                <p className="text-[17px] font-medium text-[#6E6E73]">
                  Chưa có dữ liệu
                </p>
              </div>
            ) : (
              sessions.map((s) => (
                <div
                  key={s._id}
                  className={`p-3 rounded-[14px] cursor-pointer transition-colors ${currentSessionId === s._id ? "bg-white border border-transparent shadow-[0_1px_2px_rgba(0,0,0,0.05)]" : "border border-transparent hover:bg-[#E8E8ED]"}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div
                      className="flex-1 min-w-0 cursor-pointer"
                      onClick={async () => {
                        const token = getToken();
                        setCurrentSessionId(s._id);
                        setView("chat");
                        try {
                          const res = await fetch(
                            `${API_URL}/lich-su/${s._id}?user_id=${user?.id || user?._id}`,
                            { headers: { Authorization: `Bearer ${token}` } },
                          );
                          if (res.ok) {
                            const data = await res.json();
                            const msgs = data.data ? data.data.messages : data.messages;
                            const mapped = (msgs || []).map(
                              (m: any) => ({
                                id: m.id || m._id || Math.random().toString(),
                                role: m.role || "user",
                                content: m.content || "",
                                thoughts: m.thoughts || [],
                                attachments: m.attachments || {},
                              }),
                            );
                            setMessages(mapped);
                          }
                        } catch (e) {}
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
                                const token = getToken();
                                const res = await fetch(
                                  `${API_URL}/lich-su/${s._id}/tieu-de?user_id=${user?.id || user?._id}`,
                                  {
                                    method: "PUT",
                                    headers: {
                                      Authorization: `Bearer ${token}`,
                                      "Content-Type": "application/json",
                                    },
                                    body: JSON.stringify({
                                      title: editingTitleValue,
                                    }),
                                  },
                                );
                                if (res.ok) {
                                  fetchHistory();
                                  setEditingTitleId(null);
                                }
                              } catch (err) {}
                            } else if (e.key === "Escape") {
                              setEditingTitleId(null);
                            }
                          }}
                          className="w-full text-[15px] font-medium text-[#1D1D1F] bg-[#F5F5F7] border border-[#0071E3] rounded-[8px] px-2 py-1 outline-none"
                        />
                      ) : (
                        <p className="text-[15px] font-medium text-[#1D1D1F] truncate">
                          {s.title}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <p className="text-[12px] text-[#6E6E73] whitespace-nowrap">
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
                          className="p-1.5 text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7] rounded-full transition-colors"
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
                            <div className="absolute right-0 top-full mt-1 w-36 p-1.5 bg-white  rounded-[14px] z-50">
                              <button
                                className="w-full text-left px-3 py-2 text-[13px] text-[#1D1D1F] hover:bg-[#F5F5F7] rounded-[10px] transition-colors flex items-center gap-2"
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
                                    const token = getToken();
                                    const res = await fetch(
                                      `${API_URL}/lich-su/${s._id}?user_id=${user?.id || user?._id}`,
                                      {
                                        method: "DELETE",
                                        headers: {
                                          Authorization: `Bearer ${token}`,
                                        },
                                      },
                                    );
                                    if (res.ok) {
                                      if (currentSessionId === s._id) {
                                        setCurrentSessionId(null);
                                        setMessages([]);
                                      }
                                      fetchHistory();
                                    }
                                  } catch (err) {}
                                }}
                                className="w-full text-left px-3 py-2 text-[13px] text-[#FF3B30] hover:bg-[#FFEBEB] rounded-[10px] transition-colors flex items-center gap-2"
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

        <main className="flex-1 flex flex-col min-w-0 h-full bg-[#F5F5F7] md:bg-transparent rounded-[24px] md:rounded-none relative overflow-hidden">
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto flex flex-col min-h-0 custom-scrollbar relative"
          >
            {messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
                <p className="text-[24px] font-semibold text-[#1D1D1F]">
                  Xin chào, {user.full_name}
                </p>
                <p className="text-[15px] text-[#6E6E73] mt-2 leading-relaxed max-w-sm">
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
                              className="max-w-[240px] max-h-[240px] object-cover rounded-[16px] border border-[#E8E8ED]"
                            />
                          )}
                          {msg.attachments?.file && (
                            <div className="flex items-center gap-2 bg-white px-4 py-2.5 rounded-[14px] border border-[#E8E8ED] shadow-sm">
                              <FileText className="w-5 h-5 text-[#0071E3]" />
                              <span className="text-[14px] font-medium text-[#1D1D1F]">
                                {msg.attachments.file}
                              </span>
                            </div>
                          )}
                          {msg.attachments?.folder && (
                            <div className="flex items-center gap-2 bg-white px-4 py-2.5 rounded-[14px] border border-[#E8E8ED] shadow-sm">
                              <Folder className="w-5 h-5 text-[#FF9500]" />
                              <span className="text-[14px] font-medium text-[#1D1D1F]">
                                {msg.attachments.folder}
                              </span>
                            </div>
                          )}
                          {msg.content && <UserMessage content={msg.content} />}
                        </div>
                      </div>
                    );
                  }

                  const cleanText = msg.content.replace(/<think>[\s\S]*?(?:<\/think>|$)/g, "").trim();
                  const segments = msg.content
                    .split(/(<think>[\s\S]*?(?:<\/think>|$))/g)
                    .filter((s) => s.trim() !== "");
                  
                  const isLastAssistant = idx === messages.length - 1 && msg.role === "assistant";

                  return (
                    <div key={idx} className="flex justify-start">
                      <div className="w-full">
                        <div className="py-2 w-full relative group">
                          {segments.map((segment, sIdx) => {
                            if (segment.startsWith("<think>")) {
                              const thinkContent = segment.replace(/^<think>/, "").replace(/<\/think>$/, "").trim();
                              
                              return (
                                <div key={sIdx} className="mb-3 mt-1">
                                  <details className="group/details bg-[#F5F5F7] rounded-[14px] overflow-hidden border border-[#E8E8ED]" open={isSending && idx === messages.length - 1 && sIdx === segments.length - 1}>
                                    <summary className="flex items-center gap-2 px-4 py-2.5 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-transparent group-open/details:border-[#E8E8ED] transition-colors">
                                      <div className="flex-1 flex items-center gap-2">
                                        <Activity className="w-4 h-4 text-[#0071E3]" />
                                        <span className="text-[14px] font-semibold text-[#1D1D1F]">
                                          <ThoughtTimer isRunning={isSending && idx === messages.length - 1 && sIdx === segments.length - 1} />
                                        </span>
                                      </div>
                                      <ChevronDown className="w-4 h-4 text-[#86868B] transition-transform duration-200 group-open/details:rotate-180" />
                                    </summary>
                                    <div className="px-4 py-3 bg-white text-[14px] text-[#6E6E73] border-t border-[#E8E8ED]">
                                      {thinkContent ? (
                                        <div className="prose prose-sm max-w-none prose-zinc prose-p:leading-relaxed text-[#6E6E73]">
                                          <ReactMarkdown
                                            remarkPlugins={[remarkGfm, remarkMath]}
                                            rehypePlugins={[rehypeKatex, rehypeHighlight]}
                                          >
                                            {thinkContent}
                                          </ReactMarkdown>
                                        </div>
                                      ) : (
                                        <div className="flex gap-2 items-center py-1">
                                          <Loader2 className="w-4 h-4 text-[#0071E3] animate-spin" />
                                          <span className="text-[14px] text-[#6E6E73] font-medium animate-pulse">
                                            Đang kích hoạt không gian suy luận...
                                          </span>
                                        </div>
                                      )}
                                    </div>
                                  </details>
                                </div>
                              );
                            }

                            return (
                              <ReactMarkdown
                                key={sIdx}
                                remarkPlugins={[remarkGfm, remarkMath]}
                                rehypePlugins={[rehypeKatex, rehypeHighlight]}
                                className="prose prose-sm max-w-none prose-zinc prose-p:text-[15px] prose-p:text-[#1D1D1F] prose-p:leading-relaxed prose-code:bg-[#F5F5F7] prose-code:text-[#FF3B30] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-[6px] prose-pre:bg-[#1D1D1F] prose-pre:rounded-[14px]"
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
                                        className="text-[#0071E3] font-medium hover:underline"
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
                                {segment}
                              </ReactMarkdown>
                            );
                          })}

                          {!cleanText && segments.length === 0 && (
                            <div className="flex gap-1.5 h-6 items-center">
                              <div className="w-2 h-2 rounded-full bg-[#C7C7CC] animate-pulse" />
                              <div
                                className="w-2 h-2 rounded-full bg-[#C7C7CC] animate-pulse"
                                style={{ animationDelay: "0.2s" }}
                              />
                              <div
                                className="w-2 h-2 rounded-full bg-[#C7C7CC] animate-pulse"
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
            <div className="w-full relative bg-white border border-[#D2D2D7] focus-within:border-[#0071E3] transition-colors rounded-[24px] p-2">
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
                // @ts-ignore
                webkitdirectory=""
                directory=""
                multiple
                onChange={(e) => {
                  handleFileUpload(e, "folder");
                  setShowAttachments(false);
                }}
              />

              {showAttachments && (
                <div className="absolute bottom-full left-0 mb-2 w-40 bg-white rounded-[14px] py-2 z-50 shadow-[0_4px_24px_rgba(0,0,0,0.08)] border border-[#E8E8ED]">
                  <button
                    onClick={() => {
                      fileInputRef.current?.click();
                      setShowAttachments(false);
                    }}
                    className="w-full text-left px-4 py-2.5 text-[15px] font-medium text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors flex items-center gap-3"
                  >
                    <FileText className="w-5 h-5 text-[#0071E3]" /> Tài liệu
                  </button>
                  <button
                    onClick={() => {
                      imageInputRef.current?.click();
                      setShowAttachments(false);
                    }}
                    className="w-full text-left px-4 py-2.5 text-[15px] font-medium text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors flex items-center gap-3"
                  >
                    <ImageIcon className="w-5 h-5 text-[#34C759]" /> Hình ảnh
                  </button>
                  {user?.ai_tier === "PREMIUM" && (
                    <button
                      onClick={() => {
                        folderInputRef.current?.click();
                        setShowAttachments(false);
                      }}
                      className="w-full text-left px-4 py-2.5 text-[15px] font-medium text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors flex items-center gap-3"
                    >
                      <Folder className="w-5 h-5 text-[#FF9500]" /> Thư mục
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
                        className="h-16 w-16 object-cover rounded-[14px] border border-[#E8E8ED]"
                      />
                      <button
                        onClick={() => setSelectedImage(null)}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-[#F5F5F7] text-[#6E6E73] hover:text-[#1D1D1F] flex items-center justify-center rounded-full shadow-sm"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                  {selectedFile && (
                    <div className="relative group shrink-0 h-16 px-4 bg-[#F5F5F7] border border-[#E8E8ED] flex items-center gap-3 rounded-[14px]">
                      <FileText className="w-5 h-5 text-[#0071E3] shrink-0" />
                      <span className="text-[13px] font-medium text-[#1D1D1F] truncate max-w-[150px]">
                        {selectedFile.name}
                      </span>
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-[#F5F5F7] text-[#6E6E73] hover:text-[#1D1D1F] flex items-center justify-center rounded-full shadow-sm border border-[#E8E8ED]"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}

                  {selectedFolder && (
                    <div className="relative group shrink-0">
                      <div className="flex items-center gap-3 px-4 py-3 bg-[#F5F5F7] rounded-[16px] border border-[#E8E8ED]">
                        <Folder className="w-6 h-6 text-[#FF9500]" />
                        <span className="text-[14px] font-medium text-[#1D1D1F] max-w-[150px] truncate">
                          {selectedFolder.name}
                        </span>
                      </div>
                      <button
                        onClick={() => setSelectedFolder(null)}
                        className="absolute -top-2 -right-2 bg-white text-[#86868B] hover:text-[#1D1D1F] p-1.5 rounded-full shadow-[0_2px_8px_rgba(0,0,0,0.1)] border border-[#E8E8ED] transition-colors z-10 opacity-0 group-hover:opacity-100"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              )}

              <form onSubmit={handleSubmit} className="relative flex w-full">
                {/* Mirror textarea for perfect synchronous height measurement without CSS transition interference */}
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
                    
                    // Measure single-line wrap WITHOUT transitions
                    const baseClass = "absolute top-0 left-0 w-full min-h-[56px] text-[17px] leading-[24px] font-medium font-sans opacity-0 invisible pointer-events-none -z-10 resize-none";
                    mirror.className = `${baseClass} py-[16px] pl-[56px] pr-[180px]`;
                    mirror.style.height = "auto";
                    
                    const singleLineScrollHeight = mirror.scrollHeight;
                    const multiLine = singleLineScrollHeight > 56;
                    const shouldExpand = multiLine || newValue.includes('\n');
                    
                    setIsExpanded(shouldExpand);
                    
                    if (shouldExpand) {
                       // Measure expanded height WITHOUT transitions
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
                  className={`w-full min-h-[56px] text-[17px] leading-[24px] bg-transparent outline-none font-medium text-[#1D1D1F] placeholder:text-[#6E6E73] resize-none overflow-y-auto custom-scrollbar transition-colors duration-200 ${
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
                      className="text-[#6E6E73] shrink-0 rounded-full w-10 h-10 flex items-center justify-center hover:bg-[#F5F5F7] hover:text-[#1D1D1F] transition-colors"
                    >
                      <PlusIcon className="w-5 h-5" />
                    </button>
                  </div>
                  <div className="flex items-center gap-2 pointer-events-auto">
                    <label
                      className={`flex h-10 items-center gap-2 ${user?.ai_tier !== "PREMIUM" && user?.role !== "admin" ? "cursor-not-allowed opacity-50" : "cursor-pointer"} group shrink-0 select-none`}
                    >
                      <span className="text-[14px] font-medium text-[#6E6E73] select-none">
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
                            thinking ? "bg-[#34C759]" : "bg-[#D2D2D7]"
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
                      className="w-10 h-10 shrink-0 bg-[#0071E3] text-white flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed rounded-full transition-colors hover:bg-[#0077ED]"
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
              <span className="text-[12px] italic text-[#86868B]">
                * DocLib Metis là trí tuệ nhân tạo và có thể mắc sai lầm
              </span>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
