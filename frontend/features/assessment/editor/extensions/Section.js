import { mergeAttributes, Node } from "@tiptap/core";
export const AssessmentSection = Node.create({
  name: "assessmentSection",
  group: "block",
  content: "block+",
  defining: true,
  addAttributes() {
    return { sectionId: { default: null }, title: { default: "Phần mới" } };
  },
  parseHTML() {
    return [{ tag: "section[data-assessment-section]" }];
  },
  renderHTML({ HTMLAttributes }) {
    return [
      "section",
      mergeAttributes(HTMLAttributes, {
        "data-assessment-section": HTMLAttributes.sectionId,
        class: "assessment-section",
      }),
      ["h2", { contenteditable: "false" }, HTMLAttributes.title],
      ["div", 0],
    ];
  },
});
