import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibNextChange implements BlockTool {
  static readonly feature = {
    id: "DocLibNextChange",
    title: "Next Change",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="0226c98309456d62"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="6,8 18,16 13,5 11,17 11,6 19,16"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "Next Change",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="0226c98309456d62"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="6,8 18,16 13,5 11,17 11,6 19,16"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibNextChange";
  readonly title = "Next Change";
  readonly category = "review" as const;
  readonly mode = "NextChange";
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
    const root = document.querySelector<HTMLElement>(".codex-editor");
    if (root) root.dataset.wordReview = this.mode;
    window.dispatchEvent(
      new CustomEvent("doclib-review-command", {
        detail: { command: this.id, mode: this.mode },
      }),
    );
  }
}
