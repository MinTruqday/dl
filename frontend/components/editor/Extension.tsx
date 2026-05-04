import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer } from "@tiptap/react";
import { CodeBlock } from "./CodeBlock";

export interface LatexBlockOptions {
  HTMLAttributes: Record<string, any>;
}

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    latexBlock: {
      setLatexBlock: (attributes?: { text?: string }) => ReturnType;
    };
  }
}

export const Extension = Node.create<LatexBlockOptions>({
  name: "latexBlock",

  group: "block",

  content: "inline*",

  addOptions() {
    return {
      HTMLAttributes: {
        class: "latex-block",
      },
    };
  },

  addAttributes() {
    return {
      text: {
        default: "",
        parseHTML: (element) => element.getAttribute("data-text") || "",
        renderHTML: (attributes) => {
          return {
            "data-text": attributes.text,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: "div.latex-block",
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes),
      0,
    ];
  },

  addNodeView() {
    return ReactNodeViewRenderer(CodeBlock);
  },

  addCommands() {
    return {
      setLatexBlock:
        (attributes) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: attributes,
          });
        },
    };
  },
});
