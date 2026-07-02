"use client";

import { useEffect, useState } from "react";
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
      if (list.length > 0) setSelectedDocumentId(list[0]._id || list[0].id);
    } catch {
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
    } else setComments([]);
  }, [selectedDocumentId]);

  const fetchComments = async () => {
    setLoadingComments(true);
    try {
      const data = await getCommentsByItemAPI(selectedDocumentId);
      setComments(data.data || data || []);
    } catch {
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

  if (loadingDocs) return <PageLoader />;

  return (
    <div className="flex flex-col h-full font-sans">
      <div
        className={`flex-1 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-6 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`}
        style={{ transitionDelay: "100ms" }}
      >
        <div className="bg-[#F5F5F7] p-6 rounded-[18px] flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white rounded-[10px] flex items-center justify-center shrink-0">
              <BookOpen className="w-6 h-6 text-[#1D1D1F]" />
            </div>
            <div>
              <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
                Chọn tác phẩm
              </p>
              <p className="text-[13px] text-[#6E6E73]">
                Lọc bình luận theo từng tài liệu
              </p>
            </div>
          </div>
          <div className="relative w-full sm:w-[320px]">
            <BookOpen className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6E6E73]" />
            <select
              value={selectedDocumentId}
              onChange={(e) => setSelectedDocumentId(e.target.value)}
              className="w-full h-[48px] pl-12 pr-4 text-[15px] font-medium text-[#1D1D1F] focus:outline-none focus:border-[#0071E3] bg-white rounded-[10px] appearance-none transition-colors cursor-pointer"
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
          <div className="flex-1 min-h-0 flex flex-col bg-[#F5F5F7] border-[#E8E8ED] rounded-[18px] overflow-hidden">
            <div className="p-6 flex justify-between items-center bg-[#F5F5F7] shrink-0">
              <h2 className="text-[20px] font-semibold text-[#1D1D1F] flex items-center gap-2">
                <MessageSquare className="w-5 h-5" /> Danh sách bình luận
              </h2>
              <span className="px-4 py-1.5 bg-white text-[#0071E3] font-medium text-[13px] font-medium rounded-full">
                {comments.length} phản hồi
              </span>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
              {loadingComments ? (
                <div className="h-full flex flex-col items-center justify-center">
                  <Loader2 className="w-8 h-8 animate-spin text-[#0071E3] mb-4" />
                  <p className="text-[13px] font-medium text-[#6E6E73]">
                    Đang tải bình luận...
                  </p>
                </div>
              ) : comments.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-12">
                  <div className="w-16 h-16 bg-[#F5F5F7] flex items-center justify-center rounded-[18px] mb-4">
                    <MessageSquare className="w-8 h-8 text-[#C7C7CC]" />
                  </div>
                  <p className="text-[13px] font-medium text-[#6E6E73] mb-4 mb-2">
                    Chưa có bình luận
                  </p>
                  <p className="text-[15px] text-[#6E6E73] max-w-sm">
                    Tác phẩm này hiện chưa nhận được phản hồi nào từ độc giả.
                  </p>
                </div>
              ) : (
                <div className="space-y-6 pb-6">
                  {comments.map((comment: any) => (
                    <div
                      key={comment.id || comment._id}
                      className="bg-[#F5F5F7] border-[#E8E8ED] p-6 rounded-[18px] transition-all hover: group relative"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-[#F5F5F7] rounded-full flex items-center justify-center overflow-hidden shrink-0">
                            {comment.author?.avatar_url ? (
                              <img
                                src={comment.author.avatar_url}
                                alt="Avatar"
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <span className="text-[13px] font-medium text-[#6E6E73] uppercase">
                                {comment.author?.username?.charAt(0) || "U"}
                              </span>
                            )}
                          </div>
                          <div className="flex flex-col">
                            <span className="font-semibold text-[15px] text-[#1D1D1F]">
                              {comment.author?.username || "Ẩn danh"}
                            </span>
                            <span className="text-[13px] text-[#6E6E73]">
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
                          className="w-10 h-10 flex items-center justify-center text-[#6E6E73] hover:text-[#FF3B30] hover:bg-[#FFEBEB] rounded-full transition-colors opacity-0 group-hover:opacity-100"
                          title="Xóa bình luận"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                      <div className="ml-14">
                        <p className="text-[15px] text-[#1D1D1F] leading-relaxed mb-4 bg-[#F5F5F7] p-4 rounded-[18px]">
                          {comment.content}
                        </p>
                        {replyingTo === (comment.id || comment._id) ? (
                          <div className="flex flex-col sm:flex-row gap-3 mt-4 items-end sm:items-center bg-[#F5F5F7] p-4 rounded-[18px] border-[#E8E8ED]">
                            <div className="relative w-full">
                              <CornerDownRight className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6E6E73]" />
                              <input
                                type="text"
                                value={replyContent}
                                onChange={(e) =>
                                  setReplyContent(e.target.value)
                                }
                                placeholder=""
                                className="w-full h-[48px] pl-12 pr-4 bg-[#F5F5F7] focus:bg-white text-[15px] text-[#1D1D1F] rounded-[10px] outline-none focus:border-[#0071E3] transition-colors"
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
                                className="flex-1 sm:flex-none h-[48px] px-6 text-[15px] font-medium text-[#1D1D1F] rounded-full hover:bg-[#F5F5F7] transition-colors bg-white"
                              >
                                Hủy
                              </button>
                              <button
                                onClick={handleReplyComment}
                                disabled={!replyContent.trim()}
                                className="flex-1 sm:flex-none h-[48px] px-8 bg-[#0071E3] text-white text-[15px] font-medium rounded-full hover:bg-[#0077ED] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
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
                            className="text-[13px] font-medium text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors flex items-center gap-2 px-4 py-2 rounded-full"
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
          <div className="flex-1 bg-[#F5F5F7] rounded-[18px] p-12 flex flex-col items-center justify-center gap-4 text-center">
            <div className="w-16 h-16 bg-[#F5F5F7] border-[#E8E8ED] flex items-center justify-center rounded-[18px] mb-2">
              <MessageSquare className="w-8 h-8 text-[#C7C7CC]" />
            </div>
            <p className="text-[15px] text-[#6E6E73] max-w-sm">
              Vui lòng chọn một tác phẩm từ danh sách để xem và quản lý bình
              luận
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
