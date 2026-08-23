"use client";
import { EditorContent, useEditor } from "@tiptap/react";
import { createAssessmentExtensions } from "./extensions";
export default function TiptapReadOnly({ value, label }) {
    const editor = useEditor({
        immediatelyRender: false,
        editable: false,
        extensions: createAssessmentExtensions(false),
        content: value,
        editorProps: { attributes: { class: "assessment-tiptap assessment-readonly", "aria-label": label } },
    });
    return <EditorContent editor={editor}/>;
}
