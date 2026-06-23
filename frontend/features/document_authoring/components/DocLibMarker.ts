import { API, InlineTool } from "@editorjs/editorjs";
import { IconMarker } from "@codexteam/icons";

export default class DocLibMarker implements InlineTool {
  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;
  private tag = "MARK";
  private class = "cdx-marker";

  static get isInline() {
    return true;
  }
  static get title() {
    return "DocLib Marker";
  }
  static get sanitize() {
    return { mark: { class: true } };
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = IconMarker;
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
      const mark = document.createElement(this.tag);
      mark.classList.add(this.class);
      mark.appendChild(selectedText);
      range.insertNode(mark);
      this.api.selection.expandToTag(mark);
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
