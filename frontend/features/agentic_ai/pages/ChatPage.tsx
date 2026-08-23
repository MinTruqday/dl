"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  Archive,
  FileText,
  FolderOpen,
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
  manage_user_instructions: "Cập nhật chỉ dẫn cá nhân",
  create_question_draft: "Tạo câu hỏi nháp",
  create_revision_draft: "Tạo đề xuất sửa bản nháp",
  import_assessment: "Nhập đề đánh giá",
  map_question_to_curriculum: "Gắn câu hỏi vào chương trình",
  propose_question_revision: "Tạo đề xuất phiên bản câu hỏi",
  publish_assessment_version: "Xuất bản phiên bản bài đánh giá",
  record_teacher_difficulty_estimate: "Lưu ước lượng độ khó giáo viên",
  run_calibration: "Chạy hiệu chỉnh tâm trắc học",
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
  manage_user_instructions: "Thay đổi chỉ dẫn phản hồi của trợ lý.",
  create_question_draft: "Tạo QuestionDraft để giáo viên rà soát.",
  create_revision_draft: "Tạo proposal sửa bản nháp và chờ giáo viên duyệt.",
  import_assessment: "Phân tích đề có sẵn thành candidate và giữ bước xác nhận.",
  map_question_to_curriculum: "Cập nhật curriculum links bằng optimistic concurrency.",
  propose_question_revision: "Tạo RevisionProposal mới mà không sửa phiên bản production.",
  publish_assessment_version: "Đóng băng AssessmentVersion sau phê duyệt trực tiếp của giáo viên.",
  record_teacher_difficulty_estimate: "Lưu judgment độc lập của giáo viên vào lịch sử.",
  run_calibration: "Tạo snapshot hiệu chỉnh deterministic từ response đủ điều kiện.",
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

export default function ChatPage() {
  const searchParams = useSearchParams();
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
  const [renamingId, setRenamingId] = useState("");
  const [renameValue, setRenameValue] = useState("");
  const [recording, setRecording] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [composerExpanded, setComposerExpanded] = useState(false);
  const [thinkingEnabled, setThinkingEnabled] = useState(false);
  const prefillLoaded = useRef(false);
  useEffect(() => {
    if (prefillLoaded.current) return;
    prefillLoaded.current = true;
    const prompt = searchParams.get("prompt");
    const requestedMode = searchParams.get("mode");
    if (prompt) setInput(prompt);
    if (requestedMode && modes.some((item) => item.value === requestedMode)) {
      setMode(requestedMode as ChatMode);
    }
  }, [searchParams]);
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
  const advancedModesEnabled = true;
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (
      await chat.send(
        input,
        mode,
        approvalPolicy,
        attachment,
        thinkingEnabled,
      )
    ) {
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
        <header className="flex min-h-16 items-center justify-between gap-2 border-b border-border px-4 py-2 md:gap-4 md:px-6 md:py-0">
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-[15px] font-semibold text-ink">
              {chat.sessionId
                ? chat.sessions.find(
                    (session) => (session._id ?? session.id) === chat.sessionId,
                  )?.title || "Cuộc trò chuyện"
                : "Cuộc trò chuyện mới"}
            </h1>
          </div>
          <div className="flex shrink-0 gap-1">
            <Button
              className="md:hidden"
              size="sm"
              variant="ghost"
              onClick={chat.newChat}
              aria-label="Cuộc trò chuyện mới"
            >
              Mới
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setInstructionsOpen(true)}
            >
              <span className="md:hidden">Chỉ dẫn</span>
              <span className="hidden md:inline">Chỉ dẫn cá nhân</span>
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
                  {message.pending ? (
                    <span
                      className="inline-flex items-center gap-1 py-2"
                      aria-label="Trợ lý đang xử lý yêu cầu"
                      role="status"
                    >
                      {[0, 1, 2].map((dot) => (
                        <span
                          key={dot}
                          className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand"
                          style={{ animationDelay: `${dot * 150}ms` }}
                        />
                      ))}
                    </span>
                  ) : (
                    <MessageBody
                      content={message.content}
                      collapsible={message.role === "user"}
                    />
                  )}
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
                          {[
                            { value: "work" as ChatMode, label: "Công việc" },
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
                <span className="rounded-control bg-brand-soft px-2.5 py-1 text-[12px] font-medium text-brand">
                  {modes.find((item) => item.value === mode)?.label || "Trò chuyện"}
                </span>
                {advancedModesEnabled && mode === "chat" && (
                  <button
                    type="button"
                    aria-pressed={thinkingEnabled}
                    title="Sử dụng suy luận nâng cao"
                    onClick={() => setThinkingEnabled((value) => !value)}
                    className={`shrink-0 rounded-control px-2.5 py-1 text-[12px] font-medium transition-colors ${thinkingEnabled ? "bg-brand-soft text-brand" : "text-ink-muted hover:bg-surface-quiet hover:text-ink"}`}
                  >
                    Suy nghĩ
                  </button>
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
    </div>
  );
}
