"use client";
import { useCallback, useEffect, useState } from "react";
import { assessmentRequest, reviewSourceMapping } from "../services/assessment.service";
import AdminAccountSecurityPanel from "../components/AdminAccountSecurityPanel";
function messageOf(reason) {
    return reason instanceof Error ? reason.message : "Không thể hoàn tất thao tác";
}
export default function AdminOperationsPage({ view }) {
    var _a, _b, _c, _d, _e, _f, _g, _h, _j, _k, _l, _m, _o, _p, _q, _r, _s, _t, _u, _v;
    const [data, setData] = useState({});
    const [grade, setGrade] = useState(12);
    const [maxDocuments, setMaxDocuments] = useState(1);
    const [forceRecrawl, setForceRecrawl] = useState(false);
    const [retentionDays, setRetentionDays] = useState(730);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const load = useCallback(async () => {
        setLoading(true);
        setError("");
        try {
            if (view === "curriculum") {
                const [curriculum, mappings, stats, jobs] = await Promise.all([
                    assessmentRequest("/education/curriculum?include_obsolete=true"),
                    assessmentRequest("/education/mappings/review"),
                    assessmentRequest("/thu-thap/thong-ke"),
                    assessmentRequest("/thu-thap/jobs"),
                ]);
                setData({ curriculum, mappings, stats, jobs });
            }
            else if (view === "models") {
                const [models, health] = await Promise.all([
                    assessmentRequest("/operations/models"),
                    assessmentRequest("/operations/health"),
                ]);
                setData(Object.assign(Object.assign({}, models), { health }));
            }
            else {
                const [events, privacy] = await Promise.all([
                    assessmentRequest("/audit"),
                    assessmentRequest("/operations/privacy-policy"),
                ]);
                setData({ events, privacy });
                setRetentionDays(Number(privacy.pii_retention_days || 730));
            }
        }
        catch (reason) {
            setError(messageOf(reason));
        }
        finally {
            setLoading(false);
        }
    }, [view]);
    useEffect(() => { void load(); }, [load]);
    const startCollection = async () => {
        try {
            const result = await assessmentRequest("/thu-thap/kich-hoat", {
                method: "POST",
                body: JSON.stringify({ source: "NXBGD", pages: grade, max_documents: maxDocuments, force_recrawl: forceRecrawl }),
            });
            setMessage(`Đã tạo collection job ${result.job_id}`);
            await load();
        }
        catch (reason) {
            setError(messageOf(reason));
        }
    };
    const jobAction = async (jobId, action) => {
        try {
            await assessmentRequest(`/thu-thap/jobs/${jobId}/${action}`, { method: "POST" });
            setMessage(action === "retry" ? "Đã tạo lại collection job" : "Đã yêu cầu dừng collection job");
            await load();
        }
        catch (reason) {
            setError(messageOf(reason));
        }
    };
    const confirmMapping = async (mapping) => {
        const curriculumNodes = window.prompt("Curriculum node IDs", (mapping.curriculum_node_ids || []).join(","));
        if (curriculumNodes === null)
            return;
        const concepts = window.prompt("Concept IDs", (mapping.concept_ids || []).join(","));
        if (concepts === null)
            return;
        try {
            await reviewSourceMapping(mapping.document_id, mapping._id, {
                mapping_status: "confirmed",
                mapping_confidence: 1,
                curriculum_node_ids: curriculumNodes.split(/[,;\n]+/).map((value) => value.trim()).filter(Boolean),
                concept_ids: concepts.split(/[,;\n]+/).map((value) => value.trim()).filter(Boolean),
                skill_ids: mapping.skill_ids || [],
            });
            setMessage("Đã xác nhận ánh xạ chương trình học");
            await load();
        }
        catch (reason) {
            setError(messageOf(reason));
        }
    };
    const rejectMapping = async (mapping) => {
        const reason = window.prompt("Lý do từ chối ánh xạ");
        if (!(reason === null || reason === void 0 ? void 0 : reason.trim()))
            return;
        try {
            await reviewSourceMapping(mapping.document_id, mapping._id, {
                mapping_status: "rejected",
                mapping_confidence: 0,
                curriculum_node_ids: mapping.curriculum_node_ids || [],
                concept_ids: mapping.concept_ids || [],
                skill_ids: mapping.skill_ids || [],
            });
            setMessage(`Đã từ chối ánh xạ với lý do ${reason.trim()}`);
            await load();
        }
        catch (reasonValue) {
            setError(messageOf(reasonValue));
        }
    };
    const reindexSource = async (documentId) => {
        try {
            const result = await assessmentRequest(`/education/sources/${documentId}/reindex`, { method: "POST" });
            setMessage(`Đã lập chỉ mục lại ${result.chunks_count || 0} chunk`);
            await load();
        }
        catch (reason) {
            setError(messageOf(reason));
        }
    };
    const editCurriculumNode = async (node) => {
        const titleValue = window.prompt("Tên canonical", node.title || "");
        if (!(titleValue === null || titleValue === void 0 ? void 0 : titleValue.trim()))
            return;
        const parentId = window.prompt("Parent ID", node.parent_id || "");
        if (parentId === null)
            return;
        const canonicalCode = window.prompt("Canonical code", node.canonical_code || "");
        if (!(canonicalCode === null || canonicalCode === void 0 ? void 0 : canonicalCode.trim()))
            return;
        try {
            await assessmentRequest(`/education/curriculum/${node._id}`, {
                method: "PATCH",
                body: JSON.stringify({ expected_revision: Number(node.revision || 1), title: titleValue.trim(), parent_id: parentId.trim() || null, canonical_code: canonicalCode.trim() }),
            });
            setMessage("Đã cập nhật hierarchy curriculum");
            await load();
        }
        catch (reason) {
            setError(messageOf(reason));
        }
    };
    const mergeCurriculumNode = async (target) => {
        const sourceText = window.prompt("Node IDs cần gộp vào node này");
        if (!(sourceText === null || sourceText === void 0 ? void 0 : sourceText.trim()))
            return;
        const sourceNodeIds = sourceText.split(/[,;\n]+/).map((value) => value.trim()).filter(Boolean);
        const nodesById = Object.fromEntries((data.curriculum || []).map((node) => [node._id, node]));
        const missing = sourceNodeIds.filter((nodeId) => !nodesById[nodeId]);
        if (missing.length) {
            setError(`Không tìm thấy node ${missing.join(" ")}`);
            return;
        }
        try {
            await assessmentRequest(`/education/curriculum/${target._id}/merge`, {
                method: "POST",
                body: JSON.stringify({
                    source_node_ids: sourceNodeIds,
                    expected_target_revision: Number(target.revision || 1),
                    expected_source_revisions: Object.fromEntries(sourceNodeIds.map((nodeId) => [nodeId, Number(nodesById[nodeId].revision || 1)])),
                }),
            });
            setMessage("Đã gộp node và chuyển toàn bộ quan hệ sang node đích");
            await load();
        }
        catch (reason) {
            setError(messageOf(reason));
        }
    };
    const splitCurriculumNode = async (node) => {
        var _a;
        const partsText = window.prompt("Mỗi dòng theo định dạng Tên mới | canonical code");
        if (!(partsText === null || partsText === void 0 ? void 0 : partsText.trim()))
            return;
        const parts = partsText.split("\n").map((line) => {
            const [titleValue, canonicalCode] = line.split("|").map((value) => value.trim());
            return { title: titleValue, canonical_code: canonicalCode };
        }).filter((part) => part.title && part.canonical_code);
        if (parts.length < 2) {
            setError("Cần ít nhất hai node hợp lệ để tách");
            return;
        }
        try {
            const result = await assessmentRequest(`/education/curriculum/${node._id}/split`, {
                method: "POST",
                body: JSON.stringify({ expected_revision: Number(node.revision || 1), parts }),
            });
            setMessage(`Đã tách thành ${((_a = result.parts) === null || _a === void 0 ? void 0 : _a.length) || 0} node và chuyển quan hệ hiện hữu sang phần đầu tiên`);
            await load();
        }
        catch (reason) {
            setError(messageOf(reason));
        }
    };
    const obsoleteSource = async (documentId) => {
        const reason = window.prompt("Lý do đánh dấu nguồn curriculum obsolete");
        if (!(reason === null || reason === void 0 ? void 0 : reason.trim()))
            return;
        try {
            await assessmentRequest(`/education/sources/${documentId}/obsolete`, {
                method: "POST",
                body: JSON.stringify({ reason: reason.trim() }),
            });
            setMessage("Đã đánh dấu nguồn obsolete và xóa khỏi chỉ mục truy xuất");
            await load();
        }
        catch (reasonValue) {
            setError(messageOf(reasonValue));
        }
    };
    const purgeExpiredPii = async () => {
        if (!window.confirm(`Pseudonymize dữ liệu định danh quá ${retentionDays} ngày`))
            return;
        try {
            const result = await assessmentRequest("/operations/privacy/purge", {
                method: "POST",
                body: JSON.stringify({ older_than_days: retentionDays }),
            });
            setMessage(`Đã pseudonymize ${result.attempts_pseudonymized || 0} attempt và ${result.assignments_pseudonymized || 0} assignment`);
            await load();
        }
        catch (reason) {
            setError(messageOf(reason));
        }
    };
    const title = view === "curriculum" ? "Nguồn và ánh xạ chương trình học" : view === "models" ? "Giám sát mô hình và hiệu chỉnh" : "Nhật ký kiểm toán và bảo mật";
    if (loading)
        return <div className="mx-auto max-w-[1300px] p-8"><div className="skeleton h-72"/></div>;
    return (<div className="mx-auto max-w-[1450px] space-y-6 p-5 md:p-8">
      <div><p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">Admin Operations</p><h1 className="mt-2 text-[30px] font-semibold">{title}</h1></div>
      {view === "security" && <AdminAccountSecurityPanel />}
      {view === "curriculum" && <>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">{[["Sách đã thu", ((_a = data.stats) === null || _a === void 0 ? void 0 : _a.total_documents_collected) || 0], ["Job đang chạy", ((_b = data.stats) === null || _b === void 0 ? void 0 : _b.active_jobs) || 0], ["Job lỗi", ((_c = data.stats) === null || _c === void 0 ? void 0 : _c.failed_jobs) || 0], ["Trùng đã bỏ", ((_d = data.stats) === null || _d === void 0 ? void 0 : _d.duplicates_skipped) || 0], ["Mapping cần rà soát", ((_f = (_e = data.mappings) === null || _e === void 0 ? void 0 : _e.items) === null || _f === void 0 ? void 0 : _f.length) || 0]].map(([label, value]) => <section key={String(label)} className="rounded-panel border border-border bg-surface p-5"><p className="text-[28px] font-semibold">{value}</p><p className="mt-1 text-[12px] text-ink-muted">{label}</p></section>)}</div>
        <section className="rounded-panel border border-border bg-surface p-5"><div className="flex flex-wrap items-end gap-3"><label className="text-[12px] font-semibold text-ink-muted">Khối<input className="apple-input mt-1 w-28" type="number" min="1" max="12" value={grade} onChange={(event) => setGrade(Math.min(12, Math.max(1, Number(event.target.value) || 1)))}/></label><label className="text-[12px] font-semibold text-ink-muted">Số sách tối đa<input className="apple-input mt-1 w-32" type="number" min="1" max="10" value={maxDocuments} onChange={(event) => setMaxDocuments(Math.min(10, Math.max(1, Number(event.target.value) || 1)))}/></label><label className="mb-3 flex items-center gap-2 text-[12px]"><input type="checkbox" checked={forceRecrawl} onChange={(event) => setForceRecrawl(event.target.checked)}/> Kiểm tra phiên bản mới tại URL đã thu</label><button type="button" className="apple-button" onClick={() => void startCollection()}>Chạy NXBGD collection</button></div><p className="mt-3 text-[12px] text-ink-muted">Tình trạng nguồn {((_g = data.stats) === null || _g === void 0 ? void 0 : _g.collector_status) || "Chưa xác định"} · Lần crawl gần nhất {((_h = data.stats) === null || _h === void 0 ? void 0 : _h.last_crawl) ? new Date(data.stats.last_crawl).toLocaleString("vi-VN") : "Chưa có"}</p></section>
        <section className="overflow-x-auto rounded-panel border border-border bg-surface"><table className="w-full min-w-[900px] text-left text-[12px]"><thead className="bg-surface-quiet text-ink-muted"><tr><th className="p-4">Job</th><th className="p-4">Trạng thái</th><th className="p-4">Tiến độ</th><th className="p-4">Detected</th><th className="p-4">Saved</th><th className="p-4">Failed</th><th className="p-4">Skipped</th><th className="p-4">Thao tác</th></tr></thead><tbody>{(data.jobs || []).map((job) => <tr key={job._id} className="border-t border-border"><td className="p-4 font-mono">{job._id}</td><td className="p-4">{job.status}</td><td className="p-4">{job.progress || 0} phần trăm</td><td className="p-4">{job.documents_detected || 0}</td><td className="p-4">{job.completed_items || 0}</td><td className="p-4">{job.failed_items || 0}</td><td className="p-4">{job.skipped_items || 0}</td><td className="p-4"><div className="flex gap-2">{["pending", "discovering", "running", "stopping"].includes(job.status) && <button type="button" className="text-danger" onClick={() => void jobAction(job._id, "cancel")}>Dừng</button>}{["failed", "stopped"].includes(job.status) && <button type="button" className="text-brand" onClick={() => void jobAction(job._id, "retry")}>Retry</button>}</div></td></tr>)}</tbody></table></section>
        <section className="rounded-panel border border-border bg-surface"><div className="border-b border-border px-5 py-4"><h2 className="font-semibold">Hierarchy curriculum</h2><p className="mt-1 text-[12px] text-ink-muted">Chỉnh tên canonical parent version taxonomy merge split và trạng thái obsolete với optimistic revision</p></div><div className="divide-y divide-border">{(data.curriculum || []).slice(0, 500).map((node) => <div key={node._id} className="grid items-center gap-2 px-5 py-3 text-[12px] md:grid-cols-[1fr_180px_120px_300px]"><div><p className="font-semibold">{node.title}</p><p className="text-ink-muted">{node.canonical_code} · parent {node.parent_id || "root"} · revision {node.revision || 1}</p></div><p>{node.node_type}</p><p>{node.curriculum_version} · {node.status || "active"}</p><div className="flex flex-wrap gap-2"><button type="button" className="apple-button-secondary" onClick={() => void editCurriculumNode(node)}>Sửa</button>{node.status !== "obsolete" && <><button type="button" className="apple-button-secondary" onClick={() => void mergeCurriculumNode(node)}>Gộp vào đây</button><button type="button" className="apple-button-secondary" onClick={() => void splitCurriculumNode(node)}>Tách node</button></>}</div></div>)}</div></section>
        <section className="rounded-panel border border-border bg-surface"><div className="border-b border-border px-5 py-4"><h2 className="font-semibold">Mapping cần rà soát</h2><p className="mt-1 text-[12px] text-ink-muted">Độ tin cậy thấp {((_j = data.mappings) === null || _j === void 0 ? void 0 : _j.low_confidence_count) || 0} · Chưa map {((_k = data.mappings) === null || _k === void 0 ? void 0 : _k.unmapped_count) || 0}</p></div><div className="divide-y divide-border">{(((_l = data.mappings) === null || _l === void 0 ? void 0 : _l.items) || []).slice(0, 100).map((mapping) => { var _a, _b; return <article key={mapping._id} className="grid items-center gap-2 px-5 py-4 text-[12px] md:grid-cols-[1fr_140px_120px_360px]"><div><p className="font-semibold">{mapping.document_id}</p><p className="mt-1 text-ink-muted">Chunk {mapping.chunk_id} · {((_a = mapping.curriculum_node_ids) === null || _a === void 0 ? void 0 : _a.join(", ")) || "Chưa map"} · source {mapping.source_status || "active"}</p></div><p>Confidence {(_b = mapping.mapping_confidence) !== null && _b !== void 0 ? _b : 0}</p><p>{mapping.mapping_status}</p><div className="flex flex-wrap gap-2"><a className="apple-button-secondary" href={`/tai-lieu/xem-truoc/${mapping.document_id}`}>Xem nguồn</a><button type="button" className="apple-button-secondary" onClick={() => void reindexSource(mapping.document_id)}>Lập chỉ mục lại</button>{mapping.source_type === "curriculum" && <button type="button" className="apple-button-secondary text-danger" onClick={() => void obsoleteSource(mapping.document_id)}>Đánh dấu obsolete</button>}<button type="button" className="apple-button-secondary text-danger" onClick={() => void rejectMapping(mapping)}>Từ chối</button><button type="button" className="apple-button" onClick={() => void confirmMapping(mapping)}>Sửa và xác nhận</button></div></article>; })}</div></section>
      </>}
      {view === "models" && <>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">{[["Prediction thấp confidence", data.low_confidence_prediction_count || 0], ["Calibration jobs", ((_m = data.calibration_jobs) === null || _m === void 0 ? void 0 : _m.length) || 0], ["Job lỗi", ((_o = data.failed_jobs) === null || _o === void 0 ? void 0 : _o.length) || 0], ["Drift alerts", ((_p = data.drift_alerts) === null || _p === void 0 ? void 0 : _p.length) || 0], ["Model versions", ((_q = data.prediction_versions) === null || _q === void 0 ? void 0 : _q.length) || 0]].map(([label, value]) => <section key={String(label)} className="rounded-panel border border-border bg-surface p-5"><p className="text-[28px] font-semibold">{value}</p><p className="mt-1 text-[12px] text-ink-muted">{label}</p></section>)}</div>
        <section className="rounded-panel border border-border bg-surface"><div className="flex items-center justify-between border-b border-border px-5 py-4"><div><h2 className="font-semibold">Sức khỏe dịch vụ Core</h2><p className="mt-1 text-[12px] text-ink-muted">Sẵn sàng {((_r = data.health) === null || _r === void 0 ? void 0 : _r.ready_count) || 0} · Chưa sẵn sàng {((_s = data.health) === null || _s === void 0 ? void 0 : _s.unavailable_count) || 0}</p></div><button type="button" className="apple-button-secondary" onClick={() => void load()}>Kiểm tra lại</button></div><div className="grid gap-px bg-border sm:grid-cols-2 xl:grid-cols-3">{Object.entries(((_t = data.health) === null || _t === void 0 ? void 0 : _t.services) || {}).map(([name, value]) => { var _a; return <div key={name} className="bg-surface px-5 py-4 text-[12px]"><div className="flex items-center justify-between gap-3"><span className="font-semibold">{name}</span><span className={value.status === "ready" ? "text-brand" : "text-danger"}>{value.status}</span></div><p className="mt-1 text-ink-muted">HTTP {(_a = value.http_status) !== null && _a !== void 0 ? _a : "không kết nối"}</p></div>; })}</div></section>
        <section className="rounded-panel border border-border bg-surface"><div className="border-b border-border px-5 py-4 font-semibold">Phiên bản dự đoán và sai số thực nghiệm</div><div className="divide-y divide-border">{(data.prediction_versions || []).map((model) => { var _a, _b; const errorMetric = (data.prediction_error_metrics || []).find((metric) => metric.model_version === model._id); return <div key={model._id} className="grid gap-2 px-5 py-4 text-[13px] md:grid-cols-5"><span>{model._id}</span><span>{model.count} dự đoán</span><span>Confidence {Number(model.average_confidence || 0).toFixed(3)}</span><span>MAE {(_a = errorMetric === null || errorMetric === void 0 ? void 0 : errorMetric.mae) !== null && _a !== void 0 ? _a : "Chưa đủ dữ liệu"}</span><span>RMSE {(_b = errorMetric === null || errorMetric === void 0 ? void 0 : errorMetric.rmse) !== null && _b !== void 0 ? _b : "Chưa đủ dữ liệu"}</span></div>; })}</div></section>
        <section className="overflow-x-auto rounded-panel border border-border bg-surface"><div className="border-b border-border px-5 py-4 font-semibold">Calibration jobs và lỗi</div><table className="w-full min-w-[760px] text-left text-[12px]"><thead className="bg-surface-quiet text-ink-muted"><tr><th className="p-4">Job</th><th className="p-4">Trạng thái</th><th className="p-4">Model</th><th className="p-4">Thời gian</th><th className="p-4">Lỗi</th></tr></thead><tbody>{(data.calibration_jobs || []).map((job) => <tr key={job._id} className="border-t border-border"><td className="p-4 font-mono">{job._id}</td><td className="p-4">{job.status}</td><td className="p-4">{job.model_type}</td><td className="p-4">{job.created_at ? new Date(job.created_at).toLocaleString("vi-VN") : "Chưa có"}</td><td className="p-4 text-danger">{job.error || job.error_message || "Không có"}</td></tr>)}</tbody></table></section>
        <div className="grid gap-4 lg:grid-cols-2"><section className="rounded-panel border border-border bg-surface"><div className="border-b border-border px-5 py-4 font-semibold">Item drift alerts</div><div className="divide-y divide-border">{(data.drift_alerts || []).map((alert) => { var _a; return <div key={alert._id} className="px-5 py-4 text-[12px]"><p className="font-semibold">{alert.question_version_id}</p><p className="mt-1 text-ink-muted">Difficulty {alert.difficulty} · Sample {alert.sample_size} · Context {((_a = alert.calibration_context) === null || _a === void 0 ? void 0 : _a.delivery_context) || "mixed"}</p></div>; })}{!((_u = data.drift_alerts) === null || _u === void 0 ? void 0 : _u.length) && <p className="px-5 py-8 text-center text-[12px] text-ink-muted">Không có cảnh báo drift</p>}</div></section><section className="rounded-panel border border-border bg-surface"><div className="border-b border-border px-5 py-4 font-semibold">Bank coverage theo môn và difficulty</div><div className="divide-y divide-border">{(data.bank_coverage || []).map((row) => <div key={`${row.subject}-${row.difficulty_level}`} className="grid grid-cols-3 px-5 py-3 text-[12px]"><span>{row.subject}</span><span>Level {row.difficulty_level}</span><span>{row.count} câu</span></div>)}{!((_v = data.bank_coverage) === null || _v === void 0 ? void 0 : _v.length) && <p className="px-5 py-8 text-center text-[12px] text-ink-muted">Chưa có item trong bank</p>}</div></section></div>
      </>}
      {view === "security" && <><section className="rounded-panel border border-border bg-surface p-5"><h2 className="font-semibold">Chính sách giảm thiểu PII</h2><p className="mt-2 text-[12px] text-ink-muted">Response nghiên cứu dùng HMAC participant ID và không lưu student ID thô</p><div className="mt-4 flex flex-wrap items-end gap-3"><label className="text-[12px] font-semibold text-ink-muted">Thời hạn lưu định danh ngày<input className="apple-input mt-1 w-44" type="number" min="30" max="3650" value={retentionDays} onChange={(event) => setRetentionDays(Math.min(3650, Math.max(30, Number(event.target.value) || 30)))}/></label><button type="button" className="apple-button-secondary text-danger" onClick={() => void purgeExpiredPii()}>Áp dụng retention</button></div></section><section className="overflow-x-auto rounded-panel border border-border bg-surface"><table className="w-full min-w-[900px] text-left text-[12px]"><thead className="bg-surface-quiet text-ink-muted"><tr><th className="p-4">Thời gian</th><th className="p-4">Actor</th><th className="p-4">Hành động</th><th className="p-4">Entity</th><th className="p-4">Chi tiết</th></tr></thead><tbody>{(data.events || []).map((event) => <tr key={event._id} className="border-t border-border"><td className="p-4">{new Date(event.created_at).toLocaleString("vi-VN")}</td><td className="p-4">{event.actor_id}</td><td className="p-4 font-semibold">{event.action}</td><td className="p-4">{event.entity_type} {event.entity_id}</td><td className="p-4 font-mono">{JSON.stringify(event.details || {})}</td></tr>)}</tbody></table></section></>}
      {message && <p role="status" className="rounded-control bg-brand-soft p-3 text-brand">{message}</p>}
      {error && <p role="alert" className="rounded-control bg-danger-soft p-3 text-danger">{error}</p>}
    </div>);
}
