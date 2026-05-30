import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibGif implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { url: string, caption: string };

  static get toolbox() {
    return {
      title: 'DocLib GIF',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 4 19 4 21 6 21 18 19 20 5 20 3 18 3 6 5 4"></polygon><line x1="9" y1="9" x2="15" y2="15"></line><line x1="15" y1="9" x2="9" y2="15"></line></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
      url: data.url || '',
      caption: data.caption || ''
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-gif-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-gif-styles';
        style.innerHTML = `
            .doclib-gif-wrapper { text-align: center; margin: 16px 0; }
            .doclib-gif-container { position: relative; border-radius: 12px; overflow: hidden; display: inline-block; max-width: 100%; border: 4px solid #f1f5f9; line-height: 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
            .doclib-gif-img { max-width: 100%; display: block; border-radius: 8px; }
            .doclib-gif-caption { outline: none; text-align: center; color: #64748b; font-size: 0.9em; padding: 12px 4px 4px 4px; font-style: italic; }
            .doclib-gif-caption:empty::before { content: 'Nhập chú thích ảnh GIF...'; color: #cbd5e1; pointer-events: none; }
            .doclib-gif-input-container { display: flex; align-items: center; gap: 8px; padding: 16px; background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 8px; }
        `;
        document.head.appendChild(style);
    }
    
    this.buildUI();
    return this.wrapper;
  }
  
  private buildUI() {
      if (!this.wrapper) return;
      this.wrapper.innerHTML = '';
      
      const outer = document.createElement('div');
      outer.classList.add('doclib-gif-wrapper');
      
      if (this.data.url) {
          const container = document.createElement('div');
          container.classList.add('doclib-gif-container');
          
          const img = document.createElement('img');
          img.classList.add('doclib-gif-img');
          img.src = this.data.url;
          
          const caption = document.createElement('div');
          caption.classList.add('doclib-gif-caption');
          caption.contentEditable = 'true';
          caption.innerHTML = this.data.caption;
          caption.addEventListener('input', () => this.data.caption = caption.innerHTML);
          
          container.appendChild(img);
          
          // Edit overlay
          const overlay = document.createElement('div');
          overlay.style.position = 'absolute';
          overlay.style.top = '8px';
          overlay.style.right = '8px';
          overlay.style.opacity = '0';
          overlay.style.transition = 'opacity 0.2s';
          
          const editBtn = document.createElement('button');
          editBtn.innerText = 'Đổi GIF';
          editBtn.style.padding = '4px 12px';
          editBtn.style.borderRadius = '20px';
          editBtn.style.border = 'none';
          editBtn.style.background = 'rgba(0,0,0,0.7)';
          editBtn.style.color = 'white';
          editBtn.style.cursor = 'pointer';
          editBtn.addEventListener('click', () => {
              this.data.url = '';
              this.buildUI();
          });
          overlay.appendChild(editBtn);
          container.appendChild(overlay);
          
          container.addEventListener('mouseenter', () => overlay.style.opacity = '1');
          container.addEventListener('mouseleave', () => overlay.style.opacity = '0');
          
          outer.appendChild(container);
          outer.appendChild(caption);
      } else {
          const container = document.createElement('div');
          container.classList.add('doclib-gif-input-container');

          const input = document.createElement('input');
          input.classList.add(this.api.styles.input);
          input.style.flexGrow = '1';
          input.placeholder = 'Dán link Giphy (.gif) vào đây...';

          const btn = document.createElement('button');
          btn.classList.add(this.api.styles.button);
          btn.innerText = 'Chèn GIF';

          const insert = () => {
            if (input.value) {
              this.data.url = input.value;
              this.buildUI();
            }
          };

          btn.addEventListener('click', insert);
          input.addEventListener('keydown', (e) => {
              if (e.key === 'Enter') insert();
          });
          
          container.appendChild(input);
          container.appendChild(btn);
          outer.appendChild(container);
      }
      
      this.wrapper.appendChild(outer);
  }

  save() { return this.data; }
}
