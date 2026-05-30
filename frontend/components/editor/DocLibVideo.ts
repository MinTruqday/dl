import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibVideo implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { url: string, caption: string };

  static get toolbox() {
    return {
      title: 'DocLib Video',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>'
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
    
    if (!document.getElementById('doclib-video-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-video-styles';
        style.innerHTML = `
            .doclib-video-wrapper { text-align: center; }
            .doclib-video-player { max-width: 100%; border-radius: 8px; margin-bottom: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); outline: none; }
            .doclib-video-caption { outline: none; text-align: center; color: #64748b; font-size: 0.9em; padding: 4px; }
            .doclib-video-caption:empty::before { content: 'Nhập chú thích video...'; color: #94a3b8; pointer-events: none; }
            .doclib-video-input-container { display: flex; align-items: center; }
            .doclib-video-input { flex-grow: 1; margin-right: 12px; }
        `;
        document.head.appendChild(style);
    }
    
    this.wrapper.classList.add('doclib-video-wrapper');
    this.buildUI();
    return this.wrapper;
  }
  
  private buildUI() {
      if (!this.wrapper) return;
      this.wrapper.innerHTML = '';
      
      if (this.data.url) {
          const video = document.createElement('video');
          video.src = this.data.url;
          video.controls = true;
          video.classList.add('doclib-video-player');
          
          const caption = document.createElement('div');
          caption.contentEditable = 'true';
          caption.innerHTML = this.data.caption;
          caption.classList.add('doclib-video-caption');
          
          caption.addEventListener('input', () => {
              this.data.caption = caption.innerHTML;
          });
          
          this.wrapper.appendChild(video);
          this.wrapper.appendChild(caption);
      } else {
          const container = document.createElement('div');
          container.classList.add('doclib-video-input-container');
          
          const input = document.createElement('input');
          input.classList.add(this.api.styles.input, 'doclib-video-input');
          input.placeholder = 'Nhập link file Video (VD: .mp4, .webm)...';
          
          const btn = document.createElement('button');
          btn.classList.add(this.api.styles.button);
          btn.innerText = 'Chèn';
          
          const insertVideo = () => {
              if (input.value) {
                  this.data.url = input.value;
                  this.buildUI();
              }
          };
          
          btn.addEventListener('click', insertVideo);
          input.addEventListener('keydown', (e) => {
              if (e.key === 'Enter') insertVideo();
          });
          
          container.appendChild(input);
          container.appendChild(btn);
          this.wrapper.appendChild(container);
      }
  }

  save() {
    return this.data;
  }
}
