"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import {
  DegradedBanner,
  ErrorState,
  Panel,
  ProjectCrumb,
  QaPage,
  StatusPill,
  useQaActionDialog,
} from "../../components/TestingUi";
import { testingApi } from "../../services/testing.service";
import { messageOf } from "../../lib/testing";

export default function KnowledgePage({ project }) {
  const { ask, dialog } = useQaActionDialog();
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [sources, setSources] = useState([]);
  const [error, setError] = useState("");
  const canAsk = project.current_permissions?.includes("ai.ask_project");
  const canManage = project.current_permissions?.includes("knowledge.manage");
  const loadSources = useCallback(async () => {
    try {
      setSources(await testingApi.listKnowledgeSources(project._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [project._id]);
  useEffect(() => {
    loadSources();
  }, [loadSources]);
  return (
    <QaPage
      title="Tìm kiếm trong tri thức dự án"
      actions={<ProjectCrumb projectId={project._id} />}
    >
      {error && <ErrorState message={error} />}
      <DegradedBanner mode={result?.degraded_mode} />
      {canAsk && (
        <Panel title="Hỏi đáp theo tri thức dự án">
          <form
            className="space-y-3 p-5"
            onSubmit={async (event) => {
              event.preventDefault();
              setError("");
              try {
                setAnswer(
                  await testingApi.askProject(project._id, {
                    question,
                    artifact_types: [],
                    evidence_limit: 20,
                  }),
                );
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          >
            <textarea
              aria-label="Câu hỏi về dự án"
              className="apple-input min-h-28 w-full"
              required
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Nhập câu hỏi cần trả lời từ yêu cầu tài liệu ca kiểm thử và lỗi của dự án"
            />
            <button className="apple-button" type="submit">
              Trả lời
            </button>
          </form>
          {answer && (
            <div className="space-y-4 border-t border-line p-5">
              <p className="whitespace-pre-wrap text-sm text-ink">{answer.answer}</p>
              <p className="text-xs text-ink-muted">Độ tin cậy {answer.confidence}</p>
              <DataTable
                items={answer.evidence || []}
                empty="Không có bằng chứng"
                columns={[
                  { key: "artifact_type", label: "Loại" },
                  { key: "title", label: "Nguồn" },
                  { key: "authority", label: "Thẩm quyền" },
                  { key: "score", label: "Điểm" },
                ]}
              />
            </div>
          )}
        </Panel>
      )}
      <Panel title="Tìm trong yêu cầu ca kiểm thử lỗi và kế hoạch kiểm thử">
        <form
          className="flex gap-3 p-5"
          onSubmit={async (event) => {
            event.preventDefault();
            try {
              setResult(
                await testingApi.searchKnowledge(project._id, {
                  query,
                  artifact_types: [],
                  limit: 50,
                }),
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
            placeholder="Nhập hành vi quy tắc lỗi hoặc ca kiểm thử cần tìm"
          />
          <button className="apple-button" type="submit">
            Tìm kiếm
          </button>
        </form>
      </Panel>
      {result && (
        <Panel title={`Kết quả từ ${result.retrieval_version || "nguồn tri thức"}`}>
          <DataTable
            items={result.items}
            empty="Không tìm thấy dữ liệu phù hợp"
            columns={[
              { key: "artifact_type", label: "Loại" },
              { key: "title", label: "Tên" },
              {
                key: "status",
                label: "Trạng thái",
                render: (item) => <StatusPill value={item.status} />,
              },
              { key: "authority", label: "Mức thẩm quyền" },
              { key: "score", label: "Điểm" },
              {
                key: "text",
                label: "Bằng chứng",
                render: (item) => <span className="line-clamp-3 max-w-xl">{item.text}</span>,
              },
            ]}
          />
        </Panel>
      )}
      <Panel title="Nguồn tri thức giáo viên và chương trình học">
        {canManage && (
          <form
            className="grid gap-3 border-b border-border p-5 md:grid-cols-2"
            onSubmit={async (event) => {
              event.preventDefault();
              const form = event.currentTarget;
              const values = new FormData(form);
              try {
                await testingApi.createKnowledgeSource(project._id, {
                  title: values.get("title"),
                  content: values.get("content"),
                  source_type: values.get("source_type"),
                  authority: values.get("authority"),
                  source_url: values.get("source_url") || null,
                  teacher_id: values.get("teacher_id") || null,
                  subject: values.get("subject") || null,
                  grade: values.get("grade") || null,
                  tags: String(values.get("tags") || "")
                    .split(",")
                    .map((value) => value.trim())
                    .filter(Boolean),
                });
                form.reset();
                await loadSources();
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          >
            <label className="field-label">
              Tiêu đề nguồn
              <input className="apple-input mt-2" name="title" required minLength={2} />
            </label>
            <label className="field-label">
              Loại nguồn
              <select
                className="apple-input mt-2"
                name="source_type"
                defaultValue="teacher_material"
              >
                <option value="teacher_material">Tài liệu giáo viên</option>
                <option value="official_textbook">Sách giáo khoa chính thức</option>
                <option value="curriculum">Chương trình học</option>
                <option value="reference">Tài liệu tham khảo</option>
                <option value="other">Nguồn khác</option>
              </select>
            </label>
            <label className="field-label">
              Mức thẩm quyền
              <select className="apple-input mt-2" name="authority" defaultValue="teacher">
                <option value="teacher">Giáo viên</option>
                <option value="official">Chính thức</option>
                <option value="supplemental">Bổ trợ</option>
                <option value="reference">Tham khảo</option>
              </select>
            </label>
            <label className="field-label">
              Mã giáo viên
              <input className="apple-input mt-2" name="teacher_id" />
            </label>
            <label className="field-label">
              Môn học
              <input className="apple-input mt-2" name="subject" />
            </label>
            <label className="field-label">
              Khối lớp
              <input className="apple-input mt-2" name="grade" />
            </label>
            <label className="field-label">
              Liên kết nguồn
              <input className="apple-input mt-2" name="source_url" type="url" />
            </label>
            <label className="field-label">
              Nhãn phân cách bằng dấu phẩy
              <input className="apple-input mt-2" name="tags" />
            </label>
            <label className="field-label md:col-span-2">
              Nội dung tài liệu
              <textarea className="apple-input mt-2 min-h-36" name="content" required />
            </label>
            <button className="apple-button w-fit" type="submit">
              Thêm nguồn tri thức
            </button>
          </form>
        )}
        <DataTable
          items={sources}
          empty="Chưa có nguồn tri thức"
          columns={[
            { key: "title", label: "Nguồn" },
            { key: "source_type", label: "Loại" },
            { key: "authority", label: "Thẩm quyền" },
            {
              key: "subject",
              label: "Môn và khối",
              render: (item) =>
                [item.subject, item.grade].filter(Boolean).join(" · ") || "Chưa khai báo",
            },
            { key: "index_status", label: "Lập chỉ mục" },
            ...(canManage
              ? [
                  {
                    key: "actions",
                    label: "Thao tác",
                    render: (item) => (
                      <span className="flex flex-wrap gap-2">
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={async () => {
                            try {
                              await testingApi.reindexKnowledgeSource(item._id);
                              await loadSources();
                            } catch (reason) {
                              setError(messageOf(reason));
                            }
                          }}
                        >
                          Lập chỉ mục lại
                        </button>
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={async () => {
                            const answer = await ask({
                              title: "Lưu trữ nguồn tri thức",
                              description: item.title || item.filename,
                              confirmLabel: "Lưu trữ",
                              danger: true,
                              fields: [
                                {
                                  name: "reason",
                                  label: "Lý do",
                                  required: true,
                                  multiline: true,
                                },
                              ],
                            });
                            if (!answer) return;
                            try {
                              await testingApi.archiveKnowledgeSource(item._id, {
                                expected_revision: item.revision,
                                reason: answer.reason,
                              });
                              await loadSources();
                            } catch (reason) {
                              setError(messageOf(reason));
                            }
                          }}
                        >
                          Lưu trữ
                        </button>
                      </span>
                    ),
                  },
                ]
              : []),
          ]}
        />
      </Panel>
      {dialog}
    </QaPage>
  );
}
