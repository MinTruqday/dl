import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibBeforeAfterImage implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Before/After Image",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3H5a2 2 0 0 0-2 2v4M15 3h4a2 2 0 0 1 2 2v4M9 21H5a2 2 0 0 1-2-2v-4M15 21h4a2 2 0 0 0 2-2v-4M12 3v18"></path></svg>',
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
      beforeUrl: data?.beforeUrl || "",
      afterUrl: data?.afterUrl || "",
      position: data?.position || 50,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-ba { position: relative; width: 100%; max-width: 600px; height: 350px; margin: 16px auto; overflow: hidden; border-radius: 8px; background: #e2e8f0; border: 1px solid #cbd5e1; }
      .doclib-ba-img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
      .doclib-ba-before { clip-path: inset(0 50% 0 0); z-index: 2; }
      .doclib-ba-slider { position: absolute; top: 0; bottom: 0; left: 50%; width: 4px; background: #fff; z-index: 3; cursor: ew-resize; transform: translateX(-50%); box-shadow: 0 0 4px rgba(0,0,0,0.5); }
      .doclib-ba-slider::after { content: "↔"; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 32px; height: 32px; background: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: bold; color: #334155; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
      .doclib-ba-inputs { display: flex; gap: 8px; margin-bottom: 8px; max-width: 600px; margin-left: auto; margin-right: auto; }
      .doclib-ba-input { flex: 1; padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 13px; }
      .doclib-ba-placeholder { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-family: sans-serif; font-size: 14px; }
    `;
    this.wrapper.appendChild(style);

    if (!this.readOnly) {
      const inputs = document.createElement("div");
      inputs.classList.add("doclib-ba-inputs");

      const bInput = document.createElement("input");
      bInput.classList.add("doclib-ba-input");
      bInput.placeholder = "DocLib Before Image URL";
      bInput.value = this.data.beforeUrl;

      const aInput = document.createElement("input");
      aInput.classList.add("doclib-ba-input");
      aInput.placeholder = "DocLib After Image URL";
      aInput.value = this.data.afterUrl;

      inputs.appendChild(bInput);
      inputs.appendChild(aInput);
      this.wrapper.appendChild(inputs);

      const updateImages = () => {
        this.data.beforeUrl = bInput.value;
        this.data.afterUrl = aInput.value;
        this.buildUI();
      };
      bInput.addEventListener("input", updateImages);
      aInput.addEventListener("input", updateImages);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    let container = this.wrapper.querySelector(".doclib-ba") as HTMLElement;
    if (!container) {
      container = document.createElement("div");
      container.classList.add("doclib-ba");
      this.wrapper.appendChild(container);
    } else {
      container.innerHTML = "";
    }

    if (!this.data.beforeUrl && !this.data.afterUrl) {
      const p = document.createElement("div");
      p.classList.add("doclib-ba-placeholder");
      p.innerText = "DocLib Before/After Image Preview";
      container.appendChild(p);
      return;
    }

    const afterImg = document.createElement("img");
    afterImg.classList.add("doclib-ba-img");
    afterImg.src = this.data.afterUrl;

    const beforeImg = document.createElement("img");
    beforeImg.classList.add("doclib-ba-img", "doclib-ba-before");
    beforeImg.src = this.data.beforeUrl;
    beforeImg.style.clipPath = `inset(0 ${100 - this.data.position}% 0 0)`;

    const slider = document.createElement("div");
    slider.classList.add("doclib-ba-slider");
    slider.style.left = `${this.data.position}%`;

    container.appendChild(afterImg);
    container.appendChild(beforeImg);
    container.appendChild(slider);

    let isDragging = false;
    const onMove = (e: any) => {
      if (!isDragging) return;
      const rect = container.getBoundingClientRect();
      const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      this.data.position = (x / rect.width) * 100;
      slider.style.left = `${this.data.position}%`;
      beforeImg.style.clipPath = `inset(0 ${100 - this.data.position}% 0 0)`;
    };

    slider.addEventListener("mousedown", () => {
      isDragging = true;
    });
    document.addEventListener("mouseup", () => {
      isDragging = false;
    });
    document.addEventListener("mousemove", onMove);
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
