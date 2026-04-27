"use client";

import React, { useEffect, useState, useCallback } from "react";
import AppShell from "@/app/components/AppShell";
import Link from "next/link";
import { getToken } from "@/app/lib/api";
import { Heart, MessageCircle, Globe, Sparkles, Users, Lock, Share2, PlusSquare, ArrowUp, Send, CheckCircle, XCircle, X, Bookmark, BookText, BarChart2, Trash2, Trophy, EyeOff, Edit3, Flag, Eye, Image as ImageIcon, Quote, PenTool, Book, FileText, HelpCircle, AtSign, Pin, Archive, Link as LinkIcon, Plus, Lightbulb, Flame, Smile, Coins, TrendingUp, Hash, ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import confetti from "canvas-confetti";
import { useAuth } from "@/app/contexts/AuthContext";

function ToastContainer({ toasts, removeToast }: { toasts: any[], removeToast: (id: string) => void }) {
  return (
    <div className="fixed bottom-4 left-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div key={t.id} className={`flex items-center gap-3 px-5 py-4 rounded-none border text-sm font-bold transition-all animate-in slide-in-from-left-8 ${t.type === 'success' ? 'bg-zinc-900 text-white border-zinc-800' :
            t.type === 'error' ? 'bg-zinc-950 text-white border-zinc-800' :
              'bg-white text-zinc-900 border-zinc-100'
          }`}>
          <p>{t.message}</p>
          <button onClick={() => removeToast(t.id)} className="ml-auto opacity-50 hover:opacity-100 transition-opacity">
             <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}

export default function Feed() {
  const [posts, setPosts] = useState<any[]>([]);
  const [stories, setStories] = useState<any[]>([]);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [trendingTags, setTrendingTags] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [content, setContent] = useState("");
  const [pollText1, setPollText1] = useState("");
  const [pollText2, setPollText2] = useState("");
  const [isPremium, setIsPremium] = useState(false);
  const [price, setPrice] = useState(0);
  const [readProgress, setReadProgress] = useState(0);
  const [attachedDocumentId, setAttachedDocumentId] = useState("");
  const [attachedDocumentTitle, setAttachedDocumentTitle] = useState("");
  const [mediaUrls, setMediaUrls] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [showExtras, setShowExtras] = useState(false);
  const [commentPrivacy, setCommentPrivacy] = useState("public");
  const [scheduledAt, setScheduledAt] = useState<string>("");
  const [expandedComments, setExpandedComments] = useState<string | null>(null);
  const [viewingStoryMode, setViewingStoryMode] = useState(false);
  const [activeStoryIndex, setActiveStoryIndex] = useState(-1);
  const [storyProgress, setStoryProgress] = useState(0);
  const [translationModal, setTranslationModal] = useState<{ text: string } | null>(null);
  const [showStoryArchive, setShowStoryArchive] = useState(false);
  const [archivedStories, setArchivedStories] = useState<any[]>([]);
  const [storyViewers, setStoryViewers] = useState<any[]>([]);
  const [showViewerList, setShowViewerList] = useState(false);
  const [isFetchingViewers, setIsFetchingViewers] = useState(false);
  const [filter, setFilter] = useState<"recent" | "trending">("recent");
  const [showLinkInput, setShowLinkInput] = useState(false);
  const [showMentionInput, setShowMentionInput] = useState(false);

  useEffect(() => {
    const savedDraft = localStorage.getItem("doclib_feed_draft");
    if (savedDraft) setContent(savedDraft);
  }, []);

  const [documentSuggestions, setDocumentSuggestions] = useState<any[]>([]);
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  const handleStoryNext = () => {
    if (activeStoryIndex < stories.length - 1) { setActiveStoryIndex(activeStoryIndex + 1); setStoryProgress(0); }
    else { setViewingStoryMode(false); setStoryProgress(0); }
  };

  const handleStoryPrev = () => {
    if (activeStoryIndex > 0) { setActiveStoryIndex(activeStoryIndex - 1); setStoryProgress(0); }
    else setStoryProgress(0);
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (viewingStoryMode && activeStoryIndex >= 0) {
      interval = setInterval(() => {
        setStoryProgress(prev => {
          if (prev >= 100) return 100;
          return prev + (100 / (15000 / 100)); 
        });
      }, 100);
    }
    return () => { if (interval) clearInterval(interval); }
  }, [viewingStoryMode, activeStoryIndex]);

  useEffect(() => {
    if (storyProgress >= 100 && viewingStoryMode) {
      handleStoryNext();
    }
  }, [storyProgress, viewingStoryMode]);

  useEffect(() => {
    if (viewingStoryMode && activeStoryIndex >= 0 && stories[activeStoryIndex]) {
      const storyId = stories[activeStoryIndex].id || stories[activeStoryIndex]._id;
      if (storyId) {
        fetch(`${API_URL}/social/stories/${storyId}/view`, {
          method: "POST", 
          headers: { 'Authorization': `Bearer ${getToken()}` }
        }).catch(e => console.error("Error viewing story:", e));
      }
    }
  }, [viewingStoryMode, activeStoryIndex]);

  const reactToStory = async (storyId: string) => {
    try {
      await fetch(`${API_URL}/social/stories/${storyId}/react?reaction_type=heart`, {
        method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      showToast("Đã phản hồi tin", "success");
    } catch(e) { console.error("Reaction err:", e) }
  };

  const fetchStoryViewers = async (storyId: string) => {
    setIsFetchingViewers(true);
    try {
      const res = await fetch(`${API_URL}/social/stories/${storyId}/viewers`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (res.ok) {
        const data = await res.json();
        setStoryViewers(data.viewers || []);
      }
    } catch(e) { console.error("Viewer fetch err:", e); } finally {
      setIsFetchingViewers(false);
    }
  };

  const votePoll = async (storyId: string, optionIdx: number) => {
    try {
      const res = await fetch(`${API_URL}/social/stories/${storyId}/poll/vote?option_index=${optionIdx}`, {
        method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (res.ok) {
        showToast("Đã bình chọn", "success");
        fetchStories();
      }
    } catch(e) { console.error("Poll err:", e) }
  };

  const answerQuiz = async (storyId: string, optionIdx: number) => {
    try {
      const res = await fetch(`${API_URL}/social/stories/${storyId}/quiz/answer?option_index=${optionIdx}`, {
        method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (res.ok) {
        fetchStories(); 
      } else {
        showToast("Bạn đã trả lời quiz rồi.", "error");
      }
    } catch (e) {
      console.error("Quiz err:", e);
    }
  };

  const submitReplyStory = async (storyId: string) => {
    if (!replyMessage.trim() || isReplying) return;
    setIsReplying(true);
    try {
      const res = await fetch(`${API_URL}/social/stories/${storyId}/reply?message=${encodeURIComponent(replyMessage)}`, {
        method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (res.ok) {
        showToast("Đã gửi tin nhắn cho tác giả.", "success");
        setReplyMessage("");
      } else {
        showToast("Lỗi khi gửi tin nhắn", "error");
      }
    } catch(e) { console.error(e) } finally {
      setIsReplying(false);
    }
  };

  const handleContentChange = async (e: any) => {
    const val = e.target.value;
    setContent(val);
    if (val) localStorage.setItem("doclib_feed_draft", val);
    else localStorage.removeItem("doclib_feed_draft");

    const match = val.match(/\/(book|document)\s+([^\n]+)$/);
    if (match && match[2].length > 1) {
      try {
        const res = await fetch(`${API_URL}/documents?q=${encodeURIComponent(match[2])}&limit=5`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
        if (res.ok) setDocumentSuggestions((await res.json()));
      } catch(e) { console.error("API error:", e); }
    } else {
      setDocumentSuggestions([]);
    }
  };

  const selectAttachedDocument = (doc: any) => {
    setAttachedDocumentId(doc.slug || doc.id);
    setAttachedDocumentTitle(doc.title);
    setContent(content.replace(/\/(book|document)\s+[^\n]+$/, ''));
    setDocumentSuggestions([]);
  };

  const [commentText, setCommentText] = useState("");
  const [replyToContext, setReplyToContext] = useState<{postId: string, commentId: string, userName: string} | null>(null);
  const [storyText, setStoryText] = useState("");
  const [storyBgColor, setStoryBgColor] = useState("#18181b");
  const [storyTextColor, setStoryTextColor] = useState("#ffffff");
  const [storyFontStyle, setStoryFontStyle] = useState("sans");
  const [storyPrivacy, setStoryPrivacy] = useState("public");
  const [storyLinkUrl, setStoryLinkUrl] = useState("");
  const [storyMediaUrl, setStoryMediaUrl] = useState("");
  const [isStoryUploading, setIsStoryUploading] = useState(false);
  const [showStoryModal, setShowStoryModal] = useState(false);

  const [storyAddPoll, setStoryAddPoll] = useState(false);
  const [storyPollQuestion, setStoryPollQuestion] = useState("");
  const [storyPollOptions, setStoryPollOptions] = useState(["", ""]);

  const [storyAddQuiz, setStoryAddQuiz] = useState(false);
  const [storyQuizQuestion, setStoryQuizQuestion] = useState("");
  const [storyQuizOptions, setStoryQuizOptions] = useState(["", ""]);
  const [storyQuizCorrectIdx, setStoryQuizCorrectIdx] = useState(0);
  
  const [storyMentionsInput, setStoryMentionsInput] = useState("");
  
  const [replyMessage, setReplyMessage] = useState("");
  const [isReplying, setIsReplying] = useState(false);

  const handleStoryImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    setIsStoryUploading(true);
    const formData = new FormData();
    formData.append("file", e.target.files[0]);
    try {
      const res = await fetch(`${API_URL}/social/upload-media`, {
        method: "POST",
        headers: { 'Authorization': `Bearer ${getToken()}` },
        body: formData
      });
      const data = await res.json();
      if (res.ok) setStoryMediaUrl(data.url);
      else showToast("Lỗi tải ảnh.", "error");
    } catch {
      showToast("Lỗi mạng khi tải lên.", "error");
    } finally {
      setIsStoryUploading(false);
    }
  };
  const [ranking, setRanking] = useState<any[]>([]);
  const [readerRanking, setReaderRanking] = useState<any[]>([]);
  const [tab, setTab] = useState<"foryou" | "following">("foryou");

  const [toasts, setToasts] = useState<any[]>([]);
  const { user: currentUser } = useAuth();
  const [itemType, setItemType] = useState<string>("");
  const [walletBalance, setWalletBalance] = useState<number>(0);

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  }, []);

  useEffect(() => {
    fetchFeed(true);
  }, [tab, itemType, filter]);

  useEffect(() => {
    fetchStories();
    fetchRanking();
    fetchReaderRanking();
    if (currentUser && currentUser._id) {
      fetchSuggestions();
      fetchWallet();
    }
  }, [(currentUser?._id || "")]);

  const fetchSuggestions = async () => {
    try {
      const res = await fetch(`${API_URL}/social/intersection-friends`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (res.ok) setSuggestions((await res.json()).suggestions || []);
    } catch(e) { console.error("API error:", e); }
  };

  const renderContentWithTags = (text: string) => {
    if (!text) return null;
    const parts = text.split(/(#[\w]+|https?:\/\/(?:www\.youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+|https?:\/\/open\.spotify\.com\/(?:track|album|playlist)\/[\w]+(?:.*)?|\*\*.*?\*\*|\*[^*]+\*|^> .*$)/gm);
    return parts.map((part, i) => {
      const ytMatch = part.match(/https?:\/\/(?:www\.youtube\.com\/watch\?v=|youtu\.be\/)([\w-]+)/);
      if (ytMatch) {
        return (
          <div key={i} className="my-3  overflow-hidden border border-border aspect-video">
            <iframe width="100%" height="100%" src={`https://www.youtube.com/embed/${ytMatch[1]}`} frameBorder="0" allowFullScreen></iframe>
          </div>
        );
      }
      const spotMatch = part.match(/https?:\/\/open\.spotify\.com\/(track|album|playlist)\/([\w]+)(.*)/);
      if (spotMatch) {
        return (
          <div key={i} className="my-3">
            <iframe src={`https://open.spotify.com/embed/${spotMatch[1]}/${spotMatch[2]}`} width="100%" height="80" frameBorder="0" allow="encrypted-media"></iframe>
          </div>
        );
      }
      if (part.match(/#[\w]+/)) {
        return <span key={i} className="text-black dark:text-white font-medium hover:underline cursor-pointer">{part}</span>;
      }
      if (part.match(/^\*\*(.*?)\*\*$/)) {
        return <strong key={i} className="font-bold">{part.replace(/\*\*/g, '')}</strong>;
      }
      if (part.match(/^\*(.*?)\*$/)) {
        return <em key={i} className="italic text-muted-foreground">{part.replace(/\*/g, '')}</em>;
      }
      if (part.match(/^> (.*)$/)) {
        return <blockquote key={i} className="border-l-4 border-foreground pl-3 italic text-muted-foreground my-2 bg-muted/20 py-1">{part.substring(2)}</blockquote>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  const recordView = async (postId: string) => {
    try {
      await fetch(`${API_URL}/social/posts/${postId}/view`, { method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` } });
    } catch(e) { console.error("API error:", e); }
  };

  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const fetchFeed = async (reset = false) => {
    try {
      const skip = reset ? 0 : page * 10;
      const limit = 10;
      const res = await fetch(`${API_URL}/social/feed?tab=${tab}&skip=${skip}&limit=${limit}${itemType ? `&item_type=${itemType}` : ''}${filter === 'trending' ? '&sort=trending' : ''}`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (res.ok) {
        const newData = await res.json();
        setPosts(prev => reset ? newData : [...prev, ...newData]);
        if (newData.length < limit) setHasMore(false);
        else setHasMore(true);
        if (!reset) setPage(p => p + 1);
        else setPage(1);
      } else throw new Error();

      const tagRes = await fetch(`${API_URL}/social/trending-tags`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (tagRes.ok) setTrendingTags(await tagRes.json());
      
      const booksRes = await fetch(`${API_URL}/social/suggested-documents`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (booksRes.ok) setDocumentSuggestions(await booksRes.json());
    } catch (error) {
      if (reset) showToast("Không thể tải bảng tin lúc này, vui lòng thử lại sau.", "error");
    } finally {
      setLoading(false);
    }
  };

  const fetchStories = async () => {
    try {
      const res = await fetch(`${API_URL}/social/stories`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (res.ok) setStories((await res.json()).stories || []);
    } catch(e) { console.error("API error:", e); }
  };

  const fetchArchivedStories = async () => {
    try {
      const res = await fetch(`${API_URL}/social/stories/me/archive`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (res.ok) setArchivedStories((await res.json()).stories || []);
    } catch(e) { console.error("API error:", e); }
  };

  const fetchRanking = async () => {
    try {
      const res = await fetch(`${API_URL}/social/ranking`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (res.ok) setRanking((await res.json()) || []);
    } catch(e) { console.error("API error:", e); }
  };

  const fetchReaderRanking = async () => {
    try {
      const res = await fetch(`${API_URL}/social/reader-ranking`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (res.ok) setReaderRanking((await res.json()) || []);
    } catch(e) { console.error("API error:", e); }
  };

  const createStory = async () => {
    if (!storyText.trim() && !storyMediaUrl) return showToast("Vui lòng nhập nội dung hoặc chọn ảnh.", "error");

    let finalPollData = null;
    if (storyAddPoll && storyPollQuestion.trim()) {
      const validOptions = storyPollOptions.filter(o => o.trim());
      if (validOptions.length >= 2) {
        finalPollData = { question: storyPollQuestion.trim(), options: validOptions, voters: {} };
      }
    }

    let finalQuizData = null;
    if (storyAddQuiz && storyQuizQuestion.trim()) {
      const validQuizOptions = storyQuizOptions.filter(o => o.trim());
      if (validQuizOptions.length >= 2) {
        finalQuizData = { question: storyQuizQuestion.trim(), options: validQuizOptions, correct_idx: storyQuizCorrectIdx, answers: {} };
      }
    }

    let parsedMentions: string[] = [];
    if (storyMentionsInput.trim()) {
       parsedMentions = storyMentionsInput.split(',').map(s => s.trim()).filter(s => s);
    }

    try {
      const res = await fetch(`${API_URL}/social/stories`, {
        method: "POST", headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
           text_content: storyText || undefined,
           media_url: storyMediaUrl || undefined,
           background_color: storyBgColor,
           text_color: storyTextColor,
           font_style: storyFontStyle,
           privacy: storyPrivacy,
           link_url: storyLinkUrl || null,
           poll_data: finalPollData,
           quiz_data: finalQuizData,
           mentions: parsedMentions.length > 0 ? parsedMentions : undefined
        })
      });
      if (res.ok) {
        setStoryText("");
        setStoryBgColor("#18181b");
        setStoryTextColor("#ffffff");
        setStoryFontStyle("sans");
        setStoryPrivacy("public");
        setStoryLinkUrl("");
        setStoryMediaUrl("");
        setStoryAddPoll(false);
        setStoryPollQuestion("");
        setStoryPollOptions(["", ""]);
        setStoryAddQuiz(false);
        setStoryQuizQuestion("");
        setStoryQuizOptions(["", ""]);
        setStoryQuizCorrectIdx(0);
        setStoryMentionsInput("");
        setShowStoryModal(false);
        showToast("Đã tạo tin thành công.", "success");
        fetchStories();
      }
    } catch(e) { console.error("API error:", e); }
  };

  const deletePost = async (postId: string) => {
    if(!confirm("Bạn có chắc chắn muốn xoá bài viết này không?")) return;
    try {
      const res = await fetch(`${API_URL}/social/posts/${postId}`, {
        method: "DELETE", headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (res.ok) {
        showToast("Đã xóa bài viết thành công", "success");
        fetchFeed(true);
      }
    } catch(e) { console.error("API error:", e); }
  };

  const fetchWallet = async () => {
    try {
      const res = await fetch(`${API_URL}/wallet/balance`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (res.ok) setWalletBalance((await res.json()).balance);
    } catch(e) { console.error("API error:", e); }
  };

  const overrideFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", e.target.files[0]);
    try {
      const res = await fetch(`${API_URL}/social/upload-media`, {
        method: "POST",
        headers: { 'Authorization': `Bearer ${getToken()}` },
        body: formData
      });
      const data = await res.json();
      if (res.ok) setMediaUrls(prev => [...prev, data.url]);
      else showToast("Lỗi tải ảnh/video.", "error");
    } catch {
      showToast("Lỗi mạng khi tải lên.", "error");
    } finally {
      setIsUploading(false);
    }
  };

  const [quoteText, setQuoteText] = useState("");
  const [quoteBg, setQuoteBg] = useState("bg-gray-100 dark:bg-gray-800 from-gray-200 to-gray-200");
  const [isQuoteMode, setIsQuoteMode] = useState(false);

  const createPost = async () => {
    if (!content.trim() && mediaUrls.length === 0) return showToast("Bảng tin không thể trống.", "error");
    try {
      const privacyEl = document.getElementById("post-privacy") as HTMLSelectElement;
      const privacy = privacyEl ? privacyEl.value : "public";
      const db_poll_opts = [pollText1, pollText2].filter(p => p.trim());
      const res = await fetch(`${API_URL}/social/posts`, {
        method: "POST", headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          content,
          privacy: privacy,
          comment_privacy: commentPrivacy,
          poll_options: db_poll_opts.length > 0 ? db_poll_opts : null,
          attached_document_id: attachedDocumentId || null,
          attached_document_title: attachedDocumentTitle || null,
          media_urls: mediaUrls.length > 0 ? mediaUrls : null,
          is_premium: isPremium,
          price: isPremium ? price : 0,
          read_progress: readProgress > 0 ? readProgress : null,
          item_type: isQuoteMode ? "quote" : "post",
          quote_text: isQuoteMode ? quoteText : null,
          bg_color: isQuoteMode ? quoteBg : null,
          scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null
        })
      });
      if (res.ok) {
        setContent("");
        localStorage.removeItem("doclib_feed_draft");
        setPollText1(""); setPollText2("");
        setAttachedBookId(""); setAttachedBookTitle("");
        setMediaUrls([]); setShowExtras(false);
        setIsQuoteMode(false); setQuoteText("");
        showToast("Đã đăng bài thành công.", "success");
        fetchFeed(true);
      } else throw new Error();
    } catch (e) {
      showToast("Không thể tải nội dung lúc này.", "error");
    }
  };

  const toggleLike = async (postId: string, reactionType: string = "like", event?: React.MouseEvent) => {
    try {
      const res = await fetch(`${API_URL}/social/posts/${postId}/like?reaction_type=${reactionType}`, { method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (res.ok) {
        const data = await res.json();
        if (data.message === "Đã thích" && event) {
          const rect = (event.target as HTMLElement).getBoundingClientRect();
          const x = (rect.left + rect.width / 2) / window.innerWidth;
          const y = (rect.top + rect.height / 2) / window.innerHeight;
          confetti({ particleCount: 50, spread: 60, origin: { x, y }, colors: ['#000000', '#ffffff', '#71717a'], disableForReducedMotion: true });
        }
        fetchFeed(true);
      }
    } catch (e) { showToast("Lỗi kết nối khi thích bài viết.", "error"); }
  };

  const submitComment = async (postId: string) => {
    if (!commentText.trim()) return;
    try {
      const payload: any = { item_id: postId, item_type: "post", text: commentText };
      if (replyToContext?.postId === postId) {
        payload.parent_id = replyToContext.commentId;
        payload.text = `@${replyToContext.userName} ${commentText}`;
      }
      const res = await fetch(`${API_URL}/comments`, {
        method: "POST", headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        showToast("Đã lưu tương tác thành công.", "success");
        setCommentText(""); setReplyToContext(null); fetchFeed(true); setExpandedComments(postId); 
      } else throw new Error();
    } catch (e) { showToast("Không thể gửi bình luận lúc này, vui lòng thử lại.", "error"); }
  };

  const handleVote = async (postId: string, amount: number) => {
    try {
      const res = await fetch(`${API_URL}/wallet/vote`, {
        method: "POST", headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: postId, item_type: "post", amount })
      });
      if (res.ok) {
        showToast((await res.json()).message || `Đã gửi tặng ${amount} C thành công`, "success");
        fetchWallet(); fetchFeed(true);
      } else {
        showToast((await res.json()).detail || "Giao dịch không thành công - Vui lòng kiểm tra lại số dư.", "error");
      }
    } catch (e) { showToast("Bạn không đủ số dư để thực hiện, xin nạp thêm.", "error"); }
  };

  const toggleSave = async (postId: string) => {
    try {
      const res = await fetch(`${API_URL}/social/posts/${postId}/save`, { method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (res.ok) fetchFeed(true);
    } catch(e) { console.error("API error:", e); }
  };

  const handleShare = async (postId: string) => {
    try {
      const res = await fetch(`${API_URL}/social/posts/${postId}/share`, { method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (res.ok) { showToast("Đã chia sẻ bài viết", "success"); fetchFeed(true); }
    } catch(e) { console.error("API error:", e); }
  };

  const submitPollVote = async (postId: string, optionId: string) => {
    try {
      const res = await fetch(`${API_URL}/social/posts/${postId}/poll/vote?option_id=${optionId}`, { 
        method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` } 
      });
      if (res.ok) { showToast("Bình chọn thành công", "success"); fetchFeed(true); }
    } catch(e) { console.error("API error:", e); }
  };

  const [editingPostId, setEditingPostId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState("");

  const repostPost = async (postId: string) => {
    try {
      const res = await fetch(`${API_URL}/social/posts/${postId}/repost`, { method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` } });
      if (res.ok) { showToast("Đã chia sẻ lại bài viết thành công!", "success"); fetchFeed(true); } else showToast("Chia sẻ thất bại", "error");
    } catch(e) { console.error("API error:", e); }
  };

  const togglePinPost = async (postId: string) => {
    try { const res = await fetch(`${API_URL}/social/posts/${postId}/pin`, { method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` } }); if (res.ok) fetchFeed(true); } catch(e) { console.error("API error:", e); }
  };

  const reportPost = async (postId: string) => {
    const reason = prompt("Vui lòng nhập lý do báo cáo để Quản trị viên xem xét:");
    if (!reason || !reason.trim()) return;
    try { const res = await fetch(`${API_URL}/social/posts/${postId}/report?reason=${encodeURIComponent(reason)}`, { method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` } }); if (res.ok) showToast("Cảm ơn, báo cáo đã được ghi nhận.", "success"); } catch(e) { console.error("API error:", e); }
  };

  const hidePost = async (postId: string) => {
    try { const res = await fetch(`${API_URL}/social/posts/${postId}/hide`, { method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` } }); if (res.ok) { showToast("Đã ẩn.", "info"); fetchFeed(true); } } catch(e) { console.error("API error:", e); }
  };

  const followUser = async (userId: string) => {
    try { const res = await fetch(`${API_URL}/social/users/${userId}/follow`, { method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` } }); if (res.ok) { showToast((await res.json()).message, "success"); fetchSuggestions(); } } catch(e) { console.error("API error:", e); }
  };


  const updatePost = async (postId: string) => {
    if (!editingContent.trim()) return;
    try { 
      const res = await fetch(`${API_URL}/social/posts/${postId}`, { 
        method: "PUT", 
        headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' }, 
        body: JSON.stringify({ content: editingContent }) 
      }); 
      if (res.ok) { 
        showToast("Cập nhật thành công", "success"); 
        setEditingPostId(null); 
        fetchFeed(true); 
      } 
    } catch(e) { 
      console.error("API error:", e); 
    }
  };

  return (
    <div className="feed-container">
      <ToastContainer toasts={toasts} removeToast={(id) => setToasts(prev => prev.filter(t => t.id !== id))} />

      <main className="max-w-6xl w-full mx-auto px-4 py-8 grid lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-8 flex flex-col gap-6">
          
          <div className="flex items-center justify-between border-b border-border text-sm font-semibold overflow-x-auto hide-scrollbar whitespace-nowrap">
            <div className="flex gap-6">
              <div 
                onClick={() => setTab("foryou")}
                className={`pb-3 cursor-pointer transition-all border-b-2 shrink-0 ${tab === 'foryou' ? 'border-black text-black' : 'border-transparent text-zinc-400 hover:text-black'}`}
              >
                Dành cho bạn
              </div>
              {currentUser && (
                <div 
                  onClick={() => setTab("following")}
                  className={`pb-3 cursor-pointer transition-all border-b-2 shrink-0 ${tab === 'following' ? 'border-black text-black' : 'border-transparent text-zinc-400 hover:text-black'}`}
                >
                  Đang theo dõi
                </div>
              )}
            </div>
            
            {currentUser && (
              <div className="flex gap-1 bg-zinc-50 p-1 border border-zinc-100 mb-2 shrink-0">
                 <button 
                    onClick={() => setFilter("recent")}
                    className={`px-4 py-1.5 text-[12px] font-bold tracking-widest transition-all ${filter === "recent" ? "bg-black text-white" : "text-zinc-400 hover:text-black"}`}
                 >
                    Mới nhất
                 </button>
                 <button 
                    onClick={() => setFilter("trending")}
                    className={`px-4 py-1.5 text-[12px] font-bold tracking-widest transition-all ${filter === "trending" ? "bg-black text-white" : "text-zinc-400 hover:text-black"}`}
                 >
                    Xu hướng
                 </button>
              </div>
            )}
          </div>


          {currentUser && (
            <div className="flex gap-2 overflow-x-auto pb-6 pt-2 hide-scrollbar -mx-4 px-4 md:mx-0 md:px-0">
              <div 
                onClick={() => setShowStoryModal(true)}
                className="relative w-28 h-48 rounded-none overflow-hidden cursor-pointer shrink-0 group bg-zinc-50 border border-zinc-100 flex flex-col hover:border-zinc-300 transition-all"
              >
                <div className="flex-1 bg-zinc-100 relative overflow-hidden group-hover:brightness-95 transition-all">
                  {currentUser?.avatar_url ? (
                    <img src={currentUser.avatar_url} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-zinc-200 flex items-center justify-center font-bold text-4xl text-zinc-400">
                      {currentUser?.email?.[0]?.toUpperCase() || "U"}
                    </div>
                  )}
                </div>
                <div className="h-[48px] bg-white flex flex-col justify-end pb-2.5 items-center relative">
                  <div className="absolute -top-5 w-10 h-10 bg-black text-white rounded-none flex items-center justify-center border-4 border-white z-10">
                    <Plus className="w-6 h-6" />
                  </div>
                  <span className="text-[12px] font-bold tracking-widest text-zinc-900 mt-4">Tạo tin</span>
                </div>
              </div>

              {stories.map((story, idx) => (
                <div 
                  key={story.id} 
                  className="relative w-28 h-48 rounded-none overflow-hidden cursor-pointer shrink-0 group bg-black border border-zinc-100 flex flex-col hover:border-zinc-400 transition-all"
                  onClick={() => { setActiveStoryIndex(idx); setViewingStoryMode(true); setStoryProgress(0); }}
                >
                  <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/80 z-10"></div>
                  
                  {story.media_url ? (
                    <img src={story.media_url} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 pointer-events-none" />
                  ) : (
                    <div 
                      className="absolute inset-0 flex items-center justify-center p-3 text-center text-white" 
                      style={{ backgroundColor: story.background_color || '#18181b' }}
                    >
                      <h3 className="z-20 font-bold text-[12px] tracking-tight leading-tight break-words line-clamp-6">{story.text_content}</h3>
                    </div>
                  )}

                  <div className="absolute top-3 left-3 z-20 w-9 h-9 rounded-none border-2 border-white/50 overflow-hidden bg-zinc-800 
">
                    {story.user?.avatar_url ? (
                      <img src={story.user.avatar_url} className="w-full h-full object-cover rounded-none" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-zinc-900 font-bold text-xs text-white rounded-none">
                        {story.user?.name?.[0]?.toUpperCase() || "A"}
                      </div>
                    )}
                  </div>
                  <span className="absolute bottom-3 left-3 z-20 text-[12px] font-bold tracking-widest text-white truncate w-[80%]">{story.user?.name || 'Ai đó'}</span>
                </div>
              ))}
            </div>
          )}


          {currentUser && (
            <div className="bg-white border border-zinc-100 p-6 rounded-none flex flex-col mb-8 transition-all duration-500">
              <div className="flex gap-4 items-start">
                <div className="w-12 h-12 bg-zinc-900 rounded-none border border-zinc-100 flex shrink-0 items-center justify-center text-white font-bold text-xl overflow-hidden relative cursor-pointer transition-all">
                  {currentUser?.avatar_url ? (
                    <img src={currentUser.avatar_url} className="w-full h-full object-cover" />
                  ) : (
                    currentUser?.email?.[0]?.toUpperCase() || "U"
                  )}
                </div>
                <div className="flex-1">
                  <textarea
                    id="composer-textarea"
                    className="w-full bg-transparent outline-none text-foreground resize-none min-h-[44px] text-lg placeholder:text-muted-foreground placeholder:font-normal mt-1.5"
                    placeholder={`${(currentUser?._id || "") ? `${currentUser._id} ơi, ` : ''}bạn đang nghĩ gì thế?`}
                    value={content}
                    rows={isQuoteMode ? 2 : Math.max(1 + content.split('\n').length, 2)}
                    onChange={handleContentChange}
                  ></textarea>

                  {mediaUrls.length > 0 && (
                    <div className="grid grid-cols-2 gap-1 mt-2  overflow-hidden border border-border">
                      {mediaUrls.map((url, i) => (
                        <div key={i} className={`relative w-full aspect-square ${mediaUrls.length === 1 ? 'col-span-2 aspect-video' : ''}`}>
                          {url.match(/\.(mp4|webm)$/i) ? (
                            <video src={`${API_URL}${url}`} className="object-cover w-full h-full" autoPlay muted loop />
                          ) : (
                            <img src={`${API_URL}${url}`} alt="Preview" className="object-cover w-full h-full" />
                          )}
                          <button onClick={() => setMediaUrls(mediaUrls.filter((_, idx) => idx !== i))} className="absolute top-2 right-2 bg-black/60 hover:bg-black/80 text-white rounded-none w-8 h-8 flex items-center justify-center  backblur-sm transition-colors">
                            <X className="w-5 h-5"/>
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {documentSuggestions.length > 0 && (
                    <div className="absolute z-50 bg-background border border-border   mt-1 overflow-hidden w-full max-w-md">
                      <div className="p-2 bg-muted/50 text-xs font-semibold text-muted-foreground border-b border-border">Đính kèm tài liệu</div>
                      {documentSuggestions.map((doc: any, i: number) => (
                        <div key={i} className="px-4 py-2 hover:bg-muted cursor-pointer text-sm font-medium flex justify-between" onClick={() => selectAttachedDocument(doc)}>
                          {doc.title} 
                          <span className="text-muted-foreground text-xs">{doc.author}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {showExtras && (
                <div className="mt-3 p-4 bg-muted/30  space-y-3 border border-border">
                  <div className="space-y-2">
                     <h4 className="text-xs font-bold text-muted-foreground flex items-center gap-1.5"><BarChart2 className="w-3.5 h-3.5" /> Tạo bình chọn</h4>
                     <Input value={pollText1} onChange={e => setPollText1(e.target.value)} placeholder="Lựa chọn 1" className="bg-background focus-visible:ring-1 text-sm border-border" />
                     <Input value={pollText2} onChange={e => setPollText2(e.target.value)} placeholder="Lựa chọn 2" className="bg-background focus-visible:ring-1 text-sm border-border" />
                  </div>
                </div>
              )}

              <div className="mt-3 pt-3 border-t border-border">
                <div className="flex items-center justify-between border border-border  p-2  font-semibold text-sm">
                  <span className="ml-3 hidden sm:inline-block text-muted-foreground">Thêm vào bài viết</span>
                  <div className="flex gap-1 justify-end flex-1">
                    <label className="cursor-pointer p-2 hover:bg-muted rounded-none transition-colors group flex items-center justify-center gap-2" title="Đính kèm Ảnh/Video">
                       <ImageIcon className="w-6 h-6 text-foreground scale-100 group-hover:scale-110 transition-transform" />
                       <input type="file" className="hidden" accept="image/*" onChange={overrideFileUpload} />
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}
            <>
              <div className="bg-muted text-muted-foreground text-sm py-2 px-4  flex items-center justify-between border border-border">
                <span className="font-medium">Tóm tắt bảng tin hôm nay với AI?</span>
                <button 
                  onClick={async () => {
                    try { showToast("Đang tóm tắt feed", "info"); const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/social/ai/feed-summary`, { headers: { 'Authorization': `Bearer ${getToken()}`}}); const data = await res.json(); if(data.summary) { } } catch (e) { showToast("Lỗi tóm tắt AI", "error"); }
                  }}
                  className="text-foreground font-bold hover:underline"
                >
                  Trải nghiệm ngay
                </button>
              </div>
            </>


          <div className="flex flex-col gap-5 w-full">
            {loading ? (
              <div className="text-center p-10 font-medium text-muted-foreground animate-pulse">Đang tải bảng tin</div>
            ) : posts.length === 0 ? (
              <div className="text-center p-10 text-muted-foreground border border-border border-dashed ">Chưa có bài viết nào trong bảng tin.</div>
            ) : posts.map(post => (
              <div key={post.id} className="bg-card border border-border  p-5  ">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-secondary rounded-none flex shrink-0 items-center justify-center text-secondary-foreground font-bold border border-border overflow-hidden">
                    {post.user?.avatar_url ? (
                      <img src={post.user.avatar_url} className="w-full h-full object-cover rounded-none" />
                    ) : (
                      post.user?.username?.[0]?.toUpperCase() || "U"
                    )}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-bold text-foreground text-sm">{post.user?.username || "Người dùng ẩn danh"}</h4>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">{new Date(post.created_at).toLocaleString("vi-VN")}</span>
                      {post.is_shadowbanned && (
                        <span className="px-1.5 py-0.5 bg-muted text-muted-foreground text-[12px] font-semibold rounded border border-border">
                          Bị hạn chế hiển thị
                        </span>
                      )}
                    </div>
                  </div>
                  {(currentUser?._id || "") && currentUser?._id === post.author_id ? (
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="icon" onClick={() => togglePinPost(post.id)} title={post.is_pinned ? "Bỏ ghim" : "Ghim bài viết"} className={`text-muted-foreground opacity-50 hover:opacity-100 transition-all ${post.is_pinned ? 'text-foreground opacity-100' : 'hover:text-foreground'}`}>
                        <Pin className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => { setEditingPostId(post.id); setEditingContent(post.content); }} title="Sửa bài viết" className="text-muted-foreground opacity-50 hover:opacity-100 transition-all hover:text-foreground">
                        <Edit3 className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => deletePost(post.id)} title="Xóa bài viết" className="text-muted-foreground opacity-50 hover:opacity-100 transition-all hover:text-black">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="icon" onClick={async () => {
                        showToast("Đang dịch", "info");
                        try {
                            const res = await fetch(`${API_URL}/social/posts/${post.id}/translate`, { method: "POST", headers: { 'Authorization': `Bearer ${getToken()}`}});
                            const data = await res.json();
                            if (data.translated_text) setTranslationModal({ text: data.translated_text });
                        } catch(e) { console.error("API error:", e); }
                      }} title="Dịch bài viết" className="text-muted-foreground opacity-50 hover:opacity-100 transition-all">
                        <Globe className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => hidePost(post.id)} title="Ẩn bài viết này" className="text-muted-foreground opacity-50 hover:opacity-100 hover:text-foreground transition-all">
                        <EyeOff className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => reportPost(post.id)} title="Báo cáo vi phạm" className="text-muted-foreground opacity-50 hover:opacity-100 hover:text-black transition-all">
                        <Flag className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </div>

                {editingPostId === post.id ? (
                  <div className="mb-4">
                     <textarea
                      className="w-full bg-background border border-border outline-none p-3  text-foreground resize-y h-24 focus:ring-1 focus:ring-black dark:ring-white transition-all text-sm mb-2"
                      value={editingContent}
                      onChange={(e) => setEditingContent(e.target.value)}
                    ></textarea>
                    <div className="flex gap-2 justify-end">
                      <Button variant="ghost" size="sm" onClick={() => setEditingPostId(null)}>Hủy bỏ</Button>
                      <Button size="sm" onClick={() => updatePost(post.id)}>Lưu thay đổi</Button>
                    </div>
                  </div>
                ) : (
                    <>
                      <p className={`whitespace-pre-wrap leading-relaxed text-sm break-words ${post.is_locked ? "italic text-muted-foreground blur-sm select-none" : "text-foreground"}`} onMouseEnter={() => recordView(post.id)}>
                        {renderContentWithTags(post.content)}
                      </p>
                      {post.is_locked && (
                        <div className="absolute inset-0 bg-background/60 backblur-md flex flex-col items-center justify-center z-10 ">
                          <p className="font-bold text-lg mb-2">Bài viết độc quyền</p>
                          <Button onClick={async () => {
                              try {
                                 const res = await fetch(`${API_URL}/social/posts/${post.id}/unlock`, { method: "POST", headers: { 'Authorization': `Bearer ${getToken()}` }});
                                 if(res.ok) { fetchFeed(true); fetchWallet(); } else { showToast("Mở khóa thất bại, hãy nạp thêm dl", "error"); }
                              } catch(e) { console.error("API error:", e); }
                          }} className="bg-black text-white hover:bg-zinc-800  h-11 px-6 text-xs font-bold tracking-widest flex items-center gap-2 transition-all active:scale-[0.98]">
                            Mở khóa với {post.price} <Coins className="w-4 h-4" />
                          </Button>
                        </div>
                      )}
                      {post.read_progress && (
                        <div className="mt-3 bg-muted/30  p-2">
                          <div className="flex justify-between text-xs text-muted-foreground mb-1">
                            <span>Tiến độ đọc:</span>
                            <span className="font-bold text-black dark:text-white">{post.read_progress}%</span>
                          </div>
                          <div className="w-full bg-secondary rounded-none h-1.5 overflow-hidden">
                             <div className="bg-black dark:bg-white h-1.5 rounded-none" style={{ width: `${post.read_progress}%` }}></div>
                          </div>
                        </div>
                      )}
                    </>
                )}

                {post.media_urls && post.media_urls.length > 0 && (
                  <div className="mt-3 flex overflow-x-auto snap-x snap-mandatory gap-2 pb-2 hide-scrollbar ">
                    {post.media_urls.map((url: string, i: number) => (
                      <div key={i} className="relative aspect-video shrink-0 bg-muted snap-center w-[85%]  overflow-hidden border border-border">
                        {url.match(/\.(mp4|webm)$/i) ? (
                          <video src={`${API_URL}${url}`} className="object-cover w-full h-full" controls />
                        ) : (
                          <img src={`${API_URL}${url}`} alt="Media" className="object-cover w-full h-full cursor-pointer hover:opacity-95 transition-opacity" />
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {post.document_id && (
                  <div className="mt-4 p-4 border border-border bg-muted/30  cursor-pointer border-l-4 border-l-primary hover:bg-muted/50 transition-colors flex items-center justify-between">
                    <div>
                      <span className="text-xs font-semibold text-muted-foreground tracking-wider flex items-center"><BookText className="w-4 h-4 mr-2" /> Tài liệu đính kèm</span>
                      <h5 className="font-semibold mt-1 text-sm text-foreground truncate">{post.document_title || post.document_id}</h5>
                    </div>
                    <Button variant="outline" size="sm">Đọc ngay</Button>
                  </div>
                )}

                {post.poll_options && post.poll_options.length > 0 && (
                  <div className="mt-4 space-y-2">
                     {post.poll_options.map((opt: any) => {
                       const totalPollVotes = post.poll_options.reduce((acc: number, curr: any) => acc + (curr.votes || 0), 0);
                       const percentage = totalPollVotes === 0 ? 0 : Math.round((opt.votes / totalPollVotes) * 100);
                       const isVoted = post.voted_option === opt.id;
                       
                       return (
                         <div key={opt.id} onClick={() => { if(currentUser) submitPollVote(post.id, opt.id); else showToast("Vui lòng đăng nhập để thực hiện.", "error"); }} className={`relative overflow-hidden cursor-pointer  border ${isVoted ? 'border-foreground ring-1 ring-black dark:ring-white/20' : 'border-border'} bg-muted/30 p-3 hover:bg-muted transition-colors`}>
                           <div className="absolute top-0 left-0 bottom-0 bg-black dark:bg-white/10 transition-all duration-500 " style={{ width: `${percentage}%` }}></div>
                           <div className="relative flex justify-between px-3 py-2.5 text-sm z-10 font-medium">
                             <span className={isVoted ? 'text-black dark:text-white font-bold flex items-center' : 'flex items-center text-foreground'}>
                               {opt.text}
                             </span>
                             <span className="text-muted-foreground">{percentage}%</span>
                           </div>
                         </div>
                       )
                     })}
                   </div>
                )}

                <div className="mt-5 border-t border-border pt-4 flex gap-2 text-sm items-center">
                  <div className="relative group flex items-center">
                    <Button variant="ghost" size="sm" onClick={(e) => { if(currentUser) toggleLike(post.id, "like", e); else showToast("Vui lòng đăng nhập để thực hiện.", "error"); }} className={`text-muted-foreground hover:text-foreground ${post.likes?.includes((currentUser?._id || "")) ? 'text-black font-semibold' : ''}`}>
                      <Heart className={`w-4 h-4 mr-1.5 transition-colors ${post.likes?.includes((currentUser?._id || "")) ? 'fill-black text-black' : 'hover:text-black'}`} /> {post.likes?.length || 0}
                    </Button>
                    {currentUser && (
                      <div className="absolute bottom-full left-0 mb-1 hidden group-hover:flex bg-white border border-border  p-1.5 gap-1.5 z-10 transition-all animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <button onClick={(e) => toggleLike(post.id, 'like', e)} className="p-2 hover:bg-zinc-100  transition-all text-black" title="Tim"><Heart className="w-4 h-4 fill-black" /></button>
                        <button onClick={(e) => toggleLike(post.id, 'lightbulb', e)} className="p-2 hover:bg-zinc-100  transition-all text-black" title="Sáng kiến"><Lightbulb className="w-4 h-4 fill-black" /></button>
                        <button onClick={(e) => toggleLike(post.id, 'fire', e)} className="p-2 hover:bg-zinc-100  transition-all text-black" title="Lửa"><Flame className="w-4 h-4 fill-black" /></button>
                        <button onClick={(e) => toggleLike(post.id, 'laugh', e)} className="p-2 hover:bg-zinc-100  transition-all text-black" title="Haha"><Smile className="w-4 h-4 fill-black" /></button>
                      </div>
                    )}
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => setExpandedComments(expandedComments === post.id ? null : post.id)} className="text-muted-foreground hover:text-foreground">
                    <MessageCircle className="w-4 h-4 mr-1.5" /> {(post.comments || []).length}
                  </Button>
                  <Button variant="ghost" size="sm" className="text-muted-foreground cursor-default hover:bg-transparent" title="Lượt xem">
                    <Eye className="w-4 h-4 mr-1" /> {post.view_count || 0}
                  </Button>
                  <div className="flex items-center gap-1 ml-auto">
                    <Button variant="ghost" size="sm" onClick={() => { if(currentUser) handleVote(post.id, 50); else showToast("Vui lòng đăng nhập để thực hiện", "error"); }} className="text-muted-foreground hover:text-foreground flex items-center gap-1.5" title="Tặng 50 dl">
                        <Coins className="w-3.5 h-3.5" />
                        <span className="text-xs font-bold text-zinc-400">50</span>
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => { if(currentUser) repostPost(post.id); else showToast("Vui lòng đăng nhập để thực hiện.", "error"); }} title="Chia sẻ lại" className="text-muted-foreground hover:text-foreground">
                      <Share2 className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => { if(currentUser) toggleSave(post.id); else showToast("Vui lòng đăng nhập để thực hiện.", "error"); }} className={`${post.saved ? 'text-foreground' : 'text-muted-foreground'} hover:text-foreground`} title="Lưu bài viết">
                      <Bookmark className={`w-4 h-4 ${post.saved ? 'fill-foreground' : ''}`} />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => handleShare(post.id)} className="text-muted-foreground hover:text-foreground" title="Chia sẻ">
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {expandedComments === post.id && (
                  <div className="mt-4 bg-muted/30  p-4 border border-border animate-in slide-in-from-top-2">
                    <div className="max-h-60 overflow-y-auto pr-2 space-y-4 mb-4">
                      {post.comments?.length > 0 ? post.comments.map((c: any, i: number) => (
                        <div key={i} className={`text-sm ${c.parent_id ? 'ml-6 relative pl-4 border-l-2 border-foreground/20' : ''}`}>
                          <div className="flex justify-between w-full group">
                            <div>
                              <span className="font-semibold text-foreground">{c.user.display_name || c.user?.display_name || "Người dùng"}: </span>
                              <span className="text-muted-foreground break-words">{c.content || c.text}</span>
                            </div>
                            {currentUser && (
                              <span onClick={() => {
                                setReplyToContext({ postId: post.id, commentId: c.id, userName: c.user.display_name || "Người dùng" });
                                setCommentText("");
                              }} className="text-black dark:text-white text-xs opacity-0 group-hover:opacity-100 cursor-pointer whitespace-nowrap ml-2">Trả lời</span>
                            )}
                          </div>
                        </div>
                      )) : <div className="text-sm text-muted-foreground italic">Chưa có bình luận nào. Hãy là người đầu tiên!</div>}
                    </div>
                    
                    {currentUser ? (
                      <>
                        {replyToContext && replyToContext.postId === post.id && (
                          <div className="text-xs text-muted-foreground mb-2 flex justify-between bg-muted/50 p-2 ">
                            <span>Đang trả lời <b>{replyToContext.userName}</b></span>
                            <span className="cursor-pointer text-gray-700" onClick={() => setReplyToContext(null)}>Hủy</span>
                          </div>
                        )}
                        <div className="flex gap-2 items-center pt-2">
                          {post.comment_privacy === 'private' && (currentUser?._id || "") !== post.author_id ? (
                            <div className="flex-1 text-xs text-muted-foreground italic py-2 px-4 bg-muted rounded-none border border-border text-center">
                              Bình luận đã bị khóa cho bài viết này.
                            </div>
                          ) : (
                            <>
                              <Input
                                className="bg-background"
                                placeholder="Viết bình luận"
                                value={commentText}
                                onChange={(e) => setCommentText(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter') submitComment(post.id) }}
                              />
                              <Button onClick={() => submitComment(post.id)} size="icon" className="shrink-0">
                                <Send className="w-4 h-4" />
                              </Button>
                            </>
                          )}
                        </div>
                      </>
                    ) : (
                      <div className="text-xs text-center text-muted-foreground mt-2 bg-muted py-2  border border-border">
                        Vui lòng đăng nhập để bình luận.
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            
            {!loading && hasMore && (
              <div className="flex justify-center p-4">
                <Button variant="outline" size="sm" onClick={() => fetchFeed()} disabled={loading} className="text-xs font-semibold px-6 py-2 rounded-none border-border hover:bg-muted text-muted-foreground transition-colors">
                  Tải thêm bài viết
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="hidden lg:col-span-4 lg:flex flex-col gap-4 sticky top-6 self-start">
          
          {currentUser && (
            <div className="bg-card border border-border  p-5  text-center">
              <h3 className="text-xs font-bold text-muted-foreground tracking-wider mb-2">Ví của bạn</h3>
              <p className="text-3xl font-bold text-foreground flex items-center justify-center gap-2">{walletBalance.toLocaleString("vi-VN")} <Coins className="w-5 h-5 text-zinc-400" /></p>
              <Button size="sm" variant="outline" className="mt-4 w-full" onClick={() => window.location.href = '/wallet'}>Quản lý ví</Button>
            </div>
          )}

          <div className="bg-card border border-border  p-5 ">
            <h3 className="text-xs font-bold text-foreground tracking-wider mb-4 border-b border-border pb-3 flex items-center gap-2">
               <Trophy className="w-3.5 h-3.5" /> Bảng vinh danh Tác giả
            </h3>
            
            {ranking.length === 0 ? (
              <p className="text-[12px] text-muted-foreground font-bold tracking-widest text-center py-4">Chưa có dữ liệu</p>
            ) : ranking.map((r, i) => (
              <div key={i} className="flex gap-3 items-center group border-b border-border last:border-0 pb-3 mb-3 last:pb-0 last:mb-0">
                <div className="w-8 h-8  bg-black text-white font-bold flex items-center shrink-0 justify-center text-[12px] border border-black tracking-tighter">
                  #{i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-[12px] font-bold tracking-widest text-foreground truncate">{r.full_name || "Tác giả ẩn danh"}</h4>
                  <span className="text-[13px] text-zinc-400 font-bold truncate flex items-center gap-1.5 tracking-widest"> 
                    {r.score.toLocaleString("vi-VN")} điểm
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-card border border-border  p-5 ">
            <h3 className="text-xs font-bold text-foreground tracking-wider mb-4 border-b border-border pb-3 flex items-center gap-2">
               <Users className="w-3.5 h-3.5" /> Độc giả tích cực
            </h3>
            
            {readerRanking.length === 0 ? (
              <p className="text-[12px] text-muted-foreground font-bold tracking-widest text-center py-4">Chưa có dữ liệu</p>
            ) : readerRanking.map((r, i) => (
              <div key={i} className="flex gap-3 items-center group border-b border-border last:border-0 pb-3 mb-3 last:pb-0 last:mb-0">
                <div className="w-8 h-8  bg-zinc-100 text-black font-bold flex items-center shrink-0 justify-center text-[12px] border border-zinc-200 tracking-tighter">
                  #{i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-[12px] font-bold tracking-widest text-foreground truncate">{r.full_name || "Độc giả ẩn danh"}</h4>
                  <span className="text-[13px] text-zinc-400 font-bold truncate flex items-center gap-1.5 tracking-widest"> 
                    {r.score.toLocaleString("vi-VN")} đóng góp
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-card border border-border  p-5">
            <h3 className="text-xs font-bold text-foreground tracking-wider mb-4 border-b border-border pb-3 flex items-center gap-2"><BookText className="w-3.5 h-3.5" /> Tài liệu đáng đọc</h3>
            {documentSuggestions.length === 0 ? (
              <p className="text-[12px] text-muted-foreground font-bold tracking-widest text-center py-4">Chưa có gợi ý</p>
            ) : (
              <div className="space-y-4 pt-1">
                {documentSuggestions.map((b, i) => (
                  <div key={i} className="flex gap-3 items-center group cursor-pointer border border-transparent hover:border-zinc-100 p-1 transition-all">
                    <div className="w-10 h-14 bg-zinc-50 border border-zinc-100 rounded-none shrink-0 flex items-center justify-center overflow-hidden">
                      <BookText className="w-5 h-5 text-zinc-300" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-[12px] font-bold tracking-widest text-foreground truncate group-hover:text-black transition-colors">{b.title}</h4>
                      <span className="text-[13px] text-zinc-400 font-bold tracking-widest">{b.mentions} đề xuất</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-card border border-border  p-5 ">
            <h3 className="text-xs font-bold text-foreground tracking-wider mb-4 border-b border-border pb-3 flex items-center gap-2">
               <Hash className="w-3.5 h-3.5" /> Thẻ xu hướng
            </h3>
            {trendingTags.length === 0 ? (
              <p className="text-[12px] text-muted-foreground font-bold tracking-widest text-center py-4">Chưa có xu hướng</p>
            ) : (
              <div className="space-y-3">
                {trendingTags.map((t, i) => (
                  <Link key={i} href={`/search?q=${encodeURIComponent(t.tag || t)}`} className="flex justify-between items-center group cursor-pointer">
                    <span className="text-[12px] font-bold tracking-widest text-zinc-400 group-hover:text-black transition-colors">#{t.tag || t}</span>
                    <ArrowUpRight className="w-3 h-3 text-zinc-200 group-hover:text-black transition-all" />
                  </Link>
                ))}
              </div>
            )}
          </div>

          <div className="bg-card border border-border  p-5">
            <h3 className="text-xs font-bold text-foreground tracking-wider mb-4 border-b border-border pb-3">Gợi ý kết nối</h3>
            {suggestions.length === 0 ? (
              <p className="text-sm text-muted-foreground leading-relaxed">Hãy cập nhật sở thích thẻ Bookmark để tìm vòng tròn bạn bè cùng gu tài liệu.</p>
            ) : suggestions.map((s, i) => (
              <div key={i} className="flex gap-3 items-center group cursor-pointer border-b border-border last:border-0 pb-3 last:pb-0 mb-3 last:mb-0">
                <div className="w-10 h-10 rounded-none bg-secondary text-secondary-foreground font-bold flex items-center shrink-0 justify-center text-sm border-border border">
                  {s.display_name?.[0]?.toUpperCase() || "A"}
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-[12px] font-bold tracking-widest text-foreground truncate">{s.display_name || "Ẩn danh"}</h4>
                  <span className="text-[13px] text-zinc-400 font-bold truncate tracking-widest">{s.total_match || 0} điểm chung</span>
                </div>
                <Button size="sm" variant="outline" onClick={() => { if(currentUser) followUser(s._id); else showToast("Vui lòng đăng nhập để thực hiện.", "error"); }} title="Theo dõi" className="h-7 px-3 text-xs rounded-none shrink-0 hover:bg-foreground hover:text-background transition-all">
                  Theo dõi
                </Button>
              </div>
            ))}
          </div>
        </div>
      </main>

      {currentUser && showStoryModal && (
        <div className="fixed inset-0 z-[300] bg-background/80 backblur-sm flex items-center justify-center animate-in fade-in-0 duration-200">
          <div className="bg-card w-full h-[100dvh] md:h-[85vh] max-w-sm md:  md:border border-border flex flex-col relative overflow-hidden">

            <div className="absolute z-10 top-0 left-0 right-0 p-3 flex justify-between items-center bg-gradient-to-b from-black/60 to-transparent text-white">
              <div className="flex items-center gap-2">
                <button onClick={() => setShowStoryModal(false)} className="p-2 backblur-md bg-black/20 hover:bg-black/40 rounded-none transition-colors">
                  <X className="w-5 h-5" />
                </button>
                <button
                  onClick={() => { setShowStoryArchive(!showStoryArchive); if (!showStoryArchive) fetchArchivedStories(); }}
                  className={`p-2 backblur-md rounded-none transition-colors ${showStoryArchive ? 'bg-white/30' : 'bg-black/20 hover:bg-black/40'}`}
                  title="Kho lưu trữ tin của bạn"
                >
                  <Archive className="w-5 h-5" />
                </button>
              </div>
              <div className="flex gap-2 items-center">
                <select
                  value={storyFontStyle}
                  onChange={(e) => setStoryFontStyle(e.target.value)}
                  className="bg-black/20 text-white text-xs px-3 py-1.5 rounded-none backblur-md outline-none cursor-pointer hover:bg-black/40"
                >
                  <option value="sans" className="text-black">Sans</option>
                  <option value="mono" className="text-black">Mono</option>
                </select>
                <select
                  value={storyPrivacy}
                  onChange={(e) => setStoryPrivacy(e.target.value)}
                  className="bg-black/20 text-white text-xs px-3 py-1.5 rounded-none backblur-md outline-none cursor-pointer hover:bg-black/40"
                >
                  <option value="public" className="text-black">Công khai</option>
                  <option value="friends" className="text-black">Bạn bè</option>
                  <option value="close_friends" className="text-black">Bạn thân</option>
                </select>
                <input
                  type="color"
                  value={storyBgColor}
                  onChange={(e) => setStoryBgColor(e.target.value)}
                  className="w-8 h-8 rounded-none cursor-pointer bg-transparent border-0 p-0"
                  title="Màu nền"
                />
                <input
                  type="color"
                  value={storyTextColor}
                  onChange={(e) => setStoryTextColor(e.target.value)}
                  className="w-8 h-8 rounded-none cursor-pointer bg-transparent border-0 p-0"
                  title="Màu chữ"
                />
              </div>
            </div>


            {showStoryArchive && (
              <div className="absolute z-20 top-16 left-0 right-0 bottom-0 bg-card/95 backblur-md overflow-y-auto p-4">
                <h3 className="text-sm font-bold text-foreground mb-4 border-b border-border pb-3">Kho lưu trữ tin của bạn</h3>
                {archivedStories.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 text-center">
                    <Archive className="w-10 h-10 text-muted-foreground mb-3" strokeWidth={1} />
                    <p className="text-sm text-muted-foreground">Chưa có tin nào được lưu trữ.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-2">
                    {archivedStories.map((s, i) => (
                      <div
                        key={i}
                        className="aspect-[9/16]  overflow-hidden relative border border-border cursor-pointer group"
                        style={{ backgroundColor: s.bg_color || s.background_color || '#18181b' }}
                      >
                        {s.media_url ? (
                          <img src={s.media_url} className="w-full h-full object-cover" alt="Story" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center p-2">
                            <p className="text-white text-[12px] font-semibold text-center line-clamp-4 break-words">{s.text_content}</p>
                          </div>
                        )}
                        <div className="absolute bottom-0 left-0 right-0 bg-black/50 px-2 py-1">
                          <span className="text-white text-[13px] font-medium">{new Date(s.created_at).toLocaleDateString('vi-VN')}</span>
                        </div>
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}


            <div 
              className="flex-1 flex flex-col justify-center items-center p-6 transition-colors duration-300 relative"
              style={{ backgroundColor: storyBgColor }}
            >
              {storyMediaUrl && (
                <div className="absolute inset-0 w-full h-full">
                  <img src={storyMediaUrl} alt="Story Media" className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-black/30" /> {}
                </div>
              )}

              <textarea
                className="w-full bg-transparent border-none outline-none text-center resize-none text-2xl font-bold placeholder:opacity-50 z-10"
                placeholder={storyMediaUrl ? "Thêm chữ vào ảnh" : "Góc này đang nghĩ gì thế"}
                value={storyText}
                onChange={(e) => setStoryText(e.target.value)}
                autoFocus
                rows={5}
                style={{ 
                  color: storyTextColor, 
                  fontFamily: storyFontStyle === 'mono' ? 'Courier New, monospace' : 'inherit',
                }}
              ></textarea>
              
              {storyLinkUrl && (
                <div className="mt-4 px-4 py-2 bg-white/20 backblur-md rounded-none border border-white/20 flex gap-2 items-center max-w-[80%] z-10 ">
                  <Globe className="w-4 h-4 text-white" />
                  <span className="text-white text-sm truncate font-medium">{storyLinkUrl}</span>
                  <button onClick={() => setStoryLinkUrl("")} className="text-white/70 hover:text-white ml-2"><X className="w-3 h-3" /></button>
                </div>
              )}

              {storyAddPoll && (
                <div className="mt-6 w-full max-w-[280px] bg-black/40 backblur-md  border border-white/20 p-4 z-10  flex flex-col gap-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-white text-xs font-bold tracking-wider">Tạo Khảo Sát</span>
                    <button onClick={() => setStoryAddPoll(false)} className="text-white/70 hover:text-white"><X className="w-4 h-4" /></button>
                  </div>
                  <input
                    type="text"
                    placeholder="Câu hỏi khảo sát"
                    value={storyPollQuestion}
                    onChange={(e) => setStoryPollQuestion(e.target.value)}
                    className="w-full bg-white/10 text-white text-sm border-b border-white/30 outline-none px-2 py-1 placeholder:text-white/50 font-semibold"
                  />
                  {storyPollOptions.map((opt, idx) => (
                    <input
                      key={idx}
                      type="text"
                      placeholder={`Lựa chọn ${idx + 1}`}
                      value={opt}
                      onChange={(e) => {
                        const newOpts = [...storyPollOptions];
                        newOpts[idx] = e.target.value;
                        setStoryPollOptions(newOpts);
                      }}
                      className="w-full bg-white/10  text-white text-sm border border-white/20 outline-none px-3 py-2 placeholder:text-white/50 focus:bg-white/20 transition-all font-medium text-center"
                    />
                  ))}
                  {storyPollOptions.length < 4 && (
                    <button 
                      onClick={() => setStoryPollOptions([...storyPollOptions, ""])} 
                      className="text-white/70 text-xs hover:text-white font-bold py-2 flex items-center justify-center gap-2 transition-all tracking-widest"
                    >
                      <Plus className="w-3 h-3" />
                      Thêm lựa chọn
                    </button>
                  )}
                </div>
              )}

              {storyAddQuiz && (
                <div className="mt-6 w-full max-w-[280px] bg-black/40 backblur-md  border border-white/20 p-4 z-10  flex flex-col gap-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-white text-xs font-bold tracking-wider">Tạo Trắc Nghiệm</span>
                    <button onClick={() => setStoryAddQuiz(false)} className="text-white/70 hover:text-white"><X className="w-4 h-4" /></button>
                  </div>
                  <input
                    type="text"
                    placeholder="Câu hỏi trắc nghiệm"
                    value={storyQuizQuestion}
                    onChange={(e) => setStoryQuizQuestion(e.target.value)}
                    className="w-full bg-white/10 text-white text-sm border-b border-white/30 outline-none px-2 py-1 placeholder:text-white/50 font-semibold"
                  />
                  {storyQuizOptions.map((opt, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                       <button
                         onClick={() => setStoryQuizCorrectIdx(idx)}
                         className={`w-6 h-6 flex items-center justify-center rounded-none border ${storyQuizCorrectIdx === idx ? 'bg-black border-black text-white' : 'bg-white/10 border-white/30'}`}
                       >
                         {storyQuizCorrectIdx === idx && <CheckCircle className="w-4 h-4" />}
                       </button>
                       <input
                        type="text"
                        placeholder={`Lựa chọn ${idx + 1}`}
                        value={opt}
                        onChange={(e) => {
                          const newOpts = [...storyQuizOptions];
                          setStoryQuizOptions(newOpts);
                        }}
                        className="w-full bg-white/10  text-white text-sm border border-white/20 outline-none px-3 py-2 placeholder:text-white/50 focus:bg-white/20 transition-all font-medium text-center"
                      />
                    </div>
                  ))}
                  {storyQuizOptions.length < 4 && (
                    <button 
                      onClick={() => setStoryQuizOptions([...storyQuizOptions, ""])} 
                      className="text-white/70 text-xs hover:text-white font-bold py-2 flex items-center justify-center gap-2 transition-all tracking-widest"
                    >
                      <Plus className="w-3 h-3" />
                      Thêm lựa chọn
                    </button>
                  )}
                </div>
              )}
            </div>


            <div className="bg-card w-full border-t border-border p-3 flex flex-col gap-2.5 z-10">

              {showLinkInput && (
                <div className="flex items-center gap-2 animate-in slide-in-from-bottom-2">
                  <div className="flex-1 relative flex items-center">
                    <LinkIcon className="w-4 h-4 text-muted-foreground absolute left-3" />
                    <Input
                      placeholder="Đính kèm link"
                      className="pl-9 h-9 w-full bg-muted/50 border-border text-sm rounded-none"
                      value={storyLinkUrl}
                      onChange={(e) => setStoryLinkUrl(e.target.value)}
                      autoFocus
                    />
                    {storyLinkUrl && (
                      <button onClick={() => setStoryLinkUrl('')} className="absolute right-3 text-muted-foreground hover:text-foreground">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              )}

              {showMentionInput && (
                <div className="flex items-center gap-2 animate-in slide-in-from-bottom-2">
                  <div className="flex-1 relative flex items-center">
                    <AtSign className="w-4 h-4 text-muted-foreground absolute left-3" />
                    <Input
                      placeholder="Gắt thẻ (tên đăng nhập, cách nhau bằng dấu phẩy)"
                      className="pl-9 h-9 w-full bg-muted/50 border-border text-sm rounded-none"
                      value={storyMentionsInput}
                      onChange={(e) => setStoryMentionsInput(e.target.value)}
                      autoFocus
                    />
                  </div>
                </div>
              )}

              <div className="flex items-center gap-2">
                <label className="cursor-pointer h-10 w-10 flex items-center justify-center bg-muted/50 hover:bg-muted rounded-none transition-colors border border-border shrink-0" title="Ảnh / Video">
                  {isStoryUploading ? <div className="w-4 h-4 rounded-none border-2 border-foreground border-t-transparent animate-spin"/> : <ImageIcon className="w-5 h-5 text-foreground" />}
                  <input type="file" className="hidden" accept="image/*" onChange={handleStoryImageUpload} />
                </label>
              </div></div></div></div>)}
      {viewingStoryMode && activeStoryIndex >= 0 && stories[activeStoryIndex] && (
            <div className="fixed inset-0 z-[200] bg-black/95 backblur-sm flex justify-center items-center animate-in fade-in-0 duration-200 text-white">
              <div className="absolute top-4 right-4 z-[210] flex gap-4 hidden md:flex">
                <button onClick={() => { setViewingStoryMode(false); setStoryProgress(0); }} className="text-white hover:text-gray-300 p-2 bg-white/10 hover:bg-white/20 rounded-none transition-colors  backblur-md">
                  <X className="w-6 h-6"/>
                </button>
              </div>
              
              <div className="flex-1 flex flex-col justify-between items-center relative overflow-hidden w-full max-w-sm mx-auto h-[100dvh] md:h-[85vh] md:w-[400px] group md:  md:border border-border/50"
                   style={{ backgroundColor: stories[activeStoryIndex].background_color || '#18181b' }}>
                 

                 <div className="absolute top-0 left-0 right-0 px-2 pt-2 flex gap-1 z-[205] w-full bg-gradient-to-b from-black/50 to-transparent pb-4">
                    {stories.map((s, idx) => (
                      <div key={s.id} className="flex-1 h-[3px] bg-white/30 rounded-none overflow-hidden backblur-md">
                        <div 
                          className="h-full bg-white transition-all ease-linear duration-100"
                          style={{ width: idx < activeStoryIndex ? '100%' : idx === activeStoryIndex ? `${storyProgress}%` : '0%'}}
                        />
                      </div>
                    ))}
                 </div>
                 

                 <button onClick={() => { setViewingStoryMode(false); setStoryProgress(0); }} className="absolute top-4 right-4 z-[210] text-white hover:text-gray-300 p-1 bg-black/20 hover:bg-black/40 rounded-none transition-colors  backblur-md md:hidden">
                    <X className="w-5 h-5"/>
                 </button>

                 {stories[activeStoryIndex].media_url && (
                    <div className="absolute inset-0 w-full h-full flex flex-col justify-center items-center">
                      <img src={stories[activeStoryIndex].media_url} className="absolute inset-0 w-full h-full object-cover" />
                      <div className="absolute inset-0 bg-black/30" />
                      <div className="w-full px-6 flex-1 flex flex-col gap-6 justify-center items-center overflow-hidden z-10">
                        {stories[activeStoryIndex].text_content && (
                          <h2 className="text-2xl font-bold text-center max-w-full leading-snug break-words mb-4" 
                              style={{ 
                                color: stories[activeStoryIndex].text_color || '#ffffff',
                                fontFamily: stories[activeStoryIndex].font_style === 'mono' ? 'Courier New, monospace' : 'inherit', 
                              }}>
                              {stories[activeStoryIndex].text_content}
                          </h2>
                        )}
                        {stories[activeStoryIndex].link_url && (
                            <a 
                              href={stories[activeStoryIndex].link_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-2 px-5 py-2.5 bg-white/20 hover:bg-white/30 backblur-md rounded-none text-white font-semibold  transition-all border border-white/20 max-w-[80%]"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <Globe className="w-4 h-4 shrink-0" />
                              <span className="truncate text-sm">{stories[activeStoryIndex].link_url}</span>
                            </a>
                        )}
                        {stories[activeStoryIndex].poll_data ? (
                          <div className="w-full max-w-[280px] bg-black/40 backblur-md  border border-white/20 p-4 z-10  flex flex-col gap-2 pointer-events-auto" onClick={(e) => e.stopPropagation()}>
                            <h4 className="text-white text-sm font-bold text-center mb-2">{stories[activeStoryIndex].poll_data.question}</h4>
                            {stories[activeStoryIndex].poll_data.options.map((opt: string, idx: number) => {
                              const totalVotes = Object.keys(stories[activeStoryIndex].poll_data.voters || {}).length;
                              const myVote = (stories[activeStoryIndex].poll_data.voters || {})[(currentUser?._id || "")];
                              const hasVoted = myVote !== undefined;
                              const optsVotes = Object.values(stories[activeStoryIndex].poll_data.voters || {}).filter(v => v === idx).length;
                              const percent = totalVotes > 0 ? Math.round((optsVotes / totalVotes) * 100) : 0;
                              
                              return (
                                <button 
                                  key={idx}
                                  onClick={() => !hasVoted && votePoll(stories[activeStoryIndex].id || stories[activeStoryIndex]._id, idx)}
                                  className={`relative w-full  text-white text-sm border overflow-hidden font-medium transition-all ${myVote === idx ? 'border-primary bg-primary/20' : 'border-white/20 bg-white/10'} ${(hasVoted) ? 'cursor-default' : 'hover:bg-white/20 cursor-pointer'} `}
                                >
                                  <div className="absolute top-0 bottom-0 left-0 bg-white/20 transition-all duration-500" style={{ width: hasVoted ? `${percent}%` : '0%' }} />
                                  <div className="relative px-3 py-2.5 flex justify-between items-center z-10">
                                    <span className="truncate pr-2">{opt}</span>
                                    {hasVoted && <span className="font-bold text-xs">{percent}%</span>}
                                  </div>
                                </button>
                              );
                            })}
                            <div className="text-white/50 text-[12px] text-center mt-1 font-bold tracking-widest">{Object.keys(stories[activeStoryIndex].poll_data.voters || {}).length} votes</div>
                          </div>
                        ) : stories[activeStoryIndex].quiz_data ? (
                          <div className="w-full max-w-[280px] bg-black/40 backblur-md  border border-white/20 p-4 z-10  flex flex-col gap-2 pointer-events-auto" onClick={(e) => e.stopPropagation()}>
                            <div className="text-center font-bold text-xs tracking-widest text-primary/80">Trắc Nghiệm</div>
                            <h4 className="text-white text-sm font-bold text-center mb-2">{stories[activeStoryIndex].quiz_data.question}</h4>
                            {stories[activeStoryIndex].quiz_data.options.map((opt: string, idx: number) => {
                              const myAnswer = (stories[activeStoryIndex].quiz_data.answers || {})[(currentUser?._id || "")];
                              const hasAnswered = myAnswer !== undefined;
                              const isCorrect = idx === stories[activeStoryIndex].quiz_data.correct_idx;
                              
                              let buttonClass = 'border-white/20 bg-white/10 hover:bg-white/20 cursor-pointer';
                                if (hasAnswered) {
                                  buttonClass = isCorrect ? 'border-black bg-black text-white cursor-default' : (myAnswer === idx ? 'border-zinc-300 bg-zinc-100 text-zinc-400 cursor-default' : 'border-white/20 bg-black/20 opacity-50 cursor-default');
                                }

                              return (
                                <button 
                                  key={idx}
                                  onClick={() => !hasAnswered && answerQuiz(stories[activeStoryIndex].id || stories[activeStoryIndex]._id, idx)}
                                  className={`relative w-full  text-white text-sm border overflow-hidden font-medium transition-all ${buttonClass}`}
                                >
                                  <div className="relative px-3 py-2.5 flex justify-between items-center z-10">
                                    <span className="truncate pr-2">{opt}</span>
                                    {hasAnswered && isCorrect && <CheckCircle className="w-4 h-4 text-white" />}
                                    {hasAnswered && !isCorrect && myAnswer === idx && <XCircle className="w-4 h-4 text-zinc-400" />}
                                  </div>
                                </button>
                              );
                            })}
                          </div>
                        ) : null}
                      </div>
                    </div>
                 )}
                 

                 <div className="absolute top-6 left-4 flex gap-2.5 items-center z-[210] p-1.5 pr-4 max-w-[80%]">
                   <div className="w-10 h-10 rounded-none flex justify-center items-center overflow-hidden shrink-0 bg-secondary relative">
                      {stories[activeStoryIndex].user?.avatar_url ? (
                        <img src={stories[activeStoryIndex].user.avatar_url} className="w-full h-full object-cover rounded-none" />
                      ) : (
                        <span className="text-foreground font-bold text-sm bg-muted/50 w-full h-full flex justify-center items-center rounded-none backblur-md">
                          {stories[activeStoryIndex].user?.name?.[0]?.toUpperCase() || "A"}
                        </span>
                      )}
                   </div>
                   <div className="flex flex-col justify-center">
                     <span className="text-sm font-semibold tracking-tight text-white ">
                        {stories[activeStoryIndex].user?.name || "Người dùng"}
                        {stories[activeStoryIndex].mentions && stories[activeStoryIndex].mentions.length > 0 && (
                          <span className="text-xs font-normal opacity-90 ml-1">
                            cùng với {stories[activeStoryIndex].mentions.length} người khác
                          </span>
                        )}
                     </span>
                     <span className="text-[12px] font-medium opacity-80 text-white ">{new Date(stories[activeStoryIndex].created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                   </div>
                 </div>
                 
                 {!stories[activeStoryIndex].media_url && (
                   <div className="w-full px-6 flex-1 flex flex-col gap-6 justify-center items-center overflow-hidden z-10">
                     <h2 className="text-2xl font-bold text-center max-w-full leading-snug  break-words" 
                        style={{ 
                          color: stories[activeStoryIndex].text_color || '#ffffff',
                          fontFamily: stories[activeStoryIndex].font_style === 'mono' ? 'Courier New, monospace' : 'inherit' 
                        }}>
                        {stories[activeStoryIndex].text_content}
                     </h2>
                     {stories[activeStoryIndex].link_url && (
                        <a 
                          href={stories[activeStoryIndex].link_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-5 py-2.5 bg-white/20 hover:bg-white/30 backblur-md rounded-none text-white font-semibold  transition-all border border-white/20 max-w-[80%]"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Globe className="w-4 h-4 shrink-0" />
                          <span className="truncate text-sm">{stories[activeStoryIndex].link_url}</span>
                        </a>
                     )}
                     {stories[activeStoryIndex].poll_data ? (
                          <div className="w-full max-w-[280px] bg-black/40 backblur-md  border border-white/20 p-4 z-10  flex flex-col gap-2 pointer-events-auto" onClick={(e) => e.stopPropagation()}>
                            <h4 className="text-white text-sm font-bold text-center mb-2">{stories[activeStoryIndex].poll_data.question}</h4>
                            {stories[activeStoryIndex].poll_data.options.map((opt: string, idx: number) => {
                              const totalVotes = Object.keys(stories[activeStoryIndex].poll_data.voters || {}).length;
                              const myVote = (stories[activeStoryIndex].poll_data.voters || {})[(currentUser?._id || "")];
                              const hasVoted = myVote !== undefined;
                              const optsVotes = Object.values(stories[activeStoryIndex].poll_data.voters || {}).filter(v => v === idx).length;
                              const percent = totalVotes > 0 ? Math.round((optsVotes / totalVotes) * 100) : 0;
                              
                              return (
                                <button 
                                  key={idx}
                                  onClick={() => !hasVoted && votePoll(stories[activeStoryIndex].id || stories[activeStoryIndex]._id, idx)}
                                  className={`relative w-full  text-white text-sm border overflow-hidden font-medium transition-all ${myVote === idx ? 'border-primary bg-primary/20' : 'border-white/20 bg-white/10'} ${hasVoted ? 'cursor-default' : 'hover:bg-white/20 cursor-pointer'} `}
                                >
                                  <div className="absolute top-0 bottom-0 left-0 bg-white/20 transition-all duration-500" style={{ width: hasVoted ? `${percent}%` : '0%' }} />
                                  <div className="relative px-3 py-2.5 flex justify-between items-center z-10">
                                    <span className="truncate pr-2">{opt}</span>
                                    {hasVoted && <span className="font-bold text-xs">{percent}%</span>}
                                  </div>
                                </button>
                              );
                            })}
                            <div className="text-white/50 text-[12px] text-center mt-1 font-bold tracking-widest">{Object.keys(stories[activeStoryIndex].poll_data.voters || {}).length} votes</div>
                          </div>
                      ) : stories[activeStoryIndex].quiz_data ? (
                          <div className="w-full max-w-[280px] bg-black/40 backblur-md  border border-white/20 p-4 z-10  flex flex-col gap-2 pointer-events-auto" onClick={(e) => e.stopPropagation()}>
                            <div className="text-center font-bold text-xs tracking-widest text-primary/80">Trắc Nghiệm</div>
                            <h4 className="text-white text-sm font-bold text-center mb-2">{stories[activeStoryIndex].quiz_data.question}</h4>
                            {stories[activeStoryIndex].quiz_data.options.map((opt: string, idx: number) => {
                              const myAnswer = (stories[activeStoryIndex].quiz_data.answers || {})[(currentUser?._id || "")];
                              const hasAnswered = myAnswer !== undefined;
                              const isCorrect = idx === stories[activeStoryIndex].quiz_data.correct_idx;
                              
                              let buttonClass = 'border-white/20 bg-white/10 hover:bg-white/20 cursor-pointer';
                                if (hasAnswered) {
                                  buttonClass = isCorrect ? 'border-black bg-black text-white cursor-default' : (myAnswer === idx ? 'border-zinc-300 bg-zinc-100 text-zinc-400 cursor-default' : 'border-white/20 bg-black/20 opacity-50 cursor-default');
                                }

                              return (
                                <button 
                                  key={idx}
                                  onClick={() => !hasAnswered && answerQuiz(stories[activeStoryIndex].id || stories[activeStoryIndex]._id, idx)}
                                  className={`relative w-full  text-white text-sm border overflow-hidden font-medium transition-all ${buttonClass}`}
                                >
                                  <div className="relative px-3 py-2.5 flex justify-between items-center z-10">
                                    <span className="truncate pr-2">{opt}</span>
                                    {hasAnswered && isCorrect && <CheckCircle className="w-4 h-4 text-white" />}
                                    {hasAnswered && !isCorrect && myAnswer === idx && <XCircle className="w-4 h-4 text-zinc-400" />}
                                  </div>
                                </button>
                              );
                            })}
                          </div>
                        ) : null}
                   </div>
                 )}


                 <div className="absolute top-0 bottom-0 left-0 w-1/4 z-[200] cursor-pointer" onClick={(e) => { e.stopPropagation(); handleStoryPrev(); }} />
                 <div className="absolute top-0 bottom-0 right-0 w-1/4 z-[200] cursor-pointer" onClick={(e) => { e.stopPropagation(); handleStoryNext(); }} />
                 

                 <div className="absolute bottom-4 left-0 right-0 w-full px-4 z-[205] flex justify-between items-center gap-3">
                    {(stories[activeStoryIndex].user._id === (currentUser?._id || "") || stories[activeStoryIndex].user._id === (currentUser?._id || "")) ? (
                      <div
                        className="bg-black/40  px-4 py-2.5 text-sm text-white border border-white/20 w-full flex justify-between items-center cursor-pointer hover:bg-black/50 transition-colors"
                        onClick={() => {
                          const storyId = stories[activeStoryIndex].id || stories[activeStoryIndex]._id;
                          setShowViewerList(!showViewerList);
                          if (!showViewerList) fetchStoryViewers(storyId);
                        }}
                      >
                        <span className="flex items-center gap-2 font-medium">
                          <Eye className="w-4 h-4" />
                          {stories[activeStoryIndex]?.viewer_count || 0} lượt xem
                        </span>
                        <div className="flex -space-x-1.5">
                          {storyViewers.slice(0, 3).map((v: any, i: number) => (
                            <div key={i} className="w-6 h-6 rounded-none bg-white/20 border border-white/40 overflow-hidden flex items-center justify-center text-[12px] font-bold">
                              {v.avatar_url ? (
                                <img src={v.avatar_url} className="w-full h-full object-cover" />
                              ) : (
                                v.full_name?.[0]?.toUpperCase() || "?"
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex-1 relative flex items-center">
                          <input 
                            type="text" 
                            placeholder={`Trả lời ${stories[activeStoryIndex].user?.name || 'Tin này'}`} 
                            className="w-full bg-black/30 border border-white/30  px-4 py-2.5 pr-12 text-sm text-white placeholder-white/70 outline-none focus:bg-black/50 focus:border-white/50 transition-all"
                            value={replyMessage}
                            onChange={(e) => setReplyMessage(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') submitReplyStory(stories[activeStoryIndex].id || stories[activeStoryIndex]._id);
                            }}
                          />
                          {replyMessage.trim() && (
                            <button 
                              onClick={() => submitReplyStory(stories[activeStoryIndex].id || stories[activeStoryIndex]._id)}
                              disabled={isReplying}
                              className="absolute right-2 p-1.5 text-white hover:text-white/80 transition-colors"
                            >
                              <Send className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                        <button 
                          onClick={() => reactToStory(stories[activeStoryIndex].id || stories[activeStoryIndex]._id)}
                          className="text-white active:scale-95 transition-transform bg-white/10 hover:bg-white/20 p-2.5 "
                        >
                          <Heart className="w-5 h-5" />
                        </button>
                      </>
                    )}
                 </div>

                 {showViewerList && (stories[activeStoryIndex].user._id === (currentUser?._id || "") || stories[activeStoryIndex].user._id === (currentUser?._id || "")) && (
                   <div className="absolute bottom-20 left-4 right-4 z-[210] bg-black/80 border border-white/20  p-4 animate-in slide-in-from-bottom-4 duration-200 max-h-64 overflow-y-auto">
                     <div className="flex items-center justify-between mb-3">
                       <span className="text-white text-xs font-bold tracking-widest">Người đã xem</span>
                       <button onClick={() => setShowViewerList(false)} className="text-white/50 hover:text-white">
                         <X className="w-4 h-4" />
                       </button>
                     </div>
                     {isFetchingViewers ? (
                       <div className="text-white/50 text-xs text-center py-4">Đang tải</div>
                     ) : storyViewers.length === 0 ? (
                       <div className="text-white/50 text-xs text-center py-4">Chưa có ai xem tin này.</div>
                     ) : storyViewers.map((v: any, i: number) => (
                       <div key={i} className="flex items-center gap-3 py-2 border-b border-white/10 last:border-0">
                         <div className="w-8 h-8  bg-white/20 border border-white/30 flex items-center justify-center text-sm font-bold text-white overflow-hidden">
                           {v.avatar_url ? (
                             <img src={v.avatar_url} className="w-full h-full object-cover" />
                           ) : (
                             v.full_name?.[0]?.toUpperCase() || "?"
                           )}
                         </div>
                         <div>
                           <p className="text-white text-xs font-bold">{v.full_name || "Ẩn danh"}</p>
                           <p className="text-white/50 text-[12px]">{new Date(v.viewed_at).toLocaleTimeString('vi-VN', {hour: '2-digit', minute: '2-digit'})}</p>
                         </div>
                       </div>
                     ))}
                   </div>
                 )}
              </div>
            </div>
          )}


      {translationModal && (
        <div className="fixed inset-0 z-[400] bg-black/60 backblur-sm flex items-end sm:items-center justify-center animate-in fade-in-0 duration-150 p-4">
          <div className="bg-card border border-border  w-full max-w-lg  animate-in slide-in-from-bottom-4 sm:slide-in-from-bottom-0">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <h3 className="font-semibold text-sm text-foreground">Bản dịch tự động</h3>
              <button onClick={() => setTranslationModal(null)} className="text-muted-foreground hover:text-foreground transition-colors p-1  hover:bg-muted">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-5">
              <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{translationModal.text}</p>
            </div>
            <div className="px-5 py-3 border-t border-border flex justify-end">
              <button onClick={() => setTranslationModal(null)} className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors px-4 py-1.5  hover:bg-muted">
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}