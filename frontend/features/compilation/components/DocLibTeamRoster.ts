import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibTeamRoster implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Team Roster",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>',
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
      title: data?.title || "",
      members:
        data?.members && data.members.length > 0
          ? data.members
          : [
              { name: "", role: "", avatar: "" },
              { name: "", role: "", avatar: "" },
              { name: "", role: "", avatar: "" },
            ],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-tr { font-family: sans-serif; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; margin: 16px 0; }
      .doclib-tr-title { font-size: 24px; font-weight: 800; text-align: center; color: #0f172a; margin-bottom: 24px; outline: none; }
      .doclib-tr-title:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-tr-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 24px; }
      .doclib-tr-member { display: flex; flex-direction: column; align-items: center; position: relative; }
      .doclib-tr-avatar-wrap { width: 100px; height: 100px; border-radius: 50%; background: #e2e8f0; margin-bottom: 12px; overflow: hidden; position: relative; }
      .doclib-tr-avatar { width: 100%; height: 100%; object-fit: cover; }
      .doclib-tr-input { position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; height: 100%; }
      .doclib-tr-name { font-size: 16px; font-weight: bold; color: #1e293b; outline: none; text-align: center; }
      .doclib-tr-name:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-tr-role { font-size: 13px; color: #64748b; outline: none; text-align: center; }
      .doclib-tr-role:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-tr-del { position: absolute; top: -8px; right: 0; background: #ef4444; color: #fff; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer; display: none; align-items: center; justify-content: center; font-size: 10px; }
      .doclib-tr-member:hover .doclib-tr-del { display: flex; }
      .doclib-tr-add { margin-top: 24px; padding: 8px 16px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 4px; cursor: pointer; width: 100%; color: #64748b; }
      .doclib-tr-add:hover { background: #f1f5f9; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-tr");

    const titleEl = document.createElement("div");
    titleEl.classList.add("doclib-tr-title");
    titleEl.innerText = this.data.title;
    titleEl.dataset.placeholder = "DocLib Meet the Team";
    if (!this.readOnly) {
      titleEl.contentEditable = "true";
      titleEl.addEventListener("input", () => {
        this.data.title = titleEl.innerText;
      });
    }
    container.appendChild(titleEl);

    const grid = document.createElement("div");
    grid.classList.add("doclib-tr-grid");
    container.appendChild(grid);

    const renderMembers = () => {
      grid.innerHTML = "";
      this.data.members.forEach((m: any, i: number) => {
        const memEl = document.createElement("div");
        memEl.classList.add("doclib-tr-member");

        const avWrap = document.createElement("div");
        avWrap.classList.add("doclib-tr-avatar-wrap");
        const av = document.createElement("img");
        av.classList.add("doclib-tr-avatar");
        av.src = m.avatar || "https://via.placeholder.com/100";
        avWrap.appendChild(av);

        if (!this.readOnly) {
          const avInput = document.createElement("input");
          avInput.type = "text";
          avInput.classList.add("doclib-tr-input");
          avInput.title = "Click to enter image URL";
          avInput.addEventListener("click", () => {
            const url = prompt("DocLib Image URL", m.avatar);
            if (url !== null) {
              this.data.members[i].avatar = url;
              renderMembers();
            }
          });
          avWrap.appendChild(avInput);
        }

        const nameEl = document.createElement("div");
        nameEl.classList.add("doclib-tr-name");
        nameEl.innerText = m.name;
        nameEl.dataset.placeholder = "DocLib Name";

        const roleEl = document.createElement("div");
        roleEl.classList.add("doclib-tr-role");
        roleEl.innerText = m.role;
        roleEl.dataset.placeholder = "DocLib Role";

        if (!this.readOnly) {
          nameEl.contentEditable = "true";
          nameEl.addEventListener("input", () => {
            this.data.members[i].name = nameEl.innerText;
          });
          roleEl.contentEditable = "true";
          roleEl.addEventListener("input", () => {
            this.data.members[i].role = roleEl.innerText;
          });

          const del = document.createElement("button");
          del.classList.add("doclib-tr-del");
          del.innerText = "✕";
          del.addEventListener("click", () => {
            this.data.members.splice(i, 1);
            renderMembers();
          });
          memEl.appendChild(del);
        }

        memEl.appendChild(avWrap);
        memEl.appendChild(nameEl);
        memEl.appendChild(roleEl);
        grid.appendChild(memEl);
      });
    };

    renderMembers();

    if (!this.readOnly) {
      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-tr-add");
      addBtn.innerText = "+ Add Member";
      addBtn.addEventListener("click", () => {
        this.data.members.push({ name: "", role: "", avatar: "" });
        renderMembers();
      });
      container.appendChild(addBtn);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
