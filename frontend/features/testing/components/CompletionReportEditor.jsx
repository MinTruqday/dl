"use client";

import { useEffect, useState } from "react";
import LessonsLearnedPanel from "./LessonsLearnedPanel";
import ResidualRiskPanel from "./ResidualRiskPanel";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";

export default function CompletionReportEditor({ report, members = [], onClose, onSave }) {
  const [residualRisks, setResidualRisks] = useState([]);
  const [actions, setActions] = useState([]);
  const [narrative, setNarrative] = useState({
    executive_summary: "",
    closure_summary: "",
    residual_risk_summary: "",
    recommendation_rationale: "",
  });
  useEffect(() => {
    setResidualRisks(report?.residual_risks || []);
    setActions(report?.improvement_actions || []);
    setNarrative({
      executive_summary: report?.executive_summary || "",
      closure_summary: report?.closure_summary || "",
      residual_risk_summary: report?.residual_risk_summary || "",
      recommendation_rationale: report?.recommendation_rationale || "",
    });
  }, [report]);
  if (!report) return null;
  return (
    <Modal
      isOpen
      onClose={onClose}
      className="max-h-[92vh] max-w-5xl overflow-y-auto"
      ariaLabel="Chỉnh sửa báo cáo hoàn tất kiểm thử"
    >
      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSave({
            expected_revision: report.revision,
            residual_risks: residualRisks,
            improvement_actions: actions,
            ...narrative,
          });
        }}
      >
        <ModalHeader>
          <ModalTitle>Chỉnh sửa báo cáo hoàn tất</ModalTitle>
        </ModalHeader>
        <ModalContent className="space-y-7">
          <div className="grid gap-4 md:grid-cols-2">
            {[
              ["executive_summary", "Tóm tắt điều hành"],
              ["closure_summary", "Tổng kết đóng kiểm thử"],
              ["residual_risk_summary", "Tổng kết rủi ro còn lại"],
              ["recommendation_rationale", "Cơ sở khuyến nghị"],
            ].map(([key, label]) => (
              <label className="field-label" key={key}>
                {label}
                <textarea
                  className="apple-input mt-2 min-h-24"
                  value={narrative[key]}
                  onChange={(event) =>
                    setNarrative((current) => ({ ...current, [key]: event.target.value }))
                  }
                />
              </label>
            ))}
          </div>
          <ResidualRiskPanel
            items={residualRisks}
            members={members}
            editable
            allowAdd={false}
            allowRemove={false}
            onChange={setResidualRisks}
          />
          <LessonsLearnedPanel
            lessons={report.lessons_learned || []}
            actions={actions}
            members={members}
            editableLessons={false}
            editableActions
            onActionsChange={setActions}
          />
        </ModalContent>
        <ModalFooter>
          <button className="secondary-button" type="button" onClick={onClose}>
            Hủy
          </button>
          <button className="apple-button" type="submit">
            Lưu báo cáo
          </button>
        </ModalFooter>
      </form>
    </Modal>
  );
}
