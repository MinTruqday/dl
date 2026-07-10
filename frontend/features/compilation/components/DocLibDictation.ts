import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibDictation implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { text: string };

  static get toolbox() {
    return {
      title: "DocLib Dictation",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path></svg>',
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { text: data.text || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-dictation");
    
    const btn = document.createElement("button");
    btn.innerText = "Start Dictation";
    
    const textArea = document.createElement("textarea");
    textArea.value = this.data.text;
    textArea.addEventListener("input", (e) => {
      this.data.text = (e.target as HTMLTextAreaElement).value;
    });

    this.wrapper.appendChild(btn);
    this.wrapper.appendChild(textArea);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const input = blockContent.querySelector("textarea");
    return {
      text: input ? input.value : "",
    };
  }
}
