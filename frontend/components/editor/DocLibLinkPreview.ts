import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibLinkPreview implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { link: string, meta: { title: string, site_name: string, description: string, image: { url: string } } };

  static get toolbox() {
    return {
      title: 'DocLib Bookmark',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
      link: data.link || '',
      meta: {
          title: data.meta?.title || '',
          site_name: data.meta?.site_name || '',
          description: data.meta?.description || '',
          image: { url: data.meta?.image?.url || '' }
      }
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById('doclib-link-preview-styles')) {
      const style = document.createElement('style');
      style.id = 'doclib-link-preview-styles';
      style.innerHTML = `
        .doclib-link-card { display: flex; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; background: #fff; text-decoration: none; color: inherit; margin: 12px 0; transition: box-shadow 0.2s; min-height: 120px; }
        .doclib-link-card:hover { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .doclib-link-content { padding: 16px; flex: 1; display: flex; flex-direction: column; justify-content: center; }
        .doclib-link-title { font-weight: 600; font-size: 1.05em; color: #0f172a; margin-bottom: 4px; outline: none; }
        .doclib-link-title:empty::before { content: 'Nhập tiêu đề trang...'; color: #94a3b8; pointer-events: none; }
        .doclib-link-desc { font-size: 0.9em; color: #475569; margin-bottom: 12px; outline: none; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .doclib-link-desc:empty::before { content: 'Nhập mô tả trang...'; color: #94a3b8; pointer-events: none; }
        .doclib-link-site { font-size: 0.8em; color: #64748b; font-weight: 500; outline: none; }
        .doclib-link-site:empty::before { content: 'Tên Website...'; color: #94a3b8; pointer-events: none; }
        .doclib-link-image { width: 160px; background: #f1f5f9; background-size: cover; background-position: center; border-left: 1px solid #e2e8f0; position: relative; }
        .doclib-link-image::after { content: 'Đổi ảnh'; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); color: white; display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.2s; font-size: 12px; cursor: pointer; }
        .doclib-link-image:hover::after { opacity: 1; }
        .doclib-link-input-container { display: flex; gap: 8px; align-items: center; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = '';

    if (this.data.link) {
      const card = document.createElement('a');
      card.classList.add('doclib-link-card');
      card.href = this.data.link;
      card.target = '_blank';
      
      card.addEventListener('click', (e) => {
          if ((e.target as HTMLElement).isContentEditable) e.preventDefault();
      });

      const content = document.createElement('div');
      content.classList.add('doclib-link-content');

      const title = document.createElement('div');
      title.classList.add('doclib-link-title');
      title.contentEditable = 'true';
      title.innerHTML = this.data.meta.title;
      title.addEventListener('input', () => this.data.meta.title = title.innerHTML);

      const desc = document.createElement('div');
      desc.classList.add('doclib-link-desc');
      desc.contentEditable = 'true';
      desc.innerHTML = this.data.meta.description;
      desc.addEventListener('input', () => this.data.meta.description = desc.innerHTML);

      const site = document.createElement('div');
      site.classList.add('doclib-link-site');
      site.contentEditable = 'true';
      site.innerHTML = this.data.meta.site_name || this.data.link;
      site.addEventListener('input', () => this.data.meta.site_name = site.innerHTML);

      content.appendChild(title);
      content.appendChild(desc);
      content.appendChild(site);
      card.appendChild(content);

      const img = document.createElement('div');
      img.classList.add('doclib-link-image');
      if (this.data.meta.image.url) {
          img.style.backgroundImage = `url(${this.data.meta.image.url})`;
      }
      
      img.addEventListener('click', (e) => {
          e.preventDefault();
          const newUrl = prompt('Nhập URL ảnh cover cho thẻ link này:', this.data.meta.image.url);
          if (newUrl !== null) {
              this.data.meta.image.url = newUrl;
              img.style.backgroundImage = `url(${newUrl})`;
          }
      });
      
      card.appendChild(img);
      this.wrapper.appendChild(card);
      
    } else {
      const container = document.createElement('div');
      container.classList.add('doclib-link-input-container');

      const input = document.createElement('input');
      input.classList.add(this.api.styles.input);
      input.style.flexGrow = '1';
      input.placeholder = 'Dán link (URL) để tạo Bookmark...';

      const btn = document.createElement('button');
      btn.classList.add(this.api.styles.button);
      btn.innerText = 'Tạo';

      const insertLink = () => {
        if (input.value) {
          this.data.link = input.value;
          try {
            this.data.meta.site_name = new URL(input.value).hostname;
          } catch(e) {}
          this.buildUI();
        }
      };

      btn.addEventListener('click', insertLink);
      input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') insertLink();
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
