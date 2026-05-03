"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Mathematics from "@tiptap/extension-mathematics";
import React, { useState, useEffect, useCallback } from "react";
import { Extension } from "./Extension";
import { AutoComplete } from "./AutoComplete";
import "katex/dist/katex.min.css";
import {
  Code,
  FileText,
  Download,
  Bold,
  Italic,
  Play,
  Save,
  ChevronLeft,
  Loader2,
  List,
  Image as ImageIcon,
  Link as LinkIcon,
  Underline as UnderlineIcon,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  Highlighter,
  CheckSquare,
  Subscript as SubscriptIcon,
  Superscript as SuperscriptIcon,
  Undo,
  Redo,
  Strikethrough,
  Quote,
  Code as CodeIcon,
  SquareTerminal,
  Minus,
  Video,
  Sparkles,
} from "lucide-react";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";
import {
  compilePreviewAPI,
  getSynonymsAPI,
  grammarCheckAPI,
} from "@/services/editor.service";
import { useToast } from "@/contexts/ToastContext";

import Placeholder from "@tiptap/extension-placeholder";
import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import Focus from "@tiptap/extension-focus";
import CharacterCount from "@tiptap/extension-character-count";
import Image from "@tiptap/extension-image";
import Link from "@tiptap/extension-link";
import Underline from "@tiptap/extension-underline";
import TextAlign from "@tiptap/extension-text-align";
import Highlight from "@tiptap/extension-highlight";
import Typography from "@tiptap/extension-typography";
import TaskList from "@tiptap/extension-task-list";
import TaskItem from "@tiptap/extension-task-item";
import TextStyle from "@tiptap/extension-text-style";
import Color from "@tiptap/extension-color";
import Subscript from "@tiptap/extension-subscript";
import Superscript from "@tiptap/extension-superscript";
import Dropcursor from "@tiptap/extension-dropcursor";
import Youtube from "@tiptap/extension-youtube";

