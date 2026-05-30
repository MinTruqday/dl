import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibAudio implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { url: string, caption: string };

  static get toolbox() {
    return {
      title: 'DocLib Audio',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>'
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
    
    if (!document.getElementById('doclib-audio-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-audio-styles';
        style.innerHTML = `
            .doclib-audio-wrapper { text-align: center; }
            .doclib-audio-player { width: 100%; border-radius: 8px; margin-bottom: 8px; outline: none; }
            .doclib-audio-caption { outline: none; text-align: center; color: #64748b; font-size: 0.9em; padding: 4px; }
            .doclib-audio-caption:empty::before { content: 'Nhập chú thích audio...'; color: #94a3b8; pointer-events: none; }
            .doclib-audio-input-container { display: flex; align-items: center; }
            .doclib-audio-input { flex-grow: 1; margin-right: 12px; }
        `;
        document.head.appendChild(style);
    }
    
    this.wrapper.classList.add('doclib-audio-wrapper');
    this.buildUI();
    return this.wrapper;
  }
  
  private buildUI() {
      if (!this.wrapper) return;
      this.wrapper.innerHTML = '';
      
      if (this.data.url) {
          const audio = document.createElement('audio');
          audio.src = this.data.url;
          audio.controls = true;
          audio.classList.add('doclib-audio-player');
          
          const caption = document.createElement('div');
          caption.contentEditable = 'true';
          caption.innerHTML = this.data.caption;
          caption.classList.add('doclib-audio-caption');
          
          caption.addEventListener('input', () => {
              this.data.caption = caption.innerHTML;
          });
          
          this.wrapper.appendChild(audio);
          this.wrapper.appendChild(caption);
      } else {
          const container = document.createElement('div');
          container.classList.add('doclib-audio-input-container');
          
          const input = document.createElement('input');
          input.classList.add(this.api.styles.input, 'doclib-audio-input');
          input.placeholder = 'Nhập link file Audio (VD: .mp3, .wav)...';
          
          const btn = document.createElement('button');
          btn.classList.add(this.api.styles.button);
          btn.innerText = 'Chèn';
          
          const insertAudio = () => {
              if (input.value) {
                  this.data.url = input.value;
                  this.buildUI();
              }
          };
          
          btn.addEventListener('click', insertAudio);
          input.addEventListener('keydown', (e) => {
              if (e.key === 'Enter') insertAudio();
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
