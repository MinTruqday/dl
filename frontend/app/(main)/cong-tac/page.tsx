"use client";

import { useState } from "react";
import InlineState from "@/app/_components/InlineState";
import MetricStrip from "@/app/_components/MetricStrip";
import PageHeader from "@/app/_components/PageHeader";
import SegmentedTabs from "@/app/_components/SegmentedTabs";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { useCollaboration } from "./useCollaboration";

type Tab = "people" | "tasks" | "notes" | "invites";
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
              { label: "Bản chụp", value: state.snapshots.length },
            ]}
          />
          <div className="my-6">
            <SegmentedTabs<Tab>
              label="Nội dung cộng tác"
              value={tab}
              onChange={setTab}
              tabs={[
                { id: "people", label: "Thành viên" },
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
                  />
                  <select
                    value={role}
                    onChange={(event) => setRole(event.target.value)}
                    className="apple-input mt-3 w-full"
                  >
                    <option value="editor">Chỉnh sửa</option>
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
                <div className="rounded-panel border border-border bg-surface p-5">
                  <h2 className="text-[16px] font-semibold text-ink">
                    Quyền truy cập
                  </h2>
                  <select
                    className="apple-input mt-4 w-full"
                    defaultValue="invite_only"
                    onChange={(event) => state.updateAccess(event.target.value)}
                  >
                    <option value="invite_only">Chỉ người được mời</option>
                    <option value="anyone_with_link">Người có liên kết</option>
                  </select>
                </div>
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
