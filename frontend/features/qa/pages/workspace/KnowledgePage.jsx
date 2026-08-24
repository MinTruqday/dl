"use client";
import { useState } from "react";
import DataTable from "../../components/DataTable";
import { ErrorState, Panel, ProjectCrumb, QaPage, StatusPill } from "../../components/QaUi";
import { qaApi } from "../../services/qa.service";
import { messageOf } from "../../lib/qa";

export default function KnowledgePage({ project }) {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  return (
    <QaPage
      eyebrow={`${project.key} · Knowledge`}
      title="Project scoped retrieval"
      description="Mọi kết quả bị giới hạn theo project và hiển thị nguồn phiên bản authority cùng điểm truy hồi"
      actions={<ProjectCrumb projectId={project._id} />}
    >
      {error && <ErrorState message={error} />}
      <Panel title="Tìm trong Requirement Test Case Defect và Test Plan">
        <form
          className="flex gap-3 p-5"
          onSubmit={async (event) => {
            event.preventDefault();
            try {
              setResult(
                await qaApi.searchKnowledge(project._id, { query, artifact_types: [], limit: 50 }),
              );
            } catch (reason) {
              setError(messageOf(reason));
            }
          }}
        >
          <input
            aria-label="Tìm tri thức dự án"
            className="apple-input flex-1"
            required
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Nhập hành vi quy tắc lỗi hoặc Test Case cần tìm"
          />
          <button className="apple-button" type="submit">
            Tìm kiếm
          </button>
        </form>
      </Panel>
      {result && (
        <Panel title={`Kết quả theo ${result.retrieval_version}`}>
          <DataTable
            items={result.items}
            empty="Không tìm thấy artifact phù hợp"
            columns={[
              { key: "artifact_type", label: "Loại" },
              { key: "title", label: "Tên" },
              {
                key: "status",
                label: "Trạng thái",
                render: (item) => <StatusPill value={item.status} />,
              },
              { key: "authority", label: "Authority" },
              { key: "score", label: "Điểm" },
              {
                key: "text",
                label: "Evidence",
                render: (item) => <span className="line-clamp-3 max-w-xl">{item.text}</span>,
              },
            ]}
          />
        </Panel>
      )}
    </QaPage>
  );
}
