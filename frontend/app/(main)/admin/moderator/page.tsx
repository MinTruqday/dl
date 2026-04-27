"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/app/lib/api";
import { Shield, AlertTriangle, Users, Tag, BarChart3, Clock, Ban, MessageSquare, Bug, FileWarning, Crown, ListTodo, ScrollText, Trash2, Eye } from "lucide-react";

type TabKey = "reports" | "metrics" | "tags" | "blacklist" | "bugs" | "disputes" | "vip" | "tasks" | "policies";

export default function ModeratorDashboardPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [tags, setTags] = useState<any[]>([]);
  const [blacklist, setBlacklist] = useState<any[]>([]);
  const [bugReports, setBugReports] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabKey>("reports");
  const [message, setMessage] = useState("");
  const [newTag, setNewTag] = useState("");
  const [newKeyword, setNewKeyword] = useState("");
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => { fetchAll(); }, []);

  const h = () => ({ Authorization: `Bearer ${getToken()}` });
  const jh = () => ({ "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` });

  const fetchAll = async () => {
    try {
      const [reportsR, metricsR, tagsR, blacklistR, bugsR, tasksR, policiesR] = await Promise.all([
        fetch(`${API_URL}/moderator/reports?status=pending`, { headers: h() }),
        fetch(`${API_URL}/moderator/metrics`, { headers: h() }),
        fetch(`${API_URL}/moderator/tags`, { headers: h() }),
        fetch(`${API_URL}/moderator/blacklist`, { headers: h() }),
        fetch(`${API_URL}/moderator/bug-reports`, { headers: h() }),
        fetch(`${API_URL}/moderator/tasks/mine`, { headers: h() }),
        fetch(`${API_URL}/moderator/policy-proposals`, { headers: h() }),
      ]);
      if (reportsR.ok) setReports(await reportsR.json());
      if (metricsR.ok) setMetrics(await metricsR.json());
      if (tagsR.ok) setTags(await tagsR.json());
      if (blacklistR.ok) setBlacklist(await blacklistR.json());
      if (bugsR.ok) setBugReports(await bugsR.json());
      if (tasksR.ok) setTasks(await tasksR.json());
      if (policiesR.ok) setPolicies(await policiesR.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const showMsg = (msg: string) => { setMessage(msg); setTimeout(() => setMessage(""), 3000); };

  const postAction = async (endpoint: string, payload: any, successMsg: string) => {
    try {
      const res = await fetch(`${API_URL}/moderator/${endpoint}`, {
        method: "POST",
        headers: jh(),
        body: JSON.stringify(payload),
      });
      if (res.ok) { showMsg(successMsg); fetchAll(); }
      else { const d = await res.json(); showMsg(d.detail || "Thao tác thất bại"); }
    } catch (e) { showMsg("Lỗi kết nối"); }
  };

  const putAction = async (endpoint: string, payload: any, successMsg: string) => {
    try {
      const res = await fetch(`${API_URL}/moderator/${endpoint}`, {
        method: "PUT",
        headers: jh(),
        body: JSON.stringify(payload),
      });
      if (res.ok) { showMsg(successMsg); fetchAll(); }
    } catch (e) { showMsg("Lỗi kết nối"); }
  };

  const removeContent = async (itemType: string, itemId: string) => {
    const reason = prompt("Lý do gỡ nội dung:");
    if (!reason) return;
    await postAction("content/remove", { item_type: itemType, item_id: itemId, reason }, "Đã gỡ nội dung");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center animate-in fade-in duration-300">
        <div className="w-10 h-10 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  const tabItems: { key: TabKey; label: string; icon: any }[] = [
    { key: "reports", label: "Báo cáo", icon: AlertTriangle },
    { key: "metrics", label: "Chỉ số", icon: BarChart3 },
    { key: "tags", label: "Thẻ", icon: Tag },
    { key: "blacklist", label: "Từ cấm", icon: Ban },
    { key: "bugs", label: "Lỗi hệ thống", icon: Bug },
    { key: "disputes", label: "Bản quyền", icon: FileWarning },
    { key: "vip", label: "VIP", icon: Crown },
    { key: "tasks", label: "Nhiệm vụ", icon: ListTodo },
    { key: "policies", label: "Chính sách", icon: ScrollText },
  ];

  return (
    <div className="w-full max-w-[1100px] mx-auto px-6 lg:px-8 py-12 bg-white min-h-screen animate-in fade-in duration-300">
      {message && (
        <div className="fixed top-6 right-6 z-50 px-5 py-3 bg-black text-white text-[12px] font-bold tracking-widest animate-in slide-in-from-right-4 duration-300">
          {message}
        </div>
      )}

      <header className="border-b border-black pb-8 mb-10">
        <div className="flex items-center gap-3 mb-2">
          <Shield className="w-5 h-5 text-zinc-400" />
          <span className="text-[12px] font-bold tracking-widest text-zinc-400">Kiểm duyệt</span>
        </div>
        <h1 className="text-4xl font-bold text-black tracking-tighter">Bảng điều khiển kiểm duyệt</h1>
      </header>

      <div className="flex gap-1 mb-10 border-b border-border overflow-x-auto">
        {tabItems.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-3 text-[12px] font-bold tracking-widest transition-all border-b-2 whitespace-nowrap ${
              activeTab === tab.key ? "border-black text-black" : "border-transparent text-zinc-400 hover:text-black"
            }`}
          >
            <tab.icon className="w-3.5 h-3.5" /> {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "reports" && (
        <div className="animate-in fade-in duration-300 space-y-3">
          {reports.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-border">
              <p className="text-xs text-zinc-400 font-bold tracking-widest">Không có báo cáo nào đang chờ</p>
            </div>
          ) : reports.map((r: any) => (
            <div key={r.id} className="border border-border p-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[12px] font-bold tracking-widest px-2 py-0.5 border border-zinc-300 text-zinc-500">{r.item_type}</span>
                  </div>
                  <p className="text-sm font-bold text-black">{r.reason}</p>
                  <p className="text-[12px] text-zinc-400 font-medium mt-2">Người báo cáo: {r.reporter_name}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button onClick={() => removeContent(r.item_type, r.item_id)} className="px-3 py-1.5 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-all">
                    Gỡ nội dung
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === "metrics" && metrics && (
        <div className="animate-in fade-in duration-300 grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Tổng người dùng", value: metrics.total_users, icon: Users },
            { label: "Đang hoạt động", value: metrics.active_users, icon: Users },
            { label: "Báo cáo chờ", value: metrics.pending_reports, icon: AlertTriangle },
            { label: "Bài viết", value: metrics.total_posts, icon: MessageSquare },
          ].map((m, i) => (
            <div key={i} className="border border-border p-5">
              <m.icon className="w-5 h-5 text-zinc-400 mb-3" />
              <span className="text-3xl font-bold text-black">{m.value}</span>
              <p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">{m.label}</p>
            </div>
          ))}
        </div>
      )}

      {activeTab === "tags" && (
        <div className="animate-in fade-in duration-300">
          <div className="flex gap-2 mb-6">
            <input type="text" placeholder="Tên thẻ mới" value={newTag} onChange={(e) => setNewTag(e.target.value)} onKeyDown={(e) => e.key === "Enter" && postAction("tags", { action: "create", tag_name: newTag }, "Đã tạo thẻ").then(() => setNewTag(""))} className="flex-1 px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all" />
            <button onClick={() => postAction("tags", { action: "create", tag_name: newTag }, "Đã tạo thẻ").then(() => setNewTag(""))} className="px-6 py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800">Tạo</button>
          </div>
          <div className="flex flex-wrap gap-2">
            {tags.map((t: any) => (
              <div key={t.id} className="flex items-center gap-2 px-4 py-2 border border-border hover:border-black transition-all">
                <Tag className="w-3.5 h-3.5 text-zinc-400" />
                <span className="text-xs font-bold text-black">{t.name}</span>
                <button onClick={() => postAction("tags", { action: "delete", tag_name: t.name }, "Đã xóa thẻ")} className="text-zinc-300 hover:text-black transition-colors">&times;</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "blacklist" && (
        <div className="animate-in fade-in duration-300">
          <div className="flex gap-2 mb-6">
            <input type="text" placeholder="Từ khóa cấm mới" value={newKeyword} onChange={(e) => setNewKeyword(e.target.value)} onKeyDown={(e) => e.key === "Enter" && postAction("blacklist", { action: "add", keyword: newKeyword }, "Đã thêm").then(() => setNewKeyword(""))} className="flex-1 px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all" />
            <button onClick={() => postAction("blacklist", { action: "add", keyword: newKeyword }, "Đã thêm").then(() => setNewKeyword(""))} className="px-6 py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800">Thêm</button>
          </div>
          <div className="space-y-1">{blacklist.map((k: any) => (
            <div key={k.id} className="flex items-center justify-between px-4 py-3 border-b border-zinc-50">
              <span className="text-sm font-medium text-black">{k.keyword}</span>
              <span className="text-[12px] text-zinc-400 font-bold tracking-widest">Đang áp dụng</span>
            </div>
          ))}</div>
        </div>
      )}

      {activeTab === "bugs" && (
        <div className="animate-in fade-in duration-300 space-y-3">
          {bugReports.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-border">
              <Bug className="w-8 h-8 text-zinc-200 mx-auto mb-3" />
              <p className="text-xs text-zinc-400 font-bold tracking-widest">Không có báo cáo lỗi nào</p>
            </div>
          ) : bugReports.map((b: any) => (
            <div key={b.id} className="border border-border p-5">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-sm font-bold text-black">{b.title}</span>
                  <span className={`text-[12px] font-bold tracking-widest ml-3 ${b.severity === "high" ? "text-black" : "text-zinc-400"}`}>{b.severity}</span>
                </div>
                <span className="text-[12px] font-bold tracking-widest text-zinc-400">{b.status}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === "disputes" && (
        <div className="animate-in fade-in duration-300 border border-border p-6">
          <h2 className="text-xs font-bold tracking-widest text-black mb-6">Tranh chấp bản quyền</h2>
          <p className="text-xs text-zinc-400 text-center py-8">Sử dụng API để tạo và giải quyết tranh chấp</p>
          <button onClick={() => {
            const desc = prompt("Mô tả tranh chấp:");
            if (desc) postAction("copyright-disputes", { plaintiff_id: "user_a", defendant_id: "user_b", book_id: "book_1", description: desc }, "Đã tạo tranh chấp");
          }} className="w-full py-3 border border-border text-[12px] font-bold tracking-widest hover:border-black transition-all">
            Tạo tranh chấp mới
          </button>
        </div>
      )}

      {activeTab === "vip" && (
        <div className="animate-in fade-in duration-300 border border-border p-6">
          <h2 className="text-xs font-bold tracking-widest text-black flex items-center gap-2 mb-6"><Crown className="w-4 h-4" /> Quản lý tác giả VIP</h2>
          <div className="space-y-4">
            <input type="text" placeholder="User ID cần thăng/gỡ VIP" id="vip-uid" className="w-full px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all" />
            <div className="flex gap-3">
              <button onClick={() => { const uid = (document.getElementById("vip-uid") as HTMLInputElement)?.value; if (uid) postAction("vip-author", { user_id: uid, action: "promote" }, "Đã thăng cấp VIP"); }} className="flex-1 py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800">Thăng cấp VIP</button>
              <button onClick={() => { const uid = (document.getElementById("vip-uid") as HTMLInputElement)?.value; if (uid) postAction("vip-author", { user_id: uid, action: "demote" }, "Đã gỡ VIP"); }} className="flex-1 py-3 border border-border text-[12px] font-bold tracking-widest hover:border-black">Gỡ cấp VIP</button>
            </div>
          </div>
        </div>
      )}

      {activeTab === "tasks" && (
        <div className="animate-in fade-in duration-300 space-y-3">
          {tasks.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-border">
              <ListTodo className="w-8 h-8 text-zinc-200 mx-auto mb-3" />
              <p className="text-xs text-zinc-400 font-bold tracking-widest">Chưa có nhiệm vụ nào</p>
            </div>
          ) : tasks.map((t: any) => (
            <div key={t.id} className="border border-border p-5 flex items-center justify-between">
              <div>
                <span className="text-sm font-bold text-black">{t.title}</span>
                <span className={`text-[12px] font-bold tracking-widest ml-3 ${t.priority === "high" ? "text-black" : "text-zinc-400"}`}>{t.priority}</span>
              </div>
              <span className="text-[12px] font-bold tracking-widest text-zinc-400">{t.status}</span>
            </div>
          ))}
        </div>
      )}

      {activeTab === "policies" && (
        <div className="animate-in fade-in duration-300 space-y-4">
          <button onClick={() => {
            const title = prompt("Tiêu đề đề xuất:");
            const content = prompt("Nội dung:");
            if (title && content) postAction("policy-proposals", { title, content }, "Đã gửi đề xuất");
          }} className="w-full py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-all mb-4">
            Tạo đề xuất chính sách mới
          </button>
          {policies.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-border">
              <p className="text-xs text-zinc-400 font-bold tracking-widest">Chưa có đề xuất nào</p>
            </div>
          ) : policies.map((p: any) => (
            <div key={p.id} className="border border-border p-5">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-sm font-bold text-black">{p.title}</span>
                  <span className="text-[12px] text-zinc-400 font-bold tracking-widest ml-3">{p.category}</span>
                </div>
                <span className="text-[12px] font-bold tracking-widest text-zinc-400">{p.status}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
