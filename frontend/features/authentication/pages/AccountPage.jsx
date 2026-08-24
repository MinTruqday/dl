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
      setStatus("Đã đóng toàn bộ phiên đăng nhập khác")
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể đóng các phiên khác")
    }
  };
  return <div className="mx-auto w-full max-w-3xl space-y-6 p-5 md:p-8">
    <header><p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">Account</p><h1 className="mt-2 text-[30px] font-semibold">Tài khoản và bảo mật</h1><p className="mt-2 text-[13px] text-ink-muted">Thông tin nhận dạng dùng chung cho mọi Project QA</p></header>
    <section className="rounded-panel border border-border bg-surface p-5"><dl className="grid gap-5 sm:grid-cols-2"><div><dt className="field-label">Tên hiển thị</dt><dd className="mt-2 font-semibold">{user?.full_name || "Chưa có"}</dd></div><div><dt className="field-label">Email</dt><dd className="mt-2 font-semibold">{user?.email}</dd></div><div><dt className="field-label">Vai trò hệ thống</dt><dd className="mt-2 font-semibold">{user?.role}</dd></div><div><dt className="field-label">Mã người dùng</dt><dd className="mt-2 break-all font-mono text-[12px]">{user?._id}</dd></div></dl><div className="mt-6 flex flex-wrap gap-3"><Link className="secondary-button" href="/qa/projects">Về QA Workspace</Link><button className="secondary-button" type="button" onClick={closeOtherSessions}>Đóng các phiên khác</button><button className="secondary-button text-danger" type="button" onClick={logoutState}>Đăng xuất</button></div></section>
    {status && <p role="status" className="rounded-control bg-brand-soft p-3 text-brand">{status}</p>}
    {error && <p role="alert" className="rounded-control bg-danger-soft p-3 text-danger">{error}</p>}
  </div>;
}
