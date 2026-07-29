import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibShowMarkupReviewers implements BlockTool {
  static readonly feature = {
    id: "DocLibShowMarkupReviewers",
    title: "Show Markup Reviewers",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ac1c5c3e6233595b"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="6,15 11,15 17,4 8,10 17,16 19,20"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "Show Markup Reviewers",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ac1c5c3e6233595b"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="6,15 11,15 17,4 8,10 17,16 19,20"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibShowMarkupReviewers";
  readonly title = "Show Markup Reviewers";
  readonly category = "review" as const;
  readonly mode = "ShowMarkupReviewers";
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