export default function Editor({
  initialContent,
  onSave,
}: {
  initialContent?: string;
  onSave?: (data: string) => void;
}) {
  const [isPreview, setIsPreview] = useState(false);
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const { showToast } = useToast();
  const [linkModal, setLinkModal] = useState({ isOpen: false, url: "" });

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        history: { depth: 100 },
        dropCursor: false,
      }),
      Mathematics,
      Extension,
      AutoComplete,
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
      Focus.configure({ className: "has-focus", mode: "all" }),
      CharacterCount.configure({ limit: 100000 }),
      Image.configure({ inline: true, allowBase64: true }),
      Link.configure({ openOnClick: false, autolink: true }),
      Underline,
      TextAlign.configure({ types: ["heading", "paragraph"] }),
      Highlight.configure({ multicolor: true }),
      Typography,
      TaskList,
      TaskItem.configure({ nested: true }),
      TextStyle,
      Color,
      Subscript,
      Superscript,
      Dropcursor.configure({ color: "#000000", width: 2 }),
      Youtube.configure({
        inline: false,
        width: 840,
        height: 472.5,
        controls: true,
      }),
      Placeholder.configure({
        placeholder: "Bắt đầu soạn thảo nội dung hoặc gõ \\ để chèn mã LaTeX",
      }),
    ],
    content: initialContent || "",
    editorProps: {
      attributes: {
        class:
          "prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-auto focus:outline-none min-h-[500px] border border-zinc-200 p-8 bg-white font-sans",
      },
    },
    onUpdate: ({ editor }) => {
      onSave?.(editor.getHTML());
    },
    immediatelyRender: false,
  });

  useEffect(() => {
    if (
      editor &&
      initialContent !== undefined &&
      editor.getHTML() !== initialContent
    ) {
      editor.commands.setContent(initialContent);
    }
  }, [initialContent, editor]);

  useEffect(() => {
    if (!editor) return;
    const interval = setInterval(() => {
      onSave?.(editor.getHTML());
    }, 30000);
    return () => clearInterval(interval);
  }, [editor, onSave]);

  const estimatedReadTime =
    Math.ceil((editor?.storage.characterCount.words() || 0) / 200) || 1;

  const handleCompile = async () => {
    if (!editor) return;
    setIsCompiling(true);
    try {
      const json = editor.getJSON();
      let latexContent = "";

      json.content?.forEach((node: any) => {
        if (node.type === "latexBlock") {
          latexContent += node.attrs.text + "\n\n";
        } else if (node.type === "paragraph") {
          const text =
            node.content?.map((c: any) => c.text || "").join("") || "";
          latexContent += text + "\n\n";
        }
      });

      if (!latexContent.trim()) {
        latexContent = editor.getText();
      }

      const blob = await compilePreviewAPI(latexContent, true);
      const url = URL.createObjectURL(blob);
      setPreviewPdfUrl(`${url}#view=FitH&toolbar=0`);
      setIsPreview(true);
    } catch (error) {
      console.error("Lỗi biên dịch bản xem trước:", error);
      showToast("Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau", "error");
    } finally {
      setIsCompiling(false);
    }
  };

  const handleSynonyms = async () => {
    if (!editor) return;
    const { from, to } = editor.state.selection;
    const word = editor.state.doc.textBetween(from, to, " ");
    if (!word || word.length > 50) {
      showToast("Vui lòng chọn một từ để tìm từ đồng nghĩa", "info");
      return;
    }

    try {
      const data = await getSynonymsAPI(
        word,
        editor
          .getText()
          .substring(
            Math.max(0, from - 100),
            Math.min(editor.getText().length, to + 100),
          ),
      );
      if (data.synonyms && data.synonyms.length > 0) {
        showToast(`Gợi ý cho "${word}": ${data.synonyms.join(", ")}`, "info");
      } else {
        showToast("Không tìm thấy từ đồng nghĩa phù hợp", "info");
      }
    } catch (err: any) {
      console.error("Lỗi lấy gợi ý từ đồng nghĩa:", err);
      showToast(err.message || "Không thể lấy gợi ý lúc này", "error");
    }
  };

  if (!editor) {
    return null;
  }

  return (
    <div className="flex flex-col w-full h-[85vh] mx-auto bg-white border border-zinc-200 animate-in fade-in relative font-sans">
      <div className="flex justify-between items-center bg-white border-b border-zinc-200 p-3">
        <div className="flex flex-wrap gap-2 items-center">
          <div className="flex gap-1 border-r pr-2 border-zinc-100">
            <button
              onClick={() => editor.chain().focus().undo().run()}
              disabled={!editor.can().undo()}
              className="p-2 bg-white text-zinc-600 disabled:opacity-30 "
              title="Hoàn tác"
            >
              <Undo className="w-4 h-4" />
            </button>
            <button
              onClick={() => editor.chain().focus().redo().run()}
              disabled={!editor.can().redo()}
              className="p-2 bg-white text-zinc-600 disabled:opacity-30 "
              title="Làm lại"
            >
              <Redo className="w-4 h-4" />
            </button>
          </div>

          <div className="flex gap-1 border-r pr-2 border-zinc-100">
            <button
              onClick={() => editor.chain().focus().toggleBold().run()}
              className={`p-2 ${editor.isActive("bold") ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="In đậm"
            >
              <Bold className="w-4 h-4" />
            </button>
            <button
              onClick={() => editor.chain().focus().toggleItalic().run()}
              className={`p-2 ${editor.isActive("italic") ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="In nghiêng"
            >
              <Italic className="w-4 h-4" />
            </button>
            <button
              onClick={() => editor.chain().focus().toggleUnderline().run()}
              className={`p-2 ${editor.isActive("underline") ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Gạch chân"
            >
              <UnderlineIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => editor.chain().focus().toggleStrike().run()}
              className={`p-2 ${editor.isActive("strike") ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Gạch ngang"
            >
              <Strikethrough className="w-4 h-4" />
            </button>
            <button
              onClick={() => editor.chain().focus().toggleHighlight().run()}
              className={`p-2 ${editor.isActive("highlight") ? "bg-zinc-200 text-black" : "bg-white text-zinc-600 "}`}
              title="Tô sáng"
            >
              <Highlighter className="w-4 h-4" />
            </button>
          </div>

          <div className="flex gap-1 border-r pr-2 border-zinc-100">
            <button
              onClick={() => editor.chain().focus().toggleCode().run()}
              className={`p-2 ${editor.isActive("code") ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Mã nội dòng"
            >
              <CodeIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => editor.chain().focus().toggleCodeBlock().run()}
              className={`p-2 ${editor.isActive("codeBlock") ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Khối mã"
            >
              <SquareTerminal className="w-4 h-4" />
            </button>
            <button
              onClick={() => editor.chain().focus().toggleBlockquote().run()}
              className={`p-2 ${editor.isActive("blockquote") ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Trích dẫn"
            >
              <Quote className="w-4 h-4" />
            </button>
            <button
              onClick={() => editor.chain().focus().setHorizontalRule().run()}
              className="p-2 bg-white text-zinc-600 "
              title="Đường phân cách"
            >
              <Minus className="w-4 h-4" />
            </button>
          </div>

          <div className="flex gap-1 border-r pr-2 border-zinc-100">
            <button
              onClick={() => editor.chain().focus().toggleSubscript().run()}
              className={`p-2 ${editor.isActive("subscript") ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Chỉ số dưới"
            >
              <SubscriptIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => editor.chain().focus().toggleSuperscript().run()}
              className={`p-2 ${editor.isActive("superscript") ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Chỉ số trên"
            >
              <SuperscriptIcon className="w-4 h-4" />
            </button>
          </div>

          <div className="flex gap-1 border-r pr-2 border-zinc-100">
            <button
              onClick={() => editor.chain().focus().setTextAlign("left").run()}
              className={`p-2 ${editor.isActive({ textAlign: "left" }) ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Căn trái"
            >
              <AlignLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() =>
                editor.chain().focus().setTextAlign("center").run()
              }
              className={`p-2 ${editor.isActive({ textAlign: "center" }) ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Căn giữa"
            >
              <AlignCenter className="w-4 h-4" />
            </button>
            <button
              onClick={() => editor.chain().focus().setTextAlign("right").run()}
              className={`p-2 ${editor.isActive({ textAlign: "right" }) ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Căn phải"
            >
              <AlignRight className="w-4 h-4" />
            </button>
            <button
              onClick={() =>
                editor.chain().focus().setTextAlign("justify").run()
              }
              className={`p-2 ${editor.isActive({ textAlign: "justify" }) ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Căn đều"
            >
              <AlignJustify className="w-4 h-4" />
            </button>
          </div>

          <div className="flex gap-1 border-r pr-2 border-zinc-100">
            <button
              onClick={() =>
                editor.chain().focus().toggleHeading({ level: 1 }).run()
              }
              className={`w-8 h-8 shrink-0 font-bold text-xs ${editor.isActive("heading", { level: 1 }) ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
            >
              H1
            </button>
            <button
              onClick={() =>
                editor.chain().focus().toggleHeading({ level: 2 }).run()
              }
              className={`w-8 h-8 shrink-0 font-bold text-xs ${editor.isActive("heading", { level: 2 }) ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
            >
              H2
            </button>
            <button
              onClick={() => editor.chain().focus().toggleTaskList().run()}
              className={`p-2 ${editor.isActive("taskList") ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Danh sách công việc"
            >
              <CheckSquare className="w-4 h-4" />
            </button>
            <button
              onClick={() => {
                const previousUrl = editor.getAttributes("link").href;
                setLinkModal({ isOpen: true, url: previousUrl || "" });
              }}
              className={`p-2 ${editor.isActive("link") ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Chèn liên kết"
            >
              <LinkIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => editor.chain().focus().toggleBulletList().run()}
              className={`p-2 ${editor.isActive("bulletList") ? "bg-black text-white" : "bg-white text-zinc-600 "}`}
              title="Danh sách"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => {
                const headings =
                  editor
                    .getJSON()
                    .content?.filter((n: any) => n.type === "heading") || [];
                let tocHtml =
                  "<div class='toc-container bg-white p-6 border border-zinc-200 mb-8'><h2 class='text-sm font-bold mb-4'>Mục lục</h2><ul class='space-y-2'>";
                headings.forEach((h: any) => {
                  const text =
                    h.content?.map((c: any) => c.text || "").join("") || "";
                  const level = h.attrs.level;
                  tocHtml += `<li class='text-xs ${level === 1 ? "font-bold" : "ml-4"} cursor-pointer'>${text}</li>`;
                });
                tocHtml += "</ul></div>";
                editor.chain().focus().insertContent(tocHtml).run();
              }}
              className="p-2 bg-white text-zinc-600 "
              title="Tạo mục lục"
            >
              <List className="w-4 h-4 text-zinc-400" />
            </button>
          </div>

          <div className="flex gap-2 ml-2">
            <button
              onClick={() =>
                editor.chain().focus().setLatexBlock({ text: "" }).run()
              }
              className="px-4 py-1.5 bg-black text-white flex gap-2 items-center text-xs font-bold active:scale-[0.98]"
            >
              <Code className="w-4 h-4" />
              Mã LaTeX
            </button>
            <button
              onClick={handleSynonyms}
              className="px-4 py-1.5 border border-zinc-200 text-zinc-600 flex gap-2 items-center text-xs font-bold active:scale-[0.98]"
            >
              <Sparkles className="w-4 h-4" />
              Gợi ý từ ngữ
            </button>
            <button
              onClick={async () => {
                const text = editor.getText();
                if (!text || text.length < 50) {
                  showToast(
                    "Vui lòng viết thêm nội dung (tối thiểu 50 từ) để kiểm tra ngữ pháp",
                    "info",
                  );
                  return;
                }
                showToast("Đang phân tích ngữ pháp bằng AI", "info");
                try {
                  const data = await grammarCheckAPI(text);
                  showToast(
                    `Kết quả AI: ${data.message} (Điểm: ${data.score}/100)`,
                    "success",
                  );
                } catch (err: any) {
                  showToast(err.message || "Lỗi kết nối máy chủ AI", "error");
                }
              }}
              className="px-4 py-1.5 bg-zinc-900 text-white flex gap-2 items-center text-xs font-bold active:scale-[0.98]"
            >
              <CheckSquare className="w-4 h-4 text-zinc-400" />
              Kiểm tra ngữ pháp AI
            </button>
          </div>
        </div>
        <div className="flex gap-2">
          {isPreview ? (
            <button
              onClick={() => setIsPreview(false)}
              className="px-4 py-1.5 bg-zinc-100 text-black border border-zinc-200 text-xs font-bold flex items-center gap-2 active:scale-[0.98]"
            >
              <ChevronLeft className="w-4 h-4" />
              Soạn thảo
            </button>
          ) : (
            <button
              onClick={handleCompile}
              disabled={isCompiling}
              className="px-4 py-1.5 bg-black text-white disabled:bg-zinc-100 disabled:text-zinc-400 text-xs font-bold flex items-center gap-2 active:scale-[0.98]"
            >
              {isCompiling ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Đang xử lý
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> Bản xem trước
                </>
              )}
            </button>
          )}
          <button
            onClick={() => {
              onSave?.(editor.getHTML());
              showToast("Đã lưu tài liệu thành công", "success");
            }}
            className="px-4 py-1.5 bg-black text-white text-xs font-bold flex items-center gap-2 active:scale-[0.98]"
          >
            <Save className="w-4 h-4" />
            Lưu
          </button>
        </div>
      </div>

      <div className="flex-1 w-full flex overflow-hidden relative bg-white/10">
        <div
          className={`h-full overflow-y-auto ease-in-out ${
            isPreview ? "w-1/2 border-r border-zinc-200" : "w-full"
          } flex justify-center p-8 scrollbar-thin scrollbar-thumb-zinc-100`}
        >
          <div className="w-full max-w-4xl bg-white border border-zinc-200 min-h-[800px] animate-in fade-in ">
            <EditorContent editor={editor} className="h-full" />
          </div>
        </div>

        {isPreview && previewPdfUrl && (
          <div className="w-1/2 h-full border-l border-zinc-200 overflow-hidden bg-white flex flex-col relative animate-in slide-in-from-right-8 fade-in ">
            <div className="px-4 py-3 bg-black text-white text-xs flex justify-between items-center z-10">
              <div className="flex items-center gap-3">
                <div className="p-1.5 bg-zinc-800">
                  <FileText className="w-4 h-4 text-white" />
                </div>
                <span className="font-bold tracking-tight flex flex-col">
                  Bản in PDF
                  <span className="text-[11px] text-zinc-400 font-medium">
                    Đã hoàn thành biên dịch
                  </span>
                </span>
              </div>
              <div className="flex gap-2">
                <a
                  href={previewPdfUrl}
                  download="doclib-preview.pdf"
                  className="p-1.5 transition-colors text-zinc-300 "
                  title="Tải xuống"
                >
                  <Download className="w-4 h-4" />
                </a>
              </div>
            </div>

            <div className="flex-1 bg-zinc-100 overflow-hidden relative p-4 lg:p-8 flex justify-center items-start">
              <iframe
                src={previewPdfUrl}
                className="w-full max-w-[850px] aspect-[1/1.414] bg-white border border-zinc-200 transition-transform"
                style={{ minHeight: "100%" }}
              />
            </div>
          </div>
        )}
      </div>

      <div className="absolute bottom-4 left-4 bg-white/80 backdrop-blur-sm px-3 py-1.5 border border-zinc-200 text-[11px] font-bold text-zinc-400 pointer-events-none flex gap-4">
        <span>{editor.storage.characterCount.words()} từ</span>
        <span>{editor.storage.characterCount.characters()} ký tự</span>
        <span>Khoảng {estimatedReadTime} phút đọc</span>
      </div>

      <Modal
        isOpen={linkModal.isOpen}
        onClose={() => setLinkModal({ ...linkModal, isOpen: false })}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle>Chèn liên kết</ModalTitle>
        </ModalHeader>
        <ModalContent className="space-y-6">
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest leading-relaxed">
            Nhập địa chỉ URL bạn muốn liên kết đến phần văn bản đang chọn.
          </p>
          <div className="space-y-3">
            <label className="text-[9px] font-bold text-black uppercase tracking-widest">Địa chỉ URL</label>
            <input
              type="text"
              value={linkModal.url}
              onChange={(e) => setLinkModal({ ...linkModal, url: e.target.value })}
              placeholder="https://example.com"
              autoFocus
              className="w-full h-14 bg-white border border-zinc-100 px-6 text-sm font-bold outline-none focus:border-black rounded-sm"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  if (linkModal.url) {
                    editor.chain().focus().setLink({ href: linkModal.url }).run();
                  } else {
                    editor.chain().focus().unsetLink().run();
                  }
                  setLinkModal({ ...linkModal, isOpen: false });
                }
              }}
            />
          </div>
        </ModalContent>
        <ModalFooter className="flex gap-4">
          <button
            onClick={() => setLinkModal({ ...linkModal, isOpen: false })}
            className="flex-1 h-14 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-all"
          >
            Hủy bỏ
          </button>
          <button
            onClick={() => {
              if (linkModal.url) {
                editor.chain().focus().setLink({ href: linkModal.url }).run();
              } else {
                editor.chain().focus().unsetLink().run();
              }
              setLinkModal({ ...linkModal, isOpen: false });
            }}
            className="flex-1 h-14 bg-black text-white text-[10px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-all flex items-center justify-center"
          >
            Xác nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
