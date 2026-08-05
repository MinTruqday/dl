"use client";

import { useState } from "react";
import InlineState from "@/app/_components/InlineState";
import MetricStrip from "@/app/_components/MetricStrip";
import PageHeader from "@/app/_components/PageHeader";
import SegmentedTabs from "@/app/_components/SegmentedTabs";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { useCollaboration } from "./useCollaboration";

type Tab =
  | "people"
  | "tasks"
  | "notes"
  | "invites"
  | "share_link"
  | "requests";

export default function CollaborationPage() {
  const state = useCollaboration();
  const [tab, setTab] = useState<Tab>("people");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("editor");
  const [task, setTask] = useState("");
  const [assignee, setAssignee] = useState("");
  const [memo, setMemo] = useState("");
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
          <label className="flex items-center gap-3">
            <span className="font-semibold text-ink">Tài liệu</span>
            <select
              value={state.documentId}
              onChange={(event) => state.setDocumentId(event.target.value)}
              className="apple-input min-w-64"
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
      {state.notice && (
        <div className="mb-6">
          <InlineState
            title={state.notice}
            action={
              <Button variant="ghost" onClick={state.clearNotice}>
                Đóng
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
          title="Chưa có tài liệu"
          detail="Chọn hoặc tạo tài liệu để cộng tác"
        />
      ) : (
        <>
          <MetricStrip
            items={[
              { label: "Cộng tác viên", value: state.collaborators.length },
              { label: "Đang trực tuyến", value: state.online.length },
              {
                label: "Công việc mở",
                value: state.tasks.filter((item) => !item.is_done).length,
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
                { id: "share_link", label: "Liên kết chia sẻ" },
                { id: "requests", label: "Yêu cầu xin quyền" },
                { id: "tasks", label: "Công việc" },
                { id: "notes", label: "Ghi chú" },
                { id: "invites", label: "Lời mời" },
              ]}
            />
          </div>
          {tab === "people" && (
            <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
              <section className="overflow-hidden rounded-panel border border-border bg-surface">
                <ul>
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
                            {person.role}
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
                </ul>
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
                      placeholder="Nhập mật khẩu riêng cho link..."
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
                    placeholder="Dán mã liên kết..."
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
                    placeholder="Nhập mật khẩu..."
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
                    Mã tài liệu (Document ID)
                  </label>
                  <input
                    value={reqDocId}
                    onChange={(e) => setReqDocId(e.target.value)}
                    placeholder="Nhập ID tài liệu..."
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
                    <option value="editor">Người biên tập (Editor)</option>
                    <option value="commenter">Người bình luận (Commenter)</option>
                    <option value="viewer">Người xem (Viewer)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[13px] font-semibold text-ink mb-1">
                    Lời nhắn gửi chủ tài liệu
                  </label>
                  <textarea
                    value={reqMessage}
                    onChange={(e) => setReqMessage(e.target.value)}
                    placeholder="Lý do xin tham gia..."
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
                {state.tasks.map((item) => {
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
                })}
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
          {tab === "notes" && (
            <div className="grid gap-6 lg:grid-cols-2">
              <section>
                <h2 className="mb-3 text-[16px] font-semibold text-ink">
                  Ghi chú nhóm
                </h2>
                <ul className="overflow-hidden rounded-panel border border-border bg-surface">
                  {state.memos.map((item, index) => (
                    <li
                      key={item._id ?? item.id ?? index}
                      className="border-b border-border p-4 last:border-b-0"
                    >
                      <p className="text-[14px] leading-relaxed text-ink">
                        {item.message}
                      </p>
                      <p className="mt-2 text-[12px] text-ink-muted">
                        {item.created_at
                          ? new Date(item.created_at).toLocaleString("vi-VN")
                          : ""}
                      </p>
                    </li>
                  ))}
                </ul>
                <textarea
                  value={memo}
                  onChange={(event) => setMemo(event.target.value)}
                  className="apple-input mt-3 min-h-24 w-full"
                />
                <Button
                  className="mt-2"
                  disabled={!memo.trim()}
                  onClick={() => state.sendMemo(memo)}
                >
                  Gửi ghi chú
                </Button>
              </section>
              <section>
                <h2 className="mb-3 text-[16px] font-semibold text-ink">
                  Bản chụp phiên
                </h2>
                <ul className="overflow-hidden rounded-panel border border-border bg-surface">
                  {state.snapshots.map((item, index) => (
                    <li
                      key={item._id ?? item.id ?? index}
                      className="border-b border-border p-4 text-[14px] text-ink last:border-b-0"
                    >
                      {item.version_name || item.name}
                    </li>
                  ))}
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
                {state.invites.map((invite) => {
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
                })}
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

