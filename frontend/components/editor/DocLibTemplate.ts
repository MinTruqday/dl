import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibTemplate implements InlineTool {
  private api: API;
  private button: HTMLElement | null = null;
  private state: boolean = false;
  private picker: HTMLElement | null = null;

  static get isInline() { return true; }
  static get sanitize() { return { span: { class: true, 'data-template': true } }; }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement('button');
    this.button.type = 'button';
    this.button.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>';
    this.button.classList.add(this.api.styles.inlineToolButton);
    
    if (!document.getElementById('doclib-template-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-template-styles';
        style.innerHTML = `
            span.doclib-template-var { background: #f1f5f9; color: #3b82f6; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; font-weight: 500; display: inline-block; border: 1px solid #cbd5e1; }
            .doclib-tpl-picker { position: absolute; top: 100%; left: 0; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px; display: flex; flex-direction: column; gap: 4px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); z-index: 100; margin-top: 8px; width: 200px; }
            .doclib-tpl-btn { background: transparent; border: none; text-align: left; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 13px; color: #475569; transition: background 0.2s, color 0.2s; }
            .doclib-tpl-btn:hover { background: #f1f5f9; color: #0f172a; }
        `;
        document.head.appendChild(style);
    }
    
    return this.button;
  }

  renderActions() {
      this.picker = document.createElement('div');
      this.picker.classList.add('doclib-tpl-picker');
      this.picker.style.display = 'none';
      
      const templates = [
          { name: 'Tên Khách Hàng', value: '{{customer_name}}' },
          { name: 'Tên Công Ty', value: '{{company_name}}' },
          { name: 'Ngày Hiện Tại', value: '{{current_date}}' },
          { name: 'Tổng Tiền', value: '{{total_amount}}' }
      ];
      
      templates.forEach(t => {
          const btn = document.createElement('button');
          btn.classList.add('doclib-tpl-btn');
          btn.innerText = t.name;
          btn.addEventListener('click', () => {
              this.insertTemplate(t.value);
              this.hidePicker();
          });
          this.picker!.appendChild(btn);
      });
      
      return this.picker;
  }

  surround(range: Range) {
    if (!range) return;
    this.togglePicker();
  }
  
  private insertTemplate(val: string) {
      const sel = window.getSelection();
      if (!sel || !sel.rangeCount) return;
      
      const range = sel.getRangeAt(0);
      const span = document.createElement('span');
      span.classList.add('doclib-template-var');
      span.dataset.template = val;
      span.innerText = val;
      
      range.deleteContents();
      range.insertNode(span);
      
      // Move caret after
      range.setStartAfter(span);
      range.setEndAfter(span);
      sel.removeAllRanges();
      sel.addRange(range);
  }

  private togglePicker() {
      if (!this.picker) return;
      if (this.picker.style.display === 'none') {
          this.picker.style.display = 'flex';
      } else {
          this.picker.style.display = 'none';
      }
  }
  
  private hidePicker() {
      if (this.picker) this.picker.style.display = 'none';
  }

  checkState() {
    return false;
  }
}
