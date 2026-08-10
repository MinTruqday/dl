"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Image as ImageIcon, Link2, Video } from "lucide-react";
import SegmentedTabs from "@/shared/components/navigation/SegmentedTabs";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";

function attachmentKind(file: any) {
  const type = String(file?.type ?? file?.content_type ?? "");
  const name = String(file?.name ?? file?.filename ?? "");
  if (type.startsWith("image/") || /\.(png|jpe?g|gif|webp)$/i.test(name)) return "Hình ảnh";
  if (type.startsWith("video/") || /\.(mp4|webm|mov)$/i.test(name)) return "Video";
  if (/^https?:\/\//.test(name)) return "Đường dẫn";
  return "Tệp";
}

export default function ConversationDetailsModal({
  open,
  close,
  settings,
  media,
  loadingMedia,
  loadMedia,
  setTimer,
}: {
  open: boolean;
  close: () => void;
  settings: any;
  media: any[];
  loadingMedia: boolean;
  loadMedia: () => Promise<any[]>;
  setTimer: (seconds: number) => Promise<boolean>;
}) {
  const [tab, setTab] = useState("general");
  const timer = Number(settings?.self_destruct_seconds ?? settings?.timer_seconds ?? 0);
  useEffect(() => {
    if (open && tab === "media") void loadMedia();
  }, [open, tab, loadMedia]);

  return (
    <Modal isOpen={open} onClose={close} className="max-w-2xl">
      <ModalHeader>
        <ModalTitle>Thông tin cuộc trò chuyện</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <SegmentedTabs
          label="Nội dung"
          value={tab}
          onChange={setTab}
          tabs={[
            { id: "general", label: "Cài đặt" },
            { id: "media", label: "Tệp đã chia sẻ" },
          ]}
        />
        {tab === "general" ? (
          <div className="mt-5 border-y border-border py-4">
            <label className="grid gap-2 text-[13px] font-semibold text-ink">
              Tự xóa tin nhắn sau khi đọc
              <select
                value={timer}
                onChange={(event) => void setTimer(Number(event.target.value))}
                className="apple-input h-10 min-h-10 font-normal"
              >
                <option value={0}>Tắt</option>
                <option value={60}>1 phút</option>
                <option value={3600}>1 giờ</option>
                <option value={86400}>1 ngày</option>
              </select>
            </label>
            <p className="mt-3 text-[12px] leading-5 text-ink-muted">
              Thiết lập áp dụng cho các tin nhắn gửi sau thời điểm thay đổi
            </p>
          </div>
        ) : loadingMedia ? (
          <div className="mt-5"><PageLoader rows={4} /></div>
        ) : media.length ? (
          <ul className="mt-5 max-h-[420px] divide-y divide-border overflow-y-auto border-y border-border">
            {media.map((row, index) => {
              const file = row.file ?? row;
              const url = file.display_url ?? file.url ?? file.file_url;
              const kind = attachmentKind(file);
              const Icon = kind === "Hình ảnh" ? ImageIcon : kind === "Video" ? Video : kind === "Đường dẫn" ? Link2 : FileText;
              return (
                <li key={`${row.message_id ?? url}-${index}`}>
                  <a href={url} target="_blank" rel="noreferrer" className="flex items-center gap-3 px-2 py-3 hover:bg-surface-quiet">
                    <Icon size={17} className="shrink-0 text-ink-muted" />
                    <span className="min-w-0 flex-1 truncate text-[13px] font-medium text-ink">
                      {file.name ?? file.filename ?? kind}
                    </span>
                    <span className="text-[11px] text-ink-muted">{kind}</span>
                  </a>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="mt-5 border-y border-border py-8 text-center text-[13px] text-ink-muted">Chưa có tệp được chia sẻ</p>
        )}
      </ModalContent>
      <ModalFooter>
        <Link href="/luu-tru" className="pill-button pill-button-secondary">Mở kho cá nhân</Link>
        <Button variant="secondary" onClick={close}>Đóng</Button>
      </ModalFooter>
    </Modal>
  );
}
