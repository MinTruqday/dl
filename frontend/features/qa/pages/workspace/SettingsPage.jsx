"use client";
import { useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import { ErrorState, Panel, ProjectCrumb, QaPage } from "../../components/QaUi";
import { qaApi } from "../../services/qa.service";
import { formatDate, messageOf } from "../../lib/qa";

export default function SettingsPage({ project, onProjectChange }) {
  const [audit, setAudit] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description || "");
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([qaApi.audit(project._id), qaApi.maintenanceAnalytics(project._id)])
      .then(([events, value]) => {
        setAudit(events);
        setAnalytics(value);
      })
      .catch((reason) => setError(messageOf(reason)));
  }, [project._id]);
  return (
    <QaPage
      title="Cài đặt và kiểm toán"
      description="Cấu hình an toàn theo phiên bản và ghi lại mọi quyết định quan trọng trong nhật ký"
      actions={<ProjectCrumb projectId={project._id} />}
    >
      {error && <ErrorState message={error} />}
      <div className="grid gap-5 xl:grid-cols-2">
        <Panel title="Thông tin dự án">
          <form
            className="space-y-4 p-5"
            onSubmit={async (event) => {
              event.preventDefault();
              try {
                await qaApi.updateProject(project._id, {
                  expected_revision: project.revision,
                  name,
                  description,
                });
                await onProjectChange();
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          >
            <label className="field-label">
              Tên
              <input
                className="apple-input mt-2"
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </label>
            <label className="field-label">
              Mô tả
              <textarea
                className="apple-input mt-2 min-h-28"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
              />
            </label>
            <button className="apple-button" type="submit">
              Lưu với phiên bản {project.revision}
            </button>
          </form>
        </Panel>
        <Panel title="Phân tích bảo trì">
          <div className="grid grid-cols-2 gap-4 p-5">
            <div>
              <p className="text-3xl font-semibold">{analytics?.impact_analysis_count || 0}</p>
              <p className="field-label mt-2">Phân tích ảnh hưởng</p>
            </div>
            <div>
              <p className="text-3xl font-semibold">{analytics?.tests_stale || 0}</p>
              <p className="field-label mt-2">Ca kiểm thử cũ</p>
            </div>
            <div>
              <p className="text-3xl font-semibold">
                {analytics?.proposal_acceptance_rate == null
                  ? "N/A"
                  : `${Math.round(analytics.proposal_acceptance_rate * 100)}%`}
              </p>
              <p className="field-label mt-2">Tỷ lệ chấp nhận đề xuất</p>
            </div>
          </div>
        </Panel>
      </div>
      <Panel title="Audit log bất biến">
        <DataTable
          items={audit}
          empty="Chưa có sự kiện"
          columns={[
            { key: "action", label: "Hành động" },
            { key: "artifact_type", label: "Loại dữ liệu" },
            { key: "artifact_id", label: "Mã" },
            { key: "actor_id", label: "Người thực hiện" },
            {
              key: "created_at",
              label: "Thời điểm",
              render: (item) => formatDate(item.created_at),
            },
          ]}
        />
      </Panel>
    </QaPage>
  );
}
