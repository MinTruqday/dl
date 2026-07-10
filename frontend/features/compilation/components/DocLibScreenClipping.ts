import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibScreenClipping implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { imageData: string };

  static get toolbox() {
    return {
      title: "DocLib Screen Clipping",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>',
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { imageData: data.imageData || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-screen-clipping");
    
    const btn = document.createElement("button");
    btn.innerText = "Take Screenshot";
    
    const img = document.createElement("img");
    img.src = this.data.imageData;

    this.wrapper.appendChild(btn);
    this.wrapper.appendChild(img);
    return this.wrapper;
  }

  save() {
    return {
      imageData: this.data.imageData,
    };
  }
}
