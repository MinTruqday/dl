import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibRestrictEditing implements BlockTool {
  static readonly feature = {
    id: "DocLibRestrictEditing",
    title: "DocLib RestrictEditing",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="3b3a3037d262824f"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="12,11 18,8 10,17 15,15 17,18 8,5"/></svg>',
    origin: "word-compatible",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib Restrict Editing",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="3b3a3037d262824f"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="12,11 18,8 10,17 15,15 17,18 8,5"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibRestrictEditing";
  readonly title = "DocLib Restrict Editing";
  readonly category = "review" as const;
  readonly mode = "RestrictEditing";
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
