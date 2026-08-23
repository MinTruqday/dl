"use client";

import { useEffect, useState } from "react";
import { assessmentRequest } from "../services/assessment.service";

export default function PersonaSettingsPage() {
  const [personas, setPersonas] = useState<string[]>([]);
  const [status, setStatus] = useState("");
  const [preferredQuestionTypes, setPreferredQuestionTypes] = useState("");
  const [preferredDifficulty, setPreferredDifficulty] = useState("");
  const [rubricStyle, setRubricStyle] = useState("");
  const [distractorStyle, setDistractorStyle] = useState("");
  const [useOwnMaterials, setUseOwnMaterials] = useState(true);
  const [inferredPreferences, setInferredPreferences] = useState<Record<string, unknown>>({});
  const [signals, setSignals] = useState<Record<string, any>[]>([]);
  const loadTeacherProfile = async () => {
    const [profile, recentSignals] = await Promise.all([
      assessmentRequest<Record<string, any>>("/education/teacher-profile/me"),
      assessmentRequest<Record<string, any>[]>("/education/teacher-profile/me/events"),
    ]);
    const explicit = profile.explicit_preferences || {};
    setPreferredQuestionTypes((explicit.preferred_question_types || []).join(", "));
    setPreferredDifficulty(explicit.preferred_target_difficulty == null ? "" : String(explicit.preferred_target_difficulty));
    setRubricStyle(String(explicit.rubric_style || ""));
    setDistractorStyle(String(explicit.distractor_style || ""));
    setUseOwnMaterials(profile.use_own_materials !== false);
    setInferredPreferences(profile.inferred_preferences || {});
    setSignals(recentSignals);
  };
  useEffect(() => {
    assessmentRequest<{ personas?: string[] }>("/education/profiles/me").then((profile) => setPersonas(profile.personas || []));
    loadTeacherProfile().catch(() => undefined);
  }, []);
  const toggle = (persona: string) => setPersonas((current) => current.includes(persona) ? current.filter((value) => value !== persona) : [...current, persona]);
  const save = async () => { if (!personas.length) return; await assessmentRequest("/education/profiles/me", { method: "PUT", body: JSON.stringify({ personas }) }); setStatus("Đã lưu vai trò sử dụng"); };
  const saveTeacherProfile = async () => {
    await assessmentRequest("/education/teacher-profile/me", {
      method: "PUT",
      body: JSON.stringify({
        explicit_preferences: {
          preferred_question_types: preferredQuestionTypes.split(/[,;\n]+/).map((value) => value.trim()).filter(Boolean),
          preferred_target_difficulty: preferredDifficulty ? Number(preferredDifficulty) : null,
          rubric_style: rubricStyle.trim(),
          distractor_style: distractorStyle.trim(),
        },
        use_own_materials: useOwnMaterials,
      }),
    });
    setStatus("Đã lưu tùy chọn giáo viên");
    await loadTeacherProfile();
  };
  const resetPersonalization = async () => {
    if (!window.confirm("Xóa toàn bộ tùy chọn và tín hiệu cá nhân hóa đã suy ra")) return;
    await assessmentRequest("/education/teacher-profile/me/personalization", { method: "DELETE" });
    setPreferredQuestionTypes("");
    setPreferredDifficulty("");
    setRubricStyle("");
    setDistractorStyle("");
    setInferredPreferences({});
    setSignals([]);
    setStatus("Đã đặt lại cá nhân hóa");
  };
  return <div className="mx-auto max-w-3xl space-y-6 p-5 md:p-8"><div><p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">Education Profile</p><h1 className="mt-2 text-[30px] font-semibold">Vai trò và cá nhân hóa</h1><p className="mt-2 text-[13px] text-ink-muted">Persona điều khiển trải nghiệm nghiệp vụ và không thay thế quyền bảo mật hiện tại</p></div><section className="rounded-panel border border-border bg-surface p-5"><div className="grid gap-3 sm:grid-cols-2">{[["teacher", "Giáo viên"], ["student", "Học sinh"]].map(([value, label]) => <button key={value} className={`rounded-control border p-5 text-left ${personas.includes(value) ? "border-brand bg-brand-soft" : "border-border"}`} onClick={() => toggle(value)} aria-pressed={personas.includes(value)}><p className="font-semibold">{label}</p><p className="mt-1 text-[12px] text-ink-muted">Có thể chọn đồng thời cả hai vai trò</p></button>)}</div><button className="apple-button mt-5" disabled={!personas.length} onClick={save}>Lưu vai trò sử dụng</button></section><section className="rounded-panel border border-border bg-surface p-5"><h2 className="font-semibold">Tùy chọn giáo viên có thể chỉnh sửa</h2><div className="mt-4 grid gap-3 sm:grid-cols-2"><label className="text-[12px] font-semibold text-ink-muted">Loại câu ưa dùng<input className="apple-input mt-1 w-full" value={preferredQuestionTypes} onChange={(event) => setPreferredQuestionTypes(event.target.value)} placeholder="single_choice numeric" /></label><label className="text-[12px] font-semibold text-ink-muted">Target difficulty thường dùng<input className="apple-input mt-1 w-full" type="number" min="1" max="5" step="0.1" value={preferredDifficulty} onChange={(event) => setPreferredDifficulty(event.target.value)} /></label><label className="text-[12px] font-semibold text-ink-muted">Phong cách rubric<input className="apple-input mt-1 w-full" value={rubricStyle} onChange={(event) => setRubricStyle(event.target.value)} /></label><label className="text-[12px] font-semibold text-ink-muted">Phong cách distractor<input className="apple-input mt-1 w-full" value={distractorStyle} onChange={(event) => setDistractorStyle(event.target.value)} /></label><label className="flex items-center gap-2 text-[12px] font-semibold text-ink-muted sm:col-span-2"><input type="checkbox" checked={useOwnMaterials} onChange={(event) => setUseOwnMaterials(event.target.checked)} /> Cho phép AI dùng tài liệu riêng thuộc sở hữu của tôi</label></div><div className="mt-4 flex gap-2"><button className="apple-button" onClick={() => void saveTeacherProfile()}>Lưu tùy chọn</button><button className="apple-button-secondary text-danger" onClick={() => void resetPersonalization()}>Đặt lại cá nhân hóa</button></div><details className="mt-4 rounded-control border border-border p-3 text-[12px]"><summary className="cursor-pointer font-semibold">Tùy chọn hệ thống suy ra</summary><pre className="mt-2 overflow-auto whitespace-pre-wrap text-ink-muted">{JSON.stringify(inferredPreferences, null, 2)}</pre></details><details className="mt-3 rounded-control border border-border p-3 text-[12px]"><summary className="cursor-pointer font-semibold">Tín hiệu gần đây</summary><div className="mt-2 space-y-2">{signals.slice(0, 20).map((signal) => <div key={signal._id} className="rounded-control bg-surface-quiet p-2"><p className="font-semibold">{signal.event_type}</p><p className="mt-1 text-ink-muted">{JSON.stringify(signal.payload)}</p></div>)}{!signals.length && <p className="text-ink-muted">Chưa có tín hiệu cá nhân hóa</p>}</div></details></section>{status && <p className="text-[13px] text-brand">{status}</p>}</div>;
}
