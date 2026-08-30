"use client";
import { useCallback, useEffect, useState } from "react";
import { adminApi } from "@/features/authentication/services/admin.service";
import DataTable from "./DataTable";
import { ErrorState, LoadingState, Panel, StatusPill, useQaActionDialog } from "./TestingUi";
import { formatDate, messageOf } from "../lib/testing";

export default function AdminPlatformPanel() {
  const { ask, dialog } = useQaActionDialog();
  const [projects, setProjects] = useState([]);
  const [policy, setPolicy] = useState(null);
  const [providers, setProviders] = useState([]);
  const [models, setModels] = useState([]);
  const [health, setHealth] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [projectValues, policyValue, providerValues, modelValues, healthValue, jobValues] =
        await Promise.all([
          adminApi.listProjects(),
          adminApi.getProjectPolicy(),
          adminApi.listProviders(),
          adminApi.listModels(),
          adminApi.getHealth(),
          adminApi.listJobs(),
        ]);
      setProjects(projectValues);
      setPolicy(policyValue);
      setProviders(providerValues);
      setModels(modelValues);
      setHealth(healthValue);
      setJobs(jobValues);
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-5">
      {error && <ErrorState message={error} />}
      <Panel title="Trạng thái dịch vụ nền tảng">
        <DataTable
          items={health?.services || []}
          empty="Chưa có dữ liệu trạng thái"
          columns={[
            { key: "service", label: "Dịch vụ" },
            {
              key: "healthy",
              label: "Trạng thái",
              render: (item) => <StatusPill value={item.healthy ? "ACTIVE" : "FAILED"} />,
            },
            { key: "status_code", label: "Mã phản hồi" },
          ]}
        />
      </Panel>
      <Panel title="Chính sách tạo dự án">
        <div className="flex flex-wrap items-end gap-3 p-5">
          <label className="field-label">
            Người được phép tạo dự án
            <select
              className="apple-input mt-2"
              value={policy?.project_creation_policy || "AUTHENTICATED"}
              onChange={async (event) => {
                const desired = event.target.value;
                const answer = await ask({
                  title: "Thay đổi chính sách tạo dự án",
                  description:
                    desired === "ADMIN_ONLY"
                      ? "Chỉ quản trị viên hệ thống được tạo dự án mới"
                      : "Mọi tài khoản đã xác thực được tạo dự án mới",
                  confirmLabel: "Áp dụng",
                  fields: [
                    {
                      name: "reason",
                      label: "Lý do",
                      required: true,
                      multiline: true,
                    },
                  ],
                });
                if (!answer) return;
                try {
                  await adminApi.updateProjectPolicy(desired, answer.reason);
                  await load();
                } catch (reason) {
                  setError(messageOf(reason));
                }
              }}
            >
              <option value="AUTHENTICATED">Tài khoản đã xác thực</option>
              <option value="ADMIN_ONLY">Chỉ quản trị viên</option>
            </select>
          </label>
        </div>
      </Panel>

      <Panel title="Siêu dữ liệu dự án">
        <DataTable
          items={projects}
          empty="Chưa có dự án"
          columns={[
            { key: "key", label: "Mã" },
            { key: "name", label: "Tên" },
            { key: "project_type", label: "Loại" },
            {
              key: "status",
              label: "Trạng thái",
              render: (item) => <StatusPill value={String(item.status).toUpperCase()} />,
            },
            { key: "member_count", label: "Thành viên" },
            {
              key: "updated_at",
              label: "Cập nhật",
              render: (item) => formatDate(item.updated_at),
            },
          ]}
        />
      </Panel>

      <Panel title="Nhà cung cấp và mô hình AI">
        <DataTable
          items={providers}
          empty="Chưa có cấu hình AI"
          columns={[
            { key: "_id", label: "Nhà cung cấp" },
            { key: "model", label: "Mô hình" },
            {
              key: "enabled",
              label: "Trạng thái",
              render: (item) => <StatusPill value={item.enabled ? "ACTIVE" : "DISABLED"} />,
            },
            { key: "timeout_seconds", label: "Thời gian chờ" },
            { key: "max_output_tokens", label: "Giới hạn đầu ra" },
            {
              key: "actions",
              label: "Thao tác",
              render: (item) => (
                <span className="flex flex-wrap gap-2">
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={async () => {
                      try {
                        await adminApi.testProvider(item._id);
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    Kiểm tra kết nối
                  </button>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={async () => {
                      const answer = await ask({
                        title: item.enabled ? "Tắt nhà cung cấp AI" : "Bật nhà cung cấp AI",
                        description: "Thay đổi được ghi nhận và yêu cầu khởi động lại dịch vụ AI",
                        confirmLabel: "Lưu cấu hình",
                        fields: [
                          {
                            name: "reason",
                            label: "Lý do",
                            required: true,
                          },
                        ],
                      });
                      if (!answer) return;
                      try {
                        await adminApi.updateProvider(item._id, {
                          enabled: !item.enabled,
                          reason: answer.reason,
                        });
                        await load();
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    {item.enabled ? "Tắt" : "Bật"}
                  </button>
                </span>
              ),
            },
          ]}
        />
      </Panel>
      <Panel title="Tác vụ nền">
        <DataTable
          items={jobs}
          empty="Chưa có tác vụ nền"
          columns={[
            { key: "_id", label: "Mã tác vụ" },
            { key: "kind", label: "Loại" },
            {
              key: "status",
              label: "Trạng thái",
              render: (item) => <StatusPill value={String(item.status).toUpperCase()} />,
            },
            {
              key: "updated_at",
              label: "Cập nhật",
              render: (item) => formatDate(item.updated_at),
            },
            {
              key: "retry",
              label: "Thao tác",
              render: (item) =>
                String(item.status).toLowerCase() === "failed" ? (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={async () => {
                      try {
                        await adminApi.retryJob(item._id);
                        await load();
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    Thử lại
                  </button>
                ) : null,
            },
          ]}
        />
      </Panel>
      <Panel title="Danh mục mô hình AI">
        <DataTable
          items={models}
          empty="Chưa có mô hình AI được đăng ký"
          columns={[
            { key: "provider_id", label: "Nhà cung cấp" },
            { key: "model", label: "Mô hình" },
            { key: "version", label: "Phiên bản" },
            {
              key: "enabled",
              label: "Trạng thái",
              render: (item) => <StatusPill value={item.enabled ? "ACTIVE" : "DISABLED"} />,
            },
            {
              key: "capabilities",
              label: "Năng lực",
              render: (item) => (item.capabilities || []).join(", "),
            },
          ]}
        />
      </Panel>
      {dialog}
    </div>
  );
}
