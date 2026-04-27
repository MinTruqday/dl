"use client";

import { useState, useEffect } from "react";
import { getDiscussionsAPI, createDiscussionAPI, replyDiscussionAPI } from "@/app/lib/api";
import { MessageSquare, User, Send, ChevronDown, ChevronUp, Plus } from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";

interface DiscussionSectionProps {
  documentId: string;
}

export default function DiscussionSection({ documentId }: DiscussionSectionProps) {
  const { user } = useAuth() as any;
  const [discussions, setDiscussions] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState("");

  useEffect(() => {
    loadDiscussions();
  }, [documentId]);

  const loadDiscussions = async () => {
    setLoading(true);
    try {
      const data = await getDiscussionsAPI(documentId);
      setDiscussions(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setSubmitting(true);
    try {
      await createDiscussionAPI(documentId, title, content);
      setTitle("");
      setContent("");
      setShowForm(false);
      loadDiscussions();
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReply = async (discussionId: string) => {
    if (!user || !replyContent.trim()) return;
    try {
      await replyDiscussionAPI(discussionId, replyContent);
      setReplyContent("");
      setReplyingTo(null);
      loadDiscussions();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="mt-16 space-y-12 pb-20">
      <div className="flex items-center justify-between border-b border-zinc-100 pb-4">
        <h2 className="text-lg font-bold text-black tracking-tight flex items-center gap-2">
           <MessageSquare className="w-5 h-5" />
           Thảo luận cộng đồng
        </h2>
        <button 
           onClick={() => setShowForm(!showForm)}
           className="text-[12px] font-bold text-black tracking-widest border border-black px-4 py-2 hover:bg-zinc-50 transition-all flex items-center gap-2"
        >
           {showForm ? "Hủy bỏ" : "Tạo thảo luận mới"}
           {!showForm && <Plus className="w-3 h-3" />}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-zinc-50 border border-border p-8 space-y-6 animate-in slide-in-from-top-4 duration-300">
           <div className="space-y-4">
              <label className="text-[12px] font-bold tracking-widest text-zinc-400">Tiêu đề thảo luận</label>
              <input 
                 type="text" 
                 value={title}
                 onChange={(e) => setTitle(e.target.value)}
                 placeholder="Nhập tiêu đề ngắn gọn"
                 className="w-full bg-white border border-border  p-4 text-sm font-bold focus:border-black focus:outline-none transition-all"
                 required
              />
           </div>
           <div className="space-y-4">
              <label className="text-[12px] font-bold tracking-widest text-zinc-400">Nội dung chi tiết</label>
              <textarea
                 value={content}
                 onChange={(e) => setContent(e.target.value)}
                 placeholder="Mô tả vấn đề bạn muốn trao đổi"
                 className="w-full bg-white border border-border  p-4 text-sm focus:border-black focus:outline-none min-h-[120px] transition-all"
                 required
              />
           </div>
           <button
              type="submit"
              disabled={submitting}
              className="px-8 py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-all flex items-center gap-2"
           >
              {submitting ? "Đang gửi" : "Đăng thảo luận"}
              <Send className="w-3 h-3" />
           </button>
        </form>
      )}

      <div className="space-y-6">
        {loading ? (
          <div className="space-y-6">
            {[1, 2].map((i) => (
              <div key={i} className="h-32 bg-zinc-50 animate-pulse border border-border" />
            ))}
          </div>
        ) : discussions.length > 0 ? (
          discussions.map((d) => (
            <div key={d.id} className="border border-border p-8 space-y-6 hover:border-black transition-colors group">
               <div className="flex justify-between items-start">
                  <div className="space-y-1">
                     <h3 className="text-base font-bold tracking-tight">{d.title}</h3>
                     <div className="flex items-center gap-3">
                        <div className="text-[12px] font-bold tracking-widest text-zinc-400 flex items-center gap-1">
                           <User className="w-3 h-3" />
                           {d.user_name}
                        </div>
                        <span className="w-1 h-1 rounded-none bg-zinc-200" />
                        <div className="text-[12px] font-bold tracking-widest text-zinc-300">
                           {new Date(d.created_at).toLocaleDateString("vi-VN")}
                        </div>
                     </div>
                  </div>
                  <div className="bg-zinc-100 px-3 py-1 text-[12px] font-bold tracking-widest text-zinc-500">
                     {d.replies_count} phản hồi
                  </div>
               </div>
               
               <p className="text-sm text-zinc-600 leading-relaxed border-l-2 border-zinc-100 pl-4">
                  {d.content}
               </p>

               <div className="pt-4 border-t border-zinc-50 flex items-center gap-4">
                  <button 
                     onClick={() => setReplyingTo(replyingTo === d.id ? null : d.id)}
                     className="text-[12px] font-bold tracking-widest text-black hover:underline"
                  >
                     {replyingTo === d.id ? "Hủy bỏ" : "Trả lời thảo luận"}
                  </button>
               </div>

               {replyingTo === d.id && (
                  <div className="mt-4 flex gap-2">
                     <input 
                        type="text" 
                        value={replyContent}
                        onChange={(e) => setReplyContent(e.target.value)}
                        placeholder="Viết câu trả lời của bạn"
                        className="flex-1 bg-zinc-50 border border-border px-4 py-2 text-sm focus:border-black focus:outline-none"
                     />
                     <button 
                        onClick={() => handleReply(d.id)}
                        className="bg-black text-white px-6 py-2 text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-all"
                     >
                        Gửi
                     </button>
                  </div>
               )}
            </div>
          ))
        ) : (
          <div className="py-16 text-center border border-dashed border-border bg-zinc-50/50">
             <p className="text-[12px] font-bold tracking-widest text-zinc-300">Chưa có chủ đề thảo luận nào cho tài liệu này.</p>
          </div>
        )}
      </div>
    </div>
  );
}
