import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibKanban implements BlockTool {
  static readonly feature = {
    id: "DocLibKanban",
    title: "DocLib Kanban",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="bba3a666a78199af"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="4,14 17,4 18,14 4,9 6,20 20,20"/></svg>',
    product: "doclib",
  } as const;

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
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="bba3a666a78199af"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="4,14 17,4 18,14 4,9 6,20 20,20"/></svg>',
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
            .doclib-kb-col { flex: 0 0 250px; background: hsl(var(--surface-quiet)); border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
            .doclib-kb-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
            .doclib-kb-dot { width: 12px; height: 12px; border-radius: 50%; }
            .doclib-kb-title { font-weight: 700; color: hsl(var(--ink)); outline: none; flex-grow: 1; }
            .doclib-kb-task { background: hsl(var(--surface)); padding: 12px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; gap: 8px; align-items: flex-start; }
            .doclib-kb-task-text { flex-grow: 1; outline: none; font-size: 14px; color: hsl(var(--ink)); line-height: 1.4; }
            .doclib-kb-task-text:empty::before { content: 'Enter task name'; color: hsl(var(--ink-faint)); }
            .doclib-kb-btn-rm { background: transparent; border: none; color: hsl(var(--border)); cursor: pointer; padding: 0; display: flex; opacity: 0; }
            .doclib-kb-task:hover .doclib-kb-btn-rm { opacity: 1; }
            .doclib-kb-btn-rm:hover { color: hsl(var(--danger)); }
            .doclib-kb-add { margin-top: 8px; padding: 8px; background: transparent; border: 1px dashed hsl(var(--border)); border-radius: 6px; color: hsl(var(--ink-muted)); font-weight: 500; cursor: pointer; transition: background 0.2s; }
            .doclib-kb-add:hover { background: hsl(var(--border)); }
            .doclib-kb-nav { display: flex; gap: 4px; flex-direction: column; }
            .doclib-kb-nav-btn { background: transparent; border: none; cursor: pointer; font-size: 10px; color: hsl(var(--ink-faint)); padding: 2px; }
            .doclib-kb-nav-btn:hover { color: hsl(var(--ink)); }
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
            moveLeft.innerText = "<";
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
            moveRight.innerText = ">";
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
            '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="bba3a666a78199af"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="4,14 17,4 18,14 4,9 6,20 20,20"/></svg>';
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
      addColBtn.style.border = "2px dashed hsl(var(--border))";
      addColBtn.style.borderRadius = "8px";
      addColBtn.style.cursor = "pointer";
      addColBtn.style.color = "hsl(var(--ink-faint))";
      addColBtn.innerHTML =
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="bba3a666a78199af"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="4,14 17,4 18,14 4,9 6,20 20,20"/></svg>';
      addColBtn.addEventListener("click", () => {
        this.data.columns.push({
          id: Date.now().toString(),
          title: "DocLib New Column",
          color: "hsl(var(--ink-faint))",
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
