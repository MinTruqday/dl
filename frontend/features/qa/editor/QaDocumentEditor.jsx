"use client";
import { useEffect } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import Link from "@tiptap/extension-link";
import Image from "@tiptap/extension-image";
import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableHeader from "@tiptap/extension-table-header";
import TableCell from "@tiptap/extension-table-cell";
import {
  Bold,
  Code2,
  Heading1,
  Heading2,
  ImagePlus,
  Italic,
  Link as LinkIcon,
  List,
  ListOrdered,
  Quote,
  Redo2,
  Table2,
  Underline as UnderlineIcon,
  Undo2,
} from "lucide-react";

const extensions = [
  StarterKit,
  Underline,
  Link.configure({ openOnClick: false, autolink: true }),
  Image.configure({ allowBase64: false }),
  Table.configure({ resizable: true }),
  TableRow,
  TableHeader,
  TableCell,
];

export default function QaDocumentEditor({
  value,
  onChange,
  label,
  minHeight = "min-h-40",
  readOnly = false,
}) {
  const editor = useEditor({
    immediatelyRender: false,
    extensions,
    content: value,
    editable: !readOnly,
    editorProps: {
      attributes: { class: `qa-tiptap ${minHeight}`, role: "textbox", "aria-label": label },
    },
    onUpdate({ editor: current }) {
      onChange?.(current.getJSON());
    },
  });
  useEffect(() => {
    if (!editor) return;
    editor.setEditable(!readOnly);
    if (JSON.stringify(editor.getJSON()) !== JSON.stringify(value))
      editor.commands.setContent(value, false);
  }, [editor, readOnly, value]);
  if (!editor) return <div className={`${minHeight} skeleton`} />;
  if (readOnly)
    return (
      <div className="overflow-hidden rounded-panel border border-border bg-surface">
        <EditorContent editor={editor} />
      </div>
    );
  const addLink = () => {
    const href = window.prompt(
      "Đường dẫn liên kết",
      editor.getAttributes("link").href || "https://",
    );
    if (href === null) return;
    if (!href.trim()) return editor.chain().focus().extendMarkRange("link").unsetLink().run();
    try {
      const parsed = new URL(href.trim());
      if (!["http:", "https:", "mailto:"].includes(parsed.protocol)) throw new Error("invalid");
      editor.chain().focus().extendMarkRange("link").setLink({ href: parsed.toString() }).run();
    } catch {
      window.alert("Liên kết chỉ hỗ trợ HTTP HTTPS hoặc email");
    }
  };
  const addImage = () => {
    const src = window.prompt("Đường dẫn hình ảnh");
    if (!src) return;
    const alt = window.prompt("Mô tả hình ảnh");
    if (alt?.trim()) editor.chain().focus().setImage({ src: src.trim(), alt: alt.trim() }).run();
  };
  const button = (name, active, action, icon) => (
    <button
      type="button"
      className="editor-tool"
      aria-label={name}
      aria-pressed={active}
      onClick={action}
    >
      {icon}
    </button>
  );
  return (
    <div className="overflow-hidden rounded-panel border border-border bg-surface">
      <div className="qa-editor-toolbar" aria-label="Công cụ soạn thảo QA">
        <div className="editor-tool-group">
          {button(
            "In đậm",
            editor.isActive("bold"),
            () => editor.chain().focus().toggleBold().run(),
            <Bold size={17} />,
          )}
          {button(
            "In nghiêng",
            editor.isActive("italic"),
            () => editor.chain().focus().toggleItalic().run(),
            <Italic size={17} />,
          )}
          {button(
            "Gạch chân",
            editor.isActive("underline"),
            () => editor.chain().focus().toggleUnderline().run(),
            <UnderlineIcon size={17} />,
          )}
          {button(
            "Tiêu đề cấp 1",
            editor.isActive("heading", { level: 1 }),
            () => editor.chain().focus().toggleHeading({ level: 1 }).run(),
            <Heading1 size={17} />,
          )}
          {button(
            "Tiêu đề cấp 2",
            editor.isActive("heading", { level: 2 }),
            () => editor.chain().focus().toggleHeading({ level: 2 }).run(),
            <Heading2 size={17} />,
          )}
          {button(
            "Danh sách",
            editor.isActive("bulletList"),
            () => editor.chain().focus().toggleBulletList().run(),
            <List size={17} />,
          )}
          {button(
            "Danh sách đánh số",
            editor.isActive("orderedList"),
            () => editor.chain().focus().toggleOrderedList().run(),
            <ListOrdered size={17} />,
          )}
          {button(
            "Trích dẫn",
            editor.isActive("blockquote"),
            () => editor.chain().focus().toggleBlockquote().run(),
            <Quote size={17} />,
          )}
          {button(
            "Khối mã",
            editor.isActive("codeBlock"),
            () => editor.chain().focus().toggleCodeBlock().run(),
            <Code2 size={17} />,
          )}
          {button("Liên kết", editor.isActive("link"), addLink, <LinkIcon size={17} />)}
          {button("Hình ảnh", false, addImage, <ImagePlus size={17} />)}
          {button(
            "Bảng",
            editor.isActive("table"),
            () =>
              editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(),
            <Table2 size={17} />,
          )}
          {button(
            "Hoàn tác",
            false,
            () => editor.chain().focus().undo().run(),
            <Undo2 size={17} />,
          )}
          {button("Làm lại", false, () => editor.chain().focus().redo().run(), <Redo2 size={17} />)}
        </div>
      </div>
      <EditorContent editor={editor} />
    </div>
  );
}
