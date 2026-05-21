"use client";

import { streamAiChatAPI } from "@/services/ai.service";
import { getToken, API_URL } from "@/services/authentication.service";
import { useSearchParams } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import {
  MessageCircle,
  X,
  Send,
  Cpu,
  Zap,
  Coins,
  Paperclip,
  Image as ImageIcon,
  FileText,
  Loader2,
  Maximize2,
  Minimize2,
  History as HistoryIcon,
  Edit2,
  ChevronLeft,
  Trash2,
  Plus as PlusIcon,
  User,
  Activity,
} from "lucide-react";
import { useAuth } from "@/contexts/Auth";
import { getMyQuotaAPI, QuotaUsage } from "@/services/quota.service";

function QuotaIndicator() {
  const [usage, setUsage] = useState<QuotaUsage | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchQuota = async () => {
    try {
      const data = await getMyQuotaAPI();
      setUsage(data);
    } catch (err) {
      console.error("Lỗi lấy thông tin hạn mức:", err);
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

  const reqPercent = Math.min(100, (usage.used_requests / usage.limit_requests) * 100);
  const tokenPercent = Math.min(100, (usage.used_tokens / usage.limit_tokens) * 100);

  return (
    <div className="flex flex-col gap-3 p-4 bg-zinc-50 border border-zinc-200 rounded-none animate-in fade-in slide-in-from-top-2 ">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-black" />
          <span className="text-[10px] font-bold tracking-widest text-black">
            Hạn mức sử dụng ngày
          </span>
        </div>
      </div>

      <div className="space-y-3">
        <div className="space-y-1.5">
          <div className="flex justify-between text-[10px] font-medium text-zinc-500 tracking-tighter">
            <span>Yêu cầu</span>
            <span>{usage.used_requests} / {usage.limit_requests}</span>
          </div>
          <div className="h-1 w-full bg-zinc-200 rounded-none overflow-hidden">
            <div 
              className={`h-full   ${reqPercent > 90 ? 'bg-black' : 'bg-zinc-800'}`}
              style={{ width: `${reqPercent}%` }}
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between text-[10px] font-medium text-zinc-500 tracking-tighter">
            <span>Token</span>
            <span>{usage.used_tokens.toLocaleString()} / {usage.limit_tokens.toLocaleString()}</span>
          </div>
          <div className="h-1 w-full bg-zinc-200 rounded-none overflow-hidden">
            <div 
              className={`h-full   ${tokenPercent > 90 ? 'bg-black' : 'bg-zinc-800'}`}
              style={{ width: `${tokenPercent}%` }}
            />
          </div>
        </div>
      </div>
      
      { (reqPercent >= 100 || tokenPercent >= 100) && (
        <p className="text-[10px] font-bold text-black mt-1">
          Đã đạt giới hạn hôm nay
        </p>
      )}
    </div>
  );
}
import { useToast } from "@/contexts/Toast";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";

const nodeDescriptions: Record<string, string> = {
  contextualize_question: "Đang phân tích bối cảnh hội thoại",
  route_question: "Đang xác định ý định yêu cầu",
  route_query: "Đang định tuyến tới chuyên gia",
  retrieve_db: "Đang truy xuất kho nội dung nội bộ",
  retrieve_internet: "Đang tìm kiếm thông tin trên internet",
  grade_documents: "Đang thẩm định độ tin cậy của dữ liệu",
  transform_query: "Đang tinh chỉnh chiến lược tìm kiếm",
  generate: "Đang tổng hợp câu trả lời từ dữ liệu",
  generate_direct: "Đang phản hồi trực tiếp",
  grade_generation: "Đang kiểm tra tính xác thực thông tin",
  billing: "Đang kết nối hệ thống tài chính",
  workspace: "Đang truy cập quản lý thư viện",
  multi: "Đang tổng hợp dữ liệu đa nguồn",
  rag: "Đang thực hiện quy trình RAG chuyên sâu",
  chat: "Đang trò chuyện trực tiếp",
};

interface AiChatProps {
  standalone?: boolean;
}

export default function AiChat({ standalone = false }: AiChatProps) {
  const [isOpen, setIsOpen] = useState(standalone);
  const [isExpanded, setIsExpanded] = useState(false);
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
      const res = await fetch(`${API_URL}/ai/lich-su`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data.data || []);
      }
    } catch (err) {
      console.error("Lỗi tải lịch sử hội thoại:", err);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchHistory();
    }
  }, [isOpen]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  if (!user) {
    return null;
  }

  const handleAttach = () => {
    if (!useSmart) {
      showToast(
        "Vui lòng bật Chế độ chuyên sâu để phân tích tài liệu đính kèm",
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
      showToast("Cần tối thiểu 20 dl để duy trì Chế độ chuyên sâu", "error");
      return;
    }

    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const token = getToken();
        const res = await fetch(`${API_URL}/ai/lich-su`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ first_query: userMessage }),
        });
        if (res.ok) {
          const data = await res.json();
          sessionId = data.data._id;
          setCurrentSessionId(sessionId);
          fetchHistory();
        }
      } catch (err) {
        console.error("Lỗi khởi tạo phiên hội thoại:", err);
      }
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
        document_id: documentId || undefined,
        image_data: selectedImage?.data,
        file_data: selectedFile?.data,
      });

      setSelectedFile(null);
      setSelectedImage(null);

      if (!res.ok) {
        let errorText = "Hệ thống hiện không phản hồi, vui lòng thử lại sau";
        if (res.status === 429) {
          errorText = "Bạn đã hết hạn mức sử dụng hôm nay. Vui lòng quay lại vào ngày mai hoặc nâng cấp gói cước";
        } else {
          try {
            const errJson = await res.json();
            errorText = errJson.message || errJson.detail || errorText;
          } catch (e) {
            console.error("Error parsing response error", e);
          }
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
              const nodeVi =
                nodeDescriptions[parsed.node] || parsed.node;
              setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];
                if (
                  lastMsg.role === "assistant" &&
                  !lastMsg.thoughts?.includes(nodeVi)
                ) {
                  lastMsg.thoughts = [...(lastMsg.thoughts || []), nodeVi];
                }
                return updated;
              });
            } catch (e) {
              console.error("Error parsing status data", e);
            }
          } else if (type === "plan" && data) {
            try {
              const parsed = JSON.parse(data);
              setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];
                if (lastMsg.role === "assistant") {
                  lastMsg.thoughts = [...(lastMsg.thoughts || []), "Đã lập kế hoạch:", ...(parsed.steps || [])];
                }
                return updated;
              });
            } catch (e) {
              console.error("Error parsing plan data", e);
            }
          } else if (type === "tool" && data) {
            try {
              const parsed = JSON.parse(data);
              const toolMsg = `Công cụ ${parsed.agent} xử lý thành công`;
              setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];
                if (
                  lastMsg.role === "assistant" &&
                  !lastMsg.thoughts?.includes(toolMsg)
                ) {
                  lastMsg.thoughts = [...(lastMsg.thoughts || []), toolMsg];
                }
                return updated;
              });
            } catch (e) {
              console.error("Error parsing tool data", e);
            }
          } else if (type === "message" && data) {
            try {
              const parsed = JSON.parse(data);
              fullText += parsed.chunk;
              setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];
                if (lastMsg.role === "assistant") lastMsg.content = fullText;
                return updated;
              });
            } catch (e) {
              console.error("Error parsing message data", e);
            }
          } else if (type === "done" || data === "[DONE]") {
            isDone = true;
          } else if (type === "error" && data) {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1].content =
                "Đã xảy ra lỗi khi xử lý dữ liệu";
              return updated;
            });
          } else if (!type && data) {
            try {
              const parsed = JSON.parse(data);
              if (parsed.error) {
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1].content = parsed.error;
                  return updated;
                });
                isDone = true;
              } else if (parsed.chunk) {
                fullText += parsed.chunk;
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastMsg = updated[updated.length - 1];
                  if (lastMsg.role === "assistant") lastMsg.content = fullText;
                  return updated;
                });
              }
            } catch (e) {
              console.error("Error parsing raw data", e);
            }
          }
        }
      }
    } catch (err) {
      console.error("Submission error", err);
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
    <div className="font-sans">
      {!standalone && (
        <button
          onClick={() => setIsOpen((v) => !v)}
          className={`fixed bottom-6 right-6 z-[100] w-14 h-14 border border-zinc-200 flex items-center justify-center active:scale-95 rounded-none ${isOpen ? "bg-black text-white" : "bg-white text-black"}`}
        >
          {isOpen ? (
            <X className="w-6 h-6" />
          ) : (
            <MessageCircle className="w-6 h-6" />
          )}
        </button>
      )}

      {isOpen && (
        <div
          className={
            standalone
              ? "w-full h-full bg-white flex flex-col overflow-hidden animate-in fade-in"
              : `fixed bottom-24 right-6 z-[100] ${isExpanded ? "w-[900px]" : "w-[450px]"} h-[80vh] min-h-[600px] max-h-[800px] bg-white border border-zinc-200 flex flex-col overflow-hidden animate-in slide-in-from-bottom-4 fade-in rounded-none `
          }
        >
          <div className="px-6 py-5 border-b border-zinc-200 flex items-center justify-between shrink-0 bg-white">
            <div className="flex items-center gap-4">
              <div className="w-8 h-8 bg-black flex items-center justify-center rounded-none">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="text-base font-medium text-black">
                  Thiết bị nghiên cứu
                </h3>
                <p className="text-sm text-zinc-500 mt-0.5">
                  Trợ lý AI
                </p>
              </div>
            </div>
            {!standalone && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setCurrentSessionId(null);
                    setMessages([]);
                    setView("chat");
                  }}
                  className="p-2 text-zinc-500   rounded-none border border-zinc-100 "
                  title="Cuộc hội thoại mới"
                >
                  <PlusIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setView(view === "chat" ? "history" : "chat")}
                  className={`p-2  rounded-none border ${view === "history" ? "bg-black text-white border-black" : "text-zinc-500  border-zinc-100 "}`}
                  title="Lịch sử nghiên cứu"
                >
                  <HistoryIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="p-2 text-zinc-500   rounded-none border border-zinc-100 "
                  title={isExpanded ? "Thu nhỏ" : "Mở rộng"}
                >
                  {isExpanded ? (
                    <Minimize2 className="w-4 h-4" />
                  ) : (
                    <Maximize2 className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 text-zinc-500   rounded-none border border-zinc-100 "
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
            {standalone && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setCurrentSessionId(null);
                    setMessages([]);
                    setView("chat");
                  }}
                  className="px-4 py-2 text-xs font-bold  border bg-white text-black border-zinc-200 "
                >
                  Cuộc hội thoại mới
                </button>
                <button
                  onClick={() => setView(view === "chat" ? "history" : "chat")}
                  className={`px-4 py-2 text-xs font-bold  border ${view === "history" ? "bg-black text-white border-black" : "bg-white text-black border-zinc-200 "}`}
                >
                  {view === "history" ? "Quay lại" : "Lịch sử nghiên cứu"}
                </button>
              </div>
            )}
          </div>

          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto flex flex-col min-h-0 bg-white no-scrollbar"
          >
            {view === "history" ? (
              <div className="p-6 space-y-6 animate-in fade-in w-full">
                <QuotaIndicator />
                
                {sessions.length === 0 ? (
                  <div className="py-20 text-center">
                    <HistoryIcon className="w-8 h-8 mx-auto mb-4 text-zinc-300" />
                    <p className="text-sm text-zinc-500">
                      Chưa có phiên nghiên cứu nào
                    </p>
                  </div>
                ) : (
                  sessions.map((s) => (
                    <div
                      key={s._id}
                      className={`p-5 border bg-white cursor-pointer group relative rounded-none  ${currentSessionId === s._id ? "border-black" : "border-zinc-200 "}`}
                    >
                      <div
                        onClick={async () => {
                          const token = getToken();
                          setCurrentSessionId(s._id);
                          setView("chat");
                          try {
                            const res = await fetch(`${API_URL}/ai/lich-su/${s._id}`, {
                              headers: { Authorization: `Bearer ${token}` }
                            });
                            if (res.ok) {
                              const data = await res.json();
                              const mapped = (data.data.messages || []).map((m: any) => ({
                                id: m.id || m._id || Math.random().toString(),
                                role: m.role || "user",
                                content: m.content || "",
                                thoughts: m.thoughts || [],
                              }));
                              setMessages(mapped);
                            } else {
                              const mapped = (s.messages || []).map((m: any) => ({
                                id: m.id || m._id || Math.random().toString(),
                                role: m.role || "user",
                                content: m.content || "",
                                thoughts: m.thoughts || [],
                              }));
                              setMessages(mapped);
                            }
                          } catch (e) {
                             console.error("Lỗi tải chi tiết lịch sử", e);
                          }
                        }}
                      >
                        <p className="text-sm font-medium text-black pr-8 truncate">
                          {s.title}
                        </p>
                        <p className="text-sm text-zinc-500 mt-2">
                          {new Date(s.updated_at).toLocaleDateString("vi-VN")}
                        </p>
                      </div>
                      <button
                        onClick={async (e) => {
                          e.stopPropagation();
                          try {
                            const token = getToken();
                            const res = await fetch(
                              `${API_URL}/ai/lich-su/${s._id}`,
                              {
                                method: "DELETE",
                                headers: { Authorization: `Bearer ${token}` },
                              },
                            );
                            if (res.ok) {
                              if (currentSessionId === s._id) {
                                setCurrentSessionId(null);
                                setMessages([]);
                              }
                              fetchHistory();
                            }
                          } catch (err) {
                            console.error("Delete session error", err);
                          }
                        }}
                        className="absolute top-5 right-5 p-1 text-zinc-400 opacity-0 group-   rounded-none"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            ) : messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
                <div className="w-12 h-12 bg-white border border-zinc-200 flex items-center justify-center mb-6 rounded-none">
                  <Cpu className="w-5 h-5 text-black" />
                </div>
                <p className="text-lg font-medium text-black">
                  Xin chào, {user.full_name}
                </p>
                <p className="text-sm text-zinc-500 mt-3 leading-relaxed max-w-sm">
                  Tôi có thể giúp bạn phân tích tài liệu, tìm kiếm thông tin hoặc giải đáp các thắc mắc chuyên sâu.
                </p>
                <div className="mt-8 w-full max-w-[280px]">
                  <QuotaIndicator />
                </div>
              </div>
            ) : (
              <div className="flex flex-col w-full p-6 gap-8">
              {messages.map((msg, idx) => {
                if (msg.role === "user") {
                  return (
                    <div
                      key={idx}
                      className="flex justify-end animate-in fade-in slide-in-from-right-4"
                    >
                      <div className="w-full max-w-[95%]">
                        <div className="flex items-center justify-end gap-3 mb-2">
                          <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                            Bạn
                          </span>
                          <div className="w-8 h-8 bg-black flex items-center justify-center rounded-none">
                            <User className="w-4 h-4 text-white" />
                          </div>
                        </div>
                        <div className="bg-zinc-100 border border-zinc-200 px-5 py-4 rounded-none">
                          <p className="text-sm font-medium text-black whitespace-pre-wrap leading-relaxed">
                            {msg.content}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                }

                return (
                  <div
                    key={idx}
                    className="flex justify-start animate-in fade-in slide-in-from-left-4"
                  >
                    <div className="w-full max-w-[95%]">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 bg-black flex items-center justify-center rounded-none">
                          <Cpu className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-black">
                          {useSmart ? "Trợ lý Chuyên sâu" : "Trợ lý DocLib"}
                        </span>
                        {msg.thoughts && msg.thoughts.length > 0 && (
                          <div className="flex gap-1">
                            <div className="w-1.5 h-1.5 bg-black animate-pulse" />
                            <div
                              className="w-1.5 h-1.5 bg-black animate-pulse"
                              style={{ animationDelay: "0.2s" }}
                            />
                            <div
                              className="w-1.5 h-1.5 bg-black animate-pulse"
                              style={{ animationDelay: "0.4s" }}
                            />
                          </div>
                        )}
                      </div>

                      {(() => {
                        const cleanText = msg.content
                          .replace(/<think>[\s\S]*?<\/think>/g, "")
                          .trim();

                        return (
                          <>
                            {msg.thoughts && msg.thoughts.length > 0 && (
                              <div className="mb-4 space-y-2">
                                {msg.thoughts.map((thought, tidx) => (
                                  <div
                                    key={tidx}
                                    className="flex items-center gap-3 text-zinc-400 group"
                                  >
                                    <div className="w-1 h-1 bg-zinc-300 group- " />
                                    <span className="text-[11px] font-medium tracking-tight">
                                      {nodeDescriptions[thought] || thought}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}

                            <div className="bg-white border border-zinc-200 p-0 rounded-none overflow-hidden relative group">
                              <div className="absolute top-4 right-4 flex items-center gap-2 opacity-0 group-  z-10">
                                <button
                                  onClick={() => {
                                    navigator.clipboard.writeText(msg.content);
                                    showToast("Đã sao chép vào bộ nhớ tạm");
                                  }}
                                  className="w-8 h-8 bg-white border border-zinc-200 flex items-center justify-center    rounded-none"
                                  title="Sao chép"
                                >
                                  <div className="w-3 h-3 border-2 border-current" />
                                </button>
                                <button
                                  onClick={(ev) => {
                                    const ta =
                                      ev.currentTarget.parentElement?.parentElement?.querySelector(
                                        "textarea",
                                      ) as HTMLTextAreaElement;
                                    if (ta) {
                                      ta.style.height = "auto";
                                      ta.style.height = ta.scrollHeight + "px";
                                    }
                                  }}
                                  className="w-8 h-8 bg-white border border-zinc-200 flex items-center justify-center    rounded-none"
                                  title="Phóng to"
                                >
                                  <Maximize2 className="w-3 h-3" />
                                </button>
                              </div>

                              {!cleanText &&
                              msg.thoughts &&
                              msg.thoughts.length > 0 ? (
                                <div className="p-5 flex items-center gap-3 text-zinc-400">
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                  <span className="text-sm font-medium animate-pulse">
                                    Đang suy nghĩ
                                  </span>
                                </div>
                              ) : (
                                <ReactMarkdown
                                  remarkPlugins={[remarkGfm, remarkMath]}
                                  rehypePlugins={[rehypeKatex, rehypeHighlight]}
                                  className="prose prose-sm max-w-none prose-zinc p-6
                                    prose-headings:font-bold prose-headings:tracking-tight prose-headings:text-black
                                    prose-p:text-zinc-600 prose-p:leading-relaxed prose-p:text-[14px]
                                    prose-strong:text-black prose-strong:font-bold
                                    prose-code:bg-zinc-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:text-black prose-code:before:content-none prose-code:after:content-none
                                    prose-pre:bg-zinc-950 prose-pre:rounded-none prose-pre:p-0
                                    prose-ul:list-square prose-li:text-zinc-600
                                    prose-table:border prose-table:border-zinc-200
                                    prose-th:bg-zinc-50 prose-th:p-4 prose-th:text-black
                                    prose-td:p-4 prose-td:border-t prose-td:border-zinc-100"
                                  components={{
                                    pre: ({ children }) => (
                                      <pre className="relative group bg-zinc-950 p-6 overflow-x-auto scrollbar-thin scrollbar-thumb-zinc-800 rounded-none">
                                        <div className="absolute top-4 right-4 opacity-0 group- ">
                                          <button
                                            onClick={() => {
                                              const code = (
                                                children as any
                                              )?.props?.children;
                                              if (code) {
                                                navigator.clipboard.writeText(
                                                  String(code),
                                                );
                                                showToast("Đã sao chép mã nguồn");
                                              }
                                            }}
                                            className="px-3 py-1.5 bg-zinc-800 text-zinc-400 text-[10px] font-bold uppercase tracking-widest    rounded-none"
                                          >
                                            Sao chép
                                          </button>
                                        </div>
                                        {children}
                                      </pre>
                                    ),
                                    code: ({
                                      node,
                                      inline,
                                      className,
                                      children,
                                      ...props
                                    }: any) => {
                                      if (inline) {
                                        return (
                                          <code
                                            className="bg-zinc-100 text-black px-1.5 py-0.5 font-medium rounded-none"
                                            {...props}
                                          >
                                            {children}
                                          </code>
                                        );
                                      }
                                      return (
                                        <code className={className} {...props}>
                                          {children}
                                        </code>
                                      );
                                    },
                                    table: ({ children }) => (
                                      <div className="my-6 border border-zinc-200 overflow-x-auto rounded-none">
                                        <table className="w-full border-collapse">
                                          {children}
                                        </table>
                                      </div>
                                    ),
                                    th: ({ children }) => (
                                      <th className="px-4 py-3 bg-zinc-50 text-left text-[11px] font-bold uppercase tracking-widest text-black border-b border-zinc-200">
                                        {children}
                                      </th>
                                    ),
                                    td: ({ children }) => (
                                      <td className="px-4 py-3 whitespace-nowrap text-sm text-zinc-600 border-b border-zinc-100">
                                        {children}
                                      </td>
                                    ),
                                  }}
                                >
                                  {cleanText}
                                </ReactMarkdown>
                              )}
                            </div>
                          </>
                        );
                      })()}
                    </div>
                  </div>
                );
              })}
              </div>
            )}
          </div>

          <div className="p-4 bg-white border-t border-zinc-200 shrink-0 relative flex justify-center">
            <div className="w-full relative">
              {(selectedFile || selectedImage) && (
                <div className="flex gap-4 mb-4 overflow-x-auto pb-2 scrollbar-none">
                  {selectedImage && (
                    <div className="relative group shrink-0">
                      <img
                        src={selectedImage.data}
                        alt=""
                        className="h-16 w-16 object-cover border border-zinc-200 rounded-none"
                      />
                      <button
                        onClick={() => setSelectedImage(null)}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-black text-white flex items-center justify-center  rounded-none"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                  {selectedFile && (
                    <div className="relative group shrink-0 h-16 px-4 bg-white border border-zinc-200 flex items-center gap-3 rounded-none">
                      <FileText className="w-5 h-5 text-black shrink-0" />
                      <span className="text-sm font-medium text-black truncate max-w-[150px]">
                        {selectedFile.name}
                      </span>
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-black text-white flex items-center justify-center  rounded-none"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
              )}

              {showAttachments && (
                <div className="absolute bottom-full left-0 mb-4 bg-white border border-zinc-200 p-2 flex gap-2 animate-in fade-in slide-in-from-bottom-4 z-50 rounded-none ">
                  <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept=".txt,.md,.json,.pdf,.docx,.doc,.xlsx,.xls,.pptx,.epub,.mobi,.zip,.csv"
                    onChange={(e) => handleFileUpload(e, "file")}
                  />
                  <input
                    type="file"
                    ref={imageInputRef}
                    className="hidden"
                    accept="image/*"
                    onChange={(e) => handleFileUpload(e, "image")}
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="flex flex-col items-center gap-3 p-4 min-w-[90px] rounded-none   border border-transparent "
                  >
                    <div className="w-10 h-10 border border-zinc-200 flex items-center justify-center rounded-none bg-white">
                      <FileText className="w-5 h-5 text-black" />
                    </div>
                    <span className="text-sm font-medium text-black">
                      Tài liệu
                    </span>
                  </button>
                  <button
                    onClick={() => imageInputRef.current?.click()}
                    className="flex flex-col items-center gap-3 p-4 min-w-[90px] rounded-none   border border-transparent "
                  >
                    <div className="w-10 h-10 border border-zinc-200 flex items-center justify-center rounded-none bg-white">
                      <ImageIcon className="w-5 h-5 text-black" />
                    </div>
                    <span className="text-sm font-medium text-black">
                      Hình ảnh
                    </span>
                  </button>
                </div>
              )}

              <div className="flex items-center justify-between mb-3">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <div className="relative inline-flex items-center">
                    <input
                      type="checkbox"
                      checked={useSmart}
                      onChange={handleToggleSmart}
                      className="sr-only peer"
                    />
                    <div className="w-8 h-4 bg-zinc-200 peer-focus:outline-none after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:h-3 after:w-3 after: peer-checked:after:translate-x-4 peer-checked:bg-black rounded-none "></div>
                  </div>
                  <span className="text-xs font-bold uppercase tracking-widest text-zinc-400  group-">
                    Chuyên sâu
                  </span>
                </label>
                {useSmart && (
                  <div className="flex items-center gap-1.5 px-2 py-1 bg-zinc-50 border border-zinc-200 rounded-none">
                    <span className="text-xs font-bold">
                      20 dl/tháng
                    </span>
                    <Coins className="w-3 h-3 text-black" />
                  </div>
                )}
              </div>

              <form onSubmit={handleSubmit} className="flex gap-3">
                <div className="flex-1 min-h-[56px] bg-white border border-zinc-200 flex items-center px-4 gap-3 focus-within:border-black rounded-none ">
                  <button
                    type="button"
                    onClick={handleAttach}
                    className="text-zinc-400   shrink-0 rounded-none p-1"
                  >
                    <Paperclip className="w-5 h-5" />
                  </button>
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder=""
                    disabled={isSending}
                    className="flex-1 h-full py-4 text-sm bg-transparent outline-none font-medium text-black placeholder:text-zinc-400"
                  />
                </div>
                <button
                  type="submit"
                  disabled={
                    isSending ||
                    !input.trim() ||
                    (useSmart && (user?.wallet_balance || 0) < 20)
                  }
                  className="w-14 shrink-0 bg-black text-white flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed  rounded-none"
                >
                  {isSending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
