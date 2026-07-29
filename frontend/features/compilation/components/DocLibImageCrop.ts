import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibImageCrop implements BlockTool {
  static readonly feature = {
    id: "DocLibImageCrop",
    title: "DocLib ImageCrop",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="44c11cdf59815473"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="4,10 15,6 8,14 20,17 19,7 6,9"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    url: string;
    scale: number;
    x: number;
    y: number;
    caption: string;
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Crop Image",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="44c11cdf59815473"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="4,10 15,6 8,14 20,17 19,7 6,9"/></svg>',
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
      url: data.url || "",
      scale: data.scale || 100,
      x: data.x || 50,
      y: data.y || 50,
      caption: data.caption || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-image-crop-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-image-crop-styles";
      style.innerHTML = `
            .doclib-ic-wrapper { margin: 16px 0; text-align: center; }
            .doclib-ic-container { position: relative; width: 100%; aspect-ratio: 16/9; overflow: hidden; border-radius: 12px; background: #f1f5f9; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
            .doclib-ic-img { width: 100%; height: 100%; object-fit: cover; }
            .doclib-ic-controls { padding: 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 12px; display: grid; gap: 12px; grid-template-columns: 1fr 1fr 1fr; }
            .doclib-ic-control-group { display: flex; flex-direction: column; gap: 4px; text-align: left; }
            .doclib-ic-label { font-size: 12px; font-weight: 600; color: #475569; text-transform: uppercase; }
            .doclib-ic-slider { width: 100%; accent-color: #3b82f6; }
            .doclib-ic-caption { outline: none; margin-top: 8px; color: #64748b; font-size: 0.9em; }
            .doclib-ic-caption:empty::before { content: 'Enter image caption'; color: #cbd5e1; }
        `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const outer = document.createElement("div");
    outer.classList.add("doclib-ic-wrapper");

    if (this.data.url) {
      const container = document.createElement("div");
      container.classList.add("doclib-ic-container");

      const img = document.createElement("img");
      img.classList.add("doclib-ic-img");
      img.src = this.data.url;

      img.style.objectPosition = `${this.data.x}% ${this.data.y}%`;
      img.style.transform = `scale(${this.data.scale / 100})`;

      container.appendChild(img);
      outer.appendChild(container);

      if (!this.readOnly) {
        const controls = document.createElement("div");
        controls.classList.add("doclib-ic-controls");

        const createSlider = (
          labelStr: string,
          min: number,
          max: number,
          value: number,
          onChange: (val: number) => void,
        ) => {
          const group = document.createElement("div");
          group.classList.add("doclib-ic-control-group");
          const label = document.createElement("label");
          label.classList.add("doclib-ic-label");
          label.innerText = labelStr;
          const input = document.createElement("input");
          input.type = "range";
          input.min = min.toString();
          input.max = max.toString();
          input.value = value.toString();
          input.classList.add("doclib-ic-slider");
          input.addEventListener("input", () => {
            onChange(parseInt(input.value));
            img.style.objectPosition = `${this.data.x}% ${this.data.y}%`;
            img.style.transform = `scale(${this.data.scale / 100})`;
          });
          group.appendChild(label);
          group.appendChild(input);
          return group;
        };

        controls.appendChild(
          createSlider(
            "Zoom",
            100,
            300,
            this.data.scale,
            (v) => (this.data.scale = v),
          ),
        );
        controls.appendChild(
          createSlider(
            "Horizontal Align (X)",
            0,
            100,
            this.data.x,
            (v) => (this.data.x = v),
          ),
        );
        controls.appendChild(
          createSlider(
            "Vertical Align (Y)",
            0,
            100,
            this.data.y,
            (v) => (this.data.y = v),
          ),
        );

        outer.appendChild(controls);
      }

      const caption = document.createElement("div");
      caption.classList.add("doclib-ic-caption");
      caption.contentEditable = "true";
      caption.innerHTML = this.data.caption;
      caption.addEventListener(
        "input",
        () => (this.data.caption = caption.innerHTML),
      );
      outer.appendChild(caption);
    } else {
      const uploader = document.createElement("div");
      uploader.style.padding = "32px";
      uploader.style.background = "#f8fafc";
      uploader.style.border = "2px dashed #cbd5e1";
      uploader.style.borderRadius = "8px";
      uploader.style.display = "flex";
      uploader.style.flexDirection = "column";
      uploader.style.gap = "8px";

      const input = document.createElement("input");
      input.classList.add(this.api.styles.input);
      input.placeholder = "DocLib URL";

      const btn = document.createElement("button");
      btn.classList.add(this.api.styles.button);
      btn.innerText = "Continue";
      btn.addEventListener("click", () => {
        if (input.value) {
          this.data.url = input.value;
          this.buildUI();
        }
      });

      uploader.appendChild(input);
      uploader.appendChild(btn);
      outer.appendChild(uploader);
    }

    this.wrapper.appendChild(outer);
  }

  save() {
    return this.data;
  }
}
