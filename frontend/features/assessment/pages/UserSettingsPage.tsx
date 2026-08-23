"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { assessmentRequest } from "../services/assessment.service";


export default function UserSettingsPage() {
  const [settings, setSettings] = useState<Record<string, any>>({
    ui_language: "vi",
    theme: "system",
    notifications_enabled: true,
    accessibility_preferences: {},
    default_subject: "",
    privacy_mode: false,
    data_export_format: "json",
  });
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    assessmentRequest<Record<string, any>>("/education/profiles/me/settings").then((value) => setSettings((current) => ({ ...current, ...value }))).catch((reason) => setError(reason instanceof Error ? reason.message : "Không thể tải cài đặt"));
  }, []);

  const save = async () => {
    setError("");
    try {
      const value = await assessmentRequest<Record<string, any>>("/education/profiles/me/settings", {
        method: "PUT",
        body: JSON.stringify({ ...settings, default_subject: settings.default_subject || null }),
      });
      setSettings((current) => ({ ...current, ...value }));
      setStatus("Đã lưu cài đặt người dùng");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể lưu cài đặt");
    }
  };

  const exportData = async () => {
    setError("");
    try {
      const value = await assessmentRequest<Record<string, any>>("/education/profiles/me/export");
      const csvRows = Object.entries(value).flatMap(([section, sectionValue]) => Array.isArray(sectionValue)
        ? sectionValue.map((row, index) => [section, index, JSON.stringify(row)])
        : [[section, 0, JSON.stringify(sectionValue)]]);
      const csv = ["section,index,data", ...csvRows.map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(","))].join("\n");
      const useCsv = settings.data_export_format === "csv";
      const blob = new Blob([useCsv ? csv : JSON.stringify(value, null, 2)], { type: useCsv ? "text/csv" : "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `doclib-user-data-${String(value.export_id || "export")}.${useCsv ? "csv" : "json"}`;
      anchor.click();
      URL.revokeObjectURL(url);
      setStatus("Đã tạo bản xuất dữ liệu có nhật ký kiểm toán");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể xuất dữ liệu");
    }
  };

  const updateAccessibility = (key: string, value: boolean) => setSettings((current) => ({
    ...current,
    accessibility_preferences: { ...(current.accessibility_preferences || {}), [key]: value },
  }));

  return <div className="mx-auto max-w-3xl space-y-6 p-5 md:p-8"><div><p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">User Settings</p><h1 className="mt-2 text-[30px] font-semibold">Cài đặt tài khoản và trải nghiệm</h1><p className="mt-2 text-[13px] text-ink-muted">Môn gần đây chỉ là tiện ích và không trở thành identity cố định</p></div><section className="grid gap-4 rounded-panel border border-border bg-surface p-5 sm:grid-cols-2"><label className="text-[12px] font-semibold text-ink-muted">Ngôn ngữ<select className="apple-input mt-1 w-full" value={settings.ui_language} onChange={(event) => setSettings((current) => ({ ...current, ui_language: event.target.value }))}><option value="vi">Tiếng Việt</option><option value="en">English</option></select></label><label className="text-[12px] font-semibold text-ink-muted">Theme<select className="apple-input mt-1 w-full" value={settings.theme} onChange={(event) => setSettings((current) => ({ ...current, theme: event.target.value }))}><option value="system">Theo hệ thống</option><option value="light">Sáng</option><option value="dark">Tối</option></select></label><label className="text-[12px] font-semibold text-ink-muted">Môn dùng gần đây<input className="apple-input mt-1 w-full" value={settings.default_subject || ""} onChange={(event) => setSettings((current) => ({ ...current, default_subject: event.target.value }))} /></label><label className="text-[12px] font-semibold text-ink-muted">Định dạng xuất dữ liệu<select className="apple-input mt-1 w-full" value={settings.data_export_format} onChange={(event) => setSettings((current) => ({ ...current, data_export_format: event.target.value }))}><option value="json">JSON</option><option value="csv">CSV</option></select></label><label className="flex items-center gap-2 text-[12px] font-semibold"><input type="checkbox" checked={Boolean(settings.notifications_enabled)} onChange={(event) => setSettings((current) => ({ ...current, notifications_enabled: event.target.checked }))} /> Bật thông báo</label><label className="flex items-center gap-2 text-[12px] font-semibold"><input type="checkbox" checked={Boolean(settings.privacy_mode)} onChange={(event) => setSettings((current) => ({ ...current, privacy_mode: event.target.checked }))} /> Chế độ riêng tư tăng cường</label><label className="flex items-center gap-2 text-[12px] font-semibold"><input type="checkbox" checked={Boolean(settings.accessibility_preferences?.reduced_motion)} onChange={(event) => updateAccessibility("reduced_motion", event.target.checked)} /> Giảm chuyển động</label><label className="flex items-center gap-2 text-[12px] font-semibold"><input type="checkbox" checked={Boolean(settings.accessibility_preferences?.high_contrast)} onChange={(event) => updateAccessibility("high_contrast", event.target.checked)} /> Tương phản cao</label><div className="flex flex-wrap gap-2 sm:col-span-2"><button className="apple-button" onClick={() => void save()}>Lưu cài đặt</button><button className="apple-button-secondary" onClick={() => void exportData()}>Xuất dữ liệu cá nhân</button><Link className="apple-button-secondary" href="/cai-dat/vai-tro">Vai trò và cá nhân hóa</Link></div></section>{status && <p role="status" className="rounded-control bg-brand-soft p-3 text-brand">{status}</p>}{error && <p role="alert" className="rounded-control bg-danger-soft p-3 text-danger">{error}</p>}</div>;
}
