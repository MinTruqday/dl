import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibKanban implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    columns: {
      id: string;
      title: string;
      color: string;
      tasks: { id: string; text: string }[];
    }[];
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Kanban",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>',
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
    data?: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      columns: data?.columns || [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-kanban-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-kanban-styles";
      style.innerHTML = `
            .doclib-kb-wrapper { display: flex; gap: 16px; margin: 16px 0; overflow-x: auto; padding-bottom: 12px; }
            .doclib-kb-col { flex: 0 0 250px; background: #f1f5f9; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
            .doclib-kb-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
            .doclib-kb-dot { width: 12px; height: 12px; border-radius: 50%; }
            .doclib-kb-title { font-weight: 700; color: #1e293b; outline: none; flex-grow: 1; }
            .doclib-kb-task { background: #fff; padding: 12px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; gap: 8px; align-items: flex-start; }
            .doclib-kb-task-text { flex-grow: 1; outline: none; font-size: 14px; color: #334155; line-height: 1.4; }
            .doclib-kb-task-text:empty::before { content: 'Enter task name'; color: #94a3b8; }
            .doclib-kb-btn-rm { background: transparent; border: none; color: #cbd5e1; cursor: pointer; padding: 0; display: flex; opacity: 0; }
            .doclib-kb-task:hover .doclib-kb-btn-rm { opacity: 1; }
            .doclib-kb-btn-rm:hover { color: #ef4444; }
            .doclib-kb-add { margin-top: 8px; padding: 8px; background: transparent; border: 1px dashed #cbd5e1; border-radius: 6px; color: #64748b; font-weight: 500; cursor: pointer; transition: background 0.2s; }
            .doclib-kb-add:hover { background: #e2e8f0; }
            .doclib-kb-nav { display: flex; gap: 4px; flex-direction: column; }
            .doclib-kb-nav-btn { background: transparent; border: none; cursor: pointer; font-size: 10px; color: #94a3b8; padding: 2px; }
            .doclib-kb-nav-btn:hover { color: #0f172a; }
        `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const container = document.createElement("div");
    container.classList.add("doclib-kb-wrapper");

    this.data.columns.forEach((col, colIndex) => {
      const colEl = document.createElement("div");
      colEl.classList.add("doclib-kb-col");

      const header = document.createElement("div");
      header.classList.add("doclib-kb-header");

      const dot = document.createElement("div");
      dot.classList.add("doclib-kb-dot");
      dot.style.backgroundColor = col.color;

      const title = document.createElement("div");
      title.classList.add("doclib-kb-title");
      title.contentEditable = !this.readOnly ? "true" : "false";
      title.innerHTML = col.title;
      title.addEventListener("input", () => (col.title = title.innerHTML));

      header.appendChild(dot);
      header.appendChild(title);

      if (!this.readOnly) {
        dot.style.cursor = "pointer";
        dot.addEventListener("click", () => {
          const newColor = prompt(
            "Enter color code (Hex/Name) for this column:",
            col.color,
          );
          if (newColor) {
            col.color = newColor;
            dot.style.backgroundColor = newColor;
          }
        });

        if (this.data.columns.length > 1) {
          const rmCol = document.createElement("button");
          rmCol.innerHTML = "&times;";
          rmCol.style.border = "none";
          rmCol.style.background = "transparent";
          rmCol.style.cursor = "pointer";
          rmCol.addEventListener("click", () => {
            this.data.columns.splice(colIndex, 1);
            this.buildUI();
          });
          header.appendChild(rmCol);
        }
      }
      colEl.appendChild(header);

      col.tasks.forEach((task, taskIndex) => {
        const taskEl = document.createElement("div");
        taskEl.classList.add("doclib-kb-task");

        const text = document.createElement("div");
        text.classList.add("doclib-kb-task-text");
        text.contentEditable = !this.readOnly ? "true" : "false";
        text.innerHTML = task.text;
        text.addEventListener("input", () => (task.text = text.innerHTML));

        taskEl.appendChild(text);

        if (!this.readOnly) {
          const nav = document.createElement("div");
          nav.classList.add("doclib-kb-nav");

          if (colIndex > 0) {
            const moveLeft = document.createElement("button");
            moveLeft.classList.add("doclib-kb-nav-btn");
            moveLeft.innerHTML = "◄";
            moveLeft.addEventListener("click", () => {
              this.data.columns[colIndex].tasks.splice(taskIndex, 1);
              this.data.columns[colIndex - 1].tasks.push(task);
              this.buildUI();
            });
            nav.appendChild(moveLeft);
          }

          if (colIndex < this.data.columns.length - 1) {
            const moveRight = document.createElement("button");
            moveRight.classList.add("doclib-kb-nav-btn");
            moveRight.innerHTML = "►";
            moveRight.addEventListener("click", () => {
              this.data.columns[colIndex].tasks.splice(taskIndex, 1);
              this.data.columns[colIndex + 1].tasks.push(task);
              this.buildUI();
            });
            nav.appendChild(moveRight);
          }

          taskEl.appendChild(nav);

          const rmBtn = document.createElement("button");
          rmBtn.classList.add("doclib-kb-btn-rm");
          rmBtn.innerHTML =
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
          rmBtn.addEventListener("click", () => {
            col.tasks.splice(taskIndex, 1);
            this.buildUI();
          });
          taskEl.appendChild(rmBtn);
        }

        colEl.appendChild(taskEl);
      });

      if (!this.readOnly) {
        const addBtn = document.createElement("button");
        addBtn.classList.add("doclib-kb-add");
        addBtn.innerText = "+ Add Card";
        addBtn.addEventListener("click", () => {
          col.tasks.push({ id: Date.now().toString(), text: "" });
          this.buildUI();
        });
        colEl.appendChild(addBtn);
      }

      container.appendChild(colEl);
    });

    if (!this.readOnly && this.data.columns.length < 5) {
      const addColBtn = document.createElement("div");
      addColBtn.style.flex = "0 0 50px";
      addColBtn.style.display = "flex";
      addColBtn.style.alignItems = "center";
      addColBtn.style.justifyContent = "center";
      addColBtn.style.border = "2px dashed #cbd5e1";
      addColBtn.style.borderRadius = "8px";
      addColBtn.style.cursor = "pointer";
      addColBtn.style.color = "#94a3b8";
      addColBtn.innerHTML =
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>';
      addColBtn.addEventListener("click", () => {
        this.data.columns.push({
          id: Date.now().toString(),
          title: "New Column",
          color: "#94a3b8",
          tasks: [],
        });
        this.buildUI();
      });
      container.appendChild(addColBtn);
    }

    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
