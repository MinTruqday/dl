import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibCallout implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { icon: string, text: string, bgColor: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: 'DocLib Callout',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data, readOnly }: { api: API, data?: any, readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      icon: data.icon || '',
      text: data.text || '',
      bgColor: data.bgColor || '#f8fafc'
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-callout-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-callout-styles';
        style.innerHTML = `
            .doclib-co-wrapper { display: flex; gap: 12px; padding: 16px 20px; border-radius: 8px; margin: 12px 0; border: 1px solid rgba(0,0,0,0.05); align-items: flex-start; }
            .doclib-co-icon { font-size: 24px; cursor: pointer; flex-shrink: 0; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 4px; transition: background 0.2s; }
            .doclib-co-icon:hover { background: rgba(0,0,0,0.05); }
            .doclib-co-text { flex-grow: 1; outline: none; line-height: 1.6; color: #1e293b; min-height: 24px; padding-top: 4px; }
            .doclib-co-text:empty::before { content: 'Enter highlight text'; color: #94a3b8; }
        `;
        document.head.appendChild(style);
    }
    
    this.buildUI();
    return this.wrapper;
  }
  
  renderSettings() {
      const wrapper = document.createElement('div');
      wrapper.style.display = 'flex';
      wrapper.style.gap = '4px';
      wrapper.style.padding = '4px';
      wrapper.style.flexWrap = 'wrap';
      
      const colors = ['#f8fafc', '#fef2f2', '#fff7ed', '#fefce8', '#f0fdf4', '#f0f9ff', '#f5f3ff', '#fff1f2'];
      colors.forEach(c => {
          const btn = document.createElement('div');
          btn.style.width = '24px';
          btn.style.height = '24px';
          btn.style.borderRadius = '4px';
          btn.style.backgroundColor = c;
          btn.style.cursor = 'pointer';
          btn.style.border = '1px solid rgba(0,0,0,0.1)';
          if (c === this.data.bgColor) btn.style.border = '2px solid #3b82f6';
          btn.addEventListener('click', () => {
              this.data.bgColor = c;
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
      container.classList.add('doclib-co-wrapper');
      container.style.backgroundColor = this.data.bgColor;
      
      const iconBtn = document.createElement('div');
      iconBtn.classList.add('doclib-co-icon');
      iconBtn.innerText = this.data.icon;
      if (!this.readOnly) {
          iconBtn.addEventListener('click', () => {
              const newIcon = prompt('Enter new icon:', this.data.icon);
              if (newIcon) {
                  this.data.icon = newIcon.substring(0, 2); 
                  this.buildUI();
              }
          });
      }
      
      const text = document.createElement('div');
      text.classList.add('doclib-co-text');
      text.contentEditable = !this.readOnly ? 'true' : 'false';
      text.innerHTML = this.data.text;
      text.addEventListener('input', () => this.data.text = text.innerHTML);
      
      container.appendChild(iconBtn);
      container.appendChild(text);
      this.wrapper.appendChild(container);
  }

  save() { return this.data; }
}
