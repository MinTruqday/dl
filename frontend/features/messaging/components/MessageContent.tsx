"use client";

import { FileText } from "lucide-react";

function pollData(content: string) {
  try {
    const value = JSON.parse(content);
    return value?.type === "poll" ? value.data ?? value : null;
  } catch {
    return null;
  }
}

function linkedText(content: string) {
  const parts = content.split(new RegExp("(https?:" + "\\/\\/[^\\s]+)", "g"));
  return parts.map((part, index) =>
    part.startsWith("http://") || part.startsWith("https://") ? (
      <a key={`${part}-${index}`} href={part} target="_blank" rel="noreferrer" className="underline">
        {part}
      </a>
    ) : (
      part
    ),
  );
}

export default function MessageContent({
  message,
  vote,
}: {
  message: any;
  vote: (optionId: string) => void;
}) {
  const poll = pollData(message.content ?? "");
  const attachments = message.attachments ?? [];
  if (message.is_recalled)
    return <p className="text-[14px] text-current/70">Tin nhắn đã thu hồi</p>;

  return (
    <div className="space-y-2">
      {poll ? (
        <div className="min-w-[240px]">
          <p className="text-[14px] font-semibold">{poll.question}</p>
          <div className="mt-3 space-y-2">
            {(poll.options ?? []).map((option: any, index: number) => {
              const id = String(option.id ?? option._id ?? index);
              const votes = option.votes?.length ?? option.vote_count ?? 0;
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => vote(id)}
                  className="flex w-full items-center justify-between gap-4 rounded-control border border-current/20 px-3 py-2 text-left text-[13px] hover:bg-current/10"
                >
                  <span>{option.text ?? option.label ?? option}</span>
                  <span className="text-[11px] opacity-70">{votes}</span>
                </button>
              );
            })}
          </div>
        </div>
      ) : message.content ? (
        <p className="whitespace-pre-wrap break-words text-[14px] leading-relaxed">
          {linkedText(message.content)}
        </p>
      ) : null}
      {message.image_url && (
        <a href={message.display_image_url ?? message.image_url} target="_blank" rel="noreferrer">
          <img src={message.display_image_url ?? message.image_url} alt="Hình ảnh đã gửi" className="max-h-72 rounded-control object-contain" />
        </a>
      )}
      {message.audio_url && <audio controls preload="metadata" src={message.display_audio_url ?? message.audio_url} className="h-10 w-[260px] max-w-full" />}
      {attachments.map((attachment: any, index: number) => {
        const url = attachment.display_url ?? attachment.url ?? attachment.file_url;
        const name = attachment.name ?? attachment.filename ?? "Tệp đính kèm";
        const type = String(attachment.type ?? attachment.content_type ?? "");
        if (type.startsWith("video/") || /\.(mp4|webm|mov)$/i.test(name))
          return <video key={`${url}-${index}`} controls preload="metadata" src={url} className="max-h-72 max-w-full rounded-control" />;
        if (type.startsWith("image/") || /\.(png|jpe?g|gif|webp)$/i.test(name))
          return <img key={`${url}-${index}`} src={url} alt={name} className="max-h-72 rounded-control object-contain" />;
        return (
          <a key={`${url}-${index}`} href={url} target="_blank" rel="noreferrer" className="flex items-center gap-2 rounded-control border border-current/20 px-3 py-2 text-[12px] hover:bg-current/10">
            <FileText size={15} />
            <span className="truncate">{name}</span>
          </a>
        );
      })}
      {!poll && !message.content && !message.image_url && !message.audio_url && !attachments.length && (
        <p className="text-[14px] text-current/70">Tin nhắn không có nội dung hiển thị</p>
      )}
    </div>
  );
}
