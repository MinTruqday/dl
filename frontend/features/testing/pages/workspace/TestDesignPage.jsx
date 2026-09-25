"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { uploadAssetAPI } from "@/features/cloud/services/upload.service";
import DataTable from "../../components/DataTable";
import FormalReviewPanel from "../../components/FormalReviewPanel";
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
  WorkspacePage,
  StatusPill,
  useActionDialog,
} from "../../components/WorkspacePrimitives";
import { testingApi } from "../../services/testing.service";
import { docText, messageOf, textDoc, valueLabel } from "../../lib/testing";
import DocumentEditor from "../../editor/DocumentEditor";
import ApiArtifactsPanel from "./test-design/ApiArtifactsPanel";
import DataSetsPanel from "./test-design/DataSetsPanel";
import ScenariosPanel from "./test-design/ScenariosPanel";
import TestCaseCreateModal from "./test-design/TestCaseCreateModal";
import TestCaseTransferPanel from "./test-design/TestCaseTransferPanel";
import {
  createDataSetForm,
  createScenarioForm,
  createTestCaseForm,
  AI_TEST_GENERATION_CATEGORIES,
  TEST_CASE_TYPES,
  TEST_LEVELS,
  TEST_SCENARIO_CATEGORIES,
} from "./test-design/testDesign.model";

