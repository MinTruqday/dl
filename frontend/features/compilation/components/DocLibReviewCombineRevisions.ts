import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibReviewCombineRevisions implements BlockTool {
  static readonly feature = {
    id: "DocLibReviewCombineRevisions",
    title: "DocLib ReviewCombineRevisions",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="27f19e47e78581cb"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="9,7 9,7 14,18 14,20 11,17 7,15"/></svg>',
    origin: "microsoft-word",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib ReviewCombineRevisions",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="27f19e47e78581cb"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="9,7 9,7 14,18 14,20 11,17 7,15"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibReviewCombineRevisions";
  readonly title = "DocLib ReviewCombineRevisions";
  readonly category = "review" as const;
  readonly mode = "ReviewCombineRevisions";
  readonly requiresSelection = false;
  readonly microsoftControlId = "ReviewCombineRevisions";
  readonly controlType = "button";
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
    const event = new CustomEvent("doclib-microsoft-word-control", {
      cancelable: true,
      detail: {
        command: this.id,
        controlId: this.microsoftControlId,
        controlType: this.controlType,
        editor,
      },
    });
    window.dispatchEvent(event);
    if (!event.defaultPrevented) {
      throw new Error(`No handler registered for ${this.microsoftControlId}`);
    }
  }
}
