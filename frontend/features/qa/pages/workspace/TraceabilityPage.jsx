"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import { ErrorState, Metric, Panel, ProjectCrumb, QaPage, StatusPill } from "../../components/QaUi";
import { qaApi } from "../../services/qa.service";
import { messageOf } from "../../lib/qa";

export default function TraceabilityPage({ project }) {
  const [matrix, setMatrix] = useState({ trace_links: [], requirements: [], test_cases: [] });
  const [coverage, setCoverage] = useState({});
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    try {
      const [traceValue, coverageValue] = await Promise.all([
        qaApi.traceability(project._id),
        qaApi.coverage(project._id),
      ]);
      setMatrix(traceValue);
      setCoverage(coverageValue);
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [project._id]);
  useEffect(() => {
    void load();
  }, [load]);
  const decision = async (item, accept) => {
    try {
      await (accept ? qaApi.confirmTrace(item._id) : qaApi.rejectTrace(item._id));
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <QaPage
      title="Ma trận truy vết và độ phủ"
      description="Độ phủ chỉ tính liên kết đã xác nhận và không xem đề xuất AI là sự thật"
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <button
            className="secondary-button"
            type="button"
            onClick={() =>
              qaApi.exportTraceability(project._id).catch((reason) => setError(messageOf(reason)))
            }
          >
            Xuất CSV
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={async () => {
              try {
                await qaApi.recoverTrace(project._id);
                await load();
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          >
            Khôi phục liên kết bằng AI
          </button>
          <ProjectCrumb projectId={project._id} />
        </div>
      }
    >
      {error && <ErrorState message={error} />}
      <div className="grid gap-4 sm:grid-cols-3">
        <Metric label="Độ phủ yêu cầu" value={`${coverage.requirement_coverage || 0}%`} />
        <Metric
          label="Độ phủ tiêu chí chấp nhận"
          value={`${coverage.acceptance_criterion_coverage || 0}%`}
        />
        <Metric label="Ca kiểm thử chưa liên kết" value={coverage.unlinked_tests?.length || 0} />
      </div>
      <Panel title="Liên kết truy vết">
        <DataTable
          items={matrix.trace_links || []}
          empty="Chưa có liên kết truy vết"
          columns={[
            { key: "source_type", label: "Nguồn" },
            { key: "source_id", label: "Mã nguồn" },
            { key: "target_id", label: "Phiên bản ca kiểm thử" },
            { key: "confidence", label: "Độ tin cậy" },
            {
              key: "status",
              label: "Trạng thái",
              render: (item) => <StatusPill value={item.status} />,
            },
            {
              key: "decision",
              label: "Quyết định",
              render: (item) =>
                item.status === "SUGGESTED" ? (
                  <span className="flex flex-wrap gap-2">
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => decision(item, true)}
                    >
                      Xác nhận
                    </button>
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => decision(item, false)}
                    >
                      Từ chối
                    </button>
                  </span>
                ) : (
                  ""
                ),
            },
          ]}
        />
      </Panel>
    </QaPage>
  );
}
