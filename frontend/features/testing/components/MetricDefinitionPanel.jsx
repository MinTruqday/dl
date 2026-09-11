"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "./DataTable";
import MetricTrendChart from "./MetricTrendChart";
import QualityMetricCard from "./QualityMetricCard";
import { ErrorState, Panel, StatusPill, useActionDialog } from "./WorkspacePrimitives";
import { messageOf } from "../lib/testing";
import { testingApi } from "../services/testing.service";

const METRICS = {
  REQUIREMENT_COVERAGE: ["Độ phủ yêu cầu", "Yêu cầu được bao phủ trên tổng yêu cầu", "%", "RATIO"],
  ACCEPTANCE_CRITERION_COVERAGE: ["Độ phủ tiêu chí chấp nhận", "Tiêu chí được bao phủ trên tổng tiêu chí", "%", "RATIO"],
  TEST_CONDITION_COVERAGE: ["Độ phủ TestCondition", "TestCondition được bao phủ trên tổng TestCondition", "%", "RATIO"],
  EXECUTION_PROGRESS: ["Tiến độ thực thi", "Kết quả đã hoàn tất trên tổng kết quả", "%", "RATIO"],
  PASS_RATE: ["Tỷ lệ đạt", "Kết quả đạt trên kết quả có quyết định", "%", "RATIO"],
  BLOCKED_RATE: ["Tỷ lệ bị chặn", "Kết quả bị chặn trên kết quả có quyết định", "%", "RATIO"],
  DEFECT_REOPEN_RATE: ["Tỷ lệ mở lại lỗi", "Lỗi từng mở lại trên tổng lỗi", "%", "RATIO"],
  CRITICAL_DEFECT_AGING: ["Tuổi lỗi nghiêm trọng", "Số ngày trung bình của lỗi nghiêm trọng đang mở", "ngày", "AVERAGE"],
  MEAN_TIME_TO_RETEST: ["Thời gian trung bình tới retest", "Thời gian từ xử lý tới retest", "giờ", "AVERAGE"],
  STALE_TEST_RATIO: ["Tỷ lệ test stale", "Test cần cập nhật trên tổng test", "%", "RATIO"],
  REQUIREMENT_VOLATILITY: ["Biến động yêu cầu", "Yêu cầu có nhiều phiên bản trên tổng yêu cầu", "%", "RATIO"],
  IMPACT_PROPOSAL_ACCEPTANCE_RATE: ["Tỷ lệ chấp nhận đề xuất impact", "Đề xuất được chấp nhận trên tổng đề xuất", "%", "RATIO"],
  REGRESSION_EFFECTIVENESS: ["Hiệu quả regression", "Lỗi phát hiện trên test regression được chọn", "%", "RATIO"],
  AUTOMATION_COVERAGE: ["Độ phủ tự động hóa", "Test tự động trên tổng test", "%", "RATIO"],
  AUTOMATION_PASS_STABILITY: ["Độ ổn định automation", "Lần chạy automation đạt trên tổng lần hoàn tất", "%", "RATIO"],
  ESCAPED_DEFECT_RATE: ["Tỷ lệ lỗi lọt", "Lỗi production trên tổng lỗi production và lỗi loại bỏ", "%", "RATIO"],
  DEFECT_REMOVAL_EFFICIENCY: ["Hiệu suất loại bỏ lỗi", "Lỗi loại bỏ trước production trên tổng lỗi", "%", "RATIO"],
};

export default function MetricDefinitionPanel({ project }) {
  const [definitions, setDefinitions] = useState([]);
  const [snapshots, setSnapshots] = useState([]);
  const [selectedKey, setSelectedKey] = useState("");
  const [error, setError] = useState("");
  const { ask, dialog } = useActionDialog();
  const can = (permission) => project.current_permissions?.includes(permission);
  const load = useCallback(async () => {
    try {
      const [definitionResult, snapshotResult] = await Promise.all([testingApi.listMeasurementDefinitions(project._id), testingApi.listMeasurementSnapshots(project._id)]);
      setDefinitions(definitionResult.items || []);
      setSnapshots(snapshotResult.items || []);
    } catch (reason) { setError(messageOf(reason)); }
  }, [project._id]);
  useEffect(() => { void load(); }, [load]);
  const create = async () => {
    const answer = await ask({ title: "Tạo định nghĩa đo lường", confirmLabel: "Tạo", fields: [
      { name: "key", label: "Metric", options: Object.entries(METRICS).map(([value, item]) => ({ value, label: item[0] })) },
      { name: "objective", label: "Mục tiêu", required: true, multiline: true },
      { name: "target", label: "Mục tiêu số", type: "number" },
      { name: "warning", label: "Ngưỡng cảnh báo", type: "number" },
      { name: "critical", label: "Ngưỡng nghiêm trọng", type: "number" },
    ] });
    if (!answer) return;
    const metric = METRICS[answer.key];
    try { await testingApi.createMeasurementDefinition(project._id, { idempotency_key: crypto.randomUUID(), key: answer.key, name: metric[0], objective: answer.objective, formula: metric[1], unit: metric[2], data_sources: ["testing-domain"], dimensions: ["release"], aggregation: metric[3], period: "RELEASE", target: answer.target === "" ? null : Number(answer.target), warning_threshold: answer.warning === "" ? null : Number(answer.warning), critical_threshold: answer.critical === "" ? null : Number(answer.critical), owner_role: "QA_LEAD" }); await load(); } catch (reason) { setError(messageOf(reason)); }
  };
  const latestByDefinition = Object.fromEntries(snapshots.map((item) => [item.measurement_definition_id, item]));
  const selectedSnapshots = snapshots.filter((item) => !selectedKey || item.measurement_key === selectedKey);
  return (
    <Panel title="Đo lường chất lượng" actions={can("measurement.manage") ? <button className="apple-button" type="button" onClick={create}>Tạo định nghĩa</button> : null}>
      {dialog}{error && <div className="p-4"><ErrorState message={error} /></div>}
      <div className="grid gap-3 p-5 lg:grid-cols-3">{definitions.filter((item) => item.status === "ACTIVE").map((item) => <QualityMetricCard definition={item} snapshot={latestByDefinition[item._id]} key={item._id} />)}</div>
      <DataTable items={definitions} empty="Chưa có định nghĩa đo lường" columns={[
        { key: "name", label: "Metric" }, { key: "version", label: "Phiên bản" }, { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> },
        { key: "actions", label: "Thao tác", render: (item) => <div className="flex gap-2">{item.status === "DRAFT" && can("measurement.manage") && <button className="secondary-button" type="button" onClick={async () => { await testingApi.transitionMeasurementDefinition(item._id, { expected_revision: item.revision, status: "ACTIVE", note: "Kích hoạt định nghĩa" }); await load(); }}>Kích hoạt</button>}{item.status === "ACTIVE" && can("measurement.snapshot.create") && <button className="secondary-button" type="button" onClick={async () => { try { await testingApi.createMeasurementSnapshot(project._id, { definition_id: item._id, idempotency_key: crypto.randomUUID(), dimensions: {} }); setSelectedKey(item.key); await load(); } catch (reason) { setError(messageOf(reason)); } }}>Đo ngay</button>}</div> },
      ]} />
      <div className="p-5"><MetricTrendChart snapshots={selectedSnapshots} /></div>
    </Panel>
  );
}
