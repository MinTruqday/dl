"use client";

import { useEffect, useState, useCallback } from "react";
import { getApprovalQueueAPI, getReportsAPI, moderateDocumentAPI, resolveReportAPI, getModeratorActivityAPI } from "@/services/moderation.service";
import { triggerCollectionAPI, getCollectorStatsAPI } from "@/services/administration.service";
import { 
    ShieldCheck, 
    AlertTriangle, 
    CheckCircle2, 
    XCircle, 
    Clock, 
    User as UserIcon, 
    BookOpen,
    Eye,
    Loader2,
    Search,
    Filter,
    ChevronRight,
    ArrowRight,
    MessageSquare,
    Zap,
    Award,
    Activity,
    ShieldAlert,
    DownloadCloud,
    Database,
    Link as LinkIcon,
    Globe
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { useRouter, useSearchParams } from "next/navigation";

type ModTab = "documents" | "reports" | "logs" | "collector";

export default function Moderation({ initialTab }: { initialTab?: ModTab }) {
    const { user, isLoading: authLoading } = useAuth() as any;
    const router = useRouter();
    const searchParams = useSearchParams();
    const tabFromUrl = searchParams.get("tab") as ModTab;
    
    const { showToast } = useToast();
    const [activeTab, setActiveTab] = useState<ModTab>(initialTab || tabFromUrl || "documents");
    const [pendingDocuments, setPendingDocuments] = useState<any[]>([]);
    const [reports, setReports] = useState<any[]>([]);
    const [activityLogs, setActivityLogs] = useState<any[]>([]);
    const [collectorStats, setCollectorStats] = useState<any>(null);
    const [collectionForm, setCollectionForm] = useState({ source: "AnnaArchive", url: "", index_type: "list", target_class: "10" });
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
    const [visible, setVisible] = useState(false);

    const fetchData = useCallback(async () => {
        setIsRefreshing(true);
        try {
            const [docsRes, reportsRes, logsRes] = await Promise.all([
                getApprovalQueueAPI(),
                getReportsAPI(),
                getModeratorActivityAPI()
            ]);
            
            setPendingDocuments(docsRes.data || docsRes || []);
            setReports(reportsRes.data || reportsRes || []);
            setActivityLogs(logsRes.data || logsRes || []);

            try {
                const statsRes = await getCollectorStatsAPI();
                setCollectorStats(statsRes.data || statsRes);
            } catch (err) {
                console.error("Failed to fetch collector stats:", err);
            }
        } catch (err: any) {
            showToast("Không thể kết nối hệ thống kiểm duyệt.", "error");
        } finally {
            setIsRefreshing(false);
            setIsLoading(false);
            requestAnimationFrame(() => setVisible(true));
        }
    }, []);

    useEffect(() => {
        if (!authLoading && user) {
            if (user.role !== "admin" && user.role !== "moderator") {
                router.push("/");
            } else {
                fetchData();
            }
        }
    }, [user, authLoading, fetchData, router]);

    useEffect(() => {
        if (tabFromUrl && tabFromUrl !== activeTab) {
            setActiveTab(tabFromUrl);
        }
    }, [tabFromUrl, activeTab]);

    const handleTabChange = (tab: ModTab) => {
        setActiveTab(tab);
        router.push(`/moderator/${tab}`);
    };

    const reviewDocument = async (documentId: string, status: string) => {
        try {
            await moderateDocumentAPI(documentId, status, status === "PUBLISHED" ? "Đã phê duyệt dựa trên tiêu chuẩn nội dung." : "Nội dung không đáp ứng yêu cầu cộng đồng.");
            showToast(status === "PUBLISHED" ? "Đã phê duyệt tài liệu thành công." : "Đã từ chối tài liệu.", "success");
            fetchData();
        } catch (err: any) {
            showToast(err.message || "Lỗi thao tác phê duyệt.", "error");
        }
    };

    const resolveReport = async (reportId: string, action: string) => {
        try {
            await resolveReportAPI(reportId, action);
            showToast("Báo cáo vi phạm đã được xử lý.", "success");
            fetchData();
        } catch (err: any) {
            showToast(err.message || "Lỗi xử lý báo cáo.", "error");
        }
    };

    const handleTriggerCollection = async () => {
        try {
            setIsRefreshing(true);
            await triggerCollectionAPI(collectionForm.source, collectionForm.url, collectionForm.index_type, collectionForm.target_class);
            showToast("Đã kích hoạt tiến trình thu thập thành công.", "success");
            setCollectionForm({ ...collectionForm, url: "" });
            fetchData();
        } catch (err: any) {
            showToast(err.message || "Không thể kích hoạt tiến trình thu thập.", "error");
        } finally {
            setIsRefreshing(false);
        }
    };

    if (authLoading || isLoading) {
        return (
            <div className="min-h-[80vh] flex items-center justify-center bg-white">
                <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
            </div>
        );
    }

    return (
        <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
            

            <div 
                className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-300"
                style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
            >
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
                    <div className="space-y-4">
                        <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
                            {activeTab === "documents" ? "Duyệt bản thảo" : 
                             activeTab === "reports" ? "Báo cáo vi phạm" : 
                             activeTab === "collector" ? "Thu thập dữ liệu" : "Nhật ký điều hành"}
                        </h1>
                        <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
                            Hệ thống kiểm soát nội dung DocLib <ShieldCheck className="w-3.5 h-3.5 text-zinc-100" />
                        </p>
                    </div>
                    
                    <div className="flex items-center gap-4">
                        <div className="flex bg-zinc-50 p-1 rounded-sm border border-zinc-100">
                            {[
                                { id: "documents", label: "Tài liệu", icon: BookOpen },
                                { id: "reports", label: "Báo cáo", icon: ShieldAlert },
                                { id: "collector", label: "Thu thập", icon: DownloadCloud },
                                { id: "logs", label: "Nhật ký", icon: Activity },
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => handleTabChange(tab.id as ModTab)}
                                    className={`flex items-center gap-2 px-6 py-2.5 text-[10px] font-bold uppercase tracking-widest transition-all rounded-sm ${
                                        activeTab === tab.id ? "bg-white text-black " : "text-zinc-400 hover:text-black"
                                    }`}
                                >
                                    <tab.icon className="w-3.5 h-3.5" />
                                    {tab.label}
                                </button>
                            ))}
                        </div>
                        <button 
                            onClick={fetchData}
                            disabled={isRefreshing}
                            className="h-12 px-8 bg-black text-white text-[10px] font-bold tracking-widest uppercase hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center gap-3 rounded-sm disabled:opacity-50"
                        >
                            {isRefreshing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                            Làm mới
                        </button>
                    </div>
                </div>
            </div>

            <div 
                className="transition-all duration-300 delay-75"
                style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
            >
                {activeTab === "documents" && (
                    <div className="space-y-10 animate-in fade-in duration-300">
                        <div className="flex items-center justify-between px-2">
                            <h2 className="text-[11px] font-bold text-black tracking-[0.2em] uppercase">Hàng đợi phê duyệt ({pendingDocuments.length})</h2>
                            <div className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Sắp xếp theo: Mới nhất</div>
                        </div>

                        {pendingDocuments.length === 0 ? (
                            <div className="py-48 text-center border border-dashed border-zinc-200 bg-zinc-50/10 rounded-sm">
                                <BookOpen className="w-16 h-16 text-zinc-100 mx-auto mb-8 stroke-[1]" />
                                <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Hàng chờ hiện đang trống</p>
                            </div>
                        ) : (
                            <div className="grid gap-6">
                                {pendingDocuments.map((doc: any) => (
                                    <div
                                        key={doc._id}
                                        className="group flex flex-col p-10 border border-zinc-100 hover:border-black transition-all duration-300 bg-white space-y-10 rounded-sm"
                                    >
                                        <div className="flex flex-col md:flex-row md:items-start justify-between gap-10">
                                            <div className="flex items-center gap-8 min-w-0">
                                                <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 flex items-center justify-center shrink-0 group-hover:bg-black transition-all duration-300 rounded-sm">
                                                    <BookOpen className="w-8 h-8 text-zinc-200 group-hover:text-white transition-all" />
                                                </div>
                                                <div className="min-w-0 space-y-3">
                                                    <h3 className="font-bold text-2xl text-black truncate tracking-tighter">{doc.title}</h3>
                                                    <div className="flex flex-wrap items-center gap-6 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                                                        <span className="flex items-center gap-2 text-black"><UserIcon className="w-3.5 h-3.5" /> {doc.author_name}</span>
                                                        <span className="flex items-center gap-2"><Clock className="w-3.5 h-3.5" /> {new Date(doc.created_at).toLocaleDateString("vi-VN")}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-4 shrink-0">
                                                <button 
                                                    onClick={() => window.open(`/documents/viewer/${doc._id}`, '_blank')}
                                                    className="h-12 px-8 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all rounded-sm flex items-center gap-2"
                                                >
                                                    <Eye className="w-4 h-4" /> Đọc nội dung
                                                </button>
                                            </div>
                                        </div>

                                        <div className="bg-zinc-50/30 p-8 border-l-[3px] border-zinc-100 text-[13px] text-zinc-500 font-medium leading-relaxed italic rounded-sm">
                                            "{doc.description || "Tác phẩm này chưa được tác giả cung cấp mô tả chi tiết."}"
                                        </div>

                                        <div className="flex flex-col md:flex-row items-center justify-between gap-8 pt-10 border-t border-zinc-50">
                                            <div className="flex items-center gap-4">
                                                <div className="w-2 h-2 bg-zinc-200 rounded-full" />
                                                <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest italic">Yêu cầu xác thực nội dung tri thức</span>
                                            </div>
                                            <div className="flex items-center gap-4 w-full md:w-auto">
                                                <button 
                                                    onClick={() => reviewDocument(doc._id, "REJECTED")}
                                                    className="flex-1 md:flex-none h-14 px-12 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black hover:border-black transition-all rounded-sm"
                                                >
                                                    Từ chối
                                                </button>
                                                <button 
                                                    onClick={() => reviewDocument(doc._id, "PUBLISHED")}
                                                    className="flex-1 md:flex-none h-14 px-16 bg-black text-white text-[10px] font-bold uppercase tracking-[0.2em] hover:bg-zinc-800 transition-all active:scale-[0.98] rounded-sm"
                                                >
                                                    Phê duyệt
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
                    <div className="space-y-10 animate-in fade-in duration-300">
                        <div className="flex items-center justify-between px-2">
                            <h2 className="text-[11px] font-bold text-black tracking-[0.2em] uppercase">Báo cáo vi phạm ({reports.length})</h2>
                        </div>

                        <div className="bg-white border border-zinc-100 rounded-sm overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-xs border-collapse">
                                    <thead>
                                        <tr className="bg-zinc-50/50 border-b border-zinc-100 text-zinc-300 text-[9px] font-bold uppercase tracking-[0.2em]">
                                            <th className="px-10 py-6">Đối tượng vi phạm</th>
                                            <th className="px-10 py-6">Nội dung báo cáo</th>
                                            <th className="px-10 py-6">Thời gian</th>
                                            <th className="px-10 py-6 text-right">Thao tác</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-zinc-50">
                                        {reports.length === 0 ? (
                                            <tr>
                                                <td colSpan={4} className="px-10 py-48 text-center text-[10px] font-bold text-zinc-200 uppercase tracking-widest italic">Không có dữ liệu vi phạm</td>
                                            </tr>
                                        ) : (
                                            reports.map((r: any) => (
                                                <tr key={r._id} className="hover:bg-zinc-50/20 transition-all duration-300 group">
                                                    <td className="px-10 py-10">
                                                        <div className="flex items-center gap-6">
                                                            <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center border border-zinc-100 group-hover:bg-black transition-all duration-300 rounded-sm">
                                                                <AlertTriangle className="w-5 h-5 text-zinc-200 group-hover:text-white" />
                                                            </div>
                                                            <div className="flex flex-col gap-1.5">
                                                                <span className="font-bold text-black uppercase tracking-widest text-[10px]">{r.item_type}</span>
                                                                <span className="text-[9px] font-bold text-zinc-200 truncate max-w-[150px] tracking-tight">{r.item_id}</span>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-10 py-10">
                                                        <div className="space-y-2 max-w-md">
                                                            <p className="font-bold text-black text-[11px] leading-tight uppercase tracking-tight">{r.reason}</p>
                                                            <p className="text-[10px] text-zinc-400 font-medium italic line-clamp-1">"{r.description}"</p>
                                                        </div>
                                                    </td>
                                                    <td className="px-10 py-10">
                                                        <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                                                            {new Date(r.created_at).toLocaleDateString("vi-VN")}
                                                        </span>
                                                    </td>
                                                    <td className="px-10 py-10 text-right">
                                                        <div className="flex justify-end gap-3">
                                                            <button 
                                                                onClick={() => resolveReport(r._id, "KEEP")}
                                                                className="h-10 px-6 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black hover:border-black transition-all rounded-sm"
                                                            >
                                                                Bỏ qua
                                                            </button>
                                                            <button 
                                                                onClick={() => resolveReport(r._id, "TAKEDOWN")}
                                                                className="h-10 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all rounded-sm"
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

                {activeTab === "collector" && (
                    <div className="space-y-12 animate-in fade-in duration-300">
                        <div className="grid md:grid-cols-3 gap-8">
                            <div className="md:col-span-1 space-y-10">
                                <div className="space-y-4">
                                    <h2 className="text-[11px] font-bold text-black tracking-[0.2em] uppercase px-2">Cấu hình thu thập</h2>
                                    <div className="bg-white border border-zinc-100 p-8 space-y-8 rounded-sm">
                                        <div className="space-y-4">
                                            <label className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Nguồn dữ liệu</label>
                                            <select 
                                                value={collectionForm.source}
                                                onChange={(e) => setCollectionForm({...collectionForm, source: e.target.value})}
                                                className="w-full h-12 px-4 bg-zinc-50 border border-zinc-100 text-[11px] font-bold uppercase tracking-widest outline-none focus:border-black transition-all rounded-sm"
                                            >
                                                <option value="AnnaArchive">Anna Archive</option>
                                                <option value="NXBST">NXB Sự Thật</option>
                                                <option value="NXBGDC">NXB Giáo Dục</option>
                                            </select>
                                        </div>

                                        {collectionForm.source === "AnnaArchive" && (
                                            <>
                                                <div className="space-y-4">
                                                    <label className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Loại chỉ mục</label>
                                                    <select 
                                                        value={collectionForm.index_type}
                                                        onChange={(e) => setCollectionForm({...collectionForm, index_type: e.target.value})}
                                                        className="w-full h-12 px-4 bg-zinc-50 border border-zinc-100 text-[11px] font-bold uppercase tracking-widest outline-none focus:border-black transition-all rounded-sm"
                                                    >
                                                        <option value="list">Danh sách (List)</option>
                                                        <option value="detail">Chi tiết (Detail)</option>
                                                    </select>
                                                </div>
                                                <div className="space-y-4">
                                                    <label className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">URL mục tiêu</label>
                                                    <input 
                                                        type="text"
                                                        value={collectionForm.url}
                                                        onChange={(e) => setCollectionForm({...collectionForm, url: e.target.value})}
                                                        placeholder="Nhập đường dẫn URL"
                                                        className="w-full h-12 px-4 bg-zinc-50 border border-zinc-100 text-[11px] font-medium outline-none focus:border-black transition-all rounded-sm"
                                                    />
                                                </div>
                                            </>
                                        )}

                                        {collectionForm.source === "NXBST" && (
                                            <div className="space-y-4">
                                                <label className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">URL chi tiết (Tùy chọn)</label>
                                                <input 
                                                    type="text"
                                                    value={collectionForm.url}
                                                    onChange={(e) => setCollectionForm({...collectionForm, url: e.target.value})}
                                                    placeholder="Để trống để chạy toàn bộ danh sách"
                                                    className="w-full h-12 px-4 bg-zinc-50 border border-zinc-100 text-[11px] font-medium outline-none focus:border-black transition-all rounded-sm"
                                                />
                                            </div>
                                        )}

                                        {collectionForm.source === "NXBGDC" && (
                                            <div className="space-y-4">
                                                <label className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Khối lớp (Target Class)</label>
                                                <select 
                                                    value={collectionForm.target_class}
                                                    onChange={(e) => setCollectionForm({...collectionForm, target_class: e.target.value})}
                                                    className="w-full h-12 px-4 bg-zinc-50 border border-zinc-100 text-[11px] font-bold uppercase tracking-widest outline-none focus:border-black transition-all rounded-sm"
                                                >
                                                    {[1,2,3,4,5,6,7,8,9,10,11,12].map(c => (
                                                        <option key={c} value={String(c)}>Lớp {c}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        )}

                                        <button 
                                            onClick={handleTriggerCollection}
                                            disabled={isRefreshing}
                                            className="w-full h-14 bg-black text-white text-[10px] font-bold uppercase tracking-[0.2em] hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center justify-center gap-3 rounded-sm disabled:opacity-50"
                                        >
                                            <DownloadCloud className="w-4 h-4" /> Bắt đầu thu thập
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <div className="md:col-span-2 space-y-10">
                                <div className="space-y-4">
                                    <h2 className="text-[11px] font-bold text-black tracking-[0.2em] uppercase px-2">Trạng thái hệ thống thu thập</h2>
                                    <div className="grid grid-cols-2 gap-6">
                                        <div className="bg-white border border-zinc-100 p-8 rounded-sm space-y-4">
                                            <div className="flex items-center gap-3 text-zinc-300">
                                                <Database className="w-4 h-4" />
                                                <span className="text-[10px] font-bold uppercase tracking-widest">Tổng tài liệu thu thập</span>
                                            </div>
                                            <p className="text-4xl font-bold tracking-tighter text-black">{collectorStats?.total_documents_collected || 0}</p>
                                        </div>
                                        <div className="bg-white border border-zinc-100 p-8 rounded-sm space-y-4">
                                            <div className="flex items-center gap-3 text-zinc-300">
                                                <Activity className="w-4 h-4" />
                                                <span className="text-[10px] font-bold uppercase tracking-widest">Trạng thái Worker</span>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <div className="w-2.5 h-2.5 bg-zinc-400 rounded-full animate-pulse" />
                                                <p className="text-xl font-bold tracking-tight text-black uppercase">Đang hoạt động</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <h2 className="text-[11px] font-bold text-black tracking-[0.2em] uppercase px-2">Nguồn dữ liệu sẵn dụng</h2>
                                    <div className="grid gap-4">
                                        {[
                                            { name: "Anna Archive", status: "Hoạt động", type: "Thư viện mở", icon: Globe },
                                            { name: "NXB Sự Thật", status: "Hoạt động", type: "Chính trị - Pháp luật", icon: ShieldCheck },
                                            { name: "NXB Giáo Dục", status: "Hoạt động", type: "Sách giáo khoa", icon: BookOpen },
                                        ].map((source, i) => (
                                            <div key={i} className="flex items-center justify-between p-8 border border-zinc-100 bg-white rounded-sm hover:border-black transition-all duration-300">
                                                <div className="flex items-center gap-6">
                                                    <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center border border-zinc-100 rounded-sm">
                                                        <source.icon className="w-5 h-5 text-zinc-300" />
                                                    </div>
                                                    <div className="space-y-1">
                                                        <h4 className="font-bold text-black uppercase tracking-tight text-sm">{source.name}</h4>
                                                        <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{source.type}</p>
                                                    </div>
                                                </div>
                                                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                                                    <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full" />
                                                    {source.status}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === "logs" && (
                    <div className="space-y-10 animate-in fade-in duration-300">
                        <div className="flex items-center justify-between px-2">
                            <h2 className="text-[11px] font-bold text-black tracking-[0.2em] uppercase">Nhật ký hoạt động ({activityLogs.length})</h2>
                        </div>

                        {activityLogs.length === 0 ? (
                            <div className="py-48 text-center border border-dashed border-zinc-200 bg-zinc-50/10 rounded-sm">
                                <Activity className="w-16 h-16 text-zinc-100 mx-auto mb-8 stroke-[1]" />
                                <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Nhật ký hiện đang trống</p>
                            </div>
                        ) : (
                            <div className="grid gap-4">
                                {activityLogs.map((log: any, idx: number) => (
                                    <div key={idx} className="flex items-center justify-between p-8 border border-zinc-100 bg-white hover:border-black transition-all duration-300 rounded-sm group">
                                        <div className="flex items-center gap-8">
                                            <div className="w-12 h-12 border border-zinc-50 flex items-center justify-center font-bold text-[13px] text-zinc-100 group-hover:text-black transition-all">
                                                {idx + 1}
                                            </div>
                                            <div className="space-y-1.5">
                                                <p className="text-sm font-bold text-black tracking-tight uppercase group-hover:translate-x-1 transition-transform duration-300">{log.action || "Thao tác điều hành"}</p>
                                                <div className="flex items-center gap-4 text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                                                    <span>{log.target_type}: {log.target_id}</span>
                                                    <div className="w-1 h-1 bg-zinc-100 rounded-full" />
                                                    <span>{new Date(log.created_at).toLocaleString("vi-VN")}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-[10px] font-bold text-zinc-200 group-hover:text-black uppercase tracking-widest">Hoàn tất</div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
