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
} from "../../components/TestingUi";
import { testingApi } from "../../services/testing.service";
import { formatDate, messageOf } from "../../lib/testing";

export default function DashboardPage({ project }) {
  const [value, setValue] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([testingApi.dashboard(project._id), testingApi.coverage(project._id)])
      .then(([dashboard, coverage]) => setValue({ ...dashboard, ...coverage }))
      .catch((reason) => setError(messageOf(reason)));
  }, [project._id]);
  const base = `/qa/projects/${project._id}`;
  return (
    <QaPage
      title={project.name}
      description={project.description}
      actions={<ProjectCrumb projectId={project._id} projectName="Tổng quan dự án" />}
    >
      {error && <ErrorState message={error} />}
      {!value ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <Metric label="Yêu cầu" value={value.requirements} />
            <Metric label="Kiểm thử đang hoạt động" value={value.active_tests} />
            <Metric label="Kiểm thử cần cập nhật" value={value.tests_needing_update} />
            <Metric label="Lỗi đang mở" value={value.open_defects} />
            <Metric label="Độ phủ yêu cầu" value={`${value.requirement_coverage}%`} />
            <Metric
              label="Độ phủ tiêu chí chấp nhận"
              value={`${value.acceptance_criterion_coverage}%`}
            />
            <Metric label="Độ phủ còn hiệu lực" value={`${value.fresh_coverage}%`} />
            <Metric label="Độ phủ thực thi" value={`${value.execution_coverage}%`} />
            <Metric label="Đề xuất chờ duyệt" value={value.pending_proposals} />
            <Metric label="Lần chạy hiện tại" value={value.current_runs} />
            <Metric label="Thay đổi chờ rà soát" value={value.changes_waiting_impact} />
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <Panel title="Luồng công việc" className="lg:col-span-2">
              <div className="grid gap-3 p-5 sm:grid-cols-2">
                {[
                  ["requirements", "Yêu cầu và phiên bản chuẩn"],
                  ["test-design", "Kịch bản và ca kiểm thử"],
                  ["traceability", "Truy vết và độ phủ"],
                  ["changes", "Ảnh hưởng thay đổi và đề xuất"],
                  ["ai-review", "Hàng đợi rà soát AI"],
                  ["execution", "Kế hoạch và lần chạy"],
                  ["defects", "Vòng đời lỗi"],
                  ["reports", "Báo cáo chất lượng"],
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
                  Mở kho tri thức
                </Link>
              </div>
            </Panel>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <Panel title="Lỗi đang mở theo mức độ">
              <div className="grid grid-cols-2 gap-3 p-5 sm:grid-cols-5">
                {Object.entries(value.open_defects_by_severity || {}).map(([severity, count]) => (
                  <div className="rounded-xl border border-border p-3" key={severity}>
                    <p className="text-[11px] text-ink-muted">{severity}</p>
                    <p className="mt-1 text-xl font-semibold">{count}</p>
                  </div>
                ))}
              </div>
            </Panel>
            <Panel title="Lần chạy mới nhất">
              {value.latest_run ? (
                <div className="space-y-3 p-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <Link
                      className="font-semibold text-brand"
                      href={`${base}/execution/${value.latest_run._id}`}
                    >
                      {value.latest_run.name}
                    </Link>
                    <StatusPill value={value.latest_run.status} />
                  </div>
                  <p className="text-[12px] text-ink-muted">
                    Build {value.latest_run.build || "Chưa đặt"} tại {value.latest_run.environment || "Chưa đặt"}
                  </p>
                  <div className="flex flex-wrap gap-3 text-[12px]">
                    {Object.entries(value.latest_run.result_counts || {}).map(([status, count]) => (
                      <span className="rounded-full border border-border px-3 py-1" key={status}>
                        {status} {count}
                      </span>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="p-5 text-[13px] text-ink-muted">Chưa có lần chạy</p>
              )}
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
