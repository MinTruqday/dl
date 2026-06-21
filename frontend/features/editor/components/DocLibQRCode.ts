import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibQRCode implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { content: string; size: number };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib QR Code",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect><rect x="14" y="14" width="3" height="3"></rect><line x1="17" y1="14" x2="21" y2="14"></line><line x1="21" y1="17" x2="21" y2="21"></line><line x1="17" y1="21" x2="21" y2="21"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      content: data?.content || "https://example.com",
      size: data?.size || 200,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-qrcode-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-qrcode-styles";
      style.innerHTML = `
        .doclib-qr-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; background: #fff; margin: 12px 0; display: flex; gap: 24px; align-items: flex-start; flex-wrap: wrap; }
        .doclib-qr-preview { display: flex; flex-direction: column; align-items: center; gap: 12px; }
        .doclib-qr-canvas { border: 1px solid #e2e8f0; border-radius: 4px; }
        .doclib-qr-controls { flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: 12px; }
        .doclib-qr-input { width: 100%; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; outline: none; box-sizing: border-box; }
        .doclib-qr-label { font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 4px; display: block; }
        .doclib-qr-slider { width: 100%; accent-color: #0f172a; }
        .doclib-qr-btn { padding: 8px 16px; background: #0f172a; color: #fff; border: none; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; }
        .doclib-qr-btn:hover { background: #1e293b; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private loadQRLib(): Promise<void> {
    return new Promise((resolve) => {
      if ((window as any).QRCode) { resolve(); return; }
      if (document.getElementById("qrcode-script")) {
        window.addEventListener("qrcode-loaded", () => resolve(), { once: true });
        return;
      }
      const script = document.createElement("script");
      script.id = "qrcode-script";
      script.src = "https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js";
      script.onload = () => { window.dispatchEvent(new Event("qrcode-loaded")); resolve(); };
      document.head.appendChild(script);
    });
  }

  private async renderQR(content: string, size: number, container: HTMLElement) {
    container.innerHTML = "";
    await this.loadQRLib();
    new (window as any).QRCode(container, {
      text: content || " ",
      width: size,
      height: size,
      colorDark: "#0f172a",
      colorLight: "#ffffff",
      correctLevel: (window as any).QRCode.CorrectLevel.H,
    });
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-qr-wrapper");

    const preview = document.createElement("div");
    preview.classList.add("doclib-qr-preview");

    const canvas = document.createElement("div");
    canvas.classList.add("doclib-qr-canvas");
    canvas.style.width = `${this.data.size}px`;
    canvas.style.height = `${this.data.size}px`;

    const sizeLabel = document.createElement("span");
    sizeLabel.style.fontSize = "12px";
    sizeLabel.style.color = "#64748b";
    sizeLabel.innerText = `${this.data.size} x ${this.data.size} px`;

    preview.appendChild(canvas);
    preview.appendChild(sizeLabel);

    if (this.readOnly) {
      this.wrapper.appendChild(preview);
      this.renderQR(this.data.content, this.data.size, canvas);
      return;
    }

    const controls = document.createElement("div");
    controls.classList.add("doclib-qr-controls");

    const urlLabel = document.createElement("label");
    urlLabel.classList.add("doclib-qr-label");
    urlLabel.innerText = "Content / URL";

    const input = document.createElement("input");
    input.classList.add("doclib-qr-input");
    input.value = this.data.content;
    input.placeholder = "https://example.com";

    let timeout: ReturnType<typeof setTimeout>;
    input.addEventListener("input", () => {
      this.data.content = input.value;
      clearTimeout(timeout);
      timeout = setTimeout(() => this.renderQR(this.data.content, this.data.size, canvas), 500);
    });

    const sizeCtrlLabel = document.createElement("label");
    sizeCtrlLabel.classList.add("doclib-qr-label");
    sizeCtrlLabel.innerText = `Size: ${this.data.size}px`;

    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = "100";
    slider.max = "400";
    slider.value = `${this.data.size}`;
    slider.classList.add("doclib-qr-slider");
    slider.addEventListener("input", () => {
      this.data.size = parseInt(slider.value);
      sizeCtrlLabel.innerText = `Size: ${this.data.size}px`;
      sizeLabel.innerText = `${this.data.size} x ${this.data.size} px`;
      canvas.style.width = `${this.data.size}px`;
      canvas.style.height = `${this.data.size}px`;
      clearTimeout(timeout);
      timeout = setTimeout(() => this.renderQR(this.data.content, this.data.size, canvas), 300);
    });

    const downloadBtn = document.createElement("button");
    downloadBtn.classList.add("doclib-qr-btn");
    downloadBtn.innerText = "Download PNG";
    downloadBtn.addEventListener("click", () => {
      const img = canvas.querySelector("img") as HTMLImageElement;
      if (img) {
        const a = document.createElement("a");
        a.href = img.src;
        a.download = "qrcode.png";
        a.click();
      }
    });

    controls.appendChild(urlLabel);
    controls.appendChild(input);
    controls.appendChild(sizeCtrlLabel);
    controls.appendChild(slider);
    controls.appendChild(downloadBtn);

    this.wrapper.appendChild(preview);
    this.wrapper.appendChild(controls);

    this.renderQR(this.data.content, this.data.size, canvas);
  }

  save() {
    return this.data;
  }
}
