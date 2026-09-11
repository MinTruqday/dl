"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "./DataTable";
import ReviewChecklist from "./ReviewChecklist";
import ReviewFindingsTable from "./ReviewFindingsTable";
import { ErrorState, Panel, StatusPill, useActionDialog } from "./WorkspacePrimitives";
import { messageOf } from "../lib/testing";
import { testingApi } from "../services/testing.service";

export default function FormalReviewPanel({ project, artifactType, artifactId, artifactVersionId, reviewType }) {
  const [sessions, setSessions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [members, setMembers] = useState([]);
  const [error, setError] = useState("");
  const { ask, dialog } = useActionDialog();
  const can = (permission) => project.current_permissions?.includes(permission);
  const load = useCallback(async () => {
    try {
      const [result, memberValues] = await Promise.all([
        testingApi.listReviewSessions(project._id, { artifact_type: artifactType }),
        testingApi.listMembers(project._id),
      ]);
      const values = (result.items || []).filter((item) => item.artifact_id === artifactId && item.artifact_version_id === artifactVersionId);
      setSessions(values);
      setMembers(memberValues.filter((item) => item.status === "ACTIVE"));
      if (selected?._id) setSelected(await testingApi.getReviewSession(selected._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [artifactId, artifactType, artifactVersionId, project._id, selected?._id]);
  useEffect(() => { void load(); }, [load]);
  const memberOptions = members.map((item) => ({ value: item.user_id, label: item.user_label || item.email || item.user_id }));
  const create = async () => {
    const answer = await ask({ title: "Tạo phiên rà soát chính thức", confirmLabel: "Tạo phiên", fields: [
      { name: "objective", label: "Mục tiêu", required: true, multiline: true, autoFocus: true },
      { name: "moderator_id", label: "Moderator", required: true, options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions] },
      { name: "reviewer_id", label: "Reviewer", required: true, options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions] },
      { name: "author_id", label: "Tác giả", required: true, options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions] },
    ] });
    if (!answer) return;
    try {
      const value = await testingApi.createReviewSession(project._id, { idempotency_key: crypto.randomUUID(), review_type: reviewType, artifact_type: artifactType, artifact_id: artifactId, artifact_version_id: artifactVersionId, objective: answer.objective, checklist_version: "V5-1", moderator_id: answer.moderator_id, author_id: answer.author_id, reviewers: [answer.reviewer_id], checklist: [] });
      setSelected(value);
      await load();
    } catch (reason) { setError(messageOf(reason)); }
  };
  const transition = async (action, complete = false) => {
    if (!selected) return;
    const answer = await ask({ title: complete ? "Hoàn tất phiên rà soát" : "Bắt đầu phiên rà soát", confirmLabel: complete ? "Hoàn tất" : "Bắt đầu", fields: complete ? [{ name: "decision", label: "Quyết định", required: true, options: ["ACCEPTED", "ACCEPTED_WITH_ACTIONS", "REWORK_REQUIRED", "REJECTED"].map((value) => ({ value, label: value })) }, { name: "note", label: "Ghi chú", multiline: true }] : [{ name: "note", label: "Ghi chú", multiline: true }] });
    if (!answer) return;
    try { setSelected(await action(selected._id, { expected_revision: selected.revision, ...answer })); await load(); } catch (reason) { setError(messageOf(reason)); }
  };
  const addFinding = async () => {
    const answer = await ask({ title: "Thêm finding", confirmLabel: "Thêm", fields: [
      { name: "severity", label: "Mức độ", options: ["MAJOR", "MINOR", "QUESTION", "IMPROVEMENT"].map((value) => ({ value, label: value })) },
      { name: "category", label: "Nhóm", options: ["CORRECTNESS", "COMPLETENESS", "CONSISTENCY", "TESTABILITY", "TRACEABILITY", "SECURITY", "PERFORMANCE", "MAINTAINABILITY"].map((value) => ({ value, label: value })) },
      { name: "description", label: "Nội dung", required: true, multiline: true },
      { name: "owner_id", label: "Người xử lý", required: true, options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions] },
    ] });
    if (!answer) return;
    try { await testingApi.createReviewFinding(selected._id, { ...answer, anchor: {}, suggested_action: "" }); setSelected(await testingApi.getReviewSession(selected._id)); } catch (reason) { setError(messageOf(reason)); }
  };
  return (
    <Panel title="Rà soát chính thức" actions={can("reviewsession.create") ? <button className="apple-button" type="button" onClick={create}>Tạo phiên rà soát</button> : null}>
      {dialog}
      {error && <div className="p-4"><ErrorState message={error} /></div>}
      <DataTable items={sessions} empty="Chưa có phiên rà soát" columns={[
        { key: "review_type", label: "Loại" },
        { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> },
        { key: "decision", label: "Quyết định" },
        { key: "action", label: "Thao tác", render: (item) => <button className="secondary-button" type="button" onClick={async () => setSelected(await testingApi.getReviewSession(item._id))}>Mở</button> },
      ]} />
      {selected && <div className="space-y-4 border-t border-border p-5">
        <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-semibold">{selected.objective}</p><p className="text-sm text-ink-muted">Checklist {selected.checklist_version}</p></div><div className="flex gap-2">{selected.status === "PLANNED" && can("reviewsession.update") && <button className="secondary-button" type="button" onClick={() => transition(testingApi.startReviewSession)}>Bắt đầu</button>}{selected.status === "IN_PROGRESS" && can("reviewsession.finding.manage") && <button className="secondary-button" type="button" onClick={addFinding}>Thêm finding</button>}{selected.status === "IN_PROGRESS" && can("reviewsession.complete") && <button className="apple-button" type="button" onClick={() => transition(testingApi.completeReviewSession, true)}>Hoàn tất</button>}</div></div>
        <ReviewChecklist items={selected.checklist} />
        <ReviewFindingsTable findings={selected.findings} canManage={can("reviewsession.finding.manage")} onResolve={async (item) => { const answer = await ask({ title: "Xử lý finding", confirmLabel: "Xác nhận", fields: [{ name: "resolution", label: "Kết quả", required: true, multiline: true }] }); if (answer) { await testingApi.updateReviewFinding(item._id, { expected_revision: item.revision, status: "RESOLVED", resolution: answer.resolution }); setSelected(await testingApi.getReviewSession(selected._id)); } }} />
      </div>}
    </Panel>
  );
}
