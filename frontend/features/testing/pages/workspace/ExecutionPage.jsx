"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import { uploadAssetAPI } from "@/features/cloud/services/upload.service";
import {
  ErrorState,
  Pagination,
  Panel,
  ProjectCrumb,
  QaPage,
  StatusPill,
  useQaActionDialog,
} from "../../components/TestingUi";
import { testingApi } from "../../services/testing.service";
import { docText, messageOf, textDoc, valueLabel } from "../../lib/testing";

export default function ExecutionPage({ project, section }) {
  const { ask, dialog } = useQaActionDialog();
  const runId = section[0] || "";
  const [plans, setPlans] = useState([]);
  const [suites, setSuites] = useState([]);
  const [runs, setRuns] = useState([]);
  const [runPage, setRunPage] = useState(1);
  const [runPageInfo, setRunPageInfo] = useState(null);
  const [runFilters, setRunFilters] = useState({
    name: "",
    status: "",
    environment: "",
    sort: "-updated_at",
  });
  const [planFilters, setPlanFilters] = useState({
    q: "",
    release: "",
    status: "",
    sort: "-updated_at",
  });
  const [suiteFilters, setSuiteFilters] = useState({
    q: "",
    suite_type: "",
    status: "",
    sort: "-updated_at",
  });
  const [tests, setTests] = useState([]);
  const [run, setRun] = useState(null);
  const [error, setError] = useState("");
  const [runForm, setRunForm] = useState({
    name: "",
    release: "",
    build: "",
    environment: "staging",
    testPlanId: "",
    suiteIds: [],
    versionIds: [],
  });
  const [actuals, setActuals] = useState({});
  const [stepResults, setStepResults] = useState({});
  const [attachments, setAttachments] = useState({});
  const can = (permission) => project.current_permissions?.includes(permission);
  const load = useCallback(async () => {
    try {
      const [planValues, suiteValues, runValues, testValues] = await Promise.all([
        testingApi.listPlans(project._id, planFilters),
        testingApi.listSuites(project._id, suiteFilters),
        testingApi.listRunPage(project._id, { ...runFilters, page: runPage, page_size: 50 }),
        testingApi.listTestCases(project._id, { page_size: 500 }),
      ]);
      setPlans(planValues);
      setSuites(suiteValues);
      setRuns(runValues.items);
      setRunPageInfo(runValues);
      setTests(testValues);
      if (runId) setRun(await testingApi.getRun(runId));
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [planFilters, project._id, runFilters, runId, runPage, suiteFilters]);
  useEffect(() => {
    void load();
  }, [load]);
  const versions = tests.map((item) => item.current_version_id).filter(Boolean);
  const createRun = async (event) => {
    event.preventDefault();
    try {
      await testingApi.createRun({
        project_id: project._id,
        name: runForm.name,
        test_plan_id: runForm.testPlanId || null,
        test_suite_ids: runForm.suiteIds,
        test_case_version_ids: runForm.versionIds,
        environment: runForm.environment,
        release: runForm.release,
        build: runForm.build,
      });
      setRunForm({
        name: "",
        release: "",
        build: "",
        environment: "staging",
        testPlanId: "",
        suiteIds: [],
        versionIds: [],
      });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const transition = async (execution, status, version) => {
    try {
      const values = (version.steps || []).map((step) => {
        const existing = execution.step_results?.find((item) => item.step_id === step.id);
        const edited = stepResults[execution._id]?.[step.id];
        return {
          step_id: step.id,
          status: edited?.status || existing?.status || "PASS",
          actual_doc: textDoc(edited?.actual || docText(existing?.actual_doc)),
          attachments: existing?.attachments || [],
          note: existing?.note || "",
        };
      });
      await testingApi.updateExecution(project._id, execution._id, {
        status,
        step_results: status === "IN_PROGRESS" ? execution.step_results || [] : values,
        actual_result_doc: textDoc(actuals[execution._id] || docText(execution.actual_result_doc)),
        attachments: attachments[execution._id] || execution.attachments || [],
        note: "Kết quả thực thi thủ công",
        idempotency_key: crypto.randomUUID(),
        expected_revision: execution.revision,
      });
      setRun(await testingApi.getRun(run._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const createDefectFromResult = async (result, version) => {
    try {
      await testingApi.createDefect(project._id, {
        project_id: project._id,
        title: `Lỗi khi thực thi ${version.test_case_key} ${version.title}`,
        description_doc: textDoc(`Phát hiện trong lần chạy ${run.name}`),
        steps_to_reproduce: version.steps || [],
        actual_result_doc: result.actual_result_doc || textDoc(""),
        expected_result_doc: version.expected_result_doc || textDoc(""),
        severity: "major",
        priority: version.priority || "medium",
        environment: run.environment || "",
        build: run.build || "",
        attachments: result.attachments || [],
        linked_test_result_id: result._id,
        linked_test_case_version_id: version._id,
        linked_requirement_version_ids: version.requirement_version_ids || [],
      });
      setRun(await testingApi.getRun(run._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const updatePlan = async (item) => {
    const answer = await ask({
      title: "Sửa kế hoạch kiểm thử",
      description: item.name,
      confirmLabel: "Lưu kế hoạch",
      fields: [
        { name: "name", label: "Tên", initialValue: item.name, required: true, autoFocus: true },
        {
          name: "objective",
          label: "Mục tiêu",
          initialValue: item.objective || "",
          multiline: true,
        },
      ],
    });
    if (!answer) return;
    try {
      await testingApi.updatePlan(item._id, {
        expected_revision: item.revision,
        name: answer.name,
        objective: answer.objective,
      });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const transitionPlan = async (item, action) => {
    const answer = await ask({
      title:
        action === "approve"
          ? "Phê duyệt kế hoạch"
          : action === "archive"
            ? "Lưu trữ kế hoạch"
            : "Gửi rà soát kế hoạch",
      description: item.name,
      confirmLabel:
        action === "approve" ? "Phê duyệt" : action === "archive" ? "Lưu trữ" : "Gửi rà soát",
      danger: action === "archive",
      fields: [
        { name: "note", label: "Ghi chú", required: true, multiline: true, autoFocus: true },
      ],
    });
    if (!answer) return;
    try {
      const payload =
        action === "archive"
          ? { expected_revision: item.revision, reason: answer.note }
          : { expected_revision: item.revision, review_note: answer.note };
      if (action === "approve") await testingApi.approvePlan(item._id, payload);
      else if (action === "archive") await testingApi.archivePlan(item._id, payload);
      else await testingApi.submitPlan(item._id, payload);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const updateSuite = async (item) => {
    const answer = await ask({
      title: "Sửa bộ kiểm thử",
      description: item.name,
      confirmLabel: "Lưu bộ kiểm thử",
      fields: [
        { name: "name", label: "Tên", initialValue: item.name, required: true, autoFocus: true },
      ],
    });
    if (!answer) return;
    try {
      await testingApi.updateSuite(item._id, {
        expected_revision: item.revision,
        name: answer.name,
      });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const archiveSuite = async (item) => {
    const answer = await ask({
      title: "Lưu trữ bộ kiểm thử",
      description: item.name,
      confirmLabel: "Lưu trữ",
      danger: true,
      fields: [
        { name: "reason", label: "Lý do", required: true, multiline: true, autoFocus: true },
      ],
    });
    if (!answer) return;
    try {
      await testingApi.archiveSuite(item._id, {
        expected_revision: item.revision,
        reason: answer.reason,
      });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  if (run)
    return (
      <QaPage title={run.name} actions={<ProjectCrumb projectId={project._id} />}>
        {error && <ErrorState message={error} />}
        <Panel
          title="Điều khiển lần chạy"
          actions={
            <div className="flex flex-wrap gap-2">
              {can("report.export") && (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() =>
                    testingApi
                      .exportRunReport(run._id)
                      .catch((reason) => setError(messageOf(reason)))
                  }
                >
                  Xuất báo cáo
                </button>
              )}
              {run.status === "DRAFT" && can("testrun.start") && (
                <button
                  className="apple-button"
                  type="button"
                  onClick={async () => {
                    try {
                      await testingApi.startRun(run._id);
                      setRun(await testingApi.getRun(run._id));
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                >
                  Bắt đầu
                </button>
              )}
              {run.status === "IN_PROGRESS" && (
                <>
                  {can("testrun.abort") && (
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={async () => {
                        const answer = await ask({
                          title: "Hủy lần chạy kiểm thử",
                          description: `${run.name} sẽ dừng và giữ nguyên toàn bộ kết quả đã ghi nhận`,
                          confirmLabel: "Hủy lần chạy",
                          danger: true,
                          fields: [
                            {
                              name: "reason",
                              label: "Lý do hủy",
                              initialValue: "Dừng theo quyết định kiểm thử",
                              required: true,
                              multiline: true,
                              autoFocus: true,
                            },
                          ],
                        });
                        if (!answer) return;
                        try {
                          await testingApi.abortRun(run._id, answer.reason);
                          setRun(await testingApi.getRun(run._id));
                        } catch (value) {
                          setError(messageOf(value));
                        }
                      }}
                    >
                      Hủy lần chạy
                    </button>
                  )}
                  {can("testrun.complete") && (
                    <button
                      className="apple-button"
                      type="button"
                      onClick={async () => {
                        try {
                          await testingApi.completeRun(run._id);
                          setRun(await testingApi.getRun(run._id));
                        } catch (reason) {
                          setError(messageOf(reason));
                        }
                      }}
                    >
                      Hoàn tất
                    </button>
                  )}
                </>
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
                  if (!result) return "Không có ảnh chụp thực thi";
                  if (!["NOT_RUN", "IN_PROGRESS"].includes(result.status)) {
                    const hasDefect = run.defects?.some(
                      (defect) => defect.linked_test_result_id === result._id,
                    );
                    return (
                      <span className="flex min-w-48 flex-col items-start gap-2">
                        <StatusPill value={result.status} />
                        {result.status === "FAIL" && !hasDefect && can("defect.create") && (
                          <button
                            className="apple-button"
                            type="button"
                            onClick={() => createDefectFromResult(result, item)}
                          >
                            Tạo lỗi từ kết quả thất bại
                          </button>
                        )}
                        {hasDefect && (
                          <span className="text-[11px] text-ink-muted">Đã liên kết lỗi</span>
                        )}
                      </span>
                    );
                  }
                  if (run.status !== "IN_PROGRESS") {
                    return <StatusPill value={result.status} />;
                  }
                  if (!can("testrun.execute")) {
                    return <StatusPill value={result.status} />;
                  }
                  if (result.status === "NOT_RUN") {
                    return (
                      <span className="flex flex-wrap gap-2">
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={() => transition(result, "IN_PROGRESS", item)}
                        >
                          Bắt đầu ca kiểm thử
                        </button>
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={() => transition(result, "SKIPPED", item)}
                        >
                          Bỏ qua
                        </button>
                      </span>
                    );
                  }
                  return (
                    <div className="min-w-72 space-y-3">
                      {(item.steps || []).map((step, stepIndex) => {
                        const existing = result.step_results?.find(
                          (value) => value.step_id === step.id,
                        );
                        const edited = stepResults[result._id]?.[step.id] || {};
                        return (
                          <fieldset
                            className="space-y-2 rounded-xl border border-border p-3"
                            key={step.id}
                          >
                            <legend className="px-2 text-[12px] font-semibold">
                              Bước {stepIndex + 1}
                            </legend>
                            <p className="text-[12px]">{docText(step.action_doc)}</p>
                            <p className="text-[12px] text-ink-muted">
                              Mong đợi {docText(step.expected_doc)}
                            </p>
                            <select
                              aria-label={`Trạng thái bước ${stepIndex + 1} ${item.test_case_key}`}
                              className="apple-input"
                              value={edited.status || existing?.status || "PASS"}
                              onChange={(event) =>
                                setStepResults((values) => ({
                                  ...values,
                                  [result._id]: {
                                    ...values[result._id],
                                    [step.id]: {
                                      ...values[result._id]?.[step.id],
                                      status: event.target.value,
                                    },
                                  },
                                }))
                              }
                            >
                              {["PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"].map(
                                (value) => (
                                  <option value={value} key={value}>
                                    {valueLabel(value)}
                                  </option>
                                ),
                              )}
                            </select>
                            <textarea
                              aria-label={`Kết quả bước ${stepIndex + 1} ${item.test_case_key}`}
                              className="apple-input min-h-16"
                              value={edited.actual ?? docText(existing?.actual_doc)}
                              onChange={(event) =>
                                setStepResults((values) => ({
                                  ...values,
                                  [result._id]: {
                                    ...values[result._id],
                                    [step.id]: {
                                      ...values[result._id]?.[step.id],
                                      actual: event.target.value,
                                    },
                                  },
                                }))
                              }
                              placeholder="Kết quả thực tế của bước"
                            />
                          </fieldset>
                        );
                      })}
                      <textarea
                        aria-label={`Kết quả thực tế ${item.test_case_key}`}
                        className="apple-input min-h-20"
                        value={actuals[result._id] ?? docText(result.actual_result_doc)}
                        onChange={(event) =>
                          setActuals({ ...actuals, [result._id]: event.target.value })
                        }
                        placeholder="Kết quả thực tế và bằng chứng"
                      />
                      <input
                        aria-label={`Tệp bằng chứng ${item.test_case_key}`}
                        className="apple-input"
                        type="file"
                        onChange={async (event) => {
                          const file = event.target.files?.[0];
                          if (!file) return;
                          try {
                            const uploaded = await uploadAssetAPI(file);
                            const current = attachments[result._id] || result.attachments || [];
                            setAttachments({
                              ...attachments,
                              [result._id]: [...current, uploaded.data],
                            });
                          } catch (reason) {
                            setError(messageOf(reason));
                          }
                        }}
                      />
                      {(attachments[result._id] || result.attachments || []).map((attachment) => (
                        <p className="break-all text-[11px] text-ink-muted" key={attachment.url}>
                          {attachment.filename}
                        </p>
                      ))}
                      <span className="flex flex-wrap gap-2">
                        {["PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"].map((value) => (
                          <button
                            className="secondary-button"
                            type="button"
                            key={value}
                            onClick={() => transition(result, value, item)}
                          >
                            {valueLabel(value)}
                          </button>
                        ))}
                      </span>
                    </div>
                  );
                },
                mobileRender: (item) => {
                  const result = run.results?.find(
                    (value) => value.test_case_version_id === item._id,
                  );
                  return result
                    ? `Kết quả ${valueLabel(result.status)}`
                    : "Không có ảnh chụp thực thi";
                },
              },
            ]}
          />
        </Panel>
        {dialog}
      </QaPage>
    );
  return (
    <QaPage
      title="Kế hoạch, bộ kiểm thử và lần chạy"
      actions={<ProjectCrumb projectId={project._id} />}
    >
      {error && <ErrorState message={error} />}
      <div className="grid gap-5 xl:grid-cols-3">
        {can("testplan.create") && (
          <Panel title="Tạo kế hoạch kiểm thử">
            <form
              className="space-y-3 p-5"
              onSubmit={async (event) => {
                event.preventDefault();
                const value = new FormData(event.currentTarget);
                try {
                  await testingApi.createPlan({
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
        )}
        {can("testsuite.create") && (
          <Panel title="Tạo bộ kiểm thử">
            <form
              className="space-y-3 p-5"
              onSubmit={async (event) => {
                event.preventDefault();
                const value = new FormData(event.currentTarget);
                try {
                  await testingApi.createSuite({
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
        )}
        {can("testrun.create") && (
          <Panel title="Tạo lần chạy">
            <form className="space-y-3 p-5" onSubmit={createRun}>
              <input
                aria-label="Tên lần chạy"
                required
                className="apple-input"
                value={runForm.name}
                onChange={(event) => setRunForm({ ...runForm, name: event.target.value })}
                placeholder="Tên lần chạy"
              />
              <div className="grid gap-3 sm:grid-cols-3">
                <input
                  aria-label="Bản phát hành"
                  className="apple-input"
                  placeholder="Bản phát hành"
                  value={runForm.release}
                  onChange={(event) => setRunForm({ ...runForm, release: event.target.value })}
                />
                <input
                  aria-label="Bản dựng"
                  className="apple-input"
                  placeholder="Bản dựng"
                  value={runForm.build}
                  onChange={(event) => setRunForm({ ...runForm, build: event.target.value })}
                />
                <input
                  aria-label="Môi trường"
                  className="apple-input"
                  placeholder="Môi trường"
                  value={runForm.environment}
                  onChange={(event) => setRunForm({ ...runForm, environment: event.target.value })}
                />
              </div>
              <select
                aria-label="Kế hoạch kiểm thử"
                className="apple-input"
                value={runForm.testPlanId}
                onChange={(event) => setRunForm({ ...runForm, testPlanId: event.target.value })}
              >
                <option value="">Không gắn kế hoạch</option>
                {plans.map((item) => (
                  <option key={item._id} value={item._id}>
                    {item.name}
                  </option>
                ))}
              </select>
              <label className="field-label block">
                Bộ kiểm thử
                <select
                  aria-label="Bộ kiểm thử"
                  className="apple-input mt-2 min-h-28"
                  multiple
                  value={runForm.suiteIds}
                  onChange={(event) =>
                    setRunForm({
                      ...runForm,
                      suiteIds: Array.from(event.target.selectedOptions, (option) => option.value),
                    })
                  }
                >
                  {suites.map((item) => (
                    <option key={item._id} value={item._id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field-label block">
                Phiên bản ca kiểm thử
                <select
                  aria-label="Phiên bản ca kiểm thử"
                  className="apple-input mt-2 min-h-36"
                  multiple
                  value={runForm.versionIds}
                  onChange={(event) =>
                    setRunForm({
                      ...runForm,
                      versionIds: Array.from(
                        event.target.selectedOptions,
                        (option) => option.value,
                      ),
                    })
                  }
                >
                  {tests.map((item) => (
                    <option key={item.current_version_id} value={item.current_version_id}>
                      {item.test_case_key} {item.current_version?.title}
                    </option>
                  ))}
                </select>
              </label>
              <p className="text-[12px] text-ink-muted">
                Snapshot {runForm.versionIds.length} phiên bản được chọn cùng các phiên bản trong bộ
                kiểm thử
              </p>
              <button className="apple-button" type="submit">
                Tạo lần chạy
              </button>
            </form>
          </Panel>
        )}
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        <Panel title="Kế hoạch kiểm thử">
          <div className="grid gap-3 border-b border-border p-4 sm:grid-cols-2 lg:grid-cols-4">
            <input
              aria-label="Tìm kế hoạch kiểm thử"
              className="apple-input"
              placeholder="Tìm tên hoặc mục tiêu"
              value={planFilters.q}
              onChange={(event) => setPlanFilters({ ...planFilters, q: event.target.value })}
            />
            <input
              aria-label="Lọc bản phát hành kế hoạch"
              className="apple-input"
              placeholder="Bản phát hành"
              value={planFilters.release}
              onChange={(event) => setPlanFilters({ ...planFilters, release: event.target.value })}
            />
            <select
              aria-label="Lọc trạng thái kế hoạch"
              className="apple-input"
              value={planFilters.status}
              onChange={(event) => setPlanFilters({ ...planFilters, status: event.target.value })}
            >
              <option value="">Mọi trạng thái</option>
              {["DRAFT", "IN_REVIEW", "APPROVED", "ARCHIVED"].map((value) => (
                <option value={value} key={value}>
                  {valueLabel(value)}
                </option>
              ))}
            </select>
            <select
              aria-label="Sắp xếp kế hoạch"
              className="apple-input"
              value={planFilters.sort}
              onChange={(event) => setPlanFilters({ ...planFilters, sort: event.target.value })}
            >
              <option value="-updated_at">Mới cập nhật</option>
              <option value="updated_at">Cũ cập nhật</option>
              <option value="name">Tên tăng dần</option>
            </select>
          </div>
          <DataTable
            items={plans}
            empty="Chưa có kế hoạch kiểm thử"
            columns={[
              { key: "name", label: "Tên" },
              { key: "release", label: "Bản phát hành" },
              { key: "build", label: "Bản dựng" },
              {
                key: "status",
                label: "Trạng thái",
                render: (item) => <StatusPill value={item.status} />,
              },
              {
                key: "actions",
                label: "Thao tác",
                render: (item) => (
                  <span className="flex flex-wrap gap-2">
                    {item.status === "DRAFT" && can("testplan.update") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => updatePlan(item)}
                      >
                        Sửa
                      </button>
                    )}
                    {item.status === "DRAFT" && can("testplan.submit_review") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => transitionPlan(item, "submit")}
                      >
                        Gửi rà soát
                      </button>
                    )}
                    {["DRAFT", "IN_REVIEW"].includes(item.status) && can("testplan.approve") && (
                      <button
                        className="apple-button"
                        type="button"
                        onClick={() => transitionPlan(item, "approve")}
                      >
                        Phê duyệt
                      </button>
                    )}
                    {can("testplan.create") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={async () => {
                          try {
                            await testingApi.clonePlan(item._id);
                            await load();
                          } catch (reason) {
                            setError(messageOf(reason));
                          }
                        }}
                      >
                        Nhân bản
                      </button>
                    )}
                    {item.status !== "ARCHIVED" && can("testplan.archive") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => transitionPlan(item, "archive")}
                      >
                        Lưu trữ
                      </button>
                    )}
                  </span>
                ),
              },
            ]}
          />
        </Panel>
        <Panel title="Bộ kiểm thử">
          <div className="grid gap-3 border-b border-border p-4 sm:grid-cols-2 lg:grid-cols-4">
            <input
              aria-label="Tìm bộ kiểm thử"
              className="apple-input"
              placeholder="Tìm tên bộ kiểm thử"
              value={suiteFilters.q}
              onChange={(event) => setSuiteFilters({ ...suiteFilters, q: event.target.value })}
            />
            <select
              aria-label="Lọc loại bộ kiểm thử"
              className="apple-input"
              value={suiteFilters.suite_type}
              onChange={(event) =>
                setSuiteFilters({ ...suiteFilters, suite_type: event.target.value })
              }
            >
              <option value="">Mọi loại</option>
              {[
                "smoke",
                "regression",
                "sanity",
                "feature",
                "api",
                "ui",
                "integration",
                "custom",
              ].map((value) => (
                <option value={value} key={value}>
                  {valueLabel(value)}
                </option>
              ))}
            </select>
            <select
              aria-label="Lọc trạng thái bộ kiểm thử"
              className="apple-input"
              value={suiteFilters.status}
              onChange={(event) => setSuiteFilters({ ...suiteFilters, status: event.target.value })}
            >
              <option value="">Mọi trạng thái</option>
              {["ACTIVE", "ARCHIVED"].map((value) => (
                <option value={value} key={value}>
                  {valueLabel(value)}
                </option>
              ))}
            </select>
            <select
              aria-label="Sắp xếp bộ kiểm thử"
              className="apple-input"
              value={suiteFilters.sort}
              onChange={(event) => setSuiteFilters({ ...suiteFilters, sort: event.target.value })}
            >
              <option value="-updated_at">Mới cập nhật</option>
              <option value="updated_at">Cũ cập nhật</option>
              <option value="name">Tên tăng dần</option>
            </select>
          </div>
          <DataTable
            items={suites}
            empty="Chưa có bộ kiểm thử"
            columns={[
              { key: "name", label: "Tên" },
              { key: "suite_type", label: "Loại", render: (item) => valueLabel(item.suite_type) },
              {
                key: "count",
                label: "Số ca",
                render: (item) => item.test_case_version_ids?.length || 0,
              },
              {
                key: "actions",
                label: "Thao tác",
                render: (item) => (
                  <span className="flex flex-wrap gap-2">
                    {can("testsuite.update") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => updateSuite(item)}
                      >
                        Sửa
                      </button>
                    )}
                    {can("testsuite.clone") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={async () => {
                          try {
                            await testingApi.cloneSuite(item._id);
                            await load();
                          } catch (reason) {
                            setError(messageOf(reason));
                          }
                        }}
                      >
                        Nhân bản
                      </button>
                    )}
                    {item.status !== "ARCHIVED" && can("testsuite.archive") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => archiveSuite(item)}
                      >
                        Lưu trữ
                      </button>
                    )}
                  </span>
                ),
              },
            ]}
          />
        </Panel>
      </div>
      <Panel title="Danh sách lần chạy">
        <div className="grid gap-3 border-b border-border p-4 sm:grid-cols-2 xl:grid-cols-4">
          <input
            aria-label="Tìm lần chạy"
            className="apple-input"
            placeholder="Tên lần chạy"
            value={runFilters.name}
            onChange={(event) => {
              setRunFilters({ ...runFilters, name: event.target.value });
              setRunPage(1);
            }}
          />
          <select
            aria-label="Lọc trạng thái lần chạy"
            className="apple-input"
            value={runFilters.status}
            onChange={(event) => {
              setRunFilters({ ...runFilters, status: event.target.value });
              setRunPage(1);
            }}
          >
            <option value="">Mọi trạng thái</option>
            {["DRAFT", "READY", "IN_PROGRESS", "COMPLETED", "ABORTED"].map((value) => (
              <option key={value} value={value}>
                {valueLabel(value)}
              </option>
            ))}
          </select>
          <input
            aria-label="Lọc môi trường lần chạy"
            className="apple-input"
            placeholder="Môi trường"
            value={runFilters.environment}
            onChange={(event) => {
              setRunFilters({ ...runFilters, environment: event.target.value });
              setRunPage(1);
            }}
          />
          <select
            aria-label="Sắp xếp lần chạy"
            className="apple-input"
            value={runFilters.sort}
            onChange={(event) => {
              setRunFilters({ ...runFilters, sort: event.target.value });
              setRunPage(1);
            }}
          >
            <option value="-updated_at">Mới cập nhật</option>
            <option value="updated_at">Cũ cập nhật</option>
            <option value="name">Tên tăng dần</option>
          </select>
        </div>
        <DataTable
          onSelect={(item) =>
            window.location.assign(`/qa/projects/${project._id}/execution/${item._id}`)
          }
          items={runs}
          empty="Chưa có lần chạy"
          columns={[
            { key: "name", label: "Tên" },
            { key: "environment", label: "Môi trường" },
            { key: "build", label: "Bản dựng" },
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
        <Pagination value={runPageInfo} onChange={setRunPage} />
      </Panel>
      {dialog}
    </QaPage>
  );
}
