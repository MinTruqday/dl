import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibVideo implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private config: any;
  private data: { url: string, caption: string };

  static get toolbox() {
    return {
      title: 'DocLib Video',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data, config }: { api: API, data: any }) {
    this.api = api;
    this.config = config || {};
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
            .doclib-video-caption:empty::before { content: 'Enter video caption'; color: #94a3b8; pointer-events: none; }
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
          
          const uploader = document.createElement('label');
          uploader.style.display = 'flex';
          uploader.style.flexDirection = 'column';
          uploader.style.alignItems = 'center';
          uploader.style.justifyContent = 'center';
          uploader.style.border = '2px dashed #cbd5e1';
          uploader.style.borderRadius = '12px';
          uploader.style.padding = '32px';
          uploader.style.background = '#f8fafc';
          uploader.style.cursor = 'pointer';
          uploader.style.color = '#475569';
          uploader.innerHTML = `
              <div style="color: #94a3b8; margin-bottom: 12px;"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg></div>
              <div style="font-weight: 500; font-size: 1.1em; margin-bottom: 4px;">Upload Video</div>
              <div style="font-size: 0.9em; opacity: 0.8;">Click to select file or Right click to paste URL</div>
          `;
          
          const fileInput = document.createElement('input');
          fileInput.type = 'file';
          fileInput.style.display = 'none';
          
          fileInput.addEventListener('change', () => {
              if (fileInput.files && fileInput.files[0]) {
                  const file = fileInput.files[0];
                  const formData = new FormData();
                  formData.append('file', file);
                  const endpoint = this.config?.endpoints?.byFile || '/api/uploadFile';
                  
                  uploader.innerHTML = '<div style="padding: 20px; font-weight: 500;">Uploading...</div>';
                  
                  fetch(endpoint, { method: 'POST', body: formData })
                  .then(res => res.json())
                  .then(res => {
                      if (res.success === 1 && res.file && res.file.url) {
                          this.data.url = res.file.url;
                          
                      } else {
                          this.data.url = res.url || res.data?.url || URL.createObjectURL(file);
                          
                      }
                      this.buildUI();
                  })
                  .catch(err => {
                      console.error("Upload failed", err);
                      this.data.url = URL.createObjectURL(file);
                      
                      this.buildUI();
                  });
              }
          });
          
          uploader.appendChild(fileInput);
          
          uploader.addEventListener('contextmenu', (e) => {
              e.preventDefault();
              const url = prompt('Paste direct URL:');
              if (url) {
                  this.data.url = url;
                  
                  this.buildUI();
              }
          });
          this.wrapper.appendChild(uploader);
 }
  }

  save() {
    return this.data;
  }
}
