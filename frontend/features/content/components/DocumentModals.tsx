"use client";

import { useState } from "react";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";

type Base = { open: boolean; close: () => void; processing: string | null };
export function CreateDocumentModal({
  open,
  close,
  processing,
  submit,
}: Base & {
  submit: (input: {
    title: string;
    description: string;
    visibility: string;
    file: File;
  }) => Promise<boolean>;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState("private");
  const [file, setFile] = useState<File | null>(null);
  const save = async () => {
    if (file && (await submit({ title, description, visibility, file }))) {
      setTitle("");
      setDescription("");
      setFile(null);
      close();
    }
  };
  return (
    <Modal isOpen={open} onClose={close}>
      <ModalHeader>
        <ModalTitle>Tạo tài liệu</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <div className="space-y-4">
          <div>
            <label
              htmlFor="document-title"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Tên tài liệu
            </label>
            <input
              id="document-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="apple-input w-full"
              maxLength={200}
            />
          </div>
          <div>
            <label
              htmlFor="document-description"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Mô tả
            </label>
            <textarea
              id="document-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className="apple-input min-h-24 w-full resize-y"
              maxLength={2000}
            />
          </div>
          <div>
            <label
              htmlFor="document-visibility"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Quyền truy cập
            </label>
            <select
              id="document-visibility"
              value={visibility}
              onChange={(event) => setVisibility(event.target.value)}
              className="apple-input w-full"
            >
              <option value="private">Riêng tư</option>
              <option value="unlisted">Không công bố</option>
              <option value="public">Công khai</option>
            </select>
          </div>
          <div>
            <label
              htmlFor="document-file"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Tệp nội dung
            </label>
            <input
              id="document-file"
              type="file"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              className="apple-input w-full"
            />
          </div>
        </div>
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Hủy
        </Button>
        <Button
          disabled={!title.trim() || !file || processing === "document"}
          onClick={save}
        >
          {processing === "document" ? "Đang tạo" : "Tạo tài liệu"}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
export function TextModal({
  open,
  close,
  processing,
  title,
  label,
  action,
  secret = false,
  submit,
}: Base & {
  title: string;
  label: string;
  action: string;
  secret?: boolean;
  submit: (value: string) => Promise<boolean>;
}) {
  const [value, setValue] = useState("");
  const save = async () => {
    if (await submit(value)) {
      setValue("");
      close();
    }
  };
  return (
    <Modal isOpen={open} onClose={close}>
      <ModalHeader>
        <ModalTitle>{title}</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <label
          htmlFor="text-modal-value"
          className="mb-2 block text-[13px] font-semibold text-ink"
        >
          {label}
        </label>
        <input
          id="text-modal-value"
          type={secret ? "password" : "text"}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          className="apple-input w-full"
        />
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Hủy
        </Button>
        <Button disabled={!value.trim() || Boolean(processing)} onClick={save}>
          {processing ? "Đang xử lý" : action}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

export function ImportDocumentModal({
  open,
  close,
  processing,
  submit,
}: Base & { submit: (file: File) => Promise<boolean> }) {
  const [file, setFile] = useState<File | null>(null);
  const save = async () => {
    if (file && (await submit(file))) {
      setFile(null);
      close();
    }
  };
  return (
    <Modal isOpen={open} onClose={close}>
      <ModalHeader>
        <ModalTitle>Nhập tài liệu</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <label
          htmlFor="document-import"
          className="mb-2 block text-[13px] font-semibold text-ink"
        >
          Tệp DocLib
        </label>
        <input
          id="document-import"
          type="file"
          accept=".doclib,.doclibx"
          onChange={(event) => setFile(event.target.files?.[0] || null)}
          className="apple-input w-full"
        />
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Hủy
        </Button>
        <Button disabled={!file || processing === "import"} onClick={save}>
          {processing === "import" ? "Đang nhập" : "Nhập"}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
export function ConfirmDeleteModal({
  open,
  close,
  processing,
  submit,
}: Base & { submit: () => Promise<void> }) {
  return (
    <Modal isOpen={open} onClose={close}>
      <ModalHeader>
        <ModalTitle>Xóa mục đã chọn</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <p className="text-[14px] leading-relaxed text-ink-muted">
          Tài liệu sẽ được chuyển vào thùng rác. Thư mục chỉ có thể xóa khi
          không còn dữ liệu phụ thuộc
        </p>
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Hủy
        </Button>
        <Button
          variant="danger"
          disabled={Boolean(processing)}
          onClick={submit}
        >
          {processing ? "Đang xóa" : "Xóa"}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
