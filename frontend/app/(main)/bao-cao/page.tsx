"use client";

import { useEffect, useState, useCallback } from "react";
import { Loader2, Search, AlertOctagon, CheckCircle2, XCircle, RefreshCcw, FileWarning, ShieldAlert } from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { useRouter } from "next/navigation";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from "@/shared/components/ui/Modal";
import PageLoader from "@/shared/components/common/PageLoader";

export default function ReportsManagementPage() {
 const { user, isLoading: authLoading } = useAuth() as any;
 const router = useRouter();
 const { showToast } = useToast();
 
 const [reports, setReports] = useState<any[]>([]);
 const [isLoading, setIsLoading] = useState(true);
 const [isRefreshing, setIsRefreshing] = useState(false);
 const [searchQuery, setSearchQuery] = useState("");
 const [confirmModal, setConfirmModal] = useState<{ reportId: string; action: string; } | null>(null);
 const [isProcessing, setIsProcessing] = useState(false);

 const fetchData = useCallback(async () => {
 setIsRefreshing(true);
 try { setReports([]); } catch (err: any) { showToast("Không thể kết nối máy chủ", "error"); } finally { setIsRefreshing(false); setIsLoading(false); }
 }, [showToast]);

 useEffect(() => { if (!authLoading && user) { if (user.role !== "admin" && user.role !== "moderator") router.push("/"); else fetchData(); } }, [user, authLoading, fetchData, router]);

 const confirmResolve = async () => {
 if (!confirmModal) return; setIsProcessing(true);
 try { setConfirmModal(null); } catch (err: any) { showToast(err.message || "Lỗi xử lý", "error"); } finally { setIsProcessing(false); }
 };

 const filteredReports = reports.filter(r => (r.reason || "").toLowerCase().includes(searchQuery.toLowerCase()) || (r.target_id || "").toLowerCase().includes(searchQuery.toLowerCase()) || (r.reporter_name || "").toLowerCase().includes(searchQuery.toLowerCase()));

 if (authLoading || isLoading) return <PageLoader />;
 if (user?.role !== "admin" && user?.role !== "moderator") return (
 <div className="flex flex-col items-center justify-center h-[calc(100vh-56px)] gap-6 font-sans text-center">
 <div className="w-24 h-24 bg-[#F5F5F7] flex items-center justify-center rounded-[24px]"><ShieldAlert className="w-10 h-10 text-[#FF3B30]" /></div>
 <div className="space-y-2 max-w-[300px]"><h2 className="text-[20px] font-semibold text-[#1D1D1F]">Truy cập bị hạn chế</h2><p className="text-[15px] text-[#6E6E73]">Bạn không có quyền quản trị để truy cập trang này.</p></div>
 </div>
 );

 const pendingCount = reports.filter(r => r.status !== "RESOLVED" && r.status !== "DISMISSED").length;

 return (
 <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] font-sans text-[#1D1D1F] flex flex-col gap-6">
 <div className="grid lg:grid-cols-12 gap-8 flex-1 min-h-0">
 <aside className="lg:col-span-3 flex flex-col space-y-6 overflow-y-auto no-scrollbar pb-6 pr-2">
 <div className="bg-[#F5F5F7] rounded-[24px] p-6 space-y-4">
 <h3 className="text-[17px] font-medium text-[#1D1D1F]">Giao diện</h3>
 <button onClick={fetchData} disabled={isRefreshing} className="w-full py-2 rounded-[14px] bg-white  text-[#1D1D1F] font-medium text-[14px] hover:bg-[#F5F5F7] transition-colors flex items-center justify-center gap-2">{isRefreshing ? <Loader2 className="w-4 h-4 animate-spin" /> : null} Làm mới</button>
 </div>
 </aside>

 <main className="lg:col-span-9 flex flex-col min-h-0">
 <div className="bg-[#F5F5F7] rounded-[24px] flex-1 overflow-hidden flex flex-col min-h-0">
 <div className="flex items-center justify-between p-6 bg-[#F5F5F7]/30">
 <div className="flex items-center gap-3">
 <h2 className="text-[20px] font-medium text-[#1D1D1F]">Hàng đợi báo cáo</h2>
 {pendingCount > 0 && <span className="px-3 py-1 bg-[#FF3B30]/10 text-[#FF3B30] text-[13px] font-medium rounded-full flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-[#FF3B30] animate-pulse"></div>{pendingCount} chờ xử lý</span>}
 </div>
 <span className="text-[13px] text-[#6E6E73] font-medium">Tổng: {reports.length}</span>
 </div>
 
 <div className="overflow-y-auto no-scrollbar flex-1 p-2">
 <table className="w-full text-left text-[14px] border-collapse">
 <thead>
 <tr className="text-[13px] text-[#6E6E73]">
 <th className="py-3 px-6 font-medium w-[20%]">Đối tượng</th><th className="py-3 px-6 font-medium w-[30%]">Nội dung báo cáo</th><th className="py-3 px-6 font-medium w-[15%]">Người báo cáo</th><th className="py-3 px-6 font-medium w-[15%]">Trạng thái</th><th className="py-3 px-6 font-medium text-right w-[20%]">Thao tác</th>
 </tr>
 </thead>
 <tbody>
 {filteredReports.length === 0 ? (
 <tr>
 <td colSpan={5} className="py-24 text-center">
 <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
 <div className="w-16 h-16 bg-[#F5F5F7] rounded-[16px] flex items-center justify-center mb-4"><FileWarning className="w-8 h-8 text-[#C7C7CC]" /></div>
 <h2 className="text-[20px] font-medium text-[#1D1D1F] mb-1">{searchQuery ? "Không tìm thấy" : "Chưa có báo cáo"}</h2>
 <p className="text-[17px] text-[#6E6E73]">{searchQuery ? "Vui lòng thử từ khóa khác." : "Hệ thống hiện không có vi phạm nào."}</p>
 </div>
 </td>
 </tr>
 ) : (
 filteredReports.map(r => (
 <tr key={r.id} className="hover:bg-[#F5F5F7] transition-colors group">
 <td className="py-3 px-6"><div className="flex flex-col gap-1"><span className="text-[12px] bg-[#E8E8ED] text-[#6E6E73] px-2 py-0.5 rounded-md w-fit font-medium">{r.target_type || "Nội dung"}</span><span className="text-[13px] text-[#6E6E73] font-mono truncate max-w-[150px]">{r.target_id}</span></div></td>
 <td className="py-3 px-6 max-w-sm"><div className="flex flex-col gap-1"><span className="font-medium text-[#1D1D1F]">{r.reason}</span><p className="text-[13px] text-[#6E6E73] line-clamp-2">"{r.description || "Không có mô tả chi tiết."}"</p></div></td>
 <td className="py-3 px-6"><span className="font-medium text-[#1D1D1F]">{r.reporter_name || "Ẩn danh"}</span><p className="text-[12px] text-[#6E6E73] mt-0.5">{r.created_at ? new Date(r.created_at).toLocaleDateString("vi-VN") : "--"}</p></td>
 <td className="py-3 px-6">
 {r.status === "RESOLVED" ? <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#E8F5E9] text-[#34C759] rounded-full text-[12px] font-medium"><CheckCircle2 className="w-3.5 h-3.5" /> Đã xử lý</div> : r.status === "DISMISSED" ? <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#F5F5F7] text-[#6E6E73] rounded-full text-[12px] font-medium"><XCircle className="w-3.5 h-3.5" /> Đã bỏ qua</div> : <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#FFF4E5] text-[#FF9500] rounded-full text-[12px] font-medium"><div className="w-2 h-2 rounded-full bg-[#FF9500] animate-pulse"></div> Đang chờ</div>}
 </td>
 <td className="py-3 px-6 text-right">
 {r.status !== "RESOLVED" && r.status !== "DISMISSED" ? (
 <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
 <button onClick={() => setConfirmModal({ reportId: r.id, action: "DISMISSED" })} className="px-3 py-1.5 text-[13px] font-medium text-[#6E6E73] bg-white  hover:bg-[#F5F5F7] rounded-[10px] transition-colors">Bỏ qua</button>
 <button onClick={() => setConfirmModal({ reportId: r.id, action: "RESOLVED" })} className="px-3 py-1.5 text-[13px] font-medium text-white bg-[#0071E3] hover:bg-[#0077ED] rounded-[10px] transition-colors">Xử lý</button>
 </div>
 ) : <span className="text-[#A1A1A6]">--</span>}
 </td>
 </tr>
 ))
 )}
 </tbody>
 </table>
 </div>
 </div>
 </main>
 </div>

 <Modal isOpen={!!confirmModal} onClose={() => !isProcessing && setConfirmModal(null)} className="max-w-md bg-[#F5F5F7] rounded-[24px] p-0 -2xl border-none">
 <ModalHeader className="p-6 pb-2"><ModalTitle className="text-[20px] font-semibold text-[#1D1D1F] flex items-center gap-2">{confirmModal?.action === "RESOLVED" ? <><AlertOctagon className="w-5 h-5 text-[#FF3B30]" /> Xác nhận xử lý</> : <><XCircle className="w-5 h-5 text-[#6E6E73]" /> Xác nhận bỏ qua</>}</ModalTitle></ModalHeader>
 <ModalContent className="p-6 pt-2">
 <div className="bg-[#F5F5F7] p-4 rounded-[16px] border-[#E8E8ED] mb-4 font-mono text-[13px] text-[#6E6E73]">ID: {confirmModal?.reportId}</div>
 <p className="text-[14px] text-[#6E6E73] leading-relaxed">{confirmModal?.action === "RESOLVED" ? "Bạn có chắc chắn muốn xử lý vi phạm này? Tác giả sẽ nhận được cảnh báo." : "Bạn muốn bỏ qua báo cáo này? Nội dung sẽ vẫn hiển thị bình thường."}</p>
 </ModalContent>
 <ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3"><button onClick={() => !isProcessing && setConfirmModal(null)} disabled={isProcessing} className="px-5 py-2 text-[#0071E3] font-medium hover:bg-[#F5F5F7] rounded-full disabled:opacity-50">Hủy</button><button onClick={confirmResolve} disabled={isProcessing} className={`pill-button disabled:opacity-50 flex items-center gap-2 ${confirmModal?.action === "RESOLVED" ? "bg-[#FF3B30] hover:bg-[#D70015]" : ""}`}>{isProcessing && <Loader2 className="w-4 h-4 animate-spin" />} Xác nhận</button></ModalFooter>
 </Modal>
 </div>
 );
}
