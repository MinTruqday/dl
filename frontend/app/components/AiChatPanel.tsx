"use client";
import { API_URL } from "@/app/lib/api";
import { useState, useEffect, useRef } from "react";
import { MessageCircle, X, Send, Cpu, Zap, Coins, Paperclip, Image as ImageIcon, FileText } from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";

export default function AiChatPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [usePro, setUsePro] = useState(false);
  const [messages, setMessages] = useState<{ role: string; content: string; thoughts?: string[] }[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [showAttachments, setShowAttachments] = useState(false);
  
  const [selectedFile, setSelectedFile] = useState<{name: string, data: string} | null>(null);
  const [selectedImage, setSelectedImage] = useState<{name: string, data: string} | null>(null);
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  
  const { user } = useAuth() as any;
  if (!user) return null;

  useEffect(() => {
    if (isOpen) {
      const historyKey = `doclib_chat_${user._id}`;
      const saved = localStorage.getItem(historyKey);
      if (saved) {
        try {
          setMessages(JSON.parse(saved));
        } catch (e) {}
      }
    }
  }, [isOpen, user]);

  useEffect(() => {
    if (messages.length > 0) {
      const historyKey = `doclib_chat_${user._id}`;
      localStorage.setItem(historyKey, JSON.stringify(messages));
    }
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, user]);

  const clearHistory = () => {
    const historyKey = `doclib_chat_${user._id}`;
    localStorage.removeItem(historyKey);
    setMessages([]);
  };

  const handleAttach = () => {
    if (!user) {
        alert("Vui lòng đăng nhập để đính kèm tài liệu và hình ảnh!");
        return;
    }
    if (!usePro) {
        alert("Vui lòng bật Tìm kiếm Pro để phân tích tài liệu đính kèm!");
        return;
    }
    setShowAttachments(!showAttachments);
  };
  
  const handleTogglePro = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!user && e.target.checked) {
        alert("Vui lòng đăng nhập để sử dụng tính năng AI Pro!");
        return;
    }
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
            if (type === "image") setSelectedImage({name: file.name, data});
            if (type === "file") setSelectedFile({name: file.name, data});
            setShowAttachments(false);
        }
    };
    reader.readAsDataURL(file);
    e.target.value = "";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;

    const userMessage = input;
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    setIsSending(true);
    setShowAttachments(false);

    try {
      const token = typeof window !== "undefined"
          ? localStorage.getItem("doclib_token") || localStorage.getItem("token")
          : null;
          
      setMessages((prev) => [...prev, { role: "assistant", content: "", thoughts: [] }]);
      
      const res = await fetch(`${API_URL}/api/rag/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            query: userMessage,
            usePro,
            conversation_history: messages.slice(-8),
            user_id: user ? user._id : "guest",
            image_data: selectedImage?.data,
            file_data: selectedFile?.data
          }),
      });
      
      setSelectedFile(null);
      setSelectedImage(null);
      
      if (!res.ok) {
         let errorText = "Hệ thống AI hiện không phản hồi, vui lòng thử lại sau.";
         try {
             const errJson = await res.json();
             errorText = errJson.detail || errorText;
         } catch(e) {}
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
          "router": "Đang xác định yêu cầu",
          "retrieve_db": "Đang tìm kiếm thông tin",
          "grade_documents": "Đang đối chiếu dữ liệu",
          "retrieve_internet": "Đang tra cứu bổ sung",
          "transform_query": "Đang tối ưu câu hỏi",
          "generate": "Đang soạn câu trả lời",
          "check_hallucination": "Đang xác thực thông tin",
          "sql_agent": "Đang kiểm tra tài khoản",
          "guest_router": "Đang khởi tạo kết nối",
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
                             lastMsg.thoughts = [...(lastMsg.thoughts || []), nodeVi];
                         }
                         return updated;
                      });
                  } catch(e) {}
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
                  } catch(e) {}
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
    <>
      <button
        onClick={() => setIsOpen((v) => !v)}
        className={`
          fixed bottom-6 right-6 z-[100]
          w-12 h-12 rounded-md
          flex items-center justify-center
          transition-all duration-300 shadow-xl
          ${isOpen
            ? "bg-black text-white hover:bg-zinc-800"
            : "bg-white text-black hover:bg-zinc-50 border border-zinc-200"
          }
        `}
        title="Trợ lý AI"
      >
        {isOpen ? (
          <X className="w-5 h-5 transition-transform duration-300 rotate-0" />
        ) : (
          <MessageCircle className="w-5 h-5 transition-transform duration-300 scale-100" />
        )}
      </button>

      {isOpen && (
        <div className="fixed bottom-24 right-6 z-[100] w-[380px] h-[550px] bg-white rounded-md shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-zinc-200 flex flex-col overflow-hidden animate-in slide-in-from-bottom-8 fade-in duration-300">
          <div className="px-5 py-4 border-b border-zinc-200 flex items-center justify-between shrink-0 bg-white/80 backdrop-blur-md">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-md bg-black flex items-center justify-center shadow-md">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-black tracking-tight">DocLib AI</h3>
                <p className="text-[10px] text-zinc-500 font-medium">Trợ lý tri thức</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={clearHistory} className="text-[10px] text-zinc-400 hover:text-black font-bold mr-2 transition-colors">Xóa</button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-md text-zinc-400 hover:text-black hover:bg-zinc-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto p-5 flex flex-col gap-5 min-h-0 bg-zinc-50/50">
            {messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center px-4">
                <div className="w-14 h-14 rounded-md bg-white shadow-sm border border-zinc-200 flex items-center justify-center mb-5">
                  <Zap className="w-6 h-6 text-black" />
                </div>
                <p className="text-sm font-black text-black tracking-tight">Xin chào{user ? `, ${user.full_name}` : ''}</p>
                <p className="text-xs text-zinc-500 mt-2 leading-relaxed max-w-[240px]">
                  Tôi có thể giúp bạn phân tích tài liệu, tìm kiếm kiến thức hoặc giải đáp các thắc mắc.
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`max-w-[88%] text-sm leading-relaxed animate-in fade-in duration-300 flex flex-col ${
                    msg.role === "user"
                      ? "self-end items-end"
                      : "self-start items-start w-full"
                  }`}
                >
                  <div className={`px-4 py-3 rounded-md ${
                    msg.role === "user" 
                      ? "bg-black text-white rounded-br-none shadow-sm" 
                      : "bg-white border border-zinc-200 text-black rounded-bl-none shadow-sm w-fit max-w-full"
                  }`}>
                    {msg.role === "assistant" && user && usePro && msg.thoughts && msg.thoughts.length > 0 && (
                      <details className="mb-3 group border-b border-zinc-200 pb-3 cursor-pointer overflow-hidden [&_summary::-webkit-details-marker]:hidden bg-zinc-50/50 rounded-md px-3 mt-1">
                         <summary className="flex items-center gap-2 text-[10px] font-bold text-zinc-500 hover:text-black transition-colors list-none select-none py-2">
                             <Cpu className="w-3.5 h-3.5" />
                             Quá trình xử lý
                         </summary>
                         <div className="pb-2">
                           <ul className="flex flex-col gap-2.5 border-l-2 border-zinc-300 pl-3 ml-1.5 mt-1">
                             {msg.thoughts.map((t, idx2) => (
                               <li key={idx2} className="text-[11px] text-zinc-600 flex items-center gap-2">
                                 <div className="w-1.5 h-1.5 bg-zinc-400 shrink-0" />
                                 <span className="leading-none font-medium">{t}</span>
                               </li>
                             ))}
                           </ul>
                         </div>
                      </details>
                    )}
                    <div className="whitespace-pre-wrap">
                      {msg.content ? (
                        msg.content
                      ) : msg.role === "assistant" ? (
                        <span className="flex gap-1.5 items-center h-5">
                          <span className="w-1.5 h-1.5 bg-zinc-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                          <span className="w-1.5 h-1.5 bg-zinc-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                          <span className="w-1.5 h-1.5 bg-zinc-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                        </span>
                      ) : (
                        ""
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="p-4 bg-white border-t border-zinc-200 shrink-0 relative">
            {(selectedFile || selectedImage) && (
              <div className="flex gap-2 mb-2 overflow-x-auto pb-1 hide-scrollbar">
                {selectedImage && (
                  <div className="relative group shrink-0">
                    <img src={selectedImage.data} alt="Attached" className="h-12 w-12 object-cover rounded-md border border-zinc-200" />
                    <button onClick={() => setSelectedImage(null)} className="absolute -top-1 -right-1 w-4 h-4 bg-black text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"><X className="w-2.5 h-2.5" /></button>
                  </div>
                )}
                {selectedFile && (
                  <div className="relative group shrink-0 h-12 w-28 bg-zinc-50 border border-zinc-200 rounded-md flex items-center px-2 gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-black shrink-0" />
                    <span className="text-[9px] font-medium text-zinc-600 truncate leading-tight">{selectedFile.name}</span>
                    <button onClick={() => setSelectedFile(null)} className="absolute -top-1 -right-1 w-4 h-4 bg-black text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"><X className="w-2.5 h-2.5" /></button>
                  </div>
                )}
              </div>
            )}
            
            {showAttachments && user && (
               <div className="absolute bottom-full left-4 mb-2 bg-white border border-zinc-200 shadow-xl rounded-md p-2 flex gap-2 animate-in fade-in slide-in-from-bottom-2 duration-200 z-10">
                 <input type="file" ref={fileInputRef} className="hidden" accept=".txt,.md,.json,.pdf" onChange={(e) => handleFileUpload(e, "file")} />
                 <input type="file" ref={imageInputRef} className="hidden" accept="image/*" onChange={(e) => handleFileUpload(e, "image")} />
                 
                 <button onClick={() => fileInputRef.current?.click()} type="button" className="flex flex-col items-center gap-1.5 p-3 hover:bg-zinc-100 rounded-md transition-colors min-w-[70px]">
                   <div className="w-10 h-10 bg-zinc-100 text-black flex items-center justify-center"><FileText className="w-5 h-5" /></div>
                   <span className="text-[9px] font-bold text-black">Tài liệu</span>
                 </button>
                 <button onClick={() => imageInputRef.current?.click()} type="button" className="flex flex-col items-center gap-1.5 p-3 hover:bg-zinc-100 rounded-md transition-colors min-w-[70px]">
                   <div className="w-10 h-10 bg-zinc-100 text-black flex items-center justify-center"><ImageIcon className="w-5 h-5" /></div>
                   <span className="text-[9px] font-bold text-black">Hình ảnh</span>
                 </button>
                 <button type="button" className="flex flex-col items-center gap-1.5 p-3 hover:bg-zinc-100 rounded-md transition-colors min-w-[70px] opacity-50 cursor-not-allowed">
                   <div className="w-10 h-10 bg-zinc-100 text-black flex items-center justify-center"><Cpu className="w-5 h-5" /></div>
                   <span className="text-[9px] font-bold text-black">Thư viện</span>
                 </button>
               </div>
            )}
            
            {user && (
              <div className="flex items-center justify-between mb-3 px-1">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <div className="relative inline-flex items-center">
                    <input type="checkbox" checked={usePro} onChange={handleTogglePro} className="sr-only peer" />
                    <div className="w-8 h-4 bg-zinc-200 peer-focus:outline-none peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:h-3 after:w-3 after:transition-all peer-checked:bg-black"></div>
                  </div>
                  <span className="text-[10px] font-bold text-zinc-500 group-hover:text-black transition-colors tracking-widest">Tìm kiếm chuyên sâu</span>
                </label>
                {usePro && (
                  <span className="text-[9px] font-bold text-black py-0.5 px-2 bg-zinc-100 rounded-sm flex items-center gap-1">5 <Coins className="w-3 h-3" /></span>
                )}
              </div>
            )}

            <form onSubmit={handleSubmit} className="flex gap-2 items-center">
              <div className="flex-1 h-12 bg-zinc-50 border border-zinc-200 rounded-md flex items-center overflow-hidden focus-within:border-black focus-within:bg-white transition-colors">
                {user && (
                  <button type="button" onClick={handleAttach} className="px-3 text-zinc-400 hover:text-black transition-colors shrink-0">
                    <Paperclip className="w-4 h-4" />
                  </button>
                )}
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={user ? "Bạn muốn hỏi gì?" : "Tra cứu cùng AI"}
                  disabled={isSending}
                  className={`flex-1 h-full text-sm focus:outline-none bg-transparent min-w-0 pr-3 ${!user ? 'pl-4' : ''}`}
                />
              </div>
              <button
                type="submit"
                disabled={isSending || !input.trim()}
                className="w-12 h-12 shrink-0 rounded-md bg-black text-white flex items-center justify-center hover:bg-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

