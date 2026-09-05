"use client";
import { useEffect, useState } from "react";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
export default function ChatInstructionsModal({ open, close, initial, save }) {
  const [value, setValue] = useState(initial);
  const [saving, setSaving] = useState(false);
  useEffect(() => setValue(initial), [initial, open]);
  const submit = async () => {
    setSaving(true);
    if (await save(value)) close();
    setSaving(false);
  };
  return (
    <Modal isOpen={open} onClose={close} ariaLabel="Chỉ dẫn cá nhân">
      <ModalHeader>
        <ModalTitle>Chỉ dẫn cá nhân</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <label
          htmlFor="chat-instructions"
          className="mb-2 block text-[13px] font-semibold text-ink"
        >
          Cách trợ lý nên phản hồi
        </label>
        <textarea
          id="chat-instructions"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          maxLength={4000}
          className="apple-input min-h-40 w-full resize-y"
        />
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Hủy
        </Button>
        <Button disabled={saving} onClick={submit}>
          {saving ? "Đang lưu" : "Lưu"}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
