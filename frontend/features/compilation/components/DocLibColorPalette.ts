import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibColorPalette implements BlockTool {
  static readonly feature = {
    id: "DocLibColorPalette",
    title: "Color Palette",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6b56ae6a91821a18"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="9,5 8,8 13,15 13,11 5,9 10,17"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { title: string; colors: { hex: string; name: string }[] };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "Color Palette",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6b56ae6a91821a18"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="9,5 8,8 13,15 13,11 5,9 10,17"/></svg>',
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
      title: data?.title || "",
      colors: data?.colors || [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-cp2-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-cp2-styles";
      style.innerHTML = `
        .doclib-pal-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; background: #fff; margin: 12px 0; }
        .doclib-pal-title { font-size: 13px; font-weight: 600; color: #0f172a; margin-bottom: 14px; }
        .doclib-pal-swatches { display: flex; flex-wrap: wrap; gap: 10px; }
        .doclib-pal-swatch { display: flex; flex-direction: column; align-items: center; gap: 6px; cursor: pointer; }
        .doclib-pal-color { width: 56px; height: 56px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.08); transition: transform 0.1s; }
        .doclib-pal-swatch:hover .doclib-pal-color { transform: scale(1.08); }
        .doclib-pal-hex { font-size: 10px; font-family: ui-monospace, monospace; color: #64748b; font-weight: 500; }
        .doclib-pal-name { font-size: 10px; color: #94a3b8; }
        .doclib-pal-edit { border-top: 1px solid #f1f5f9; margin-top: 14px; padding-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; }
        .doclib-pal-color-edit { display: flex; align-items: center; gap: 6px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px 8px; }
        .doclib-pal-color-input { width: 28px; height: 28px; border: none; padding: 0; cursor: pointer; border-radius: 4px; }
        .doclib-pal-name-input { font-size: 11px; border: none; background: transparent; outline: none; color: #475569; width: 80px; }
        .doclib-pal-del { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 14px; }
        .doclib-pal-add-btn { padding: 6px 12px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 11px; cursor: pointer; align-self: center; }
        .doclib-pal-copied { font-size: 10px; color: #059669; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-pal-wrapper");

    const title = document.createElement("div");
    title.classList.add("doclib-pal-title");
    title.innerText = this.data.title;

    const swatches = document.createElement("div");
    swatches.classList.add("doclib-pal-swatches");

    this.data.colors.forEach((color) => {
      const swatch = document.createElement("div");
      swatch.classList.add("doclib-pal-swatch");
      swatch.title = `Click to copy ${color.hex}`;

      const colorEl = document.createElement("div");
      colorEl.classList.add("doclib-pal-color");
      colorEl.style.background = color.hex;

      const hexEl = document.createElement("div");
      hexEl.classList.add("doclib-pal-hex");
      hexEl.innerText = color.hex;

      const nameEl = document.createElement("div");
      nameEl.classList.add("doclib-pal-name");
      nameEl.innerText = color.name;

      swatch.addEventListener("click", () => {
        navigator.clipboard.writeText(color.hex).then(() => {
          hexEl.classList.add("doclib-pal-copied");
          hexEl.innerText = "Copied";
          setTimeout(() => {
            hexEl.classList.remove("doclib-pal-copied");
            hexEl.innerText = color.hex;
          }, 1200);
        });
      });

      swatch.appendChild(colorEl);
      swatch.appendChild(hexEl);
      swatch.appendChild(nameEl);
      swatches.appendChild(swatch);
    });

    this.wrapper.appendChild(title);
    this.wrapper.appendChild(swatches);

    if (!this.readOnly) {
      const editArea = document.createElement("div");
      editArea.classList.add("doclib-pal-edit");

      const renderEdits = () => {
        editArea.innerHTML = "";
        this.data.colors.forEach((color, i) => {
          const row = document.createElement("div");
          row.classList.add("doclib-pal-color-edit");

          const colorInput = document.createElement("input");
          colorInput.type = "color";
          colorInput.classList.add("doclib-pal-color-input");
          colorInput.value = color.hex;
          colorInput.addEventListener("input", () => {
            color.hex = colorInput.value;
            this.buildUI();
          });

          const nameInput = document.createElement("input");
          nameInput.classList.add("doclib-pal-name-input");
          nameInput.value = color.name;
          nameInput.placeholder = "DocLib Name";
          nameInput.addEventListener("input", () => {
            color.name = nameInput.value;
          });

          const del = document.createElement("button");
          del.classList.add("doclib-pal-del");
          del.innerText = "x";
          del.addEventListener("click", () => {
            this.data.colors.splice(i, 1);
            this.buildUI();
          });

          row.appendChild(colorInput);
          row.appendChild(nameInput);
          row.appendChild(del);
          editArea.appendChild(row);
        });

        const addBtn = document.createElement("button");
        addBtn.classList.add("doclib-pal-add-btn");
        addBtn.innerText = "Add color";
        addBtn.addEventListener("click", () => {
          this.data.colors.push({ hex: "#6366f1", name: "Indigo" });
          this.buildUI();
        });
        editArea.appendChild(addBtn);
      };

      renderEdits();
      this.wrapper.appendChild(editArea);
    }
  }

  save() {
    return this.data;
  }
}
