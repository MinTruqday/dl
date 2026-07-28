import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibKanbanBoard implements BlockTool {
  static readonly feature = {
    id: "DocLibKanbanBoard",
    title: "DocLib KanbanBoard",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="08e2f3296b39cf12"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="12,9 9,11 9,10 7,5 6,5 5,15"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    columns: {
      id: string;
      title: string;
      tasks: { id: string; text: string; color: string }[];
    }[];
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Kanban",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="08e2f3296b39cf12"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="12,9 9,11 9,10 7,5 6,5 5,15"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  private mkId() {
    return Math.random().toString(36).substring(2, 8);
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
        .doclib-kanban-wrapper { display: flex; gap: 16px; overflow-x: auto; padding: 12px 0; margin: 12px 0; align-items: flex-start; }
        .doclib-kanban-col { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; width: 280px; min-width: 280px; padding: 12px; display: flex; flex-direction: column; gap: 10px; }
        .doclib-kanban-header { display: flex; justify-content: space-between; align-items: center; font-size: 14px; font-weight: 700; color: #0f172a; }
        .doclib-kanban-title-input { font-size: 14px; font-weight: 700; border: none; background: transparent; outline: none; width: 100%; color: #0f172a; }
        .doclib-kanban-del-col { background: none; border: none; color: #94a3b8; cursor: pointer; padding: 0; font-size: 16px; }
        .doclib-kanban-tasks { display: flex; flex-direction: column; gap: 8px; min-height: 20px; }
        .doclib-kanban-task { padding: 10px 12px; background: #fff; border: 1px solid #e2e8f0; border-left: 4px solid #cbd5e1; border-radius: 6px; font-size: 13px; color: #334155; box-shadow: 0 1px 2px rgba(0,0,0,0.05); cursor: grab; position: relative; }
        .doclib-kanban-task:active { cursor: grabbing; }
        .doclib-kanban-task-input { width: 100%; border: none; outline: none; resize: none; font-family: inherit; font-size: 13px; color: #334155; background: transparent; padding: 0; margin: 0; }
        .doclib-kanban-task-del { position: absolute; top: 6px; right: 6px; font-size: 12px; color: #94a3b8; background: #fff; border: none; cursor: pointer; display: none; border-radius: 4px; }
        .doclib-kanban-task:hover .doclib-kanban-task-del { display: block; }
        .doclib-kanban-add-task { background: transparent; border: 1px dashed #cbd5e1; color: #64748b; padding: 8px; border-radius: 6px; font-size: 12px; cursor: pointer; text-align: left; }
        .doclib-kanban-add-task:hover { background: #f1f5f9; color: #0f172a; }
        .doclib-kanban-add-col { background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; width: 280px; min-width: 280px; padding: 12px; font-size: 14px; font-weight: 600; color: #64748b; cursor: pointer; text-align: center; }
        .doclib-kanban-add-col:hover { background: #f1f5f9; color: #0f172a; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    const wrapper = this.wrapper;
    wrapper.innerHTML = "";
    wrapper.classList.add("doclib-kanban-wrapper");

    let draggedTask: { colId: string; taskId: string } | null = null;

    this.data.columns.forEach((col, colIdx) => {
      const colEl = document.createElement("div");
      colEl.classList.add("doclib-kanban-col");

      const header = document.createElement("div");
      header.classList.add("doclib-kanban-header");

      if (!this.readOnly) {
        const titleInput = document.createElement("input");
        titleInput.classList.add("doclib-kanban-title-input");
        titleInput.value = col.title;
        titleInput.addEventListener("change", () => {
          col.title = titleInput.value;
        });
        header.appendChild(titleInput);

        const delBtn = document.createElement("button");
        delBtn.classList.add("doclib-kanban-del-col");
        delBtn.innerText = "x";
        delBtn.addEventListener("click", () => {
          this.data.columns.splice(colIdx, 1);
          this.buildUI();
        });
        header.appendChild(delBtn);
      } else {
        header.innerText = col.title;
      }

      colEl.appendChild(header);

      const tasksArea = document.createElement("div");
      tasksArea.classList.add("doclib-kanban-tasks");

      if (!this.readOnly) {
        tasksArea.addEventListener("dragover", (e) => {
          e.preventDefault();
        });
        tasksArea.addEventListener("drop", (e) => {
          e.preventDefault();
          if (!draggedTask) return;
          if (draggedTask.colId === col.id) return;
          const sourceCol = this.data.columns.find(
            (c) => c.id === draggedTask!.colId,
          );
          if (!sourceCol) return;
          const taskIdx = sourceCol.tasks.findIndex(
            (t) => t.id === draggedTask!.taskId,
          );
          if (taskIdx === -1) return;
          const [task] = sourceCol.tasks.splice(taskIdx, 1);
          col.tasks.push(task);
          this.buildUI();
        });
      }

      col.tasks.forEach((task, taskIdx) => {
        const taskEl = document.createElement("div");
        taskEl.classList.add("doclib-kanban-task");
        taskEl.style.borderLeftColor = task.color;

        if (!this.readOnly) {
          taskEl.draggable = true;
          taskEl.addEventListener("dragstart", () => {
            draggedTask = { colId: col.id, taskId: task.id };
          });

          const input = document.createElement("textarea");
          input.classList.add("doclib-kanban-task-input");
          input.value = task.text;
          input.rows = task.text.split("\n").length;
          input.addEventListener("input", () => {
            task.text = input.value;
            input.rows = task.text.split("\n").length || 1;
          });
          taskEl.appendChild(input);

          const delBtn = document.createElement("button");
          delBtn.classList.add("doclib-kanban-task-del");
          delBtn.innerText = "x";
          delBtn.addEventListener("click", () => {
            col.tasks.splice(taskIdx, 1);
            this.buildUI();
          });
          taskEl.appendChild(delBtn);
        } else {
          taskEl.innerText = task.text;
        }

        tasksArea.appendChild(taskEl);
      });

      colEl.appendChild(tasksArea);

      if (!this.readOnly) {
        const addBtn = document.createElement("button");
        addBtn.classList.add("doclib-kanban-add-task");
        addBtn.innerText = "+ Add Task";
        addBtn.addEventListener("click", () => {
          col.tasks.push({
            id: this.mkId(),
            text: "New task",
            color: ["#e2e8f0", "#fef08a", "#bbf7d0", "#bfdbfe", "#fbcfe8"][
              Math.floor(Math.random() * 5)
            ],
          });
          this.buildUI();
        });
        colEl.appendChild(addBtn);
      }

      wrapper.appendChild(colEl);
    });

    if (!this.readOnly) {
      const addCol = document.createElement("button");
      addCol.classList.add("doclib-kanban-add-col");
      addCol.innerText = "Add Column";
      addCol.addEventListener("click", () => {
        this.data.columns.push({
          id: this.mkId(),
          title: "DocLib New Column",
          tasks: [],
        });
        this.buildUI();
      });
      wrapper.appendChild(addCol);
    }
  }

  save() {
    return this.data;
  }
}
