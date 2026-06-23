"use client";

import { useEffect, useState } from "react";
import { getMyDocumentsAPI } from "@/features/content/services/document_metadata.service";
import {
  getCommentsByItemAPI,
  createCommentAPI,
  deleteCommentAPI,
} from "@/features/messaging/services/inline_comment.service";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2, MessageSquare, Trash2, BookOpen, Send, Reply, CornerDownRight } from "lucide-react";

export default function CommentsPage() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [loadingDocs, setLoadingDocs] = useState(true);

  const [comments, setComments] = useState<any[]>([]);
  const [loadingComments, setLoadingComments] = useState(false);
  const [replyContent, setReplyContent] = useState("");
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    fetchInitData();
  }, []);

  const fetchInitData = async () => {
    setLoadingDocs(true);
    try {
      const docsData = await getMyDocumentsAPI();
      const list = docsData.data || docsData || [];
      setDocuments(list);
      if (list.length > 0) {
        setSelectedDocumentId(list[0]._id || list[0].id);
      }
    } catch (e: any) {
      showToast("Lỗi tải danh sách tác phẩm", "error");
    } finally {
      setLoadingDocs(false);
      requestAnimationFrame(() => setVisible(true));
    }
  };

  useEffect(() => {
    if (selectedDocumentId) {
      fetchComments();
      setReplyingTo(null);
      setReplyContent("");
    } else {
      setComments([]);
    }
  }, [selectedDocumentId]);

  const fetchComments = async () => {
    setLoadingComments(true);
    try {
      const data = await getCommentsByItemAPI(selectedDocumentId);
      setComments(data.data || data || []);
    } catch (err: any) {
      setComments([]);
    } finally {
      setLoadingComments(false);
    }
  };

  const handleReplyComment = async () => {
    if (!replyContent.trim() || !selectedDocumentId) return;
    try {
      await createCommentAPI({
        item_id: selectedDocumentId,
        item_type: "document",
        content: replyContent.trim(),
        parent_id: replyingTo,
      });
      showToast("Đã gửi phản hồi", "success");
      setReplyContent("");
      setReplyingTo(null);
      fetchComments();
    } catch (e: any) {
      showToast(e.message || "Gửi phản hồi thất bại", "error");
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    try {
      await deleteCommentAPI(commentId);
      showToast("Đã xóa bình luận", "success");
      fetchComments();
    } catch (e: any) {
      showToast(e.message || "Xóa bình luận thất bại", "error");
    }
  };

  if (loadingDocs) {
    return (
      <div className="h-full min-h-[400px] flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400 mb-4" />
        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Đang tải cấu hình...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-zinc-100 pb-4 mb-6 shrink-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
          Bình luận & Phản hồi
        </h1>
        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
          Theo dõi và tương tác với độc giả
        </p>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-6 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0, transitionDelay: "100ms" }}>
        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 rounded-3xl shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0 transition-all duration-300 hover:border-zinc-200">
          <div className="space-y-1.5 flex items-center gap-3">
            <div className="w-10 h-10 bg-zinc-50 border border-zinc-100 rounded-2xl flex items-center justify-center shrink-0">
              <BookOpen className="w-5 h-5 text-black" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">
                Chọn tác phẩm
              </h2>
              <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                Lọc bình luận theo từng tài liệu
              </p>
            </div>
          </div>
          <div className="relative w-full sm:w-72">
            <BookOpen className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <select
              value={selectedDocumentId}
              onChange={(e) => setSelectedDocumentId(e.target.value)}
              className="w-full h-11 pl-10 pr-4 border border-zinc-200 text-sm font-bold text-zinc-900 focus:outline-none focus:border-black bg-zinc-50 focus:bg-white rounded-2xl appearance-none transition-all duration-200 shadow-sm cursor-pointer"
            >
              {documents.length === 0 && <option value="" disabled>Chưa có tác phẩm</option>}
              {documents.map((d) => (
                <option key={d.id || d._id} value={d.id || d._id}>
                  {d.title || "Chưa có tiêu đề"}
                </option>
              ))}
            </select>
          </div>
        </div>

        {selectedDocumentId ? (
          <div className="flex-1 min-h-0 flex flex-col bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm overflow-hidden">
            <div className="border-b border-zinc-100 p-5 flex justify-between items-center bg-zinc-50/50 shrink-0">
              <h2 className="text-[10px] font-bold text-zinc-900 uppercase tracking-widest flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-black" />
                Danh sách bình luận
              </h2>
              <span className="px-3 py-1 bg-white border border-zinc-100 text-zinc-900 text-[9px] font-bold uppercase tracking-widest rounded-xl shadow-sm">
                {comments.length} phản hồi
              </span>
            </div>
            
            <div className="flex-1 overflow-y-auto custom-scrollbar p-5">
              {loadingComments ? (
                <div className="h-full flex flex-col items-center justify-center">
                  <Loader2 className="w-8 h-8 animate-spin text-zinc-300 mb-4" />
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Đang tải bình luận...</p>
                </div>
              ) : comments.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-12">
                  <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
                    <MessageSquare className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
                  </div>
                  <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-1">Chưa có bình luận</h3>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 max-w-sm">
                    Tác phẩm này hiện chưa nhận được phản hồi nào từ độc giả.
                  </p>
                </div>
              ) : (
                <div className="space-y-4 pb-6">
                  {comments.map((comment: any) => (
                    <div
                      key={comment.id || comment._id}
                      className="bg-white border border-zinc-100 p-5 rounded-2xl shadow-sm transition-all duration-300 hover:border-zinc-300 hover:shadow-md group relative overflow-hidden"
                    >
                      <div className="absolute top-0 left-0 w-1 h-full bg-zinc-200 group-hover:bg-black transition-colors duration-300"></div>
                      
                      <div className="flex justify-between items-start mb-3 ml-2">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-zinc-100 border border-zinc-200 rounded-full flex items-center justify-center overflow-hidden shrink-0 shadow-sm">
                            {comment.author?.avatar_url ? (
                              <img src={comment.author.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                            ) : (
                              <span className="text-[10px] font-bold text-zinc-500 uppercase">
                                {comment.author?.username?.charAt(0) || "U"}
                              </span>
                            )}
                          </div>
                          <div className="flex flex-col">
                            <span className="font-bold text-xs text-zinc-900">
                              {comment.author?.username || "Ẩn danh"}
                            </span>
                            <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-400">
                              {new Date(comment.created_at).toLocaleString("vi-VN")}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteComment(comment.id || comment._id)}
                          className="w-8 h-8 flex items-center justify-center text-zinc-400 hover:text-red-500 bg-white border border-transparent hover:border-red-100 hover:bg-red-50 rounded-xl transition-all opacity-0 group-hover:opacity-100 shadow-sm"
                          title="Xóa bình luận"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      
                      <div className="ml-11">
                        <p className="text-sm text-zinc-700 leading-relaxed font-medium mb-4 bg-zinc-50/50 p-4 rounded-2xl border border-zinc-100/50">
                          {comment.content}
                        </p>

                        {replyingTo === (comment.id || comment._id) ? (
                          <div className="flex flex-col sm:flex-row gap-3 mt-4 items-end sm:items-center bg-zinc-50 p-3 rounded-2xl border border-zinc-100 shadow-inner">
                            <div className="relative w-full">
                              <CornerDownRight className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                              <input
                                type="text"
                                value={replyContent}
                                onChange={(e) => setReplyContent(e.target.value)}
                                placeholder="Nhập phản hồi của bạn..."
                                className="w-full h-11 pl-10 pr-4 border border-zinc-200 bg-white text-sm font-bold text-zinc-900 rounded-xl outline-none focus:border-black shadow-sm transition-all"
                                autoFocus
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') handleReplyComment();
                                  if (e.key === 'Escape') setReplyingTo(null);
                                }}
                              />
                            </div>
                            <div className="flex gap-2 w-full sm:w-auto shrink-0">
                              <button
                                onClick={() => setReplyingTo(null)}
                                className="flex-1 sm:flex-none h-11 px-4 border border-zinc-200 text-[10px] font-bold uppercase tracking-widest text-zinc-600 rounded-xl hover:bg-zinc-100 transition-colors bg-white shadow-sm"
                              >
                                Hủy
                              </button>
                              <button
                                onClick={handleReplyComment}
                                disabled={!replyContent.trim()}
                                className="flex-1 sm:flex-none h-11 px-6 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-xl hover:bg-zinc-800 transition-colors disabled:opacity-50 shadow-md flex items-center justify-center gap-2"
                              >
                                Gửi <Send className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button
                            onClick={() => setReplyingTo(comment.id || comment._id)}
                            className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 hover:text-black transition-colors flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-zinc-100"
                          >
                            <Reply className="w-3.5 h-3.5" /> Phản hồi
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl p-12 flex flex-col items-center justify-center gap-4 text-center shadow-sm">
            <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-2">
              <MessageSquare className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
            </div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 max-w-xs">
              Vui lòng chọn một tác phẩm từ danh sách để xem và quản lý bình luận
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
