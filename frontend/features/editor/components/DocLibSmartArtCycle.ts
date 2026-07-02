import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibSmartArtCycle implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib SmartArt Cycle",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12A10 10 0 1 1 12 2v10z"/><path d="M12 2a10 10 0 0 1 10 10h-10z"/></svg>',
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
      items:
        data?.items && data.items.length > 0
          ? data.items
          : ["DocLib Text", "DocLib Text", "DocLib Text"],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-cycle { display: flex; flex-direction: column; align-items: center; margin: 32px 0; }
      .doclib-cycle-chart { position: relative; width: 300px; height: 300px; border-radius: 50%; border: 16px solid #e2e8f0; display: flex; align-items: center; justify-content: center; }
      .doclib-cycle-center { width: 100px; height: 100px; background: #fff; border-radius: 50%; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); z-index: 10; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #3b82f6; }
      .doclib-cycle-node { position: absolute; width: 80px; height: 80px; background: #3b82f6; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; text-align: center; font-size: 12px; font-weight: 600; padding: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); outline: none; }
      
      .doclib-cycle-edit { margin-top: 24px; display: flex; flex-direction: column; gap: 8px; width: 100%; max-width: 400px; }
      .doclib-cycle-row { display: flex; gap: 8px; }
      .doclib-cycle-input { flex: 1; padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; }
      .doclib-cycle-btn { padding: 8px; background: #ef4444; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
      .doclib-cycle-add { padding: 8px; background: #10b981; color: #fff; border: none; border-radius: 4px; cursor: pointer; align-self: center; width: 100%; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-cycle");

    const chart = document.createElement("div");
    chart.classList.add("doclib-cycle-chart");

    const center = document.createElement("div");
    center.classList.add("doclib-cycle-center");
    center.innerText = "CYCLE";
    chart.appendChild(center);

    const renderChart = () => {
      chart.querySelectorAll(".doclib-cycle-node").forEach((n) => n.remove());
      const n = this.data.items.length;
      const radius = 150;
      this.data.items.forEach((text: string, i: number) => {
        const angle = i * (360 / n) - 90;
        const rad = angle * (Math.PI / 180);
        const x = Math.cos(rad) * radius;
        const y = Math.sin(rad) * radius;

        const node = document.createElement("div");
        node.classList.add("doclib-cycle-node");
        node.innerText = text;
        node.style.transform = `translate(${x}px, ${y}px)`;
        chart.appendChild(node);
      });
    };

    renderChart();
    container.appendChild(chart);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-cycle-edit");

      const renderEdit = () => {
        edit.innerHTML = "";
        this.data.items.forEach((text: string, i: number) => {
          const row = document.createElement("div");
          row.classList.add("doclib-cycle-row");

          const input = document.createElement("input");
          input.classList.add("doclib-cycle-input");
          input.value = text;
          input.placeholder = "DocLib Input";
          input.addEventListener("input", () => {
            this.data.items[i] = input.value;
            renderChart();
          });

          const del = document.createElement("button");
          del.classList.add("doclib-cycle-btn");
          del.innerText = "X";
          del.addEventListener("click", () => {
            this.data.items.splice(i, 1);
            renderChart();
            renderEdit();
          });

          row.appendChild(input);
          row.appendChild(del);
          edit.appendChild(row);
        });

        if (this.data.items.length < 8) {
          const add = document.createElement("button");
          add.classList.add("doclib-cycle-add");
          add.innerText = "+ Add Step";
          add.addEventListener("click", () => {
            this.data.items.push("DocLib Text");
            renderChart();
            renderEdit();
          });
          edit.appendChild(add);
        }
      };

      renderEdit();
      container.appendChild(edit);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      items: this.data.items,
    };
  }
}
