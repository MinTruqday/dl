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
      eyebrow={`${project.key} · Settings`}
      title="Cài đặt và kiểm toán"
      description="Cấu hình dùng optimistic concurrency và mọi quyết định quan trọng đều được ghi vào audit log"
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
              Lưu bằng revision {project.revision}
            </button>
          </form>
        </Panel>
        <Panel title="Maintenance analytics">
          <div className="grid grid-cols-2 gap-4 p-5">
            <div>
              <p className="text-3xl font-semibold">{analytics?.impact_analysis_count || 0}</p>
              <p className="field-label mt-2">Impact Analysis</p>
            </div>
            <div>
              <p className="text-3xl font-semibold">{analytics?.tests_stale || 0}</p>
              <p className="field-label mt-2">Test stale</p>
            </div>
            <div>
              <p className="text-3xl font-semibold">
                {analytics?.proposal_acceptance_rate == null
                  ? "N/A"
                  : `${Math.round(analytics.proposal_acceptance_rate * 100)}%`}
              </p>
              <p className="field-label mt-2">Proposal acceptance</p>
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
            { key: "artifact_type", label: "Artifact" },
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
