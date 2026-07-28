import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibChart implements BlockTool {
  static readonly feature = {
    id: "DocLibChart",
    title: "DocLib Chart",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6ce5dd1cb9985287"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="10,12 4,15 19,20 18,20 12,14 4,13"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    type:
      | "bar"
      | "line"
      | "pie"
      | "radar"
      | "doughnut"
      | "polarArea"
      | "scatter"
      | "bubble";
    title: string;
    showLegend: boolean;
    stacked: boolean;
    tension: number;
    labels: string[];
    datasets: {
      label: string;
      data: number[];
      backgroundColor?: string;
      borderColor?: string;
    }[];
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Chart",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6ce5dd1cb9985287"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="10,12 4,15 19,20 18,20 12,14 4,13"/></svg>',
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
      type: data?.type || "bar",
      title: data?.title || "",
      showLegend: data?.showLegend !== undefined ? data?.showLegend : true,
      stacked: data?.stacked || false,
      tension: data?.tension !== undefined ? data?.tension : 0.4,
      labels: data?.labels || [],
      datasets: data?.datasets || [],
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
        .doclib-chart-canvas-container { width: 100%; height: 400px; display: flex; justify-content: center; align-items: center; margin-bottom: 24px; }
        .doclib-chart-config { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 16px; padding: 16px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }
        .doclib-chart-config-item { display: flex; flex-direction: column; gap: 4px; }
        .doclib-chart-config-label { font-size: 12px; font-weight: 600; color: #475569; }
        .doclib-chart-config-input { padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; font-size: 13px; }
        .doclib-chart-config-check { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #475569; font-weight: 500; cursor: pointer; }
        .doclib-chart-editor { width: 100%; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; font-size: 13px; overflow-x: auto; }
        .doclib-chart-row { display: flex; border-bottom: 1px solid #e2e8f0; min-width: fit-content; }
        .doclib-chart-row:last-child { border-bottom: none; }
        .doclib-chart-cell { flex: 1; padding: 8px; border-right: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: center; min-width: 120px; flex-direction: column; gap: 4px; }
        .doclib-chart-cell.header { background: #f8fafc; font-weight: 600; color: #475569; flex-direction: row; }
        .doclib-chart-input { width: 100%; border: none; outline: none; background: transparent; text-align: center; }
        .doclib-chart-color-picker { width: 24px; height: 24px; padding: 0; border: none; cursor: pointer; border-radius: 4px; }
        .doclib-chart-btn-group { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
        .doclib-chart-btn { padding: 6px 12px; font-size: 13px; border: 1px solid #cbd5e1; border-radius: 4px; background: #fff; cursor: pointer; color: #475569; font-weight: 500; transition: background 0.2s; }
        .doclib-chart-btn:hover { background: #f1f5f9; }
        .doclib-chart-btn.danger { color: #ef4444; border-color: #fca5a5; }
        .doclib-chart-btn.danger:hover { background: #fef2f2; }
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
      { type: "scatter", label: "Scatter" },
      { type: "bubble", label: "Bubble" },
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

          const options: any = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: this.data.showLegend,
                position: "bottom",
              },
              title: {
                display: !!this.data.title,
                text: this.data.title,
                font: { size: 16 },
              },
            },
          };

          if (this.data.type === "bar" && this.data.stacked) {
            options.scales = {
              x: { stacked: true },
              y: { stacked: true },
            };
          }

          new (window as any).Chart(ctx, {
            type: this.data.type,
            data: {
              labels: this.data.labels,
              datasets: this.data.datasets.map((ds, i) => {
                const defaultColors = [
                  "rgba(59, 130, 246, 0.6)",
                  "rgba(16, 185, 129, 0.6)",
                  "rgba(245, 158, 11, 0.6)",
                  "rgba(239, 68, 68, 0.6)",
                ];
                const defaultBorderColors = [
                  "rgba(59, 130, 246, 1)",
                  "rgba(16, 185, 129, 1)",
                  "rgba(245, 158, 11, 1)",
                  "rgba(239, 68, 68, 1)",
                ];

                let bg: any =
                  ds.backgroundColor || defaultColors[i % defaultColors.length];
                let border: any =
                  ds.borderColor ||
                  defaultBorderColors[i % defaultBorderColors.length];

                if (["pie", "doughnut", "polarArea"].includes(this.data.type)) {
                  bg = defaultColors;
                  border = defaultBorderColors;
                }

                return {
                  label: ds.label,
                  data: ds.data,
                  backgroundColor: bg,
                  borderColor: border,
                  borderWidth: 1,
                  tension: this.data.tension,
                };
              }),
            },
            options: options,
          });
        } catch (e) {
          canvasContainer.innerHTML =
            '<span style="color:#ef4444; font-weight: 500;">Error rendering Chart.js</span>';
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

    if (!this.readOnly) {
      const configPanel = document.createElement("div");
      configPanel.classList.add("doclib-chart-config");

      const titleItem = document.createElement("div");
      titleItem.classList.add("doclib-chart-config-item");
      const titleLabel = document.createElement("div");
      titleLabel.classList.add("doclib-chart-config-label");
      titleLabel.innerText = "Chart Title";
      const titleInput = document.createElement("input");
      titleInput.classList.add("doclib-chart-config-input");
      titleInput.value = this.data.title;
      titleInput.placeholder = "DocLib Chart Title";
      titleInput.addEventListener("input", () => {
        this.data.title = titleInput.value;
        renderChart();
      });
      titleItem.appendChild(titleLabel);
      titleItem.appendChild(titleInput);
      configPanel.appendChild(titleItem);

      const legendLabel = document.createElement("label");
      legendLabel.classList.add("doclib-chart-config-check");
      const legendCheck = document.createElement("input");
      legendCheck.type = "checkbox";
      legendCheck.checked = this.data.showLegend;
      legendCheck.addEventListener("change", () => {
        this.data.showLegend = legendCheck.checked;
        renderChart();
      });
      legendLabel.appendChild(legendCheck);
      legendLabel.appendChild(document.createTextNode("Show Legend"));
      configPanel.appendChild(legendLabel);

      if (this.data.type === "bar") {
        const stackedLabel = document.createElement("label");
        stackedLabel.classList.add("doclib-chart-config-check");
        const stackedCheck = document.createElement("input");
        stackedCheck.type = "checkbox";
        stackedCheck.checked = this.data.stacked;
        stackedCheck.addEventListener("change", () => {
          this.data.stacked = stackedCheck.checked;
          renderChart();
        });
        stackedLabel.appendChild(stackedCheck);
        stackedLabel.appendChild(document.createTextNode("Stacked Mode"));
        configPanel.appendChild(stackedLabel);
      }

      if (["line", "radar"].includes(this.data.type)) {
        const tensionItem = document.createElement("div");
        tensionItem.classList.add("doclib-chart-config-item");
        const tensionLabel = document.createElement("div");
        tensionLabel.classList.add("doclib-chart-config-label");
        tensionLabel.innerText = "Curve Tension";
        const tensionInput = document.createElement("input");
        tensionInput.type = "range";
        tensionInput.min = "0";
        tensionInput.max = "1";
        tensionInput.step = "0.1";
        tensionInput.value = this.data.tension.toString();
        tensionInput.addEventListener("input", () => {
          this.data.tension = parseFloat(tensionInput.value);
          renderChart();
        });
        tensionItem.appendChild(tensionLabel);
        tensionItem.appendChild(tensionInput);
        configPanel.appendChild(tensionItem);
      }

      this.wrapper.appendChild(configPanel);
    }

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
        input.placeholder = "Dataset Name";
        input.addEventListener("input", () => {
          ds.label = input.value;
          renderChart();
        });
        cell.appendChild(input);

        const colorPicker = document.createElement("input");
        colorPicker.type = "color";
        colorPicker.classList.add("doclib-chart-color-picker");
        colorPicker.value = ds.backgroundColor
          ? ds.backgroundColor.slice(0, 7)
          : "#3b82f6";
        colorPicker.title = "Pick dataset color";
        colorPicker.addEventListener("input", () => {
          ds.backgroundColor = colorPicker.value + "99";
          ds.borderColor = colorPicker.value;
          renderChart();
        });
        cell.appendChild(colorPicker);

        const delBtn = document.createElement("button");
        delBtn.classList.add("doclib-chart-btn", "danger");
        delBtn.style.padding = "2px 6px";
        delBtn.innerText = "X";
        delBtn.addEventListener("click", () => {
          this.data.datasets.splice(dsIndex, 1);
          this.buildUI();
        });
        cell.appendChild(delBtn);

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
        labelInput.placeholder = "Label";
        labelInput.addEventListener("input", () => {
          this.data.labels[labelIndex] = labelInput.value;
          renderChart();
        });
        labelCell.appendChild(labelInput);
        row.appendChild(labelCell);

        this.data.datasets.forEach((ds) => {
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
      rmRowBtn.classList.add("doclib-chart-btn", "danger");
      rmRowBtn.innerText = "- Delete Last Row";
      rmRowBtn.addEventListener("click", () => {
        if (this.data.labels.length > 0) {
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
