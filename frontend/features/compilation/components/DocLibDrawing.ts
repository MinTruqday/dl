import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibDrawing implements BlockTool {
  static readonly feature = {
    id: "DocLibDrawing",
    title: "DocLib Drawing",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="1501f2721d1fbe32"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="8,5 8,16 16,18 7,20 20,16 4,19"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { image: string };
  private readOnly: boolean;
  private canvas: HTMLCanvasElement | null = null;
  private ctx: CanvasRenderingContext2D | null = null;
  private isDrawing: boolean = false;

  static get toolbox() {
    return {
      title: "DocLib Drawing",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="1501f2721d1fbe32"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="8,5 8,16 16,18 7,20 20,16 4,19"/></svg>',
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
    this.data = { image: data.image || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-drawing-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-drawing-styles";
      style.innerHTML = `
            .doclib-drawing-wrapper { margin: 16px 0; border: 1px solid hsl(var(--border)); border-radius: 8px; overflow: hidden; background: hsl(var(--surface)); }
            .doclib-drawing-canvas { width: 100%; height: 300px; display: block; cursor: crosshair; touch-action: none; background: hsl(var(--surface-raised)); }
            .doclib-drawing-controls { padding: 8px 16px; background: hsl(var(--surface-quiet)); border-bottom: 1px solid hsl(var(--border)); display: flex; justify-content: space-between; }
            .doclib-drawing-btn { font-size: 13px; padding: 4px 12px; border: 1px solid hsl(var(--border)); background: hsl(var(--surface)); border-radius: 4px; cursor: pointer; transition: background 0.2s; }
            .doclib-drawing-btn:hover { background: hsl(var(--border)); }
            .doclib-drawing-colors { display: flex; gap: 8px; }
            .doclib-drawing-color { width: 24px; height: 24px; border-radius: 50%; cursor: pointer; border: 2px solid transparent; }
            .doclib-drawing-color.active { border-color: hsl(var(--brand)); transform: scale(1.1); }
            .doclib-drawing-readonly-img { width: 100%; height: auto; display: block; }
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
    container.classList.add("doclib-drawing-wrapper");

    if (this.readOnly && this.data.image) {
      const img = document.createElement("img");
      img.classList.add("doclib-drawing-readonly-img");
      img.src = this.data.image;
      container.appendChild(img);
      this.wrapper.appendChild(container);
      return;
    }

    const controls = document.createElement("div");
    controls.classList.add("doclib-drawing-controls");

    const colorsDiv = document.createElement("div");
    colorsDiv.classList.add("doclib-drawing-colors");
    const colors = ["hsl(var(--ink))", "hsl(var(--danger))", "hsl(var(--brand))", "hsl(var(--brand))", "hsl(var(--warning))"];
    let currentColor = "hsl(var(--ink))";

    colors.forEach((c) => {
      const cBtn = document.createElement("div");
      cBtn.classList.add("doclib-drawing-color");
      cBtn.style.backgroundColor = c;
      if (c === currentColor) cBtn.classList.add("active");
      cBtn.addEventListener("click", () => {
        currentColor = c;
        if (this.ctx) this.ctx.strokeStyle = c;
        Array.from(colorsDiv.children).forEach((child) =>
          child.classList.remove("active"),
        );
        cBtn.classList.add("active");
      });
      colorsDiv.appendChild(cBtn);
    });

    const clearBtn = document.createElement("button");
    clearBtn.classList.add("doclib-drawing-btn");
    clearBtn.innerText = "Delete draft";
    clearBtn.addEventListener("click", () => {
      if (this.ctx && this.canvas) {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.data.image = "";
      }
    });

    controls.appendChild(colorsDiv);
    controls.appendChild(clearBtn);
    container.appendChild(controls);

    this.canvas = document.createElement("canvas");
    this.canvas.classList.add("doclib-drawing-canvas");
    container.appendChild(this.canvas);

    this.wrapper.appendChild(container);

    setTimeout(() => {
      if (!this.canvas) return;
      this.canvas.width = this.canvas.offsetWidth;
      this.canvas.height = this.canvas.offsetHeight;
      this.ctx = this.canvas.getContext("2d");
      if (!this.ctx) return;

      this.ctx.lineCap = "round";
      this.ctx.lineJoin = "round";
      this.ctx.lineWidth = 3;
      this.ctx.strokeStyle = currentColor;

      if (this.data.image) {
        const img = new Image();
        img.onload = () => this.ctx?.drawImage(img, 0, 0);
        img.src = this.data.image;
      }

      const startDrawing = (e: MouseEvent | TouchEvent) => {
        this.isDrawing = true;
        draw(e);
      };

      const stopDrawing = () => {
        this.isDrawing = false;
        if (this.ctx) this.ctx.beginPath();
        if (this.canvas) this.data.image = this.canvas.toDataURL("image/png");
      };

      const draw = (e: MouseEvent | TouchEvent) => {
        if (!this.isDrawing || !this.ctx || !this.canvas) return;
        e.preventDefault();

        const rect = this.canvas.getBoundingClientRect();
        let x = 0,
          y = 0;

        if (e instanceof MouseEvent) {
          x = e.clientX - rect.left;
          y = e.clientY - rect.top;
        } else if (e instanceof TouchEvent) {
          x = e.touches[0].clientX - rect.left;
          y = e.touches[0].clientY - rect.top;
        }

        this.ctx.lineTo(x, y);
        this.ctx.stroke();
        this.ctx.beginPath();
        this.ctx.moveTo(x, y);
      };

      this.canvas.addEventListener("mousedown", startDrawing);
      this.canvas.addEventListener("mousemove", draw);
      this.canvas.addEventListener("mouseup", stopDrawing);
      this.canvas.addEventListener("mouseout", stopDrawing);

      this.canvas.addEventListener("touchstart", startDrawing);
      this.canvas.addEventListener("touchmove", draw);
      this.canvas.addEventListener("touchend", stopDrawing);
    }, 0);
  }

  save() {
    return this.data;
  }
}
