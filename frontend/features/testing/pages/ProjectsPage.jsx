"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Plus, Search } from "lucide-react";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  Panel,
  QaPage,
  StatusPill,
  useQaActionDialog,
} from "../components/TestingUi";
import { testingApi } from "../services/testing.service";
import { formatDate, messageOf } from "../lib/testing";

export default function ProjectsPage() {
  const { ask, dialog } = useQaActionDialog();
  const [items, setItems] = useState([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("active");
  const [form, setForm] = useState({ key: "", name: "", description: "", project_type: "web" });
  const [creating, setCreating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async (value = "", statusValue = "active") => {
    setLoading(true);
    setError("");
    try {
      setItems(await testingApi.listProjects(value, statusValue));
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void load("", status);
  }, [load, status]);
  const submit = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await testingApi.createProject({
        ...form,
        key: form.key.trim().toUpperCase(),
        name: form.name.trim(),
      });
      setForm({ key: "", name: "", description: "", project_type: "web" });
      setCreating(false);
      await load("", status);
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <QaPage
      title="Dự án kiểm thử"
      actions={
        <button
          type="button"
          className="apple-button"
          onClick={() => setCreating((value) => !value)}
        >
          <Plus size={16} />
          Tạo dự án
        </button>
      }
    >
      {error && <ErrorState message={error} />}
      {creating && (
        <Panel title="Tạo dự án mới">
          <form onSubmit={submit} className="grid gap-5 p-5 md:grid-cols-2">
            <label className="field-label block min-w-0">
              Mã dự án
              <input
                className="apple-input mt-2 w-full"
                required
                minLength={2}
                pattern="[A-Za-z][A-Za-z0-9_]+"
                value={form.key}
                onChange={(event) => setForm({ ...form, key: event.target.value })}
                placeholder="THANHTOAN"
              />
            </label>
            <label className="field-label block min-w-0">
              Tên dự án
              <input
                className="apple-input mt-2 w-full"
                required
                minLength={2}
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                placeholder="Nền tảng thanh toán"
              />
            </label>
            <label className="field-label block min-w-0">
              Loại dự án
              <select
                className="apple-input mt-2 w-full"
                value={form.project_type}
                onChange={(event) => setForm({ ...form, project_type: event.target.value })}
              >
                <option value="web">Web</option>
                <option value="mobile">Ứng dụng di động</option>
                <option value="api">API</option>
                <option value="desktop">Ứng dụng máy tính</option>
                <option value="embedded">Thiết bị nhúng</option>
                <option value="other">Khác</option>
              </select>
            </label>
            <label className="field-label block min-w-0 md:col-span-2">
              Mô tả
              <textarea
                className="apple-input mt-2 min-h-24 w-full resize-y"
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
              />
            </label>
            <div className="md:col-span-2">
              <button className="apple-button" type="submit">
                Lưu dự án
              </button>
            </div>
          </form>
        </Panel>
      )}
      <Panel
        title="Danh sách dự án"
        actions={
          <form
            className="flex flex-wrap items-center gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              void load(query, status);
            }}
          >
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-ink-faint" size={16} />
              <input
                aria-label="Tìm dự án"
                className="apple-input w-64 pl-9"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Tìm mã hoặc tên"
              />
            </div>
            <select
              aria-label="Trạng thái dự án"
              className="apple-input"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
            >
              <option value="active">Đang hoạt động</option>
              <option value="archived">Đã lưu trữ</option>
              <option value="all">Tất cả</option>
            </select>
          </form>
        }
      >
        {loading ? (
          <div className="p-5">
            <LoadingState />
          </div>
        ) : items.length === 0 ? (
          <EmptyState actionLabel="Tạo dự án đầu tiên" onAction={() => setCreating(true)}>
            Chưa có dự án kiểm thử
          </EmptyState>
        ) : (
          <div className="divide-y divide-border">
            {items.map((item) => (
              <div
                key={item._id}
                className="grid gap-3 p-5 transition hover:bg-surface-quiet md:grid-cols-[120px_1fr_140px_160px_auto] md:items-center"
              >
                <span className="font-mono text-[13px] font-semibold text-brand">{item.key}</span>
                <Link href={`/du-an/${item._id}`} className="min-w-0">
                  <strong className="block text-[14px]">{item.name}</strong>
                  <small className="line-clamp-1 text-ink-muted">
                    {item.description || "Chưa có mô tả"}
                  </small>
                </Link>
                <StatusPill value={String(item.status).toUpperCase()} />
                <span className="text-[12px] text-ink-muted">{formatDate(item.updated_at)}</span>
                {item.status === "archived" &&
                  item.current_permissions?.includes("project.restore") && (
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={async () => {
                        const answer = await ask({
                          title: "Khôi phục dự án",
                          description: `${item.key} sẽ hoạt động trở lại và tiếp tục nhận thay đổi`,
                          confirmLabel: "Khôi phục",
                          fields: [
                            {
                              name: "reason",
                              label: "Lý do khôi phục",
                              initialValue: "Tiếp tục thực hiện dự án",
                              required: true,
                            },
                          ],
                        });
                        if (!answer) return;
                        try {
                          await testingApi.restoreProject(item._id, {
                            expected_revision: item.revision,
                            reason: answer.reason,
                          });
                          await load(query, status);
                        } catch (reason) {
                          setError(messageOf(reason));
                        }
                      }}
                    >
                      Khôi phục
                    </button>
                  )}
              </div>
            ))}
          </div>
        )}
      </Panel>
      {dialog}
    </QaPage>
  );
}
