"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../components/DataTable";
import { ErrorState, LoadingState, Metric, Panel, QaPage, StatusPill } from "../components/TestingUi";
import { formatDate, messageOf } from "../lib/testing";
import { testingApi } from "../services/testing.service";

export default function OperationsPage() {
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
    return !query || [item.action, item.entity_type, item.entity_id, item.actor_id].some((field) => String(field || "").toLowerCase().includes(query));
  });
  return (
    <QaPage
      title="Vận hành nền tảng"
      description="Theo dõi các job lỗi hàng đợi worker backlog lập chỉ mục và phiên bản mô hình đang hoạt động"
    >
      {error && <ErrorState message={error} />}
      {!value ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
            <Metric label="Backlog lập chỉ mục knowledge" value={value.knowledge_indexing_backlog} />
            <Metric label="Job nhập liệu lỗi" value={value.failed_ingestion_jobs.length} />
            <Metric label="Phân tích ảnh hưởng lỗi" value={value.failed_impact_jobs.length} />
            <Metric label="Worker failure" value={value.worker_failures.length} />
          </div>
          <div className="grid gap-5 xl:grid-cols-2">
            <Panel title="Mô hình đang hoạt động">
              <DataTable
                items={Object.entries(value.ai_models).map(([name, version]) => ({ _id: name, name, version }))}
                columns={[{ key: "name", label: "Tác vụ" }, { key: "version", label: "Phiên bản" }]}
              />
            </Panel>
            <Panel title="Số liệu AI đã ghi nhận">
              <DataTable
                items={Object.entries(value.ai_request_metrics).map(([name, count]) => ({ _id: name, name, count }))}
                columns={[{ key: "name", label: "Loại" }, { key: "count", label: "Số lượng" }]}
              />
            </Panel>
          </div>
          <Panel title="Job nhập liệu lỗi">
            <DataTable
              items={value.failed_ingestion_jobs}
              empty="Không có job nhập liệu lỗi"
              columns={[
                { key: "_id", label: "Mã" },
                { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> },
                { key: "error_code", label: "Mã lỗi" },
                { key: "created_at", label: "Thời điểm", render: (item) => formatDate(item.created_at) },
              ]}
            />
          </Panel>
          <Panel title="Job worker lỗi">
            <div className="mb-4">
              <label className="field-label block" htmlFor="operations-audit-query">Tìm trong audit</label>
              <input id="operations-audit-query" className="apple-input mt-2" value={auditQuery} onChange={(event) => setAuditQuery(event.target.value)} placeholder="Sự kiện mã thực thể hoặc người thực hiện" />
            </div>
            <DataTable
              items={value.worker_failures}
              empty="Không có worker failure"
              columns={[
                { key: "_id", label: "Mã" },
                { key: "event", label: "Sự kiện" },
                { key: "error_code", label: "Mã lỗi" },
                { key: "completed_at", label: "Thời điểm", render: (item) => formatDate(item.completed_at) },
                { key: "retry", label: "Thao tác", render: (item) => <button className="secondary-button" type="button" onClick={() => retryJob(item._id)}>Retry</button> },
              ]}
            />
          </Panel>
          <Panel title="Dung lượng theo dự án">
            <DataTable
              items={value.storage_usage || []}
              empty="Chưa có dữ liệu dung lượng"
              columns={[{ key: "project_key", label: "Dự án" }, { key: "files", label: "Tệp" }, { key: "bytes", label: "Byte" }]}
            />
          </Panel>
          <Panel title="Audit hệ thống">
            <DataTable
              items={auditEvents}
              empty="Không có audit phù hợp"
              columns={[{ key: "action", label: "Sự kiện" }, { key: "entity_type", label: "Loại" }, { key: "entity_id", label: "Mã" }, { key: "actor_id", label: "Người thực hiện" }, { key: "created_at", label: "Thời điểm", render: (item) => formatDate(item.created_at) }]}
            />
          </Panel>
        </>
      )}
    </QaPage>
  );
}
