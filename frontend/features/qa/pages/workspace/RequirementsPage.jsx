"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import DataTable from "../../components/DataTable";
import {
  ErrorState,
  LoadingState,
  Panel,
  ProjectCrumb,
  QaPage,
  StatusPill,
} from "../../components/QaUi";
import { qaApi } from "../../services/qa.service";
import { emptyDoc, messageOf, textDoc, valueLabel } from "../../lib/qa";
import QaDocumentEditor from "../../editor/QaDocumentEditor";

const initialForm = {
  title: "",
  type: "functional",
  priority: "medium",
  risk: "medium",
  content_doc: emptyDoc(),
  acceptance: "",
};

export default function RequirementsPage({ project, section }) {
  const requirementId = section[0] && !["new", "import"].includes(section[0]) ? section[0] : "";
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [versions, setVersions] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [lint, setLint] = useState(null);
  const [importValue, setImportValue] = useState({
    filename: "requirements.md",
    format: "md",
    content: "",
  });
  const [preview, setPreview] = useState(null);
  const [upload, setUpload] = useState(null);
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const values = await qaApi.listRequirements(project._id, query);
      setItems(values);
      if (requirementId) {
        const detail = await qaApi.getRequirement(requirementId);
        setSelected(detail);
        setVersions(await qaApi.listRequirementVersions(requirementId));
      }
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setLoading(false);
    }
  }, [project._id, query, requirementId]);
  useEffect(() => {
    void load();
  }, [load]);
  const current = selected?.current_version;
  const criteria = useMemo(
    () =>
      form.acceptance
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line, index) => ({
          key: `AC-${index + 1}`,
          content_doc: textDoc(line),
          status: "draft",
        })),
    [form.acceptance],
  );
  const create = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await qaApi.createRequirement(project._id, {
        title: form.title,
        type: form.type,
        priority: form.priority,
        risk: form.risk,
        content_doc: form.content_doc,
        acceptance_criteria: criteria,
        business_rules: [],
        actors: [],
        dependencies: [],
        source_refs: [],
      });
      setForm(initialForm);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const baseline = async () => {
    if (!window.confirm("Xác nhận đặt phiên bản yêu cầu này làm phiên bản chuẩn")) return;
    try {
      await qaApi.baselineRequirement(current._id, current.revision);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const createVersion = async () => {
    const title = window.prompt("Tên yêu cầu cho phiên bản mới", current.title);
    if (!title) return;
    const reason = window.prompt("Lý do thay đổi", "Cập nhật quy tắc nghiệp vụ");
    if (!reason) return;
    try {
      await qaApi.createRequirementVersion(selected._id, {
        requirement_key: selected.requirement_key,
        title,
        type: current.type,
        priority: current.priority,
        risk: current.risk,
        content_doc: current.content_doc,
        acceptance_criteria: (current.acceptance_criteria || []).map((item) => ({
          key: item.key,
          content_doc: item.content_doc,
          status: item.status,
        })),
        business_rules: current.business_rules || [],
        actors: current.actors || [],
        dependencies: current.dependencies || [],
        source_refs: current.source_refs || [],
        change_reason: reason,
        expected_current_version_id: selected.current_version_id,
      });
      await load();
    } catch (reasonValue) {
      setError(messageOf(reasonValue));
    }
  };
  const importPreview = async (event) => {
    event.preventDefault();
    try {
      setPreview(await qaApi.createRequirementImport(project._id, importValue));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const confirmImport = async () => {
    try {
      await qaApi.confirmRequirementImport(
        preview._id,
        preview.preview.map((_, index) => index),
      );
      setPreview(null);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const uploadPreview = async (event) => {
    event.preventDefault();
    if (!upload) return;
    const format = upload.name.split(".").pop().toLowerCase();
    try {
      setPreview(await qaApi.uploadRequirementImport(project._id, upload, format));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <QaPage
      title={
        selected
          ? `${selected.requirement_key} ${current?.title || ""}`
          : "Yêu cầu và phiên bản chuẩn"
      }
      description="Yêu cầu được quản lý theo phiên bản cùng tiêu chí chấp nhận và quyết định phiên bản chuẩn do người dùng kiểm soát"
      actions={<ProjectCrumb projectId={project._id} />}
    >
      {error && <ErrorState message={error} />}
      {selected ? (
        <>
          <Panel
            title="Phiên bản hiện tại"
            actions={
              <div className="flex flex-wrap gap-2">
                <button
                  className="secondary-button"
                  type="button"
                  onClick={async () => {
                    try {
                      setLint(await qaApi.lintRequirement(current._id));
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                >
                  Kiểm tra chất lượng bằng AI
                </button>
                <button className="secondary-button" type="button" onClick={createVersion}>
                  Tạo phiên bản mới
                </button>
                {current.status !== "BASELINED" && (
                  <button className="apple-button" type="button" onClick={baseline}>
                    Đặt làm phiên bản chuẩn
                  </button>
                )}
              </div>
            }
          >
            <div className="grid gap-5 p-5 md:grid-cols-3">
              <div>
                <p className="field-label">Trạng thái</p>
                <div className="mt-2">
                  <StatusPill value={current.status} />
                </div>
              </div>
              <div>
                <p className="field-label">Phiên bản</p>
                <p className="mt-2 font-semibold">v{current.version}</p>
              </div>
              <div>
                <p className="field-label">Rủi ro</p>
                <p className="mt-2 font-semibold">{current.risk}</p>
              </div>
              <div className="md:col-span-3">
                <QaDocumentEditor
                  value={current.content_doc}
                  onChange={() => {}}
                  label="Nội dung yêu cầu"
                  readOnly
                />
              </div>
            </div>
          </Panel>
          {lint && (
            <Panel title={lint.valid ? "AI lint không có lỗi chặn" : "AI lint phát hiện vấn đề"}>
              <DataTable
                items={lint.findings}
                empty="Không có finding"
                columns={[
                  { key: "severity", label: "Mức độ" },
                  { key: "code", label: "Mã" },
                  { key: "message", label: "Nội dung" },
                ]}
              />
            </Panel>
          )}
          <Panel title="Lịch sử phiên bản">
            <DataTable
              items={versions}
              columns={[
                { key: "version", label: "Phiên bản", render: (item) => `v${item.version}` },
                { key: "title", label: "Tên" },
                {
                  key: "status",
                  label: "Trạng thái",
                  render: (item) => <StatusPill value={item.status} />,
                },
                { key: "change_reason", label: "Lý do" },
              ]}
            />
          </Panel>
        </>
      ) : (
        <>
          {loading ? (
            <LoadingState />
          ) : (
            <Panel
              title="Danh sách yêu cầu"
              actions={
                <input
                  aria-label="Tìm yêu cầu"
                  className="apple-input w-64"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Tìm yêu cầu"
                />
              }
            >
              <DataTable
                onSelect={(item) =>
                  window.location.assign(`/qa/projects/${project._id}/requirements/${item._id}`)
                }
                items={items}
                empty="Chưa có yêu cầu"
                columns={[
                  { key: "requirement_key", label: "Mã" },
                  { key: "title", label: "Tên", render: (item) => item.current_version?.title },
                  {
                    key: "type",
                    label: "Loại",
                    render: (item) => valueLabel(item.current_version?.type),
                  },
                  {
                    key: "risk",
                    label: "Rủi ro",
                    render: (item) => valueLabel(item.current_version?.risk),
                  },
                  {
                    key: "status",
                    label: "Trạng thái",
                    render: (item) => <StatusPill value={item.status} />,
                  },
                ]}
              />
            </Panel>
          )}
          <div className="grid gap-5 xl:grid-cols-2">
            <Panel title="Tạo yêu cầu thủ công">
              <form className="space-y-4 p-5" onSubmit={create}>
                <label className="field-label">
                  Tên
                  <input
                    className="apple-input mt-2"
                    required
                    minLength={2}
                    value={form.title}
                    onChange={(event) => setForm({ ...form, title: event.target.value })}
                  />
                </label>
                <div className="grid gap-3 sm:grid-cols-3">
                  <label className="field-label">
                    Loại
                    <select
                      className="apple-input mt-2"
                      value={form.type}
                      onChange={(event) => setForm({ ...form, type: event.target.value })}
                    >
                      <option value="functional">Chức năng</option>
                      <option value="non_functional">Phi chức năng</option>
                      <option value="business_rule">Quy tắc nghiệp vụ</option>
                      <option value="api">API</option>
                      <option value="ui">UI</option>
                    </select>
                  </label>
                  <label className="field-label">
                    Ưu tiên
                    <select
                      className="apple-input mt-2"
                      value={form.priority}
                      onChange={(event) => setForm({ ...form, priority: event.target.value })}
                    >
                      {["critical", "high", "medium", "low"].map((value) => (
                        <option key={value} value={value}>
                          {valueLabel(value)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="field-label">
                    Rủi ro
                    <select
                      className="apple-input mt-2"
                      value={form.risk}
                      onChange={(event) => setForm({ ...form, risk: event.target.value })}
                    >
                      {["critical", "high", "medium", "low"].map((value) => (
                        <option key={value} value={value}>
                          {valueLabel(value)}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <QaDocumentEditor
                  value={form.content_doc}
                  onChange={(content_doc) => setForm({ ...form, content_doc })}
                  label="Nội dung yêu cầu"
                />
                <label className="field-label">
                  Tiêu chí chấp nhận mỗi dòng một điều kiện
                  <textarea
                    className="apple-input mt-2 min-h-28"
                    value={form.acceptance}
                    onChange={(event) => setForm({ ...form, acceptance: event.target.value })}
                  />
                </label>
                <button className="apple-button" type="submit">
                  Lưu yêu cầu
                </button>
              </form>
            </Panel>
            <Panel title="Nhập tài liệu" description="Luôn xem trước và xác nhận trước khi ghi">
              <form onSubmit={uploadPreview} className="space-y-4 border-b border-border p-5">
                <label className="field-label">
                  Tệp SRS BRD hoặc bảng yêu cầu
                  <input
                    className="apple-input mt-2"
                    type="file"
                    accept=".pdf,.docx,.txt,.md,.csv,.xlsx"
                    onChange={(event) => setUpload(event.target.files?.[0] || null)}
                  />
                </label>
                <button className="secondary-button" type="submit" disabled={!upload}>
                  Tải lên và xem trước
                </button>
              </form>
              <form onSubmit={importPreview} className="space-y-4 p-5">
                <label className="field-label">
                  Tên tệp
                  <input
                    className="apple-input mt-2"
                    value={importValue.filename}
                    onChange={(event) =>
                      setImportValue({ ...importValue, filename: event.target.value })
                    }
                  />
                </label>
                <label className="field-label">
                  Định dạng
                  <select
                    className="apple-input mt-2"
                    value={importValue.format}
                    onChange={(event) =>
                      setImportValue({ ...importValue, format: event.target.value })
                    }
                  >
                    {["md", "txt", "csv", "openapi", "postman", "pdf", "docx", "xlsx"].map(
                      (value) => (
                        <option key={value}>{value}</option>
                      ),
                    )}
                  </select>
                </label>
                <label className="field-label">
                  Nội dung nguồn
                  <textarea
                    className="apple-input mt-2 min-h-48 font-mono"
                    required
                    value={importValue.content}
                    onChange={(event) =>
                      setImportValue({ ...importValue, content: event.target.value })
                    }
                  />
                </label>
                <button className="secondary-button" type="submit">
                  Tạo bản xem trước
                </button>
              </form>
              {preview && (
                <div className="border-t border-border p-5">
                  <DataTable
                    items={preview.preview.map((item, index) => ({ ...item, _id: index }))}
                    columns={[
                      { key: "title", label: "Yêu cầu phát hiện" },
                      { key: "type", label: "Loại" },
                    ]}
                  />
                  <button className="apple-button mt-4" type="button" onClick={confirmImport}>
                    Xác nhận nhập {preview.preview.length} yêu cầu
                  </button>
                </div>
              )}
            </Panel>
          </div>
        </>
      )}
    </QaPage>
  );
}
