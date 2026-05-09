"use client";

import { streamAiChatAPI } from "@/services/ai.service";
import { getToken, API_URL } from "@/services/authentication.service";
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
    if (!usePro) {
      showToast(
        "Vui lòng bật Chế độ chuyên sâu để phân tích tài liệu đính kèm",
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

    if (usePro && (user?.wallet_balance || 0) < 20) {
      showToast("Cần tối thiểu 20 dl để duy trì Chế độ chuyên nghiệp", "error");
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
              ? "w-full h-full bg-white border-zinc-200 flex flex-col overflow-hidden animate-in fade-in"
              : `fixed bottom-24 right-6 z-[100] ${isExpanded ? "w-[900px]" : "w-[450px]"} h-[80vh] min-h-[600px] max-h-[800px] bg-white border border-zinc-200 flex flex-col overflow-hidden animate-in slide-in-from-bottom-4 fade-in rounded-none shadow-none`
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
                  onClick={() => setView(view === "chat" ? "history" : "chat")}
                  className={`p-2 transition-colors rounded-none ${view === "history" ? "bg-black text-white" : "text-zinc-500 hover:text-black"}`}
                >
                  <HistoryIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="p-2 text-zinc-500 hover:text-black transition-colors rounded-none"
                >
                  {isExpanded ? (
                    <Minimize2 className="w-4 h-4" />
                  ) : (
                    <Maximize2 className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 text-zinc-500 hover:text-black transition-colors rounded-none"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
            {standalone && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setView(view === "chat" ? "history" : "chat")}
                  className={`px-4 py-2 text-xs font-bold transition-all border ${view === "history" ? "bg-black text-white border-black" : "bg-white text-black border-zinc-200 hover:bg-zinc-50"}`}
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
              <div className="p-6 space-y-4 animate-in fade-in max-w-3xl mx-auto w-full">
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
                      className={`p-5 border bg-white cursor-pointer group relative rounded-none transition-colors ${currentSessionId === s._id ? "border-black" : "border-zinc-200 hover:border-black"}`}
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
                        className="absolute top-5 right-5 p-1 text-zinc-400 opacity-0 group-hover:opacity-100 hover:text-black transition-all rounded-none"
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
              </div>
            ) : (
              <div className="flex flex-col w-full p-6 gap-8">
              {messages.map((msg, idx) => {
                const isTyping =
                  msg.role === "assistant" && !msg.content && isSending;
                
                if (msg.role === "user") {
                  return (
                    <div key={idx} className="flex flex-col items-end w-full animate-in fade-in">
                      <div className="w-full flex justify-end items-center gap-1">
                        {!isSending && editingMessageId !== msg.id && (
                          <button
                            onClick={() => setEditingMessageId(msg.id || null)}
                            className="p-1 text-zinc-300 hover:text-black transition-colors rounded-none"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                        <div className="max-w-[85%]">
                          {editingMessageId && editingMessageId === msg.id ? (
                            <div className="w-full min-w-[300px] md:min-w-[450px] bg-white border border-zinc-200 p-4 shadow-none">
                              <textarea
                                 defaultValue={msg.content}
                                className="w-full bg-zinc-50 text-black p-3 text-sm border border-zinc-200 focus:outline-none focus:border-black min-h-[100px] rounded-none transition-colors"
                                onKeyDown={(e: any) =>
                                  e.key === "Enter" &&
                                  !e.shiftKey &&
                                  (e.preventDefault(),
                                  handleSubmit(undefined, e.target.value))
                                }
                              />
                              <div className="flex justify-end gap-3 mt-3">
                                <button
                                  onClick={() => setEditingMessageId(null)}
                                  className="text-xs font-bold uppercase tracking-widest px-4 py-2 border border-zinc-200 hover:bg-zinc-50 transition-colors rounded-none text-black"
                                >
                                  Hủy bỏ
                                </button>
                                <button
                                  onClick={(ev) => {
                                    const ta =
                                      ev.currentTarget.parentElement?.parentElement?.querySelector(
                                        "textarea",
                                      ) as HTMLTextAreaElement;
                                    handleSubmit(undefined, ta.value);
                                  }}
                                  className="text-xs font-bold uppercase tracking-widest px-4 py-2 bg-black text-white hover:bg-zinc-800 transition-colors rounded-none"
                                >
                                  Gửi lại
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="bg-zinc-100 border border-zinc-200 px-5 py-4 rounded-none">
                              <p className="text-sm font-medium text-black whitespace-pre-wrap leading-relaxed">
                                {msg.content}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                }

                return (
                  <div key={idx} className="flex flex-col items-start w-full animate-in fade-in">
                    <div className="w-full max-w-[95%]">
                      {msg.thoughts && msg.thoughts.length > 0 && (
                        <details className="mb-4 border border-zinc-200 rounded-none group/thoughts bg-zinc-50/50">
                          <summary className="flex items-center gap-3 p-3 cursor-pointer text-xs font-bold uppercase tracking-widest text-zinc-500 group-hover/thoughts:text-black transition-colors list-none">
                            <Cpu className="w-3.5 h-3.5" />
                            <span>Quá trình phân tích dữ liệu AI</span>
                          </summary>
                          <div className="p-3 pt-0 flex flex-col gap-2">
                            <div className="h-px w-full bg-zinc-200 mb-1" />
                            {msg.thoughts.map((t, idx2) => (
                              <div
                                key={idx2}
                                className="text-sm text-zinc-600 flex items-center gap-3"
                              >
                                <div className="w-1.5 h-1.5 bg-zinc-300 shrink-0 rounded-none" />
                                <span>{t}</span>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                      
                      <div className="w-full prose prose-zinc max-w-none text-sm leading-relaxed">
                        {isTyping ? (
                          <div className="flex items-center gap-2 py-2">
                            <Loader2 className="w-4 h-4 animate-spin text-zinc-400" />
                          </div>
                        ) : (
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm, remarkMath]}
                            rehypePlugins={[rehypeKatex, rehypeHighlight]}
                            components={{
                              p: ({ children }) => (
                                <p className="mb-4 last:mb-0">
                                  {children}
                                </p>
                              ),
                              code({ node, inline, className, children, ...props }: any) {
                                const match = /language-(\w+)/.exec(className || "");
                                const content = String(children).replace(/\n$/, "");
                                if (!inline && match) {
                                  const lang = match[1];
                                  return (
                                    <div className="my-5 bg-black border border-black rounded-none overflow-hidden">
                                      <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800 bg-black">
                                        <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                                          {lang}
                                        </span>
                                        <button
                                          onClick={() => {
                                            navigator.clipboard.writeText(content);
                                            showToast("Đã sao chép", "info");
                                          }}
                                          className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 hover:text-white transition-colors rounded-none"
                                        >
                                          Sao chép
                                        </button>
                                      </div>
                                      <pre className="p-4 overflow-x-auto m-0">
                                        <code className="text-[13px] font-mono text-zinc-300 leading-relaxed">
                                          {content}
                                        </code>
                                      </pre>
                                    </div>
                                  );
                                }
                                return (
                                  <code
                                    className={`${className} bg-zinc-100 border border-zinc-200 px-1.5 py-0.5 text-black font-mono text-[13px] rounded-none`}
                                    {...props}
                                  >
                                    {children}
                                  </code>
                                );
                              },
                              table: ({ children }) => (
                                <div className="overflow-x-auto my-5 border border-zinc-200 rounded-none">
                                  <table className="min-w-full divide-y divide-zinc-200">
                                    {children}
                                  </table>
                                </div>
                              ),
                              th: ({ children }) => (
                                <th className="px-4 py-3 bg-zinc-50 text-left text-xs font-bold uppercase tracking-widest text-black border-b border-zinc-200">
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
                            {msg.content || ""}
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

          <div className="p-4 bg-white border-t border-zinc-200 shrink-0 relative flex justify-center">
            <div className="w-full max-w-3xl relative">
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
                        className="absolute -top-2 -right-2 w-6 h-6 bg-black text-white flex items-center justify-center transition-colors rounded-none"
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
                        className="absolute -top-2 -right-2 w-6 h-6 bg-black text-white flex items-center justify-center transition-colors rounded-none"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
              )}

              {showAttachments && (
                <div className="absolute bottom-full left-0 mb-4 bg-white border border-zinc-200 p-2 flex gap-2 animate-in fade-in slide-in-from-bottom-4 z-50 rounded-none shadow-none">
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
                    className="flex flex-col items-center gap-3 p-4 min-w-[90px] rounded-none hover:bg-zinc-50 transition-colors border border-transparent hover:border-zinc-200"
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
                    className="flex flex-col items-center gap-3 p-4 min-w-[90px] rounded-none hover:bg-zinc-50 transition-colors border border-transparent hover:border-zinc-200"
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
                      checked={usePro}
                      onChange={handleTogglePro}
                      className="sr-only peer"
                    />
                    <div className="w-8 h-4 bg-zinc-200 peer-focus:outline-none after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:h-3 after:w-3 after: peer-checked:after:translate-x-4 peer-checked:bg-black rounded-none transition-all"></div>
                  </div>
                  <span className="text-xs font-bold uppercase tracking-widest text-zinc-400 transition-colors group-hover:text-black">
                    Chuyên sâu
                  </span>
                </label>
                {usePro && (
                  <div className="flex items-center gap-1.5 px-2 py-1 bg-zinc-50 border border-zinc-200 rounded-none">
                    <span className="text-xs font-bold">
                      20 dl/tháng
                    </span>
                    <Coins className="w-3 h-3 text-black" />
                  </div>
                )}
              </div>

              <form onSubmit={handleSubmit} className="flex gap-3">
                <div className="flex-1 min-h-[56px] bg-white border border-zinc-200 flex items-center px-4 gap-3 focus-within:border-black rounded-none transition-colors">
                  <button
                    type="button"
                    onClick={handleAttach}
                    className="text-zinc-400 hover:text-black transition-colors shrink-0 rounded-none p-1"
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
                    (usePro && (user?.wallet_balance || 0) < 20)
                  }
                  className="w-14 shrink-0 bg-black text-white flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition-colors rounded-none"
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
