import { API, BlockTool } from "@editorjs/editorjs";

interface GanttTask {
  name: string;
  start: number;
  end: number;
  color: string;
}

export default class DocLibGantt implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { title: string; tasks: GanttTask[]; totalDays: number };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Gantt",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="12" x2="15" y2="12"></line><line x1="3" y1="18" x2="18" y2="18"></line></svg>',
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
      totalDays: data?.totalDays || 30,
      tasks: data?.tasks || [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-gantt-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-gantt-styles";
      style.innerHTML = `
        .doclib-gantt-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; background: #fff; margin: 12px 0; overflow-x: auto; }
        .doclib-gantt-title { font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 16px; }
        .doclib-gantt-header { display: flex; margin-bottom: 4px; padding-left: 160px; }
        .doclib-gantt-day-label { flex: 1; font-size: 10px; color: #94a3b8; text-align: center; }
        .doclib-gantt-row { display: flex; align-items: center; height: 36px; margin-bottom: 6px; }
        .doclib-gantt-task-name { width: 150px; min-width: 150px; font-size: 12px; font-weight: 500; color: #475569; padding-right: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .doclib-gantt-track { flex: 1; height: 100%; background: #f1f5f9; border-radius: 4px; position: relative; overflow: hidden; }
        .doclib-gantt-bar { position: absolute; height: 100%; border-radius: 4px; display: flex; align-items: center; padding: 0 8px; font-size: 10px; font-weight: 600; color: #fff; white-space: nowrap; overflow: hidden; }
        .doclib-gantt-edit { border-top: 1px solid #e2e8f0; margin-top: 16px; padding-top: 14px; }
        .doclib-gantt-task-edit { display: grid; grid-template-columns: 2fr 1fr 1fr 30px; gap: 6px; align-items: center; margin-bottom: 6px; }
        .doclib-gantt-input { padding: 6px 8px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 12px; outline: none; width: 100%; box-sizing: border-box; }
        .doclib-gantt-del-btn { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 16px; line-height: 1; }
        .doclib-gantt-del-btn:hover { color: #ef4444; }
        .doclib-gantt-add-btn { margin-top: 8px; padding: 7px 14px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 12px; cursor: pointer; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildChart(container: HTMLElement) {
    container.innerHTML = "";

    const title = document.createElement("div");
    title.classList.add("doclib-gantt-title");
    title.innerText = this.data.title;
    container.appendChild(title);

    const headerRow = document.createElement("div");
    headerRow.classList.add("doclib-gantt-header");
    const step = this.data.totalDays <= 30 ? 5 : 10;
    for (let d = 0; d <= this.data.totalDays; d += step) {
      const lbl = document.createElement("div");
      lbl.classList.add("doclib-gantt-day-label");
      lbl.innerText = `D${d}`;
      headerRow.appendChild(lbl);
    }
    container.appendChild(headerRow);

    this.data.tasks.forEach((task) => {
      const row = document.createElement("div");
      row.classList.add("doclib-gantt-row");

      const nameDiv = document.createElement("div");
      nameDiv.classList.add("doclib-gantt-task-name");
      nameDiv.innerText = task.name;
      nameDiv.title = task.name;

      const track = document.createElement("div");
      track.classList.add("doclib-gantt-track");

      const startPct = (task.start / this.data.totalDays) * 100;
      const widthPct = ((task.end - task.start) / this.data.totalDays) * 100;

      const bar = document.createElement("div");
      bar.classList.add("doclib-gantt-bar");
      bar.style.left = `${startPct}%`;
      bar.style.width = `${widthPct}%`;
      bar.style.background = task.color;
      bar.innerText = task.name;
      bar.title = `${task.name}: Day ${task.start}  ${task.end}`;

      track.appendChild(bar);
      row.appendChild(nameDiv);
      row.appendChild(track);
      container.appendChild(row);
    });
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-gantt-wrapper");

    const chartArea = document.createElement("div");
    this.buildChart(chartArea);
    this.wrapper.appendChild(chartArea);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-gantt-edit");

      const totalLabel = document.createElement("div");
      totalLabel.style.cssText =
        "font-size:12px;color:#64748b;margin-bottom:8px;";
      totalLabel.innerText = `Total days: ${this.data.totalDays}`;

      const totalInput = document.createElement("input");
      totalInput.classList.add("doclib-gantt-input");
      totalInput.type = "number";
      totalInput.value = `${this.data.totalDays}`;
      totalInput.style.width = "80px";
      totalInput.min = "7";
      totalInput.max = "365";
      totalInput.addEventListener("change", () => {
        this.data.totalDays = parseInt(totalInput.value) || 30;
        this.buildChart(chartArea);
        totalLabel.innerText = `Total days: ${this.data.totalDays}`;
      });

      edit.appendChild(totalLabel);
      edit.appendChild(totalInput);

      const colHeader = document.createElement("div");
      colHeader.style.cssText =
        "display:grid;grid-template-columns:2fr 1fr 1fr 30px;gap:6px;font-size:10px;font-weight:600;color:#94a3b8;text-transform:uppercase;margin-top:12px;margin-bottom:4px;";
      colHeader.innerHTML =
        "<span>Task name</span><span>Start</span><span>End</span><span></span>";
      edit.appendChild(colHeader);

      const taskRows = document.createElement("div");

      const renderTaskEdits = () => {
        taskRows.innerHTML = "";
        this.data.tasks.forEach((task, i) => {
          const row = document.createElement("div");
          row.classList.add("doclib-gantt-task-edit");

          const nameIn = document.createElement("input");
          nameIn.classList.add("doclib-gantt-input");
          nameIn.value = task.name;
          nameIn.addEventListener("input", () => {
            task.name = nameIn.value;
            this.buildChart(chartArea);
          });

          const startIn = document.createElement("input");
          startIn.classList.add("doclib-gantt-input");
          startIn.type = "number";
          startIn.min = "0";
          startIn.value = `${task.start}`;
          startIn.addEventListener("change", () => {
            task.start = Math.max(0, parseInt(startIn.value) || 0);
            this.buildChart(chartArea);
          });

          const endIn = document.createElement("input");
          endIn.classList.add("doclib-gantt-input");
          endIn.type = "number";
          endIn.min = "1";
          endIn.value = `${task.end}`;
          endIn.addEventListener("change", () => {
            task.end = Math.max(
              task.start + 1,
              parseInt(endIn.value) || task.start + 1,
            );
            this.buildChart(chartArea);
          });

          const delBtn = document.createElement("button");
          delBtn.classList.add("doclib-gantt-del-btn");
          delBtn.innerText = "x";
          delBtn.addEventListener("click", () => {
            this.data.tasks.splice(i, 1);
            renderTaskEdits();
            this.buildChart(chartArea);
          });

          row.appendChild(nameIn);
          row.appendChild(startIn);
          row.appendChild(endIn);
          row.appendChild(delBtn);
          taskRows.appendChild(row);
        });
      };

      renderTaskEdits();
      edit.appendChild(taskRows);

      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-gantt-add-btn");
      addBtn.innerText = "Add task";
      const colors = [
        "#0284c7",
        "#7c3aed",
        "#059669",
        "#d97706",
        "#dc2626",
        "#0891b2",
        "#db2777",
      ];
      addBtn.addEventListener("click", () => {
        const last = this.data.tasks[this.data.tasks.length - 1];
        const start = last ? last.end : 0;
        this.data.tasks.push({
          name: `Task ${this.data.tasks.length + 1}`,
          start,
          end: Math.min(start + 5, this.data.totalDays),
          color: colors[this.data.tasks.length % colors.length],
        });
        renderTaskEdits();
        this.buildChart(chartArea);
      });

      edit.appendChild(addBtn);
      this.wrapper.appendChild(edit);
    }
  }

  save() {
    return this.data;
  }
}
