import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibColumns implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { cols: number, contents: string[] };

  static get toolbox() {
    return {
      title: 'DocLib Columns',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="12" y1="3" x2="12" y2="21"></line></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
      cols: data.cols || 2,
      contents: Array.isArray(data.contents) && data.contents.length > 0 ? data.contents : ['', '']
    };
    // Ensure array length matches cols
    while (this.data.contents.length < this.data.cols) this.data.contents.push('');
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-columns-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-columns-styles';
        style.innerHTML = `
            .doclib-cols-wrapper { display: flex; gap: 16px; margin: 16px 0; }
            .doclib-cols-col { flex: 1; min-height: 60px; padding: 12px; border: 1px dashed transparent; border-radius: 8px; transition: border 0.2s, background 0.2s; outline: none; line-height: 1.6; }
            .doclib-cols-col:focus-within { border-color: #cbd5e1; background: #f8fafc; }
            .doclib-cols-col:empty::before { content: 'Nhập nội dung cột...'; color: #94a3b8; pointer-events: none; }
        `;
        document.head.appendChild(style);
    }
    
    this.buildUI();
    return this.wrapper;
  }
  
  renderSettings() {
      const wrapper = document.createElement('div');
      
      [2, 3, 4].forEach(cols => {
          const btn = document.createElement('div');
          btn.classList.add(this.api.styles.settingsButton);
          if (this.data.cols === cols) btn.classList.add(this.api.styles.settingsButtonActive);
          btn.innerHTML = `<b>${cols}</b> Cột`;
          btn.addEventListener('click', () => {
              this.data.cols = cols;
              while (this.data.contents.length < cols) this.data.contents.push('');
              this.data.contents.length = cols;
              this.buildUI();
          });
          wrapper.appendChild(btn);
      });
      
      return wrapper;
  }

  private buildUI() {
      if (!this.wrapper) return;
      this.wrapper.innerHTML = '';
      
      const container = document.createElement('div');
      container.classList.add('doclib-cols-wrapper');
      
      for (let i = 0; i < this.data.cols; i++) {
          const col = document.createElement('div');
          col.classList.add('doclib-cols-col');
          col.contentEditable = !this.api.readOnly.toggle ? 'true' : 'false';
          col.innerHTML = this.data.contents[i] || '';
          col.addEventListener('input', () => this.data.contents[i] = col.innerHTML);
          container.appendChild(col);
      }
      
      this.wrapper.appendChild(container);
  }

  save() { return this.data; }
}
