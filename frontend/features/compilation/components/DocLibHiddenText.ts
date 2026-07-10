import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibHiddenText implements InlineTool {
  static get isInline() {
    return true;
  }

  static get title() {
    return "DocLib Hidden Text";
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
    this.button.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 3L21 21M10.5 10.677C10.189 11.03 10 11.493 10 12C10 13.1046 10.8954 14 12 14C12.507 14 12.97 13.811 13.323 13.5M17.657 16.657C16.101 17.765 14.154 18.5 12 18.5C6.47715 18.5 2 12 2 12C2 12 3.636 8.5 6.343 6.343M6.343 6.343C7.899 5.235 9.846 4.5 12 4.5C17.5228 4.5 22 11 22 11C22 11 20.364 14.5 17.657 16.657M6.343 6.343L17.657 16.657" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    return this.button;
  }

  surround(range: Range) {
    if (!range) return;
    const termWrapper = this.api.selection.findParentTag(this.tag, "DocLibHiddenText");
    if (termWrapper) {
      this.unwrap(termWrapper);
    } else {
      this.wrap(range);
    }
  }

  wrap(range: Range) {
    const el = document.createElement(this.tag);
    el.classList.add("DocLibHiddenText");
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
    const termWrapper = this.api.selection.findParentTag(this.tag, "DocLibHiddenText");
    if (this.button) {
      this.button.classList.toggle(
        this.api.styles.inlineToolButtonActive,
        !!termWrapper
      );
    }
    return !!termWrapper;
  }
}
