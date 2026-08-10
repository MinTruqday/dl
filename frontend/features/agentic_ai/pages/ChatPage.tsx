"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import {
  Archive,
  Check,
  ChevronDown,
  FileText,
  FolderOpen,
  LoaderCircle,
  Maximize2,
  Mic,
  MicOff,
  Minimize2,
  Pencil,
  Paperclip,
  Pin,
  Send,
  Square,
  Trash2,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import InlineState from "@/shared/components/common/InlineState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";
import ChatInstructionsModal from "../components/ChatInstructionsModal";
import McpPresetModal from "../components/McpPresetModal";
import { ChatMode, useChat } from "../hooks/useChat";

const modes: Array<{ value: ChatMode; label: string; detail: string }> = [
  { value: "chat", label: "Trò chuyện", detail: "Trao đổi trực tiếp" },
  { value: "work", label: "Công việc", detail: "Lập kế hoạch và thực hiện" },
  { value: "goal", label: "Mục tiêu", detail: "Theo đuổi mục tiêu nhiều lượt" },
  { value: "learn", label: "Học tập", detail: "Học theo từng bước" },
  { value: "plan", label: "Kế hoạch", detail: "Chỉ lập kế hoạch" },
];

const toolLabels: Record<string, string> = {
  create_document: "Tạo tài liệu",
  update_document_metadata: "Cập nhật thông tin tài liệu",
  replace_document_content: "Thay nội dung tài liệu",
  edit_document_text: "Sửa văn bản tài liệu",
  edit_document_block: "Sửa khối nội dung",
  propose_document_edits: "Đề xuất chỉnh sửa",
  delete_document: "Xóa tài liệu",
  restore_document: "Khôi phục tài liệu",
  execute_python: "Chạy mã Python",
  execute_mcp_tool: "Chạy công cụ MCP",
  manage_user_instructions: "Cập nhật chỉ dẫn cá nhân",
};

const toolDescriptions: Record<string, string> = {
  create_document: "Tạo một tài liệu mới trong không gian của bạn.",
  update_document_metadata: "Cập nhật tên, mô tả hoặc thuộc tính của tài liệu.",
  replace_document_content: "Thay toàn bộ nội dung hiện tại của tài liệu.",
  edit_document_text: "Chỉnh sửa một phần văn bản trong tài liệu.",
  edit_document_block: "Chỉnh sửa một khối nội dung trong tài liệu.",
  propose_document_edits: "Tạo đề xuất chỉnh sửa để bạn xem lại.",
  delete_document: "Xóa tài liệu đã chọn.",
  restore_document: "Khôi phục tài liệu đã xóa.",
  execute_python: "Chạy mã Python trong môi trường giới hạn.",
  execute_mcp_tool: "Gọi công cụ từ máy chủ MCP đã kết nối.",
  manage_user_instructions: "Thay đổi chỉ dẫn phản hồi của trợ lý.",
};

function normalizeDoclibHref(href?: string) {
  if (!href) return "#";
  const uuid = "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}";
  const legacyHost = href.match(new RegExp(`^https?://docs\\.doclib\\.ai/(${uuid})/?$`));
  if (legacyHost) return `/tai-lieu/xem-truoc/${legacyHost[1]}`;
  const legacyPath = href.match(new RegExp(`^/tai-lieu/(${uuid})/?$`));
  if (legacyPath) return `/tai-lieu/xem-truoc/${legacyPath[1]}`;
  return href;
}

