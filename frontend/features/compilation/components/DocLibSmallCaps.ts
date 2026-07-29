import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibSmallCaps implements InlineTool {
  static readonly feature = {
    id: "DocLibSmallCaps",
    title: "Small Caps",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="bc9bffe0e1c5f856"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="5,6 4,7 8,14 14,5 15,7 13,12"/></svg>',
    product: "doclib",
  } as const;

  static get isInline() {
    return true;
  }

  static get title() {
    return "Small Caps";
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
    this.button.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="bc9bffe0e1c5f856"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="5,6 4,7 8,14 14,5 15,7 13,12"/></svg>`;
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
    el.style.fontVariantCaps = "small-caps";
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
