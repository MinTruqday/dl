"use client";
import { useEffect, useState } from "react";
import DataTable from "../../components/DataTable";
import {
  ErrorState,
  Panel,
  ProjectCrumb,
  QaPage,
  useQaActionDialog,
} from "../../components/TestingUi";
import { testingApi } from "../../services/testing.service";
import { formatDate, messageOf } from "../../lib/testing";

export default function SettingsPage({ project, onProjectChange }) {
  const { ask, dialog } = useQaActionDialog();
  const [audit, setAudit] = useState([]);
  const [members, setMembers] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description || "");
  const [settings, setSettings] = useState({
    requirement_approval_required: project.settings?.requirement_approval_required ?? true,
    testcase_approval_required: project.settings?.testcase_approval_required ?? true,
    ai_auto_draft: project.settings?.ai_auto_draft ?? true,
    impact_confidence_threshold: project.settings?.impact_confidence_threshold ?? 0.75,
  });
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([
      testingApi.audit(project._id),
      testingApi.maintenanceAnalytics(project._id),
      testingApi.listMembers(project._id),
    ])
      .then(([events, value, memberValues]) => {
        setAudit(events);
        setAnalytics(value);
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
                await testingApi.updateProject(project._id, {
                  expected_revision: project.revision,
                  name,
                  description,
                  settings: {
                    ...(project.settings || {}),
                    ...settings,
                    requirement_approval_required: true,
                    testcase_approval_required: true,
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
            <div className="space-y-3 rounded-xl border border-border p-4">
              <p className="text-[13px] font-semibold">Phê duyệt yêu cầu luôn bắt buộc</p>
              <p className="text-[13px] font-semibold">Phê duyệt ca kiểm thử luôn bắt buộc</p>
              <label className="flex items-center gap-3 text-[13px]">
                <input
                  type="checkbox"
                  checked={settings.ai_auto_draft}
                  onChange={(event) =>
                    setSettings({ ...settings, ai_auto_draft: event.target.checked })
                  }
                />
                Cho phép AI tạo bản nháp
              </label>
              <label className="field-label">
                Ngưỡng tin cậy phân tích ảnh hưởng
                <input
                  className="apple-input mt-2"
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={settings.impact_confidence_threshold}
                  onChange={(event) =>
                    setSettings({
                      ...settings,
                      impact_confidence_threshold: Number(event.target.value),
                    })
                  }
                />
              </label>
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
                  window.location.assign("/qa/projects");
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
                const value = new FormData(event.currentTarget);
                try {
                  await testingApi.inviteMember(project._id, {
                    user_id: value.get("user_id"),
                    project_role: value.get("project_role"),
                  });
                  event.currentTarget.reset();
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
