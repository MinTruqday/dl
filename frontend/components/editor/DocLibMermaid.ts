import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibMermaid implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { code: string };

  static get toolbox() {
    return {
      title: 'DocLib Mermaid',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="14" width="18" height="7" rx="2"></rect><rect x="3" y="3" width="18" height="7" rx="2"></rect><line x1="12" y1="10" x2="12" y2="14"></line></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
        code: data.code || 'graph TD;\n    A-->B;\n    A-->C;\n    B-->D;\n    C-->D;'
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-mermaid-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-mermaid-styles';
        style.innerHTML = `
            .doclib-mermaid-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin: 10px 0; }
            .doclib-mermaid-textarea { width: 100%; min-height: 120px; padding: 16px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; border: none; border-bottom: 1px solid #e2e8f0; outline: none; resize: vertical; background: #f8fafc; font-size: 14px; line-height: 1.5; }
            .doclib-mermaid-preview { padding: 24px; text-align: center; background: white; min-height: 120px; display: flex; justify-content: center; align-items: center; overflow-x: auto; }
        `;
        document.head.appendChild(style);
    }
    
    this.wrapper.classList.add('doclib-mermaid-wrapper');
    this.buildUI();
    return this.wrapper;
  }
  
  private buildUI() {
      if (!this.wrapper) return;
      this.wrapper.innerHTML = '';
      
      const textarea = document.createElement('textarea');
      textarea.classList.add('doclib-mermaid-textarea');
      textarea.value = this.data.code;
      textarea.placeholder = 'Nhập mã Mermaid Graph...';
      
      const preview = document.createElement('div');
      preview.classList.add('doclib-mermaid-preview');
      
      const renderPreview = () => {
          preview.innerHTML = '';
          const id = `mermaid-${Math.floor(Math.random() * 1000000)}`;
          const container = document.createElement('div');
          container.id = id;
          preview.appendChild(container);
          
          if (!(window as any).mermaid) {
              const script = document.createElement('script');
              script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
              script.onload = () => {
                  (window as any).mermaid.initialize({ startOnLoad: false, theme: 'default' });
                  renderMermaid(id, textarea.value, container);
              };
              document.head.appendChild(script);
          } else {
              renderMermaid(id, textarea.value, container);
          }
      };
      
      const renderMermaid = async (id: string, code: string, container: HTMLElement) => {
          try {
              const { svg } = await (window as any).mermaid.render(id, code);
              container.innerHTML = svg;
          } catch (e) {
              container.innerHTML = `<span style="color: #ef4444; font-weight: 500;">Lỗi cú pháp Mermaid</span>`;
          }
      };
      
      textarea.addEventListener('input', () => {
          this.data.code = textarea.value;
      });
      
      let timeout: any;
      textarea.addEventListener('input', () => {
          clearTimeout(timeout);
          timeout = setTimeout(renderPreview, 500);
      });
      
      renderPreview();
      
      this.wrapper.appendChild(textarea);
      this.wrapper.appendChild(preview);
  }

  save() {
    return this.data;
  }
}
