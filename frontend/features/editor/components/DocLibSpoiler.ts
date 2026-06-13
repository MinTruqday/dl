import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibSpoiler implements InlineTool {
  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;
  private tag = 'SPAN';
  private class = 'cdx-spoiler';

  static get isInline() { return true; }
  static get title() { return "DocLib Spoiler"; }
  
  get state() { return this._state; }
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
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle><line x1="3" y1="3" x2="21" y2="21"></line></svg>';
    
    if (!document.getElementById('doclib-spoiler-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-spoiler-styles';
        style.innerHTML = `
            .cdx-spoiler { background-color: #333; color: transparent; cursor: pointer; border-radius: 3px; transition: color 0.3s, background-color 0.3s; padding: 0 4px; user-select: none; }
            .cdx-spoiler:hover, .cdx-spoiler.revealed { color: inherit; background-color: rgba(0,0,0,0.1); }
        `;
        document.head.appendChild(style);
        
        document.addEventListener('click', (e: Event) => {
            const target = e.target as HTMLElement;
            if (target && target.classList.contains('cdx-spoiler')) {
                target.classList.toggle('revealed');
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
      }
    };
  }
}
