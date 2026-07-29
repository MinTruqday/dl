import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibHighlightColorGreen implements BlockTool {
  static readonly feature = {
    id: "DocLibHighlightColorGreen",
    title: "Highlight Color Green",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="8d72e3100973af94"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="9,16 10,20 13,17 9,16 14,17 9,13"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "Highlight Color Green",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="8d72e3100973af94"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="9,16 10,20 13,17 9,16 14,17 9,13"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibHighlightColorGreen";
  readonly title = "Highlight Color Green";
  readonly category = "format" as const;
  readonly mode = "HighlightColorGreen";
  readonly requiresSelection = false;
  private api?: API;
  private data: BlockToolData;
  private wrapper: HTMLElement | null = null;

  constructor(
    { api, data }: { api?: API; data?: BlockToolData } = {},
  ) {
    this.api = api;
    this.data = data || {};
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add("cdx-block", "doclib-word-command");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = this.title;
    button.classList.add("doclib-word-command__button");
    button.dataset.applied = this.data.applied === true ? "true" : "false";
    button.addEventListener("click", () => {
      if (!this.api || !this.wrapper) return;
      void this.execute(this.api)
        .then(() => {
          if (!this.wrapper) return;
          this.wrapper.dataset.applied = "true";
          button.dataset.applied = "true";
          this.data = {
            feature: this.id,
            mode: this.mode,
            applied: true,
          };
        })
        .catch((error) => {
          if (this.wrapper) {
            this.wrapper.dataset.error =
              error instanceof Error ? error.message : "Command failed";
          }
        });
    });
    this.wrapper.appendChild(button);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return {
      feature: this.id,
      mode: this.mode,
      applied: blockContent.dataset.applied === "true",
    };
  }

  validate(savedData: BlockToolData) {
    return savedData.feature === this.id && savedData.mode === this.mode;
  }

  async execute(editor: any) {
    const selection = window.getSelection();
    const anchor = selection?.anchorNode;
    const element =
      anchor instanceof HTMLElement ? anchor : anchor?.parentElement || null;
    document.execCommand("backColor", false, "#bbf7d0");
  }
}
