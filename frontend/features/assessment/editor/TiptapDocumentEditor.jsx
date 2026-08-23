"use client";
import { useEffect } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import {
  AlignCenter,
  AlignJustify,
  AlignLeft,
  AlignRight,
  Bold,
  Braces,
  ChevronDownSquare,
  Code2,
  Columns3,
  Heading1,
  Heading2,
  Heading3,
  Highlighter,
  ImagePlus,
  Italic,
  Link as LinkIcon,
  List,
  ListChecks,
  ListOrdered,
  Minus,
  PlusSquare,
  Quote,
  Redo2,
  Rows3,
  SeparatorHorizontal,
  Sigma,
  Strikethrough,
  Subscript as SubscriptIcon,
  Superscript as SuperscriptIcon,
  Table2,
  Trash2,
  Underline as UnderlineIcon,
  Undo2,
  Unlink,
  Video,
} from "lucide-react";
import { createAssessmentExtensions } from "./extensions";
export default function TiptapDocumentEditor({ value, onChange, label, minHeight = "min-h-40" }) {
  const editor = useEditor({
    immediatelyRender: false,
    extensions: createAssessmentExtensions(true),
    content: value,
    editorProps: {
      attributes: {
        class: `assessment-tiptap ${minHeight}`,
        role: "textbox",
        "aria-label": label,
      },
    },
    onUpdate({ editor: current }) {
      onChange(current.getJSON());
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
    if (alt?.trim()) editor.chain().focus().setImage({ src: url.trim(), alt: alt.trim() }).run();
  };
  const addLink = () => {
    const previousUrl = editor.getAttributes("link").href;
    const url = window.prompt("Đường dẫn liên kết", previousUrl || "https://");
    if (url === null) return;
    if (!url.trim()) {
      editor.chain().focus().extendMarkRange("link").unsetLink().run();
      return;
    }
    try {
      const parsed = new URL(url.trim());
      if (!["http:", "https:", "mailto:"].includes(parsed.protocol))
        throw new Error("invalid_protocol");
      editor.chain().focus().extendMarkRange("link").setLink({ href: parsed.toString() }).run();
    } catch {
      window.alert("Liên kết chỉ hỗ trợ HTTP HTTPS hoặc email");
    }
  };
  const addMath = () => {
    const latex = window.prompt("Công thức LaTeX");
    if (latex?.trim()) editor.chain().focus().insertContent(`$${latex.trim()}$`).run();
  };
  const addVideo = () => {
    const url = window.prompt("Đường dẫn video YouTube");
    if (url?.trim()) editor.commands.setYoutubeVideo({ src: url.trim(), width: 640, height: 360 });
  };
  const addAssessmentNode = () => {
    const action = window.prompt("Nhập section pagebreak hoặc question");
    if (action === "section")
      editor
        .chain()
        .focus()
        .insertContent({
          type: "assessmentSection",
          attrs: { sectionId: crypto.randomUUID(), title: "Phần mới" },
          content: [{ type: "paragraph" }],
        })
        .run();
    if (action === "pagebreak") editor.chain().focus().insertContent({ type: "pageBreak" }).run();
    if (action === "question") {
      const questionId = window.prompt("Mã QuestionDraft hoặc QuestionVersion");
      if (questionId)
        editor
          .chain()
          .focus()
          .insertContent({
            type: "questionRef",
            attrs: { questionId, label: `Câu hỏi ${questionId}` },
          })
          .run();
    }
  };
  const tool = (labelText, active, action, icon, disabled = false) => (
    <button
      type="button"
      className="editor-tool"
      aria-label={labelText}
      aria-pressed={active}
      disabled={disabled}
      onClick={action}
    >
      {icon}
    </button>
  );
  return (
    <div className="overflow-hidden rounded-panel border border-border bg-surface">
      <div className="assessment-editor-toolbar" aria-label="Công cụ soạn thảo">
        <div className="editor-tool-group">
          {tool(
            "In đậm",
            editor.isActive("bold"),
            () => editor.chain().focus().toggleBold().run(),
            <Bold size={17} />,
          )}
          {tool(
            "In nghiêng",
            editor.isActive("italic"),
            () => editor.chain().focus().toggleItalic().run(),
            <Italic size={17} />,
          )}
          {tool(
            "Gạch chân",
            editor.isActive("underline"),
            () => editor.chain().focus().toggleUnderline().run(),
            <UnderlineIcon size={17} />,
          )}
          {tool(
            "Gạch ngang",
            editor.isActive("strike"),
            () => editor.chain().focus().toggleStrike().run(),
            <Strikethrough size={17} />,
          )}
          {tool(
            "Mã nội dòng",
            editor.isActive("code"),
            () => editor.chain().focus().toggleCode().run(),
            <Braces size={17} />,
          )}
          {tool(
            "Đánh dấu",
            editor.isActive("highlight"),
            () => editor.chain().focus().toggleHighlight({ color: "#fef08a" }).run(),
            <Highlighter size={17} />,
          )}
          {tool(
            "Chỉ số dưới",
            editor.isActive("subscript"),
            () => editor.chain().focus().toggleSubscript().run(),
            <SubscriptIcon size={17} />,
          )}
          {tool(
            "Chỉ số trên",
            editor.isActive("superscript"),
            () => editor.chain().focus().toggleSuperscript().run(),
            <SuperscriptIcon size={17} />,
          )}
        </div>
        <div className="editor-tool-group">
          {tool(
            "Đoạn văn",
            editor.isActive("paragraph"),
            () => editor.chain().focus().setParagraph().run(),
            <span className="text-sm font-semibold">P</span>,
          )}
          {tool(
            "Tiêu đề cấp 1",
            editor.isActive("heading", { level: 1 }),
            () => editor.chain().focus().toggleHeading({ level: 1 }).run(),
            <Heading1 size={17} />,
          )}
          {tool(
            "Tiêu đề cấp 2",
            editor.isActive("heading", { level: 2 }),
            () => editor.chain().focus().toggleHeading({ level: 2 }).run(),
            <Heading2 size={17} />,
          )}
          {tool(
            "Tiêu đề cấp 3",
            editor.isActive("heading", { level: 3 }),
            () => editor.chain().focus().toggleHeading({ level: 3 }).run(),
            <Heading3 size={17} />,
          )}
          {tool(
            "Trích dẫn",
            editor.isActive("blockquote"),
            () => editor.chain().focus().toggleBlockquote().run(),
            <Quote size={17} />,
          )}
          {tool(
            "Khối mã",
            editor.isActive("codeBlock"),
            () => editor.chain().focus().toggleCodeBlock().run(),
            <Code2 size={17} />,
          )}
        </div>
        <div className="editor-tool-group">
          {tool(
            "Danh sách dấu đầu dòng",
            editor.isActive("bulletList"),
            () => editor.chain().focus().toggleBulletList().run(),
            <List size={17} />,
          )}
          {tool(
            "Danh sách đánh số",
            editor.isActive("orderedList"),
            () => editor.chain().focus().toggleOrderedList().run(),
            <ListOrdered size={17} />,
          )}
          {tool(
            "Danh sách tác vụ",
            editor.isActive("taskList"),
            () => editor.chain().focus().toggleTaskList().run(),
            <ListChecks size={17} />,
          )}
          {tool(
            "Căn trái",
            editor.isActive({ textAlign: "left" }),
            () => editor.chain().focus().setTextAlign("left").run(),
            <AlignLeft size={17} />,
          )}
          {tool(
            "Căn giữa",
            editor.isActive({ textAlign: "center" }),
            () => editor.chain().focus().setTextAlign("center").run(),
            <AlignCenter size={17} />,
          )}
          {tool(
            "Căn phải",
            editor.isActive({ textAlign: "right" }),
            () => editor.chain().focus().setTextAlign("right").run(),
            <AlignRight size={17} />,
          )}
          {tool(
            "Căn đều",
            editor.isActive({ textAlign: "justify" }),
            () => editor.chain().focus().setTextAlign("justify").run(),
            <AlignJustify size={17} />,
          )}
        </div>
        <div className="editor-tool-group">
          {tool("Thêm hoặc sửa liên kết", editor.isActive("link"), addLink, <LinkIcon size={17} />)}
          {tool(
            "Xóa liên kết",
            false,
            () => editor.chain().focus().unsetLink().run(),
            <Unlink size={17} />,
            !editor.isActive("link"),
          )}
          <label className="editor-tool" aria-label="Màu chữ">
            <input
              type="color"
              className="h-5 w-5 cursor-pointer border-0 bg-transparent p-0"
              value={editor.getAttributes("textStyle").color || "#1d1d1f"}
              onChange={(event) => editor.chain().focus().setColor(event.target.value).run()}
            />
          </label>
          <select
            className="editor-select"
            aria-label="Phông chữ"
            value={editor.getAttributes("textStyle").fontFamily || ""}
            onChange={(event) =>
              event.target.value
                ? editor.chain().focus().setFontFamily(event.target.value).run()
                : editor.chain().focus().unsetFontFamily().run()
            }
          >
            <option value="">Mặc định</option>
            <option value="Arial">Arial</option>
            <option value="Georgia">Georgia</option>
            <option value="Times New Roman">Times New Roman</option>
            <option value="Courier New">Courier New</option>
          </select>
        </div>
        <div className="editor-tool-group">
          {tool("Công thức", false, addMath, <Sigma size={17} />)}
          {tool("Hình ảnh", false, addImage, <ImagePlus size={17} />)}
          {tool("Video YouTube", false, addVideo, <Video size={17} />)}
          {tool(
            "Khối thu gọn",
            editor.isActive("details"),
            () => editor.chain().focus().setDetails().run(),
            <ChevronDownSquare size={17} />,
          )}
          {tool(
            "Đường phân cách",
            false,
            () => editor.chain().focus().setHorizontalRule().run(),
            <Minus size={17} />,
          )}
          {tool(
            "Thêm section ngắt trang hoặc câu hỏi",
            false,
            addAssessmentNode,
            <PlusSquare size={17} />,
          )}
          {tool(
            "Ngắt trang",
            false,
            () => editor.chain().focus().insertContent({ type: "pageBreak" }).run(),
            <SeparatorHorizontal size={17} />,
          )}
        </div>
        <div className="editor-tool-group">
          {tool(
            "Chèn bảng",
            editor.isActive("table"),
            () =>
              editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(),
            <Table2 size={17} />,
          )}
          {tool(
            "Thêm hàng",
            false,
            () => editor.chain().focus().addRowAfter().run(),
            <Rows3 size={17} />,
            !editor.isActive("table"),
          )}
          {tool(
            "Thêm cột",
            false,
            () => editor.chain().focus().addColumnAfter().run(),
            <Columns3 size={17} />,
            !editor.isActive("table"),
          )}
          {tool(
            "Xóa hàng",
            false,
            () => editor.chain().focus().deleteRow().run(),
            <span className="text-xs font-semibold">−R</span>,
            !editor.isActive("table"),
          )}
          {tool(
            "Xóa cột",
            false,
            () => editor.chain().focus().deleteColumn().run(),
            <span className="text-xs font-semibold">−C</span>,
            !editor.isActive("table"),
          )}
          {tool(
            "Xóa bảng",
            false,
            () => editor.chain().focus().deleteTable().run(),
            <Trash2 size={17} />,
            !editor.isActive("table"),
          )}
        </div>
        <div className="editor-tool-group">
          {tool(
            "Hoàn tác",
            false,
            () => editor.chain().focus().undo().run(),
            <Undo2 size={17} />,
            !editor.can().undo(),
          )}
          {tool(
            "Làm lại",
            false,
            () => editor.chain().focus().redo().run(),
            <Redo2 size={17} />,
            !editor.can().redo(),
          )}
        </div>
        <output className="ml-auto px-2 text-[11px] font-medium text-ink-faint" aria-live="polite">
          {editor.storage.characterCount.characters()} ký tự ·{" "}
          {editor.storage.characterCount.words()} từ
        </output>
      </div>
      <EditorContent editor={editor} />
    </div>
  );
}
