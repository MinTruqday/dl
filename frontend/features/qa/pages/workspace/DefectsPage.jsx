"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import { ErrorState, Panel, ProjectCrumb, QaPage, StatusPill } from "../../components/QaUi";
import { qaApi } from "../../services/qa.service";
import { messageOf, textDoc, valueLabel } from "../../lib/qa";

const nextStates = {
  NEW: ["CONFIRMED", "REJECTED", "DUPLICATE"],
  CONFIRMED: ["IN_PROGRESS", "REJECTED", "DUPLICATE"],
  IN_PROGRESS: ["RESOLVED"],
  RESOLVED: ["READY_FOR_RETEST", "REOPENED"],
  READY_FOR_RETEST: ["CLOSED", "REOPENED"],
  REOPENED: ["IN_PROGRESS", "RESOLVED"],
  CLOSED: ["REOPENED"],
  REJECTED: ["REOPENED"],
  DUPLICATE: ["REOPENED"],
};

export default function DefectsPage({ project }) {
  const [items, setItems] = useState([]);
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
  });
  const load = useCallback(async () => {
    try {
      setItems(await qaApi.listDefects(project._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [project._id]);
  useEffect(() => {
    void load();
  }, [load]);
  const create = async (event) => {
    event.preventDefault();
    try {
      await qaApi.createDefect(project._id, {
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
        attachments: [],
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
      });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const transition = async (item, to_status) => {
    const reason = window.prompt(
      `Lý do chuyển sang ${to_status}`,
      "Đã xác minh điều kiện chuyển trạng thái",
    );
    if (!reason) return;
    try {
      await qaApi.transitionDefect(item._id, { to_status, reason });
      await load();
    } catch (value) {
      setError(messageOf(value));
    }
  };
  return (
    <QaPage
      title="Quản lý lỗi"
      description="Mỗi lỗi có vòng đời rõ ràng và có thể liên kết ngược với lần chạy yêu cầu cùng phiên bản ca kiểm thử"
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <button
            className="secondary-button"
            type="button"
            onClick={() =>
              qaApi.exportDefects(project._id).catch((reason) => setError(messageOf(reason)))
            }
          >
            Xuất CSV
          </button>
          <ProjectCrumb projectId={project._id} />
        </div>
      }
    >
      {error && <ErrorState message={error} />}
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
            Build
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
          <div>
            <button className="apple-button" type="submit">
              Lưu lỗi
            </button>
          </div>
        </form>
      </Panel>
      <Panel title="Danh sách lỗi">
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
              key: "transition",
              label: "Chuyển trạng thái",
              render: (item) => (
                <select
                  aria-label={`Chuyển trạng thái ${item.defect_key}`}
                  className="apple-input"
                  value=""
                  onChange={(event) => transition(item, event.target.value)}
                >
                  <option value="">Chọn</option>
                  {(nextStates[item.status] || []).map((value) => (
                    <option key={value} value={value}>
                      {valueLabel(value)}
                    </option>
                  ))}
                </select>
              ),
            },
          ]}
        />
      </Panel>
    </QaPage>
  );
}
