"use client";

import React, { useEffect, useState, useCallback } from "react";
import { 
  getSocialFeedAPI, 
  getSocialStoriesAPI, 
  getSocialRankingAPI, 
  createSocialPostAPI, 
  reactToPostAPI, 
  deleteSocialPostAPI, 
  uploadSocialMediaAPI,
  getTrendingDocumentsAPI
} from "@/app/lib/api";
import {
  Heart,
  MessageCircle,
  TrendingUp,
  Share2,
  PlusSquare,
  ArrowUp,
  Send,
  X,
  Bookmark,
  FileText,
  BarChart2,
  Trash2,
  Trophy,
  Edit3,
  Flag,
  Eye,
  Image as ImageIcon,
  Loader2,
  Pin,
  Flame,
  Lightbulb,
  MoreVertical,
  ChevronRight,
  Sparkles,
  Zap
} from "lucide-react";
import confetti from "canvas-confetti";
import { useAuth } from "@/app/contexts/AuthContext";
import { Notification } from "@/app/components/NotificationToast";

export default function FeedPage() {
  const { user: currentUser } = useAuth() as any;
  const [posts, setPosts] = useState<any[]>([]);
  const [stories, setStories] = useState<any[]>([]);
  const [ranking, setRanking] = useState<any[]>([]);
  const [documentSuggestions, setDocumentSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [content, setContent] = useState("");
  const [tab, setTab] = useState<"foryou" | "following">("foryou");
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const [mediaUrls, setMediaUrls] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [showExtras, setShowExtras] = useState(false);
  const [pollText1, setPollText1] = useState("");
  const [pollText2, setPollText2] = useState("");

  const [viewingStoryMode, setViewingStoryMode] = useState(false);
  const [activeStoryIndex, setActiveStoryIndex] = useState(0);

  const [expandedPostId, setExpandedPostId] = useState<string | null>(null);
  const [visible, setVisible] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [feedData, storiesData, rankingData, trendingData] = await Promise.all([
        getSocialFeedAPI(tab),
        getSocialStoriesAPI(),
        getSocialRankingAPI(),
        getTrendingDocumentsAPI()
      ]);

      setPosts(feedData.data || []);
      setStories(storiesData.data || []);
      setRanking(rankingData.data || []);
      setDocumentSuggestions(trendingData.data || []);
    } catch (err: any) {
      setNotification({ type: "error", text: "Không thể tải dữ liệu bảng tin." });
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [tab]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    try {
      const data = await uploadSocialMediaAPI(file);
      if (data.data?.url) {
        setMediaUrls((prev) => [...prev, data.data.url]);
      }
    } catch (err: any) {
      setNotification({ type: "error", text: "Tải phương tiện thất bại." });
    } finally {
      setIsUploading(false);
    }
  };

  const handleCreatePost = async () => {
    if (!content.trim() && mediaUrls.length === 0) return;
    try {
      await createSocialPostAPI({
        content,
        media_urls: mediaUrls,
        poll_options: [pollText1, pollText2].filter((p) => p.trim())
      });
      setContent("");
      setMediaUrls([]);
      setPollText1("");
      setPollText2("");
      setShowExtras(false);
      setNotification({ type: "success", text: "Đã chia sẻ trạng thái mới." });
      fetchData();
    } catch (err: any) {
      setNotification({ type: "error", text: err.message || "Không thể đăng bài viết." });
    }
  };

  const handleToggleLike = async (postId: string, reactionType: string = "like", event?: React.MouseEvent) => {
    try {
      await reactToPostAPI(postId, reactionType);
      if (event) {
        const rect = (event.target as HTMLElement).getBoundingClientRect();
        confetti({
          particleCount: 40,
          spread: 50,
          origin: { x: (rect.left + rect.width / 2) / window.innerWidth, y: rect.top / window.innerHeight },
          colors: ["#000000", "#71717a"],
        });
      }
      fetchData();
    } catch (err: any) {
      setNotification({ type: "error", text: "Thao tác tương tác thất bại." });
    }
  };

  const handleDeletePost = async (postId: string) => {
    try {
      await deleteSocialPostAPI(postId);
      setNotification({ type: "success", text: "Đã xóa bài viết." });
      fetchData();
    } catch (err: any) {
      setNotification({ type: "error", text: "Không thể xóa bài viết." });
    }
  };

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      {notification && (
        <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      <main className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div 
          className="lg:col-span-8 flex flex-col gap-10 transition-all duration-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="flex flex-col gap-6">
              <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">Bảng tin</h1>
              <nav className="flex gap-10 border-b border-zinc-100">
                {[
                  { id: "foryou", label: "DÀNH CHO BẠN" },
                  ...(currentUser ? [{ id: "following", label: "ĐANG THEO DÕI" }] : []),
                ].map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setTab(t.id as any)}
                    className={`pb-5 text-[11px] font-bold tracking-[0.2em] transition-all border-b-2 active:scale-95 ${
                      tab === t.id ? "border-black text-black" : "border-transparent text-zinc-300 hover:text-black"
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </nav>
          </div>

          {stories.length > 0 && (
            <div className="flex gap-4 overflow-x-auto pb-6 scrollbar-hide">
              {stories.map((story, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setActiveStoryIndex(idx);
                    setViewingStoryMode(true);
                  }}
                  className="w-24 h-40 bg-zinc-50 border border-zinc-100 shrink-0 relative overflow-hidden group transition-all active:scale-[0.98] rounded-sm"
                >
                  {story.media_url ? (
                    <img
                      src={story.media_url}
                      className="absolute inset-0 w-full h-full object-cover grayscale group-hover:grayscale-0 group-hover:scale-105 transition-all duration-1000 opacity-60"
                      alt=""
                    />
                  ) : (
                    <div
                      className="absolute inset-0 p-4 flex items-center justify-center text-center text-white text-[10px] font-bold leading-relaxed"
                      style={{ backgroundColor: story.background_color || "#000" }}
                    >
                      {story.text_content}
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent opacity-60" />
                  <div className="absolute top-3 left-3 w-8 h-8 border border-white/20 bg-zinc-800 overflow-hidden rounded-sm">
                    <img
                      src={story.user?.avatar_url || "/placeholder-user.png"}
                      className="w-full h-full object-cover"
                      alt=""
                    />
                  </div>
                  <span className="absolute bottom-3 left-3 text-[10px] font-bold text-white truncate w-18 text-left tracking-tight">
                    {story.user?.display_name || story.user?.name}
                  </span>
                </button>
              ))}
            </div>
          )}

          {currentUser && (
            <div className="bg-white border border-zinc-100 p-10 space-y-8 rounded-sm group hover:border-black transition-all duration-500">
              <div className="flex gap-6 items-start">
                <div className="w-14 h-14 bg-zinc-50 border border-zinc-100 flex shrink-0 items-center justify-center text-black font-bold text-xl rounded-sm">
                  {currentUser?.avatar_url ? (
                    <img src={currentUser.avatar_url} className="w-full h-full object-cover grayscale" alt="" />
                  ) : (
                    currentUser?.username?.[0]?.toUpperCase()
                  )}
                </div>
                <div className="flex-1">
                  <textarea
                    className="w-full bg-transparent outline-none text-black resize-none min-h-[80px] text-xl font-bold tracking-tight placeholder:text-zinc-100 mt-2"
                    placeholder="Bạn đang nghiên cứu điều gì"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                  />
                  {mediaUrls.length > 0 && (
                    <div className="grid grid-cols-2 gap-4 mt-6">
                      {mediaUrls.map((url, i) => (
                        <div key={i} className="relative aspect-video border border-zinc-100 group/media rounded-sm overflow-hidden">
                          <img src={url} className="w-full h-full object-cover grayscale hover:grayscale-0 transition-all duration-1000" alt="" />
                          <button
                            onClick={() => setMediaUrls((prev) => prev.filter((_, idx) => idx !== i))}
                            className="absolute top-3 right-3 w-8 h-8 bg-black text-white flex items-center justify-center opacity-0 group-hover/media:opacity-100 transition-all active:scale-[0.98] rounded-sm"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between pt-8 border-t border-zinc-50">
                <div className="flex gap-4">
                  <label className="w-12 h-12 flex items-center justify-center border border-zinc-100 text-zinc-300 hover:text-black hover:border-black transition-all cursor-pointer rounded-sm">
                    <ImageIcon className="w-5 h-5" />
                    <input type="file" className="hidden" onChange={handleFileUpload} />
                  </label>
                  <button
                    onClick={() => setShowExtras(!showExtras)}
                    className={`w-12 h-12 flex items-center justify-center border transition-all rounded-sm ${
                      showExtras ? "bg-black text-white border-black" : "border-zinc-100 text-zinc-300 hover:text-black"
                    }`}
                  >
                    <BarChart2 className="w-5 h-5" />
                  </button>
                </div>
                <button
                  onClick={handleCreatePost}
                  disabled={!content.trim() && mediaUrls.length === 0}
                  className="bg-black text-white h-14 px-12 text-[11px] font-bold uppercase tracking-[0.2em] hover:bg-zinc-800 transition-all active:scale-[0.98] disabled:opacity-50 rounded-sm"
                >
                  Chia sẻ ngay
                </button>
              </div>

              {showExtras && (
                <div className="p-8 bg-zinc-50 border border-zinc-100 space-y-6 animate-in slide-in-from-top-4 duration-300 rounded-sm">
                  <div className="flex items-center gap-3 text-black">
                    <BarChart2 className="w-4 h-4" />
                    <h4 className="text-[11px] font-bold uppercase tracking-widest">Bình chọn cộng đồng</h4>
                  </div>
                  <div className="grid gap-4">
                    <input
                      className="h-14 bg-white border border-zinc-100 px-6 text-sm font-bold focus:border-black outline-none transition-all rounded-sm"
                      placeholder="Lựa chọn 1"
                      value={pollText1}
                      onChange={(e) => setPollText1(e.target.value)}
                    />
                    <input
                      className="h-14 bg-white border border-zinc-100 px-6 text-sm font-bold focus:border-black outline-none transition-all rounded-sm"
                      placeholder="Lựa chọn 2"
                      value={pollText2}
                      onChange={(e) => setPollText2(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="flex flex-col gap-8">
            {loading ? (
              <div className="py-24 flex flex-col items-center gap-6">
                <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
                <span className="text-[11px] font-bold text-zinc-200 uppercase tracking-[0.3em]">Hệ thống đang đồng bộ</span>
              </div>
            ) : posts.length === 0 ? (
              <div className="py-40 text-center border border-dashed border-zinc-100 rounded-sm">
                 <div className="flex flex-col items-center gap-6 text-zinc-100">
                    <Zap className="w-16 h-16 stroke-[1]" />
                    <span className="text-[11px] font-bold uppercase tracking-[0.2em]">Bảng tin hiện chưa có hoạt động nào</span>
                 </div>
              </div>
            ) : (
              posts.map((post) => (
                <div
                  key={post.id}
                  className="bg-white border border-zinc-100 p-10 hover:border-black transition-all duration-300 group/post rounded-sm"
                >
                  <div className="flex items-center justify-between mb-10">
                    <div className="flex items-center gap-5">
                      <div className="w-14 h-14 bg-zinc-50 border border-zinc-100 flex items-center justify-center font-bold text-black overflow-hidden group-hover/post:border-black transition-all shrink-0 rounded-sm">
                        {post.user?.avatar_url ? (
                          <img src={post.user.avatar_url} className="w-full h-full object-cover grayscale" alt="" />
                        ) : (
                          <span className="text-xl">{(post.user?.display_name || post.user?.username)?.[0]?.toUpperCase()}</span>
                        )}
                      </div>
                      <div className="space-y-1">
                        <h4 className="text-base font-bold text-black hover:underline cursor-pointer tracking-tight">
                          {post.user?.display_name || post.user?.username || "Người dùng DocLib"}
                        </h4>
                        <div className="flex items-center gap-3">
                            <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                                {post.created_at ? new Date(post.created_at).toLocaleDateString("vi-VN") : "Vừa xong"}
                            </span>
                            <div className="w-1 h-1 bg-zinc-100 rounded-full" />
                            <span className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest">Global Activity</span>
                        </div>
                      </div>
                    </div>
                    {currentUser && currentUser._id === post.author_id && (
                      <button
                        onClick={() => handleDeletePost(post.id)}
                        className="w-10 h-10 border border-zinc-50 text-zinc-100 hover:text-black hover:border-black transition-all active:scale-[0.98] flex items-center justify-center rounded-sm"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  <p className="text-2xl font-bold text-black leading-tight tracking-tighter mb-10 selection:bg-black selection:text-white">
                    {post.content}
                  </p>

                  {post.media_urls && post.media_urls.length > 0 && (
                    <div className="grid grid-cols-1 gap-6 mb-10">
                      {post.media_urls.map((url: string, i: number) => (
                        <div key={i} className="bg-zinc-50 border border-zinc-100 p-2 overflow-hidden rounded-sm">
                          <img src={url} className="w-full h-full object-cover grayscale hover:grayscale-0 transition-all duration-1000" alt="" />
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center gap-10 pt-8 border-t border-zinc-50">
                    <button
                      onClick={(e) => currentUser && handleToggleLike(post.id, "like", e)}
                      disabled={!currentUser}
                      className={`flex items-center gap-3 text-[11px] font-bold transition-all active:scale-[0.98] ${
                        post.is_liked ? "text-black" : "text-zinc-300 hover:text-black"
                      } ${!currentUser ? "cursor-default opacity-50" : ""}`}
                    >
                      <Heart className={`w-4.5 h-4.5 ${post.is_liked ? "fill-black" : ""}`} />
                      {post.likes_count || 0}
                    </button>
                    <button
                      onClick={() => setExpandedPostId(expandedPostId === post.id ? null : post.id)}
                      className="flex items-center gap-3 text-[11px] font-bold text-zinc-300 hover:text-black transition-all active:scale-[0.98]"
                    >
                      <MessageCircle className="w-4.5 h-4.5" />
                      {post.comments?.length || 0}
                    </button>
                    <button className="flex items-center gap-3 text-[11px] font-bold text-zinc-100 hover:text-black transition-all active:scale-[0.98]">
                      <Share2 className="w-4.5 h-4.5" />
                    </button>
                  </div>

                  {expandedPostId === post.id && (
                    <div className="mt-10 p-10 bg-zinc-50 border border-zinc-100 space-y-10 animate-in slide-in-from-top-4 duration-300 rounded-sm">
                      {post.comments?.length > 0 ? (
                        <div className="space-y-8">
                          {post.comments.map((c: any, i: number) => (
                            <div key={i} className="flex gap-5 items-start">
                              <div className="w-10 h-10 bg-white border border-zinc-100 flex shrink-0 items-center justify-center font-bold text-[11px] uppercase rounded-sm">
                                {c.user_name?.[0]}
                              </div>
                              <div className="space-y-1.5 flex-1">
                                <p className="text-[11px] font-bold text-black uppercase tracking-widest">{c.user_name}</p>
                                <p className="text-[14px] text-zinc-500 leading-relaxed font-medium">{c.text || c.content}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-6">
                            <p className="text-[11px] font-bold text-zinc-200 uppercase tracking-widest italic">Hiện chưa có thảo luận nào cho nội dung này</p>
                        </div>
                      )}
                      
                      {currentUser ? (
                        <div className="flex gap-4 border-t border-zinc-100 pt-10">
                          <input
                            className="flex-1 h-14 bg-white border border-zinc-100 px-6 text-sm font-bold focus:border-black outline-none transition-all rounded-sm"
                            placeholder="Viết phản hồi của bạn"
                          />
                          <button className="w-14 h-14 bg-black text-white flex items-center justify-center active:scale-[0.98] transition-all rounded-sm group">
                            <Send className="w-5 h-5 group-hover:translate-x-1 group-hover:-translate-y-1 transition-all" />
                          </button>
                        </div>
                      ) : (
                        <div className="text-center pt-6 border-t border-zinc-100">
                             <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-[0.2em]">Đăng nhập để tham gia thảo luận</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        <aside 
          className="hidden lg:col-span-4 lg:flex flex-col gap-12 sticky top-12 self-start transition-all duration-300 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {currentUser && (
            <div className="bg-black text-white p-10 space-y-8 rounded-sm text-center">
              <span className="text-[10px] font-bold uppercase tracking-[0.3em] opacity-40">Tài khoản tri thức</span>
              <div className="space-y-1">
                  <h3 className="text-5xl font-bold tracking-tighter">
                    {currentUser.wallet_balance?.toLocaleString("vi-VN") || 0}
                  </h3>
                  <span className="text-[11px] font-black uppercase tracking-[0.4em] opacity-20">DocLib Units</span>
              </div>
              <button
                onClick={() => (window.location.href = "/profile")}
                className="w-full h-14 border border-white/10 text-[11px] font-bold uppercase tracking-[0.2em] hover:bg-white hover:text-black transition-all rounded-sm"
              >
                Quản lý ví cá nhân
              </button>
            </div>
          )}

          <div className="bg-white border border-zinc-100 p-8 space-y-10 rounded-sm">
            <div className="flex items-center justify-between border-b border-zinc-50 pb-6">
                <h3 className="text-[11px] font-bold text-black uppercase tracking-[0.2em] flex items-center gap-3">
                <Trophy className="w-4.5 h-4.5" /> Vinh danh tuần
                </h3>
                <Sparkles className="w-4 h-4 text-zinc-100" />
            </div>
            <div className="space-y-6">
              {ranking.map((r, i) => (
                <div key={i} className="flex items-center gap-5 group cursor-pointer">
                  <div className="w-10 h-10 border border-zinc-50 flex items-center justify-center font-bold text-[11px] group-hover:bg-black group-hover:text-white transition-all duration-300 shrink-0 rounded-sm">
                    {i + 1}
                  </div>
                  <div className="min-w-0 space-y-0.5">
                    <h4 className="text-[14px] font-bold text-black truncate tracking-tight">{r.display_name || "Ẩn danh"}</h4>
                    <p className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest">{r.total_dl || 0} DL</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white border border-zinc-100 p-8 space-y-10 rounded-sm">
            <div className="flex items-center justify-between border-b border-zinc-50 pb-6">
                <h3 className="text-[11px] font-bold text-black uppercase tracking-[0.2em] flex items-center gap-3">
                <Flame className="w-4.5 h-4.5" /> Xu hướng tri thức
                </h3>
                <TrendingUp className="w-4 h-4 text-zinc-100" />
            </div>
            <div className="space-y-8">
              {documentSuggestions.slice(0, 4).map((doc, i) => (
                <div key={i} className="flex gap-5 group cursor-pointer">
                  <div className="w-12 h-16 bg-zinc-50 border border-zinc-100 shrink-0 group-hover:border-black transition-all duration-300 flex items-center justify-center rounded-sm">
                    <FileText className="w-6 h-6 text-zinc-100 group-hover:text-black transition-all" />
                  </div>
                  <div className="min-w-0 flex flex-col justify-center space-y-1">
                    <h4 className="text-[14px] font-bold text-black truncate tracking-tighter group-hover:underline">{doc.title}</h4>
                    <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2">
                        {doc.mentions || 0} Đề cập <ChevronRight className="w-3 h-3" />
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </main>

      {viewingStoryMode && activeStoryIndex >= 0 && stories[activeStoryIndex] && (
        <div className="fixed inset-0 z-[2000] bg-black/95 flex justify-center items-center animate-in fade-in duration-500 backdrop-blur-xl">
          <button
            onClick={() => setViewingStoryMode(false)}
            className="absolute top-10 right-10 text-white/20 hover:text-white transition-all z-50 active:scale-[0.98]"
          >
            <X className="w-10 h-10" />
          </button>
          <div
            className="w-full max-w-md aspect-[9/16] relative overflow-hidden bg-zinc-900 animate-in zoom-in-95 duration-500 rounded-sm border border-white/5 shadow-2xl"
            style={{ backgroundColor: stories[activeStoryIndex].background_color }}
          >
            {stories[activeStoryIndex].media_url && (
              <img src={stories[activeStoryIndex].media_url} className="absolute inset-0 w-full h-full object-cover" alt="" />
            )}
            <div className="absolute inset-0 p-12 flex items-center justify-center text-center">
              <h2 className="text-4xl font-black tracking-tighter text-white leading-tight">
                {stories[activeStoryIndex].text_content}
              </h2>
            </div>
            <div className="absolute top-10 left-10 flex items-center gap-4">
              <div className="w-12 h-12 bg-white/20 border border-white/20 overflow-hidden rounded-sm">
                <img src={stories[activeStoryIndex].user?.avatar_url} className="w-full h-full object-cover" alt="" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-bold text-white tracking-tight">{stories[activeStoryIndex].user?.display_name || stories[activeStoryIndex].user?.name}</span>
                <span className="text-[9px] font-bold text-white/40 uppercase tracking-widest">Story Activity</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}