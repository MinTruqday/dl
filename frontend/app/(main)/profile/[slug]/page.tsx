"use client";
import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { API_URL, getToken } from "@/app/lib/api";

export default function ProfilePage() {
  const { slug } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/profile/${slug}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Not found");
        return res.json();
      })
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((e) => {
        console.error(e);
        setLoading(false);
      });
  }, [slug]);

  if (loading) return <div className="p-8 text-center text-muted-foreground">Đang tải hồ sơ</div>;
  if (!data) return <div className="p-8 text-center text-black font-bold outline-black">Không tìm thấy người dùng.</div>;

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="border-b border-border pb-8 relative mb-8">
        <div className="h-48 bg-gradient-to-r from-gray-900 to-gray-900 w-full relative"></div>
        
        <div className="px-8 pb-8 pt-0 relative flex flex-col md:flex-row md:items-end gap-6 justify-between border-b pb-8">
          <div className="flex flex-col md:flex-row items-center md:items-end gap-6 -mt-16 md:-mt-16 z-10">
            <div className="w-32 h-32 rounded-none overflow-hidden border border-border bg-muted flex-shrink-0">
              <img 
                src={data.avatar || "/default-avatar.png"} 
                alt={data.name || data.email} 
                className="w-full h-full object-cover"
              />
            </div>
            
            <div className="text-center md:text-left mb-2">
              <h1 className="text-3xl font-bold text-foreground">{data.name || "Author"}</h1>
              <p className="text-muted-foreground">@{slug}</p>
            </div>
          </div>
        </div>
        
        <div className="px-8 py-6">
            <h2 className="text-xl font-bold mb-4">Thông tin</h2>
            <div className="grid grid-cols-2 gap-4">
                <div className="border p-4 rounded text-center">
                    <div className="font-bold text-2xl">{data.followers_count || 0}</div>
                    <div className="text-muted-foreground">Người theo dõi</div>
                </div>
                <div className="border p-4 rounded text-center">
                    <div className="font-bold text-2xl">{data.published_books?.length || 0}</div>
                    <div className="text-muted-foreground">Tác phẩm xuất bản</div>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
