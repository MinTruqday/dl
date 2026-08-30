"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../components/DataTable";
import PlatformOperationsPanel from "../components/PlatformOperationsPanel";
import PlatformUsersPanel from "../components/PlatformUsersPanel";
import {
  ErrorState,
  LoadingState,
  Metric,
  Panel,
  QaPage,
  StatusPill,
} from "../components/TestingUi";
import { formatDate, messageOf } from "../lib/testing";
import { testingApi } from "../services/testing.service";

const taskLabels = {
  impact_analysis: "Phân tích ảnh hưởng",
  maintenance_proposal: "Đề xuất bảo trì",
  regression: "Kiểm thử hồi quy",
};

const modelLabels = {
  "agentic-hybrid-v1": "Mô hình tác tử kết hợp phiên bản 1",
  "maintenance-agent-v1": "Mô hình bảo trì phiên bản 1",
  "risk-score-v1": "Mô hình chấm điểm rủi ro phiên bản 1",
};

export default function OperationsPage() {
  const [section, setSection] = useState("overview");
  const [value, setValue] = useState(null);
  const [error, setError] = useState("");
  const [auditQuery, setAuditQuery] = useState("");
  const load = useCallback(async () => {
    try {
      setValue(await testingApi.operations());
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);
  const retryJob = async (jobId) => {
    try {
      await testingApi.retryOperationJob(jobId);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const auditEvents = (value?.audit_events || []).filter((item) => {
    const query = auditQuery.trim().toLowerCase();
    return (
      !query ||
      [item.action, item.entity_type, item.entity_id, item.actor_id].some((field) =>
        String(field || "")
          .toLowerCase()
          .includes(query),
      )
    );
  });
  const impactMetrics = value?.ai_request_metrics?.impact_classification || {};
  const aiMetrics = [
    { _id: "impact_total", name: "Lượt phân loại ảnh hưởng", count: impactMetrics.total || 0 },
    { _id: "impact_success", name: "Lượt phân loại thành công", count: impactMetrics.success || 0 },
    { _id: "impact_degraded", name: "Lượt xử lý giới hạn", count: impactMetrics.degraded || 0 },
    {
      _id: "impact_success_rate",
      name: "Tỷ lệ thành công",
      count: `${Math.round((impactMetrics.success_rate || 0) * 100)}%`,
    },
    {
      _id: "impact_latency",
      name: "Độ trễ trung bình",
      count: `${Math.round(impactMetrics.average_latency_ms || 0)} mili giây`,
    },
    {
      _id: "proposals",
      name: "Đề xuất bảo trì",
      count: value?.ai_request_metrics?.proposals || 0,
    },
  ];
  return (
    <QaPage
      title="Quản trị nền tảng"
      actions={
        <div className="flex flex-wrap gap-2">
          {[
            ["overview", "Tổng quan vận hành"],
            ["users", "Tài khoản"],
            ["platform", "Dự án và AI"],
          ].map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={section === value ? "apple-button" : "secondary-button"}
              onClick={() => setSection(value)}
            >
              {label}
            </button>
          ))}
        </div>
      }
    >
      {error && <ErrorState message={error} />}
      {section === "users" ? (
        <PlatformUsersPanel />
      ) : section === "platform" ? (
        <PlatformOperationsPanel />
      ) : !value ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
            <Metric label="Tài liệu chờ lập chỉ mục" value={value.knowledge_indexing_backlog} />
            <Metric label="Lần nhập liệu bị lỗi" value={value.failed_ingestion_jobs.length} />
            <Metric label="Phân tích ảnh hưởng lỗi" value={value.failed_impact_jobs.length} />
            <Metric label="Lỗi xử lý nền" value={value.worker_failures.length} />
          </div>
          <div className="grid gap-5 xl:grid-cols-2">
            <Panel title="Mô hình đang hoạt động">
              <DataTable
                items={Object.entries(value.ai_models).map(([name, version]) => ({
                  _id: name,
                  name,
                  version,
                }))}
                columns={[
                  {
                    key: "name",
                    label: "Tác vụ",
                    render: (item) => taskLabels[item.name] || item.name,
                  },
                  {
                    key: "version",
                    label: "Phiên bản",
                    render: (item) => modelLabels[item.version] || item.version,
                  },
                ]}
              />
            </Panel>
            <Panel title="Số liệu AI đã ghi nhận">
              <DataTable
                items={aiMetrics}
                columns={[
                  { key: "name", label: "Loại" },
                  { key: "count", label: "Số lượng" },
                ]}
              />
            </Panel>
          </div>
          <Panel title="Lần nhập liệu bị lỗi">
            <DataTable
              items={value.failed_ingestion_jobs}
              empty="Không có lần nhập liệu bị lỗi"
              columns={[
                { key: "_id", label: "Mã" },
                {
                  key: "status",
                  label: "Trạng thái",
                  render: (item) => <StatusPill value={item.status} />,
                },
                { key: "error_code", label: "Mã lỗi" },
                {
                  key: "created_at",
                  label: "Thời điểm",
                  render: (item) => formatDate(item.created_at),
                },
              ]}
            />
          </Panel>
          <Panel title="Lỗi xử lý nền">
            <DataTable
              items={value.worker_failures}
              empty="Không có lỗi xử lý nền"
              columns={[
                { key: "_id", label: "Mã" },
                { key: "event", label: "Sự kiện" },
                { key: "error_code", label: "Mã lỗi" },
                {
                  key: "completed_at",
                  label: "Thời điểm",
                  render: (item) => formatDate(item.completed_at),
                },
                {
                  key: "retry",
                  label: "Thao tác",
                  render: (item) => (
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => retryJob(item._id)}
                    >
                      Thử lại
                    </button>
                  ),
                },
              ]}
            />
          </Panel>
          <Panel title="Dung lượng theo dự án">
            <DataTable
              items={value.storage_usage || []}
              empty="Chưa có dữ liệu dung lượng"
              columns={[
                { key: "project_key", label: "Dự án" },
                { key: "files", label: "Tệp" },
                { key: "bytes", label: "Dung lượng theo byte" },
              ]}
            />
          </Panel>
          <Panel
            title="Nhật ký hệ thống"
            actions={
              <input
                aria-label="Tìm trong nhật ký"
                id="operations-audit-query"
                className="apple-input w-full sm:w-80"
                value={auditQuery}
                onChange={(event) => setAuditQuery(event.target.value)}
                placeholder="Sự kiện mã đối tượng hoặc người thực hiện"
              />
            }
          >
            <DataTable
              items={auditEvents}
              empty="Không có sự kiện phù hợp"
              columns={[
                { key: "action", label: "Sự kiện" },
                { key: "entity_type", label: "Loại" },
                { key: "entity_id", label: "Mã" },
                { key: "actor_id", label: "Người thực hiện" },
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
    </QaPage>
  );
}
