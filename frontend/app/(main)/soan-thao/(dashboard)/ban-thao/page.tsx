"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMyDocumentsAPI } from "@/features/content/services/document_metadata.service";
import { Loader2, FileText, Calendar, PenTool, ArrowRight, FolderOpen } from "lucide-react";
import { useToast } from "@/shared/contexts/ToastContext";

export default function DraftsPage() {
 const router = useRouter();
 const { showToast } = useToast();
 const [drafts, setDrafts] = useState<any[]>([]);
 const [loading, setLoading] = useState(true);
 const [visible, setVisible] = useState(false);

 useEffect(() => {
 fetchDrafts();
 }, []);

 const fetchDrafts = async () => {
 setLoading(true);
 try {
 const data = await getMyDocumentsAPI();
 const list = data.data || data || [];
 setDrafts(list.filter((d: any) => d.status === "draft"));
 } catch {
 showToast("Không thể tải danh sách bản nháp", "error");
 } finally {
 setLoading(false);
 requestAnimationFrame(() => setVisible(true));
 }
 };

 return (
 <div className="flex flex-col h-full font-sans">


 <div className={`flex-1 overflow-y-auto custom-scrollbar pr-2 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`} style={{ transitionDelay: "100ms" }}>
 {loading ? (
 <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px]">
 <Loader2 className="w-8 h-8 animate-spin text-[#0071E3] mb-4" />
 <p className="text-[13px] font-medium text-[#6E6E73]">Đang đồng bộ dữ liệu...</p>
 </div>
 ) : drafts.length === 0 ? (
 <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] p-12 text-center">
 <div className="w-16 h-16 bg-[#F5F5F7] border-[#E8E8ED] flex items-center justify-center rounded-[18px] mb-4">
 <FolderOpen className="w-8 h-8 text-[#C7C7CC]" />
 </div>
 <p className="text-[13px] font-medium text-[#6E6E73] mb-4 mb-2">Chưa có bản nháp nào</p>
 <p className="text-[15px] text-[#6E6E73] max-w-sm mb-6">Bạn chưa có tác phẩm nào đang trong quá trình soạn thảo. Bắt đầu sáng tác ngay.</p>
 <button onClick={() => router.push("/cung-cap")} className="h-[44px] px-6 bg-[#0071E3] text-white text-[15px] font-medium rounded-full hover:bg-[#0077ED] transition-colors flex items-center gap-2">
 <PenTool className="w-4 h-4" /> Tạo tác phẩm mới
 </button>
 </div>
 ) : (
 <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 pb-6">
 {drafts.map((draft: any) => (
 <button key={draft._id || draft.id} onClick={() => router.push(`/soan-thao?tai-lieu=${draft._id || draft.id}`)} className="group flex flex-col bg-[#F5F5F7] border-[#E8E8ED] rounded-[18px] hover: transition-all duration-300 overflow-hidden text-left hover:-translate-y-1">
 <div className="aspect-[3/4] w-full bg-[#F5F5F7] relative overflow-hidden flex items-center justify-center">
 {draft.cover_url ? (
 <img src={draft.cover_url} alt={draft.title} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
 ) : (
 <div className="w-full h-full bg-[#F5F5F7] flex items-center justify-center transition-transform duration-700 group-hover:scale-105">
 <FileText className="w-12 h-12 text-[#C7C7CC]" />
 </div>
 )}
 <div className="absolute top-4 left-4 px-3 py-1.5 bg-white/90 backdrop-blur-md rounded-[10px]">
 <span className="text-[12px] font-medium text-[#6E6E73] flex items-center gap-2">
 <div className="w-2 h-2 rounded-full bg-[#0071E3] animate-pulse" /> Bản nháp
 </span>
 </div>
 <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-300 flex items-center justify-center">
 <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center opacity-0 translate-y-4 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300 text-[#1D1D1F]">
 <ArrowRight className="w-5 h-5" />
 </div>
 </div>
 </div>
 <div className="p-5 flex flex-col flex-1 gap-4 w-full bg-white">
 <p className="text-[13px] font-medium text-[#6E6E73] mb-4 line-clamp-2 leading-relaxed">{draft.title || "Tác phẩm chưa có tiêu đề"}</p>
 <div className="mt-auto pt-4 border-[#E8E8ED] flex items-center justify-between">
 <div className="flex items-center gap-2 text-[#6E6E73]">
 <Calendar className="w-4 h-4" />
 <span className="text-[13px] font-medium">{new Date(draft.updated_at || draft.created_at).toLocaleDateString("vi-VN")}</span>
 </div>
 <div className="w-8 h-8 rounded-full bg-[#F5F5F7] flex items-center justify-center group-hover:bg-[#0071E3] transition-colors">
 <PenTool className="w-4 h-4 text-[#6E6E73] group-hover:text-white transition-colors" />
 </div>
 </div>
 </div>
 </button>
 ))}
 </div>
 )}
 </div>
 </div>
 );
}
