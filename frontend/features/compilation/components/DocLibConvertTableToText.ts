import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibConvertTableToText implements BlockTool {
  static get toolbox() {
    return {
      title: "DocLib Convert Table To Text",
      icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M20 6H14M20 12H14M20 18H14M10 12H4L7 9M4 12L7 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    };
  }

  private api: API;
  private data: BlockToolData;
  private wrapper: HTMLElement;

  constructor({ api, data }: { api: API; data: BlockToolData }) {
    this.api = api;
    this.data = data || { content: "" };
    this.wrapper = document.createElement("div");
  }

  render() {
    this.wrapper.classList.add("ce-block");
    const input = document.createElement("input");
    input.classList.add("ce-paragraph", "cdx-block");
    input.value = this.data.content || "";
    input.placeholder = "DocLib Convert Table To Text";
    this.wrapper.appendChild(input);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const input = blockContent.querySelector("input") as HTMLInputElement;
    return {
      content: input ? input.value : "",
    };
  }
}
