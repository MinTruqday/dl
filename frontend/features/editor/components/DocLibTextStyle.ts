import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibTextStyle implements InlineTool {
  private api: API;
  private button: HTMLElement | null = null;
  private state: boolean = false;

  static get isInline() { return true; }
  static get sanitize() { return { span: { style: true } }; }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement('button');
    this.button.type = 'button';
    
    this.button.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line></svg>';
    this.button.classList.add(this.api.styles.inlineToolButton);
    return this.button;
  }

  surround(range: Range) {
    if (!range) return;
    
    
    const termWrapper = this.api.selection.findParentTag('SPAN');
    
    if (termWrapper && termWrapper.style.fontSize) {
        if (termWrapper.style.fontSize === '1.2em') {
            termWrapper.style.fontSize = '0.8em';
            termWrapper.style.fontWeight = 'normal';
        } else if (termWrapper.style.fontSize === '0.8em') {
            this.unwrap(termWrapper);
        }
    } else {
        this.wrap(range);
    }
  }

  wrap(range: Range) {
      const span = document.createElement('span');
      span.style.fontSize = '1.2em';
      span.style.fontWeight = '500';
      span.appendChild(range.extractContents());
      range.insertNode(span);
      this.api.selection.expandToTag(span);
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
    const termTag = this.api.selection.findParentTag('SPAN');
    this.state = !!(termTag && termTag.style.fontSize);
    if (this.state) {
        this.button?.classList.add(this.api.styles.inlineToolButtonActive);
    } else {
        this.button?.classList.remove(this.api.styles.inlineToolButtonActive);
    }
    return this.state;
  }
}
