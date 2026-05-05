"use client";

import { streamAiChatAPI } from "@/services/ai.service";
import { getToken, API_URL } from "@/services/auth.service";
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
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
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
  retrieve_db: "Đang truy xuất kho tri thức nội bộ",
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

export default function AiChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [view, setView] = useState<"chat" | "history">("chat");
  const [usePro, setUsePro] = useState(false);
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
      const res = await fetch(`${API_URL}/ai/history`, {
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
    if (!usePro) {
      showToast(
        "Vui lòng bật Chế độ chuyên nghiệp để phân tích tài liệu đính kèm",
        "info",
      );
      return;
    }
    setShowAttachments(!showAttachments);
  };

  const handleTogglePro = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUsePro(e.target.checked);
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

    if (usePro && (user?.wallet_balance || 0) < 10) {
      showToast("Số dư không đủ để sử dụng Chế độ chuyên nghiệp", "error");
      return;
    }

    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const token = getToken();
        const res = await fetch(`${API_URL}/ai/history`, {
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
        usePro,
        session_id: sessionId,
        conversation_history: messages.slice(-8),
        user_id: user?._id || "guest",
        image_data: selectedImage?.data,
        file_data: selectedFile?.data,
      });

      setSelectedFile(null);
      setSelectedImage(null);

      if (!res.ok) {
        let errorText = "Hệ thống hiện không phản hồi, vui lòng thử lại sau";
        try {
          const errJson = await res.json();
          errorText = errJson.detail || errorText;
        } catch (e) {
          console.error("Error parsing response error", e);
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
                nodeDescriptions[parsed.node] || `Đang xử lý (${parsed.node})`;
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
      <button
        onClick={() => setIsOpen((v) => !v)}
        className={`fixed bottom-6 right-6 z-[100] w-14 h-14 border border-zinc-200 flex items-center justify-center active:scale-90 rounded-sm ${isOpen ? "bg-black text-white " : "bg-white text-black "}`}
      >
        {isOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <MessageCircle className="w-6 h-6" />
        )}
      </button>

      {isOpen && (
        <div
          className={`fixed bottom-24 right-6 z-[100] ${isExpanded ? "w-[850px]" : "w-[450px]"} h-[700px] bg-white border border-zinc-200 flex flex-col overflow-hidden animate-in slide-in-from-bottom-8 fade-in rounded-md shadow-none`}
        >
          <div className="px-5 py-5 border-b border-zinc-100 flex items-center justify-between shrink-0 bg-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-black flex items-center justify-center border border-black rounded-sm">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-black tracking-tight">
                  DocLib AI
                </h3>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <div className="w-1.5 h-1.5 bg-zinc-400 rounded-sm animate-pulse" />
                  <p className="text-[11px] text-zinc-400 font-bold uppercase tracking-tight">
                    Trợ lý tri thức
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setView(view === "chat" ? "history" : "chat")}
                className={`p-1.5 transition-colors rounded-sm ${view === "history" ? "bg-black text-white" : "text-zinc-400"}`}
              >
                <HistoryIcon className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1.5 text-zinc-400 transition-colors rounded-sm"
              >
                {isExpanded ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-zinc-400 transition-colors rounded-sm"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 min-h-0 bg-white/20 scrollbar-thin scrollbar-thumb-zinc-200"
          >
            {view === "history" ? (
              <div className="space-y-4 animate-in fade-in ">
                <button
                  onClick={() => setView("chat")}
                  className="flex items-center gap-2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-4"
                >
                  <ChevronLeft className="w-3 h-3" /> Quay lại trò chuyện
                </button>
                {sessions.length === 0 ? (
                  <div className="py-20 text-center opacity-30">
                    <HistoryIcon className="w-10 h-10 mx-auto mb-4 stroke-[1]" />
                    <p className="text-[10px] font-bold uppercase tracking-widest">
                      Chưa có dấu ấn tri thức nào
                    </p>
                  </div>
                ) : (
                  sessions.map((s) => (
                    <div
                      key={s._id}
                      className={`p-6 border rounded-sm bg-white cursor-pointer group relative ${currentSessionId === s._id ? "border-black" : "border-zinc-100"}`}
                    >
                      <div
                        onClick={() => {
                          setCurrentSessionId(s._id);
                          const mapped = (s.messages || []).map((m: any) => ({
                            id: m.id || m._id || Date.now().toString(),
                            role: m.role || "user",
                            content: m.content || "",
                            thoughts: m.thoughts || [],
                          }));
                          setMessages(mapped);
                          setView("chat");
                        }}
                      >
                        <p className="text-[11px] font-bold text-black uppercase tracking-tight pr-8">
                          {s.title}
                        </p>
                        <p className="text-[9px] font-bold text-zinc-400 mt-2 uppercase tracking-widest">
                          {new Date(s.updated_at).toLocaleDateString("vi-VN")}
                        </p>
                      </div>
                      <button
                        onClick={async (e) => {
                          e.stopPropagation();
                          try {
                            const token = getToken();
                            const res = await fetch(
                              `${API_URL}/ai/history/${s._id}`,
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
                        className="absolute top-4 right-4 p-1.5 text-zinc-300 opacity-0 rounded-sm"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            ) : messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center px-4">
                <div className="w-16 h-16 bg-white border border-zinc-200 flex items-center justify-center mb-6 rounded-sm">
                  <Cpu className="w-8 h-8 text-black" />
                </div>
                <p className="text-sm font-bold text-black tracking-tight">
                  Xin chào, {user.full_name}
                </p>
                <p className="text-[12px] text-zinc-400 mt-3 leading-relaxed max-w-[240px] font-medium">
                  Tôi có thể giúp bạn phân tích tài liệu, tìm kiếm kiến thức
                  hoặc giải đáp các thắc mắc chuyên sâu
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => {
                const isTyping =
                  msg.role === "assistant" && !msg.content && isSending;
                return (
                  <div
                    key={idx}
                    className={`max-w-[98%] text-sm leading-relaxed animate-in fade-in flex flex-col ${msg.role === "user" ? "self-end items-end" : "self-start items-start"}`}
                  >
                    <div
                      className={`border relative group rounded-sm ${isTyping ? "px-4 py-3 bg-white border-zinc-100 inline-flex items-center" : msg.role === "user" ? "px-5 py-4 bg-black text-white border-black" : "px-5 py-4 bg-white border-zinc-100 text-black w-full"}`}
                    >
                      {msg.role === "user" && !isSending && (
                        <button
                          onClick={() => setEditingMessageId(msg.id || null)}
                          className="absolute -left-10 top-1/2 -translate-y-1/2 opacity-0 p-2 text-zinc-300 rounded-sm"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                      {editingMessageId && editingMessageId === msg.id ? (
                        <div className="flex flex-col gap-3 py-1">
                          <textarea
                            defaultValue={msg.content}
                            className="w-full bg-zinc-900 text-white p-3 text-[13px] border border-zinc-700 focus:outline-none min-h-[80px] rounded-sm"
                            onKeyDown={(e: any) =>
                              e.key === "Enter" &&
                              !e.shiftKey &&
                              (e.preventDefault(),
                              handleSubmit(undefined, e.target.value))
                            }
                          />
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => setEditingMessageId(null)}
                              className="text-[10px] font-bold uppercase px-3 py-1.5 text-zinc-400 transition-colors rounded-sm"
                            >
                              Hủy
                            </button>
                            <button
                              onClick={(ev) => {
                                const ta =
                                  ev.currentTarget.parentElement?.parentElement?.querySelector(
                                    "textarea",
                                  ) as HTMLTextAreaElement;
                                handleSubmit(undefined, ta.value);
                              }}
                              className="text-[10px] font-bold uppercase px-3 py-1.5 bg-white text-black rounded-sm"
                            >
                              Gửi lại
                            </button>
                          </div>
                        </div>
                      ) : (
                        <>
                          {msg.role === "assistant" &&
                            msg.thoughts &&
                            msg.thoughts.length > 0 && (
                              <details className="mb-4 border-b border-zinc-100 pb-4 cursor-pointer group/thoughts">
                                <summary className="flex items-center gap-2 text-[11px] font-bold text-zinc-400 group-hover/thoughts:text-black transition-colors list-none">
                                  <Cpu className="w-3.5 h-3.5" />
                                  <span>Quá trình xử lý tri thức</span>
                                </summary>
                                <div className="mt-4 flex flex-col gap-3 pl-2 border-l border-zinc-100 ml-1.5">
                                  {msg.thoughts.map((t, idx2) => (
                                    <div
                                      key={idx2}
                                      className="text-[12px] text-zinc-500 flex items-center gap-3"
                                    >
                                      <div className="w-1 h-1 bg-zinc-300 shrink-0 rounded-sm" />
                                      <span className="font-medium">{t}</span>
                                    </div>
                                  ))}
                                </div>
                              </details>
                            )}
                          <div
                            className={`w-full prose prose-sm max-w-none ${msg.role === "user" ? "prose-invert" : "prose-zinc"}`}
                          >
                            {msg.role === "assistant" &&
                            !msg.content &&
                            isSending ? (
                              <div className="flex items-center gap-1.5 py-2">
                                <div
                                  className="w-2 h-2 bg-zinc-300 rounded-sm animate-bounce"
                                  style={{ animationDelay: "0ms" }}
                                />
                                <div
                                  className="w-2 h-2 bg-zinc-300 rounded-sm animate-bounce"
                                  style={{ animationDelay: "150ms" }}
                                />
                                <div
                                  className="w-2 h-2 bg-zinc-300 rounded-sm animate-bounce"
                                  style={{ animationDelay: "300ms" }}
                                />
                              </div>
                            ) : (
                              <ReactMarkdown
                                remarkPlugins={[remarkGfm, remarkMath]}
                                rehypePlugins={[rehypeKatex, rehypeHighlight]}
                                components={{
                                  p: ({ children }) => (
                                    <p className="mb-4 last:mb-0 font-medium leading-relaxed">
                                      {children}
                                    </p>
                                  ),
                                  code({
                                    node,
                                    inline,
                                    className,
                                    children,
                                    ...props
                                  }: any) {
                                    const match = /language-(\w+)/.exec(
                                      className || "",
                                    );
                                    const content = String(children).replace(
                                      /\n$/,
                                      "",
                                    );
                                    if (!inline && match) {
                                      const lang = match[1];
                                      return (
                                        <div className="my-3 bg-zinc-900 border border-zinc-800 overflow-x-auto rounded-sm">
                                          <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-800">
                                            <span className="text-[10px] font-bold text-zinc-500 uppercase">
                                              {lang}
                                            </span>
                                            <button
                                              onClick={() => {
                                                navigator.clipboard.writeText(
                                                  content,
                                                );
                                                showToast(
                                                  "Đã sao chép",
                                                  "info",
                                                );
                                              }}
                                              className="text-[10px] font-bold text-zinc-500 transition-colors uppercase rounded-sm"
                                            >
                                              Sao chép
                                            </button>
                                          </div>
                                          <pre className="p-4 overflow-x-auto">
                                            <code className="text-[13px] font-mono text-zinc-300">
                                              {content}
                                            </code>
                                          </pre>
                                        </div>
                                      );
                                    }
                                    return (
                                      <code
                                        className={`${className} bg-zinc-100 px-1 py-0.5 text-black font-mono text-[13px] rounded-sm`}
                                        {...props}
                                      >
                                        {children}
                                      </code>
                                    );
                                  },
                                  table: ({ children }) => (
                                    <div className="overflow-x-auto my-4 border border-zinc-100 rounded-sm">
                                      <table className="min-w-full divide-y divide-zinc-200">
                                        {children}
                                      </table>
                                    </div>
                                  ),
                                  th: ({ children }) => (
                                    <th className="px-3 py-2 bg-white text-left text-[11px] font-bold text-black uppercase tracking-wider">
                                      {children}
                                    </th>
                                  ),
                                  td: ({ children }) => (
                                    <td className="px-3 py-2 whitespace-nowrap text-zinc-600 border-t border-zinc-100">
                                      {children}
                                    </td>
                                  ),
                                }}
                              >
                                {msg.content || ""}
                              </ReactMarkdown>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div className="p-5 bg-white border-t border-zinc-100 shrink-0 relative">
            {(selectedFile || selectedImage) && (
              <div className="flex gap-3 mb-4 overflow-x-auto pb-1 scrollbar-none">
                {selectedImage && (
                  <div className="relative group shrink-0">
                    <img
                      src={selectedImage.data}
                      alt=""
                      className="h-14 w-14 object-cover border border-zinc-200 rounded-sm"
                    />
                    <button
                      onClick={() => setSelectedImage(null)}
                      className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-black text-white flex items-center justify-center transition-colors rounded-sm"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                )}
                {selectedFile && (
                  <div className="relative group shrink-0 h-14 px-4 bg-white border border-zinc-200 flex items-center gap-3 rounded-sm">
                    <FileText className="w-4 h-4 text-black shrink-0" />
                    <span className="text-[12px] font-bold text-zinc-600 truncate max-w-[120px]">
                      {selectedFile.name}
                    </span>
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-black text-white flex items-center justify-center transition-colors rounded-sm"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>
            )}

            {showAttachments && (
              <div className="absolute bottom-full left-4 mb-4 bg-white border border-zinc-200 p-2 flex gap-2 animate-in fade-in slide-in-from-bottom-4 z-50 rounded-sm">
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
                  className="flex flex-col items-center gap-2 p-4 min-w-[80px] rounded-sm"
                >
                  <div className="w-12 h-12 border border-zinc-200 flex items-center justify-center rounded-sm">
                    <FileText className="w-6 h-6 text-black" />
                  </div>
                  <span className="text-[11px] font-bold text-black">
                    Tài liệu
                  </span>
                </button>
                <button
                  onClick={() => imageInputRef.current?.click()}
                  className="flex flex-col items-center gap-2 p-4 min-w-[80px] rounded-sm"
                >
                  <div className="w-12 h-12 border border-zinc-200 flex items-center justify-center rounded-sm">
                    <ImageIcon className="w-6 h-6 text-black" />
                  </div>
                  <span className="text-[11px] font-bold text-black">
                    Hình ảnh
                  </span>
                </button>
              </div>
            )}

            <div className="flex items-center justify-between mb-4 px-1">
              <label className="flex items-center gap-3 cursor-pointer group">
                <div className="relative inline-flex items-center">
                  <input
                    type="checkbox"
                    checked={usePro}
                    onChange={handleTogglePro}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-zinc-200 peer-focus:outline-none after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:h-4 after:w-4 after: peer-checked:after:translate-x-full peer-checked:bg-black rounded-sm"></div>
                </div>
                <span className="text-[11px] font-bold text-zinc-400 transition-colors">
                  Chế độ chuyên nghiệp
                </span>
              </label>
              {usePro && (
                <div className="flex items-center gap-1.5 px-3 py-1 bg-white border border-zinc-100 rounded-sm">
                  <span className="text-[11px] font-bold text-black">
                    10 dl
                  </span>
                  <Coins className="w-3 h-3 text-black" />
                </div>
              )}
            </div>

            <form onSubmit={handleSubmit} className="flex gap-2">
              <div className="flex-1 h-14 bg-white border border-zinc-200 flex items-center px-4 gap-3 focus-within:border-black focus-within:bg-white rounded-sm">
                <button
                  type="button"
                  onClick={handleAttach}
                  className="text-zinc-400 transition-colors shrink-0 rounded-sm"
                >
                  <Paperclip className="w-5 h-5" />
                </button>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder=""
                  disabled={isSending}
                  className="flex-1 h-full text-sm bg-transparent outline-none font-medium"
                />
              </div>
              <button
                type="submit"
                disabled={
                  isSending ||
                  !input.trim() ||
                  (usePro && (user?.wallet_balance || 0) < 10)
                }
                className="w-14 h-14 bg-black text-white flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed active:scale-95 rounded-sm"
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
      )}
    </div>
  );
}