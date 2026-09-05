"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import DataTable from "../../components/DataTable";
import ReviewCommentsPanel from "../../components/ReviewCommentsPanel";
import CollaborationPanel from "../../components/CollaborationPanel";
import {
  ErrorState,
  LoadingState,
  Pagination,
  Panel,
  ProjectCrumb,
  QaPage,
  StatusPill,
  useQaActionDialog,
} from "../../components/TestingUi";
import { testingApi } from "../../services/testing.service";
import { docText, emptyDoc, messageOf, textDoc, valueLabel } from "../../lib/testing";
import QaDocumentEditor from "../../editor/QaDocumentEditor";
import { Modal, ModalHeader, ModalTitle } from "@/shared/components/ui/Modal";

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

function splitBlocks(value) {
  return value
    .split(/\n\s*---\s*\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function acceptanceCriteria(value) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item, index) => ({
      key: `AC-${index + 1}`,
      content_doc: textDoc(item),
      status: "draft",
    }));
}

export default function RequirementsPage({ project, section }) {
  const { ask, dialog } = useQaActionDialog();
  const requirementId = section[0] && !["new", "import"].includes(section[0]) ? section[0] : "";
  const [items, setItems] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [selected, setSelected] = useState(null);
  const [versions, setVersions] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({
    status: "",
    coverage: "",
    tag: "",
    owner: "",
    sort: "-updated_at",
  });
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
  const [sourceDocuments, setSourceDocuments] = useState([]);
  const [draft, setDraft] = useState(null);
  const [draftDirty, setDraftDirty] = useState(false);
  const [saveState, setSaveState] = useState("saved");
  const draftSequence = useRef(0);
  const loadedVersion = useRef("");
  const [comparison, setComparison] = useState(null);
  const [duplicateScan, setDuplicateScan] = useState(null);
  const [compareFrom, setCompareFrom] = useState("");
  const [compareTo, setCompareTo] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const values = await testingApi.listRequirementPage(project._id, {
        q: query,
        ...filters,
        page,
        page_size: 50,
      });
      setItems(values.items);
      setPageInfo(values);
      if (project.current_permissions?.includes("requirement_document.read")) {
        setSourceDocuments(await testingApi.listRequirementDocuments(project._id));
      }
      if (requirementId) {
        const detail = await testingApi.getRequirement(requirementId);
        setSelected(detail);
        const history = await testingApi.listRequirementVersions(requirementId);
        setVersions(history);
        setCompareFrom(history[1]?._id || history[0]?._id || "");
        setCompareTo(history[0]?._id || "");
      }
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setLoading(false);
    }
  }, [filters, page, project._id, project.current_permissions, query, requirementId]);
  const can = useCallback(
    (permission) => project.current_permissions?.includes(permission),
    [project.current_permissions],
  );
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
        const result = await testingApi.applyRequirementCollaborationOperation(
          project._id,
          selected._id,
          {
            base_revision: current.revision,
            operation_id: crypto.randomUUID(),
            changes: {
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
              actors: snapshot.actors
                .split(",")
                .map((value) => value.trim())
                .filter(Boolean),
              dependencies: snapshot.dependencies
                .split("\n")
                .map((value) => value.trim())
                .filter(Boolean),
              tags: snapshot.tags
                .split(",")
                .map((value) => value.trim())
                .filter(Boolean),
              owner_id: snapshot.ownerId.trim() || null,
            },
          },
        );
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
    if (saving) return;
    setSaving(true);
    setError("");
    try {
      await testingApi.createRequirement(project._id, {
        title: form.title,
        type: form.type,
        priority: form.priority,
        risk: form.risk,
        content_doc: form.content_doc,
        acceptance_criteria: criteria,
        business_rules: form.businessRules
          .split("\n")
          .map((value) => value.trim())
          .filter(Boolean),
        actors: form.actors
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
        dependencies: form.dependencies
          .split("\n")
          .map((value) => value.trim())
          .filter(Boolean),
        source_refs: [],
        tags: form.tags
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
        owner_id: form.ownerId.trim() || null,
      });
      setForm(initialForm);
      setCreating(false);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setSaving(false);
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
        await testingApi.submitRequirementReview(project._id, selected._id, payload);
      } else if (action === "changes") {
        await testingApi.requestRequirementChanges(project._id, selected._id, payload);
      } else {
        await testingApi.approveRequirement(project._id, selected._id, payload);
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
      await testingApi.createRequirementVersion(selected._id, {
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
      const document = await testingApi.createRequirementDocument(project._id, importValue);
      setSourceDocument(document);
      const result = await testingApi.extractRequirementDocument(
        document._id,
        `source-${document.content_hash}`,
      );
      setPreview(result);
      setSelectedIndexes(result.preview.map((_, index) => index));
      setSourceDocument(await testingApi.getRequirementDocument(document._id));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const confirmImport = async () => {
    try {
      await testingApi.confirmRequirementImport(preview._id, selectedIndexes, preview.revision);
      setPreview(null);
      setSelectedIndexes([]);
      setImporting(false);
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
      const document = await testingApi.uploadRequirementDocument(project._id, upload, format);
      setSourceDocument(document);
      if (document.status === "PARSE_FAILED") {
        setPreview(null);
        setError("Tệp gốc đã được lưu nhưng bộ phân tích không đọc được nội dung");
        return;
      }
      const result = await testingApi.extractRequirementDocument(
        document._id,
        `source-${document.content_hash}`,
      );
      setPreview(result);
      setSelectedIndexes(result.preview.map((_, index) => index));
      setSourceDocument(await testingApi.getRequirementDocument(document._id));
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
      const result = await testingApi.updateRequirementImport(preview._id, {
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
      title: candidates
        .map((candidate) => candidate.title)
        .join(" và ")
        .slice(0, 300),
      content_doc: textDoc(
        candidates.map((candidate) => docText(candidate.content_doc)).join("\n\n"),
      ),
      acceptance_criteria: candidates.flatMap((candidate) => candidate.acceptance_criteria || []),
      business_rules: [
        ...new Set(candidates.flatMap((candidate) => candidate.business_rules || [])),
      ],
      actors: [...new Set(candidates.flatMap((candidate) => candidate.actors || []))],
      dependencies: [...new Set(candidates.flatMap((candidate) => candidate.dependencies || []))],
      source_refs: candidates.flatMap((candidate) => candidate.source_refs || []),
      extraction_confidence: Math.min(
        ...candidates.map((candidate) => candidate.extraction_confidence ?? 1),
      ),
      candidate_relation: "merged",
    };
    try {
      const result = await testingApi.mergeRequirementCandidates(preview._id, {
        expected_revision: preview.revision,
        candidate_ids: candidates.map((candidate) => candidate.candidate_id),
        merged,
        reason: "Gộp các ứng viên yêu cầu",
      });
      setPreview(result);
      setSelectedIndexes([firstIndex]);
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const splitCandidate = async () => {
    if (selectedIndexes.length !== 1) {
      setError("Cần chọn đúng một ứng viên để tách");
      return;
    }
    const index = selectedIndexes[0];
    const candidate = preview.preview[index];
    const sourceText = docText(candidate.content_doc).trim();
    let parts = sourceText
      .split(/\n+/)
      .map((part) => part.trim())
      .filter(Boolean);
    if (parts.length < 2) {
      parts = (sourceText.match(/[^.!?;]+[.!?;]?/g) || [])
        .map((part) => part.trim())
        .filter(Boolean);
    }
    if (parts.length < 2) {
      setError("Nội dung cần ít nhất hai dòng hoặc hai câu để tách");
      return;
    }
    const split = parts.map((part) => ({
      ...candidate,
      title: part.slice(0, 300),
      content_doc: textDoc(part),
    }));
    try {
      const result = await testingApi.splitRequirementCandidate(
        preview._id,
        candidate.candidate_id,
        {
          expected_revision: preview.revision,
          drafts: split,
          reason: "Tách ứng viên yêu cầu",
        },
      );
      setPreview(result);
      setSelectedIndexes(split.map((_, offset) => index + offset));
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const rejectCandidate = async () => {
    if (selectedIndexes.length !== 1) {
      setError("Cần chọn đúng một ứng viên để từ chối");
      return;
    }
    const index = selectedIndexes[0];
    const candidate = preview.preview[index];
    const answer = await ask({
      title: "Từ chối ứng viên yêu cầu",
      description: candidate.title,
      confirmLabel: "Từ chối ứng viên",
      danger: true,
      fields: [
        {
          name: "reason",
          label: "Lý do",
          initialValue: "Không thuộc phạm vi hoặc không tạo thành yêu cầu độc lập",
          multiline: true,
          autoFocus: true,
        },
      ],
    });
    if (!answer) return;
    try {
      const result = await testingApi.rejectRequirementCandidate(
        preview._id,
        candidate.candidate_id,
        { expected_revision: preview.revision, reason: answer.reason },
      );
      setPreview(result);
      setSelectedIndexes([]);
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const splitBaseline = async () => {
    const sourceText = docText(current.content_doc).trim();
    let defaultParts = sourceText
      .split(/\n+/)
      .map((item) => item.trim())
      .filter(Boolean);
    if (defaultParts.length < 2) {
      defaultParts = (sourceText.match(/[^.!?;]+[.!?;]?/g) || [])
        .map((item) => item.trim())
        .filter(Boolean);
    }
    if (defaultParts.length < 2) {
      defaultParts = [sourceText, "Nội dung yêu cầu mới cần hoàn thiện"];
    }
    const currentCriteria = (current.acceptance_criteria || []).map((item) =>
      docText(item.content_doc),
    );
    const answer = await ask({
      title: "Tách yêu cầu đã phê duyệt",
      description: `${selected.requirement_key} sẽ chuyển sang trạng thái được thay thế và các phần mới được tạo dưới dạng bản nháp`,
      confirmLabel: "Xác nhận tách",
      fields: [
        {
          name: "titles",
          label: "Tên các yêu cầu mới mỗi dòng một tên",
          initialValue: defaultParts.map((item) => item.slice(0, 120)).join("\n"),
          required: true,
          multiline: true,
          autoFocus: true,
        },
        {
          name: "contents",
          label: "Nội dung từng yêu cầu phân cách bằng một dòng ---",
          initialValue: defaultParts.join("\n---\n"),
          required: true,
          multiline: true,
        },
        {
          name: "acceptance",
          label: "Tiêu chí từng yêu cầu phân cách bằng một dòng ---",
          initialValue: defaultParts
            .map(
              (_, index) =>
                currentCriteria[index] || currentCriteria[0] || "Cần bổ sung tiêu chí chấp nhận",
            )
            .join("\n---\n"),
          required: true,
          multiline: true,
        },
        {
          name: "reason",
          label: "Lý do tách",
          initialValue: "Tách các trách nhiệm nghiệp vụ độc lập để quản lý và truy vết chính xác",
          required: true,
          multiline: true,
        },
      ],
    });
    if (!answer) return;
    const titles = answer.titles
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean);
    const contents = splitBlocks(answer.contents);
    const criteriaBlocks = splitBlocks(answer.acceptance);
    if (
      contents.length < 2 ||
      titles.length !== contents.length ||
      criteriaBlocks.length !== contents.length
    ) {
      setError("Số tên nội dung và nhóm tiêu chí phải bằng nhau và có ít nhất hai phần");
      return;
    }
    try {
      const result = await testingApi.splitRequirement(project._id, selected._id, {
        expected_source_version_id: current._id,
        idempotency_key: crypto.randomUUID(),
        reason: answer.reason,
        drafts: contents.map((content, index) => ({
          title: titles[index],
          type: current.type,
          priority: current.priority,
          risk: current.risk,
          content_doc: textDoc(content),
          acceptance_criteria: acceptanceCriteria(criteriaBlocks[index]),
          business_rules: current.business_rules || [],
          actors: current.actors || [],
          dependencies: current.dependencies || [],
          source_refs: [],
          tags: selected.tags || current.tags || [],
          owner_id: selected.owner_id || current.owner_id || null,
        })),
      });
      const first = result.requirements?.[0];
      window.location.assign(
        first ? `/du-an/${project._id}/yeu-cau/${first._id}` : `/du-an/${project._id}/yeu-cau`,
      );
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const mergeBaselines = async () => {
    const sourceSummaries = items.filter((item) => selectedIds.includes(item._id));
    if (sourceSummaries.length < 2) {
      setError("Cần chọn ít nhất hai yêu cầu để gộp");
      return;
    }
    if (sourceSummaries.some((item) => item.status !== "BASELINED")) {
      setError("Chỉ có thể gộp các yêu cầu đã phê duyệt hiện hành");
      return;
    }
    let sources;
    try {
      sources = await Promise.all(
        sourceSummaries.map((item) => testingApi.getRequirement(item._id)),
      );
    } catch (reason) {
      setError(messageOf(reason));
      return;
    }
    if (sources.some((item) => item.current_version?.status !== "BASELINED")) {
      setError("Một yêu cầu đã thay đổi sau khi danh sách được tải vui lòng tải lại và chọn lại");
      return;
    }
    const answer = await ask({
      title: "Gộp các yêu cầu đã phê duyệt",
      description: `${sources.map((item) => item.requirement_key).join(", ")} sẽ được giữ lịch sử và chuyển sang trạng thái được thay thế`,
      confirmLabel: "Xác nhận gộp",
      fields: [
        {
          name: "title",
          label: "Tên yêu cầu hợp nhất",
          initialValue: sources
            .map((item) => item.current_version.title)
            .join(" và ")
            .slice(0, 300),
          required: true,
          autoFocus: true,
        },
        {
          name: "content",
          label: "Nội dung hợp nhất",
          initialValue: sources
            .map((item) => docText(item.current_version.content_doc))
            .join("\n\n"),
          required: true,
          multiline: true,
        },
        {
          name: "acceptance",
          label: "Tiêu chí chấp nhận mỗi dòng một điều kiện",
          initialValue: sources
            .flatMap((item) => item.current_version.acceptance_criteria || [])
            .map((item) => docText(item.content_doc))
            .join("\n"),
          required: true,
          multiline: true,
        },
        {
          name: "type",
          label: "Loại yêu cầu",
          initialValue: sources[0].current_version.type,
          options: [
            { value: "functional", label: "Chức năng" },
            { value: "non_functional", label: "Phi chức năng" },
            { value: "business_rule", label: "Quy tắc nghiệp vụ" },
            { value: "api", label: "API" },
            { value: "ui", label: "Giao diện" },
            { value: "data", label: "Dữ liệu" },
            { value: "permission", label: "Phân quyền" },
            { value: "integration", label: "Tích hợp" },
            { value: "constraint", label: "Ràng buộc" },
          ],
        },
        {
          name: "reason",
          label: "Lý do gộp",
          initialValue: "Hợp nhất các yêu cầu trùng hoặc cùng một trách nhiệm nghiệp vụ",
          required: true,
          multiline: true,
        },
      ],
    });
    if (!answer) return;
    try {
      const result = await testingApi.mergeRequirements(project._id, {
        source_requirement_ids: sources.map((item) => item._id),
        expected_source_version_ids: Object.fromEntries(
          sources.map((item) => [item._id, item.current_version_id]),
        ),
        idempotency_key: crypto.randomUUID(),
        reason: answer.reason,
        draft: {
          title: answer.title,
          type: answer.type,
          priority: sources[0].current_version.priority,
          risk: sources[0].current_version.risk,
          content_doc: textDoc(answer.content),
          acceptance_criteria: acceptanceCriteria(answer.acceptance),
          business_rules: [
            ...new Set(sources.flatMap((item) => item.current_version.business_rules || [])),
          ],
          actors: [...new Set(sources.flatMap((item) => item.current_version.actors || []))],
          dependencies: [
            ...new Set(sources.flatMap((item) => item.current_version.dependencies || [])),
          ],
          source_refs: [],
          tags: [
            ...new Set(sources.flatMap((item) => item.tags || item.current_version.tags || [])),
          ],
          owner_id: sources[0].owner_id || sources[0].current_version.owner_id || null,
        },
      });
      setSelectedIds([]);
      const merged = result.requirements?.[0];
      window.location.assign(
        merged ? `/du-an/${project._id}/yeu-cau/${merged._id}` : `/du-an/${project._id}/yeu-cau`,
      );
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const scanDuplicates = async () => {
    if (selectedIds.length === 1) {
      setError("Chọn ít nhất hai yêu cầu hoặc bỏ chọn để kiểm tra toàn bộ dự án");
      return;
    }
    try {
      setDuplicateScan(
        await testingApi.findDuplicateRequirements(project._id, {
          requirement_ids: selectedIds,
          threshold: 0.72,
          limit: 100,
        }),
      );
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <QaPage
      title={selected ? `${selected.requirement_key} ${current?.title || ""}` : "Yêu cầu"}
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <ProjectCrumb projectId={project._id} />
          {!selected && can("requirement_document.upload") && (
            <button
              type="button"
              className="secondary-button"
              onClick={() => {
                setError("");
                setImporting(true);
              }}
            >
              Nhập tài liệu
            </button>
          )}
          {!selected && can("requirement.create") && (
            <button
              type="button"
              className="apple-button"
              onClick={() => {
                setError("");
                setCreating(true);
              }}
            >
              Tạo yêu cầu
            </button>
          )}
        </div>
      }
    >
      {error && <ErrorState message={error} />}
      {selected ? (
        <>
          <Panel
            title="Phiên bản hiện tại"
            actions={
              <div className="flex flex-wrap gap-2">
                {can("ai.run_lint") && (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={async () => {
                      try {
                        setLint(await testingApi.lintRequirement(current._id));
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    Kiểm tra chất lượng bằng AI
                  </button>
                )}
                {current.status === "BASELINED" && can("requirement.version.create") && (
                  <button className="secondary-button" type="button" onClick={createVersion}>
                    Tạo phiên bản mới
                  </button>
                )}
                {current.status === "BASELINED" && can("requirement.split") && (
                  <button className="secondary-button" type="button" onClick={splitBaseline}>
                    Tách yêu cầu
                  </button>
                )}
                {current.status !== "OBSOLETE" && can("requirement.archive") && (
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
                        await testingApi.obsoleteRequirement(selected._id, {
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
                {current.status === "OBSOLETE" && can("requirement.restore") && (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={async () => {
                      const answer = await ask({
                        title: "Khôi phục yêu cầu",
                        description: `${selected.requirement_key} sẽ trở lại trạng thái trước khi bị đánh dấu không còn hiệu lực`,
                        confirmLabel: "Khôi phục",
                        fields: [
                          {
                            name: "reason",
                            label: "Lý do",
                            initialValue: "Yêu cầu tiếp tục thuộc phạm vi sản phẩm",
                            required: true,
                            multiline: true,
                            autoFocus: true,
                          },
                        ],
                      });
                      if (!answer) return;
                      try {
                        await testingApi.restoreRequirement(selected._id, {
                          expected_current_version_id: selected.current_version_id,
                          reason: answer.reason,
                        });
                        await load();
                      } catch (value) {
                        setError(messageOf(value));
                      }
                    }}
                  >
                    Khôi phục yêu cầu
                  </button>
                )}
                {current.status === "DRAFT" && can("requirement.submit_review") && (
                  <button className="apple-button" type="button" onClick={() => review("submit")}>
                    Gửi rà soát
                  </button>
                )}
                {current.status === "IN_REVIEW" && can("requirement.review") && (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => review("changes")}
                  >
                    Yêu cầu chỉnh sửa
                  </button>
                )}
                {current.status === "IN_REVIEW" && can("requirement.approve") && (
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
              {current.status === "DRAFT" && draft && can("requirement.update") ? (
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
                      {["critical", "high", "medium", "low"].map((value) => (
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
                      {["critical", "high", "medium", "low"].map((value) => (
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
                empty="Không có vấn đề"
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
                        await testingApi.compareRequirement(selected._id, compareFrom, compareTo),
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
                      await testingApi.createChangeSet(selected._id, {
                        from_version_id: compareFrom,
                        to_version_id: compareTo,
                      });
                      window.location.assign(`/du-an/${project._id}/thay-doi`);
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
                  {
                    key: "type",
                    label: "Loại thay đổi",
                    render: (item) => valueLabel(item.type),
                  },
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
          <CollaborationPanel
            project={project}
            artifactType="requirement"
            artifactId={selected._id}
            onResolved={load}
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
                  {selectedIds.length > 0 && can("requirement.update") && (
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={async () => {
                        const answer = await ask({
                          title: "Cập nhật nhãn hàng loạt",
                          description: `${selectedIds.length} yêu cầu đã chọn`,
                          confirmLabel: "Cập nhật nhãn",
                          fields: [
                            {
                              name: "add",
                              label: "Nhãn cần thêm phân cách bằng dấu phẩy",
                              autoFocus: true,
                            },
                            { name: "remove", label: "Nhãn cần gỡ phân cách bằng dấu phẩy" },
                          ],
                        });
                        if (!answer) return;
                        try {
                          const splitTags = (value) =>
                            value
                              .split(",")
                              .map((item) => item.trim())
                              .filter(Boolean);
                          await testingApi.bulkTags(project._id, {
                            artifact_type: "requirement",
                            ids: selectedIds,
                            add_tags: splitTags(answer.add),
                            remove_tags: splitTags(answer.remove),
                            idempotency_key: crypto.randomUUID(),
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
                  )}
                  {can("requirement.duplicate_check") && (
                    <button className="secondary-button" type="button" onClick={scanDuplicates}>
                      {selectedIds.length ? "Kiểm tra các mục đã chọn" : "Kiểm tra trùng lặp"}
                    </button>
                  )}
                  {selectedIds.length > 0 && can("requirement.merge") && (
                    <button
                      className="secondary-button"
                      disabled={selectedIds.length < 2}
                      type="button"
                      onClick={mergeBaselines}
                    >
                      Gộp yêu cầu
                    </button>
                  )}
                  {selectedIds.length > 0 && can("requirement.archive") && (
                    <button
                      className="danger-button"
                      type="button"
                      onClick={async () => {
                        const answer = await ask({
                          title: "Lưu trữ yêu cầu hàng loạt",
                          description: `${selectedIds.length} yêu cầu vẫn được giữ toàn bộ lịch sử`,
                          confirmLabel: "Lưu trữ",
                          danger: true,
                          fields: [
                            {
                              name: "reason",
                              label: "Lý do",
                              required: true,
                              multiline: true,
                              autoFocus: true,
                            },
                          ],
                        });
                        if (!answer) return;
                        try {
                          await testingApi.bulkArchive(project._id, {
                            artifact_type: "requirement",
                            ids: selectedIds,
                            reason: answer.reason,
                            idempotency_key: crypto.randomUUID(),
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
                  )}
                </div>
              }
            >
              <details className="border-b border-border p-4">
                <summary className="cursor-pointer text-sm font-medium">
                  Bộ lọc và sắp xếp
                  {[filters.status, filters.coverage, filters.tag, filters.owner].filter(Boolean)
                    .length > 0 && (
                    <span className="ml-2 text-ink-muted">
                      {
                        [filters.status, filters.coverage, filters.tag, filters.owner].filter(
                          Boolean,
                        ).length
                      }{" "}
                      bộ lọc đang dùng
                    </span>
                  )}
                </summary>
                <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
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
                    <option value="SUPERSEDED">Đã được thay thế</option>
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
              </details>
              <DataTable
                onSelect={(item) =>
                  window.location.assign(`/du-an/${project._id}/yeu-cau/${item._id}`)
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
          {duplicateScan && (
            <Panel
              title="Ứng viên yêu cầu trùng lặp"
              actions={
                <span className="text-[12px] text-ink-muted">
                  {duplicateScan.candidate_count} cặp từ thuật toán {duplicateScan.algorithm?.name}
                </span>
              }
            >
              <DataTable
                items={(duplicateScan.candidates || []).map((item, index) => ({
                  ...item,
                  _id: `${item.left_requirement_id}-${item.right_requirement_id}-${index}`,
                }))}
                empty="Không phát hiện cặp yêu cầu vượt ngưỡng trùng lặp"
                columns={[
                  { key: "left_requirement_id", label: "Yêu cầu thứ nhất" },
                  { key: "right_requirement_id", label: "Yêu cầu thứ hai" },
                  {
                    key: "match_type",
                    label: "Loại khớp",
                    render: (item) => valueLabel(item.match_type),
                  },
                  {
                    key: "score",
                    label: "Điểm",
                    render: (item) => `${Math.round(item.score * 100)}%`,
                  },
                  { key: "reasons", label: "Cơ sở", render: (item) => item.reasons.join(" · ") },
                ]}
              />
            </Panel>
          )}
          {can("requirement_document.read") && (
            <Panel title="Kho tài liệu nguồn">
              <DataTable
                items={sourceDocuments}
                empty="Chưa có tài liệu nguồn"
                columns={[
                  { key: "filename", label: "Tên tệp" },
                  { key: "format", label: "Định dạng" },
                  {
                    key: "source_type",
                    label: "Loại nguồn",
                    render: (item) => valueLabel(item.source_type || "reference"),
                  },
                  {
                    key: "authority",
                    label: "Thẩm quyền",
                    render: (item) => valueLabel(item.authority || "reference"),
                  },
                  {
                    key: "subject",
                    label: "Môn và khối",
                    render: (item) =>
                      [item.subject, item.grade].filter(Boolean).join(" · ") || "Chưa khai báo",
                  },
                  {
                    key: "status",
                    label: "Trạng thái",
                    render: (item) => <StatusPill value={item.status} />,
                  },
                  { key: "revision", label: "Phiên bản" },
                  {
                    key: "actions",
                    label: "Thao tác",
                    render: (item) => (
                      <span className="flex flex-wrap gap-2">
                        {can("knowledge.manage") && item.status !== "ARCHIVED" && (
                          <>
                            <button
                              className="secondary-button"
                              type="button"
                              onClick={async () => {
                                const answer = await ask({
                                  title: "Phân loại tài liệu nguồn",
                                  description: item.filename,
                                  confirmLabel: "Lưu metadata",
                                  fields: [
                                    {
                                      name: "title",
                                      label: "Tiêu đề",
                                      initialValue: item.title || item.filename,
                                      required: true,
                                    },
                                    {
                                      name: "source_type",
                                      label: "Loại nguồn",
                                      initialValue: item.source_type || "reference",
                                      options: [
                                        { value: "teacher_material", label: "Tài liệu giáo viên" },
                                        {
                                          value: "official_textbook",
                                          label: "Sách giáo khoa chính thức",
                                        },
                                        { value: "curriculum", label: "Chương trình học" },
                                        { value: "reference", label: "Tài liệu tham khảo" },
                                        { value: "api_contract", label: "Đặc tả API" },
                                        { value: "other", label: "Nguồn khác" },
                                      ],
                                    },
                                    {
                                      name: "authority",
                                      label: "Mức thẩm quyền",
                                      initialValue: item.authority || "reference",
                                      options: [
                                        { value: "teacher", label: "Giáo viên" },
                                        { value: "official", label: "Chính thức" },
                                        { value: "supplemental", label: "Bổ trợ" },
                                        { value: "reference", label: "Tham khảo" },
                                      ],
                                    },
                                    {
                                      name: "teacher_id",
                                      label: "Mã giáo viên",
                                      initialValue: item.teacher_id || "",
                                    },
                                    {
                                      name: "subject",
                                      label: "Môn học",
                                      initialValue: item.subject || "",
                                    },
                                    {
                                      name: "grade",
                                      label: "Khối lớp",
                                      initialValue: item.grade || "",
                                    },
                                    {
                                      name: "tags",
                                      label: "Nhãn phân cách bằng dấu phẩy",
                                      initialValue: (item.tags || []).join(", "),
                                    },
                                  ],
                                });
                                if (!answer) return;
                                try {
                                  await testingApi.updateRequirementDocument(item._id, {
                                    expected_revision: item.revision,
                                    title: answer.title,
                                    source_type: answer.source_type,
                                    authority: answer.authority,
                                    teacher_id: answer.teacher_id || null,
                                    subject: answer.subject || null,
                                    grade: answer.grade || null,
                                    tags: answer.tags
                                      .split(",")
                                      .map((value) => value.trim())
                                      .filter(Boolean),
                                  });
                                  await load();
                                } catch (reason) {
                                  setError(messageOf(reason));
                                }
                              }}
                            >
                              Phân loại
                            </button>
                            <button
                              className="secondary-button"
                              type="button"
                              onClick={async () => {
                                try {
                                  await testingApi.reindexRequirementDocument(item._id);
                                  await load();
                                } catch (reason) {
                                  setError(messageOf(reason));
                                }
                              }}
                            >
                              Lập chỉ mục lại
                            </button>
                          </>
                        )}
                        {can("requirement_document.download") && (
                          <button
                            className="secondary-button"
                            type="button"
                            onClick={async () => {
                              try {
                                await testingApi.downloadRequirementDocument(
                                  item._id,
                                  item.filename,
                                );
                              } catch (reason) {
                                setError(messageOf(reason));
                              }
                            }}
                          >
                            Tải xuống
                          </button>
                        )}
                        {item.status === "ARCHIVED"
                          ? can("requirement_document.restore") && (
                              <button
                                className="secondary-button"
                                type="button"
                                onClick={async () => {
                                  const answer = await ask({
                                    title: "Khôi phục tài liệu nguồn",
                                    description: item.filename,
                                    confirmLabel: "Khôi phục",
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
                                    await testingApi.restoreRequirementDocument(item._id, {
                                      expected_revision: item.revision,
                                      reason: answer.reason,
                                    });
                                    await load();
                                  } catch (reason) {
                                    setError(messageOf(reason));
                                  }
                                }}
                              >
                                Khôi phục
                              </button>
                            )
                          : can("requirement_document.archive") && (
                              <button
                                className="secondary-button"
                                type="button"
                                onClick={async () => {
                                  const answer = await ask({
                                    title: "Lưu trữ tài liệu nguồn",
                                    description: item.filename,
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
                                    await testingApi.archiveRequirementDocument(item._id, {
                                      expected_revision: item.revision,
                                      reason: answer.reason,
                                    });
                                    await load();
                                  } catch (reason) {
                                    setError(messageOf(reason));
                                  }
                                }}
                              >
                                Lưu trữ
                              </button>
                            )}
                      </span>
                    ),
                  },
                ]}
              />
            </Panel>
          )}
          <div className="grid gap-5 xl:grid-cols-2">
            {can("requirement.create") && (
              <Modal
                isOpen={creating}
                onClose={() => {
                  if (!saving) setCreating(false);
                }}
                ariaLabel="Tạo yêu cầu"
                className="max-w-3xl max-h-[90dvh] overflow-y-auto"
              >
                <ModalHeader>
                  <ModalTitle>Tạo yêu cầu</ModalTitle>
                </ModalHeader>
                {error && (
                  <div className="px-5 pt-4">
                    <ErrorState message={error} />
                  </div>
                )}
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
                  <div className="flex justify-end gap-3">
                    <button
                      className="secondary-button"
                      type="button"
                      disabled={saving}
                      onClick={() => setCreating(false)}
                    >
                      Hủy
                    </button>
                    <button className="apple-button" type="submit" disabled={saving}>
                      {saving ? "Đang lưu" : "Lưu yêu cầu"}
                    </button>
                  </div>
                </form>
              </Modal>
            )}
            {can("requirement_document.upload") && (
              <Modal
                isOpen={importing}
                onClose={() => setImporting(false)}
                ariaLabel="Nhập tài liệu"
                className="max-w-5xl max-h-[90dvh] overflow-y-auto"
              >
                <ModalHeader>
                  <ModalTitle>Nhập tài liệu</ModalTitle>
                </ModalHeader>
                {error && <ErrorState message={error} />}
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
                          <button
                            className="secondary-button"
                            type="button"
                            onClick={splitCandidate}
                          >
                            Tách mục đã chọn
                          </button>
                          <button
                            className="secondary-button"
                            type="button"
                            onClick={mergeCandidates}
                          >
                            Gộp các mục đã chọn
                          </button>
                          <button className="danger-button" type="button" onClick={rejectCandidate}>
                            Từ chối mục đã chọn
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
                                    ? [...values, item.candidateIndex].sort(
                                        (left, right) => left - right,
                                      )
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
                        {
                          key: "type",
                          label: "Loại",
                          render: (item) => valueLabel(item.type),
                        },
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
                          {preview.preview.length - selectedIndexes.length} ứng viên bị loại sẽ
                          không được ghi
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
                            const document = await testingApi.retryRequirementDocumentParse(
                              sourceDocument._id,
                              sourceDocument.revision,
                            );
                            setSourceDocument(document);
                            if (document.status !== "READY") {
                              setError("Bộ phân tích vẫn chưa đọc được tệp gốc");
                              return;
                            }
                            const result = await testingApi.extractRequirementDocument(
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
              </Modal>
            )}
          </div>
        </>
      )}
      {dialog}
    </QaPage>
  );
}
