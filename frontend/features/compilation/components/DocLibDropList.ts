import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDropList implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Drop List",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"></path></svg>',
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
      options:
        data?.options && data.options.length > 0
          ? data.options
          : ["DocLib Option 1", "DocLib Option 2"],
      selected: data?.selected || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-droplist { font-family: sans-serif; display: flex; flex-direction: column; gap: 8px; margin: 16px 0; max-width: 400px; }
      .doclib-dl-label { font-size: 14px; font-weight: bold; color: #1e293b; outline: none; }
      .doclib-dl-label:empty:before { content: "DocLib Dropdown Field"; color: #94a3b8; font-weight: normal; }
      .doclib-dl-select { padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 14px; outline: none; background: #fff; cursor: pointer; width: 100%; appearance: auto; }
      .doclib-dl-select:focus { border-color: #3b82f6; }
      .doclib-dl-config { margin-top: 8px; padding: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; display: flex; flex-direction: column; gap: 8px; }
      .doclib-dl-opt-row { display: flex; align-items: center; gap: 8px; }
      .doclib-dl-opt-input { flex: 1; padding: 6px 8px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 13px; outline: none; }
      .doclib-dl-del { font-size: 12px; color: #ef4444; border: none; background: none; cursor: pointer; font-weight: bold; }
      .doclib-dl-add { padding: 6px; font-size: 12px; text-align: center; color: #3b82f6; border: 1px dashed #cbd5e1; border-radius: 4px; cursor: pointer; background: #fff; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-droplist");

    const label = document.createElement("div");
    label.classList.add("doclib-dl-label");
    label.innerText = this.data.label;
    if (!this.readOnly) {
      label.contentEditable = "true";
      label.addEventListener("input", () => {
        this.data.label = label.innerText;
      });
    }
    container.appendChild(label);

    const select = document.createElement("select");
    select.classList.add("doclib-dl-select");
    if (this.readOnly) select.disabled = true;

    const buildOptions = () => {
      select.innerHTML = "";
      const defaultOpt = document.createElement("option");
      defaultOpt.value = "";
      defaultOpt.innerText = "DocLib Select...";
      defaultOpt.disabled = true;
      if (!this.data.selected) defaultOpt.selected = true;
      select.appendChild(defaultOpt);

      this.data.options.forEach((opt: string) => {
        const option = document.createElement("option");
        option.value = opt;
        option.innerText = opt;
        if (this.data.selected === opt) option.selected = true;
        select.appendChild(option);
      });
    };

    buildOptions();

    if (!this.readOnly) {
      select.addEventListener("change", () => {
        this.data.selected = select.value;
      });
    }
    container.appendChild(select);

    if (!this.readOnly) {
      const config = document.createElement("div");
      config.classList.add("doclib-dl-config");

      const renderConfig = () => {
        config.innerHTML = "";
        const title = document.createElement("div");
        title.innerText = "Options Editor";
        title.style.fontSize = "12px";
        title.style.fontWeight = "bold";
        title.style.color = "#64748b";
        config.appendChild(title);

        this.data.options.forEach((opt: string, i: number) => {
          const row = document.createElement("div");
          row.classList.add("doclib-dl-opt-row");

          const inp = document.createElement("input");
          inp.classList.add("doclib-dl-opt-input");
          inp.value = opt;
          inp.addEventListener("change", () => {
            this.data.options[i] = inp.value;
            buildOptions();
          });

          const del = document.createElement("button");
          del.classList.add("doclib-dl-del");
          del.innerText = "✕";
          del.addEventListener("click", () => {
            if (this.data.selected === this.data.options[i])
              this.data.selected = "";
            this.data.options.splice(i, 1);
            renderConfig();
            buildOptions();
          });

          row.appendChild(inp);
          row.appendChild(del);
          config.appendChild(row);
        });

        const add = document.createElement("div");
        add.classList.add("doclib-dl-add");
        add.innerText = "+ Add Option";
        add.addEventListener("click", () => {
          this.data.options.push("DocLib New Option");
          renderConfig();
          buildOptions();
        });
        config.appendChild(add);
      };
      renderConfig();
      container.appendChild(config);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
