import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibBarcode implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Barcode",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5v14"></path><path d="M8 5v14"></path><path d="M12 5v14"></path><path d="M17 5v14"></path><path d="M21 5v14"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      code: data?.code || "DOCLIB12345",
      type: data?.type || "CODE128",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-barcode { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; margin: 16px auto; max-width: 400px; font-family: monospace; }
      .doclib-barcode-img { width: 100%; height: 80px; background: repeating-linear-gradient(90deg, #000, #000 2px, #fff 2px, #fff 4px, #000 4px, #000 8px, #fff 8px, #fff 10px); opacity: 0.8; margin-bottom: 8px; }
      .doclib-barcode-text { font-size: 16px; letter-spacing: 4px; color: #000; font-weight: bold; outline: none; text-align: center; }
      .doclib-barcode-text:empty:before { content: "DOCLIB_BARCODE"; color: #94a3b8; font-style: italic; letter-spacing: normal; }
      .doclib-barcode-type { margin-top: 16px; font-size: 10px; color: #94a3b8; font-family: sans-serif; text-transform: uppercase; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-barcode");

    // Simulated barcode image using repeating linear gradient pattern
    const img = document.createElement("div");
    img.classList.add("doclib-barcode-img");
    container.appendChild(img);

    const text = document.createElement("div");
    text.classList.add("doclib-barcode-text");
    text.innerText = this.data.code;
    if (!this.readOnly) {
      text.contentEditable = "true";
      text.addEventListener("input", () => {
        this.data.code = text.innerText;
        // Generate pseudo random pattern based on length
        const len = this.data.code.length || 5;
        img.style.background = `repeating-linear-gradient(90deg, #000, #000 ${len%3+1}px, #fff ${len%3+1}px, #fff ${len%4+2}px, #000 ${len%4+2}px, #000 ${len%5+4}px, #fff ${len%5+4}px, #fff ${len%2+6}px)`;
      });
    }
    container.appendChild(text);

    const type = document.createElement("div");
    type.classList.add("doclib-barcode-type");
    type.innerText = `Type: ${this.data.type}`;
    container.appendChild(type);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
