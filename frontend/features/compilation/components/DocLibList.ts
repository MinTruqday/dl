import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibList implements BlockTool {
  static readonly feature = {
    id: "DocLibList",
    title: "Danh sách",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="15848ce23aef5fe0"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="8,17 8,9 11,5 14,7 9,14 7,11"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private data: { style: "ordered" | "unordered"; items: string[] };
  private wrapper: HTMLElement | null = null;
  private listElement: HTMLElement | null = null;

  static get toolbox() {
    return {
      title: "Danh sách",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="15848ce23aef5fe0"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="8,17 8,9 11,5 14,7 9,14 7,11"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }
  static get enableLineBreaks() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      style: data.style === "ordered" ? "ordered" : "unordered",
      items:
        Array.isArray(data.items) && data.items.length > 0 ? data.items : [""],
    };
  }

  renderSettings() {
    const wrapper = document.createElement("div");
    const unorderedBtn = document.createElement("div");
    unorderedBtn.classList.add(this.api.styles.settingsButton);
    unorderedBtn.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="15848ce23aef5fe0"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="8,17 8,9 11,5 14,7 9,14 7,11"/></svg>';

    const orderedBtn = document.createElement("div");
    orderedBtn.classList.add(this.api.styles.settingsButton);
    orderedBtn.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="15848ce23aef5fe0"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="8,17 8,9 11,5 14,7 9,14 7,11"/></svg>';

    if (this.data.style === "unordered")
      unorderedBtn.classList.add(this.api.styles.settingsButtonActive);
    if (this.data.style === "ordered")
      orderedBtn.classList.add(this.api.styles.settingsButtonActive);

    unorderedBtn.addEventListener("click", () => {
      this.data.style = "unordered";
      this.buildList();
      unorderedBtn.classList.add(this.api.styles.settingsButtonActive);
      orderedBtn.classList.remove(this.api.styles.settingsButtonActive);
    });

    orderedBtn.addEventListener("click", () => {
      this.data.style = "ordered";
      this.buildList();
      orderedBtn.classList.add(this.api.styles.settingsButtonActive);
      unorderedBtn.classList.remove(this.api.styles.settingsButtonActive);
    });

    wrapper.appendChild(unorderedBtn);
    wrapper.appendChild(orderedBtn);
    return wrapper;
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-list-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-list-styles";
      style.innerHTML = `
            .doclib-list { padding-left: 24px; margin: 12px 0; outline: none; }
            .doclib-list li { margin-bottom: 6px; line-height: 1.6; }
        `;
      document.head.appendChild(style);
    }

    this.buildList();
    return this.wrapper;
  }

  private buildList() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    this.listElement = document.createElement(
      this.data.style === "ordered" ? "ol" : "ul",
    );
    this.listElement.classList.add("doclib-list");
    this.listElement.contentEditable = "true";

    this.data.items.forEach((item) => {
      const li = document.createElement("li");
      li.innerHTML = item;
      this.listElement!.appendChild(li);
    });

    this.listElement.addEventListener("input", () => {
      this.data.items = Array.from(
        this.listElement!.querySelectorAll("li"),
      ).map((li) => li.innerHTML);
    });

    this.wrapper.appendChild(this.listElement);
  }

  save() {
    if (this.listElement) {
      this.data.items = Array.from(this.listElement.querySelectorAll("li")).map(
        (li) => li.innerHTML,
      );
    }
    return this.data;
  }

  static get sanitize() {
    return {
      style: true,
      items: { br: true, b: true, i: true, a: true, span: true },
    };
  }
}
