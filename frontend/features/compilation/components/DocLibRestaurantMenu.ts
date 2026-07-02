import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibRestaurantMenu implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Restaurant Menu",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 2v20"></path><path d="M3 2v6a4 4 0 0 0 8 0V2"></path><path d="M21 2v20"></path><path d="M19 14h4"></path><path d="M19 10h4"></path><path d="M19 6h4"></path></svg>',
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
      category: data?.category || "",
      items:
        data?.items && data.items.length > 0
          ? data.items
          : [{ name: "", price: "", desc: "" }],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-menu { font-family: serif; max-width: 600px; margin: 24px auto; padding: 16px; border: 2px solid #1e293b; border-radius: 4px; background: #fafaf9; }
      .doclib-menu-cat { font-size: 28px; font-weight: bold; text-align: center; text-transform: uppercase; margin-bottom: 24px; color: #0f172a; border-bottom: 2px solid #0f172a; padding-bottom: 8px; outline: none; }
      .doclib-menu-cat:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-menu-item { margin-bottom: 16px; position: relative; }
      .doclib-menu-row { display: flex; align-items: baseline; justify-content: space-between; position: relative; z-index: 1; }
      .doclib-menu-row::after { content: ""; position: absolute; bottom: 6px; left: 0; right: 0; border-bottom: 1px dotted #94a3b8; z-index: -1; }
      .doclib-menu-name { font-size: 18px; font-weight: bold; color: #1e293b; background: #fafaf9; padding-right: 8px; outline: none; }
      .doclib-menu-name:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-menu-price { font-size: 18px; font-weight: bold; color: #b91c1c; background: #fafaf9; padding-left: 8px; outline: none; }
      .doclib-menu-price:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-menu-desc { font-size: 14px; color: #475569; font-style: italic; margin-top: 4px; outline: none; }
      .doclib-menu-desc:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-menu-add { margin-top: 16px; padding: 8px 16px; background: #e2e8f0; border: none; border-radius: 4px; cursor: pointer; font-family: sans-serif; font-weight: 500; }
      .doclib-menu-del { position: absolute; right: -30px; top: 0; background: none; border: none; color: #ef4444; cursor: pointer; font-weight: bold; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-menu");

    const catEl = document.createElement("div");
    catEl.classList.add("doclib-menu-cat");
    catEl.innerText = this.data.category;
    catEl.dataset.placeholder = "DocLib Category";
    if (!this.readOnly) {
      catEl.contentEditable = "true";
      catEl.addEventListener("input", () => {
        this.data.category = catEl.innerText;
      });
    }
    container.appendChild(catEl);

    const itemsCont = document.createElement("div");
    container.appendChild(itemsCont);

    const renderItems = () => {
      itemsCont.innerHTML = "";
      this.data.items.forEach((item: any, i: number) => {
        const itemEl = document.createElement("div");
        itemEl.classList.add("doclib-menu-item");

        const row = document.createElement("div");
        row.classList.add("doclib-menu-row");

        const nameEl = document.createElement("div");
        nameEl.classList.add("doclib-menu-name");
        nameEl.innerText = item.name;
        nameEl.dataset.placeholder = "DocLib Dish Name";

        const priceEl = document.createElement("div");
        priceEl.classList.add("doclib-menu-price");
        priceEl.innerText = item.price;
        priceEl.dataset.placeholder = "DocLib Price";

        row.appendChild(nameEl);
        row.appendChild(priceEl);

        const descEl = document.createElement("div");
        descEl.classList.add("doclib-menu-desc");
        descEl.innerText = item.desc;
        descEl.dataset.placeholder = "DocLib Ingredients";

        if (!this.readOnly) {
          nameEl.contentEditable = "true";
          nameEl.addEventListener("input", () => {
            this.data.items[i].name = nameEl.innerText;
          });
          priceEl.contentEditable = "true";
          priceEl.addEventListener("input", () => {
            this.data.items[i].price = priceEl.innerText;
          });
          descEl.contentEditable = "true";
          descEl.addEventListener("input", () => {
            this.data.items[i].desc = descEl.innerText;
          });

          const delBtn = document.createElement("button");
          delBtn.classList.add("doclib-menu-del");
          delBtn.innerText = "X";
          delBtn.addEventListener("click", () => {
            this.data.items.splice(i, 1);
            renderItems();
          });
          itemEl.appendChild(delBtn);
        }

        itemEl.appendChild(row);
        itemEl.appendChild(descEl);
        itemsCont.appendChild(itemEl);
      });
    };

    renderItems();

    if (!this.readOnly) {
      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-menu-add");
      addBtn.innerText = "+ Add Item";
      addBtn.addEventListener("click", () => {
        this.data.items.push({ name: "", price: "", desc: "" });
        renderItems();
      });
      container.appendChild(addBtn);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