function MessageBody({ content, collapsible = false }: { content: string; collapsible?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = collapsible && (content.length > 480 || content.split("\n").length > 7);
  return (
    <>
      <div className={`prose prose-sm max-w-none text-[15px] leading-7 text-ink ${isLong && !expanded ? "relative max-h-40 overflow-hidden after:absolute after:inset-x-0 after:bottom-0 after:h-12 after:bg-gradient-to-t after:from-brand-soft after:to-transparent" : ""}`}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({ href, children, ...props }) => {
              const normalized = normalizeDoclibHref(href);
              const external = /^https?:\/\//i.test(normalized);
              return (
                <a
                  {...props}
                  href={normalized}
                  className="font-medium text-brand underline decoration-brand/35 underline-offset-4 hover:decoration-brand"
                  target={external ? "_blank" : undefined}
                  rel={external ? "noreferrer" : undefined}
                >
                  {children}
                </a>
              );
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
      {isLong && (
        <button
          type="button"
          className="mt-2 text-[12px] font-medium text-brand hover:text-brand-strong"
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? "Thu gọn" : "Mở rộng"}
        </button>
      )}
    </>
  );
}

function ActivityDisclosure({ activity, active }: { activity?: Array<{ id: string; label: string; status: "running" | "completed" }>; active: boolean }) {
  if (!activity?.length) return null;
  return (
    <details className="group mb-3 text-[12px] text-ink-muted" open={active}>
      <summary className="flex w-fit cursor-pointer list-none items-center gap-1.5 font-medium hover:text-ink">
        {active ? <LoaderCircle className="animate-spin" size={14} /> : <Check size={14} />}
        Quá trình xử lý
        <ChevronDown className="transition-transform group-open:rotate-180" size={14} />
      </summary>
      <ol className="ml-1 mt-2 space-y-1.5 border-l border-border pl-3">
        {activity.map((item) => (
          <li key={item.id}>{item.label.replace(/^Đang /, item.status === "completed" ? "Đã " : "Đang ")}</li>
        ))}
      </ol>
    </details>
  );
}

export default function ChatPage() {
  const chat = useChat();
  useNoticeToast(chat.notice);
  useNoticeToast(chat.error, "error");
  const fileInput = useRef<HTMLInputElement>(null);
  const folderInput = useRef<HTMLInputElement>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const mediaStream = useRef<MediaStream | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const [input, setInput] = useState("");
  const [attachment, setAttachment] = useState<{
    kind: "file" | "folder";
    files: File[];
  } | null>(null);
  const [attachmentMenuOpen, setAttachmentMenuOpen] = useState(false);
  const [mode, setMode] = useState<ChatMode>("chat");
  const [approvalPolicy, setApprovalPolicy] = useState<"manual" | "auto_safe">(
    "manual",
  );
  const [instructionsOpen, setInstructionsOpen] = useState(false);
  const [mcpOpen, setMcpOpen] = useState(false);
  const [renamingId, setRenamingId] = useState("");
  const [renameValue, setRenameValue] = useState("");
  const [recording, setRecording] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [composerExpanded, setComposerExpanded] = useState(false);
  useEffect(
    () => () => {
      mediaRecorder.current?.stop();
      mediaStream.current?.getTracks().forEach((track) => track.stop());
    },
    [],
  );
  const toggleRecording = async () => {
    if (recording) {
      mediaRecorder.current?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStream.current = stream;
      audioChunks.current = [];
      const recorder = new MediaRecorder(stream);
      mediaRecorder.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size) audioChunks.current.push(event.data);
      };
      recorder.onstop = () => {
        const type = recorder.mimeType || "audio/webm";
        const blob = new Blob(audioChunks.current, { type });
        setAttachment({
          kind: "file",
          files: [new File([blob], `ghi-am-${Date.now()}.webm`, { type })],
        });
        mediaStream.current?.getTracks().forEach((track) => track.stop());
        setRecording(false);
      };
      recorder.start();
      setRecording(true);
    } catch {
      chat.reportError("Không thể truy cập micro");
    }
  };
  useEffect(() => {
    if (chat.openedMode) setMode(chat.openedMode);
  }, [chat.openedMode]);
  const advancedModesEnabled =
    String(chat.user?.role || "").toLowerCase() === "admin" ||
    ["PRO", "PREMIUM"].includes(
      String(chat.user?.ai_tier || "BASIC").toUpperCase(),
    );
  useEffect(() => {
    if (!advancedModesEnabled && mode !== "chat") setMode("chat");
  }, [advancedModesEnabled, mode]);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (await chat.send(input, mode, approvalPolicy, attachment)) {
      setInput("");
      setAttachment(null);
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
    <div className="flex h-[calc(100dvh-60px)] w-full overflow-hidden bg-surface">
      <aside className="hidden w-[288px] shrink-0 flex-col border-r border-border bg-surface md:flex">
        <div className="border-b border-border p-4">
          <Button className="w-full" size="sm" onClick={chat.newChat}>
            Cuộc trò chuyện mới
          </Button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          <ul className="space-y-1">
            {chat.sessions
              .filter((session) => showArchived ? session.is_archived : !session.is_archived)
              .map((session) => {
              const id = session._id ?? session.id;
              return (
                <li
                  key={id}
                  className={`group flex items-center rounded-control ${chat.sessionId === id ? "bg-brand-soft" : "hover:bg-surface-quiet"}`}
                >
                  {renamingId === id ? (
                    <form
                      className="flex min-w-0 flex-1 items-center gap-1 px-2 py-2"
                      onSubmit={async (event) => {
                        event.preventDefault();
                        if (!renameValue.trim()) return;
                        await chat.renameSession(id, renameValue);
                        setRenamingId("");
                      }}
                    >
                      <input
                        aria-label="Tên cuộc trò chuyện"
                        value={renameValue}
                        onChange={(event) => setRenameValue(event.target.value)}
                        className="apple-input h-9 min-w-0 flex-1 py-1 text-[13px]"
                        autoFocus
                      />
                      <Button size="sm" type="submit">Lưu</Button>
                    </form>
                  ) : (
                    <button
                      onClick={() => chat.openSession(id)}
                      className="min-w-0 flex-1 truncate px-3 py-3 text-left text-[13px] font-medium text-ink"
                    >
                      {session.title || session.first_query || "Cuộc trò chuyện"}
                    </button>
                  )}
                  <button
                    aria-label="Đổi tên cuộc trò chuyện"
                    onClick={() => {
                      setRenamingId(id);
                      setRenameValue(session.title || session.first_query || "Cuộc trò chuyện");
                    }}
                    className="p-2 text-ink-muted opacity-0 group-hover:opacity-100 focus:opacity-100"
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    aria-label={session.is_pinned ? "Bỏ ghim" : "Ghim cuộc trò chuyện"}
                    onClick={() => chat.setSessionState(id, { is_pinned: !session.is_pinned })}
                    className={`p-2 focus:opacity-100 ${session.is_pinned ? "text-brand" : "text-ink-muted opacity-0 group-hover:opacity-100"}`}
                  >
                    <Pin size={14} />
                  </button>
                  <button
                    aria-label={session.is_archived ? "Khôi phục" : "Lưu trữ cuộc trò chuyện"}
                    onClick={() => chat.setSessionState(id, { is_archived: !session.is_archived })}
                    className="p-2 text-ink-muted opacity-0 group-hover:opacity-100 focus:opacity-100"
                  >
                    <Archive size={14} />
                  </button>
                  <button
                    aria-label="Xóa cuộc trò chuyện"
                    onClick={() => chat.removeSession(id)}
                    className="mr-2 p-2 text-ink-muted opacity-0 group-hover:opacity-100 focus:opacity-100"
                  >
                    <Trash2 size={14} />
                  </button>
                </li>
              );
            })}
          </ul>
          {(showArchived || chat.sessions.some((session) => session.is_archived)) && (
            <button
              className="mt-3 w-full rounded-control px-3 py-2 text-left text-[12px] font-medium text-ink-muted hover:bg-surface-quiet"
              onClick={() => setShowArchived((value) => !value)}
            >
              {showArchived ? "Quay lại trò chuyện" : "Xem mục lưu trữ"}
            </button>
          )}
        </div>
      </aside>
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex min-h-16 items-center justify-between gap-4 border-b border-border px-4 md:px-6">
          <div className="min-w-0">
            <h1 className="truncate text-[15px] font-semibold text-ink">
              {chat.sessionId
                ? chat.sessions.find(
                    (session) => (session._id ?? session.id) === chat.sessionId,
                  )?.title || "Cuộc trò chuyện"
                : "Cuộc trò chuyện mới"}
            </h1>
            <p className="mt-1 text-[11px] text-ink-muted">
              Ngày {(daily?.used_tokens ?? 0).toLocaleString("vi-VN")} / {(daily?.limit_tokens ?? 0) < 0 ? "Không giới hạn" : (daily?.limit_tokens ?? 0).toLocaleString("vi-VN")}
              <span aria-hidden="true"> · </span>
              Tuần {(weekly?.used_tokens ?? 0).toLocaleString("vi-VN")} / {(weekly?.limit_tokens ?? 0) < 0 ? "Không giới hạn" : (weekly?.limit_tokens ?? 0).toLocaleString("vi-VN")}
            </p>
          </div>
          <div className="flex shrink-0 gap-1">
            <Button
              className="md:hidden"
              size="sm"
              variant="ghost"
              onClick={chat.newChat}
            >
              Cuộc trò chuyện mới
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setInstructionsOpen(true)}
            >
              Chỉ dẫn cá nhân
            </Button>
          </div>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto bg-surface-quiet px-5 pb-4 pt-8 md:px-10">
          {chat.approvals.map((approval) => (
            <div
              key={approval.intervention_id}
              className="mx-auto mb-5 max-w-3xl rounded-panel border border-warning/40 bg-surface px-4 py-3"
            >
              <p className="text-[13px] font-semibold text-ink">
                {toolLabels[approval.action_type] || "Thao tác của trợ lý"}
              </p>
              <p className="mt-1 text-[13px] leading-5 text-ink-muted">
                {toolDescriptions[approval.action_type] ||
                  "Trợ lý cần quyền để tiếp tục thao tác này."}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  size="sm"
                  onClick={() =>
                    chat.resolveApproval(approval.intervention_id, "APPROVED", "once")
                  }
                >
                  Một lần
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() =>
                    chat.resolveApproval(approval.intervention_id, "APPROVED", "session")
                  }
                >
                  Trong phiên
                </Button>
                {approval.risk_level !== "high" && approval.risk_level !== "critical" && (
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() =>
                      chat.resolveApproval(approval.intervention_id, "APPROVED", "safe_session")
                    }
                  >
                    Mọi thao tác an toàn
                  </Button>
                )}
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
            <div className="mx-auto max-w-5xl space-y-7">
              {chat.messages.map((message) => (
                <article
                  key={message.id}
                  className={
                    message.role === "user"
                      ? "ml-auto w-fit max-w-[min(85%,46rem)] rounded-control bg-brand-soft px-4 py-3"
                      : "max-w-none px-1 py-2"
                  }
                >
                  {message.attachment && (
                    <p className="mb-2 text-[12px] text-ink-muted">
                      Tệp: {message.attachment}
                    </p>
                  )}
                  {message.role === "assistant" && (
                    <ActivityDisclosure
                      activity={message.activity}
                      active={chat.sending && !message.content}
                    />
                  )}
                  <MessageBody
                    content={message.content || (chat.sending ? "Đang xử lý" : "")}
                    collapsible={message.role === "user"}
                  />
                </article>
              ))}
            </div>
          ) : null}
        </div>
        <form
          onSubmit={submit}
          className="bg-surface-quiet px-4 pb-5 pt-2"
        >
          <div className={`mx-auto rounded-panel border border-border-strong bg-surface p-3 shadow-sm transition-[max-width] focus-within:border-brand ${composerExpanded ? "max-w-5xl" : "max-w-3xl"}`}>
            {attachment && (
              <div className="mb-2 flex items-center justify-between gap-3 rounded-control bg-surface-quiet px-3 py-2 text-[12px] text-ink-muted">
                <span className="flex min-w-0 items-center gap-2 truncate">
                  {attachment.kind === "folder" ? <FolderOpen size={15} /> : <FileText size={15} />}
                  <span className="truncate">{attachment.files.length === 1
                      ? attachment.files[0].name
                      : `${attachment.files.length} tệp`}</span>
                </span>
                <button
                  type="button"
                  className="shrink-0 text-ink-muted hover:text-ink"
                  onClick={() => setAttachment(null)}
                >
                  Bỏ chọn
                </button>
              </div>
            )}
            <textarea
              rows={1}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              className="h-12 min-h-12 max-h-32 w-full resize-none bg-transparent px-2 py-2 text-[15px] leading-6 text-ink outline-none"
              placeholder="Nhập yêu cầu"
            />
            <div className="flex items-center justify-between">
              <div className="flex min-w-0 items-center gap-2">
                <input
                  ref={fileInput}
                  type="file"
                  accept="image/*,audio/*,.pdf,.txt,.md,.doc,.docx"
                  className="hidden"
                  onChange={(event) => {
                    const files = Array.from(event.target.files ?? []);
                    if (files.length) setAttachment({ kind: "file", files });
                    event.target.value = "";
                  }}
                />
                <input
                  ref={folderInput}
                  type="file"
                  multiple
                  className="hidden"
                  {...({ webkitdirectory: "", directory: "" } as any)}
                  onChange={(event) => {
                    const files = Array.from(event.target.files ?? []);
                    if (files.length) setAttachment({ kind: "folder", files });
                    event.target.value = "";
                  }}
                />
                <div className="relative">
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  aria-label="Mở menu đính kèm"
                  aria-expanded={attachmentMenuOpen}
                  onClick={() => setAttachmentMenuOpen((value) => !value)}
                >
                  <Paperclip size={17} />
                </Button>
                  {attachmentMenuOpen && (
                    <div className="absolute bottom-12 left-0 z-30 w-56 rounded-panel border border-border bg-surface p-1.5 shadow-xl">
                      <button
                        type="button"
                        className="flex w-full items-center rounded-control px-3 py-2 text-left text-[13px] hover:bg-surface-quiet"
                        onClick={() => {
                          setAttachmentMenuOpen(false);
                          fileInput.current?.click();
                        }}
                      >
                        Chọn tệp
                      </button>
                      <button
                        type="button"
                        className="flex w-full items-center rounded-control px-3 py-2 text-left text-[13px] hover:bg-surface-quiet"
                        onClick={() => {
                          setAttachmentMenuOpen(false);
                          folderInput.current?.click();
                        }}
                      >
                        Chọn thư mục
                      </button>
                      {advancedModesEnabled && (
                        <div className="mt-1 border-t border-border pt-1">
                          {chat.mcpAvailable && (
                            <button
                              type="button"
                              className="flex w-full items-center rounded-control px-3 py-2 text-left text-[13px] text-ink hover:bg-surface-quiet"
                              onClick={() => {
                                setAttachmentMenuOpen(false);
                                setMcpOpen(true);
                              }}
                            >
                              Kết nối MCP
                            </button>
                          )}
                          {[
                            { value: "plan" as ChatMode, label: "Kế hoạch" },
                            { value: "goal" as ChatMode, label: "Mục tiêu" },
                            { value: "learn" as ChatMode, label: "Học tập" },
                          ].map((item) => (
                            <button
                              key={item.value}
                              type="button"
                              aria-pressed={mode === item.value}
                              className={`flex w-full items-center rounded-control px-3 py-2 text-left text-[13px] hover:bg-surface-quiet ${mode === item.value ? "bg-brand-soft text-brand" : "text-ink"}`}
                              onClick={() => {
                                setMode(item.value);
                                setAttachmentMenuOpen(false);
                              }}
                            >
                              {item.label}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
                {chat.audioAvailable && (
                  <Button
                    type="button"
                    size="icon"
                    variant={recording ? "secondary" : "ghost"}
                    aria-label={recording ? "Dừng ghi âm" : "Ghi âm"}
                    onClick={toggleRecording}
                  >
                    {recording ? <MicOff size={17} /> : <Mic size={17} />}
                  </Button>
                )}
                <div className="flex gap-1 rounded-control bg-surface-quiet p-1">
                  {modes.filter((item) => item.value === "chat" || item.value === "work").map((item) => {
                    const locked = item.value === "work" && !advancedModesEnabled;
                    return (
                    <button
                      key={item.value}
                      type="button"
                      onClick={() => !locked && setMode(item.value)}
                      disabled={locked}
                      title={locked ? `${item.detail}. Cần gói Pro` : item.detail}
                      className={`shrink-0 rounded-control px-2.5 py-1 text-[12px] font-medium disabled:cursor-not-allowed disabled:opacity-45 ${mode === item.value ? "bg-surface text-ink shadow-sm" : "text-ink-muted"}`}
                    >
                      {item.label}
                    </button>
                    );
                  })}
                </div>
                {!(["chat", "work"] as ChatMode[]).includes(mode) && (
                  <span className="hidden rounded-control bg-brand-soft px-2.5 py-1 text-[12px] font-medium text-brand sm:inline">
                    {modes.find((item) => item.value === mode)?.label}
                  </span>
                )}
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
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  aria-label={composerExpanded ? "Thu gọn vùng nhập" : "Mở rộng vùng nhập"}
                  onClick={() => setComposerExpanded((value) => !value)}
                >
                  {composerExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                </Button>
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
                  disabled={!input.trim() && !attachment?.files.length}
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
      <McpPresetModal open={mcpOpen} onClose={() => setMcpOpen(false)} />
    </div>
  );
}
