import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibWatermarkImage implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Watermark Image",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/><path d="M4 4l16 16"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      url: data?.url || "",
      opacity: data?.opacity || "",
      scale: data?.scale || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-wmi { position: relative; margin: 16px 0; min-height: 100px; border: 1px dashed #cbd5e1; display: flex; align-items: center; justify-content: center; background: #f8fafc; overflow: hidden; border-radius: 8px; }
      .doclib-wmi-img { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); pointer-events: none; z-index: 0; }
      .doclib-wmi-edit { z-index: 10; display: flex; gap: 8px; background: rgba(255,255,255,0.9); padding: 12px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; flex-wrap: wrap; justify-content: center; width: 80%; }
      .doclib-wmi-input { padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; flex: 1; min-width: 120px; }
      .doclib-wmi-select { padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-wmi");

    const img = document.createElement("img");
    img.classList.add("doclib-wmi-img");
    
    const applyImage = () => {
      if (this.data.url) {
        img.src = this.data.url;
        img.style.opacity = this.data.opacity;
        img.style.width = this.data.scale;
        img.style.display = "block";
        
        const editorRoot = document.querySelector(".codex-editor") as HTMLElement;
        if (editorRoot) {
          editorRoot.style.backgroundImage = `url(${this.data.url})`;
          editorRoot.style.backgroundPosition = "center";
          editorRoot.style.backgroundRepeat = "no-repeat";
          editorRoot.style.backgroundSize = "contain";
          editorRoot.style.backgroundAttachment = "fixed";
          editorRoot.style.opacity = "1"; 
        }
      } else {
        img.style.display = "none";
      }
    };
    applyImage();
    container.appendChild(img);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-wmi-edit");

      const urlInput = document.createElement("input");
      urlInput.classList.add("doclib-wmi-input");
      urlInput.placeholder = "DocLib URL";
      urlInput.value = this.data.url;
      urlInput.addEventListener("input", () => { this.data.url = urlInput.value; applyImage(); });

      const opSelect = document.createElement("select");
      opSelect.classList.add("doclib-wmi-select");
      ["0.1", "0.2", "0.3", "0.5", "0.8", "1.0"].forEach(v => {
        const opt = document.createElement("option");
        opt.value = v;
        opt.text = `Opacity ${v}`;
        opt.selected = this.data.opacity === v;
        opSelect.appendChild(opt);
      });
      opSelect.addEventListener("change", () => { this.data.opacity = opSelect.value; applyImage(); });

      const scSelect = document.createElement("select");
      scSelect.classList.add("doclib-wmi-select");
      ["50%", "100%", "150%", "200%"].forEach(v => {
        const opt = document.createElement("option");
        opt.value = v;
        opt.text = `Scale ${v}`;
        opt.selected = this.data.scale === v;
        scSelect.appendChild(opt);
      });
      scSelect.addEventListener("change", () => { this.data.scale = scSelect.value; applyImage(); });

      edit.appendChild(urlInput);
      edit.appendChild(opSelect);
      edit.appendChild(scSelect);
      container.appendChild(edit);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      url: this.data.url,
      opacity: this.data.opacity,
      scale: this.data.scale,
    };
  }
}
