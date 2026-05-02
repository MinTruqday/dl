"use client";
import React, { useEffect, useState } from "react";
import Workspace from "@/components/Workspace";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { User, ShieldCheck, UserPlus, Users, Link as LinkIcon, BookOpen, AlertCircle, Loader2 } from "lucide-react";
import { getUserProfileAPI, followUserAPI } from "@/services/social.service";
import { getDocumentsAPI } from "@/services/document.service";
import { API_URL } from "@/services/auth.service";

export default function AuthorProfilePage() {
  const params = useParams();
  const slug = params?.slug as string;
  const router = useRouter();
  const [author, setAuthor] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isFollowing, setIsFollowing] = useState(false);
  const [activeTab, setActiveTab] = useState<"works" | "about">("works");
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
      setAuthor(data.data || data);
      setIsFollowing(data.is_following || (data.data && data.data.is_following) || false);
      
      const docData = await getDocumentsAPI(undefined, "latest", undefined, undefined, slug);
      setDocuments(docData.data || docData || []);
    } catch (err: any) {
      console.error("Lỗi tải thông tin tác giả:", err);
      setError(err.message || "Không thể tải thông tin tác giả");
    } finally {
      setLoading(false);
    }
  };

  const toggleFollow = async () => {
    if (!author) return;
    try {
      await followUserAPI(author._id || author.id || slug);
      setIsFollowing(!isFollowing);
      setAuthor((prev: any) => ({
        ...prev,
        followers_count: (prev.followers_count || 0) + (isFollowing ? -1 : 1)
      }));
    } catch (err: any) {
        console.error("Thao tác thất bại:", err);
    }
  };

  if (loading) {
    return (
      <Workspace>
        <div className="flex h-[80vh] items-center justify-center">
          <div className="flex flex-col items-center gap-6">
            <Loader2 className="w-10 h-10 animate-spin text-zinc-300" />
            <p className="text-[11px] font-bold text-zinc-300">Đang đồng bộ dữ liệu tri thức</p>
          </div>
        </div>
      </Workspace>
    );
  }

  if (error || !author) {
    return (
      <Workspace>
        <div className="flex h-[80vh] flex-col items-center justify-center gap-6 animate-in fade-in duration-300">
          <AlertCircle className="w-16 h-16 text-zinc-300" />
          <p className="text-sm font-bold text-zinc-400">{error || "Tác giả không tồn tại"}</p>
        </div>
      </Workspace>
    );
  }

  return (
    <Workspace>
      <div 
        className="max-w-5xl mx-auto px-4 py-12 md:py-20 transition-all duration-300 font-sans" 
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(12px)" }}
      >
        <div className="bg-white border border-zinc-200 rounded-sm p-8 md:p-12 flex flex-col md:flex-row items-center md:items-start gap-12 mb-16 hover:border-black transition-all">
          <div className="w-32 h-32 md:w-40 md:h-40 bg-zinc-50 border border-zinc-100 overflow-hidden shrink-0 grayscale hover:grayscale-0 transition-all">
            {author.avatar_url ? (
              <img src={author.avatar_url} alt={author.username} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-zinc-200">
                <User className="w-16 h-16" />
              </div>
            )}
          </div>
          <div className="flex-1 text-center md:text-left">
            <div className="inline-flex items-center px-4 py-1.5 bg-zinc-50 border border-zinc-100 text-zinc-400 text-[10px] font-bold mb-4">
              Hồ sơ tác giả
            </div>
            <h1 className="text-4xl font-bold text-black flex items-center justify-center md:justify-start gap-3 mb-2 tracking-tighter">
              {author.full_name || author.username}
              {author.role === "author" && <ShieldCheck className="w-6 h-6 text-black" />}
            </h1>
            <p className="text-zinc-500 font-medium mb-8 text-sm">@{author.slug || author.username}</p>
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-8 text-[11px] font-bold text-zinc-400 mb-10">
              <span className="flex items-center gap-2">
                <Users className="w-4 h-4" /> {author.followers_count || 0} người theo dõi
              </span>
              <span className="flex items-center gap-2">
                <BookOpen className="w-4 h-4" /> {documents.length} tài liệu xuất bản
              </span>
            </div>
            <div className="flex items-center justify-center md:justify-start gap-4">
               <Button
                onClick={toggleFollow}
                className={`px-10 h-14 flex items-center gap-3 text-[11px] font-bold transition-all active:scale-95 ${isFollowing ? "bg-zinc-100 text-black border border-zinc-200" : "bg-black text-white"}`}
              >
                <UserPlus className="w-4 h-4" />
                {isFollowing ? "Đang theo dõi" : "Theo dõi tác giả"}
              </Button>
            </div>
          </div>
        </div>

        <div className="border-b border-zinc-100 mb-12">
          <nav className="-mb-px flex gap-12 justify-center md:justify-start">
            {[
              { id: "works", label: "Tài liệu đã xuất bản" },
              { id: "about", label: "Tiểu sử chi tiết" }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                 className={`whitespace-nowrap py-6 border-b-2 font-bold text-[11px] transition-all active:scale-95 ${activeTab === tab.id ? "border-black text-black" : "border-transparent text-zinc-400 hover:text-black"}`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="min-h-[400px]">
          {activeTab === "works" && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
              {documents.length > 0 ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {documents.map((doc) => (
                    <a key={doc.id || doc._id} href={`/documents/${doc.slug || doc.id || doc._id}`} className="group block bg-white border border-zinc-100 p-6 hover:border-black transition-all">
                      <div className="aspect-[2/3] w-full bg-zinc-50 border border-zinc-50 relative overflow-hidden mb-6">
                        {doc.cover_image ? (
                          <img src={doc.cover_image} alt={doc.title} className="w-full h-full object-cover grayscale group-hover:grayscale-0 group-hover:scale-105 transition-all duration-500" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-zinc-200">
                            <BookOpen className="w-12 h-12" />
                          </div>
                        )}
                        {doc.price_dl > 0 && (
                          <div className="absolute top-4 right-4 bg-black text-white text-[9px] font-bold px-3 py-1.5 border border-white/20">
                            {doc.price_dl} DL
                          </div>
                        )}
                      </div>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-[9px] font-bold text-zinc-300">{doc.category_name || "Tri thức"}</span>
                          <span className="text-[9px] font-bold text-zinc-300">{doc.views_count || 0} lượt xem</span>
                        </div>
                        <h3 className="font-bold text-black text-sm tracking-tight line-clamp-2 group-hover:underline underline-offset-4 decoration-1">{doc.title}</h3>
                      </div>
                    </a>
                  ))}
                </div>
              ) : (
                <div className="text-center py-32 text-zinc-300 border border-dashed border-zinc-200 bg-zinc-50/20">
                  <BookOpen className="w-12 h-12 mx-auto mb-6 opacity-20" />
                  <p className="font-bold text-[11px]">Chưa có tài liệu nào được công khai</p>
                </div>
              )}
            </div>
          )}

          {activeTab === "about" && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
              <div className="bg-white border border-zinc-100 p-10 max-w-3xl">
                <div className="flex items-center gap-4 mb-8 border-b border-zinc-50 pb-6">
                  <LinkIcon className="w-5 h-5 text-zinc-300" />
                  <h2 className="text-lg font-bold text-black tracking-tight">Hành trình tri thức</h2>
                </div>
                <div className="prose prose-zinc max-w-none text-zinc-600 leading-relaxed text-sm font-medium">
                  {author.bio ? (
                    <div dangerouslySetInnerHTML={{ __html: author.bio.replace(/\n/g, "<br/>") }} />
                  ) : (
                    <p className="italic text-zinc-300 text-center py-20 font-bold">Tác giả chưa cập nhật thông tin giới thiệu</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Workspace>
  );
}
