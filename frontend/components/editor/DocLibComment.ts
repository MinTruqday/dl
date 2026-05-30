import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibComment implements InlineTool {
  private api: API;
  private button: HTMLElement | null = null;
  private state: boolean = false;
  private tooltip: HTMLElement | null = null;

  static get isInline() { return true; }
  static get sanitize() { return { mark: { 'data-comment': true, class: true, title: true } }; }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement('button');
    this.button.type = 'button';
    this.button.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>';
    this.button.classList.add(this.api.styles.inlineToolButton);
    
    if (!document.getElementById('doclib-comment-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-comment-styles';
        style.innerHTML = `
            mark.doclib-comment-mark { background-color: rgba(250, 204, 21, 0.3); border-bottom: 2px solid #eab308; padding: 0 2px; cursor: help; position: relative; color: inherit; }
            mark.doclib-comment-mark:hover::after { content: attr(title); position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%); background: #1e293b; color: white; padding: 6px 12px; border-radius: 6px; font-size: 13px; white-space: nowrap; z-index: 100; pointer-events: none; margin-bottom: 4px; font-weight: 500; font-family: sans-serif; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
            .doclib-comment-input-wrapper { position: absolute; top: 100%; left: 0; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; display: flex; gap: 8px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); z-index: 100; margin-top: 8px; width: 300px; }
            .doclib-comment-input { flex-grow: 1; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 12px; font-size: 14px; outline: none; transition: border 0.2s; }
            .doclib-comment-input:focus { border-color: #3b82f6; }
            .doclib-comment-btn { background: #3b82f6; color: white; border: none; border-radius: 6px; padding: 6px 12px; font-size: 14px; font-weight: 500; cursor: pointer; transition: background 0.2s; }
            .doclib-comment-btn:hover { background: #2563eb; }
            .doclib-comment-rm { background: #ef4444; color: white; border: none; border-radius: 6px; padding: 6px 12px; font-size: 14px; font-weight: 500; cursor: pointer; transition: background 0.2s; }
            .doclib-comment-rm:hover { background: #dc2626; }
        `;
        document.head.appendChild(style);
    }
    
    return this.button;
  }

  renderActions() {
      this.tooltip = document.createElement('div');
      this.tooltip.classList.add('doclib-comment-input-wrapper');
      this.tooltip.style.display = 'none';
      
      const input = document.createElement('input');
      input.classList.add('doclib-comment-input');
      input.placeholder = 'Enter comment/note';
      
      const btn = document.createElement('button');
      btn.classList.add('doclib-comment-btn');
      btn.innerText = 'Save';
      
      const rmBtn = document.createElement('button');
      rmBtn.classList.add('doclib-comment-rm');
      rmBtn.innerText = 'Delete';
      
      btn.addEventListener('click', () => {
          const mark = this.api.selection.findParentTag('MARK', 'class');
          if (mark) {
              mark.setAttribute('title', input.value);
              this.hideTooltip();
          }
      });
      
      rmBtn.addEventListener('click', () => {
          const mark = this.api.selection.findParentTag('MARK', 'class');
          if (mark) {
              this.unwrap(mark);
              this.hideTooltip();
          }
      });
      
      this.tooltip.appendChild(input);
      this.tooltip.appendChild(btn);
      this.tooltip.appendChild(rmBtn);
      
      return this.tooltip;
  }

  surround(range: Range) {
    if (!range) return;
    const termWrapper = this.api.selection.findParentTag('MARK', 'class');
    
    if (termWrapper) {
        this.toggleTooltip(termWrapper);
    } else {
        const mark = document.createElement('mark');
        mark.classList.add('doclib-comment-mark');
        mark.dataset.comment = 'true';
        mark.setAttribute('title', 'New comment');
        mark.appendChild(range.extractContents());
        range.insertNode(mark);
        this.api.selection.expandToTag(mark);
        this.toggleTooltip(mark);
    }
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

  private toggleTooltip(mark: HTMLElement) {
      if (!this.tooltip) return;
      if (this.tooltip.style.display === 'none') {
          this.tooltip.style.display = 'flex';
          const input = this.tooltip.querySelector('input');
          if (input) {
              input.value = mark.getAttribute('title') || '';
              input.focus();
          }
      } else {
          this.tooltip.style.display = 'none';
      }
  }
  
  private hideTooltip() {
      if (this.tooltip) this.tooltip.style.display = 'none';
  }

  checkState() {
    const termTag = this.api.selection.findParentTag('MARK', 'class');
    this.state = !!termTag;
    if (this.state) {
        this.button?.classList.add(this.api.styles.inlineToolButtonActive);
    } else {
        this.button?.classList.remove(this.api.styles.inlineToolButtonActive);
        this.hideTooltip();
    }
    return this.state;
  }
}
