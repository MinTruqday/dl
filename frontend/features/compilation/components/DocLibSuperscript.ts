import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibSuperscript implements InlineTool {
  static readonly feature = {
    id: "DocLibSuperscript",
    title: "DocLib Superscript",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="99e7a14bc4c34da5"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="4,14 12,11 13,12 13,16 8,17 19,11"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;
  private tag = "SUP";
  private class = "cdx-superscript";

  static get isInline() {
    return true;
  }
  static get title() {
    return "DocLib Superscript";
  }
  static get sanitize() {
    return { sup: { class: true } };
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    (this.button as HTMLButtonElement).type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="99e7a14bc4c34da5"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="4,14 12,11 13,12 13,16 8,17 19,11"/></svg>';
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
      this.button.classList.toggle(
        this.api.styles.inlineToolButtonActive,
        this._state,
      );
    }
    return this._state;
  }
}
