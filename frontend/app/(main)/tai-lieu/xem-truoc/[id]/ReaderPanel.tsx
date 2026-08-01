"use client";

import { useState } from "react";
import SegmentedTabs from "@/app/_components/SegmentedTabs";
import { Button } from "@/shared/components/ui/Button";

type Tab = "ai" | "highlights" | "archive" | "history";
export default function ReaderPanel({ reader }: { reader: any }) {
  const [tab, setTab] = useState<Tab>(
    reader.document?.content_format === "zip" ? "archive" : "ai",
  );
  const [question, setQuestion] = useState("");
  const [thinking, setThinking] = useState(false);
  const [highlightText, setHighlightText] = useState("");
  const send = async () => {
    await reader.ask(question, thinking);
    setQuestion("");
  };
  const saveHighlight = async () => {
    if (await reader.highlight(highlightText)) setHighlightText("");
  };
  const tabs: { id: Tab; label: string }[] = [
    { id: "ai", label: "Hỏi đáp" },
    { id: "highlights", label: "Nổi bật" },
    { id: "history", label: "Lịch sử" },
    ...(reader.document?.content_format === "zip"
      ? [{ id: "archive" as Tab, label: "Tệp nén" }]
      : []),
  ];
  return (
    <aside className="flex min-h-0 flex-col border-l border-border bg-surface lg:w-[360px]">
      <div className="border-b border-border p-4">
        <SegmentedTabs<Tab>
          label="Công cụ đọc"
          value={tab}
          onChange={setTab}
          tabs={tabs}
        />
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-5">
        {tab === "ai" && (
          <div className="space-y-4">
            {reader.messages.length ? (
              reader.messages.map((message: any) => (
                <div
                  key={message.id}
                  className={`rounded-control p-3 text-[13px] leading-relaxed ${message.role === "user" ? "ml-8 bg-brand-soft text-ink" : "mr-8 bg-surface-quiet text-ink"}`}
                >
                  <p className="mb-1 text-[11px] font-semibold text-ink-muted">
                    {message.role === "user" ? "Bạn" : "Trợ lý"}
                  </p>
                  {message.content}
                </div>
              ))
            ) : (
              <p className="text-[13px] text-ink-muted">
                Đặt câu hỏi dựa trên nội dung tài liệu
              </p>
            )}
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              className="apple-input min-h-24 w-full resize-y"
            />
            <label className="flex items-center gap-2 text-[12px] text-ink-muted">
              <input
                type="checkbox"
                checked={thinking}
                onChange={(event) => setThinking(event.target.checked)}
                className="accent-[hsl(var(--brand))]"
              />
              Phân tích sâu
            </label>
            <Button
              className="w-full"
              disabled={!question.trim() || reader.processing === "ask"}
              onClick={send}
            >
              {reader.processing === "ask" ? "Đang trả lời" : "Gửi câu hỏi"}
            </Button>
          </div>
        )}
        {tab === "highlights" && (
          <div>
            <textarea
              value={highlightText}
              onChange={(event) => setHighlightText(event.target.value)}
              className="apple-input min-h-24 w-full resize-y"
              placeholder="Dán đoạn cần lưu"
            />
            <div className="mt-2 flex gap-2">
              <Button
                size="sm"
                disabled={
                  !highlightText.trim() || reader.processing === "highlight"
                }
                onClick={saveHighlight}
              >
                Lưu
              </Button>
              <Button
                size="sm"
                variant="secondary"
                disabled={
                  !highlightText.trim() || reader.processing === "translate"
                }
                onClick={() => reader.translate(highlightText)}
              >
                Dịch
              </Button>
            </div>
            <ul className="mt-5 divide-y divide-border">
              {reader.highlights.map((item: any) => {
                const id = item._id ?? item.id;
                return (
                  <li key={id} className="py-4">
                    <p className="text-[13px] leading-relaxed text-ink">
                      {item.text}
                    </p>
                    {item.note && (
                      <p className="mt-2 text-[12px] text-ink-muted">
                        {item.note}
                      </p>
                    )}
                    <button
                      className="mt-2 text-[12px] font-semibold text-danger"
                      onClick={() => reader.removeHighlight(id)}
                    >
                      Xóa
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
        {tab === "history" && (
          <ul className="divide-y divide-border">
            {reader.sessions.length ? (
              reader.sessions.map((session: any) => (
                <li key={session._id ?? session.id} className="py-3">
                  <p className="text-[13px] font-semibold text-ink">
                    {session.title || session.first_query || "Phiên hỏi đáp"}
                  </p>
                  <p className="mt-1 text-[11px] text-ink-muted">
                    {session.created_at
                      ? new Date(session.created_at).toLocaleString("vi-VN")
                      : ""}
                  </p>
                </li>
              ))
            ) : (
              <li className="text-[13px] text-ink-muted">
                Chưa có phiên hỏi đáp
              </li>
            )}
          </ul>
        )}
        {tab === "archive" && (
          <ul className="divide-y divide-border">
            {reader.archive.map((item: any) => (
              <li key={item.path}>
                <button
                  disabled={item.is_dir}
                  onClick={() => reader.openArchiveFile(item)}
                  className="w-full px-1 py-3 text-left text-[13px] text-ink disabled:font-semibold"
                >
                  {item.path}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
