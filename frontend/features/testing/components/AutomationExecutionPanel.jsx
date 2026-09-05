"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "./DataTable";
import { ErrorState, Panel, StatusPill, useQaActionDialog } from "./TestingUi";
import { testingApi } from "../services/testing.service";
import { messageOf } from "../lib/testing";

export default function AutomationExecutionPanel({ project }) {
  const { ask, dialog } = useQaActionDialog();
  const [items, setItems] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [evidence, setEvidence] = useState(null);
  const [error, setError] = useState("");
  const can = (permission) => project.current_permissions?.includes(permission);
  const load = useCallback(async () => {
    if (!project.current_permissions?.includes("automation.read")) return;
    try {
      const [executionValues, artifactValues] = await Promise.all([
        testingApi.listAutomationExecutions(project._id),
        testingApi.listApiArtifacts(project._id),
      ]);
      setItems(executionValues);
      setArtifacts(
        artifactValues.filter((item) => item.format === "postman" && item.status === "CONFIRMED"),
      );
      setSelected(
        (current) => executionValues.find((item) => item._id === current?._id) || current,
      );
      setError("");
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [project._id, project.current_permissions]);
  useEffect(() => {
    void load();
  }, [load]);
  const create = async () => {
    const answer = await ask({
      title: "Tạo lần chạy Newman",
      description: "Collection phải được nhập rà soát và xác nhận trước khi thực thi",
      confirmLabel: "Tạo lần chạy",
      fields: [
        { name: "name", label: "Tên lần chạy", required: true, autoFocus: true },
        {
          name: "artifactId",
          label: "Collection Postman đã xác nhận",
          required: true,
          options: artifacts.map((item) => ({ value: item._id, label: item.filename })),
          initialValue: artifacts[0]?._id || "",
        },
      ],
    });
    if (!answer) return;
    try {
      const value = await testingApi.createAutomationExecution(project._id, {
        name: answer.name.trim(),
        postman_artifact_id: answer.artifactId,
        idempotency_key: crypto.randomUUID(),
      });
      setSelected(value);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const open = async (item) => {
    try {
      const value = await testingApi.getAutomationExecution(item._id);
      setSelected(value);
      setEvidence(await testingApi.getAutomationEvidence(item._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const start = async () => {
    try {
      const value = await testingApi.startAutomationExecution(selected._id, {
        expected_revision: selected.revision,
        idempotency_key: crypto.randomUUID(),
      });
      setSelected(value);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const cancel = async () => {
    try {
      const value = await testingApi.cancelAutomationExecution(selected._id, {
        expected_revision: selected.revision,
        idempotency_key: crypto.randomUUID(),
      });
      setSelected(value);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  if (!can("automation.read")) return null;
  return (
    <Panel
      title="Thực thi Newman"
      description="Runner hoạt động tách biệt và kết quả được chuẩn hóa về dự án"
      actions={
        can("automation.create") ? (
          <button
            className="apple-button"
            type="button"
            disabled={!artifacts.length}
            onClick={create}
          >
            Tạo lần chạy Newman
          </button>
        ) : null
      }
    >
      <div className="space-y-5 p-5">
        {error && <ErrorState message={error} />}
        {!artifacts.length && can("automation.create") && (
          <p className="text-sm text-ink-muted">Cần xác nhận ít nhất một collection Postman</p>
        )}
        <DataTable
          items={items}
          empty="Chưa có lần thực thi tự động"
          onSelect={open}
          columns={[
            { key: "name", label: "Tên" },
            { key: "runner", label: "Runner" },
            {
              key: "status",
              label: "Trạng thái",
              render: (item) => <StatusPill value={item.status} />,
            },
            { key: "operation_id", label: "Mã tác vụ" },
          ]}
        />
        {selected && (
          <div className="space-y-3 rounded-xl border border-border p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-medium">{selected.name}</p>
                <p className="mt-1 text-xs text-ink-muted">
                  Không hiển thị giá trị bí mật trong log và evidence
                </p>
              </div>
              <div className="flex gap-2">
                {selected.status === "CREATED" && can("automation.execute") && (
                  <button className="apple-button" type="button" onClick={start}>
                    Bắt đầu Newman
                  </button>
                )}
                {selected.status === "QUEUED" && can("automation.execute") && (
                  <button className="secondary-button" type="button" onClick={cancel}>
                    Hủy tác vụ
                  </button>
                )}
                <button className="secondary-button" type="button" onClick={() => open(selected)}>
                  Tải evidence
                </button>
              </div>
            </div>
            {evidence && (
              <div className="grid gap-3 sm:grid-cols-3">
                <div>
                  <p className="text-2xl font-semibold">{evidence.results?.length || 0}</p>
                  <p className="field-label">Kết quả request</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold">{evidence.logs?.length || 0}</p>
                  <p className="field-label">Dòng nhật ký an toàn</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold">{evidence.artifact_refs?.length || 0}</p>
                  <p className="field-label">Tệp bằng chứng</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      {dialog}
    </Panel>
  );
}
