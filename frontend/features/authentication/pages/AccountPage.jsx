"use client";
import Link from "next/link";
import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { logoutAPI } from "../services/session.service";

export default function AccountPage() {
  const { user, logoutState } = useAuth();
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const closeOtherSessions = async () => {
    setError("");
    try {
      await logoutAPI(true);
      setStatus("Đã đóng toàn bộ phiên đăng nhập khác");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể đóng các phiên khác");
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
        <dl className="grid gap-5 p-5 sm:grid-cols-2">
          <div>
            <dt className="field-label">Tên hiển thị</dt>
            <dd className="mt-2 font-semibold">{user?.full_name || "Chưa có"}</dd>
          </div>
          <div>
            <dt className="field-label">Email</dt>
            <dd className="mt-2 font-semibold">{user?.email}</dd>
          </div>
          <div>
            <dt className="field-label">Vai trò hệ thống</dt>
            <dd className="mt-2 font-semibold">
              {user?.role === "author" ? "Người đóng góp" : user?.role}
            </dd>
          </div>
          <div>
            <dt className="field-label">Mã người dùng</dt>
            <dd className="mt-2 break-all font-mono text-[12px]">{user?._id}</dd>
          </div>
        </dl>
        <div className="flex flex-wrap gap-3 border-t border-border p-5">
          <Link className="secondary-button" href="/qa/projects">
            Về không gian kiểm thử
          </Link>
          <button className="secondary-button" type="button" onClick={closeOtherSessions}>
            Đóng các phiên khác
          </button>
          <button className="secondary-button text-danger" type="button" onClick={logoutState}>
            Đăng xuất
          </button>
        </div>
      </section>
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
