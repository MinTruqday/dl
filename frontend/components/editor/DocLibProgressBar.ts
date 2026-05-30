import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibProgressBar implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { label: string, percentage: number, color: string };

  static get toolbox() {
    return {
      title: 'DocLib Progress',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="12" x2="2" y2="12"></line><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
      label: data.label || 'Tiến độ dự án',
      percentage: data.percentage !== undefined ? data.percentage : 50,
      color: data.color || '#3b82f6'
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-progress-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-progress-styles';
        style.innerHTML = `
            .doclib-pg-wrapper { margin: 16px 0; padding: 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; }
            .doclib-pg-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
            .doclib-pg-label { font-weight: 600; color: #0f172a; outline: none; flex-grow: 1; }
            .doclib-pg-percent { font-weight: 700; color: #475569; font-variant-numeric: tabular-nums; }
            .doclib-pg-track { width: 100%; height: 12px; background: #f1f5f9; border-radius: 6px; overflow: hidden; position: relative; }
            .doclib-pg-fill { height: 100%; border-radius: 6px; transition: width 0.3s ease-out; }
            .doclib-pg-slider { width: 100%; margin-top: 12px; accent-color: inherit; }
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
      
      const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
      colors.forEach(c => {
          const btn = document.createElement('div');
          btn.style.width = '24px';
          btn.style.height = '24px';
          btn.style.borderRadius = '4px';
          btn.style.backgroundColor = c;
          btn.style.cursor = 'pointer';
          if (c === this.data.color) btn.style.border = '2px solid #0f172a';
          btn.addEventListener('click', () => {
              this.data.color = c;
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
      container.classList.add('doclib-pg-wrapper');
      
      const header = document.createElement('div');
      header.classList.add('doclib-pg-header');
      
      const label = document.createElement('div');
      label.classList.add('doclib-pg-label');
      label.contentEditable = !this.api.readOnly.toggle ? 'true' : 'false';
      label.innerHTML = this.data.label;
      label.addEventListener('input', () => this.data.label = label.innerHTML);
      
      const pct = document.createElement('div');
      pct.classList.add('doclib-pg-percent');
      pct.innerText = `${this.data.percentage}%`;
      
      header.appendChild(label);
      header.appendChild(pct);
      
      const track = document.createElement('div');
      track.classList.add('doclib-pg-track');
      const fill = document.createElement('div');
      fill.classList.add('doclib-pg-fill');
      fill.style.width = `${this.data.percentage}%`;
      fill.style.backgroundColor = this.data.color;
      track.appendChild(fill);
      
      container.appendChild(header);
      container.appendChild(track);
      
      if (!this.api.readOnly.toggle) {
          const slider = document.createElement('input');
          slider.type = 'range';
          slider.min = '0';
          slider.max = '100';
          slider.value = this.data.percentage.toString();
          slider.classList.add('doclib-pg-slider');
          slider.style.accentColor = this.data.color;
          slider.addEventListener('input', () => {
              this.data.percentage = parseInt(slider.value);
              pct.innerText = `${this.data.percentage}%`;
              fill.style.width = `${this.data.percentage}%`;
          });
          container.appendChild(slider);
      }
      
      this.wrapper.appendChild(container);
  }

  save() { return this.data; }
}
