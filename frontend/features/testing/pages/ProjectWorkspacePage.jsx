"use client";
import { ErrorState, LoadingState } from "../components/TestingUi";
import { useProject } from "../hooks/useProject";
import ChangesPage from "./workspace/ChangesPage";
import DashboardPage from "./workspace/DashboardPage";
import DefectsPage from "./workspace/DefectsPage";
import ExecutionPage from "./workspace/ExecutionPage";
import KnowledgePage from "./workspace/KnowledgePage";
import RequirementsPage from "./workspace/RequirementsPage";
import ReportsPage from "./workspace/ReportsPage";
import ReviewQueuePage from "./workspace/ReviewQueuePage";
import SettingsPage from "./workspace/SettingsPage";
import TestDesignPage from "./workspace/TestDesignPage";
import TraceabilityPage from "./workspace/TraceabilityPage";

export default function ProjectWorkspacePage({ projectId, section }) {
  const state = useProject(projectId);
  if (state.loading)
    return (
      <div className="p-8">
        <LoadingState />
      </div>
    );
  if (state.error || !state.project)
    return (
      <div className="p-8">
        <ErrorState message={state.error || "Không tìm thấy dự án"} />
      </div>
    );
  const area = section[0] || "dashboard";
  const requiredPermissions = {
    dashboard: "project.read",
    requirements: "requirement.read",
    "test-design": "testcase.read",
    traceability: "trace.read",
    changes: "impact.read",
    "ai-review": "proposal.read",
    execution: "testrun.read",
    defects: "defect.read",
    knowledge: "knowledge.read",
    reports: "report.read",
    settings: "project.settings.manage",
  };
  const requiredPermission = requiredPermissions[area];
  if (requiredPermission && !state.project.current_permissions?.includes(requiredPermission)) {
    return (
      <div className="p-8">
        <ErrorState message="Bạn không có quyền mở khu vực này trong dự án" />
      </div>
    );
  }
  const props = {
    project: state.project,
    section: section.slice(1),
    setGlobalError: state.setError,
  };
  const pages = {
    requirements: <RequirementsPage {...props} />,
    "test-design": <TestDesignPage {...props} />,
    traceability: <TraceabilityPage {...props} />,
    changes: <ChangesPage {...props} />,
    "ai-review": <ReviewQueuePage {...props} />,
    execution: <ExecutionPage {...props} />,
    defects: <DefectsPage {...props} />,
    knowledge: <KnowledgePage {...props} />,
    reports: <ReportsPage {...props} />,
    settings: <SettingsPage {...props} onProjectChange={state.reload} />,
  };
  return (
    <>
      {state.project.access_context?.mode === "BREAK_GLASS" && (
        <div className="border-b border-warning/40 bg-warning-soft px-5 py-3 text-[13px] font-semibold text-warning">
          Quyền truy cập khẩn cấp đang hoạt động đến{" "}
          {new Date(state.project.access_context.expires_at).toLocaleString("vi-VN")}
        </div>
      )}
      {pages[area] || <DashboardPage {...props} />}
    </>
  );
}
