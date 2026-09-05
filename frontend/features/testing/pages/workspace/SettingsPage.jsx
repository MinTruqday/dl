"use client";
import { useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import ProjectNotificationsPanel from "../../components/ProjectNotificationsPanel";
import WebhookPanel from "../../components/WebhookPanel";
import ProjectConnectorsPanel from "../../components/ProjectConnectorsPanel";
import CicdPanel from "../../components/CicdPanel";
import {
  ErrorState,
  Panel,
  ProjectCrumb,
  QaPage,
  useQaActionDialog,
} from "../../components/TestingUi";
import { testingApi } from "../../services/testing.service";
import { formatDate, messageOf } from "../../lib/testing";

const toggleSettings = [
  ["requirement_lint_blocking", "Chặn duyệt yêu cầu khi còn lỗi kiểm tra"],
  ["trace_before_baseline", "Bắt buộc truy vết trước khi baseline yêu cầu"],
  ["ba_can_approve_requirements", "Cho phép BA duyệt yêu cầu theo chính sách"],
  ["testcase_lint_blocking", "Chặn duyệt ca kiểm thử khi còn lỗi kiểm tra"],
  ["trace_before_testcase_approve", "Bắt buộc truy vết trước khi duyệt ca kiểm thử"],
  ["tester_can_create_run", "Cho phép Tester tạo Test Run"],
  ["tester_can_manage_runs", "Cho phép Tester quản lý Test Run"],
  ["tester_can_assign_runs", "Cho phép Tester gán Test Run và ca kiểm thử"],
  ["tester_can_start_runs", "Cho phép Tester bắt đầu Test Run"],
  ["tester_can_complete_runs", "Cho phép Tester hoàn tất Test Run"],
  ["tester_can_abort_runs", "Cho phép Tester huỷ Test Run"],
  ["tester_can_correct_results", "Cho phép Tester sửa kết quả bằng sự kiện hiệu chỉnh"],
  ["tester_can_assign_testplans", "Cho phép Tester phân công thành viên trong Test Plan"],
  ["partial_complete_allowed", "Cho phép hoàn tất một phần Test Run"],
  ["allow_not_applicable_results", "Cho phép kết quả Không áp dụng khi có lý do"],
  ["tester_can_close_defect", "Cho phép Tester đóng Defect"],
  ["tester_can_reject_defect", "Cho phép Tester từ chối Defect"],
  ["tester_can_mark_duplicate_defect", "Cho phép Tester đánh dấu Defect trùng"],
  ["ba_can_create_defect", "Cho phép BA tạo Defect"],
  ["developer_can_create_defect", "Cho phép Developer tạo Defect"],
  ["ba_can_update_defect", "Cho phép BA cập nhật Defect"],
  ["tester_can_confirm_trace", "Cho phép Tester xác nhận Trace"],
  ["tester_can_revoke_trace", "Cho phép Tester thu hồi Trace"],
  ["ba_can_confirm_trace", "Cho phép BA xác nhận Trace"],
  ["ba_can_revoke_trace", "Cho phép BA thu hồi Trace"],
  ["tester_can_override_impact", "Cho phép Tester override Impact"],
  ["tester_can_close_impact", "Cho phép Tester đóng Impact"],
  ["tester_can_manage_knowledge", "Cho phép Tester quản lý Knowledge"],
  ["tester_can_archive_testcase_templates", "Cho phép Tester lưu trữ mẫu ca kiểm thử"],
  ["viewer_can_export", "Cho phép Viewer xuất báo cáo"],
  ["developer_can_export", "Cho phép Developer xuất báo cáo"],
  ["ai_auto_draft", "Cho phép AI tạo bản nháp"],
];

const numberSettings = [
  ["impact_confidence_threshold", "Ngưỡng tin cậy Impact", 0, 1, 0.01],
  ["testcase_duplicate_threshold", "Ngưỡng phát hiện ca kiểm thử trùng", 0, 1, 0.01],
  ["impact_candidate_limit", "Số ứng viên Impact tối đa", 1, 5000, 1],
];

const selectSettings = [
  ["default_invite_role", "Vai trò mời mặc định", ["TESTER", "BA", "DEVELOPER", "VIEWER"]],
  ["read_after_archive_policy", "Quyền đọc sau khi lưu trữ", ["ALLOW_READ", "DENY_READ"]],
  ["default_environment", "Môi trường mặc định", ["development", "staging", "production"]],
];

export default function SettingsPage({ project, onProjectChange }) {
  const { ask, dialog } = useQaActionDialog();
  const [audit, setAudit] = useState([]);
  const [members, setMembers] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description || "");
  const [projectType, setProjectType] = useState(project.project_type || "web");
  const [locale, setLocale] = useState(project.locale || "vi-VN");
  const [timezone, setTimezone] = useState(project.timezone || "Asia/Ho_Chi_Minh");
  const [settings, setSettings] = useState({
    requirement_approval_required: project.settings?.requirement_approval_required ?? true,
    testcase_approval_required: project.settings?.testcase_approval_required ?? true,
    ai_auto_draft: project.settings?.ai_auto_draft ?? true,
    impact_confidence_threshold: project.settings?.impact_confidence_threshold ?? 0.75,
    ...Object.fromEntries(
      toggleSettings.map(([key]) => [
        key,
        project.settings?.[key] ??
          ["ai_auto_draft", "ba_can_create_defect", "developer_can_create_defect"].includes(key),
      ]),
    ),
    ...Object.fromEntries(
      numberSettings.map(([key, , , , step]) => [
        key,
        project.settings?.[key] ?? (step === 1 ? 100 : 0.75),
      ]),
    ),
    ...Object.fromEntries(
      selectSettings.map(([key, , values]) => [key, project.settings?.[key] ?? values[0]]),
    ),
  });
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([
      testingApi.audit(project._id),
      testingApi.maintenanceAnalytics(project._id),
      testingApi.aiAnalytics(project._id),
      testingApi.listMembers(project._id),
    ])
      .then(([events, value, aiValue, memberValues]) => {
        setAudit(events);
        setAnalytics({ ...value, ...aiValue });
        setMembers(memberValues);
      })
      .catch((reason) => setError(messageOf(reason)));
  }, [project._id]);
  return (
    <QaPage title="Cài đặt và kiểm toán" actions={<ProjectCrumb projectId={project._id} />}>
      {error && <ErrorState message={error} />}
      <div className="grid gap-5 xl:grid-cols-2">
        <Panel title="Thông tin dự án">
          <form
            className="space-y-4 p-5"
            onSubmit={async (event) => {
              event.preventDefault();
              try {
                await testingApi.updateProjectSettings(project._id, {
                  expected_revision: project.revision,
                  name,
                  description,
                  project_type: projectType,
                  locale,
                  timezone,
                  settings: {
                    ...(project.settings || {}),
                    ...settings,
                    action_policies: {
                      ...(project.settings?.action_policies || {}),
                      "defect.rejected": settings.tester_can_reject_defect
                        ? ["QA_LEAD", "TESTER"]
                        : ["QA_LEAD"],
                      "defect.duplicate": settings.tester_can_mark_duplicate_defect
                        ? ["QA_LEAD", "TESTER"]
                        : ["QA_LEAD"],
                      "testplan.assignments": settings.tester_can_assign_testplans
                        ? ["QA_LEAD", "TESTER"]
                        : ["QA_LEAD"],
                      "testcase.template.archive": settings.tester_can_archive_testcase_templates
                        ? ["QA_LEAD", "TESTER"]
                        : ["QA_LEAD"],
                    },
                  },
                });
                await onProjectChange();
              } catch (reason) {
                setError(messageOf(reason));
              }
            }}
          >
            <label className="field-label">
              Tên
              <input
                className="apple-input mt-2"
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </label>
            <div className="grid gap-3 rounded-xl border border-border p-4 sm:grid-cols-2">
              <label className="field-label">
                Loại dự án
                <select
                  className="apple-input mt-2"
                  value={projectType}
                  onChange={(event) => setProjectType(event.target.value)}
                >
                  {["web", "mobile", "api", "desktop", "embedded", "other"].map((value) => (
                    <option value={value} key={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field-label">
                Ngôn ngữ và vùng
                <input
                  className="apple-input mt-2"
                  value={locale}
                  onChange={(event) => setLocale(event.target.value)}
                />
              </label>
              <label className="field-label sm:col-span-2">
                Múi giờ
                <input
                  className="apple-input mt-2"
                  value={timezone}
                  onChange={(event) => setTimezone(event.target.value)}
                />
              </label>
            </div>
            <div className="space-y-3 rounded-xl border border-border p-4">
              <p className="text-[13px] font-semibold">Chính sách dự án</p>
              {toggleSettings.map(([key, label]) => (
                <label className="flex items-center gap-3 text-[13px]" key={key}>
                  <input
                    type="checkbox"
                    checked={Boolean(settings[key])}
                    onChange={(event) =>
                      setSettings((current) => ({ ...current, [key]: event.target.checked }))
                    }
                  />
                  {label}
                </label>
              ))}
              {numberSettings.map(([key, label, min, max, step]) => (
                <label className="field-label" key={key}>
                  {label}
                  <input
                    className="apple-input mt-2"
                    type="number"
                    min={min}
                    max={max}
                    step={step}
                    value={settings[key]}
                    onChange={(event) =>
                      setSettings((current) => ({ ...current, [key]: Number(event.target.value) }))
                    }
                  />
                </label>
              ))}
              {selectSettings.map(([key, label, values]) => (
                <label className="field-label" key={key}>
                  {label}
                  <select
                    className="apple-input mt-2"
                    value={settings[key]}
                    onChange={(event) =>
                      setSettings((current) => ({ ...current, [key]: event.target.value }))
                    }
                  >
                    {values.map((value) => (
                      <option value={value} key={value}>
                        {value}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
            <label className="field-label">
              Mô tả
              <textarea
                className="apple-input mt-2 min-h-28"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
              />
            </label>
            <button className="apple-button" type="submit">
              Lưu với phiên bản {project.revision}
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={async () => {
                const answer = await ask({
                  title: "Lưu trữ dự án",
                  description: `${project.key} sẽ ngừng nhận thay đổi mới nhưng vẫn giữ lịch sử và bằng chứng`,
                  confirmLabel: "Lưu trữ",
                  danger: true,
                  fields: [
                    {
                      name: "reason",
                      label: "Lý do lưu trữ",
                      initialValue: "Dự án đã kết thúc vòng đời hoạt động",
                      required: true,
                      multiline: true,
                      autoFocus: true,
                    },
                  ],
                });
                if (!answer) return;
                try {
                  await testingApi.archiveProject(project._id, {
                    expected_revision: project.revision,
                    reason: answer.reason,
                  });
                  window.location.assign("/du-an");
                } catch (value) {
                  setError(messageOf(value));
                }
              }}
            >
              Lưu trữ dự án
            </button>
          </form>
        </Panel>
        <Panel title="Thành viên dự án">
          <div className="space-y-3 p-5">
            <form
              className="grid gap-2 sm:grid-cols-[1fr_150px_auto]"
              onSubmit={async (event) => {
                event.preventDefault();
                const form = event.currentTarget;
                const value = new FormData(form);
                try {
                  await testingApi.inviteMember(project._id, {
                    user_id: value.get("user_id"),
                    project_role: value.get("project_role"),
                  });
                  form.reset();
                  setMembers(await testingApi.listMembers(project._id));
                } catch (reason) {
                  setError(messageOf(reason));
                }
              }}
            >
              <input
                className="apple-input"
                name="user_id"
                required
                placeholder="Mã người dùng"
                aria-label="Mã người dùng"
              />
              <select className="apple-input" name="project_role" aria-label="Vai trò dự án">
                <option value="TESTER">Kiểm thử viên</option>
                <option value="BA">Phân tích nghiệp vụ</option>
                <option value="DEVELOPER">Lập trình viên</option>
                <option value="VIEWER">Người xem</option>
                <option value="QA_LEAD">Trưởng nhóm kiểm thử</option>
              </select>
              <button className="secondary-button" type="submit">
                Gửi lời mời
              </button>
            </form>
            <DataTable
              items={members}
              empty="Chưa có thành viên"
              columns={[
                { key: "user_id", label: "Người dùng" },
                {
                  key: "project_role",
                  label: "Vai trò",
                  render: (item) => (
                    <select
                      aria-label={`Vai trò ${item.user_id}`}
                      className="apple-input"
                      value={item.project_role}
                      disabled={item.status !== "ACTIVE"}
                      onChange={async (event) => {
                        try {
                          await testingApi.updateMember(project._id, item.user_id, {
                            expected_revision: item.membership_revision,
                            project_role: event.target.value,
                          });
                          setMembers(await testingApi.listMembers(project._id));
                        } catch (reason) {
                          setError(messageOf(reason));
                        }
                      }}
                    >
                      {["QA_LEAD", "TESTER", "BA", "DEVELOPER", "VIEWER"].map((role) => (
                        <option key={role} value={role}>
                          {
                            {
                              QA_LEAD: "Trưởng nhóm kiểm thử",
                              TESTER: "Kiểm thử viên",
                              BA: "Phân tích nghiệp vụ",
                              DEVELOPER: "Lập trình viên",
                              VIEWER: "Người xem",
                            }[role]
                          }
                        </option>
                      ))}
                    </select>
                  ),
                },
                { key: "status", label: "Trạng thái" },
                { key: "membership_revision", label: "Lần sửa đổi" },
                {
                  key: "actions",
                  label: "Thao tác",
                  render: (item) => (
                    <span className="flex flex-wrap gap-2">
                      {item.status === "INVITED" ? (
                        <>
                          <button
                            className="secondary-button"
                            type="button"
                            onClick={async () => {
                              try {
                                await testingApi.resendMemberInvite(project._id, item.user_id);
                                setMembers(await testingApi.listMembers(project._id));
                              } catch (reason) {
                                setError(messageOf(reason));
                              }
                            }}
                          >
                            Gửi lại lời mời
                          </button>
                          <button
                            className="secondary-button"
                            type="button"
                            onClick={async () => {
                              try {
                                await testingApi.cancelMemberInvite(project._id, item.user_id);
                                setMembers(await testingApi.listMembers(project._id));
                              } catch (reason) {
                                setError(messageOf(reason));
                              }
                            }}
                          >
                            Hủy lời mời
                          </button>
                        </>
                      ) : item.status !== "CANCELLED" ? (
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={async () => {
                            try {
                              await testingApi.updateMember(project._id, item.user_id, {
                                expected_revision: item.membership_revision,
                                status: item.status === "ACTIVE" ? "INACTIVE" : "ACTIVE",
                              });
                              setMembers(await testingApi.listMembers(project._id));
                            } catch (reason) {
                              setError(messageOf(reason));
                            }
                          }}
                        >
                          {item.status === "ACTIVE" ? "Vô hiệu hóa" : "Kích hoạt"}
                        </button>
                      ) : null}
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={async () => {
                          const answer = await ask({
                            title: "Xóa thành viên khỏi dự án",
                            description: `${item.user_id} sẽ mất toàn bộ quyền truy cập dự án này`,
                            confirmLabel: "Xóa thành viên",
                            danger: true,
                          });
                          if (!answer) return;
                          try {
                            await testingApi.removeMember(project._id, item.user_id);
                            setMembers(await testingApi.listMembers(project._id));
                          } catch (reason) {
                            setError(messageOf(reason));
                          }
                        }}
                      >
                        Xóa
                      </button>
                    </span>
                  ),
                },
              ]}
            />
          </div>
        </Panel>
        <Panel title="Phân tích bảo trì">
          <div className="grid grid-cols-2 gap-4 p-5">
            <div>
              <p className="text-3xl font-semibold">{analytics?.impact_analysis_count || 0}</p>
              <p className="field-label mt-2">Phân tích ảnh hưởng</p>
            </div>
            <div>
              <p className="text-3xl font-semibold">{analytics?.tests_stale || 0}</p>
              <p className="field-label mt-2">Ca kiểm thử cũ</p>
            </div>
            <div>
              <p className="text-3xl font-semibold">
                {analytics?.proposal_acceptance_rate == null
                  ? "Chưa có dữ liệu"
                  : `${Math.round(analytics.proposal_acceptance_rate * 100)}%`}
              </p>
              <p className="field-label mt-2">Tỷ lệ chấp nhận đề xuất</p>
            </div>
          </div>
        </Panel>
      </div>
      <ProjectNotificationsPanel project={project} />
      <ProjectConnectorsPanel project={project} />
      <CicdPanel project={project} />
      <WebhookPanel project={project} />
      <Panel title="Nhật ký kiểm toán">
        <DataTable
          items={audit}
          empty="Chưa có sự kiện"
          columns={[
            { key: "action", label: "Hành động" },
            { key: "artifact_type", label: "Loại dữ liệu" },
            { key: "artifact_id", label: "Mã" },
            { key: "actor_id", label: "Người thực hiện" },
            {
              key: "created_at",
              label: "Thời điểm",
              render: (item) => formatDate(item.created_at),
            },
          ]}
        />
      </Panel>
      {dialog}
    </QaPage>
  );
}
