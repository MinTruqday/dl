import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibSmartArtList implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib SmartArt List",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="6"></rect><rect x="3" y="11" width="18" height="6"></rect><rect x="3" y="19" width="18" height="6"></rect></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      items: data?.items && data.items.length > 0 ? data.items : [
        { title: "DocLib Main Point 1", desc: "DocLib Detail 1" },
        { title: "DocLib Main Point 2", desc: "DocLib Detail 2" }
      ],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-sal { display: flex; flex-direction: column; gap: 12px; margin: 16px 0; max-width: 600px; font-family: sans-serif; }
      .doclib-sal-item { display: flex; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; position: relative; }
      .doclib-sal-title { width: 150px; background: #6366f1; color: #fff; padding: 16px; font-weight: bold; font-size: 16px; display: flex; align-items: center; justify-content: center; text-align: center; outline: none; }
      .doclib-sal-desc { flex: 1; background: #f8fafc; padding: 16px; font-size: 14px; color: #334155; display: flex; align-items: center; outline: none; }
      .doclib-sal-title:empty:before { content: "DocLib Title"; color: #c7d2fe; font-weight: normal; }
      .doclib-sal-desc:empty:before { content: "DocLib Description text goes here"; color: #94a3b8; font-style: italic; }
      .doclib-sal-del { position: absolute; top: 8px; right: 8px; font-size: 12px; color: #ef4444; background: transparent; border: none; cursor: pointer; display: none; }
      .doclib-sal-item:hover .doclib-sal-del { display: block; }
      .doclib-sal-add { padding: 12px; background: #f1f5f9; border: 1px dashed #cbd5e1; border-radius: 8px; text-align: center; color: #64748b; font-weight: bold; cursor: pointer; font-size: 14px; }
      .doclib-sal-add:hover { background: #e2e8f0; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-sal");

    const renderList = () => {
      container.innerHTML = "";
      this.data.items.forEach((item: any, i: number) => {
        const row = document.createElement("div");
        row.classList.add("doclib-sal-item");

        const tEl = document.createElement("div");
        tEl.classList.add("doclib-sal-title");
        tEl.innerText = item.title;
        
        const dEl = document.createElement("div");
        dEl.classList.add("doclib-sal-desc");
        dEl.innerText = item.desc;

        if (!this.readOnly) {
          tEl.contentEditable = "true";
          tEl.addEventListener("input", () => { this.data.items[i].title = tEl.innerText; });
          
          dEl.contentEditable = "true";
          dEl.addEventListener("input", () => { this.data.items[i].desc = dEl.innerText; });

          const del = document.createElement("button");
          del.classList.add("doclib-sal-del");
          del.innerText = "✕";
          del.addEventListener("click", () => {
            this.data.items.splice(i, 1);
            renderList();
          });
          row.appendChild(del);
        }

        row.appendChild(tEl);
        row.appendChild(dEl);
        container.appendChild(row);
      });

      if (!this.readOnly) {
        const addBtn = document.createElement("button");
        addBtn.classList.add("doclib-sal-add");
        addBtn.innerText = "+ Add List Item";
        addBtn.addEventListener("click", () => {
          this.data.items.push({ title: "DocLib Title", desc: "DocLib Description" });
          renderList();
        });
        container.appendChild(addBtn);
      }
    };

    renderList();
    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
