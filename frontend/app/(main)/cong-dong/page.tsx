"use client";

import React, { useEffect, useState, useCallback } from "react";
import Workspace from "@/components/Workspace";
import Link from "next/link";
import {
  getFeedAPI,
  toggleReactionAPI,
  getTrendingTagsAPI,
  getSuggestedDocumentsAPI,
  createPostAPI,
  deletePostAPI,
  repostPostAPI,
  savePostAPI,
  togglePinPostAPI as pinPostAPI,
  reportPostAPI,
  hidePostAPI,
  toggleFollowUserAPI as followUserAPI,
  votePollAPI as submitPollVoteAPI,
  recordPostViewAPI,
  uploadMediaAPI,
  getFriendSuggestionsAPI as getIntersectionFriendsAPI,
  getAIFeedSummaryAPI,
  updatePostAPI,
} from "@/services/social.service";
import { suggestEngagementAPI, createPostAPI as createPostAI, createStoryAPI as createStoryAI } from "@/services/ai.service";
import {
  getStoriesAPI,
  createStoryAPI,
  viewStoryAPI,
  reactToStoryAPI,
  getStoryViewersAPI,
  voteStoryPollAPI,
  answerStoryQuizAPI,
  replyStoryAPI,
  getArchivedStoriesAPI,
  deleteStoryAPI,
} from "@/services/story.service";
import { getSocialRankingAPI, getReaderRankingAPI } from "@/services/rank.service";
import { createCommentAPI } from "@/services/comment.service";
import { getDocumentsAPI } from "@/services/document.service";
import { translateTextAPI } from "@/services/inference.service";
import { getWalletBalanceAPI as getWalletAPI, getDetailedHistoryAPI as getTransactionsAPI, voteItemAPI } from "@/services/wallet.service";
import { API_URL } from "@/services/authentication.service";
import {
  Heart,
  MessageCircle,
  Globe,
  Sparkles,
  Users,
  User as UserIcon,
  Lock,
  Share2,
  PlusSquare,
  ArrowUp,
  Send,
  CheckCircle,
  XCircle,
  X,
  Bookmark,
  BookText,
  BarChart2,
  Trash2,
  Trophy,
  EyeOff,
  Edit3,
  Flag,
  Eye,
  Image as ImageIcon,
  Quote,
  PenTool,
  Book,
  FileText,
  HelpCircle,
  AtSign,
  Pin,
  Archive,
  Link as LinkIcon,
  Plus,
  Lightbulb,
  Flame,
  Smile,
  Coins,
  TrendingUp,
  Hash,
  ArrowUpRight,
  ChevronRight,
  RotateCw,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/contexts/Auth";
import { useToast } from "@/contexts/Toast";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";
import { parseUTC } from "@/lib/utils";

const getTimeElapsed = (dateString: string) => {
  const diff = Date.now() - parseUTC(dateString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${Math.max(1, mins)} phút trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} giờ trước`;
  return `${Math.floor(hours / 24)} ngày trước`;
};

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
  const [replyMessage, setReplyMessage] = useState("");
  const [isReplying, setIsReplying] = useState(false);
  const [storyMentionsInput, setStoryMentionsInput] = useState("");
  
  const [aiDraftPost, setAiDraftPost] = useState("");
  const [isAiDraftActive, setIsAiDraftActive] = useState(false);
  const [aiDraftStory, setAiDraftStory] = useState("");
  const [isAiDraftStoryActive, setIsAiDraftStoryActive] = useState(false);
  const [wasAiAppliedPost, setWasAiAppliedPost] = useState(false);
  const [wasAiAppliedStory, setWasAiAppliedStory] = useState(false);

  const applyAiDraftPost = () => {
    setContent(aiDraftPost);
    setWasAiAppliedPost(true);
    setAiDraftPost("");
    setIsAiDraftActive(false);
  };

  const discardAiDraftPost = () => {
    setAiDraftPost("");
    setIsAiDraftActive(false);
    setWasAiAppliedPost(false);
  };

  const applyAiDraftStory = () => {
    setStoryText(aiDraftStory);
    setWasAiAppliedStory(true);
    setAiDraftStory("");
    setIsAiDraftStoryActive(false);
  };

  const discardAiDraftStory = () => {
    setAiDraftStory("");
    setIsAiDraftStoryActive(false);
    setWasAiAppliedStory(false);
  };

  const [translationModal, setTranslationModal] = useState<{
    text: string;
  } | null>(null);
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
  const [deleteStoryConfirm, setDeleteStoryConfirm] = useState<string | null>(
    null
  );
  const [deletePostConfirm, setDeletePostConfirm] = useState<string | null>(
    null
  );
  const [reportModal, setReportModal] = useState<{
    postId: string;
    reason: string;
  } | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [giftModal, setGiftModal] = useState<{
    postId: string;
    authorId: string;
    amount: number;
  } | null>(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [isQuoteMode, setIsQuoteMode] = useState(false);
  const [engagementSuggestions, setEngagementSuggestions] = useState<Record<string, string[]>>({});
  const [isGeneratingSuggestions, setIsGeneratingSuggestions] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const savedDraft = localStorage.getItem("doclib_feed_draft");
    if (savedDraft) setContent(savedDraft);
  }, []);

  const [documentSuggestions, setDocumentSuggestions] = useState<any[]>([]);
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  const handleStoryNext = () => {
    if (activeStoryIndex < stories.length - 1) {
      setActiveStoryIndex(activeStoryIndex + 1);
      setStoryProgress(0);
    } else {
      setViewingStoryMode(false);
      setStoryProgress(0);
    }
  };

  const handleStoryPrev = () => {
    if (activeStoryIndex > 0) {
      setActiveStoryIndex(activeStoryIndex - 1);
      setStoryProgress(0);
    } else setStoryProgress(0);
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (viewingStoryMode && activeStoryIndex >= 0) {
      interval = setInterval(() => {
        setStoryProgress((prev) => {
          if (prev >= 100) return 100;
          return prev + 100 / (15000 / 100);
        });
      }, 100);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [viewingStoryMode, activeStoryIndex]);

  useEffect(() => {
    if (storyProgress >= 100 && viewingStoryMode) {
      handleStoryNext();
    }
  }, [storyProgress, viewingStoryMode]);

  useEffect(() => {
    if (
      viewingStoryMode &&
      activeStoryIndex >= 0 &&
      stories[activeStoryIndex]
    ) {
      const storyId =
        stories[activeStoryIndex].id || stories[activeStoryIndex]._id;
      if (storyId) {
        viewStoryAPI(storyId).catch((e) =>
          console.error("Error viewing story:", e)
        );
      }
    }
  }, [viewingStoryMode, activeStoryIndex]);

  const reactToStory = async (storyId: string) => {
    try {
      await reactToStoryAPI(storyId, "heart");
      showToast("Đã phản hồi tin", "success");
    } catch (e) {
      console.error("Reaction err:", e);
    }
  };

  const fetchStoryViewers = async (storyId: string) => {
    setIsFetchingViewers(true);
    try {
      const data = await getStoryViewersAPI(storyId);
      setStoryViewers(data.viewers || []);
    } catch (e) {
      console.error("Viewer fetch err:", e);
    } finally {
      setIsFetchingViewers(false);
    }
  };

  const votePoll = async (storyId: string, optionIdx: number) => {
    try {
      await voteStoryPollAPI(storyId, optionIdx);
      showToast("Đã bình chọn", "success");
      fetchStories();
    } catch (e) {
      console.error("Poll err:", e);
    }
  };

  const answerQuiz = async (storyId: string, optionIdx: number) => {
    try {
      await answerStoryQuizAPI(storyId, optionIdx);
      fetchStories();
    } catch (e: any) {
      console.error("Quiz err:", e);
      showToast(e.message || "Bạn đã trả lời quiz rồi.", "error");
    }
  };

  const submitReplyStory = async (storyId: string) => {
    if (!replyMessage.trim() || isReplying) return;
    setIsReplying(true);
    try {
      await replyStoryAPI(storyId, replyMessage);
      showToast("Đã gửi tin nhắn cho tác giả.", "success");
      setReplyMessage("");
    } catch (e: any) {
      console.error(e);
      showToast(e.message || "Lỗi khi gửi tin nhắn", "error");
    } finally {
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
        const data = await getDocumentsAPI(match[2], undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, 5);
        setDocumentSuggestions(data.data || data);
      } catch (e) {
        showToast("Lỗi hệ thống", "error");
      }
    } else {
      setDocumentSuggestions([]);
    }
  };

  const selectAttachedDocument = (doc: any) => {
    setAttachedDocumentId(doc.slug || doc.id);
    setAttachedDocumentTitle(doc.title);
    setContent(content.replace(/\/(book|document)\s+[^\n]+$/, ""));
    setDocumentSuggestions([]);
  };

  const [commentText, setCommentText] = useState("");
  const [replyToContext, setReplyToContext] = useState<{
    postId: string;
    commentId: string;
    userName: string;
  } | null>(null);
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

  const [storyTextPos, setStoryTextPos] = useState({ x: 0, y: 0 });
  const [isDraggingText, setIsDraggingText] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [storyStickers, setStoryStickers] = useState<any[]>([]);
  const [showEmojiMenu, setShowEmojiMenu] = useState(false);

  const [isDraggingSticker, setIsDraggingSticker] = useState<number | null>(null);

  const handleDragStart = (e: React.MouseEvent | React.TouchEvent, type: 'text' | 'sticker', id?: number) => {
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    
    if (type === 'text') {
      setIsDraggingText(true);
      setDragStart({ x: clientX - storyTextPos.x, y: clientY - storyTextPos.y });
    } else if (id !== undefined) {
      setIsDraggingSticker(id);
      const sticker = storyStickers.find(s => s.id === id);
      setDragStart({ x: clientX - sticker.x, y: clientY - sticker.y });
    }
  };

  const handleDragMove = (e: React.MouseEvent | React.TouchEvent) => {
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;

    if (isDraggingText) {
      setStoryTextPos({ x: clientX - dragStart.x, y: clientY - dragStart.y });
    } else if (isDraggingSticker !== null) {
      setStoryStickers(prev => prev.map(s => 
        s.id === isDraggingSticker ? { ...s, x: clientX - dragStart.x, y: clientY - dragStart.y } : s
      ));
    }
  };

  const handleDragEnd = () => {
    setIsDraggingText(false);
    setIsDraggingSticker(null);
  };

  const addSticker = (content: string, type: 'emoji' | 'icon' = 'emoji') => {
    setStoryStickers([...storyStickers, { id: Date.now(), content, type, x: 0, y: 0 }]);
    setShowEmojiMenu(false);
  };

  const handleStoryImageUpload = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (!e.target.files?.length) return;
    setIsStoryUploading(true);
    const formData = new FormData();
    formData.append("file", e.target.files[0]);
    try {
      const data = await uploadMediaAPI(formData);
      setStoryMediaUrl(data.data?.url || data.url);
    } catch (e: any) {
      showToast(e.message || "Lỗi mạng khi tải lên.", "error");
    } finally {
      setIsStoryUploading(false);
    }
  };
  const [ranking, setRanking] = useState<any[]>([]);
  const [readerRanking, setReaderRanking] = useState<any[]>([]);
  const [tab, setTab] = useState<"foryou" | "following">("foryou");

  const { user: currentUser } = useAuth();
  const { showToast } = useToast();
  const [itemType, setItemType] = useState<string>("");

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
    }
  }, [currentUser?._id || "", showStoryArchive]);

  const fetchSuggestions = async () => {
    try {
      const json = await getIntersectionFriendsAPI();
      setSuggestions(json.data?.suggestions || json.suggestions || []);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };

  const parseInlineStyles = (text: string) => {
    if (!text) return "";
    const inlineParts = text.split(
      /(https?:\/\/(?:www\.youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+|https?:\/\/open\.spotify\.com\/(?:track|album|playlist)\/[\w]+(?:.*)?|\*\*.*?\*\*|\*[^*]+\*|#[\w]+)/g
    );
    return inlineParts.map((part, i) => {
      const ytMatch = part.match(
        /https?:\/\/(?:www\.youtube\.com\/watch\?v=|youtu\.be\/)([\w-]+)/
      );
      if (ytMatch) {
        return (
          <div
            key={i}
            className="my-3 overflow-hidden border border-zinc-200 aspect-video max-w-md"
          >
            <iframe
              width="100%"
              height="100%"
              src={`https://www.youtube.com/embed/${ytMatch[1]}`}
              frameBorder="0"
              allowFullScreen
            ></iframe>
          </div>
        );
      }
      const spotMatch = part.match(
        /https?:\/\/open\.spotify\.com\/(track|album|playlist)\/([\w]+)(.*)/
      );
      if (spotMatch) {
        return (
          <div key={i} className="my-2 max-w-md">
            <iframe
              src={`https://open.spotify.com/embed/${spotMatch[1]}/${spotMatch[2]}`}
              width="100%"
              height="80"
              frameBorder="0"
              allow="encrypted-media"
            ></iframe>
          </div>
        );
      }
      if (part.match(/^\*\*(.*?)\*\*$/)) {
        return (
          <strong key={i} className="font-semibold text-black">
            {part.replace(/\*\*/g, "")}
          </strong>
        );
      }
      if (part === "*Nội dung được tạo bởi DocLib AI*") {
        return (
          <span key={i} className="block mt-2 text-[10px] text-zinc-400 italic leading-none">
            Nội dung được tạo bởi DocLib AI
          </span>
        );
      }
      if (part.match(/^\*(.*?)\*$/)) {
        return (
          <em key={i} className="italic text-zinc-600">
            {part.replace(/\*/g, "")}
          </em>
        );
      }
      if (part.match(/#[\w]+/)) {
        const tagName = part.substring(1);
        return (
          <Link
            key={i}
            href={`/tim-kiem?q=${encodeURIComponent(tagName)}`}
            className="text-black font-semibold hover:underline cursor-pointer transition-all"
          >
            {part}
          </Link>
        );
      }
      return part;
    });
  };

  const renderContentWithTags = (text: string) => {
    if (!text) return null;
    const normalizedText = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    const lines = normalizedText.split("\n");
    
    const cleanLines: string[] = [];
    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();
      if (trimmed === "") {
        if (cleanLines.length > 0 && cleanLines[cleanLines.length - 1] !== "") {
          cleanLines.push("");
        }
      } else {
        cleanLines.push(trimmed);
      }
    }
    
    if (cleanLines.length > 0 && cleanLines[cleanLines.length - 1] === "") {
      cleanLines.pop();
    }

    return cleanLines.map((line, i) => {
      if (line === "") {
        return <div key={i} className="h-2 first:mt-0" />;
      }
      const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
      if (headingMatch) {
        const level = headingMatch[1].length;
        const headingText = headingMatch[2];
        const className = "font-bold text-black block mt-3 mb-1 first:mt-0 " + (
          level === 1 ? "text-xl font-bold" :
          level === 2 ? "text-lg font-bold" :
          level === 3 ? "text-base font-semibold" : "text-sm font-semibold"
        );
        return (
          <span key={i} className={className}>
            {parseInlineStyles(headingText)}
          </span>
        );
      }
      if (line.startsWith("> ")) {
        return (
          <blockquote
            key={i}
            className="border-l-2 border-black pl-4 italic text-zinc-600 my-2 bg-zinc-50 py-1 first:mt-0"
          >
            {parseInlineStyles(line.substring(2))}
          </blockquote>
        );
      }
      const listMatch = line.match(/^\s*[-*]\s+(.*)$/);
      if (listMatch) {
        return (
          <span key={i} className="block pl-4 text-zinc-800 my-0.5 flex items-start gap-2 first:mt-0">
            <span className="shrink-0 text-zinc-400">•</span>
            <span>{parseInlineStyles(listMatch[1])}</span>
          </span>
        );
      }
      return (
        <div key={i} className="leading-relaxed first:mt-0">
          {parseInlineStyles(line)}
        </div>
      );
    });
  };

  useEffect(() => {
    const handleScroll = () => {
      if (
        window.innerHeight + document.documentElement.scrollTop >=
          document.documentElement.offsetHeight - 500 &&
        !loading &&
        hasMore
      ) {
        fetchFeed();
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [loading, hasMore, page]);

  const recordView = async (postId: string) => {
    try {
      await recordPostViewAPI(postId);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };



  const fetchFeed = async (reset = false) => {
    try {
      const skip = reset ? 0 : page * 10;
      const limit = 10;
      const json = await getFeedAPI(
        tab,
        skip,
        limit,
        itemType,
        filter === "trending" ? "trending" : undefined
      );
      const rawData = json.data || json || [];
      const newData = Array.isArray(rawData)
        ? rawData.map((item: any) => ({
            ...item,
            id: item.id || item._id,
          }))
        : [];
      setPosts((prev) => (reset ? newData : [...prev, ...newData]));
      if (newData.length < limit) setHasMore(false);
      else setHasMore(true);
      if (!reset) setPage((p) => p + 1);
      else setPage(1);
    } catch (error) {
      if (reset)
        showToast(
         "Không thể tải bảng tin lúc này, vui lòng thử lại sau.",
         "error"
        );
    } finally {
      setLoading(false);
    }
  };

  const enhanceContent = async () => {
    if (!content.trim() || isEnhancing) return;
    setIsEnhancing(true);
    showToast("Đang tối ưu nội dung bằng AI", "info");
    try {
      const data = await translateTextAPI(content, "enhance_social");
      if (data.result) {
        setContent(data.result);
        showToast("Đã tối ưu nội dung!", "success");
      }
    } catch (e: any) {
      showToast(e.message || "Lỗi khi tối ưu nội dung", "error");
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleGiftDL = async () => {
    if (!giftModal || isProcessing) return;
    if (giftModal.amount <= 0) {
      showToast("Số lượng dl không hợp lệ", "error");
      return;
    }
    setIsProcessing(true);
    try {
      const data = await voteItemAPI(giftModal.postId, "status_update", giftModal.amount);
      showToast(data.message || "Đã tặng quà thành công!", "success");
      setGiftModal(null);
    } catch (e: any) {
      showToast(e.message || "Lỗi khi tặng quà", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const fetchStories = async () => {
    try {
      const json = await getStoriesAPI();
      setStories(json.data?.stories || json.data || json.stories || []);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };

  const fetchArchivedStories = async () => {
    try {
      const json = await getArchivedStoriesAPI();
      setArchivedStories(json.data?.stories || json.data || json.stories || []);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };

  const fetchRanking = async () => {
    try {
      const json = await getSocialRankingAPI();
      setRanking(json.data?.top_authors || json.top_authors || []);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };

  const fetchReaderRanking = async () => {
    try {
      const json = await getReaderRankingAPI();
      setReaderRanking(json.data || json || []);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };

  const createStory = async () => {
    if (!storyText.trim() && !storyMediaUrl)
      return showToast("Vui lòng nhập nội dung hoặc chọn ảnh.", "error");

    let finalPollData = null;
    if (storyAddPoll && storyPollQuestion.trim()) {
      const validOptions = storyPollOptions.filter((o) => o.trim());
      if (validOptions.length >= 2) {
        finalPollData = {
          question: storyPollQuestion.trim(),
          options: validOptions,
          voters: {},
        };
      }
    }

    let finalQuizData = null;
    if (storyAddQuiz && storyQuizQuestion.trim()) {
      const validQuizOptions = storyQuizOptions.filter((o) => o.trim());
      if (validQuizOptions.length >= 2) {
        finalQuizData = {
          question: storyQuizQuestion.trim(),
          options: validQuizOptions,
          correct_idx: storyQuizCorrectIdx,
          answers: {},
        };
      }
    }

    let parsedMentions: string[] = [];
    if (storyMentionsInput.trim()) {
      parsedMentions = storyMentionsInput
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s);
    }

    try {
      await createStoryAPI({
        text_content: wasAiAppliedStory && storyText
          ? storyText + "\n\n*Nội dung được tạo bởi DocLib AI*"
          : (storyText || undefined),
        media_url: storyMediaUrl || undefined,
        background_color: storyBgColor,
        text_color: storyTextColor,
        font_style: storyFontStyle,
        privacy: storyPrivacy,
        link_url: storyLinkUrl || null,
        poll_data: finalPollData,
        quiz_data: finalQuizData,
        mentions: parsedMentions.length > 0 ? parsedMentions : undefined,
      });
      setStoryText("");
      discardAiDraftStory();
      setWasAiAppliedStory(false);
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
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };

  const deleteStory = async (storyIdParam?: string) => {
    const idToDelete = storyIdParam || deleteStoryConfirm;
    if (!idToDelete) return;
    setIsProcessing(true);
    try {
      await deleteStoryAPI(idToDelete);
      showToast("Đã xóa tin thành công", "success");
      setViewingStoryMode(false);
      setDeleteStoryConfirm(null);
      fetchStories();
    } catch (e: any) {
      showToast("Lỗi hệ thống", "error");
      showToast(e.message || "Xóa tin thất bại", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const repostPost = async (postId: string) => {
    if (!currentUser)
      return showToast("Vui lòng đăng nhập để thực hiện.", "error");
    try {
      await repostPostAPI(postId);
      showToast("Đã chia sẻ lại bài viết thành công", "success");
      fetchFeed(true);
    } catch (e: any) {
      showToast(e.message || "Không thể chia sẻ lại bài viết", "error");
    }
  };

  const translatePost = async (postId: string, text: string) => {
    if (isTranslating) return;
    setIsTranslating(true);
    showToast("Đang dịch nội dung", "info");
    try {
      const json = await translateTextAPI(text, "vi");
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

  const handleSuggestEngagement = async (postId: string, content: string) => {
    if (isGeneratingSuggestions[postId]) return;
    setIsGeneratingSuggestions(prev => ({ ...prev, [postId]: true }));
    try {
      const data = await suggestEngagementAPI(content);
      const suggestions = data.data?.suggestions || data.suggestions;
      if (suggestions) {
        setEngagementSuggestions(prev => ({ ...prev, [postId]: suggestions }));
      }
    } catch (err: any) {
      showToast(err.message || "Không thể lấy gợi ý", "error");
    } finally {
      setIsGeneratingSuggestions(prev => ({ ...prev, [postId]: false }));
    }
  };

  const streamText = (
    targetText: string,
    setter: (val: string) => void,
    onComplete?: () => void
  ) => {
    let currentText = "";
    let index = 0;
    const stepSize = Math.max(1, Math.ceil(targetText.length / 80));
    const interval = setInterval(() => {
      if (index >= targetText.length) {
        clearInterval(interval);
        setter(targetText);
        if (onComplete) onComplete();
      } else {
        currentText += targetText.substring(index, index + stepSize);
        index += stepSize;
        setter(currentText);
      }
    }, 15);
  };

  const generatePostWithAI = async () => {
    if (isEnhancing) return;
    setIsEnhancing(true);
    showToast("AI đang soạn thảo bài đăng...", "info");
    try {
      const data = await createPostAI(content, attachedDocumentTitle || "");
      const postText = data.data?.post || data.post;
      if (postText) {
        setAiDraftPost("");
        setIsAiDraftActive(true);
        streamText(postText, setAiDraftPost, () => {
          showToast("Đã soạn thảo xong bản thảo AI!", "success");
        });
      }
    } catch (err: any) {
      showToast(err.message || "Lỗi khi tạo bài đăng", "error");
    } finally {
      setIsEnhancing(false);
    }
  };

  const generateStoryWithAI = async () => {
    if (isStoryUploading) return;
    setIsStoryUploading(true);
    showToast("AI đang lên kịch bản story...", "info");
    try {
      const data = await createStoryAI(storyText);
      const storyResult = data.data?.story || data.story;
      if (storyResult) {
        setAiDraftStory("");
        setIsAiDraftStoryActive(true);
        streamText(storyResult, setAiDraftStory, () => {
          showToast("Đã xong kịch bản bản thảo AI!", "success");
        });
      }
    } catch (err: any) {
      showToast(err.message || "Lỗi khi tạo kịch bản", "error");
    } finally {
      setIsStoryUploading(false);
    }
  };

  const deletePost = async () => {
    if (!deletePostConfirm) return;
    setIsProcessing(true);
    try {
      await deletePostAPI(deletePostConfirm);
      showToast("Đã xóa bài viết thành công", "success");
      setDeletePostConfirm(null);
      fetchFeed(true);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const overrideFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", e.target.files[0]);
    try {
      const json = await uploadMediaAPI(formData);
      setMediaUrls((prev) => [...prev, json.data?.url || json.url]);
    } catch (e: any) {
      showToast(e.message || "Lỗi tải ảnh/video.", "error");
    } finally {
      setIsUploading(false);
    }
  };

  const [quoteText, setQuoteText] = useState("");
  const [quoteBg, setQuoteBg] = useState(
   "bg-gray-100 dark:bg-gray-800 from-gray-200 to-gray-200"
  );

  const createPost = async () => {
    if (!content.trim() && mediaUrls.length === 0)
      return showToast("Bảng tin không thể trống.", "error");
    try {
      const privacyEl = document.getElementById(
       "post-privacy"
      ) as HTMLSelectElement;
      const privacy = privacyEl ? privacyEl.value : "public";
      const db_poll_opts = [pollText1, pollText2].filter((p) => p.trim());
      await createPostAPI({
        content: wasAiAppliedPost
          ? content + "\n\n*Nội dung được tạo bởi DocLib AI*"
          : content,
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
        scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
      });
      setContent("");
      discardAiDraftPost();
      setWasAiAppliedPost(false);
      localStorage.removeItem("doclib_feed_draft");
      setPollText1("");
      setPollText2("");
      setAttachedDocumentId("");
      setAttachedDocumentTitle("");
      setMediaUrls([]);
      setShowExtras(false);
      setIsQuoteMode(false);
      setQuoteText("");
      showToast("Đã đăng bài thành công.", "success");
      fetchFeed(true);
    } catch (e) {
      showToast("Không thể tải nội dung lúc này.", "error");
    }
  };

  const toggleLike = async (
    postId: string,
    reactionType: string = "like",
    event?: React.MouseEvent
  ) => {
    try {
      const data = await toggleReactionAPI(postId, reactionType);
      if (data.message === "Đã thích" && event) {
      }
      fetchFeed(true);
    } catch (e) {
      showToast("Lỗi kết nối khi thích bài viết.", "error");
    }
  };

  const submitComment = async (postId: string) => {
    if (!commentText.trim()) return;
    try {
      const payload: any = {
        item_id: postId,
        item_type: "post",
        text: commentText,
      };
      if (replyToContext?.postId === postId) {
        payload.parent_id = replyToContext.commentId;
        payload.text = `@${replyToContext.userName} ${commentText}`;
      }
      await createCommentAPI(payload);
      showToast("Đã lưu tương tác thành công.", "success");
      setCommentText("");
      setReplyToContext(null);
      fetchFeed(true);
      setExpandedComments(postId);
    } catch (e) {
      showToast("Không thể gửi bình luận lúc này, vui lòng thử lại.", "error");
    }
  };

  const toggleSave = async (postId: string) => {
    try {
      await savePostAPI(postId);
      fetchFeed(true);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };

  const submitPollVote = async (postId: string, optionId: string) => {
    try {
      await submitPollVoteAPI(postId, optionId);
      showToast("Bình chọn thành công", "success");
      fetchFeed(true);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };

  const [editingPostId, setEditingPostId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState("");

  const togglePinPost = async (postId: string) => {
    try {
      await pinPostAPI(postId);
      fetchFeed(true);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };

  const reportPost = async () => {
    if (!reportModal || !reportModal.reason.trim()) return;
    setIsProcessing(true);
    try {
      await reportPostAPI(reportModal.postId, reportModal.reason);
      showToast("Cảm ơn, báo cáo đã được ghi nhận.", "success");
      setReportModal(null);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const hidePost = async (postId: string) => {
    try {
      await hidePostAPI(postId);
      showToast("Đã ẩn.", "info");
      fetchFeed(true);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };

  const followUser = async (userId: string) => {
    try {
      const data = await followUserAPI(userId);
      showToast(data.message, "success");
      fetchSuggestions();
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };

  const updatePost = async (postId: string) => {
    if (!editingContent.trim()) return;
    try {
      await updatePostAPI(postId, editingContent);
      showToast("Cập nhật thành công", "success");
      setEditingPostId(null);
      fetchFeed(true);
    } catch (e) {
      showToast("Lỗi hệ thống", "error");
    }
  };

  return (
    <>
      <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
        <div className="mb-8 border-b border-zinc-200 pb-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold text-black">Bảng tin</h1>
              <p className="text-zinc-500 text-sm font-medium flex items-center gap-2">
                Kết nối và chia sẻ nội dung <Sparkles className="w-4 h-4" />
              </p>
            </div>
            <div className="flex border border-zinc-200 bg-white rounded-none">
              <button
                onClick={() => setFilter("recent")}
                className={`px-4 py-2 text-xs font-medium   border-r border-zinc-200 ${
                  filter === "recent"
                    ? "bg-zinc-100 text-black"
                    : "text-zinc-500"
                }`}
              >
                Mới nhất
              </button>
              <button
                onClick={() => setFilter("trending")}
                className={`px-4 py-2 text-xs font-medium ${
                  filter === "trending"
                    ? "bg-zinc-100 text-black"
                    : "text-zinc-500"
                }`}
              >
                Xu hướng
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          <aside className="lg:col-span-3 space-y-8 order-2 lg:order-1 hidden lg:block">
            <div className="border border-zinc-200 bg-white rounded-none p-6">
              <h3 className="text-xs font-semibold text-black mb-4 border-b border-zinc-200 pb-3 flex items-center gap-2">
                Bảng vinh danh tác giả
              </h3>
              {ranking.length === 0 ? (
                <p className="text-xs font-medium text-zinc-500 text-center py-4">
                  Chưa có dữ liệu
                </p>
              ) : (
                <div className="space-y-4">
                  {ranking.map((r, i) => (
                    <Link href={`/thanh-vien/${r.slug || r._id}`} key={i} className="flex gap-3 items-center group cursor-pointer hover:bg-zinc-50 p-1 -m-1 transition-colors">
                      <div className="w-8 h-8 bg-zinc-100 text-black font-semibold flex items-center justify-center text-xs border border-zinc-200 shrink-0 group-hover:border-black transition-colors">
                        #{i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-xs font-semibold text-black truncate group-hover:underline">
                          {r.full_name || "Tác giả ẩn danh"}
                        </h4>
                        <span className="text-[10px] text-zinc-500 font-medium truncate">
                          {r.score.toLocaleString("vi-VN")} điểm
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {trendingTags.length > 0 && (
              <div className="border border-zinc-200 bg-white rounded-none p-6">
                <h3 className="text-xs font-semibold text-black mb-4 border-b border-zinc-200 pb-3 flex items-center gap-2">
                  Xu hướng hashtag
                </h3>
                <div className="flex flex-wrap gap-2">
                   {trendingTags.map((tag: any, i: number) => (
                     <Link
                       key={i}
                       href={`/tim-kiem?q=${encodeURIComponent(tag.tag)}`}
                       className="px-3 py-1 bg-zinc-50 border border-zinc-200 text-xs font-medium text-zinc-600 hover:bg-zinc-100 transition-colors"
                     >
                       #{tag.tag}
                     </Link>
                   ))}
                </div>
              </div>
            )}

            <div className="border border-zinc-200 bg-white rounded-none p-6">
              <h3 className="text-xs font-semibold text-black mb-4 border-b border-zinc-200 pb-3 flex items-center gap-2">
                Gợi ý kết nối
              </h3>
              {(() => {
                const filteredSuggestions = suggestions.filter((s: any) => {
                  const n = (s.full_name || s.username || "").toLowerCase();
                  return !(
                    n.includes("moderator") ||
                    n.includes("active reader") ||
                    n.includes("doclib admin") ||
                    n.includes("creative author") ||
                    n.includes("potential author") ||
                    n.includes("content mod")
                  );
                });
                return filteredSuggestions.length === 0 ? (
                  <p className="text-xs font-medium text-zinc-500 text-center py-4">
                    Chưa có dữ liệu
                  </p>
                ) : (
                  <div className="space-y-4">
                    {filteredSuggestions.map((s, i) => (
                      <div key={i} className="flex gap-3 items-center">
                        <div className="w-8 h-8 bg-zinc-100 text-black font-semibold flex items-center justify-center text-xs border border-zinc-200 shrink-0">
                          {s.full_name?.[0]?.toUpperCase() || "A"}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-xs font-semibold text-black truncate">
                            {s.full_name}
                          </h4>
                          <span className="text-[10px] text-zinc-500 font-medium truncate">
                            {s.total_match || 0} điểm chung
                          </span>
                        </div>
                        <button
                          onClick={() => {
                            if (currentUser) followUser(s._id);
                            else showToast("Vui lòng đăng nhập.", "error");
                          }}
                          className="h-7 px-3 border border-zinc-200 text-[10px] font-medium"
                        >
                          Theo dõi
                        </button>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>

            <div className="border border-zinc-200 bg-white rounded-none p-6">
              <h3 className="text-xs font-semibold text-black mb-4 border-b border-zinc-200 pb-3 flex items-center gap-2">
                Tài liệu đáng đọc
              </h3>
              {documentSuggestions.length === 0 ? (
                <p className="text-xs font-medium text-zinc-500 text-center py-4">
                  Chưa có dữ liệu
                  </p>
              ) : (
                <div className="space-y-4">
                  {documentSuggestions.map((b, i) => (
                    <div key={i} className="flex gap-3 items-center">
                      <div className="w-8 h-10 bg-zinc-50 border border-zinc-200 shrink-0 flex items-center justify-center">
                        <BookText className="w-4 h-4 text-zinc-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-xs font-semibold text-black truncate cursor-pointer">
                          {b.title}
                        </h4>
                        <span className="text-[10px] text-zinc-500 font-medium">
                          {b.mentions} đề xuất
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </aside>

          <main className="lg:col-span-9 order-1 lg:order-2">
            <div className="max-w-2xl mx-auto space-y-8">
              <div className="flex gap-4 overflow-x-auto pb-2 hide-scrollbar">
                {currentUser && (
                  <div
                    onClick={() => setShowStoryModal(true)}
                    className="flex flex-col items-center gap-2 cursor-pointer shrink-0"
                  >
                    <div className="w-16 h-16 rounded-none border border-zinc-200 flex items-center justify-center relative bg-zinc-50 overflow-hidden">
                      {currentUser?.avatar_url ? (
                        <img
                          src={currentUser.avatar_url}
                          className="w-full h-full object-cover grayscale mix-blend-multiply"
                        />
                      ) : (
                        <Plus className="w-6 h-6 text-zinc-400" />
                      )}
                    </div>
                    <span className="text-[10px] font-medium text-zinc-600">
                      Tạo tin
                    </span>
                  </div>
                )}

                {stories.map((story, idx) => (
                  <div
                    key={story.id}
                    onClick={() => {
                      setActiveStoryIndex(idx);
                      setViewingStoryMode(true);
                      setStoryProgress(0);
                    }}
                    className="flex flex-col items-center gap-2 cursor-pointer shrink-0"
                  >
                    <div className="w-16 h-16 rounded-none border border-zinc-200 p-[2px]">
                      <div className="w-full h-full rounded-none overflow-hidden bg-zinc-100 border border-zinc-200">
                        {story.user?.avatar_url ? (
                          <img
                            src={story.user.avatar_url}
                            className="w-full h-full object-cover grayscale mix-blend-multiply"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center bg-zinc-100">
                            <UserIcon className="w-6 h-6 text-zinc-400 stroke-[1]" />
                          </div>
                        )}
                      </div>
                    </div>
                    <span className="text-[10px] font-medium text-zinc-600 truncate w-16 text-center">
                      {story.user?.username || story.user?.name || "Người dùng"}
                    </span>
                  </div>
                ))}
              </div>

              {currentUser && (
                <div className="bg-white border border-zinc-200 p-6 rounded-none flex flex-col space-y-4">
                  <div className="flex gap-4 items-start">
                    <div className="w-10 h-10 rounded-none bg-zinc-100 border border-zinc-200 flex shrink-0 items-center justify-center overflow-hidden">
                      {currentUser?.avatar_url ? (
                        <img
                          src={currentUser.avatar_url}
                          className="w-full h-full object-cover grayscale mix-blend-multiply"
                        />
                      ) : (
                        <UserIcon className="w-5 h-5 text-zinc-400 stroke-[1]" />
                      )}
                    </div>
                    <div className="flex-1">
                      <textarea
                        className="w-full bg-transparent outline-none text-black resize-none min-h-[32px] text-sm font-medium placeholder:text-zinc-400"
                        placeholder="Chia sẻ nội dung của bạn"
                        value={content}
                        rows={
                          isQuoteMode
                            ? 2
                            : Math.max(content.split("\n").length, 1)
                        }
                        onChange={handleContentChange}
                      />

                      {isAiDraftActive && (
                        <div className="mt-2 space-y-2">
                          <div className="text-[10px] font-bold text-zinc-500">
                            Gợi ý từ DocLib AI
                          </div>
                          <div className="w-full bg-zinc-50 border border-zinc-200 p-4 min-h-[80px] text-sm font-medium text-black leading-relaxed whitespace-pre-wrap select-text">
                            {renderContentWithTags(aiDraftPost)}
                          </div>
                          <div className="flex items-center gap-3">
                            <button
                              type="button"
                              onClick={applyAiDraftPost}
                              className="bg-black text-white hover:bg-zinc-800 text-xs font-bold px-4 py-2 border border-black transition-all"
                            >
                              Áp dụng
                            </button>
                            <button
                              type="button"
                              onClick={discardAiDraftPost}
                              className="bg-white text-zinc-600 hover:text-black border border-zinc-200 hover:border-zinc-300 text-xs font-bold px-4 py-2 transition-all"
                            >
                              Xóa
                            </button>
                          </div>
                        </div>
                      )}

                      {documentSuggestions.length > 0 && (
                        <div className="bg-white border border-zinc-200 mt-2 max-h-48 overflow-y-auto rounded-none">
                          <div className="px-4 py-2 border-b border-zinc-100 text-xs font-semibold text-zinc-500 bg-zinc-50">
                            Gợi ý tài liệu
                          </div>
                          {documentSuggestions.map((doc: any, i: number) => (
                            <div
                              key={i}
                              className="px-4 py-3 cursor-pointer border-b border-zinc-50  flex justify-between items-center"
                              onClick={() => selectAttachedDocument(doc)}
                            >
                              <div className="flex flex-col">
                                <span className="text-xs font-medium text-black">
                                  {doc.title}
                                </span>
                                <span className="text-[10px] text-zinc-500">
                                  {doc.author_name ||
                                    doc.author ||
                                   "Tác giả ẩn danh"}
                                </span>
                              </div>
                              <ChevronRight className="w-4 h-4 text-zinc-400" />
                            </div>
                          ))}
                        </div>
                      )}

                      {attachedDocumentId && (
                        <div className="mt-4 p-4 border border-zinc-200 bg-zinc-50 flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-10 bg-white border border-zinc-200 flex items-center justify-center">
                              <BookText className="w-4 h-4 text-zinc-400" />
                            </div>
                            <div className="flex flex-col">
                              <span className="text-[10px] font-medium text-zinc-500">
                                Đã đính kèm
                              </span>
                              <span className="text-xs font-semibold text-black">
                                {attachedDocumentTitle}
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={() => {
                              setAttachedDocumentId("");
                              setAttachedDocumentTitle("");
                            }}
                            className="p-1 text-zinc-400"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      )}

                      {mediaUrls.length > 0 && (
                        <div
                          className={`grid gap-2 mt-4 ${
                            mediaUrls.length > 1 ? "grid-cols-2" : "grid-cols-1"
                          }`}
                        >
                          {mediaUrls.map((url, i) => (
                            <div
                              key={i}
                              className="relative w-full border border-zinc-200 bg-zinc-50"
                            >
                              {url.match(/\.(mp4|webm)$/i) ? (
                                <video
                                  src={`${API_URL}${url}`}
                                  className="w-full max-h-48 object-cover"
                                  autoPlay
                                  muted
                                  loop
                                />
                              ) : (
                                <img
                                  src={`${API_URL}${url}`}
                                  className="w-full max-h-48 object-cover grayscale mix-blend-multiply"
                                />
                              )}
                              <button
                                onClick={() =>
                                  setMediaUrls(
                                    mediaUrls.filter((_, idx) => idx !== i)
                                  )
                                }
                                className="absolute top-2 right-2 bg-white border border-zinc-200 p-1 text-black"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}

                      {showExtras && (
                        <div className="mt-4 p-4 border border-zinc-200 bg-zinc-50 space-y-3">
                          <h4 className="text-xs font-medium text-black flex items-center gap-2">
                            <BarChart2 className="w-4 h-4" /> Tạo bình chọn
                          </h4>
                          <Input
                            value={pollText1}
                            onChange={(e) => setPollText1(e.target.value)}
                            placeholder="Lựa chọn 1"
                            className="h-10 bg-white border-zinc-200 text-xs font-medium rounded-none focus-visible:ring-black"
                          />
                          <Input
                            value={pollText2}
                            onChange={(e) => setPollText2(e.target.value)}
                            placeholder="Lựa chọn 2"
                            className="h-10 bg-white border-zinc-200 text-xs font-medium rounded-none focus-visible:ring-black"
                          />
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="pt-4 border-t border-zinc-200 flex flex-wrap items-center justify-between gap-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <label className="cursor-pointer h-10 w-10 border border-zinc-200 flex items-center justify-center text-zinc-500 hover:bg-zinc-50 transition-colors">
                        <ImageIcon className="w-4 h-4" />
                        <input
                          type="file"
                          className="hidden"
                          accept="image/*,video/*"
                          multiple
                          onChange={overrideFileUpload}
                        />
                      </label>
                      <button
                        onClick={() => setShowExtras(!showExtras)}
                        className={`h-10 w-10 border flex items-center justify-center transition-colors ${
                          showExtras
                            ? "bg-black border-black text-white"
                            : "bg-white border-zinc-200 text-zinc-500 hover:bg-zinc-50"
                        }`}
                      >
                        <BarChart2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setIsQuoteMode(!isQuoteMode)}
                        className={`h-10 w-10 border flex items-center justify-center transition-colors ${
                          isQuoteMode
                            ? "bg-black border-black text-white"
                            : "bg-white border-zinc-200 text-zinc-500 hover:bg-zinc-50"
                        }`}
                      >
                        <Quote className="w-4 h-4" />
                      </button>

                      {/* Sleek Vertical Divider */}
                      <div className="h-6 w-[1px] bg-zinc-200 mx-1" />

                      <select
                        id="post-privacy"
                        className="h-10 px-3 bg-white border border-zinc-200 text-xs font-medium outline-none cursor-pointer hover:bg-zinc-50 transition-colors"
                      >
                        <option value="public">Công khai</option>
                        <option value="following">Người theo dõi</option>
                        <option value="private">Chỉ mình tôi</option>
                      </select>
                      <button
                        onClick={enhanceContent}
                        disabled={!content.trim() || isEnhancing}
                        className="h-10 px-4 border border-zinc-200 text-black text-xs font-medium disabled:opacity-50 flex items-center gap-2 hover:bg-zinc-50 transition-colors"
                      >
                        {isEnhancing ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Sparkles className="w-3 h-3" />
                        )}
                        Tối ưu AI
                      </button>
                      <button
                        onClick={generatePostWithAI}
                        disabled={isEnhancing}
                        className="h-10 px-4 border border-zinc-200 text-black text-xs font-medium disabled:opacity-50 flex items-center gap-2 hover:bg-zinc-50 transition-colors"
                      >
                        <PenTool className="w-3 h-3" />
                        Soạn thảo AI
                      </button>
                    </div>

                    <button
                      onClick={createPost}
                      disabled={!content.trim() && mediaUrls.length === 0}
                      className="h-10 px-6 bg-black text-white text-xs font-medium disabled:opacity-50 hover:bg-zinc-800 transition-colors"
                    >
                      Đăng bài
                    </button>
                  </div>
                </div>
              )}

              {currentUser && (
                <div className="bg-white border border-zinc-200 p-6 rounded-none flex flex-col space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm font-semibold text-black">
                      <Sparkles className="w-4 h-4 text-zinc-500" />
                      Phân tích bảng tin với AI
                    </div>
                    <button
                      onClick={async () => {
                        if (isSummarizing) return;
                        setIsSummarizing(true);
                        showToast("Đang phân tích bảng tin", "info");
                        try {
                          const json = await getAIFeedSummaryAPI();
                          if (json.data?.summary) {
                            setAiSummary(json.data.summary);
                            showToast("Đã xong", "success");
                          }
                        } catch (e) {
                          showToast("Lỗi", "error");
                        } finally {
                          setIsSummarizing(false);
                        }
                      }}
                      disabled={isSummarizing}
                      className="px-4 py-2 border border-zinc-200 text-xs font-medium text-black disabled:opacity-50"
                    >
                      {isSummarizing ? "Đang xử lý" : "Bắt đầu tóm tắt"}
                    </button>
                  </div>
                  {aiSummary && (
                    <div className="pt-4 border-t border-zinc-100 text-sm text-black italic font-medium leading-relaxed">
                     "{aiSummary}"
                    </div>
                  )}
                </div>
              )}

              <div className="flex flex-col gap-8">
                {loading ? (
                  <div className="space-y-6">
                    {[...Array(3)].map((_, i) => (
                      <div
                        key={i}
                        className="h-48 bg-zinc-50 border border-zinc-200 animate-pulse rounded-none"
                      />
                    ))}
                  </div>
                ) : posts.length === 0 ? (
                  <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white">
                    <p className="text-sm font-medium text-zinc-500">Chưa có dữ liệu</p>
                  </div>
                ) : (
                  posts.map((post) => (
                    <article
                      key={post.id}
                      className="border border-zinc-200 bg-white p-6 space-y-4"
                    >
                      <div className="flex flex-row justify-between items-start">
                        <div className="flex gap-3 items-center">
                          <Link href={`/thanh-vien/${post.user?.slug || post.user?.username || post.user_id}`} className="w-10 h-10 rounded-none border border-zinc-200 overflow-hidden bg-zinc-100 shrink-0 hover:border-black transition-colors block">
                            {post.user?.avatar_url ? (
                              <img
                                src={post.user.avatar_url}
                                className="w-full h-full object-cover grayscale mix-blend-multiply hover:grayscale-0 transition-all"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <UserIcon className="w-5 h-5 text-zinc-400 stroke-[1]" />
                              </div>
                            )}
                          </Link>
                          <div className="flex flex-col">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <Link href={`/thanh-vien/${post.user?.slug || post.user?.username || post.user_id}`} className="font-semibold text-sm text-black cursor-pointer hover:underline">
                                {post.user?.username ||
                                  post.user?.full_name ||
                                 "Ẩn danh"}
                              </Link>
                              {post.user?.role === "admin" && (
                                <span className="px-1.5 py-0.5 border border-zinc-200 text-[10px] font-medium text-zinc-500">
                                  Admin
                                </span>
                              )}
                              {post.user?.role === "author" && (
                                <span className="px-1.5 py-0.5 border border-zinc-200 text-[10px] font-medium text-zinc-500">
                                  Tác giả
                                </span>
                              )}
                              <span className="text-zinc-400 text-xs">•</span>
                              <span className="text-xs font-medium text-zinc-500">
                                {getTimeElapsed(post.created_at)}
                              </span>
                            </div>
                            {post.is_pinned && (
                              <div className="flex items-center gap-1 text-[10px] font-medium text-black mt-0.5">
                                <Pin className="w-3 h-3 fill-black" /> Đã ghim
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => translatePost(post.id, post.content)}
                            className="p-2 text-zinc-400"
                          >
                            <Sparkles className="w-4 h-4" />
                          </button>
                          {(currentUser?._id || "") &&
                          (currentUser?._id === post.author_id ||
                            currentUser?._id === post.user_id) ? (
                            <>
                              <button
                                onClick={() => togglePinPost(post.id)}
                                className="p-2 text-zinc-400"
                              >
                                <Pin
                                  className={`w-4 h-4 ${
                                    post.is_pinned
                                      ? "fill-black text-black"
                                      : ""
                                  }`}
                                />
                              </button>
                              <button
                                onClick={() => setDeletePostConfirm(post.id)}
                                className="p-2 text-zinc-400"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => hidePost(post.id)}
                                className="p-2 text-zinc-400"
                              >
                                <EyeOff className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() =>
                                  setReportModal({
                                    postId: post.id,
                                    reason: "",
                                  })
                                }
                                className="p-2 text-zinc-400"
                              >
                                <Flag className="w-4 h-4" />
                              </button>
                            </>
                          )}
                        </div>
                      </div>

                      <div className="text-sm font-medium text-black leading-relaxed whitespace-pre-wrap">
                        {renderContentWithTags(post.content)}
                      </div>

                      {post.media_urls && post.media_urls.length > 0 && (
                        <div
                          className={`grid gap-2 mt-4 ${
                            post.media_urls.length > 1
                              ? "grid-cols-2"
                              : "grid-cols-1"
                          }`}
                        >
                          {post.media_urls.map(
                            (url: string, i: number) => (
                              <div
                                key={i}
                                className="relative w-full border border-zinc-200 bg-zinc-50 overflow-hidden"
                              >
                                {url.match(/\.(mp4|webm)$/i) ? (
                                  <video
                                    src={url.startsWith("http") ? url : `${API_URL}/${url.startsWith("/") ? url.substring(1) : url}`}
                                    className="w-full h-auto max-h-96 object-cover"
                                    controls
                                  />
                                ) : (
                                  <img
                                    src={url.startsWith("http") ? url : `${API_URL}/${url.startsWith("/") ? url.substring(1) : url}`}
                                    className="w-full h-auto max-h-96 object-cover grayscale mix-blend-multiply"
                                  />
                                )}
                              </div>
                            )
                          )}
                        </div>
                      )}

                      {post.attached_document_id && (
                        <Link
                          href={`/tai-lieu/${post.attached_document_id}`}
                          className="mt-4 flex items-center justify-between p-4 border border-zinc-200 bg-zinc-50"
                        >
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-14 bg-white border border-zinc-200 flex items-center justify-center shrink-0">
                              <BookText className="w-5 h-5 text-zinc-400" />
                            </div>
                            <div className="flex flex-col">
                              <span className="text-[10px] font-medium text-zinc-500">
                                Tài liệu đính kèm
                              </span>
                              <span className="text-sm font-semibold text-black line-clamp-1">
                                {post.attached_document_title || "Xem tài liệu"}
                              </span>
                            </div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-zinc-400" />
                        </Link>
                      )}

                      {post.poll_data && (
                        <div className="mt-4 space-y-2 border border-zinc-200 p-4">
                          <div className="text-sm font-semibold text-black mb-2">
                            {post.poll_data.question || "Bình chọn"}
                          </div>
                          {post.poll_data.options.map(
                            (opt: any, idx: number) => {
                              const totalVotes = Object.keys(
                                post.poll_data.voters || {}
                              ).length;
                              const myVote = (post.poll_data.voters || {})[
                                currentUser?._id || ""
                              ];
                              const hasVoted = myVote !== undefined;
                              const optsVotes = Object.values(
                                post.poll_data.voters || {}
                              ).filter((v) => v === idx).length;
                              const percent =
                                totalVotes > 0
                                  ? Math.round((optsVotes / totalVotes) * 100)
                                  : 0;

                              return (
                                <button
                                  key={idx}
                                  onClick={() =>
                                    !hasVoted &&
                                    submitPollVote(post.id, idx.toString())
                                  }
                                  className="relative w-full border border-zinc-200 bg-white text-left overflow-hidden h-10"
                                >
                                  <div
                                    className="absolute inset-y-0 left-0 bg-zinc-100"
                                    style={{ width: hasVoted ? `${percent}%` : "0%" }}
                                  />
                                  <div className="absolute inset-0 flex items-center justify-between px-3 z-10 text-xs font-medium text-black">
                                    <span>
                                      {typeof opt === "string" ? opt : opt.text}
                                    </span>
                                    {hasVoted && <span>{percent}%</span>}
                                  </div>
                                </button>
                              );
                            }
                          )}
                        </div>
                      )}

                      <div className="pt-4 mt-4 border-t border-zinc-100 flex items-center justify-between">
                        <div className="flex items-center gap-6">
                          <button
                            onClick={() => setGiftModal({ postId: post.id, authorId: post.user?._id || post.author_id, amount: 10 })}
                            className="flex items-center gap-2 text-xs font-medium text-zinc-500 "
                          >
                            <Coins className="w-4 h-4" />
                            Tặng quà
                          </button>
                          <button
                            onClick={(e) => toggleLike(post.id, "like", e)}
                            className={`flex items-center gap-2 text-xs font-medium  ${
                              post.likes?.includes(currentUser?._id || "")
                                ? "text-black"
                                : "text-zinc-500"
                            }`}
                          >
                            <Heart
                              className={`w-4 h-4 ${
                                post.likes?.includes(currentUser?._id || "")
                                  ? "fill-black text-black"
                                  : ""
                              }`}
                            />
                            {post.likes?.length || 0}
                          </button>
                          <button
                            onClick={() =>
                              setExpandedComments(
                                expandedComments === post.id ? null : post.id
                              )
                            }
                            className="flex items-center gap-2 text-xs font-medium text-zinc-500 "
                          >
                            <MessageCircle className="w-4 h-4" />
                            {(post.comments || []).length}
                          </button>
                          <button
                            onClick={() => repostPost(post.id)}
                            className="flex items-center gap-2 text-xs font-medium text-zinc-500 "
                          >
                            <RotateCw className="w-4 h-4" />
                          </button>
                        </div>
                        <div className="flex items-center gap-6">
                          <button
                            onClick={() => toggleSave(post.id)}
                            className={`flex items-center gap-2 text-xs font-medium  ${
                              post.saved
                                ? "text-black"
                                : "text-zinc-500"
                            }`}
                          >
                            <Bookmark
                              className={`w-4 h-4 ${
                                post.saved ? "fill-black text-black" : ""
                              }`}
                            />
                          </button>
                          <button
                            onClick={() => {}}
                            className="flex items-center gap-2 text-xs font-medium text-zinc-500 "
                          >
                            <Share2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      {expandedComments === post.id && (
                        <div className="mt-4 pt-4 border-t border-zinc-100">
                          <div className="max-h-64 overflow-y-auto space-y-4 mb-4">
                            {post.comments?.length > 0 ? (
                              post.comments.map((c: any, i: number) => (
                                <div
                                  key={i}
                                  className={`text-sm ${
                                    c.parent_id
                                      ? "ml-8 relative pl-4 border-l border-zinc-200"
                                      : ""
                                  }`}
                                >
                                  <div className="flex justify-between items-start group">
                                    <div className="space-y-1">
                                      <span className="font-semibold text-black text-xs">
                                        {c.user.full_name || "Người dùng"}
                                      </span>
                                      <p className="text-zinc-600 font-medium text-xs leading-relaxed">
                                        {c.content || c.text}
                                      </p>
                                    </div>
                                    {currentUser && (
                                      <button
                                        onClick={() => {
                                          setReplyToContext({
                                            postId: post.id,
                                            commentId: c.id,
                                            userName:
                                              c.user.full_name ||
                                             "Người dùng",
                                          });
                                          setCommentText("");
                                        }}
                                        className="text-[10px] font-semibold text-zinc-400   opacity-0 group- shrink-0 ml-4"
                                      >
                                        Trả lời
                                      </button>
                                    )}
                                  </div>
                                </div>
                              ))
                            ) : (
                              <div className="text-xs font-medium text-zinc-400 italic py-2">
                                Chưa có bình luận
                              </div>
                            )}
                          </div>

                          {currentUser ? (
                            <div className="space-y-4">
                              {(!engagementSuggestions[post.id] || engagementSuggestions[post.id].length === 0) ? (
                                <button
                                  onClick={() => handleSuggestEngagement(post.id, post.content)}
                                  disabled={isGeneratingSuggestions[post.id]}
                                  className="w-full py-2 border border-zinc-200 text-[10px] font-bold uppercase tracking-widest text-zinc-500 hover:text-black hover:border-black transition-all flex items-center justify-center gap-2"
                                >
                                  {isGeneratingSuggestions[post.id] ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                  ) : (
                                    <Sparkles className="w-3 h-3" />
                                  )}
                                  Gợi ý phản hồi bằng AI
                                </button>
                              ) : (
                                <div className="flex flex-wrap gap-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                                  {engagementSuggestions[post.id].map((suggestion, idx) => (
                                    <button
                                      key={idx}
                                      onClick={() => {
                                        setCommentText(suggestion);
                                        setEngagementSuggestions(prev => ({ ...prev, [post.id]: [] }));
                                      }}
                                      className="px-3 py-1.5 bg-zinc-50 border border-zinc-200 text-[10px] font-semibold text-black hover:bg-black hover:text-white transition-all text-left max-w-full truncate"
                                    >
                                      {suggestion}
                                    </button>
                                  ))}
                                  <button 
                                    onClick={() => setEngagementSuggestions(prev => ({ ...prev, [post.id]: [] }))}
                                    className="p-1.5 border border-zinc-200 text-zinc-400"
                                  >
                                    <X className="w-3 h-3" />
                                  </button>
                                </div>
                              )}

                              {replyToContext &&
                                replyToContext.postId === post.id && (
                                  <div className="text-xs font-medium text-zinc-500 flex justify-between bg-zinc-50 border border-zinc-200 p-2 rounded-none">
                                    <span>
                                      Đang trả lời{" "}
                                      <b className="text-black">
                                        {replyToContext.userName}
                                      </b>
                                    </span>
                                    <button
                                      className=" "
                                      onClick={() => setReplyToContext(null)}
                                    >
                                      Hủy bỏ
                                    </button>
                                  </div>
                                )}
                              <div className="flex gap-2 items-center">
                                <Input
                                  className="h-10 bg-white border-zinc-200 text-xs font-medium focus-visible:ring-black rounded-none"
                                  placeholder="Viết bình luận"
                                  value={commentText}
                                  onChange={(e) =>
                                    setCommentText(e.target.value)
                                  }
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter")
                                      submitComment(post.id);
                                  }}
                                />
                                <button
                                  onClick={() => submitComment(post.id)}
                                  className="h-10 w-10 bg-black border border-black text-white rounded-none shrink-0 flex items-center justify-center hover:bg-zinc-800 transition-colors"
                                >
                                  <Send className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="text-xs font-medium text-zinc-500 text-center py-3 bg-zinc-50 border border-zinc-200 rounded-none">
                              Đăng nhập để bình luận
                            </div>
                          )}
                        </div>
                      )}
                    </article>
                  ))
                )}

                {!loading && hasMore && (
                  <div className="flex justify-center pt-4">
                    <button
                      onClick={() => fetchFeed()}
                      disabled={loading}
                      className="px-8 py-3 border border-zinc-200 bg-white text-xs font-medium text-black disabled:opacity-50"
                    >
                      {loading ? "Đang tải" : "Xem thêm bài viết"}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </main>
        </div>
      </div>

      {currentUser && showStoryModal && (
        <div className="fixed inset-0 z-[300] bg-black/60 flex items-center justify-center backdrop-blur-sm p-4">
          <div className="w-full h-[85vh] max-h-[800px] max-w-sm mx-auto border border-zinc-200 bg-zinc-50 flex flex-col relative overflow-hidden ">
            <div className="absolute z-10 top-0 left-0 right-0 p-3 flex justify-between items-center bg-white border-b border-zinc-200">
              <div className="flex gap-2 items-center">
                <select
                  value={storyFontStyle}
                  onChange={(e) => setStoryFontStyle(e.target.value)}
                  className="bg-zinc-100 text-black text-[10px] font-bold uppercase tracking-wider px-2 py-1 outline-none border border-zinc-200"
                >
                  <option value="sans">Sans</option>
                  <option value="mono">Mono</option>
                </select>
                <select
                  value={storyPrivacy}
                  onChange={(e) => setStoryPrivacy(e.target.value)}
                  className="bg-zinc-100 text-black text-[10px] font-bold uppercase tracking-wider px-2 py-1 outline-none border border-zinc-200"
                >
                  <option value="public">Công khai</option>
                  <option value="friends">Bạn bè</option>
                  <option value="close_friends">Bạn thân</option>
                </select>
                <input
                  type="color"
                  value={storyBgColor}
                  onChange={(e) => setStoryBgColor(e.target.value)}
                  className="w-5 h-5 p-0 border border-zinc-200 cursor-pointer"
                  title="Màu nền"
                />
                <input
                  type="color"
                  value={storyTextColor}
                  onChange={(e) => setStoryTextColor(e.target.value)}
                  className="w-5 h-5 p-0 border border-zinc-200 cursor-pointer"
                  title="Màu chữ"
                />
                <button
                  onClick={generateStoryWithAI}
                  disabled={isStoryUploading}
                  className="bg-black text-white text-[10px] font-bold uppercase tracking-wider px-3 py-1 border border-black flex items-center gap-1.5"
                >
                  <Sparkles className="w-3 h-3" />
                  Kịch bản AI
                </button>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => {
                    setShowStoryArchive(!showStoryArchive);
                    if (!showStoryArchive) fetchArchivedStories();
                  }}
                  className={`p-1.5 ${
                    showStoryArchive ? "bg-zinc-100" : ""
                  }`}
                  title="Kho lưu trữ tin"
                >
                  <Archive className="w-4 h-4 text-black" />
                </button>
                <button
                  onClick={() => setShowStoryModal(false)}
                  className="p-1.5"
                >
                  <X className="w-4 h-4 text-black" />
                </button>
              </div>
            </div>

            {showStoryArchive && (
              <div className="absolute z-20 top-[60px] left-0 right-0 bottom-0 bg-white overflow-y-auto p-4 border-t border-zinc-200">
                <h3 className="text-sm font-semibold text-black mb-4 border-b border-zinc-200 pb-2">
                  Kho lưu trữ tin của bạn
                </h3>
                {archivedStories.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <Archive className="w-8 h-8 text-zinc-300 mb-2" />
                    <p className="text-xs font-medium text-zinc-500">
                      Chưa có tin nào được lưu trữ.
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-2">
                    {archivedStories.map((s, i) => (
                      <div
                        key={i}
                        className="aspect-[9/16] overflow-hidden relative border border-zinc-200 cursor-pointer"
                        style={{
                          backgroundColor:
                            s.bg_color || s.background_color || "#f4f4f5",
                        }}
                      >
                        {s.media_url ? (
                          <img
                            src={s.media_url}
                            className="w-full h-full object-cover grayscale mix-blend-multiply"
                            alt="Story"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center p-2">
                            <p className="text-black text-[10px] font-semibold text-center line-clamp-4 break-words">
                              {s.text_content}
                            </p>
                          </div>
                        )}
                        <div className="absolute bottom-0 left-0 right-0 bg-white/90 border-t border-zinc-200 px-1 py-0.5">
                          <span className="text-black text-[10px] font-semibold">
                            {new Date(s.created_at).toLocaleDateString("vi-VN")}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div
              className="flex-1 flex flex-col justify-center items-center p-6 relative select-none overflow-hidden"
              style={{ backgroundColor: storyBgColor }}
              onMouseMove={handleDragMove}
              onTouchMove={handleDragMove}
              onMouseUp={handleDragEnd}
              onTouchEnd={handleDragEnd}
            >
              {storyMediaUrl && (
                <div className="absolute inset-0 w-full h-full">
                  <img
                    src={storyMediaUrl}
                    alt="Story Media"
                    className="w-full h-full object-cover grayscale mix-blend-multiply opacity-50"
                  />
                </div>
              )}

                <div
                  className="z-10 cursor-move "
                  style={{ transform: `translate(${storyTextPos.x}px, ${storyTextPos.y}px)` }}
                  onMouseDown={(e) => handleDragStart(e, 'text')}
                  onTouchStart={(e) => handleDragStart(e, 'text')}
                >
                  <textarea
                    className="bg-transparent border-none outline-none text-center resize-none text-2xl font-bold placeholder:opacity-50 p-0 overflow-hidden"
                    placeholder="Nhập nội dung tin"
                    value={storyText}
                    onChange={(e) => {
                      setStoryText(e.target.value);
                      e.target.style.height = "auto";
                      e.target.style.height = e.target.scrollHeight + "px";
                    }}
                    autoFocus
                    rows={1}
                    style={{
                      color: storyTextColor,
                      fontFamily:
                        storyFontStyle === "mono"
                          ? "Courier New, monospace"
                          : "inherit",
                    }}
                  />
                </div>

                {isAiDraftStoryActive && (
                  <div className="z-30 mt-2 space-y-2 w-full text-left max-w-xs">
                    <div className="text-[10px] font-bold text-zinc-400">
                      Gợi ý từ DocLib AI
                    </div>
                    <div className="w-full bg-black/60 border border-zinc-700 p-3 text-xs text-white leading-relaxed whitespace-pre-wrap select-text max-h-40 overflow-y-auto">
                      {aiDraftStory}
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={applyAiDraftStory}
                        className="bg-white text-black hover:bg-zinc-200 text-[10px] font-bold px-3 py-1.5 transition-all"
                      >
                        Áp dụng
                      </button>
                      <button
                        type="button"
                        onClick={discardAiDraftStory}
                        className="bg-transparent text-zinc-400 hover:text-white border border-zinc-700 text-[10px] font-bold px-3 py-1.5 transition-all"
                      >
                        Xóa
                      </button>
                    </div>
                  </div>
                )}

                {storyStickers.map((sticker) => (
                  <div
                    key={sticker.id}
                    className="absolute z-20 text-5xl cursor-move select-none "
                    style={{ transform: `translate(${sticker.x}px, ${sticker.y}px)` }}
                    onMouseDown={(e) => handleDragStart(e, 'sticker', sticker.id)}
                    onTouchStart={(e) => handleDragStart(e, 'sticker', sticker.id)}
                  >
                    {sticker.content}
                  </div>
                ))}

              {storyLinkUrl && (
                <div className="mt-4 px-3 py-1.5 bg-white border border-zinc-200 flex gap-2 items-center z-10 max-w-[80%]">
                  <Globe className="w-3 h-3 text-black" />
                  <span className="text-xs font-semibold text-black truncate">
                    {storyLinkUrl}
                  </span>
                  <button
                    onClick={() => setStoryLinkUrl("")}
                    className="text-zinc-400 ml-1"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              )}

              {storyAddPoll && (
                <div className="mt-4 w-full max-w-[240px] bg-white border border-zinc-200 p-4 z-10 flex flex-col gap-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-black text-xs font-semibold">
                      Tạo khảo sát
                    </span>
                    <button
                      onClick={() => setStoryAddPoll(false)}
                      className="text-zinc-400"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                  <input
                    type="text"
                    placeholder="Câu hỏi"
                    value={storyPollQuestion}
                    onChange={(e) => setStoryPollQuestion(e.target.value)}
                    className="w-full bg-zinc-50 border border-zinc-200 text-black text-xs outline-none px-2 py-1.5 font-medium"
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
                      className="w-full bg-white border border-zinc-200 text-black text-xs outline-none px-2 py-1.5 text-center font-medium"
                    />
                  ))}
                  {storyPollOptions.length < 4 && (
                    <button
                      onClick={() =>
                        setStoryPollOptions([...storyPollOptions, ""])
                      }
                      className="text-zinc-500 text-[10px] font-semibold py-1 flex items-center justify-center gap-1 border border-dashed border-zinc-200"
                    >
                      <Plus className="w-3 h-3" />
                      Thêm lựa chọn
                    </button>
                  )}
                </div>
              )}

              {storyAddQuiz && (
                <div className="mt-4 w-full max-w-[240px] bg-white border border-zinc-200 p-4 z-10 flex flex-col gap-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-black text-xs font-semibold">
                      Tạo trắc nghiệm
                    </span>
                    <button
                      onClick={() => setStoryAddQuiz(false)}
                      className="text-zinc-400"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                  <input
                    type="text"
                    placeholder="Câu hỏi"
                    value={storyQuizQuestion}
                    onChange={(e) => setStoryQuizQuestion(e.target.value)}
                    className="w-full bg-zinc-50 border border-zinc-200 text-black text-xs outline-none px-2 py-1.5 font-medium"
                  />
                  {storyQuizOptions.map((opt, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <button
                        onClick={() => setStoryQuizCorrectIdx(idx)}
                        className={`w-5 h-5 flex shrink-0 items-center justify-center border ${
                          storyQuizCorrectIdx === idx
                            ? "bg-black border-black text-white"
                            : "bg-zinc-50 border-zinc-200"
                        }`}
                      >
                        {storyQuizCorrectIdx === idx && (
                          <CheckCircle className="w-3 h-3" />
                        )}
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
                        className="w-full bg-white border border-zinc-200 text-black text-xs outline-none px-2 py-1.5 text-center font-medium"
                      />
                    </div>
                  ))}
                  {storyQuizOptions.length < 4 && (
                    <button
                      onClick={() =>
                        setStoryQuizOptions([...storyQuizOptions, ""])
                      }
                      className="text-zinc-500 text-[10px] font-semibold py-1 flex items-center justify-center gap-1 border border-dashed border-zinc-200"
                    >
                      <Plus className="w-3 h-3" />
                      Thêm lựa chọn
                    </button>
                  )}
                </div>
              )}
            </div>

            <div className="bg-white w-full border-t border-zinc-200 p-4 flex flex-col gap-3 z-10">
              {showLinkInput && (
                <div className="flex items-center gap-2">
                  <div className="flex-1 relative flex items-center border border-zinc-200">
                    <LinkIcon className="w-4 h-4 text-zinc-400 absolute left-2" />
                    <Input
                      placeholder="Nhập liên kết"
                      className="pl-8 h-8 w-full bg-zinc-50 border-none text-xs rounded-none"
                      value={storyLinkUrl}
                      onChange={(e) => setStoryLinkUrl(e.target.value)}
                      autoFocus
                    />
                  </div>
                </div>
              )}

              {showMentionInput && (
                <div className="flex items-center gap-2">
                  <div className="flex-1 relative flex items-center border border-zinc-200">
                    <AtSign className="w-4 h-4 text-zinc-400 absolute left-2" />
                    <Input
                      placeholder="Nhắc đến người dùng"
                      className="pl-8 h-8 w-full bg-zinc-50 border-none text-xs rounded-none"
                      value={storyMentionsInput}
                      onChange={(e) => setStoryMentionsInput(e.target.value)}
                      autoFocus
                    />
                  </div>
                </div>
              )}

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <label
                    className="cursor-pointer h-8 w-8 flex items-center justify-center bg-zinc-50 border border-zinc-200 shrink-0"
                    title="Ảnh / Video"
                  >
                    {isStoryUploading ? (
                      <div className="w-3 h-3 border-2 border-black border-t-transparent animate-spin" />
                    ) : (
                      <ImageIcon className="w-4 h-4 text-black" />
                    )}
                    <input
                      type="file"
                      className="hidden"
                      accept="image/*"
                      onChange={handleStoryImageUpload}
                    />
                  </label>
                  <div className="relative">
                    <button
                      onClick={() => setShowEmojiMenu(!showEmojiMenu)}
                      className={`h-8 w-8 flex items-center justify-center border border-zinc-200 shrink-0 ${showEmojiMenu ? 'bg-black text-white' : 'bg-zinc-50 text-black'}`}
                      title="Thêm emoji"
                    >
                      <Smile className="w-4 h-4" />
                    </button>
                    {showEmojiMenu && (
                      <div className="absolute bottom-full left-0 mb-2 p-2 bg-white border border-zinc-200  grid grid-cols-5 gap-1 z-[400]    w-[200px]">
                        {["🔥", "⭐", "❤️", "😂", "🚀", "✨", "🙌", "💯", "👏", "🎉", "💡", "📍", "👋", "🥳", "🤔"].map(e => (
                          <button
                            key={e}
                            onClick={() => addSticker(e)}
                            className="w-8 h-8 flex items-center justify-center text-xl"
                          >
                            {e}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => setShowLinkInput(!showLinkInput)}
                    className="h-8 w-8 flex items-center justify-center bg-zinc-50 border border-zinc-200 shrink-0"
                  >
                    <LinkIcon className="w-4 h-4 text-black" />
                  </button>
                  <button
                    onClick={() => setShowMentionInput(!showMentionInput)}
                    className="h-8 w-8 flex items-center justify-center bg-zinc-50 border border-zinc-200 shrink-0"
                  >
                    <AtSign className="w-4 h-4 text-black" />
                  </button>
                  <button
                    onClick={() => setStoryAddPoll(!storyAddPoll)}
                    className="h-8 w-8 flex items-center justify-center bg-zinc-50 border border-zinc-200 shrink-0"
                  >
                    <BarChart2 className="w-4 h-4 text-black" />
                  </button>
                  <button
                    onClick={() => setStoryAddQuiz(!storyAddQuiz)}
                    className="h-8 w-8 flex items-center justify-center bg-zinc-50 border border-zinc-200 shrink-0"
                  >
                    <HelpCircle className="w-4 h-4 text-black" />
                  </button>
                </div>
                <button
                  onClick={createStory}
                  className="px-4 h-8 bg-black text-white text-xs font-medium"
                >
                  Đăng tin
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {viewingStoryMode &&
        activeStoryIndex >= 0 &&
        stories[activeStoryIndex] && (
          <div className="fixed inset-0 z-[200] bg-white flex justify-center items-center">
            <div className="absolute top-4 right-4 z-[210] hidden md:flex gap-3">
              {(stories[activeStoryIndex].user_id ===
                (currentUser?._id || "") ||
                stories[activeStoryIndex].author_id ===
                  (currentUser?._id || "")) && (
                <button
                  onClick={() =>
                    deleteStory(
                      stories[activeStoryIndex].id ||
                        stories[activeStoryIndex]._id
                    )
                  }
                  className="text-black p-2 bg-zinc-50 border border-zinc-200"
                  title="Xóa tin này"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              )}
              <button
                onClick={() => {
                  setViewingStoryMode(false);
                  setStoryProgress(0);
                }}
                className="text-black p-2 bg-zinc-50 border border-zinc-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div
              className="flex-1 flex flex-col justify-between items-center relative overflow-hidden w-full max-w-sm mx-auto h-[100dvh] md:h-[85vh] md:w-[400px] border border-zinc-200"
              style={{
                backgroundColor:
                  stories[activeStoryIndex].background_color || "#f4f4f5",
              }}
            >
              <div className="absolute top-4 right-4 z-[210] flex gap-2 md:hidden">
                {(stories[activeStoryIndex].user_id ===
                  (currentUser?._id || "") ||
                  stories[activeStoryIndex].author_id ===
                    (currentUser?._id || "")) && (
                  <button
                    onClick={() =>
                      deleteStory(
                        stories[activeStoryIndex].id ||
                          stories[activeStoryIndex]._id
                      )
                    }
                    className="text-black p-1.5 bg-white border border-zinc-200"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => {
                    setViewingStoryMode(false);
                    setStoryProgress(0);
                  }}
                  className="text-black p-1.5 bg-white border border-zinc-200"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="absolute top-0 left-0 right-0 h-1 z-[220] flex gap-1 p-1">
                {stories.map((_, i) => (
                  <div
                    key={i}
                    className="flex-1 h-full bg-black/10 overflow-hidden"
                  >
                    <div
                      className="h-full bg-black"
                      style={{
                        width:
                          i < activeStoryIndex
                            ? "100%"
                            : i === activeStoryIndex
                            ? `${storyProgress}%`
                            : "0%",
                      }}
                    />
                  </div>
                ))}
              </div>

              <div
                className="absolute inset-0 flex items-center justify-center pointer-events-none p-8"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const x = e.clientX - rect.left;
                  if (x < rect.width / 3) handleStoryPrev();
                  else handleStoryNext();
                }}
              >
                {stories[activeStoryIndex].media_url && (
                  <div className="absolute inset-0 w-full h-full">
                    <img
                      src={stories[activeStoryIndex].media_url}
                      className="w-full h-full object-cover grayscale mix-blend-multiply opacity-50"
                    />
                  </div>
                )}
                <p
                  className="text-black text-2xl font-bold text-center break-words w-full z-10 pointer-events-auto"
                  style={{
                    fontFamily:
                      stories[activeStoryIndex].font_style === "mono"
                        ? "Courier New, monospace"
                        : "inherit",
                  }}
                >
                  {stories[activeStoryIndex].text_content}
                </p>

                {stories[activeStoryIndex].link_url && (
                  <a
                    href={stories[activeStoryIndex].link_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="absolute bottom-24 left-1/2 -translate-x-1/2 px-4 py-2 bg-white border border-zinc-200 flex gap-2 items-center z-10 pointer-events-auto"
                  >
                    <Globe className="w-4 h-4 text-black" />
                    <span className="text-xs font-semibold text-black">
                      Xem liên kết
                    </span>
                  </a>
                )}

                {stories[activeStoryIndex].poll_data ? (
                  <div
                    className="w-full max-w-[240px] bg-white border border-zinc-200 p-4 z-10 flex flex-col gap-2 pointer-events-auto "
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="text-center font-bold text-[10px] uppercase text-zinc-500 mb-1">
                      Khảo sát
                    </div>
                    <h4 className="text-black text-xs font-semibold text-center mb-2">
                      {stories[activeStoryIndex].poll_data.question}
                    </h4>
                    {stories[activeStoryIndex].poll_data.options.map(
                      (opt: string, idx: number) => {
                        const voters =
                          stories[activeStoryIndex].poll_data.voters || {};
                        const totalVotes = Object.keys(voters).length;
                        const votesForThis = Object.values(voters).filter(
                          (v) => v === idx
                        ).length;
                        const percent =
                          totalVotes > 0
                            ? Math.round((votesForThis / totalVotes) * 100)
                            : 0;
                        const hasVoted = voters[currentUser?._id || ""] !== undefined;

                        return (
                          <button
                            key={idx}
                            onClick={() =>
                              !hasVoted &&
                              votePoll(
                                stories[activeStoryIndex].id ||
                                  stories[activeStoryIndex]._id,
                                idx
                              )
                            }
                            className="relative w-full text-black text-[10px] border border-zinc-200 bg-zinc-50 overflow-hidden font-medium h-8 flex items-center"
                          >
                            <div
                              className="absolute top-0 bottom-0 left-0 bg-zinc-200"
                              style={{ width: hasVoted ? `${percent}%` : "0%" }}
                            />
                            <div className="relative w-full px-2 flex justify-between items-center z-10">
                              <span className="truncate pr-2">{opt}</span>
                              {hasVoted && (
                                <span className="font-semibold">{percent}%</span>
                              )}
                            </div>
                          </button>
                        );
                      }
                    )}
                    <div className="text-zinc-500 text-[10px] text-center mt-1 font-medium">
                      {Object.keys(stories[activeStoryIndex].poll_data.voters || {}).length} phiếu
                    </div>
                  </div>
                ) : stories[activeStoryIndex].quiz_data ? (
                  <div
                    className="w-full max-w-[240px] bg-white border border-zinc-200 p-4 z-10 flex flex-col gap-2 pointer-events-auto "
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="text-center font-bold text-[10px] uppercase text-zinc-500 mb-1">
                      Trắc nghiệm
                    </div>
                    <h4 className="text-black text-xs font-semibold text-center mb-2">
                      {stories[activeStoryIndex].quiz_data.question}
                    </h4>
                    {stories[activeStoryIndex].quiz_data.options.map(
                      (opt: string, idx: number) => {
                        const myAnswer = (stories[activeStoryIndex].quiz_data
                          .answers || {})[currentUser?._id || ""];
                        const hasAnswered = myAnswer !== undefined;
                        const isCorrect =
                          idx ===
                          stories[activeStoryIndex].quiz_data.correct_idx;

                        let buttonClass = "border-zinc-200 bg-zinc-50";
                        if (hasAnswered) {
                          buttonClass = isCorrect
                            ? "border-black bg-black text-white"
                            : myAnswer === idx
                            ? "border-zinc-300 bg-zinc-200 text-zinc-500"
                            : "border-zinc-200 bg-zinc-50 opacity-50";
                        }

                        return (
                          <button
                            key={idx}
                            onClick={() =>
                              !hasAnswered &&
                              answerQuiz(
                                stories[activeStoryIndex].id ||
                                  stories[activeStoryIndex]._id,
                                idx
                              )
                            }
                            className={`relative w-full text-[10px] border font-medium h-8 flex items-center ${buttonClass}`}
                          >
                            <div className="relative w-full px-2 flex justify-between items-center z-10">
                              <span className="truncate pr-2">{opt}</span>
                              {hasAnswered && isCorrect && (
                                <CheckCircle className="w-3 h-3 text-white" />
                              )}
                              {hasAnswered && !isCorrect && myAnswer === idx && (
                                <XCircle className="w-3 h-3 text-zinc-500" />
                              )}
                            </div>
                          </button>
                        );
                      }
                    )}
                  </div>
                ) : null}
              </div>

              <div className="absolute top-10 left-4 flex gap-3 items-center z-[210]">
                <div className="w-10 h-10 border border-zinc-200 flex justify-center items-center overflow-hidden shrink-0 bg-white">
                  {stories[activeStoryIndex].user?.avatar_url ? (
                    <img
                      src={stories[activeStoryIndex].user.avatar_url}
                      className="w-full h-full object-cover grayscale mix-blend-multiply"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-zinc-100 text-black text-xs font-bold">
                      {stories[activeStoryIndex].user?.full_name?.[0]?.toUpperCase() ||
                       "A"}
                    </div>
                  )}
                </div>
                <div className="flex flex-col">
                  <span className="text-black text-xs font-bold truncate">
                    {stories[activeStoryIndex].user?.full_name}
                  </span>
                  <span className="text-zinc-500 text-[10px] font-medium">
                    {new Date(
                      stories[activeStoryIndex].created_at
                    ).toLocaleTimeString("vi-VN", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              </div>

              <div className="absolute bottom-0 left-0 right-0 p-4 bg-white/90 border-t border-zinc-200 z-[210] flex gap-2 items-center">
                {stories[activeStoryIndex].user?._id ===
                (currentUser?._id || "") ? (
                  <button
                    onClick={() => {
                      fetchStoryViewers(
                        stories[activeStoryIndex].id ||
                          stories[activeStoryIndex]._id
                      );
                      setShowViewerList(true);
                    }}
                    className="flex-1 py-2 text-black text-xs font-semibold flex items-center justify-center gap-2 border border-zinc-200"
                  >
                    <Eye className="w-4 h-4" />
                    {stories[activeStoryIndex].viewer_count || 0} người xem
                  </button>
                ) : (
                  <>
                    <div className="flex-1 relative flex items-center border border-zinc-200 bg-white">
                      <input
                        placeholder="Gửi tin nhắn..."
                        className="h-9 w-full bg-transparent border-none text-xs font-medium pr-10 focus-visible:ring-0 rounded-none px-3 outline-none"
                        value={replyMessage}
                        onChange={(e) => setReplyMessage(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter")
                            submitReplyStory(
                              stories[activeStoryIndex].id ||
                                stories[activeStoryIndex]._id
                            );
                        }}
                      />
                      {replyMessage.trim() && (
                        <button
                          onClick={() =>
                            submitReplyStory(
                              stories[activeStoryIndex].id ||
                                stories[activeStoryIndex]._id
                            )
                          }
                          disabled={isReplying}
                          className="absolute right-2 p-1 text-black"
                        >
                          <Send className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    <button
                      onClick={() =>
                        reactToStory(
                          stories[activeStoryIndex].id ||
                            stories[activeStoryIndex]._id
                        )
                      }
                      className="text-black bg-white border border-zinc-200 p-2 shrink-0"
                    >
                      <Heart className="w-4 h-4" />
                    </button>
                  </>
                )}
              </div>

              {showViewerList && (
                <div className="absolute bottom-16 left-4 right-4 z-[210] bg-white border border-zinc-200 p-4 max-h-64 overflow-y-auto ">
                  <div className="flex items-center justify-between mb-3 border-b border-zinc-100 pb-2">
                    <span className="text-black text-xs font-semibold">
                      Người đã xem
                    </span>
                    <button
                      onClick={() => setShowViewerList(false)}
                      className="text-zinc-400"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  {isFetchingViewers ? (
                    <div className="text-zinc-500 text-xs text-center py-4">
                      Đang tải
                    </div>
                  ) : storyViewers.length === 0 ? (
                    <div className="text-zinc-500 text-xs text-center py-4">
                      Chưa có ai xem tin này.
                    </div>
                  ) : (
                    <div className="space-y-3 mt-2">
                      {storyViewers.map((v: any, i: number) => (
                        <div key={i} className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-zinc-50 border border-zinc-200 flex items-center justify-center text-[10px] font-bold text-black overflow-hidden shrink-0">
                            {v.avatar_url ? (
                              <img
                                src={v.avatar_url}
                                className="w-full h-full object-cover grayscale mix-blend-multiply"
                              />
                            ) : (
                              v.full_name?.[0]?.toUpperCase() || "?"
                            )}
                          </div>
                          <div className="flex flex-col">
                            <span className="text-black text-xs font-semibold">
                              {v.full_name || "Ẩn danh"}
                            </span>
                            <span className="text-zinc-500 text-[10px] font-medium">
                              {new Date(v.viewed_at).toLocaleTimeString(
                               "vi-VN",
                                { hour: "2-digit", minute: "2-digit" }
                              )}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

      <Modal
        isOpen={!!translationModal}
        onClose={() => setTranslationModal(null)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle className="text-sm font-semibold text-black">
            Bản dịch tự động
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-sm text-black leading-relaxed font-medium whitespace-pre-wrap">
            {translationModal?.text}
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setTranslationModal(null)}
            className="px-6 py-2 bg-white border border-zinc-200 text-xs font-medium text-black "
          >
            Đóng
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!deleteStoryConfirm}
        onClose={() => !isProcessing && setDeleteStoryConfirm(null)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle className="text-sm font-semibold text-black">
            Xác nhận xóa tin
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs text-zinc-500 font-medium leading-relaxed">
            Bạn có chắc chắn muốn xóa tin này không? Hành động này không thể hoàn tác.
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setDeleteStoryConfirm(null)}
            disabled={isProcessing}
            className="flex-1 py-2 bg-white border border-zinc-200 text-xs font-medium text-black   disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={() => deleteStory()}
            disabled={isProcessing}
            className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium   flex items-center justify-center disabled:opacity-50"
          >
            {isProcessing ? <Loader2 className="w-3 h-3 animate-spin" /> : "Xác nhận xóa"}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!deletePostConfirm}
        onClose={() => !isProcessing && setDeletePostConfirm(null)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle className="text-sm font-semibold text-black">
            Xác nhận xóa bài viết
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs text-zinc-500 font-medium leading-relaxed">
            Bạn có chắc chắn muốn xóa bài viết này không? Nội dung sẽ bị gỡ bỏ vĩnh viễn khỏi bảng tin.
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setDeletePostConfirm(null)}
            disabled={isProcessing}
            className="flex-1 py-2 bg-white border border-zinc-200 text-xs font-medium text-black   disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={deletePost}
            disabled={isProcessing}
            className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium   flex items-center justify-center disabled:opacity-50"
          >
            {isProcessing ? <Loader2 className="w-3 h-3 animate-spin" /> : "Xác nhận xóa"}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!reportModal}
        onClose={() => !isProcessing && setReportModal(null)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle className="text-sm font-semibold text-black">
            Báo cáo bài viết
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs text-zinc-500 font-medium leading-relaxed">
            Vui lòng cung cấp lý do báo cáo để đội ngũ quản trị viên DocLib xem xét và xử lý kịp thời.
          </p>
          <div className="space-y-2">
            <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
              Lý do báo cáo
            </label>
            <textarea
              value={reportModal?.reason || ""}
              onChange={(e) =>
                setReportModal((prev) =>
                  prev ? { ...prev, reason: e.target.value } : null
                )
              }
              placeholder="Nhập chi tiết"
              autoFocus
              className="w-full min-h-[100px] p-3 bg-zinc-50 border border-zinc-200 text-xs font-medium focus:border-black outline-none resize-none "
            />
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setReportModal(null)}
            disabled={isProcessing}
            className="flex-1 py-2 bg-white border border-zinc-200 text-xs font-medium text-black   disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={reportPost}
            disabled={isProcessing || !reportModal?.reason.trim()}
            className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium   flex items-center justify-center disabled:opacity-50"
          >
            {isProcessing ? <Loader2 className="w-3 h-3 animate-spin" /> : "Gửi báo cáo"}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!giftModal}
        onClose={() => !isProcessing && setGiftModal(null)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle className="text-sm font-semibold text-black">
            Tặng quà dl cho tác giả
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs text-zinc-500 font-medium mb-6">
            Chọn số lượng dl bạn muốn tặng để ủng hộ tác giả. Bạn sẽ nhận được 10% hoàn trả nếu tặng từ 50 dl trở lên!
          </p>
          <div className="grid grid-cols-3 gap-3">
            {[10, 20, 50, 100, 200, 500].map((amt) => (
              <button
                key={amt}
                onClick={() => setGiftModal(prev => prev ? { ...prev, amount: amt } : null)}
                className={`py-3 border text-xs font-bold  ${
                  giftModal?.amount === amt
                    ? "bg-black border-black text-white"
                    : "bg-white border-zinc-200 text-black"
                }`}
              >
                {amt} dl
              </button>
            ))}
          </div>
          <div className="mt-4">
             <label className="text-[10px] font-semibold text-black uppercase tracking-widest mb-1 block">Hoặc nhập số khác</label>
             <input
               type="number"
               className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium focus:border-black outline-none bg-zinc-50 "
               value={giftModal?.amount || ""}
               onChange={(e) => setGiftModal(prev => prev ? { ...prev, amount: parseInt(e.target.value) || 0 } : null)}
             />
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setGiftModal(null)}
            disabled={isProcessing}
            className="flex-1 py-2 bg-white border border-zinc-200 text-xs font-medium text-black "
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleGiftDL}
            disabled={isProcessing || !giftModal?.amount}
            className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium   flex items-center justify-center gap-2"
          >
            {isProcessing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Coins className="w-3 h-3" />}
            Xác nhận tặng
          </button>
        </ModalFooter>
      </Modal>
    </>
  );
}
