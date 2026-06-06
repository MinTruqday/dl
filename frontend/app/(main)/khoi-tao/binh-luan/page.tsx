"use client";

import { useEffect, useState } from "react";
import { getMyDocumentsAPI } from "@/services/document.service";
import { getCommentsByItemAPI, createCommentAPI, deleteCommentAPI } from "@/services/comment.service";
import { useToast } from "@/contexts/Toast";
import { Loader2, MessageSquare, Trash2 } from "lucide-react";

export default function CommentsPage() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [loadingDocs, setLoadingDocs] = useState(true);

  const [comments, setComments] = useState<any[]>([]);
  const [loadingComments, setLoadingComments] = useState(false);
  const [replyContent, setReplyContent] = useState("");
  const [replyingTo, setReplyingTo] = useState<string | null>(null);

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
        parent_id: replyingTo
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
    return <div className="flex justify-center py-24"><Loader2 className="w-8 h-8 animate-spin text-zinc-400" /></div>;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="bg-white border border-zinc-200 p-6 rounded-2xl shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: '150ms', animationFillMode: 'both' }}>
        <div className="space-y-1">
          <h2 className="text-xl font-medium text-black flex items-center gap-2"><MessageSquare className="w-5 h-5" /> Quản lý bình luận</h2>
          <p className="text-sm font-medium text-zinc-500">Theo dõi và phản hồi độc giả</p>
        </div>
        <select 
          value={selectedDocumentId} 
          onChange={e => setSelectedDocumentId(e.target.value)}
          className="w-full sm:w-64 h-10 border border-zinc-200 px-3 text-sm outline-none bg-white rounded-xl focus:border-black"
        >
          {documents.map(d => (
            <option key={d.id || d._id} value={d.id || d._id}>{d.title}</option>
          ))}
        </select>
      </div>

      {selectedDocumentId ? (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: '150ms', animationFillMode: 'both' }}>
          {loadingComments ? (
            <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-zinc-300" /></div>
          ) : comments.length === 0 ? (
            <div className="text-center py-20 border border-zinc-200 bg-white rounded-2xl shadow-sm">
               <MessageSquare className="w-12 h-12 text-zinc-200 mx-auto mb-4" />
               <p className="text-zinc-500 font-medium">Chưa có bình luận nào cho tác phẩm này.</p>
            </div>
          ) : (
            <div className="space-y-4">
               {comments.map((comment: any) => (
                 <div key={comment.id || comment._id} className="bg-white border border-zinc-200 p-6 rounded-2xl shadow-sm space-y-4">
                   <div className="flex justify-between items-start">
                     <div>
                       <span className="font-semibold text-sm text-black">{comment.author?.username || "Ẩn danh"}</span>
                       <span className="text-xs text-zinc-400 ml-2">{new Date(comment.created_at).toLocaleDateString("vi-VN")}</span>
                     </div>
                     <button onClick={() => handleDeleteComment(comment.id || comment._id)} className="text-zinc-400 hover:text-red-500 transition-colors p-1">
                       <Trash2 className="w-4 h-4" />
                     </button>
                   </div>
                   <p className="text-sm text-zinc-700 leading-relaxed">{comment.content}</p>
                   
                   {replyingTo === (comment.id || comment._id) ? (
                     <div className="flex gap-2 mt-4 items-center">
                       <input
                         type="text"
                         value={replyContent}
                         onChange={(e) => setReplyContent(e.target.value)}
                         placeholder="Nhập phản hồi..."
                         className="flex-1 h-10 border border-zinc-200 px-3 text-sm font-medium rounded-xl outline-none focus:border-black"
                         autoFocus
                       />
                       <button onClick={() => setReplyingTo(null)} className="h-10 px-4 border border-zinc-200 text-sm font-medium rounded-xl hover:bg-zinc-50 transition-colors">Hủy</button>
                       <button onClick={handleReplyComment} className="h-10 px-6 bg-black text-white text-sm font-medium rounded-xl hover:bg-zinc-800 transition-colors">Gửi</button>
                     </div>
                   ) : (
                     <button onClick={() => setReplyingTo(comment.id || comment._id)} className="text-xs font-semibold text-zinc-500 hover:text-black transition-colors mt-2">Phản hồi</button>
                   )}
                 </div>
               ))}
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white border border-zinc-200 p-16 rounded-2xl flex flex-col items-center justify-center gap-4 text-center">
          <MessageSquare className="w-8 h-8 text-zinc-300" />
          <p className="text-sm font-medium text-zinc-500">Vui lòng chọn một tác phẩm để quản lý bình luận</p>
        </div>
      )}
    </div>
  );
}
