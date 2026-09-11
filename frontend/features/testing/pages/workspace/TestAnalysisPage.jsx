"use client";
import { useCallback, useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import TestBasisPanel from "../../components/TestBasisPanel";
import TestConditionEditor from "../../components/TestConditionEditor";
import TestConditionTable from "../../components/TestConditionTable";
import TestabilityFindingsPanel from "../../components/TestabilityFindingsPanel";
import { ErrorState, Panel, ProjectCrumb, StatusPill, WorkspacePage, useActionDialog } from "../../components/WorkspacePrimitives";
import { Modal, ModalHeader, ModalTitle } from "@/shared/components/ui/Modal";
import { docText, messageOf } from "../../lib/testing";
import { testingApi } from "../../services/testing.service";


export default function TestAnalysisPage({ project }) {
  const { ask, dialog } = useActionDialog();
  const [conditions, setConditions] = useState([]);
  const [requirements, setRequirements] = useState([]);
  const [coverage, setCoverage] = useState(null);
  const [selected, setSelected] = useState(null);
  const [editing, setEditing] = useState(false);
  const [basisRefs, setBasisRefs] = useState([]);
  const [aiResult, setAiResult] = useState(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const can = (permission) => project.current_permissions?.includes(permission);
  const load = useCallback(async () => {
    try {
      const [conditionResult, requirementValues, coverageValue] = await Promise.all([
        testingApi.listTestConditions(project._id, { q: query, status, page_size: 200 }),
        testingApi.listRequirements(project._id, { status: "BASELINED", page_size: 500 }),
        testingApi.getTestConditionCoverage(project._id),
      ]);
      setConditions(conditionResult.items || []);
      setRequirements(requirementValues);
      setCoverage(coverageValue);
      setSelected((current) => conditionResult.items?.find((item) => item._id === current?._id) || current);
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [project._id, query, status]);
  useEffect(() => { void load(); }, [load]);
  const transition = async (title, confirmLabel, action) => {
    const answer = await ask({ title, confirmLabel, fields: [{ name: "note", label: "Ghi chú", required: true, multiline: true }] });
    if (!answer) return;
    try {
      await action(selected._id, { expected_revision: selected.revision, note: answer.note });
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <WorkspacePage
      title="Phân tích kiểm thử"
      actions={<><ProjectCrumb projectId={project._id} />{can("testcondition.create") && <button className="apple-button" type="button" onClick={() => { setSelected(null); setEditing(true); }}>Tạo test condition</button>}</>}
    >
      {dialog}
      {error && <ErrorState message={error} />}
      <Panel title="Test condition">
        <form className="grid gap-3 p-5 sm:grid-cols-[1fr_220px_auto]" onSubmit={(event) => { event.preventDefault(); void load(); }}>
          <input className="apple-input" aria-label="Tìm test condition" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm mã condition hoặc coverage item" />
          <select className="apple-input" aria-label="Lọc trạng thái condition" value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">Tất cả trạng thái</option>
            {["DRAFT", "IN_REVIEW", "APPROVED", "ARCHIVED"].map((item) => <option key={item}>{item}</option>)}
          </select>
          <button className="secondary-button" type="submit">Lọc</button>
        </form>
        <TestConditionTable items={conditions} onSelect={setSelected} />
      </Panel>
      {can("testanalysis.run_ai") && (
        <Panel title="Đề xuất condition bằng AI">
          <div className="space-y-4 p-5">
            <TestBasisPanel refs={basisRefs} onChange={setBasisRefs} requirements={requirements} />
            <button
              className="secondary-button"
              type="button"
              disabled={!basisRefs.length}
              onClick={async () => {
                try {
                  setAiResult(await testingApi.runTestAnalysisAi(project._id, { basis_refs: basisRefs, instruction: "Phân tích đầy đủ hành vi dương âm biên trạng thái quyền tích hợp dữ liệu lỗi và phi chức năng", idempotency_key: crypto.randomUUID() }));
                } catch (reason) {
                  setError(messageOf(reason));
                }
              }}
            >
              Phân tích và tạo candidate
            </button>
            {aiResult?.degraded_mode && <p className="text-sm text-warning">AI chưa sẵn sàng và chưa tạo condition nào</p>}
            <DataTable items={aiResult?.candidates || []} empty="Chưa có candidate" columns={[
              { key: "title", label: "Candidate" },
              { key: "coverage_item", label: "Coverage item" },
              { key: "risk", label: "Rủi ro", render: (item) => <StatusPill value={item.risk} /> },
              { key: "status", label: "Trạng thái", render: () => <StatusPill value="CANDIDATE" /> },
              ...(can("testcondition.create") ? [{ key: "actions", label: "Thao tác", render: (item) => <button className="secondary-button" type="button" onClick={() => { setSelected({ ...item, basis_refs: item.basis_refs || basisRefs, origin: "AI_CANDIDATE_CONFIRMED", ai_result_id: aiResult._id }); setEditing(true); }}>Dùng làm bản nháp</button> }] : []),
            ]} />
          </div>
        </Panel>
      )}
      {selected?._id && (
        <Panel title={`${selected.condition_key} ${selected.title}`} actions={<div className="flex flex-wrap gap-2">
          {can("testcondition.update") && selected.status === "DRAFT" && <button className="secondary-button" type="button" onClick={() => setEditing(true)}>Chỉnh sửa</button>}
          {can("testcondition.review") && selected.status === "DRAFT" && <button className="secondary-button" type="button" onClick={() => transition("Gửi condition để rà soát", "Gửi rà soát", testingApi.submitTestCondition)}>Gửi rà soát</button>}
          {can("testcondition.approve") && selected.status === "IN_REVIEW" && <button className="apple-button" type="button" onClick={() => transition("Phê duyệt test condition", "Phê duyệt", testingApi.approveTestCondition)}>Phê duyệt</button>}
          {can("testcondition.archive") && ["DRAFT", "APPROVED"].includes(selected.status) && <button className="secondary-button" type="button" onClick={() => transition("Lưu trữ test condition", "Lưu trữ", testingApi.archiveTestCondition)}>Lưu trữ</button>}
        </div>}>
          <div className="grid gap-4 p-5 md:grid-cols-3">
            <div><p className="field-label">Mô tả</p><p className="mt-2 whitespace-pre-wrap text-sm">{docText(selected.description_doc)}</p></div>
            <div><p className="field-label">Test Basis</p><p className="mt-2 text-sm">{selected.basis_refs?.map((item) => item.artifact_version_id || item.artifact_id).join(" · ")}</p></div>
            <div><p className="field-label">Kỹ thuật</p><p className="mt-2 text-sm">{selected.technique_candidates?.join(" · ") || "Chưa xác định"}</p></div>
          </div>
          <TestabilityFindingsPanel
            condition={selected}
            canResolve={can("testanalysis.resolve_finding")}
            onResolve={async (finding) => {
              const answer = await ask({ title: "Giải quyết finding", confirmLabel: "Ghi nhận", fields: [
                { name: "status", label: "Kết quả", options: [{ value: "RESOLVED", label: "Đã giải quyết" }, { value: "ACCEPTED_RISK", label: "Chấp nhận rủi ro" }] },
                { name: "resolution_ref", label: "Tham chiếu xử lý", required: true },
                { name: "note", label: "Ghi chú", required: true, multiline: true },
              ] });
              if (!answer) return;
              try {
                await testingApi.resolveTestAnalysisFinding(selected._id, finding.finding_id, { expected_revision: selected.revision, ...answer });
                await load();
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          />
        </Panel>
      )}
      <Panel title="Truy vết Requirement đến Condition đến Test Case">
        <DataTable items={coverage?.items || []} empty="Chưa có condition để tính coverage" columns={[
          { key: "condition_key", label: "Condition" },
          { key: "basis_refs", label: "Requirement hoặc basis", render: (item) => item.basis_refs.map((ref) => ref.artifact_version_id || ref.artifact_id).join(" · ") },
          { key: "scenario_ids", label: "Scenario", render: (item) => item.scenario_ids.length },
          { key: "test_case_version_ids", label: "Test case", render: (item) => item.test_case_version_ids.length },
          { key: "uncovered", label: "Coverage", render: (item) => <StatusPill value={item.uncovered ? "UNCOVERED" : "COVERED"} /> },
        ]} />
      </Panel>
      <Modal isOpen={editing} onClose={() => setEditing(false)} ariaLabel="Biên tập test condition" className="max-h-[94dvh] max-w-5xl overflow-y-auto">
        <ModalHeader><ModalTitle>{selected?._id ? "Chỉnh sửa test condition" : "Tạo test condition"}</ModalTitle></ModalHeader>
        <TestConditionEditor
          initialValue={selected ? { ...selected, description: docText(selected.description_doc) } : null}
          requirements={requirements}
          onCancel={() => setEditing(false)}
          onSave={async (payload) => {
            const value = selected?._id
              ? await testingApi.updateTestCondition(selected._id, { ...payload, expected_revision: selected.revision })
              : await testingApi.createTestCondition(project._id, payload);
            setSelected(value);
            setEditing(false);
            await load();
          }}
        />
      </Modal>
    </WorkspacePage>
  );
}
