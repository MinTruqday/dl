"use client";

import { useState } from "react";
import {
  BellOff,
  Blocks as Block,
  BarChart3,
  Cloud,
  Edit3,
  Languages,
  Pin,
  Search,
  Settings,
  Trash2,
} from "lucide-react";
import InlineState from "@/app/_components/InlineState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import NewConversationModal from "./NewConversationModal";
import ConversationDetailsModal from "./ConversationDetailsModal";
import MessageComposer from "./MessageComposer";
import MessageContent from "./MessageContent";
import MessageReactions from "./MessageReactions";
import PollModal from "./PollModal";
import {
  canBlockConversation,
  conversationId,
  conversationName,
  conversationPreview,
  useMessages,
} from "./useMessages";

export default function MessagesPage() {
  const state = useMessages();
  const [newOpen, setNewOpen] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [pollOpen, setPollOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [showPinned, setShowPinned] = useState(false);
  const [editing, setEditing] = useState<any>(null);
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
  const search = async () => setResults(await state.search(query));
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
  return (
    <div className="flex h-[calc(100dvh-60px)] overflow-hidden bg-surface">
      <aside
        className={`w-full shrink-0 border-r border-border md:w-[304px] ${state.selected ? "hidden md:flex md:flex-col" : "flex flex-col"}`}
      >
        <div className="flex min-h-14 items-center justify-end border-b border-border px-3">
          <h1 className="sr-only">Tin nhắn</h1>
          <Button size="sm" onClick={() => setNewOpen(true)}>
            Mới
          </Button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <ul>
            {state.conversations.map((conversation) => {
              const id = conversationId(conversation);
              return (
                <li key={`${id}-${conversationName(conversation)}`}>
                  <button
                    onClick={() => state.open(conversation)}
                    className={`w-full border-b border-border px-4 py-4 text-left ${conversationId(state.selected) === id ? "bg-brand-soft" : "hover:bg-surface-quiet"}`}
                  >
                    <div className="flex items-baseline justify-between gap-3">
                      <p className="truncate text-[14px] font-semibold text-ink">
                        {conversationName(conversation)}
                      </p>
                      {conversation.unread_count > 0 && (
                        <span className="rounded-full bg-brand px-2 py-0.5 text-[11px] font-semibold text-white">
                          {conversation.unread_count}
                        </span>
                      )}
                    </div>
                    <p className="mt-1 truncate text-[12px] text-ink-muted">
                      {conversationPreview(conversation)}
                    </p>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      </aside>
      <main
        className={`min-w-0 flex-1 flex-col ${state.selected ? "flex" : "hidden md:flex"}`}
      >
        {state.selected ? (
          <>
            <header className="flex min-h-14 items-center justify-between gap-4 border-b border-border px-4">
              <div className="min-w-0">
                <button
                  onClick={() => state.setSelected(null)}
                  className="mb-1 text-[12px] text-brand md:hidden"
                >
                  Quay lại
                </button>
                <h2 className="truncate text-[16px] font-semibold text-ink">
                  {conversationName(state.selected)}
                </h2>
                <p className="mt-1 text-[11px] text-ink-muted">
                  {state.blocked
                    ? "Đã chặn"
                    : state.muted
                      ? "Đã tắt thông báo"
                      : "Đang hoạt động"}
                </p>
              </div>
              <div className="flex gap-1">
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Tắt thông báo"
                  onClick={state.toggleMute}
                >
                  <BellOff size={16} />
                </Button>
                {canBlockConversation(state.selected) && (
                  <Button
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
                  size="icon"
                  variant="ghost"
                  aria-label="Xóa cuộc trò chuyện"
                  onClick={state.removeConversation}
                >
                  <Trash2 size={16} />
                </Button>
              </div>
            </header>
            {state.error && (
              <div className="border-b border-border p-3">
                <InlineState
                  title="Không thể hoàn tất thao tác"
                  detail={state.error}
                  tone="danger"
                />
              </div>
            )}
            {state.notice && (
              <div className="border-b border-border p-3">
                <InlineState title={state.notice} action={<Button variant="ghost" onClick={state.clearNotice}>Đóng</Button>} />
              </div>
            )}
            <div className="border-b border-border p-3">
              <div className="flex gap-2">
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  className="apple-input min-w-0 flex-1"
                  placeholder="Tìm trong cuộc trò chuyện"
                />
                <Button
                  size="icon"
                  variant="secondary"
                  aria-label="Tìm"
                  onClick={search}
                >
                  <Search size={16} />
                </Button>
                <Button
                  variant={showPinned ? "primary" : "secondary"}
                  onClick={() => setShowPinned((value) => !value)}
                >
                  Đã ghim {state.pinnedMessages.length}
                </Button>
                <Button
                  size="icon"
                  variant="secondary"
                  aria-label="Tạo bình chọn"
                  onClick={() => setPollOpen(true)}
                >
                  <BarChart3 size={16} />
                </Button>
              </div>
              {showPinned && (
                <ul className="mt-2 max-h-32 overflow-y-auto rounded-control border border-border bg-surface p-2">
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
                    <li className="px-2 py-2 text-[12px] text-ink-muted">
                      Chưa có tin nhắn được ghim
                    </li>
                  )}
                </ul>
              )}
              {results.length > 0 && (
                <ul className="mt-2 max-h-28 overflow-y-auto rounded-control bg-surface-quiet p-2">
                  {results.map((message) => (
                    <li
                      key={message._id ?? message.id}
                      className="truncate px-2 py-1 text-[12px] text-ink"
                    >
                      {message.content}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto bg-surface-quiet px-4 py-6 md:px-8">
              {state.loadingMessages ? (
                <PageLoader rows={6} />
              ) : (
                <div className="mx-auto max-w-3xl space-y-3">
                  {state.messages
                    .filter((message) => !message.is_deleted_for_me)
                    .map((message) => {
                      const id = message._id ?? message.id;
                      const mine =
                        (message.sender_id ?? message.sender) === currentUserId;
                      return (
                        <article
                          key={id}
                          className={`group flex ${mine ? "justify-end" : "justify-start"}`}
                        >
                          <div
                            className={`max-w-[78%] rounded-control px-4 py-3 ${mine ? "bg-brand text-white" : "border border-border bg-surface text-ink"}`}
                          >
                            <MessageContent message={message} vote={(optionId) => state.votePoll(message, optionId)} />
                            {message.translated_content && (
                              <p className="mt-3 border-t border-current/20 pt-2 text-[12px]">
                                {message.translated_content}
                              </p>
                            )}
                            <div
                              className="mt-2 flex flex-wrap items-center gap-1"
                            >
                              <MessageReactions
                                reactions={message.reactions}
                                react={(reaction) => state.react(message, reaction)}
                              />
                              <button
                                aria-label="Ghim"
                                onClick={() => state.pin(message)}
                                className="p-1 opacity-70 hover:opacity-100"
                              >
                                <Pin size={13} />
                              </button>
                              <button
                                aria-label="Dịch"
                                onClick={() => state.translate(message)}
                                className="p-1 opacity-70 hover:opacity-100"
                              >
                                <Languages size={13} />
                              </button>
                              <button
                                aria-label="Lưu vào kho cá nhân"
                                onClick={() => state.saveToCloud(message)}
                                className="p-1 opacity-70 hover:opacity-100"
                              >
                                <Cloud size={13} />
                              </button>
                              {mine && !message.is_recalled && (
                                <>
                                  <button
                                    aria-label="Sửa"
                                    onClick={() => {
                                      setEditing(message);
                                      state.setDraft(message.content || "");
                                    }}
                                    className="p-1 opacity-70 hover:opacity-100"
                                  >
                                    <Edit3 size={13} />
                                  </button>
                                  <button
                                    aria-label="Thu hồi"
                                    onClick={() => state.recall(message)}
                                    className="p-1 opacity-70 hover:opacity-100"
                                  >
                                    <Trash2 size={13} />
                                  </button>
                                </>
                              )}
                              <span className="ml-auto pl-2 text-[10px] opacity-65">
                                {message.created_at
                                  ? new Date(message.created_at).toLocaleTimeString("vi-VN", {
                                      hour: "2-digit",
                                      minute: "2-digit",
                                    })
                                  : ""}
                                {message.self_destruct_seconds ? `  Tự xóa ${message.self_destruct_seconds}s` : ""}
                              </span>
                            </div>
                          </div>
                        </article>
                      );
                    })}
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
          <div className="flex h-full items-center justify-center">
            <InlineState
              title="Chọn cuộc trò chuyện"
              detail="Mở một cuộc trò chuyện từ danh sách"
            />
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
