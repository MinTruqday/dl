import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibWatermark implements BlockTool {
  static readonly feature = {
    id: "DocLibWatermark",
    title: "DocLib Watermark",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="e6caee02a19dba4e"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="13,19 4,6 12,8 20,14 14,19 12,5"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Watermark",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="e6caee02a19dba4e"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="13,19 4,6 12,8 20,14 14,19 12,5"/></svg>',
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
      text: data?.text || "",
      opacity: data?.opacity || 0.1,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-watermark-edit {
        padding: 16px;
        background: #f8fafc;
        border: 1px dashed #cbd5e1;
        border-radius: 8px;
        display: flex;
        gap: 12px;
        align-items: center;
      }
      .doclib-watermark-input {
        flex: 1;
        padding: 8px 12px;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        font-size: 14px;
        outline: none;
      }
      .doclib-watermark-slider {
        width: 100px;
      }
      .doclib-watermark-preview {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
      }
      .doclib-watermark-preview span {
        font-size: 120px;
        font-weight: 900;
        color: #000;
        text-transform: uppercase;
        transform: rotate(-45deg);
        user-select: none;
      }
    `;
    this.wrapper.appendChild(style);

    const applyWatermark = () => {
      let preview = document.getElementById("doclib-global-watermark");
      if (!preview) {
        preview = document.createElement("div");
        preview.id = "doclib-global-watermark";
        preview.classList.add("doclib-watermark-preview");
        document.body.appendChild(preview);
      }
      preview.innerHTML = "";
      if (this.data.text) {
        const span = document.createElement("span");
        span.innerText = this.data.text;
        span.style.opacity = this.data.opacity.toString();
        preview.appendChild(span);
      }
    };

    if (this.readOnly) {
      applyWatermark();
      this.wrapper.style.display = "none";
      return this.wrapper;
    }

    const edit = document.createElement("div");
    edit.classList.add("doclib-watermark-edit");

    const input = document.createElement("input");
    input.classList.add("doclib-watermark-input");
    input.placeholder = "DocLib Text";
    input.value = this.data.text;
    input.addEventListener("input", () => {
      this.data.text = input.value;
      applyWatermark();
    });

    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = "0.05";
    slider.max = "0.5";
    slider.step = "0.05";
    slider.value = this.data.opacity.toString();
    slider.classList.add("doclib-watermark-slider");
    slider.addEventListener("input", () => {
      this.data.opacity = parseFloat(slider.value);
      applyWatermark();
    });

    edit.appendChild(input);
    edit.appendChild(slider);
    this.wrapper.appendChild(edit);

    setTimeout(() => {
      applyWatermark();
    }, 100);

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      text: this.data.text,
      opacity: this.data.opacity,
    };
  }
}
