import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer } from "@tiptap/react";
import LatexBlockNodeView from "./LatexBlockNodeView";

export const Extension = Node.create({
  name: "latexBlock",
  group: "block",
  content: "text*",
  marks: "",
  defining: true,

  addAttributes() {
    return {
      content: {
        default: "",
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="latex-block"]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(HTMLAttributes, { "data-type": "latex-block" }),
      0,
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(LatexBlockNodeView);
  },
});
