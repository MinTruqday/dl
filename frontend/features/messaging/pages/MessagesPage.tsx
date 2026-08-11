"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowLeft,
  BellOff,
  Blocks as Block,
  BarChart3,
  Cloud,
  Edit3,
  Languages,
  MessageSquare,
  MoreHorizontal,
  Pin,
  Plus,
  Search,
  Settings,
  Trash2,
} from "lucide-react";
import InlineState from "@/shared/components/common/InlineState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";
import NewConversationModal from "../components/NewConversationModal";
import ConversationDetailsModal from "../components/ConversationDetailsModal";
import MessageComposer from "../components/MessageComposer";
import MessageContent from "../components/MessageContent";
import MessageReactions from "../components/MessageReactions";
import PollModal from "../components/PollModal";
import {
  canBlockConversation,
  conversationId,
  conversationName,
  conversationPreview,
  useMessages,
} from "../hooks/useMessages";

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function messageDate(value: unknown) {
  const date = new Date(String(value ?? ""));
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleDateString("vi-VN");
}

function dateLabel(value: unknown) {
  const date = new Date(String(value ?? ""));
  if (Number.isNaN(date.getTime())) return "";
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  const key = date.toDateString();
  if (key === today.toDateString()) return "Hôm nay";
  if (key === yesterday.toDateString()) return "Hôm qua";
  return date.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export default function MessagesPage() {
  const state = useMessages();
  useNoticeToast(state.notice);
  useNoticeToast(state.error, "error");
  const [newOpen, setNewOpen] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [pollOpen, setPollOpen] = useState(false);
  const [showPinned, setShowPinned] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [search, setSearch] = useState("");
  const [mobileActionsOpen, setMobileActionsOpen] = useState(false);
  const messageList = useRef<HTMLDivElement>(null);
  const filteredConversations = useMemo(() => {
    const query = search.trim().toLocaleLowerCase("vi-VN");
    if (!query) return state.conversations;
    return state.conversations.filter((conversation) =>
      conversationName(conversation).toLocaleLowerCase("vi-VN").includes(query),
    );
  }, [search, state.conversations]);
  useEffect(() => {
    const element = messageList.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [state.messages.length, state.selected]);
  const submit = async (file?: File | null) => {
    if (editing) {
      if (await state.edit(editing, state.draft)) {
        setEditing(null);
        state.setDraft("");
        return true;
      }
      return false;
    }
    return state.send(state.draft, file);
  };
  if (state.authLoading || (state.loading && !state.user))
    return <PageLoader rows={8} />;
  if (!state.user)
    return (
      <InlineState
        title="Cần đăng nhập"
        detail="Đăng nhập để sử dụng tin nhắn"
      />
    );
  const currentUserId = state.user._id;
  const visibleMessages = state.messages.filter(
    (message) => !message.is_deleted_for_me,
  );
  return (
    <div className="flex h-[calc(100dvh-60px)] w-full overflow-hidden bg-surface">
      <aside
        className={`w-full shrink-0 border-r border-border bg-surface md:w-[320px] ${state.selected ? "hidden md:flex md:flex-col" : "flex flex-col"}`}
      >
        <div className="flex min-h-16 items-center justify-between border-b border-border px-4">
          <h1 className="text-[18px] font-semibold tracking-[-0.02em] text-ink">Tin nhắn</h1>
          <Button size="sm" aria-label="Tin nhắn mới" onClick={() => setNewOpen(true)}>
            <Plus size={17} />
            Tin nhắn mới
          </Button>
        </div>
        <div className="border-b border-border px-3 py-3">
          <label className="flex h-10 items-center gap-2 rounded-control bg-surface-quiet px-3 text-ink-muted focus-within:ring-1 focus-within:ring-brand">
            <Search size={15} />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="min-w-0 flex-1 bg-transparent text-[13px] text-ink outline-none"
              placeholder="Tìm cuộc trò chuyện"
              aria-label="Tìm cuộc trò chuyện"
            />
          </label>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
          <ul className="space-y-1">
            {filteredConversations.map((conversation) => {
              const id = conversationId(conversation);
              const name = conversationName(conversation);
              const preview = conversationPreview(conversation);
              const previewVisible = preview !== "Chưa có tin nhắn";
              return (
                <li key={`${id}-${name}`}>
                  <button
                    onClick={() => state.open(conversation)}
                    className={`flex w-full items-center gap-3 rounded-control px-3 py-3 text-left transition-colors ${conversationId(state.selected) === id ? "bg-brand-soft" : "hover:bg-surface-quiet"}`}
                  >
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-soft text-[12px] font-semibold text-brand-strong">
                      {initials(name)}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline justify-between gap-2">
                        <p className="truncate text-[14px] font-semibold text-ink">{name}</p>
                        {conversation.last_message?.created_at && (
                          <time className="shrink-0 text-[10px] text-ink-subtle">
                            {new Date(conversation.last_message.created_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}
                          </time>
                        )}
                      </div>
                      <div className="mt-1 flex min-h-4 items-center justify-between gap-2">
                        {previewVisible ? (
                          <p className="truncate text-[12px] text-ink-muted">{preview}</p>
                        ) : <span />}
                        {conversation.unread_count > 0 && (
                          <span className="flex h-5 min-w-5 shrink-0 items-center justify-center rounded-full bg-brand px-1.5 text-[10px] font-semibold text-white">
                            {conversation.unread_count}
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
          {!filteredConversations.length && (
            <p className="px-3 py-8 text-center text-[13px] text-ink-muted">
              Không tìm thấy cuộc trò chuyện
            </p>
          )}
        </div>
      </aside>
      <main
        className={`min-w-0 flex-1 flex-col ${state.selected ? "flex" : "hidden md:flex"}`}
      >
        {state.selected ? (
          <>
            <header className="flex min-h-16 items-center justify-between gap-4 border-b border-border px-4 md:px-6">
              <div className="flex min-w-0 items-center gap-3">
                <Button
                  size="icon"
                  variant="ghost"
                  className="md:hidden"
                  aria-label="Quay lại danh sách cuộc trò chuyện"
                  onClick={() => state.setSelected(null)}
                >
                  <ArrowLeft size={17} />
                </Button>
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-soft text-[12px] font-semibold text-brand-strong">
                  {initials(conversationName(state.selected))}
                </span>
                <div className="min-w-0">
                  <h2 className="truncate text-[15px] font-semibold text-ink">
                    {conversationName(state.selected)}
                  </h2>
                  <p className="mt-0.5 hidden text-[11px] text-ink-muted sm:block">
                    {state.blocked
                      ? "Đã chặn"
                      : state.muted
                        ? "Đã tắt thông báo"
                        : "Đang hoạt động"}
                  </p>
                </div>
              </div>
              <div className="relative flex shrink-0 gap-1">
                {state.pinnedMessages.length > 0 && (
                  <Button
                    className="hidden sm:inline-flex"
                    size="icon"
                    variant={showPinned ? "secondary" : "ghost"}
                    aria-label={`Tin nhắn đã ghim, ${state.pinnedMessages.length}`}
                    onClick={() => setShowPinned((value) => !value)}
                  >
                    <Pin size={16} />
                  </Button>
                )}
                <Button
                  className="hidden sm:inline-flex"
                  size="icon"
                  variant="ghost"
                  aria-label="Tạo bình chọn"
                  onClick={() => setPollOpen(true)}
                >
                  <BarChart3 size={16} />
                </Button>
                <Button
                  className="hidden sm:inline-flex"
                  size="icon"
                  variant="ghost"
                  aria-label="Tắt thông báo"
                  onClick={state.toggleMute}
                >
                  <BellOff size={16} />
                </Button>
                {canBlockConversation(state.selected) && (
                  <Button
                    className="hidden sm:inline-flex"
                    size="icon"
                    variant="ghost"
                    aria-label={state.blocked ? "Bỏ chặn" : "Chặn"}
                    onClick={state.toggleBlock}
                  >
                    <Block size={16} />
                  </Button>
                )}
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Thông tin cuộc trò chuyện"
                  onClick={() => setDetailsOpen(true)}
                >
                  <Settings size={16} />
                </Button>
                <Button
                  className="hidden sm:inline-flex"
                  size="icon"
                  variant="ghost"
                  aria-label="Xóa cuộc trò chuyện"
                  onClick={state.removeConversation}
                >
                  <Trash2 size={16} />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  className="sm:hidden"
                  aria-label="Thêm thao tác"
                  aria-expanded={mobileActionsOpen}
                  onClick={() => setMobileActionsOpen((value) => !value)}
                >
                  <MoreHorizontal size={17} />
                </Button>
                {mobileActionsOpen && (
                  <div className="absolute right-0 top-11 z-30 w-48 rounded-panel border border-border bg-surface p-1.5 shadow-xl sm:hidden">
                    <button type="button" className="w-full rounded-control px-3 py-2 text-left text-[13px] hover:bg-surface-quiet" onClick={() => { setPollOpen(true); setMobileActionsOpen(false); }}>Tạo bình chọn</button>
                    <button type="button" className="w-full rounded-control px-3 py-2 text-left text-[13px] hover:bg-surface-quiet" onClick={() => { void state.toggleMute(); setMobileActionsOpen(false); }}>Tắt thông báo</button>
                    {canBlockConversation(state.selected) && (
                      <button type="button" className="w-full rounded-control px-3 py-2 text-left text-[13px] hover:bg-surface-quiet" onClick={() => { void state.toggleBlock(); setMobileActionsOpen(false); }}>{state.blocked ? "Bỏ chặn" : "Chặn"}</button>
                    )}
                    <button type="button" className="w-full rounded-control px-3 py-2 text-left text-[13px] text-danger hover:bg-surface-quiet" onClick={() => { void state.removeConversation(); setMobileActionsOpen(false); }}>Xóa cuộc trò chuyện</button>
                  </div>
                )}
              </div>
            </header>
            {showPinned && state.pinnedMessages.length > 0 && (
              <div className="border-b border-border bg-surface px-4 py-3 md:px-6">
                <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-muted">Tin nhắn đã ghim</p>
                <ul className="max-h-32 overflow-y-auto rounded-control bg-surface-quiet p-2">
                  {state.pinnedMessages.length ? (
                    state.pinnedMessages.map((message) => (
                      <li
                        key={message._id ?? message.id}
                        className="border-b border-border px-2 py-2 text-[12px] text-ink last:border-b-0"
                      >
                        {message.content || "Tệp đính kèm"}
                      </li>
                    ))
                  ) : (
                    null
                  )}
                </ul>
              </div>
            )}
            <div ref={messageList} className="min-h-0 flex-1 overflow-y-auto bg-surface-quiet px-4 py-6 md:px-8">
              {state.loadingMessages ? (
                <PageLoader rows={6} />
              ) : (
                <div className="mx-auto max-w-4xl space-y-2">
                  {visibleMessages.map((message, index) => {
                      const id = message._id ?? message.id;
                      const mine =
                        (message.sender_id ?? message.sender) === currentUserId;
                      const currentDate = messageDate(message.created_at);
                      const previousDate = index > 0
                        ? messageDate(visibleMessages[index - 1]?.created_at)
                        : "";
                      return (
                        <div key={id}>
                          {currentDate && currentDate !== previousDate && (
                            <div className="my-5 flex items-center gap-3" role="separator">
                              <span className="h-px flex-1 bg-border" />
                              <time className="text-[11px] font-medium text-ink-muted">{dateLabel(message.created_at)}</time>
                              <span className="h-px flex-1 bg-border" />
                            </div>
                          )}
                          <article className={`group flex ${mine ? "justify-end" : "justify-start"}`}>
                            <div className={`flex max-w-[min(82%,38rem)] flex-col ${mine ? "items-end" : "items-start"}`}>
                              <div
                                className={`rounded-[18px] px-4 py-2.5 ${mine ? "rounded-br-md bg-brand text-white" : "rounded-bl-md border border-border bg-surface text-ink"}`}
                              >
                                <MessageContent message={message} vote={(optionId) => state.votePoll(message, optionId)} />
                                {message.translated_content && (
                                  <p className="mt-3 border-t border-current/20 pt-2 text-[12px]">
                                    {message.translated_content}
                                  </p>
                                )}
                              </div>
                              <div className={`mt-1 flex min-h-7 items-center gap-1 ${mine ? "flex-row-reverse" : ""}`}>
                              <MessageReactions
                                reactions={message.reactions}
                                react={(reaction) => state.react(message, reaction)}
                              />
                                <div className="flex items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
                                  <button aria-label="Ghim" onClick={() => state.pin(message)} className="rounded-full p-1.5 text-ink-muted hover:bg-surface hover:text-ink"><Pin size={13} /></button>
                                  <button aria-label="Dịch" onClick={() => state.translate(message)} className="rounded-full p-1.5 text-ink-muted hover:bg-surface hover:text-ink"><Languages size={13} /></button>
                                  <button aria-label="Lưu vào kho cá nhân" onClick={() => state.saveToCloud(message)} className="rounded-full p-1.5 text-ink-muted hover:bg-surface hover:text-ink"><Cloud size={13} /></button>
                                  {mine && !message.is_recalled && (
                                    <>
                                      <button
                                        aria-label="Sửa"
                                        onClick={() => {
                                          setEditing(message);
                                          state.setDraft(message.content || "");
                                        }}
                                        className="rounded-full p-1.5 text-ink-muted hover:bg-surface hover:text-ink"
                                      >
                                        <Edit3 size={13} />
                                      </button>
                                      <button aria-label="Thu hồi" onClick={() => state.recall(message)} className="rounded-full p-1.5 text-ink-muted hover:bg-surface hover:text-danger"><Trash2 size={13} /></button>
                                    </>
                                  )}
                                </div>
                                <time className="px-1 text-[10px] text-ink-subtle">
                                {message.created_at
                                  ? new Date(message.created_at).toLocaleTimeString("vi-VN", {
                                      hour: "2-digit",
                                      minute: "2-digit",
                                    })
                                  : ""}
                                {message.self_destruct_seconds ? `  Tự xóa ${message.self_destruct_seconds}s` : ""}
                                </time>
                              </div>
                            </div>
                          </article>
                        </div>
                      );
                    })}
                  {!visibleMessages.length && (
                    <p className="py-16 text-center text-[13px] text-ink-muted">Chưa có tin nhắn</p>
                  )}
                </div>
              )}
            </div>
            <MessageComposer
              value={state.draft}
              setValue={state.setDraft}
              send={submit}
              disabled={state.blocked}
              processing={state.processing}
              editing={Boolean(editing)}
              cancelEditing={() => {
                setEditing(null);
                state.setDraft("");
              }}
            />
          </>
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-ink-muted">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-quiet">
              <MessageSquare size={20} />
            </span>
            <p className="text-[14px] font-medium">Chọn cuộc trò chuyện</p>
          </div>
        )}
      </main>
      <NewConversationModal
        open={newOpen}
        close={() => setNewOpen(false)}
        findUsers={state.findUsers}
        start={state.startWithUser}
        createGroup={state.createGroup}
      />
      <ConversationDetailsModal
        open={detailsOpen}
        close={() => setDetailsOpen(false)}
        settings={state.settings}
        media={state.media}
        loadingMedia={state.loadingMedia}
        loadMedia={state.loadMedia}
        setTimer={state.setDisappearingTimer}
      />
      <PollModal open={pollOpen} close={() => setPollOpen(false)} create={state.createPoll} />
    </div>
  );
}
