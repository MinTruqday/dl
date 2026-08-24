"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import {
  ErrorState,
  LoadingState,
  Metric,
  Panel,
  ProjectCrumb,
  QaPage,
  StatusPill,
} from "../../components/QaUi";
import { qaApi } from "../../services/qa.service";
import { formatDate, messageOf } from "../../lib/qa";

export default function DashboardPage({ project }) {
  const [value, setValue] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    qaApi
      .dashboard(project._id)
      .then(setValue)
      .catch((reason) => setError(messageOf(reason)));
  }, [project._id]);
  const base = `/qa/projects/${project._id}`;
  return (
    <QaPage
      eyebrow={project.key}
      title={project.name}
      description={project.description || "Trung tâm kiểm soát chất lượng và thay đổi"}
      actions={<ProjectCrumb projectId={project._id} projectName="Tổng quan dự án" />}
    >
      {error && <ErrorState message={error} />}
      {!value ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Metric label="Requirement" value={value.requirements} />
            <Metric label="Test Case đang hoạt động" value={value.active_tests} />
            <Metric label="Test cần cập nhật" value={value.tests_needing_update} />
            <Metric label="Defect đang mở" value={value.open_defects} />
            <Metric label="Coverage Requirement" value={`${value.requirement_coverage}%`} />
            <Metric
              label="Coverage Acceptance Criteria"
              value={`${value.acceptance_criterion_coverage}%`}
            />
            <Metric label="Đề xuất chờ duyệt" value={value.pending_proposals} />
            <Metric label="Test Run hiện tại" value={value.current_runs} />
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <Panel title="Luồng công việc" className="lg:col-span-2">
              <div className="grid gap-3 p-5 sm:grid-cols-2">
                {[
                  ["requirements", "Requirement và baseline"],
                  ["test-design", "Scenario và Test Case"],
                  ["traceability", "Traceability và coverage"],
                  ["changes", "Change impact và proposal"],
                  ["execution", "Plan Suite và Run"],
                  ["defects", "Defect lifecycle"],
                ].map(([href, label]) => (
                  <Link
                    className="rounded-control border border-border p-4 text-[13px] font-semibold hover:border-brand hover:text-brand"
                    href={`${base}/${href}`}
                    key={href}
                  >
                    {label}
                  </Link>
                ))}
              </div>
            </Panel>
            <Panel title="Tri thức dự án">
              <div className="space-y-3 p-5">
                <p className="text-[13px] leading-6 text-ink-muted">
                  Tìm theo phạm vi dự án với nguồn và phiên bản có thể kiểm chứng
                </p>
                <Link className="apple-button w-full" href={`${base}/knowledge`}>
                  Mở Knowledge Search
                </Link>
              </div>
            </Panel>
          </div>
          <Panel title="Thay đổi gần đây">
            <DataTable
              items={value.recent_changes}
              empty="Chưa có Change Set"
              columns={[
                { key: "_id", label: "Mã" },
                {
                  key: "status",
                  label: "Trạng thái",
                  render: (item) => <StatusPill value={item.status} />,
                },
                {
                  key: "created_at",
                  label: "Tạo lúc",
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
