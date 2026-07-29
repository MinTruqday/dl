import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibUnderline implements InlineTool {
  static readonly feature = {
    id: "DocLibUnderline",
    title: "Underline",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="15e98a919845814a"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="8,16 6,13 20,5 14,10 8,8 7,20"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;
  private tag = "U";
  private class = "cdx-underline";

  static get isInline() {
    return true;
  }
  static get title() {
    return "Underline";
  }
  static get sanitize() {
    return { u: { class: true } };
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    (this.button as HTMLButtonElement).type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="15e98a919845814a"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="8,16 6,13 20,5 14,10 8,8 7,20"/></svg>';
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
      this.button.classList.toggle(
        this.api.styles.inlineToolButtonActive,
        this._state,
      );
    }
    return this._state;
  }
}
