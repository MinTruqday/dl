import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibEndnote implements InlineTool {
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
    this.button.innerHTML = "EN";
    return this.button;
  }

  surround(range: Range) {
    const wrapper = document.createElement("sup");
    wrapper.classList.add("doclib-endnote-marker");
    const id = Math.random().toString(36).substring(2, 9);
    wrapper.dataset.endnoteId = id;
    wrapper.innerText = "E";
    range.surroundContents(wrapper);
  }

  checkState() {
    return false;
  }
}
