import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibImageWithLink implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { url: string, link: string, caption: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: 'DocLib Banner',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data, readOnly }: { api: API, data?: any, readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      url: data.url || '',
      link: data.link || '',
      caption: data.caption || ''
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-image-link-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-image-link-styles';
        style.innerHTML = `
            .doclib-il-wrapper { text-align: center; margin: 16px 0; }
            .doclib-il-container { position: relative; display: inline-block; max-width: 100%; border-radius: 8px; overflow: hidden; transition: transform 0.2s, box-shadow 0.2s; line-height: 0; }
            .doclib-il-container:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
            .doclib-il-img { max-width: 100%; display: block; border-radius: inherit; }
            .doclib-il-caption { outline: none; text-align: center; color: #64748b; font-size: 0.9em; padding: 8px 4px 4px 4px; }
            .doclib-il-caption:empty::before { content: 'Enter Banner caption'; color: #94a3b8; pointer-events: none; }
            .doclib-il-inputs { display: flex; flex-direction: column; gap: 8px; padding: 16px; background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 8px; }
            .doclib-il-btn { position: absolute; top: 8px; right: 8px; padding: 4px 12px; font-size: 12px; background: rgba(0,0,0,0.6); color: white; border: none; border-radius: 4px; cursor: pointer; opacity: 0; transition: opacity 0.2s; z-index: 10; }
            .doclib-il-container:hover .doclib-il-btn { opacity: 1; }
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
      outer.classList.add('doclib-il-wrapper');
      
      if (this.data.url) {
          const container = document.createElement('a');
          container.classList.add('doclib-il-container');
          if (this.data.link) {
              container.href = this.data.link;
              container.target = '_blank';
          }
          
          container.addEventListener('click', (e) => {
              if (this.readOnly) return;
              
              e.preventDefault();
          });
          
          const img = document.createElement('img');
          img.classList.add('doclib-il-img');
          img.src = this.data.url;
          
          const caption = document.createElement('div');
          caption.classList.add('doclib-il-caption');
          caption.contentEditable = 'true';
          caption.innerHTML = this.data.caption;
          caption.addEventListener('input', () => this.data.caption = caption.innerHTML);
          
          const editBtn = document.createElement('button');
          editBtn.classList.add('doclib-il-btn');
          editBtn.innerText = 'Edit Link / Change Image';
          editBtn.addEventListener('click', (e) => {
              e.preventDefault();
              e.stopPropagation();
              this.data.url = '';
              this.buildUI();
          });
          
          container.appendChild(img);
          if (!this.readOnly) {
              container.appendChild(editBtn);
          }
          
          outer.appendChild(container);
          outer.appendChild(caption);
      } else {
          const container = document.createElement('div');
          container.classList.add('doclib-il-inputs');

          const imgInput = document.createElement('input');
          imgInput.classList.add(this.api.styles.input);
          imgInput.placeholder = 'Paste Static Image or GIF URL';
          imgInput.value = this.data.url;

          const linkInput = document.createElement('input');
          linkInput.classList.add(this.api.styles.input);
          linkInput.placeholder = 'Paste Destination Link URL (on click)';
          linkInput.value = this.data.link;

          const btn = document.createElement('button');
          btn.classList.add(this.api.styles.button);
          btn.innerText = 'Create Banner';

          const insert = () => {
            if (imgInput.value) {
              this.data.url = imgInput.value;
              this.data.link = linkInput.value;
              this.buildUI();
            }
          };

          btn.addEventListener('click', insert);
          
          container.appendChild(imgInput);
          container.appendChild(linkInput);
          container.appendChild(btn);
          outer.appendChild(container);
      }
      
      this.wrapper.appendChild(outer);
  }

  save() { return this.data; }
}
