"use client";

import React, { useEffect, useState, useCallback } from "react";
import { getToken, API_URL } from "@/app/lib/api";
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
} from "lucide-react";
import confetti from "canvas-confetti";
import { useAuth } from "@/app/contexts/AuthContext";
import { useToast } from "@/app/contexts/ToastContext";

export default function FeedPage() {
  const { user: currentUser } = useAuth() as any;
  const [posts, setPosts] = useState<any[]>([]);
  const [stories, setStories] = useState<any[]>([]);
  const [ranking, setRanking] = useState<any[]>([]);
  const [documentSuggestions, setDocumentSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [content, setContent] = useState("");
  const [tab, setTab] = useState<"foryou" | "following">("foryou");
  const [walletBalance, setWalletBalance] = useState<number>(0);
  const { showToast } = useToast();

  // Post creation state
  const [mediaUrls, setMediaUrls] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [showExtras, setShowExtras] = useState(false);
  const [pollText1, setPollText1] = useState("");
  const [pollText2, setPollText2] = useState("");
  const [attachedDocumentId, setAttachedDocumentId] = useState<string | null>(null);

  // Story viewing state
  const [viewingStoryMode, setViewingStoryMode] = useState(false);
  const [activeStoryIndex, setActiveStoryIndex] = useState(0);
  const [storyProgress, setStoryProgress] = useState(0);

  // UI state
  const [expandedPostId, setExpandedPostId] = useState<string | null>(null);
  const [visible, setVisible] = useState(false);

  const fetchFeed = useCallback(async (isRefresh = false) => {
    if (isRefresh) setLoading(true);
    try {
      const headers: any = {};
      const token = getToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const [postsRes, storiesRes, rankingRes, docsRes] = await Promise.all([
        fetch(`${API_URL}/social/feed?tab=${tab}`, { headers }),
        fetch(`${API_URL}/social/stories`, { headers }),
        fetch(`${API_URL}/social/ranking`, { headers }),
        fetch(`${API_URL}/documents/trending`, { headers }),
      ]);

      if (postsRes.ok) {
        const data = await postsRes.json();
        setPosts(data.data || []);
      }
      if (storiesRes.ok) {
        const data = await storiesRes.json();
        setStories(data.data || []);
      }
      if (rankingRes.ok) {
        const data = await rankingRes.json();
        setRanking(data.data || []);
      }
      if (docsRes.ok) {
        const data = await docsRes.json();
        setDocumentSuggestions(data.data || []);
      }
    } catch (err) {
      console.error("Lỗi tải bảng tin:", err);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    fetchFeed();
    requestAnimationFrame(() => setVisible(true));
    if (currentUser) {
      setWalletBalance(currentUser.wallet_balance || 0);
    }
  }, [fetchFeed, currentUser]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API_URL}/social/upload-media`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        body: formData,
      });
      const data = await res.json();
      if (data.data?.url) {
        setMediaUrls((prev) => [...prev, data.data.url]);
      }
    } catch (e) {
      showToast("Tải phương tiện thất bại", "error");
    } finally {
      setIsUploading(false);
    }
  };

  const createPost = async () => {
    if (!content.trim() && mediaUrls.length === 0) return;
    try {
      const res = await fetch(`${API_URL}/social/posts`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          content,
          media_urls: mediaUrls,
          poll_options: [pollText1, pollText2].filter((p) => p.trim()),
          attached_document_id: attachedDocumentId || null,
        }),
      });
      if (res.ok) {
        setContent("");
        setMediaUrls([]);
        setPollText1("");
        setPollText2("");
        setShowExtras(false);
        showToast("Đã chia sẻ thành công!", "success");
        fetchFeed(true);
      }
    } catch (e) {
      showToast("Không thể đăng tải nội dung lúc này", "error");
    }
  };

  const toggleLike = async (postId: string, reactionType: string = "like", event?: React.MouseEvent) => {
    try {
      const res = await fetch(`${API_URL}/social/posts/${postId}/like?reaction_type=${reactionType}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        if (event) {
          const rect = (event.target as HTMLElement).getBoundingClientRect();
          confetti({
            particleCount: 40,
            spread: 50,
            origin: { x: (rect.left + rect.width / 2) / window.innerWidth, y: rect.top / window.innerHeight },
            colors: ["#000000", "#71717a"],
          });
        }
        fetchFeed(true);
      }
    } catch (err: any) {
      console.error("Lỗi tương tác bài viết:", err);
    }
  };

  const deletePost = async (postId: string) => {
    try {
      const res = await fetch(`${API_URL}/social/posts/${postId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        showToast("Đã xóa bài viết", "success");
        fetchFeed(true);
      }
    } catch (e) {
      showToast("Xóa bài viết thất bại", "error");
    }
  };

  const handleStoryNext = () => {
    if (activeStoryIndex < stories.length - 1) {
      setActiveStoryIndex(activeStoryIndex + 1);
      setStoryProgress(0);
    } else {
      setViewingStoryMode(false);
    }
  };

  const handleStoryPrev = () => {
    if (activeStoryIndex > 0) {
      setActiveStoryIndex(activeStoryIndex - 1);
      setStoryProgress(0);
    }
  };

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-8 font-sans text-black selection:bg-black selection:text-white">
      <main className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        <div 
          className="lg:col-span-8 flex flex-col gap-8 transition-all duration-700"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
        >
          <nav className="flex gap-8 border-b border-zinc-100 pb-0.5">
            {[
              { id: "foryou", label: "DÀNH CHO BẠN" },
              ...(currentUser ? [{ id: "following", label: "ĐANG THEO DÕI" }] : []),
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id as any)}
                className={`pb-4 text-[10px] font-bold tracking-[0.2em] transition-all border-b-2 active:scale-95 ${
                  tab === t.id ? "border-black text-black" : "border-transparent text-zinc-300 hover:text-black"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>

          {stories.length > 0 && (
            <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
              {stories.map((story, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setActiveStoryIndex(idx);
                    setViewingStoryMode(true);
                  }}
                  className="w-20 h-32 bg-zinc-50 border border-zinc-100 shrink-0 relative overflow-hidden group transition-all active:scale-95"
                >
                  {story.media_url ? (
                    <img
                      src={story.media_url}
                      className="absolute inset-0 w-full h-full object-cover grayscale group-hover:grayscale-0 group-hover:scale-105 transition-all duration-700 opacity-60"
                      alt=""
                    />
                  ) : (
                    <div
                      className="absolute inset-0 p-3 flex items-center justify-center text-center text-white text-[9px] font-bold"
                      style={{ backgroundColor: story.background_color || "#000" }}
                    >
                      {story.text_content}
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                  <div className="absolute top-2 left-2 w-7 h-7 border border-white/20 bg-zinc-800 overflow-hidden">
                    <img
                      src={story.user?.avatar_url || "/placeholder-user.png"}
                      className="w-full h-full object-cover"
                      alt=""
                    />
                  </div>
                  <span className="absolute bottom-2 left-2 text-[9px] font-bold text-white truncate w-16 text-left">
                    {story.user?.display_name || story.user?.name}
                  </span>
                </button>
              ))}
            </div>
          )}

          {currentUser && (
            <div className="bg-white border border-zinc-100 p-6 space-y-6 group hover:border-zinc-200 transition-all duration-500">
              <div className="flex gap-5 items-start">
                <div className="w-12 h-12 bg-zinc-50 border border-zinc-100 flex shrink-0 items-center justify-center text-black font-bold text-lg relative group">
                  {currentUser?.avatar_url ? (
                    <img src={currentUser.avatar_url} className="w-full h-full object-cover grayscale" alt="" />
                  ) : (
                    currentUser?.username?.[0]?.toUpperCase()
                  )}
                </div>
                <div className="flex-1">
                  <textarea
                    className="w-full bg-transparent outline-none text-black resize-none min-h-[60px] text-lg font-bold tracking-tight placeholder:text-zinc-100 mt-1"
                    placeholder=""
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                  />
                  {mediaUrls.length > 0 && (
                    <div className="grid grid-cols-2 gap-3 mt-4">
                      {mediaUrls.map((url, i) => (
                        <div key={i} className="relative aspect-video border border-zinc-100 group/media">
                          <img src={url} className="w-full h-full object-cover" alt="" />
                          <button
                            onClick={() => setMediaUrls((prev) => prev.filter((_, idx) => idx !== i))}
                            className="absolute top-2 right-2 w-7 h-7 bg-black text-white flex items-center justify-center opacity-0 group-hover/media:opacity-100 transition-all active:scale-95"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between pt-6 border-t border-zinc-50">
                <div className="flex gap-3">
                  <label className="p-2.5 hover:bg-zinc-50 border border-zinc-100 text-zinc-300 hover:text-black transition-all cursor-pointer">
                    <ImageIcon className="w-4 h-4" />
                    <input type="file" className="hidden" onChange={handleFileUpload} />
                  </label>
                  <button
                    onClick={() => setShowExtras(!showExtras)}
                    className={`p-2.5 border transition-all ${
                      showExtras ? "bg-black text-white border-black" : "border-zinc-100 text-zinc-300 hover:text-black"
                    }`}
                  >
                    <BarChart2 className="w-4 h-4" />
                  </button>
                </div>
                <button
                  onClick={createPost}
                  disabled={!content.trim() && mediaUrls.length === 0}
                  className="bg-black text-white h-12 px-10 text-sm font-bold hover:bg-zinc-800 transition-all active:scale-[0.98] disabled:opacity-50"
                >
                  Đăng tải ngay
                </button>
              </div>

              {showExtras && (
                <div className="p-6 bg-zinc-50/50 border border-zinc-100 space-y-4 animate-in slide-in-from-top-4">
                  <h4 className="text-[10px] font-bold text-black uppercase tracking-wider">Bình chọn tri thức</h4>
                  <div className="grid gap-3">
                    <input
                      className="h-12 bg-white border border-zinc-100 px-5 text-sm font-bold focus:border-black outline-none transition-all"
                      placeholder=""
                      value={pollText1}
                      onChange={(e) => setPollText1(e.target.value)}
                    />
                    <input
                      className="h-12 bg-white border border-zinc-100 px-5 text-sm font-bold focus:border-black outline-none transition-all"
                      placeholder=""
                      value={pollText2}
                      onChange={(e) => setPollText2(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="flex flex-col gap-6">
            {loading ? (
              <div className="py-20 flex flex-col items-center gap-4">
                <Loader2 className="w-8 h-8 animate-spin text-zinc-200" />
                <span className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Đang tải bảng tin</span>
              </div>
            ) : posts.length === 0 ? (
              <div className="py-32 text-center border border-dashed border-zinc-100 text-[11px] font-bold text-zinc-300 uppercase tracking-[0.2em]">
                Không có hoạt động mới nào
              </div>
            ) : (
              posts.map((post) => (
                <div
                  key={post.id}
                  className="bg-white border border-zinc-100 p-8 hover:border-black transition-all duration-700 group/post"
                >
                  <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-zinc-50 border border-zinc-100 flex items-center justify-center font-bold text-black overflow-hidden group-hover/post:border-black transition-all shrink-0">
                        {post.user?.avatar_url ? (
                          <img src={post.user.avatar_url} className="w-full h-full object-cover grayscale" alt="" />
                        ) : (
                          <span className="text-lg">{(post.user?.display_name || post.user?.username)?.[0]?.toUpperCase()}</span>
                        )}
                      </div>
                      <div className="min-w-0">
                        <h4 className="text-sm font-bold text-black hover:underline cursor-pointer truncate">
                          {post.user?.display_name || post.user?.username || "Người dùng DocLib"}
                        </h4>
                        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mt-0.5">
                          {post.created_at ? new Date(post.created_at).toLocaleDateString("vi-VN") : "Vừa xong"}
                        </p>
                      </div>
                    </div>
                    {currentUser && currentUser._id === post.author_id && (
                      <button
                        onClick={() => deletePost(post.id)}
                        className="p-2.5 text-zinc-200 hover:text-black hover:bg-zinc-50 transition-all active:scale-90"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  <p className="text-lg font-bold text-black leading-tight tracking-tight mb-8 selection:bg-black selection:text-white">
                    {post.content}
                  </p>

                  {post.media_urls && post.media_urls.length > 0 && (
                    <div className="grid grid-cols-1 gap-4 mb-8">
                      {post.media_urls.map((url: string, i: number) => (
                        <div key={i} className="bg-zinc-50 border border-zinc-100 p-1.5 overflow-hidden">
                          <img src={url} className="w-full h-full object-cover grayscale hover:grayscale-0 transition-all duration-1000" alt="" />
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center gap-8 pt-6 border-t border-zinc-50">
                    <button
                      onClick={(e) => currentUser && toggleLike(post.id, "like", e)}
                      disabled={!currentUser}
                      className={`flex items-center gap-2.5 text-[11px] font-bold transition-all active:scale-90 ${
                        post.is_liked ? "text-black" : "text-zinc-300 hover:text-black"
                      } ${!currentUser ? "cursor-default opacity-50" : ""}`}
                    >
                      <Heart className={`w-4 h-4 ${post.is_liked ? "fill-black" : ""}`} />
                      {post.likes_count || 0}
                    </button>
                    <button
                      onClick={() => setExpandedPostId(expandedPostId === post.id ? null : post.id)}
                      className="flex items-center gap-2.5 text-[11px] font-bold text-zinc-300 hover:text-black transition-all active:scale-90"
                    >
                      <MessageCircle className="w-4 h-4" />
                      {post.comments?.length || 0}
                    </button>
                  </div>

                  {expandedPostId === post.id && (
                    <div className="mt-8 p-6 bg-zinc-50/50 border border-zinc-100 space-y-8 animate-in slide-in-from-top-4 duration-500">
                      {post.comments?.length > 0 ? (
                        <div className="space-y-5">
                          {post.comments.map((c: any, i: number) => (
                            <div key={i} className="flex gap-3 items-start">
                              <div className="w-7 h-7 bg-zinc-50 border border-zinc-100 flex shrink-0 items-center justify-center font-bold text-[9px] uppercase">
                                {c.user_name?.[0]}
                              </div>
                              <div className="flex-1 space-y-0.5">
                                <p className="text-[10px] font-bold text-black">{c.user_name}</p>
                                <p className="text-[12px] text-zinc-500 leading-relaxed font-medium">{c.text || c.content}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-[10px] font-bold text-zinc-300 italic">Hiện chưa có thảo luận nào</p>
                      )}
                      
                      {currentUser ? (
                        <div className="flex gap-3">
                          <input
                            className="flex-1 h-11 bg-white border border-zinc-100 px-5 text-sm font-bold focus:border-black outline-none transition-all"
                            placeholder=""
                          />
                          <button className="w-11 h-11 bg-black text-white flex items-center justify-center active:scale-95 transition-all">
                            <Send className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <p className="text-[10px] font-bold text-zinc-400 text-center">Vui lòng đăng nhập để thảo luận</p>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        <aside 
          className="hidden lg:col-span-4 lg:flex flex-col gap-10 sticky top-10 self-start transition-all duration-700 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {currentUser && (
            <div className="bg-white border border-zinc-100 p-8 space-y-6 text-center hover:border-black transition-all duration-500">
              <span className="text-[10px] font-bold text-black uppercase tracking-widest">Tài khoản tri thức</span>
              <h3 className="text-4xl font-bold text-black tracking-tighter">
                {walletBalance.toLocaleString("vi-VN")} <span className="text-xs font-bold text-zinc-200">DL</span>
              </h3>
              <button
                onClick={() => (window.location.href = "/profile")}
                className="w-full h-12 border border-zinc-100 text-[10px] font-bold text-black uppercase tracking-wider hover:border-black hover:bg-black hover:text-white transition-all"
              >
                Ví cá nhân
              </button>
            </div>
          )}

          <div className="bg-white border border-zinc-100 p-6 space-y-8">
            <h3 className="text-[10px] font-bold text-black flex items-center gap-3 uppercase tracking-widest">
              <Trophy className="w-4 h-4 text-black" /> Vinh danh tuần
            </h3>
            <div className="space-y-4">
              {ranking.map((r, i) => (
                <div key={i} className="flex items-center gap-4 group">
                  <div className="w-8 h-8 bg-zinc-50 border border-zinc-100 flex items-center justify-center font-bold text-[10px] group-hover:bg-black group-hover:text-white transition-all duration-500 shrink-0">
                    0{i + 1}
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-[13px] font-bold text-black truncate">{r.display_name || "Ẩn danh"}</h4>
                    <p className="text-[10px] font-bold text-zinc-300">{r.total_dl || 0} DL</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white border border-zinc-100 p-6 space-y-8">
            <h3 className="text-[10px] font-bold text-black flex items-center gap-3 uppercase tracking-widest">
              <FileText className="w-4 h-4 text-black" /> Thịnh hành
            </h3>
            <div className="space-y-6">
              {documentSuggestions.slice(0, 3).map((doc, i) => (
                <div key={i} className="flex gap-4 group cursor-pointer">
                  <div className="w-10 h-14 bg-zinc-50 border border-zinc-100 shrink-0 group-hover:border-black transition-all duration-500 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-zinc-200" />
                  </div>
                  <div className="min-w-0 flex flex-col justify-center">
                    <h4 className="text-[13px] font-bold text-black truncate tracking-tight">{doc.title}</h4>
                    <p className="text-[10px] font-bold text-zinc-400 mt-0.5">{doc.mentions || 0} đề cập</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </main>

      {viewingStoryMode && activeStoryIndex >= 0 && stories[activeStoryIndex] && (
        <div className="fixed inset-0 z-[2000] bg-black flex justify-center items-center animate-in fade-in duration-500">
          <button
            onClick={() => setViewingStoryMode(false)}
            className="absolute top-8 right-8 text-white/40 hover:text-white transition-all z-50 active:scale-90"
          >
            <X className="w-8 h-8" />
          </button>
          <div
            className="w-full max-w-md aspect-[9/16] relative overflow-hidden bg-zinc-900 animate-in zoom-in-95 duration-500"
            style={{ backgroundColor: stories[activeStoryIndex].background_color }}
          >
            {stories[activeStoryIndex].media_url && (
              <img src={stories[activeStoryIndex].media_url} className="absolute inset-0 w-full h-full object-cover" alt="" />
            )}
            <div className="absolute inset-0 p-10 flex items-center justify-center text-center">
              <h2 className="text-3xl font-bold tracking-tighter text-white">
                {stories[activeStoryIndex].text_content}
              </h2>
            </div>
            <div className="absolute top-8 left-8 flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 border border-white/20 overflow-hidden">
                <img src={stories[activeStoryIndex].user?.avatar_url} className="w-full h-full object-cover" alt="" />
              </div>
              <span className="text-sm font-bold text-white tracking-tight">{stories[activeStoryIndex].user?.display_name || stories[activeStoryIndex].user?.name}</span>
            </div>
            <div className="absolute inset-0 flex z-10">
              <div className="flex-1 cursor-pointer" onClick={handleStoryPrev} />
              <div className="flex-1 cursor-pointer" onClick={handleStoryNext} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}