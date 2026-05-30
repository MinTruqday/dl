import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibFile implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { file: { url: string, name: string, size: number, extension: string }, title: string };

  static get toolbox() {
    return {
      title: 'DocLib File Attachment',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
      file: {
          url: data?.file?.url || '',
          name: data?.file?.name || '',
          size: data?.file?.size || 0,
          extension: data?.file?.extension || ''
      },
      title: data?.title || ''
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById('doclib-file-styles')) {
      const style = document.createElement('style');
      style.id = 'doclib-file-styles';
      style.innerHTML = `
        .doclib-file-card { display: flex; align-items: center; padding: 12px 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc; margin: 12px 0; text-decoration: none; color: inherit; }
        .doclib-file-icon { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: #e0f2fe; color: #0284c7; border-radius: 8px; margin-right: 16px; font-weight: bold; font-size: 12px; text-transform: uppercase; }
        .doclib-file-info { flex-grow: 1; display: flex; flex-direction: column; gap: 4px; }
        .doclib-file-title { font-weight: 600; font-size: 1em; outline: none; }
        .doclib-file-title:empty::before { content: 'Nhập tên tệp đính kèm...'; color: #94a3b8; pointer-events: none; }
        .doclib-file-meta { font-size: 0.85em; color: #64748b; }
        .doclib-file-download { color: #0284c7; cursor: pointer; padding: 8px; }
        .doclib-file-input-container { display: flex; align-items: center; gap: 8px; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = '';

    if (this.data.file.url) {
      const card = document.createElement('div');
      card.classList.add('doclib-file-card');

      const icon = document.createElement('div');
      icon.classList.add('doclib-file-icon');
      icon.innerText = this.data.file.extension || 'FILE';

      const info = document.createElement('div');
      info.classList.add('doclib-file-info');

      const title = document.createElement('div');
      title.classList.add('doclib-file-title');
      title.contentEditable = 'true';
      title.innerHTML = this.data.title || this.data.file.name;
      title.addEventListener('input', () => this.data.title = title.innerHTML);

      const meta = document.createElement('div');
      meta.classList.add('doclib-file-meta');
      const sizeMB = this.data.file.size ? (this.data.file.size / 1024 / 1024).toFixed(2) + ' MB' : '';
      meta.innerText = `${this.data.file.name} ${sizeMB ? '• ' + sizeMB : ''}`;

      info.appendChild(title);
      info.appendChild(meta);

      const download = document.createElement('a');
      download.classList.add('doclib-file-download');
      download.href = this.data.file.url;
      download.target = '_blank';
      download.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>';

      card.appendChild(icon);
      card.appendChild(info);
      card.appendChild(download);
      this.wrapper.appendChild(card);
    } else {
      const container = document.createElement('div');
      container.classList.add('doclib-file-input-container');

      const input = document.createElement('input');
      input.classList.add(this.api.styles.input);
      input.style.flexGrow = '1';
      input.placeholder = 'Nhập URL file đính kèm...';

      const extInput = document.createElement('input');
      extInput.classList.add(this.api.styles.input);
      extInput.style.width = '80px';
      extInput.placeholder = 'ZIP, PDF';

      const btn = document.createElement('button');
      btn.classList.add(this.api.styles.button);
      btn.innerText = 'Đính kèm';

      const insertFile = () => {
        if (input.value) {
          const url = input.value;
          const name = url.split('/').pop() || 'file';
          const ext = extInput.value || name.split('.').pop() || 'FILE';
          
          this.data.file = { url, name, size: 0, extension: ext.substring(0, 4).toUpperCase() };
          this.data.title = name;
          this.buildUI();
        }
      };

      btn.addEventListener('click', insertFile);
      
      container.appendChild(input);
      container.appendChild(extInput);
      container.appendChild(btn);
      this.wrapper.appendChild(container);
    }
  }

  save() {
    return this.data;
  }
}
