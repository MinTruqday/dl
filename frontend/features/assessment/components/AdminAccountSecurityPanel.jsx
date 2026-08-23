"use client";
import { useCallback, useEffect, useState } from "react";
import { assessmentRequest } from "../services/assessment.service";
export default function AdminAccountSecurityPanel() {
  const [accounts, setAccounts] = useState([]);
  const [events, setEvents] = useState([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const load = useCallback(async () => {
    try {
      const query = search.trim() ? `?search=${encodeURIComponent(search.trim())}` : "";
      const [accountResult, auditResult] = await Promise.all([
        assessmentRequest(`/xac-thuc/quan-tri/tai-khoan${query}`),
        assessmentRequest("/xac-thuc/quan-tri/nhat-ky?limit=200"),
      ]);
      setAccounts(accountResult.data || []);
      setEvents(auditResult.data || []);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tải quản trị tài khoản");
    }
  }, [search]);
  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 250);
    return () => window.clearTimeout(timer);
  }, [load]);
  const updateAccount = async (account, changes) => {
    const reason = window.prompt("Lý do thực hiện hành động quản trị");
    if (!reason?.trim()) return;
    setError("");
    try {
      await assessmentRequest(`/xac-thuc/quan-tri/tai-khoan/${encodeURIComponent(account._id)}`, {
        method: "PATCH",
        body: JSON.stringify({
          ...changes,
          reason: reason.trim(),
        }),
      });
      setMessage("Đã cập nhật tài khoản và thu hồi toàn bộ phiên hiện hữu");
      await load();
    } catch (reasonValue) {
      setError(reasonValue instanceof Error ? reasonValue.message : "Không thể cập nhật tài khoản");
    }
  };
  const changeRole = async (account) => {
    const role = window.prompt("Vai trò mới reader author admin", account.role || "reader");
    if (!role || !["reader", "author", "admin"].includes(role)) {
      if (role !== null) setError("Vai trò không hợp lệ");
      return;
    }
    await updateAccount(account, { role });
  };
  return (
    <div className="space-y-6">
      <section className="rounded-panel border border-border bg-surface">
        <div className="border-b border-border p-5">
          <h2 className="font-semibold">Quản trị tài khoản theo RBAC</h2>
          <input
            className="apple-input mt-3 w-full max-w-md"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Tìm email tên hoặc slug"
          />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[850px] text-left text-[12px]">
            <thead className="bg-surface-quiet text-ink-muted">
              <tr>
                <th className="p-4">Tài khoản</th>
                <th className="p-4">Vai trò</th>
                <th className="p-4">Trạng thái</th>
                <th className="p-4">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((account) => (
                <tr key={account._id} className="border-t border-border">
                  <td className="p-4">
                    <p className="font-semibold">{account.full_name}</p>
                    <p className="text-ink-muted">
                      {account.email} · {account.slug}
                    </p>
                  </td>
                  <td className="p-4">{account.role}</td>
                  <td className="p-4">{account.is_active ? "Đang hoạt động" : "Đã khóa"}</td>
                  <td className="p-4">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        className="apple-button-secondary"
                        onClick={() => void changeRole(account)}
                      >
                        Đổi vai trò
                      </button>
                      <button
                        type="button"
                        className="apple-button-secondary text-danger"
                        onClick={() =>
                          void updateAccount(account, { is_active: !account.is_active })
                        }
                      >
                        {account.is_active ? "Khóa" : "Mở khóa"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="overflow-x-auto rounded-panel border border-border bg-surface">
        <div className="border-b border-border px-5 py-4 font-semibold">
          Nhật ký xác thực và hành động tài khoản
        </div>
        <table className="w-full min-w-[850px] text-left text-[12px]">
          <thead className="bg-surface-quiet text-ink-muted">
            <tr>
              <th className="p-4">Thời gian</th>
              <th className="p-4">Actor</th>
              <th className="p-4">Hành động</th>
              <th className="p-4">Lý do</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event._id} className="border-t border-border">
                <td className="p-4">
                  {event.timestamp ? new Date(event.timestamp).toLocaleString("vi-VN") : "Chưa có"}
                </td>
                <td className="p-4">{event.actor_email || event.actor_slug || "Không xác định"}</td>
                <td className="p-4 font-semibold">{event.action}</td>
                <td className="p-4">{event.reason || event.ip || "Không có"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {message && (
        <p role="status" className="rounded-control bg-brand-soft p-3 text-brand">
          {message}
        </p>
      )}
      {error && (
        <p role="alert" className="rounded-control bg-danger-soft p-3 text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
