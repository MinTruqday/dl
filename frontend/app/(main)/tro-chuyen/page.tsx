"use client";

import { FormEvent, useRef, useState } from "react";
import { Paperclip, Send, Settings, Trash2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import InlineState from "@/app/_components/InlineState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import ChatInstructionsModal from "./ChatInstructionsModal";
import { useChat } from "./useChat";

export default function ChatPage() {
  const chat = useChat();
  const fileInput = useRef<HTMLInputElement>(null);
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [thinking, setThinking] = useState(false);
  const [instructionsOpen, setInstructionsOpen] = useState(false);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (await chat.send(input, thinking, file)) {
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
  const quota = chat.quota as any;
  const used = quota?.used ?? quota?.used_tokens ?? 0;
  const limit = quota?.limit ?? quota?.token_limit ?? 0;
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
          <p className="text-[12px] text-ink-muted">
            Hạn mức {used.toLocaleString("vi-VN")}
            {limit ? ` / ${limit.toLocaleString("vi-VN")}` : ""}
          </p>
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
              <div className="flex items-center gap-2">
                <input
                  ref={fileInput}
                  type="file"
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
                <label className="flex items-center gap-2 text-[12px] text-ink-muted">
                  <input
                    type="checkbox"
                    checked={thinking}
                    onChange={(event) => setThinking(event.target.checked)}
                    className="accent-[hsl(var(--brand))]"
                  />
                  Phân tích sâu
                </label>
              </div>
              <Button
                type="submit"
                size="icon"
                aria-label="Gửi"
                disabled={chat.sending || (!input.trim() && !file)}
              >
                <Send size={17} />
              </Button>
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
