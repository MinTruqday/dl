"use client";
import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import {
  User,
  ShieldCheck,
  UserPlus,
  Users,
  Link as LinkIcon,
  BookOpen,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { getUserProfileAPI } from "@/services/profile.service";
import { getDocumentsAPI } from "@/services/document.service";
import { API_URL } from "@/services/authentication.service";

export default function UserProfilePage() {
  const params = useParams();
  const slug = params?.slug as string;
  const router = useRouter();
  const [author, setAuthor] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (slug) fetchAuthorProfile();
  }, [slug]);

  useEffect(() => {
    if (!loading && author) requestAnimationFrame(() => setVisible(true));
  }, [loading, author]);

  const fetchAuthorProfile = async () => {
    try {
      const data = await getUserProfileAPI(slug);
      const profileData = data.data || data;
      setAuthor(profileData);

      const docData = await getDocumentsAPI(
        undefined,
        "latest",
        undefined,
        undefined,
        slug,
      );
      setDocuments(docData.data || docData || []);
    } catch (err: any) {
      console.error("Error loading member details:", err);
      setError(err.message || "Không thể tải thông tin thành viên");
    } finally {
      setLoading(false);
    }
  };



  if (loading) {
    return (
      <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-16 pb-20 flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-black mb-4" />
        <p className="text-sm font-semibold text-zinc-500">Đang tải hồ sơ...</p>
      </div>
    );
  }

  if (error || !author) {
    return (
      <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-16 pb-20 flex flex-col items-center justify-center min-h-[60vh] animate-in fade-in">
        <AlertCircle className="w-12 h-12 text-zinc-300 mb-4" />
        <p className="text-base font-semibold text-black mb-2">Thành viên không tồn tại</p>
        <p className="text-sm font-medium text-zinc-500">Người dùng này có thể đã bị khoá hoặc đổi tên.</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-10 pb-24 font-sans text-black selection:bg-black selection:text-white">
      <div 
        className="flex flex-col md:flex-row gap-10 md:gap-16 items-start border-b border-zinc-200 pb-12 mb-12"
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(12px)",
          transition: "all 0.5s cubic-bezier(0.16, 1, 0.3, 1)"
        }}
      >
        <div className="w-32 h-32 md:w-48 md:h-48 border border-zinc-200 bg-zinc-50 shrink-0 p-1.5 group">
          <div className="w-full h-full overflow-hidden bg-zinc-100">
            {author.avatar_url ? (
              <img 
                src={author.avatar_url} 
                alt="Avatar" 
                className="w-full h-full object-cover grayscale mix-blend-multiply group-  " 
              />
            ) : (
              <User className="w-full h-full p-8 text-zinc-300" />
            )}
          </div>
        </div>
        
        <div className="flex-1 space-y-6 pt-2">
          <div className="space-y-3">
            <div className="inline-flex items-center px-2 py-1 bg-zinc-100 border border-zinc-200 text-zinc-500 text-[10px] font-bold uppercase tracking-widest">
              {author.role === "AUTHOR" ? "Hồ sơ tác giả" : author.role === "ADMIN" ? "Quản trị viên" : "Hồ sơ thành viên"}
            </div>
            <div className="flex items-center gap-3">
              <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-black">
                {author.full_name || author.username || "Ẩn danh"}
              </h1>
              {author.role === "AUTHOR" && (
                <ShieldCheck className="w-8 h-8 text-black" title="Tác giả được xác thực" />
              )}
            </div>
            <p className="text-zinc-500 font-medium text-lg">@{author.slug || author.username}</p>
          </div>
          
          <div className="flex flex-wrap items-center gap-6 md:gap-10 text-sm font-semibold text-zinc-600">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-zinc-400"/> 
              <span className="text-black">{documents.length}</span> tài liệu
            </div>
          </div>
        </div>
      </div>

      {/* Content Section */}
      <div 
        className="grid grid-cols-1 lg:grid-cols-12 gap-16"
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(12px)",
          transition: "all 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.1s"
        }}
      >
        <aside className="lg:col-span-3 space-y-8">
          <div className="space-y-4 sticky top-24">
            <h3 className="text-sm font-semibold text-black border-b border-zinc-200 pb-3 flex items-center gap-2">
              <User className="w-4 h-4" />
              Giới thiệu
            </h3>
            <div className="text-sm text-zinc-600 leading-relaxed font-medium">
              {author.bio ? (
                <div dangerouslySetInnerHTML={{ __html: author.bio.replace(/\n/g, "<br/>") }} />
              ) : (
                <span className="text-zinc-400 italic">Thành viên chưa cập nhật thông tin giới thiệu.</span>
              )}
            </div>
          </div>
        </aside>

        <div className="lg:col-span-9 space-y-16">
          


          <div>
            <div className="flex items-center justify-between border-b border-zinc-200 pb-3 mb-8">
              <h3 className="text-sm font-semibold text-black flex items-center gap-2">
                <BookOpen className="w-4 h-4" />
                Tài liệu đã chia sẻ
              </h3>
              <span className="text-xs font-semibold text-zinc-500">{documents.length} kết quả</span>
            </div>
            
            {documents.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-x-6 gap-y-10">
                {documents.map((doc) => (
                  <a
                    key={doc.id || doc._id}
                    href={`/tai-lieu/${doc.slug || doc.id || doc._id}`}
                    className="group flex flex-col gap-4 cursor-pointer"
                  >
                    <div className="relative aspect-[2/3] w-full border border-zinc-200 bg-zinc-50 overflow-hidden p-1">
                      <div className="w-full h-full bg-zinc-100 overflow-hidden">
                        {doc.cover_image || doc.cover_url ? (
                          <img
                            src={doc.cover_image || doc.cover_url}
                            className="w-full h-full object-cover grayscale mix-blend-multiply group-  "
                            alt={doc.title}
                          />
                        ) : (
                          <div className="absolute inset-0 flex items-center justify-center">
                            <BookOpen className="w-8 h-8 text-zinc-300" />
                          </div>
                        )}
                      </div>
                      {doc.price_dl > 0 && (
                        <div className="absolute top-3 right-3 bg-white text-black text-[10px] font-bold px-2 py-1 border border-zinc-200 ">
                          {doc.price_dl} dl
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center justify-between text-[10px] font-bold text-zinc-400 uppercase tracking-wider">
                        <span>{doc.category_name || "Tài liệu"}</span>
                        <span>{doc.views_count || 0} xem</span>
                      </div>
                      <h3 className="text-sm font-semibold text-black line-clamp-2 leading-snug group- underline-offset-4 decoration-1">
                        {doc.title}
                      </h3>
                    </div>
                  </a>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-32 bg-zinc-50 border border-zinc-200">
                <BookOpen className="w-12 h-12 text-zinc-300 mb-4" />
                <p className="font-semibold text-sm text-zinc-500">
                  Chưa có tài liệu nào được công khai
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
