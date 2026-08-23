import { mergeAttributes, Node } from "@tiptap/core";
export const QuestionRef = Node.create({
  name: "questionRef",
  group: "block",
  atom: true,
  selectable: true,
  addAttributes() {
    return {
      questionId: { default: null },
      label: { default: "Câu hỏi" },
    };
  },
  parseHTML() {
    return [{ tag: "div[data-question-ref]" }];
  },
  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(HTMLAttributes, {
        "data-question-ref": HTMLAttributes.questionId,
        class: "assessment-question-ref",
      }),
      HTMLAttributes.label,
    ];
  },
});
