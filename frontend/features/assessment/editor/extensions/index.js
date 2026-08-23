import CharacterCount from "@tiptap/extension-character-count";
import CodeBlockLowlight from "@tiptap/extension-code-block-lowlight";
import Color from "@tiptap/extension-color";
import Details from "@tiptap/extension-details";
import DetailsContent from "@tiptap/extension-details-content";
import DetailsSummary from "@tiptap/extension-details-summary";
import FontFamily from "@tiptap/extension-font-family";
import Highlight from "@tiptap/extension-highlight";
import Image from "@tiptap/extension-image";
import Link from "@tiptap/extension-link";
import Mathematics from "@tiptap/extension-mathematics";
import Placeholder from "@tiptap/extension-placeholder";
import Subscript from "@tiptap/extension-subscript";
import Superscript from "@tiptap/extension-superscript";
import Table from "@tiptap/extension-table";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import TableRow from "@tiptap/extension-table-row";
import TaskItem from "@tiptap/extension-task-item";
import TaskList from "@tiptap/extension-task-list";
import TextAlign from "@tiptap/extension-text-align";
import TextStyle from "@tiptap/extension-text-style";
import Typography from "@tiptap/extension-typography";
import Underline from "@tiptap/extension-underline";
import Youtube from "@tiptap/extension-youtube";
import StarterKit from "@tiptap/starter-kit";
import { common, createLowlight } from "lowlight";
import { PageBreak } from "./PageBreak";
import { QuestionRef } from "./QuestionRef";
import { AssessmentSection } from "./Section";
const lowlight = createLowlight(common);
export function createAssessmentExtensions(editable) {
    return [
        StarterKit.configure({ codeBlock: false }),
        CodeBlockLowlight.configure({ lowlight }),
        Underline,
        Highlight.configure({ multicolor: true }),
        Subscript,
        Superscript,
        TextStyle,
        Color,
        FontFamily,
        TextAlign.configure({ types: ["heading", "paragraph"] }),
        Link.configure({
            autolink: true,
            linkOnPaste: true,
            openOnClick: !editable,
            HTMLAttributes: { rel: "noopener noreferrer nofollow", target: "_blank" },
        }),
        Placeholder.configure({ placeholder: "Nhập nội dung" }),
        CharacterCount,
        Typography,
        Mathematics,
        Image.configure({ allowBase64: false, HTMLAttributes: { loading: "lazy" } }),
        Youtube.configure({ nocookie: true, controls: true }),
        TaskList,
        TaskItem.configure({ nested: true }),
        Details.configure({ persist: true }),
        DetailsSummary,
        DetailsContent,
        Table.configure({ resizable: editable }),
        TableRow,
        TableHeader,
        TableCell,
        AssessmentSection,
        QuestionRef,
        PageBreak,
    ];
}
