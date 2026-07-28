import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibSubscript implements InlineTool {
  static readonly feature = {
    id: "DocLibSubscript",
    title: "DocLib Subscript",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="613d363e5dae2712"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="16,14 7,15 12,8 9,5 13,20 13,5"/></svg>',
    origin: "microsoft-word",
  } as const;

  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;
  private tag = "SUB";
  private class = "cdx-subscript";

  static get isInline() {
    return true;
  }
  static get title() {
    return "DocLib Subscript";
  }
  static get sanitize() {
    return { sub: { class: true } };
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    (this.button as HTMLButtonElement).type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="613d363e5dae2712"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="16,14 7,15 12,8 9,5 13,20 13,5"/></svg>';
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
      const sub = document.createElement(this.tag);
      sub.classList.add(this.class);
      sub.appendChild(selectedText);
      range.insertNode(sub);
      this.api.selection.expandToTag(sub);
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
