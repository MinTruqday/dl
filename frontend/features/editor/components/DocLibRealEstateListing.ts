import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibRealEstateListing implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib RealEstate Listing",
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
