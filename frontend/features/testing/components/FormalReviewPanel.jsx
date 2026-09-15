"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "./DataTable";
import ReviewChecklist from "./ReviewChecklist";
import ReviewFindingsTable from "./ReviewFindingsTable";
import { ErrorState, Panel, StatusPill, useActionDialog } from "./WorkspacePrimitives";
import { messageOf } from "../lib/testing";
import { testingApi } from "../services/testing.service";

export default function FormalReviewPanel({
  project,
  artifactType,
  artifactId,
  artifactVersionId,
  reviewType,
}) {
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
      const values = (result.items || []).filter(
        (item) => item.artifact_id === artifactId && item.artifact_version_id === artifactVersionId,
      );
      setSessions(values);
      setMembers(memberValues.filter((item) => item.status === "ACTIVE"));
      if (selected?._id) setSelected(await testingApi.getReviewSession(selected._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [artifactId, artifactType, artifactVersionId, project._id, selected?._id]);
  useEffect(() => {
    void load();
  }, [load]);
  const memberOptions = members.map((item) => ({
    value: item.user_id,
    label: item.user_label || item.email || item.user_id,
  }));
  const create = async () => {
    const answer = await ask({
      title: "Tạo phiên rà soát chính thức",
      confirmLabel: "Tạo phiên",
      fields: [
        { name: "objective", label: "Mục tiêu", required: true, multiline: true, autoFocus: true },
        {
          name: "moderator_id",
          label: "Moderator",
          required: true,
          options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions],
        },
        {
          name: "reviewer_id",
          label: "Reviewer",
          required: true,
          options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions],
        },
        {
          name: "author_id",
          label: "Tác giả",
          required: true,
          options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions],
        },
      ],
    });
    if (!answer) return;
    try {
      const value = await testingApi.createReviewSession(project._id, {
        idempotency_key: crypto.randomUUID(),
        review_type: reviewType,
        artifact_type: artifactType,
        artifact_id: artifactId,
        artifact_version_id: artifactVersionId,
        objective: answer.objective,
        checklist_version: "1",
        moderator_id: answer.moderator_id,
        author_id: answer.author_id,
        reviewers: [answer.reviewer_id],
        checklist: [],
      });
      setSelected(value);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const transition = async (action, mode = "start") => {
    if (!selected) return;
    const decision = mode === "decision";
    const complete = mode === "complete";
    const answer = await ask({
      title: decision
        ? "Ghi nhận quyết định rà soát"
        : complete
          ? "Hoàn tất phiên rà soát"
          : "Bắt đầu phiên rà soát",
      confirmLabel: decision ? "Ghi quyết định" : complete ? "Hoàn tất" : "Bắt đầu",
      fields: decision
        ? [
            {
              name: "decision",
              label: "Quyết định",
              required: true,
              options: ["ACCEPTED", "ACCEPTED_WITH_ACTIONS", "REWORK_REQUIRED", "REJECTED"].map(
                (value) => ({ value, label: value }),
              ),
            },
            { name: "note", label: "Ghi chú", multiline: true },
          ]
        : [{ name: "note", label: "Ghi chú", multiline: true }],
    });
    if (!answer) return;
    try {
      setSelected(await action(selected._id, { expected_revision: selected.revision, ...answer }));
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const addFinding = async () => {
    const answer = await ask({
      title: "Thêm phát hiện",
      confirmLabel: "Thêm",
      fields: [
        {
          name: "severity",
          label: "Mức độ",
          options: ["MAJOR", "MINOR", "QUESTION", "IMPROVEMENT"].map((value) => ({
            value,
            label: value,
          })),
        },
        {
          name: "category",
          label: "Nhóm",
          options: [
            "CORRECTNESS",
            "COMPLETENESS",
            "CONSISTENCY",
            "TESTABILITY",
            "TRACEABILITY",
            "SECURITY",
            "PERFORMANCE",
            "MAINTAINABILITY",
          ].map((value) => ({ value, label: value })),
        },
        { name: "description", label: "Nội dung", required: true, multiline: true },
        {
          name: "owner_id",
          label: "Người xử lý",
          options: [{ value: "", label: "Chưa phân công" }, ...memberOptions],
        },
        { name: "due_at", label: "Hạn xử lý", type: "datetime-local" },
      ],
    });
    if (!answer) return;
    try {
      await testingApi.createReviewFinding(selected._id, {
        ...answer,
        owner_id: answer.owner_id || null,
        due_at: answer.due_at ? new Date(answer.due_at).toISOString() : null,
        anchor: {},
        suggested_action: "",
      });
      setSelected(await testingApi.getReviewSession(selected._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const assignParticipants = async () => {
    const answer = await ask({
      title: "Phân công phiên rà soát",
      confirmLabel: "Lưu phân công",
      fields: [
        {
          name: "moderator_id",
          label: "Moderator",
          required: true,
          options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions],
          initialValue: selected.moderator_id,
        },
        {
          name: "reviewer_id",
          label: "Reviewer",
          required: true,
          options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions],
          initialValue: (selected.reviewer_ids || selected.reviewers || [])[0],
        },
        {
          name: "scribe_id",
          label: "Scribe",
          options: [{ value: "", label: "Không phân công" }, ...memberOptions],
          initialValue: selected.scribe_id || "",
        },
      ],
    });
    if (!answer) return;
    try {
      setSelected(
        await testingApi.assignReviewSessionReviewers(selected._id, {
          expected_revision: selected.revision,
          moderator_id: answer.moderator_id,
          reviewer_ids: [answer.reviewer_id],
          scribe_id: answer.scribe_id || null,
        }),
      );
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const assignFinding = async (item) => {
    const answer = await ask({
      title: "Gán phát hiện",
      confirmLabel: "Gán",
      fields: [
        {
          name: "owner_id",
          label: "Người xử lý",
          required: true,
          options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions],
          initialValue: item.owner_id,
        },
      ],
    });
    if (!answer) return;
    try {
      await testingApi.assignReviewFinding(item._id, {
        expected_revision: item.revision,
        owner_id: answer.owner_id,
      });
      setSelected(await testingApi.getReviewSession(selected._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const resolveFinding = async (item) => {
    const answer = await ask({
      title: "Giải quyết phát hiện",
      confirmLabel: "Ghi nhận",
      fields: [{ name: "resolution", label: "Kết quả", required: true, multiline: true }],
    });
    if (!answer) return;
    try {
      await testingApi.resolveReviewFinding(item._id, {
        expected_revision: item.revision,
        resolution: answer.resolution,
      });
      setSelected(await testingApi.getReviewSession(selected._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const verifyFinding = async (item) => {
    const answer = await ask({
      title: "Xác minh phát hiện",
      confirmLabel: "Xác minh",
      fields: [{ name: "note", label: "Kết quả xác minh", required: true, multiline: true }],
    });
    if (!answer) return;
    try {
      await testingApi.verifyReviewFinding(item._id, {
        expected_revision: item.revision,
        note: answer.note,
      });
      setSelected(await testingApi.getReviewSession(selected._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const createFollowUp = async () => {
    const answer = await ask({
      title: "Tạo phiên rà soát tiếp theo",
      confirmLabel: "Tạo phiên",
      fields: [
        { name: "objective", label: "Mục tiêu", required: true, multiline: true },
        {
          name: "moderator_id",
          label: "Moderator",
          required: true,
          options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions],
          initialValue: selected.moderator_id,
        },
        {
          name: "reviewer_id",
          label: "Reviewer",
          required: true,
          options: [{ value: "", label: "Chọn thành viên" }, ...memberOptions],
          initialValue: (selected.reviewer_ids || selected.reviewers || [])[0],
        },
      ],
    });
    if (!answer) return;
    try {
      setSelected(
        await testingApi.createFollowUpReviewSession(selected._id, {
          expected_revision: selected.revision,
          idempotency_key: crypto.randomUUID(),
          objective: answer.objective,
          moderator_id: answer.moderator_id,
          reviewer_ids: [answer.reviewer_id],
          scribe_id: null,
        }),
      );
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const terminalTransition = async (targetStatus) => {
    const title = targetStatus === "ARCHIVED" ? "Lưu trữ phiên rà soát" : "Hủy phiên rà soát";
    const answer = await ask({
      title,
      confirmLabel: title,
      fields: [{ name: "note", label: "Lý do", required: true, multiline: true }],
    });
    if (!answer) return;
    try {
      setSelected(
        await testingApi.transitionReviewSessionTerminal(selected._id, {
          expected_revision: selected.revision,
          target_status: targetStatus,
          note: answer.note,
        }),
      );
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <Panel
      title="Rà soát chính thức"
      actions={
        can("reviewsession.create") ? (
          <button className="apple-button" type="button" onClick={create}>
            Tạo phiên rà soát
          </button>
        ) : null
      }
    >
      {dialog}
      {error && (
        <div className="p-4">
          <ErrorState message={error} />
        </div>
      )}
      <DataTable
        items={sessions}
        empty="Chưa có phiên rà soát"
        columns={[
          { key: "review_type", label: "Loại" },
          {
            key: "status",
            label: "Trạng thái",
            render: (item) => <StatusPill value={item.status} />,
          },
          { key: "decision", label: "Quyết định" },
          {
            key: "action",
            label: "Thao tác",
            render: (item) => (
              <button
                className="secondary-button"
                type="button"
                onClick={async () => setSelected(await testingApi.getReviewSession(item._id))}
              >
                Mở
              </button>
            ),
          },
        ]}
      />
      {selected && (
        <div className="space-y-4 border-t border-border p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-semibold">{selected.objective}</p>
              <p className="text-sm text-ink-muted">
                Checklist {selected.checklist_version_id || selected.checklist_version}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {selected.status === "PLANNED" && can("reviewsession.update") && (
                <>
                  <button className="secondary-button" type="button" onClick={assignParticipants}>
                    Phân công
                  </button>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => transition(testingApi.startReviewSession)}
                  >
                    Bắt đầu
                  </button>
                  {can("reviewsession.complete") && (
                    <button
                      className="danger-button"
                      type="button"
                      onClick={() => terminalTransition("CANCELLED")}
                    >
                      Hủy phiên
                    </button>
                  )}
                </>
              )}
              {selected.status === "IN_PROGRESS" && can("reviewsession.finding.manage") && (
                <button className="secondary-button" type="button" onClick={addFinding}>
                  Thêm phát hiện
                </button>
              )}
              {selected.status === "IN_PROGRESS" && can("reviewsession.complete") && (
                <button
                  className="apple-button"
                  type="button"
                  onClick={() => transition(testingApi.recordReviewSessionDecision, "decision")}
                >
                  Ghi quyết định
                </button>
              )}
              {selected.status === "DECISION_PENDING" && can("reviewsession.complete") && (
                <button
                  className="apple-button"
                  type="button"
                  onClick={() => transition(testingApi.completeReviewSession, "complete")}
                >
                  Hoàn tất
                </button>
              )}
              {selected.status === "COMPLETED" && can("reviewsession.create") && (
                <button className="secondary-button" type="button" onClick={createFollowUp}>
                  Tạo phiên tiếp theo
                </button>
              )}
              {selected.status === "COMPLETED" && can("reviewsession.complete") && (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => terminalTransition("ARCHIVED")}
                >
                  Lưu trữ
                </button>
              )}
              <button
                className="secondary-button"
                type="button"
                onClick={() =>
                  testingApi
                    .exportReviewSession(selected._id)
                    .catch((reason) => setError(messageOf(reason)))
                }
              >
                Xuất CSV
              </button>
            </div>
          </div>
          {selected.metrics && (
            <div className="grid gap-3 text-sm sm:grid-cols-4">
              <p>
                <span className="field-label">Tổng phát hiện</span>
                <br />
                {selected.metrics.finding_count || 0}
              </p>
              <p>
                <span className="field-label">Phát hiện nghiêm trọng</span>
                <br />
                {selected.metrics.major_count || 0}
              </p>
              <p>
                <span className="field-label">Chưa xử lý</span>
                <br />
                {selected.metrics.open_count || 0}
              </p>
              <p>
                <span className="field-label">Đã xác minh</span>
                <br />
                {selected.metrics.verified_count || 0}
              </p>
            </div>
          )}
          <ReviewChecklist items={selected.checklist} />
          <ReviewFindingsTable
            findings={selected.findings}
            canManage={can("reviewsession.finding.manage")}
            onAssign={assignFinding}
            onResolve={resolveFinding}
            onVerify={verifyFinding}
          />
        </div>
      )}
    </Panel>
  );
}
