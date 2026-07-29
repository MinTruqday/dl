import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibDoubleStrikethrough implements InlineTool {
  static readonly feature = {
    id: "DocLibDoubleStrikethrough",
    title: "DocLib DoubleStrikethrough",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="73d112c156899a38"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="17,9 5,10 5,5 5,9 4,18 17,19"/></svg>',
    product: "doclib",
  } as const;

  static get isInline() {
    return true;
  }

  static get title() {
    return "DocLib Double Strikethrough";
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
    this.button.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="73d112c156899a38"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="17,9 5,10 5,5 5,9 4,18 17,19"/></svg>`;
    return this.button;
  }

  surround(range: Range) {
    if (!range) return;
    const termWrapper = this.api.selection.findParentTag(this.tag, "DocLibDoubleStrikethrough");
    if (termWrapper) {
      this.unwrap(termWrapper);
    } else {
      this.wrap(range);
    }
  }

  wrap(range: Range) {
    const el = document.createElement(this.tag);
    el.classList.add("DocLibDoubleStrikethrough");
    el.style.textDecorationLine = "line-through";
    el.style.textDecorationStyle = "double";
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
    const termWrapper = this.api.selection.findParentTag(this.tag, "DocLibDoubleStrikethrough");
    if (this.button) {
      this.button.classList.toggle(
        this.api.styles.inlineToolButtonActive,
        !!termWrapper
      );
    }
    return !!termWrapper;
  }
}
