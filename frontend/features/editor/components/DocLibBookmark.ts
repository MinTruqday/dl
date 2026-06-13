import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibBookmark implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { url: string, title: string, desc: string, img: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: 'DocLib Bookmark',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data, readOnly }: { api: API, data?: any, readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      url: data.url || '',
      title: data.title || '',
      desc: data.desc || '',
      img: data.img || ''
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-bookmark-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-bookmark-styles';
        style.innerHTML = `
            .doclib-bm-wrapper { display: flex; border: 1px solid #e2e8f0; border-radius: 8px; margin: 16px 0; overflow: hidden; background: #fff; cursor: pointer; text-decoration: none; color: inherit; transition: background 0.2s; height: 120px; }
            .doclib-bm-wrapper:hover { background: #f8fafc; }
            .doclib-bm-content { flex: 1; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; }
            .doclib-bm-title { font-weight: 600; font-size: 15px; color: #0f172a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; outline: none; }
            .doclib-bm-title:empty::before { content: 'Web page title'; color: #94a3b8; }
            .doclib-bm-desc { font-size: 13px; color: #475569; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; outline: none; line-height: 1.4; }
            .doclib-bm-desc:empty::before { content: 'Short description'; color: #94a3b8; }
            .doclib-bm-url { font-size: 12px; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 8px; }
            .doclib-bm-img-box { width: 30%; min-width: 120px; border-left: 1px solid #e2e8f0; position: relative; background: #f1f5f9; }
            .doclib-bm-img { width: 100%; height: 100%; object-fit: cover; }
            .doclib-bm-input-wrapper { display: flex; gap: 8px; padding: 16px; border: 1px dashed #cbd5e1; border-radius: 8px; background: #f8fafc; }
        `;
        document.head.appendChild(style);
    }
    
    this.buildUI();
    return this.wrapper;
  }
  
  private buildUI() {
      if (!this.wrapper) return;
      this.wrapper.innerHTML = '';
      
      if (this.data.url) {
          const container = document.createElement('a');
          container.classList.add('doclib-bm-wrapper');
          container.href = this.data.url;
          container.target = '_blank';
          container.addEventListener('click', (e) => {
              if (!this.readOnly) e.preventDefault(); 
          });
          
          const content = document.createElement('div');
          content.classList.add('doclib-bm-content');
          
          const title = document.createElement('div');
          title.classList.add('doclib-bm-title');
          title.contentEditable = !this.readOnly ? 'true' : 'false';
          title.innerHTML = this.data.title;
          title.addEventListener('input', () => this.data.title = title.innerHTML);
          
          const desc = document.createElement('div');
          desc.classList.add('doclib-bm-desc');
          desc.contentEditable = !this.readOnly ? 'true' : 'false';
          desc.innerHTML = this.data.desc;
          desc.addEventListener('input', () => this.data.desc = desc.innerHTML);
          
          const url = document.createElement('div');
          url.classList.add('doclib-bm-url');
          url.innerText = this.data.url;
          
          content.appendChild(title);
          content.appendChild(desc);
          content.appendChild(url);
          container.appendChild(content);
          
          const imgBox = document.createElement('div');
          imgBox.classList.add('doclib-bm-img-box');
          const img = document.createElement('img');
          img.classList.add('doclib-bm-img');
          img.src = this.data.img || 'https://via.placeholder.com/300x200?text=No+Image';
          imgBox.appendChild(img);
          
          if (!this.readOnly) {
              const editImg = document.createElement('button');
              editImg.innerHTML = 'Change image';
              editImg.style.position = 'absolute';
              editImg.style.bottom = '4px';
              editImg.style.right = '4px';
              editImg.style.fontSize = '10px';
              editImg.addEventListener('click', (e) => {
                  e.stopPropagation();
                  const newImg = prompt('Preview Image URL:', this.data.img);
                  if (newImg) {
                      this.data.img = newImg;
                      this.buildUI();
                  }
              });
              imgBox.appendChild(editImg);
          }
          
          container.appendChild(imgBox);
          this.wrapper.appendChild(container);
      } else {
          const inputWrapper = document.createElement('div');
          inputWrapper.classList.add('doclib-bm-input-wrapper');
          
          const input = document.createElement('input');
          input.classList.add(this.api.styles.input);
          input.placeholder = 'Paste Web Bookmark Link';
          
          const btn = document.createElement('button');
          btn.classList.add(this.api.styles.button);
          btn.innerText = 'Create';
          btn.addEventListener('click', () => {
              if (input.value) {
                  this.data.url = input.value;
                  this.data.title = 'Page title';
                  this.data.desc = 'Description trang web';
                  this.buildUI();
              }
          });
          
          inputWrapper.appendChild(input);
          inputWrapper.appendChild(btn);
          this.wrapper.appendChild(inputWrapper);
      }
  }

  save() { return this.data; }
}
