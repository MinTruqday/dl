"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import {
  Mic,
  Paperclip,
  Send,
  Square,
  X,
} from "lucide-react";
import { Button } from "@/shared/components/ui/Button";

export default function MessageComposer({
  value,
  setValue,
  send,
  disabled,
  processing,
  editing,
  cancelEditing,
}: {
  value: string;
  setValue: (value: string) => void;
  send: (file?: File | null) => Promise<boolean>;
  disabled: boolean;
  processing: boolean;
  editing: boolean;
  cancelEditing: () => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const chunks = useRef<Blob[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [menu, setMenu] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recordError, setRecordError] = useState("");

  useEffect(
    () => () => {
      stream.current?.getTracks().forEach((track) => track.stop());
    },
    [],
  );

  const choose = (accept: string) => {
    if (!input.current) return;
    input.current.accept = accept;
    input.current.click();
    setMenu(false);
  };
  const startRecording = async () => {
    setRecordError("");
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(mediaStream);
      chunks.current = [];
      stream.current = mediaStream;
      recorder.current = mediaRecorder;
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size) chunks.current.push(event.data);
      };
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks.current, { type: mediaRecorder.mimeType || "audio/webm" });
        setFile(new File([blob], `ghi-am-${Date.now()}.webm`, { type: blob.type }));
        mediaStream.getTracks().forEach((track) => track.stop());
        setRecording(false);
      };
      mediaRecorder.start();
      setRecording(true);
    } catch {
      setRecordError("Không thể truy cập micro");
    }
  };
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (await send(file)) setFile(null);
  };

  return (
    <form onSubmit={submit} className="border-t border-border bg-surface px-3 py-3 md:px-5">
      <div className="relative mx-auto max-w-3xl rounded-panel border border-border bg-surface focus-within:border-brand">
        {(editing || file || recording || recordError) && (
          <div className="flex min-h-9 items-center justify-between gap-3 border-b border-border px-3 text-[12px]">
            <span className={recordError ? "text-danger" : "truncate text-ink-muted"}>
              {recordError || (recording ? "Đang ghi âm" : editing ? "Đang sửa tin nhắn" : file?.name)}
            </span>
            {(editing || file) && (
              <button
                type="button"
                aria-label="Hủy"
                className="text-ink-muted hover:text-ink"
                onClick={() => {
                  setFile(null);
                  if (editing) cancelEditing();
                }}
              >
                <X size={15} />
              </button>
            )}
          </div>
        )}
        <textarea
          rows={1}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              event.currentTarget.form?.requestSubmit();
            }
          }}
          className="h-12 min-h-12 max-h-28 w-full resize-none bg-transparent px-4 py-3 text-[14px] leading-6 text-ink outline-none"
          placeholder={disabled ? "Không thể gửi vào cuộc trò chuyện này" : "Nhập tin nhắn"}
          disabled={disabled}
        />
        <div className="flex items-center justify-between border-t border-border px-2 py-1">
          <div className="relative flex items-center gap-1">
            <input
              ref={input}
              type="file"
              className="hidden"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
            <Button
              type="button"
              size="icon"
              variant="ghost"
              className="h-9 w-9"
              aria-label="Chọn loại tệp"
              onClick={() => setMenu((value) => !value)}
            >
              <Paperclip size={17} />
            </Button>
            {menu && (
              <div className="absolute bottom-11 left-0 z-20 w-48 rounded-panel border border-border bg-surface p-1 shadow-xl">
                {[
                  ["Hình ảnh", "image/*"],
                  ["Video", "video/*"],
                  ["Tài liệu", ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip"],
                  ["Tệp khác", "*/*"],
                ].map(([label, accept]) => (
                  <button
                    key={label}
                    type="button"
                    className="flex w-full items-center rounded-control px-3 py-2 text-left text-[13px] text-ink hover:bg-surface-quiet"
                    onClick={() => choose(accept)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            )}
            <Button
              type="button"
              size="icon"
              variant={recording ? "primary" : "ghost"}
              className="h-9 w-9"
              aria-label={recording ? "Dừng ghi âm" : "Ghi âm"}
              onClick={() =>
                recording ? recorder.current?.stop() : void startRecording()
              }
            >
              {recording ? <Square size={15} /> : <Mic size={17} />}
            </Button>
          </div>
          <Button
            type="submit"
            size="icon"
            className="h-9 w-9"
            aria-label="Gửi"
            disabled={processing || disabled || recording || (!value.trim() && !file)}
          >
            <Send size={17} />
          </Button>
        </div>
      </div>
    </form>
  );
}
