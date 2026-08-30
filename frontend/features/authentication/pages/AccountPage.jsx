"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  changeMyPassword,
  listMySessions,
  logoutAPI,
  revokeMySession,
  updateMyProfile,
} from "../services/session.service";

export default function AccountPage() {
  const { user, logoutState, refreshUser } = useAuth();
  const [profile, setProfile] = useState({
    full_name: "",
    locale: "vi-VN",
    timezone: "Asia/Ho_Chi_Minh",
  });
  const [password, setPassword] = useState({ current_password: "", new_password: "" });
  const [sessions, setSessions] = useState([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);

  useEffect(() => {
    setProfile({
      full_name: user?.full_name || "",
      locale: user?.locale || "vi-VN",
      timezone: user?.timezone || "Asia/Ho_Chi_Minh",
    });
  }, [user]);
  const loadSessions = useCallback(async () => {
    try {
      const data = await listMySessions();
      setSessions(Array.isArray(data) ? data : []);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể tải danh sách phiên đăng nhập",
      );
    }
  }, []);
  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);
  const submitProfile = async (event) => {
    event.preventDefault();
    setSavingProfile(true);
    setStatus("");
    setError("");
    try {
      await updateMyProfile(profile);
      await refreshUser();
      setStatus("Đã cập nhật thông tin cá nhân");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể cập nhật thông tin cá nhân");
    } finally {
      setSavingProfile(false);
    }
  };
  const submitPassword = async (event) => {
    event.preventDefault();
    setSavingPassword(true);
    setStatus("");
    setError("");
    try {
      await changeMyPassword(password);
      setPassword({ current_password: "", new_password: "" });
      await loadSessions();
      setStatus("Đã đổi mật khẩu và đóng các phiên khác");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể đổi mật khẩu");
    } finally {
      setSavingPassword(false);
    }
  };
  const closeOtherSessions = async () => {
    setError("");
    try {
      await logoutAPI(true);
      await loadSessions();
      setStatus("Đã đóng toàn bộ phiên đăng nhập khác");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể đóng các phiên khác");
    }
  };
  const revokeSession = async (sessionId) => {
    setError("");
    try {
      await revokeMySession(sessionId);
      await loadSessions();
      setStatus("Đã thu hồi phiên đăng nhập");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể thu hồi phiên đăng nhập");
    }
  };
  return (
    <div className="mx-auto w-full max-w-[980px] space-y-7 p-4 sm:p-6 md:p-9">
      <header className="border-b border-border pb-6">
        <h1 className="text-[32px] font-semibold tracking-[-0.04em]">Tài khoản và bảo mật</h1>
        <p className="mt-3 max-w-2xl text-[14px] leading-7 text-ink-muted">
          Quản lý danh tính, quyền truy cập và các phiên đăng nhập của bạn
        </p>
      </header>
      <section className="overflow-hidden rounded-2xl border border-border bg-surface shadow-[0_8px_24px_rgba(48,47,42,0.04)]">
        <div className="border-b border-border bg-surface-raised px-5 py-4">
          <h2 className="font-semibold">Thông tin cá nhân</h2>
          <p className="mt-1 text-[12px] text-ink-muted">
            Thông tin này được dùng chung trong không gian kiểm thử
          </p>
        </div>
        <form className="grid gap-5 p-5 sm:grid-cols-2" onSubmit={submitProfile}>
          <label className="field-label">
            Tên hiển thị
            <input
              className="text-input mt-2"
              value={profile.full_name}
              onChange={(event) => setProfile({ ...profile, full_name: event.target.value })}
              required
            />
          </label>
          <div>
            <span className="field-label">Email</span>
            <p className="mt-2 font-semibold">{user?.email}</p>
          </div>
          <div>
            <span className="field-label">Vai trò hệ thống</span>
            <p className="mt-2 font-semibold">
              {user?.role === "author" ? "Người đóng góp" : user?.role}
            </p>
          </div>
          <div>
            <span className="field-label">Mã người dùng</span>
            <p className="mt-2 break-all font-mono text-[12px]">{user?._id}</p>
          </div>
          <label className="field-label">
            Ngôn ngữ
            <input
              className="text-input mt-2"
              value={profile.locale}
              onChange={(event) => setProfile({ ...profile, locale: event.target.value })}
            />
          </label>
          <label className="field-label">
            Múi giờ
            <input
              className="text-input mt-2"
              value={profile.timezone}
              onChange={(event) => setProfile({ ...profile, timezone: event.target.value })}
            />
          </label>
          <div className="sm:col-span-2">
            <button className="primary-button" type="submit" disabled={savingProfile}>
              {savingProfile ? "Đang lưu" : "Lưu thông tin"}
            </button>
          </div>
        </form>
      </section>
      <section className="rounded-2xl border border-border bg-surface p-5">
        <h2 className="font-semibold">Đổi mật khẩu</h2>
        <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={submitPassword}>
          <label className="field-label">
            Mật khẩu hiện tại
            <input
              className="text-input mt-2"
              type="password"
              value={password.current_password}
              onChange={(event) =>
                setPassword({ ...password, current_password: event.target.value })
              }
              required
            />
          </label>
          <label className="field-label">
            Mật khẩu mới
            <input
              className="text-input mt-2"
              type="password"
              minLength={12}
              value={password.new_password}
              onChange={(event) => setPassword({ ...password, new_password: event.target.value })}
              required
            />
          </label>
          <div className="sm:col-span-2">
            <button className="secondary-button" type="submit" disabled={savingPassword}>
              {savingPassword ? "Đang cập nhật" : "Đổi mật khẩu"}
            </button>
          </div>
        </form>
      </section>
      <section className="rounded-2xl border border-border bg-surface p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-semibold">Phiên đăng nhập</h2>
            <p className="mt-1 text-[12px] text-ink-muted">
              Thu hồi từng phiên hoặc đóng toàn bộ phiên khác
            </p>
          </div>
          <button className="secondary-button" type="button" onClick={closeOtherSessions}>
            Đóng các phiên khác
          </button>
        </div>
        <div className="mt-4 divide-y divide-border border-y border-border">
          {sessions.length ? (
            sessions.map((session) => (
              <div
                className="flex flex-wrap items-center justify-between gap-3 py-3"
                key={session._id}
              >
                <div>
                  <p className="text-sm font-medium">
                    {session.is_current ? "Phiên hiện tại" : "Thiết bị đã đăng nhập"}
                  </p>
                  <p className="text-xs text-ink-muted">
                    {session.created_at
                      ? new Date(session.created_at).toLocaleString("vi-VN")
                      : "Không rõ thời điểm"}
                  </p>
                </div>
                {!session.is_current && (
                  <button
                    className="text-sm text-danger"
                    type="button"
                    onClick={() => revokeSession(session._id)}
                  >
                    Thu hồi
                  </button>
                )}
              </div>
            ))
          ) : (
            <p className="py-4 text-sm text-ink-muted">Chưa có phiên đăng nhập</p>
          )}
        </div>
      </section>
      <div className="flex flex-wrap gap-3">
        <Link className="secondary-button" href="/qa/projects">
          Về không gian kiểm thử
        </Link>
        <button className="secondary-button text-danger" type="button" onClick={logoutState}>
          Đăng xuất
        </button>
      </div>
      {status && (
        <p role="status" className="rounded-control bg-brand-soft p-3 text-brand">
          {status}
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
