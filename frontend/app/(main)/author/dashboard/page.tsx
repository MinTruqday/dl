"use client";

import React, { useEffect, useState } from "react";
import AppShell from "@/app/components/AppShell";
import { 
  BarChart3, 
  BookOpen, 
  DollarSign,
  Star, 
  Eye, 
  Users, 
  Plus, 
  Settings, 
  ChevronRight, 
  MessageSquare,
  TrendingUp,
  Clock
} from "lucide-react";
import Link from "next/link";
import { getBooksAPI, getToken } from "@/app/lib/api";

export default function AuthorDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [myBooks, setMyBooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    const fetchData = async () => {
      const token = getToken();
      if (!token) return;

      try {

        const revRes = await fetch(`${API_URL}/author/revenue`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (revRes.ok) setStats(await revRes.json());


        const booksRes = await fetch(`${API_URL}/author/books`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (booksRes.ok) setMyBooks(await booksRes.json());
      } catch (e) {
        console.error("Dashboard fetch error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [API_URL]);

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="w-8 h-8 border-2 border-zinc-900 border-t-transparent animate-spin" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto px-6 py-12 animate-in fade-in duration-500">
        <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-4xl font-bold tracking-tighter text-zinc-900 mb-2">Bảng điều khiển Tác giả</h1>
            <p className="text-zinc-500 text-sm tracking-widest font-bold">Quản lý tài liệu và doanh thu của bạn</p>
          </div>
          <Link 
            href="/editor/new"
            className="inline-flex items-center gap-2 bg-zinc-900 text-white px-6 py-3 text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Viết tài liệu mới
          </Link>
        </header>


        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <StatCard 
            icon={<Eye className="w-5 h-5" />} 
            label="Tổng lượt xem" 
            value={stats?.total_views || 0} 
            trend="+12%" 
          />
          <StatCard 
            icon={<Users className="w-5 h-5" />} 
            label="Độc giả mua" 
            value={stats?.total_sales || 0} 
            trend="+5%" 
          />
          <StatCard 
            icon={<DollarSign className="w-5 h-5" />} 
            label="Doanh thu (Coin)" 
            value={stats?.total_revenue || 0} 
            trend="+18%" 
          />
          <StatCard 
            icon={<BookOpen className="w-5 h-5" />} 
            label="Số tài liệu" 
            value={stats?.total_books || 0} 
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">

          <div className="lg:col-span-2">
            <h2 className="text-xl font-bold text-zinc-900 tracking-tight mb-6 flex items-center gap-2">
              <BookOpen className="w-5 h-5" />
              Tài liệu của tôi
            </h2>
            <div className="space-y-4">
              {myBooks.length === 0 ? (
                <div className="border border-dashed border-zinc-200 p-12 text-center">
                  <p className="text-zinc-400 text-xs font-bold tracking-widest">Chưa có tài liệu nào</p>
                </div>
              ) : (
                myBooks.map((book) => (
                  <Link 
                    key={book.id} 
                    href={`/author/books/${book.id}`}
                    className="group flex items-center gap-6 p-6 border border-zinc-200 hover:border-zinc-900 transition-all duration-300"
                  >
                    <div className="w-16 h-20 bg-zinc-50 border border-zinc-100 flex items-center justify-center shrink-0">
                      {book.cover_url ? (
                        <img src={book.cover_url} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <BookOpen className="w-6 h-6 text-zinc-200" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-[10px] font-bold tracking-widest px-2 py-0.5 border ${
                          book.status === 'published' ? 'border-zinc-900 bg-zinc-900 text-white' : 'border-zinc-200 text-zinc-400'
                        }`}>
                          {book.status === 'published' ? 'Đã đăng' : 'Bản nháp'}
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-zinc-900 truncate group-hover:underline underline-offset-4">{book.title}</h3>
                      <div className="flex items-center gap-4 mt-2 text-[12px] font-bold text-zinc-400 tracking-widest">
                        <span className="flex items-center gap-1"><Eye className="w-3 h-3" /> {book.views}</span>
                        <span className="flex items-center gap-1"><Star className="w-3 h-3" /> {book.average_rating || 0}</span>
                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(book.created_at).toLocaleDateString('vi-VN')}</span>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-zinc-300 group-hover:text-zinc-900 transition-colors" />
                  </Link>
                ))
              )}
            </div>
          </div>


          <div className="space-y-12">
            <div>
              <h2 className="text-xl font-bold text-zinc-900 tracking-tight mb-6 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Giao dịch gần đây
              </h2>
              <div className="border border-zinc-200 p-6 space-y-6">
                {!stats?.recent_sales || stats.recent_sales.length === 0 ? (
                  <p className="text-zinc-400 text-[12px] font-bold tracking-widest text-center py-4">Chưa có giao dịch</p>
                ) : (
                  stats.recent_sales.map((sale: any, i: number) => (
                    <div key={i} className="flex justify-between items-start border-b border-zinc-100 last:border-0 pb-4 last:pb-0">
                      <div>
                        <p className="text-[12px] font-bold text-zinc-900 truncate max-w-[150px]">{sale.book_title}</p>
                        <p className="text-[10px] font-bold text-zinc-400 tracking-widest">{new Date(sale.date).toLocaleDateString('vi-VN')}</p>
                      </div>
                      <span className="text-xs font-bold text-zinc-900">+{sale.price}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div>
              <h2 className="text-xl font-bold text-zinc-900 tracking-tight mb-6">Tiện ích nhanh</h2>
              <div className="grid grid-cols-1 gap-3">
                <QuickAction icon={<MessageSquare className="w-4 h-4" />} label="Phản hồi độc giả" href="/author/feedback" />
                <QuickAction icon={<BarChart3 className="w-4 h-4" />} label="Thống kê chi tiết" href="/author/analytics" />
                <QuickAction icon={<Settings className="w-4 h-4" />} label="Cài đặt thương hiệu" href="/author/brand" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function StatCard({ icon, label, value, trend }: any) {
  return (
    <div className="border border-zinc-200 p-6 hover:border-zinc-900 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className="text-zinc-400">{icon}</div>
        {trend && <span className="text-[10px] font-bold text-zinc-900 bg-zinc-100 px-1.5 py-0.5">{trend}</span>}
      </div>
      <p className="text-[12px] font-bold text-zinc-400 tracking-widest mb-1">{label}</p>
      <p className="text-3xl font-bold text-zinc-900 tracking-tighter">{value}</p>
    </div>
  );
}

function QuickAction({ icon, label, href }: any) {
  return (
    <Link 
      href={href}
      className="flex items-center gap-3 p-4 border border-zinc-200 hover:bg-zinc-50 transition-colors text-[12px] font-bold tracking-widest text-zinc-900"
    >
      {icon}
      {label}
    </Link>
  );
}
