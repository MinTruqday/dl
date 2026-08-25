"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import { ErrorState, Panel, ProjectCrumb, QaPage, StatusPill } from "../../components/QaUi";
import { qaApi } from "../../services/qa.service";
import { messageOf, valueLabel } from "../../lib/qa";

export default function ExecutionPage({ project, section }) {
  const runId = section[0] || "";
  const [plans, setPlans] = useState([]);
  const [suites, setSuites] = useState([]);
  const [runs, setRuns] = useState([]);
  const [tests, setTests] = useState([]);
  const [run, setRun] = useState(null);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const load = useCallback(async () => {
    try {
      const [planValues, suiteValues, runValues, testValues] = await Promise.all([
        qaApi.listPlans(project._id),
        qaApi.listSuites(project._id),
        qaApi.listRuns(project._id),
        qaApi.listTestCases(project._id),
      ]);
      setPlans(planValues);
      setSuites(suiteValues);
      setRuns(runValues);
      setTests(testValues);
      if (runId) setRun(await qaApi.getRun(runId));
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [project._id, runId]);
  useEffect(() => {
    void load();
  }, [load]);
  const versions = tests.map((item) => item.current_version_id).filter(Boolean);
  const createRun = async (event) => {
    event.preventDefault();
    try {
      await qaApi.createRun({
        project_id: project._id,
        name,
        test_plan_id: plans[0]?._id || null,
        test_suite_ids: [],
        test_case_version_ids: versions,
        environment: "staging",
        build: "local",
      });
      setName("");
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const record = async (versionId, status) => {
    try {
      await qaApi.recordResult(run._id, versionId, {
        status,
        step_results: [],
        attachments: [],
        note: "Kết quả thực thi thủ công",
        idempotency_key: crypto.randomUUID(),
      });
      setRun(await qaApi.getRun(run._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  if (run)
    return (
      <QaPage
        title={run.name}
        description={`Ảnh chụp bất biến gồm ${run.test_case_version_ids.length} phiên bản ca kiểm thử`}
        actions={<ProjectCrumb projectId={project._id} />}
      >
        {error && <ErrorState message={error} />}
        <Panel
          title="Điều khiển lần chạy"
          actions={
            <div className="flex flex-wrap gap-2">
              <button
                className="secondary-button"
                type="button"
                onClick={() =>
                  qaApi.exportRunReport(run._id).catch((reason) => setError(messageOf(reason)))
                }
              >
                Xuất báo cáo
              </button>
              {run.status === "DRAFT" && (
                <button
                  className="apple-button"
                  type="button"
                  onClick={async () => {
                    try {
                      setRun(await qaApi.startRun(run._id));
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                >
                  Bắt đầu
                </button>
              )}
              {run.status === "IN_PROGRESS" && (
                <button
                  className="apple-button"
                  type="button"
                  onClick={async () => {
                    try {
                      setRun(await qaApi.completeRun(run._id));
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                >
                  Hoàn tất
                </button>
              )}
            </div>
          }
        >
          <div className="p-5">
            <StatusPill value={run.status} />
          </div>
        </Panel>
        <Panel title="Kết quả thủ công">
          <DataTable
            items={run.test_case_versions || []}
            columns={[
              { key: "test_case_key", label: "Ca kiểm thử" },
              { key: "version", label: "Phiên bản", render: (item) => `v${item.version}` },
              { key: "title", label: "Tên" },
              {
                key: "result",
                label: "Kết quả",
                render: (item) => {
                  const result = run.results?.find(
                    (value) => value.test_case_version_id === item._id,
                  );
                  return result ? (
                    <StatusPill value={result.status} />
                  ) : run.status === "IN_PROGRESS" ? (
                    <span className="flex flex-wrap gap-2">
                      {["PASS", "FAIL", "BLOCKED", "SKIPPED"].map((value) => (
                        <button
                          className="secondary-button"
                          type="button"
                          key={value}
                          onClick={() => record(item._id, value)}
                        >
                          {value}
                        </button>
                      ))}
                    </span>
                  ) : (
                    "Chưa chạy"
                  );
                },
              },
            ]}
          />
        </Panel>
      </QaPage>
    );
  return (
    <QaPage
      title="Kế hoạch, bộ kiểm thử và lần chạy"
      description="Mỗi lần chạy giữ đúng ảnh chụp các phiên bản ca kiểm thử tại thời điểm tạo"
      actions={<ProjectCrumb projectId={project._id} />}
    >
      {error && <ErrorState message={error} />}
      <div className="grid gap-5 xl:grid-cols-3">
        <Panel title="Tạo kế hoạch kiểm thử">
          <form
            className="space-y-3 p-5"
            onSubmit={async (event) => {
              event.preventDefault();
              const value = new FormData(event.currentTarget);
              try {
                await qaApi.createPlan({
                  project_id: project._id,
                  name: value.get("name"),
                  objective: value.get("objective"),
                  scope_in: [],
                  scope_out: [],
                  environment: "staging",
                  entry_criteria: [],
                  exit_criteria: [],
                  risks: [],
                  test_types: ["functional"],
                  members: [],
                  release: "",
                  build: "",
                });
                event.currentTarget.reset();
                await load();
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          >
            <input
              aria-label="Tên kế hoạch kiểm thử"
              name="name"
              required
              className="apple-input"
              placeholder="Tên kế hoạch kiểm thử"
            />
            <textarea
              aria-label="Mục tiêu kế hoạch kiểm thử"
              name="objective"
              className="apple-input min-h-20"
              placeholder="Mục tiêu"
            />
            <button className="secondary-button" type="submit">
              Lưu kế hoạch
            </button>
          </form>
        </Panel>
        <Panel title="Tạo bộ kiểm thử">
          <form
            className="space-y-3 p-5"
            onSubmit={async (event) => {
              event.preventDefault();
              const value = new FormData(event.currentTarget);
              try {
                await qaApi.createSuite({
                  project_id: project._id,
                  name: value.get("name"),
                  suite_type: value.get("type"),
                  test_case_version_ids: versions,
                });
                event.currentTarget.reset();
                await load();
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          >
            <input
              aria-label="Tên bộ kiểm thử"
              name="name"
              required
              className="apple-input"
              placeholder="Tên bộ kiểm thử"
            />
            <select aria-label="Loại bộ kiểm thử" name="type" className="apple-input">
              <option value="smoke">{valueLabel("smoke")}</option>
              <option value="regression">{valueLabel("regression")}</option>
              <option value="feature">{valueLabel("feature")}</option>
            </select>
            <button className="secondary-button" type="submit">
              Lưu bộ kiểm thử
            </button>
          </form>
        </Panel>
        <Panel title="Tạo lần chạy">
          <form className="space-y-3 p-5" onSubmit={createRun}>
            <input
              aria-label="Tên lần chạy"
              required
              className="apple-input"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Tên lần chạy"
            />
            <p className="text-[12px] text-ink-muted">
              Snapshot {versions.length} phiên bản hiện tại
            </p>
            <button className="apple-button" type="submit">
              Tạo lần chạy
            </button>
          </form>
        </Panel>
      </div>
      <Panel title="Danh sách lần chạy">
        <DataTable
          onSelect={(item) =>
            window.location.assign(`/qa/projects/${project._id}/execution/${item._id}`)
          }
          items={runs}
          empty="Chưa có lần chạy"
          columns={[
            { key: "name", label: "Tên" },
            { key: "environment", label: "Môi trường" },
            { key: "build", label: "Build" },
            {
              key: "count",
              label: "Số ca kiểm thử",
              render: (item) => item.test_case_version_ids.length,
            },
            {
              key: "status",
              label: "Trạng thái",
              render: (item) => <StatusPill value={item.status} />,
            },
          ]}
        />
      </Panel>
    </QaPage>
  );
}
