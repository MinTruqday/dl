import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibPersonality implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { name: string, description: string, link: string, photo: string };

  static get toolbox() {
    return {
      title: 'DocLib Personality',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
      name: data.name || '',
      description: data.description || '',
      link: data.link || '',
      photo: data.photo || ''
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById('doclib-personality-styles')) {
      const style = document.createElement('style');
      style.id = 'doclib-personality-styles';
      style.innerHTML = `
        .doclib-personality { display: flex; align-items: center; padding: 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; margin: 12px 0; }
        .doclib-personality-avatar { width: 64px; height: 64px; border-radius: 50%; object-fit: cover; background: #f1f5f9; margin-right: 16px; border: 1px solid #e2e8f0; cursor: pointer; }
        .doclib-personality-info { flex-grow: 1; display: flex; flex-direction: column; gap: 4px; }
        .doclib-personality-name { font-weight: 700; font-size: 1.1em; outline: none; }
        .doclib-personality-name:empty::before { content: 'Tên nhân vật...'; color: #94a3b8; pointer-events: none; }
        .doclib-personality-desc { font-size: 0.9em; color: #64748b; outline: none; }
        .doclib-personality-desc:empty::before { content: 'Mô tả ngắn gọn...'; color: #94a3b8; pointer-events: none; }
        .doclib-personality-link { font-size: 0.85em; color: #3b82f6; outline: none; }
        .doclib-personality-link:empty::before { content: 'Liên kết (tùy chọn)...'; color: #94a3b8; pointer-events: none; }
      `;
      document.head.appendChild(style);
    }

    this.wrapper.classList.add('doclib-personality');
    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = '';

    const img = document.createElement('img');
    img.classList.add('doclib-personality-avatar');
    img.src = this.data.photo || 'https://ui-avatars.com/api/?name=User&background=f1f5f9&color=94a3b8';
    img.addEventListener('click', () => {
        const newUrl = prompt('Nhập URL ảnh đại diện:', this.data.photo);
        if (newUrl !== null) {
            this.data.photo = newUrl;
            img.src = newUrl || 'https://ui-avatars.com/api/?name=User&background=f1f5f9&color=94a3b8';
        }
    });

    const info = document.createElement('div');
    info.classList.add('doclib-personality-info');

    const name = document.createElement('div');
    name.classList.add('doclib-personality-name');
    name.contentEditable = 'true';
    name.innerHTML = this.data.name;
    name.addEventListener('input', () => this.data.name = name.innerHTML);

    const desc = document.createElement('div');
    desc.classList.add('doclib-personality-desc');
    desc.contentEditable = 'true';
    desc.innerHTML = this.data.description;
    desc.addEventListener('input', () => this.data.description = desc.innerHTML);

    const link = document.createElement('div');
    link.classList.add('doclib-personality-link');
    link.contentEditable = 'true';
    link.innerHTML = this.data.link;
    link.addEventListener('input', () => this.data.link = link.innerHTML);

    info.appendChild(name);
    info.appendChild(desc);
    info.appendChild(link);

    this.wrapper.appendChild(img);
    this.wrapper.appendChild(info);
  }

  save() {
    return this.data;
  }
}
