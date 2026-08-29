"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import DataTable from "../../components/DataTable";
import ReviewCommentsPanel from "../../components/ReviewCommentsPanel";
import {
  ErrorState,
  LoadingState,
  Pagination,
  Panel,
  ProjectCrumb,
  QaPage,
  StatusPill,
  useQaActionDialog,
} from "../../components/QaUi";
import { qaApi } from "../../services/qa.service";
import { docText, emptyDoc, messageOf, textDoc, valueLabel } from "../../lib/qa";
import QaDocumentEditor from "../../editor/QaDocumentEditor";

const initialForm = {
  title: "",
  type: "functional",
  priority: "medium",
  risk: "medium",
  content_doc: emptyDoc(),
  acceptance: "",
  businessRules: "",
  actors: "",
  dependencies: "",
  tags: "",
  ownerId: "",
};

export default function RequirementsPage({ project, section }) {
  const { ask, dialog } = useQaActionDialog();
  const requirementId = section[0] && !["new", "import"].includes(section[0]) ? section[0] : "";
  const [items, setItems] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [selected, setSelected] = useState(null);
  const [versions, setVersions] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({ status: "", coverage: "", tag: "", owner: "", sort: "-updated_at" });
  const [page, setPage] = useState(1);
  const [pageInfo, setPageInfo] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [lint, setLint] = useState(null);
  const [importValue, setImportValue] = useState({
    filename: "requirements.md",
    format: "md",
    content: "",
  });
  const [preview, setPreview] = useState(null);
  const [selectedIndexes, setSelectedIndexes] = useState([]);
  const [upload, setUpload] = useState(null);
  const [sourceDocument, setSourceDocument] = useState(null);
  const [draft, setDraft] = useState(null);
  const [draftDirty, setDraftDirty] = useState(false);
  const [saveState, setSaveState] = useState("saved");
  const draftSequence = useRef(0);
  const loadedVersion = useRef("");
  const [comparison, setComparison] = useState(null);
  const [compareFrom, setCompareFrom] = useState("");
  const [compareTo, setCompareTo] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const values = await qaApi.listRequirementPage(project._id, {
        q: query,
        ...filters,
        page,
        page_size: 50,
      });
      setItems(values.items);
      setPageInfo(values);
      if (requirementId) {
        const detail = await qaApi.getRequirement(requirementId);
        setSelected(detail);
        const history = await qaApi.listRequirementVersions(requirementId);
        setVersions(history);
        setCompareFrom(history[1]?._id || history[0]?._id || "");
        setCompareTo(history[0]?._id || "");
      }
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setLoading(false);
    }
  }, [filters, page, project._id, query, requirementId]);
  useEffect(() => {
    void load();
  }, [load]);
  const current = selected?.current_version;
  useEffect(() => {
    if (!current) return;
    if (loadedVersion.current === current._id) return;
    loadedVersion.current = current._id;
    setDraft({
      title: current.title,
      type: current.type,
      priority: current.priority,
      risk: current.risk,
      content_doc: current.content_doc,
      acceptance: (current.acceptance_criteria || [])
        .map((item) => docText(item.content_doc))
        .join("\n"),
      businessRules: (current.business_rules || []).join("\n"),
      actors: (current.actors || []).join(", "),
      dependencies: (current.dependencies || []).join("\n"),
      tags: (selected.tags || current.tags || []).join(", "),
      ownerId: selected.owner_id || current.owner_id || "",
    });
    setDraftDirty(false);
    setSaveState("saved");
  }, [current, selected]);
  const changeDraft = (patch) => {
    draftSequence.current += 1;
    setDraft((value) => ({ ...value, ...patch }));
    setDraftDirty(true);
    setSaveState("pending");
  };
  const persistDraft = useCallback(
    async (snapshot, sequence) => {
      if (!snapshot || !current || !selected) return;
      setSaveState("saving");
      try {
        const result = await qaApi.updateRequirementDraft(project._id, selected._id, {
          expected_revision: current.revision,
          title: snapshot.title,
          type: snapshot.type,
          priority: snapshot.priority,
          risk: snapshot.risk,
          content_doc: snapshot.content_doc,
          acceptance_criteria: snapshot.acceptance
            .split("\n")
            .map((line) => line.trim())
            .filter(Boolean)
            .map((line, index) => ({
              key: `AC-${index + 1}`,
              content_doc: textDoc(line),
              status: "draft",
            })),
          business_rules: snapshot.businessRules
            .split("\n")
            .map((value) => value.trim())
            .filter(Boolean),
          actors: snapshot.actors.split(",").map((value) => value.trim()).filter(Boolean),
          dependencies: snapshot.dependencies
            .split("\n")
            .map((value) => value.trim())
            .filter(Boolean),
          tags: snapshot.tags.split(",").map((value) => value.trim()).filter(Boolean),
          owner_id: snapshot.ownerId.trim() || null,
        });
        setSelected(result);
        if (draftSequence.current === sequence) {
          setDraftDirty(false);
          setSaveState("saved");
        } else {
          setSaveState("pending");
        }
      } catch (reason) {
        setSaveState("error");
        setError(messageOf(reason));
      }
    },
    [current, project._id, selected],
  );
  useEffect(() => {
    if (!draftDirty || current?.status !== "DRAFT" || !draft) return undefined;
    const sequence = draftSequence.current;
    const timer = window.setTimeout(() => {
      void persistDraft(draft, sequence);
    }, 1500);
    return () => window.clearTimeout(timer);
  }, [current?.status, draft, draftDirty, persistDraft]);
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
        business_rules: form.businessRules.split("\n").map((value) => value.trim()).filter(Boolean),
        actors: form.actors.split(",").map((value) => value.trim()).filter(Boolean),
        dependencies: form.dependencies.split("\n").map((value) => value.trim()).filter(Boolean),
        source_refs: [],
        tags: form.tags.split(",").map((value) => value.trim()).filter(Boolean),
        owner_id: form.ownerId.trim() || null,
      });
      setForm(initialForm);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const review = async (action) => {
    const answer = await ask({
      title: action === "approve" ? "Phê duyệt yêu cầu" : "Rà soát yêu cầu",
      description: `${selected.requirement_key} phiên bản ${current.version}`,
      confirmLabel: action === "changes" ? "Yêu cầu chỉnh sửa" : "Xác nhận",
      fields: [
        {
          name: "note",
          label: action === "changes" ? "Nội dung cần chỉnh sửa" : "Ghi chú rà soát",
          initialValue:
            action === "changes"
              ? "Cần cập nhật theo nhận xét rà soát"
              : "Đã rà soát nội dung và nguồn",
          required: true,
          multiline: true,
          autoFocus: true,
        },
      ],
    });
    if (!answer) return;
    try {
      const payload = { expected_revision: current.revision, review_note: answer.note };
      if (action === "submit") {
        await qaApi.submitRequirementReview(project._id, selected._id, payload);
      } else if (action === "changes") {
        await qaApi.requestRequirementChanges(project._id, selected._id, payload);
      } else {
        await qaApi.approveRequirement(project._id, selected._id, payload);
      }
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const saveDraft = async () => {
    await persistDraft(draft, draftSequence.current);
  };
  const createVersion = async () => {
    const answer = await ask({
      title: "Tạo phiên bản yêu cầu mới",
      description: `${selected.requirement_key} sẽ giữ nguyên phiên bản chuẩn hiện tại để truy vết`,
      confirmLabel: "Tạo phiên bản",
      fields: [
        {
          name: "title",
          label: "Tên yêu cầu",
          initialValue: current.title,
          required: true,
          autoFocus: true,
        },
        {
          name: "reason",
          label: "Lý do thay đổi",
          initialValue: "Cập nhật quy tắc nghiệp vụ",
          required: true,
          multiline: true,
        },
      ],
    });
    if (!answer) return;
    try {
      await qaApi.createRequirementVersion(selected._id, {
        requirement_key: selected.requirement_key,
        title: answer.title,
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
        tags: selected.tags || current.tags || [],
        owner_id: selected.owner_id || current.owner_id || null,
        change_reason: answer.reason,
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
      const document = await qaApi.createRequirementDocument(project._id, importValue);
      setSourceDocument(document);
      const result = await qaApi.extractRequirementDocument(
        document._id,
        `source-${document.content_hash}`,
      );
      setPreview(result);
      setSelectedIndexes(result.preview.map((_, index) => index));
      setSourceDocument(await qaApi.getRequirementDocument(document._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const confirmImport = async () => {
    try {
      await qaApi.confirmRequirementImport(
        preview._id,
        selectedIndexes,
        preview.revision,
      );
      setPreview(null);
      setSelectedIndexes([]);
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
      const document = await qaApi.uploadRequirementDocument(project._id, upload, format);
      setSourceDocument(document);
      if (document.status === "PARSE_FAILED") {
        setPreview(null);
        setError("Tệp gốc đã được lưu nhưng bộ phân tích không đọc được nội dung");
        return;
      }
      const result = await qaApi.extractRequirementDocument(
        document._id,
        `source-${document.content_hash}`,
      );
      setPreview(result);
      setSelectedIndexes(result.preview.map((_, index) => index));
      setSourceDocument(await qaApi.getRequirementDocument(document._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const editCandidate = (index, patch) => {
    setPreview((value) => ({
      ...value,
      preview: value.preview.map((candidate, candidateIndex) =>
        candidateIndex === index ? { ...candidate, ...patch } : candidate,
      ),
    }));
  };
  const saveImportReview = async (nextPreview, reviewNote, nextSelection = selectedIndexes) => {
    try {
      const result = await qaApi.updateRequirementImport(preview._id, {
        expected_revision: preview.revision,
        preview: nextPreview,
        review_note: reviewNote,
      });
      setPreview(result);
      setSelectedIndexes(nextSelection.filter((index) => index < result.preview.length));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const mergeCandidates = async () => {
    const indexes = [...selectedIndexes].sort((left, right) => left - right);
    if (indexes.length < 2) {
      setError("Cần chọn ít nhất hai ứng viên để gộp");
      return;
    }
    const candidates = indexes.map((index) => preview.preview[index]);
    const firstIndex = indexes[0];
    const merged = {
      ...candidates[0],
      title: candidates.map((candidate) => candidate.title).join(" và ").slice(0, 300),
      content_doc: textDoc(candidates.map((candidate) => docText(candidate.content_doc)).join("\n\n")),
      acceptance_criteria: candidates.flatMap(
        (candidate) => candidate.acceptance_criteria || [],
      ),
      business_rules: [...new Set(candidates.flatMap((candidate) => candidate.business_rules || []))],
      actors: [...new Set(candidates.flatMap((candidate) => candidate.actors || []))],
      dependencies: [...new Set(candidates.flatMap((candidate) => candidate.dependencies || []))],
      source_refs: candidates.flatMap((candidate) => candidate.source_refs || []),
      extraction_confidence: Math.min(
        ...candidates.map((candidate) => candidate.extraction_confidence ?? 1),
      ),
      candidate_relation: "merged",
    };
    const next = preview.preview
      .map((candidate, index) => (index === firstIndex ? merged : candidate))
      .filter((_, index) => index === firstIndex || !indexes.includes(index));
    await saveImportReview(next, "Gộp các ứng viên yêu cầu", [firstIndex]);
  };
  const splitCandidate = async () => {
    if (selectedIndexes.length !== 1) {
      setError("Cần chọn đúng một ứng viên để tách");
      return;
    }
    const index = selectedIndexes[0];
    const candidate = preview.preview[index];
    const sourceText = docText(candidate.content_doc).trim();
    let parts = sourceText.split(/\n+/).map((part) => part.trim()).filter(Boolean);
    if (parts.length < 2) {
      parts = (sourceText.match(/[^.!?;]+[.!?;]?/g) || [])
        .map((part) => part.trim())
        .filter(Boolean);
    }
    if (parts.length < 2) {
      setError("Nội dung cần ít nhất hai dòng hoặc hai câu để tách");
      return;
    }
    const split = parts.map((part, partIndex) => ({
      ...candidate,
      title: part.slice(0, 300),
      content_doc: textDoc(part),
      candidate_relation: `split-${partIndex + 1}`,
    }));
    const next = [...preview.preview];
    next.splice(index, 1, ...split);
    await saveImportReview(
      next,
      "Tách ứng viên yêu cầu",
      split.map((_, offset) => index + offset),
    );
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
                {current.status === "BASELINED" && (
                  <button className="secondary-button" type="button" onClick={createVersion}>
                    Tạo phiên bản mới
                  </button>
                )}
                {current.status !== "OBSOLETE" && (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={async () => {
                      const answer = await ask({
                        title: "Đánh dấu yêu cầu không còn hiệu lực",
                        description: `${selected.requirement_key} vẫn được giữ trong lịch sử truy vết`,
                        confirmLabel: "Đánh dấu",
                        danger: true,
                        fields: [
                          {
                            name: "reason",
                            label: "Lý do",
                            initialValue: "Yêu cầu không còn thuộc phạm vi sản phẩm",
                            required: true,
                            multiline: true,
                            autoFocus: true,
                          },
                        ],
                      });
                      if (!answer) return;
                      try {
                        await qaApi.obsoleteRequirement(selected._id, {
                          expected_current_version_id: selected.current_version_id,
                          reason: answer.reason,
                        });
                        await load();
                      } catch (value) {
                        setError(messageOf(value));
                      }
                    }}
                  >
                    Đánh dấu không còn hiệu lực
                  </button>
                )}
                {current.status === "DRAFT" && (
                  <button className="apple-button" type="button" onClick={() => review("submit")}>
                    Gửi rà soát
                  </button>
                )}
                {current.status === "IN_REVIEW" && (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => review("changes")}
                  >
                    Yêu cầu chỉnh sửa
                  </button>
                )}
                {current.status === "IN_REVIEW" && (
                  <button className="apple-button" type="button" onClick={() => review("approve")}>
                    Phê duyệt phiên bản
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
              {current.status === "DRAFT" && draft ? (
                <div className="space-y-4 md:col-span-3">
                  <input
                    aria-label="Tên yêu cầu"
                    className="apple-input"
                    value={draft.title}
                    onChange={(event) => changeDraft({ title: event.target.value })}
                  />
                  <div className="grid gap-3 sm:grid-cols-3">
                    <select
                      aria-label="Loại yêu cầu"
                      className="apple-input"
                      value={draft.type}
                      onChange={(event) => changeDraft({ type: event.target.value })}
                    >
                      {[
                        "functional",
                        "non_functional",
                        "business_rule",
                        "api",
                        "ui",
                        "data",
                        "permission",
                        "integration",
                        "constraint",
                      ].map((value) => (
                        <option key={value} value={value}>
                          {valueLabel(value)}
                        </option>
                      ))}
                    </select>
                    <select
                      aria-label="Ưu tiên yêu cầu"
                      className="apple-input"
                      value={draft.priority}
                      onChange={(event) => changeDraft({ priority: event.target.value })}
                    >
                      {['critical', 'high', 'medium', 'low'].map((value) => (
                        <option key={value} value={value}>
                          {valueLabel(value)}
                        </option>
                      ))}
                    </select>
                    <select
                      aria-label="Rủi ro yêu cầu"
                      className="apple-input"
                      value={draft.risk}
                      onChange={(event) => changeDraft({ risk: event.target.value })}
                    >
                      {['critical', 'high', 'medium', 'low'].map((value) => (
                        <option key={value} value={value}>
                          {valueLabel(value)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <QaDocumentEditor
                    value={draft.content_doc}
                    onChange={(content_doc) => changeDraft({ content_doc })}
                    label="Nội dung yêu cầu"
                  />
                  <textarea
                    aria-label="Tiêu chí chấp nhận"
                    className="apple-input min-h-28"
                    value={draft.acceptance}
                    onChange={(event) => changeDraft({ acceptance: event.target.value })}
                  />
                  <div className="grid gap-3 lg:grid-cols-3">
                    <textarea
                      aria-label="Quy tắc nghiệp vụ"
                      className="apple-input min-h-24"
                      value={draft.businessRules}
                      onChange={(event) => changeDraft({ businessRules: event.target.value })}
                      placeholder="Mỗi dòng một quy tắc nghiệp vụ"
                    />
                    <textarea
                      aria-label="Tác nhân"
                      className="apple-input min-h-24"
                      value={draft.actors}
                      onChange={(event) => changeDraft({ actors: event.target.value })}
                      placeholder="Các tác nhân phân tách bằng dấu phẩy"
                    />
                    <textarea
                      aria-label="Phụ thuộc yêu cầu"
                      className="apple-input min-h-24"
                      value={draft.dependencies}
                      onChange={(event) => changeDraft({ dependencies: event.target.value })}
                      placeholder="Mỗi dòng một phụ thuộc"
                    />
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <input
                      aria-label="Nhãn yêu cầu"
                      className="apple-input"
                      value={draft.tags}
                      onChange={(event) => changeDraft({ tags: event.target.value })}
                      placeholder="Nhãn phân cách bằng dấu phẩy"
                    />
                    <input
                      aria-label="Người phụ trách yêu cầu"
                      className="apple-input"
                      value={draft.ownerId}
                      onChange={(event) => changeDraft({ ownerId: event.target.value })}
                      placeholder="Mã người phụ trách"
                    />
                  </div>
                  <button className="secondary-button" type="button" onClick={saveDraft}>
                    Lưu bản nháp
                  </button>
                  <span className="ml-3 text-[12px] text-ink-muted" aria-live="polite">
                    {saveState === "saving"
                      ? "Đang tự động lưu"
                      : saveState === "pending"
                        ? "Có thay đổi chưa lưu"
                        : saveState === "error"
                          ? "Tự động lưu thất bại"
                          : "Đã tự động lưu"}
                  </span>
                </div>
              ) : (
                <div className="md:col-span-3">
                  <QaDocumentEditor
                    value={current.content_doc}
                    onChange={() => {}}
                    label="Nội dung yêu cầu"
                    readOnly
                  />
                </div>
              )}
            </div>
          </Panel>
          <Panel title="Dấu vết nguồn">
            <DataTable
              items={(current.source_refs || []).map((item, index) => ({
                ...item,
                _id: `${item.requirement_document_id || "source"}-${index}`,
              }))}
              empty="Yêu cầu được tạo thủ công và chưa có nguồn tài liệu đính kèm"
              columns={[
                { key: "requirement_document_id", label: "Tài liệu nguồn" },
                { key: "format", label: "Định dạng" },
                {
                  key: "location",
                  label: "Vị trí",
                  render: (item) =>
                    item.source_start !== undefined
                      ? `${item.source_start} đến ${item.source_end}`
                      : item.candidate_index !== undefined
                        ? `Mục ${item.candidate_index + 1}`
                        : "Toàn bộ tài liệu",
                },
                { key: "content_hash", label: "SHA256" },
              ]}
            />
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
            {versions.length > 1 && (
              <div className="flex flex-wrap gap-3 border-t border-border p-5">
                <select
                  aria-label="Phiên bản gốc"
                  className="apple-input min-w-48"
                  value={compareFrom}
                  onChange={(event) => setCompareFrom(event.target.value)}
                >
                  {versions.map((item) => (
                    <option key={item._id} value={item._id}>
                      v{item.version} {item.title}
                    </option>
                  ))}
                </select>
                <select
                  aria-label="Phiên bản so sánh"
                  className="apple-input min-w-48"
                  value={compareTo}
                  onChange={(event) => setCompareTo(event.target.value)}
                >
                  {versions.map((item) => (
                    <option key={item._id} value={item._id}>
                      v{item.version} {item.title}
                    </option>
                  ))}
                </select>
                <button
                  className="secondary-button"
                  type="button"
                  disabled={!compareFrom || !compareTo || compareFrom === compareTo}
                  onClick={async () => {
                    try {
                      setComparison(
                        await qaApi.compareRequirement(selected._id, compareFrom, compareTo),
                      );
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                >
                  So sánh phiên bản
                </button>
              </div>
            )}
          </Panel>
          {comparison && (
            <Panel
              title="Khác biệt phiên bản"
              actions={
                <button
                  className="apple-button"
                  type="button"
                  onClick={async () => {
                    try {
                      await qaApi.createChangeSet(selected._id, {
                        from_version_id: compareFrom,
                        to_version_id: compareTo,
                      });
                      window.location.assign(`/qa/projects/${project._id}/changes`);
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                >
                  Tạo bộ thay đổi
                </button>
              }
            >
              <DataTable
                items={comparison.changes.map((item, index) => ({ ...item, _id: index }))}
                empty="Hai phiên bản không có khác biệt ngữ nghĩa"
                columns={[
                  { key: "type", label: "Loại thay đổi" },
                  { key: "field", label: "Trường" },
                  { key: "before", label: "Trước", render: (item) => JSON.stringify(item.before) },
                  { key: "after", label: "Sau", render: (item) => JSON.stringify(item.after) },
                ]}
              />
            </Panel>
          )}
          <ReviewCommentsPanel
            projectId={project._id}
            artifactType="requirement_version"
            artifactId={current._id}
          />
        </>
      ) : (
        <>
          {loading ? (
            <LoadingState />
          ) : (
            <Panel
              title="Danh sách yêu cầu"
              actions={
                <div className="flex flex-wrap gap-2">
                  <input
                    aria-label="Tìm yêu cầu"
                    className="apple-input w-64"
                    value={query}
                    onChange={(event) => {
                      setQuery(event.target.value);
                      setPage(1);
                    }}
                    placeholder="Tìm yêu cầu"
                  />
                  <button
                    className="secondary-button"
                    disabled={!selectedIds.length}
                    type="button"
                    onClick={async () => {
                      const answer = await ask({
                        title: "Cập nhật nhãn hàng loạt",
                        description: `${selectedIds.length} yêu cầu đã chọn`,
                        confirmLabel: "Cập nhật nhãn",
                        fields: [
                          { name: "add", label: "Nhãn cần thêm phân cách bằng dấu phẩy", autoFocus: true },
                          { name: "remove", label: "Nhãn cần gỡ phân cách bằng dấu phẩy" },
                        ],
                      });
                      if (!answer) return;
                      try {
                        const splitTags = (value) => value.split(",").map((item) => item.trim()).filter(Boolean);
                        await qaApi.bulkTags(project._id, {
                          artifact_type: "requirement",
                          ids: selectedIds,
                          add_tags: splitTags(answer.add),
                          remove_tags: splitTags(answer.remove),
                        });
                        setSelectedIds([]);
                        await load();
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    Cập nhật nhãn
                  </button>
                  <button
                    className="danger-button"
                    disabled={!selectedIds.length}
                    type="button"
                    onClick={async () => {
                      const answer = await ask({
                        title: "Lưu trữ yêu cầu hàng loạt",
                        description: `${selectedIds.length} yêu cầu vẫn được giữ toàn bộ lịch sử`,
                        confirmLabel: "Lưu trữ",
                        danger: true,
                        fields: [{ name: "reason", label: "Lý do", required: true, multiline: true, autoFocus: true }],
                      });
                      if (!answer) return;
                      try {
                        await qaApi.bulkArchive(project._id, {
                          artifact_type: "requirement",
                          ids: selectedIds,
                          reason: answer.reason,
                        });
                        setSelectedIds([]);
                        await load();
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    Lưu trữ
                  </button>
                </div>
              }
            >
              <div className="grid gap-3 border-b border-border p-4 sm:grid-cols-2 xl:grid-cols-5">
                <select
                  aria-label="Lọc trạng thái yêu cầu"
                  className="apple-input"
                  value={filters.status}
                  onChange={(event) => {
                    setFilters({ ...filters, status: event.target.value });
                    setPage(1);
                  }}
                >
                  <option value="">Mọi trạng thái</option>
                  <option value="DRAFT">Bản nháp</option>
                  <option value="IN_REVIEW">Đang rà soát</option>
                  <option value="BASELINED">Đã phê duyệt</option>
                  <option value="OBSOLETE">Không còn hiệu lực</option>
                </select>
                <select
                  aria-label="Lọc độ phủ yêu cầu"
                  className="apple-input"
                  value={filters.coverage}
                  onChange={(event) => {
                    setFilters({ ...filters, coverage: event.target.value });
                    setPage(1);
                  }}
                >
                  <option value="">Mọi độ phủ</option>
                  <option value="covered">Đã phủ</option>
                  <option value="uncovered">Chưa phủ</option>
                </select>
                <input
                  aria-label="Lọc nhãn yêu cầu"
                  className="apple-input"
                  placeholder="Nhãn"
                  value={filters.tag}
                  onChange={(event) => {
                    setFilters({ ...filters, tag: event.target.value });
                    setPage(1);
                  }}
                />
                <input
                  aria-label="Lọc người phụ trách yêu cầu"
                  className="apple-input"
                  placeholder="Mã người phụ trách"
                  value={filters.owner}
                  onChange={(event) => {
                    setFilters({ ...filters, owner: event.target.value });
                    setPage(1);
                  }}
                />
                <select
                  aria-label="Sắp xếp yêu cầu"
                  className="apple-input"
                  value={filters.sort}
                  onChange={(event) => {
                    setFilters({ ...filters, sort: event.target.value });
                    setPage(1);
                  }}
                >
                  <option value="-updated_at">Mới cập nhật</option>
                  <option value="updated_at">Cũ cập nhật</option>
                  <option value="requirement_key">Mã tăng dần</option>
                  <option value="title">Tên tăng dần</option>
                </select>
              </div>
              <DataTable
                onSelect={(item) =>
                  window.location.assign(`/qa/projects/${project._id}/requirements/${item._id}`)
                }
                items={items}
                selectedIds={selectedIds}
                onSelectionChange={setSelectedIds}
                selectionLabel="Chọn yêu cầu"
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
              <Pagination value={pageInfo} onChange={setPage} />
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
                <label className="field-label">
                  Quy tắc nghiệp vụ mỗi dòng một quy tắc
                  <textarea
                    className="apple-input mt-2 min-h-24"
                    value={form.businessRules}
                    onChange={(event) => setForm({ ...form, businessRules: event.target.value })}
                  />
                </label>
                <label className="field-label">
                  Tác nhân phân tách bằng dấu phẩy
                  <input
                    className="apple-input mt-2"
                    value={form.actors}
                    onChange={(event) => setForm({ ...form, actors: event.target.value })}
                  />
                </label>
                <label className="field-label">
                  Phụ thuộc mỗi dòng một mục
                  <textarea
                    className="apple-input mt-2 min-h-20"
                    value={form.dependencies}
                    onChange={(event) => setForm({ ...form, dependencies: event.target.value })}
                  />
                </label>
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="field-label">
                    Nhãn phân cách bằng dấu phẩy
                    <input
                      className="apple-input mt-2"
                      value={form.tags}
                      onChange={(event) => setForm({ ...form, tags: event.target.value })}
                    />
                  </label>
                  <label className="field-label">
                    Mã người phụ trách
                    <input
                      className="apple-input mt-2"
                      value={form.ownerId}
                      onChange={(event) => setForm({ ...form, ownerId: event.target.value })}
                    />
                  </label>
                </div>
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
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold">
                        {preview.status === "CONFIRMED"
                          ? "Nguồn này đã được nhập trước đó"
                          : "Rà soát ứng viên trước khi nhập"}
                      </p>
                      <p className="mt-1 text-[12px] text-ink-muted">
                        Đã chọn {selectedIndexes.length} trên {preview.preview.length} ứng viên
                      </p>
                    </div>
                    {preview.status === "PREVIEW_READY" && (
                      <div className="flex flex-wrap gap-2">
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={() =>
                            saveImportReview(
                              preview.preview,
                              "Chỉnh sửa nội dung ứng viên yêu cầu",
                            )
                          }
                        >
                          Lưu chỉnh sửa
                        </button>
                        <button className="secondary-button" type="button" onClick={splitCandidate}>
                          Tách mục đã chọn
                        </button>
                        <button className="secondary-button" type="button" onClick={mergeCandidates}>
                          Gộp các mục đã chọn
                        </button>
                      </div>
                    )}
                  </div>
                  <DataTable
                    items={preview.preview.map((item, index) => ({
                      ...item,
                      _id: `candidate-${index}`,
                      candidateIndex: index,
                    }))}
                    columns={[
                      {
                        key: "selected",
                        label: "Nhập",
                        render: (item) => (
                          <input
                            aria-label={`Chọn ứng viên ${item.candidateIndex + 1}`}
                            type="checkbox"
                            checked={selectedIndexes.includes(item.candidateIndex)}
                            disabled={preview.status !== "PREVIEW_READY"}
                            onChange={(event) =>
                              setSelectedIndexes((values) =>
                                event.target.checked
                                  ? [...values, item.candidateIndex].sort((left, right) => left - right)
                                  : values.filter((value) => value !== item.candidateIndex),
                              )
                            }
                          />
                        ),
                      },
                      {
                        key: "title",
                        label: "Yêu cầu phát hiện",
                        render: (item) => (
                          <input
                            aria-label={`Tên ứng viên ${item.candidateIndex + 1}`}
                            className="apple-input min-w-64"
                            value={item.title}
                            disabled={preview.status !== "PREVIEW_READY"}
                            onChange={(event) =>
                              editCandidate(item.candidateIndex, { title: event.target.value })
                            }
                          />
                        ),
                      },
                      {
                        key: "content_doc",
                        label: "Nội dung",
                        render: (item) => (
                          <textarea
                            aria-label={`Nội dung ứng viên ${item.candidateIndex + 1}`}
                            className="apple-input min-h-20 min-w-72"
                            value={docText(item.content_doc)}
                            disabled={preview.status !== "PREVIEW_READY"}
                            onChange={(event) =>
                              editCandidate(item.candidateIndex, {
                                content_doc: textDoc(event.target.value),
                              })
                            }
                          />
                        ),
                      },
                      { key: "type", label: "Loại" },
                      {
                        key: "candidate_relation",
                        label: "Quan hệ ứng viên",
                        render: (item) => item.candidate_relation || "Nguyên bản",
                      },
                      {
                        key: "extraction_confidence",
                        label: "Độ tin cậy trích xuất",
                        render: (item) =>
                          `${Math.round((item.extraction_confidence ?? 1) * 100)}%`,
                      },
                      {
                        key: "source_refs",
                        label: "Vị trí nguồn",
                        render: (item) => {
                          const source = item.source_refs?.[0];
                          if (!source) return "Không có";
                          if (source.source_start !== undefined) {
                            return `${source.source_start} đến ${source.source_end}`;
                          }
                          return `Mục ${source.candidate_index + 1}`;
                        },
                      },
                    ]}
                  />
                  {preview.status === "PREVIEW_READY" && (
                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <button
                        className="apple-button"
                        type="button"
                        disabled={selectedIndexes.length === 0}
                        onClick={confirmImport}
                      >
                        Xác nhận nhập {selectedIndexes.length} yêu cầu
                      </button>
                      <p className="text-[12px] text-ink-muted">
                        {preview.preview.length - selectedIndexes.length} ứng viên bị loại sẽ không được ghi
                      </p>
                    </div>
                  )}
                </div>
              )}
              {sourceDocument && (
                <div className="border-t border-border p-5 text-[12px] text-ink-muted">
                  <p>Nguồn {sourceDocument.filename}</p>
                  <p>Trạng thái {sourceDocument.status}</p>
                  <p className="break-all">SHA256 {sourceDocument.content_hash}</p>
                  {sourceDocument.status === "PARSE_FAILED" && (
                    <button
                      className="secondary-button mt-3"
                      type="button"
                      onClick={async () => {
                        try {
                          const document = await qaApi.retryRequirementDocumentParse(
                            sourceDocument._id,
                            sourceDocument.revision,
                          );
                          setSourceDocument(document);
                          if (document.status !== "READY") {
                            setError("Bộ phân tích vẫn chưa đọc được tệp gốc");
                            return;
                          }
                          const result = await qaApi.extractRequirementDocument(
                            document._id,
                            `source-${document.content_hash}`,
                          );
                          setPreview(result);
                          setSelectedIndexes(result.preview.map((_, index) => index));
                        } catch (reason) {
                          setError(messageOf(reason));
                        }
                      }}
                    >
                      Thử phân tích lại từ tệp gốc
                    </button>
                  )}
                </div>
              )}
            </Panel>
          </div>
        </>
      )}
      {dialog}
    </QaPage>
  );
}
