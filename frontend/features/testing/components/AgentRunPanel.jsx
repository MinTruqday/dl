"use client";

import { useState } from "react";
import { messageOf, valueLabel } from "../lib/testing";
import { testingApi } from "../services/testing.service";
import { ErrorState, Panel, StatusPill } from "./WorkspacePrimitives";

const INTENTS = [
  { value: "project_question", label: "Hỏi đáp dự án", permission: "ai.ask_project" },
  {
    value: "requirement_analysis",
    label: "Phân tích yêu cầu",
    permission: "ai.run_lint",
  },
  {
    value: "generate_test_cases",
    label: "Sinh ca kiểm thử",
    permission: "ai.generate_testcase",
  },
  { value: "change_impact", label: "Phân tích ảnh hưởng", permission: "ai.run_impact" },
  {
    value: "regression_recommendation",
    label: "Đề xuất hồi quy",
    permission: "ai.generate_regression",
  },
  {
    value: "execution_failure_analysis",
    label: "Phân tích lỗi thực thi",
    permission: "testrun.read",
  },
  {
    value: "status_report",
    label: "Báo cáo trạng thái",
    permission: "teststatusreport.update",
  },
  {
    value: "completion_report",
    label: "Báo cáo hoàn tất",
    permission: "testcompletion.update",
  },
];

export default function AgentRunPanel({ project }) {
  const intents = INTENTS.filter((item) => project.current_permissions?.includes(item.permission));
  const [intent, setIntent] = useState(intents[0]?.value || "");
  const [objective, setObjective] = useState("");
  const [targetIds, setTargetIds] = useState("");
  const [decisionNote, setDecisionNote] = useState("");
  const [actionEdits, setActionEdits] = useState("");
  const [run, setRun] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const canRun = Boolean(intent);

  const execute = async () => {
    if (!objective.trim()) return;
    setBusy(true);
    setError("");
    try {
      const nextRun = await testingApi.runAgent({
        project_id: project._id,
        objective: objective.trim(),
        intent,
        target_artifact_ids: targetIds
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      });
      setRun(nextRun);
      setActionEdits(JSON.stringify(nextRun.proposal?.actions || [], null, 2));
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setBusy(false);
    }
  };

  const decide = async (decision) => {
    setBusy(true);
    setError("");
    if (!decisionNote.trim()) {
      setError("Cần nhập ghi chú quyết định");
      setBusy(false);
      return;
    }
    try {
      let edits = [];
      if (decision === "EDIT") {
        try {
          edits = JSON.parse(actionEdits);
        } catch {
          setError("Nội dung chỉnh sửa phải là JSON hợp lệ");
          setBusy(false);
          return;
        }
        if (!Array.isArray(edits) || edits.length === 0) {
          setError("Cần ít nhất một hành động được chỉnh sửa");
          setBusy(false);
          return;
        }
      }
      const nextRun = await testingApi.decideAgentRun(run.run_id, {
        decision,
        expected_revision: run.revision,
        note: decisionNote.trim(),
        action_edits: edits,
      });
      setRun(nextRun);
      setActionEdits(JSON.stringify(nextRun.proposal?.actions || [], null, 2));
      setDecisionNote("");
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setBusy(false);
    }
  };

  if (!canRun) return null;

  return (
    <Panel title="Tác tử kiểm thử">
      <div className="grid gap-4 p-4">
        {error && <ErrorState message={error} />}
        <label className="grid gap-2 text-sm font-medium text-ink">
          Năng lực
          <select
            className="apple-input"
            value={intent}
            onChange={(event) => setIntent(event.target.value)}
          >
            {intents.map((item) => (
              <option value={item.value} key={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-2 text-sm font-medium text-ink">
          Mục tiêu
          <textarea
            className="apple-input min-h-24"
            value={objective}
            onChange={(event) => setObjective(event.target.value)}
            placeholder="Phân tích rủi ro và đề xuất phạm vi kiểm thử"
          />
        </label>
        <label className="grid gap-2 text-sm font-medium text-ink">
          Mã hiện vật liên quan
          <input
            className="apple-input"
            value={targetIds}
            onChange={(event) => setTargetIds(event.target.value)}
            placeholder="REQ-105, RUN-204"
          />
        </label>
        <div>
          <button
            className="apple-button"
            type="button"
            disabled={busy || !objective.trim()}
            onClick={execute}
          >
            {busy ? "Đang xử lý" : "Chạy tác tử"}
          </button>
        </div>
        {run && (
          <div className="grid gap-4 border-t border-border pt-4 text-sm">
            <div className="flex flex-wrap items-center gap-3">
              <StatusPill value={run.status} />
              <span>{run.run_id}</span>
              <span>Vai trò {valueLabel(run.role)}</span>
            </div>
            {run.proposal?.summary && (
              <div>
                <h3 className="font-semibold text-ink">Kết quả</h3>
                <p className="mt-1 whitespace-pre-wrap text-ink-muted">{run.proposal.summary}</p>
              </div>
            )}
            {run.evidence_refs?.length > 0 && (
              <div>
                <h3 className="font-semibold text-ink">Bằng chứng</h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {run.evidence_refs.map((item) => (
                    <span
                      className="rounded-full border border-border bg-surface px-3 py-1 text-xs"
                      key={item}
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {run.proposal?.warnings?.length > 0 && (
              <div>
                <h3 className="font-semibold text-ink">Cảnh báo</h3>
                <ul className="mt-2 grid gap-1 text-ink-muted">
                  {run.proposal.warnings.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            {run.status === "APPROVAL_REQUIRED" && (
              <div className="grid gap-3">
                <label className="grid gap-2 font-medium text-ink">
                  Hành động đề xuất dạng JSON
                  <textarea
                    className="apple-input min-h-40 font-mono text-xs"
                    value={actionEdits}
                    onChange={(event) => setActionEdits(event.target.value)}
                  />
                </label>
                <label className="grid gap-2 font-medium text-ink">
                  Ghi chú quyết định
                  <textarea
                    className="apple-input min-h-20"
                    value={decisionNote}
                    onChange={(event) => setDecisionNote(event.target.value)}
                  />
                </label>
                <div className="flex flex-wrap gap-2">
                  <button
                    className="apple-button"
                    type="button"
                    disabled={busy || !decisionNote.trim()}
                    onClick={() => decide("APPROVE")}
                  >
                    Duyệt và áp dụng
                  </button>
                  <button
                    className="secondary-button"
                    type="button"
                    disabled={busy || !decisionNote.trim() || !actionEdits.trim()}
                    onClick={() => decide("EDIT")}
                  >
                    Lưu chỉnh sửa
                  </button>
                  <button
                    className="secondary-button"
                    type="button"
                    disabled={busy || !decisionNote.trim()}
                    onClick={() => decide("REJECT")}
                  >
                    Từ chối
                  </button>
                </div>
              </div>
            )}
            {run.proposal?.verification && (
              <div>
                <h3 className="font-semibold text-ink">Xác minh</h3>
                <p className="mt-1 text-ink-muted">
                  {run.proposal.verification.verified
                    ? "Đã xác minh kết quả"
                    : "Xác minh kết quả chưa đạt"}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </Panel>
  );
}
