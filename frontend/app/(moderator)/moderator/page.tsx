"use client";

import { useEffect, useState, useCallback } from "react";
import { getToken, API_URL, formatError } from "@/app/lib/api";
import { 
    ShieldCheck, 
    AlertTriangle, 
    CheckCircle2, 
    XCircle, 
    Clock, 
    User, 
    BookOpen,
    Eye,
    Loader2,
    Search,
    Filter,
    ChevronRight,
    ArrowRight,
    MessageSquare,
    Zap,
    Award
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/app/contexts/AuthContext";
import { Notification } from "@/app/components/NotificationToast";

type ModTab = "documents" | "reports" | "logs";

export default function ModerationDashboard() {
    const { user, isLoading } = useAuth() as any;
    const [activeTab, setActiveTab] = useState<ModTab>("documents");
    const [pendingDocuments, setPendingDocuments] = useState<any[]>([]);
    const [reports, setReports] = useState<any[]>([]);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
    const [visible, setVisible] = useState(false);

    const fetchData = useCallback(async () => {
        setIsRefreshing(true);
        try {
            const headers = { 'Authorization': `Bearer ${getToken()}` };
            const [docsRes, reportsRes] = await Promise.all([
                fetch(`${API_URL}/moderator/approval-queue`, { headers }),
                fetch(`${API_URL}/moderator/reports`, { headers })
            ]);
            
            if (docsRes.ok) {
                const docsData = await docsRes.json();
                setPendingDocuments(docsData.data || docsData || []);
            }
            if (reportsRes.ok) {
                const reportsData = await reportsRes.json();
                setReports(reportsData.data || reportsData || []);
            }
        } catch (err: any) {
            setNotification({ type: "error", text: "Không thể kết nối máy chủ kiểm duyệt." });
        } finally {
            setIsRefreshing(false);
            requestAnimationFrame(() => setVisible(true));
        }
    }, [API_URL]);

    useEffect(() => {
        if (isLoading) return;
        if (!user || (user.role !== "admin" && user.role !== "moderator")) {
            window.location.href = "/";
        } else {
            fetchData();
        }
    }, [user, isLoading, fetchData]);

    const reviewDocument = async (documentId: string, status: string) => {
        try {
            const res = await fetch(`${API_URL}/moderator/documents/${documentId}/moderate`, {
                method: "POST",
                headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: status, reason: status === "PUBLISHED" ? "Duyệt" : "Không đạt yêu cầu" })
            });
            if (res.ok) {
                setNotification({ type: "success", text: status === "PUBLISHED" ? "Đã phê duyệt tài liệu." : "Đã từ chối tài liệu." });
                fetchData();
            } else {
                const err = await res.json();
                setNotification({ type: "error", text: formatError(err.detail) || "Lỗi thao tác phê duyệt." });
            }
        } catch (err: any) { 
            setNotification({ type: "error", text: "Lỗi kết nối máy chủ." });
        }
    };

    const resolveReport = async (reportId: string, action: string) => {
        try {
            const res = await fetch(`${API_URL}/admin/reports/${reportId}/resolve`, {
                method: "POST",
                headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({ action })
            });
            if (res.ok) {
                setNotification({ type: "success", text: "Báo cáo đã được xử lý." });
                fetchData();
            } else {
                const err = await res.json();
                setNotification({ type: "error", text: formatError(err.detail) || "Lỗi xử lý báo cáo." });
            }
        } catch (err: any) { 
            setNotification({ type: "error", text: "Lỗi kết nối máy chủ." });
        }
    };

    if (isLoading || !user) {
        return (
            <div className="min-h-[80vh] flex items-center justify-center">
                <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
            </div>
        );
    }

    const tabs = [
        { id: "documents", label: "Phê duyệt tài liệu", icon: BookOpen, count: pendingDocuments.length },
        { id: "reports", label: "Báo cáo vi phạm", icon: AlertTriangle, count: reports.length },
        { id: "logs", label: "Lịch sử thao tác", icon: Clock, count: 0 },
    ];

    return (
        <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-10 font-sans text-black selection:bg-black selection:text-white">
            {notification && (
                <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
                    <Notification type={notification.type} message={notification.text} />
                </div>
            )}

            {/* Header - Matching Author Dashboard exactly */}
            <div 
                className="mb-10 border-b border-zinc-100 pb-10 transition-all duration-700"
                style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
            >
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
                    <div className="space-y-3">
                        <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
                            Kiểm duyệt viên
                        </h1>
                        <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
                            Moderation Center <ShieldCheck className="w-3.5 h-3.5 text-zinc-100" />
                        </p>
                    </div>
                    
                    <button 
                        onClick={fetchData}
                        disabled={isRefreshing}
                        className="h-14 px-12 bg-black text-white text-[11px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all active:scale-95 flex items-center gap-4 rounded-none shadow-xl shadow-black/5"
                    >
                        {isRefreshing ? <Loader2 className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />}
                        Làm mới hàng chờ
                    </button>
                </div>
            </div>

            <div className="grid lg:grid-cols-12 gap-12">
                {/* Sidebar Navigation - Matching Author Dashboard layout */}
                <aside 
                    className="lg:col-span-3 space-y-10 transition-all duration-700 delay-150"
                    style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
                >
                    <div className="space-y-6">
                        <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-[0.2em] px-1">
                            <Filter className="w-4 h-4 text-zinc-300" /> Điều phối hệ thống
                        </div>
                        <nav className="flex flex-col gap-1">
                            {tabs.map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as ModTab)}
                                    className={`flex items-center justify-between px-6 py-4 text-[11px] font-bold uppercase tracking-widest transition-all border ${
                                        activeTab === tab.id
                                            ? "bg-black text-white border-black"
                                            : "bg-white text-zinc-400 border-zinc-100 hover:bg-zinc-50 hover:text-black"
                                    }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <tab.icon className="w-4 h-4" /> 
                                        <span>{tab.label}</span>
                                        {tab.count > 0 && (
                                            <span className={`ml-2 px-1.5 py-0.5 text-[9px] ${activeTab === tab.id ? "bg-white text-black" : "bg-zinc-50 text-zinc-400"}`}>
                                                {tab.count}
                                            </span>
                                        )}
                                    </div>
                                    <ChevronRight className={`w-3.5 h-3.5 transition-transform ${activeTab === tab.id ? "rotate-90" : ""}`} />
                                </button>
                            ))}
                        </nav>
                    </div>

                    <div className="p-8 border border-zinc-100 bg-zinc-50/30 space-y-4">
                        <div className="text-[10px] font-bold text-black uppercase tracking-widest mb-2">Quy tắc cộng đồng</div>
                        <p className="text-[10px] font-medium text-zinc-400 leading-relaxed italic">
                            "Luôn giữ vững sự minh bạch và công tâm trong quá trình kiểm duyệt tri thức."
                        </p>
                    </div>
                </aside>

                {/* Main Content Area - Matching Author Dashboard patterns */}
                <main 
                    className="lg:col-span-9 transition-all duration-700 delay-300"
                    style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
                >
                    {activeTab === "documents" && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <div className="flex items-center gap-6">
                                <h2 className="text-sm font-bold text-black tracking-widest uppercase">Phê duyệt bản thảo mới</h2>
                                <div className="flex-1 h-px bg-zinc-50" />
                                <span className="text-[11px] font-bold text-zinc-300 uppercase tracking-[0.2em]">{pendingDocuments.length} YÊU CẦU</span>
                            </div>

                            {pendingDocuments.length === 0 ? (
                                <div className="py-48 text-center border border-dashed border-zinc-200 bg-zinc-50/20">
                                    <BookOpen className="w-16 h-16 text-zinc-100 mx-auto mb-10 stroke-[1]" />
                                    <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Hiện tại hàng chờ đang trống</p>
                                </div>
                            ) : (
                                <div className="grid gap-6">
                                    {pendingDocuments.map((doc: any) => (
                                        <div
                                            key={doc._id}
                                            className="group flex flex-col p-10 border border-zinc-100 hover:border-black transition-all duration-700 bg-white space-y-10"
                                        >
                                            <div className="flex flex-col md:flex-row md:items-start justify-between gap-8">
                                                <div className="flex items-center gap-8 min-w-0">
                                                    <div className="w-14 h-14 bg-zinc-50 border border-zinc-100 flex items-center justify-center shrink-0 group-hover:bg-black group-hover:border-black transition-all duration-500">
                                                        <BookOpen className="w-7 h-7 text-zinc-200 group-hover:text-white transition-all" />
                                                    </div>
                                                    <div className="min-w-0 space-y-2">
                                                        <h3 className="font-bold text-xl text-black truncate tracking-tight">{doc.title}</h3>
                                                        <div className="flex items-center gap-5 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                                                            <span className="flex items-center gap-2 text-black"><User className="w-3 h-3" /> {doc.author_name}</span>
                                                            <div className="w-1 h-1 bg-zinc-100" />
                                                            <span className="flex items-center gap-2"><Clock className="w-3 h-3" /> {new Date(doc.created_at).toLocaleDateString("vi-VN")}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-4 shrink-0">
                                                    <button className="h-10 px-6 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all">Kiểm tra nội dung</button>
                                                </div>
                                            </div>

                                            <div className="bg-zinc-50/50 p-6 border-l-[4px] border-zinc-100 italic text-[13px] text-zinc-400 font-medium leading-relaxed">
                                                "{doc.description || "Tác phẩm này chưa có mô tả chi tiết từ tác giả."}"
                                            </div>

                                            <div className="flex flex-col md:flex-row items-center justify-between gap-6 pt-8 border-t border-zinc-50">
                                                <div className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Hành động kiểm định:</div>
                                                <div className="flex items-center gap-3 w-full md:w-auto">
                                                    <button 
                                                        onClick={() => reviewDocument(doc._id, "REJECTED")}
                                                        className="flex-1 md:flex-none h-12 px-10 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-red-600 hover:border-red-600 transition-all"
                                                    >
                                                        Từ chối
                                                    </button>
                                                    <button 
                                                        onClick={() => reviewDocument(doc._id, "PUBLISHED")}
                                                        className="flex-1 md:flex-none h-12 px-12 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-[0.98]"
                                                    >
                                                        Phê duyệt xuất bản
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === "reports" && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                             <div className="flex items-center gap-6">
                                <h2 className="text-sm font-bold text-black tracking-widest uppercase">Báo cáo vi phạm cộng đồng</h2>
                                <div className="flex-1 h-px bg-zinc-50" />
                                <span className="text-[11px] font-bold text-zinc-300 uppercase tracking-[0.2em]">{reports.length} PHẢN HỒI</span>
                            </div>

                            <div className="bg-white border border-zinc-100 overflow-hidden shadow-sm">
                                <div className="overflow-x-auto">
                                    <table className="w-full text-left text-xs border-collapse">
                                        <thead>
                                            <tr className="bg-zinc-50/50 border-b border-zinc-100 text-zinc-300 text-[9px] font-bold uppercase tracking-[0.2em]">
                                                <th className="px-10 py-6">Đối tượng vi phạm</th>
                                                <th className="px-10 py-6">Lý do & Chi tiết</th>
                                                <th className="px-10 py-6">Ngày gửi</th>
                                                <th className="px-10 py-6 text-right">Xử lý</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-zinc-50">
                                            {reports.length === 0 ? (
                                                <tr>
                                                    <td colSpan={4} className="px-10 py-32 text-center text-[10px] font-bold text-zinc-200 uppercase tracking-widest">Không có báo cáo vi phạm nào</td>
                                                </tr>
                                            ) : (
                                                reports.map((r: any) => (
                                                    <tr key={r._id} className="hover:bg-zinc-50/20 transition-colors group">
                                                        <td className="px-10 py-8">
                                                            <div className="flex items-center gap-4">
                                                                <div className="w-10 h-10 bg-zinc-50 flex items-center justify-center border border-zinc-50 group-hover:bg-black group-hover:text-white transition-all">
                                                                    <AlertTriangle className="w-4 h-4 text-zinc-200 group-hover:text-white" />
                                                                </div>
                                                                <div className="flex flex-col gap-1">
                                                                    <span className="font-bold text-black uppercase tracking-widest text-[10px]">{r.item_type}</span>
                                                                    <span className="text-[9px] font-bold text-zinc-300 truncate max-w-[120px]">{r.item_id}</span>
                                                                </div>
                                                            </div>
                                                        </td>
                                                        <td className="px-10 py-8">
                                                            <div className="space-y-1.5">
                                                                <p className="font-bold text-black text-[11px] leading-tight">{r.reason}</p>
                                                                <p className="text-[10px] text-zinc-400 font-medium italic line-clamp-1 italic">"{r.description}"</p>
                                                            </div>
                                                        </td>
                                                        <td className="px-10 py-8">
                                                            <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                                                                {new Date(r.created_at).toLocaleDateString("vi-VN")}
                                                            </span>
                                                        </td>
                                                        <td className="px-10 py-8 text-right">
                                                            <div className="flex justify-end gap-3">
                                                                <button 
                                                                    onClick={() => resolveReport(r._id, "KEEP")}
                                                                    className="h-9 px-6 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all"
                                                                >
                                                                    Bỏ qua
                                                                </button>
                                                                <button 
                                                                    onClick={() => resolveReport(r._id, "TAKEDOWN")}
                                                                    className="h-9 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-[0.98]"
                                                                >
                                                                    Gỡ bỏ
                                                                </button>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === "logs" && (
                        <div className="animate-in slide-in-from-bottom-4 duration-700 space-y-10">
                             <div className="flex items-center gap-6">
                                <h2 className="text-sm font-bold text-black tracking-widest uppercase">Lịch sử thao tác hệ thống</h2>
                                <div className="flex-1 h-px bg-zinc-50" />
                            </div>
                            <div className="py-48 text-center border border-dashed border-zinc-200 bg-zinc-50/20">
                                <Clock className="w-16 h-16 text-zinc-100 mx-auto mb-10 stroke-[1]" />
                                <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Nhật ký đang được lưu trữ định kỳ</p>
                            </div>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
