"use client";

import { useEffect, useState } from "react";
import {
  checkPlagiarismAPI,
  extractGlossaryAPI,
  factCheckTextAPI,
  summarizeTextAPI,
} from "@/features/agentic_ai/services/inference.service";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";

type TextTool = "summary" | "glossary" | "fact_check" | "plagiarism";

function plainText(content: string) {
  try {
    const parsed = JSON.parse(content);
    if (!Array.isArray(parsed?.blocks)) return content;
    return parsed.blocks
      .map((block: any) => {
        const data = block.data ?? {};
        return data.text ?? data.caption ?? data.code ?? data.items?.join("\n") ?? "";
      })
      .filter(Boolean)
      .join("\n\n");
  } catch {
    return content;
  }
}

export default function EditorTextToolsModal({ open, close, content }: { open: boolean; close: () => void; content: string }) {
  const [tool, setTool] = useState<TextTool>("summary");
  const [source, setSource] = useState("");
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [processing, setProcessing] = useState(false);
  useEffect(() => {
    if (open) setSource(plainText(content));
    else {
      setResult("");
      setError("");
    }
  }, [open, content]);
  const submit = async () => {
    setProcessing(true);
    setError("");
    try {
      const actions = {
        summary: () => summarizeTextAPI(source.trim()),
        glossary: () => extractGlossaryAPI(source.trim()),
        fact_check: () => factCheckTextAPI(source.trim()),
        plagiarism: () => checkPlagiarismAPI(source.trim()),
      };
      const data = await actions[tool]();
      if (tool === "summary") setResult(data.summary || "Không có kết quả");
      else if (tool === "fact_check") setResult(data.fact_check_report || "Không có kết quả");
      else if (tool === "glossary") setResult((data.glossary || []).map((row: any) => `${row.term}: ${row.definition}`).join("\n\n") || "Không có kết quả");
      else {
        const score = Math.round(Number(data.plagiarism_score || 0) * 100);
        setResult([`Mức trùng lặp: ${score}%`, data.message, ...(data.matched_sources || [])].filter(Boolean).join("\n\n"));
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể xử lý nội dung");
    } finally {
      setProcessing(false);
    }
  };
  return (
    <Modal isOpen={open} onClose={close} className="max-w-2xl">
      <ModalHeader><ModalTitle>Công cụ văn bản</ModalTitle></ModalHeader>
      <ModalContent>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {([['summary', 'Tóm tắt'], ['glossary', 'Thuật ngữ'], ['fact_check', 'Kiểm chứng'], ['plagiarism', 'Trùng lặp']] as [TextTool, string][]).map(([id, label]) => (
              <Button key={id} size="sm" variant={tool === id ? "primary" : "secondary"} onClick={() => setTool(id)}>{label}</Button>
            ))}
          </div>
          <textarea value={source} onChange={(event) => setSource(event.target.value)} className="apple-input min-h-44 w-full resize-y" placeholder="Nội dung cần xử lý" />
          {error && <p className="text-[13px] text-danger">{error}</p>}
          {result && <div className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-control border border-border bg-surface-quiet p-4 text-[13px] leading-6 text-ink">{result}</div>}
        </div>
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>Đóng</Button>
        <Button disabled={!source.trim() || processing} onClick={submit}>{processing ? "Đang xử lý" : "Thực hiện"}</Button>
      </ModalFooter>
    </Modal>
  );
}
