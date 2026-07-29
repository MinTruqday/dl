import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibTextBox implements BlockTool {
  static readonly feature = {
    id: "DocLibTextBox",
    title: "Text Box",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a9d8d524c8d9badf"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="20,16 13,6 17,17 20,6 14,19 4,11"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Text Box",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a9d8d524c8d9badf"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="20,16 13,6 17,17 20,6 14,19 4,11"/></svg>',
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
      float: data?.float || "none",
      width: data?.width || "100%",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-textbox-wrapper { clear: both; margin: 16px 0; }
      .doclib-textbox { border: 1px solid #1e293b; background: #fff; padding: 16px; box-shadow: 2px 2px 0px rgba(0,0,0,0.1); font-size: 15px; line-height: 1.6; outline: none; transition: all 0.3s ease; }
      .doclib-textbox:empty::before { content: "DocLib Text"; color: #94a3b8; pointer-events: none; }
      .doclib-textbox-controls { display: flex; gap: 8px; margin-top: 8px; background: #f8fafc; padding: 8px; border-radius: 4px; border: 1px solid #e2e8f0; clear: both; }
      .doclib-textbox-select { padding: 4px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-textbox-wrapper");

    const box = document.createElement("div");
    box.classList.add("doclib-textbox");
    box.innerText = this.data.text;

    const applyStyle = () => {
      box.style.float = this.data.float;
      box.style.width = this.data.width;
      if (this.data.float !== "none") {
        box.style.margin =
          this.data.float === "left" ? "0 16px 16px 0" : "0 0 16px 16px";
      } else {
        box.style.margin = "0";
      }
    };
    applyStyle();

    if (!this.readOnly) {
      box.contentEditable = "true";
      box.addEventListener("input", () => {
        this.data.text = box.innerText;
      });
    }

    container.appendChild(box);
    this.wrapper.appendChild(container);

    if (!this.readOnly) {
      const controls = document.createElement("div");
      controls.classList.add("doclib-textbox-controls");

      const floatSelect = document.createElement("select");
      floatSelect.classList.add("doclib-textbox-select");
      ["none", "left", "right"].forEach((f) => {
        const opt = document.createElement("option");
        opt.value = f;
        opt.text = `Float ${f}`;
        opt.selected = this.data.float === f;
        floatSelect.appendChild(opt);
      });
      floatSelect.addEventListener("change", () => {
        this.data.float = floatSelect.value;
        applyStyle();
      });

      const widthSelect = document.createElement("select");
      widthSelect.classList.add("doclib-textbox-select");
      ["100%", "75%", "50%", "33%", "25%"].forEach((w) => {
        const opt = document.createElement("option");
        opt.value = w;
        opt.text = `Width ${w}`;
        opt.selected = this.data.width === w;
        widthSelect.appendChild(opt);
      });
      widthSelect.addEventListener("change", () => {
        this.data.width = widthSelect.value;
        applyStyle();
      });

      controls.appendChild(floatSelect);
      controls.appendChild(widthSelect);
      this.wrapper.appendChild(controls);
    }

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      text: this.data.text,
      float: this.data.float,
      width: this.data.width,
    };
  }
}
