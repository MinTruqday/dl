"use client";
import React, { useEffect, useState } from "react";
import { API_URL, getToken, toggleBookmarkAPI, purchaseDocumentAPI } from "@/app/lib/api";
import { useParams, useRouter } from "next/navigation";
import { 
  BookOpen, 
  Star, 
  MessageSquare, 
  Share2, 
  AlertCircle, 
  ShoppingCart, 
  Bookmark, 
  Loader2, 
  Eye, 
  User, 
  Lock, 
  ShieldCheck, 
  ChevronRight, 
  ExternalLink 
} from "lucide-react";
import ReviewSection from "@/app/components/ReviewSection";
import NestedComments from "@/app/components/NestedComments";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/app/contexts/AuthContext";

export default function DocumentDetailsPage() {
  const params = useParams();
  const slug = params?.slug as string;
  const router = useRouter();
  const { user } = useAuth() as any;
  
  const [docData, setDocData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"about" | "preview" | "reviews" | "comments">("about");
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (slug) fetchDocument();
  }, [slug]);

  useEffect(() => {
    if (!loading) {
      requestAnimationFrame(() => setVisible(true));
    }
  }, [loading]);

  const fetchDocument = async () => {
    try {
      const res = await fetch(`${API_URL}/documents/slug/${slug}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await res.json();
      if (res.ok && data.data) {
        setDocData(data.data);
        setIsBookmarked(data.data.is_bookmarked || false);
      } else {
        setError(data.message || "Không thể tải thông tin tài liệu");
      }
    } catch (err: any) {
      console.error("Lỗi tải thông tin tài liệu:", err);
      setError("Mất kết nối với máy chủ");
    } finally {
      setLoading(false);
    }
  };

  const handleRead = () => {
    router.push(`/documents/viewer/${docData._id || docData.id}`);
  };

  const handlePreview = () => {
    setActiveTab("preview");
    const tabsElement = window.document.getElementById("document-tabs");
    if (tabsElement) {
        tabsElement.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handleBookmark = async () => {
    if (!docData) return;
    try {
      const ok = await toggleBookmarkAPI(docData._id || docData.id);
      if (ok) setIsBookmarked(!isBookmarked);
    } catch (err: any) {
      console.error("Lỗi đánh dấu tài liệu:", err);
    }
  };

  const handlePurchase = async () => {
    if (!docData) return;
    setLoading(true);
    try {
      const res = await purchaseDocumentAPI(docData._id || docData.id);
      if (res.status === 200 || res.status === "purchased") {
        window.location.reload();
      }
    } catch (err: any) {
      console.error("Giao dịch thất bại:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
        <div className="flex h-[80vh] items-center justify-center">
          <div className="flex flex-col items-center gap-6">
            <Loader2 className="w-10 h-10 animate-spin text-zinc-300" />
            <p className="text-[11px] font-bold text-zinc-300">Đang chuẩn bị dữ liệu tri thức</p>
          </div>
        </div>
    );
  }

  if (error || !docData) {
    return (
        <div className="flex h-[80vh] flex-col items-center justify-center gap-6 animate-in fade-in duration-300">
          <AlertCircle className="w-16 h-16 text-zinc-300" />
          <p className="text-sm font-bold text-zinc-400">{error || "Tài liệu không tồn tại"}</p>
          <Button onClick={() => router.back()} className="h-12 px-8 bg-black text-white hover:bg-zinc-800 transition-all active:scale-95">
            Quay lại
          </Button>
        </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans bg-white selection:bg-black selection:text-white">
        
        {/* Dynamic Hero Section - With Layered Push-Up Animations */}
        <div 
            className="relative h-[450px] overflow-hidden bg-zinc-50 border border-zinc-100 flex items-center mb-16 transition-all duration-1000 ease-out"
            style={{ 
                opacity: visible ? 1 : 0, 
                transform: visible ? "translateY(0)" : "translateY(40px)" 
            }}
        >
            <div className="absolute inset-0 z-0 transition-transform duration-1000" style={{ transform: visible ? 'scale(1)' : 'scale(1.1)' }}>
                {docData.cover_image && (
                    <img src={docData.cover_image} className="w-full h-full object-cover opacity-10 grayscale" alt="" />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-zinc-50 via-zinc-50/80 to-transparent" />
            </div>

            <div className="w-full px-10 relative z-10 grid grid-cols-12 gap-20 items-center h-full">
                <div className={`col-span-4 hidden lg:flex justify-center transition-all duration-1000 delay-300 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}>
                    <div className="aspect-[2/3] w-full max-w-[240px] bg-white border border-zinc-100 p-3 relative group transition-all duration-700 hover:scale-[1.02]">
                         <div className="w-full h-full border border-zinc-50 relative overflow-hidden">
                            {docData.cover_image ? (
                                <img src={docData.cover_image} className="w-full h-full object-cover grayscale" alt="" />
                            ) : (
                                <div className="w-full h-full flex flex-col items-center justify-center p-8 text-center bg-zinc-50/50">
                                    <BookOpen className="w-10 h-10 text-zinc-100 mb-4" />
                                    <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">{docData.title}</span>
                                </div>
                            )}
                         </div>
                         <div className="absolute inset-0 border border-black/5 pointer-events-none -m-[1px]" />
                    </div>
                </div>

                <div className="col-span-12 lg:col-span-8 space-y-12">
                    <div className={`flex flex-wrap items-center gap-6 transition-all duration-700 delay-500 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
                        <span className="px-4 py-1.5 bg-black text-white text-[10px] font-bold uppercase tracking-widest">{docData.category_name || "Tri thức"}</span>
                        <div className="flex items-center gap-2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                            <Star className="w-4 h-4 fill-zinc-200 text-zinc-200" />
                            <span>{docData.average_rating ? docData.average_rating.toFixed(1) : "0.0"} / 5.0 Rating</span>
                        </div>
                    </div>

                    <h1 className={`text-6xl lg:text-7xl font-bold tracking-tighter text-black leading-[0.9] max-w-4xl text-balance transition-all duration-700 delay-700 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
                        {docData.title}
                    </h1>

                    <div className={`flex flex-wrap items-center gap-12 pt-4 transition-all duration-700 delay-1000 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
                        <button 
                            onClick={() => router.push(`/authors/${docData.author?.slug || docData.author_id}`)}
                            className="flex items-center gap-4 group"
                        >
                            <div className="w-10 h-10 bg-white border border-zinc-200 group-hover:border-black transition-all flex items-center justify-center overflow-hidden">
                                {docData.author?.avatar_url ? (
                                    <img src={docData.author.avatar_url} className="w-full h-full object-cover grayscale" alt="" />
                                ) : <User className="w-4 h-4 text-zinc-300" />}
                            </div>
                            <div className="flex flex-col items-start">
                                <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Được biên soạn bởi</span>
                                <span className="text-[13px] font-bold text-black uppercase tracking-tight group-hover:underline underline-offset-4">
                                    {docData.author?.username || "Cộng tác viên DocLib"}
                                </span>
                            </div>
                        </button>

                        <div className="flex items-center gap-12 text-[13px] font-bold text-black">
                            <div className="flex flex-col items-start">
                                <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Lượt tiếp cận</span>
                                <span>{docData.view_count?.toLocaleString() || 0}</span>
                            </div>
                            <div className="flex flex-col items-start">
                                <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Số trang</span>
                                <span>{docData.pages_count || "--"}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div 
            className="py-4 transition-all duration-700 delay-300"
            style={{ 
                opacity: visible ? 1 : 0, 
                transform: visible ? "translateY(0)" : "translateY(10px)" 
            }}
        >
            <div className="grid grid-cols-12 gap-16 items-start">
                <div className="col-span-12 lg:col-span-3 space-y-12 lg:sticky lg:top-32">
                    <div className="space-y-2">
                         <button 
                            onClick={handleRead}
                            className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.25em] hover:bg-zinc-800 transition-all flex items-center justify-center gap-3 active:scale-95"
                         >
                            <BookOpen className="w-4 h-4" />
                            Đọc tài liệu ngay
                         </button>

                         <button 
                            onClick={handlePreview}
                            className="w-full h-16 bg-white text-black border border-zinc-100 text-[11px] font-bold uppercase tracking-[0.25em] hover:border-black transition-all flex items-center justify-center gap-3 active:scale-95"
                         >
                            <Eye className="w-4 h-4" />
                            Xem trước nội dung
                         </button>

                         {docData.is_premium && (
                            <button 
                                onClick={handlePurchase}
                                className="w-full h-16 bg-zinc-50 text-black border border-zinc-50 text-[11px] font-bold uppercase tracking-[0.25em] hover:bg-black hover:text-white transition-all flex items-center justify-center gap-3 active:scale-95"
                            >
                                <ShoppingCart className="w-4 h-4" />
                                Sở hữu với {docData.price_dl?.toLocaleString()} DL
                            </button>
                         )}
                    </div>

                    <div className="pt-10 border-t border-zinc-100 grid grid-cols-2 gap-4">
                        <button onClick={handleBookmark} className="flex flex-col items-center gap-3 group transition-all">
                            <div className={`w-full h-16 border flex items-center justify-center transition-all ${isBookmarked ? 'bg-black text-white border-black' : 'bg-white text-zinc-200 border-zinc-100 group-hover:border-black group-hover:text-black'}`}>
                                <Bookmark className={`w-5 h-5 ${isBookmarked ? 'fill-current' : ''}`} />
                            </div>
                            <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest group-hover:text-black">{isBookmarked ? "Đã lưu" : "Lưu lại"}</span>
                        </button>
                        <button className="flex flex-col items-center gap-3 group transition-all">
                            <div className="w-full h-16 border border-zinc-100 text-zinc-200 flex items-center justify-center bg-white group-hover:border-black group-hover:text-black transition-all">
                                <Share2 className="w-5 h-5" />
                            </div>
                            <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest group-hover:text-black">Chia sẻ</span>
                        </button>
                    </div>

                    <div className="space-y-6 pt-10 border-t border-zinc-100">
                        <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-[0.2em] px-1">
                            <ShieldCheck className="w-4 h-4 text-zinc-300" /> Chứng thực
                        </div>
                        <div className="p-8 border border-zinc-100 bg-zinc-50/50 space-y-6">
                            <p className="text-[10px] font-bold text-zinc-500 leading-relaxed uppercase tracking-tight">
                                Tài liệu đã qua kiểm định chất lượng và tuân thủ các tiêu chuẩn tri thức cộng đồng.
                            </p>
                            <div className="h-1 w-full bg-zinc-100" />
                            <div className="flex items-center gap-3 text-[9px] font-bold text-black uppercase tracking-widest">
                                <div className="w-2 h-2 bg-green-500" />
                                AN TOÀN TRUY CẬP
                            </div>
                        </div>
                    </div>

                    <div className="space-y-6 pt-10 border-t border-zinc-100">
                        <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-[0.2em] px-1">
                            <ExternalLink className="w-4 h-4 text-zinc-300" /> Hành động khác
                        </div>
                        <div className="flex flex-col gap-2">
                            <button className="h-14 px-8 border border-zinc-100 bg-white hover:border-black transition-all text-[10px] font-bold uppercase tracking-widest flex items-center justify-between">
                                Chia sẻ tri thức <ChevronRight className="w-4 h-4 text-zinc-300" />
                            </button>
                            <button className="h-14 px-8 border border-zinc-100 bg-white hover:border-black transition-all text-[10px] font-bold uppercase tracking-widest flex items-center justify-between">
                                Báo cáo vi phạm <ChevronRight className="w-4 h-4 text-zinc-300" />
                            </button>
                        </div>
                    </div>
                </div>

                <div className="col-span-12 lg:col-span-9 space-y-16">
                    <div id="document-tabs" className="border-b border-zinc-100 flex gap-12 overflow-x-auto no-scrollbar">
                        {[
                            { id: "about", label: "Tóm lược nội dung" },
                            { id: "preview", label: "Xem trước nội dung" },
                            { id: "reviews", label: "Đánh giá cộng đồng" },
                            { id: "comments", label: "Thảo luận tri thức" }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={`pb-8 text-[11px] font-bold uppercase tracking-[0.2em] transition-all relative ${
                                    activeTab === tab.id ? "text-black" : "text-zinc-300 hover:text-black"
                                }`}
                            >
                                {tab.label}
                                {activeTab === tab.id && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-black" />}
                            </button>
                        ))}
                    </div>

                    <div className="min-h-[600px] animate-in fade-in slide-in-from-bottom-2 duration-700">
                        {activeTab === "about" && (
                            <div className="space-y-16">
                                <div className="prose prose-zinc max-w-none">
                                    <div className="text-black leading-[1.8] text-lg font-medium space-y-8">
                                        {docData.description ? (
                                            <div dangerouslySetInnerHTML={{ __html: docData.description.replace(/\n/g, '<br/>') }} />
                                        ) : (
                                            <p className="italic text-zinc-200">Không có bản tóm lược cho nội dung này.</p>
                                        )}
                                    </div>
                                </div>

                                {docData.tags && docData.tags.length > 0 && (
                                    <div className="pt-16 border-t border-zinc-100 space-y-8">
                                        <h4 className="text-[10px] font-bold text-zinc-300 uppercase tracking-[0.3em]">Hệ thống từ khóa</h4>
                                        <div className="flex flex-wrap gap-3">
                                            {docData.tags.map((tag: string, i: number) => (
                                                <span key={i} className="px-6 py-2.5 bg-white border border-zinc-100 text-[10px] font-bold text-zinc-400 hover:border-black hover:text-black transition-all cursor-pointer uppercase tracking-widest">
                                                    #{tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === "preview" && (
                            <div className="space-y-12">
                                {(() => {
                                    const isPrivileged = user && (["admin", "author", "moderator"].includes(user.role.toLowerCase()));
                                    const hasPaid = docData.has_purchased || !docData.is_premium;
                                    const canSeeFull = isPrivileged || hasPaid;
                                    const previewLimit = docData.preview_pages || 5;
                                    const rawContent = (docData.content || "");
                                    const contentToDisplay = canSeeFull ? rawContent : rawContent.slice(0, previewLimit * 1000);

                                    return (
                                        <div className="bg-white border border-zinc-100 min-h-[800px] relative">
                                            <div className="p-12 md:p-24 space-y-12">
                                                <article className="prose prose-zinc max-w-none">
                                                    <div className="text-black leading-[2.2] text-xl md:text-2xl font-serif space-y-12">
                                                        {docData.content ? (
                                                            <div dangerouslySetInnerHTML={{ __html: contentToDisplay.replace(/\n/g, '<br/><br/>') }} />
                                                        ) : (
                                                            <div className="space-y-10">
                                                                <p className="first-letter:text-7xl first-letter:font-bold first-letter:mr-3 first-letter:float-left first-letter:text-black">
                                                                    Nội dung của tài liệu "{docData.title}" đang được chuẩn bị để hiển thị tốt nhất trên thiết bị của bạn. 
                                                                </p>
                                                                <p className="text-zinc-500 font-sans text-lg">{docData.description || "Tài liệu này là một phần của kho tàng tri thức DocLib."}</p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </article>

                                                {!canSeeFull && (
                                                    <div className="mt-40 pt-40 border-t border-zinc-100 flex flex-col items-center text-center space-y-10 relative">
                                                        <div className="absolute inset-x-0 bottom-0 h-96 bg-gradient-to-t from-white via-white/95 to-transparent pointer-events-none" />
                                                        <div className="relative z-20 space-y-8 pb-20">
                                                            <div className="w-20 h-20 bg-black text-white flex items-center justify-center mx-auto">
                                                                <Lock className="w-8 h-8" />
                                                            </div>
                                                            <div className="space-y-4">
                                                                <h3 className="text-3xl font-bold text-black tracking-tighter uppercase">Giới hạn xem trước</h3>
                                                                <p className="text-[11px] font-bold text-zinc-400 leading-relaxed uppercase tracking-[0.2em] max-w-lg mx-auto">
                                                                    Bạn đã đọc hết phần xem trước cho phép. <br/>
                                                                    Hãy mở khóa để tiếp tục hành trình khám phá {docData.pages_count} trang tri thức.
                                                                </p>
                                                            </div>
                                                            <Button 
                                                                onClick={handlePurchase}
                                                                className="h-20 px-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.4em] hover:bg-zinc-800 transition-all rounded-none"
                                                            >
                                                                SỞ HỮU TOÀN BỘ TRI THỨC
                                                            </Button>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })()}
                            </div>
                        )}

                        {activeTab === "reviews" && <ReviewSection documentId={docData._id || docData.id} />}
                        
                        {activeTab === "comments" && (
                            <div className="bg-zinc-50/20 p-10 border border-zinc-100">
                                <NestedComments itemId={docData._id || docData.id} itemType="document" />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    </div>
  );
}
