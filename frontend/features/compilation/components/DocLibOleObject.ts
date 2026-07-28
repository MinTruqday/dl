import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibOleObject implements BlockTool {
  static readonly feature = {
    id: "DocLibOleObject",
    title: "DocLib OleObject",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="06b45609fcf8bd9c"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="10,14 5,13 18,14 6,7 6,15 8,8"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { objectId: string };

  static get toolbox() {
    return {
      title: "DocLib OLE Object",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="06b45609fcf8bd9c"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="10,14 5,13 18,14 6,7 6,15 8,8"/></svg>'
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
    this.wrapper.textContent = this.data.objectId;
    this.wrapper.dataset.placeholder = "OLE Object ID";

    this.wrapper.addEventListener("input", () => {
      this.data.objectId = this.wrapper!.textContent || "";
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { objectId: blockContent.textContent || "" };
  }
}
