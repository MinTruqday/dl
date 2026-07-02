import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibFootnote implements InlineTool {
  private api: API;
  private button: HTMLElement | null = null;
  private state: boolean = false;

  static get isInline() {
    return true;
  }
  static get sanitize() {
    return { sup: { "data-footnote": true } };
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    (this.button as HTMLButtonElement).type = "button";
    this.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path><polyline points="16 6 12 2 8 6"></polyline><line x1="12" y1="2" x2="12" y2="15"></line></svg>';
    this.button.classList.add(this.api.styles.inlineToolButton);

    if (!document.getElementById("doclib-footnote-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-footnote-styles";
      style.innerHTML = `
            sup[data-footnote] { color: #3b82f6; cursor: pointer; padding: 0 2px; text-decoration: underline dotted; font-weight: 600; }
            sup[data-footnote]:hover::after { content: attr(data-footnote); position: absolute; background: #1e293b; color: #fff; padding: 6px 10px; border-radius: 6px; font-size: 12px; white-space: nowrap; z-index: 50; margin-top: -34px; margin-left: 10px; font-weight: normal; text-decoration: none; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        `;
      document.head.appendChild(style);
    }

    return this.button;
  }

  surround(range: Range) {
    if (!range) return;
    const termWrapper = this.api.selection.findParentTag(
      "SUP",
      "data-footnote",
    );

    if (termWrapper) {
      this.unwrap(termWrapper);
    } else {
      this.wrap(range);
    }
  }

  wrap(range: Range) {
    const footnote = prompt("Enter footnote content:");
    if (!footnote) return;

    const sup = document.createElement("sup");
    sup.dataset.footnote = footnote;
    sup.appendChild(range.extractContents());
    range.insertNode(sup);
    this.api.selection.expandToTag(sup);
  }

  unwrap(termWrapper: HTMLElement) {
    this.api.selection.expandToTag(termWrapper);
    const sel = window.getSelection();
    const range = sel?.getRangeAt(0);
    const unwrappedContent = range?.extractContents();
    if (unwrappedContent) {
      termWrapper.parentNode?.replaceChild(unwrappedContent, termWrapper);
    }
  }

  checkState() {
    const termTag = this.api.selection.findParentTag("SUP", "data-footnote");
    this.state = !!termTag;
    if (this.state) {
      this.button?.classList.add(this.api.styles.inlineToolButtonActive);
    } else {
      this.button?.classList.remove(this.api.styles.inlineToolButtonActive);
    }
    return this.state;
  }
}
