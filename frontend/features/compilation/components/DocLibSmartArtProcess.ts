import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibSmartArtProcess implements BlockTool {
  static readonly feature = {
    id: "DocLibSmartArtProcess",
    title: "DocLib SmartArtProcess",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="d695e65339eba8c2"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="14,17 13,19 10,18 19,11 20,16 14,6"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib SmartArt Process",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="d695e65339eba8c2"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="14,17 13,19 10,18 19,11 20,16 14,6"/></svg>',
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
      steps:
        data?.steps && data.steps.length > 0
          ? data.steps
          : ["DocLib Step 1", "DocLib Step 2", "DocLib Step 3"],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-sap { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 16px; padding: 24px; background: hsl(var(--surface-raised)); border-radius: 8px; margin: 16px 0; }
      .doclib-sap-item { display: flex; align-items: center; gap: 16px; }
      .doclib-sap-box { background: hsl(var(--brand)); color: hsl(var(--surface)); padding: 12px 24px; border-radius: 4px; font-weight: bold; font-family: sans-serif; min-width: 120px; text-align: center; outline: none; position: relative; }
      .doclib-sap-box:empty:before { content: "DocLib Process Step"; color: hsl(var(--brand-soft)); font-weight: normal; }
      .doclib-sap-arrow { color: hsl(var(--ink-faint)); font-size: 24px; font-weight: bold; }
      .doclib-sap-del { position: absolute; top: -8px; right: -8px; width: 20px; height: 20px; background: hsl(var(--danger)); color: hsl(var(--surface)); border-radius: 50%; font-size: 10px; display: none; align-items: center; justify-content: center; cursor: pointer; border: none; }
      .doclib-sap-box:hover .doclib-sap-del { display: flex; }
      .doclib-sap-add { width: 40px; height: 40px; border-radius: 50%; border: 2px dashed hsl(var(--ink-faint)); color: hsl(var(--ink-faint)); background: transparent; font-size: 20px; display: flex; align-items: center; justify-content: center; cursor: pointer; }
      .doclib-sap-add:hover { border-color: hsl(var(--brand)); color: hsl(var(--brand)); }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-sap");

    const renderSteps = () => {
      container.innerHTML = "";
      this.data.steps.forEach((step: string, i: number) => {
        const itemWrap = document.createElement("div");
        itemWrap.classList.add("doclib-sap-item");

        const box = document.createElement("div");
        box.classList.add("doclib-sap-box");
        box.innerText = step;

        if (!this.readOnly) {
          box.contentEditable = "true";
          box.addEventListener("input", () => {
            this.data.steps[i] = box.innerText;
          });

          const del = document.createElement("button");
          del.classList.add("doclib-sap-del");
          del.innerText = "x";
          del.addEventListener("click", () => {
            this.data.steps.splice(i, 1);
            renderSteps();
          });
          box.appendChild(del);
        }
        itemWrap.appendChild(box);

        if (i < this.data.steps.length - 1) {
          const arrow = document.createElement("div");
          arrow.classList.add("doclib-sap-arrow");
          arrow.innerHTML = "->";
          itemWrap.appendChild(arrow);
        }

        container.appendChild(itemWrap);
      });

      if (!this.readOnly) {
        const addBtn = document.createElement("button");
        addBtn.classList.add("doclib-sap-add");
        addBtn.innerText = "+";
        addBtn.addEventListener("click", () => {
          this.data.steps.push("DocLib New Step");
          renderSteps();
        });
        container.appendChild(addBtn);
      }
    };

    renderSteps();

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
