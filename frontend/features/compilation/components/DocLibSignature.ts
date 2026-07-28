import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibSignature implements BlockTool {
  static readonly feature = {
    id: "DocLibSignature",
    title: "DocLib Signature",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="4b187d15a64b6154"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="11,11 10,8 17,11 16,20 18,17 8,12"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { dataUrl: string; label: string };
  private readOnly: boolean;
  private canvas: HTMLCanvasElement | null = null;
  private drawing = false;
  private ctx: CanvasRenderingContext2D | null = null;

  static get toolbox() {
    return {
      title: "DocLib Signature",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="4b187d15a64b6154"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="11,11 10,8 17,11 16,20 18,17 8,12"/></svg>',
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
      dataUrl: data?.dataUrl || "",
      label: data?.label || "DocLib Button",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-sig-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-sig-styles";
      style.innerHTML = `
        .doclib-sig-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin: 12px 0; }
        .doclib-sig-header { padding: 10px 16px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; }
        .doclib-sig-label { font-size: 13px; font-weight: 600; color: #475569; }
        .doclib-sig-actions { display: flex; gap: 6px; }
        .doclib-sig-btn { padding: 5px 12px; border: 1px solid #e2e8f0; border-radius: 5px; background: #fff; font-size: 12px; cursor: pointer; color: #475569; }
        .doclib-sig-btn:hover { background: #f0f9ff; border-color: #0284c7; color: #0284c7; }
        .doclib-sig-canvas { width: 100%; height: 180px; background: #fff; cursor: crosshair; display: block; touch-action: none; }
        .doclib-sig-canvas.readonly { cursor: default; }
        .doclib-sig-footer { padding: 8px 16px; background: #f8fafc; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private getPos(
    canvas: HTMLCanvasElement,
    e: MouseEvent | TouchEvent,
  ): { x: number; y: number } {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    if (e instanceof TouchEvent) {
      const touch = e.touches[0];
      return {
        x: (touch.clientX - rect.left) * scaleX,
        y: (touch.clientY - rect.top) * scaleY,
      };
    }
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-sig-wrapper");

    const header = document.createElement("div");
    header.classList.add("doclib-sig-header");

    const label = document.createElement("div");
    label.classList.add("doclib-sig-label");
    label.innerText = ` ${this.data.label}`;

    header.appendChild(label);

    const canvas = document.createElement("canvas");
    canvas.classList.add("doclib-sig-canvas");
    canvas.width = 800;
    canvas.height = 180;

    this.canvas = canvas;
    const ctx = canvas.getContext("2d");
    this.ctx = ctx;

    if (this.data.dataUrl && ctx) {
      const img = new Image();
      img.src = this.data.dataUrl;
      img.onload = () => ctx.drawImage(img, 0, 0);
    }

    if (!this.readOnly && ctx) {
      canvas.style.cursor = "crosshair";

      const start = (e: MouseEvent | TouchEvent) => {
        e.preventDefault();
        this.drawing = true;
        ctx.beginPath();
        const pos = this.getPos(canvas, e);
        ctx.moveTo(pos.x, pos.y);
      };

      const draw = (e: MouseEvent | TouchEvent) => {
        if (!this.drawing) return;
        e.preventDefault();
        const pos = this.getPos(canvas, e);
        ctx.lineTo(pos.x, pos.y);
        ctx.strokeStyle = "#0f172a";
        ctx.lineWidth = 2;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.stroke();
      };

      const stop = () => {
        if (!this.drawing) return;
        this.drawing = false;
        this.data.dataUrl = canvas.toDataURL();
      };

      canvas.addEventListener("mousedown", start);
      canvas.addEventListener("mousemove", draw);
      canvas.addEventListener("mouseup", stop);
      canvas.addEventListener("mouseleave", stop);
      canvas.addEventListener("touchstart", start, { passive: false });
      canvas.addEventListener("touchmove", draw, { passive: false });
      canvas.addEventListener("touchend", stop);

      const actions = document.createElement("div");
      actions.classList.add("doclib-sig-actions");

      const clearBtn = document.createElement("button");
      clearBtn.classList.add("doclib-sig-btn");
      clearBtn.innerText = "Clear";
      clearBtn.addEventListener("click", () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        this.data.dataUrl = "";
      });

      const downloadBtn = document.createElement("button");
      downloadBtn.classList.add("doclib-sig-btn");
      downloadBtn.innerText = "Download PNG";
      downloadBtn.addEventListener("click", () => {
        const a = document.createElement("a");
        a.href = canvas.toDataURL("image/png");
        a.download = "signature.png";
        a.click();
      });

      const labelInput = document.createElement("input");
      labelInput.style.cssText =
        "padding:4px 8px;border:1px solid #e2e8f0;border-radius:5px;font-size:12px;outline:none;color:#475569;";
      labelInput.value = this.data.label;
      labelInput.placeholder = "DocLib Input";
      labelInput.addEventListener("input", () => {
        this.data.label = labelInput.value;
        label.innerText = ` ${this.data.label}`;
      });

      actions.appendChild(labelInput);
      actions.appendChild(clearBtn);
      actions.appendChild(downloadBtn);
      header.appendChild(actions);
    } else {
      canvas.classList.add("readonly");
      canvas.style.cursor = "default";
    }

    const footer = document.createElement("div");
    footer.classList.add("doclib-sig-footer");
    footer.innerText = this.readOnly
      ? `${this.data.label}`
      : "Sign with mouse or touch";

    this.wrapper.appendChild(header);
    this.wrapper.appendChild(canvas);
    this.wrapper.appendChild(footer);
  }

  save() {
    if (this.canvas) this.data.dataUrl = this.canvas.toDataURL();
    return this.data;
  }
}
