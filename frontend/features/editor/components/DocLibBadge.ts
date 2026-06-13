import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibBadge implements InlineTool {
  private api: API;
  private button: HTMLElement | null = null;
  private state: boolean = false;
  private picker: HTMLElement | null = null;

  static get isInline() { return true; }
  static get sanitize() { return { span: { class: true, 'data-badge': true, style: true } }; }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement('button');
    this.button.type = 'button';
    this.button.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>';
    this.button.classList.add(this.api.styles.inlineToolButton);
    
    if (!document.getElementById('doclib-badge-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-badge-styles';
        style.innerHTML = `
            span.doclib-badge-mark { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; font-weight: 600; line-height: 1.2; margin: 0 2px; vertical-align: middle; }
            .doclib-bdg-picker { position: absolute; top: 100%; left: 0; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px; display: flex; flex-wrap: wrap; gap: 6px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); z-index: 100; margin-top: 8px; width: 140px; }
            .doclib-bdg-color { width: 24px; height: 24px; border-radius: 50%; cursor: pointer; border: 1px solid rgba(0,0,0,0.1); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; }
            .doclib-bdg-color:hover { transform: scale(1.1); }
        `;
        document.head.appendChild(style);
    }
    
    return this.button;
  }

  renderActions() {
      this.picker = document.createElement('div');
      this.picker.classList.add('doclib-bdg-picker');
      this.picker.style.display = 'none';
      
      const colors = [
          { bg: '#fee2e2', text: '#ef4444', label: 'R' }, 
          { bg: '#fef3c7', text: '#f59e0b', label: 'Y' }, 
          { bg: '#dcfce7', text: '#10b981', label: 'G' }, 
          { bg: '#dbeafe', text: '#3b82f6', label: 'B' }, 
          { bg: '#f3e8ff', text: '#8b5cf6', label: 'P' }, 
          { bg: '#f1f5f9', text: '#475569', label: 'G' }  
      ];
      
      colors.forEach(c => {
          const btn = document.createElement('div');
          btn.classList.add('doclib-bdg-color');
          btn.style.backgroundColor = c.bg;
          btn.style.color = c.text;
          btn.innerText = c.label;
          btn.addEventListener('click', () => {
              this.applyColor(c.bg, c.text);
              this.hidePicker();
          });
          this.picker!.appendChild(btn);
      });
      
      const clearBtn = document.createElement('div');
      clearBtn.classList.add('doclib-bdg-color');
      clearBtn.style.background = '#fff';
      clearBtn.innerHTML = '&times;';
      clearBtn.addEventListener('click', () => {
          this.removeBadge();
          this.hidePicker();
      });
      this.picker.appendChild(clearBtn);
      
      return this.picker;
  }

  surround(range: Range) {
    if (!range) return;
    const termWrapper = this.api.selection.findParentTag('SPAN', 'doclib-badge-mark');
    
    if (termWrapper) {
        this.togglePicker();
    } else {
        const span = document.createElement('span');
        span.classList.add('doclib-badge-mark');
        span.dataset.badge = 'true';
        span.style.backgroundColor = '#dbeafe'; 
        span.style.color = '#3b82f6';
        span.appendChild(range.extractContents());
        range.insertNode(span);
        this.api.selection.expandToTag(span);
        this.togglePicker();
    }
  }

  private applyColor(bg: string, text: string) {
      const termWrapper = this.api.selection.findParentTag('SPAN', 'doclib-badge-mark');
      if (termWrapper) {
          termWrapper.style.backgroundColor = bg;
          termWrapper.style.color = text;
      }
  }

  private removeBadge() {
      const termWrapper = this.api.selection.findParentTag('SPAN', 'doclib-badge-mark');
      if (termWrapper) {
          this.api.selection.expandToTag(termWrapper);
          const sel = window.getSelection();
          const r = sel?.getRangeAt(0);
          const unwrapped = r?.extractContents();
          if (unwrapped) termWrapper.parentNode?.replaceChild(unwrapped, termWrapper);
      }
  }

  private togglePicker() {
      if (!this.picker) return;
      this.picker.style.display = this.picker.style.display === 'none' ? 'flex' : 'none';
  }
  
  private hidePicker() {
      if (this.picker) this.picker.style.display = 'none';
  }

  checkState() {
    const termTag = this.api.selection.findParentTag('SPAN', 'doclib-badge-mark');
    this.state = !!termTag;
    if (this.state) {
        this.button?.classList.add(this.api.styles.inlineToolButtonActive);
    } else {
        this.button?.classList.remove(this.api.styles.inlineToolButtonActive);
        this.hidePicker();
    }
    return this.state;
  }
}
