import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibList implements BlockTool {
  private api: API;
  private data: { style: "ordered" | "unordered"; items: string[] };
  private wrapper: HTMLElement | null = null;
  private listElement: HTMLElement | null = null;

  static get toolbox() {
    return {
      title: "DocLib List",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>',
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
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>';

    const orderedBtn = document.createElement("div");
    orderedBtn.classList.add(this.api.styles.settingsButton);
    orderedBtn.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="10" y1="6" x2="21" y2="6"></line><line x1="10" y1="12" x2="21" y2="12"></line><line x1="10" y1="18" x2="21" y2="18"></line><path d="M4 6h1v4"></path><path d="M4 10h2"></path><path d="M6 18H4c0-1 2-2 2-3s-1-1.5-2-1"></path></svg>';

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
