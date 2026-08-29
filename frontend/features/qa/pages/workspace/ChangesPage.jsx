"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import ProposalDiffPanel from "../../components/ProposalDiffPanel";
import {
  DegradedBanner,
  ErrorState,
  Panel,
  ProjectCrumb,
  QaPage,
  StatusPill,
  useQaActionDialog,
} from "../../components/QaUi";
import { qaApi } from "../../services/qa.service";
import { messageOf } from "../../lib/qa";

export default function ChangesPage({ project }) {
  const { ask, dialog } = useQaActionDialog();
  const [sets, setSets] = useState([]);
  const [proposals, setProposals] = useState([]);
  const [selectedProposalIds, setSelectedProposalIds] = useState([]);
  const [selected, setSelected] = useState(null);
  const [impact, setImpact] = useState(null);
  const [regression, setRegression] = useState(null);
  const [overrides, setOverrides] = useState({});
  const [changeFacts, setChangeFacts] = useState([]);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    try {
      const [changeValues, proposalValues] = await Promise.all([
        qaApi.listChangeSets(project._id),
        qaApi.listProposals(project._id),
      ]);
      setSets(changeValues);
      setProposals(proposalValues);
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [project._id]);
  useEffect(() => {
    void load();
  }, [load]);
  const openChangeSet = async (item) => {
    try {
      const value = await qaApi.getChangeSet(item._id);
      setSelected(value);
      setChangeFacts(value.changes || []);
      setImpact(null);
      setRegression(null);
      if (value.status === "ANALYZED") {
        const result = await qaApi.analyzeImpact(item._id);
        setImpact(result);
        setOverrides({});
        if (result.status === "REVIEWED") {
          setRegression(await qaApi.regression(item._id));
        }
      }
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const analyze = async () => {
    try {
      const result = await qaApi.analyzeImpact(selected._id);
      setSelected(await qaApi.getChangeSet(selected._id));
      setImpact(result);
      setOverrides({});
      setRegression(result.status === "REVIEWED" ? await qaApi.regression(selected._id) : null);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const decide = async (item, action) => {
    const fields = [
      {
        name: "note",
        label: action === "reject" ? "Lý do từ chối" : "Ghi chú rà soát",
        initialValue:
          action === "reject" ? "Không phù hợp với ý định kiểm thử" : "Đã rà soát bằng chứng",
        required: true,
        multiline: true,
        autoFocus: true,
      },
    ];
    if (action === "edit")
      fields.push({
        name: "patch",
        label: "Patch JSON sau khi chỉnh sửa",
        initialValue: JSON.stringify(item.patch, null, 2),
        required: true,
        multiline: true,
      });
    const answer = await ask({
      title: action === "reject" ? "Từ chối đề xuất bảo trì" : "Chấp nhận đề xuất bảo trì",
      description: `${item.test_case_key || item.test_case_id} tạo phiên bản mới khi được chấp nhận`,
      confirmLabel: action === "reject" ? "Từ chối" : "Chấp nhận",
      danger: action === "reject",
      fields,
    });
    if (!answer) return;
    try {
      if (action === "reject")
        await qaApi.rejectProposal(item._id, {
          expected_revision: item.revision,
          review_note: answer.note,
        });
      else {
        let patch = null;
        if (action === "edit") {
          try {
            patch = JSON.parse(answer.patch);
          } catch {
            setError("Patch phải là JSON hợp lệ");
            return;
          }
        }
        await qaApi.acceptProposal(
          item._id,
          {
            expected_revision: item.revision,
            review_note: answer.note,
            patch,
          },
          action === "edit",
        );
      }
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const reviewImpact = async () => {
    const answer = await ask({
      title: "Duyệt phân tích ảnh hưởng",
      description: `${impact.affected_test_cases?.length || 0} ca kiểm thử sẽ được chốt phân loại`,
      confirmLabel: "Duyệt phân tích",
      fields: [
        {
          name: "note",
          label: "Ghi chú duyệt",
          initialValue: "Đã kiểm tra bằng chứng và phân loại",
          required: true,
          multiline: true,
          autoFocus: true,
        },
      ],
    });
    if (!answer) return;
    try {
      const items = impact.affected_test_cases || [];
      const payload = items
        .filter((item) => overrides[item.test_case_version_id])
        .map((item) => ({
          test_case_version_id: item.test_case_version_id,
          classification: overrides[item.test_case_version_id],
          reason: "Người rà soát điều chỉnh từ giao diện",
        }));
      const reviewed = await qaApi.reviewImpact(impact._id, {
        expected_revision: impact.revision,
        overrides: payload,
        review_note: answer.note,
      });
      setImpact(reviewed);
      await qaApi.createProposals(reviewed._id);
      setRegression(await qaApi.regression(selected._id));
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <QaPage
      title="Ảnh hưởng thay đổi và bảo trì"
      description="Hệ thống phân loại thay đổi, sau đó người dùng duyệt từng đề xuất trước khi tạo phiên bản ca kiểm thử mới"
      actions={<ProjectCrumb projectId={project._id} />}
    >
      {error && <ErrorState message={error} />}
      <Panel title="Change Set">
        <DataTable
          onSelect={openChangeSet}
          items={sets}
          empty="Tạo phiên bản yêu cầu mới rồi tạo bộ thay đổi để bắt đầu"
          columns={[
            { key: "_id", label: "Mã" },
            { key: "requirement_id", label: "Yêu cầu" },
            {
              key: "status",
              label: "Trạng thái",
              render: (item) => <StatusPill value={item.status} />,
            },
            { key: "summary", label: "Tóm tắt" },
          ]}
        />
      </Panel>
      {selected && (
        <div className="grid gap-5 xl:grid-cols-2">
          <Panel
            title="So sánh thay đổi"
            actions={
              selected.status === "READY" ? (
                <button
                  className="apple-button"
                  type="button"
                  onClick={async () => {
                    try {
                      const value = await qaApi.reviewChangeSet(selected._id, {
                        expected_revision: selected.revision,
                        changes: changeFacts,
                        review_note: "Đã xác nhận ChangeFact trên giao diện",
                      });
                      setSelected(value);
                      setChangeFacts(value.changes);
                      await load();
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                >
                  Xác nhận ChangeFact
                </button>
              ) : selected.status === "REVIEWED" ? (
                <button className="apple-button" type="button" onClick={analyze}>
                  Phân tích ảnh hưởng
                </button>
              ) : null
            }
          >
            <DataTable
              items={changeFacts.map((item, index) => ({ ...item, _id: index, factIndex: index }))}
              empty="Không phát hiện thay đổi ngữ nghĩa"
              columns={[
                {
                  key: "type",
                  label: "Loại",
                  render: (item) =>
                    selected.status === "READY" ? (
                      <select
                        aria-label={`Loại ChangeFact ${item.factIndex + 1}`}
                        className="apple-input min-w-48"
                        value={item.type}
                        onChange={(event) =>
                          setChangeFacts((values) =>
                            values.map((value, index) =>
                              index === item.factIndex
                                ? { ...value, type: event.target.value }
                                : value,
                            ),
                          )
                        }
                      >
                        {[
                          "TEXT_ONLY",
                          "MODIFIED_INPUT",
                          "MODIFIED_BOUNDARY",
                          "MODIFIED_PERMISSION",
                          "MODIFIED_ERROR",
                          "ADDED_BEHAVIOR",
                          "REMOVED_BEHAVIOR",
                        ].map((value) => (
                          <option key={value} value={value}>{value}</option>
                        ))}
                      </select>
                    ) : (
                      item.type
                    ),
                },
                { key: "subject", label: "Đối tượng" },
                { key: "before", label: "Trước", render: (item) => JSON.stringify(item.before) },
                { key: "after", label: "Sau", render: (item) => JSON.stringify(item.after) },
                {
                  key: "wording_only",
                  label: "Chỉ đổi cách diễn đạt",
                  render: (item) => (
                    <input
                      aria-label={`Chỉ đổi cách diễn đạt ${item.factIndex + 1}`}
                      type="checkbox"
                      checked={item.wording_only || item.type === "TEXT_ONLY"}
                      disabled={selected.status !== "READY"}
                      onChange={(event) =>
                        setChangeFacts((values) =>
                          values.map((value, index) =>
                            index === item.factIndex
                              ? {
                                  ...value,
                                  wording_only: event.target.checked,
                                  type: event.target.checked ? "TEXT_ONLY" : value.type,
                                }
                              : value,
                          ),
                        )
                      }
                    />
                  ),
                },
              ]}
            />
          </Panel>
          <Panel title="Regression recommendation">
            <DataTable
              items={regression?.items || []}
              empty="Chưa có khuyến nghị"
              columns={[
                { key: "test_case_id", label: "Ca kiểm thử" },
                {
                  key: "level",
                  label: "Khuyến nghị",
                  render: (item) => <StatusPill value={item.level} />,
                },
                { key: "reasons", label: "Lý do", render: (item) => item.reasons?.join(", ") },
              ]}
            />
            {regression?.status === "PENDING_APPROVAL" && (
              <div className="border-t border-border p-5">
                <button
                  className="apple-button"
                  type="button"
                  onClick={async () => {
                    const answer = await ask({
                      title: "Phê duyệt phạm vi hồi quy",
                      description: "Các ca mức bắt buộc và nên chạy sẽ được đưa vào bộ kiểm thử",
                      confirmLabel: "Phê duyệt và tạo bộ",
                      fields: [
                        {
                          name: "note",
                          label: "Ghi chú phê duyệt",
                          initialValue: "Đã kiểm tra mức độ và bằng chứng",
                          required: true,
                          multiline: true,
                          autoFocus: true,
                        },
                      ],
                    });
                    if (!answer) return;
                    try {
                      const value = await qaApi.approveRegression(regression._id, {
                        expected_revision: regression.revision,
                        selected_test_case_version_ids: regression.items
                          .filter((item) => ["MUST_RUN", "SHOULD_RUN"].includes(item.level))
                          .map((item) => item.test_case_version_id),
                        review_note: answer.note,
                      });
                      setRegression(value.recommendation);
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                >
                  Phê duyệt và tạo bộ kiểm thử
                </button>
              </div>
            )}
          </Panel>
        </div>
      )}
      {impact && (
        <Panel
          title="Phân tích ảnh hưởng"
          actions={
            impact.status === "REVIEW_READY" ? (
              <button className="apple-button" type="button" onClick={reviewImpact}>
                Duyệt phân tích
              </button>
            ) : null
          }
        >
          <div className="p-5 pb-0">
            <DegradedBanner
              mode={impact.mode === "DEGRADED_AI" ? "DEGRADED_AI" : "NORMAL"}
              message="Mô hình AI không khả dụng nên hệ thống dùng ứng viên trực tiếp ngữ nghĩa và kỹ thuật có thể kiểm chứng"
            />
          </div>
          <DataTable
            items={impact.reviewed_affected_test_cases || impact.affected_test_cases || []}
            columns={[
              { key: "test_case_key", label: "Ca kiểm thử" },
              {
                key: "classification",
                label: "Phân loại",
                render: (item) =>
                  impact.status === "REVIEW_READY" ? (
                    <select
                      aria-label={`Phân loại ${item.test_case_key}`}
                      className="apple-input"
                      value={overrides[item.test_case_version_id] || item.classification}
                      onChange={(event) =>
                        setOverrides({
                          ...overrides,
                          [item.test_case_version_id]: event.target.value,
                        })
                      }
                    >
                      {["STILL_VALID", "POTENTIALLY_AFFECTED", "NEEDS_UPDATE", "OBSOLETE"].map(
                        (value) => (
                          <option key={value} value={value}>
                            {value}
                          </option>
                        ),
                      )}
                    </select>
                  ) : (
                    <StatusPill value={item.classification} />
                  ),
              },
              { key: "confidence", label: "Confidence" },
              { key: "reasons", label: "Bằng chứng", render: (item) => item.reasons?.join(", ") },
            ]}
          />
        </Panel>
      )}
      <Panel
        title="Đề xuất bảo trì chờ duyệt"
        actions={
          <button
            className="apple-button"
            disabled={!selectedProposalIds.length}
            type="button"
            onClick={async () => {
              const answer = await ask({
                title: "Duyệt hàng loạt đề xuất an toàn",
                description: `${selectedProposalIds.length} mục đã chọn sẽ vẫn được kiểm tra ngưỡng chính sách riêng lẻ`,
                confirmLabel: "Duyệt các mục đạt chính sách",
                fields: [{ name: "note", label: "Ghi chú duyệt", required: true, multiline: true, autoFocus: true }],
              });
              if (!answer) return;
              try {
                await qaApi.bulkApproveProposals(project._id, {
                  proposal_ids: selectedProposalIds,
                  review_note: answer.note,
                });
                setSelectedProposalIds([]);
                await load();
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          >
            Duyệt hàng loạt theo chính sách
          </button>
        }
      >
        <DataTable
          items={proposals}
          selectedIds={selectedProposalIds}
          onSelectionChange={setSelectedProposalIds}
          selectionLabel="Chọn đề xuất"
          empty="Không có đề xuất chờ duyệt"
          columns={[
            { key: "test_case_key", label: "Ca kiểm thử" },
            { key: "proposal_type", label: "Loại đề xuất" },
            { key: "base_version_id", label: "Phiên bản gốc" },
            {
              key: "patch",
              label: "Thay đổi đề xuất",
              render: (item) => <ProposalDiffPanel proposal={item} />,
            },
            { key: "reason", label: "Lý do" },
            {
              key: "confidence",
              label: "Mức tin cậy hỗ trợ",
              render: (item) => `${item.confidence ?? 0} điểm cần người duyệt`,
            },
            {
              key: "status",
              label: "Trạng thái",
              render: (item) => <StatusPill value={item.status} />,
            },
            {
              key: "decision",
              label: "Quyết định HITL",
              render: (item) => (
                <span className="flex flex-wrap gap-2">
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => decide(item, "accept")}
                  >
                    Chấp nhận
                  </button>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => decide(item, "edit")}
                  >
                    Sửa rồi nhận
                  </button>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => decide(item, "reject")}
                  >
                    Từ chối
                  </button>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={async () => {
                      const answer = await ask({
                        title: "Yêu cầu tạo lại đề xuất",
                        description: item.test_case_key || item.target_artifact_id || item._id,
                        confirmLabel: "Tạo lại",
                        fields: [{ name: "instruction", label: "Hướng điều chỉnh", required: true, multiline: true, autoFocus: true }],
                      });
                      if (!answer) return;
                      try {
                        await qaApi.regenerateProposal(item._id, {
                          expected_revision: item.revision,
                          instruction: answer.instruction,
                        });
                        await load();
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    Tạo lại
                  </button>
                </span>
              ),
            },
          ]}
        />
      </Panel>
      {dialog}
    </QaPage>
  );
}
