"use client";

import { useEffect, useState } from "react";
import { getAuthorStatsAPI, getAuthorDemographicsAPI } from "@/app/lib/api";
import { useAuth } from "@/app/contexts/AuthContext";
import { BarChart2, TrendingUp, Users, BookOpen, ChevronRight, ArrowUpRight, PieChart, Star } from "lucide-react";
import Link from "next/link";

export default function AnalyticsDashboard() {
  const { user } = useAuth() as any;
  const [stats, setStats] = useState<any>(null);
  const [demographics, setDemographics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, d] = await Promise.all([getAuthorStatsAPI(), getAuthorDemographicsAPI()]);
      setStats(s);
      setDemographics(d);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-[1200px] mx-auto px-6 py-12">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight leading-none">Phân tích tác giả</h1>
          <p className="text-muted-foreground text-xs font-medium tracking-wide">Dữ liệu hiệu quả hoạt động và nhân khẩu học độc giả.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="p-8 bg-zinc-50 border border-border space-y-4">
          <div className="flex items-center gap-2 text-[12px] font-bold tracking-widest text-muted-foreground">
            <BookOpen className="w-3.5 h-3.5" />
            Tổng tài liệu
          </div>
          <div className="text-4xl font-bold">{stats?.total_documents || 0}</div>
          <div className="flex items-center gap-1.5 text-[12px] font-bold text-black">
            <ArrowUpRight className="w-3 h-3" />
            +12% so với tháng trước
          </div>
        </div>

        <div className="p-8 bg-zinc-50 border border-border space-y-4">
          <div className="flex items-center gap-2 text-[12px] font-bold tracking-widest text-muted-foreground">
            <TrendingUp className="w-3.5 h-3.5" />
            Tổng lượt xem
          </div>
          <div className="text-4xl font-bold">{stats?.total_views?.toLocaleString() || 0}</div>
          <div className="flex items-center gap-1.5 text-[12px] font-bold text-black">
             <ArrowUpRight className="w-3 h-3" />
             Tăng trưởng ổn định
          </div>
        </div>

        <div className="p-8 bg-zinc-50 border border-border space-y-4">
          <div className="flex items-center gap-2 text-[12px] font-bold tracking-widest text-muted-foreground">
            <Users className="w-3.5 h-3.5" />
            Người theo dõi
          </div>
          <div className="text-4xl font-bold">{stats?.followers_count || 0}</div>
          <div className="flex items-center gap-1.5 text-[12px] font-bold text-black">
             Đang hoạt động tích cực
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        <div className="space-y-8">
          <h2 className="text-lg font-bold tracking-tight border-b border-border pb-4 flex items-center gap-2">
             <BarChart2 className="w-4 h-4" />
             Hiệu quả từng tài liệu
          </h2>
          <div className="space-y-1">
            {stats?.documents?.map((doc: any) => (
              <div key={doc.id} className="flex items-center justify-between p-4 border border-border hover:bg-zinc-50 transition-colors">
                <div className="space-y-1">
                  <div className="text-sm font-bold">{doc.title}</div>
                  <div className="text-[12px] font-bold text-zinc-400 tracking-widest flex items-center">
                    {doc.rating.toFixed(1)} <Star className="w-3 h-3 inline-block mx-1 fill-current" /> Đánh giá
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold">{doc.views}</div>
                  <div className="text-[12px] font-bold text-zinc-400 tracking-widest">Lượt xem</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-8">
           <h2 className="text-lg font-bold tracking-tight border-b border-border pb-4 flex items-center gap-2">
              <PieChart className="w-4 h-4" />
              Nhân khẩu học độc giả
           </h2>
           <div className="p-8 bg-zinc-50 border border-border space-y-8">
              <div className="space-y-4">
                 <div className="text-[12px] font-bold tracking-widest text-muted-foreground">Độ tuổi</div>
                 <div className="space-y-3">
                    {Object.entries(demographics?.age_groups || {}).map(([group, val]: any) => (
                       <div key={group} className="space-y-1.5">
                          <div className="flex justify-between text-[12px] font-bold">
                             <span>{group}</span>
                             <span>{val}%</span>
                          </div>
                          <div className="h-1 bg-zinc-200">
                             <div className="h-full bg-black" style={{ width: `${val}%` }} />
                          </div>
                       </div>
                    ))}
                 </div>
              </div>

              <div className="space-y-4">
                 <div className="text-[12px] font-bold tracking-widest text-muted-foreground">Giới tính</div>
                 <div className="flex gap-4">
                    {Object.entries(demographics?.gender_ratio || {}).map(([gender, val]: any) => (
                       <div key={gender} className="flex-1 space-y-1.5">
                          <div className="text-[12px] font-bold truncate">{gender === 'male' ? 'Nam' : gender === 'female' ? 'Nữ' : 'Khác'}</div>
                          <div className="text-lg font-bold">{val}%</div>
                          <div className="h-1 bg-zinc-200">
                             <div className="h-full bg-black" style={{ width: `${val}%` }} />
                          </div>
                       </div>
                    ))}
                 </div>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
