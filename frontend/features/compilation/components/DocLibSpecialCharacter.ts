import { API, InlineTool } from "@editorjs/editorjs";
import { requestEditorInput } from "./editor-dialog";

export default class DocLibSpecialCharacter implements InlineTool {
  static readonly feature = {
    id: "DocLibSpecialCharacter",
    title: "DocLib Special Character",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="253c11e2f2daa59f"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="7,13 4,9 8,18 16,10 19,17 12,13"/></svg>',
    product: "doclib",
  } as const;

  static get isInline() {
    return true;
  }

  private api: API;
  private button: HTMLButtonElement | null = null;

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = "S";
    return this.button;
  }

  surround(range: Range) {
    void requestEditorInput({
      title: "DocLib Special Character",
      label: "Ký tự",
    }).then((char) => {
      if (!char) return;
      const textNode = document.createTextNode(char);
      range.insertNode(textNode);
    });
  }

  checkState(selection: Selection) {
    return false;
  }
}
