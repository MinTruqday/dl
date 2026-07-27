import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibSmartArtProcess implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib SmartArt Process",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="9" width="6" height="6"></rect><rect x="15" y="9" width="6" height="6"></rect><line x1="9" y1="12" x2="15" y2="12"></line><polygon points="13 10 15 12 13 14"></polygon></svg>',
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
      .doclib-sap { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 16px; padding: 24px; background: #f8fafc; border-radius: 8px; margin: 16px 0; }
      .doclib-sap-item { display: flex; align-items: center; gap: 16px; }
      .doclib-sap-box { background: #3b82f6; color: #fff; padding: 12px 24px; border-radius: 4px; font-weight: bold; font-family: sans-serif; min-width: 120px; text-align: center; outline: none; position: relative; }
      .doclib-sap-box:empty:before { content: "DocLib Process Step"; color: #bfdbfe; font-weight: normal; }
      .doclib-sap-arrow { color: #94a3b8; font-size: 24px; font-weight: bold; }
      .doclib-sap-del { position: absolute; top: -8px; right: -8px; width: 20px; height: 20px; background: #ef4444; color: #fff; border-radius: 50%; font-size: 10px; display: none; align-items: center; justify-content: center; cursor: pointer; border: none; }
      .doclib-sap-box:hover .doclib-sap-del { display: flex; }
      .doclib-sap-add { width: 40px; height: 40px; border-radius: 50%; border: 2px dashed #94a3b8; color: #94a3b8; background: transparent; font-size: 20px; display: flex; align-items: center; justify-content: center; cursor: pointer; }
      .doclib-sap-add:hover { border-color: #3b82f6; color: #3b82f6; }
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
