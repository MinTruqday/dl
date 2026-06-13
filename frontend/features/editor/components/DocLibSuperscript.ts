import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibSuperscript implements InlineTool {
  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;
  private tag = "SUP";
  private class = "cdx-superscript";

  static get isInline() { return true; }
  static get title() { return "DocLib Superscript"; }
  static get sanitize() { return { sup: { class: true } }; }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24"><text x="2" y="18" font-size="16" font-family="sans-serif" font-weight="bold" fill="currentColor">X</text><text x="14" y="10" font-size="11" font-family="sans-serif" font-weight="bold" fill="currentColor">2</text></svg>';
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
      const sup = document.createElement(this.tag);
      sup.classList.add(this.class);
      sup.appendChild(selectedText);
      range.insertNode(sup);
      this.api.selection.expandToTag(sup);
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
