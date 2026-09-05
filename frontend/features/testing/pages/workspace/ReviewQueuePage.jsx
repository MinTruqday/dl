"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import ProposalDiffPanel from "../../components/ProposalDiffPanel";
import {
  ErrorState,
  Panel,
  ProjectCrumb,
  QaPage,
  StatusPill,
  useQaActionDialog,
} from "../../components/TestingUi";
import { messageOf, valueLabel } from "../../lib/testing";
import { testingApi } from "../../services/testing.service";

export default function ReviewQueuePage({ project }) {
  const { ask, dialog } = useQaActionDialog();
  const [items, setItems] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [filters, setFilters] = useState({
    status: "PENDING",
    proposal_type: "",
    target_artifact_id: "",
    sort: "-created_at",
  });
  const [error, setError] = useState("");
  const can = (permission) => project.current_permissions?.includes(permission);
  const load = useCallback(async () => {
    try {
      setItems(await testingApi.listProposals(project._id, filters));
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [filters, project._id]);
  useEffect(() => {
    void load();
  }, [load]);
  const decide = async (item, action) => {
    const fields = [
      {
        name: "note",
        label: action === "reject" ? "Lý do từ chối" : "Ghi chú rà soát",
        required: true,
        multiline: true,
        autoFocus: true,
      },
    ];
    if (action === "edit") {
      fields.push({
        name: "patch",
        label: "Nội dung đề xuất sau chỉnh sửa dạng JSON",
        initialValue: JSON.stringify(item.patch, null, 2),
        required: true,
        multiline: true,
      });
    }
    const answer = await ask({
      title: action === "reject" ? "Từ chối đề xuất" : "Duyệt đề xuất",
      description: `${item.test_case_key || item.target_artifact_id || item._id} dựa trên ${item.base_version_id || "đề xuất tạo mới"}`,
      confirmLabel: action === "reject" ? "Từ chối" : "Duyệt",
      danger: action === "reject",
      fields,
    });
    if (!answer) return;
    try {
      if (action === "reject") {
        await testingApi.rejectProposal(item._id, {
          expected_revision: item.revision,
          review_note: answer.note,
        });
      } else {
        let patch = null;
        if (action === "edit") {
          try {
            patch = JSON.parse(answer.patch);
          } catch {
            setError("Nội dung chỉnh sửa phải là JSON hợp lệ");
            return;
          }
        }
        await testingApi.acceptProposal(
          item._id,
          { expected_revision: item.revision, review_note: answer.note, patch },
          action === "edit",
        );
      }
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const regenerate = async (item) => {
    const answer = await ask({
      title: "Yêu cầu tạo lại đề xuất",
      description: item.test_case_key || item.target_artifact_id || item._id,
      confirmLabel: "Tạo lại",
      fields: [
        {
          name: "instruction",
          label: "Hướng điều chỉnh",
          required: true,
          multiline: true,
          autoFocus: true,
        },
      ],
    });
    if (!answer) return;
    try {
      await testingApi.regenerateProposal(item._id, {
        expected_revision: item.revision,
        instruction: answer.instruction,
      });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <QaPage title="Rà soát đề xuất AI" actions={<ProjectCrumb projectId={project._id} />}>
      {error && <ErrorState message={error} />}
      <Panel
        title="Đề xuất đang chờ"
        actions={
          can("proposal.approve") && selectedIds.length > 0 ? (
            <button
              className="apple-button"
              type="button"
              onClick={async () => {
                const answer = await ask({
                  title: "Duyệt hàng loạt theo chính sách",
                  description: `${selectedIds.length} mục đã chọn mỗi mục vẫn phải đạt ngưỡng cấu hình`,
                  confirmLabel: "Duyệt các mục an toàn",
                  fields: [
                    {
                      name: "note",
                      label: "Ghi chú",
                      required: true,
                      multiline: true,
                      autoFocus: true,
                    },
                  ],
                });
                if (!answer) return;
                try {
                  await testingApi.bulkApproveProposals(project._id, {
                    proposal_ids: selectedIds,
                    review_note: answer.note,
                    idempotency_key: crypto.randomUUID(),
                  });
                  setSelectedIds([]);
                  await load();
                } catch (reason) {
                  setError(messageOf(reason));
                }
              }}
            >
              Duyệt hàng loạt theo chính sách
            </button>
          ) : null
        }
      >
        <details className="border-b border-border p-4">
          <summary className="cursor-pointer text-sm font-medium text-ink">Bộ lọc</summary>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <select
              aria-label="Lọc trạng thái đề xuất"
              className="apple-input"
              value={filters.status}
              onChange={(event) => setFilters({ ...filters, status: event.target.value })}
            >
              <option value="">Mọi trạng thái</option>
              {["PENDING", "APPROVED", "REJECTED", "APPLY_PARTIAL", "EXPIRED"].map((value) => (
                <option value={value} key={value}>
                  {valueLabel(value)}
                </option>
              ))}
            </select>
            <select
              aria-label="Lọc loại đề xuất"
              className="apple-input"
              value={filters.proposal_type}
              onChange={(event) => setFilters({ ...filters, proposal_type: event.target.value })}
            >
              <option value="">Mọi loại</option>
              {["UPDATE_TEST_CASE", "CREATE_TEST_CASE", "OBSOLETE_TEST_CASE"].map((value) => (
                <option value={value} key={value}>
                  {valueLabel(value)}
                </option>
              ))}
            </select>
            <input
              aria-label="Lọc đối tượng đề xuất"
              className="apple-input"
              placeholder="Mã đối tượng"
              value={filters.target_artifact_id}
              onChange={(event) =>
                setFilters({ ...filters, target_artifact_id: event.target.value })
              }
            />
            <select
              aria-label="Sắp xếp đề xuất"
              className="apple-input"
              value={filters.sort}
              onChange={(event) => setFilters({ ...filters, sort: event.target.value })}
            >
              <option value="-created_at">Mới nhất</option>
              <option value="created_at">Cũ nhất</option>
              <option value="-confidence">Tin cậy cao</option>
            </select>
          </div>
        </details>
        <DataTable
          items={items}
          selectedIds={can("proposal.approve") ? selectedIds : undefined}
          onSelectionChange={can("proposal.approve") ? setSelectedIds : undefined}
          selectionLabel="Chọn đề xuất"
          empty="Không có đề xuất đang chờ"
          columns={[
            { key: "proposal_type", label: "Loại" },
            { key: "test_case_key", label: "Đối tượng" },
            { key: "base_version_id", label: "Phiên bản gốc" },
            { key: "impact_analysis_id", label: "Phân tích thay đổi" },
            {
              key: "confidence",
              label: "Mức tin cậy hỗ trợ",
              render: (item) => `${item.confidence ?? 0} điểm cần người duyệt`,
            },
            { key: "reason", label: "Lập luận" },
            {
              key: "evidence",
              label: "Bằng chứng",
              render: (item) => (
                <pre className="max-w-sm whitespace-pre-wrap text-[11px]">
                  {JSON.stringify(item.evidence || [], null, 2)}
                </pre>
              ),
            },
            {
              key: "diff",
              label: "So sánh",
              render: (item) => <ProposalDiffPanel proposal={item} />,
            },
            { key: "model_version", label: "Mô hình" },
            {
              key: "status",
              label: "Trạng thái",
              render: (item) => <StatusPill value={item.status} />,
            },
            {
              key: "actions",
              label: "Quyết định",
              render: (item) =>
                can("proposal.approve") || can("proposal.reject") || can("ai.create_proposal") ? (
                  <span className="flex flex-wrap gap-2">
                    {can("proposal.approve") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => decide(item, "accept")}
                      >
                        Duyệt
                      </button>
                    )}
                    {can("proposal.approve") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => decide(item, "edit")}
                      >
                        Sửa rồi duyệt
                      </button>
                    )}
                    {can("proposal.reject") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => decide(item, "reject")}
                      >
                        Từ chối
                      </button>
                    )}
                    {can("ai.create_proposal") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => regenerate(item)}
                      >
                        Tạo lại
                      </button>
                    )}
                  </span>
                ) : null,
            },
          ]}
        />
      </Panel>
      {dialog}
    </QaPage>
  );
}
