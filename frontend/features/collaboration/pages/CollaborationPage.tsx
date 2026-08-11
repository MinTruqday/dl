"use client";

import { useState } from "react";
import InlineState from "@/shared/components/common/InlineState";
import MetricStrip from "@/shared/components/data-display/MetricStrip";
import PageHeader from "@/shared/components/layout/PageHeader";
import SegmentedTabs from "@/shared/components/navigation/SegmentedTabs";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";
import { useCollaboration } from "../hooks/useCollaboration";

type Tab =
  | "people"
  | "settings"
  | "share_link"
  | "requests"
  | "tasks"
  | "snapshots"
  | "invites";

function roleLabel(role?: string) {
  if (role === "editor") return "Chỉnh sửa";
  if (role === "commenter") return "Bình luận";
  if (role === "viewer") return "Chỉ xem";
  return "Chưa xác định";
}

function modeLabel(mode?: string) {
  if (mode === "COMMENT_ONLY") return "Chỉ bình luận";
  if (mode === "READ_ONLY") return "Chỉ xem";
  if (mode === "CLOSED") return "Đóng hoàn toàn";
  return "Mở đầy đủ";
}

export default function CollaborationPage() {
  const state = useCollaboration();
  useNoticeToast(state.notice);
  const [tab, setTab] = useState<Tab>("people");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("editor");
  const [task, setTask] = useState("");
  const [assignee, setAssignee] = useState("");
  const [snapshot, setSnapshot] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [sharePassword, setSharePassword] = useState("");
  const [shareRole, setShareRole] = useState("editor");
  const [shareActive, setShareActive] = useState(true);
  const [shareExpiresHours, setShareExpiresHours] = useState("");
  const [joinLinkToken, setJoinLinkToken] = useState("");
  const [joinLinkPassword, setJoinLinkPassword] = useState("");
  const [reqDocId, setReqDocId] = useState("");
  const [reqRole, setReqRole] = useState("editor");
  const [reqMessage, setReqMessage] = useState("");
  const [selectedMode, setSelectedMode] = useState<string>("");
  const [localSchedules, setLocalSchedules] = useState<any[]>([]);
  const [schedTitle, setSchedTitle] = useState("");
  const [schedStart, setSchedStart] = useState("");
  const [schedEnd, setSchedEnd] = useState("");
  const [schedMode, setSchedMode] = useState("EDIT");
  const [schedFallback, setSchedFallback] = useState("READ_ONLY");

  const currentMode = selectedMode || state.collabMode || "OPEN";
  const activeSchedulesList = localSchedules.length > 0 ? localSchedules : state.collabSchedules;


  if (state.loading && !state.documents.length) return <PageLoader rows={7} />;
  return (
    <div className="w-full">
      <PageHeader
        title="Cộng tác"
        actions={
          <>
            <Button
              variant="secondary"
              disabled={!state.documentId || Boolean(state.processing)}
              onClick={state.toggleLock}
            >
              {state.lock.is_locked ? "Mở khóa phiên" : "Khóa phiên"}
            </Button>
            <Button
              variant="secondary"
              disabled={!state.documentId || Boolean(state.processing)}
              onClick={state.generateCode}
            >
              Tạo mã mời
            </Button>
          </>
        }
        meta={
          <label className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center sm:gap-3">
            <span className="font-semibold text-ink">Tài liệu</span>
            <select
              value={state.documentId}
              onChange={(event) => state.setDocumentId(event.target.value)}
              className="apple-input w-full min-w-0 sm:min-w-64"
            >
              <option value="">Chọn tài liệu</option>
              {state.documents.map((document) => (
                <option
                  key={document._id ?? document.id}
                  value={document._id ?? document.id}
                >
                  {document.title || "Chưa đặt tên"}
                </option>
              ))}
            </select>
          </label>
        }
      />
      {state.error && (
        <div className="mb-6">
          <InlineState
            title="Không thể xử lý cộng tác"
            detail={state.error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={state.reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}
      {state.inviteCode && (
        <div className="mb-6">
          <InlineState title="Mã mời đã sẵn sàng" detail={state.inviteCode} />
        </div>
      )}
      {!state.documentId ? (
        <InlineState
          title={state.documents.length ? "Chọn tài liệu để bắt đầu" : "Chưa có tài liệu"}
          detail={state.documents.length ? undefined : "Tạo tài liệu trước khi sử dụng không gian cộng tác"}
        />
      ) : (
        <>
          <MetricStrip
            items={[
              { label: "Cộng tác viên", value: state.collaborators.length },
              { label: "Đang trực tuyến", value: state.online.length },
              {
                label: "Chế độ truy cập",
                value:
                  state.collabMode === "CLOSED"
                    ? "Đóng hoàn toàn"
                    : state.collabMode === "READ_ONLY"
                    ? "Chỉ xem"
                    : state.collabMode === "COMMENT_ONLY"
                    ? "Chỉ bình luận"
                    : "Mở đầy đủ",
              },
              { label: "Yêu cầu xin quyền", value: state.accessRequests.length },
            ]}
          />
          <div className="my-6">
            <SegmentedTabs<Tab>
              label="Nội dung cộng tác"
              value={tab}
              onChange={setTab}
              tabs={[
                { id: "people", label: "Thành viên" },
                { id: "settings", label: "Đóng mở & Hẹn giờ" },
                { id: "share_link", label: "Liên kết chia sẻ" },
                { id: "requests", label: "Yêu cầu xin quyền" },
                { id: "tasks", label: "Công việc" },
                { id: "snapshots", label: "Bản chụp phiên" },
                { id: "invites", label: "Lời mời" },
              ]}
            />
          </div>
          {tab === "settings" && (
            <div className="space-y-6">
              <section className="rounded-panel border border-border bg-surface p-5">
                <div className="mb-4">
                  <h2 className="text-[16px] font-semibold text-ink">
                    Trạng thái đóng mở tài liệu
                  </h2>
                  <p className="mt-1 text-[13px] text-ink-muted">
                    Kiểm soát quyền truy cập và thao tác của tất cả cộng tác viên và liên kết chia sẻ
                  </p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {[
                    {
                      id: "OPEN",
                      title: "Mở đầy đủ",
                      desc: "Cho phép xem, bình luận và chỉnh sửa nội dung theo vai trò",
                    },
                    {
                      id: "COMMENT_ONLY",
                      title: "Chỉ bình luận",
                      desc: "Chỉ cho phép đọc và để lại bình luận, không cho chỉnh sửa",
                    },
                    {
                      id: "READ_ONLY",
                      title: "Chỉ xem",
                      desc: "Khóa toàn bộ thao tác nhập, chỉ cho phép đọc nội dung",
                    },
                    {
                      id: "CLOSED",
                      title: "Đóng hoàn toàn",
                      desc: "Khóa không gian, liên kết ngoài không thể truy cập",
                    },
                  ].map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setSelectedMode(item.id)}
                      className={`flex flex-col text-left rounded-xl border p-4 transition ${
                        currentMode === item.id
                          ? "border-primary bg-primary/5 text-primary ring-2 ring-primary/20"
                          : "border-border bg-surface-hover/30 hover:border-ink/20"
                      }`}
                    >
                      <span className="font-semibold text-[14px] text-ink">{item.title}</span>
                      <span className="mt-1 text-[12px] text-ink-muted">{item.desc}</span>
                    </button>
                  ))}
                </div>
                <div className="mt-5 flex items-center justify-between border-t border-border pt-4">
                  <div className="text-[13px] text-ink-muted">
                    Trạng thái thực thi hiện tại:{" "}
                    <span className="font-semibold text-ink">
                      {modeLabel(state.effectiveStatus?.effective_mode ?? state.collabMode)}
                    </span>
                  </div>
                  <Button
                    disabled={Boolean(state.processing)}
                    onClick={() => state.updateCollaborationMode(currentMode)}
                  >
                    Lưu chế độ truy cập
                  </Button>
                </div>
              </section>

              <section className="rounded-panel border border-border bg-surface p-5">
                <div className="mb-4">
                  <h2 className="text-[16px] font-semibold text-ink">
                    Lịch hẹn giờ quyền hạn cộng tác
                  </h2>
                  <p className="mt-1 text-[13px] text-ink-muted">
                    Thiết lập nhiều khung giờ cho phép chỉnh sửa hoặc bình luận, tự động chuyển về chỉ xem hoặc đóng khi hết giờ
                  </p>
                </div>

                <div className="space-y-3 mb-6">
                  {activeSchedulesList.length === 0 ? (
                    <div className="rounded-lg border border-dashed border-border p-4 text-center text-[13px] text-ink-muted">
                      Chưa thiết lập khung giờ hẹn. Tài liệu sẽ áp dụng chế độ đóng mở mặc định.
                    </div>
                  ) : (
                    activeSchedulesList.map((sch: any, idx: number) => (
                      <div
                        key={sch.id || idx}
                        className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-surface-hover/40 p-3"
                      >
                        <div className="min-w-0 flex-1">
                          <p className="font-medium text-[14px] text-ink">{sch.title || "Khung giờ hẹn"}</p>
                          <p className="mt-0.5 text-[12px] text-ink-muted">
                            {sch.start_at ? `Từ ${new Date(sch.start_at).toLocaleString("vi-VN")} ` : "Bắt đầu ngay "}
                            đến {new Date(sch.end_at).toLocaleString("vi-VN")}
                          </p>
                          <div className="mt-1 flex items-center gap-2 text-[11px]">
                            <span className="rounded bg-primary/10 px-2 py-0.5 font-medium text-primary">
                              Trong giờ: {sch.mode === "EDIT" ? "Chỉnh sửa" : sch.mode === "COMMENT_ONLY" ? "Chỉ bình luận" : "Chỉ xem"}
                            </span>
                            <span className="rounded bg-amber-500/10 px-2 py-0.5 font-medium text-amber-700">
                              Hết giờ: {sch.fallback_mode === "CLOSED" ? "Đóng hoàn toàn" : "Chỉ xem"}
                            </span>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            const updated = activeSchedulesList.filter((_: any, i: number) => i !== idx);
                            setLocalSchedules(updated);
                          }}
                        >
                          Xóa
                        </Button>
                      </div>
                    ))
                  )}
                </div>

                <div className="rounded-lg border border-border bg-surface-hover/20 p-4">
                  <h3 className="mb-3 text-[14px] font-semibold text-ink">Thêm khung giờ mới</h3>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <div>
                      <label className="mb-1 block text-[12px] text-ink-muted">Tên khung giờ</label>
                      <input
                        type="text"
                        placeholder="Ví dụ: Giờ sửa bài tập"
                        value={schedTitle}
                        onChange={(e) => setSchedTitle(e.target.value)}
                        className="apple-input w-full"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-[12px] text-ink-muted">Bắt đầu (tùy chọn)</label>
                      <input
                        type="datetime-local"
                        value={schedStart}
                        onChange={(e) => setSchedStart(e.target.value)}
                        className="apple-input w-full"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-[12px] text-ink-muted">Kết thúc (bắt buộc)</label>
                      <input
                        type="datetime-local"
                        value={schedEnd}
                        onChange={(e) => setSchedEnd(e.target.value)}
                        className="apple-input w-full"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-[12px] text-ink-muted">Quyền hạn trong khung giờ</label>
                      <select
                        value={schedMode}
                        onChange={(e) => setSchedMode(e.target.value)}
                        className="apple-input w-full"
                      >
                        <option value="EDIT">Cho phép chỉnh sửa</option>
                        <option value="COMMENT_ONLY">Chỉ cho phép bình luận</option>
                        <option value="READ_ONLY">Chỉ cho phép xem</option>
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-[12px] text-ink-muted">Hành vi sau khi hết giờ</label>
                      <select
                        value={schedFallback}
                        onChange={(e) => setSchedFallback(e.target.value)}
                        className="apple-input w-full"
                      >
                        <option value="READ_ONLY">Chuyển sang chỉ xem</option>
                        <option value="CLOSED">Đóng hoàn toàn tài liệu</option>
                      </select>
                    </div>
                    <div className="flex items-end">
                      <Button
                        type="button"
                        variant="secondary"
                        className="w-full"
                        disabled={!schedEnd}
                        onClick={() => {
                          if (!schedEnd) return;
                          const newRule = {
                            id: Math.random().toString(36).substring(2, 9),
                            title: schedTitle.trim() || "Khung giờ hẹn",
                            start_at: schedStart ? new Date(schedStart).toISOString() : null,
                            end_at: new Date(schedEnd).toISOString(),
                            mode: schedMode,
                            fallback_mode: schedFallback,
                            is_active: true,
                          };
                          setLocalSchedules([...activeSchedulesList, newRule]);
                          setSchedTitle("");
                          setSchedStart("");
                          setSchedEnd("");
                        }}
                      >
                        Thêm khung giờ
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="mt-5 flex justify-end">
                  <Button
                    disabled={Boolean(state.processing)}
                    onClick={() => state.updateCollaborationSchedules(activeSchedulesList)}
                  >
                    Lưu toàn bộ lịch hẹn giờ
                  </Button>
                </div>
              </section>
            </div>
          )}
          {tab === "people" && (

            <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
              <section className="overflow-hidden rounded-panel border border-border bg-surface">
                {state.collaborators.length ? <ul>
                  {state.collaborators.map((person) => {
                    const id = person._id ?? person.id;
                    return (
                      <li
                        key={id}
                        className="flex items-center justify-between gap-4 border-b border-border p-4 last:border-b-0"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-[14px] font-semibold text-ink">
                            {person.email || person.user_name || person.user_id}
                          </p>
                          <p className="mt-1 text-[12px] text-ink-muted">
                            {roleLabel(person.role)}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <select
                            aria-label="Vai trò"
                            value={person.role}
                            onChange={(event) =>
                              state.updateRole(id, event.target.value)
                            }
                            className="apple-input"
                          >
                            <option value="viewer">Xem</option>
                            <option value="commenter">Bình luận</option>
                            <option value="editor">Sửa</option>
                          </select>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => state.remove(id)}
                          >
                            Thu hồi
                          </Button>
                        </div>
                      </li>
                    );
                  })}
                </ul> : <InlineState title="Chưa có thành viên cộng tác" />}
              </section>
              <aside className="space-y-5">
                <div className="rounded-panel border border-border bg-surface p-5">
                  <h2 className="text-[16px] font-semibold text-ink">
                    Mời thành viên
                  </h2>
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="apple-input mt-4 w-full"
                    placeholder="Email người nhận"
                  />
                  <select
                    value={role}
                    onChange={(event) => setRole(event.target.value)}
                    className="apple-input mt-3 w-full"
                  >
                    <option value="editor">Chỉnh sửa</option>
                    <option value="commenter">Bình luận</option>
                    <option value="viewer">Chỉ xem</option>
                  </select>
                  <Button
                    className="mt-3 w-full"
                    disabled={!email.trim()}
                    onClick={() => state.invite(email, role)}
                  >
                    Gửi lời mời
                  </Button>
                </div>
              </aside>
            </div>
          )}
          {tab === "share_link" && (
            <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
              <section className="rounded-panel border border-border bg-surface p-5 space-y-4">
                <h2 className="text-[16px] font-semibold text-ink">
                  Cấu hình liên kết cộng tác
                </h2>
                {state.shareConfig?.share_token && (
                  <div className="rounded-card border border-border bg-subtle p-4 space-y-2">
                    <p className="text-[13px] font-semibold text-ink">
                      Mã liên kết phòng cộng tác:
                    </p>
                    <p className="font-mono text-[13px] text-ink break-all select-all">
                      {state.shareConfig.share_token}
                    </p>
                    <div className="flex flex-wrap gap-2 text-[12px] text-ink-muted">
                      <span>
                        Trạng thái:{" "}
                        {state.shareConfig.is_active ? "Đang bật" : "Đã tắt"}
                      </span>
                      <span>•</span>
                      <span>
                        Bảo vệ mật khẩu:{" "}
                        {state.shareConfig.is_password_protected ? "Có" : "Không"}
                      </span>
                      <span>•</span>
                      <span>Vai trò mặc định: {state.shareConfig.default_role}</span>
                    </div>
                  </div>
                )}
                <div className="space-y-3">
                  <label className="flex items-center gap-2 text-[13px] text-ink cursor-pointer">
                    <input
                      type="checkbox"
                      checked={shareActive}
                      onChange={(e) => setShareActive(e.target.checked)}
                      className="h-4 w-4 accent-[hsl(var(--brand))]"
                    />
                    <span>Kích hoạt liên kết chia sẻ</span>
                  </label>
                  <div>
                    <label className="block text-[13px] font-semibold text-ink mb-1">
                      Mật khẩu truy cập phòng cộng tác (để trống nếu không cần)
                    </label>
                    <input
                      type="password"
                      value={sharePassword}
                      onChange={(e) => setSharePassword(e.target.value)}
                      placeholder="Nhập mật khẩu riêng cho liên kết"
                      className="apple-input w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-[13px] font-semibold text-ink mb-1">
                      Vai trò được cấp mặc định
                    </label>
                    <select
                      value={shareRole}
                      onChange={(e) => setShareRole(e.target.value)}
                      className="apple-input w-full"
                    >
                      <option value="editor">Người biên tập (Editor)</option>
                      <option value="commenter">Người bình luận (Commenter)</option>
                      <option value="viewer">Người xem (Viewer)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[13px] font-semibold text-ink mb-1">
                      Thời hạn hiệu lực (giờ, để trống nếu vô hạn)
                    </label>
                    <input
                      type="number"
                      value={shareExpiresHours}
                      onChange={(e) => setShareExpiresHours(e.target.value)}
                      placeholder="Ví dụ: 24"
                      className="apple-input w-full"
                    />
                  </div>
                  <Button
                    onClick={() =>
                      state.configureShareLink({
                        is_active: shareActive,
                        password: sharePassword || undefined,
                        default_role: shareRole,
                        expires_in_hours: shareExpiresHours
                          ? parseInt(shareExpiresHours, 10)
                          : undefined,
                      })
                    }
                  >
                    Lưu cấu hình liên kết
                  </Button>
                </div>
              </section>
              <aside className="rounded-panel border border-border bg-surface p-5 space-y-4">
                <h2 className="text-[16px] font-semibold text-ink">
                  Tham gia qua liên kết
                </h2>
                <div>
                  <label className="block text-[13px] font-semibold text-ink mb-1">
                    Mã liên kết phòng
                  </label>
                  <input
                    value={joinLinkToken}
                    onChange={(e) => setJoinLinkToken(e.target.value)}
                    placeholder="Dán mã liên kết "
                    className="apple-input w-full"
                  />
                </div>
                <div>
                  <label className="block text-[13px] font-semibold text-ink mb-1">
                    Mật khẩu phòng (nếu có)
                  </label>
                  <input
                    type="password"
                    value={joinLinkPassword}
                    onChange={(e) => setJoinLinkPassword(e.target.value)}
                    placeholder="Nhập mật khẩu"
                    className="apple-input w-full"
                  />
                </div>
                <Button
                  className="w-full"
                  disabled={!joinLinkToken.trim()}
                  onClick={() =>
                    state.joinViaShareLink(joinLinkToken, joinLinkPassword)
                  }
                >
                  Tham gia phòng cộng tác
                </Button>
              </aside>
            </div>
          )}
          {tab === "requests" && (
            <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
              <section className="overflow-hidden rounded-panel border border-border bg-surface">
                <div className="p-4 border-b border-border font-semibold text-ink">
                  Yêu cầu xin quyền tới tài liệu của bạn
                </div>
                {state.accessRequests.length === 0 ? (
                  <div className="p-6 text-center text-ink-muted text-[14px]">
                    Không có yêu cầu xin quyền nào đang chờ duyệt
                  </div>
                ) : (
                  <ul>
                    {state.accessRequests.map((req) => (
                      <li
                        key={req.id}
                        className="flex items-center justify-between gap-4 border-b border-border p-4 last:border-b-0"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-[14px] font-semibold text-ink">
                            {req.user_name || req.user_email || req.user_id}
                          </p>
                          <p className="text-[12px] text-ink-muted mt-1">
                            Tài liệu: {req.document_title || req.document_id} • Vai trò xin:{" "}
                            <span className="font-semibold text-ink">
                              {req.requested_role}
                            </span>
                          </p>
                          {req.message && (
                            <p className="text-[13px] text-ink mt-1 italic">
                              &ldquo;{req.message}&rdquo;
                            </p>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() =>
                              state.reviewAccessRequest(req.id, "ACCEPTED")
                            }
                          >
                            Duyệt
                          </Button>
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() =>
                              state.reviewAccessRequest(req.id, "REJECTED")
                            }
                          >
                            Từ chối
                          </Button>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
              <aside className="rounded-panel border border-border bg-surface p-5 space-y-4">
                <h2 className="text-[16px] font-semibold text-ink">
                  Gửi yêu cầu xin tham gia
                </h2>
                <div>
                  <label className="block text-[13px] font-semibold text-ink mb-1">
                    Mã tài liệu
                  </label>
                  <input
                    value={reqDocId}
                    onChange={(e) => setReqDocId(e.target.value)}
                    placeholder="Nhập mã tài liệu"
                    className="apple-input w-full"
                  />
                </div>
                <div>
                  <label className="block text-[13px] font-semibold text-ink mb-1">
                    Vai trò mong muốn
                  </label>
                  <select
                    value={reqRole}
                    onChange={(e) => setReqRole(e.target.value)}
                    className="apple-input w-full"
                  >
                    <option value="editor">Người biên tập</option>
                    <option value="commenter">Người bình luận</option>
                    <option value="viewer">Người xem</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[13px] font-semibold text-ink mb-1">
                    Lời nhắn gửi chủ tài liệu
                  </label>
                  <textarea
                    value={reqMessage}
                    onChange={(e) => setReqMessage(e.target.value)}
                    placeholder="Lý do xin tham gia"
                    className="apple-input min-h-20 w-full"
                  />
                </div>
                <Button
                  className="w-full"
                  disabled={!reqDocId.trim()}
                  onClick={() => state.requestAccess(reqDocId, reqRole, reqMessage)}
                >
                  Gửi yêu cầu
                </Button>
              </aside>
            </div>
          )}
          {tab === "tasks" && (
            <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
              <ul className="overflow-hidden rounded-panel border border-border bg-surface">
                {state.tasks.length ? state.tasks.map((item) => {
                  const id = item._id ?? item.id;
                  return (
                    <li
                      key={id}
                      className="flex items-start gap-3 border-b border-border p-4 last:border-b-0"
                    >
                      <input
                        type="checkbox"
                        checked={Boolean(item.is_done)}
                        onChange={(event) =>
                          state.toggleTask(id, event.target.checked)
                        }
                        className="mt-1 h-4 w-4 accent-[hsl(var(--brand))]"
                      />
                      <div>
                        <p
                          className={`text-[14px] font-semibold ${item.is_done ? "text-ink-muted line-through" : "text-ink"}`}
                        >
                          {item.task_desc || item.description}
                        </p>
                        <p className="mt-1 text-[12px] text-ink-muted">
                          {item.assigned_to || "Chưa phân công"}
                        </p>
                      </div>
                    </li>
                  );
                }) : <li><InlineState title="Chưa có công việc" /></li>}
              </ul>
              <aside className="rounded-panel border border-border bg-surface p-5">
                <h2 className="text-[16px] font-semibold text-ink">
                  Tạo công việc
                </h2>
                <textarea
                  value={task}
                  onChange={(event) => setTask(event.target.value)}
                  className="apple-input mt-4 min-h-24 w-full"
                />
                <input
                  value={assignee}
                  onChange={(event) => setAssignee(event.target.value)}
                  className="apple-input mt-3 w-full"
                  placeholder="Mã người phụ trách"
                />
                <Button
                  className="mt-3 w-full"
                  disabled={!task.trim()}
                  onClick={() => state.createTask(task, assignee)}
                >
                  Tạo
                </Button>
              </aside>
            </div>
          )}
          {tab === "snapshots" && (
            <div className="grid gap-6 lg:grid-cols-2">
              <section>
                <h2 className="mb-3 text-[16px] font-semibold text-ink">
                  Bản chụp phiên
                </h2>
                <ul className="overflow-hidden rounded-panel border border-border bg-surface">
                  {state.snapshots.length ? state.snapshots.map((item, index) => (
                    <li
                      key={item._id ?? item.id ?? index}
                      className="border-b border-border p-4 text-[14px] text-ink last:border-b-0"
                    >
                      {item.version_name || item.name}
                    </li>
                  )) : <li><InlineState title="Chưa có bản chụp phiên" /></li>}
                </ul>
                <div className="mt-3 flex gap-2">
                  <input
                    value={snapshot}
                    onChange={(event) => setSnapshot(event.target.value)}
                    className="apple-input min-w-0 flex-1"
                  />
                  <Button
                    disabled={!snapshot.trim()}
                    onClick={() => state.snapshot(snapshot)}
                  >
                    Tạo bản chụp
                  </Button>
                </div>
              </section>
            </div>
          )}
          {tab === "invites" && (
            <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
              <ul className="overflow-hidden rounded-panel border border-border bg-surface">
                {state.invites.length ? state.invites.map((invite) => {
                  const id = invite._id ?? invite.id;
                  return (
                    <li
                      key={id}
                      className="flex items-center justify-between gap-4 border-b border-border p-4 last:border-b-0"
                    >
                      <div>
                        <p className="text-[14px] font-semibold text-ink">
                          {invite.document_title ||
                            invite.email ||
                            "Lời mời cộng tác"}
                        </p>
                        <p className="mt-1 text-[12px] text-ink-muted">
                          {invite.role}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={() => state.respond(id, "ACCEPTED")}
                        >
                          Chấp nhận
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => state.respond(id, "REJECTED")}
                        >
                          Từ chối
                        </Button>
                      </div>
                    </li>
                  );
                }) : <li><InlineState title="Chưa có lời mời cộng tác" /></li>}
              </ul>
              <aside className="rounded-panel border border-border bg-surface p-5">
                <h2 className="text-[16px] font-semibold text-ink">
                  Tham gia bằng mã
                </h2>
                <input
                  value={joinCode}
                  onChange={(event) => setJoinCode(event.target.value)}
                  className="apple-input mt-4 w-full"
                />
                <Button
                  className="mt-3 w-full"
                  disabled={!joinCode.trim()}
                  onClick={() => state.join(joinCode)}
                >
                  Tham gia
                </Button>
              </aside>
            </div>
          )}
        </>
      )}
    </div>
  );
}
