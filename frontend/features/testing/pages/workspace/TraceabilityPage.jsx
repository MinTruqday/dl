"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import {
  ErrorState,
  Metric,
  Panel,
  ProjectCrumb,
  QaPage,
  StatusPill,
  useQaActionDialog,
} from "../../components/QaUi";
import { qaApi } from "../../services/qa.service";
import { formatDate, messageOf } from "../../lib/qa";

export default function TraceabilityPage({ project }) {
  const { ask, dialog } = useQaActionDialog();
  const [matrix, setMatrix] = useState({ trace_links: [], requirements: [], test_cases: [] });
  const [coverage, setCoverage] = useState({});
  const [snapshots, setSnapshots] = useState([]);
  const [linkForm, setLinkForm] = useState({ source_id: "", target_id: "" });
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    try {
      const [traceValue, coverageValue, snapshotValues] = await Promise.all([
        qaApi.traceability(project._id),
        qaApi.coverage(project._id),
        qaApi.listCoverageSnapshots(project._id),
      ]);
      setMatrix(traceValue);
      setCoverage(coverageValue);
      setSnapshots(snapshotValues);
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
          <button
            className="secondary-button"
            type="button"
            onClick={async () => {
              const answer = await ask({
                title: "Lưu ảnh chụp độ phủ",
                description: "Ảnh chụp giữ nguyên các chỉ số tại thời điểm hiện tại để đối chiếu release",
                confirmLabel: "Lưu ảnh chụp",
                fields: [
                  {
                    name: "label",
                    label: "Tên ảnh chụp",
                    initialValue: "Độ phủ hiện tại",
                    required: true,
                    autoFocus: true,
                  },
                ],
              });
              if (!answer) return;
              try {
                await qaApi.createCoverageSnapshot(project._id, {
                  label: answer.label,
                  idempotency_key: crypto.randomUUID(),
                });
                await load();
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          >
            Lưu ảnh chụp độ phủ
          </button>
          <ProjectCrumb projectId={project._id} />
        </div>
      }
    >
      {error && <ErrorState message={error} />}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <Metric label="Độ phủ yêu cầu" value={`${coverage.requirement_coverage || 0}%`} />
        <Metric
          label="Độ phủ tiêu chí chấp nhận"
          value={`${coverage.acceptance_criterion_coverage || 0}%`}
        />
        <Metric label="Độ phủ còn hiệu lực" value={`${coverage.fresh_coverage || 0}%`} />
        <Metric label="Độ phủ thực thi" value={`${coverage.execution_coverage || 0}%`} />
        <Metric label="Ca kiểm thử chưa liên kết" value={coverage.unlinked_tests?.length || 0} />
      </div>
      <Panel title="Tạo liên kết thủ công">
        <form
          className="grid gap-3 p-5 md:grid-cols-[1fr_1fr_auto]"
          onSubmit={async (event) => {
            event.preventDefault();
            try {
              await qaApi.createTrace({
                project_id: project._id,
                source_type: "requirement_version",
                source_id: linkForm.source_id,
                target_type: "test_case_version",
                target_id: linkForm.target_id,
                link_type: "verifies",
                confidence: 1,
                origin: "manual",
                evidence: [],
              });
              setLinkForm({ source_id: "", target_id: "" });
              await load();
            } catch (reason) {
              setError(messageOf(reason));
            }
          }}
        >
          <select
            aria-label="Phiên bản yêu cầu nguồn"
            className="apple-input"
            required
            value={linkForm.source_id}
            onChange={(event) => setLinkForm({ ...linkForm, source_id: event.target.value })}
          >
            <option value="">Chọn phiên bản yêu cầu</option>
            {(matrix.requirement_versions || []).map((item) => (
              <option key={item._id} value={item._id}>
                {item.requirement_key} v{item.version} {item.title}
              </option>
            ))}
          </select>
          <select
            aria-label="Phiên bản ca kiểm thử đích"
            className="apple-input"
            required
            value={linkForm.target_id}
            onChange={(event) => setLinkForm({ ...linkForm, target_id: event.target.value })}
          >
            <option value="">Chọn phiên bản ca kiểm thử</option>
            {(matrix.test_case_versions || []).map((item) => (
              <option key={item._id} value={item._id}>
                {item.test_case_key} v{item.version} {item.title}
              </option>
            ))}
          </select>
          <button className="apple-button" type="submit">
            Tạo liên kết
          </button>
        </form>
      </Panel>
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
              key: "freshness",
              label: "Hiệu lực",
              render: (item) => {
                const testCase = (matrix.test_cases || []).find(
                  (value) => value.current_version_id === item.target_id,
                );
                return <StatusPill value={testCase?.status || "HISTORICAL"} />;
              },
            },
            {
              key: "latest_execution",
              label: "Thực thi mới nhất",
              render: (item) => {
                const result = coverage.latest_execution?.[item.target_id];
                return result ? <StatusPill value={result.status} /> : "Chưa thực thi";
              },
            },
            {
              key: "defects",
              label: "Lỗi đang mở",
              render: (item) =>
                (matrix.defects || []).filter(
                  (defect) => defect.linked_test_case_version_id === item.target_id,
                ).length,
            },
            {
              key: "status",
              label: "Trạng thái",
              render: (item) => (
                <span className="flex flex-col items-start gap-1">
                  <StatusPill value={item.status} />
                  {item.obsolete && (
                    <span className="text-[11px] font-semibold text-danger">
                      Liên kết đến dữ liệu không còn hiệu lực
                    </span>
                  )}
                </span>
              ),
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
                ) : item.status === "CONFIRMED" ? (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={async () => {
                      try {
                        await qaApi.revokeTrace(item._id);
                        await load();
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    Thu hồi
                  </button>
                ) : (
                  ""
                ),
            },
          ]}
        />
      </Panel>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Yêu cầu chưa được phủ">
          <DataTable
            items={coverage.uncovered_requirements || []}
            empty="Tất cả yêu cầu hiện hành đã có liên kết xác nhận"
            columns={[
              { key: "requirement_key", label: "Mã" },
              { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> },
            ]}
          />
        </Panel>
        <Panel title="Ca kiểm thử chưa liên kết">
          <DataTable
            items={coverage.unlinked_tests || []}
            empty="Tất cả ca kiểm thử hiện hành đã được liên kết"
            columns={[
              { key: "test_case_key", label: "Mã" },
              { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> },
            ]}
          />
        </Panel>
      </div>
      <Panel title="Lịch sử ảnh chụp độ phủ">
        <DataTable
          items={snapshots}
          empty="Chưa có ảnh chụp độ phủ"
          columns={[
            { key: "label", label: "Tên" },
            {
              key: "requirement_coverage",
              label: "Yêu cầu",
              render: (item) => `${item.metrics?.requirement_coverage || 0}%`,
            },
            {
              key: "fresh_coverage",
              label: "Còn hiệu lực",
              render: (item) => `${item.metrics?.fresh_coverage || 0}%`,
            },
            {
              key: "execution_coverage",
              label: "Thực thi",
              render: (item) => `${item.metrics?.execution_coverage || 0}%`,
            },
            { key: "created_at", label: "Thời điểm", render: (item) => formatDate(item.created_at) },
          ]}
        />
      </Panel>
      {dialog}
    </QaPage>
  );
}
