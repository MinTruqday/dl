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

export default function PollModal({ open, close, create }: { open: boolean; close: () => void; create: (question: string, options: string[]) => Promise<boolean> }) {
  const [question, setQuestion] = useState("");
  const [options, setOptions] = useState(["", ""]);
  const [processing, setProcessing] = useState(false);
  const submit = async () => {
    setProcessing(true);
    const values = options.map((value) => value.trim()).filter(Boolean);
    if (await create(question.trim(), values)) {
      setQuestion("");
      setOptions(["", ""]);
      close();
    }
    setProcessing(false);
  };
  return (
    <Modal isOpen={open} onClose={close} className="max-w-lg">
      <ModalHeader><ModalTitle>Tạo bình chọn</ModalTitle></ModalHeader>
      <ModalContent>
        <div className="space-y-3">
          <input value={question} onChange={(event) => setQuestion(event.target.value)} className="apple-input w-full" placeholder="Câu hỏi" />
          {options.map((option, index) => (
            <input
              key={index}
              value={option}
              onChange={(event) => setOptions((rows) => rows.map((row, rowIndex) => rowIndex === index ? event.target.value : row))}
              className="apple-input w-full"
              placeholder={`Lựa chọn ${index + 1}`}
            />
          ))}
          {options.length < 6 && <Button size="sm" variant="secondary" onClick={() => setOptions((rows) => [...rows, ""])}>Thêm lựa chọn</Button>}
        </div>
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>Đóng</Button>
        <Button disabled={processing || !question.trim() || options.filter((value) => value.trim()).length < 2} onClick={submit}>{processing ? "Đang tạo" : "Tạo"}</Button>
      </ModalFooter>
    </Modal>
  );
}
