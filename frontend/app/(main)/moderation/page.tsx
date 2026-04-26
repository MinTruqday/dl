"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/app/lib/api";
import { 
    ShieldCheck, 
    AlertTriangle, 
    CheckCircle2, 
    XCircle, 
    Clock, 
    User, 
    BookOpen,
    Eye,
    MoreHorizontal
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/app/contexts/AuthContext";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function ModerationDashboard() {
    const { user, isLoading } = useAuth();
    const [pendingBooks, setPendingBooks] = useState<any[]>([]);
    const [reports, setReports] = useState<any[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);

    const API_URL = process.env.NEXT_PUBLIC_API_URL;

    useEffect(() => {
        if (isLoading) return;
        if (!user || (user.role !== "admin" && user.role !== "moderator")) {
            window.location.href = "/";
        } else {
            fetchPendingBooks();
            fetchReports();
        }
    }, [user, isLoading]);

    const fetchPendingBooks = async () => {
        const res = await fetch(`${API_URL}/moderation/books/pending`, { headers: { 'Authorization': `Bearer ${getToken()}` }});
        if (res.ok) setPendingBooks(await res.json());
    };

    const fetchReports = async () => {
        const res = await fetch(`${API_URL}/moderation/reports`, { headers: { 'Authorization': `Bearer ${getToken()}` }});
        if (res.ok) setReports(await res.json());
    };

    const reviewBook = async (bookId: string, status: string, reason: string = "") => {
        setIsProcessing(true);
        const res = await fetch(`${API_URL}/moderation/books/${bookId}/review`, {
            method: "POST",
            headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ status, reason })
        });
        if (res.ok) {
            fetchPendingBooks();
        }
        setIsProcessing(false);
    };

    const resolveReport = async (reportId: string, action: string) => {
        setIsProcessing(true);
        const res = await fetch(`${API_URL}/moderation/reports/${reportId}/resolve`, {
            method: "POST",
            headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        if (res.ok) {
            fetchReports();
        }
        setIsProcessing(false);
    };

    if (isLoading || !user) return <div className="p-8 text-center text-muted-foreground animate-pulse">Đang tải dữ liệu kiểm duyệt</div>;

    return (
        <div className="container max-w-7xl mx-auto py-10 px-6 font-sans">
            <header className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h1 className="text-4xl font-black tracking-tighter text-foreground italic">Trung tâm Kiểm duyệt</h1>
                    <p className="text-muted-foreground mt-2 text-sm font-medium">DocLib Moderation & Quality Control</p>
                </div>
                <div className="bg-muted px-4 py-2 rounded-sm border border-border flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-foreground" />
                    <span className="text-[10px] font-bold tracking-widest">Vai trò: {user.role}</span>
                </div>
            </header>

            <Tabs defaultValue="books" className="space-y-8">
                <TabsList className="bg-muted/50 p-1 rounded-sm border border-border inline-flex h-auto w-full md:w-auto overflow-x-auto whitespace-nowrap">
                    <TabsTrigger value="books" className="gap-2 px-6 py-2.5 data-[state=active]:bg-white data-[state=active]: transition-all duration-200">
                        <Clock className="w-4 h-4" /> Duyệt tác phẩm ({pendingBooks.length})
                    </TabsTrigger>
                    <TabsTrigger value="reports" className="gap-2 px-6 py-2.5 data-[state=active]:bg-white data-[state=active]: transition-all duration-200">
                        <AlertTriangle className="w-4 h-4" /> Báo cáo vi phạm ({reports.length})
                    </TabsTrigger>
                </TabsList>

                {}
                <TabsContent value="books" className="animate-in fade-in slide-in-from-bottom-2 duration-500">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {pendingBooks.length === 0 ? (
                            <div className="lg:col-span-2 py-20 text-center border-2 border-dashed border-border rounded-sm">
                                <BookOpen className="w-8 h-8 mx-auto text-muted-foreground opacity-20 mb-4" />
                                <p className="text-sm font-bold text-muted-foreground tracking-widest">Hàng đợi đang trống</p>
                            </div>
                        ) : (
                            pendingBooks.map((book) => (
                                <div key={book._id} className="bg-white border border-border rounded-sm overflow-hidden flex flex-col group hover:border-foreground transition-colors duration-300">
                                    <div className="p-6 flex-1">
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex-1">
                                                <h3 className="text-lg font-black tracking-tight leading-tight mb-2">{book.title}</h3>
                                                <div className="flex items-center gap-4 text-[10px] font-bold text-muted-foreground tracking-widest mb-4">
                                                    <span className="flex items-center gap-1"><User className="w-3 h-3" /> {book.author_name || "Unknown"}</span>
                                                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(book.created_at).toLocaleDateString("vi-VN")}</span>
                                                </div>
                                                <p className="text-sm text-muted-foreground line-clamp-3 leading-relaxed">
                                                    {book.description || "Không có mô tả."}
                                                </p>
                                            </div>
                                            <div className="w-20 h-28 bg-muted rounded-sm flex-shrink-0 border border-border overflow-hidden">
                                                {book.cover_url ? (
                                                    <img src={book.cover_url} alt={book.title} className="w-full h-full object-cover" />
                                                ) : (
                                                    <div className="w-full h-full flex items-center justify-center text-muted-foreground opacity-20">
                                                        <BookOpen className="w-8 h-8" />
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="p-4 bg-muted/20 border-t border-border flex items-center justify-between gap-2">
                                        <Button variant="outline" size="sm" className="h-9 px-4 rounded-none text-[10px] font-bold tracking-widest gap-2">
                                            <Eye className="w-3.5 h-3.5" /> Xem chi tiết
                                        </Button>
                                        <div className="flex gap-2">
                                            <Button 
                                                variant="secondary" 
                                                size="sm" 
                                                className="h-9 px-4 rounded-none text-[10px] font-bold tracking-widest gap-2 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border-emerald-100"
                                                onClick={() => reviewBook(book._id, "PUBLISHED")}
                                                disabled={isProcessing}
                                            >
                                                <CheckCircle2 className="w-3.5 h-3.5" /> Duyệt
                                            </Button>
                                            <Button 
                                                variant="destructive" 
                                                size="sm" 
                                                className="h-9 px-4 rounded-none text-[10px] font-bold tracking-widest gap-2"
                                                onClick={() => reviewBook(book._id, "REJECTED")}
                                                disabled={isProcessing}
                                            >
                                                <XCircle className="w-3.5 h-3.5" /> Từ chối
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </TabsContent>

                {}
                <TabsContent value="reports" className="animate-in fade-in slide-in-from-bottom-2 duration-500">
                    <div className="bg-white border border-border rounded-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm whitespace-nowrap">
                                <thead>
                                    <tr className="text-muted-foreground border-b border-border bg-muted/10 font-bold tracking-widest text-[10px]">
                                        <th className="p-4 font-medium">Đối tượng báo cáo</th>
                                        <th className="p-4 font-medium">Lý do</th>
                                        <th className="p-4 font-medium">Ngày báo cáo</th>
                                        <th className="p-4 font-medium text-right">Thao tác</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {reports.length === 0 ? (
                                        <tr>
                                            <td colSpan={4} className="p-10 text-center text-muted-foreground italic text-sm">
                                                Không có báo cáo nào cần xử lý.
                                            </td>
                                        </tr>
                                    ) : (
                                        reports.map((report: any) => (
                                            <tr key={report._id} className="border-b border-border last:border-0 hover:bg-muted/10 transition-colors">
                                                <td className="p-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="bg-muted p-2 rounded-sm text-muted-foreground">
                                                            {report.item_type === 'USER' ? <User className="w-4 h-4" /> : <BookOpen className="w-4 h-4" />}
                                                        </div>
                                                        <div>
                                                            <div className="font-bold tracking-tight text-[11px]">{report.item_type}</div>
                                                            <div className="text-xs text-muted-foreground font-medium">{report.item_id}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="p-4">
                                                    <div className="font-bold text-rose-600 text-[10px] tracking-widest mb-1">{report.reason}</div>
                                                    <div className="text-xs text-muted-foreground line-clamp-1 max-w-[200px]">{report.description}</div>
                                                </td>
                                                <td className="p-4 text-xs font-medium text-muted-foreground">
                                                    {new Date(report.created_at).toLocaleString("vi-VN")}
                                                </td>
                                                <td className="p-4 text-right">
                                                    <div className="flex justify-end gap-2">
                                                        <Button 
                                                            variant="secondary" 
                                                            size="sm" 
                                                            className="h-8 rounded-none text-[9px] font-black tracking-widest"
                                                            onClick={() => resolveReport(report._id, "KEEP")}
                                                            disabled={isProcessing}
                                                        >
                                                            Bỏ qua
                                                        </Button>
                                                        <Button 
                                                            variant="destructive" 
                                                            size="sm" 
                                                            className="h-8 rounded-none text-[9px] font-black tracking-widest"
                                                            onClick={() => resolveReport(report._id, "TAKEDOWN")}
                                                            disabled={isProcessing}
                                                        >
                                                            Gỡ bỏ
                                                        </Button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
}
