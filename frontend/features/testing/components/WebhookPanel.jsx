"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "./DataTable";
import { ErrorState, Panel, StatusPill, useQaActionDialog } from "./TestingUi";
import { formatDate, messageOf } from "../lib/testing";
import { testingApi } from "../services/testing.service";

export default function WebhookPanel({ project }) {
  const { ask, dialog } = useQaActionDialog();
  const [subscriptions, setSubscriptions] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [form, setForm] = useState({
    name: "",
    endpointReference: "",
    secretReference: "",
    events: "DEFECT_CREATED",
  });
  const [error, setError] = useState("");
  const canRead = project.current_permissions?.includes("webhook.project.read");
  const canManage = project.current_permissions?.includes("webhook.project.manage");
  const canReplay = project.current_permissions?.includes("webhook.project.replay");
  const load = useCallback(async () => {
    if (!canRead) return;
    try {
      const [subscriptionValues, deliveryValues] = await Promise.all([
        testingApi.listWebhookSubscriptions(project._id),
        testingApi.listWebhookDeliveries(project._id),
      ]);
      setSubscriptions(subscriptionValues);
      setDeliveries(deliveryValues);
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [canRead, project._id]);
  useEffect(() => {
    void load();
  }, [load]);
  if (!canRead) return null;
  return (
    <Panel title="Móc gọi dự án">
      {error && <ErrorState message={error} />}
      {canManage && (
        <form
          className="grid gap-3 border-b border-border p-5 lg:grid-cols-2"
          onSubmit={async (event) => {
            event.preventDefault();
            try {
              await testingApi.createWebhookSubscription(project._id, {
                name: form.name,
                endpoint_reference: form.endpointReference,
                secret_reference: form.secretReference,
                events: form.events
                  .split("\n")
                  .map((value) => value.trim())
                  .filter(Boolean),
                enabled: true,
              });
              setForm({
                name: "",
                endpointReference: "",
                secretReference: "",
                events: "DEFECT_CREATED",
              });
              await load();
            } catch (reason) {
              setError(messageOf(reason));
            }
          }}
        >
          <input
            aria-label="Tên móc gọi"
            className="apple-input"
            required
            placeholder="Tên móc gọi"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
          />
          <input
            aria-label="Tham chiếu điểm cuối móc gọi"
            className="apple-input"
            pattern="endpoint://.*"
            required
            placeholder="endpoint://nen-tang/ten-diem-cuoi"
            value={form.endpointReference}
            onChange={(event) => setForm({ ...form, endpointReference: event.target.value })}
          />
          <input
            aria-label="Tham chiếu bí mật móc gọi"
            className="apple-input"
            pattern="secret://.*"
            required
            placeholder="secret://nen-tang/ten-bi-mat"
            value={form.secretReference}
            onChange={(event) => setForm({ ...form, secretReference: event.target.value })}
          />
          <textarea
            aria-label="Sự kiện móc gọi"
            className="apple-input min-h-20"
            required
            placeholder="Mỗi dòng là một mã sự kiện"
            value={form.events}
            onChange={(event) => setForm({ ...form, events: event.target.value })}
          />
          <button className="apple-button lg:col-span-2" type="submit">
            Tạo đăng ký móc gọi
          </button>
        </form>
      )}
      <div className="space-y-5 p-5">
        <DataTable
          items={subscriptions}
          empty="Chưa có đăng ký móc gọi"
          columns={[
            { key: "name", label: "Tên" },
            { key: "events", label: "Sự kiện", render: (item) => item.events.join(", ") },
            {
              key: "references",
              label: "Tham chiếu",
              render: (item) => `${item.endpoint_reference} · ${item.secret_reference}`,
            },
            {
              key: "enabled",
              label: "Trạng thái",
              render: (item) => <StatusPill value={item.enabled ? "ACTIVE" : "DISABLED"} />,
            },
            {
              key: "actions",
              label: "Thao tác",
              render: (item) =>
                canManage ? (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={async () => {
                      try {
                        await testingApi.updateWebhookSubscription(project._id, item._id, {
                          expected_revision: item.revision,
                          enabled: !item.enabled,
                        });
                        await load();
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    {item.enabled ? "Vô hiệu hóa" : "Kích hoạt"}
                  </button>
                ) : null,
            },
          ]}
        />
        <DataTable
          items={deliveries}
          empty="Chưa có lần giao móc gọi"
          columns={[
            { key: "event_type", label: "Sự kiện" },
            {
              key: "status",
              label: "Trạng thái",
              render: (item) => <StatusPill value={item.status} />,
            },
            { key: "response_status", label: "Mã phản hồi" },
            { key: "error_code", label: "Mã lỗi" },
            {
              key: "created_at",
              label: "Thời điểm",
              render: (item) => formatDate(item.created_at),
            },
            {
              key: "actions",
              label: "Thao tác",
              render: (item) =>
                canReplay && item.status === "FAILED" ? (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={async () => {
                      const answer = await ask({
                        title: "Phát lại lần giao móc gọi",
                        description: `${item.event_type} ${item.error_code || ""}`,
                        confirmLabel: "Đưa vào hàng đợi",
                        fields: [
                          {
                            name: "reason",
                            label: "Lý do phát lại",
                            required: true,
                            multiline: true,
                          },
                        ],
                      });
                      if (!answer) return;
                      try {
                        await testingApi.replayWebhookDelivery(project._id, item._id, {
                          idempotency_key: crypto.randomUUID(),
                          reason: answer.reason,
                        });
                        await load();
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    Phát lại
                  </button>
                ) : null,
            },
          ]}
        />
      </div>
      {dialog}
    </Panel>
  );
}
