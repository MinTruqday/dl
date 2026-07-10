import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibIcons implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { iconName: string };

  static get toolbox() {
    return {
      title: "DocLib Icons",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 22h20L12 2z"></path></svg>',
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { iconName: data.iconName || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-icons");
    const input = document.createElement("input");
    input.placeholder = "Enter icon name";
    input.value = this.data.iconName;
    input.addEventListener("input", (e) => {
      this.data.iconName = (e.target as HTMLInputElement).value;
    });
    this.wrapper.appendChild(input);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const input = blockContent.querySelector("input");
    return {
      iconName: input ? input.value : "",
    };
  }
}
