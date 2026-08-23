"use client";

import { useEffect } from "react";
import Image from "@tiptap/extension-image";
import Mathematics from "@tiptap/extension-mathematics";
import Table from "@tiptap/extension-table";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import TableRow from "@tiptap/extension-table-row";
import StarterKit from "@tiptap/starter-kit";
import { EditorContent, useEditor } from "@tiptap/react";
import { AlignCenter, AlignLeft, Bold, Heading2, ImagePlus, Italic, List, ListOrdered, PlusSquare, Redo2, SeparatorHorizontal, Sigma, Table2, Underline as UnderlineIcon, Undo2 } from "lucide-react";
import type { TiptapDoc } from "../types";
import { PageBreak } from "./extensions/PageBreak";
import { QuestionRef } from "./extensions/QuestionRef";
import { AssessmentSection } from "./extensions/Section";
import { TextAlign } from "./extensions/TextAlign";
import { Underline } from "./extensions/Underline";

type Props = {
  value: TiptapDoc;
  onChange: (value: TiptapDoc) => void;
  label: string;
  minHeight?: string;
};

export default function TiptapDocumentEditor({ value, onChange, label, minHeight = "min-h-40" }: Props) {
  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit,
      Underline,
      TextAlign,
      Mathematics,
      Image.configure({ allowBase64: false }),
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
      AssessmentSection,
      QuestionRef,
      PageBreak,
    ],
    content: value,
    editorProps: {
      attributes: {
        class: `assessment-tiptap ${minHeight}`,
        role: "textbox",
        "aria-label": label,
      },
    },
    onUpdate({ editor: current }) {
      onChange(current.getJSON() as TiptapDoc);
    },
  });

  useEffect(() => {
    if (!editor) return;
    if (JSON.stringify(editor.getJSON()) !== JSON.stringify(value)) {
      editor.commands.setContent(value, false);
    }
  }, [editor, value]);

  if (!editor) return <div className={`${minHeight} skeleton`} />;

  const addImage = () => {
    const url = window.prompt("Đường dẫn hình ảnh");
    if (!url) return;
    const alt = window.prompt("Mô tả hình ảnh cho người dùng trình đọc màn hình");
    if (alt?.trim()) editor.chain().focus().setImage({ src: url, alt: alt.trim() }).run();
  };

  const addMath = () => {
    const latex = window.prompt("Công thức LaTeX");
    if (latex?.trim()) editor.chain().focus().insertContent({ type: "text", text: `$${latex.trim()}$` }).run();
  };

  const addAssessmentNode = () => {
    const action = window.prompt("Nhập section pagebreak hoặc question");
    if (action === "section") editor.chain().focus().insertContent({ type: "assessmentSection", attrs: { sectionId: crypto.randomUUID(), title: "Phần mới" }, content: [{ type: "paragraph" }] }).run();
    if (action === "pagebreak") editor.chain().focus().insertContent({ type: "pageBreak" }).run();
    if (action === "question") {
      const questionId = window.prompt("Mã QuestionDraft hoặc QuestionVersion");
      if (questionId) editor.chain().focus().insertContent({ type: "questionRef", attrs: { questionId, label: `Câu hỏi ${questionId}` } }).run();
    }
  };

  return (
    <div className="overflow-hidden rounded-panel border border-border bg-surface">
      <div className="flex flex-wrap items-center gap-1 border-b border-border bg-surface-quiet px-2 py-2" aria-label="Công cụ soạn thảo">
        <button type="button" className="editor-tool" aria-label="In đậm" aria-pressed={editor.isActive("bold")} onClick={() => editor.chain().focus().toggleBold().run()}>
          <Bold size={17} />
        </button>
        <button type="button" className="editor-tool" aria-label="In nghiêng" aria-pressed={editor.isActive("italic")} onClick={() => editor.chain().focus().toggleItalic().run()}><Italic size={17} /></button>
        <button type="button" className="editor-tool" aria-label="Gạch chân" aria-pressed={editor.isActive("underline")} onClick={() => editor.chain().focus().toggleMark("underline").run()}><UnderlineIcon size={17} /></button>
        <button type="button" className="editor-tool" aria-label="Tiêu đề" aria-pressed={editor.isActive("heading", { level: 2 })} onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}>
          <Heading2 size={17} />
        </button>
        <button type="button" className="editor-tool" aria-label="Danh sách" aria-pressed={editor.isActive("bulletList")} onClick={() => editor.chain().focus().toggleBulletList().run()}>
          <List size={17} />
        </button>
        <button type="button" className="editor-tool" aria-label="Danh sách đánh số" aria-pressed={editor.isActive("orderedList")} onClick={() => editor.chain().focus().toggleOrderedList().run()}><ListOrdered size={17} /></button>
        <button type="button" className="editor-tool" aria-label="Căn trái" onClick={() => editor.chain().focus().updateAttributes("paragraph", { textAlign: "left" }).updateAttributes("heading", { textAlign: "left" }).run()}><AlignLeft size={17} /></button>
        <button type="button" className="editor-tool" aria-label="Căn giữa" onClick={() => editor.chain().focus().updateAttributes("paragraph", { textAlign: "center" }).updateAttributes("heading", { textAlign: "center" }).run()}><AlignCenter size={17} /></button>
        <button type="button" className="editor-tool" aria-label="Công thức" onClick={addMath}>
          <Sigma size={17} />
        </button>
        <button type="button" className="editor-tool" aria-label="Bảng" onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}>
          <Table2 size={17} />
        </button>
        <button type="button" className="editor-tool" aria-label="Hình ảnh" onClick={addImage}>
          <ImagePlus size={17} />
        </button>
        <button type="button" className="editor-tool" aria-label="Thêm section ngắt trang hoặc câu hỏi" onClick={addAssessmentNode}><PlusSquare size={17} /></button>
        <button type="button" className="editor-tool" aria-label="Ngắt trang" onClick={() => editor.chain().focus().insertContent({ type: "pageBreak" }).run()}><SeparatorHorizontal size={17} /></button>
        <button type="button" className="editor-tool" aria-label="Hoàn tác" disabled={!editor.can().undo()} onClick={() => editor.chain().focus().undo().run()}><Undo2 size={17} /></button>
        <button type="button" className="editor-tool" aria-label="Làm lại" disabled={!editor.can().redo()} onClick={() => editor.chain().focus().redo().run()}><Redo2 size={17} /></button>
      </div>
      <EditorContent editor={editor} />
    </div>
  );
}
