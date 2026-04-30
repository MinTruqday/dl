"use client";

import { API_URL, getToken } from "@/app/lib/api";
import { useState, useEffect, useRef } from "react";
import { MessageCircle, X, Send, Cpu, Zap, Coins, Paperclip, Image as ImageIcon, FileText, Loader2 } from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";
import { useToast } from "@/app/contexts/ToastContext";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";

export default function AiChatPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [usePro, setUsePro] = useState(false);
  const [messages, setMessages] = useState<{ role: string; content: string; thoughts?: string[] }[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [showAttachments, setShowAttachments] = useState(false);
  const { showToast } = useToast();

  const [selectedFile, setSelectedFile] = useState<{ name: string; data: string } | null>(null);
  const [selectedImage, setSelectedImage] = useState<{ name: string; data: string } | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  const { user } = useAuth() as any;

  useEffect(() => {
    if (isOpen && user?._id) {
      const historyKey = `doclib_chat_${user._id}`;
      const saved = localStorage.getItem(historyKey);
      if (saved) {
        try {
          setMessages(JSON.parse(saved));
        } catch (err) {
          console.error("Lỗi tải lịch sử chat:", err);
        }
      }
    }
  }, [isOpen, user?._id]);

  useEffect(() => {
    if (messages.length > 0 && user?._id) {
      const historyKey = `doclib_chat_${user._id}`;
      localStorage.setItem(historyKey, JSON.stringify(messages));
    }
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, user?._id]);

  if (!user) return null;

  const clearHistory = () => {
    const historyKey = `doclib_chat_${user._id}`;
    localStorage.removeItem(historyKey);
    setMessages([]);
    showToast("Đã xóa lịch sử trò chuyện", "info");
  };

  const handleAttach = () => {
    if (!usePro) {
      showToast("Vui lòng bật Chế độ chuyên nghiệp để phân tích tài liệu đính kèm", "info");
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

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>, type: "image" | "file") => {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;

    if (usePro && (user?.wallet_balance || 0) < 10) {
      showToast("Số dư không đủ để sử dụng Chế độ chuyên nghiệp (cần tối thiểu 10 dl)", "error");
      return;
    }

    const userMessage = input;
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    setIsSending(true);
    setShowAttachments(false);

    try {
      const token = getToken();
      setMessages((prev) => [...prev, { role: "assistant", content: "", thoughts: [] }]);

      const res = await fetch(`${API_URL}/rag/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          query: userMessage,
          usePro,
          conversation_history: messages.slice(-8),
          user_id: user?._id || "guest",
          image_data: selectedImage?.data,
          file_data: selectedFile?.data,
        }),
      });

      setSelectedFile(null);
      setSelectedImage(null);

      if (!res.ok) {
        let errorText = "Hệ thống hiện không phản hồi, vui lòng thử lại sau.";
        try {
          const errJson = await res.json();
          errorText = errJson.detail || errorText;
        } catch (err) {
          console.error("Lỗi phân tích lỗi phản hồi:", err);
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
      const nodeDescriptions: Record<string, string> = {
        router: "Đang xác định yêu cầu",
        retrieve_db: "Đang tìm kiếm thông tin",
        grade_documents: "Đang đối chiếu dữ liệu",
        retrieve_internet: "Đang tra cứu bổ sung",
        transform_query: "Đang tối ưu câu hỏi",
        generate: "Đang soạn câu trả lời",
        check_hallucination: "Đang xác thực thông tin",
        sql_agent: "Đang kiểm tra tài khoản",
        guest_router: "Đang khởi tạo kết nối",
        route_query: "Đang định tuyến yêu cầu",
        rag: "Đang xử lý tạo sinh tăng cường bằng truy xuất",
        chat: "Đang trò chuyện",
      };

      let isDone = false;
      while (!isDone) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunkStr = decoder.decode(value, { stream: true });

        const events = chunkStr.split("\n\n");
        for (const ev of events) {
          if (!ev.trim()) continue;
          const lines = ev.split("\n");
          let type = "";
          let data = "";
          for (const line of lines) {
            if (line.startsWith("event:")) type = line.replace("event:", "").trim();
            else if (line.startsWith("data:")) data = line.replace("data:", "").trim();
          }

          if (type === "status" && data) {
            try {
              const parsed = JSON.parse(data);
              const nodeVi = nodeDescriptions[parsed.node] || `Đang xử lý (${parsed.node})`;
              setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];
                if (lastMsg.role === "assistant") {
                  if (!lastMsg.thoughts?.includes(nodeVi)) {
                    lastMsg.thoughts = [...(lastMsg.thoughts || []), nodeVi];
                  }
                }
                return updated;
              });
            } catch (err) {
              console.error("Lỗi phân tích trạng thái xử lý:", err);
            }
          } else if (type === "message" && data) {
            try {
              const parsed = JSON.parse(data);
              fullText += parsed.chunk;
              setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];
                if (lastMsg.role === "assistant") {
                  lastMsg.content = fullText;
                }
                return updated;
              });
            } catch (err) {
              console.error("Lỗi phân tích nội dung phản hồi:", err);
            }
          } else if (type === "done" || data === "[DONE]") {
            isDone = true;
          } else if (type === "error" && data) {
            setMessages((prev) => {
              const updated = [...prev];
              const lastMsg = updated[updated.length - 1];
              if (lastMsg.role === "assistant") {
                lastMsg.content = "Đã xảy ra lỗi khi xử lý dữ liệu.";
              }
              return updated;
            });
          }
        }
      }
    } catch (e) {
      setMessages((prev) => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (lastMsg.role === "assistant" && !lastMsg.content) {
          lastMsg.content = "Kết nối bị gián đoạn, vui lòng kiểm tra mạng.";
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
        className={`
          fixed bottom-6 right-6 z-[100]
          w-14 h-14 border border-zinc-200
          flex items-center justify-center
          transition-all duration-300 active:scale-90
          ${isOpen ? "bg-black text-white hover:bg-zinc-800" : "bg-white text-black hover:bg-zinc-50"}
        `}
        title="Trợ lý AI"
      >
        {isOpen ? <X className="w-6 h-6" /> : <MessageCircle className="w-6 h-6" />}
      </button>

      {isOpen && (
        <div className="fixed bottom-24 right-6 z-[100] w-[450px] h-[700px] bg-white border border-zinc-200 flex flex-col overflow-hidden animate-in slide-in-from-bottom-8 fade-in duration-300 shadow-2xl">

          <div className="px-5 py-5 border-b border-zinc-100 flex items-center justify-between shrink-0 bg-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-black flex items-center justify-center border border-black">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-black tracking-tight">DocLib AI</h3>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-pulse" />
                  <p className="text-[11px] text-zinc-400 font-bold">Trợ lý tri thức</p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={clearHistory}
                className="text-[11px] text-zinc-400 hover:text-black font-bold transition-colors"
              >
                Xóa lịch sử
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-zinc-400 hover:text-black transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 min-h-0 bg-zinc-50/20 scrollbar-thin scrollbar-thumb-zinc-200"
          >
            {messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center px-4">
                <div className="w-16 h-16 bg-white border border-zinc-200 flex items-center justify-center mb-6">
                  <Cpu className="w-8 h-8 text-black" />
                </div>
                <p className="text-sm font-bold text-black tracking-tight">Xin chào, {user.full_name}</p>
                <p className="text-[12px] text-zinc-400 mt-3 leading-relaxed max-w-[240px] font-medium">
                  Tôi có thể giúp bạn phân tích tài liệu, tìm kiếm kiến thức hoặc giải đáp các thắc mắc chuyên sâu.
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`max-w-[98%] text-sm leading-relaxed animate-in fade-in duration-300 flex flex-col ${
                    msg.role === "user" ? "self-end items-end" : "self-start items-start w-full"
                  }`}
                >
                  <div
                    className={`px-5 py-4 border ${
                      msg.role === "user"
                        ? "bg-black text-white border-black"
                        : "bg-white border-zinc-100 text-black w-full"
                    }`}
                  >
                    {msg.role === "assistant" && usePro && msg.thoughts && msg.thoughts.length > 0 && (
                      <details className="mb-4 border-b border-zinc-100 pb-4 cursor-pointer">
                        <summary className="flex items-center gap-2 text-[11px] font-bold text-zinc-400 hover:text-black transition-colors list-none">
                          <Cpu className="w-3.5 h-3.5" />
                          <span>Quá trình xử lý tri thức</span>
                        </summary>
                        <div className="mt-4 flex flex-col gap-3 pl-2 border-l border-zinc-100 ml-1.5">
                          {msg.thoughts.map((t, idx2) => (
                            <div key={idx2} className="text-[12px] text-zinc-500 flex items-center gap-3">
                              <div className="w-1 h-1 bg-zinc-300 shrink-0" />
                              <span className="font-medium">{t}</span>
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                    <div className="w-full prose prose-sm max-w-none dark:prose-invert">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex, rehypeHighlight]}
                        components={{
                          p: ({ children }) => <p className="mb-4 last:mb-0 font-medium leading-relaxed">{children}</p>,
                          code({ node, inline, className, children, ...props }: any) {
                            const match = /language-(\w+)/.exec(className || "");
                            const content = String(children).replace(/\n$/, "");
                            
                            if (!inline && match) {
                              const lang = match[1];
                              const handleDownload = () => {
                                const blob = new Blob([content], { type: "text/plain" });
                                const url = URL.createObjectURL(blob);
                                const a = document.createElement("a");
                                a.href = url;
                                a.download = `doclib_${Date.now()}.${lang}`;
                                a.click();
                                URL.revokeObjectURL(url);
                              };

                              return (
                                <button
                                  onClick={handleDownload}
                                  className="my-3 flex items-center gap-2 text-blue-600 hover:text-blue-800 font-bold underline transition-colors cursor-pointer group"
                                  title="Nhấp để tải xuống"
                                >
                                  <FileText className="w-4 h-4 group-hover:scale-110 transition-transform" />
                                  <span>doclib_output.{lang}</span>
                                </button>
                              );
                            }
                            return (
                              <code className={`${className} bg-zinc-100 px-1 py-0.5 rounded text-black font-mono text-[13px]`} {...props}>
                                {children}
                              </code>
                            );
                          },
                          table: ({ children }) => (
                            <div className="overflow-x-auto my-4 border border-zinc-100">
                              <table className="min-w-full divide-y divide-zinc-200">{children}</table>
                            </div>
                          ),
                          th: ({ children }) => <th className="px-3 py-2 bg-zinc-50 text-left text-[11px] font-bold text-black uppercase tracking-wider">{children}</th>,
                          td: ({ children }) => <td className="px-3 py-2 whitespace-nowrap text-zinc-600 border-t border-zinc-100">{children}</td>,
                        }}
                      >
                        {msg.content || (msg.role === "assistant" ? "..." : "")}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="p-5 bg-white border-t border-zinc-100 shrink-0 relative">
            {(selectedFile || selectedImage) && (
              <div className="flex gap-3 mb-4 overflow-x-auto pb-1 scrollbar-none">
                {selectedImage && (
                  <div className="relative group shrink-0">
                    <img src={selectedImage.data} alt="" className="h-14 w-14 object-cover border border-zinc-200" />
                    <button
                      onClick={() => setSelectedImage(null)}
                      className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-black text-white flex items-center justify-center hover:bg-zinc-800 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                )}
                {selectedFile && (
                  <div className="relative group shrink-0 h-14 px-4 bg-zinc-50 border border-zinc-200 flex items-center gap-3">
                    <FileText className="w-4 h-4 text-black shrink-0" />
                    <span className="text-[12px] font-bold text-zinc-600 truncate max-w-[120px]">
                      {selectedFile.name}
                    </span>
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-black text-white flex items-center justify-center hover:bg-zinc-800 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>
            )}

            {showAttachments && (
              <div className="absolute bottom-full left-4 mb-4 bg-white border border-zinc-200 p-2 flex gap-2 animate-in fade-in slide-in-from-bottom-4 duration-300 z-50 shadow-xl">
                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  accept=".txt,.md,.json,.pdf"
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
                  className="flex flex-col items-center gap-2 p-4 hover:bg-zinc-50 transition-all min-w-[80px]"
                >
                  <div className="w-12 h-12 border border-zinc-200 flex items-center justify-center">
                    <FileText className="w-6 h-6 text-black" />
                  </div>
                  <span className="text-[11px] font-bold text-black">Tài liệu</span>
                </button>
                <button
                  onClick={() => imageInputRef.current?.click()}
                  className="flex flex-col items-center gap-2 p-4 hover:bg-zinc-50 transition-all min-w-[80px]"
                >
                  <div className="w-12 h-12 border border-zinc-200 flex items-center justify-center">
                    <ImageIcon className="w-6 h-6 text-black" />
                  </div>
                  <span className="text-[11px] font-bold text-black">Hình ảnh</span>
                </button>
              </div>
            )}

            <div className="flex items-center justify-between mb-4 px-1">
              <label className="flex items-center gap-3 cursor-pointer group">
                <div className="relative inline-flex items-center">
                  <input type="checkbox" checked={usePro} onChange={handleTogglePro} className="sr-only peer" />
                  <div className="w-9 h-5 bg-zinc-200 peer-focus:outline-none after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-full peer-checked:bg-black"></div>
                </div>
                <span className="text-[11px] font-bold text-zinc-400 group-hover:text-black transition-colors">
                  Chế độ chuyên nghiệp
                </span>
              </label>
              {usePro && (
                <div className="flex items-center gap-1.5 px-3 py-1 bg-zinc-50 border border-zinc-100">
                  <span className="text-[11px] font-bold text-black">10 dl</span>
                  <Coins className="w-3 h-3 text-black" />
                </div>
              )}
            </div>

            <form onSubmit={handleSubmit} className="flex gap-2">
              <div className="flex-1 h-14 bg-zinc-50 border border-zinc-200 flex items-center px-4 gap-3 focus-within:border-black focus-within:bg-white transition-all">
                <button
                  type="button"
                  onClick={handleAttach}
                  className="text-zinc-400 hover:text-black transition-colors shrink-0"
                >
                  <Paperclip className="w-5 h-5" />
                </button>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Nhập câu hỏi..."
                  disabled={isSending}
                  className="flex-1 h-full text-sm bg-transparent outline-none font-medium"
                />
              </div>
              <button
                type="submit"
                disabled={isSending || !input.trim() || (usePro && (user?.wallet_balance || 0) < 10)}
                className="w-14 h-14 bg-black text-white flex items-center justify-center hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-95"
              >
                {isSending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
