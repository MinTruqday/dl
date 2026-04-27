"use client";

import { useEffect, useState } from "react";
import { getNotificationsAPI, markNotificationReadAPI } from "@/app/lib/api";
import { Bell, Check, Clock, Trash2, ExternalLink, Mail, MessageSquare, CreditCard, UserPlus } from "lucide-react";
import Link from "next/link";

export default function NotificationPage() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await getNotificationsAPI();
      setNotifications(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const markRead = async (id: string) => {
    try {
      await markNotificationReadAPI(id);
      setNotifications(notifications.map(n => n._id === id ? { ...n, is_read: true } : n));
    } catch (e) {
      console.error(e);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case "purchase": return <CreditCard className="w-4 h-4" />;
      case "reply": return <MessageSquare className="w-4 h-4" />;
      case "follow": return <UserPlus className="w-4 h-4" />;
      default: return <Bell className="w-4 h-4" />;
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 animate-in fade-in duration-300">
      <header className="flex items-center justify-between border-b border-black pb-8 mb-12">
        <div>
           <div className="flex items-center gap-3 mb-2">
              <Bell className="w-5 h-5 text-black" />
              <span className="text-[12px] font-bold tracking-widest text-zinc-400">Cập nhật hệ thống</span>
           </div>
           <h1 className="text-4xl font-bold text-black tracking-tighter">Trung tâm thông báo</h1>
        </div>
        <div className="text-right">
           <p className="text-xs font-bold tracking-widest text-zinc-400">Tổng cộng</p>
           <p className="text-2xl font-bold">{notifications.length}</p>
        </div>
      </header>

      <div className="space-y-4">
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-24 bg-zinc-50 border border-border animate-pulse" />
            ))}
          </div>
        ) : notifications.length > 0 ? (
          notifications.map((n) => (
            <div 
              key={n._id} 
              className={`group relative p-6 border transition-all duration-300 flex items-start gap-6 ${n.is_read ? 'bg-white border-zinc-100 opacity-60' : 'bg-white border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]'}`}
            >
              <div className={`w-10 h-10 shrink-0 flex items-center justify-center border ${n.is_read ? 'border-zinc-200 text-zinc-300' : 'border-black bg-black text-white'}`}>
                {getIcon(n.type)}
              </div>
              
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                   <h3 className={`text-sm font-bold ${n.is_read ? 'text-zinc-500' : 'text-black'}`}>{n.title}</h3>
                   <span className="text-[12px] font-bold text-zinc-400 tracking-widest flex items-center gap-1.5">
                      <Clock className="w-3 h-3" />
                      {new Date(n.created_at).toLocaleDateString("vi-VN")}
                   </span>
                </div>
                <p className="text-xs text-zinc-600 leading-relaxed max-w-2xl">{n.message || n.body}</p>
                
                <div className="pt-4 flex items-center gap-4">
                   {n.link && (
                      <Link href={n.link} className="text-[12px] font-bold tracking-widest text-black hover:underline flex items-center gap-1">
                         Xem chi tiết <ExternalLink className="w-3 h-3" />
                      </Link>
                   )}
                   {!n.is_read && (
                      <button 
                         onClick={() => markRead(n._id)}
                         className="text-[12px] font-bold tracking-widest text-zinc-400 hover:text-black transition-colors"
                      >
                         Đánh dấu đã đọc
                      </button>
                   )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="py-24 text-center border border-dashed border-border bg-zinc-50/50">
             <Mail className="w-8 h-8 text-zinc-200 mx-auto mb-4" />
             <p className="text-[12px] font-bold tracking-widest text-zinc-300">Không có thông báo mới.</p>
          </div>
        )}
      </div>
    </div>
  );
}
