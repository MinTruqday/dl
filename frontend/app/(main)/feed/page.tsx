"use client";

import React, { useEffect, useState, useCallback } from "react";
import Workspace from "@/components/Workspace";
import Link from "next/link";
import {
  getFeedAPI,
  toggleReactionAPI,
  getStoriesAPI,
  createStoryAPI,
  viewStoryAPI,
  reactToStoryAPI,
  getStoryViewersAPI,
  voteStoryPollAPI,
  answerStoryQuizAPI,
  replyStoryAPI,
  getArchivedStoriesAPI,
  getSocialRankingAPI,
  getReaderRankingAPI,
  getIntersectionFriendsAPI,
  getTrendingTagsAPI,
  getSuggestedDocumentsAPI,
  createPostAPI,
  updatePostAPI,
  deletePostAPI,
  repostPostAPI,
  savePostAPI,
  pinPostAPI,
  reportPostAPI,
  hidePostAPI,
  followUserAPI,
  votePostAPI,
  submitPollVoteAPI,
  createCommentAPI,
  recordPostViewAPI,
  uploadMediaAPI,
} from "@/services/social.service";
import { getDocumentsAPI } from "@/services/document.service";
import { getWalletBalanceAPI } from "@/services/wallet.service";
import { translateTextAPI, getAIFeedSummaryAPI } from "@/services/ai.service";
import { API_URL } from "@/services/auth.service";
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
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import confetti from "canvas-confetti";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";

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
  const [deleteStoryConfirm, setDeleteStoryConfirm] = useState<string | null>(null);
  const [deletePostConfirm, setDeletePostConfirm] = useState<string | null>(null);
  const [reportModal, setReportModal] = useState<{ postId: string; reason: string } | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

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
          console.error("Error viewing story:", e),
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
        const data = await getDocumentsAPI(match[2], 5);
        setDocumentSuggestions(data.data || data);
      } catch (e) {
        console.error("API error:", e);
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

  const [storyMentionsInput, setStoryMentionsInput] = useState("");

  const [replyMessage, setReplyMessage] = useState("");
  const [isReplying, setIsReplying] = useState(false);

  const handleStoryImageUpload = async (
    e: React.ChangeEvent<HTMLInputElement>,
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
  const [walletBalance, setWalletBalance] = useState<number>(0);

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
  }, [currentUser?._id || "", showStoryArchive]);

  const fetchSuggestions = async () => {
    try {
      const json = await getIntersectionFriendsAPI();
      setSuggestions(json.data?.suggestions || json.suggestions || []);
    } catch (e) {
      console.error("API error:", e);
    }
  };

  const renderContentWithTags = (text: string) => {
    if (!text) return null;
    const parts = text.split(
      /(#[\w]+|https?:\/\/(?:www\.youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+|https?:\/\/open\.spotify\.com\/(?:track|album|playlist)\/[\w]+(?:.*)?|\*\*.*?\*\*|\*[^*]+\*|^> .*$)/gm,
    );
    return parts.map((part, i) => {
      const ytMatch = part.match(
        /https?:\/\/(?:www\.youtube\.com\/watch\?v=|youtu\.be\/)([\w-]+)/,
      );
      if (ytMatch) {
        return (
          <div
            key={i}
            className="my-3 overflow-hidden border border-border aspect-video"
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
        /https?:\/\/open\.spotify\.com\/(track|album|playlist)\/([\w]+)(.*)/,
      );
      if (spotMatch) {
        return (
          <div key={i} className="my-3">
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
      if (part.match(/#[\w]+/)) {
        return (
          <span
            key={i}
            className="text-black dark:text-white font-medium cursor-pointer"
          >
            {part}
          </span>
        );
      }
      if (part.match(/^\*\*(.*?)\*\*$/)) {
        return (
          <strong key={i} className="font-bold">
            {part.replace(/\*\*/g, "")}
          </strong>
        );
      }
      if (part.match(/^\*(.*?)\*$/)) {
        return (
          <em key={i} className="italic text-muted-foreground">
            {part.replace(/\*/g, "")}
          </em>
        );
      }
      if (part.match(/^> (.*)$/)) {
        return (
          <blockquote
            key={i}
            className="border-l-4 border-foreground pl-3 italic text-muted-foreground my-2 bg-muted/20 py-1"
          >
            {part.substring(2)}
          </blockquote>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  const recordView = async (postId: string) => {
    try {
      await recordPostViewAPI(postId);
    } catch (e) {
      console.error("API error:", e);
    }
  };

  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const fetchFeed = async (reset = false) => {
    try {
      const skip = reset ? 0 : page * 10;
      const limit = 10;
      const json = await getFeedAPI(
        tab,
        skip,
        limit,
        itemType,
        filter === "trending" ? "trending" : undefined,
      );
      const newData = json.data || json;
      setPosts((prev) => (reset ? newData : [...prev, ...newData]));
      if (newData.length < limit) setHasMore(false);
      else setHasMore(true);
      if (!reset) setPage((p) => p + 1);
      else setPage(1);

      const tagJson = await getTrendingTagsAPI();
      setTrendingTags(tagJson.data || tagJson);

      const booksJson = await getSuggestedDocumentsAPI();
      setDocumentSuggestions(booksJson.data || booksJson);
    } catch (error) {
      if (reset)
        showToast(
          "Không thể tải bảng tin lúc này, vui lòng thử lại sau.",
          "error",
        );
    } finally {
      setLoading(false);
    }
  };

  const fetchStories = async () => {
    try {
      const json = await getStoriesAPI();
      setStories(json.data?.stories || json.data || json.stories || []);
    } catch (e) {
      console.error("API error:", e);
    }
  };

  const fetchArchivedStories = async () => {
    try {
      const json = await getArchivedStoriesAPI();
      setArchivedStories(json.data?.stories || json.data || json.stories || []);
    } catch (e) {
      console.error("API error:", e);
    }
  };

  const fetchRanking = async () => {
    try {
      const json = await getSocialRankingAPI();
      setRanking(json.data || json || []);
    } catch (e) {
      console.error("API error:", e);
    }
  };

  const fetchReaderRanking = async () => {
    try {
      const json = await getReaderRankingAPI();
      setReaderRanking(json.data || json || []);
    } catch (e) {
      console.error("API error:", e);
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
        text_content: storyText || undefined,
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
      console.error("API error:", e);
    }
  };

  const deleteStory = async () => {
    if (!deleteStoryConfirm) return;
    setIsProcessing(true);
    try {
      await deleteStoryAPI(deleteStoryConfirm);
      showToast("Đã xóa tin thành công", "success");
      setViewingStoryMode(false);
      setDeleteStoryConfirm(null);
      fetchStories();
    } catch (e: any) {
      console.error("API error:", e);
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

  const deletePost = async () => {
    if (!deletePostConfirm) return;
    setIsProcessing(true);
    try {
      await deletePostAPI(deletePostConfirm);
      showToast("Đã xóa bài viết thành công", "success");
      setDeletePostConfirm(null);
      fetchFeed(true);
    } catch (e) {
      console.error("API error:", e);
    } finally {
      setIsProcessing(false);
    }
  };

  const fetchWallet = async () => {
    try {
      const json = await getWalletBalanceAPI();
      setWalletBalance(json.data?.balance || json.balance || 0);
    } catch (e) {
      console.error("API error:", e);
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
    "bg-gray-100 dark:bg-gray-800 from-gray-200 to-gray-200",
  );
  const [isQuoteMode, setIsQuoteMode] = useState(false);

  const createPost = async () => {
    if (!content.trim() && mediaUrls.length === 0)
      return showToast("Bảng tin không thể trống.", "error");
    try {
      const privacyEl = document.getElementById(
        "post-privacy",
      ) as HTMLSelectElement;
      const privacy = privacyEl ? privacyEl.value : "public";
      const db_poll_opts = [pollText1, pollText2].filter((p) => p.trim());
      await createPostAPI({
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
        scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
      });
      setContent("");
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
    event?: React.MouseEvent,
  ) => {
    try {
      const data = await toggleReactionAPI(postId, "posts", reactionType);
      if (data.message === "Đã thích" && event) {
        const rect = (event.target as HTMLElement).getBoundingClientRect();
        const x = (rect.left + rect.width / 2) / window.innerWidth;
        const y = (rect.top + rect.height / 2) / window.innerHeight;
        confetti({
          particleCount: 50,
          spread: 60,
          origin: { x, y },
          colors: ["#000000", "#ffffff", "#71717a"],
          disableForReducedMotion: true,
        });
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

  const handleVote = async (postId: string, amount: number) => {
    try {
      const data = await votePostAPI(postId, amount);
      showToast(
        data.message || `Đã gửi tặng ${amount} C thành công`,
        "success",
      );
      fetchWallet();
      fetchFeed(true);
    } catch (e: any) {
      showToast(
        e.message || "Bạn không đủ số dư để thực hiện, xin nạp thêm.",
        "error",
      );
    }
  };

  const toggleSave = async (postId: string) => {
    try {
      await savePostAPI(postId);
      fetchFeed(true);
    } catch (e) {
      console.error("API error:", e);
    }
  };

  const submitPollVote = async (postId: string, optionId: string) => {
    try {
      await submitPollVoteAPI(postId, optionId);
      showToast("Bình chọn thành công", "success");
      fetchFeed(true);
    } catch (e) {
      console.error("API error:", e);
    }
  };

  const [editingPostId, setEditingPostId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState("");

  const togglePinPost = async (postId: string) => {
    try {
      await pinPostAPI(postId);
      fetchFeed(true);
    } catch (e) {
      console.error("API error:", e);
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
      console.error("API error:", e);
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
      console.error("API error:", e);
    }
  };

  const followUser = async (userId: string) => {
    try {
      const data = await followUserAPI(userId);
      showToast(data.message, "success");
      fetchSuggestions();
    } catch (e) {
      console.error("API error:", e);
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
      console.error("API error:", e);
    }
  };

  return (
    <>
      <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
        <div className="mb-12 border-b border-zinc-200 pb-10 ">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="space-y-3">
              <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
                Bảng tin
              </h1>
              <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
                Kết nối và chia sẻ tri thức{" "}
                <Sparkles className="w-3.5 h-3.5 text-zinc-200" />
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex border border-zinc-200 p-1 bg-white rounded-sm">
                <button
                  onClick={() => setFilter("recent")}
                  className={`px-6 py-2.5 text-[10px] font-bold tracking-[0.2em] uppercase rounded-sm ${filter === "recent" ? "bg-black text-white" : "text-zinc-400 "}`}
                >
                  Mới nhất
                </button>
                <button
                  onClick={() => setFilter("trending")}
                  className={`px-6 py-2.5 text-[10px] font-bold tracking-[0.2em] uppercase rounded-sm ${filter === "trending" ? "bg-black text-white" : "text-zinc-400 "}`}
                >
                  Xu hướng
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          <aside className="lg:col-span-3 space-y-10 order-2 lg:order-1">
            <div className="bg-card border border-border p-8 rounded-sm">
              <h3 className="text-[10px] font-bold text-foreground tracking-[0.2em] uppercase mb-6 border-b border-border pb-4 flex items-center gap-2">
                <Trophy className="w-4 h-4" /> Bảng vinh danh Tác giả
              </h3>

              {ranking.length === 0 ? (
                <p className="text-[11px] text-muted-foreground font-bold tracking-widest text-center py-4">
                  Chưa có dữ liệu
                </p>
              ) : (
                ranking.map((r, i) => (
                  <div
                    key={i}
                    className="flex gap-4 items-center group border-b border-border last:border-0 pb-4 mb-4 last:pb-0 last:mb-0"
                  >
                    <div className="w-10 h-10 bg-black text-white font-bold flex items-center shrink-0 justify-center text-[12px] border border-black tracking-tighter rounded-sm">
                      #{i + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-[12px] font-bold tracking-widest text-foreground truncate uppercase">
                        {r.full_name || "Tác giả ẩn danh"}
                      </h4>
                      <span className="text-[10px] text-zinc-400 font-bold truncate flex items-center gap-1.5 tracking-widest uppercase">
                        {r.score.toLocaleString("vi-VN")} điểm
                      </span>
                    </div>
                  </div>
                ))
              )}
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
                      className="px-4 py-2 bg-white border border-zinc-100 text-[10px] font-bold text-zinc-400 rounded-sm uppercase tracking-widest"
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
                <p className="text-[11px] text-muted-foreground font-bold tracking-widest text-center py-4">
                  Chưa có dữ liệu
                </p>
              ) : (
                readerRanking.map((r, i) => (
                  <div
                    key={i}
                    className="flex gap-4 items-center group border-b border-border last:border-0 pb-4 mb-4 last:pb-0 last:mb-0"
                  >
                    <div className="w-10 h-10 bg-zinc-200 text-black font-bold flex items-center shrink-0 justify-center text-[12px] border border-zinc-200 tracking-tighter rounded-sm">
                      #{i + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-[12px] font-bold tracking-widest text-foreground truncate uppercase">
                        {r.full_name || "Độc giả ẩn danh"}
                      </h4>
                      <span className="text-[10px] text-zinc-400 font-bold truncate flex items-center gap-1.5 tracking-widest uppercase">
                        {r.score.toLocaleString("vi-VN")} đóng góp
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="bg-card border border-border p-8 rounded-sm">
              <h3 className="text-[10px] font-bold text-foreground tracking-[0.2em] uppercase mb-6 border-b border-border pb-4 flex items-center gap-2">
                <BookText className="w-4 h-4" /> Tài liệu đáng đọc
              </h3>
              {documentSuggestions.length === 0 ? (
                <p className="text-[11px] text-muted-foreground font-bold tracking-widest text-center py-4">
                  Chưa có gợi ý
                </p>
              ) : (
                <div className="space-y-6 pt-1">
                  {documentSuggestions.map((b, i) => (
                    <div
                      key={i}
                      className="flex gap-4 items-center group cursor-pointer border border-transparent p-2 rounded-sm"
                    >
                      <div className="w-12 h-16 bg-white border border-zinc-200 rounded-sm shrink-0 flex items-center justify-center overflow-hidden grayscale ">
                        <BookText className="w-6 h-6 text-zinc-200" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-[12px] font-bold tracking-widest text-foreground truncate transition-colors uppercase">
                          {b.title}
                        </h4>
                        <span className="text-[10px] text-zinc-400 font-bold tracking-widest uppercase">
                          {b.mentions} đề xuất
                        </span>
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
                <p className="text-[11px] text-muted-foreground leading-relaxed font-bold uppercase tracking-widest text-center py-4">
                  Không có gợi ý
                </p>
              ) : (
                suggestions.map((s, i) => (
                  <div
                    key={i}
                    className="flex gap-4 items-center group cursor-pointer border-b border-border last:border-0 pb-4 last:pb-0 mb-4 last:mb-0"
                  >
                    <div className="w-10 h-10 bg-black text-white font-bold flex items-center shrink-0 justify-center text-[12px] border border-black tracking-tighter rounded-sm">
                      {s.display_name?.[0]?.toUpperCase() || "A"}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-[12px] font-bold tracking-widest text-foreground truncate uppercase">
                        {s.display_name}
                      </h4>
                      <span className="text-[10px] text-zinc-400 font-bold truncate tracking-widest uppercase">
                        {s.total_match || 0} điểm chung
                      </span>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        if (currentUser) followUser(s._id);
                        else
                          showToast(
                            "Vui lòng đăng nhập để thực hiện.",
                            "error",
                          );
                      }}
                      title="Theo dõi"
                      className="h-8 px-4 text-[10px] font-bold uppercase tracking-widest rounded-none shrink-0 border-zinc-200"
                    >
                      Theo dõi
                    </Button>
                  </div>
                ))
              )}
            </div>
          </aside>

          <main className="lg:col-span-9 space-y-12 order-1 lg:order-2">
            <div className="flex gap-4 overflow-x-auto pb-10 pt-2 hide-scrollbar -mx-4 px-4 md:mx-0 md:px-0 border-b border-zinc-100">
              {currentUser && (
                <div
                  onClick={() => setShowStoryModal(true)}
                  className="relative w-32 h-48 rounded-sm overflow-hidden cursor-pointer shrink-0 group bg-white border border-zinc-200 flex flex-col "
                >
                  <div className="flex-1 bg-zinc-200 relative overflow-hidden ">
                    {currentUser?.avatar_url ? (
                      <img
                        src={currentUser.avatar_url}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Plus className="w-8 h-8 text-zinc-400" />
                      </div>
                    )}
                  </div>
                  <div className="p-3 bg-white text-center">
                    <span className="text-[10px] font-bold tracking-widest uppercase text-black">
                      Tạo tin
                    </span>
                  </div>
                </div>
              )}

              {stories.map((story, idx) => (
                <div
                  key={story.id}
                  className="relative w-32 h-48 rounded-sm overflow-hidden cursor-pointer shrink-0 group bg-black border border-zinc-200 flex flex-col "
                >
                  <div
                    className="absolute inset-0 bg-gradient-to-b from-black/20 via-transparent to-black/60 z-10"
                    onClick={() => {
                      setActiveStoryIndex(idx);
                      setViewingStoryMode(true);
                      setStoryProgress(0);
                    }}
                  ></div>
                  {story.media_url ? (
                    <img
                      src={story.media_url}
                      className="w-full h-full object-cover grayscale "
                    />
                  ) : (
                    <div
                      className="w-full h-full flex items-center justify-center p-4 text-center bg-zinc-900"
                      style={{ color: story.text_color || "#ffffff" }}
                    >
                      <span className="text-[10px] font-bold tracking-tighter leading-tight line-clamp-4">
                        {story.text_content}
                      </span>
                    </div>
                  )}
                  {currentUser &&
                    (story.user_id === currentUser.id ||
                      story.author_id === currentUser.id) && (
                      <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteStoryConfirm(story.id);
                          }}
                        className="absolute top-2 right-2 z-20 h-8 w-8 bg-black/40 text-white flex items-center justify-center border border-white/20 rounded-sm"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                </div>
              ))}
            </div>

            <div className="space-y-12">
              {currentUser && (
                <div className="bg-white border border-zinc-200 p-8 rounded-sm flex flex-col ">
                  <div className="flex gap-6 items-start">
                    <div className="w-14 h-14 bg-zinc-900 rounded-sm border border-zinc-200 flex shrink-0 items-center justify-center text-white font-bold text-xl overflow-hidden relative cursor-pointer ">
                      {currentUser?.avatar_url ? (
                        <img
                          src={currentUser.avatar_url}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        currentUser?.display_name?.[0]?.toUpperCase() || "U"
                      )}
                    </div>
                    <div className="flex-1">
                      <textarea
                        id="composer-textarea"
                        className="w-full bg-transparent outline-none text-foreground resize-none min-h-[56px] text-xl font-bold tracking-tighter placeholder:text-muted-foreground placeholder:font-normal mt-1.5"
                        placeholder=""
                        value={content}
                        rows={
                          isQuoteMode
                            ? 2
                            : Math.max(1 + content.split("\n").length, 2)
                        }
                        onChange={handleContentChange}
                      ></textarea>

                      <div className="relative">
                        {documentSuggestions.length > 0 && (
                          <div className="absolute top-full left-0 z-50 bg-white border border-zinc-200 mt-2 overflow-hidden w-full max-w-md animate-in slide-in-from-top-2 rounded-sm">
                            <div className="px-6 py-4 bg-white border-b border-zinc-100">
                              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.3em] flex items-center gap-2">
                                <BookText className="w-3.5 h-3.5" /> Gợi ý tài
                                liệu
                              </span>
                            </div>
                            <div className="max-h-[300px] overflow-y-auto">
                              {documentSuggestions.map(
                                (doc: any, i: number) => (
                                  <div
                                    key={i}
                                    className="px-6 py-4 cursor-pointer border-b border-zinc-50 last:border-0 flex justify-between items-center group "
                                    onClick={() => selectAttachedDocument(doc)}
                                  >
                                    <div className="flex-1 min-w-0 pr-4">
                                      <p className="text-[12px] font-bold text-black uppercase tracking-widest truncate transition-transform">
                                        {doc.title}
                                      </p>
                                      <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-tighter mt-1">
                                        {doc.author_name ||
                                          doc.author ||
                                          "Tác giả ẩn danh"}
                                      </p>
                                    </div>
                                    <ChevronRight className="w-4 h-4 text-zinc-200 transition-colors" />
                                  </div>
                                ),
                              )}
                            </div>
                          </div>
                        )}
                      </div>

                      {attachedDocumentId && (
                        <div className="mt-6 p-6 bg-white border border-zinc-200 rounded-sm flex items-center justify-between group animate-in fade-in ">
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-14 bg-white border border-zinc-100 flex items-center justify-center shrink-0">
                              <BookText className="w-5 h-5 text-zinc-200" />
                            </div>
                            <div className="space-y-1">
                              <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                                Đã đính kèm
                              </p>
                              <p className="text-[12px] font-bold text-black uppercase tracking-widest">
                                {attachedDocumentTitle}
                              </p>
                            </div>
                          </div>
                          <button
                            onClick={() => {
                              setAttachedDocumentId("");
                              setAttachedDocumentTitle("");
                            }}
                            className="p-3 text-zinc-300 transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      )}

                      {mediaUrls.length > 0 && (
                        <div className="grid grid-cols-2 gap-2 mt-6 overflow-hidden border border-border rounded-sm">
                          {mediaUrls.map((url, i) => (
                            <div
                              key={i}
                              className={`relative w-full aspect-square ${mediaUrls.length === 1 ? "col-span-2 aspect-video" : ""}`}
                            >
                              {url.match(/\.(mp4|webm)$/i) ? (
                                <video
                                  src={`${API_URL}${url}`}
                                  className="object-cover w-full h-full"
                                  autoPlay
                                  muted
                                  loop
                                />
                              ) : (
                                <img
                                  src={`${API_URL}${url}`}
                                  alt="Preview"
                                  className="object-cover w-full h-full"
                                />
                              )}
                              <button
                                onClick={() =>
                                  setMediaUrls(
                                    mediaUrls.filter((_, idx) => idx !== i),
                                  )
                                }
                                className="absolute top-3 right-3 bg-black/60 text-white rounded-none w-10 h-10 flex items-center justify-center backblur-sm transition-colors"
                              >
                                <X className="w-6 h-6" />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {showExtras && (
                    <div className="mt-8 p-6 bg-white space-y-4 border border-zinc-100 rounded-sm">
                      <div className="space-y-3">
                        <h4 className="text-[10px] font-bold text-muted-foreground flex items-center gap-2 uppercase tracking-widest">
                          <BarChart2 className="w-4 h-4" /> Tạo bình chọn
                        </h4>
                        <Input
                          value={pollText1}
                          onChange={(e) => setPollText1(e.target.value)}
                          placeholder=""
                          className="h-12 bg-white text-xs font-bold border-zinc-200 rounded-sm focus-visible:ring-black"
                        />
                        <Input
                          value={pollText2}
                          onChange={(e) => setPollText2(e.target.value)}
                          placeholder=""
                          className="h-12 bg-white text-xs font-bold border-zinc-200 rounded-sm focus-visible:ring-black"
                        />
                      </div>
                    </div>
                  )}

                  <div className="mt-8 pt-6 border-t border-zinc-100">
                    <div className="flex items-center justify-between">
                      <div className="flex gap-2">
                        <label
                          className="cursor-pointer h-12 w-12 border border-zinc-100 rounded-sm flex items-center justify-center text-zinc-400 "
                          title="Đính kèm Ảnh/Video"
                        >
                          <ImageIcon className="w-5 h-5" />
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
                          className={`h-12 w-12 border rounded-sm flex items-center justify-center ${showExtras ? "bg-black text-white border-black" : "bg-white text-zinc-400 border-zinc-100"}`}
                          title="Thêm bình chọn"
                        >
                          <BarChart2 className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => setIsQuoteMode(!isQuoteMode)}
                          className={`h-12 w-12 border rounded-sm flex items-center justify-center ${isQuoteMode ? "bg-black text-white border-black" : "bg-white text-zinc-400 border-zinc-100"}`}
                          title="Chế độ Trích dẫn"
                        >
                          <Quote className="w-5 h-5" />
                        </button>
                      </div>

                      <div className="flex items-center gap-4">
                        <select
                          id="post-privacy"
                          className="h-12 px-6 bg-white border border-zinc-100 text-[10px] font-bold uppercase tracking-widest outline-none cursor-pointer rounded-sm"
                        >
                          <option value="public">Công khai</option>
                          <option value="following">Người theo dõi</option>
                          <option value="private">Chỉ mình tôi</option>
                        </select>
                        <button
                          onClick={createPost}
                          disabled={!content.trim() && mediaUrls.length === 0}
                          className="h-12 px-10 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] disabled:opacity-30 disabled:pointer-events-none active:scale-95 rounded-sm"
                        >
                          Đăng bài
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {currentUser && (
                <div className="space-y-6">
                  <div className="bg-white border border-zinc-200 text-xs py-5 px-8 flex items-center justify-between rounded-sm">
                    <div className="flex items-center gap-4">
                      <Sparkles className="w-5 h-5 text-zinc-400" />
                      <span className="font-bold tracking-[0.2em] uppercase text-black">
                        Phân tích bảng tin với AI
                      </span>
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
                      className="h-10 px-8 border border-black text-black font-bold uppercase text-[10px] tracking-widest disabled:opacity-50 rounded-sm"
                    >
                      {isSummarizing ? "Đang xử lý" : "Bắt đầu tóm tắt"}
                    </button>
                  </div>
                  {aiSummary && (
                    <div className="bg-white p-8 border border-zinc-200 border-t-0 animate-in fade-in slide-in-from-top-4 rounded-sm">
                      <p className="text-lg leading-relaxed text-black italic font-medium tracking-tight">
                        "{aiSummary}"
                      </p>
                    </div>
                  )}
                </div>
              )}

              <div className="flex flex-col gap-10">
                {loading ? (
                  <div className="space-y-8">
                    {[...Array(3)].map((_, i) => (
                      <div
                        key={i}
                        className="h-60 bg-white border border-zinc-100 animate-pulse rounded-sm"
                      />
                    ))}
                  </div>
                ) : posts.length === 0 ? (
                  <div className="text-center py-32 border border-dashed border-zinc-100 bg-white rounded-sm">
                    <MessageCircle className="w-16 h-16 text-zinc-100 mx-auto mb-10 stroke-[1]" />
                    <h3 className="text-2xl font-bold tracking-tighter text-black uppercase">
                      Chưa có nội dung nào
                    </h3>
                    <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest mt-4">
                      Hãy là người đầu tiên chia sẻ tri thức hôm nay
                    </p>
                  </div>
                ) : (
                  posts.map((post) => (
                    <div
                      key={post.id}
                      className="bg-white border border-zinc-200 p-10 rounded-sm group"
                    >
                      <div className="flex items-center gap-6 mb-8">
                        <div className="w-14 h-14 bg-white rounded-sm flex shrink-0 items-center justify-center text-zinc-300 font-bold border border-zinc-100 overflow-hidden relative">
                          {post.user?.avatar_url ? (
                            <img
                              src={post.user.avatar_url}
                              className="w-full h-full object-cover grayscale "
                            />
                          ) : (
                            <UserIcon className="w-6 h-6 stroke-[1]" />
                          )}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-bold text-black text-lg tracking-tight uppercase transition-transform">
                            {post.user?.username || "Người dùng ẩn danh"}
                          </h4>
                          <div className="flex items-center gap-4 text-[10px] font-bold text-zinc-400 uppercase tracking-widest pt-1">
                            <span>
                              {new Date(post.created_at).toLocaleString(
                                "vi-VN",
                              )}
                            </span>
                            {post.is_pinned && (
                              <span className="flex items-center gap-1.5 text-black">
                                <Pin className="w-3 h-3 fill-black" /> Đã ghim
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-1 opacity-0 transition-opacity">
                          <button
                            onClick={() => translatePost(post.id, post.content)}
                            className="p-3 rounded-sm text-zinc-300 "
                          >
                            <Sparkles className="w-4 h-4" />
                          </button>
                          {(currentUser?._id || "") &&
                          (currentUser?._id === post.author_id ||
                            currentUser?._id === post.user_id) ? (
                            <>
                              <button
                                onClick={() => togglePinPost(post.id)}
                                className="p-3 rounded-sm text-zinc-300 "
                              >
                                <Pin
                                  className={`w-4 h-4 ${post.is_pinned ? "fill-black text-black" : ""}`}
                                />
                              </button>
                              <button
                                onClick={() => setDeletePostConfirm(post.id)}
                                className="p-3 rounded-sm text-zinc-300 "
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => hidePost(post.id)}
                                className="p-3 rounded-sm text-zinc-300 "
                              >
                                <EyeOff className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => setReportModal({ postId: post.id, reason: "" })}
                                className="p-3 rounded-sm text-zinc-300 "
                              >
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
                              <div
                                key={i}
                                className={`relative overflow-hidden bg-white ${post.media_urls.length === 1 ? "md:col-span-2" : ""}`}
                              >
                                {url.match(/\.(mp4|webm)$/i) ? (
                                  <video
                                    src={`${API_URL}${url}`}
                                    className="w-full h-full object-cover"
                                    controls
                                  />
                                ) : (
                                  <img
                                    src={`${API_URL}${url}`}
                                    alt="Feed"
                                    className="w-full h-full object-cover grayscale cursor-pointer"
                                  />
                                )}
                              </div>
                            ))}
                          </div>
                        )}

                        {post.attached_document_id && (
                          <Link
                            href={`/documents/${post.attached_document_id}`}
                            className="flex items-center justify-between p-6 bg-white border border-transparent rounded-sm"
                          >
                            <div className="flex items-center gap-6">
                              <div className="w-12 h-16 bg-white border border-zinc-100 rounded-sm flex items-center justify-center shrink-0">
                                <BookText className="w-6 h-6 text-zinc-200" />
                              </div>
                              <div className="space-y-1">
                                <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                                  Tài liệu đính kèm
                                </p>
                                <h5 className="text-base font-bold text-black tracking-tight uppercase">
                                  {post.attached_document_title ||
                                    "Xem tài liệu"}
                                </h5>
                              </div>
                            </div>
                            <ChevronRight className="w-5 h-5 text-zinc-300" />
                          </Link>
                        )}
                      </div>

                      <div className="mt-10 pt-8 border-t border-zinc-50 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={(e) => toggleLike(post.id, "like", e)}
                            className={`h-12 px-6 flex items-center gap-3 border rounded-sm font-bold text-[11px] uppercase tracking-widest ${post.likes?.includes(currentUser?._id || "") ? "bg-black text-white border-black" : "bg-white text-zinc-400 border-zinc-100"}`}
                          >
                            <Heart
                              className={`w-4 h-4 ${post.likes?.includes(currentUser?._id || "") ? "fill-white" : ""}`}
                            />
                            {post.likes?.length || 0}
                          </button>
                          <button
                            onClick={() =>
                              setExpandedComments(
                                expandedComments === post.id ? null : post.id,
                              )
                            }
                            className={`h-12 px-6 flex items-center gap-3 border border-zinc-100 bg-white text-zinc-400 rounded-sm font-bold text-[11px] uppercase tracking-widest`}
                          >
                            <MessageCircle className="w-4 h-4" />
                            {(post.comments || []).length}
                          </button>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => toggleSave(post.id)}
                            className={`h-12 w-12 flex items-center justify-center border rounded-sm ${post.saved ? "bg-black text-white border-black" : "bg-white text-zinc-400 border-zinc-100"}`}
                          >
                            <Bookmark
                              className={`w-4 h-4 ${post.saved ? "fill-white" : ""}`}
                            />
                          </button>
                          <button
                            onClick={() => repostPost(post.id)}
                            className="h-12 w-12 flex items-center justify-center border border-zinc-100 bg-white text-zinc-400 rounded-sm"
                            title="Chia sẻ lại"
                          >
                            <RotateCw className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      {expandedComments === post.id && (
                        <div className="mt-6 bg-white p-6 border border-zinc-100 rounded-sm animate-in slide-in-from-top-4 ">
                          <div className="max-h-80 overflow-y-auto pr-4 space-y-6 mb-6">
                            {post.comments?.length > 0 ? (
                              post.comments.map((c: any, i: number) => (
                                <div
                                  key={i}
                                  className={`text-sm ${c.parent_id ? "ml-10 relative pl-6 border-l border-zinc-200" : ""}`}
                                >
                                  <div className="flex justify-between w-full group">
                                    <div className="space-y-1">
                                      <span className="font-bold text-black uppercase tracking-widest text-[10px]">
                                        {c.user.display_name || "Người dùng"}
                                        :{" "}
                                      </span>
                                      <p className="text-zinc-500 font-medium leading-relaxed">
                                        {c.content || c.text}
                                      </p>
                                    </div>
                                    {currentUser && (
                                      <span
                                        onClick={() => {
                                          setReplyToContext({
                                            postId: post.id,
                                            commentId: c.id,
                                            userName:
                                              c.user.display_name ||
                                              "Người dùng",
                                          });
                                          setCommentText("");
                                        }}
                                        className="text-black text-[10px] font-bold uppercase tracking-widest opacity-0 cursor-pointer ml-4"
                                      >
                                        Trả lời
                                      </span>
                                    )}
                                  </div>
                                </div>
                              ))
                            ) : (
                              <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest italic text-center py-4">
                                Chưa có bình luận
                              </div>
                            )}
                          </div>

                          {currentUser ? (
                            <div className="space-y-4">
                              {replyToContext &&
                                replyToContext.postId === post.id && (
                                  <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex justify-between bg-white border border-zinc-100 p-3 rounded-sm">
                                    <span>
                                      Đang trả lời{" "}
                                      <b className="text-black">
                                        {replyToContext.userName}
                                      </b>
                                    </span>
                                    <span
                                      className="cursor-pointer "
                                      onClick={() => setReplyToContext(null)}
                                    >
                                      Hủy bỏ
                                    </span>
                                  </div>
                                )}
                              <div className="flex gap-4 items-center">
                                <Input
                                  className="h-12 bg-white border-zinc-100 text-xs font-bold focus-visible:ring-black rounded-sm"
                                  placeholder=""
                                  value={commentText}
                                  onChange={(e) =>
                                    setCommentText(e.target.value)
                                  }
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter")
                                      submitComment(post.id);
                                  }}
                                />
                                <Button
                                  onClick={() => submitComment(post.id)}
                                  className="h-12 w-12 bg-black text-white rounded-sm shrink-0"
                                >
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
                  ))
                )}
              </div>

              {!loading && hasMore && (
                <div className="flex justify-center pt-10">
                  <button
                    onClick={() => fetchFeed()}
                    disabled={loading}
                    className="h-16 px-16 bg-white border border-zinc-100 text-[11px] font-bold uppercase tracking-[0.2em] disabled:opacity-30 rounded-sm"
                  >
                    {loading ? "Đang tải" : "Xem thêm bài viết"}
                  </button>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>

      {currentUser && showStoryModal && (
        <div className="fixed inset-0 z-[300] bg-background/80 backblur-sm flex items-center justify-center animate-in fade-in-0 ">
          <div className="bg-card w-full h-[100dvh] md:h-[85vh] max-w-sm md: md:border border-border flex flex-col relative overflow-hidden">
            <div className="absolute z-10 top-0 left-0 right-0 p-3 flex justify-between items-center bg-gradient-to-b from-black/60 to-transparent text-white">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowStoryModal(false)}
                  className="p-2 backblur-md bg-black/20 rounded-none transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
                <button
                  onClick={() => {
                    setShowStoryArchive(!showStoryArchive);
                    if (!showStoryArchive) fetchArchivedStories();
                  }}
                  className={`p-2 backblur-md rounded-none transition-colors ${showStoryArchive ? "bg-white/30" : "bg-black/20"}`}
                  title="Kho lưu trữ tin của bạn"
                >
                  <Archive className="w-5 h-5" />
                </button>
              </div>
              <div className="flex gap-2 items-center">
                <select
                  value={storyFontStyle}
                  onChange={(e) => setStoryFontStyle(e.target.value)}
                  className="bg-black/20 text-white text-xs px-3 py-1.5 rounded-none backblur-md outline-none cursor-pointer "
                >
                  <option value="sans" className="text-black">
                    Sans
                  </option>
                  <option value="mono" className="text-black">
                    Mono
                  </option>
                </select>
                <select
                  value={storyPrivacy}
                  onChange={(e) => setStoryPrivacy(e.target.value)}
                  className="bg-black/20 text-white text-xs px-3 py-1.5 rounded-none backblur-md outline-none cursor-pointer "
                >
                  <option value="public" className="text-black">
                    Công khai
                  </option>
                  <option value="friends" className="text-black">
                    Bạn bè
                  </option>
                  <option value="close_friends" className="text-black">
                    Bạn thân
                  </option>
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
                <h3 className="text-sm font-bold text-foreground mb-4 border-b border-border pb-3">
                  Kho lưu trữ tin của bạn
                </h3>
                {archivedStories.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 text-center">
                    <Archive
                      className="w-10 h-10 text-muted-foreground mb-3"
                      strokeWidth={1}
                    />
                    <p className="text-sm text-muted-foreground">
                      Chưa có tin nào được lưu trữ.
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-2">
                    {archivedStories.map((s, i) => (
                      <div
                        key={i}
                        className="aspect-[9/16] overflow-hidden relative border border-border cursor-pointer group"
                        style={{
                          backgroundColor:
                            s.bg_color || s.background_color || "#18181b",
                        }}
                      >
                        {s.media_url ? (
                          <img
                            src={s.media_url}
                            className="w-full h-full object-cover"
                            alt="Story"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center p-2">
                            <p className="text-white text-[12px] font-semibold text-center line-clamp-4 break-words">
                              {s.text_content}
                            </p>
                          </div>
                        )}
                        <div className="absolute bottom-0 left-0 right-0 bg-black/50 px-2 py-1">
                          <span className="text-white text-[13px] font-medium">
                            {new Date(s.created_at).toLocaleDateString("vi-VN")}
                          </span>
                        </div>
                        <div className="absolute inset-0 bg-black/0 transition-colors" />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div
              className="flex-1 flex flex-col justify-center items-center p-6 transition-colors relative"
              style={{ backgroundColor: storyBgColor }}
            >
              {storyMediaUrl && (
                <div className="absolute inset-0 w-full h-full">
                  <img
                    src={storyMediaUrl}
                    alt="Story Media"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-black/30" />
                </div>
              )}

              <textarea
                className="w-full bg-transparent border-none outline-none text-center resize-none text-2xl font-bold placeholder:opacity-50 z-10"
                placeholder=""
                value={storyText}
                onChange={(e) => setStoryText(e.target.value)}
                autoFocus
                rows={5}
                style={{
                  color: storyTextColor,
                  fontFamily:
                    storyFontStyle === "mono"
                      ? "Courier New, monospace"
                      : "inherit",
                }}
              ></textarea>

              {storyLinkUrl && (
                <div className="mt-4 px-4 py-2 bg-white/20 backblur-md rounded-none border border-white/20 flex gap-2 items-center max-w-[80%] z-10 ">
                  <Globe className="w-4 h-4 text-white" />
                  <span className="text-white text-sm truncate font-medium">
                    {storyLinkUrl}
                  </span>
                  <button
                    onClick={() => setStoryLinkUrl("")}
                    className="text-white/70 ml-2"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              )}

              {storyAddPoll && (
                <div className="mt-6 w-full max-w-[280px] bg-black/40 backblur-md border border-white/20 p-4 z-10 flex flex-col gap-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-white text-xs font-bold tracking-wider">
                      Tạo Khảo Sát
                    </span>
                    <button
                      onClick={() => setStoryAddPoll(false)}
                      className="text-white/70 "
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <input
                    type="text"
                    placeholder=""
                    value={storyPollQuestion}
                    onChange={(e) => setStoryPollQuestion(e.target.value)}
                    className="w-full bg-white/10 text-white text-sm border-b border-white/30 outline-none px-2 py-1 placeholder:text-white/50 font-semibold"
                  />
                  {storyPollOptions.map((opt, idx) => (
                    <input
                      key={idx}
                      type="text"
                      placeholder=""
                      value={opt}
                      onChange={(e) => {
                        const newOpts = [...storyPollOptions];
                        newOpts[idx] = e.target.value;
                        setStoryPollOptions(newOpts);
                      }}
                      className="w-full bg-white/10 text-white text-sm border border-white/20 outline-none px-3 py-2 placeholder:text-white/50 focus:bg-white/20 font-medium text-center"
                    />
                  ))}
                  {storyPollOptions.length < 4 && (
                    <button
                      onClick={() =>
                        setStoryPollOptions([...storyPollOptions, ""])
                      }
                      className="text-white/70 text-xs font-bold py-2 flex items-center justify-center gap-2 tracking-widest"
                    >
                      <Plus className="w-3 h-3" />
                      Thêm lựa chọn
                    </button>
                  )}
                </div>
              )}

              {storyAddQuiz && (
                <div className="mt-6 w-full max-w-[280px] bg-black/40 backblur-md border border-white/20 p-4 z-10 flex flex-col gap-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-white text-xs font-bold tracking-wider">
                      Tạo Trắc Nghiệm
                    </span>
                    <button
                      onClick={() => setStoryAddQuiz(false)}
                      className="text-white/70 "
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <input
                    type="text"
                    placeholder=""
                    value={storyQuizQuestion}
                    onChange={(e) => setStoryQuizQuestion(e.target.value)}
                    className="w-full bg-white/10 text-white text-sm border-b border-white/30 outline-none px-2 py-1 placeholder:text-white/50 font-semibold"
                  />
                  {storyQuizOptions.map((opt, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <button
                        onClick={() => setStoryQuizCorrectIdx(idx)}
                        className={`w-6 h-6 flex items-center justify-center rounded-none border ${storyQuizCorrectIdx === idx ? "bg-black border-black text-white" : "bg-white/10 border-white/30"}`}
                      >
                        {storyQuizCorrectIdx === idx && (
                          <CheckCircle className="w-4 h-4" />
                        )}
                      </button>
                      <input
                        type="text"
                        placeholder=""
                        value={opt}
                        onChange={(e) => {
                          const newOpts = [...storyQuizOptions];
                          newOpts[idx] = e.target.value;
                          setStoryQuizOptions(newOpts);
                        }}
                        className="w-full bg-white/10 text-white text-sm border border-white/20 outline-none px-3 py-2 placeholder:text-white/50 focus:bg-white/20 font-medium text-center"
                      />
                    </div>
                  ))}
                  {storyQuizOptions.length < 4 && (
                    <button
                      onClick={() =>
                        setStoryQuizOptions([...storyQuizOptions, ""])
                      }
                      className="text-white/70 text-xs font-bold py-2 flex items-center justify-center gap-2 tracking-widest"
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
                      placeholder=""
                      className="pl-9 h-9 w-full bg-muted/50 border-border text-sm rounded-none"
                      value={storyLinkUrl}
                      onChange={(e) => setStoryLinkUrl(e.target.value)}
                      autoFocus
                    />
                    {storyLinkUrl && (
                      <button
                        onClick={() => setStoryLinkUrl("")}
                        className="absolute right-3 text-muted-foreground "
                      >
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
                      placeholder=""
                      className="pl-9 h-9 w-full bg-muted/50 border-border text-sm rounded-none"
                      value={storyMentionsInput}
                      onChange={(e) => setStoryMentionsInput(e.target.value)}
                      autoFocus
                    />
                  </div>
                </div>
              )}

              <div className="flex items-center gap-2">
                <label
                  className="cursor-pointer h-10 w-10 flex items-center justify-center bg-muted/50 rounded-none transition-colors border border-border shrink-0"
                  title="Ảnh / Video"
                >
                  {isStoryUploading ? (
                    <div className="w-4 h-4 rounded-none border-2 border-foreground border-t-transparent animate-spin" />
                  ) : (
                    <ImageIcon className="w-5 h-5 text-foreground" />
                  )}
                  <input
                    type="file"
                    className="hidden"
                    accept="image/*"
                    onChange={handleStoryImageUpload}
                  />
                </label>
              </div>
            </div>
          </div>
        </div>
      )}
      {viewingStoryMode &&
        activeStoryIndex >= 0 &&
        stories[activeStoryIndex] && (
          <div className="fixed inset-0 z-[200] bg-black/95 backblur-sm flex justify-center items-center animate-in fade-in-0 text-white">
            <div className="absolute top-4 right-4 z-[210] flex gap-4 hidden md:flex">
              {(stories[activeStoryIndex].user_id ===
                (currentUser?._id || "") ||
                stories[activeStoryIndex].author_id ===
                  (currentUser?._id || "")) && (
                <button
                  onClick={() =>
                    deleteStory(
                      stories[activeStoryIndex].id ||
                        stories[activeStoryIndex]._id,
                    )
                  }
                  className="text-white p-2 bg-white/10 rounded-none transition-colors backblur-md"
                  title="Xóa tin này"
                >
                  <Trash2 className="w-6 h-6" />
                </button>
              )}
              <button
                onClick={() => {
                  setViewingStoryMode(false);
                  setStoryProgress(0);
                }}
                className="text-white p-2 bg-white/10 rounded-none transition-colors backblur-md"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div
              className="flex-1 flex flex-col justify-between items-center relative overflow-hidden w-full max-w-sm mx-auto h-[100dvh] md:h-[85vh] md:w-[400px] group md: md:border border-border/50"
              style={{
                backgroundColor:
                  stories[activeStoryIndex].background_color || "#18181b",
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
                          stories[activeStoryIndex]._id,
                      )
                    }
                    className="text-white p-1 bg-black/20 rounded-none transition-colors backblur-md"
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
                  className="text-white p-1 bg-black/20 rounded-none transition-colors backblur-md"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="absolute top-0 left-0 right-0 px-2 pt-2 flex gap-1 z-[205] w-full bg-gradient-to-b from-black/50 to-transparent pb-4">
                {stories.map((s, idx) => (
                  <div
                    key={s.id}
                    className="flex-1 h-[3px] bg-white/30 rounded-none overflow-hidden backblur-md"
                  >
                    <div
                      className="h-full bg-white ease-linear "
                      style={{
                        width:
                          idx < activeStoryIndex
                            ? "100%"
                            : idx === activeStoryIndex
                              ? `${storyProgress}%`
                              : "0%",
                      }}
                    />
                  </div>
                ))}
              </div>

              {stories[activeStoryIndex].media_url && (
                <div className="absolute inset-0 w-full h-full flex flex-col justify-center items-center">
                  <img
                    src={stories[activeStoryIndex].media_url}
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-black/30" />
                  <div className="w-full px-6 flex-1 flex flex-col gap-6 justify-center items-center overflow-hidden z-10">
                    {stories[activeStoryIndex].text_content && (
                      <h2
                        className="text-2xl font-bold text-center max-w-full leading-snug break-words mb-4"
                        style={{
                          color:
                            stories[activeStoryIndex].text_color || "#ffffff",
                          fontFamily:
                            stories[activeStoryIndex].font_style === "mono"
                              ? "Courier New, monospace"
                              : "inherit",
                        }}
                      >
                        {stories[activeStoryIndex].text_content}
                      </h2>
                    )}
                    {stories[activeStoryIndex].link_url && (
                      <a
                        href={stories[activeStoryIndex].link_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-5 py-2.5 bg-white/20 backblur-md rounded-none text-white font-semibold border border-white/20 max-w-[80%]"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Globe className="w-4 h-4 shrink-0" />
                        <span className="truncate text-sm">
                          {stories[activeStoryIndex].link_url}
                        </span>
                      </a>
                    )}
                    {stories[activeStoryIndex].poll_data ? (
                      <div
                        className="w-full max-w-[280px] bg-black/40 backblur-md border border-white/20 p-4 z-10 flex flex-col gap-2 pointer-events-auto"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <h4 className="text-white text-sm font-bold text-center mb-2">
                          {stories[activeStoryIndex].poll_data.question}
                        </h4>
                        {stories[activeStoryIndex].poll_data.options.map(
                          (opt: string, idx: number) => {
                            const totalVotes = Object.keys(
                              stories[activeStoryIndex].poll_data.voters || {},
                            ).length;
                            const myVote = (stories[activeStoryIndex].poll_data
                              .voters || {})[currentUser?._id || ""];
                            const hasVoted = myVote !== undefined;
                            const optsVotes = Object.values(
                              stories[activeStoryIndex].poll_data.voters || {},
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
                                  votePoll(
                                    stories[activeStoryIndex].id ||
                                      stories[activeStoryIndex]._id,
                                    idx,
                                  )
                                }
                                className={`relative w-full text-white text-sm border overflow-hidden font-medium ${myVote === idx ? "border-primary bg-primary/20" : "border-white/20 bg-white/10"} ${hasVoted ? "cursor-default" : " cursor-pointer"} `}
                              >
                                <div
                                  className="absolute top-0 bottom-0 left-0 bg-white/20 "
                                  style={{
                                    width: hasVoted ? `${percent}%` : "0%",
                                  }}
                                />
                                <div className="relative px-3 py-2.5 flex justify-between items-center z-10">
                                  <span className="truncate pr-2">{opt}</span>
                                  {hasVoted && (
                                    <span className="font-bold text-xs">
                                      {percent}%
                                    </span>
                                  )}
                                </div>
                              </button>
                            );
                          },
                        )}
                        <div className="text-white/50 text-[12px] text-center mt-1 font-bold tracking-widest">
                          {
                            Object.keys(
                              stories[activeStoryIndex].poll_data.voters || {},
                            ).length
                          }{" "}
                          votes
                        </div>
                      </div>
                    ) : stories[activeStoryIndex].quiz_data ? (
                      <div
                        className="w-full max-w-[280px] bg-black/40 backblur-md border border-white/20 p-4 z-10 flex flex-col gap-2 pointer-events-auto"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="text-center font-bold text-xs tracking-widest text-primary/80">
                          Trắc Nghiệm
                        </div>
                        <h4 className="text-white text-sm font-bold text-center mb-2">
                          {stories[activeStoryIndex].quiz_data.question}
                        </h4>
                        {stories[activeStoryIndex].quiz_data.options.map(
                          (opt: string, idx: number) => {
                            const myAnswer = (stories[activeStoryIndex]
                              .quiz_data.answers || {})[currentUser?._id || ""];
                            const hasAnswered = myAnswer !== undefined;
                            const isCorrect =
                              idx ===
                              stories[activeStoryIndex].quiz_data.correct_idx;

                            let buttonClass =
                              "border-white/20 bg-white/10 cursor-pointer";
                            if (hasAnswered) {
                              buttonClass = isCorrect
                                ? "border-black bg-black text-white cursor-default"
                                : myAnswer === idx
                                  ? "border-zinc-300 bg-zinc-200 text-zinc-400 cursor-default"
                                  : "border-white/20 bg-black/20 opacity-50 cursor-default";
                            }

                            return (
                              <button
                                key={idx}
                                onClick={() =>
                                  !hasAnswered &&
                                  answerQuiz(
                                    stories[activeStoryIndex].id ||
                                      stories[activeStoryIndex]._id,
                                    idx,
                                  )
                                }
                                className={`relative w-full text-white text-sm border overflow-hidden font-medium ${buttonClass}`}
                              >
                                <div className="relative px-3 py-2.5 flex justify-between items-center z-10">
                                  <span className="truncate pr-2">{opt}</span>
                                  {hasAnswered && isCorrect && (
                                    <CheckCircle className="w-4 h-4 text-white" />
                                  )}
                                  {hasAnswered &&
                                    !isCorrect &&
                                    myAnswer === idx && (
                                      <XCircle className="w-4 h-4 text-zinc-400" />
                                    )}
                                </div>
                              </button>
                            );
                          },
                        )}
                      </div>
                    ) : null}
                  </div>
                </div>
              )}

              <div className="absolute top-6 left-4 flex gap-2.5 items-center z-[210] p-1.5 pr-4 max-w-[80%]">
                <div className="w-10 h-10 rounded-none flex justify-center items-center overflow-hidden shrink-0 bg-secondary relative">
                  {stories[activeStoryIndex].user?.avatar_url ? (
                    <img
                      src={stories[activeStoryIndex].user.avatar_url}
                      className="w-full h-full object-cover rounded-none"
                    />
                  ) : (
                    <span className="text-foreground font-bold text-sm bg-muted/50 w-full h-full flex justify-center items-center rounded-none backblur-md">
                      {stories[
                        activeStoryIndex
                      ].user?.name?.[0]?.toUpperCase() || "A"}
                    </span>
                  )}
                </div>
                <div className="flex flex-col justify-center">
                  <span className="text-sm font-semibold tracking-tight text-white ">
                    {stories[activeStoryIndex].user?.name || "Người dùng"}
                    {stories[activeStoryIndex].mentions &&
                      stories[activeStoryIndex].mentions.length > 0 && (
                        <span className="text-xs font-normal opacity-90 ml-1">
                          cùng với {stories[activeStoryIndex].mentions.length}{" "}
                          người khác
                        </span>
                      )}
                  </span>
                  <span className="text-[12px] font-medium opacity-80 text-white ">
                    {new Date(
                      stories[activeStoryIndex].created_at,
                    ).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              </div>

              {!stories[activeStoryIndex].media_url && (
                <div className="w-full px-6 flex-1 flex flex-col gap-6 justify-center items-center overflow-hidden z-10">
                  <h2
                    className="text-2xl font-bold text-center max-w-full leading-snug break-words"
                    style={{
                      color: stories[activeStoryIndex].text_color || "#ffffff",
                      fontFamily:
                        stories[activeStoryIndex].font_style === "mono"
                          ? "Courier New, monospace"
                          : "inherit",
                    }}
                  >
                    {stories[activeStoryIndex].text_content}
                  </h2>
                  {stories[activeStoryIndex].link_url && (
                    <a
                      href={stories[activeStoryIndex].link_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 px-5 py-2.5 bg-white/20 backblur-md rounded-none text-white font-semibold border border-white/20 max-w-[80%]"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Globe className="w-4 h-4 shrink-0" />
                      <span className="truncate text-sm">
                        {stories[activeStoryIndex].link_url}
                      </span>
                    </a>
                  )}
                  {stories[activeStoryIndex].poll_data ? (
                    <div
                      className="w-full max-w-[280px] bg-black/40 backblur-md border border-white/20 p-4 z-10 flex flex-col gap-2 pointer-events-auto"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <h4 className="text-white text-sm font-bold text-center mb-2">
                        {stories[activeStoryIndex].poll_data.question}
                      </h4>
                      {stories[activeStoryIndex].poll_data.options.map(
                        (opt: string, idx: number) => {
                          const totalVotes = Object.keys(
                            stories[activeStoryIndex].poll_data.voters || {},
                          ).length;
                          const myVote = (stories[activeStoryIndex].poll_data
                            .voters || {})[currentUser?._id || ""];
                          const hasVoted = myVote !== undefined;
                          const optsVotes = Object.values(
                            stories[activeStoryIndex].poll_data.voters || {},
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
                                votePoll(
                                  stories[activeStoryIndex].id ||
                                    stories[activeStoryIndex]._id,
                                  idx,
                                )
                              }
                              className={`relative w-full text-white text-sm border overflow-hidden font-medium ${myVote === idx ? "border-primary bg-primary/20" : "border-white/20 bg-white/10"} ${hasVoted ? "cursor-default" : " cursor-pointer"} `}
                            >
                              <div
                                className="absolute top-0 bottom-0 left-0 bg-white/20 "
                                style={{
                                  width: hasVoted ? `${percent}%` : "0%",
                                }}
                              />
                              <div className="relative px-3 py-2.5 flex justify-between items-center z-10">
                                <span className="truncate pr-2">{opt}</span>
                                {hasVoted && (
                                  <span className="font-bold text-xs">
                                    {percent}%
                                  </span>
                                )}
                              </div>
                            </button>
                          );
                        },
                      )}
                      <div className="text-white/50 text-[12px] text-center mt-1 font-bold tracking-widest">
                        {
                          Object.keys(
                            stories[activeStoryIndex].poll_data.voters || {},
                          ).length
                        }{" "}
                        votes
                      </div>
                    </div>
                  ) : stories[activeStoryIndex].quiz_data ? (
                    <div
                      className="w-full max-w-[280px] bg-black/40 backblur-md border border-white/20 p-4 z-10 flex flex-col gap-2 pointer-events-auto"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div className="text-center font-bold text-xs tracking-widest text-primary/80">
                        Trắc Nghiệm
                      </div>
                      <h4 className="text-white text-sm font-bold text-center mb-2">
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

                          let buttonClass =
                            "border-white/20 bg-white/10 cursor-pointer";
                          if (hasAnswered) {
                            buttonClass = isCorrect
                              ? "border-black bg-black text-white cursor-default"
                              : myAnswer === idx
                                ? "border-zinc-300 bg-zinc-200 text-zinc-400 cursor-default"
                                : "border-white/20 bg-black/20 opacity-50 cursor-default";
                          }

                          return (
                            <button
                              key={idx}
                              onClick={() =>
                                !hasAnswered &&
                                answerQuiz(
                                  stories[activeStoryIndex].id ||
                                    stories[activeStoryIndex]._id,
                                  idx,
                                )
                              }
                              className={`relative w-full text-white text-sm border overflow-hidden font-medium ${buttonClass}`}
                            >
                              <div className="relative px-3 py-2.5 flex justify-between items-center z-10">
                                <span className="truncate pr-2">{opt}</span>
                                {hasAnswered && isCorrect && (
                                  <CheckCircle className="w-4 h-4 text-white" />
                                )}
                                {hasAnswered &&
                                  !isCorrect &&
                                  myAnswer === idx && (
                                    <XCircle className="w-4 h-4 text-zinc-400" />
                                  )}
                              </div>
                            </button>
                          );
                        },
                      )}
                    </div>
                  ) : null}
                </div>
              )}

              <div
                className="absolute top-0 bottom-0 left-0 w-1/4 z-[200] cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  handleStoryPrev();
                }}
              />
              <div
                className="absolute top-0 bottom-0 right-0 w-1/4 z-[200] cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  handleStoryNext();
                }}
              />

              <div className="absolute bottom-4 left-0 right-0 w-full px-4 z-[205] flex justify-between items-center gap-3">
                {stories[activeStoryIndex].user._id ===
                  (currentUser?._id || "") ||
                stories[activeStoryIndex].user._id ===
                  (currentUser?._id || "") ? (
                  <div
                    className="bg-black/40 px-4 py-2.5 text-sm text-white border border-white/20 w-full flex justify-between items-center cursor-pointer transition-colors"
                    onClick={() => {
                      const storyId =
                        stories[activeStoryIndex].id ||
                        stories[activeStoryIndex]._id;
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
                        <div
                          key={i}
                          className="w-6 h-6 rounded-none bg-white/20 border border-white/40 overflow-hidden flex items-center justify-center text-[12px] font-bold"
                        >
                          {v.avatar_url ? (
                            <img
                              src={v.avatar_url}
                              className="w-full h-full object-cover"
                            />
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
                        placeholder=""
                        className="w-full bg-black/30 border border-white/30 px-4 py-2.5 pr-12 text-sm text-white placeholder-white/70 outline-none focus:bg-black/50 focus:border-white/50 "
                        value={replyMessage}
                        onChange={(e) => setReplyMessage(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter")
                            submitReplyStory(
                              stories[activeStoryIndex].id ||
                                stories[activeStoryIndex]._id,
                            );
                        }}
                      />
                      {replyMessage.trim() && (
                        <button
                          onClick={() =>
                            submitReplyStory(
                              stories[activeStoryIndex].id ||
                                stories[activeStoryIndex]._id,
                            )
                          }
                          disabled={isReplying}
                          className="absolute right-2 p-1.5 text-white transition-colors"
                        >
                          <Send className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    <button
                      onClick={() =>
                        reactToStory(
                          stories[activeStoryIndex].id ||
                            stories[activeStoryIndex]._id,
                        )
                      }
                      className="text-white active:scale-95 transition-transform bg-white/10 p-2.5 "
                    >
                      <Heart className="w-5 h-5" />
                    </button>
                  </>
                )}
              </div>

              {showViewerList &&
                (stories[activeStoryIndex].user._id ===
                  (currentUser?._id || "") ||
                  stories[activeStoryIndex].user._id ===
                    (currentUser?._id || "")) && (
                  <div className="absolute bottom-20 left-4 right-4 z-[210] bg-black/80 border border-white/20 p-4 animate-in slide-in-from-bottom-4 max-h-64 overflow-y-auto">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-white text-xs font-bold tracking-widest">
                        Người đã xem
                      </span>
                      <button
                        onClick={() => setShowViewerList(false)}
                        className="text-white/50 "
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    {isFetchingViewers ? (
                      <div className="text-white/50 text-xs text-center py-4">
                        Đang tải
                      </div>
                    ) : storyViewers.length === 0 ? (
                      <div className="text-white/50 text-xs text-center py-4">
                        Chưa có ai xem tin này.
                      </div>
                    ) : (
                      storyViewers.map((v: any, i: number) => (
                        <div
                          key={i}
                          className="flex items-center gap-3 py-2 border-b border-white/10 last:border-0"
                        >
                          <div className="w-8 h-8 bg-white/20 border border-white/30 flex items-center justify-center text-sm font-bold text-white overflow-hidden">
                            {v.avatar_url ? (
                              <img
                                src={v.avatar_url}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              v.full_name?.[0]?.toUpperCase() || "?"
                            )}
                          </div>
                          <div>
                            <p className="text-white text-xs font-bold">
                              {v.full_name || "Ẩn danh"}
                            </p>
                            <p className="text-white/50 text-[12px]">
                              {new Date(v.viewed_at).toLocaleTimeString(
                                "vi-VN",
                                { hour: "2-digit", minute: "2-digit" },
                              )}
                            </p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
            </div>
          </div>
        )}

      <Modal
        isOpen={!!translationModal}
        onClose={() => setTranslationModal(null)}
        className="max-w-lg"
      >
        <ModalHeader>
          <ModalTitle>Bản dịch tự động</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap font-medium">
            {translationModal?.text}
          </p>
        </ModalContent>
        <ModalFooter className="flex justify-end">
          <button
            onClick={() => setTranslationModal(null)}
            className="h-12 px-8 text-[10px] font-bold uppercase tracking-widest text-zinc-400 hover:text-black transition-colors"
          >
            Đóng
          </button>
        </ModalFooter>
      </Modal>
      <Modal
        isOpen={!!deleteStoryConfirm}
        onClose={() => !isProcessing && setDeleteStoryConfirm(null)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle>Xác nhận xóa tin</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-sm font-bold text-zinc-400 uppercase tracking-widest leading-relaxed">
            Bạn có chắc chắn muốn xóa tin này không? Hành động này không thể hoàn tác.
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-4">
          <button
            onClick={() => setDeleteStoryConfirm(null)}
            disabled={isProcessing}
            className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-all disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={deleteStory}
            disabled={isProcessing}
            className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-all disabled:opacity-50 flex items-center justify-center"
          >
            {isProcessing ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xác nhận xóa"}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!deletePostConfirm}
        onClose={() => !isProcessing && setDeletePostConfirm(null)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle>Xác nhận xóa bài viết</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-sm font-bold text-zinc-400 uppercase tracking-widest leading-relaxed">
            Bạn có chắc chắn muốn xóa bài viết này không? Nội dung sẽ bị gỡ bỏ vĩnh viễn khỏi bảng tin.
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-4">
          <button
            onClick={() => setDeletePostConfirm(null)}
            disabled={isProcessing}
            className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-all disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={deletePost}
            disabled={isProcessing}
            className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-all disabled:opacity-50 flex items-center justify-center"
          >
            {isProcessing ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xác nhận xóa"}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={!!reportModal}
        onClose={() => !isProcessing && setReportModal(null)}
        className="max-w-xl"
      >
        <ModalHeader>
          <ModalTitle>Báo cáo bài viết</ModalTitle>
        </ModalHeader>
        <ModalContent className="space-y-6">
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest leading-relaxed">
            Vui lòng cung cấp lý do báo cáo để đội ngũ quản trị viên DocLib xem xét và xử lý kịp thời.
          </p>
          <div className="space-y-3">
            <label className="text-[9px] font-bold text-black uppercase tracking-widest">Lý do báo cáo</label>
            <textarea
              value={reportModal?.reason || ""}
              onChange={(e) => setReportModal(prev => prev ? { ...prev, reason: e.target.value } : null)}
              placeholder=""
              autoFocus
              className="w-full min-h-[120px] p-6 bg-white border border-zinc-100 text-sm font-medium focus:border-black outline-none rounded-sm resize-none"
            />
          </div>
        </ModalContent>
        <ModalFooter className="flex gap-4">
          <button
            onClick={() => setReportModal(null)}
            disabled={isProcessing}
            className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-all disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={reportPost}
            disabled={isProcessing || !reportModal?.reason.trim()}
            className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-all disabled:opacity-50 flex items-center justify-center"
          >
            {isProcessing ? <Loader2 className="w-5 h-5 animate-spin" /> : "Gửi báo cáo"}
          </button>
        </ModalFooter>
      </Modal>
    </>
  );
}
