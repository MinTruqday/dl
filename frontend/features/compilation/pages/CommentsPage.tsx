"use client";

import { useCallback, useEffect, useState } from "react";
import { getMyDocumentsAPI } from "@/features/content/services/document.service";
import {
  getCommentsByItemAPI,
  createCommentAPI,
  deleteCommentAPI,
} from "@/features/content/services/collaboration.service";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Loader2,
  MessageSquare,
  Trash2,
  BookOpen,
  Send,
  Reply,
  CornerDownRight,
} from "lucide-react";
import PageLoader from "@/shared/components/common/PageLoader";
import PageHeader from "@/shared/components/common/PageHeader";

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

  const fetchInitData = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const docsData = await getMyDocumentsAPI();
      const list = docsData.data || docsData || [];
      setDocuments(list);
      if (list.length > 0) setSelectedDocumentId(list[0]._id || list[0].id);
    } catch {
      showToast("Lỗi trích xuất bộ sưu tập tài liệu", "error");
    } finally {
      setLoadingDocs(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [showToast]);

  useEffect(() => {
    fetchInitData();
  }, [fetchInitData]);

  const fetchComments = useCallback(async () => {
    setLoadingComments(true);
    try {
      const data = await getCommentsByItemAPI(selectedDocumentId);
      setComments(data.data || data || []);
    } catch {
      setComments([]);
    } finally {
      setLoadingComments(false);
    }
  }, [selectedDocumentId]);

  useEffect(() => {
    if (selectedDocumentId) {
      fetchComments();
      setReplyingTo(null);
      setReplyContent("");
    } else setComments([]);
  }, [fetchComments, selectedDocumentId]);

  const handleReplyComment = async () => {
    if (!replyContent.trim() || !selectedDocumentId) return;
    try {
      await createCommentAPI({
        item_id: selectedDocumentId,
        item_type: "document",
        content: replyContent.trim(),
        parent_id: replyingTo,
      });
      showToast("Lưu trữ dữ liệu phản hồi hoàn tất", "success");
      setReplyContent("");
      setReplyingTo(null);
      fetchComments();
    } catch (e: any) {
      showToast(e.message || "Lỗi lưu trữ dữ liệu phản hồi", "error");
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    try {
      await deleteCommentAPI(commentId);
      showToast("Hủy bỏ bản ghi dữ liệu phản hồi hoàn tất", "success");
      fetchComments();
    } catch (e: any) {
      showToast(e.message || "Lỗi hủy bỏ bản ghi dữ liệu phản hồi", "error");
    }
  };

  if (loadingDocs) return <PageLoader />;

  return (
    <div className="app-page gap-6">
      <PageHeader title="Bình luận" />
      <div
        className={`bg-[var(--surface-quiet)] md:bg-transparent rounded-[var(--radius-panel)] md:rounded-none p-6 md:px-0 md:pt-6 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-6 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`}
        style={{ transitionDelay: "100ms" }}
      >
        <div className="bg-white p-6 rounded-[var(--radius-panel)] flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white rounded-[var(--radius-control)] flex items-center justify-center shrink-0">
              <BookOpen className="w-6 h-6 text-[var(--ink)]" />
            </div>
            <div>
              <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
                Chọn tác phẩm
              </p>
              <p className="text-[13px] text-[var(--ink-muted)]">
                Lọc bình luận theo từng tài liệu
              </p>
            </div>
          </div>
          <div className="relative w-full sm:w-[320px]">
            <BookOpen className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--ink-muted)]" />
            <select
              value={selectedDocumentId}
              onChange={(e) => setSelectedDocumentId(e.target.value)}
              className="w-full h-[48px] pl-12 pr-4 text-[15px] font-medium text-[var(--ink)] focus:outline-none focus:border-[var(--brand)] bg-white rounded-[var(--radius-control)] appearance-none transition-colors cursor-pointer"
            >
              {documents.length === 0 && (
                <option value="" disabled>
                  Chưa có tác phẩm
                </option>
              )}
              {documents.map((d) => (
                <option key={d.id || d._id} value={d.id || d._id}>
                  {d.title || "Chưa có tiêu đề"}
                </option>
              ))}
            </select>
          </div>
        </div>

        {selectedDocumentId ? (
          <div className="flex-1 min-h-0 flex flex-col bg-white border border-[var(--border)] rounded-[var(--radius-panel)] overflow-hidden">
            <div className="p-6 flex justify-between items-center bg-white border-b border-[var(--border)] shrink-0">
              <h2 className="text-[20px] font-semibold text-[var(--ink)] flex items-center gap-2">
                <MessageSquare className="w-5 h-5" /> Danh sách bình luận
              </h2>
              <span className="px-4 py-1.5 bg-white text-[var(--brand)] font-medium text-[13px] font-medium rounded-full">
                {comments.length} phản hồi
              </span>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
              {loadingComments ? (
                <div className="h-full flex flex-col items-center justify-center">
                  <Loader2 className="w-8 h-8 animate-spin text-[var(--brand)] mb-4" />
                  <p className="text-[13px] font-medium text-[var(--ink-muted)]">
                    Đang tải bình luận
                  </p>
                </div>
              ) : comments.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-12">
                  <div className="w-16 h-16 bg-[var(--surface-quiet)] flex items-center justify-center rounded-[var(--radius-panel)] mb-4">
                    <MessageSquare className="w-8 h-8 text-[var(--border-strong)]" />
                  </div>
                  <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4 mb-2">
                    Chưa có bình luận
                  </p>
                  <p className="text-[15px] text-[var(--ink-muted)] max-w-sm">
                    Tác phẩm này hiện chưa nhận được phản hồi nào từ độc giả.
                  </p>
                </div>
              ) : (
                <div className="space-y-6 pb-6">
                  {comments.map((comment: any) => (
                    <div
                      key={comment.id || comment._id}
                      className="bg-[var(--surface-quiet)] border-[var(--border)] p-6 rounded-[var(--radius-panel)] transition-all hover: group relative"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-[var(--surface-quiet)] rounded-full flex items-center justify-center overflow-hidden shrink-0">
                            {comment.author?.avatar_url ? (
                              <img
                                src={comment.author.avatar_url}
                                alt="Avatar"
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <span className="text-[13px] font-medium text-[var(--ink-muted)] uppercase">
                                {comment.author?.username?.charAt(0) || "U"}
                              </span>
                            )}
                          </div>
                          <div className="flex flex-col">
                            <span className="font-semibold text-[15px] text-[var(--ink)]">
                              {comment.author?.username || "Ẩn danh"}
                            </span>
                            <span className="text-[13px] text-[var(--ink-muted)]">
                              {new Date(comment.created_at).toLocaleString(
                                "vi-VN",
                              )}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() =>
                            handleDeleteComment(comment.id || comment._id)
                          }
                          className="w-10 h-10 flex items-center justify-center text-[var(--ink-muted)] hover:text-[var(--danger)] hover:bg-[#FFEBEB] rounded-full transition-colors opacity-0 group-hover:opacity-100"
                          title="Xóa bình luận"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                      <div className="ml-14">
                        <p className="text-[15px] text-[var(--ink)] leading-relaxed mb-4 bg-[var(--surface-quiet)] p-4 rounded-[var(--radius-panel)]">
                          {comment.content}
                        </p>
                        {replyingTo === (comment.id || comment._id) ? (
                          <div className="flex flex-col sm:flex-row gap-3 mt-4 items-end sm:items-center bg-[var(--surface-quiet)] p-4 rounded-[var(--radius-panel)] border-[var(--border)]">
                            <div className="relative w-full">
                              <CornerDownRight className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--ink-muted)]" />
                              <input
                                type="text"
                                value={replyContent}
                                onChange={(e) =>
                                  setReplyContent(e.target.value)
                                }
                                placeholder=""
                                className="w-full h-[48px] pl-12 pr-4 bg-[var(--surface-quiet)] focus:bg-white text-[15px] text-[var(--ink)] rounded-[var(--radius-control)] outline-none focus:border-[var(--brand)] transition-colors"
                                autoFocus
                                onKeyDown={(e) => {
                                  if (e.key === "Enter") handleReplyComment();
                                  if (e.key === "Escape") setReplyingTo(null);
                                }}
                              />
                            </div>
                            <div className="flex gap-2 w-full sm:w-auto shrink-0">
                              <button
                                onClick={() => setReplyingTo(null)}
                                className="flex-1 sm:flex-none h-[48px] px-6 text-[15px] font-medium text-[var(--ink)] rounded-full hover:bg-[var(--surface-quiet)] transition-colors bg-white"
                              >
                                Hủy
                              </button>
                              <button
                                onClick={handleReplyComment}
                                disabled={!replyContent.trim()}
                                className="flex-1 sm:flex-none h-[48px] px-8 bg-[var(--brand)] text-white text-[15px] font-medium rounded-full hover:bg-[var(--brand-hover)] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                              >
                                Gửi <Send className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button
                            onClick={() =>
                              setReplyingTo(comment.id || comment._id)
                            }
                            className="text-[13px] font-medium text-[var(--ink-muted)] hover:text-[var(--ink)] hover:bg-[var(--surface-quiet)] transition-colors flex items-center gap-2 px-4 py-2 rounded-full"
                          >
                            <Reply className="w-4 h-4" /> Phản hồi
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
          <div className="flex-1 bg-white rounded-[var(--radius-panel)] p-12 flex flex-col items-center justify-center gap-4 text-center">
            <div className="w-16 h-16 bg-[var(--surface-quiet)] border-[var(--border)] flex items-center justify-center rounded-[var(--radius-panel)] mb-2">
              <MessageSquare className="w-8 h-8 text-[var(--border-strong)]" />
            </div>
            <p className="text-[15px] text-[var(--ink-muted)] max-w-sm">
              Vui lòng chọn một tác phẩm từ danh sách để xem và quản lý bình
              luận
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
