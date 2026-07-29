import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibActiveXTextBox implements BlockTool {
  static readonly feature = {
    id: "DocLibActiveXTextBox",
    title: "DocLib ActiveXTextBox",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="b99d04fc873f5a26"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="19,8 8,18 20,16 9,8 16,6 5,19"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib Active X Text Box",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="b99d04fc873f5a26"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="19,8 8,18 20,16 9,8 16,6 5,19"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibActiveXTextBox";
  readonly title = "DocLib Active X Text Box";
  readonly category = "automation" as const;
  readonly mode = "ActiveXTextBox";
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
    window.dispatchEvent(
      new CustomEvent("doclib-word-automation", {
        detail: { command: this.id, mode: this.mode },
      }),
    );
  }
}
