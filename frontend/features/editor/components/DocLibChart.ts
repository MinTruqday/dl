import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibChart implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    type: "bar" | "line" | "pie" | "radar" | "doughnut" | "polarArea";
    labels: string[];
    datasets: { label: string; data: number[] }[];
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Chart",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
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
      type: data?.type || "continuous",
      labels:
        data?.labels || [],
      datasets:
        data?.datasets || [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-chart-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-chart-styles";
      style.innerHTML = `
            .doclib-chart-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; background: #fff; margin: 16px 0; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
            .doclib-chart-canvas-container { width: 100%; height: 350px; display: flex; justify-content: center; align-items: center; margin-bottom: 24px; }
            .doclib-chart-editor { width: 100%; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; font-size: 13px; }
            .doclib-chart-row { display: flex; border-bottom: 1px solid #e2e8f0; }
            .doclib-chart-row:last-child { border-bottom: none; }
            .doclib-chart-cell { flex: 1; padding: 8px; border-right: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: center; min-width: 80px; }
            .doclib-chart-cell:last-child { border-right: none; }
            .doclib-chart-cell.header { background: #f8fafc; font-weight: 600; color: #475569; }
            .doclib-chart-input { width: 100%; border: none; outline: none; background: transparent; text-align: center; }
            .doclib-chart-btn-group { display: flex; gap: 8px; margin-top: 12px; }
            .doclib-chart-btn { padding: 6px 12px; font-size: 13px; border: 1px solid #cbd5e1; border-radius: 4px; background: #fff; cursor: pointer; color: #475569; font-weight: 500; transition: background 0.2s; }
            .doclib-chart-btn:hover { background: #f1f5f9; }
        `;
      document.head.appendChild(style);
    }

    this.wrapper.classList.add("doclib-chart-wrapper");
    this.buildUI();
    return this.wrapper;
  }

  renderSettings() {
    const wrapper = document.createElement("div");

    const types = [
      { type: "bar", label: "Bar" },
      { type: "line", label: "Line" },
      { type: "pie", label: "Pie" },
      { type: "radar", label: "Radar" },
      { type: "doughnut", label: "Doughnut" },
      { type: "polarArea", label: "Polar Area" },
    ];

    types.forEach((t) => {
      const btn = document.createElement("div");
      btn.classList.add(this.api.styles.settingsButton);
      if (this.data.type === t.type)
        btn.classList.add(this.api.styles.settingsButtonActive);
      btn.innerText = t.label;
      btn.addEventListener("click", () => {
        this.data.type = t.type as any;
        this.buildUI();
      });
      wrapper.appendChild(btn);
    });

    return wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const canvasContainer = document.createElement("div");
    canvasContainer.classList.add("doclib-chart-canvas-container");

    const renderChart = () => {
      canvasContainer.innerHTML = "";
      const canvas = document.createElement("canvas");
      canvasContainer.appendChild(canvas);

      const loadAndRender = () => {
        try {
          const ctx = canvas.getContext("2d");
          new (window as any).Chart(ctx, {
            type: this.data.type,
            data: {
              labels: this.data.labels,
              datasets: this.data.datasets.map((ds, i) => {
                const colors = [
                  "rgba(59, 130, 246, 0.6)",
                  "rgba(16, 185, 129, 0.6)",
                  "rgba(245, 158, 11, 0.6)",
                  "rgba(239, 68, 68, 0.6)",
                ];
                const borderColors = [
                  "rgba(59, 130, 246, 1)",
                  "rgba(16, 185, 129, 1)",
                  "rgba(245, 158, 11, 1)",
                  "rgba(239, 68, 68, 1)",
                ];

                let bg = colors[i % colors.length];
                let border = borderColors[i % borderColors.length];

                if (["pie", "doughnut", "polarArea"].includes(this.data.type)) {
                  bg = colors as any;
                  border = borderColors as any;
                }

                return {
                  label: ds.label,
                  data: ds.data,
                  backgroundColor: bg,
                  borderColor: border,
                  borderWidth: 1,
                };
              }),
            },
            options: { responsive: true, maintainAspectRatio: false },
          });
        } catch (e) {
          canvasContainer.innerHTML =
            '<span style="color:#ef4444; font-weight: 500;">Error render Chart.js</span>';
        }
      };

      if (!(window as any).Chart) {
        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/npm/chart.js";
        script.onload = loadAndRender;
        document.head.appendChild(script);
      } else {
        loadAndRender();
      }
    };

    this.wrapper.appendChild(canvasContainer);

    if (!this.readOnly) {
      const editor = document.createElement("div");
      editor.classList.add("doclib-chart-editor");

      const headerRow = document.createElement("div");
      headerRow.classList.add("doclib-chart-row");
      const emptyCell = document.createElement("div");
      emptyCell.classList.add("doclib-chart-cell", "header");
      emptyCell.innerText = "Label (X)";
      headerRow.appendChild(emptyCell);

      this.data.datasets.forEach((ds, dsIndex) => {
        const cell = document.createElement("div");
        cell.classList.add("doclib-chart-cell", "header");
        const input = document.createElement("input");
        input.classList.add("doclib-chart-input");
        input.value = ds.label;
        input.addEventListener("input", () => {
          ds.label = input.value;
          renderChart();
        });
        cell.appendChild(input);
        headerRow.appendChild(cell);
      });
      editor.appendChild(headerRow);

      this.data.labels.forEach((label, labelIndex) => {
        const row = document.createElement("div");
        row.classList.add("doclib-chart-row");

        const labelCell = document.createElement("div");
        labelCell.classList.add("doclib-chart-cell", "header");
        const labelInput = document.createElement("input");
        labelInput.classList.add("doclib-chart-input");
        labelInput.value = label;
        labelInput.addEventListener("input", () => {
          this.data.labels[labelIndex] = labelInput.value;
          renderChart();
        });
        labelCell.appendChild(labelInput);
        row.appendChild(labelCell);

        this.data.datasets.forEach((ds, dsIndex) => {
          const cell = document.createElement("div");
          cell.classList.add("doclib-chart-cell");
          const input = document.createElement("input");
          input.classList.add("doclib-chart-input");
          input.type = "number";
          input.value = (ds.data[labelIndex] || 0).toString();
          input.addEventListener("input", () => {
            ds.data[labelIndex] = parseFloat(input.value) || 0;
            renderChart();
          });
          cell.appendChild(input);
          row.appendChild(cell);
        });

        editor.appendChild(row);
      });

      this.wrapper.appendChild(editor);

      const btnGroup = document.createElement("div");
      btnGroup.classList.add("doclib-chart-btn-group");

      const addRowBtn = document.createElement("button");
      addRowBtn.classList.add("doclib-chart-btn");
      addRowBtn.innerText = "+ Add Row";
      addRowBtn.addEventListener("click", () => {
        this.data.labels.push("New label");
        this.data.datasets.forEach((ds) => ds.data.push(0));
        this.buildUI();
      });

      const addColBtn = document.createElement("button");
      addColBtn.classList.add("doclib-chart-btn");
      addColBtn.innerText = "+ Add Dataset";
      addColBtn.addEventListener("click", () => {
        this.data.datasets.push({
          label: "New dataset",
          data: new Array(this.data.labels.length).fill(0),
        });
        this.buildUI();
      });

      const rmRowBtn = document.createElement("button");
      rmRowBtn.classList.add("doclib-chart-btn");
      rmRowBtn.innerText = "- Delete Last Row";
      rmRowBtn.addEventListener("click", () => {
        if (this.data.labels.length > 1) {
          this.data.labels.pop();
          this.data.datasets.forEach((ds) => ds.data.pop());
          this.buildUI();
        }
      });

      btnGroup.appendChild(addRowBtn);
      btnGroup.appendChild(addColBtn);
      btnGroup.appendChild(rmRowBtn);
      this.wrapper.appendChild(btnGroup);
    }

    renderChart();
  }

  save() {
    return this.data;
  }
}
