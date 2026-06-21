import os

d = '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend/features/editor/components'

comps = {
    'DocLibProductCard': """import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibProductCard implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib ProductCard",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path><line x1="3" y1="6" x2="21" y2="6"></line><path d="M16 10a4 4 0 0 1-8 0"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      image: data?.image || "",
      title: data?.title || "",
      price: data?.price || "",
      desc: data?.desc || "",
      btnText: data?.btnText || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-prod-card { display: flex; flex-direction: column; max-width: 350px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; font-family: sans-serif; background: #fff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin: 16px auto; }
      .doclib-prod-img-wrap { width: 100%; height: 250px; background: #f8fafc; display: flex; align-items: center; justify-content: center; position: relative; }
      .doclib-prod-img { width: 100%; height: 100%; object-fit: cover; }
      .doclib-prod-img-placeholder { color: #94a3b8; font-size: 14px; }
      .doclib-prod-content { padding: 20px; display: flex; flex-direction: column; gap: 12px; }
      .doclib-prod-title { font-size: 20px; font-weight: 700; color: #0f172a; outline: none; }
      .doclib-prod-title:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-prod-price { font-size: 24px; font-weight: 800; color: #2563eb; outline: none; }
      .doclib-prod-price:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-prod-desc { font-size: 14px; color: #475569; line-height: 1.5; outline: none; }
      .doclib-prod-desc:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-prod-btn { width: 100%; padding: 12px; background: #2563eb; color: #fff; border: none; border-radius: 6px; font-weight: 600; font-size: 16px; cursor: pointer; outline: none; text-align: center; }
      .doclib-prod-btn:empty:before { content: attr(data-placeholder); color: rgba(255,255,255,0.7); }
      .doclib-prod-input { position: absolute; top: 8px; right: 8px; padding: 4px 8px; font-size: 12px; border: 1px solid #cbd5e1; border-radius: 4px; z-index: 10; }
    `;
    this.wrapper.appendChild(style);

    const card = document.createElement("div");
    card.classList.add("doclib-prod-card");

    const imgWrap = document.createElement("div");
    imgWrap.classList.add("doclib-prod-img-wrap");

    const img = document.createElement("img");
    img.classList.add("doclib-prod-img");
    const updateImg = () => {
      if (this.data.image) {
        img.src = this.data.image;
        img.style.display = "block";
      } else {
        img.style.display = "none";
      }
    };
    updateImg();

    const placeholder = document.createElement("div");
    placeholder.classList.add("doclib-prod-img-placeholder");
    placeholder.innerText = "DocLib Image Area";

    if (!this.readOnly) {
      const urlInput = document.createElement("input");
      urlInput.classList.add("doclib-prod-input");
      urlInput.placeholder = "DocLib Image URL";
      urlInput.value = this.data.image;
      urlInput.addEventListener("input", () => {
        this.data.image = urlInput.value;
        updateImg();
      });
      imgWrap.appendChild(urlInput);
    }

    imgWrap.appendChild(placeholder);
    imgWrap.appendChild(img);
    card.appendChild(imgWrap);

    const content = document.createElement("div");
    content.classList.add("doclib-prod-content");

    const titleEl = document.createElement("div");
    titleEl.classList.add("doclib-prod-title");
    titleEl.innerText = this.data.title;
    titleEl.dataset.placeholder = "DocLib Product Name";
    if (!this.readOnly) {
      titleEl.contentEditable = "true";
      titleEl.addEventListener("input", () => { this.data.title = titleEl.innerText; });
    }

    const priceEl = document.createElement("div");
    priceEl.classList.add("doclib-prod-price");
    priceEl.innerText = this.data.price;
    priceEl.dataset.placeholder = "DocLib Price";
    if (!this.readOnly) {
      priceEl.contentEditable = "true";
      priceEl.addEventListener("input", () => { this.data.price = priceEl.innerText; });
    }

    const descEl = document.createElement("div");
    descEl.classList.add("doclib-prod-desc");
    descEl.innerText = this.data.desc;
    descEl.dataset.placeholder = "DocLib Description";
    if (!this.readOnly) {
      descEl.contentEditable = "true";
      descEl.addEventListener("input", () => { this.data.desc = descEl.innerText; });
    }

    const btnEl = document.createElement("div");
    btnEl.classList.add("doclib-prod-btn");
    btnEl.innerText = this.data.btnText;
    btnEl.dataset.placeholder = "DocLib Button Text";
    if (!this.readOnly) {
      btnEl.contentEditable = "true";
      btnEl.addEventListener("input", () => { this.data.btnText = btnEl.innerText; });
    }

    content.appendChild(titleEl);
    content.appendChild(priceEl);
    content.appendChild(descEl);
    content.appendChild(btnEl);
    
    card.appendChild(content);
    this.wrapper.appendChild(card);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
""",
    'DocLibDonationBox': """import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDonationBox implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib DonationBox",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      title: data?.title || "",
      desc: data?.desc || "",
      amounts: data?.amounts && data.amounts.length > 0 ? data.amounts : ["$5", "$10", "$50"],
      customLabel: data?.customLabel || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-don-box { max-width: 400px; padding: 24px; border-radius: 12px; background: #fff; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; margin: 16px auto; font-family: sans-serif; }
      .doclib-don-title { font-size: 24px; font-weight: 700; color: #1e293b; text-align: center; margin-bottom: 8px; outline: none; }
      .doclib-don-title:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-don-desc { font-size: 14px; color: #64748b; text-align: center; margin-bottom: 24px; outline: none; }
      .doclib-don-desc:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-don-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
      .doclib-don-amt { padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; text-align: center; font-weight: 600; color: #334155; outline: none; cursor: pointer; transition: all 0.2s; }
      .doclib-don-amt:focus, .doclib-don-amt:hover { border-color: #10b981; color: #10b981; }
      .doclib-don-custom { width: 100%; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; font-weight: 600; color: #334155; text-align: center; outline: none; margin-bottom: 24px; }
      .doclib-don-custom:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-don-btn { width: 100%; padding: 14px; background: #10b981; color: #fff; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; }
    `;
    this.wrapper.appendChild(style);

    const box = document.createElement("div");
    box.classList.add("doclib-don-box");

    const titleEl = document.createElement("div");
    titleEl.classList.add("doclib-don-title");
    titleEl.innerText = this.data.title;
    titleEl.dataset.placeholder = "DocLib Donation Title";

    const descEl = document.createElement("div");
    descEl.classList.add("doclib-don-desc");
    descEl.innerText = this.data.desc;
    descEl.dataset.placeholder = "DocLib Description";

    if (!this.readOnly) {
      titleEl.contentEditable = "true";
      titleEl.addEventListener("input", () => { this.data.title = titleEl.innerText; });
      descEl.contentEditable = "true";
      descEl.addEventListener("input", () => { this.data.desc = descEl.innerText; });
    }

    const grid = document.createElement("div");
    grid.classList.add("doclib-don-grid");

    this.data.amounts.forEach((amt: string, i: number) => {
      const amtEl = document.createElement("div");
      amtEl.classList.add("doclib-don-amt");
      amtEl.innerText = amt;
      if (!this.readOnly) {
        amtEl.contentEditable = "true";
        amtEl.addEventListener("input", () => { this.data.amounts[i] = amtEl.innerText; });
      }
      grid.appendChild(amtEl);
    });

    const custom = document.createElement("div");
    custom.classList.add("doclib-don-custom");
    custom.innerText = this.data.customLabel;
    custom.dataset.placeholder = "DocLib Custom Amount";
    if (!this.readOnly) {
      custom.contentEditable = "true";
      custom.addEventListener("input", () => { this.data.customLabel = custom.innerText; });
    }

    const btn = document.createElement("button");
    btn.classList.add("doclib-don-btn");
    btn.innerText = "Donate Now";

    box.appendChild(titleEl);
    box.appendChild(descEl);
    box.appendChild(grid);
    box.appendChild(custom);
    box.appendChild(btn);

    this.wrapper.appendChild(box);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
""",
    'DocLibRestaurantMenu': """import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibRestaurantMenu implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib RestaurantMenu",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 2v20"></path><path d="M3 2v6a4 4 0 0 0 8 0V2"></path><path d="M21 2v20"></path><path d="M19 14h4"></path><path d="M19 10h4"></path><path d="M19 6h4"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      category: data?.category || "",
      items: data?.items && data.items.length > 0 ? data.items : [{ name: "", price: "", desc: "" }],
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
      catEl.addEventListener("input", () => { this.data.category = catEl.innerText; });
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
          nameEl.addEventListener("input", () => { this.data.items[i].name = nameEl.innerText; });
          priceEl.contentEditable = "true";
          priceEl.addEventListener("input", () => { this.data.items[i].price = priceEl.innerText; });
          descEl.contentEditable = "true";
          descEl.addEventListener("input", () => { this.data.items[i].desc = descEl.innerText; });

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
""",
    'DocLibRealEstateListing': """import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibRealEstateListing implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib RealEstateListing",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      image: data?.image || "",
      price: data?.price || "",
      address: data?.address || "",
      beds: data?.beds || "",
      baths: data?.baths || "",
      sqft: data?.sqft || "",
      contact: data?.contact || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-re-card { display: flex; flex-direction: column; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; font-family: sans-serif; background: #fff; max-width: 400px; margin: 16px auto; }
      .doclib-re-img-wrap { width: 100%; height: 220px; background: #e2e8f0; position: relative; }
      .doclib-re-img { width: 100%; height: 100%; object-fit: cover; }
      .doclib-re-input { position: absolute; top: 8px; right: 8px; padding: 4px 8px; border-radius: 4px; border: 1px solid #cbd5e1; font-size: 12px; }
      .doclib-re-content { padding: 16px; }
      .doclib-re-price { font-size: 28px; font-weight: bold; color: #1e293b; margin-bottom: 8px; outline: none; }
      .doclib-re-price:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-re-addr { font-size: 15px; color: #64748b; margin-bottom: 16px; outline: none; }
      .doclib-re-addr:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-re-stats { display: flex; gap: 16px; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; padding: 12px 0; margin-bottom: 16px; }
      .doclib-re-stat { display: flex; flex-direction: column; align-items: center; flex: 1; border-right: 1px solid #e2e8f0; }
      .doclib-re-stat:last-child { border-right: none; }
      .doclib-re-stat-val { font-weight: bold; color: #1e293b; font-size: 18px; outline: none; }
      .doclib-re-stat-val:empty:before { content: "0"; color: #94a3b8; }
      .doclib-re-stat-lbl { font-size: 12px; color: #64748b; text-transform: uppercase; }
      .doclib-re-contact { width: 100%; padding: 12px; background: #0f172a; color: #fff; font-weight: bold; border: none; border-radius: 4px; cursor: pointer; outline: none; text-align: center; }
      .doclib-re-contact:empty:before { content: attr(data-placeholder); color: rgba(255,255,255,0.7); }
    `;
    this.wrapper.appendChild(style);

    const card = document.createElement("div");
    card.classList.add("doclib-re-card");

    const imgWrap = document.createElement("div");
    imgWrap.classList.add("doclib-re-img-wrap");

    const img = document.createElement("img");
    img.classList.add("doclib-re-img");
    const updateImg = () => {
      if (this.data.image) {
        img.src = this.data.image;
        img.style.display = "block";
      } else {
        img.style.display = "none";
      }
    };
    updateImg();

    if (!this.readOnly) {
      const urlInput = document.createElement("input");
      urlInput.classList.add("doclib-re-input");
      urlInput.placeholder = "DocLib Image URL";
      urlInput.value = this.data.image;
      urlInput.addEventListener("input", () => {
        this.data.image = urlInput.value;
        updateImg();
      });
      imgWrap.appendChild(urlInput);
    }

    imgWrap.appendChild(img);
    card.appendChild(imgWrap);

    const content = document.createElement("div");
    content.classList.add("doclib-re-content");

    const createField = (key: string, className: string, placeholder: string) => {
      const el = document.createElement("div");
      el.classList.add(className);
      el.innerText = this.data[key];
      el.dataset.placeholder = placeholder;
      if (!this.readOnly) {
        el.contentEditable = "true";
        el.addEventListener("input", () => { this.data[key] = el.innerText; });
      }
      return el;
    };

    content.appendChild(createField("price", "doclib-re-price", "DocLib Price"));
    content.appendChild(createField("address", "doclib-re-addr", "DocLib Address"));

    const stats = document.createElement("div");
    stats.classList.add("doclib-re-stats");

    const createStat = (key: string, lbl: string) => {
      const st = document.createElement("div");
      st.classList.add("doclib-re-stat");
      const val = createField(key, "doclib-re-stat-val", "0");
      const label = document.createElement("div");
      label.classList.add("doclib-re-stat-lbl");
      label.innerText = lbl;
      st.appendChild(val);
      st.appendChild(label);
      return st;
    };

    stats.appendChild(createStat("beds", "Beds"));
    stats.appendChild(createStat("baths", "Baths"));
    stats.appendChild(createStat("sqft", "Sq. Ft."));
    content.appendChild(stats);

    content.appendChild(createField("contact", "doclib-re-contact", "DocLib Contact Agent"));

    card.appendChild(content);
    this.wrapper.appendChild(card);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
""",
    'DocLibCouponCode': """import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibCouponCode implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib CouponCode",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      title: data?.title || "",
      discount: data?.discount || "",
      code: data?.code || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-coupon { border: 2px dashed #f59e0b; border-radius: 12px; padding: 24px; background: #fffbeb; text-align: center; max-width: 400px; margin: 24px auto; position: relative; font-family: sans-serif; }
      .doclib-coupon::before, .doclib-coupon::after { content: ""; position: absolute; width: 20px; height: 20px; background: #fff; border-radius: 50%; top: 50%; transform: translateY(-50%); border: 2px solid #f59e0b; border-left: none; }
      .doclib-coupon::before { left: -12px; border-radius: 0 10px 10px 0; border: 2px dashed #f59e0b; border-left: none; }
      .doclib-coupon::after { right: -12px; border-radius: 10px 0 0 10px; border: 2px dashed #f59e0b; border-right: none; }
      .doclib-coupon-title { font-size: 16px; color: #b45309; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; outline: none; }
      .doclib-coupon-title:empty:before { content: attr(data-placeholder); color: #d97706; }
      .doclib-coupon-discount { font-size: 36px; font-weight: 900; color: #b45309; margin-bottom: 16px; outline: none; }
      .doclib-coupon-discount:empty:before { content: attr(data-placeholder); color: #d97706; }
      .doclib-coupon-code-wrap { display: flex; align-items: center; justify-content: space-between; background: #fff; border: 1px solid #fcd34d; border-radius: 6px; padding: 8px 16px; }
      .doclib-coupon-code { font-family: monospace; font-size: 18px; font-weight: bold; color: #1e293b; letter-spacing: 2px; outline: none; flex: 1; text-align: left; }
      .doclib-coupon-code:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-coupon-copy { padding: 6px 12px; background: #f59e0b; color: #fff; font-weight: bold; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
    `;
    this.wrapper.appendChild(style);

    const box = document.createElement("div");
    box.classList.add("doclib-coupon");

    const titleEl = document.createElement("div");
    titleEl.classList.add("doclib-coupon-title");
    titleEl.innerText = this.data.title;
    titleEl.dataset.placeholder = "DocLib Promo Title";

    const discEl = document.createElement("div");
    discEl.classList.add("doclib-coupon-discount");
    discEl.innerText = this.data.discount;
    discEl.dataset.placeholder = "DocLib Discount";

    if (!this.readOnly) {
      titleEl.contentEditable = "true";
      titleEl.addEventListener("input", () => { this.data.title = titleEl.innerText; });
      discEl.contentEditable = "true";
      discEl.addEventListener("input", () => { this.data.discount = discEl.innerText; });
    }

    const wrap = document.createElement("div");
    wrap.classList.add("doclib-coupon-code-wrap");

    const codeEl = document.createElement("div");
    codeEl.classList.add("doclib-coupon-code");
    codeEl.innerText = this.data.code;
    codeEl.dataset.placeholder = "DOCLIBCODE";

    if (!this.readOnly) {
      codeEl.contentEditable = "true";
      codeEl.addEventListener("input", () => { this.data.code = codeEl.innerText; });
    }

    const btn = document.createElement("button");
    btn.classList.add("doclib-coupon-copy");
    btn.innerText = "Copy";
    btn.addEventListener("click", () => {
      navigator.clipboard.writeText(this.data.code || "DOCLIBCODE").then(() => {
        btn.innerText = "Copied";
        setTimeout(() => { btn.innerText = "Copy"; }, 1500);
      });
    });

    wrap.appendChild(codeEl);
    wrap.appendChild(btn);

    box.appendChild(titleEl);
    box.appendChild(discEl);
    box.appendChild(wrap);

    this.wrapper.appendChild(box);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
"""
}

for k, v in comps.items():
    with open(os.path.join(d, k + '.ts'), 'w') as f:
        f.write(v)

print("Created 5 components")
