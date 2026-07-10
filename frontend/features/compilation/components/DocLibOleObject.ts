import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibOleObject implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { objectId: string };

  static get toolbox() {
    return {
      title: "DocLib OLE Object",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { objectId: data.objectId || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-ole-object");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.objectId;
    this.wrapper.dataset.placeholder = "OLE Object ID";

    this.wrapper.addEventListener("input", () => {
      this.data.objectId = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { objectId: blockContent.innerHTML };
  }
}