export default function TestDesignPage({ project }) {
  const { ask, dialog } = useActionDialog();
  const [requirements, setRequirements] = useState([]);
  const [testConditions, setTestConditions] = useState([]);
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
  const [scenarioForm, setScenarioForm] = useState(createScenarioForm);
  const [dataSetForm, setDataSetForm] = useState(createDataSetForm);
  const [form, setForm] = useState(createTestCaseForm);
  const [error, setError] = useState("");
  const [creatingTest, setCreatingTest] = useState(false);
  const [creatingScenario, setCreatingScenario] = useState(false);
  const [creatingDataSet, setCreatingDataSet] = useState(false);
  const [aiAction, setAiAction] = useState("");
  const can = (permission) => project.current_permissions?.includes(permission);
  const canReadTestData = project.current_permissions?.includes("testdata.read");
  const load = useCallback(async () => {
    try {
      const [
        requirementValues,
        testConditionValues,
        scenarioValues,
        dataSetValues,
        draftValues,
        testValues,
        suiteValues,
        apiArtifactValues,
        operationValues,
      ] = await Promise.all([
        testingApi.listRequirements(project._id, { page_size: 500, status: "BASELINED" }),
        testingApi.listTestConditions(project._id, { status: "APPROVED", page_size: 200 }),
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
      setTestConditions(testConditionValues.items || []);
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
      testConditionIds: selectedDraft.test_condition_ids || [],
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
        test_condition_ids: form.testConditionIds,
        requirement_version_ids: selectedRequirement ? [selectedRequirement] : [],
        acceptance_criterion_ids: [],
        origin: "manual",
        source_evidence: [],
      });
      setForm(createTestCaseForm());
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
        test_condition_ids: scenarioForm.testConditionIds,
        status: "draft",
        origin: "manual",
      });
      setScenarioForm(createScenarioForm());
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
      setDataSetForm(createDataSetForm());
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
    setAiAction("testcase");
    try {
      await testingApi.generateTestCases(selectedRequirement, {
        categories: AI_TEST_GENERATION_CATEGORIES,
        count_per_category: 1,
        instruction: "Tạo theo phiên bản chuẩn và tiêu chí chấp nhận",
      });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setAiAction("");
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
              test_condition_ids: snapshot.testConditionIds,
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
    <WorkspacePage
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
        <Panel title="Hỗ trợ thiết kế kiểm thử">
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
              <button
                aria-busy={aiAction === "testcase"}
                className="apple-button"
                disabled={Boolean(aiAction)}
                type="button"
                onClick={generate}
              >
                {aiAction === "testcase" ? "AI đang tạo ca kiểm thử" : "Tạo 4 nhóm ca kiểm thử"}
              </button>
            )}
            {can("ai.generate_scenario") && can("testscenario.create") && (
              <button
                className="secondary-button"
                aria-busy={aiAction === "scenario"}
                disabled={Boolean(aiAction)}
                type="button"
                onClick={async () => {
                  if (!selectedRequirement) return;
                  setAiAction("scenario");
                  try {
                    await testingApi.generateScenarios(selectedRequirement, {
                      categories: AI_TEST_GENERATION_CATEGORIES,
                      count_per_category: 1,
                    });
                    await load();
                  } catch (reason) {
                    setError(messageOf(reason));
                  } finally {
                    setAiAction("");
                  }
                }}
              >
                {aiAction === "scenario" ? "AI đang tạo kịch bản" : "Tạo kịch bản"}
              </button>
            )}
            {can("testcase.duplicate_check") && can("ai.run_duplicate_check") && (
              <button
                className="secondary-button"
                aria-busy={aiAction === "duplicates"}
                disabled={Boolean(aiAction)}
                type="button"
                onClick={async () => {
                  setAiAction("duplicates");
                  try {
                    setDuplicates(await testingApi.findDuplicates(project._id));
                  } catch (reason) {
                    setError(messageOf(reason));
                  } finally {
                    setAiAction("");
                  }
                }}
              >
                {aiAction === "duplicates"
                  ? "Đang tìm ca kiểm thử trùng lặp"
                  : "Tìm ca kiểm thử trùng lặp"}
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
      {selectedTestId &&
        testVersions[0] &&
        project.current_permissions?.includes("reviewsession.read") && (
          <FormalReviewPanel
            project={project}
            artifactType="TEST_CASE"
            artifactId={selectedTestId}
            artifactVersionId={testVersions[0]._id}
            reviewType="TEST_CASE_REVIEW"
          />
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
                  {TEST_CASE_TYPES.map((value) => (
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
                  {TEST_LEVELS.map((value) => (
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
                  {TEST_LEVELS.map((value) => (
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
                Điều kiện kiểm thử đã phê duyệt
                <select
                  aria-label="Điều kiện kiểm thử của bản nháp"
                  className="apple-input mt-2 min-h-28"
                  disabled={selectedDraft.status !== "DRAFT" || !can("testcase.update")}
                  multiple
                  value={draftEdit.testConditionIds}
                  onChange={(event) =>
                    changeDraftEdit({
                      testConditionIds: Array.from(
                        event.target.selectedOptions,
                        (option) => option.value,
                      ),
                    })
                  }
                >
                  {testConditions.map((item) => (
                    <option key={item._id} value={item._id}>
                      {item.condition_key} {item.title}
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
          <TestCaseCreateModal
            isOpen={creatingTest}
            onClose={() => setCreatingTest(false)}
            form={form}
            setForm={setForm}
            dataSets={dataSets}
            testConditions={testConditions}
            onSubmit={create}
          />
        )}
        <ScenariosPanel
          can={can}
          scenarios={scenarios}
          filters={scenarioFilters}
          setFilters={setScenarioFilters}
          isCreating={creatingScenario}
          setCreating={setCreatingScenario}
          form={scenarioForm}
          setForm={setScenarioForm}
          testConditions={testConditions}
          onSubmit={createScenario}
          ask={ask}
          reload={load}
          onError={setError}
        />
      </div>
      <DataSetsPanel
        can={can}
        canRead={canReadTestData}
        items={dataSets}
        isCreating={creatingDataSet}
        setCreating={setCreatingDataSet}
        form={dataSetForm}
        setForm={setDataSetForm}
        onSubmit={createDataSet}
        ask={ask}
        reload={load}
        onError={setError}
      />
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
      <TestCaseTransferPanel
        projectId={project._id}
        can={can}
        preview={testImport}
        setPreview={setTestImport}
        reload={load}
        onError={setError}
      />
      <ApiArtifactsPanel
        projectId={project._id}
        can={can}
        ask={ask}
        apiImport={apiImport}
        setApiImport={setApiImport}
        artifacts={apiArtifacts}
        operations={operations}
        compareFrom={apiCompareFrom}
        setCompareFrom={setApiCompareFrom}
        compareTo={apiCompareTo}
        setCompareTo={setApiCompareTo}
        difference={apiDifference}
        setDifference={setApiDifference}
        reload={load}
        onError={setError}
      />
      {dialog}
    </WorkspacePage>
  );
}
