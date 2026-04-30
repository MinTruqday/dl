"use client";

import React, { useEffect, useState, useCallback } from "react";
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
  ExternalLink,
  Clock,
  CheckCircle2,
  Flag
} from "lucide-react";
import ReviewSection from "@/app/components/ReviewSection";
import NestedComments from "@/app/components/NestedComments";
import { Notification } from "@/app/components/NotificationToast";
import { useAuth } from "@/app/contexts/AuthContext";
import ReportModal from "@/app/components/ReportModal";

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
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [showReportModal, setShowReportModal] = useState(false);

  const fetchDocument = useCallback(async () => {
    try {
      const token = getToken();
      const headers: any = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      
      const res = await fetch(`${API_URL}/documents/slug/${slug}`, {
        headers: headers
      });
      const data = await res.json();
      if (res.ok && data.data) {
        setDocData(data.data);
        setIsBookmarked(data.data.is_bookmarked || false);
      } else {
        setError(data.message || "Không thể truy xuất dữ liệu tài liệu");
      }
    } catch (err: any) {
      setError("Mất kết nối với hệ thống lưu trữ tri thức");
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    if (slug) fetchDocument();
  }, [slug, fetchDocument]);

  useEffect(() => {
    if (!loading) {
      requestAnimationFrame(() => setVisible(true));
    }
  }, [loading]);

  const handleRead = () => {
    if (!docData) return;
    router.push(`/documents/viewer/${docData._id || docData.id}`);
  };

  const handlePreview = () => {
    setActiveTab("preview");
    const tabsElement = document.getElementById("document-tabs");
    if (tabsElement) {
        tabsElement.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handleBookmark = async () => {
    if (!docData) return;
    if (!user) {
        setNotification({ type: "error", text: "Vui lòng đăng nhập để lưu tài liệu" });
        return;
    }
    try {
      const ok = await toggleBookmarkAPI(docData._id || docData.id);
      if (ok) {
          setIsBookmarked(!isBookmarked);
          setNotification({ type: "success", text: isBookmarked ? "Đã xóa khỏi thư viện" : "Đã lưu vào thư viện tri thức" });
      }
    } catch (err: any) {
      setNotification({ type: "error", text: "Không thể cập nhật trạng thái lưu trữ" });
    }
  };

  const handlePurchase = async () => {
    if (!docData) return;
    if (!user) {
        setNotification({ type: "error", text: "Vui lòng đăng nhập để thực hiện giao dịch" });
        return;
    }
    setLoading(true);
    try {
      const res = await purchaseDocumentAPI(docData._id || docData.id);
      if (res.status === 200 || res.status === "purchased") {
        setNotification({ type: "success", text: "Giao dịch tri thức thành công" });
        setTimeout(() => window.location.reload(), 1500);
      } else {
        setNotification({ type: "error", text: res.message || "Số dư không đủ để thực hiện giao dịch" });
      }
    } catch (err: any) {
      setNotification({ type: "error", text: "Giao dịch thất bại. Vui lòng thử lại sau" });
    } finally {
      setLoading(false);
    }
  };

  const handleShare = () => {
      if (typeof navigator !== 'undefined' && navigator.share) {
          navigator.share({
              title: docData?.title,
              text: docData?.description,
              url: window.location.href
          }).catch(() => {
              setNotification({ type: "error", text: "Không thể thực hiện chia sẻ" });
          });
      } else {
          navigator.clipboard.writeText(window.location.href);
          setNotification({ type: "success", text: "Đã sao chép liên kết tri thức" });
      }
  };

  if (loading) {
    return (
        <div className="flex h-[80vh] items-center justify-center font-sans">
          <div className="flex flex-col items-center gap-8">
            <Loader2 className="w-12 h-12 animate-spin text-zinc-100" />
            <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-[0.3em]">Đang giải mã mạng lưới tri thức</p>
          </div>
        </div>
    );
  }

  if (error || !docData) {
    return (
        <div className="flex h-[80vh] flex-col items-center justify-center gap-10 animate-in fade-in duration-500 font-sans">
          <AlertCircle className="w-20 h-20 text-zinc-50 stroke-[1]" />
          <p className="text-sm font-bold text-zinc-400 uppercase tracking-widest">{error || "Thực thể tri thức không tồn tại"}</p>
          <button 
            onClick={() => router.back()} 
            className="h-14 px-12 bg-black text-white text-[11px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-95 rounded-sm"
          >
            Quay lại hành trình
          </button>
        </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans bg-white text-black selection:bg-black selection:text-white">
        {notification && (
            <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
                <Notification type={notification.type} message={notification.text} />
            </div>
        )}

        {showReportModal && (
            <ReportModal 
                itemId={docData._id || docData.id} 
                itemType="document" 
                onClose={() => setShowReportModal(false)} 
            />
        )}
        
        <div 
            className="relative h-[500px] overflow-hidden bg-zinc-50 border border-zinc-100 flex items-center mb-20 transition-all duration-1000 ease-out rounded-sm"
            style={{ 
                opacity: visible ? 1 : 0, 
                transform: visible ? "translateY(0)" : "translateY(20px)" 
            }}
        >
            <div className="absolute inset-0 z-0 transition-transform duration-1000" style={{ transform: visible ? 'scale(1)' : 'scale(1.05)' }}>
                {docData.cover_image && (
                    <img src={docData.cover_image} className="w-full h-full object-cover opacity-5 grayscale" alt="" />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-zinc-50 via-zinc-50/90 to-transparent" />
            </div>

            <div className="w-full px-12 relative z-10 grid grid-cols-12 gap-24 items-center h-full">
                <div className={`col-span-4 hidden lg:flex justify-center transition-all duration-1000 delay-300 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                    <div className="aspect-[2/3] w-full max-w-[280px] bg-white border border-zinc-100 p-4 relative group transition-all duration-700 hover:scale-[1.02] rounded-sm">
                         <div className="w-full h-full border border-zinc-50 relative overflow-hidden rounded-sm bg-zinc-50">
                            {docData.cover_image ? (
                                <img src={docData.cover_image} className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-700" alt="" />
                            ) : (
                                <div className="w-full h-full flex flex-col items-center justify-center p-10 text-center">
                                    <BookOpen className="w-12 h-12 text-zinc-100 mb-6 stroke-[1]" />
                                    <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{docData.title}</span>
                                </div>
                            )}
                         </div>
                    </div>
                </div>

                <div className="col-span-12 lg:col-span-8 space-y-14">
                    <div className={`flex flex-wrap items-center gap-8 transition-all duration-700 delay-500 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
                        <span className="px-5 py-2 bg-black text-white text-[10px] font-bold uppercase tracking-[0.2em] rounded-sm">{docData.category_name || "Tri thức"}</span>
                        <div className="flex items-center gap-3 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                            <Star className="w-4 h-4 fill-zinc-200 text-zinc-200" />
                            <span className="text-black">{docData.average_rating ? docData.average_rating.toFixed(1) : "0.0"}</span>
                            <span className="text-zinc-200">/</span>
                            <span>5.0 Rating</span>
                        </div>
                    </div>

                    <h1 className={`text-6xl lg:text-8xl font-bold tracking-tighter text-black leading-[0.85] max-w-5xl text-balance transition-all duration-700 delay-700 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
                        {docData.title}
                    </h1>

                    <div className={`flex flex-wrap items-center gap-16 pt-6 transition-all duration-700 delay-1000 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
                        <button 
                            onClick={() => router.push(`/authors/${docData.author?.slug || docData.author_id}`)}
                            className="flex items-center gap-5 group"
                        >
                            <div className="w-12 h-12 bg-white border border-zinc-100 group-hover:border-black transition-all flex items-center justify-center overflow-hidden rounded-sm">
                                {docData.author?.avatar_url ? (
                                    <img src={docData.author.avatar_url} className="w-full h-full object-cover grayscale" alt="" />
                                ) : <User className="w-5 h-5 text-zinc-100" />}
                            </div>
                            <div className="flex flex-col items-start space-y-0.5">
                                <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Biên soạn bởi</span>
                                <span className="text-sm font-bold text-black uppercase tracking-tight group-hover:underline underline-offset-4">
                                    {docData.author?.display_name || docData.author?.username || "Cộng tác viên"}
                                </span>
                            </div>
                        </button>

                        <div className="flex items-center gap-16 text-sm font-bold text-black uppercase tracking-tight">
                            <div className="flex flex-col items-start space-y-0.5">
                                <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Lượt tiếp cận</span>
                                <span>{docData.view_count?.toLocaleString() || 0}</span>
                            </div>
                            <div className="flex flex-col items-start space-y-0.5">
                                <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Số trang</span>
                                <span>{docData.pages_count || "--"}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div 
            className="transition-all duration-700 delay-300"
            style={{ 
                opacity: visible ? 1 : 0, 
                transform: visible ? "translateY(0)" : "translateY(10px)" 
            }}
        >
            <div className="grid grid-cols-12 gap-20 items-start">
                <div className="col-span-12 lg:col-span-3 space-y-14 lg:sticky lg:top-32">
                    <div className="space-y-3">
                         <button 
                            onClick={handleRead}
                            className="w-full h-18 bg-black text-white text-[11px] font-bold uppercase tracking-[0.3em] hover:bg-zinc-800 transition-all flex items-center justify-center gap-4 active:scale-95 rounded-sm"
                         >
                            <BookOpen className="w-4 h-4" />
                            Đọc tài liệu ngay
                         </button>

                         <button 
                            onClick={handlePreview}
                            className="w-full h-18 bg-white text-black border border-zinc-100 text-[11px] font-bold uppercase tracking-[0.3em] hover:border-black transition-all flex items-center justify-center gap-4 active:scale-95 rounded-sm"
                         >
                            <Eye className="w-4 h-4" />
                            Xem trước nội dung
                         </button>

                         {docData.is_premium && (
                            <button 
                                onClick={handlePurchase}
                                className="w-full h-18 bg-zinc-50 text-black border border-zinc-100 text-[11px] font-bold uppercase tracking-[0.3em] hover:bg-black hover:text-white transition-all flex items-center justify-center gap-4 active:scale-95 rounded-sm"
                            >
                                <ShoppingCart className="w-4 h-4" />
                                Sở hữu {docData.price_dl?.toLocaleString()} DL
                            </button>
                         )}
                    </div>

                    <div className="pt-12 border-t border-zinc-100 grid grid-cols-2 gap-6">
                        <button onClick={handleBookmark} className="flex flex-col items-center gap-4 group transition-all">
                            <div className={`w-full h-18 border flex items-center justify-center transition-all rounded-sm ${isBookmarked ? 'bg-black text-white border-black' : 'bg-white text-zinc-100 border-zinc-100 group-hover:border-black group-hover:text-black'}`}>
                                <Bookmark className={`w-5 h-5 ${isBookmarked ? 'fill-current' : ''}`} />
                            </div>
                            <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest group-hover:text-black">{isBookmarked ? "Đã lưu" : "Lưu lại"}</span>
                        </button>
                        <button onClick={handleShare} className="flex flex-col items-center gap-4 group transition-all">
                            <div className="w-full h-18 border border-zinc-100 text-zinc-100 flex items-center justify-center bg-white group-hover:border-black group-hover:text-black transition-all rounded-sm">
                                <Share2 className="w-5 h-5" />
                            </div>
                            <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest group-hover:text-black">Chia sẻ</span>
                        </button>
                    </div>

                    <div className="space-y-8 pt-12 border-t border-zinc-100">
                        <div className="flex items-center gap-4 text-[11px] font-bold text-black uppercase tracking-[0.3em]">
                            <ShieldCheck className="w-4 h-4 text-zinc-200" /> Hệ thống chứng thực
                        </div>
                        <div className="p-10 border border-zinc-100 bg-zinc-50/30 space-y-8 rounded-sm">
                            <p className="text-[11px] font-medium text-zinc-400 leading-loose uppercase tracking-tight">
                                Tài liệu đã được hội đồng chuyên môn DocLib kiểm định chất lượng và đảm bảo tính toàn vẹn tri thức.
                            </p>
                            <div className="flex items-center gap-4 text-[10px] font-bold text-black uppercase tracking-widest">
                                <CheckCircle2 className="w-4 h-4 text-black" />
                                Bảo mật tuyệt đối
                            </div>
                        </div>
                    </div>

                    <div className="space-y-8 pt-12 border-t border-zinc-100">
                        <div className="flex items-center gap-4 text-[11px] font-bold text-black uppercase tracking-[0.3em]">
                            <Flag className="w-4 h-4 text-zinc-200" /> Phản hồi thực thể
                        </div>
                        <div className="flex flex-col gap-3">
                            <button 
                                onClick={() => setShowReportModal(true)}
                                className="h-16 px-8 border border-zinc-100 bg-white hover:border-black transition-all text-[10px] font-bold uppercase tracking-widest flex items-center justify-between rounded-sm group"
                            >
                                Báo cáo vi phạm <ChevronRight className="w-4 h-4 text-zinc-100 group-hover:text-black transition-all" />
                            </button>
                        </div>
                    </div>
                </div>

                <div className="col-span-12 lg:col-span-9 space-y-20">
                    <div id="document-tabs" className="border-b border-zinc-100 flex gap-16 overflow-x-auto scrollbar-hide">
                        {[
                            { id: "about", label: "Tóm lược nội dung" },
                            { id: "preview", label: "Xem trước tri thức" },
                            { id: "reviews", label: "Đánh giá cộng đồng" },
                            { id: "comments", label: "Thảo luận tri thức" }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={`pb-10 text-[11px] font-bold uppercase tracking-[0.3em] transition-all relative shrink-0 ${
                                    activeTab === tab.id ? "text-black" : "text-zinc-200 hover:text-black"
                                }`}
                            >
                                {tab.label}
                                {activeTab === tab.id && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-black" />}
                            </button>
                        ))}
                    </div>

                    <div className="min-h-[800px] animate-in fade-in slide-in-from-bottom-4 duration-700">
                        {activeTab === "about" && (
                            <div className="space-y-20">
                                <div className="prose prose-zinc max-w-none">
                                    <div className="text-black leading-[2] text-lg font-medium space-y-10">
                                        {docData.description ? (
                                            <div dangerouslySetInnerHTML={{ __html: docData.description.replace(/\n/g, '<br/>') }} />
                                        ) : (
                                            <div className="py-20 border border-dashed border-zinc-100 flex items-center justify-center italic text-zinc-200 uppercase tracking-widest text-[10px]">
                                                Không có bản tóm lược hệ thống cho thực thể này
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {docData.tags && docData.tags.length > 0 && (
                                    <div className="pt-20 border-t border-zinc-100 space-y-10">
                                        <h4 className="text-[11px] font-bold text-zinc-200 uppercase tracking-[0.4em]">Mạng lưới từ khóa liên kết</h4>
                                        <div className="flex flex-wrap gap-4">
                                            {docData.tags.map((tag: string, i: number) => (
                                                <span key={i} className="px-8 py-3 bg-white border border-zinc-100 text-[10px] font-bold text-zinc-400 hover:border-black hover:text-black transition-all cursor-pointer uppercase tracking-[0.2em] rounded-sm">
                                                    #{tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === "preview" && (
                            <div className="space-y-16">
                                {(() => {
                                    const isPrivileged = user && (["admin", "author", "moderator"].includes(user.role.toLowerCase()));
                                    const hasPaid = docData.has_purchased || !docData.is_premium;
                                    const canSeeFull = isPrivileged || hasPaid;
                                    const previewLimit = docData.preview_pages || 5;
                                    const rawContent = (docData.content || "");
                                    const contentToDisplay = canSeeFull ? rawContent : rawContent.slice(0, previewLimit * 1000);

                                    return (
                                        <div className="bg-white border border-zinc-100 min-h-[1000px] relative rounded-sm">
                                            <div className="p-16 md:p-32 space-y-16">
                                                <article className="prose prose-zinc max-w-none">
                                                    <div className="text-black leading-[2.4] text-xl md:text-2xl font-sans space-y-16">
                                                        {docData.content ? (
                                                            <div dangerouslySetInnerHTML={{ __html: contentToDisplay.replace(/\n/g, '<br/><br/>') }} />
                                                        ) : (
                                                            <div className="space-y-12">
                                                                <p className="first-letter:text-8xl first-letter:font-bold first-letter:mr-6 first-letter:float-left first-letter:text-black tracking-tight">
                                                                    Dữ liệu của thực thể tri thức "{docData.title}" đang được trích xuất và hiển thị theo tiêu chuẩn DocLib. 
                                                                </p>
                                                                <p className="text-zinc-400 font-sans text-xl leading-loose">{docData.description || "Thực thể này là một phần cốt lõi trong hạ tầng tri thức của chúng tôi."}</p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </article>

                                                {!canSeeFull && (
                                                    <div className="mt-60 pt-60 border-t border-zinc-100 flex flex-col items-center text-center space-y-14 relative">
                                                        <div className="absolute inset-x-0 bottom-0 h-[600px] bg-gradient-to-t from-white via-white/98 to-transparent pointer-events-none" />
                                                        <div className="relative z-20 space-y-10 pb-32">
                                                            <div className="w-24 h-24 bg-black text-white flex items-center justify-center mx-auto rounded-sm">
                                                                <Lock className="w-10 h-10 stroke-[1]" />
                                                            </div>
                                                            <div className="space-y-6">
                                                                <h3 className="text-4xl font-bold text-black tracking-tighter uppercase">Rào cản tri thức</h3>
                                                                <p className="text-[11px] font-bold text-zinc-300 leading-relaxed uppercase tracking-[0.3em] max-w-xl mx-auto">
                                                                    Bạn đã tiếp cận hết giới hạn xem trước cho phép. <br/>
                                                                    Mở khóa để khám phá toàn bộ {docData.pages_count} trang tri thức chuyên sâu.
                                                                </p>
                                                            </div>
                                                            <button 
                                                                onClick={handlePurchase}
                                                                className="h-24 px-20 bg-black text-white text-[12px] font-bold uppercase tracking-[0.5em] hover:bg-zinc-800 transition-all rounded-sm active:scale-95"
                                                            >
                                                                Sở hữu toàn bộ tri thức
                                                            </button>
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
                            <div className="bg-zinc-50/30 p-12 border border-zinc-100 rounded-sm">
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
