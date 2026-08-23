import { Mark, mergeAttributes } from "@tiptap/core";

export const Underline = Mark.create({
  name: "underline",
  parseHTML() {
    return [{ tag: "u" }, { style: "text-decoration", consuming: false, getAttrs: (style: string) => style.includes("underline") ? {} : false }];
  },
  renderHTML({ HTMLAttributes }) {
    return ["u", mergeAttributes(HTMLAttributes), 0];
  },
  addKeyboardShortcuts() {
    return { "Mod-u": () => this.editor.commands.toggleMark(this.name) };
  },
});
