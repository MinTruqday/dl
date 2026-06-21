import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibChangelog implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Changelog",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      version: data?.version || "",
      date: data?.date || "",
      items: data?.items && data.items.length > 0 ? data.items : [{ type: "Added", text: "" }],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-clog { font-family: sans-serif; border-left: 2px solid #e2e8f0; margin-left: 12px; padding-left: 24px; position: relative; margin-bottom: 24px; }
      .doclib-clog::before { content: ""; position: absolute; width: 12px; height: 12px; border-radius: 50%; background: #3b82f6; left: -7px; top: 8px; border: 2px solid #fff; }
      .doclib-clog-header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 12px; }
      .doclib-clog-ver { font-size: 20px; font-weight: bold; color: #0f172a; outline: none; }
      .doclib-clog-ver:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-clog-date { font-size: 14px; color: #64748b; outline: none; }
      .doclib-clog-date:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-clog-items { display: flex; flex-direction: column; gap: 8px; }
      .doclib-clog-item { display: flex; align-items: flex-start; gap: 8px; position: relative; }
      .doclib-clog-badge { padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; outline: none; cursor: pointer; color: #fff; }
      .doclib-clog-badge[data-type="Added"] { background: #10b981; }
      .doclib-clog-badge[data-type="Fixed"] { background: #ef4444; }
      .doclib-clog-badge[data-type="Changed"] { background: #f59e0b; }
      .doclib-clog-badge[data-type="Deprecated"] { background: #64748b; }
      .doclib-clog-text { flex: 1; font-size: 14px; color: #334155; line-height: 1.5; outline: none; }
      .doclib-clog-text:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-clog-del { background: none; border: none; color: #ef4444; cursor: pointer; font-weight: bold; font-size: 12px; margin-top: 2px; }
      .doclib-clog-add { margin-top: 12px; padding: 6px 12px; font-size: 12px; background: #e2e8f0; border: none; border-radius: 4px; cursor: pointer; }
    `;
    this.wrapper.appendChild(style);

    const clog = document.createElement("div");
    clog.classList.add("doclib-clog");

    const header = document.createElement("div");
    header.classList.add("doclib-clog-header");

    const verEl = document.createElement("div");
    verEl.classList.add("doclib-clog-ver");
    verEl.innerText = this.data.version;
    verEl.dataset.placeholder = "v1.0.0";
    if (!this.readOnly) {
      verEl.contentEditable = "true";
      verEl.addEventListener("input", () => { this.data.version = verEl.innerText; });
    }

    const dateEl = document.createElement("div");
    dateEl.classList.add("doclib-clog-date");
    dateEl.innerText = this.data.date;
    dateEl.dataset.placeholder = "DocLib Release Date";
    if (!this.readOnly) {
      dateEl.contentEditable = "true";
      dateEl.addEventListener("input", () => { this.data.date = dateEl.innerText; });
    }

    header.appendChild(verEl);
    header.appendChild(dateEl);
    clog.appendChild(header);

    const itemsCont = document.createElement("div");
    itemsCont.classList.add("doclib-clog-items");

    const types = ["Added", "Fixed", "Changed", "Deprecated"];

    const renderItems = () => {
      itemsCont.innerHTML = "";
      this.data.items.forEach((item: any, i: number) => {
        const itemEl = document.createElement("div");
        itemEl.classList.add("doclib-clog-item");

        const badge = document.createElement("div");
        badge.classList.add("doclib-clog-badge");
        badge.dataset.type = item.type;
        badge.innerText = item.type;
        if (!this.readOnly) {
          badge.addEventListener("click", () => {
            const currentIdx = types.indexOf(item.type);
            const nextIdx = (currentIdx + 1) % types.length;
            this.data.items[i].type = types[nextIdx];
            renderItems();
          });
        }

        const textEl = document.createElement("div");
        textEl.classList.add("doclib-clog-text");
        textEl.innerText = item.text;
        textEl.dataset.placeholder = "DocLib Changelog description";
        if (!this.readOnly) {
          textEl.contentEditable = "true";
          textEl.addEventListener("input", () => { this.data.items[i].text = textEl.innerText; });

          const delBtn = document.createElement("button");
          delBtn.classList.add("doclib-clog-del");
          delBtn.innerText = "✕";
          delBtn.addEventListener("click", () => {
            this.data.items.splice(i, 1);
            renderItems();
          });
          
          itemEl.appendChild(badge);
          itemEl.appendChild(textEl);
          itemEl.appendChild(delBtn);
        } else {
          itemEl.appendChild(badge);
          itemEl.appendChild(textEl);
        }

        itemsCont.appendChild(itemEl);
      });
    };

    renderItems();
    clog.appendChild(itemsCont);

    if (!this.readOnly) {
      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-clog-add");
      addBtn.innerText = "+ Add Item";
      addBtn.addEventListener("click", () => {
        this.data.items.push({ type: "Added", text: "" });
        renderItems();
      });
      clog.appendChild(addBtn);
    }

    this.wrapper.appendChild(clog);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
