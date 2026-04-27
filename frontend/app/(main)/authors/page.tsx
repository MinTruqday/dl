"use client";

import { useEffect, useState } from "react";
import { getFeaturedAuthorsAPI } from "@/app/lib/api";
import Link from "next/link";
import { User, Users, ChevronRight, BookOpen } from "lucide-react";

export default function AuthorsPage() {
  const [authors, setAuthors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAuthors();
  }, []);

  const loadAuthors = async () => {
    try {
      const data = await getFeaturedAuthorsAPI(10);
      setAuthors(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-[1200px] mx-auto px-6 py-12">
      <div className="space-y-2 mb-16">
        <h1 className="text-4xl font-bold tracking-tight leading-none">Tác giả nổi bật</h1>
        <p className="text-muted-foreground text-sm font-medium tracking-wide">Kết nối và theo dõi những cây viết hàng đầu trong cộng đồng DocLib.</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-64 bg-zinc-100 animate-pulse border border-border" />
          ))}
        </div>
      ) : authors.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {authors.map((author) => (
            <Link key={author.id} href={`/authors/${author.slug}`} className="group p-8 bg-white border border-border hover:border-black transition-all duration-300">
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="w-20 h-20  bg-zinc-100 border border-border overflow-hidden">
                  {author.avatar_url ? (
                    <img src={author.avatar_url} alt={author.full_name} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-zinc-400">
                      <User className="w-8 h-8" />
                    </div>
                  )}
                </div>
                <div className="space-y-1">
                  <h3 className="text-sm font-bold tracking-widest">{author.full_name}</h3>
                  <p className="text-[12px] text-zinc-400 font-bold tracking-tighter">@{author.slug}</p>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed min-h-[48px]">
                  {author.bio}
                </p>
                <div className="pt-4 flex items-center gap-4 text-[12px] font-bold tracking-widest text-zinc-400 group-hover:text-black transition-colors">
                  <span className="flex items-center gap-1.5"><BookOpen className="w-3 h-3" /> 12 Books</span>
                  <span className="flex items-center gap-1.5"><Users className="w-3 h-3" /> 450 Follows</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="h-[400px] flex flex-col items-center justify-center text-center border border-dashed border-border bg-zinc-50/50 p-12">
           <Users className="w-12 h-12 text-zinc-200 mb-4" />
           <h3 className="text-sm font-bold tracking-widest mb-1">Hiện chưa có tác giả nào</h3>
           <p className="text-xs text-muted-foreground">Cộng đồng tác giả của chúng tôi đang trong quá trình phát triển.</p>
        </div>
      )}
    </div>
  );
}
