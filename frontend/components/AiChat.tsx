"use client";

import { streamAiChatAPI } from "@/services/ai.service";
import { getToken, API_URL } from "@/services/auth.service";
import { useState, useEffect, useRef } from "react";
import {
  MessageSquare,
  X,
  Send,
  Cpu,
  Zap,
  Coins,
  Paperclip,
  Image as ImageIcon,
  FileText,
  Loader2,
  History as HistoryIcon,
  Edit2,
  Trash2,
  Terminal
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
  contextualize_question: "Phân tích bối cảnh hội thoại",
  route_question: "Xác định ý định yêu cầu",
  route_query: "Định tuyến chuyên gia",
  retrieve_db: "Truy xuất kho tri thức",
  retrieve_internet: "Tìm kiếm thông tin",
  grade_documents: "Thẩm định độ tin cậy",
  transform_query: "Tinh chỉnh chiến lược",
  generate: "Tổng hợp câu trả lời",
  generate_direct: "Phản hồi trực tiếp",
  grade_generation: "Kiểm tra tính xác thực",
  billing: "Kết nối hệ thống tài chính",
  workspace: "Truy cập quản lý thư viện",
  multi: "Tổng hợp dữ liệu đa nguồn",
  rag: "Thực hiện quy trình RAG chuyên sâu",
  chat: "Trò chuyện trực tiếp",
};

