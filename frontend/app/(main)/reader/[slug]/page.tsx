"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { getToken } from "@/app/lib/api";
import { Download, Type, Moon, Sun, ArrowLeftRight, Paintbrush, ShieldAlert, CheckCircle, XCircle, AlertCircle, X, MessageCircle, Send, BookOpen, Loader2, Sparkles, Languages, Lock, ShoppingCart, ChevronLeft } from "lucide-react";
import ReportModal from "@/app/components/ReportModal";

function ToastContainer({ toasts, removeToast }: { toasts: any[], removeToast: (id: string) => void }) {
  return (
    <div className="fixed bottom-6 left-6 z-[9999] flex flex-col gap-3">
      {toasts.map((t) => (
        <div key={t.id} className={`flex items-center gap-3 px-5 py-4  border text-[11px] font-bold tracking-widest transition-all animate-in slide-in-from-left-8 duration-300 ${
          t.type === 'success' ? 'bg-white border-black text-black' :
          t.type === 'error' ? 'bg-black border-black text-white' :
          'bg-zinc-50 border-border text-black'
        }`}>
          {t.type === 'success' && <CheckCircle className="w-4 h-4" />}
          {t.type === 'error' && <XCircle className="w-4 h-4" />}
          {t.type === 'info' && <AlertCircle className="w-4 h-4" />}
          <p>{t.message}</p>
          <button onClick={() => removeToast(t.id)} className="ml-4 opacity-40 hover:opacity-100 transition-opacity">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}

export default function AdvancedReader() {
  const { slug } = useParams();
  const bookId = slug; // Unify slug as bookId for internal logic
  const router = useRouter();
  const [book, setBook] = useState<any>(null);
  
  const [isDyslexic, setIsDyslexic] = useState(false);
  const [isRTL, setIsRTL] = useState(false);
  const [theme, setTheme] = useState<"light"|"dark"|"gray">("light");
  const [highlightColor, setHighlightColor] = useState<string>("#fef08a");
  const [toasts, setToasts] = useState<any[]>([]);

  const scrollTimer = useRef<NodeJS.Timeout | null>(null);
  const lastScrollY = useRef(0);
  const entryTime = useRef(Date.now());

  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<{ role: string, content: string }[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isSendingChat, setIsSendingChat] = useState(false);

  const [flashcardBtn, setFlashcardBtn] = useState<{show: boolean, x: number, y: number, text: string, context: string}>({show: false, x: 0, y: 0, text: "", context: ""});
  const [flashcardResult, setFlashcardResult] = useState<{front: string, back: string} | null>(null);
  const [isGeneratingFlashcard, setIsGeneratingFlashcard] = useState(false);

  const [savedHighlights, setSavedHighlights] = useState<any[]>([]);
  const [showNotesPanel, setShowNotesPanel] = useState(false);
  
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isBookOwned, setIsBookOwned] = useState(false);
  const [purchasing, setPurchasing] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    if (bookId) {
      fetchSavedHighlights();
      loadReadingPreferences();
    }
  }, [bookId]);

  const fetchSavedHighlights = async () => {
    try {
      const res = await fetch(`${API_URL}/reading/books/${bookId}/highlights`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) setSavedHighlights(await res.json());
    } catch (e) {
      console.error("Highlight fetch error:", e);
    }
  };

  const saveHighlightToServer = async (text: string, note: string = "") => {
    try {
      await fetch(`${API_URL}/reading/books/${bookId}/highlights`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ text, color: highlightColor, note }),
      });
      fetchSavedHighlights();
    } catch (e) {
      console.error("Highlight save error:", e);
    }
  };

  const deleteHighlightFromServer = async (highlightId: string) => {
    try {
      await fetch(`${API_URL}/reading/highlights/${highlightId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      setSavedHighlights(prev => prev.filter(h => h.id !== highlightId));
      showToast("Đã xóa ghi chú", "success");
    } catch (e) {
      console.error("Highlight delete error:", e);
    }
  };

  const loadReadingPreferences = async () => {
    try {
      const res = await fetch(`${API_URL}/reading/preferences`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        const prefs = await res.json();
        if (prefs.theme) setTheme(prefs.theme);
        if (prefs.is_dyslexic_mode) setIsDyslexic(prefs.is_dyslexic_mode);
      }
    } catch (e) {
      console.error("Preferences fetch error:", e);
    }
  };

  const saveReadingPreferences = async (newTheme?: string) => {
    try {
      await fetch(`${API_URL}/reading/preferences`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({
          theme: newTheme || theme,
          is_dyslexic_mode: isDyslexic,
        }),
      });
    } catch (e) {
      console.error("Preferences save error:", e);
    }
  };

  const generateFlashcard = async () => {
    if (!flashcardBtn.text) return;
    setIsGeneratingFlashcard(true);
    setFlashcardBtn(prev => ({...prev, show: false}));
    try {
      const token = getToken();
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/reading/books/${bookId}/flashcards/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          text: flashcardBtn.text,
          context: flashcardBtn.context
        })
      });
      if (!res.ok) throw new Error("Không thể tạo thẻ ghi nhớ");
      const data = await res.json();
      setFlashcardResult(data);
      showToast("Tạo thẻ ghi nhớ thành công", "success");
    } catch (error) {
      showToast("Không thể kết nối AI để tạo thẻ", "error");
    } finally {
      setIsGeneratingFlashcard(false);
    }
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isSendingChat) return;

    const userMessage = chatInput;
    setChatMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setChatInput("");
    setIsSendingChat(true);

    setChatMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const token = getToken();
      
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/rag/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          query: userMessage,
          book_id: bookId,     
          useWeb: false,       
          conversation_id: "reader_session_" + bookId
        })
      });

      if (!res.ok) throw new Error("Lỗi kết nối máy chủ");
      if (!res.body) throw new Error("Dữ liệu trống");

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let botResponse = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunks = decoder.decode(value, { stream: true }).split("\n\n");
        for (const chunk of chunks) {
          if (!chunk.trim()) continue;
          
          if (chunk.includes('event: message')) {
             const dataStr = chunk.split("data: ")[1];
             if (dataStr) {
                 try {
                     const data = JSON.parse(dataStr);
                     botResponse += data.chunk;

                     setChatMessages((prev) => {
                         const newMsgs = [...prev];
                         newMsgs[newMsgs.length - 1].content = botResponse;
                         return newMsgs;
                     });
                 } catch(e) { console.error(e); }
             }
          }
        }
      }
    } catch (e: any) {
      console.error(e);
      setChatMessages((prev) => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1].content = "Hệ thống đang bảo trì, vui lòng thử lại sau.";
          return newMsgs;
      });
    } finally {
      setIsSendingChat(false);
    }
  };

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  }, []);

  const handleReport = async (reason: string) => {
    try {
      const res = await fetch(`${API_URL}/reader/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ item_type: "book", item_id: bookId, reason }),
      });
      if (res.ok) {
        showToast("Báo cáo đã được gửi cho Ban Quản Trị", "success");
        setIsReportModalOpen(false);
      }
    } catch (e) {
      showToast("Lỗi khi gửi báo cáo", "error");
    }
  };

  const purchaseBook = async () => {
    setPurchasing(true);
    try {
      const res = await fetch(`${API_URL}/reader/purchase/book/${bookId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      const data = await res.json();
      if (res.ok) {
        showToast("Mua tài liệu thành công", "success");
        setIsBookOwned(true);
      } else {
        showToast(data.detail || "Không đủ số dư ví. Vui lòng nạp thêm.", "error");
      }
    } catch (e) {
      showToast("Lỗi thanh toán", "error");
    }
    setPurchasing(false);
  };

  useEffect(() => {
    fetchBookInfo();
    const cleanupAntiScraping = setupAntiScraping();
    setupScrollTelemetry();

    const handleBeforeUnload = () => {
        sendDropoffTelemetry();
    };
    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
        cleanupAntiScraping();
        window.removeEventListener("beforeunload", handleBeforeUnload);
        sendDropoffTelemetry(); 
    }
  }, [bookId]);

  const sendDropoffTelemetry = () => {
      const dwellTime = Math.floor((Date.now() - entryTime.current) / 1000);
      const scrollPercent = document.body.scrollHeight > window.innerHeight 
          ? Math.floor((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100) 
          : 100;
          
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/telemetry/dropoff`, {
          method: "POST",
          headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json'},
          body: JSON.stringify({ book_id: bookId, chapter: 1, scroll_percent: scrollPercent, dwell_time: dwellTime })
      }).catch(e => {}); 
  };

  const setupScrollTelemetry = () => {
      const onScroll = () => {
          if (scrollTimer.current) clearTimeout(scrollTimer.current);
          
          const currentY = window.scrollY;
          const distance = Math.abs(currentY - lastScrollY.current);
          lastScrollY.current = currentY;

          scrollTimer.current = setTimeout(() => {
              const pps = distance / 0.5; 
              if (pps > 4000) {
                  fetch(`${process.env.NEXT_PUBLIC_API_URL}/telemetry/scroll-speed`, {
                      method: "POST",
                      headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json'},
                      body: JSON.stringify({ pixels_per_second: pps })
                  });
              }
          }, 500);
      };
      window.addEventListener("scroll", onScroll);
  };

  const fetchBookInfo = async () => {
    try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/books/${bookId}`, {
            headers: { 'Authorization': `Bearer ${getToken()}`}
        });
        if (res.ok) setBook(await res.json());
        else showToast("Không tìm thấy tài liệu hoặc chưa được cấp quyền", "error");
    } catch(e) {
        showToast("Mất kết nối mạng", "error");
    }
  };

  const setupAntiScraping = () => {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((m) => {
            if(m.type === 'characterData' || m.type === 'childList') {
                showToast("Hệ thống phát hiện thay đổi DOM không hợp lệ", "error");
            }
        });
    });
    setTimeout(() => {
        const readerNode = document.getElementById("doclib-reader-core");
        if(readerNode) observer.observe(readerNode, { childList: true, characterData: true, subtree: true });
    }, 1000);
    return () => observer.disconnect();
  };

  const downloadWatermarkedPDF = async () => {
    showToast("Đang chuẩn bị bản in bảo vệ", "info");
    try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/books/${bookId}/export/pdf`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        if(!res.ok) throw new Error("Quyền truy cập bị từ chối");
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `DocLib_${bookId}_baomat.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        showToast("Tải xuống thành công", "success");
    } catch(e) {
        showToast("Bạn cần sở hữu tài liệu để tải về", "error");
    }
  };

  const applyHighlight = async () => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
        setFlashcardBtn(prev => ({...prev, show: false}));
        return;
    }
    
    const anchorNode = selection.anchorNode;
    let context = "";
    if (anchorNode && anchorNode.parentElement) {
      context = anchorNode.parentElement.textContent || "";
    }
    
    const text = selection.toString();
    if(text.length > 250) {
        showToast("Đoạn trích quá dài để xử lý", "error");
        selection.removeAllRanges();
        setFlashcardBtn(prev => ({...prev, show: false}));
        return;
    }

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    
    setFlashcardBtn({
      show: true,
      x: rect.x + (rect.width / 2) - 60, 
      y: rect.y - 48, 
      text: text,
      context: context
    });

    const span = document.createElement("span");
    span.style.backgroundColor = highlightColor;
    span.className = " px-1 transition-colors hover:opacity-80 cursor-pointer doclib-flashcard-trigger decoration-black/20";
    span.title = "Click để tạo Flashcard";
    
    try {
        range.surroundContents(span);
        selection.removeAllRanges();
        showToast("Đã lưu đoạn trích", "success");
        saveHighlightToServer(text);
    } catch(e) { console.error(e); }
  };

  if(!book) return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-4">
      <Loader2 className="w-10 h-10 animate-spin text-zinc-300" strokeWidth={1} />
      <span className="text-[10px] font-bold tracking-[0.3em] text-zinc-400">Đang tải tài liệu</span>
    </div>
  );

  return (
    <div className={`min-h-screen transition-all duration-500 ${theme === 'dark' ? 'bg-zinc-950 text-zinc-200' : theme === 'gray' ? 'bg-zinc-100 text-zinc-800' : 'bg-white text-black'} ${isDyslexic ? 'font-opendyslexic tracking-wider leading-loose' : 'font-medium'} ${isRTL ? 'active-rtl text-right' : ''}`} dir={isRTL ? "rtl" : "ltr"}>
      <ToastContainer toasts={toasts} removeToast={(id) => setToasts(prev => prev.filter(t => t.id !== id))} />

      <div className="sticky top-0 z-50 p-5 border-b border-zinc-200 flex items-center justify-between bg-inherit backdrop-blur-md transition-all">
        <div className="flex items-center gap-4 max-w-lg">
          <button onClick={() => router.back()} className="p-2 border border-black hover:bg-zinc-50 transition-all">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2 overflow-hidden">
            <BookOpen className="w-5 h-5 shrink-0" />
            <h1 className="text-sm font-bold tracking-tight truncate">{book.title}</h1>
          </div>
        </div>
        
        <div className="flex gap-1.5 items-center">
            <div className="flex items-center border border-border  px-3 py-1.5 mr-4 bg-zinc-50/50">
                <Paintbrush className="w-3.5 h-3.5 mr-3 text-zinc-400" />
                <div className="flex gap-2">
                    {['#fef08a', '#bbf7d0', '#bfdbfe', '#fbcfe8', '#fecdd3'].map(c => 
                        <button key={c} onClick={() => setHighlightColor(c)} className={`w-4 h-4  border transition-all ${highlightColor === c ? 'border-black scale-110' : 'border-zinc-200 hover:border-zinc-400'}`} style={{backgroundColor: c}}></button>
                    )}
                </div>
            </div>

            <button onClick={() => { setIsDyslexic(!isDyslexic); saveReadingPreferences(); }} className={`p-2.5  transition-all ${isDyslexic ? 'bg-black text-white' : 'hover:bg-zinc-100'}`} title="Phông cho người khiếm đọc"><Type className="w-4 h-4" /></button>
            <button onClick={() => setIsRTL(!isRTL)} className={`p-2.5  transition-all ${isRTL ? 'bg-black text-white' : 'hover:bg-zinc-100'}`} title="Chế độ đọc ngược"><Languages className="w-4 h-4" /></button>
            <button onClick={() => { const next = theme === 'dark' ? 'light' : theme === 'light' ? 'gray' : 'dark'; setTheme(next as any); saveReadingPreferences(next); }} className="p-2.5  hover:bg-zinc-100 transition-all">
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            <button onClick={() => setIsChatOpen(!isChatOpen)} className={`p-2.5  transition-all ml-2 ${isChatOpen ? 'bg-black text-white' : 'border border-border hover:border-black'}`} title="Hỏi đáp AI"><MessageCircle className="w-4 h-4" /></button>

            <button onClick={downloadWatermarkedPDF} className="ml-4 flex items-center gap-2 bg-black text-white px-6 py-2.5  text-[11px] font-bold tracking-widest hover:bg-zinc-800 transition-all">
                <Download className="w-3.5 h-3.5" /> Bản in bảo vệ
            </button>
        </div>
      </div>

      <div className="w-full max-w-3xl mx-auto px-6 py-16 animate-in fade-in duration-700">
        <div className="mb-12 p-4 bg-zinc-50 border border-black  flex gap-4 items-center opacity-90 select-none">
            <ShieldAlert className="w-5 h-5 text-black" />
            <div className="flex flex-col">
              <span className="text-[10px] font-black tracking-widest text-black">Bảo vệ bản quyền</span>
              <p className="text-xs font-medium text-zinc-600 mt-0.5">Tài liệu này đã được bảo vệ bản quyền. Nghiêm cấm mọi hành vi sao chép trái phép.</p>
            </div>
        </div>

        <article id="doclib-reader-core" className="text-xl leading-[2.2] selection:bg-zinc-900 selection:text-white" onMouseUp={applyHighlight}>
            {book.content?.split('\n').map((para: string, i: number) => (
                <p key={i} className="mb-8 indent-12 text-justify">{para}</p>
            )) || <div className="text-center py-20 text-zinc-300 font-bold tracking-widest">Tài liệu không có nội dung văn bản.</div>}
        </article>
      </div>

       {isChatOpen && (
        <div className="fixed bottom-24 right-8 w-96 h-[600px] bg-white  border border-black flex flex-col z-50 overflow-hidden animate-in slide-in-from-right-10 fade-in duration-300">
          <div className="bg-black p-5 text-white flex justify-between items-center shrink-0">
            <div className="flex flex-col">
               <div className="flex items-center gap-2.5 font-bold text-sm tracking-tight">
                 <Sparkles className="w-4 h-4" />
                 Hỏi đáp nội dung
               </div>
               <span className="text-[10px] text-zinc-400 truncate max-w-[220px] font-medium mt-1 tracking-widest">{book.title}</span>
            </div>
            <button onClick={() => setIsChatOpen(false)} className="hover:bg-zinc-800 p-2  transition-all">
              <X className="w-4 h-4 text-white" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 bg-zinc-50/50 flex flex-col gap-4 min-h-0 scrollbar-thin scrollbar-thumb-zinc-200">
            {chatMessages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center gap-4">
                <div className="w-12 h-12 bg-white border border-border  flex items-center justify-center">
                  <MessageCircle className="w-6 h-6 text-zinc-200" />
                </div>
                <p className="text-[10px] font-bold text-zinc-400 tracking-widest leading-relaxed max-w-[200px]">
                  Đặt câu hỏi về nội dung, nhân vật hoặc tóm tắt tài liệu này.
                </p>
              </div>
            ) : (
              chatMessages.map((msg, idx) => (
                <div key={idx} className={`max-w-[85%] px-5 py-3.5 text-sm leading-relaxed border ${
                  msg.role === 'user' 
                    ? 'bg-black text-white border-black self-end ' 
                    : 'bg-white border-border text-black self-start '
                }`}>
                  {msg.content}
                </div>
              ))
            )}
            {isSendingChat && (
              <div className="bg-white border border-border text-zinc-400 self-start px-5 py-3.5 text-xs font-bold tracking-widest animate-pulse flex items-center gap-3">
                 <Loader2 className="w-3.5 h-3.5 animate-spin" />
                 Đang xử lý
              </div>
            )}
          </div>

          <div className="p-4 bg-white border-t border-border shrink-0">
            <form onSubmit={handleChatSubmit} className="flex gap-2 relative items-center">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Nhập câu hỏi của bạn tại đây"
                className="flex-1 border border-border  px-5 py-3.5 text-xs font-bold tracking-widest focus:outline-none focus:border-black bg-zinc-50 transition-all"
                disabled={isSendingChat}
              />
              <button 
                type="submit" 
                disabled={isSendingChat || !chatInput.trim()}
                className="absolute right-2 p-2.5 bg-black text-white  hover:bg-zinc-800 disabled:opacity-20 transition-all"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}

      {flashcardBtn.show && (
        <button
          onClick={generateFlashcard}
          style={{ top: flashcardBtn.y + window.scrollY, left: flashcardBtn.x }}
          className="absolute z-50 px-5 py-2.5 bg-black text-white text-[10px] font-bold tracking-[0.2em]  hover:bg-zinc-800 transition-all flex items-center gap-2.5 animate-in fade-in zoom-in-95"
        >
          <Sparkles className="w-3.5 h-3.5" />
          Lưu thẻ ghi nhớ
        </button>
      )}

      {isGeneratingFlashcard && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in">
           <div className="bg-white p-10  border border-black flex flex-col items-center gap-6">
              <Loader2 className="w-10 h-10 animate-spin text-black" strokeWidth={1.5} />
              <p className="text-[10px] font-bold tracking-[0.3em] text-black">Đang xử lý</p>
           </div>
        </div>
      )}

      {flashcardResult && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-6" onClick={() => setFlashcardResult(null)}>
          <div className="bg-white max-w-md w-full  border border-black overflow-hidden animate-in zoom-in-95 duration-300" onClick={e => e.stopPropagation()}>
            <div className="bg-zinc-50 p-6 border-b border-border">
               <div className="flex items-center gap-2 mb-4">
                  <Type className="w-4 h-4 text-zinc-400" />
                  <h3 className="font-black text-[10px] tracking-widest text-zinc-400">Nội dung</h3>
               </div>
               <p className="text-xl font-black text-black tracking-tight leading-tight">{flashcardResult.front}</p>
            </div>
            <div className="p-8 min-h-[140px]">
               <div className="flex items-center gap-2 mb-4">
                  <Sparkles className="w-4 h-4 text-black" />
                  <h3 className="font-black text-[10px] tracking-widest text-black">Giải nghĩa</h3>
               </div>
               <p className="text-zinc-600 text-sm font-medium leading-relaxed">{flashcardResult.back}</p>
            </div>
            <div className="p-6 bg-zinc-50 border-t border-border flex justify-end">
               <button onClick={() => setFlashcardResult(null)} className="px-10 py-3 bg-black text-white  text-[11px] font-bold tracking-widest hover:bg-zinc-800 transition-all">
                 Hoàn tất
               </button>
            </div>
          </div>
        </div>
      )}
      
      <ReportModal 
        isOpen={isReportModalOpen} 
        onClose={() => setIsReportModalOpen(false)} 
        onSubmit={handleReport} 
      />
    </div>
  );
}
