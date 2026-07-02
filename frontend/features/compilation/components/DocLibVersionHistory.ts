import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibVersionHistory implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Version History",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"></path><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({
    api,
    data,
    readOnly,
  }: {
    api: API;
    data: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      versions:
        data?.versions && data.versions.length > 0
          ? data.versions
          : [
              { v: "v1.0", desc: "DocLib Initial release", date: "2024-01-01" },
              { v: "v1.1", desc: "DocLib Minor update", date: "2024-01-15" },
            ],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-vh { font-family: sans-serif; display: flex; flex-direction: column; gap: 0; margin: 16px 0; max-width: 500px; border-left: 2px solid #cbd5e1; padding-left: 16px; margin-left: 8px; }
      .doclib-vh-item { position: relative; padding: 12px 0 12px 16px; display: flex; flex-direction: column; gap: 4px; border-bottom: 1px dashed #e2e8f0; }
      .doclib-vh-item:last-child { border-bottom: none; }
      .doclib-vh-item::before { content: ""; position: absolute; left: -22px; top: 16px; width: 10px; height: 10px; background: #3b82f6; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 0 1px #cbd5e1; }
      .doclib-vh-head { display: flex; align-items: center; justify-content: space-between; }
      .doclib-vh-v { font-weight: bold; color: #1e293b; font-size: 14px; outline: none; }
      .doclib-vh-v:empty:before { content: "v?.?"; color: #94a3b8; }
      .doclib-vh-date { font-size: 12px; color: #64748b; outline: none; }
      .doclib-vh-date:empty:before { content: "YYYY-MM-DD"; color: #cbd5e1; }
      .doclib-vh-desc { font-size: 13px; color: #475569; outline: none; line-height: 1.4; }
      .doclib-vh-desc:empty:before { content: "DocLib Description"; color: #94a3b8; font-style: italic; }
      .doclib-vh-del { position: absolute; top: 12px; right: 0; color: #ef4444; font-size: 10px; border: none; background: transparent; cursor: pointer; display: none; }
      .doclib-vh-item:hover .doclib-vh-del { display: block; }
      .doclib-vh-add { margin-top: 16px; padding: 8px; border: 1px dashed #cbd5e1; border-radius: 4px; text-align: center; color: #3b82f6; cursor: pointer; font-size: 13px; font-weight: bold; background: #f8fafc; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-vh");

    const renderList = () => {
      container.innerHTML = "";
      this.data.versions.forEach((item: any, i: number) => {
        const row = document.createElement("div");
        row.classList.add("doclib-vh-item");

        const head = document.createElement("div");
        head.classList.add("doclib-vh-head");

        const v = document.createElement("div");
        v.classList.add("doclib-vh-v");
        v.innerText = item.v;

        const date = document.createElement("div");
        date.classList.add("doclib-vh-date");
        date.innerText = item.date;

        head.appendChild(v);
        head.appendChild(date);
        row.appendChild(head);

        const desc = document.createElement("div");
        desc.classList.add("doclib-vh-desc");
        desc.innerText = item.desc;
        row.appendChild(desc);

        if (!this.readOnly) {
          v.contentEditable = "true";
          v.addEventListener("input", () => {
            this.data.versions[i].v = v.innerText;
          });

          date.contentEditable = "true";
          date.addEventListener("input", () => {
            this.data.versions[i].date = date.innerText;
          });

          desc.contentEditable = "true";
          desc.addEventListener("input", () => {
            this.data.versions[i].desc = desc.innerText;
          });

          const del = document.createElement("button");
          del.classList.add("doclib-vh-del");
          del.innerText = "✕";
          del.addEventListener("click", () => {
            this.data.versions.splice(i, 1);
            renderList();
          });
          row.appendChild(del);
        }

        container.appendChild(row);
      });

      if (!this.readOnly) {
        const add = document.createElement("button");
        add.classList.add("doclib-vh-add");
        add.innerText = "+ Add Version";
        add.addEventListener("click", () => {
          this.data.versions.push({
            v: "v1.x",
            desc: "DocLib Detail",
            date: "2024-12-31",
          });
          renderList();
        });
        container.appendChild(add);
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
