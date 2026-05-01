"use client";

import React, { useEffect, useState, useCallback } from "react";
import AppShell from "@/app/components/AppShell";
import Link from "next/link";
import { getToken, getAuthHeaders, API_URL } from "@/app/lib/api";
import { Heart, MessageCircle, Globe, Sparkles, Users, User as UserIcon, Lock, Share2, PlusSquare, ArrowUp, Send, CheckCircle, XCircle, X, Bookmark, BookText, BarChart2, Trash2, Trophy, EyeOff, Edit3, Flag, Eye, Image as ImageIcon, Quote, PenTool, Book, FileText, HelpCircle, AtSign, Pin, Archive, Link as LinkIcon, Plus, Lightbulb, Flame, Smile, Coins, TrendingUp, Hash, ArrowUpRight, ChevronRight, RotateCw } from "lucide-react";
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
              'bg-white text-zinc-900 border-zinc-200'
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
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);

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
          headers: getAuthHeaders()
        }).catch(e => console.error("Error viewing story:", e));
      }
    }
  }, [viewingStoryMode, activeStoryIndex]);

  const reactToStory = async (storyId: string) => {
    try {
      await fetch(`${API_URL}/social/stories/${storyId}/react?reaction_type=heart`, {
        method: "POST", headers: getAuthHeaders()
      });
      showToast("Đã phản hồi tin", "success");
    } catch(e) { console.error("Reaction err:", e) }
  };

  const fetchStoryViewers = async (storyId: string) => {
    setIsFetchingViewers(true);
    try {
      const res = await fetch(`${API_URL}/social/stories/${storyId}/viewers`, {
        headers: getAuthHeaders()
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
        method: "POST", headers: getAuthHeaders()
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
        method: "POST", headers: getAuthHeaders()
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
        method: "POST", headers: getAuthHeaders()
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
        const res = await fetch(`${API_URL}/documents?q=${encodeURIComponent(match[2])}&limit=5`, { headers: getAuthHeaders() });
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
        headers: getAuthHeaders(),
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
    if (showStoryArchive) {
      fetchArchivedStories();
    }
    if (currentUser && currentUser._id) {
      fetchSuggestions();
      fetchWallet();
    }
  }, [(currentUser?._id || ""), showStoryArchive]);

  const fetchSuggestions = async () => {
    try {
      const res = await fetch(`${API_URL}/social/intersection-friends`, { headers: getAuthHeaders() });
      if (res.ok) {
        const json = await res.json();
        setSuggestions(json.data?.suggestions || json.suggestions || []);
      }
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
      await fetch(`${API_URL}/social/posts/${postId}/view`, { method: "POST", headers: getAuthHeaders() });
    } catch(e) { console.error("API error:", e); }
  };

  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const fetchFeed = async (reset = false) => {
    try {
      const skip = reset ? 0 : page * 10;
      const limit = 10;
      const res = await fetch(`${API_URL}/social/feed?tab=${tab}&skip=${skip}&limit=${limit}${itemType ? `&item_type=${itemType}` : ''}${filter === 'trending' ? '&sort=trending' : ''}`, { headers: getAuthHeaders() });
      if (res.ok) {
        const json = await res.json();
        const newData = json.data || json;
        setPosts(prev => reset ? newData : [...prev, ...newData]);
        if (newData.length < limit) setHasMore(false);
        else setHasMore(true);
        if (!reset) setPage(p => p + 1);
        else setPage(1);
      } else throw new Error();

      const tagRes = await fetch(`${API_URL}/social/trending-tags`, { headers: getAuthHeaders() });
      if (tagRes.ok) {
        const tagJson = await tagRes.json();
        setTrendingTags(tagJson.data || tagJson);
      }
      
      const booksRes = await fetch(`${API_URL}/social/suggested-documents`, { headers: getAuthHeaders() });
      if (booksRes.ok) {
        const booksJson = await booksRes.json();
        setDocumentSuggestions(booksJson.data || booksJson);
      }
    } catch (error) {
      if (reset) showToast("Không thể tải bảng tin lúc này, vui lòng thử lại sau.", "error");
    } finally {
      setLoading(false);
    }
  };

  const fetchStories = async () => {
    try {
      const res = await fetch(`${API_URL}/social/stories`, { headers: getAuthHeaders() });
      if (res.ok) {
        const json = await res.json();
        setStories((json.data?.stories || json.data || json.stories || []));
      }
    } catch(e) { console.error("API error:", e); }
  };

  const fetchArchivedStories = async () => {
    try {
      const res = await fetch(`${API_URL}/social/stories/me/archive`, { headers: getAuthHeaders() });
      if (res.ok) {
        const json = await res.json();
        setArchivedStories((json.data?.stories || json.data || json.stories || []));
      }
    } catch(e) { console.error("API error:", e); }
  };

  const fetchRanking = async () => {
    try {
      const res = await fetch(`${API_URL}/social/ranking`, { headers: getAuthHeaders() });
      if (res.ok) {
        const json = await res.json();
        setRanking(json.data || json || []);
      }
    } catch(e) { console.error("API error:", e); }
  };

  const fetchReaderRanking = async () => {
    try {
      const res = await fetch(`${API_URL}/social/reader-ranking`, { headers: getAuthHeaders() });
      if (res.ok) {
        const json = await res.json();
        setReaderRanking(json.data || json || []);
      }
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
        method: "POST", headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
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

  const deleteStory = async (storyId: string) => {
    if (!confirm("Bạn có chắc chắn muốn xóa tin này không?")) return;
    try {
      const res = await fetch(`${API_URL}/social/stories/${storyId}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });
      if (res.ok) {
        showToast("Đã xóa tin thành công", "success");
        setViewingStoryMode(false);
        fetchStories();
      }
    } catch (e) {
      console.error("API error:", e);
    }
  };

  const repostPost = async (postId: string) => {
    if (!currentUser) return showToast("Vui lòng đăng nhập để thực hiện.", "error");
    try {
      const res = await fetch(`${API_URL}/social/posts/${postId}/repost`, {
        method: "POST",
        headers: getAuthHeaders()
      });
      if (res.ok) {
        showToast("Đã chia sẻ lại bài viết thành công", "success");
        fetchFeed(true);
      } else {
        const json = await res.json();
        showToast(json.message || "Không thể chia sẻ lại bài viết", "error");
      }
    } catch (e) { 
      showToast("Lỗi kết nối máy chủ", "error"); 
    }
  };


  const translatePost = async (postId: string, text: string) => {
    if (isTranslating) return;
    setIsTranslating(true);
    showToast("Đang dịch nội dung", "info");
    try {
      const res = await fetch(`${API_URL}/inference/translate`, {
        method: "POST",
        headers: { 
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text, target_lang: "vi" })
      });
      const json = await res.json();
      if (json.data?.result) {
        setTranslationModal({ text: json.data.result });
      } else {
        showToast("Không thể dịch nội dung này", "error");
      }
    } catch (e) {
      showToast("Lỗi kết nối dịch thuật", "error");
    } finally {
      setIsTranslating(false);
    }
  };

  const deletePost = async (postId: string) => {
    if(!confirm("Bạn có chắc chắn muốn xoá bài viết này không?")) return;
    try {
      const res = await fetch(`${API_URL}/social/posts/${postId}`, {
        method: "DELETE", headers: getAuthHeaders()
      });
      if (res.ok) {
        showToast("Đã xóa bài viết thành công", "success");
        fetchFeed(true);
      }
    } catch(e) { console.error("API error:", e); }
  };

  const fetchWallet = async () => {
    try {
      const res = await fetch(`${API_URL}/wallet/balance`, { headers: getAuthHeaders() });
      if (res.ok) {
        const json = await res.json();
        setWalletBalance(json.data?.balance || json.balance || 0);
      }
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
        headers: getAuthHeaders(),
        body: formData
      });
      const json = await res.json();
      if (res.ok) setMediaUrls(prev => [...prev, json.data?.url || json.url]);
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
        method: "POST", headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
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
      const res = await fetch(`${API_URL}/social/posts/${postId}/like?reaction_type=${reactionType}`, { method: "POST", headers: getAuthHeaders() });
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
        method: "POST", headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
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
        method: "POST", headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
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
      const res = await fetch(`${API_URL}/social/posts/${postId}/save`, { method: "POST", headers: getAuthHeaders() });
      if (res.ok) fetchFeed(true);
    } catch(e) { console.error("API error:", e); }
  };


  const submitPollVote = async (postId: string, optionId: string) => {
    try {
      const res = await fetch(`${API_URL}/social/polls/${postId}/vote/${optionId}`, { 
        method: "POST", headers: getAuthHeaders() 
      });
      if (res.ok) { showToast("Bình chọn thành công", "success"); fetchFeed(true); }
    } catch(e) { console.error("API error:", e); }
  };

  const [editingPostId, setEditingPostId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState("");


  const togglePinPost = async (postId: string) => {
    try { const res = await fetch(`${API_URL}/social/posts/${postId}/pin`, { method: "POST", headers: getAuthHeaders() }); if (res.ok) fetchFeed(true); } catch(e) { console.error("API error:", e); }
  };

  const reportPost = async (postId: string) => {
    const reason = prompt("Vui lòng nhập lý do báo cáo để Quản trị viên xem xét:");
    if (!reason || !reason.trim()) return;
    try { const res = await fetch(`${API_URL}/social/posts/${postId}/report?reason=${encodeURIComponent(reason)}`, { method: "POST", headers: getAuthHeaders() }); if (res.ok) showToast("Cảm ơn, báo cáo đã được ghi nhận.", "success"); } catch(e) { console.error("API error:", e); }
  };

  const hidePost = async (postId: string) => {
    try { const res = await fetch(`${API_URL}/social/posts/${postId}/hide`, { method: "POST", headers: getAuthHeaders() }); if (res.ok) { showToast("Đã ẩn.", "info"); fetchFeed(true); } } catch(e) { console.error("API error:", e); }
  };

  const followUser = async (userId: string) => {
    try { const res = await fetch(`${API_URL}/social/users/${userId}/follow`, { method: "POST", headers: getAuthHeaders() }); if (res.ok) { showToast((await res.json()).message, "success"); fetchSuggestions(); } } catch(e) { console.error("API error:", e); }
  };


  const updatePost = async (postId: string) => {
    if (!editingContent.trim()) return;
    try { 
      const res = await fetch(`${API_URL}/social/posts/${postId}`, { 
        method: "PUT", 
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }, 
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
    <>
      <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
        
        <div className="mb-12 border-b border-zinc-200 pb-10 transition-all duration-300">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="space-y-3">
              <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
                Bảng tin
              </h1>
              <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
                Kết nối và chia sẻ tri thức <Sparkles className="w-3.5 h-3.5 text-zinc-200" />
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex border border-zinc-200 p-1 bg-zinc-50/50 rounded-sm">
                 <button 
                    onClick={() => setFilter("recent")}
                    className={`px-6 py-2.5 text-[10px] font-bold tracking-[0.2em] uppercase transition-all rounded-sm ${filter === "recent" ? "bg-black text-white" : "text-zinc-400 hover:text-black"}`}
                 >
                    Mới nhất
                 </button>
                 <button 
                    onClick={() => setFilter("trending")}
                    className={`px-6 py-2.5 text-[10px] font-bold tracking-[0.2em] uppercase transition-all rounded-sm ${filter === "trending" ? "bg-black text-white" : "text-zinc-400 hover:text-black"}`}
                 >
                    Xu hướng
                 </button>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          
          <aside className="lg:col-span-3 space-y-10 order-2 lg:order-1">
            
            {currentUser && (
              <div className="bg-card border border-border p-8 text-center rounded-sm">
                <h3 className="text-[10px] font-bold text-muted-foreground tracking-[0.2em] uppercase mb-4">Số dư ví</h3>
                <div className="flex items-center justify-center gap-2 mb-6">
                  <span className="text-3xl font-bold tracking-tighter">{walletBalance.toLocaleString("vi-VN")}</span>
                  <Coins className="w-5 h-5 text-zinc-400" />
                </div>
                <Button size="sm" variant="outline" className="w-full text-[10px] font-bold uppercase tracking-widest rounded-none h-14 border-zinc-200 hover:bg-black hover:text-white transition-all" onClick={() => window.location.href = '/wallet'}>Quản lý ví</Button>
              </div>
            )}

            <div className="bg-card border border-border p-8 rounded-sm">
              <h3 className="text-[10px] font-bold text-foreground tracking-[0.2em] uppercase mb-6 border-b border-border pb-4 flex items-center gap-2">
                 <Trophy className="w-4 h-4" /> Bảng vinh danh Tác giả
              </h3>
              
              {ranking.length === 0 ? (
                <p className="text-[11px] text-muted-foreground font-bold tracking-widest text-center py-4">Chưa có dữ liệu</p>
              ) : ranking.map((r, i) => (
                <div key={i} className="flex gap-4 items-center group border-b border-border last:border-0 pb-4 mb-4 last:pb-0 last:mb-0">
                  <div className="w-10 h-10 bg-black text-white font-bold flex items-center shrink-0 justify-center text-[12px] border border-black tracking-tighter rounded-sm">
                    #{i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-[12px] font-bold tracking-widest text-foreground truncate uppercase">{r.full_name || "Tác giả ẩn danh"}</h4>
                    <span className="text-[10px] text-zinc-400 font-bold truncate flex items-center gap-1.5 tracking-widest uppercase"> 
                      {r.score.toLocaleString("vi-VN")} điểm
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {trendingTags.length > 0 && (
              <div className="bg-card border border-border p-8 rounded-sm">
                <h3 className="text-[10px] font-bold text-foreground tracking-[0.2em] uppercase mb-6 border-b border-border pb-4 flex items-center gap-2">
                  <Hash className="w-4 h-4" /> Xu hướng Hashtag
                </h3>
                <div className="flex flex-wrap gap-2">
                  {trendingTags.map((tag: any, i: number) => (
                    <Link 
                      key={i} 
                      href={`/search?q=${encodeURIComponent(tag.tag)}&type=posts`}
                      className="px-4 py-2 bg-zinc-50 border border-zinc-100 text-[10px] font-bold text-zinc-400 hover:border-black hover:text-black transition-all rounded-sm uppercase tracking-widest"
                    >
                      #{tag.tag}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-card border border-border p-8 rounded-sm">
              <h3 className="text-[10px] font-bold text-foreground tracking-[0.2em] uppercase mb-6 border-b border-border pb-4 flex items-center gap-2">
                 <Users className="w-4 h-4" /> Độc giả tích cực
              </h3>
              
              {readerRanking.length === 0 ? (
                <p className="text-[11px] text-muted-foreground font-bold tracking-widest text-center py-4">Chưa có dữ liệu</p>
              ) : readerRanking.map((r, i) => (
                <div key={i} className="flex gap-4 items-center group border-b border-border last:border-0 pb-4 mb-4 last:pb-0 last:mb-0">
                  <div className="w-10 h-10 bg-zinc-200 text-black font-bold flex items-center shrink-0 justify-center text-[12px] border border-zinc-200 tracking-tighter rounded-sm">
                    #{i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-[12px] font-bold tracking-widest text-foreground truncate uppercase">{r.full_name || "Độc giả ẩn danh"}</h4>
                    <span className="text-[10px] text-zinc-400 font-bold truncate flex items-center gap-1.5 tracking-widest uppercase"> 
                      {r.score.toLocaleString("vi-VN")} đóng góp
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-card border border-border p-8 rounded-sm">
              <h3 className="text-[10px] font-bold text-foreground tracking-[0.2em] uppercase mb-6 border-b border-border pb-4 flex items-center gap-2">
                <BookText className="w-4 h-4" /> Tài liệu đáng đọc
              </h3>
              {documentSuggestions.length === 0 ? (
                <p className="text-[11px] text-muted-foreground font-bold tracking-widest text-center py-4">Chưa có gợi ý</p>
              ) : (
                <div className="space-y-6 pt-1">
                  {documentSuggestions.map((b, i) => (
                    <div key={i} className="flex gap-4 items-center group cursor-pointer border border-transparent hover:border-zinc-200 p-2 transition-all rounded-sm">
                      <div className="w-12 h-16 bg-zinc-50 border border-zinc-200 rounded-sm shrink-0 flex items-center justify-center overflow-hidden grayscale group-hover:grayscale-0 transition-all">
                        <BookText className="w-6 h-6 text-zinc-200" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-[12px] font-bold tracking-widest text-foreground truncate group-hover:text-black transition-colors uppercase">{b.title}</h4>
                        <span className="text-[10px] text-zinc-400 font-bold tracking-widest uppercase">{b.mentions} đề xuất</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-card border border-border p-8 rounded-sm">
              <h3 className="text-[10px] font-bold text-foreground tracking-[0.2em] uppercase mb-6 border-b border-border pb-4 flex items-center gap-2">
                 <Users className="w-4 h-4" /> Gợi ý kết nối
              </h3>
              {suggestions.length === 0 ? (
                <p className="text-[11px] text-muted-foreground leading-relaxed font-bold uppercase tracking-widest text-center py-4">Không có gợi ý</p>
              ) : suggestions.map((s, i) => (
                <div key={i} className="flex gap-4 items-center group cursor-pointer border-b border-border last:border-0 pb-4 last:pb-0 mb-4 last:mb-0">
                  <div className="w-10 h-10 bg-black text-white font-bold flex items-center shrink-0 justify-center text-[12px] border border-black tracking-tighter rounded-sm">
                    {s.display_name?.[0]?.toUpperCase() || "A"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-[12px] font-bold tracking-widest text-foreground truncate uppercase">{s.display_name}</h4>
                    <span className="text-[10px] text-zinc-400 font-bold truncate tracking-widest uppercase">{s.total_match || 0} điểm chung</span>
                  </div>
                  <Button size="sm" variant="outline" onClick={() => { if(currentUser) followUser(s._id); else showToast("Vui lòng đăng nhập để thực hiện.", "error"); }} title="Theo dõi" className="h-8 px-4 text-[10px] font-bold uppercase tracking-widest rounded-none shrink-0 hover:bg-black hover:text-white transition-all border-zinc-200">
                    Theo dõi
                  </Button>
                </div>
              ))}
            </div>
          </aside>

          <main className="lg:col-span-9 space-y-12 order-1 lg:order-2">
            
            <div className="flex gap-4 overflow-x-auto pb-10 pt-2 hide-scrollbar -mx-4 px-4 md:mx-0 md:px-0 border-b border-zinc-100">
              <div 
                onClick={() => setShowStoryModal(true)}
                className="relative w-32 h-48 rounded-sm overflow-hidden cursor-pointer shrink-0 group bg-zinc-50 border border-zinc-200 flex flex-col hover:border-black transition-all duration-300"
              >
                <div className="flex-1 bg-zinc-200 relative overflow-hidden group-hover:brightness-95 transition-all">
                  {currentUser?.avatar_url ? (
                    <img src={currentUser.avatar_url} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Plus className="w-8 h-8 text-zinc-400" />
                    </div>
                  )}
                </div>
                <div className="p-3 bg-white text-center">
                  <span className="text-[10px] font-bold tracking-widest uppercase text-black">Tạo tin</span>
                </div>
              </div>

              {stories.map((story, idx) => (
                <div 
                  key={story.id} 
                  className="relative w-32 h-48 rounded-sm overflow-hidden cursor-pointer shrink-0 group bg-black border border-zinc-200 flex flex-col hover:border-black transition-all duration-300"
                >
                  <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-transparent to-black/60 z-10" onClick={() => { setActiveStoryIndex(idx); setViewingStoryMode(true); setStoryProgress(0); }}></div>
                  {story.media_url ? (
                    <img src={story.media_url} className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-300" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center p-4 text-center bg-zinc-900" style={{ color: story.text_color || '#ffffff' }}>
                      <span className="text-[10px] font-bold tracking-tighter leading-tight line-clamp-4">{story.text_content}</span>
                    </div>
                  )}
                  {currentUser && (story.user_id === currentUser.id || story.author_id === currentUser.id) && (
                    <button 
                      onClick={(e) => { e.stopPropagation(); deleteStory(story.id); }}
                      className="absolute top-2 right-2 z-20 h-8 w-8 bg-black/40 text-white flex items-center justify-center border border-white/20 hover:bg-red-500 hover:border-red-500 transition-all rounded-sm"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>

            <div className="space-y-12">
              
              {currentUser && (
                <div className="bg-white border border-zinc-200 p-8 rounded-sm flex flex-col transition-all duration-500 hover:border-black">
                  <div className="flex gap-6 items-start">
                    <div className="w-14 h-14 bg-zinc-900 rounded-sm border border-zinc-200 flex shrink-0 items-center justify-center text-white font-bold text-xl overflow-hidden relative cursor-pointer transition-all">
                      {currentUser?.avatar_url ? (
                        <img src={currentUser.avatar_url} className="w-full h-full object-cover" />
                      ) : (
                        currentUser?.display_name?.[0]?.toUpperCase() || "U"
                      )}
                    </div>
                    <div className="flex-1">
                      <textarea
                        id="composer-textarea"
                        className="w-full bg-transparent outline-none text-foreground resize-none min-h-[56px] text-xl font-bold tracking-tighter placeholder:text-muted-foreground placeholder:font-normal mt-1.5"
                        placeholder={`${(currentUser?.display_name || "") ? `${currentUser.display_name} ơi, ` : ''}bạn đang nghĩ gì thế?`}
                        value={content}
                        rows={isQuoteMode ? 2 : Math.max(1 + content.split('\n').length, 2)}
                        onChange={handleContentChange}
                      ></textarea>

                      <div className="relative">
                        {documentSuggestions.length > 0 && (
                          <div className="absolute top-full left-0 z-50 bg-white border border-zinc-200 mt-2 overflow-hidden w-full max-w-md animate-in slide-in-from-top-2 duration-300 rounded-sm">
                            <div className="px-6 py-4 bg-zinc-50 border-b border-zinc-100">
                              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.3em] flex items-center gap-2">
                                <BookText className="w-3.5 h-3.5" /> Gợi ý tài liệu
                              </span>
                            </div>
                            <div className="max-h-[300px] overflow-y-auto">
                              {documentSuggestions.map((doc: any, i: number) => (
                                <div 
                                  key={i} 
                                  className="px-6 py-4 hover:bg-zinc-50 cursor-pointer border-b border-zinc-50 last:border-0 flex justify-between items-center group transition-all" 
                                  onClick={() => selectAttachedDocument(doc)}
                                >
                                  <div className="flex-1 min-w-0 pr-4">
                                    <p className="text-[12px] font-bold text-black uppercase tracking-widest truncate group-hover:translate-x-1 transition-transform">
                                      {doc.title}
                                    </p>
                                    <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-tighter mt-1">
                                      {doc.author_name || doc.author || "Tác giả ẩn danh"}
                                    </p>
                                  </div>
                                  <ChevronRight className="w-4 h-4 text-zinc-200 group-hover:text-black transition-colors" />
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {attachedDocumentId && (
                        <div className="mt-6 p-6 bg-zinc-50 border border-zinc-200 rounded-sm flex items-center justify-between group animate-in fade-in duration-500">
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-14 bg-white border border-zinc-100 flex items-center justify-center shrink-0">
                               <BookText className="w-5 h-5 text-zinc-200" />
                            </div>
                            <div className="space-y-1">
                               <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Đã đính kèm</p>
                               <p className="text-[12px] font-bold text-black uppercase tracking-widest">{attachedDocumentTitle}</p>
                            </div>
                          </div>
                          <button 
                            onClick={() => { setAttachedDocumentId(""); setAttachedDocumentTitle(""); }}
                            className="p-3 text-zinc-300 hover:text-black transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      )}

                      {mediaUrls.length > 0 && (
                        <div className="grid grid-cols-2 gap-2 mt-6 overflow-hidden border border-border rounded-sm">
                          {mediaUrls.map((url, i) => (
                            <div key={i} className={`relative w-full aspect-square ${mediaUrls.length === 1 ? 'col-span-2 aspect-video' : ''}`}>
                              {url.match(/\.(mp4|webm)$/i) ? (
                                <video src={`${API_URL}${url}`} className="object-cover w-full h-full" autoPlay muted loop />
                              ) : (
                                <img src={`${API_URL}${url}`} alt="Preview" className="object-cover w-full h-full" />
                              )}
                              <button onClick={() => setMediaUrls(mediaUrls.filter((_, idx) => idx !== i))} className="absolute top-3 right-3 bg-black/60 hover:bg-black/80 text-white rounded-none w-10 h-10 flex items-center justify-center backblur-sm transition-colors">
                                <X className="w-6 h-6"/>
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {showExtras && (
                    <div className="mt-8 p-6 bg-zinc-50/50 space-y-4 border border-zinc-100 rounded-sm">
                      <div className="space-y-3">
                         <h4 className="text-[10px] font-bold text-muted-foreground flex items-center gap-2 uppercase tracking-widest"><BarChart2 className="w-4 h-4" /> Tạo bình chọn</h4>
                         <Input value={pollText1} onChange={e => setPollText1(e.target.value)} placeholder="Lựa chọn 1" className="h-12 bg-white text-xs font-bold border-zinc-200 rounded-sm focus-visible:ring-black" />
                         <Input value={pollText2} onChange={e => setPollText2(e.target.value)} placeholder="Lựa chọn 2" className="h-12 bg-white text-xs font-bold border-zinc-200 rounded-sm focus-visible:ring-black" />
                      </div>
                    </div>
                  )}

                  <div className="mt-8 pt-6 border-t border-zinc-100">
                    <div className="flex items-center justify-between">
                      <div className="flex gap-2">
                        <label className="cursor-pointer h-12 w-12 hover:bg-zinc-50 border border-zinc-100 rounded-sm transition-all flex items-center justify-center text-zinc-400 hover:text-black" title="Đính kèm Ảnh/Video">
                          <ImageIcon className="w-5 h-5" />
                          <input type="file" className="hidden" accept="image/*,video/*" multiple onChange={overrideFileUpload} />
                        </label>
                        <button onClick={() => setShowExtras(!showExtras)} className={`h-12 w-12 border transition-all rounded-sm flex items-center justify-center ${showExtras ? 'bg-black text-white border-black' : 'bg-white text-zinc-400 border-zinc-100 hover:border-black hover:text-black'}`} title="Thêm bình chọn">
                          <BarChart2 className="w-5 h-5" />
                        </button>
                        <button onClick={() => setIsQuoteMode(!isQuoteMode)} className={`h-12 w-12 border transition-all rounded-sm flex items-center justify-center ${isQuoteMode ? 'bg-black text-white border-black' : 'bg-white text-zinc-400 border-zinc-100 hover:border-black hover:text-black'}`} title="Chế độ Trích dẫn">
                          <Quote className="w-5 h-5" />
                        </button>
                      </div>
                      
                      <div className="flex items-center gap-4">
                        <select id="post-privacy" className="h-12 px-6 bg-zinc-50 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest outline-none cursor-pointer hover:bg-zinc-100 transition-all rounded-sm">
                          <option value="public">Công khai</option>
                          <option value="following">Người theo dõi</option>
                          <option value="private">Chỉ mình tôi</option>
                        </select>
                        <button 
                          onClick={createPost}
                          disabled={!content.trim() && mediaUrls.length === 0}
                          className="h-12 px-10 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] hover:bg-zinc-800 disabled:opacity-30 disabled:pointer-events-none transition-all active:scale-95 rounded-sm"
                        >
                          Đăng bài
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-6">
                <div className="bg-zinc-50 border border-zinc-200 text-xs py-5 px-8 flex items-center justify-between transition-all duration-300 rounded-sm">
                  <div className="flex items-center gap-4">
                    <Sparkles className="w-5 h-5 text-zinc-400" />
                    <span className="font-bold tracking-[0.2em] uppercase text-black">Phân tích bảng tin với AI</span>
                  </div>
                  <button 
                    onClick={async () => {
                      if (isSummarizing) return;
                      setIsSummarizing(true);
                      showToast("Đang phân tích bảng tin", "info");
                      try {
                        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/social/ai/feed-summary`, { 
                          headers: getAuthHeaders()
                        });
                        const json = await res.json();
                        if (json.data?.summary) {
                          setAiSummary(json.data.summary);
                          showToast("Đã xong", "success");
                        }
                      } catch (e) { showToast("Lỗi", "error"); }
                      finally { setIsSummarizing(false); }
                    }}
                    disabled={isSummarizing}
                    className="h-10 px-8 border border-black text-black font-bold uppercase text-[10px] tracking-widest hover:bg-black hover:text-white transition-all disabled:opacity-50 rounded-sm"
                  >
                    {isSummarizing ? "Đang xử lý" : "Bắt đầu tóm tắt"}
                  </button>
                </div>
                {aiSummary && (
                  <div className="bg-white p-8 border border-zinc-200 border-t-0 animate-in fade-in slide-in-from-top-4 duration-300 rounded-sm">
                    <p className="text-lg leading-relaxed text-black italic font-medium tracking-tight">
                      "{aiSummary}"
                    </p>
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-10">
                {loading ? (
                  <div className="space-y-8">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="h-60 bg-white border border-zinc-100 animate-pulse rounded-sm" />
                    ))}
                  </div>
                ) : posts.length === 0 ? (
                  <div className="text-center py-32 border border-dashed border-zinc-100 bg-zinc-50/30 rounded-sm">
                    <MessageCircle className="w-16 h-16 text-zinc-100 mx-auto mb-10 stroke-[1]" />
                    <h3 className="text-2xl font-bold tracking-tighter text-black uppercase">Chưa có nội dung nào</h3>
                    <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest mt-4">Hãy là người đầu tiên chia sẻ tri thức hôm nay</p>
                  </div>
                ) : posts.map(post => (
                  <div key={post.id} className="bg-white border border-zinc-200 p-10 hover:border-black transition-all duration-300 rounded-sm group">
                    <div className="flex items-center gap-6 mb-8">
                      <div className="w-14 h-14 bg-zinc-50 rounded-sm flex shrink-0 items-center justify-center text-zinc-300 font-bold border border-zinc-100 overflow-hidden relative">
                        {post.user?.avatar_url ? (
                          <img src={post.user.avatar_url} className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-300" />
                        ) : (
                          <UserIcon className="w-6 h-6 stroke-[1]" />
                        )}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-bold text-black text-lg tracking-tight uppercase group-hover:translate-x-1 transition-transform">{post.user?.username || "Người dùng ẩn danh"}</h4>
                        <div className="flex items-center gap-4 text-[10px] font-bold text-zinc-400 uppercase tracking-widest pt-1">
                          <span>{new Date(post.created_at).toLocaleString("vi-VN")}</span>
                          {post.is_pinned && <span className="flex items-center gap-1.5 text-black"><Pin className="w-3 h-3 fill-black" /> Đã ghim</span>}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => translatePost(post.id, post.content)} className="p-3 hover:bg-zinc-50 transition-all rounded-sm text-zinc-300 hover:text-black">
                          <Sparkles className="w-4 h-4" />
                        </button>
                        {(currentUser?._id || "") && (currentUser?._id === post.author_id || currentUser?._id === post.user_id) ? (
                          <>
                            <button onClick={() => togglePinPost(post.id)} className="p-3 hover:bg-zinc-50 transition-all rounded-sm text-zinc-300 hover:text-black">
                              <Pin className={`w-4 h-4 ${post.is_pinned ? 'fill-black text-black' : ''}`} />
                            </button>
                            <button onClick={() => deletePost(post.id)} className="p-3 hover:bg-zinc-50 transition-all rounded-sm text-zinc-300 hover:text-black">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        ) : (
                          <>
                            <button onClick={() => hidePost(post.id)} className="p-3 hover:bg-zinc-50 transition-all rounded-sm text-zinc-300 hover:text-black">
                              <EyeOff className="w-4 h-4" />
                            </button>
                            <button onClick={() => reportPost(post.id)} className="p-3 hover:bg-zinc-50 transition-all rounded-sm text-zinc-300 hover:text-black">
                              <Flag className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="space-y-6">
                      <p className="text-lg leading-relaxed text-black font-medium tracking-tight whitespace-pre-wrap">
                        {renderContentWithTags(post.content)}
                      </p>

                      {post.media_urls && post.media_urls.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border border-zinc-100 rounded-sm overflow-hidden">
                          {post.media_urls.map((url: string, i: number) => (
                            <div key={i} className={`relative overflow-hidden bg-zinc-50 ${post.media_urls.length === 1 ? 'md:col-span-2' : ''}`}>
                              {url.match(/\.(mp4|webm)$/i) ? (
                                <video src={`${API_URL}${url}`} className="w-full h-full object-cover" controls />
                              ) : (
                                <img src={`${API_URL}${url}`} alt="Feed" className="w-full h-full object-cover grayscale hover:grayscale-0 transition-all duration-500 cursor-pointer" />
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {post.attached_document_id && (
                        <Link href={`/documents/${post.attached_document_id}`} className="flex items-center justify-between p-6 bg-zinc-50 border border-transparent hover:border-black hover:bg-white transition-all duration-300 rounded-sm">
                          <div className="flex items-center gap-6">
                            <div className="w-12 h-16 bg-white border border-zinc-100 rounded-sm flex items-center justify-center shrink-0">
                               <BookText className="w-6 h-6 text-zinc-200" />
                            </div>
                            <div className="space-y-1">
                               <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Tài liệu đính kèm</p>
                               <h5 className="text-base font-bold text-black tracking-tight uppercase">{post.attached_document_title || "Xem tài liệu"}</h5>
                            </div>
                          </div>
                          <ChevronRight className="w-5 h-5 text-zinc-300" />
                        </Link>
                      )}
                    </div>

                    <div className="mt-10 pt-8 border-t border-zinc-50 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <button onClick={(e) => toggleLike(post.id, "like", e)} className={`h-12 px-6 flex items-center gap-3 border transition-all rounded-sm font-bold text-[11px] uppercase tracking-widest ${post.likes?.includes(currentUser?._id || "") ? 'bg-black text-white border-black' : 'bg-white text-zinc-400 border-zinc-100 hover:border-black hover:text-black'}`}>
                          <Heart className={`w-4 h-4 ${post.likes?.includes(currentUser?._id || "") ? 'fill-white' : ''}`} />
                          {post.likes?.length || 0}
                        </button>
                        <button onClick={() => setExpandedComments(expandedComments === post.id ? null : post.id)} className={`h-12 px-6 flex items-center gap-3 border border-zinc-100 bg-white text-zinc-400 hover:border-black hover:text-black transition-all rounded-sm font-bold text-[11px] uppercase tracking-widest`}>
                          <MessageCircle className="w-4 h-4" />
                          {(post.comments || []).length}
                        </button>
                      </div>

                      <div className="flex items-center gap-2">
                        <button onClick={() => toggleSave(post.id)} className={`h-12 w-12 flex items-center justify-center border transition-all rounded-sm ${post.saved ? 'bg-black text-white border-black' : 'bg-white text-zinc-400 border-zinc-100 hover:border-black hover:text-black'}`}>
                          <Bookmark className={`w-4 h-4 ${post.saved ? 'fill-white' : ''}`} />
                        </button>
                        <button onClick={() => repostPost(post.id)} className="h-12 w-12 flex items-center justify-center border border-zinc-100 bg-white text-zinc-400 hover:border-black hover:text-black transition-all rounded-sm" title="Chia sẻ lại">
                          <RotateCw className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {expandedComments === post.id && (
                      <div className="mt-6 bg-zinc-50/50 p-6 border border-zinc-100 rounded-sm animate-in slide-in-from-top-4 duration-300">
                        <div className="max-h-80 overflow-y-auto pr-4 space-y-6 mb-6">
                          {post.comments?.length > 0 ? post.comments.map((c: any, i: number) => (
                            <div key={i} className={`text-sm ${c.parent_id ? 'ml-10 relative pl-6 border-l border-zinc-200' : ''}`}>
                              <div className="flex justify-between w-full group">
                                <div className="space-y-1">
                                  <span className="font-bold text-black uppercase tracking-widest text-[10px]">{c.user.display_name || "Người dùng"}: </span>
                                  <p className="text-zinc-500 font-medium leading-relaxed">{c.content || c.text}</p>
                                </div>
                                {currentUser && (
                                  <span onClick={() => {
                                    setReplyToContext({ postId: post.id, commentId: c.id, userName: c.user.display_name || "Người dùng" });
                                    setCommentText("");
                                  }} className="text-black text-[10px] font-bold uppercase tracking-widest opacity-0 group-hover:opacity-100 cursor-pointer transition-all ml-4">Trả lời</span>
                                )}
                              </div>
                            </div>
                          )) : <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest italic text-center py-4">Chưa có bình luận</div>}
                        </div>
                        
                        {currentUser ? (
                          <div className="space-y-4">
                            {replyToContext && replyToContext.postId === post.id && (
                              <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex justify-between bg-white border border-zinc-100 p-3 rounded-sm">
                                <span>Đang trả lời <b className="text-black">{replyToContext.userName}</b></span>
                                <span className="cursor-pointer hover:text-black" onClick={() => setReplyToContext(null)}>Hủy bỏ</span>
                              </div>
                            )}
                            <div className="flex gap-4 items-center">
                              <Input
                                className="h-12 bg-white border-zinc-100 text-xs font-bold focus-visible:ring-black rounded-sm"
                                placeholder="Viết bình luận của bạn"
                                value={commentText}
                                onChange={(e) => setCommentText(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter') submitComment(post.id) }}
                              />
                              <Button onClick={() => submitComment(post.id)} className="h-12 w-12 bg-black text-white hover:bg-zinc-800 rounded-sm shrink-0">
                                <Send className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em] text-center py-4 bg-white border border-zinc-100 rounded-sm">
                            Đăng nhập để bình luận
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              {!loading && hasMore && (
                <div className="flex justify-center pt-10">
                  <button onClick={() => fetchFeed()} disabled={loading} className="h-16 px-16 bg-white border border-zinc-100 text-[11px] font-bold uppercase tracking-[0.2em] hover:border-black transition-all disabled:opacity-30 rounded-sm">
                    {loading ? "Đang tải" : "Xem thêm bài viết"}
                  </button>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>

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
                  <div className="absolute inset-0 bg-black/30" />
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
                          newOpts[idx] = e.target.value;
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
              </div>
            </div>
          </div>
        </div>
      )}
      {viewingStoryMode && activeStoryIndex >= 0 && stories[activeStoryIndex] && (
            <div className="fixed inset-0 z-[200] bg-black/95 backblur-sm flex justify-center items-center animate-in fade-in-0 duration-200 text-white">
              <div className="absolute top-4 right-4 z-[210] flex gap-4 hidden md:flex">
                {(stories[activeStoryIndex].user_id === (currentUser?._id || "") || stories[activeStoryIndex].author_id === (currentUser?._id || "")) && (
                  <button 
                    onClick={() => deleteStory(stories[activeStoryIndex].id || stories[activeStoryIndex]._id)} 
                    className="text-white hover:text-red-400 p-2 bg-white/10 hover:bg-white/20 rounded-none transition-colors backblur-md"
                    title="Xóa tin này"
                  >
                    <Trash2 className="w-6 h-6"/>
                  </button>
                )}
                <button onClick={() => { setViewingStoryMode(false); setStoryProgress(0); }} className="text-white hover:text-gray-300 p-2 bg-white/10 hover:bg-white/20 rounded-none transition-colors  backblur-md">
                  <X className="w-6 h-6"/>
                </button>
              </div>
              
              <div className="flex-1 flex flex-col justify-between items-center relative overflow-hidden w-full max-w-sm mx-auto h-[100dvh] md:h-[85vh] md:w-[400px] group md:  md:border border-border/50"
                   style={{ backgroundColor: stories[activeStoryIndex].background_color || '#18181b' }}>
                 <div className="absolute top-4 right-4 z-[210] flex gap-2 md:hidden">
                    {(stories[activeStoryIndex].user_id === (currentUser?._id || "") || stories[activeStoryIndex].author_id === (currentUser?._id || "")) && (
                      <button 
                        onClick={() => deleteStory(stories[activeStoryIndex].id || stories[activeStoryIndex]._id)} 
                        className="text-white hover:text-red-400 p-1 bg-black/20 hover:bg-black/40 rounded-none transition-colors backblur-md"
                        title="Xóa tin này"
                      >
                        <Trash2 className="w-5 h-5"/>
                      </button>
                    )}
                    <button onClick={() => { setViewingStoryMode(false); setStoryProgress(0); }} className="text-white hover:text-gray-300 p-1 bg-black/20 hover:bg-black/40 rounded-none transition-colors  backblur-md">
                        <X className="w-5 h-5"/>
                    </button>
                 </div>

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
                                  buttonClass = isCorrect ? 'border-black bg-black text-white cursor-default' : (myAnswer === idx ? 'border-zinc-300 bg-zinc-200 text-zinc-400 cursor-default' : 'border-white/20 bg-black/20 opacity-50 cursor-default');
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
                                  buttonClass = isCorrect ? 'border-black bg-black text-white cursor-default' : (myAnswer === idx ? 'border-zinc-300 bg-zinc-200 text-zinc-400 cursor-default' : 'border-white/20 bg-black/20 opacity-50 cursor-default');
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

    </>
  );
}