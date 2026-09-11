"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import ExitCriteriaPanel from "../../components/ExitCriteriaPanel";
import PlanVsActualPanel from "../../components/PlanVsActualPanel";
import QualityGateBadge from "../../components/QualityGateBadge";
import TestControlActionPanel from "../../components/TestControlActionPanel";
import TestProgressBoard from "../../components/TestProgressBoard";
import { ErrorState, Panel, ProjectCrumb, WorkspacePage, useActionDialog } from "../../components/WorkspacePrimitives";
import { messageOf } from "../../lib/testing";
import { testingApi } from "../../services/testing.service";


const controlTypes = [
  "PAUSE_EXECUTION",
  "RESUME_EXECUTION",
  "REQUEST_RETEST",
  "CREATE_ADDITIONAL_TEST_SCOPE",
  "REQUEST_NEW_BUILD",
  "BLOCK_RELEASE",
  "ACCEPT_RISK",
  "ESCALATE_DEFECT",
  "REPRIORITIZE_REGRESSION",
  "EXTEND_TEST_WINDOW",
];


export default function MonitoringPage({ project }) {
  const { ask, dialog } = useActionDialog();
  const [plans, setPlans] = useState([]);
  const [members, setMembers] = useState([]);
  const [snapshots, setSnapshots] = useState([]);
  const [actions, setActions] = useState([]);
  const [selectedPlanId, setSelectedPlanId] = useState("");
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);
  const [error, setError] = useState("");
  const can = (permission) => project.current_permissions?.includes(permission);
  const load = useCallback(async () => {
    try {
      const [planValues, memberValues, snapshotValues, actionValues] = await Promise.all([
        testingApi.listPlans(project._id, { status: "APPROVED" }),
        testingApi.listMembers(project._id),
        testingApi.listMonitoringSnapshots(project._id, selectedPlanId ? { test_plan_id: selectedPlanId } : {}),
        testingApi.listControlActions(project._id),
      ]);
      setPlans(planValues);
      setMembers(memberValues);
      setSnapshots(snapshotValues);
      setActions(actionValues);
      setSelectedPlanId((current) => current || planValues[0]?._id || "");
      setSelectedSnapshot((current) => snapshotValues.find((item) => item._id === current?._id) || snapshotValues[0] || null);
      setError("");
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [project._id, selectedPlanId]);
  useEffect(() => { void load(); }, [load]);
  const createSnapshot = async () => {
    if (!selectedPlanId) return;
    const answer = await ask({
      title: "Tạo monitoring snapshot",
      confirmLabel: "Tạo snapshot",
      fields: [
        { name: "actual_effort", label: "Nỗ lực thực tế theo giờ", type: "number" },
        { name: "expected_completion", label: "Thời điểm dự kiến hoàn thành", type: "datetime-local" },
      ],
    });
    if (!answer) return;
    try {
      const value = await testingApi.createMonitoringSnapshot(project._id, {
        test_plan_id: selectedPlanId,
        actual_effort: answer.actual_effort === "" ? null : Number(answer.actual_effort),
        expected_completion: answer.expected_completion || null,
        risks: [],
        blockers: [],
      });
      setSelectedSnapshot(value);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const createAction = async () => {
    if (!selectedSnapshot) return;
    const answer = await ask({
      title: "Tạo control action",
      confirmLabel: "Tạo hành động",
      fields: [
        { name: "type", label: "Loại", required: true, options: controlTypes.map((value) => ({ value, label: value })) },
        { name: "title", label: "Nội dung", required: true },
        { name: "description", label: "Mô tả", multiline: true },
        { name: "owner_id", label: "Người phụ trách", required: true, options: members.map((item) => ({ value: item.user_id, label: item.identity?.label || item.full_name || item.email || item.user_id })) },
        { name: "due_at", label: "Hạn xử lý", required: true, type: "datetime-local" },
        { name: "priority", label: "Ưu tiên", required: true, options: ["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((value) => ({ value, label: value })) },
        { name: "decision_reason", label: "Lý do quyết định", required: true, multiline: true },
      ],
    });
    if (!answer) return;
    try {
      await testingApi.createControlAction(project._id, { ...answer, snapshot_id: selectedSnapshot._id, evidence_refs: [selectedSnapshot._id] });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <WorkspacePage
      title="Giám sát và điều khiển kiểm thử"
      actions={<><ProjectCrumb projectId={project._id} />{can("testmonitor.snapshot.create") && <button className="apple-button" type="button" disabled={!selectedPlanId} onClick={createSnapshot}>Tạo snapshot</button>}</>}
    >
      {dialog}
      {error && <ErrorState message={error} />}
      <Panel title="Phạm vi giám sát">
        <div className="grid gap-4 p-5 md:grid-cols-2">
          <label className="field-label">Kế hoạch đã phê duyệt<select className="apple-input mt-2" value={selectedPlanId} onChange={(event) => { setSelectedPlanId(event.target.value); setSelectedSnapshot(null); }}><option value="">Chọn kế hoạch</option>{plans.map((item) => <option key={item._id} value={item._id}>{item.name}</option>)}</select></label>
          <label className="field-label">Snapshot<select className="apple-input mt-2" value={selectedSnapshot?._id || ""} onChange={(event) => setSelectedSnapshot(snapshots.find((item) => item._id === event.target.value) || null)}><option value="">Chọn snapshot</option>{snapshots.map((item) => <option key={item._id} value={item._id}>{new Date(item.snapshot_at).toLocaleString("vi-VN")} {item.source_fingerprint.slice(0, 8)}</option>)}</select></label>
        </div>
      </Panel>
      {selectedSnapshot ? (
        <>
          <TestProgressBoard metrics={selectedSnapshot.metrics} />
          <Panel title="Kế hoạch và thực tế"><PlanVsActualPanel snapshot={selectedSnapshot} /></Panel>
          <Panel title="Exit criteria" actions={<QualityGateBadge status={selectedSnapshot.effective_quality_gate_status || selectedSnapshot.quality_gate_status} />}>
            <ExitCriteriaPanel
              snapshot={selectedSnapshot}
              canOverride={can("testmonitor.exit_criteria.override")}
              onOverride={async (criterion) => {
                const answer = await ask({ title: "Ghi đè exit criterion", confirmLabel: "Ghi nhận", fields: [
                  { name: "status", label: "Kết quả", required: true, options: ["PASS", "FAIL"].map((value) => ({ value, label: value })) },
                  { name: "reason", label: "Lý do", required: true, multiline: true },
                ] });
                if (!answer) return;
                try {
                  const value = await testingApi.overrideMonitoringCriterion(selectedSnapshot._id, { expected_revision: selectedSnapshot.revision, criterion_id: criterion.criterion_id, ...answer, evidence_refs: [] });
                  setSelectedSnapshot(value);
                  await load();
                } catch (reason) {
                  setError(messageOf(reason));
                }
              }}
            />
          </Panel>
          <Panel title="Sai lệch và blocker">
            <DataTable items={[...(selectedSnapshot.deviations || []), ...(selectedSnapshot.blockers || []).map((item) => ({ type: "BLOCKER", actual: item.title || item.defect_id || String(item) }))]} empty="Không có sai lệch hoặc blocker" columns={[{ key: "type", label: "Loại" }, { key: "planned", label: "Kế hoạch" }, { key: "actual", label: "Thực tế" }, { key: "unit", label: "Đơn vị" }]} />
          </Panel>
          <Panel title="Control action">
            <TestControlActionPanel
              items={actions.filter((item) => item.snapshot_id === selectedSnapshot._id)}
              canCreate={can("testmonitor.control.create")}
              canUpdate={can("testmonitor.control.update")}
              onCreate={createAction}
              onUpdate={async (item, status) => {
                try {
                  await testingApi.updateControlAction(item._id, { expected_revision: item.revision, status });
                  await load();
                } catch (reason) {
                  setError(messageOf(reason));
                }
              }}
            />
          </Panel>
        </>
      ) : <Panel title="Monitoring snapshot"><p className="p-8 text-sm text-ink-muted">Chọn kế hoạch đã phê duyệt và tạo snapshot đầu tiên</p></Panel>}
    </WorkspacePage>
  );
}
