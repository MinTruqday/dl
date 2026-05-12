"use client";

import React, { useState } from "react";
import { X, Brain, Quote, Wind, ClipboardCheck, Loader2, Share2, FileText, Layout } from "lucide-react";
import { 
  generateMindmapAPI, 
  suggestCitationsAPI, 
  transformToneAPI, 
  peerReviewAPI,
  createPostAPI,
  createStoryAPI
} from "@/services/ai.service";
import { useToast } from "@/contexts/ToastContext";
import ReactMarkdown from "react-markdown";

interface AIToolsModalProps {
  isOpen: boolean;
  onClose: () => void;
  editorContent: string;
}

export default function AIToolsModal({ isOpen, onClose, editorContent }: AIToolsModalProps) {
  const [activeTool, setActiveTool] = useState<"mindmap" | "citation" | "tone" | "review" | "publish" | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const { showToast } = useToast();

  const [toneOptions, setToneOptions] = useState({ tone: "chuyên nghiệp", expansion: false });

  if (!isOpen) return null;

  const handleToolAction = async (tool: typeof activeTool) => {
    setActiveTool(tool);
    setLoading(true);
    setResult(null);
    try {
      let data;
      switch (tool) {
        case "mindmap":
          data = await generateMindmapAPI(editorContent);
          break;
        case "citation":
          data = await suggestCitationsAPI(editorContent);
          break;
        case "tone":
          data = await transformToneAPI(editorContent, toneOptions.tone, toneOptions.expansion);
          break;
        case "review":
          data = await peerReviewAPI(editorContent);
          break;
        case "publish":
          data = {
            post: (await createPostAPI(editorContent, "Dựa trên tài liệu đang soạn thảo")).post,
            story: (await createStoryAPI(editorContent)).story
          };
          break;
      }
      setResult(data);
    } catch (err: any) {
      showToast(err.message || "Xử lý AI thất bại", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-white w-full max-w-4xl h-[80vh] border border-zinc-200 flex flex-col overflow-hidden animate-in zoom-in-95 duration-300 rounded-none shadow-none">
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-200 bg-white">
          <div className="flex items-center gap-3">
            <Brain className="w-5 h-5 text-black" />
            <h3 className="text-sm font-bold uppercase tracking-widest text-black">
              Công cụ nghiên cứu AI
            </h3>
          </div>
          <button onClick={onClose} className="p-2 text-zinc-400 hover:text-black transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          <div className="w-64 border-r border-zinc-200 bg-zinc-50 p-4 space-y-2">
            {[
              { id: "mindmap", label: "Bản đồ tư duy", icon: Brain },
              { id: "citation", label: "Gợi ý trích dẫn", icon: Quote },
              { id: "tone", label: "Biến đổi giọng văn", icon: Wind },
              { id: "review", label: "Thẩm định nội dung", icon: ClipboardCheck },
              { id: "publish", label: "Phát hành mạng xã hội", icon: Share2 },
            ].map((tool) => (
              <button
                key={tool.id}
                onClick={() => handleToolAction(tool.id as any)}
                className={`w-full flex items-center gap-3 px-4 py-3 text-xs font-bold uppercase tracking-tight transition-all border ${
                  activeTool === tool.id ? "bg-black text-white border-black" : "bg-white text-zinc-600 border-zinc-200 hover:border-black"
                }`}
              >
                <tool.icon className="w-4 h-4" />
                {tool.label}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto p-8 bg-white relative">
            {!activeTool ? (
              <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
                <Brain className="w-12 h-12 mb-4 text-zinc-300" />
                <p className="text-sm font-medium text-zinc-500">Chọn một công cụ để bắt đầu phân tích văn bản</p>
              </div>
            ) : (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
                <div className="mb-6 pb-6 border-b border-zinc-100">
                  <h4 className="text-lg font-medium text-black capitalize">
                    {activeTool === 'mindmap' ? 'Bản đồ tư duy' : 
                     activeTool === 'citation' ? 'Gợi ý trích dẫn' : 
                     activeTool === 'tone' ? 'Biến đổi giọng văn' : 
                     activeTool === 'review' ? 'Thẩm định nội dung' :
                     'Phát hành mạng xã hội'}
                  </h4>
                  <p className="text-xs text-zinc-400 mt-1 uppercase tracking-widest font-bold">Kết quả phân tích từ AI</p>
                </div>

                {loading ? (
                  <div className="py-20 flex flex-col items-center justify-center gap-4">
                    <Loader2 className="w-8 h-8 animate-spin text-black" />
                    <p className="text-xs font-bold uppercase tracking-widest text-zinc-400">Đang xử lý dữ liệu</p>
                  </div>
                ) : result ? (
                  <div className="prose prose-zinc max-w-none text-sm leading-relaxed">
                    {activeTool === "mindmap" && (
                      <div className="space-y-6">
                        <div className="p-6 border border-zinc-200 bg-zinc-50">
                          <p className="text-xs font-bold uppercase mb-4 text-zinc-400">Cấu trúc đề xuất</p>
                          <div className="space-y-4">
                            {result.nodes?.filter((n: any) => n.id === 'root').map((root: any) => (
                              <div key={root.id} className="space-y-4">
                                <div className="p-3 bg-black text-white text-center font-bold">{root.label}</div>
                                <div className="grid grid-cols-2 gap-4">
                                  {result.edges?.filter((e: any) => e.from === root.id).map((edge: any) => {
                                    const child = result.nodes?.find((n: any) => n.id === edge.to);
                                    return child && (
                                      <div key={child.id} className="p-3 border border-zinc-300 bg-white text-center text-xs font-medium">
                                        {child.label}
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                        <p className="text-[10px] text-zinc-400 italic">Lưu ý: Tính năng hiển thị sơ đồ trực quan đang được nâng cấp.</p>
                      </div>
                    )}
                    {activeTool === "citation" && (
                      <div className="whitespace-pre-wrap text-zinc-700 bg-zinc-50 p-6 border border-zinc-200">
                        {result.citations}
                      </div>
                    )}
                    {activeTool === "tone" && (
                      <div className="space-y-4">
                         <div className="flex gap-2 mb-4">
                            {["Chuyên nghiệp", "Hàn lâm", "Thuyết phục", "Sáng tạo"].map(t => (
                              <button 
                                key={t}
                                onClick={() => {
                                  setToneOptions(prev => ({ ...prev, tone: t.toLowerCase() }));
                                  handleToolAction("tone");
                                }}
                                className={`px-3 py-1 text-[10px] font-bold uppercase border ${toneOptions.tone === t.toLowerCase() ? "bg-black text-white border-black" : "bg-white text-zinc-400 border-zinc-200 hover:border-black"}`}
                              >
                                {t}
                              </button>
                            ))}
                         </div>
                         <div className="bg-zinc-50 p-6 border border-zinc-200 italic">
                            {result.transformed_text}
                         </div>
                      </div>
                    )}
                    {activeTool === "review" && (
                      <div className="bg-white">
                         <ReactMarkdown>{result.review_report}</ReactMarkdown>
                      </div>
                    )}
                    {activeTool === "publish" && (
                      <div className="space-y-8">
                        <div className="space-y-4">
                           <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-black">
                              <FileText className="w-4 h-4" /> Nội dung bài đăng (Post)
                           </div>
                           <div className="bg-zinc-50 p-6 border border-zinc-200 text-sm leading-relaxed whitespace-pre-wrap">
                              {result.post}
                           </div>
                           <button 
                             onClick={() => {
                               navigator.clipboard.writeText(result.post);
                               showToast("Đã sao chép nội dung bài đăng", "success");
                             }}
                             className="px-4 py-2 bg-black text-white text-[10px] font-bold uppercase tracking-widest active:scale-95"
                           >
                             Sao chép bài đăng
                           </button>
                        </div>

                        <div className="space-y-4 pt-8 border-t border-zinc-100">
                           <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-black">
                              <Layout className="w-4 h-4" /> Kịch bản Story (Slides)
                           </div>
                           <div className="bg-zinc-50 p-6 border border-zinc-200 text-sm leading-relaxed whitespace-pre-wrap italic">
                              {result.story}
                           </div>
                           <button 
                             onClick={() => {
                               navigator.clipboard.writeText(result.story);
                               showToast("Đã sao chép kịch bản story", "success");
                             }}
                             className="px-4 py-2 border border-black text-black text-[10px] font-bold uppercase tracking-widest active:scale-95"
                           >
                             Sao chép kịch bản
                           </button>
                        </div>
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
