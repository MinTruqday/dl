import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibSteps implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { steps: { title: string, desc: string }[] };

  static get toolbox() {
    return {
      title: 'DocLib Steps',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
      steps: data.steps && data.steps.length > 0 ? data.steps : [
          { title: 'Bước 1', desc: 'Mô tả chi tiết bước 1' }
      ]
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-steps-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-steps-styles';
        style.innerHTML = `
            .doclib-stp-wrapper { margin: 16px 0; display: flex; flex-direction: column; gap: 16px; counter-reset: step; }
            .doclib-stp-item { display: flex; gap: 16px; position: relative; }
            .doclib-stp-item::before { counter-increment: step; content: counter(step); display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 50%; background: #eff6ff; color: #3b82f6; font-weight: 700; font-size: 14px; flex-shrink: 0; z-index: 2; border: 2px solid #fff; box-shadow: 0 0 0 1px #bfdbfe; }
            .doclib-stp-item:not(:last-child)::after { content: ''; position: absolute; left: 15px; top: 32px; bottom: -16px; width: 2px; background: #e2e8f0; z-index: 1; }
            .doclib-stp-content { flex-grow: 1; padding-top: 4px; padding-bottom: 8px; }
            .doclib-stp-title { font-weight: 700; color: #0f172a; outline: none; margin-bottom: 4px; font-size: 1.1em; }
            .doclib-stp-title:empty::before { content: 'Nhập tiêu đề bước...'; color: #94a3b8; }
            .doclib-stp-desc { color: #475569; outline: none; line-height: 1.5; font-size: 0.95em; }
            .doclib-stp-desc:empty::before { content: 'Nhập mô tả chi tiết...'; color: #94a3b8; }
            .doclib-stp-rm { background: #fee2e2; color: #ef4444; border: none; width: 24px; height: 24px; border-radius: 4px; display: flex; align-items: center; justify-content: center; cursor: pointer; opacity: 0; transition: opacity 0.2s; }
            .doclib-stp-item:hover .doclib-stp-rm { opacity: 1; }
            .doclib-stp-add { margin-left: 48px; padding: 8px 16px; background: transparent; border: 1px dashed #cbd5e1; border-radius: 8px; color: #64748b; font-weight: 500; cursor: pointer; text-align: center; }
            .doclib-stp-add:hover { background: #f8fafc; border-color: #94a3b8; }
        `;
        document.head.appendChild(style);
    }
    
    this.buildUI();
    return this.wrapper;
  }
  
  private buildUI() {
      if (!this.wrapper) return;
      this.wrapper.innerHTML = '';
      
      const container = document.createElement('div');
      container.classList.add('doclib-stp-wrapper');
      
      this.data.steps.forEach((step, index) => {
          const item = document.createElement('div');
          item.classList.add('doclib-stp-item');
          
          const content = document.createElement('div');
          content.classList.add('doclib-stp-content');
          
          const title = document.createElement('div');
          title.classList.add('doclib-stp-title');
          title.contentEditable = !this.api.readOnly.toggle ? 'true' : 'false';
          title.innerHTML = step.title;
          title.addEventListener('input', () => step.title = title.innerHTML);
          
          const desc = document.createElement('div');
          desc.classList.add('doclib-stp-desc');
          desc.contentEditable = !this.api.readOnly.toggle ? 'true' : 'false';
          desc.innerHTML = step.desc;
          desc.addEventListener('input', () => step.desc = desc.innerHTML);
          
          content.appendChild(title);
          content.appendChild(desc);
          item.appendChild(content);
          
          if (!this.api.readOnly.toggle && this.data.steps.length > 1) {
              const rm = document.createElement('button');
              rm.classList.add('doclib-stp-rm');
              rm.innerHTML = '&times;';
              rm.addEventListener('click', () => {
                  this.data.steps.splice(index, 1);
                  this.buildUI();
              });
              item.appendChild(rm);
          }
          
          container.appendChild(item);
      });
      
      if (!this.api.readOnly.toggle) {
          const add = document.createElement('button');
          add.classList.add('doclib-stp-add');
          add.innerText = '+ Thêm Bước';
          add.addEventListener('click', () => {
              this.data.steps.push({ title: '', desc: '' });
              this.buildUI();
          });
          container.appendChild(add);
      }
      
      this.wrapper.appendChild(container);
  }

  save() { return this.data; }
}
