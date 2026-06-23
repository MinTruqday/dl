import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibInlineCode implements InlineTool {
  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;
  private tag = "CODE";
  private class = "inline-code";

  static get isInline() {
    return true;
  }
  static get title() {
    return "DocLib Inline Code";
  }
  static get sanitize() {
    return { code: { class: true } };
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 18l-6-6 6-6"/><path d="M14 6l6 6-6 6"/></svg>';
    return this.button;
  }

  surround(range: Range) {
    if (!range) return;

    if (this._state) {
      const parent = this.api.selection.findParentTag(this.tag, this.class);
      if (parent) {
        this.api.selection.expandToTag(parent);
        const text = document.createTextNode(parent.textContent || "");
        parent.parentNode?.replaceChild(text, parent);
      }
    } else {
      const selectedText = range.extractContents();
      const code = document.createElement(this.tag);
      code.classList.add(this.class);
      code.appendChild(selectedText);
      range.insertNode(code);
      this.api.selection.expandToTag(code);
    }
  }

  checkState() {
    const parentNode = this.api.selection.findParentTag(this.tag, this.class);
    this._state = !!parentNode;
    if (this.button) {
      this.button.classList.toggle(
        this.api.styles.inlineToolButtonActive,
        this._state,
      );
    }
    return this._state;
  }
}
