"use client";

import { useEffect, useState, useCallback } from "react";
import { getModeratorActivityAPI } from "@/features/provision/services/audit_logs.service";
import { Loader2, RefreshCcw, Activity, FileText, Database, ShieldAlert, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { useRouter } from "next/navigation";

export default function LogsPage() {
 const { user, isLoading: authLoading } = useAuth() as any;
 const router = useRouter();
 const { showToast } = useToast();

 const [activityLogs, setActivityLogs] = useState<any[]>([]);
 const [isLoading, setIsLoading] = useState(true);
 const [isRefreshing, setIsRefreshing] = useState(false);

 const fetchData = useCallback(async () => {
 setIsRefreshing(true);
 try {
 const logsRes = await getModeratorActivityAPI();
 setActivityLogs(logsRes.data || logsRes || []);
 } catch (err: any) {
 showToast("Không thể tải nhật ký hệ thống.", "error");
 } finally {
 setIsRefreshing(false);
 setIsLoading(false);
 }
 }, [showToast]);

 useEffect(() => {
 if (!authLoading && user) {
 if (user.role !== "admin" && user.role !== "moderator") {
 router.push("/");
 } else {
 fetchData();
 }
 }
 }, [user, authLoading, fetchData, router]);

 if (authLoading || isLoading) {
 return (
 <div className="flex h-[80vh] items-center justify-center">
 <Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" />
 </div>
 );
 }

 if (user?.role !== "admin" && user?.role !== "moderator") {
 return (
 <div className="flex flex-col items-center justify-center h-[calc(100vh-56px)] gap-6 font-sans text-center">
 <div className="w-24 h-24 bg-[#F5F5F7] flex items-center justify-center rounded-[18px]">
 <ShieldAlert className="w-10 h-10 text-[#FF3B30]" />
 </div>
 <div className="space-y-2 max-w-[300px]">
 <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
 Truy cập bị hạn chế
 </p>
 <p className="text-[15px] text-[#6E6E73]">
 Bạn không có quyền quản trị để truy cập trang này.
 </p>
 </div>
 </div>
 );
 }

 return (
 <div className="w-full max-w-[1200px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] font-sans text-[#1D1D1F] flex flex-col gap-6">
 <div className="bg-[#F5F5F7] rounded-[18px] overflow-hidden flex flex-col flex-1 min-h-0">
 <div className="flex items-center justify-between p-6 bg-[#F5F5F7]/30">
 <button
 onClick={fetchData}
 disabled={isRefreshing}
 className="pill-button flex items-center gap-2 disabled:opacity-50 bg-white  text-[#1D1D1F] hover:bg-[#F5F5F7]"
 >
 {isRefreshing ? (
 <Loader2 className="w-4 h-4 animate-spin" />
 ) : (
 <RefreshCcw className="w-4 h-4" />
 )}
 Đồng bộ dữ liệu
 </button>
 <span className="px-3 py-1 bg-white  text-[#6E6E73] text-[13px] font-medium rounded-full">
 {activityLogs.length} bản ghi
 </span>
 </div>
 
 <div className="overflow-y-auto no-scrollbar flex-1 p-2">
 <table className="w-full text-left text-[14px] border-collapse">
 <thead>
 <tr className="text-[13px] text-[#6E6E73]">
 <th className="py-3 px-6 font-medium w-[25%]">Thao tác</th>
 <th className="py-3 px-6 font-medium w-[35%]">Đối tượng</th>
 <th className="py-3 px-6 font-medium w-[25%]">Thời gian</th>
 <th className="py-3 px-6 font-medium text-right w-[15%]">Trạng thái</th>
 </tr>
 </thead>
 <tbody>
 {activityLogs.length === 0 ? (
 <tr>
 <td colSpan={4} className="py-24 text-center">
 <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
 <div className="w-16 h-16 bg-[#F5F5F7] rounded-[16px] flex items-center justify-center mb-4">
 <FileText className="w-8 h-8 text-[#C7C7CC]" />
 </div>
 <h2 className="text-[20px] font-medium text-[#1D1D1F] mb-1">Nhật ký trống</h2>
 <p className="text-[17px] text-[#6E6E73]">
 Chưa có hoạt động quản trị nào được ghi nhận.
 </p>
 </div>
 </td>
 </tr>
 ) : (
 activityLogs.map((log: any, idx: number) => (
 <tr
 key={idx}
 className="hover:bg-[#F5F5F7] transition-colors"
 >
 <td className="py-3 px-6">
 <span className="font-medium text-[#1D1D1F]">
 {log.action || "Thao tác điều hành"}
 </span>
 </td>
 <td className="py-3 px-6">
 <div className="flex flex-col gap-1">
 <span className="text-[12px] bg-[#E8E8ED] text-[#6E6E73] px-2 py-0.5 rounded-md w-fit font-medium">
 {log.target_type}
 </span>
 <span className="text-[13px] text-[#6E6E73] font-mono">
 {log.target_id}
 </span>
 </div>
 </td>
 <td className="py-3 px-6">
 <span className="text-[#6E6E73]">
 {new Date(log.created_at).toLocaleString("vi-VN")}
 </span>
 </td>
 <td className="py-3 px-6 text-right">
 <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#E8F5E9] text-[#34C759] rounded-full text-[13px] font-medium">
 <CheckCircle2 className="w-4 h-4" /> Hoàn tất
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
 );
}
