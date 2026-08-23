"use client";

import Image from "@tiptap/extension-image";
import Mathematics from "@tiptap/extension-mathematics";
import Table from "@tiptap/extension-table";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import TableRow from "@tiptap/extension-table-row";
import StarterKit from "@tiptap/starter-kit";
import { EditorContent, useEditor } from "@tiptap/react";
import type { TiptapDoc } from "../types";
import { AssessmentSection } from "./extensions/Section";
import { PageBreak } from "./extensions/PageBreak";
import { QuestionRef } from "./extensions/QuestionRef";
import { TextAlign } from "./extensions/TextAlign";
import { Underline } from "./extensions/Underline";

export default function TiptapReadOnly({ value, label }: { value: TiptapDoc; label: string }) {
  const editor = useEditor({
    immediatelyRender: false,
    editable: false,
    extensions: [StarterKit, Underline, TextAlign, Mathematics, Image.configure({ allowBase64: false }), Table, TableRow, TableHeader, TableCell, AssessmentSection, QuestionRef, PageBreak],
    content: value,
    editorProps: { attributes: { class: "assessment-tiptap assessment-readonly", "aria-label": label } },
  });
  return <EditorContent editor={editor} />;
}
