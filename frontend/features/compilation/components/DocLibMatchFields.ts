import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibMatchFields implements BlockTool {
  static readonly feature = {
    id: "DocLibMatchFields",
    title: "Match Fields",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="d5f4b14f6d5c9223"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="13,10 11,15 11,11 14,5 5,6 5,19"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "Match Fields",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="d5f4b14f6d5c9223"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="13,10 11,15 11,11 14,5 5,6 5,19"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibMatchFields";
  readonly title = "Match Fields";
  readonly category = "mailing" as const;
  readonly mode = "MatchFields";
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
      new CustomEvent("doclib-mailing-command", {
        detail: { command: this.id, mode: this.mode },
      }),
    );
  }
}
