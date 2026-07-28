import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibKeyboard implements InlineTool {
  static readonly feature = {
    id: "DocLibKeyboard",
    title: "DocLib Keyboard",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="154032f3878f4532"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="8,17 20,9 20,11 5,20 10,18 19,16"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private button: HTMLElement | null = null;
  private state: boolean = false;

  static get isInline() {
    return true;
  }
  static get sanitize() {
    return { kbd: { class: true } };
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    (this.button as HTMLButtonElement).type = "button";
    this.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="154032f3878f4532"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="8,17 20,9 20,11 5,20 10,18 19,16"/></svg>';
    this.button.classList.add(this.api.styles.inlineToolButton);

    if (!document.getElementById("doclib-kbd-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-kbd-styles";
      style.innerHTML = `
            kbd.doclib-kbd-mark { display: inline-block; padding: 2px 6px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 0.85em; font-weight: 600; line-height: 1.2; color: #1e293b; background-color: #f8fafc; border: 1px solid #cbd5e1; border-bottom-width: 2px; border-radius: 4px; box-shadow: inset 0 -1px 0 #cbd5e1; margin: 0 2px; }
        `;
      document.head.appendChild(style);
    }

    return this.button;
  }

  surround(range: Range) {
    if (!range) return;
    const termWrapper = this.api.selection.findParentTag(
      "KBD",
      "doclib-kbd-mark",
    );

    if (termWrapper) {
      this.api.selection.expandToTag(termWrapper);
      const sel = window.getSelection();
      const r = sel?.getRangeAt(0);
      const unwrapped = r?.extractContents();
      if (unwrapped)
        termWrapper.parentNode?.replaceChild(unwrapped, termWrapper);
    } else {
      const kbd = document.createElement("kbd");
      kbd.classList.add("doclib-kbd-mark");
      kbd.appendChild(range.extractContents());
      range.insertNode(kbd);
      this.api.selection.expandToTag(kbd);
    }
  }

  checkState() {
    const termTag = this.api.selection.findParentTag("KBD", "doclib-kbd-mark");
    this.state = !!termTag;
    if (this.state) {
      this.button?.classList.add(this.api.styles.inlineToolButtonActive);
    } else {
      this.button?.classList.remove(this.api.styles.inlineToolButtonActive);
    }
    return this.state;
  }
}
