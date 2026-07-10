import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibSmallCaps implements InlineTool {
  static get isInline() {
    return true;
  }

  static get title() {
    return "DocLib Small Caps";
  }

  private api: API;
  private button: HTMLButtonElement | null = null;
  private tag = "SPAN";

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5 18V6H13V8H7V11H12V13H7V18H5ZM16 18V10H22V12H18V14H21V16H18V18H16Z" fill="currentColor"/></svg>`;
    return this.button;
  }

  surround(range: Range) {
    if (!range) return;
    const termWrapper = this.api.selection.findParentTag(this.tag, "DocLibSmallCaps");
    if (termWrapper) {
      this.unwrap(termWrapper);
    } else {
      this.wrap(range);
    }
  }

  wrap(range: Range) {
    const el = document.createElement(this.tag);
    el.classList.add("DocLibSmallCaps");
    el.appendChild(range.extractContents());
    range.insertNode(el);
    this.api.selection.expandToTag(el);
  }

  unwrap(termWrapper: HTMLElement) {
    this.api.selection.expandToTag(termWrapper);
    const sel = window.getSelection();
    if (sel && sel.rangeCount > 0) {
      const range = sel.getRangeAt(0);
      const unwrappedContent = range.extractContents();
      termWrapper.parentNode?.removeChild(termWrapper);
      range.insertNode(unwrappedContent);
      sel.removeAllRanges();
      sel.addRange(range);
    }
  }

  checkState() {
    const termWrapper = this.api.selection.findParentTag(this.tag, "DocLibSmallCaps");
    if (this.button) {
      this.button.classList.toggle(
        this.api.styles.inlineToolButtonActive,
        !!termWrapper
      );
    }
    return !!termWrapper;
  }
}
