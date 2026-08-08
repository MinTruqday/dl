"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import {
  Check,
  Circle,
  LoaderCircle,
  Paperclip,
  Send,
  Settings,
  Square,
  Trash2,
  X,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import InlineState from "@/app/_components/InlineState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import ChatInstructionsModal from "./ChatInstructionsModal";
import { ChatMode, useChat } from "./useChat";

const modes: Array<{ value: ChatMode; label: string }> = [
  { value: "chat", label: "Chat" },
  { value: "work", label: "Work" },
  { value: "goal", label: "Goal" },
  { value: "learn", label: "Learn" },
  { value: "plan", label: "Plan" },
];

export default function ChatPage() {
  const chat = useChat();
  const fileInput = useRef<HTMLInputElement>(null);
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<ChatMode>("chat");
  const [approvalPolicy, setApprovalPolicy] = useState<"manual" | "auto_safe">(
    "manual",
  );
  const [instructionsOpen, setInstructionsOpen] = useState(false);
  useEffect(() => {
    if (chat.openedMode) setMode(chat.openedMode);
  }, [chat.openedMode]);
  const advancedModesEnabled = ["PRO", "PREMIUM"].includes(
    String(chat.user?.ai_tier || "BASIC").toUpperCase(),
  );
  useEffect(() => {
    if (!advancedModesEnabled && mode !== "chat") setMode("chat");
  }, [advancedModesEnabled, mode]);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (await chat.send(input, mode, approvalPolicy, file)) {
      setInput("");
      setFile(null);
    }
  };
  if (chat.authLoading || (chat.loading && !chat.user))
    return <PageLoader rows={8} />;
  if (!chat.user)
    return (
      <InlineState
        title="Cần đăng nhập"
        detail="Đăng nhập để sử dụng trợ lý AI"
      />
    );
  const daily = chat.quota?.windows?.find((window) => window.name === "daily");
  const weekly = chat.quota?.windows?.find(
    (window) => window.name === "weekly",
  );
  return (
    <div className="flex h-[calc(100dvh-60px)] overflow-hidden bg-surface">
      <aside className="hidden w-[304px] shrink-0 flex-col border-r border-border md:flex">
        <div className="flex min-h-14 items-center border-b border-border px-3">
          <Button className="w-full" size="sm" onClick={chat.newChat}>
            Cuộc trò chuyện mới
          </Button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          <ul className="space-y-1">
            {chat.sessions.map((session) => {
              const id = session._id ?? session.id;
              return (
                <li
                  key={id}
                  className={`group flex items-center rounded-control ${chat.sessionId === id ? "bg-brand-soft" : "hover:bg-surface-quiet"}`}
                >
                  <button
                    onClick={() => chat.openSession(id)}
                    className="min-w-0 flex-1 truncate px-3 py-3 text-left text-[13px] font-medium text-ink"
                  >
                    {session.title || session.first_query || "Cuộc trò chuyện"}
                  </button>
                  <button
                    aria-label="Xóa cuộc trò chuyện"
                    onClick={() => chat.removeSession(id)}
                    className="mr-2 p-2 text-ink-muted opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 size={14} />
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
        <div className="border-t border-border p-4">
          <div className="space-y-1 text-[12px] text-ink-muted">
            <p>
              Ngày {(daily?.used_tokens ?? 0).toLocaleString("vi-VN")} /{" "}
              {(daily?.limit_tokens ?? 0).toLocaleString("vi-VN")}
            </p>
            <p>
              Tuần {(weekly?.used_tokens ?? 0).toLocaleString("vi-VN")} /{" "}
              {(weekly?.limit_tokens ?? 0).toLocaleString("vi-VN")}
            </p>
          </div>
          <Button
            className="mt-3 w-full"
            variant="secondary"
            icon={<Settings size={15} />}
            onClick={() => setInstructionsOpen(true)}
          >
            Chỉ dẫn cá nhân
          </Button>
        </div>
      </aside>
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex min-h-14 items-center justify-between gap-3 border-b border-border px-4 md:px-6">
          <p className="truncate text-[14px] font-semibold text-ink">
            {chat.sessionId
              ? chat.sessions.find(
                  (session) => (session._id ?? session.id) === chat.sessionId,
                )?.title || "Cuộc trò chuyện"
              : "Cuộc trò chuyện mới"}
          </p>
          <div className="flex gap-1 md:hidden">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setInstructionsOpen(true)}
            >
              Chỉ dẫn
            </Button>
          </div>
        </header>
        {chat.error && (
          <div className="border-b border-border p-3">
            <InlineState
              title="Không thể hoàn tất yêu cầu"
              detail={chat.error}
              tone="danger"
              action={
                <Button variant="ghost" onClick={chat.reload}>
                  Tải lại
                </Button>
              }
            />
          </div>
        )}
        {chat.notice && (
          <div className="border-b border-border p-3">
            <InlineState
              title={chat.notice}
              action={
                <Button variant="ghost" onClick={chat.clearNotice}>
                  Đóng
                </Button>
              }
            />
          </div>
        )}
        <div className="min-h-0 flex-1 overflow-y-auto bg-surface-quiet px-5 py-8 md:px-10">
          {chat.planSteps.length > 0 && (
            <div className="mx-auto mb-5 max-w-3xl rounded-panel border border-border bg-surface px-4 py-3">
              <ol className="space-y-2">
                {chat.planSteps.map((step) => (
                  <li
                    key={step.id}
                    className="flex items-start gap-2 text-[13px] leading-5 text-ink"
                  >
                    {step.status === "completed" ? (
                      <Check className="mt-0.5 shrink-0 text-brand" size={14} />
                    ) : step.status === "running" ? (
                      <LoaderCircle
                        className="mt-0.5 shrink-0 animate-spin text-brand"
                        size={14}
                      />
                    ) : step.status === "failed" ? (
                      <X className="mt-0.5 shrink-0 text-danger" size={14} />
                    ) : (
                      <Circle className="mt-0.5 shrink-0 text-ink-muted" size={14} />
                    )}
                    <span>{step.task}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}
          {chat.approvals.map((approval) => (
            <div
              key={approval.intervention_id}
              className="mx-auto mb-5 max-w-3xl rounded-panel border border-warning/40 bg-surface px-4 py-3"
            >
              <p className="text-[13px] font-semibold text-ink">
                {approval.action_type}
              </p>
              <p className="mt-1 text-[13px] leading-5 text-ink-muted">
                {approval.description}
              </p>
              <div className="mt-3 flex gap-2">
                <Button
                  size="sm"
                  onClick={() =>
                    chat.resolveApproval(approval.intervention_id, "APPROVED")
                  }
                >
                  Xác nhận
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() =>
                    chat.resolveApproval(approval.intervention_id, "REJECTED")
                  }
                >
                  Từ chối
                </Button>
              </div>
            </div>
          ))}
          {chat.messages.length ? (
            <div className="mx-auto max-w-3xl space-y-7">
              {chat.messages.map((message) => (
                <article
                  key={message.id}
                  className={
                    message.role === "user"
                      ? "ml-auto max-w-[80%] rounded-control bg-brand-soft px-4 py-3"
                      : "max-w-none rounded-control border border-border bg-surface px-4 py-3"
                  }
                >
                  <p className="mb-2 text-[11px] font-semibold text-ink-muted">
                    {message.role === "user" ? "Bạn" : "Trợ lý"}
                  </p>
                  {message.attachment && (
                    <p className="mb-2 text-[12px] text-ink-muted">
                      Tệp: {message.attachment}
                    </p>
                  )}
                  <div className="prose prose-sm max-w-none text-[15px] leading-7 text-ink">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content || (chat.sending ? "Đang xử lý" : "")}
                    </ReactMarkdown>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="mx-auto flex h-full max-w-lg items-center justify-center text-center">
              <p className="text-[13px] text-ink-muted">
                Nhập yêu cầu hoặc đính kèm tệp để bắt đầu
              </p>
            </div>
          )}
        </div>
        <form
          onSubmit={submit}
          className="border-t border-border bg-surface p-4"
        >
          <div className="mx-auto max-w-3xl rounded-panel border border-border bg-surface p-3 focus-within:border-brand">
            <textarea
              rows={1}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              className="h-12 min-h-12 max-h-32 w-full resize-none bg-transparent px-2 py-2 text-[15px] leading-6 text-ink outline-none"
              placeholder="Nhập yêu cầu"
            />
            {file && (
              <p className="px-2 pb-2 text-[12px] text-ink-muted">
                {file.name}
              </p>
            )}
            <div className="flex items-center justify-between">
              <div className="flex min-w-0 items-center gap-2">
                <input
                  ref={fileInput}
                  type="file"
                  accept="image/*,audio/*,.pdf,.txt,.md,.doc,.docx"
                  className="hidden"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                />
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  aria-label="Đính kèm tệp"
                  onClick={() => fileInput.current?.click()}
                >
                  <Paperclip size={17} />
                </Button>
                <div className="flex max-w-[55vw] gap-1 overflow-x-auto rounded-control bg-surface-quiet p-1">
                  {modes
                    .filter(
                      (item) => item.value === "chat" || advancedModesEnabled,
                    )
                    .map((item) => (
                    <button
                      key={item.value}
                      type="button"
                      onClick={() => setMode(item.value)}
                      className={`shrink-0 rounded-control px-2.5 py-1 text-[12px] font-medium ${mode === item.value ? "bg-surface text-ink shadow-sm" : "text-ink-muted"}`}
                    >
                      {item.label}
                    </button>
                    ))}
                </div>
                {(mode === "work" || mode === "goal") && (
                  <select
                    value={approvalPolicy}
                    onChange={(event) =>
                      setApprovalPolicy(
                        event.target.value as "manual" | "auto_safe",
                      )
                    }
                    className="rounded-control border border-border bg-surface px-2 py-1 text-[12px] text-ink"
                    aria-label="Quyền công cụ"
                  >
                    <option value="manual">Xác nhận</option>
                    <option value="auto_safe">Tự động an toàn</option>
                  </select>
                )}
              </div>
              {chat.sending ? (
                <Button
                  type="button"
                  size="icon"
                  aria-label="Dừng"
                  onClick={chat.stop}
                >
                  <Square size={15} fill="currentColor" />
                </Button>
              ) : (
                <Button
                  type="submit"
                  size="icon"
                  aria-label="Gửi"
                  disabled={!input.trim() && !file}
                >
                  <Send size={17} />
                </Button>
              )}
            </div>
          </div>
        </form>
      </main>
      <ChatInstructionsModal
        open={instructionsOpen}
        close={() => setInstructionsOpen(false)}
        initial={chat.instructions}
        save={chat.saveInstructions}
      />
    </div>
  );
}
