import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibFormSpinButton implements BlockTool {
  static readonly feature = {
    id: "DocLibFormSpinButton",
    title: "DocLib Form Spin Button",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="0d2967285d4704db"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="17,11 5,10 12,7 8,19 19,15 8,17"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Form Spin Button",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="0d2967285d4704db"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="17,11 5,10 12,7 8,19 19,15 8,17"/></svg>',
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
      label: data?.label || "",
      value: data?.value || 0,
      min: data?.min || 0,
      max: data?.max || 100,
      step: data?.step || 1,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-spin { font-family: sans-serif; display: flex; align-items: center; gap: 16px; padding: 12px 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; margin: 16px 0; max-width: 400px; }
      .doclib-spin-label { font-size: 14px; font-weight: bold; color: #1e293b; outline: none; flex: 1; }
      .doclib-spin-label:empty:before { content: "DocLib Spin Setting"; color: #94a3b8; font-weight: normal; }
      .doclib-spin-ctrl { display: flex; align-items: center; border: 1px solid #cbd5e1; border-radius: 4px; overflow: hidden; }
      .doclib-spin-btn { width: 32px; height: 32px; background: #f8fafc; border: none; cursor: pointer; font-size: 16px; font-weight: bold; color: #475569; display: flex; align-items: center; justify-content: center; }
      .doclib-spin-btn:hover { background: #e2e8f0; }
      .doclib-spin-val { width: 48px; height: 32px; border: none; border-left: 1px solid #cbd5e1; border-right: 1px solid #cbd5e1; text-align: center; font-size: 14px; font-weight: bold; outline: none; -moz-appearance: textfield; }
      .doclib-spin-val::-webkit-outer-spin-button, .doclib-spin-val::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-spin");

    const label = document.createElement("div");
    label.classList.add("doclib-spin-label");
    label.innerText = this.data.label;
    if (!this.readOnly) {
      label.contentEditable = "true";
      label.addEventListener("input", () => {
        this.data.label = label.innerText;
      });
    }
    container.appendChild(label);

    const ctrl = document.createElement("div");
    ctrl.classList.add("doclib-spin-ctrl");

    const decBtn = document.createElement("button");
    decBtn.classList.add("doclib-spin-btn");
    decBtn.innerText = "-";

    const input = document.createElement("input");
    input.type = "number";
    input.classList.add("doclib-spin-val");
    input.value = this.data.value;
    input.min = this.data.min;
    input.max = this.data.max;
    input.step = this.data.step;
    if (this.readOnly) input.disabled = true;

    const incBtn = document.createElement("button");
    incBtn.classList.add("doclib-spin-btn");
    incBtn.innerText = "+";

    if (!this.readOnly) {
      const updateVal = (newVal: number) => {
        if (newVal < this.data.min) newVal = this.data.min;
        if (newVal > this.data.max) newVal = this.data.max;
        this.data.value = newVal;
        input.value = this.data.value.toString();
      };
      decBtn.addEventListener("click", () =>
        updateVal(Number(this.data.value) - Number(this.data.step)),
      );
      incBtn.addEventListener("click", () =>
        updateVal(Number(this.data.value) + Number(this.data.step)),
      );
      input.addEventListener("change", () => updateVal(Number(input.value)));
    }

    ctrl.appendChild(decBtn);
    ctrl.appendChild(input);
    ctrl.appendChild(incBtn);
    container.appendChild(ctrl);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
