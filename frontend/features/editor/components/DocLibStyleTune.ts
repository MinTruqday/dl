import { API } from "@editorjs/editorjs";

export default class DocLibStyleTune {
  private api: API;
  private data: { bg: string, radius: number, shadow: boolean };
  private wrapper: HTMLElement | null = null;

  static get isTune() { return true; }

  constructor({ api, data }: { api: API, data?: any }) {
    this.api = api;
    this.data = {
      bg: data?.bg || 'transparent',
      radius: data?.radius || 0,
      shadow: data?.shadow || false
    };
  }

  render() {
    const wrapper = document.createElement('div');
    
    if (!document.getElementById('doclib-styletune-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-styletune-styles';
        style.innerHTML = `
            .doclib-st-menu { padding: 8px; display: flex; flex-direction: column; gap: 8px; }
            .doclib-st-colors { display: flex; flex-wrap: wrap; gap: 4px; }
            .doclib-st-color { width: 24px; height: 24px; border-radius: 4px; cursor: pointer; border: 1px solid rgba(0,0,0,0.1); }
            .doclib-st-color:hover { transform: scale(1.1); }
            .doclib-st-color.active { border: 2px solid #3b82f6; }
            .doclib-st-row { display: flex; align-items: center; justify-content: space-between; font-size: 13px; color: #475569; font-weight: 500; }
        `;
        document.head.appendChild(style);
    }
    
    wrapper.classList.add('doclib-st-menu');
    
    const colors = ['transparent', '#f8fafc', '#f1f5f9', '#fef2f2', '#fff7ed', '#fefce8', '#f0fdf4', '#f0f9ff', '#f5f3ff', '#fff1f2'];
    const colorsDiv = document.createElement('div');
    colorsDiv.classList.add('doclib-st-colors');
    colors.forEach(c => {
        const cBtn = document.createElement('div');
        cBtn.classList.add('doclib-st-color');
        cBtn.style.backgroundColor = c;
        if (c === this.data.bg) cBtn.classList.add('active');
        cBtn.addEventListener('click', () => {
            this.data.bg = c;
            Array.from(colorsDiv.children).forEach(child => child.classList.remove('active'));
            cBtn.classList.add('active');
            this.applyStyles();
        });
        if (c === 'transparent') {
            cBtn.innerHTML = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line></svg>';
        }
        colorsDiv.appendChild(cBtn);
    });
    
    const shadowRow = document.createElement('div');
    shadowRow.classList.add('doclib-st-row');
    shadowRow.innerHTML = `<span>Shadow</span>`;
    const shadowToggle = document.createElement('input');
    shadowToggle.type = 'checkbox';
    shadowToggle.checked = this.data.shadow;
    shadowToggle.addEventListener('change', () => {
        this.data.shadow = shadowToggle.checked;
        this.applyStyles();
    });
    shadowRow.appendChild(shadowToggle);
    
    const radiusRow = document.createElement('div');
    radiusRow.classList.add('doclib-st-row');
    radiusRow.innerHTML = `<span>Corner radius (px)</span>`;
    const radiusInput = document.createElement('input');
    radiusInput.type = 'number';
    radiusInput.value = this.data.radius.toString();
    radiusInput.style.width = '50px';
    radiusInput.addEventListener('input', () => {
        this.data.radius = parseInt(radiusInput.value) || 0;
        this.applyStyles();
    });
    radiusRow.appendChild(radiusInput);
    
    wrapper.appendChild(colorsDiv);
    wrapper.appendChild(shadowRow);
    wrapper.appendChild(radiusRow);
    
    return wrapper;
  }

  wrap(blockContent: HTMLElement) {
    this.wrapper = document.createElement('div');
    this.wrapper.appendChild(blockContent);
    this.applyStyles();
    return this.wrapper;
  }
  
  private applyStyles() {
      if (!this.wrapper) return;
      this.wrapper.style.backgroundColor = this.data.bg;
      this.wrapper.style.borderRadius = `${this.data.radius}px`;
      this.wrapper.style.boxShadow = this.data.shadow ? '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)' : 'none';
      if (this.data.bg !== 'transparent' || this.data.shadow) {
          this.wrapper.style.padding = '16px';
          this.wrapper.style.margin = '8px 0';
      } else {
          this.wrapper.style.padding = '0';
          this.wrapper.style.margin = '0';
      }
  }

  save() { return this.data; }
}
