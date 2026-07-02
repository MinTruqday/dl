import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibIframeEmbed implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { url: string; height: number };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Embed",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>',
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
      height: data.height || 400,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-iframe-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-iframe-styles";
      style.innerHTML = `
            .doclib-if-wrapper { margin: 16px 0; border-radius: 8px; overflow: hidden; background: #f8fafc; border: 1px solid #e2e8f0; }
            .doclib-if-iframe { width: 100%; border: none; display: block; }
            .doclib-if-input-wrapper { display: flex; flex-direction: column; gap: 8px; padding: 24px; align-items: center; text-align: center; }
            .doclib-if-input { width: 100%; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px 12px; outline: none; }
            .doclib-if-input:focus { border-color: #3b82f6; }
            .doclib-if-btn { background: #3b82f6; color: white; border: none; padding: 10px 24px; border-radius: 6px; font-weight: 500; cursor: pointer; }
            .doclib-if-btn:hover { background: #2563eb; }
            .doclib-if-controls { padding: 8px 16px; background: #f1f5f9; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }
            .doclib-if-height-btn { background: #fff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 12px; }
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
    container.classList.add("doclib-if-wrapper");

    if (this.data.url) {
      const iframe = document.createElement("iframe");
      iframe.classList.add("doclib-if-iframe");
      iframe.src = this.data.url;
      iframe.style.height = `${this.data.height}px`;
      iframe.allow =
        "accelerometer; ambient-light-sensor; camera; encrypted-media; geolocation; gyroscope; hid; microphone; midi; payment; usb; vr; xr-spatial-tracking";
      iframe.sandbox.add(
        "allow-forms",
        "allow-modals",
        "allow-popups",
        "allow-presentation",
        "allow-same-origin",
        "allow-scripts",
      );

      container.appendChild(iframe);

      if (!this.readOnly) {
        const controls = document.createElement("div");
        controls.classList.add("doclib-if-controls");

        const heightBtn = document.createElement("button");
        heightBtn.classList.add("doclib-if-height-btn");
        heightBtn.innerText = `Height: ${this.data.height}px`;
        heightBtn.addEventListener("click", () => {
          const h = prompt("Enter height (px):", this.data.height.toString());
          if (h && !isNaN(parseInt(h))) {
            this.data.height = parseInt(h);
            this.buildUI();
          }
        });

        const rmBtn = document.createElement("button");
        rmBtn.classList.add("doclib-if-height-btn");
        rmBtn.style.color = "#ef4444";
        rmBtn.innerText = "Change Link";
        rmBtn.addEventListener("click", () => {
          this.data.url = "";
          this.buildUI();
        });

        controls.appendChild(heightBtn);
        controls.appendChild(rmBtn);
        container.appendChild(controls);
      }
    } else {
      const inputWrap = document.createElement("div");
      inputWrap.classList.add("doclib-if-input-wrapper");

      const icon = document.createElement("div");
      icon.innerHTML =
        '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>';

      const input = document.createElement("input");
      input.classList.add("doclib-if-input");
      input.placeholder = "DocLib URL";

      const btn = document.createElement("button");
      btn.classList.add("doclib-if-btn");
      btn.innerText = "Embed (Embed)";

      const submit = () => {
        if (input.value) {
          this.data.url = input.value;
          this.buildUI();
        }
      };

      btn.addEventListener("click", submit);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") submit();
      });

      inputWrap.appendChild(icon);
      inputWrap.appendChild(input);
      inputWrap.appendChild(btn);
      container.appendChild(inputWrap);
    }

    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
