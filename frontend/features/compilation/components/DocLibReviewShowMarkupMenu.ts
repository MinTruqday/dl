import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibReviewShowMarkupMenu implements BlockTool {
  static readonly feature = {
    id: "DocLibReviewShowMarkupMenu",
    title: "DocLib ReviewShowMarkupMenu",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6f2ef5e0e89d65d0"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="13,16 11,7 15,8 20,8 13,12 11,20"/></svg>',
    origin: "microsoft-word",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib ReviewShowMarkupMenu",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6f2ef5e0e89d65d0"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="13,16 11,7 15,8 20,8 13,12 11,20"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibReviewShowMarkupMenu";
  readonly title = "DocLib ReviewShowMarkupMenu";
  readonly category = "review" as const;
  readonly mode = "ReviewShowMarkupMenu";
  readonly requiresSelection = false;
  readonly microsoftControlId = "ReviewShowMarkupMenu";
  readonly controlType = "menu";
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
