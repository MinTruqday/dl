import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibEquationArray implements BlockTool {
  static readonly feature = {
    id: "DocLibEquationArray",
    title: "Equation Array",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="11e7c3b765e78075"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="4,14 12,17 20,14 13,19 7,10 9,8"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Equation Array",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="11e7c3b765e78075"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="4,14 12,17 20,14 13,19 7,10 9,8"/></svg>',
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
      equations:
        data?.equations && data.equations.length > 0
          ? data.equations
          : ["x + y = z", "a^2 + b^2 = c^2"],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-eqarray { font-family: "Cambria Math", "Times New Roman", serif; font-size: 18px; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fdfdfd; margin: 16px auto; max-width: 500px; display: flex; flex-direction: column; gap: 8px; align-items: center; }
      .doclib-eqarray-row { display: flex; align-items: center; gap: 12px; width: 100%; justify-content: center; position: relative; }
      .doclib-eqarray-text { outline: none; min-width: 100px; text-align: center; font-style: italic; border-bottom: 1px dashed transparent; transition: 0.3s; }
      .doclib-eqarray-text:focus { border-bottom-color: #3b82f6; }
      .doclib-eqarray-text:empty:before { content: "DocLib Equation"; color: #94a3b8; font-style: normal; font-family: sans-serif; font-size: 14px; }
      .doclib-eqarray-del { position: absolute; right: 0; color: #ef4444; font-size: 12px; border: none; background: transparent; cursor: pointer; display: none; font-family: sans-serif; }
      .doclib-eqarray-row:hover .doclib-eqarray-del { display: block; }
      .doclib-eqarray-add { font-family: sans-serif; font-size: 12px; color: #3b82f6; border: 1px dashed #3b82f6; background: transparent; border-radius: 4px; padding: 6px 12px; cursor: pointer; margin-top: 16px; }
      .doclib-eqarray-add:hover { background: #eff6ff; }
      .doclib-eqarray-bracket { font-size: 40px; font-weight: 100; color: #1e293b; display: flex; align-items: center; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-eqarray");

    const inner = document.createElement("div");
    inner.style.display = "flex";
    inner.style.alignItems = "center";
    inner.style.gap = "16px";
    inner.style.width = "100%";

    const lBracket = document.createElement("div");
    lBracket.classList.add("doclib-eqarray-bracket");
    lBracket.innerText = "{";
    inner.appendChild(lBracket);

    const list = document.createElement("div");
    list.style.flex = "1";
    list.style.display = "flex";
    list.style.flexDirection = "column";
    list.style.gap = "8px";
    inner.appendChild(list);

    const renderList = () => {
      list.innerHTML = "";
      this.data.equations.forEach((eq: string, i: number) => {
        const row = document.createElement("div");
        row.classList.add("doclib-eqarray-row");

        const text = document.createElement("div");
        text.classList.add("doclib-eqarray-text");
        text.innerText = eq;

        if (!this.readOnly) {
          text.contentEditable = "true";
          text.addEventListener("input", () => {
            this.data.equations[i] = text.innerText;
          });

          const del = document.createElement("button");
          del.classList.add("doclib-eqarray-del");
          del.innerText = "x";
          del.addEventListener("click", () => {
            this.data.equations.splice(i, 1);
            renderList();
          });
          row.appendChild(text);
          row.appendChild(del);
        } else {
          row.appendChild(text);
        }

        list.appendChild(row);
      });

      const h = Math.max(40, this.data.equations.length * 30);
      lBracket.style.fontSize = `${h}px`;
    };

    renderList();

    container.appendChild(inner);

    if (!this.readOnly) {
      const add = document.createElement("button");
      add.classList.add("doclib-eqarray-add");
      add.innerText = "+ Add Equation";
      add.addEventListener("click", () => {
        this.data.equations.push("DocLib New Eq");
        renderList();
      });
      container.appendChild(add);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