export default function AiChat() {
  const [isOpen, setIsOpen] = useState(false);
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

  const [selectedFile, setSelectedFile] = useState<{ name: string; data: string; } | null>(null);
  const [selectedImage, setSelectedImage] = useState<{ name: string; data: string; } | null>(null);

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

  if (!user) return null;

  const handleAttach = () => {
    if (!usePro) {
      showToast("Vui lòng bật chế độ chuyên nghiệp để phân tích tài liệu đính kèm", "info");
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

  const handleSubmit = async (e?: React.FormEvent, retryText?: string) => {
    if (e) e.preventDefault();
    const userMessage = retryText || input.trim();
    if (!userMessage || isSending) return;

    if (usePro && (user?.wallet_balance || 0) < 10) {
      showToast("Số dư không đủ để sử dụng chế độ chuyên nghiệp", "error");
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
          console.error("Lỗi phân tích phản hồi", e);
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
              const nodeVi = nodeDescriptions[parsed.node] || `Xử lý: ${parsed.node}`;
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
              console.error("Lỗi phân tích dữ liệu trạng thái", e);
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
              console.error("Lỗi phân tích dữ liệu tin nhắn", e);
            }
          } else if (type === "done" || data === "[DONE]") {
            isDone = true;
          } else if (type === "error" && data) {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1].content = "Đã xảy ra lỗi khi xử lý dữ liệu";
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
              console.error("Lỗi phân tích dữ liệu thô", e);
            }
          }
        }
      }
    } catch (err) {
      console.error("Lỗi gửi tin nhắn", err);
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
        className={`fixed bottom-8 right-8 z-[100] w-12 h-12 border border-black flex items-center justify-center transition-colors rounded-none ${isOpen ? "bg-black text-white" : "bg-white text-black hover:bg-gray-100"}`}
      >
        {isOpen ? <X className="w-5 h-5" /> : <Terminal className="w-5 h-5" />}
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-[150] bg-white flex flex-col animate-in fade-in duration-300">
          <header className="h-16 border-b border-black flex items-center justify-between px-8 bg-white shrink-0">
            <div className="flex items-center gap-4">
              <Terminal className="w-5 h-5 text-black" />
              <div>
                <h2 className="text-sm font-bold uppercase tracking-widest text-black">Thiết bị đầu cuối AI</h2>
                <div className="flex items-center gap-2 mt-1">
                   <div className="w-1.5 h-1.5 bg-black rounded-none animate-pulse" />
                   <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Trực tuyến</p>
                </div>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-[10px] font-bold uppercase tracking-widest text-black hover:underline">
              Đóng phiên
            </button>
          </header>

          <div className="flex flex-1 overflow-hidden">
            {view === "history" && (
              <aside className="w-80 border-r border-black bg-white flex flex-col shrink-0">
                <div className="p-6 border-b border-black flex justify-between items-center">
                  <h3 className="text-xs font-bold uppercase tracking-widest text-black">Lịch sử phiên</h3>
                  <button onClick={() => setView("chat")} className="text-[10px] font-bold uppercase tracking-widest text-gray-500 hover:text-black">Đóng</button>
                </div>
                <div className="flex-1 overflow-y-auto">
                  {sessions.length === 0 ? (
                    <div className="p-10 text-center opacity-50">
                       <p className="text-[10px] font-bold uppercase tracking-widest text-black">Không có dữ liệu</p>
                    </div>
                  ) : (
                    sessions.map((s) => (
                      <div key={s._id} className={`border-b border-black group relative ${currentSessionId === s._id ? "bg-black text-white" : "bg-white text-black hover:bg-gray-50"}`}>
                        <div
                          className="p-6 cursor-pointer"
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
                          <p className="text-xs font-bold uppercase tracking-tight pr-8 line-clamp-2">{s.title}</p>
                          <p className={`text-[10px] font-bold mt-2 uppercase tracking-widest ${currentSessionId === s._id ? "text-gray-300" : "text-gray-500"}`}>
                            {new Date(s.updated_at).toLocaleDateString("vi-VN")}
                          </p>
                        </div>
                        <button
                          onClick={async (e) => {
                            e.stopPropagation();
                            try {
                              const token = getToken();
                              const res = await fetch(`${API_URL}/ai/history/${s._id}`, {
                                method: "DELETE",
                                headers: { Authorization: `Bearer ${token}` },
                              });
                              if (res.ok) {
                                if (currentSessionId === s._id) {
                                  setCurrentSessionId(null);
                                  setMessages([]);
                                }
                                fetchHistory();
                              }
                            } catch (err) {
                              console.error("Lỗi xóa phiên", err);
                            }
                          }}
                          className={`absolute top-6 right-6 p-2 rounded-none opacity-0 group-hover:opacity-100 transition-opacity ${currentSessionId === s._id ? "text-white hover:bg-gray-800" : "text-black hover:bg-gray-200"}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </aside>
            )}

            <main className="flex-1 flex flex-col relative bg-white overflow-hidden">
              <div className="h-12 border-b border-black flex items-center justify-between px-8 bg-gray-50 shrink-0">
                <button onClick={() => setView(view === "history" ? "chat" : "history")} className="flex items-center gap-2 text-[10px] font-bold text-black uppercase tracking-widest hover:underline">
                  <HistoryIcon className="w-3.5 h-3.5" />
                  {view === "history" ? "Ẩn lịch sử" : "Xem lịch sử"}
                </button>
                <label className="flex items-center gap-3 cursor-pointer">
                  <span className="text-[10px] font-bold text-black uppercase tracking-widest">Chuyên nghiệp</span>
                  <div className="relative inline-flex items-center">
                    <input type="checkbox" checked={usePro} onChange={handleTogglePro} className="sr-only peer" />
                    <div className="w-8 h-4 border border-black bg-white peer-checked:bg-black after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-black peer-checked:after:bg-white after:border after:border-black after:h-3 after:w-3 after:transition-all peer-checked:after:translate-x-4 rounded-none"></div>
                  </div>
                  {usePro && (
                    <div className="flex items-center gap-1.5 px-2 py-0.5 border border-black bg-white">
                      <span className="text-[10px] font-bold text-black">{user?.wallet_balance || 0}</span>
                      <Coins className="w-3 h-3 text-black" />
                    </div>
                  )}
                </label>
              </div>

              <div ref={scrollRef} className="flex-1 overflow-y-auto">
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center min-h-full p-8 text-center">
                    <Terminal className="w-12 h-12 text-black mb-6 stroke-[1]" />
                    <p className="text-sm font-bold text-black uppercase tracking-widest">Hệ thống sẵn sàng</p>
                    <p className="text-xs text-gray-500 mt-2 max-w-md font-medium uppercase tracking-widest">Nhập truy vấn để bắt đầu phân tích dữ liệu</p>
                  </div>
                ) : (
                  <div className="flex flex-col">
                    {messages.map((msg, idx) => {
                      const isTyping = msg.role === "assistant" && !msg.content && isSending;
                      return (
                        <div key={idx} className={`w-full border-b border-black ${msg.role === "user" ? "bg-white" : "bg-gray-50"}`}>
                          <div className="max-w-4xl mx-auto px-8 py-10 flex gap-8">
                            <div className="w-24 shrink-0">
                               <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                                 {msg.role === "user" ? "Người dùng" : "Trợ lý AI"}
                               </span>
                            </div>
                            <div className="flex-1 min-w-0">
                               {msg.role === "user" && !isSending && (
                                 <button onClick={() => setEditingMessageId(msg.id || null)} className="float-right text-[10px] font-bold uppercase tracking-widest text-gray-400 hover:text-black">Sửa</button>
                               )}
                               {editingMessageId && editingMessageId === msg.id ? (
                                  <div className="flex flex-col gap-4">
                                     <textarea
                                       defaultValue={msg.content}
                                       className="w-full bg-white text-black p-4 text-sm font-medium border border-black focus:outline-none min-h-[100px] resize-none rounded-none"
                                       onKeyDown={(e: any) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleSubmit(undefined, e.target.value))}
                                     />
                                     <div className="flex justify-end gap-4">
                                       <button onClick={() => setEditingMessageId(null)} className="text-[10px] font-bold uppercase tracking-widest text-gray-500 hover:text-black">Hủy</button>
                                       <button onClick={(ev) => { const ta = ev.currentTarget.parentElement?.parentElement?.querySelector("textarea") as HTMLTextAreaElement; handleSubmit(undefined, ta.value); }} className="px-6 py-2 bg-black text-white text-[10px] font-bold uppercase tracking-widest">Cập nhật</button>
                                     </div>
                                  </div>
                               ) : (
                                  <>
                                    {msg.role === "assistant" && msg.thoughts && msg.thoughts.length > 0 && (
                                       <div className="mb-6 pb-6 border-b border-gray-200">
                                          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-4 flex items-center gap-2"><Cpu className="w-3.5 h-3.5" /> Luồng thực thi</p>
                                          <div className="flex flex-col gap-2">
                                             {msg.thoughts.map((t, idx2) => (
                                                <div key={idx2} className="text-xs text-gray-600 font-medium flex items-center gap-3">
                                                   <span className="w-1.5 h-1.5 bg-black rounded-none shrink-0" />
                                                   <span className="uppercase tracking-widest text-[10px]">{t}</span>
                                                </div>
                                             ))}
                                          </div>
                                       </div>
                                    )}
                                    <div className="prose prose-sm prose-zinc max-w-none prose-p:leading-relaxed prose-pre:bg-gray-100 prose-pre:border prose-pre:border-black prose-pre:rounded-none">
                                       {isTyping ? (
                                          <div className="flex items-center gap-2 py-2">
                                            <div className="w-2 h-2 bg-black rounded-none animate-pulse" />
                                            <div className="w-2 h-2 bg-black rounded-none animate-pulse delay-75" />
                                            <div className="w-2 h-2 bg-black rounded-none animate-pulse delay-150" />
                                          </div>
                                       ) : (
                                          <ReactMarkdown
                                            remarkPlugins={[remarkGfm, remarkMath]}
                                            rehypePlugins={[rehypeKatex, rehypeHighlight]}
                                            components={{
                                              p: ({ children }) => <p className={`mb-4 last:mb-0 ${msg.role === "user" ? "text-base font-medium text-black" : "text-sm text-gray-800"}`}>{children}</p>,
                                              code({ inline, className, children, ...props }: any) {
                                                const match = /language-(\w+)/.exec(className || "");
                                                const content = String(children).replace(/\n$/, "");
                                                if (!inline && match) {
                                                  return (
                                                    <div className="my-6 border border-black bg-gray-50 rounded-none">
                                                      <div className="flex items-center justify-between px-4 py-2 border-b border-black bg-white">
                                                        <span className="text-[10px] font-bold uppercase tracking-widest text-black">{match[1]}</span>
                                                        <button onClick={() => { navigator.clipboard.writeText(content); showToast("Đã sao chép", "info"); }} className="text-[10px] font-bold uppercase tracking-widest text-gray-500 hover:text-black">Sao chép</button>
                                                      </div>
                                                      <pre className="p-4 overflow-x-auto"><code className="text-xs font-mono text-black">{content}</code></pre>
                                                    </div>
                                                  );
                                                }
                                                return <code className="bg-gray-200 px-1.5 py-0.5 text-black font-mono text-xs rounded-none" {...props}>{children}</code>;
                                              },
                                              table: ({ children }) => <div className="overflow-x-auto my-6 border border-black"><table className="min-w-full divide-y divide-black">{children}</table></div>,
                                              th: ({ children }) => <th className="px-4 py-3 bg-white text-left text-[10px] font-bold uppercase tracking-widest text-black">{children}</th>,
                                              td: ({ children }) => <td className="px-4 py-3 whitespace-nowrap text-sm text-black border-t border-black bg-gray-50">{children}</td>,
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
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="border-t border-black bg-white p-6 shrink-0 relative">
                <div className="max-w-4xl mx-auto">
                  {(selectedFile || selectedImage) && (
                    <div className="flex gap-4 mb-4">
                      {selectedImage && (
                        <div className="relative border border-black p-1 bg-white">
                          <img src={selectedImage.data} alt="" className="h-16 w-16 object-cover grayscale" />
                          <button onClick={() => setSelectedImage(null)} className="absolute -top-2 -right-2 bg-black text-white w-5 h-5 flex items-center justify-center rounded-none"><X className="w-3 h-3" /></button>
                        </div>
                      )}
                      {selectedFile && (
                        <div className="relative border border-black h-18 px-4 flex items-center gap-4 bg-gray-50">
                          <FileText className="w-5 h-5 text-black" />
                          <span className="text-xs font-bold uppercase tracking-widest max-w-[150px] truncate text-black">{selectedFile.name}</span>
                          <button onClick={() => setSelectedFile(null)} className="absolute -top-2 -right-2 bg-black text-white w-5 h-5 flex items-center justify-center rounded-none"><X className="w-3 h-3" /></button>
                        </div>
                      )}
                    </div>
                  )}

                  {showAttachments && (
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 bg-white border border-black p-4 flex gap-4 z-50 shadow-[4px_4px_0_0_#000]">
                      <input type="file" ref={fileInputRef} className="hidden" accept=".txt,.md,.json,.pdf,.docx,.doc,.xlsx,.xls,.pptx,.epub,.mobi,.zip,.csv" onChange={(e) => handleFileUpload(e, "file")} />
                      <input type="file" ref={imageInputRef} className="hidden" accept="image/*" onChange={(e) => handleFileUpload(e, "image")} />
                      <button onClick={() => fileInputRef.current?.click()} className="flex flex-col items-center gap-3 p-4 border border-black hover:bg-gray-50">
                        <FileText className="w-6 h-6 text-black" />
                        <span className="text-[10px] font-bold uppercase tracking-widest text-black">Tài liệu</span>
                      </button>
                      <button onClick={() => imageInputRef.current?.click()} className="flex flex-col items-center gap-3 p-4 border border-black hover:bg-gray-50">
                        <ImageIcon className="w-6 h-6 text-black" />
                        <span className="text-[10px] font-bold uppercase tracking-widest text-black">Hình ảnh</span>
                      </button>
                    </div>
                  )}

                  <form onSubmit={handleSubmit} className="relative flex items-end border border-black bg-white focus-within:ring-1 focus-within:ring-black">
                    <button type="button" onClick={handleAttach} className="p-4 text-black hover:bg-gray-100 shrink-0 border-r border-black">
                      <Paperclip className="w-5 h-5" />
                    </button>
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder="NHẬP TRUY VẤN CỦA BẠN..."
                      className="flex-1 max-h-48 min-h-[56px] p-4 text-sm font-bold bg-transparent resize-none focus:outline-none placeholder:text-gray-400 placeholder:uppercase placeholder:tracking-widest"
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          handleSubmit();
                        }
                      }}
                    />
                    <button type="submit" disabled={!input.trim() || isSending} className="p-4 bg-black text-white disabled:bg-gray-300 disabled:text-gray-500 shrink-0">
                      {isSending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                    </button>
                  </form>
                  <p className="text-[9px] font-bold text-center mt-3 text-gray-400 uppercase tracking-widest">
                    AI có thể cung cấp thông tin không chính xác. Vui lòng xác minh dữ liệu.
                  </p>
                </div>
              </div>
            </main>
          </div>
        </div>
      )}
    </div>
  );
}
