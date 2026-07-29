import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibSpoiler implements InlineTool {
  static readonly feature = {
    id: "DocLibSpoiler",
    title: "DocLib Spoiler",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f846714337da456b"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="14,6 15,20 8,18 5,9 20,13 10,7"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;
  private tag = "SPAN";
  private class = "cdx-spoiler";

  static get isInline() {
    return true;
  }
  static get title() {
    return "Spoiler";
  }

  get state() {
    return this._state;
  }
  set state(s: boolean) {
    this._state = s;
    if (this.button) {
      this.button.classList.toggle(this.api.styles.inlineToolButtonActive, s);
    }
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    (this.button as HTMLButtonElement).type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f846714337da456b"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="14,6 15,20 8,18 5,9 20,13 10,7"/></svg>';

    if (!document.getElementById("doclib-spoiler-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-spoiler-styles";
      style.innerHTML = `
            .cdx-spoiler { background-color: #333; color: transparent; cursor: pointer; border-radius: 3px; transition: color 0.3s, background-color 0.3s; padding: 0 4px; user-select: none; }
            .cdx-spoiler:hover, .cdx-spoiler.revealed { color: inherit; background-color: rgba(0,0,0,0.1); }
        `;
      document.head.appendChild(style);

      document.addEventListener("click", (e: Event) => {
        const target = e.target as HTMLElement;
        if (target && target.classList.contains("cdx-spoiler")) {
          target.classList.toggle("revealed");
        }
      });
    }
    return this.button;
  }

  surround(range: Range) {
    if (this.state) {
      this.unwrap(range);
    } else {
      this.wrap(range);
    }
  }

  wrap(range: Range) {
    const selectedText = range.extractContents();
    const span = document.createElement(this.tag);
    span.classList.add(this.class);
    span.appendChild(selectedText);
    range.insertNode(span);
    this.api.selection.expandToTag(span);
  }

  unwrap(range: Range) {
    const span = this.api.selection.findParentTag(this.tag, this.class);
    if (!span) return;
    const text = range.extractContents();
    span.remove();
    range.insertNode(text);
  }

  checkState() {
    const span = this.api.selection.findParentTag(this.tag, this.class);
    this.state = !!span;
    return this.state;
  }

  static get sanitize() {
    return {
      span: () => {
        return { class: true };
      },
    };
  }
}
