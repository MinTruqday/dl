"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle, ArrowRight, ClipboardCheck, FilePlus2, Gauge, Sparkles } from "lucide-react";
import { getTeacherDashboard } from "../services/assessment.service";
import { getMyDocumentsAPI } from "@/features/content/services/document.service";
export default function TeacherDashboardPage() {
    var _a, _b, _c;
    const [data, setData] = useState({});
    const [materials, setMaterials] = useState([]);
    const [error, setError] = useState("");
    useEffect(() => {
        Promise.all([getTeacherDashboard(), getMyDocumentsAPI("", "", 20)]).then(([dashboard, documents]) => {
            var _a, _b;
            setData(dashboard);
            const rows = (_b = (_a = documents.data) !== null && _a !== void 0 ? _a : documents) !== null && _b !== void 0 ? _b : [];
            setMaterials(rows.filter((row) => { var _a; return ((_a = row.education_metadata) === null || _a === void 0 ? void 0 : _a.source_type) === "teacher_material"; }).slice(0, 5));
        }).catch((reason) => setError(reason instanceof Error ? reason.message : "Không thể tải dữ liệu"));
    }, []);
    const metrics = [
        ["Đề đã xuất bản", ((_a = data.published_assessments) === null || _a === void 0 ? void 0 : _a.length) || 0, ClipboardCheck],
        ["Đang chờ rà soát", data.review_queue_count || 0, AlertTriangle],
        ["Câu bị gắn cờ", data.flagged_item_count || 0, Gauge],
        ["Sẵn sàng hiệu chỉnh", data.calibration_ready_count || 0, Sparkles],
    ];
    return (<div className="mx-auto max-w-[1400px] space-y-7 p-5 md:p-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div><p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">Không gian giáo viên</p><h1 className="mt-2 text-[32px] font-semibold tracking-[-0.04em]">Bảng điều khiển đánh giá</h1></div>
        <div className="flex flex-wrap gap-2"><Link className="apple-button-secondary" href="/giao-vien/de/nhap">Nhập đề</Link><Link className="apple-button-secondary" href="/giao-vien/de/sinh-ai">AI tạo đề</Link><Link className="apple-button-secondary" href="/giao-vien/tai-lieu">Thêm tài liệu</Link><Link className="apple-button-secondary" href="/giao-vien/cau-hoi">Ngân hàng câu hỏi</Link><Link className="apple-button" href="/giao-vien/de/soan-thao"><FilePlus2 size={16}/> Tạo đề mới</Link></div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(([label, value, Icon]) => <section key={label} className="rounded-panel border border-border bg-surface p-5"><Icon className="text-brand" size={20}/><p className="mt-5 text-[30px] font-semibold">{value}</p><p className="text-[13px] text-ink-muted">{label}</p></section>)}
      </div>
      <section className="rounded-panel border border-border bg-surface">
        <div className="flex items-center justify-between border-b border-border px-5 py-4"><h2 className="font-semibold">Bản nháp gần đây</h2><Link className="text-[13px] font-semibold text-brand" href="/giao-vien/de">Xem tất cả</Link></div>
        <div className="divide-y divide-border">
          {(data.recent_drafts || []).map((draft) => <Link key={draft._id} href={`/giao-vien/de/soan-thao?id=${draft._id}`} className="flex items-center gap-4 px-5 py-4 hover:bg-surface-quiet"><div className="min-w-0 flex-1"><p className="truncate text-[14px] font-semibold">{draft.title}</p><p className="mt-1 text-[12px] text-ink-muted">{draft.status}</p></div><ArrowRight size={17}/></Link>)}
          {!((_b = data.recent_drafts) === null || _b === void 0 ? void 0 : _b.length) && <p className="px-5 py-10 text-center text-[13px] text-ink-muted">Chưa có bản nháp</p>}
        </div>
      </section>
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-panel border border-border bg-surface"><div className="flex items-center justify-between border-b border-border px-5 py-4"><h2 className="font-semibold">Cảnh báo dự đoán so với thực nghiệm</h2><Link className="text-[13px] font-semibold text-brand" href="/giao-vien/hieu-chinh">Mở hiệu chỉnh</Link></div><div className="divide-y divide-border">{(data.predicted_empirical_alerts || []).map((alert) => <div key={alert.question_version_id} className="px-5 py-4 text-[13px]"><p className="font-semibold">{alert.question_version_id}</p><p className="mt-1 text-ink-muted">AI {alert.predicted_difficulty} · Thực nghiệm {alert.empirical_difficulty} · Gap {alert.gap} · Mẫu {alert.sample_size} {alert.drift_flag ? "· Có drift" : ""}</p></div>)}{!((_c = data.predicted_empirical_alerts) === null || _c === void 0 ? void 0 : _c.length) && <p className="px-5 py-10 text-center text-[13px] text-ink-muted">Chưa có cảnh báo sai lệch</p>}</div></section>
        <section className="rounded-panel border border-border bg-surface"><div className="flex items-center justify-between border-b border-border px-5 py-4"><h2 className="font-semibold">Tài liệu gần đây</h2><Link className="text-[13px] font-semibold text-brand" href="/giao-vien/tai-lieu">Mở thư viện</Link></div><div className="divide-y divide-border">{materials.map((material) => { var _a; return <Link key={material._id} href={`/tai-lieu/xem-truoc/${material._id}`} className="block px-5 py-4 hover:bg-surface-quiet"><p className="font-semibold">{material.title}</p><p className="mt-1 text-[12px] text-ink-muted">{material.indexing_status || (material.is_indexed ? "indexed" : "queued")} · {((_a = material.education_metadata) === null || _a === void 0 ? void 0 : _a.subject) || "Chưa gắn môn"}</p></Link>; })}{!materials.length && <p className="px-5 py-10 text-center text-[13px] text-ink-muted">Chưa có tài liệu bổ trợ</p>}</div></section>
      </div>
      {error && <p role="alert" className="rounded-control bg-danger-soft p-3 text-danger">{error}</p>}
    </div>);
}
