import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibGroupImage implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { urls: string[], layout: 'grid' | 'masonry' };

  static get toolbox() {
    return {
      title: 'DocLib Group Image',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
      urls: Array.isArray(data.urls) ? data.urls : [],
      layout: data.layout || 'grid'
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-group-image-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-group-image-styles';
        style.innerHTML = `
            .doclib-gi-wrapper { margin: 16px 0; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px; background: #f8fafc; }
            .doclib-gi-grid { display: grid; gap: 8px; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
            .doclib-gi-masonry { columns: 2 150px; column-gap: 8px; }
            .doclib-gi-item { position: relative; border-radius: 6px; overflow: hidden; margin-bottom: 8px; break-inside: avoid; }
            .doclib-gi-item img { width: 100%; height: auto; display: block; }
            .doclib-gi-item-overlay { position: absolute; top: 4px; right: 4px; display: flex; gap: 4px; opacity: 0; transition: opacity 0.2s; }
            .doclib-gi-item:hover .doclib-gi-item-overlay { opacity: 1; }
            .doclib-gi-btn { width: 24px; height: 24px; border-radius: 4px; background: rgba(0,0,0,0.6); color: white; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 14px; }
            .doclib-gi-btn:hover { background: rgba(0,0,0,0.8); }
            .doclib-gi-add { margin-top: 8px; width: 100%; padding: 8px; background: #e2e8f0; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; color: #475569; display: flex; align-items: center; justify-content: center; gap: 8px; transition: background 0.2s; }
            .doclib-gi-add:hover { background: #cbd5e1; }
        `;
        document.head.appendChild(style);
    }
    
    this.buildUI();
    return this.wrapper;
  }
  
  renderSettings() {
      const wrapper = document.createElement('div');
      
      const gridBtn = document.createElement('div');
      gridBtn.classList.add(this.api.styles.settingsButton);
      if (this.data.layout === 'grid') gridBtn.classList.add(this.api.styles.settingsButtonActive);
      gridBtn.innerHTML = 'Grid';
      gridBtn.addEventListener('click', () => {
          this.data.layout = 'grid';
          this.buildUI();
      });
      
      const masonryBtn = document.createElement('div');
      masonryBtn.classList.add(this.api.styles.settingsButton);
      if (this.data.layout === 'masonry') masonryBtn.classList.add(this.api.styles.settingsButtonActive);
      masonryBtn.innerHTML = 'Masonry';
      masonryBtn.addEventListener('click', () => {
          this.data.layout = 'masonry';
          this.buildUI();
      });
      
      wrapper.appendChild(gridBtn);
      wrapper.appendChild(masonryBtn);
      
      return wrapper;
  }

  private buildUI() {
      if (!this.wrapper) return;
      this.wrapper.innerHTML = '';
      
      const container = document.createElement('div');
      container.classList.add('doclib-gi-wrapper');
      
      if (this.data.urls.length > 0) {
          const grid = document.createElement('div');
          grid.classList.add(this.data.layout === 'masonry' ? 'doclib-gi-masonry' : 'doclib-gi-grid');
          
          this.data.urls.forEach((url, index) => {
              const item = document.createElement('div');
              item.classList.add('doclib-gi-item');
              
              const img = document.createElement('img');
              img.src = url;
              item.appendChild(img);
              
              if (!this.api.readOnly.toggle) {
                  const overlay = document.createElement('div');
                  overlay.classList.add('doclib-gi-item-overlay');
                  
                  const rmBtn = document.createElement('button');
                  rmBtn.classList.add('doclib-gi-btn');
                  rmBtn.innerHTML = '&times;';
                  rmBtn.addEventListener('click', () => {
                      this.data.urls.splice(index, 1);
                      this.buildUI();
                  });
                  
                  overlay.appendChild(rmBtn);
                  item.appendChild(overlay);
              }
              
              grid.appendChild(item);
          });
          container.appendChild(grid);
      }
      
      if (!this.api.readOnly.toggle) {
          const addBtn = document.createElement('button');
          addBtn.classList.add('doclib-gi-add');
          addBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg> Add Image';
          addBtn.addEventListener('click', () => {
              const url = prompt('Enter image URL:');
              if (url) {
                  this.data.urls.push(url);
                  this.buildUI();
              }
          });
          container.appendChild(addBtn);
      }
      
      if (this.data.urls.length === 0 && this.api.readOnly.toggle) {
          return;
      }
      
      this.wrapper.appendChild(container);
  }

  save() { return this.data; }
}
