"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "./DataTable";
import PreventiveActionTable from "./PreventiveActionTable";
import { ErrorState, Panel, StatusPill, useActionDialog } from "./WorkspacePrimitives";
import { messageOf } from "../lib/testing";
import { testingApi } from "../services/testing.service";

const ROOT_CAUSE_CATEGORIES = ["REQUIREMENT", "DESIGN", "IMPLEMENTATION", "CONFIGURATION", "TEST_DATA", "TEST_CASE_GAP", "ENVIRONMENT", "INTEGRATION", "DEPLOYMENT", "PROCESS", "UNKNOWN"];
const NEXT_STATUS = { OPEN: "IN_PROGRESS", IN_PROGRESS: "IMPLEMENTED", IMPLEMENTED: "EFFECTIVENESS_REVIEW", EFFECTIVENESS_REVIEW: "CLOSED" };
const lines = (value) => String(value || "").split("\n").map((item) => item.trim()).filter(Boolean);

export default function CausalAnalysisPanel({ project }) {
  const [items, setItems] = useState([]);
  const [defects, setDefects] = useState([]);
  const [members, setMembers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [hypotheses, setHypotheses] = useState([]);
  const [error, setError] = useState("");
  const { ask, dialog } = useActionDialog();
  const can = (permission) => project.current_permissions?.includes(permission);
  const load = useCallback(async () => {
    try {
      const [result, defectValues, memberValues] = await Promise.all([
        testingApi.listCausalAnalyses(project._id),
        testingApi.listDefects(project._id),
        testingApi.listMembers(project._id),
      ]);
      setItems(result.items || []);
      setDefects(defectValues);
      setMembers(memberValues.filter((item) => item.status === "ACTIVE"));
      if (selected?._id) setSelected(await testingApi.getCausalAnalysis(selected._id));
      setError("");
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [project._id, selected?._id]);
  useEffect(() => { void load(); }, [load]);
  const memberOptions = members.map((item) => ({ value: item.user_id, label: item.user_label || item.email || item.user_id }));
  const refreshSelected = async () => setSelected(await testingApi.getCausalAnalysis(selected._id));
  const create = async () => {
    const eligible = defects.filter((item) => ["blocker", "critical"].includes(item.severity) || item.status === "REOPENED");
    const answer = await ask({ title: "Tạo phân tích nguyên nhân", confirmLabel: "Tạo", fields: [
      { name: "defect_ids", label: "Mã lỗi cách nhau bởi dấu phẩy", required: true, initialValue: eligible.map((item) => item._id).join(",") },
      { name: "problem_statement", label: "Mô tả vấn đề", required: true, multiline: true },
      { name: "evidence", label: "Bằng chứng", required: true, multiline: true },
      { name: "owner_id", label: "Phụ trách", required: true, options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions] },
    ] });
    if (!answer) return;
    try {
      const value = await testingApi.createCausalAnalysis(project._id, { idempotency_key: crypto.randomUUID(), defect_ids: answer.defect_ids.split(",").map((item) => item.trim()).filter(Boolean), problem_statement: answer.problem_statement, evidence: [answer.evidence], root_causes: [], contributing_factors: [], five_whys: [], owner_id: answer.owner_id });
      setSelected(value);
      await load();
    } catch (reason) { setError(messageOf(reason)); }
  };
  const editAnalysis = async () => {
    const rootCause = selected.root_causes?.[0] || {};
    const answer = await ask({ title: "Cập nhật nguyên nhân", confirmLabel: "Lưu", fields: [
      { name: "problem_statement", label: "Mô tả vấn đề", required: true, multiline: true, initialValue: selected.problem_statement },
      { name: "category", label: "Nhóm nguyên nhân", options: ROOT_CAUSE_CATEGORIES.map((value) => ({ value, label: value })), initialValue: rootCause.category || rootCause.root_cause_category || "UNKNOWN" },
      { name: "detail", label: "Nguyên nhân", required: true, multiline: true, initialValue: rootCause.detail || rootCause.hypothesis || "" },
      { name: "contributing_factors", label: "Yếu tố đóng góp mỗi dòng một mục", multiline: true, initialValue: (selected.contributing_factors || []).map((item) => typeof item === "string" ? item : item.detail || JSON.stringify(item)).join("\n") },
      { name: "five_whys", label: "Five whys mỗi dòng một mục", multiline: true, initialValue: (selected.five_whys || []).join("\n") },
    ] });
    if (!answer) return;
    try {
      setSelected(await testingApi.updateCausalAnalysis(selected._id, { expected_revision: selected.revision, problem_statement: answer.problem_statement, root_causes: [{ category: answer.category, detail: answer.detail }], contributing_factors: lines(answer.contributing_factors), five_whys: lines(answer.five_whys).slice(0, 5) }));
      setError("");
    } catch (reason) { setError(messageOf(reason)); }
  };
  const decideRootCause = async () => {
    const answer = await ask({ title: "Quyết định nguyên nhân gốc", confirmLabel: "Ghi nhận", fields: [
      { name: "decision", label: "Quyết định", options: [{ value: "APPROVE", label: "Xác nhận" }, { value: "REQUEST_CHANGES", label: "Yêu cầu chỉnh sửa" }] },
      { name: "note", label: "Ghi chú", required: true, multiline: true },
    ] });
    if (!answer) return;
    try { setSelected(await testingApi.approveCausalRootCause(selected._id, { expected_revision: selected.revision, ...answer })); } catch (reason) { setError(messageOf(reason)); }
  };
  const generateHypotheses = async () => {
    try {
      const value = await testingApi.generateCausalHypotheses(selected._id, { idempotency_key: crypto.randomUUID(), instruction: "Đề xuất dựa trên bằng chứng dự án" });
      setHypotheses(value.suggestions || []);
      setError(value.status === "SUCCESS" ? "" : "AI chưa sẵn sàng và không tạo được giả thuyết");
    } catch (reason) { setError(messageOf(reason)); }
  };
  const applyHypothesis = async (item) => {
    try {
      setSelected(await testingApi.updateCausalAnalysis(selected._id, { expected_revision: selected.revision, root_causes: [{ category: item.root_cause_category, detail: item.hypothesis }], contributing_factors: item.contributing_factors || [], five_whys: (item.five_whys || []).slice(0, 5) }));
      setError("");
    } catch (reason) { setError(messageOf(reason)); }
  };
  const addAction = async () => {
    const answer = await ask({ title: "Thêm hành động CAPA", confirmLabel: "Thêm", fields: [
      { name: "action_type", label: "Loại", options: ["CORRECTIVE", "PREVENTIVE"].map((value) => ({ value, label: value })) },
      { name: "title", label: "Tên hành động", required: true },
      { name: "description", label: "Mô tả", required: true, multiline: true },
      { name: "owner_id", label: "Phụ trách", required: true, options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions] },
      { name: "due_at", label: "Hạn", required: true, type: "datetime-local" },
    ] });
    if (!answer) return;
    try { await testingApi.createPreventionAction(selected._id, { ...answer, due_at: new Date(answer.due_at).toISOString(), evidence_refs: [] }); await refreshSelected(); } catch (reason) { setError(messageOf(reason)); }
  };
  const advanceAnalysis = async () => {
    const status = NEXT_STATUS[selected.status];
    if (!status) return;
    const answer = await ask({ title: `Chuyển phân tích sang ${status}`, confirmLabel: "Chuyển", fields: [{ name: "note", label: "Ghi chú", required: true, multiline: true }] });
    if (!answer) return;
    try { setSelected(await testingApi.transitionCausalAnalysis(selected._id, { expected_revision: selected.revision, status, note: answer.note })); } catch (reason) { setError(messageOf(reason)); }
  };
  return <Panel title="Phân tích nguyên nhân và CAPA" actions={can("causalanalysis.create") ? <button className="apple-button" type="button" onClick={create}>Tạo phân tích</button> : null}>
    {dialog}{error && <div className="p-4"><ErrorState message={error} /></div>}
    <DataTable items={items} empty="Chưa có phân tích nguyên nhân" columns={[{ key: "problem_statement", label: "Vấn đề" }, { key: "defect_ids", label: "Lỗi", render: (item) => item.defect_ids?.length || 0 }, { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> }, { key: "action", label: "Thao tác", render: (item) => <button className="secondary-button" type="button" onClick={async () => { try { setSelected(await testingApi.getCausalAnalysis(item._id)); setHypotheses([]); } catch (reason) { setError(messageOf(reason)); } }}>Mở</button> }]} />
    {selected && <div className="space-y-4 border-t border-border p-5">
      <div className="flex flex-wrap justify-between gap-3"><div><p className="font-semibold">{selected.problem_statement}</p><p className="text-sm text-ink-muted">Nguyên nhân đã xác nhận {selected.root_cause_approved ? "Có" : "Chưa"}</p></div><div className="flex flex-wrap gap-2">{selected.status !== "CLOSED" && can("causalanalysis.update") && <><button className="secondary-button" type="button" onClick={editAnalysis}>Cập nhật nguyên nhân</button><button className="secondary-button" type="button" onClick={generateHypotheses}>AI đề xuất giả thuyết</button>{NEXT_STATUS[selected.status] && NEXT_STATUS[selected.status] !== "CLOSED" && <button className="secondary-button" type="button" onClick={advanceAnalysis}>Chuyển {NEXT_STATUS[selected.status]}</button>}</>}{NEXT_STATUS[selected.status] === "CLOSED" && can("causalanalysis.approve") && <button className="secondary-button" type="button" onClick={advanceAnalysis}>Đóng phân tích</button>}{selected.root_causes?.length > 0 && !selected.root_cause_approved && can("causalanalysis.approve") && <button className="apple-button" type="button" onClick={decideRootCause}>Xác nhận nguyên nhân</button>}{selected.status !== "CLOSED" && can("preventionaction.manage") && <button className="apple-button" type="button" onClick={addAction}>Thêm CAPA</button>}</div></div>
      <DataTable items={selected.root_causes || []} empty="Chưa ghi nhận nguyên nhân" columns={[{ key: "category", label: "Nhóm" }, { key: "detail", label: "Nguyên nhân" }]} />
      {hypotheses.length > 0 && <DataTable items={hypotheses} empty="Chưa có giả thuyết" columns={[{ key: "root_cause_category", label: "Nhóm" }, { key: "hypothesis", label: "Giả thuyết" }, { key: "confidence", label: "Tin cậy" }, { key: "action", label: "Thao tác", render: (item) => can("causalanalysis.update") ? <button className="secondary-button" type="button" onClick={() => applyHypothesis(item)}>Dùng làm bản nháp</button> : null }]} />}
      <PreventiveActionTable items={selected.actions} canManage={can("preventionaction.manage")} onAdvance={async (item, status) => { const answer = await ask({ title: `Chuyển hành động sang ${status}`, confirmLabel: "Chuyển", fields: [{ name: "result", label: "Kết quả", required: !["IN_PROGRESS"].includes(status), multiline: true }] }); if (answer) { try { await testingApi.updatePreventionAction(item._id, { expected_revision: item.revision, status, result: answer.result || "Đang thực hiện" }); await refreshSelected(); } catch (reason) { setError(messageOf(reason)); } } }} />
    </div>}
  </Panel>;
}
