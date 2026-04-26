"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getAuthorPublicProfileAPI } from "@/app/lib/api";
import { BookOpen, Users, Star, Calendar, Share2, MessageSquare, ShieldCheck, ArrowUpRight } from "lucide-react";
import Link from "next/link";

export default function AuthorProfilePage() {
  const params = useParams();
  const slug = params.slug as string;
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (slug) loadProfile();
  }, [slug]);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const data = await getAuthorPublicProfileAPI(slug);
      setProfile(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen space-y-4">
        <h1 className="text-2xl font-bold tracking-tighter">Không tìm thấy tác giả</h1>
        <Link href="/authors" className="text-xs font-bold tracking-widest border border-black px-6 py-2 hover:bg-black hover:text-white transition-all">Trở về danh sách</Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 animate-in fade-in duration-500">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div className="lg:col-span-4 space-y-8">
           <div className="border border-black p-8 text-center space-y-6">
              <div className="w-32 h-32 mx-auto border border-black overflow-hidden bg-zinc-50">
                 {profile.avatar_url ? (
                    <img src={profile.avatar_url} alt={profile.full_name} className="w-full h-full object-cover" />
                 ) : (
                    <div className="w-full h-full flex items-center justify-center text-4xl font-black">{profile.full_name[0]}</div>
                 )}
              </div>
              <div>
                 <h1 className="text-2xl font-black tracking-tighter mb-1 flex items-center justify-center gap-2">
                    {profile.full_name}
                    <ShieldCheck className="w-5 h-5 text-zinc-400" />
                 </h1>
                 <p className="text-[10px] font-bold text-zinc-400 tracking-widest">Tác giả chuyên nghiệp • DocLib Verified</p>
              </div>
              <p className="text-sm text-zinc-600 leading-relaxed italic">
                 "{profile.bio || "Tác giả này chưa cập nhật tiểu sử."}"
              </p>
              <div className="pt-6 border-t border-zinc-100 grid grid-cols-2 gap-4">
                 <div className="space-y-1">
                    <p className="text-xl font-black tracking-tighter">{profile.followers_count || 0}</p>
                    <p className="text-[9px] font-bold text-zinc-400 tracking-widest">Người theo dõi</p>
                 </div>
                 <div className="space-y-1">
                    <p className="text-xl font-black tracking-tighter">{profile.books?.length || 0}</p>
                    <p className="text-[9px] font-bold text-zinc-400 tracking-widest">Tác phẩm</p>
                 </div>
              </div>
              <button className="w-full bg-black text-white text-[10px] font-bold tracking-widest py-4 hover:bg-zinc-800 transition-all">
                 Theo dõi tác giả
              </button>
           </div>

           <div className="border border-zinc-100 p-8 space-y-6">
              <h3 className="text-xs font-bold tracking-widest border-b border-zinc-100 pb-4">Thông tin bổ sung</h3>
              <div className="space-y-4">
                 <div className="flex items-center justify-between text-xs font-bold">
                    <span className="text-zinc-400 tracking-widest flex items-center gap-2"><Calendar className="w-3.5 h-3.5" /> Tham gia</span>
                    <span>{new Date(profile.joined_at).toLocaleDateString("vi-VN")}</span>
                 </div>
                 <div className="flex items-center justify-between text-xs font-bold">
                    <span className="text-zinc-400 tracking-widest flex items-center gap-2"><Share2 className="w-3.5 h-3.5" /> Chia sẻ</span>
                    <div className="flex gap-2">
                       <button className="hover:text-black transition-colors">FB</button>
                       <button className="hover:text-black transition-colors">TW</button>
                    </div>
                 </div>
              </div>
           </div>
        </div>

        <div className="lg:col-span-8 space-y-12">
           <div className="flex items-center justify-between border-b-2 border-black pb-4">
              <h2 className="text-lg font-black tracking-tighter flex items-center gap-2">
                 <BookOpen className="w-5 h-5" />
                 Danh sách tác phẩm
              </h2>
              <div className="text-[10px] font-bold text-zinc-400 tracking-widest">Sắp xếp theo: Mới nhất</div>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {profile.books?.map((book: any) => (
                 <Link key={book.id} href={`/preview?slug=${book.slug}`} className="group space-y-4">
                    <div className="aspect-[3/4] bg-zinc-50 border border-zinc-200 overflow-hidden relative">
                       {book.cover_url ? (
                          <img src={book.cover_url} alt={book.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                       ) : (
                          <div className="w-full h-full flex items-center justify-center text-zinc-200 font-black text-2xl text-center p-8">{book.title}</div>
                       )}
                       <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
                    </div>
                    <div className="space-y-2">
                       <div className="flex items-center justify-between">
                          <h3 className="text-base font-bold tracking-tight line-clamp-1">{book.title}</h3>
                          <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-all" />
                       </div>
                       <div className="flex items-center gap-4 text-[10px] font-bold text-zinc-400 tracking-widest">
                          <span className="flex items-center gap-1"><Star className="w-3 h-3 text-black" /> {book.average_rating?.toFixed(1) || "0.0"}</span>
                          <span className="flex items-center gap-1"><MessageSquare className="w-3 h-3" /> {book.views || 0} lượt xem</span>
                       </div>
                    </div>
                 </Link>
              ))}
           </div>

           {profile.books?.length === 0 && (
              <div className="py-24 text-center border border-dashed border-border bg-zinc-50/50">
                 <p className="text-[10px] font-bold tracking-widest text-zinc-300">Chưa có tác phẩm nào được xuất bản.</p>
              </div>
           )}
        </div>
      </div>
    </div>
  );
}
