"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "./DataTable";
import QualityGateBadge from "./QualityGateBadge";
import { ErrorState, Metric, Panel, StatusPill, useActionDialog } from "./WorkspacePrimitives";
import { formatDate, messageOf, valueLabel } from "../lib/testing";
import { testingApi } from "../services/testing.service";


const recommendations = ["ON_TRACK", "AT_RISK", "BLOCKED", "CONTINUE_TESTING", "READY_WITH_RISK", "NOT_READY"];


function lines(value) {
  return String(value || "").split("\n").map((item) => item.trim()).filter(Boolean);
}


export default function TestStatusReportPanel({ project }) {
  const { ask, dialog } = useActionDialog();
  const [reports, setReports] = useState([]);
  const [snapshots, setSnapshots] = useState([]);
  const [builds, setBuilds] = useState([]);
  const [selected, setSelected] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [aiDraft, setAiDraft] = useState(null);
  const [error, setError] = useState("");
  const can = (permission) => project.current_permissions?.includes(permission);
  const load = useCallback(async () => {
    try {
      const [reportValues, snapshotValues, buildValues] = await Promise.all([
        testingApi.listTestStatusReports(project._id),
        testingApi.listMonitoringSnapshots(project._id),
        testingApi.listBuilds(project._id),
      ]);
      setReports(reportValues);
      setSnapshots(snapshotValues);
      setBuilds(buildValues);
      setSelected((current) => reportValues.find((item) => item._id === current?._id) || reportValues[0] || null);
      setError("");
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [project._id]);
  useEffect(() => { void load(); }, [load]);

  const run = async (operation) => {
    try {
      const value = await operation();
      setComparison(null);
      setAiDraft(null);
      await load();
      if (value?._id) setSelected(value);
    } catch (reason) {
      setError(messageOf(reason));
    }
  };

  const create = async () => {
    const today = new Date();
    const end = today.toISOString().slice(0, 16);
    const startDate = new Date(today.getTime() - 7 * 86400000);
    const answer = await ask({
      title: "Tạo báo cáo trạng thái từ snapshot",
      confirmLabel: "Tạo báo cáo",
      fields: [
        { name: "snapshot_id", label: "Monitoring snapshot", required: true, options: snapshots.map((item) => ({ value: item._id, label: `${formatDate(item.snapshot_at)} · ${item.source_fingerprint.slice(0, 8)}` })) },
        { name: "build_id", label: "Bản dựng", required: true, options: builds.map((item) => ({ value: item._id, label: `${item.identifier} · ${item.version}` })) },
        { name: "start_at", label: "Bắt đầu kỳ báo cáo", required: true, type: "datetime-local", initialValue: startDate.toISOString().slice(0, 16) },
        { name: "end_at", label: "Kết thúc kỳ báo cáo", required: true, type: "datetime-local", initialValue: end },
        { name: "executive_summary", label: "Tóm tắt điều hành", multiline: true },
        { name: "forecast", label: "Dự báo", multiline: true },
        { name: "recommendation", label: "Khuyến nghị", options: recommendations.map((value) => ({ value, label: valueLabel(value) })) },
        { name: "distribution", label: "Danh sách phân phối mỗi dòng một người", multiline: true },
        { name: "evidence_refs", label: "Mã bằng chứng mỗi dòng một mã", multiline: true },
      ],
    });
    if (!answer) return;
    await run(() => testingApi.generateTestStatusReport(project._id, {
      snapshot_id: answer.snapshot_id,
      build_id: answer.build_id,
      reporting_period: { start_at: answer.start_at, end_at: answer.end_at },
      executive_summary: answer.executive_summary,
      forecast: answer.forecast,
      recommendation: answer.recommendation || null,
      distribution: lines(answer.distribution),
      evidence_refs: lines(answer.evidence_refs),
    }));
  };

  const edit = async () => {
    if (!selected) return;
    const answer = await ask({
      title: "Chỉnh sửa nội dung báo cáo",
      confirmLabel: "Lưu nội dung",
      fields: [
        { name: "executive_summary", label: "Tóm tắt điều hành", multiline: true, initialValue: selected.executive_summary },
        { name: "progress_summary", label: "Tóm tắt tiến độ", multiline: true, initialValue: selected.progress_summary },
        { name: "coverage_summary", label: "Tóm tắt độ phủ", multiline: true, initialValue: selected.coverage_summary },
        { name: "defect_summary", label: "Tóm tắt lỗi", multiline: true, initialValue: selected.defect_summary },
        { name: "forecast", label: "Dự báo", multiline: true, initialValue: selected.forecast },
        { name: "recommendation", label: "Khuyến nghị", required: true, initialValue: selected.recommendation, options: recommendations.map((value) => ({ value, label: valueLabel(value) })) },
        { name: "distribution", label: "Danh sách phân phối mỗi dòng một người", multiline: true, initialValue: (selected.distribution || []).join("\n") },
      ],
    });
    if (!answer) return;
    await run(() => testingApi.updateTestStatusReport(selected._id, { expected_revision: selected.revision, ...answer, distribution: lines(answer.distribution) }));
  };

  const attachEvidence = async () => {
    if (!selected) return;
    const answer = await ask({ title: "Gắn bằng chứng", confirmLabel: "Gắn bằng chứng", fields: [{ name: "evidence_refs", label: "Mã bằng chứng mỗi dòng một mã", required: true, multiline: true }] });
    if (!answer) return;
    await run(() => testingApi.attachTestStatusReportEvidence(selected._id, { expected_revision: selected.revision, evidence_refs: lines(answer.evidence_refs) }));
  };

  const transition = async (action, title) => {
    const answer = await ask({ title, confirmLabel: title, fields: [{ name: "note", label: "Ghi chú", multiline: true }] });
    if (!answer) return;
    await run(() => testingApi[action](selected._id, { expected_revision: selected.revision, note: answer.note }));
  };

  const compare = async () => {
    const candidates = reports.filter((item) => item._id !== selected?._id);
    const answer = await ask({ title: "So sánh báo cáo", confirmLabel: "So sánh", fields: [{ name: "other_report_id", label: "Báo cáo đối chiếu", required: true, options: candidates.map((item) => ({ value: item._id, label: `Lần ${item.sequence} · ${formatDate(item.created_at)}` })) }] });
    if (!answer) return;
    try {
      setComparison(await testingApi.compareTestStatusReports(selected._id, answer.other_report_id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };

  const draftNarrative = async () => {
    try {
      const value = await testingApi.draftTestStatusReportNarrative(selected._id, { idempotency_key: crypto.randomUUID(), instruction: "Diễn giải ngắn gọn chính xác và nêu rõ rủi ro cần chú ý" });
      const ready = value.status === "SUCCESS" && value.suggestions?.[0]?.executive_summary;
      setAiDraft(ready ? value : null);
      setError(ready ? "" : "AI chưa sẵn sàng và chưa tạo được bản nháp");
    } catch (reason) {
      setError(messageOf(reason));
    }
  };

  const applyAiDraft = async () => {
    const candidate = aiDraft?.suggestions?.[0];
    if (!candidate) return;
    await run(() => testingApi.updateTestStatusReport(selected._id, { expected_revision: selected.revision, ...candidate }));
  };

  return (
    <Panel
      title="Báo cáo trạng thái kiểm thử"
      actions={can("teststatusreport.create") ? <button className="apple-button" type="button" disabled={!snapshots.length || !builds.length} onClick={create}>Tạo từ snapshot</button> : null}
    >
      {dialog}
      {error && <div className="p-5"><ErrorState message={error} /></div>}
      <div className="grid border-t border-border-subtle xl:grid-cols-[320px_minmax(0,1fr)]">
        <div className="border-r border-border-subtle">
          <DataTable
            items={reports}
            empty="Chưa có báo cáo trạng thái"
            columns={[
              { key: "sequence", label: "Lần" },
              { key: "created_at", label: "Thời điểm", render: (item) => <button className="text-left text-accent" type="button" onClick={() => { setSelected(item); setComparison(null); setAiDraft(null); }}>{formatDate(item.created_at)}</button> },
              { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> },
            ]}
          />
        </div>
        <div className="min-w-0 p-5">
          {!selected ? <p className="text-sm text-ink-muted">Chọn hoặc tạo báo cáo trạng thái</p> : (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center gap-2">
                <StatusPill value={selected.status} />
                <QualityGateBadge status={selected.snapshot_basis?.quality_gate_status} />
                {selected.status === "DRAFT" && can("teststatusreport.update") && <button className="secondary-button" type="button" onClick={edit}>Chỉnh sửa</button>}
                {selected.status === "DRAFT" && can("teststatusreport.update") && <button className="secondary-button" type="button" onClick={draftNarrative}>AI soạn bản nháp</button>}
                {selected.status === "DRAFT" && can("teststatusreport.update") && <button className="secondary-button" type="button" onClick={attachEvidence}>Gắn bằng chứng</button>}
                {selected.status === "DRAFT" && can("teststatusreport.review") && <button className="secondary-button" type="button" onClick={() => transition("submitTestStatusReport", "Gửi rà soát")}>Gửi rà soát</button>}
                {selected.status === "IN_REVIEW" && can("teststatusreport.review") && <button className="secondary-button" type="button" onClick={() => transition("requestTestStatusReportChanges", "Yêu cầu chỉnh sửa")}>Yêu cầu chỉnh sửa</button>}
                {selected.status === "IN_REVIEW" && can("teststatusreport.approve") && <button className="apple-button" type="button" onClick={() => transition("approveTestStatusReport", "Phê duyệt")}>Phê duyệt</button>}
                {selected.status === "APPROVED" && can("teststatusreport.approve") && <button className="apple-button" type="button" onClick={() => transition("publishTestStatusReport", "Phát hành")}>Phát hành</button>}
                {reports.length > 1 && <button className="secondary-button" type="button" onClick={compare}>So sánh</button>}
                {can("teststatusreport.export") && [{ format: "pdf", label: "Xuất PDF" }, { format: "docx", label: "Xuất DOCX" }, { format: "csv", label: "Xuất CSV" }].map((item) => <button className="secondary-button" type="button" key={item.format} onClick={() => testingApi.exportTestStatusReport(selected._id, item.format).catch((reason) => setError(messageOf(reason)))}>{item.label}</button>)}
              </div>
              {aiDraft?.suggestions?.[0] && <Panel title="Bản nháp diễn giải do AI đề xuất"><div className="space-y-4 text-sm">{[["Tóm tắt điều hành", "executive_summary"], ["Tiến độ", "progress_summary"], ["Độ phủ", "coverage_summary"], ["Lỗi", "defect_summary"], ["Dự báo", "forecast"]].map(([label, key]) => <div key={key}><p className="field-label">{label}</p><p className="mt-1 whitespace-pre-wrap">{aiDraft.suggestions[0][key]}</p></div>)}<p className="text-xs text-ink-muted">Đây là ứng viên cần người dùng xác nhận và không thay đổi số liệu snapshot</p><button className="apple-button" type="button" onClick={applyAiDraft}>Dùng làm bản nháp</button></div></Panel>}
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <Metric label="Thực thi" value={`${selected.snapshot_basis?.metrics?.execution_percent ?? 0}%`} />
                <Metric label="Tỷ lệ đạt" value={`${selected.snapshot_basis?.metrics?.pass_rate ?? 0}%`} />
                <Metric label="Độ phủ yêu cầu" value={`${selected.snapshot_basis?.metrics?.requirement_coverage ?? 0}%`} />
                <Metric label="Độ phủ condition" value={`${selected.snapshot_basis?.metrics?.test_condition_coverage ?? 0}%`} />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                {[
                  ["Tóm tắt điều hành", selected.executive_summary],
                  ["Tiến độ", selected.progress_summary],
                  ["Độ phủ", selected.coverage_summary],
                  ["Lỗi", selected.defect_summary],
                  ["Dự báo", selected.forecast],
                  ["Khuyến nghị", valueLabel(selected.recommendation)],
                ].map(([label, value]) => <div key={label}><p className="field-label">{label}</p><p className="mt-2 whitespace-pre-wrap text-sm text-ink">{value || "Chưa ghi nhận"}</p></div>)}
              </div>
              <DataTable items={(selected.control_actions || []).map((item, index) => ({ ...item, _id: item._id || `action-${index}` }))} empty="Không có control action" columns={[{ key: "title", label: "Control action" }, { key: "owner_id", label: "Người phụ trách" }, { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> }]} />
              {comparison && <Panel title="Kết quả so sánh"><DataTable items={(comparison.changes || []).map((item) => ({ ...item, _id: item.field }))} empty="Hai báo cáo không khác nhau" columns={[{ key: "field", label: "Trường" }, { key: "from", label: "Báo cáo hiện tại", render: (item) => typeof item.from === "string" ? item.from : JSON.stringify(item.from) }, { key: "to", label: "Báo cáo đối chiếu", render: (item) => typeof item.to === "string" ? item.to : JSON.stringify(item.to) }]} /></Panel>}
              <p className="break-all text-xs text-ink-muted">Snapshot {selected.snapshot_id} · {selected.snapshot_source_fingerprint}</p>
            </div>
          )}
        </div>
      </div>
    </Panel>
  );
}
