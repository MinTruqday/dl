"use client";

import React, { useState } from "react";
import { X, Combine, Search, Loader2, Sparkles, FileText } from "lucide-react";
import { multiDocSynthesisAPI } from "@/services/ai.service";
import { useToast } from "@/contexts/ToastContext";
import ReactMarkdown from "react-markdown";

interface LibraryAISynthesisModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableDocuments: any[];
}

export default function LibraryAISynthesisModal({ isOpen, onClose, availableDocuments }: LibraryAISynthesisModalProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const { showToast } = useToast();

  if (!isOpen) return null;

  const handleSynthesize = async () => {
    if (selectedIds.length === 0) {
      showToast("Vui lòng chọn ít nhất một tài liệu", "info");
      return;
    }
    if (!query.trim()) {
      showToast("Vui lòng nhập câu hỏi tổng hợp", "info");
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      const data = await multiDocSynthesisAPI(selectedIds, query);
      setResult(data.synthesis);
    } catch (err: any) {
      showToast(err.message || "Tổng hợp thất bại", "error");
    } finally {
      setLoading(false);
    }
  };

  const toggleDoc = (id: string) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-white w-full max-w-5xl h-[85vh] border border-zinc-200 flex flex-col overflow-hidden animate-in zoom-in-95 duration-300 rounded-none shadow-none">
        <div className="flex items-center justify-between px-8 py-5 border-b border-zinc-200 bg-white">
          <div className="flex items-center gap-3">
            <Combine className="w-6 h-6 text-black" />
            <div>
              <h3 className="text-sm font-bold uppercase tracking-widest text-black">
                Tổng hợp đa tài liệu AI
              </h3>
              <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-tighter mt-0.5">Phân tích chéo dữ liệu từ thư viện cá nhân</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-zinc-400 hover:text-black transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          <div className="w-80 border-r border-zinc-200 bg-zinc-50 flex flex-col">
            <div className="p-4 border-b border-zinc-200 bg-white">
              <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Chọn tài liệu nguồn ({selectedIds.length})</span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {availableDocuments.map((doc) => (
                <button
                  key={doc.document_id || doc.id}
                  onClick={() => toggleDoc(doc.document_id || doc.id)}
                  className={`w-full flex items-start gap-3 p-3 text-left transition-all border ${
                    selectedIds.includes(doc.document_id || doc.id)
                      ? "bg-black text-white border-black"
                      : "bg-white text-black border-zinc-200 hover:border-black"
                  }`}
                >
                  <FileText className={`w-4 h-4 mt-0.5 shrink-0 ${selectedIds.includes(doc.document_id || doc.id) ? "text-zinc-400" : "text-zinc-400"}`} />
                  <span className="text-xs font-medium line-clamp-2 leading-tight">
                    {doc.document_title || doc.title}
                  </span>
                </button>
              ))}
              {availableDocuments.length === 0 && (
                <p className="text-[11px] text-zinc-400 text-center py-10 italic">Không có tài liệu nào khả dụng để tổng hợp</p>
              )}
            </div>
          </div>

          <div className="flex-1 flex flex-col bg-white">
            <div className="p-8 border-b border-zinc-100 bg-white">
              <div className="relative">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Nhập câu hỏi tổng hợp (ví dụ: 'Tìm điểm chung về phương pháp luận giữa các bài viết này')"
                  className="w-full h-14 pl-12 pr-4 bg-zinc-50 border border-zinc-200 focus:outline-none focus:border-black text-sm font-medium transition-all rounded-none"
                  onKeyDown={(e) => e.key === "Enter" && handleSynthesize()}
                />
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
                <button
                  onClick={handleSynthesize}
                  disabled={loading || selectedIds.length === 0}
                  className="absolute right-2 top-1/2 -translate-y-1/2 h-10 px-6 bg-black text-white text-xs font-bold uppercase tracking-widest disabled:opacity-30 transition-all active:scale-95"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Tổng hợp"}
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-12 relative">
              {loading ? (
                <div className="h-full flex flex-col items-center justify-center gap-6">
                  <div className="relative">
                     <Combine className="w-12 h-12 text-black animate-pulse" />
                     <Sparkles className="absolute -top-2 -right-2 w-6 h-6 text-zinc-300 animate-bounce" />
                  </div>
                  <div className="text-center space-y-2">
                    <p className="text-sm font-bold uppercase tracking-widest text-black">Đang liên kết dữ liệu</p>
                    <p className="text-xs text-zinc-400">Hệ thống đang quét nội dung từ {selectedIds.length} tài liệu...</p>
                  </div>
                </div>
              ) : result ? (
                <div className="animate-in fade-in duration-700 prose prose-zinc max-w-none text-sm leading-relaxed">
                  <div className="flex items-center gap-3 mb-8 pb-4 border-b border-zinc-100">
                    <div className="w-8 h-8 bg-black flex items-center justify-center">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <h4 className="text-sm font-bold uppercase tracking-widest">Báo cáo tổng hợp từ AI</h4>
                  </div>
                  <ReactMarkdown>{result}</ReactMarkdown>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center opacity-30">
                  <Combine className="w-16 h-16 mb-6 text-zinc-300 stroke-[1]" />
                  <p className="text-sm font-medium text-zinc-500 max-w-sm">
                    Chọn các tài liệu nguồn ở bên trái và đặt câu hỏi để AI thực hiện phân tích tổng hợp liên văn bản.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
