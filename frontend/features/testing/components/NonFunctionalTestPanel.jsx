"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "./DataTable";
import { ErrorState, Panel, StatusPill, useActionDialog } from "./WorkspacePrimitives";
import { messageOf } from "../lib/testing";
import { testingApi } from "../services/testing.service";

const splitLines = (value) => String(value || "").split("\n").map((item) => item.trim()).filter(Boolean);

export default function NonFunctionalTestPanel({ project }) {
  const [items, setItems] = useState([]);
  const [conditions, setConditions] = useState([]);
  const [cases, setCases] = useState([]);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");
  const { ask, dialog } = useActionDialog();
  const can = (permission) => project.current_permissions?.includes(permission);
  const load = useCallback(async () => {
    try {
      const [result, conditionResult, caseValues] = await Promise.all([
        testingApi.listNonFunctionalTestPlans(project._id),
        testingApi.listTestConditions(project._id),
        testingApi.listTestCases(project._id, { page_size: 500 }),
      ]);
      setItems(result.items || []);
      setConditions(conditionResult.items || []);
      setCases(caseValues);
      if (selected?._id) setSelected(await testingApi.getNonFunctionalTestPlan(selected._id));
      setError("");
    } catch (reason) { setError(messageOf(reason)); }
  }, [project._id, selected?._id]);
  useEffect(() => { void load(); }, [load]);
  const create = async () => {
    const answer = await ask({ title: "Tạo kế hoạch kiểm thử phi chức năng", confirmLabel: "Tạo", fields: [
      { name: "plan_type", label: "Loại", options: [{ value: "SECURITY_TEST_PLAN", label: "Security Test Plan" }, { value: "PERFORMANCE_TEST_PLAN", label: "Performance Test Plan" }] },
      { name: "name", label: "Tên", required: true },
      { name: "objective", label: "Mục tiêu", required: true, multiline: true },
      { name: "scope", label: "Phạm vi mỗi dòng một mục", required: true, multiline: true },
      { name: "approach", label: "Cách tiếp cận", required: true, multiline: true },
      { name: "entry_criteria", label: "Điều kiện bắt đầu mỗi dòng một mục", multiline: true },
      { name: "exit_criteria", label: "Điều kiện kết thúc mỗi dòng một mục", multiline: true },
      { name: "tools", label: "Công cụ mỗi dòng một mục", multiline: true },
      { name: "condition_ids", label: "Mã TestCondition cách nhau bởi dấu phẩy", initialValue: conditions.map((item) => item._id).join(",") },
      { name: "case_ids", label: "Mã phiên bản TestCase cách nhau bởi dấu phẩy", initialValue: cases.map((item) => item.current_version_id).filter(Boolean).join(",") },
    ] });
    if (!answer) return;
    try {
      const value = await testingApi.createNonFunctionalTestPlan(project._id, { idempotency_key: crypto.randomUUID(), plan_type: answer.plan_type, name: answer.name, objective: answer.objective, scope: splitLines(answer.scope), approach: answer.approach, entry_criteria: splitLines(answer.entry_criteria), exit_criteria: splitLines(answer.exit_criteria), test_condition_ids: answer.condition_ids.split(",").map((item) => item.trim()).filter(Boolean), test_case_version_ids: answer.case_ids.split(",").map((item) => item.trim()).filter(Boolean), requirement_version_ids: [], source_ai_result_ids: [], tools: splitLines(answer.tools) });
      setSelected(await testingApi.getNonFunctionalTestPlan(value._id));
      await load();
    } catch (reason) { setError(messageOf(reason)); }
  };
  const edit = async () => {
    const answer = await ask({ title: "Cập nhật kế hoạch NFR", confirmLabel: "Lưu", fields: [
      { name: "name", label: "Tên", required: true, initialValue: selected.name },
      { name: "objective", label: "Mục tiêu", required: true, multiline: true, initialValue: selected.objective },
      { name: "scope", label: "Phạm vi mỗi dòng một mục", required: true, multiline: true, initialValue: selected.scope?.join("\n") },
      { name: "approach", label: "Cách tiếp cận", required: true, multiline: true, initialValue: selected.approach },
      { name: "entry_criteria", label: "Điều kiện bắt đầu mỗi dòng một mục", multiline: true, initialValue: selected.entry_criteria?.join("\n") },
      { name: "exit_criteria", label: "Điều kiện kết thúc mỗi dòng một mục", multiline: true, initialValue: selected.exit_criteria?.join("\n") },
      { name: "tools", label: "Công cụ mỗi dòng một mục", multiline: true, initialValue: selected.tools?.join("\n") },
    ] });
    if (!answer) return;
    try {
      setSelected(await testingApi.updateNonFunctionalTestPlan(selected._id, { expected_revision: selected.revision, name: answer.name, objective: answer.objective, scope: splitLines(answer.scope), approach: answer.approach, entry_criteria: splitLines(answer.entry_criteria), exit_criteria: splitLines(answer.exit_criteria), tools: splitLines(answer.tools) }));
      setError("");
    } catch (reason) { setError(messageOf(reason)); }
  };
  const importEvidence = async () => {
    const answer = await ask({ title: "Nhập bằng chứng thực thi bên ngoài", confirmLabel: "Nhập", fields: [
      { name: "provider", label: "Công cụ", options: ["GENERIC", "K6", "JMETER", "OWASP_ZAP", "PLAYWRIGHT"].map((value) => ({ value, label: value })) },
      { name: "external_run_ref", label: "Mã lần chạy", required: true },
      { name: "executed_at", label: "Thời điểm chạy", required: true, type: "datetime-local" },
      { name: "evidence_refs", label: "Tham chiếu bằng chứng mỗi dòng một mục", required: true, multiline: true },
      { name: "result_summary", label: "Tóm tắt kết quả JSON", required: true, multiline: true, initialValue: "{}" },
      { name: "raw_result_hash", label: "SHA256 kết quả gốc", required: true },
    ] });
    if (!answer) return;
    try {
      const resultSummary = JSON.parse(answer.result_summary);
      await testingApi.importNonFunctionalEvidence(selected._id, { idempotency_key: crypto.randomUUID(), provider: answer.provider, external_run_ref: answer.external_run_ref, executed_at: new Date(answer.executed_at).toISOString(), evidence_refs: splitLines(answer.evidence_refs), result_summary: resultSummary, raw_result_hash: answer.raw_result_hash.trim() });
      setSelected(await testingApi.getNonFunctionalTestPlan(selected._id));
      await load();
    } catch (reason) { setError(reason instanceof SyntaxError ? "Tóm tắt kết quả phải là JSON hợp lệ" : messageOf(reason)); }
  };
  const transition = async (approve) => {
    try {
      setSelected(await testingApi.transitionNonFunctionalTestPlan(selected._id, { expected_revision: selected.revision, note: approve ? "Phê duyệt kế hoạch" : "Gửi rà soát" }, approve));
      await load();
    } catch (reason) { setError(messageOf(reason)); }
  };
  return <Panel title="Kiểm thử phi chức năng" actions={can("nfrtest.manage") ? <button className="apple-button" type="button" onClick={create}>Tạo kế hoạch NFR</button> : null}>
    {dialog}{error && <div className="p-4"><ErrorState message={error} /></div>}
    <DataTable items={items} empty="Chưa có kế hoạch kiểm thử phi chức năng" columns={[{ key: "plan_type", label: "Loại" }, { key: "name", label: "Tên" }, { key: "test_condition_ids", label: "TestCondition", render: (item) => item.test_condition_ids?.length || 0 }, { key: "test_case_version_ids", label: "TestCase", render: (item) => item.test_case_version_ids?.length || 0 }, { key: "external_evidence_ids", label: "Bằng chứng", render: (item) => item.external_evidence_ids?.length || 0 }, { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> }, { key: "action", label: "Thao tác", render: (item) => <button className="secondary-button" type="button" onClick={async () => { try { setSelected(await testingApi.getNonFunctionalTestPlan(item._id)); } catch (reason) { setError(messageOf(reason)); } }}>Mở</button> }]} />
    {selected && <div className="space-y-4 border-t border-border p-5">
      <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-semibold">{selected.name}</p><p className="mt-1 max-w-3xl whitespace-pre-wrap text-sm text-ink-muted">{selected.objective}</p></div><div className="flex flex-wrap gap-2">{["DRAFT", "IN_REVIEW"].includes(selected.status) && can("nfrtest.manage") && <button className="secondary-button" type="button" onClick={edit}>Chỉnh sửa</button>}{selected.status === "DRAFT" && can("nfrtest.review") && <button className="secondary-button" type="button" onClick={() => transition(false)}>Gửi rà soát</button>}{selected.status === "IN_REVIEW" && can("nfrtest.approve") && <button className="apple-button" type="button" onClick={() => transition(true)}>Phê duyệt</button>}{can("nfrtest.evidence.import") && <button className="apple-button" type="button" onClick={importEvidence}>Nhập bằng chứng</button>}</div></div>
      <div className="grid gap-3 text-sm md:grid-cols-3"><div><p className="field-label">Phạm vi</p><p>{selected.scope?.join(", ")}</p></div><div><p className="field-label">Công cụ</p><p>{selected.tools?.join(", ") || "Chưa khai báo"}</p></div><div><p className="field-label">Kết quả gần nhất</p><pre className="whitespace-pre-wrap">{JSON.stringify(selected.result_summary || {}, null, 2)}</pre></div></div>
      <DataTable items={selected.external_evidence || []} empty="Chưa nhập bằng chứng bên ngoài" columns={[{ key: "provider", label: "Công cụ" }, { key: "external_run_ref", label: "Lần chạy" }, { key: "executed_at", label: "Thời điểm" }, { key: "raw_result_hash", label: "Hash" }]} />
    </div>}
  </Panel>;
}
