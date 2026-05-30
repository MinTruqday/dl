import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibUnderline implements InlineTool {
  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;
  private tag = "U";
  private class = "cdx-underline";

  static get isInline() { return true; }
  static get title() { return "DocLib Underline"; }
  static get sanitize() { return { u: { class: true } }; }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"></path><line x1="4" y1="21" x2="20" y2="21"></line></svg>';
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
      const u = document.createElement(this.tag);
      u.classList.add(this.class);
      u.appendChild(selectedText);
      range.insertNode(u);
      this.api.selection.expandToTag(u);
    }
  }

  checkState() {
    const parentNode = this.api.selection.findParentTag(this.tag, this.class);
    this._state = !!parentNode;
    if (this.button) {
      this.button.classList.toggle(this.api.styles.inlineToolButtonActive, this._state);
    }
    return this._state;
  }
}
