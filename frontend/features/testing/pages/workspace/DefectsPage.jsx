"use client";
import { useCallback, useEffect, useState } from "react";
import { uploadAssetAPI } from "@/features/cloud/services/upload.service";
import DataTable from "../../components/DataTable";
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
import { messageOf, textDoc, valueLabel } from "../../lib/testing";

const nextStates = {
  NEW: ["CONFIRMED", "REJECTED", "DUPLICATE"],
  CONFIRMED: ["IN_PROGRESS", "REJECTED", "DUPLICATE"],
  IN_PROGRESS: ["RESOLVED"],
  RESOLVED: ["READY_FOR_RETEST", "REOPENED"],
  READY_FOR_RETEST: [],
  REOPENED: ["IN_PROGRESS", "RESOLVED"],
  CLOSED: ["REOPENED"],
  REJECTED: ["REOPENED"],
  DUPLICATE: ["REOPENED"],
};

export default function DefectsPage({ project }) {
  const { ask, dialog } = useQaActionDialog();
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [pageInfo, setPageInfo] = useState(null);
  const [filters, setFilters] = useState({
    q: "",
    status: "",
    severity: "",
    priority: "",
    assignee: "",
    sort: "-updated_at",
  });
  const [results, setResults] = useState([]);
  const [duplicates, setDuplicates] = useState([]);
  const [traceReview, setTraceReview] = useState(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    title: "",
    severity: "major",
    priority: "medium",
    environment: "staging",
    build: "",
    description: "",
    actual: "",
    expected: "",
    attachments: [],
  });
  const can = (permission) => project.current_permissions?.includes(permission);
  const role = project.current_membership?.project_role;
  const userId = project.current_membership?.user_id;
  const canManageTrace = (item) =>
    can("defect.trace.manage") || (role === "DEVELOPER" && item.assignee === userId);
  const transitionAllowed = (item, status) => {
    if (["CONFIRMED", "REJECTED", "DUPLICATE"].includes(status)) {
      if (!can("defect.triage")) return false;
      if (status === "REJECTED") {
        const configured = project.settings?.action_policies?.["defect.rejected"];
        return Array.isArray(configured) ? configured.includes(role) : role === "QA_LEAD";
      }
      if (status === "DUPLICATE") {
        const configured = project.settings?.action_policies?.["defect.duplicate"];
        return Array.isArray(configured) ? configured.includes(role) : role === "QA_LEAD";
      }
      return true;
    }
    if (["IN_PROGRESS", "RESOLVED"].includes(status)) {
      return (
        can("defect.transition.developer") || (role === "DEVELOPER" && item.assignee === userId)
      );
    }
    if (["READY_FOR_RETEST", "REOPENED"].includes(status)) return can("defect.retest");
    if (status === "CLOSED") return can("defect.close");
    return can("defect.update");
  };
  const load = useCallback(async () => {
    try {
      const [defectValues, resultValues] = await Promise.all([
        testingApi.listDefectPage(project._id, { ...filters, page, page_size: 50 }),
        testingApi.listResults(project._id, "PASS,FAIL"),
      ]);
      setItems(defectValues.items);
      setPageInfo(defectValues);
      setResults(resultValues);
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [filters, page, project._id]);
  useEffect(() => {
    void load();
  }, [load]);
  const create = async (event) => {
    event.preventDefault();
    try {
      await testingApi.createDefect(project._id, {
        project_id: project._id,
        title: form.title,
        description_doc: textDoc(form.description),
        steps_to_reproduce: [],
        actual_result_doc: textDoc(form.actual),
        expected_result_doc: textDoc(form.expected),
        severity: form.severity,
        priority: form.priority,
        environment: form.environment,
        build: form.build,
        attachments: form.attachments,
        linked_requirement_version_ids: [],
      });
      setForm({
        title: "",
        severity: "major",
        priority: "medium",
        environment: "staging",
        build: "",
        description: "",
        actual: "",
        expected: "",
        attachments: [],
      });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const transition = async (item, to_status) => {
    const answer = await ask({
      title: "Chuyển trạng thái lỗi",
      description: `${item.defect_key} từ ${item.status} sang ${to_status}`,
      confirmLabel: "Chuyển trạng thái",
      fields: [
        {
          name: "reason",
          label: "Lý do",
          initialValue: "Đã xác minh điều kiện chuyển trạng thái",
          required: true,
          multiline: true,
          autoFocus: true,
        },
      ],
    });
    if (!answer) return;
    try {
      await testingApi.transitionDefect(item._id, {
        expected_revision: item.revision,
        to_status,
        reason: answer.reason,
      });
      await load();
    } catch (value) {
      setError(messageOf(value));
    }
  };
  const assignDefect = async (item) => {
    const answer = await ask({
      title: "Gán người xử lý lỗi",
      description: item.defect_key,
      confirmLabel: "Lưu người xử lý",
      fields: [
        {
          name: "assignee",
          label: "Mã người dùng để trống nếu muốn bỏ gán",
          initialValue: item.assignee || "",
          autoFocus: true,
        },
      ],
    });
    if (!answer) return;
    try {
      await testingApi.updateDefect(item._id, {
        expected_revision: item.revision,
        assignee: answer.assignee.trim() || null,
      });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <QaPage
      title="Quản lý lỗi"
      actions={
        <div className="flex flex-wrap items-center gap-3">
          {can("report.export") && (
            <button
              className="secondary-button"
              type="button"
              onClick={() =>
                testingApi.exportDefects(project._id).catch((reason) => setError(messageOf(reason)))
              }
            >
              Xuất CSV
            </button>
          )}
          {can("defect.duplicate_check") && (
            <button
              className="secondary-button"
              type="button"
              onClick={async () => {
                try {
                  setDuplicates(await testingApi.findDuplicateDefects(project._id));
                } catch (reason) {
                  setError(messageOf(reason));
                }
              }}
            >
              Tìm lỗi có thể trùng
            </button>
          )}
          <ProjectCrumb projectId={project._id} />
        </div>
      }
    >
      {error && <ErrorState message={error} />}
      {can("defect.create") && (
        <Panel title="Tạo lỗi">
          <form className="grid gap-4 p-5 md:grid-cols-2" onSubmit={create}>
            <label className="field-label md:col-span-2">
              Tên
              <input
                required
                className="apple-input mt-2"
                value={form.title}
                onChange={(event) => setForm({ ...form, title: event.target.value })}
              />
            </label>
            <label className="field-label">
              Mức độ nghiêm trọng
              <select
                className="apple-input mt-2"
                value={form.severity}
                onChange={(event) => setForm({ ...form, severity: event.target.value })}
              >
                {["blocker", "critical", "major", "minor", "trivial"].map((value) => (
                  <option key={value} value={value}>
                    {valueLabel(value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="field-label">
              Mức ưu tiên
              <select
                className="apple-input mt-2"
                value={form.priority}
                onChange={(event) => setForm({ ...form, priority: event.target.value })}
              >
                {["critical", "high", "medium", "low"].map((value) => (
                  <option key={value} value={value}>
                    {valueLabel(value)}
                  </option>
                ))}
              </select>
            </label>
            <label className="field-label">
              Môi trường
              <input
                className="apple-input mt-2"
                value={form.environment}
                onChange={(event) => setForm({ ...form, environment: event.target.value })}
              />
            </label>
            <label className="field-label">
              Bản dựng
              <input
                className="apple-input mt-2"
                value={form.build}
                onChange={(event) => setForm({ ...form, build: event.target.value })}
              />
            </label>
            <label className="field-label">
              Mô tả
              <textarea
                className="apple-input mt-2 min-h-24"
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
              />
            </label>
            <label className="field-label">
              Kết quả thực tế
              <textarea
                className="apple-input mt-2 min-h-24"
                value={form.actual}
                onChange={(event) => setForm({ ...form, actual: event.target.value })}
              />
            </label>
            <label className="field-label md:col-span-2">
              Kết quả mong đợi
              <textarea
                className="apple-input mt-2 min-h-24"
                value={form.expected}
                onChange={(event) => setForm({ ...form, expected: event.target.value })}
              />
            </label>
            <label className="field-label md:col-span-2">
              Tệp bằng chứng
              <input
                className="apple-input mt-2"
                type="file"
                onChange={async (event) => {
                  const file = event.target.files?.[0];
                  if (!file) return;
                  try {
                    const uploaded = await uploadAssetAPI(file);
                    setForm({ ...form, attachments: [...form.attachments, uploaded.data] });
                  } catch (reason) {
                    setError(messageOf(reason));
                  }
                }}
              />
              {form.attachments.map((attachment) => (
                <span
                  className="mt-2 block break-all text-[11px] text-ink-muted"
                  key={attachment.url}
                >
                  {attachment.filename}
                </span>
              ))}
            </label>
            <div>
              <button className="apple-button" type="submit">
                Lưu lỗi
              </button>
            </div>
          </form>
        </Panel>
      )}
      {duplicates.length > 0 && (
        <Panel title="Ứng viên lỗi trùng cần người dùng xác nhận">
          <DataTable
            items={duplicates}
            columns={[
              {
                key: "left",
                label: "Lỗi thứ nhất",
                render: (item) => `${item.left.defect_key} ${item.left.title}`,
              },
              {
                key: "right",
                label: "Lỗi thứ hai",
                render: (item) => `${item.right.defect_key} ${item.right.title}`,
              },
              {
                key: "similarity",
                label: "Mức tương đồng",
                render: (item) => `${Math.round(item.similarity * 100)}%`,
              },
              { key: "reason", label: "Lý do" },
            ]}
          />
        </Panel>
      )}
      {traceReview && (
        <Panel
          title={`Ứng viên truy vết cho ${traceReview.defect.defect_key}`}
          description="Mức tin cậy là tín hiệu xếp hạng và phải được người dùng xác nhận"
        >
          <DataTable
            items={traceReview.candidates}
            empty="Không tìm thấy ca kiểm thử liên quan trong dự án"
            columns={[
              { key: "test_case_key", label: "Ca kiểm thử" },
              { key: "title", label: "Tên" },
              { key: "confidence_band", label: "Mức tín hiệu" },
              {
                key: "reason_codes",
                label: "Bằng chứng",
                render: (item) => item.reason_codes.join(", "),
              },
              {
                key: "action",
                label: "Quyết định",
                render: (candidate) =>
                  canManageTrace(traceReview.defect) ? (
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={async () => {
                        try {
                          await testingApi.updateDefect(traceReview.defect._id, {
                            expected_revision: traceReview.defect.revision,
                            linked_test_case_version_id: candidate.test_case_version_id,
                            linked_requirement_version_ids: candidate.requirement_version_ids,
                          });
                          setTraceReview(null);
                          await load();
                        } catch (reason) {
                          setError(messageOf(reason));
                        }
                      }}
                    >
                      Liên kết
                    </button>
                  ) : null,
              },
            ]}
          />
        </Panel>
      )}
      <Panel title="Danh sách lỗi">
        <div className="grid gap-3 border-b border-border p-4 sm:grid-cols-2 xl:grid-cols-6">
          <input
            aria-label="Tìm lỗi"
            className="apple-input xl:col-span-2"
            placeholder="Tìm theo mã hoặc tên"
            value={filters.q}
            onChange={(event) => {
              setFilters({ ...filters, q: event.target.value });
              setPage(1);
            }}
          />
          <select
            aria-label="Lọc trạng thái lỗi"
            className="apple-input"
            value={filters.status}
            onChange={(event) => {
              setFilters({ ...filters, status: event.target.value });
              setPage(1);
            }}
          >
            <option value="">Mọi trạng thái</option>
            {Object.keys(nextStates).map((value) => (
              <option key={value} value={value}>
                {valueLabel(value)}
              </option>
            ))}
          </select>
          <select
            aria-label="Lọc mức độ lỗi"
            className="apple-input"
            value={filters.severity}
            onChange={(event) => {
              setFilters({ ...filters, severity: event.target.value });
              setPage(1);
            }}
          >
            <option value="">Mọi mức độ</option>
            {["blocker", "critical", "major", "minor", "trivial"].map((value) => (
              <option key={value} value={value}>
                {valueLabel(value)}
              </option>
            ))}
          </select>
          <input
            aria-label="Lọc người xử lý lỗi"
            className="apple-input"
            placeholder="Mã người xử lý"
            value={filters.assignee}
            onChange={(event) => {
              setFilters({ ...filters, assignee: event.target.value });
              setPage(1);
            }}
          />
          <select
            aria-label="Sắp xếp lỗi"
            className="apple-input"
            value={filters.sort}
            onChange={(event) => {
              setFilters({ ...filters, sort: event.target.value });
              setPage(1);
            }}
          >
            <option value="-updated_at">Mới cập nhật</option>
            <option value="updated_at">Cũ cập nhật</option>
            <option value="severity">Theo mức độ</option>
            <option value="priority">Theo ưu tiên</option>
          </select>
        </div>
        <DataTable
          items={items}
          empty="Chưa có lỗi"
          columns={[
            { key: "defect_key", label: "Mã" },
            { key: "title", label: "Tên" },
            { key: "severity", label: "Mức độ", render: (item) => valueLabel(item.severity) },
            { key: "priority", label: "Ưu tiên", render: (item) => valueLabel(item.priority) },
            {
              key: "status",
              label: "Trạng thái",
              render: (item) => <StatusPill value={item.status} />,
            },
            {
              key: "trace",
              label: "Truy vết",
              render: (item) => (
                <span className="flex min-w-48 flex-col items-start gap-2">
                  <span className="text-[11px] text-ink-muted">
                    {item.linked_test_case_version_id || "Chưa liên kết ca kiểm thử"}
                  </span>
                  <span className="flex flex-wrap gap-2">
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={async () => {
                        try {
                          setTraceReview({
                            defect: item,
                            candidates: await testingApi.findDefectTraceCandidates(item._id),
                          });
                        } catch (reason) {
                          setError(messageOf(reason));
                        }
                      }}
                    >
                      Gợi ý liên kết
                    </button>
                    {item.linked_test_case_version_id && canManageTrace(item) && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={async () => {
                          const answer = await ask({
                            title: "Thu hồi liên kết lỗi",
                            description: `${item.defect_key} sẽ không còn liên kết với ca kiểm thử hiện tại`,
                            confirmLabel: "Thu hồi liên kết",
                            danger: true,
                          });
                          if (!answer) return;
                          try {
                            await testingApi.updateDefect(item._id, {
                              expected_revision: item.revision,
                              linked_test_case_version_id: null,
                              linked_requirement_version_ids: [],
                            });
                            await load();
                          } catch (reason) {
                            setError(messageOf(reason));
                          }
                        }}
                      >
                        Thu hồi
                      </button>
                    )}
                  </span>
                </span>
              ),
            },
            {
              key: "assignee",
              label: "Người xử lý",
              render: (item) =>
                can("defect.assign") ? (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => assignDefect(item)}
                  >
                    {item.assignee || "Gán người xử lý"}
                  </button>
                ) : (
                  item.assignee || "Chưa gán"
                ),
            },
            {
              key: "transition",
              label: "Chuyển trạng thái",
              render: (item) =>
                item.status === "READY_FOR_RETEST" && can("defect.retest") ? (
                  <select
                    aria-label={`Kết quả retest ${item.defect_key}`}
                    className="apple-input"
                    value=""
                    onChange={async (event) => {
                      if (!event.target.value) return;
                      try {
                        await testingApi.retestDefect(project._id, item._id, {
                          test_result_id: event.target.value,
                          expected_revision: item.revision,
                          note: "Retest từ giao diện quản lý lỗi",
                          idempotency_key: crypto.randomUUID(),
                        });
                        await load();
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    <option value="">Chọn kết quả kiểm thử lại</option>
                    {results
                      .filter(
                        (result) =>
                          (!item.linked_test_case_version_id ||
                            result.test_case_version_id === item.linked_test_case_version_id) &&
                          (result.status !== "PASS" || can("defect.close")),
                      )
                      .map((result) => (
                        <option key={result._id} value={result._id}>
                          {valueLabel(result.status)} {result.build || result._id}
                        </option>
                      ))}
                  </select>
                ) : (
                  <select
                    aria-label={`Chuyển trạng thái ${item.defect_key}`}
                    className="apple-input"
                    value=""
                    onChange={(event) => transition(item, event.target.value)}
                  >
                    <option value="">Chọn</option>
                    {(nextStates[item.status] || [])
                      .filter((value) => transitionAllowed(item, value))
                      .map((value) => (
                        <option key={value} value={value}>
                          {valueLabel(value)}
                        </option>
                      ))}
                  </select>
                ),
            },
          ]}
        />
        <Pagination value={pageInfo} onChange={setPage} />
      </Panel>
      {dialog}
    </QaPage>
  );
}
