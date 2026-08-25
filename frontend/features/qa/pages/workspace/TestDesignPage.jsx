"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import { ErrorState, Panel, ProjectCrumb, QaPage, StatusPill } from "../../components/QaUi";
import { qaApi } from "../../services/qa.service";
import { emptyDoc, messageOf, textDoc, valueLabel } from "../../lib/qa";
import QaDocumentEditor from "../../editor/QaDocumentEditor";

export default function TestDesignPage({ project }) {
  const [requirements, setRequirements] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [drafts, setDrafts] = useState([]);
  const [tests, setTests] = useState([]);
  const [duplicates, setDuplicates] = useState([]);
  const [operations, setOperations] = useState([]);
  const [testImport, setTestImport] = useState(null);
  const [apiImport, setApiImport] = useState({
    filename: "openapi.json",
    format: "openapi",
    content: "",
  });
  const [selectedRequirement, setSelectedRequirement] = useState("");
  const [form, setForm] = useState({
    title: "",
    type: "happy_path",
    priority: "medium",
    risk: "medium",
    action: emptyDoc(),
    expected: emptyDoc(),
  });
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    try {
      const [requirementValues, scenarioValues, draftValues, testValues, operationValues] =
        await Promise.all([
          qaApi.listRequirements(project._id),
          qaApi.listScenarios(project._id),
          qaApi.listTestDrafts(project._id),
          qaApi.listTestCases(project._id),
          qaApi.listApiOperations(project._id),
        ]);
      setRequirements(requirementValues);
      setScenarios(scenarioValues);
      setDrafts(draftValues);
      setTests(testValues);
      setOperations(operationValues);
      setSelectedRequirement(
        (current) => current || requirementValues[0]?.current_version_id || "",
      );
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [project._id]);
  useEffect(() => {
    void load();
  }, [load]);
  const create = async (event) => {
    event.preventDefault();
    try {
      await qaApi.createTestDraft(project._id, {
        title: form.title,
        type: form.type,
        priority: form.priority,
        risk: form.risk,
        preconditions_doc: textDoc("Hệ thống sẵn sàng"),
        steps: [
          {
            id: crypto.randomUUID(),
            order: 1,
            action_doc: form.action,
            test_data: {},
            expected_doc: form.expected,
          },
        ],
        test_data: {},
        expected_result_doc: form.expected,
        postconditions_doc: textDoc("Dữ liệu kiểm thử được kiểm soát"),
        tags: [],
        automation_status: "manual",
        requirement_version_ids: selectedRequirement ? [selectedRequirement] : [],
        acceptance_criterion_ids: [],
        origin: "manual",
        source_evidence: [],
      });
      setForm({
        title: "",
        type: "happy_path",
        priority: "medium",
        risk: "medium",
        action: emptyDoc(),
        expected: emptyDoc(),
      });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const generate = async () => {
    if (!selectedRequirement) return setError("Cần chọn yêu cầu trước khi tạo ca kiểm thử");
    try {
      await qaApi.generateTestCases(selectedRequirement, {
        categories: ["happy_path", "negative", "boundary", "validation"],
        count_per_category: 1,
        instruction: "Tạo theo phiên bản chuẩn và tiêu chí chấp nhận",
      });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const freeze = async (draft) => {
    if (!window.confirm(`Phê duyệt ${draft.test_case_key} thành phiên bản bất biến`)) return;
    try {
      await qaApi.freezeTestDraft(draft._id, draft.revision, "Phê duyệt sau rà soát của con người");
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <QaPage
      title="Kịch bản và ca kiểm thử"
      description="AI chỉ tạo bản nháp có bằng chứng, mọi ca kiểm thử đều phải qua rà soát và phê duyệt của người dùng"
      actions={<ProjectCrumb projectId={project._id} />}
    >
      {error && <ErrorState message={error} />}
      <Panel
        title="Tạo bằng AI"
        description="Kết quả chỉ là bản nháp và không tự động trở thành phiên bản hoạt động"
      >
        <div className="flex flex-wrap gap-3 p-5">
          <select
            aria-label="Yêu cầu nguồn"
            className="apple-input min-w-72"
            value={selectedRequirement}
            onChange={(event) => setSelectedRequirement(event.target.value)}
          >
            <option value="">Chọn yêu cầu</option>
            {requirements.map((item) => (
              <option key={item._id} value={item.current_version_id}>
                {item.requirement_key} {item.current_version?.title}
              </option>
            ))}
          </select>
          <button className="apple-button" type="button" onClick={generate}>
            Tạo 4 nhóm ca kiểm thử
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={async () => {
              if (!selectedRequirement) return;
              try {
                await qaApi.generateScenarios(selectedRequirement, {
                  categories: ["happy_path", "negative", "boundary", "validation"],
                  count_per_category: 1,
                });
                await load();
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          >
            Tạo kịch bản
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={async () => {
              try {
                setDuplicates(await qaApi.findDuplicates(project._id));
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          >
            Tìm ca kiểm thử trùng lặp
          </button>
        </div>
      </Panel>
      <div className="grid gap-5 xl:grid-cols-2">
        <Panel title="Bản nháp ca kiểm thử">
          <DataTable
            items={drafts}
            empty="Chưa có bản nháp"
            columns={[
              { key: "test_case_key", label: "Mã" },
              { key: "title", label: "Tên" },
              { key: "type", label: "Loại" },
              {
                key: "status",
                label: "Trạng thái",
                render: (item) => <StatusPill value={item.status} />,
              },
              {
                key: "action",
                label: "Duyệt",
                render: (item) =>
                  item.status === "DRAFT" ? (
                    <button className="secondary-button" type="button" onClick={() => freeze(item)}>
                      Lint và phê duyệt
                    </button>
                  ) : (
                    ""
                  ),
              },
            ]}
          />
        </Panel>
        <Panel title="Phiên bản ca kiểm thử">
          <DataTable
            items={tests}
            empty="Chưa có ca kiểm thử được phê duyệt"
            columns={[
              { key: "test_case_key", label: "Mã" },
              { key: "title", label: "Tên", render: (item) => item.current_version?.title },
              {
                key: "version",
                label: "Phiên bản",
                render: (item) => `v${item.current_version?.version}`,
              },
              {
                key: "status",
                label: "Trạng thái",
                render: (item) => <StatusPill value={item.status} />,
              },
            ]}
          />
        </Panel>
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        <Panel title="Tạo ca kiểm thử thủ công">
          <form onSubmit={create} className="space-y-4 p-5">
            <label className="field-label">
              Tên
              <input
                className="apple-input mt-2"
                required
                value={form.title}
                onChange={(event) => setForm({ ...form, title: event.target.value })}
              />
            </label>
            <div className="grid gap-3 sm:grid-cols-3">
              <select
                aria-label="Loại ca kiểm thử"
                className="apple-input"
                value={form.type}
                onChange={(event) => setForm({ ...form, type: event.target.value })}
              >
                {[
                  "happy_path",
                  "negative",
                  "boundary",
                  "validation",
                  "permission",
                  "state_transition",
                  "integration",
                  "error_handling",
                  "data_persistence",
                  "concurrency",
                  "api",
                  "ui",
                  "custom",
                ].map((value) => (
                  <option key={value} value={value}>
                    {valueLabel(value)}
                  </option>
                ))}
              </select>
              <select
                aria-label="Ưu tiên ca kiểm thử"
                className="apple-input"
                value={form.priority}
                onChange={(event) => setForm({ ...form, priority: event.target.value })}
              >
                {["critical", "high", "medium", "low"].map((value) => (
                  <option key={value} value={value}>
                    {valueLabel(value)}
                  </option>
                ))}
              </select>
              <select
                aria-label="Rủi ro ca kiểm thử"
                className="apple-input"
                value={form.risk}
                onChange={(event) => setForm({ ...form, risk: event.target.value })}
              >
                {["critical", "high", "medium", "low"].map((value) => (
                  <option key={value} value={value}>
                    {valueLabel(value)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <p className="field-label mb-2">Thao tác</p>
              <QaDocumentEditor
                value={form.action}
                onChange={(action) => setForm({ ...form, action })}
                label="Thao tác của ca kiểm thử"
                minHeight="min-h-24"
              />
            </div>
            <div>
              <p className="field-label mb-2">Kết quả mong đợi</p>
              <QaDocumentEditor
                value={form.expected}
                onChange={(expected) => setForm({ ...form, expected })}
                label="Kết quả mong đợi của ca kiểm thử"
                minHeight="min-h-24"
              />
            </div>
            <button className="apple-button" type="submit">
              Lưu bản nháp
            </button>
          </form>
        </Panel>
        <Panel title="Kịch bản">
          <DataTable
            items={scenarios}
            empty="Chưa có kịch bản"
            columns={[
              { key: "scenario_key", label: "Mã" },
              { key: "title", label: "Tên" },
              { key: "category", label: "Nhóm" },
              { key: "origin", label: "Nguồn" },
            ]}
          />
        </Panel>
      </div>
      {duplicates.length > 0 && (
        <Panel title="Các ca kiểm thử có khả năng trùng">
          <DataTable
            items={duplicates.map((item, index) => ({ ...item, _id: index }))}
            columns={[
              {
                key: "left",
                label: "Ca kiểm thử bên trái",
                render: (item) => item.left.test_case_key,
              },
              {
                key: "right",
                label: "Ca kiểm thử bên phải",
                render: (item) => item.right.test_case_key,
              },
              { key: "similarity", label: "Độ tương đồng" },
              { key: "reasons", label: "Bằng chứng", render: (item) => item.reasons.join(", ") },
            ]}
          />
        </Panel>
      )}
      <Panel
        title="Nhập và xuất ca kiểm thử"
        description="CSV và XLSX luôn tạo bản xem trước trước khi người dùng xác nhận"
        actions={
          <div className="flex flex-wrap gap-2">
            <button
              className="secondary-button"
              type="button"
              onClick={() =>
                qaApi
                  .exportTestCases(project._id, "csv")
                  .catch((reason) => setError(messageOf(reason)))
              }
            >
              Xuất CSV
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() =>
                qaApi
                  .exportTestCases(project._id, "xlsx")
                  .catch((reason) => setError(messageOf(reason)))
              }
            >
              Xuất XLSX
            </button>
          </div>
        }
      >
        <div className="space-y-4 p-5">
          <input
            className="apple-input"
            aria-label="Tệp ca kiểm thử CSV hoặc XLSX"
            type="file"
            accept=".csv,.xlsx"
            onChange={async (event) => {
              const file = event.target.files?.[0];
              if (!file) return;
              try {
                setTestImport(await qaApi.uploadTestImport(project._id, file));
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          />
          {testImport && (
            <>
              <DataTable
                items={testImport.preview.map((item, index) => ({ ...item, _id: index }))}
                empty="Tệp không có ca kiểm thử hợp lệ"
                columns={[
                  { key: "title", label: "Tên" },
                  { key: "type", label: "Loại" },
                  { key: "priority", label: "Ưu tiên" },
                  { key: "expected", label: "Kết quả mong đợi" },
                ]}
              />
              <button
                className="apple-button"
                type="button"
                onClick={async () => {
                  try {
                    await qaApi.confirmTestImport(
                      testImport._id,
                      testImport.preview.map((_, index) => index),
                    );
                    setTestImport(null);
                    await load();
                  } catch (reason) {
                    setError(messageOf(reason));
                  }
                }}
              >
                Xác nhận nhập toàn bộ
              </button>
            </>
          )}
        </div>
      </Panel>
      <Panel
        title="OpenAPI và Postman"
        description="Nhập dữ liệu đã lọc thông tin nhạy cảm rồi tạo ca kiểm thử chỉ từ phản hồi có trong đặc tả"
      >
        <div className="grid gap-5 p-5 xl:grid-cols-2">
          <form
            className="space-y-4"
            onSubmit={async (event) => {
              event.preventDefault();
              try {
                await qaApi.importApiArtifact(project._id, apiImport);
                setApiImport({ ...apiImport, content: "" });
                await load();
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          >
            <label className="field-label">
              Loại nguồn
              <select
                className="apple-input mt-2"
                value={apiImport.format}
                onChange={(event) =>
                  setApiImport({
                    ...apiImport,
                    format: event.target.value,
                    filename: `${event.target.value}.json`,
                  })
                }
              >
                <option value="openapi">OpenAPI</option>
                <option value="postman">Postman</option>
              </select>
            </label>
            <label className="field-label">
              JSON đặc tả
              <textarea
                className="apple-input mt-2 min-h-48 font-mono"
                required
                value={apiImport.content}
                onChange={(event) => setApiImport({ ...apiImport, content: event.target.value })}
              />
            </label>
            <button className="secondary-button" type="submit">
              Import API metadata
            </button>
          </form>
          <DataTable
            items={operations}
            empty="Chưa có API Operation"
            columns={[
              { key: "method", label: "Method" },
              { key: "path", label: "Path" },
              { key: "title", label: "Tên" },
              {
                key: "generate",
                label: "Sinh test",
                render: (item) => (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={async () => {
                      try {
                        await qaApi.generateApiTests(item._id);
                        await load();
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    Tạo ca kiểm thử
                  </button>
                ),
              },
            ]}
          />
        </div>
      </Panel>
    </QaPage>
  );
}
