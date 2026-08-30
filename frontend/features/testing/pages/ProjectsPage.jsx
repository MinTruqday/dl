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
} from "../components/TestingUi";
import { testingApi } from "../services/testing.service";
import { formatDate, messageOf } from "../lib/testing";

export default function ProjectsPage() {
  const [items, setItems] = useState([]);
  const [query, setQuery] = useState("");
  const [form, setForm] = useState({ key: "", name: "", description: "", project_type: "web" });
  const [creating, setCreating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(
    async (value = query) => {
      setLoading(true);
      setError("");
      try {
        setItems(await testingApi.listProjects(value));
      } catch (reason) {
        setError(messageOf(reason));
      } finally {
        setLoading(false);
      }
    },
    [query],
  );
  useEffect(() => {
    void load("");
  }, [load]);
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
      await load("");
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
            className="relative"
            onSubmit={(event) => {
              event.preventDefault();
              void load(query);
            }}
          >
            <Search className="absolute left-3 top-2.5 text-ink-faint" size={16} />
            <input
              aria-label="Tìm dự án"
              className="apple-input w-64 pl-9"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Tìm mã hoặc tên"
            />
          </form>
        }
      >
        {loading ? (
          <div className="p-5">
            <LoadingState />
          </div>
        ) : items.length === 0 ? (
          <EmptyState actionLabel="Tạo dự án đầu tiên" actionHref="#">
            Chưa có dự án kiểm thử
          </EmptyState>
        ) : (
          <div className="divide-y divide-border">
            {items.map((item) => (
              <Link
                key={item._id}
                href={`/qa/projects/${item._id}`}
                className="grid gap-3 p-5 transition hover:bg-surface-quiet md:grid-cols-[120px_1fr_140px_160px] md:items-center"
              >
                <span className="font-mono text-[13px] font-semibold text-brand">{item.key}</span>
                <span>
                  <strong className="block text-[14px]">{item.name}</strong>
                  <small className="line-clamp-1 text-ink-muted">
                    {item.description || "Chưa có mô tả"}
                  </small>
                </span>
                <StatusPill value={String(item.status).toUpperCase()} />
                <span className="text-[12px] text-ink-muted">{formatDate(item.updated_at)}</span>
              </Link>
            ))}
          </div>
        )}
      </Panel>
    </QaPage>
  );
}
