import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLib3DModels implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { modelUrl: string };

  static get toolbox() {
    return {
      title: "DocLib 3D Models",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><box></box></svg>',
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { modelUrl: data.modelUrl || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-3d-models");
    const input = document.createElement("input");
    input.placeholder = "Enter GLTF model URL";
    input.value = this.data.modelUrl;
    input.addEventListener("input", (e) => {
      this.data.modelUrl = (e.target as HTMLInputElement).value;
    });
    this.wrapper.appendChild(input);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const input = blockContent.querySelector("input");
    return {
      modelUrl: input ? input.value : "",
    };
  }
}
