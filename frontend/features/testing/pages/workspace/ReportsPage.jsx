"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import {
  ErrorState,
  LoadingState,
  Metric,
  Panel,
  ProjectCrumb,
  QaPage,
  useQaActionDialog,
} from "../../components/TestingUi";
import { formatDate, messageOf, valueLabel } from "../../lib/testing";
import { testingApi } from "../../services/testing.service";

export default function ReportsPage({ project }) {
  const { ask, dialog } = useQaActionDialog();
  const [value, setValue] = useState(null);
  const [scope, setScope] = useState({ release: "", environment: "", build: "" });
  const [error, setError] = useState("");
  const canReadAiAnalytics = project.current_permissions?.includes("analytics.ai.read");
  const canCreateSnapshot = project.current_permissions?.includes("coverage.snapshot.create");
  const load = useCallback(async () => {
    try {
      const [dashboard, coverage, snapshots, maintenance, ai, execution, defects, activity] =
        await Promise.all([
          testingApi.dashboard(project._id),
          testingApi.coverage(project._id, scope),
          testingApi.listCoverageSnapshots(project._id),
          testingApi.maintenanceAnalytics(project._id),
          canReadAiAnalytics ? testingApi.aiAnalytics(project._id) : Promise.resolve(null),
          testingApi.executionReport(project._id, scope),
          testingApi.defectReport(project._id, scope),
          testingApi.projectActivity(project._id),
        ]);
      setValue({ dashboard, coverage, snapshots, maintenance, ai, execution, defects, activity });
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [canReadAiAnalytics, project._id, scope]);
  useEffect(() => {
    void load();
  }, [load]);
  return (
    <QaPage title="Báo cáo chất lượng" actions={<ProjectCrumb projectId={project._id} />}>
      {error && <ErrorState message={error} />}
      <Panel
        title="Phạm vi báo cáo"
        actions={
          canCreateSnapshot ? (
            <button
              className="apple-button"
              type="button"
              onClick={async () => {
                const answer = await ask({
                  title: "Lưu ảnh chụp độ phủ",
                  description: `Bản phát hành ${scope.release || "tất cả"} bản dựng ${scope.build || "tất cả"}`,
                  confirmLabel: "Lưu ảnh chụp",
                  fields: [
                    { name: "label", label: "Tên ảnh chụp", required: true, autoFocus: true },
                  ],
                });
                if (!answer) return;
                try {
                  await testingApi.createCoverageSnapshot(project._id, {
                    label: answer.label,
                    release: scope.release,
                    build: scope.build,
                    idempotency_key: crypto.randomUUID(),
                  });
                  await load();
                } catch (reason) {
                  setError(messageOf(reason));
                }
              }}
            >
              Lưu ảnh chụp
            </button>
          ) : null
        }
      >
        <div className="grid gap-3 p-5 sm:grid-cols-3">
          <input
            aria-label="Lọc theo môi trường"
            className="apple-input"
            placeholder="Môi trường"
            value={scope.environment}
            onChange={(event) => setScope({ ...scope, environment: event.target.value })}
          />
          <input
            aria-label="Lọc theo bản phát hành"
            className="apple-input"
            placeholder="Bản phát hành"
            value={scope.release}
            onChange={(event) => setScope({ ...scope, release: event.target.value })}
          />
          <input
            aria-label="Lọc theo bản dựng"
            className="apple-input"
            placeholder="Bản dựng"
            value={scope.build}
            onChange={(event) => setScope({ ...scope, build: event.target.value })}
          />
        </div>
      </Panel>
      {!value ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
            <Metric label="Độ phủ yêu cầu" value={`${value.coverage.requirement_coverage}%`} />
            <Metric
              label="Độ phủ tiêu chí chấp nhận"
              value={`${value.coverage.acceptance_criterion_coverage}%`}
            />
            <Metric label="Độ phủ còn hiệu lực" value={`${value.coverage.fresh_coverage}%`} />
            <Metric label="Độ phủ thực thi" value={`${value.coverage.execution_coverage}%`} />
            <Metric label="Ca kiểm thử cần cập nhật" value={value.coverage.stale_tests} />
            <Metric label="Lỗi đang mở" value={value.dashboard.open_defects} />
            <Metric
              label="Tỷ lệ kiểm thử đạt"
              value={
                value.execution.pass_rate === null
                  ? "Chưa đủ dữ liệu"
                  : `${Math.round(value.execution.pass_rate * 100)}%`
              }
            />
            <Metric label="Số lần mở lại lỗi" value={value.defects.reopened_count} />
            <Metric
              label="Tuổi trung bình lỗi mở"
              value={`${value.defects.average_open_age_days} ngày`}
            />
            <Metric label="Phân tích ảnh hưởng" value={value.maintenance.impact_analysis_count} />
            {value.ai && (
              <Metric
                label="Tỷ lệ đề xuất được chấp nhận"
                value={
                  value.ai.proposal_acceptance_rate === null
                    ? "Chưa đủ dữ liệu"
                    : `${Math.round(value.ai.proposal_acceptance_rate * 100)}%`
                }
              />
            )}
            {value.ai && (
              <Metric label="Số lần điều chỉnh kết quả AI" value={value.ai.override_count} />
            )}
            {value.ai && (
              <Metric
                label="Tỷ lệ AI chạy suy giảm"
                value={`${Math.round(value.ai.degraded_rate * 100)}%`}
              />
            )}
            {value.ai && (
              <Metric
                label="Độ trễ AI trung bình"
                value={`${Math.round(value.ai.average_latency_ms)} ms`}
              />
            )}
          </div>
          <div className="grid gap-5 xl:grid-cols-2">
            <Panel title="Kết quả thực thi">
              <DataTable
                items={Object.entries(value.execution.result_counts || {}).map(
                  ([status, count]) => ({ _id: status, status, count }),
                )}
                empty="Chưa có kết quả thực thi"
                columns={[
                  { key: "status", label: "Trạng thái", render: (item) => valueLabel(item.status) },
                  { key: "count", label: "Số lượng" },
                ]}
              />
            </Panel>
            <Panel title="Lỗi theo mức độ">
              <DataTable
                items={Object.entries(value.defects.severity_counts || {}).map(
                  ([severity, count]) => ({ _id: severity, severity, count }),
                )}
                empty="Chưa có lỗi"
                columns={[
                  { key: "severity", label: "Mức độ", render: (item) => valueLabel(item.severity) },
                  { key: "count", label: "Số lượng" },
                ]}
              />
            </Panel>
          </div>
          <div className="grid gap-5 xl:grid-cols-2">
            <Panel title="Độ phủ theo kỹ thuật">
              <DataTable
                items={Object.entries(value.coverage.category_coverage || {}).map(
                  ([category, coverage]) => ({ _id: category, category, coverage }),
                )}
                empty="Chưa có dữ liệu kỹ thuật"
                columns={[
                  {
                    key: "category",
                    label: "Kỹ thuật",
                    render: (item) => valueLabel(item.category),
                  },
                  { key: "coverage", label: "Độ phủ", render: (item) => `${item.coverage}%` },
                ]}
              />
            </Panel>
            {value.ai && (
              <Panel title="Trạng thái đề xuất AI">
                <DataTable
                  items={(value.ai.proposal_status || []).map((item) => ({
                    ...item,
                    status: item._id,
                  }))}
                  empty="Chưa có đề xuất"
                  columns={[
                    {
                      key: "status",
                      label: "Trạng thái",
                      render: (item) => valueLabel(item.status),
                    },
                    { key: "count", label: "Số lượng" },
                  ]}
                />
              </Panel>
            )}
            {value.ai && (
              <Panel title="Phiên bản mô hình AI">
                <DataTable
                  items={Object.entries(value.ai.model_versions || {}).map(([model, count]) => ({
                    _id: model,
                    model,
                    count,
                  }))}
                  empty="Chưa có lần chạy AI"
                  columns={[
                    { key: "model", label: "Mô hình" },
                    { key: "count", label: "Số lần chạy" },
                  ]}
                />
              </Panel>
            )}
          </div>
          <Panel title="Ảnh chụp độ phủ">
            <DataTable
              items={value.snapshots}
              empty="Chưa lưu ảnh chụp"
              columns={[
                { key: "label", label: "Tên" },
                {
                  key: "created_at",
                  label: "Thời điểm",
                  render: (item) => formatDate(item.created_at),
                },
                {
                  key: "requirement_coverage",
                  label: "Độ phủ yêu cầu",
                  render: (item) => `${item.metrics?.requirement_coverage ?? 0}%`,
                },
                {
                  key: "fresh_coverage",
                  label: "Độ phủ còn hiệu lực",
                  render: (item) => `${item.metrics?.fresh_coverage ?? 0}%`,
                },
                {
                  key: "execution_coverage",
                  label: "Độ phủ thực thi",
                  render: (item) => `${item.metrics?.execution_coverage ?? 0}%`,
                },
              ]}
            />
          </Panel>
          <Panel title="Hoạt động chất lượng gần đây">
            <DataTable
              items={value.activity}
              empty="Chưa có hoạt động"
              columns={[
                { key: "action", label: "Hành động", render: (item) => valueLabel(item.action) },
                {
                  key: "entity_type",
                  label: "Loại dữ liệu",
                  render: (item) => valueLabel(item.entity_type),
                },
                { key: "entity_id", label: "Mã" },
                {
                  key: "created_at",
                  label: "Thời điểm",
                  render: (item) => formatDate(item.created_at),
                },
              ]}
            />
          </Panel>
        </>
      )}
      {dialog}
    </QaPage>
  );
}
