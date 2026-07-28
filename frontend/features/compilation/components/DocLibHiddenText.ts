import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibHiddenText implements InlineTool {
  static readonly feature = {
    id: "DocLibHiddenText",
    title: "DocLib HiddenText",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="8775ac1ebab1e9a9"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="20,19 6,17 20,11 16,20 11,13 12,5"/></svg>',
    product: "doclib",
  } as const;

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
    this.button.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="8775ac1ebab1e9a9"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="20,19 6,17 20,11 16,20 11,13 12,5"/></svg>`;
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
    el.style.opacity = "0.35";
    el.style.textDecoration = "underline dashed";
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
