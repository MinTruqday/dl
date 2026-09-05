"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { uploadAssetAPI } from "@/features/cloud/services/upload.service";
import DataTable from "../../components/DataTable";
import ReviewCommentsPanel from "../../components/ReviewCommentsPanel";
import TestCaseTemplatesPanel from "../../components/TestCaseTemplatesPanel";
import SpecializedDesignPanel from "../../components/SpecializedDesignPanel";
import AutomationScriptsPanel from "../../components/AutomationScriptsPanel";
import CollaborationPanel from "../../components/CollaborationPanel";
import {
  ErrorState,
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

export default function TestDesignPage({ project }) {
  const { ask, dialog } = useQaActionDialog();
  const [requirements, setRequirements] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [dataSets, setDataSets] = useState([]);
  const [drafts, setDrafts] = useState([]);
  const [tests, setTests] = useState([]);
  const [suites, setSuites] = useState([]);
  const [selectedTestIds, setSelectedTestIds] = useState([]);
  const [testPage, setTestPage] = useState(1);
  const [testPageInfo, setTestPageInfo] = useState(null);
  const [testFilters, setTestFilters] = useState({
    q: "",
    status: "",
    priority: "",
    stale_status: "",
    automation_status: "",
    sort: "-updated_at",
  });
  const [scenarioFilters, setScenarioFilters] = useState({
    q: "",
    category: "",
    risk: "",
    status: "",
    sort: "-updated_at",
  });
  const [duplicates, setDuplicates] = useState([]);
  const [operations, setOperations] = useState([]);
  const [apiArtifacts, setApiArtifacts] = useState([]);
  const [apiCompareFrom, setApiCompareFrom] = useState("");
  const [apiCompareTo, setApiCompareTo] = useState("");
  const [apiDifference, setApiDifference] = useState(null);
  const [testImport, setTestImport] = useState(null);
  const [apiImport, setApiImport] = useState({
    filename: "openapi.json",
    format: "openapi",
    content: "",
  });
  const [selectedRequirement, setSelectedRequirement] = useState("");
  const [selectedDraftId, setSelectedDraftId] = useState("");
  const [selectedTestId, setSelectedTestId] = useState("");
  const [testVersions, setTestVersions] = useState([]);
  const [draftEdit, setDraftEdit] = useState(null);
  const [draftDirty, setDraftDirty] = useState(false);
  const [draftSaveState, setDraftSaveState] = useState("saved");
  const draftSequence = useRef(0);
  const loadedDraft = useRef("");
  const [testLint, setTestLint] = useState(null);
  const [scenarioForm, setScenarioForm] = useState({
    title: "",
    objective: "",
    category: "happy_path",
  });
  const [dataSetForm, setDataSetForm] = useState({
    name: "",
    variables: "{}",
    secretRefs: "{}",
  });
  const [form, setForm] = useState({
    title: "",
    type: "happy_path",
    priority: "medium",
    risk: "medium",
    action: emptyDoc(),
    expected: emptyDoc(),
    dataSetVersionIds: [],
  });
  const [error, setError] = useState("");
  const [creatingTest, setCreatingTest] = useState(false);
  const [creatingScenario, setCreatingScenario] = useState(false);
  const [creatingDataSet, setCreatingDataSet] = useState(false);
  const can = (permission) => project.current_permissions?.includes(permission);
  const canReadTestData = project.current_permissions?.includes("testdata.read");
  const load = useCallback(async () => {
    try {
      const [
        requirementValues,
        scenarioValues,
        dataSetValues,
        draftValues,
        testValues,
        suiteValues,
        apiArtifactValues,
        operationValues,
      ] = await Promise.all([
        testingApi.listRequirements(project._id, { page_size: 500, status: "BASELINED" }),
        testingApi.listScenarios(project._id, scenarioFilters),
        canReadTestData ? testingApi.listDataSets(project._id) : Promise.resolve([]),
        testingApi.listTestDrafts(project._id),
        testingApi.listTestCasePage(project._id, {
          ...testFilters,
          page: testPage,
          page_size: 50,
        }),
        testingApi.listSuites(project._id),
        testingApi.listApiArtifacts(project._id),
        testingApi.listApiOperations(project._id),
      ]);
      setRequirements(requirementValues);
      setScenarios(scenarioValues);
      setDataSets(dataSetValues);
      setDrafts(draftValues);
      setTests(testValues.items);
      setTestPageInfo(testValues);
      setSuites(suiteValues);
      setApiArtifacts(apiArtifactValues);
      const confirmedArtifacts = apiArtifactValues.filter((item) => item.status === "CONFIRMED");
      setApiCompareFrom((current) =>
        confirmedArtifacts.some((item) => item._id === current)
          ? current
          : confirmedArtifacts[1]?._id || "",
      );
      setApiCompareTo((current) =>
        confirmedArtifacts.some((item) => item._id === current)
          ? current
          : confirmedArtifacts[0]?._id || "",
      );
      setOperations(operationValues);
      setSelectedRequirement(
        (current) => current || requirementValues[0]?.current_version_id || "",
      );
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [canReadTestData, project._id, scenarioFilters, testFilters, testPage]);
  useEffect(() => {
    void load();
  }, [load]);
  const selectedDraft = drafts.find((item) => item._id === selectedDraftId) || null;
  useEffect(() => {
    if (!selectedDraft) {
      loadedDraft.current = "";
      setDraftEdit(null);
      setTestLint(null);
      return;
    }
    if (loadedDraft.current === selectedDraft._id) return;
    loadedDraft.current = selectedDraft._id;
    setTestLint(null);
    setDraftEdit({
      title: selectedDraft.title,
      type: selectedDraft.type,
      priority: selectedDraft.priority,
      risk: selectedDraft.risk,
      objective: docText(selectedDraft.objective_doc),
      preconditions: docText(selectedDraft.preconditions_doc),
      steps: (selectedDraft.steps || []).map((step) => ({
        id: step.id,
        action: docText(step.action_doc),
        data: JSON.stringify(step.test_data || {}, null, 2),
        expected: docText(step.expected_doc),
      })),
      testData: JSON.stringify(selectedDraft.test_data || {}, null, 2),
      expected: docText(selectedDraft.expected_result_doc),
      postconditions: docText(selectedDraft.postconditions_doc),
      techniques: (selectedDraft.techniques || []).join(", "),
      tags: (selectedDraft.tags || []).join(", "),
      ownerId: selectedDraft.owner_id || "",
      automationStatus: selectedDraft.automation_status || "manual",
      attachments: selectedDraft.attachments || [],
      dataSetVersionIds: selectedDraft.data_set_version_ids || [],
    });
    setDraftDirty(false);
    setDraftSaveState("saved");
  }, [selectedDraft]);
  const changeDraftEdit = (next) => {
    draftSequence.current += 1;
    setDraftEdit((value) => (typeof next === "function" ? next(value) : { ...value, ...next }));
    setDraftDirty(true);
    setDraftSaveState("pending");
  };
  const create = async (event) => {
    event.preventDefault();
    try {
      await testingApi.createTestDraft(project._id, {
        title: form.title,
        type: form.type,
        priority: form.priority,
        risk: form.risk,
        objective_doc: textDoc(form.title),
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
        techniques: [],
        automation_status: "manual",
        attachments: [],
        data_set_version_ids: form.dataSetVersionIds,
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
        dataSetVersionIds: [],
      });
      setCreatingTest(false);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const createScenario = async (event) => {
    event.preventDefault();
    try {
      await testingApi.createScenario(project._id, {
        title: scenarioForm.title,
        objective: scenarioForm.objective,
        category: scenarioForm.category,
        risk: "medium",
        priority: "medium",
        requirement_version_ids: selectedRequirement ? [selectedRequirement] : [],
        acceptance_criterion_ids: [],
        status: "draft",
        origin: "manual",
      });
      setScenarioForm({ title: "", objective: "", category: "happy_path" });
      setCreatingScenario(false);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const createDataSet = async (event) => {
    event.preventDefault();
    try {
      await testingApi.createDataSet(project._id, {
        name: dataSetForm.name,
        variables: JSON.parse(dataSetForm.variables || "{}"),
        secret_refs: JSON.parse(dataSetForm.secretRefs || "{}"),
      });
      setDataSetForm({ name: "", variables: "{}", secretRefs: "{}" });
      setCreatingDataSet(false);
      await load();
    } catch (reason) {
      setError(
        reason instanceof SyntaxError ? "Bộ dữ liệu phải là JSON hợp lệ" : messageOf(reason),
      );
    }
  };
  const generate = async () => {
    if (!selectedRequirement) return setError("Cần chọn yêu cầu trước khi tạo ca kiểm thử");
    try {
      await testingApi.generateTestCases(selectedRequirement, {
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
    const answer = await ask({
      title: "Phê duyệt ca kiểm thử",
      description: `${draft.test_case_key} sẽ trở thành phiên bản bất biến và được dùng trong lần chạy`,
      confirmLabel: "Phê duyệt",
    });
    if (!answer) return;
    try {
      await testingApi.freezeTestDraft(
        draft._id,
        draft.revision,
        "Phê duyệt sau rà soát của con người",
      );
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const reviewDraft = async (draft, action) => {
    const answer = await ask({
      title: action === "changes" ? "Yêu cầu chỉnh sửa ca kiểm thử" : "Gửi ca kiểm thử để rà soát",
      description: draft.test_case_key,
      confirmLabel: action === "changes" ? "Yêu cầu chỉnh sửa" : "Gửi rà soát",
      fields: [
        {
          name: "note",
          label: action === "changes" ? "Nội dung cần chỉnh sửa" : "Ghi chú rà soát",
          initialValue:
            action === "changes" ? "Cần cập nhật theo nhận xét" : "Đã rà soát các bước và dữ liệu",
          required: true,
          multiline: true,
          autoFocus: true,
        },
      ],
    });
    if (!answer) return;
    try {
      const payload = { expected_revision: draft.revision, review_note: answer.note };
      if (action === "submit") {
        await testingApi.submitTestCaseReview(project._id, draft._id, payload);
      } else {
        await testingApi.requestTestCaseChanges(project._id, draft._id, payload);
      }
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  const persistDraft = useCallback(
    async (snapshot, sequence) => {
      try {
        const testData = JSON.parse(snapshot.testData || "{}");
        const steps = snapshot.steps.map((step, index) => ({
          id: step.id || crypto.randomUUID(),
          order: index + 1,
          action_doc: textDoc(step.action),
          test_data: JSON.parse(step.data || "{}"),
          expected_doc: textDoc(step.expected),
        }));
        setDraftSaveState("saving");
        const result = await testingApi.applyTestCaseCollaborationOperation(
          project._id,
          selectedDraft._id,
          {
            base_revision: selectedDraft.revision,
            operation_id: crypto.randomUUID(),
            changes: {
              title: snapshot.title,
              type: snapshot.type,
              priority: snapshot.priority,
              risk: snapshot.risk,
              objective_doc: textDoc(snapshot.objective),
              preconditions_doc: textDoc(snapshot.preconditions),
              steps,
              test_data: testData,
              expected_result_doc: textDoc(snapshot.expected),
              postconditions_doc: textDoc(snapshot.postconditions),
              techniques: snapshot.techniques
                .split(",")
                .map((value) => value.trim())
                .filter(Boolean),
              tags: snapshot.tags
                .split(",")
                .map((value) => value.trim())
                .filter(Boolean),
              owner_id: snapshot.ownerId.trim() || null,
              automation_status: snapshot.automationStatus,
              attachments: snapshot.attachments,
              data_set_version_ids: snapshot.dataSetVersionIds,
            },
          },
        );
        setDrafts((values) => values.map((item) => (item._id === result._id ? result : item)));
        if (draftSequence.current === sequence) {
          setDraftDirty(false);
          setDraftSaveState("saved");
        } else {
          setDraftSaveState("pending");
        }
      } catch (reason) {
        setDraftSaveState(reason instanceof SyntaxError ? "invalid" : "error");
        setError(
          reason instanceof SyntaxError
            ? "Dữ liệu kiểm thử phải là JSON hợp lệ"
            : messageOf(reason),
        );
      }
    },
    [project._id, selectedDraft],
  );
  const saveDraft = async () => {
    await persistDraft(draftEdit, draftSequence.current);
  };
  useEffect(() => {
    if (
      !draftDirty ||
      selectedDraft?.status !== "DRAFT" ||
      !draftEdit ||
      !project.current_permissions?.includes("testcase.update")
    )
      return undefined;
    const sequence = draftSequence.current;
    const timer = window.setTimeout(() => {
      void persistDraft(draftEdit, sequence);
    }, 1500);
    return () => window.clearTimeout(timer);
  }, [draftDirty, draftEdit, persistDraft, project.current_permissions, selectedDraft?.status]);
  return (
    <QaPage
      title="Thiết kế kiểm thử"
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <ProjectCrumb projectId={project._id} />
          {can("testcase.create") && (
            <button className="apple-button" type="button" onClick={() => setCreatingTest(true)}>
              Tạo ca kiểm thử
            </button>
          )}
        </div>
      }
    >
      {error && <ErrorState message={error} />}
      {(can("ai.generate_testcase") ||
        can("ai.generate_scenario") ||
        can("testcase.duplicate_check")) && (
        <Panel title="Tạo bằng AI">
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
            {can("ai.generate_testcase") && can("testcase.create") && (
              <button className="apple-button" type="button" onClick={generate}>
                Tạo 4 nhóm ca kiểm thử
              </button>
            )}
            {can("ai.generate_scenario") && can("testscenario.create") && (
              <button
                className="secondary-button"
                type="button"
                onClick={async () => {
                  if (!selectedRequirement) return;
                  try {
                    await testingApi.generateScenarios(selectedRequirement, {
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
            )}
            {can("testcase.duplicate_check") && can("ai.run_duplicate_check") && (
              <button
                className="secondary-button"
                type="button"
                onClick={async () => {
                  try {
                    setDuplicates(await testingApi.findDuplicates(project._id));
                  } catch (reason) {
                    setError(messageOf(reason));
                  }
                }}
              >
                Tìm ca kiểm thử trùng lặp
              </button>
            )}
          </div>
        </Panel>
      )}
      {can("testcase.template.read") && <TestCaseTemplatesPanel project={project} />}
      <SpecializedDesignPanel project={project} requirements={requirements} />
      <AutomationScriptsPanel project={project} tests={tests} />
      <div className="grid gap-5 xl:grid-cols-2">
        <Panel title="Bản nháp ca kiểm thử">
          <DataTable
            onSelect={(item) => setSelectedDraftId(item._id)}
            items={drafts}
            empty="Chưa có bản nháp"
            columns={[
              { key: "test_case_key", label: "Mã" },
              { key: "title", label: "Tên" },
              { key: "type", label: "Loại", render: (item) => valueLabel(item.type) },
              {
                key: "status",
                label: "Trạng thái",
                render: (item) => <StatusPill value={item.status} />,
              },
              {
                key: "action",
                label: "Duyệt",
                render: (item) => (
                  <span className="flex flex-wrap gap-2">
                    {item.status === "DRAFT" && can("testcase.submit_review") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          void reviewDraft(item, "submit");
                        }}
                      >
                        Gửi rà soát
                      </button>
                    )}
                    {item.status === "IN_REVIEW" && can("testcase.review") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          void reviewDraft(item, "changes");
                        }}
                      >
                        Yêu cầu sửa
                      </button>
                    )}
                    {item.status === "IN_REVIEW" && can("testcase.approve") && (
                      <button
                        className="apple-button"
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          void freeze(item);
                        }}
                      >
                        Phê duyệt
                      </button>
                    )}
                  </span>
                ),
              },
            ]}
          />
        </Panel>
        <Panel
          title="Phiên bản ca kiểm thử"
          actions={
            <div className="flex flex-wrap gap-2">
              {selectedTestIds.length > 0 && can("testcase.bulk.update") && (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={async () => {
                    const answer = await ask({
                      title: "Cập nhật nhãn ca kiểm thử",
                      description: `${selectedTestIds.length} ca kiểm thử đã chọn`,
                      confirmLabel: "Cập nhật",
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
                    const splitTags = (value) =>
                      value
                        .split(",")
                        .map((item) => item.trim())
                        .filter(Boolean);
                    try {
                      await testingApi.bulkTags(project._id, {
                        artifact_type: "test_case",
                        ids: selectedTestIds,
                        add_tags: splitTags(answer.add),
                        remove_tags: splitTags(answer.remove),
                        idempotency_key: crypto.randomUUID(),
                      });
                      setSelectedTestIds([]);
                      await load();
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                >
                  Cập nhật nhãn
                </button>
              )}
              {selectedTestIds.length > 0 && can("testcase.bulk.update") && (
                <button
                  className="secondary-button"
                  disabled={!suites.length}
                  type="button"
                  onClick={async () => {
                    const answer = await ask({
                      title: "Thêm vào bộ kiểm thử",
                      description: `${selectedTestIds.length} ca kiểm thử đã chọn`,
                      confirmLabel: "Thêm vào bộ",
                      fields: [
                        {
                          name: "suiteId",
                          label: "Bộ kiểm thử",
                          required: true,
                          autoFocus: true,
                          initialValue: suites[0]?._id || "",
                          options: suites.map((item) => ({ value: item._id, label: item.name })),
                        },
                      ],
                    });
                    if (!answer) return;
                    const suite = suites.find((item) => item._id === answer.suiteId);
                    try {
                      await testingApi.bulkAddToSuite(project._id, {
                        suite_id: answer.suiteId,
                        test_case_ids: selectedTestIds,
                        expected_revision: suite?.revision || 1,
                        idempotency_key: crypto.randomUUID(),
                      });
                      setSelectedTestIds([]);
                      await load();
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                >
                  Thêm vào bộ
                </button>
              )}
              {selectedTestIds.length > 0 && can("testcase.bulk.update") && (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={async () => {
                    const answer = await ask({
                      title: "Đánh dấu cần rà soát",
                      description: `${selectedTestIds.length} ca kiểm thử đã chọn`,
                      confirmLabel: "Đánh dấu",
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
                      await testingApi.bulkMarkReviewRequired(project._id, {
                        test_case_ids: selectedTestIds,
                        reason: answer.reason,
                        idempotency_key: crypto.randomUUID(),
                      });
                      setSelectedTestIds([]);
                      await load();
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                >
                  Cần rà soát
                </button>
              )}
              {selectedTestIds.length > 0 && can("testcase.bulk.archive") && (
                <button
                  className="danger-button"
                  type="button"
                  onClick={async () => {
                    const answer = await ask({
                      title: "Lưu trữ ca kiểm thử",
                      description:
                        "Các ca đang nằm trong lần chạy chưa kết thúc sẽ bị từ chối riêng lẻ",
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
                        artifact_type: "test_case",
                        ids: selectedTestIds,
                        reason: answer.reason,
                        idempotency_key: crypto.randomUUID(),
                      });
                      setSelectedTestIds([]);
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
              Tìm kiếm bộ lọc và sắp xếp
            </summary>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
              <input
                aria-label="Tìm ca kiểm thử"
                className="apple-input xl:col-span-2"
                placeholder="Tìm theo mã hoặc tên"
                value={testFilters.q}
                onChange={(event) => {
                  setTestFilters({ ...testFilters, q: event.target.value });
                  setTestPage(1);
                }}
              />
              <select
                aria-label="Lọc trạng thái ca kiểm thử"
                className="apple-input"
                value={testFilters.status}
                onChange={(event) => {
                  setTestFilters({ ...testFilters, status: event.target.value });
                  setTestPage(1);
                }}
              >
                <option value="">Mọi trạng thái</option>
                <option value="ACTIVE">Đang hoạt động</option>
                <option value="NEEDS_UPDATE">Cần cập nhật</option>
                <option value="OBSOLETE">Không còn hiệu lực</option>
              </select>
              <select
                aria-label="Lọc ưu tiên ca kiểm thử"
                className="apple-input"
                value={testFilters.priority}
                onChange={(event) => {
                  setTestFilters({ ...testFilters, priority: event.target.value });
                  setTestPage(1);
                }}
              >
                <option value="">Mọi ưu tiên</option>
                <option value="critical">Nghiêm trọng</option>
                <option value="high">Cao</option>
                <option value="medium">Trung bình</option>
                <option value="low">Thấp</option>
              </select>
              <select
                aria-label="Lọc độ mới ca kiểm thử"
                className="apple-input"
                value={testFilters.stale_status}
                onChange={(event) => {
                  setTestFilters({ ...testFilters, stale_status: event.target.value });
                  setTestPage(1);
                }}
              >
                <option value="">Mọi độ mới</option>
                <option value="FRESH">Còn phù hợp</option>
                <option value="STALE">Đã lỗi thời</option>
              </select>
              <select
                aria-label="Sắp xếp ca kiểm thử"
                className="apple-input"
                value={testFilters.sort}
                onChange={(event) => {
                  setTestFilters({ ...testFilters, sort: event.target.value });
                  setTestPage(1);
                }}
              >
                <option value="-updated_at">Mới cập nhật</option>
                <option value="updated_at">Cũ cập nhật</option>
                <option value="test_case_key">Mã tăng dần</option>
                <option value="title">Tên tăng dần</option>
              </select>
            </div>
          </details>
          <DataTable
            onSelect={async (item) => {
              setSelectedTestId(item._id);
              try {
                setTestVersions(await testingApi.listTestVersions(item._id));
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
            items={tests}
            selectedIds={
              can("testcase.bulk.update") || can("testcase.bulk.archive")
                ? selectedTestIds
                : undefined
            }
            onSelectionChange={
              can("testcase.bulk.update") || can("testcase.bulk.archive")
                ? setSelectedTestIds
                : undefined
            }
            selectionLabel="Chọn ca kiểm thử"
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
              {
                key: "lifecycle",
                label: "Vòng đời",
                render: (item) => (
                  <span className="flex flex-wrap gap-2">
                    {can("testcase.clone") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={async (event) => {
                          event.stopPropagation();
                          try {
                            await testingApi.cloneTestCase(item._id, {
                              expected_current_version_id: item.current_version_id,
                              title: `${item.current_version?.title || item.test_case_key} bản sao`,
                            });
                            await load();
                          } catch (reasonValue) {
                            setError(messageOf(reasonValue));
                          }
                        }}
                      >
                        Nhân bản
                      </button>
                    )}
                    {item.status !== "OBSOLETE" && can("testcase.bulk.archive") ? (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={async (event) => {
                          event.stopPropagation();
                          const answer = await ask({
                            title: "Đánh dấu ca kiểm thử không còn hiệu lực",
                            description: `${item.test_case_key} vẫn được giữ trong lịch sử phiên bản`,
                            confirmLabel: "Đánh dấu",
                            danger: true,
                            fields: [
                              {
                                name: "reason",
                                label: "Lý do",
                                initialValue: "Hành vi kiểm thử không còn thuộc phạm vi",
                                required: true,
                                multiline: true,
                                autoFocus: true,
                              },
                            ],
                          });
                          if (!answer) return;
                          try {
                            await testingApi.obsoleteTestCase(item._id, {
                              expected_current_version_id: item.current_version_id,
                              reason: answer.reason,
                            });
                            await load();
                            if (selectedTestId === item._id) {
                              setTestVersions(await testingApi.listTestVersions(item._id));
                            }
                          } catch (reasonValue) {
                            setError(messageOf(reasonValue));
                          }
                        }}
                      >
                        Đánh dấu không còn hiệu lực
                      </button>
                    ) : item.status === "OBSOLETE" && can("testcase.restore") ? (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={async (event) => {
                          event.stopPropagation();
                          const answer = await ask({
                            title: "Khôi phục ca kiểm thử",
                            description: `${item.test_case_key} sẽ trở lại trạng thái hoạt động`,
                            confirmLabel: "Khôi phục",
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
                            await testingApi.restoreTestCase(item._id, {
                              expected_current_version_id: item.current_version_id,
                              reason: answer.reason,
                            });
                            await load();
                          } catch (reasonValue) {
                            setError(messageOf(reasonValue));
                          }
                        }}
                      >
                        Khôi phục
                      </button>
                    ) : item.status === "OBSOLETE" ? (
                      <span className="text-[11px] text-ink-muted">Đã lưu lịch sử</span>
                    ) : null}
                  </span>
                ),
              },
            ]}
          />
          <Pagination value={testPageInfo} onChange={setTestPage} />
        </Panel>
      </div>
      {selectedTestId && (
        <Panel title="Lịch sử phiên bản ca kiểm thử">
          <DataTable
            items={testVersions}
            empty="Chưa có phiên bản"
            columns={[
              { key: "test_case_key", label: "Mã" },
              { key: "version", label: "Phiên bản", render: (item) => `v${item.version}` },
              { key: "title", label: "Tên" },
              { key: "change_reason", label: "Lý do thay đổi" },
              {
                key: "status",
                label: "Trạng thái",
                render: (item) => <StatusPill value={item.status} />,
              },
            ]}
          />
        </Panel>
      )}
      {selectedDraft && draftEdit && (
        <>
          <Panel
            title={`Biên tập ${selectedDraft.test_case_key}`}
            actions={
              can("testcase.lint") && can("ai.run_lint") ? (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={async () => {
                    try {
                      setTestLint(await testingApi.lintTestDraft(selectedDraft._id));
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                >
                  Kiểm tra chất lượng
                </button>
              ) : null
            }
          >
            <div className="grid gap-4 p-5 lg:grid-cols-2">
              <label className="field-label lg:col-span-2">
                Tên ca kiểm thử
                <input
                  className="apple-input mt-2"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.title}
                  onChange={(event) => changeDraftEdit({ title: event.target.value })}
                />
              </label>
              <div className="grid gap-3 lg:col-span-2 sm:grid-cols-3">
                <select
                  aria-label="Loại bản nháp ca kiểm thử"
                  className="apple-input"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.type}
                  onChange={(event) => changeDraftEdit({ type: event.target.value })}
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
                  aria-label="Ưu tiên bản nháp ca kiểm thử"
                  className="apple-input"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.priority}
                  onChange={(event) => changeDraftEdit({ priority: event.target.value })}
                >
                  {["critical", "high", "medium", "low"].map((value) => (
                    <option key={value} value={value}>
                      {valueLabel(value)}
                    </option>
                  ))}
                </select>
                <select
                  aria-label="Rủi ro bản nháp ca kiểm thử"
                  className="apple-input"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.risk}
                  onChange={(event) => changeDraftEdit({ risk: event.target.value })}
                >
                  {["critical", "high", "medium", "low"].map((value) => (
                    <option key={value} value={value}>
                      {valueLabel(value)}
                    </option>
                  ))}
                </select>
              </div>
              <label className="field-label lg:col-span-2">
                Mục tiêu kiểm thử
                <textarea
                  className="apple-input mt-2 min-h-20"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.objective}
                  onChange={(event) => changeDraftEdit({ objective: event.target.value })}
                />
              </label>
              <label className="field-label">
                Điều kiện trước
                <textarea
                  className="apple-input mt-2 min-h-24"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.preconditions}
                  onChange={(event) => changeDraftEdit({ preconditions: event.target.value })}
                />
              </label>
              <div className="space-y-4 lg:col-span-2">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="field-label">Các bước kiểm thử</p>
                  {selectedDraft.status === "DRAFT" && can("testcase.update") && (
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() =>
                        changeDraftEdit({
                          steps: [
                            ...draftEdit.steps,
                            { id: crypto.randomUUID(), action: "", data: "{}", expected: "" },
                          ],
                        })
                      }
                    >
                      Thêm bước
                    </button>
                  )}
                </div>
                {draftEdit.steps.map((step, index) => (
                  <fieldset
                    className="grid gap-3 rounded-xl border border-border p-4 lg:grid-cols-2"
                    key={step.id}
                  >
                    <legend className="px-2 text-[12px] font-semibold">Bước {index + 1}</legend>
                    <label className="field-label">
                      Thao tác
                      <textarea
                        className="apple-input mt-2 min-h-24"
                        disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                        value={step.action}
                        onChange={(event) => {
                          const steps = [...draftEdit.steps];
                          steps[index] = { ...step, action: event.target.value };
                          changeDraftEdit({ steps });
                        }}
                      />
                    </label>
                    <label className="field-label">
                      Kết quả mong đợi
                      <textarea
                        className="apple-input mt-2 min-h-24"
                        disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                        value={step.expected}
                        onChange={(event) => {
                          const steps = [...draftEdit.steps];
                          steps[index] = { ...step, expected: event.target.value };
                          changeDraftEdit({ steps });
                        }}
                      />
                    </label>
                    <label className="field-label lg:col-span-2">
                      Dữ liệu dạng JSON
                      <textarea
                        className="apple-input mt-2 min-h-24 font-mono"
                        disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                        value={step.data}
                        onChange={(event) => {
                          const steps = [...draftEdit.steps];
                          steps[index] = { ...step, data: event.target.value };
                          changeDraftEdit({ steps });
                        }}
                      />
                    </label>
                    {selectedDraft.status === "DRAFT" &&
                      can("testcase.update") &&
                      draftEdit.steps.length > 1 && (
                        <button
                          className="secondary-button w-fit"
                          type="button"
                          onClick={() =>
                            changeDraftEdit({
                              steps: draftEdit.steps.filter((_, stepIndex) => stepIndex !== index),
                            })
                          }
                        >
                          Xóa bước
                        </button>
                      )}
                  </fieldset>
                ))}
              </div>
              <label className="field-label">
                Dữ liệu dùng chung dạng JSON
                <textarea
                  className="apple-input mt-2 min-h-28 font-mono"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.testData}
                  onChange={(event) => changeDraftEdit({ testData: event.target.value })}
                />
              </label>
              <label className="field-label">
                Phiên bản bộ dữ liệu tham số
                <select
                  aria-label="Phiên bản bộ dữ liệu của bản nháp"
                  className="apple-input mt-2 min-h-28"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  multiple
                  value={draftEdit.dataSetVersionIds}
                  onChange={(event) =>
                    changeDraftEdit({
                      dataSetVersionIds: Array.from(
                        event.target.selectedOptions,
                        (option) => option.value,
                      ),
                    })
                  }
                >
                  {dataSets.map((item) => (
                    <option key={item.current_version_id} value={item.current_version_id}>
                      {item.name} v{item.current_version?.version}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field-label">
                Kết quả mong đợi tổng thể
                <textarea
                  className="apple-input mt-2 min-h-28"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.expected}
                  onChange={(event) => changeDraftEdit({ expected: event.target.value })}
                />
              </label>
              <label className="field-label lg:col-span-2">
                Điều kiện sau
                <textarea
                  className="apple-input mt-2 min-h-24"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.postconditions}
                  onChange={(event) => changeDraftEdit({ postconditions: event.target.value })}
                />
              </label>
              <label className="field-label">
                Kỹ thuật kiểm thử phân tách bằng dấu phẩy
                <input
                  className="apple-input mt-2"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.techniques}
                  onChange={(event) => changeDraftEdit({ techniques: event.target.value })}
                />
              </label>
              <label className="field-label">
                Nhãn phân tách bằng dấu phẩy
                <input
                  className="apple-input mt-2"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.tags}
                  onChange={(event) => changeDraftEdit({ tags: event.target.value })}
                />
              </label>
              <label className="field-label">
                Trạng thái tự động hóa
                <select
                  className="apple-input mt-2"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.automationStatus}
                  onChange={(event) => changeDraftEdit({ automationStatus: event.target.value })}
                >
                  {["manual", "candidate", "automated"].map((value) => (
                    <option value={value} key={value}>
                      {valueLabel(value)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field-label">
                Mã người phụ trách
                <input
                  className="apple-input mt-2"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  value={draftEdit.ownerId}
                  onChange={(event) => changeDraftEdit({ ownerId: event.target.value })}
                />
              </label>
              <label className="field-label">
                Tệp đính kèm
                <input
                  className="apple-input mt-2"
                  type="file"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  onChange={async (event) => {
                    const file = event.target.files?.[0];
                    if (!file) return;
                    try {
                      const uploaded = await uploadAssetAPI(file);
                      changeDraftEdit({
                        attachments: [...draftEdit.attachments, uploaded.data],
                      });
                    } catch (reason) {
                      setError(messageOf(reason));
                    }
                  }}
                />
                {draftEdit.attachments.map((attachment) => (
                  <span
                    className="mt-2 block break-all text-[11px] text-ink-muted"
                    key={attachment.url}
                  >
                    {attachment.filename}
                  </span>
                ))}
              </label>
              {selectedDraft.status === "DRAFT" && can("testcase.update") && (
                <div className="flex flex-wrap items-center gap-3 lg:col-span-2">
                  <button className="secondary-button w-fit" type="button" onClick={saveDraft}>
                    Lưu bản nháp
                  </button>
                  <span className="text-[12px] text-ink-muted" aria-live="polite">
                    {draftSaveState === "saving"
                      ? "Đang tự động lưu"
                      : draftSaveState === "pending"
                        ? "Có thay đổi chưa lưu"
                        : draftSaveState === "invalid"
                          ? "JSON chưa hợp lệ nên chưa tự động lưu"
                          : draftSaveState === "error"
                            ? "Tự động lưu thất bại"
                            : "Đã tự động lưu"}
                  </span>
                </div>
              )}
            </div>
            {testLint && (
              <div className="border-t border-border">
                <DataTable
                  items={testLint.findings}
                  empty="Không có vấn đề chất lượng"
                  columns={[
                    { key: "severity", label: "Mức độ" },
                    { key: "code", label: "Mã" },
                    { key: "message", label: "Nội dung" },
                  ]}
                />
              </div>
            )}
          </Panel>
          <ReviewCommentsPanel
            projectId={project._id}
            artifactType="test_case_draft"
            artifactId={selectedDraft._id}
          />
          <CollaborationPanel
            project={project}
            artifactType="test_case"
            artifactId={selectedDraft._id}
            onResolved={load}
          />
        </>
      )}
      <div className="grid gap-5 xl:grid-cols-2">
        {can("testcase.create") && (
          <Modal
            isOpen={creatingTest}
            onClose={() => setCreatingTest(false)}
            ariaLabel="Tạo ca kiểm thử"
            className="max-w-3xl max-h-[90dvh] overflow-y-auto"
          >
            <ModalHeader>
              <ModalTitle>Tạo ca kiểm thử</ModalTitle>
            </ModalHeader>
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
              <label className="field-label">
                Bộ dữ liệu tham số
                <select
                  aria-label="Bộ dữ liệu cho ca kiểm thử mới"
                  className="apple-input mt-2 min-h-28"
                  multiple
                  value={form.dataSetVersionIds}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      dataSetVersionIds: Array.from(
                        event.target.selectedOptions,
                        (option) => option.value,
                      ),
                    })
                  }
                >
                  {dataSets.map((item) => (
                    <option key={item.current_version_id} value={item.current_version_id}>
                      {item.name} v{item.current_version?.version}
                    </option>
                  ))}
                </select>
              </label>
              <div className="flex justify-end gap-3">
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => setCreatingTest(false)}
                >
                  Hủy
                </button>
                <button className="apple-button" type="submit">
                  Lưu bản nháp
                </button>
              </div>
            </form>
          </Modal>
        )}
        <Panel
          title="Kịch bản"
          actions={
            can("testscenario.create") ? (
              <button
                className="secondary-button"
                type="button"
                onClick={() => setCreatingScenario(true)}
              >
                Tạo kịch bản
              </button>
            ) : null
          }
        >
          {can("testscenario.create") && (
            <Modal
              isOpen={creatingScenario}
              onClose={() => setCreatingScenario(false)}
              ariaLabel="Tạo kịch bản"
              className="max-w-xl"
            >
              <ModalHeader>
                <ModalTitle>Tạo kịch bản</ModalTitle>
              </ModalHeader>
              <form className="space-y-3 p-5" onSubmit={createScenario}>
                <input
                  aria-label="Tên kịch bản"
                  className="apple-input"
                  required
                  value={scenarioForm.title}
                  onChange={(event) =>
                    setScenarioForm({ ...scenarioForm, title: event.target.value })
                  }
                  placeholder="Tên kịch bản"
                />
                <textarea
                  aria-label="Mục tiêu kịch bản"
                  className="apple-input min-h-20"
                  value={scenarioForm.objective}
                  onChange={(event) =>
                    setScenarioForm({ ...scenarioForm, objective: event.target.value })
                  }
                  placeholder="Mục tiêu và phạm vi"
                />
                <select
                  aria-label="Nhóm kịch bản"
                  className="apple-input"
                  value={scenarioForm.category}
                  onChange={(event) =>
                    setScenarioForm({ ...scenarioForm, category: event.target.value })
                  }
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
                  ].map((value) => (
                    <option key={value} value={value}>
                      {valueLabel(value)}
                    </option>
                  ))}
                </select>
                <div className="flex justify-end gap-3">
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => setCreatingScenario(false)}
                  >
                    Hủy
                  </button>
                  <button className="apple-button" type="submit">
                    Lưu kịch bản
                  </button>
                </div>
              </form>
            </Modal>
          )}
          <details className="border-b border-border p-4">
            <summary className="cursor-pointer text-sm font-medium">
              Tìm kiếm bộ lọc và sắp xếp
            </summary>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              <input
                aria-label="Tìm kịch bản"
                className="apple-input"
                placeholder="Tìm mã hoặc tên"
                value={scenarioFilters.q}
                onChange={(event) =>
                  setScenarioFilters({ ...scenarioFilters, q: event.target.value })
                }
              />
              <select
                aria-label="Lọc nhóm kịch bản"
                className="apple-input"
                value={scenarioFilters.category}
                onChange={(event) =>
                  setScenarioFilters({ ...scenarioFilters, category: event.target.value })
                }
              >
                <option value="">Mọi nhóm</option>
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
                ].map((value) => (
                  <option value={value} key={value}>
                    {valueLabel(value)}
                  </option>
                ))}
              </select>
              <select
                aria-label="Lọc rủi ro kịch bản"
                className="apple-input"
                value={scenarioFilters.risk}
                onChange={(event) =>
                  setScenarioFilters({ ...scenarioFilters, risk: event.target.value })
                }
              >
                <option value="">Mọi rủi ro</option>
                {["critical", "high", "medium", "low"].map((value) => (
                  <option value={value} key={value}>
                    {valueLabel(value)}
                  </option>
                ))}
              </select>
              <select
                aria-label="Lọc trạng thái kịch bản"
                className="apple-input"
                value={scenarioFilters.status}
                onChange={(event) =>
                  setScenarioFilters({ ...scenarioFilters, status: event.target.value })
                }
              >
                <option value="">Mọi trạng thái</option>
                {["draft", "in_review", "approved", "archived"].map((value) => (
                  <option value={value} key={value}>
                    {valueLabel(value)}
                  </option>
                ))}
              </select>
              <select
                aria-label="Sắp xếp kịch bản"
                className="apple-input"
                value={scenarioFilters.sort}
                onChange={(event) =>
                  setScenarioFilters({ ...scenarioFilters, sort: event.target.value })
                }
              >
                <option value="-updated_at">Mới cập nhật</option>
                <option value="updated_at">Cũ cập nhật</option>
                <option value="scenario_key">Mã tăng dần</option>
                <option value="title">Tên tăng dần</option>
              </select>
            </div>
          </details>
          <DataTable
            onSelect={async (item) => {
              if (item.status !== "draft" || !can("testscenario.update")) return;
              const answer = await ask({
                title: "Đổi tên kịch bản kiểm thử",
                description: item.scenario_key,
                confirmLabel: "Lưu tên",
                fields: [
                  {
                    name: "title",
                    label: "Tên kịch bản",
                    initialValue: item.title,
                    required: true,
                    autoFocus: true,
                  },
                ],
              });
              if (!answer || answer.title === item.title) return;
              try {
                await testingApi.updateScenario(item._id, {
                  expected_revision: item.revision,
                  title: answer.title,
                });
                await load();
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
            items={scenarios}
            empty="Chưa có kịch bản"
            columns={[
              { key: "scenario_key", label: "Mã" },
              { key: "title", label: "Tên" },
              { key: "category", label: "Nhóm" },
              { key: "origin", label: "Nguồn" },
              {
                key: "actions",
                label: "Thao tác",
                render: (item) => (
                  <span className="flex flex-wrap gap-2">
                    {can("testscenario.clone") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={async (event) => {
                          event.stopPropagation();
                          try {
                            await testingApi.cloneScenario(item._id);
                            await load();
                          } catch (reason) {
                            setError(messageOf(reason));
                          }
                        }}
                      >
                        Nhân bản
                      </button>
                    )}
                    {item.status !== "archived" && can("testscenario.archive") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={async (event) => {
                          event.stopPropagation();
                          const answer = await ask({
                            title: "Lưu trữ kịch bản",
                            description: item.title,
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
                            await testingApi.archiveScenario(item._id, {
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
      </div>
      {canReadTestData && (
        <Panel
          title="Bộ dữ liệu kiểm thử có phiên bản"
          actions={
            can("testcase.create") ? (
              <button
                className="secondary-button"
                type="button"
                onClick={() => setCreatingDataSet(true)}
              >
                Tạo bộ dữ liệu
              </button>
            ) : null
          }
        >
          {can("testcase.create") && (
            <Modal
              isOpen={creatingDataSet}
              onClose={() => setCreatingDataSet(false)}
              ariaLabel="Tạo bộ dữ liệu"
              className="max-w-2xl max-h-[90dvh] overflow-y-auto"
            >
              <ModalHeader>
                <ModalTitle>Tạo bộ dữ liệu</ModalTitle>
              </ModalHeader>
              <form className="grid gap-3 p-5" onSubmit={createDataSet}>
                <label className="field-label">
                  Tên bộ dữ liệu
                  <input
                    className="apple-input mt-2"
                    required
                    value={dataSetForm.name}
                    onChange={(event) =>
                      setDataSetForm({ ...dataSetForm, name: event.target.value })
                    }
                  />
                </label>
                <label className="field-label">
                  Biến JSON
                  <textarea
                    className="apple-input mt-2 min-h-28 font-mono"
                    required
                    value={dataSetForm.variables}
                    onChange={(event) =>
                      setDataSetForm({ ...dataSetForm, variables: event.target.value })
                    }
                  />
                </label>
                <label className="field-label">
                  Secret refs JSON
                  <textarea
                    className="apple-input mt-2 min-h-28 font-mono"
                    required
                    value={dataSetForm.secretRefs}
                    onChange={(event) =>
                      setDataSetForm({ ...dataSetForm, secretRefs: event.target.value })
                    }
                  />
                </label>
                <div className="flex justify-end gap-3">
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => setCreatingDataSet(false)}
                  >
                    Hủy
                  </button>
                  <button className="apple-button" type="submit">
                    Tạo bộ dữ liệu
                  </button>
                </div>
              </form>
            </Modal>
          )}
          <DataTable
            items={dataSets}
            empty="Chưa có bộ dữ liệu tham số"
            onSelect={async (item) => {
              if (!can("testcase.update")) return;
              const answer = await ask({
                title: "Tạo phiên bản bộ dữ liệu mới",
                description: `${item.name} v${item.current_version?.version}`,
                confirmLabel: "Tạo phiên bản",
                fields: [
                  {
                    name: "name",
                    label: "Tên bộ dữ liệu",
                    initialValue: item.name,
                    required: true,
                    autoFocus: true,
                  },
                  {
                    name: "variables",
                    label: "Biến JSON",
                    initialValue: JSON.stringify(item.current_version?.variables || {}, null, 2),
                    required: true,
                    multiline: true,
                  },
                  {
                    name: "secretRefs",
                    label: "Danh sách tham chiếu bí mật dạng JSON",
                    initialValue: JSON.stringify(item.current_version?.secret_refs || {}, null, 2),
                    required: true,
                    multiline: true,
                  },
                  {
                    name: "reason",
                    label: "Lý do thay đổi",
                    initialValue: "Cập nhật dữ liệu kiểm thử",
                    required: true,
                    multiline: true,
                  },
                ],
              });
              if (!answer) return;
              try {
                await testingApi.createDataSetVersion(item._id, {
                  expected_current_version_id: item.current_version_id,
                  name: answer.name,
                  variables: JSON.parse(answer.variables),
                  secret_refs: JSON.parse(answer.secretRefs),
                  change_reason: answer.reason,
                });
                await load();
              } catch (reason) {
                setError(
                  reason instanceof SyntaxError
                    ? "Bộ dữ liệu phải là JSON hợp lệ"
                    : messageOf(reason),
                );
              }
            }}
            columns={[
              { key: "name", label: "Tên" },
              {
                key: "version",
                label: "Phiên bản",
                render: (item) => `v${item.current_version?.version || 1}`,
              },
              {
                key: "variables",
                label: "Biến",
                render: (item) => Object.keys(item.current_version?.variables || {}).join(", "),
              },
              {
                key: "secret_refs",
                label: "Tham chiếu bí mật",
                render: (item) => Object.keys(item.current_version?.secret_refs || {}).join(", "),
              },
            ]}
          />
        </Panel>
      )}
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
        actions={
          <div className="flex flex-wrap gap-2">
            {can("testcase.export") && (
              <button
                className="secondary-button"
                type="button"
                onClick={() =>
                  testingApi
                    .exportTestCases(project._id, "csv")
                    .catch((reason) => setError(messageOf(reason)))
                }
              >
                Xuất CSV
              </button>
            )}
            {can("testcase.export") && (
              <button
                className="secondary-button"
                type="button"
                onClick={() =>
                  testingApi
                    .exportTestCases(project._id, "xlsx")
                    .catch((reason) => setError(messageOf(reason)))
                }
              >
                Xuất XLSX
              </button>
            )}
          </div>
        }
      >
        {can("testcase.import") && (
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
                  setTestImport(await testingApi.uploadTestImport(project._id, file));
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
                    { key: "type", label: "Loại", render: (item) => valueLabel(item.type) },
                    {
                      key: "priority",
                      label: "Ưu tiên",
                      render: (item) => valueLabel(item.priority),
                    },
                    { key: "expected", label: "Kết quả mong đợi" },
                  ]}
                />
                <button
                  className="apple-button"
                  type="button"
                  onClick={async () => {
                    try {
                      await testingApi.confirmTestImport(
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
        )}
      </Panel>
      <Panel title="OpenAPI và Postman">
        <div className="grid gap-5 p-5 xl:grid-cols-2">
          {can("apiartifact.import") && (
            <form
              className="space-y-4"
              onSubmit={async (event) => {
                event.preventDefault();
                try {
                  await testingApi.importApiArtifact(project._id, apiImport);
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
                Tạo bản xem trước
              </button>
            </form>
          )}
          <div className="space-y-5">
            <DataTable
              items={apiArtifacts}
              empty="Chưa có nguồn đặc tả API"
              columns={[
                { key: "filename", label: "Nguồn" },
                { key: "format", label: "Định dạng" },
                {
                  key: "status",
                  label: "Trạng thái",
                  render: (item) => <StatusPill value={item.status} />,
                },
                { key: "preview_count", label: "Thao tác" },
                {
                  key: "actions",
                  label: "Xử lý",
                  render: (item) => (
                    <div className="flex flex-wrap gap-2">
                      {item.status === "PREVIEW_READY" && can("apiartifact.review") && (
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={async () => {
                            try {
                              await testingApi.reviewApiArtifact(item._id, {
                                expected_revision: item.revision,
                                selected_indexes: [],
                                review_note: "Đã rà soát toàn bộ thao tác",
                              });
                              await load();
                            } catch (reason) {
                              setError(messageOf(reason));
                            }
                          }}
                        >
                          Rà soát
                        </button>
                      )}
                      {item.status === "REVIEWED" && can("apiartifact.confirm") && (
                        <button
                          className="apple-button"
                          type="button"
                          onClick={async () => {
                            try {
                              await testingApi.confirmApiArtifact(item._id, {
                                expected_revision: item.revision,
                                idempotency_key: crypto.randomUUID(),
                              });
                              await load();
                            } catch (reason) {
                              setError(messageOf(reason));
                            }
                          }}
                        >
                          Xác nhận
                        </button>
                      )}
                      {item.status !== "ARCHIVED" && can("apiartifact.archive") && (
                        <button
                          className="danger-button"
                          type="button"
                          onClick={async () => {
                            const answer = await ask({
                              title: "Lưu trữ nguồn đặc tả API",
                              description: item.filename,
                              confirmLabel: "Lưu trữ",
                            });
                            if (!answer) return;
                            try {
                              await testingApi.archiveApiArtifact(item._id, {
                                expected_revision: item.revision,
                                reason: "Nguồn đặc tả không còn được sử dụng",
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
                    </div>
                  ),
                },
              ]}
            />
            {apiArtifacts.filter((item) => item.status === "CONFIRMED").length >= 2 && (
              <div className="rounded-2xl border border-[var(--border)] p-4">
                <div className="grid gap-3 md:grid-cols-2">
                  <label className="field-label">
                    Phiên bản trước
                    <select
                      className="apple-input mt-2"
                      value={apiCompareFrom}
                      onChange={(event) => setApiCompareFrom(event.target.value)}
                    >
                      {apiArtifacts
                        .filter((item) => item.status === "CONFIRMED")
                        .map((item) => (
                          <option key={item._id} value={item._id}>
                            {item.filename}
                          </option>
                        ))}
                    </select>
                  </label>
                  <label className="field-label">
                    Phiên bản sau
                    <select
                      className="apple-input mt-2"
                      value={apiCompareTo}
                      onChange={(event) => setApiCompareTo(event.target.value)}
                    >
                      {apiArtifacts
                        .filter((item) => item.status === "CONFIRMED")
                        .map((item) => (
                          <option key={item._id} value={item._id}>
                            {item.filename}
                          </option>
                        ))}
                    </select>
                  </label>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    className="secondary-button"
                    disabled={!apiCompareFrom || !apiCompareTo || apiCompareFrom === apiCompareTo}
                    type="button"
                    onClick={async () => {
                      try {
                        setApiDifference(
                          await testingApi.diffApiArtifacts(
                            project._id,
                            apiCompareFrom,
                            apiCompareTo,
                          ),
                        );
                      } catch (reason) {
                        setError(messageOf(reason));
                      }
                    }}
                  >
                    So sánh đặc tả
                  </button>
                  {can("impact.execute") && (
                    <button
                      className="secondary-button"
                      disabled={!apiCompareFrom || !apiCompareTo || apiCompareFrom === apiCompareTo}
                      type="button"
                      onClick={async () => {
                        try {
                          await testingApi.analyzeApiArtifactImpact(project._id, {
                            from_artifact_id: apiCompareFrom,
                            to_artifact_id: apiCompareTo,
                          });
                        } catch (reason) {
                          setError(messageOf(reason));
                        }
                      }}
                    >
                      Phân tích ảnh hưởng
                    </button>
                  )}
                </div>
                {apiDifference && (
                  <p className="mt-3 text-sm text-[var(--muted)]">
                    Thêm {apiDifference.added.length} thay đổi {apiDifference.changed.length} loại
                    bỏ {apiDifference.removed.length}
                  </p>
                )}
              </div>
            )}
            <DataTable
              items={operations}
              empty="Chưa có thao tác API đã xác nhận"
              columns={[
                { key: "method", label: "Phương thức" },
                { key: "path", label: "Đường dẫn" },
                { key: "title", label: "Tên" },
                {
                  key: "generate",
                  label: "Tạo ca kiểm thử",
                  render: (item) =>
                    can("ai.generate_api_testcase") && can("testcase.create") ? (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={async () => {
                          try {
                            await testingApi.generateApiTests(item._id);
                            await load();
                          } catch (reason) {
                            setError(messageOf(reason));
                          }
                        }}
                      >
                        Tạo ca kiểm thử
                      </button>
                    ) : null,
                },
              ]}
            />
          </div>
        </div>
      </Panel>
      {dialog}
    </QaPage>
  );
}
