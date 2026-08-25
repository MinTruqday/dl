"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import { ErrorState, Panel, ProjectCrumb, QaPage, StatusPill } from "../../components/QaUi";
import { qaApi } from "../../services/qa.service";
import { messageOf } from "../../lib/qa";

export default function ChangesPage({ project }) {
  const [sets, setSets] = useState([]);
  const [proposals, setProposals] = useState([]);
  const [selected, setSelected] = useState(null);
  const [impact, setImpact] = useState(null);
  const [regression, setRegression] = useState(null);
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
  const analyze = async (item) => {
    try {
      setSelected(await qaApi.getChangeSet(item._id));
      const result = await qaApi.analyzeImpact(item._id);
      setImpact(result);
      await qaApi.createProposals(result._id);
      setRegression(await qaApi.regression(item._id));
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const decide = async (item, action) => {
    const note =
      window.prompt(
        action === "reject" ? "Lý do từ chối" : "Ghi chú rà soát",
        action === "reject" ? "Không phù hợp với ý định kiểm thử" : "Đã rà soát evidence",
      ) || "";
    try {
      if (action === "reject")
        await qaApi.rejectProposal(item._id, {
          expected_revision: item.revision,
          review_note: note,
        });
      else
        await qaApi.acceptProposal(
          item._id,
          {
            expected_revision: item.revision,
            review_note: note,
            patch: action === "edit" ? item.patch : null,
          },
          action === "edit",
        );
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
          onSelect={analyze}
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
          <Panel title="So sánh thay đổi">
            <DataTable
              items={(selected.changes || []).map((item, index) => ({ ...item, _id: index }))}
              empty="Không phát hiện thay đổi ngữ nghĩa"
              columns={[
                { key: "type", label: "Loại" },
                { key: "field", label: "Trường" },
                { key: "before", label: "Trước", render: (item) => JSON.stringify(item.before) },
                { key: "after", label: "Sau", render: (item) => JSON.stringify(item.after) },
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
          </Panel>
        </div>
      )}
      {impact && (
        <Panel title="Phân tích ảnh hưởng">
          <DataTable
            items={impact.items || []}
            columns={[
              { key: "test_case_key", label: "Ca kiểm thử" },
              {
                key: "classification",
                label: "Phân loại",
                render: (item) => <StatusPill value={item.classification} />,
              },
              { key: "confidence", label: "Confidence" },
              { key: "reasons", label: "Bằng chứng", render: (item) => item.reasons?.join(", ") },
            ]}
          />
        </Panel>
      )}
      <Panel title="Đề xuất bảo trì chờ duyệt">
        <DataTable
          items={proposals}
          empty="Không có đề xuất chờ duyệt"
          columns={[
            { key: "test_case_key", label: "Ca kiểm thử" },
            { key: "proposal_type", label: "Loại đề xuất" },
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
                </span>
              ),
            },
          ]}
        />
      </Panel>
    </QaPage>
  );
}
