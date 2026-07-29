import { API, InlineTool } from "@editorjs/editorjs";
import { IconStrikethrough } from "@codexteam/icons";

export default class DocLibStrikethrough implements InlineTool {
  static readonly feature = {
    id: "DocLibStrikethrough",
    title: "Strikethrough",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a485b8f0b84c670b"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="15,18 18,6 18,12 5,15 4,8 5,11"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;
  private tag = "S";
  private class = "cdx-strikethrough";

  static get isInline() {
    return true;
  }
  static get title() {
    return "Strikethrough";
  }
  static get sanitize() {
    return { s: { class: true } };
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    (this.button as HTMLButtonElement).type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = IconStrikethrough;

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
      const s = document.createElement(this.tag);
      s.classList.add(this.class);
      s.appendChild(selectedText);
      range.insertNode(s);
      this.api.selection.expandToTag(s);
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
