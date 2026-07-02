"use client";
import { streamAiChatAPI } from "@/features/agentic_ai/services/interaction.service";
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
  Sparkles,
  MoreVertical,
  ArrowRight,
  Activity,
} from "lucide-react";
import { usePayOS } from "@payos/payos-checkout";
import {
  getMyQuotaAPI,
  QuotaUsage,
} from "@/features/management/services/quota.service";

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

export default function TroChuyenPage() {
  const [view, setView] = useState<"chat" | "history">("chat");
  const [useSmart, setUseSmart] = useState(false);
  const [messages, setMessages] = useState<
    { id?: string; role: string; content: string; thoughts?: string[] }[]
  >([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
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
  } | null>(null);
  const [selectedImage, setSelectedImage] = useState<{
    name: string;
    data: string;
  } | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
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
    if (!useSmart) {
      showToast(
        "Vui lòng bật Chế độ Suy nghĩ để phân tích tài liệu đính kèm",
        "info",
      );
      return;
    }
    setShowAttachments(!showAttachments);
  };

  const handleToggleSmart = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUseSmart(e.target.checked);
    if (!e.target.checked) {
      setSelectedFile(null);
      setSelectedImage(null);
      setShowAttachments(false);
    }
  };

  const handleFileUpload = (
    e: React.ChangeEvent<HTMLInputElement>,
    type: "image" | "file",
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      if (event.target?.result) {
        const data = event.target.result as string;
        if (type === "image") setSelectedImage({ name: file.name, data });
        if (type === "file") setSelectedFile({ name: file.name, data });
        setShowAttachments(false);
      }
    };
    reader.readAsDataURL(file);
    e.target.value = "";
  };

  const handleSubmit = async (e?: React.FormEvent, retryText?: string) => {
    if (e) e.preventDefault();
    const userMessage = retryText || input.trim();
    if (!userMessage || isSending) return;

    if (useSmart && (user?.wallet_balance || 0) < 20) {
      showToast("Cần tối thiểu 20 dl để duy trì Chế độ Suy nghĩ", "error");
      return;
    }

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

    const msgId = Date.now().toString();
    setMessages((prev) => [
      ...prev,
      { id: msgId, role: "user", content: userMessage },
    ]);
    setInput("");
    setIsSending(true);
    setEditingMessageId(null);
    setShowAttachments(false);

    try {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "", thoughts: [] },
      ]);
      const res = await streamAiChatAPI({
        query: userMessage,
        useSmart,
        session_id: sessionId,
        conversation_history: messages.slice(-8),
        user_id: user?.id || user?._id || "guest",
        document_ids: documentId ? [documentId] : [],
        image_data: selectedImage?.data,
        file_data: selectedFile?.data,
      });

      setSelectedFile(null);
      setSelectedImage(null);

      if (!res.ok) {
        let errorText = "Hệ thống hiện không phản hồi, vui lòng thử lại sau";
        if (res.status === 429)
          errorText =
            "Bạn đã hết hạn mức sử dụng hôm nay. Vui lòng quay lại vào ngày mai hoặc nâng cấp gói cước";
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
              lastMsg.content = "Đã xảy ra lỗi khi xử lý dữ liệu";
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
          lastMsg.content = "Kết nối bị gián đoạn, vui lòng kiểm tra mạng";
        }
        return updated;
      });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="w-full max-w-[1200px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] flex flex-col font-sans text-[#1D1D1F]">
      <div className="flex flex-1 min-h-0 gap-6">
        <aside className="w-full lg:w-[320px] bg-[#F5F5F7] rounded-[18px] flex flex-col overflow-hidden shrink-0 hidden lg:flex">
          <div className="p-6 flex items-center justify-between shrink-0">
            <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
              Lịch sử
            </h2>
            <button
              onClick={() => {
                setCurrentSessionId(null);
                setMessages([]);
              }}
              className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
            >
              <PlusIcon className="w-4 h-4" />
            </button>
          </div>
          <div className="px-6 pb-4 shrink-0">
            <button
              onClick={() => (window.location.href = "/nang-cap")}
              className="w-full flex items-center justify-center gap-2 py-3 bg-[#0071E3] text-white text-[13px] font-semibold rounded-[14px] hover:bg-[#0077ED] transition-colors"
            >
              <Sparkles className="w-4 h-4 text-white" /> Nâng cấp Gói AI
            </button>
          </div>
          <div className="overflow-y-auto px-6 pb-6 flex flex-col gap-2 shrink custom-scrollbar">
            {sessions.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px]">
                <p className="text-[13px] font-medium text-[#6E6E73]">
                  Lịch sử rỗng
                </p>
              </div>
            ) : (
              sessions.map((s) => (
                <div
                  key={s._id}
                  className={`p-3 mx-2 mt-2 rounded-[14px] cursor-pointer transition-colors ${currentSessionId === s._id ? "bg-white border border-transparent" : "border border-transparent hover:bg-[#E8E8ED]"}`}
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
                            `${API_URL}/lich-su/${s._id}`,
                            { headers: { Authorization: `Bearer ${token}` } },
                          );
                          if (res.ok) {
                            const data = await res.json();
                            const mapped = (data.data.messages || []).map(
                              (m: any) => ({
                                id: m.id || m._id || Math.random().toString(),
                                role: m.role || "user",
                                content: m.content || "",
                                thoughts: m.thoughts || [],
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
                                  `${API_URL}/lich-su/${s._id}/tieu-de`,
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
                                      `${API_URL}/lich-su/${s._id}`,
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

        <main className="flex-1 flex flex-col min-w-0 h-full bg-[#F5F5F7] rounded-[24px] relative overflow-hidden">
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto flex flex-col min-h-0 custom-scrollbar relative"
          >
            {messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
                <div className="w-16 h-16 rounded-full bg-[#0071E3] flex items-center justify-center mb-6">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
                <p className="text-[24px] font-semibold text-[#1D1D1F]">
                  Xin chào, {user.full_name}
                </p>
                <p className="text-[15px] text-[#6E6E73] mt-2 leading-relaxed max-w-sm">
                  Tôi có thể giúp gì cho bạn hôm nay?
                </p>
              </div>
            ) : (
              <div className="flex flex-col w-full px-8 py-6 gap-6">
                {messages.map((msg, idx) => {
                  if (msg.role === "user") {
                    return (
                      <div key={idx} className="flex justify-end">
                        <div className="max-w-[85%] bg-[#0071E3] text-white px-5 py-3.5 rounded-[20px] rounded-tr-[4px]">
                          <p className="text-[15px] whitespace-pre-wrap leading-relaxed min-w-0">
                            {msg.content}
                          </p>
                        </div>
                      </div>
                    );
                  }

                  const cleanText = msg.content
                    .replace(/<think>[\s\S]*?<\/think>/g, "")
                    .replace(/<think>[\s\S]*$/, "")
                    .trim();

                  return (
                    <div key={idx} className="flex justify-start">
                      <div className="w-full max-w-[85%]">
                        <div className="py-2 w-full relative group">
                          {msg.thoughts && msg.thoughts.length > 0 && (
                            <div className="mb-3 flex flex-wrap gap-2">
                              {msg.thoughts.map((t, i) => (
                                <span
                                  key={i}
                                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#F5F5F7]  text-[12px] font-medium text-[#6E6E73] whitespace-nowrap"
                                >
                                  <Zap className="w-3.5 h-3.5 text-[#0071E3]" />{" "}
                                  {t}
                                </span>
                              ))}
                            </div>
                          )}
                          {!cleanText && (
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

                          {cleanText && (
                            <ReactMarkdown
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
                              {cleanText}
                            </ReactMarkdown>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="shrink-0 p-6 pt-2">
            <div className="w-full relative">
              {(selectedFile || selectedImage) && (
                <div className="flex gap-4 mb-4 overflow-x-auto pb-2 scrollbar-none">
                  {selectedImage && (
                    <div className="relative group shrink-0">
                      <img
                        src={selectedImage.data}
                        alt=""
                        className="h-16 w-16 object-cover  rounded-[14px]"
                      />
                      <button
                        onClick={() => setSelectedImage(null)}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-[#1D1D1F] text-white flex items-center justify-center rounded-full"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                  {selectedFile && (
                    <div className="relative group shrink-0 h-16 px-4 bg-white  flex items-center gap-3 rounded-[14px]">
                      <FileText className="w-5 h-5 text-[#0071E3] shrink-0" />
                      <span className="text-[13px] font-medium text-[#1D1D1F] truncate max-w-[150px]">
                        {selectedFile.name}
                      </span>
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-[#1D1D1F] text-white flex items-center justify-center rounded-full"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
              )}

              {showAttachments && (
                <div className="absolute bottom-full left-0 mb-2 w-40 bg-white rounded-[14px] py-2 z-50">
                  <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept=".txt,.md,.json,.pdf,.docx,.doc,.xlsx,.xls,.pptx,.mobi,.zip,.csv"
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
                  <button
                    onClick={() => {
                      fileInputRef.current?.click();
                      setShowAttachments(false);
                    }}
                    className="w-full text-left px-4 py-2.5 text-[13px] font-medium text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors flex items-center gap-3"
                  >
                    <FileText className="w-4 h-4 text-[#0071E3]" /> Tài liệu
                  </button>
                  <button
                    onClick={() => {
                      imageInputRef.current?.click();
                      setShowAttachments(false);
                    }}
                    className="w-full text-left px-4 py-2.5 text-[13px] font-medium text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors flex items-center gap-3"
                  >
                    <ImageIcon className="w-4 h-4 text-[#34C759]" /> Hình ảnh
                  </button>
                </div>
              )}

              <form onSubmit={handleSubmit} className="flex gap-3">
                <div className="flex-1 min-h-[56px] bg-white flex items-center px-4 gap-3 focus-within:border-[#0071E3] border border-transparent rounded-[20px] transition-colors">
                  {useSmart && (
                    <button
                      type="button"
                      onClick={handleAttach}
                      className="text-[#6E6E73] shrink-0 rounded-full p-2 hover:bg-[#E8E8ED] transition-colors"
                    >
                      <PlusIcon className="w-5 h-5" />
                    </button>
                  )}
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder=""
                    disabled={isSending}
                    className="flex-1 min-w-0 h-full py-4 text-[15px] bg-transparent outline-none font-medium text-[#1D1D1F] placeholder:text-[#6E6E73]"
                  />
                  <label
                    className={`flex items-center gap-2 ${user?.ai_tier !== "PREMIUM" && user?.role !== "admin" ? "cursor-not-allowed opacity-50" : "cursor-pointer"} group shrink-0 pl-4 border-l border-[#E8E8ED]`}
                  >
                    <span className="text-[13px] font-medium text-[#6E6E73] select-none">
                      Suy nghĩ
                    </span>
                    <div className="relative inline-flex items-center">
                      <input
                        type="checkbox"
                        checked={useSmart}
                        onChange={handleToggleSmart}
                        disabled={
                          user?.ai_tier !== "PREMIUM" && user?.role !== "admin"
                        }
                        className="sr-only peer"
                      />
                      <div className="w-10 h-6 bg-[#D2D2D7] peer-focus:outline-none rounded-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:h-5 after:w-5 after:rounded-full peer-checked:after:translate-x-4 peer-checked:bg-[#34C759] transition-colors"></div>
                    </div>
                  </label>
                </div>
                <button
                  type="submit"
                  disabled={
                    isSending ||
                    !input.trim() ||
                    (useSmart && (user?.wallet_balance || 0) < 20)
                  }
                  className="w-14 h-[56px] shrink-0 bg-[#0071E3] text-white flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed rounded-[20px] transition-colors hover:bg-[#0077ED]"
                >
                  {isSending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <ArrowRight className="w-5 h-5" />
                  )}
                </button>
              </form>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
